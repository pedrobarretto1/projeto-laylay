"""Regressões focadas do diagnóstico passivo de encerramento."""
from __future__ import annotations

# P0_DIAGNOSTICO_ENCERRAMENTO_TESTES_V1_20260815
import json
from pathlib import Path
import tempfile

from cliente.executor_roteiro_laylay import _registrar_saida_processo
from mente_laylay.integracao.diagnostico_encerramento import (
    SentinelaEncerramento,
    registrar_evento_encerramento,
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


def test_fontes_contem_instrumentacao_sem_mudar_lifecycle() -> None:
    raiz = Path(__file__).resolve().parents[1]
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
