"""Regressões focadas do diagnóstico passivo de encerramento."""
from __future__ import annotations

# P0_DIAGNOSTICO_ENCERRAMENTO_TESTES_V1_20260815
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap

from cliente.executor_roteiro_laylay import _registrar_saida_processo
from mente_laylay.integracao.diagnostico_encerramento import (
    SentinelaEncerramento,
    registrar_evento_encerramento,
)
from mente_laylay.integracao.instancia_unica import (
    codigo_saida_instancia_ocupada,
)


def test_evento_encerramento_e_jsonl_persistente() -> None:
    with tempfile.TemporaryDirectory() as pasta:
        assert registrar_evento_encerramento(
            pasta, "marco_teste", componente="pytest", codigo=7,
        )
        caminho = Path(pasta) / "diagnostico_encerramento.log"
        dado = json.loads(caminho.read_text(encoding="utf-8").splitlines()[-1])
        assert dado["evento"] == "marco_teste"
        assert dado["componente"] == "pytest"
        assert dado["codigo"] == 7
        assert isinstance(dado["pid"], int)


def test_sentinela_registra_inicio_sem_faulthandler() -> None:
    with tempfile.TemporaryDirectory() as pasta:
        sentinela = SentinelaEncerramento(
            pasta, componente="teste", habilitar_faulthandler=False,
        )
        try:
            assert sentinela.marcar("depois_do_inicio", valor=True)
            eventos = [
                json.loads(linha)["evento"]
                for linha in (Path(pasta) / "diagnostico_encerramento.log")
                .read_text(encoding="utf-8").splitlines()
            ]
            assert eventos[:2] == ["processo_observado", "depois_do_inicio"]
        finally:
            sentinela.desregistrar_para_teste()


def _processo_com_callback_tardio(
    pasta: Path, *, falha_nativa: bool = False,
    captura: bool = True, desregistrar: bool = False,
) -> subprocess.CompletedProcess:
    codigo = textwrap.dedent('''
        import atexit, faulthandler, json, os, sys
        from mente_laylay.integracao.diagnostico_encerramento import SentinelaEncerramento
        if os.name == "nt":
            import ctypes
            ctypes.WinDLL("kernel32").SetErrorMode(3)
        def callback_de_encerramento_tardio():
            print("CAPTURA_TARDIA " + json.dumps(faulthandler.is_enabled()), flush=True)
            if sys.argv[2] == "falha":
                faulthandler._sigsegv()
        atexit.register(callback_de_encerramento_tardio)
        sentinela = SentinelaEncerramento(sys.argv[1], habilitar_faulthandler=sys.argv[3] == "ativa")
        print("CAPTURA_INICIAL " + json.dumps(faulthandler.is_enabled()), flush=True)
        if sys.argv[4] == "limpar":
            fd = sentinela._fault_fd
            sentinela.desregistrar_para_teste()
            sentinela.desregistrar_para_teste()
            try:
                os.fstat(fd)
            except OSError:
                print("DESCRITOR_LIBERADO", flush=True)
    ''')
    ambiente = dict(os.environ, PYTHONIOENCODING="utf-8")
    ambiente.pop("PYTHONFAULTHANDLER", None)
    return subprocess.run(
        [sys.executable, "-c", codigo, str(pasta), "falha" if falha_nativa else "normal",
         "ativa" if captura else "inativa", "limpar" if desregistrar else "preservar"],
        cwd=Path(__file__).resolve().parents[2],
        env=ambiente,
        capture_output=True, text=True, encoding="utf-8", timeout=20,
    )


def test_sentinela_mantem_captura_ativa_para_demais_callbacks_de_saida(tmp_path: Path) -> None:
    processo = _processo_com_callback_tardio(tmp_path)
    assert processo.returncode == 0, processo.stderr
    assert "CAPTURA_INICIAL true" in processo.stdout
    assert "CAPTURA_TARDIA true" in processo.stdout, "a sentinela não é o último callback de atexit"


def test_falha_nativa_de_callback_tardio_permanece_na_caixa_preta(tmp_path: Path) -> None:
    # Somente o filho descartável sofre a falha; não inicia Laylay ou hardware.
    processo = _processo_com_callback_tardio(tmp_path, falha_nativa=True)
    assert "CAPTURA_INICIAL true" in processo.stdout
    assert processo.returncode != 0, "uma falha nativa não pode aparentar saída normal"
    nativo = (tmp_path / "falhas_nativas.log").read_text(encoding="utf-8")
    assert "callback_de_encerramento_tardio" in nativo, "a captura foi desativada antes da falha"


def test_sentinela_sem_captura_nao_habilita_handler_nem_abre_arquivo_nativo(tmp_path: Path) -> None:
    processo = _processo_com_callback_tardio(tmp_path, captura=False)
    assert processo.returncode == 0, processo.stderr
    assert "CAPTURA_INICIAL false" in processo.stdout and "CAPTURA_TARDIA false" in processo.stdout
    assert not (tmp_path / "falhas_nativas.log").exists()


def test_desregistro_explicito_para_teste_desativa_e_libera_descritor(tmp_path: Path) -> None:
    processo = _processo_com_callback_tardio(tmp_path, desregistrar=True)
    assert processo.returncode == 0, processo.stderr
    assert "CAPTURA_INICIAL true" in processo.stdout and "CAPTURA_TARDIA false" in processo.stdout
    assert "DESCRITOR_LIBERADO" in processo.stdout


def test_executor_registra_codigo_windows_em_hex() -> None:
    with tempfile.TemporaryDirectory() as pasta:
        raiz = Path(pasta)
        caminho = _registrar_saida_processo(
            raiz, roteiro=raiz / "roteiro.py", codigo=0xC0000005,
            iniciado_em=10.0, finalizado_em=12.5, estado="finalizado",
        )
        assert caminho is not None
        dado = json.loads(Path(caminho).read_text(encoding="utf-8").splitlines()[-1])
        assert dado["codigo"] == 0xC0000005
        assert dado["codigo_hex"] == "0xC0000005"
        assert dado["duracao_s"] == 2.5


def test_instancia_ocupada_nao_pode_fingir_que_roteiro_passou() -> None:
    assert codigo_saida_instancia_ocupada([]) == 0
    assert codigo_saida_instancia_ocupada([
        "--roteiro", "roteiro_teste_personalidade_viva_p15.py",
    ]) != 0


def test_fontes_contem_instrumentacao_sem_mudar_lifecycle() -> None:
    raiz = Path(__file__).resolve().parents[2]
    laylay = (raiz / "laylay.py").read_text(encoding="utf-8")
    assert "P0_DIAGNOSTICO_SENTINELA_LAYLAY_V1_20260815" in laylay
    assert 'os.environ["LAYLAY_DIAGNOSTICO_DIR"]' in laylay
    assert "configuracao_roteiro.encerrar_ao_final" in laylay

    roteiro = (raiz / "mente_laylay/integracao/roteiro_teste_conversa.py").read_text(encoding="utf-8")
    assert "P0_DIAGNOSTICO_FINALIZACAO_ROTEIRO_V1_20260815" in roteiro
    assert '"resumo_impresso"' in roteiro
    assert '"callback_concluido"' in roteiro

    desktop = (raiz / "mente_laylay/integracao/desktop_bridge.py").read_text(encoding="utf-8")
    assert "P0_DIAGNOSTICO_TERMINAL_FILHO_V1_20260815" in desktop
    assert 'ambiente["PYTHONFAULTHANDLER"] = "1"' in desktop
    assert '"terminal_cliente.log"' in desktop
