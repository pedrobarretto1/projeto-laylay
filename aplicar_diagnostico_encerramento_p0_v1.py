#!/usr/bin/env python3
"""P0 Diagnóstico de encerramento v1 — instrumentação passiva da Laylay.

Este patch NÃO altera políticas de encerramento. Ele apenas acrescenta:
- exit code persistente do subprocesso laylay.py;
- sentinela atexit + faulthandler da mente durante roteiros;
- marcadores finos da finalização do testador;
- stdout/stderr próprio do Terminal 2 apenas durante roteiros.

Uso:
    python aplicar_diagnostico_encerramento_p0_v1.py --dry-run
    python aplicar_diagnostico_encerramento_p0_v1.py
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable

MARCADOR_MODULO = "P0_DIAGNOSTICO_ENCERRAMENTO_V1_20260815"
MARCADOR_EXECUTOR = "P0_DIAGNOSTICO_EXIT_CODE_V1_20260815"
MARCADOR_DESKTOP = "P0_DIAGNOSTICO_TERMINAL_FILHO_V1_20260815"
MARCADOR_ROTEIRO = "P0_DIAGNOSTICO_FINALIZACAO_ROTEIRO_V1_20260815"
MARCADOR_LAYLAY = "P0_DIAGNOSTICO_SENTINELA_LAYLAY_V1_20260815"
MARCADOR_TESTE = "P0_DIAGNOSTICO_ENCERRAMENTO_TESTES_V1_20260815"

ARQUIVO_MODULO = Path("mente_laylay/integracao/diagnostico_encerramento.py")
ARQUIVO_EXECUTOR = Path("cliente/executor_roteiro_laylay.py")
ARQUIVO_DESKTOP = Path("mente_laylay/integracao/desktop_bridge.py")
ARQUIVO_ROTEIRO = Path("mente_laylay/integracao/roteiro_teste_conversa.py")
ARQUIVO_LAYLAY = Path("laylay.py")
ARQUIVO_TESTE = Path("tests/test_p0_diagnostico_encerramento_v1.py")
ARQUIVOS_EXISTENTES = (
    ARQUIVO_EXECUTOR, ARQUIVO_DESKTOP, ARQUIVO_ROTEIRO, ARQUIVO_LAYLAY,
)

MODULO_DIAGNOSTICO = r'''"""Observabilidade passiva para encerramentos inesperados da Laylay."""
from __future__ import annotations

import atexit
import faulthandler
import json
import os
from pathlib import Path
import threading
import time
from typing import Any, TextIO

# P0_DIAGNOSTICO_ENCERRAMENTO_V1_20260815
NOME_LOG_ENCERRAMENTO = "diagnostico_encerramento.log"
NOME_LOG_FALHAS_NATIVAS = "falhas_nativas.log"


def registrar_evento_encerramento(
    diretorio: str | os.PathLike[str],
    evento: str,
    *,
    componente: str = "laylay",
    **campos: Any,
) -> bool:
    """Persiste um evento JSONL com fsync sem afetar a disponibilidade."""
    try:
        pasta = Path(diretorio).expanduser().resolve()
        pasta.mkdir(parents=True, exist_ok=True)
        registro = {
            "ts": time.time(),
            "monotonic": time.monotonic(),
            "pid": os.getpid(),
            "thread": threading.current_thread().name,
            "componente": str(componente or "laylay")[:64],
            "evento": str(evento or "evento")[:96],
        }
        for chave, valor in campos.items():
            nome = str(chave or "")[:64]
            if not nome:
                continue
            registro[nome] = (
                valor
                if isinstance(valor, (str, int, float, bool)) or valor is None
                else str(valor)[:240]
            )
        caminho = pasta / NOME_LOG_ENCERRAMENTO
        with open(caminho, "a", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        return True
    except Exception:
        return False


class SentinelaEncerramento:
    """Mantém a caixa-preta nativa viva e marca saídas Python normais."""
    def __init__(
        self,
        diretorio: str | os.PathLike[str],
        *,
        componente: str = "laylay",
        habilitar_faulthandler: bool = True,
    ) -> None:
        self.diretorio = Path(diretorio).expanduser().resolve()
        self.componente = str(componente or "laylay")[:64]
        self._fault_file: TextIO | None = None
        self._faulthandler_ativo = False
        self._atexit_registrado = False
        self.marcar("processo_observado", python=_versao_python())
        if habilitar_faulthandler:
            self._habilitar_faulthandler()
        try:
            atexit.register(self._ao_sair_normalmente)
            self._atexit_registrado = True
        except Exception:
            self.marcar("atexit_registro_falhou")

    def marcar(self, evento: str, **campos: Any) -> bool:
        return registrar_evento_encerramento(
            self.diretorio, evento, componente=self.componente, **campos,
        )

    def _habilitar_faulthandler(self) -> None:
        try:
            self.diretorio.mkdir(parents=True, exist_ok=True)
            self._fault_file = open(
                self.diretorio / NOME_LOG_FALHAS_NATIVAS,
                "a", encoding="utf-8", buffering=1,
            )
            faulthandler.enable(file=self._fault_file, all_threads=True)
            self._faulthandler_ativo = True
            self.marcar("faulthandler_ativo")
        except Exception as erro:
            self._faulthandler_ativo = False
            self.marcar("faulthandler_indisponivel", erro_tipo=type(erro).__name__)
            try:
                if self._fault_file is not None:
                    self._fault_file.close()
            except Exception:
                pass
            self._fault_file = None

    def _ao_sair_normalmente(self) -> None:
        self.marcar("atexit_iniciado")
        if self._faulthandler_ativo:
            try:
                faulthandler.disable()
            except Exception:
                pass
            self._faulthandler_ativo = False
        self.marcar("atexit_concluido")
        try:
            if self._fault_file is not None and not self._fault_file.closed:
                self._fault_file.flush()
                os.fsync(self._fault_file.fileno())
                self._fault_file.close()
        except Exception:
            pass

    def desregistrar_para_teste(self) -> None:
        if self._atexit_registrado:
            try:
                atexit.unregister(self._ao_sair_normalmente)
            except Exception:
                pass
            self._atexit_registrado = False
        if self._faulthandler_ativo:
            try:
                faulthandler.disable()
            except Exception:
                pass
            self._faulthandler_ativo = False
        try:
            if self._fault_file is not None and not self._fault_file.closed:
                self._fault_file.close()
        except Exception:
            pass


def _versao_python() -> str:
    try:
        import sys
        return ".".join(str(item) for item in sys.version_info[:3])
    except Exception:
        return ""


def criar_sentinela_encerramento(
    diretorio: str | os.PathLike[str], *, componente: str = "laylay",
) -> SentinelaEncerramento:
    return SentinelaEncerramento(diretorio, componente=componente)
'''

TESTE_DIAGNOSTICO = r'''"""Regressões focadas do diagnóstico passivo de encerramento."""
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
'''


def localizar_raiz(explicita: str | None) -> Path:
    candidatos = [Path.cwd(), Path(__file__).resolve().parent]
    if explicita:
        candidatos.insert(0, Path(explicita).expanduser())
    vistos: set[Path] = set()
    for candidato in candidatos:
        atual = candidato.resolve()
        for base in (atual, *atual.parents):
            if base in vistos:
                continue
            vistos.add(base)
            if all((base / rel).is_file() for rel in ARQUIVOS_EXISTENTES):
                return base
    raise SystemExit("Não encontrei a raiz da Laylay. Use --raiz CAMINHO.")


def substituir_uma_vez(texto: str, antigo: str, novo: str, descricao: str) -> str:
    qtd = texto.count(antigo)
    if qtd != 1:
        raise RuntimeError(f"Âncora '{descricao}' esperada 1 vez, encontrada {qtd}.")
    return texto.replace(antigo, novo, 1)


def validar_estado_inicial(raiz: Path) -> bool:
    pares = {
        ARQUIVO_EXECUTOR: MARCADOR_EXECUTOR,
        ARQUIVO_DESKTOP: MARCADOR_DESKTOP,
        ARQUIVO_ROTEIRO: MARCADOR_ROTEIRO,
        ARQUIVO_LAYLAY: MARCADOR_LAYLAY,
    }
    marcados = [marcador in (raiz / arq).read_text(encoding="utf-8") for arq, marcador in pares.items()]
    modulo = raiz / ARQUIVO_MODULO
    teste = raiz / ARQUIVO_TESTE
    if all(marcados) and modulo.is_file() and teste.is_file():
        return (
            MARCADOR_MODULO in modulo.read_text(encoding="utf-8")
            and MARCADOR_TESTE in teste.read_text(encoding="utf-8")
        )
    if any(marcados) or modulo.exists() or teste.exists():
        raise RuntimeError("Estado parcial do patch encontrado; aplicação abortada por segurança.")
    return False


def construir_alteracoes(raiz: Path) -> dict[Path, str]:
    alteracoes: dict[Path, str] = {
        ARQUIVO_MODULO: MODULO_DIAGNOSTICO,
        ARQUIVO_TESTE: TESTE_DIAGNOSTICO,
    }

    # executor ----------------------------------------------------------
    texto = (raiz / ARQUIVO_EXECUTOR).read_text(encoding="utf-8")
    texto = substituir_uma_vez(
        texto,
        "import subprocess\nfrom pathlib import Path\nimport sys\n",
        "import json\nimport os\nimport subprocess\nfrom pathlib import Path\nimport sys\nimport time\n",
        "imports executor",
    )
    texto = substituir_uma_vez(
        texto,
        "\n\ndef executar_roteiro(caminho: str, *, retomar: bool = False) -> int:\n",
        r'''

# P0_DIAGNOSTICO_EXIT_CODE_V1_20260815
def _registrar_saida_processo(
    raiz: Path,
    *,
    roteiro: Path,
    codigo: int,
    iniciado_em: float,
    finalizado_em: float,
    estado: str,
) -> Path | None:
    try:
        pasta = Path(raiz) / "resultados_testes"
        pasta.mkdir(parents=True, exist_ok=True)
        caminho = pasta / "executor_roteiro_exit.log"
        codigo_inteiro = int(codigo)
        registro = {
            "ts": float(finalizado_em),
            "launcher_pid": os.getpid(),
            "roteiro": str(Path(roteiro).name),
            "estado": str(estado or "finalizado"),
            "codigo": codigo_inteiro,
            "codigo_hex": f"0x{codigo_inteiro & 0xFFFFFFFF:08X}",
            "duracao_s": round(max(0.0, float(finalizado_em) - float(iniciado_em)), 3),
        }
        with open(caminho, "a", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        return caminho
    except Exception:
        return None


def executar_roteiro(caminho: str, *, retomar: bool = False) -> int:
''',
        "entrada executar_roteiro",
    )
    texto = substituir_uma_vez(
        texto,
        '''    try:\n        return int(subprocess.call(comando, cwd=str(raiz)))\n    except KeyboardInterrupt:\n        return 130\n'''.replace('\\n','\n'),
        '''    iniciado_em = time.time()\n    ambiente = dict(os.environ)\n    ambiente.setdefault("PYTHONFAULTHANDLER", "1")\n    try:\n        codigo = int(subprocess.call(comando, cwd=str(raiz), env=ambiente))\n        finalizado_em = time.time()\n        caminho_log = _registrar_saida_processo(\n            raiz, roteiro=roteiro, codigo=codigo, iniciado_em=iniciado_em,\n            finalizado_em=finalizado_em, estado="finalizado",\n        )\n        print(\n            "🔬 [ROTEIRO:PROCESSO] laylay.py encerrou "\n            f"| codigo={codigo} hex=0x{codigo & 0xFFFFFFFF:08X}"\n            + (f" | log={caminho_log}" if caminho_log else "")\n        )\n        return codigo\n    except KeyboardInterrupt:\n        _registrar_saida_processo(\n            raiz, roteiro=roteiro, codigo=130, iniciado_em=iniciado_em,\n            finalizado_em=time.time(), estado="interrompido_launcher",\n        )\n        return 130\n'''.replace('\\n','\n'),
        "subprocess.call executor",
    )
    alteracoes[ARQUIVO_EXECUTOR] = texto

    # desktop bridge ----------------------------------------------------
    texto = (raiz / ARQUIVO_DESKTOP).read_text(encoding="utf-8")
    antigo = '''        ambiente.update({\n            "LAYLAY_DESKTOP_HOST": self.host,\n            "LAYLAY_DESKTOP_PORT": str(self.port),\n            "LAYLAY_DESKTOP_TOKEN": self.token,\n            "LAYLAY_PROJECT_ROOT": str(arquivo.parents[1]),\n            "LAYLAY_DESKTOP_SESSION": self.session_id,\n            "LAYLAY_PARENT_PID": str(self.parent_pid),\n            "LAYLAY_PARENT_STARTED_AT": str(self.started_at),\n        })\n        comando = [sys.executable, str(arquivo)]\n        try:\n            self._processo = subprocess.Popen(comando, env=ambiente, cwd=str(arquivo.parents[1]))\n            self.log(\n'''.replace('\\n','\n')
    novo = '''        ambiente.update({\n            "LAYLAY_DESKTOP_HOST": self.host,\n            "LAYLAY_DESKTOP_PORT": str(self.port),\n            "LAYLAY_DESKTOP_TOKEN": self.token,\n            "LAYLAY_PROJECT_ROOT": str(arquivo.parents[1]),\n            "LAYLAY_DESKTOP_SESSION": self.session_id,\n            "LAYLAY_PARENT_PID": str(self.parent_pid),\n            "LAYLAY_PARENT_STARTED_AT": str(self.started_at),\n        })\n        # P0_DIAGNOSTICO_TERMINAL_FILHO_V1_20260815\n        diretorio_diagnostico = str(ambiente.get("LAYLAY_DIAGNOSTICO_DIR") or "").strip()\n        saida_terminal = None\n        if diretorio_diagnostico:\n            ambiente["PYTHONFAULTHANDLER"] = "1"\n            ambiente["PYTHONUNBUFFERED"] = "1"\n            try:\n                pasta_diagnostico = Path(diretorio_diagnostico).resolve()\n                pasta_diagnostico.mkdir(parents=True, exist_ok=True)\n                saida_terminal = open(\n                    pasta_diagnostico / "terminal_cliente.log", "ab", buffering=0,\n                )\n            except OSError as erro:\n                saida_terminal = None\n                self.log(\n                    "⚠️ [TERMINAL 2:DIAGNÓSTICO] log do cliente indisponível "\n                    f"| tipo={type(erro).__name__}"\n                )\n        comando = [sys.executable, str(arquivo)]\n        try:\n            self._processo = subprocess.Popen(\n                comando, env=ambiente, cwd=str(arquivo.parents[1]),\n                stdout=saida_terminal,\n                stderr=subprocess.STDOUT if saida_terminal is not None else None,\n            )\n            self.log(\n'''.replace('\\n','\n')
    texto = substituir_uma_vez(texto, antigo, novo, "spawn Terminal 2")
    antigo = '''            return True\n        except Exception as erro:\n            self.log(f"⚠️ [TERMINAL 2] interface indisponível: {type(erro).__name__}: {erro}")\n            return False\n\n    def _servir(self) -> None:\n'''.replace('\\n','\n')
    novo = '''            return True\n        except Exception as erro:\n            self.log(f"⚠️ [TERMINAL 2] interface indisponível: {type(erro).__name__}: {erro}")\n            return False\n        finally:\n            if saida_terminal is not None:\n                try:\n                    saida_terminal.close()\n                except OSError:\n                    pass\n\n    def _servir(self) -> None:\n'''.replace('\\n','\n')
    texto = substituir_uma_vez(texto, antigo, novo, "handle log Terminal 2")
    alteracoes[ARQUIVO_DESKTOP] = texto

    # roteiro -----------------------------------------------------------
    texto = (raiz / ARQUIVO_ROTEIRO).read_text(encoding="utf-8")
    antigo = '''from mente_laylay.integracao.avaliador_roteiro_teste import (\n    avaliar_turno_roteiro,\n    gravar_relatorios_roteiro,\n)\n# UPGRADE_TESTADOR_SEMANTICO_V32_20260814\n'''.replace('\\n','\n')
    novo = '''from mente_laylay.integracao.avaliador_roteiro_teste import (\n    avaliar_turno_roteiro,\n    gravar_relatorios_roteiro,\n)\nfrom mente_laylay.integracao.diagnostico_encerramento import (\n    registrar_evento_encerramento,\n)\n# UPGRADE_TESTADOR_SEMANTICO_V32_20260814\n'''.replace('\\n','\n')
    texto = substituir_uma_vez(texto, antigo, novo, "import diagnóstico roteiro")
    antigo = '''        # V32: RESUMO_SEMANTICO_FINAL\n        try:\n            resumo_semantico = gravar_relatorios_roteiro(\n                self._estado,\n                self.diretorio,\n            )\n            self.log(\n                "📊 [ROTEIRO:RESUMO] "\n                f"avaliados={resumo_semantico.get('avaliados_semanticamente')} | "\n                f"passaram={resumo_semantico.get('passaram')} | "\n                f"falharam={resumo_semantico.get('falharam')} | "\n                f"alertas={resumo_semantico.get('alertas')} | "\n                f"p95={(resumo_semantico.get('latencia_s') or {}).get('p95')}s"\n            )\n        except Exception as erro:\n            self.log(\n                "⚠️ [ROTEIRO:RELATORIO] relatório final indisponível "\n                f"| tipo={type(erro).__name__}"\n            )\n\n        self.log(\n            f"🧪 [ROTEIRO] {estado} | conversa={self.conversa_path} "\n            f"checkpoint={self.checkpoint_path}"\n        )\n        if callable(self.ao_finalizar):\n            self.ao_finalizar(sucesso_total)\n        return sucesso_total\n'''.replace('\\n','\n')
    novo = '''        # V32: RESUMO_SEMANTICO_FINAL\n        # P0_DIAGNOSTICO_FINALIZACAO_ROTEIRO_V1_20260815\n        registrar_evento_encerramento(\n            self.diretorio, "relatorio_final_iniciado", componente="roteiro",\n            sucesso=bool(sucesso_total),\n        )\n        try:\n            resumo_semantico = gravar_relatorios_roteiro(\n                self._estado,\n                self.diretorio,\n            )\n            registrar_evento_encerramento(\n                self.diretorio, "relatorio_final_concluido", componente="roteiro",\n            )\n            self.log(\n                "📊 [ROTEIRO:RESUMO] "\n                f"avaliados={resumo_semantico.get('avaliados_semanticamente')} | "\n                f"passaram={resumo_semantico.get('passaram')} | "\n                f"falharam={resumo_semantico.get('falharam')} | "\n                f"alertas={resumo_semantico.get('alertas')} | "\n                f"p95={(resumo_semantico.get('latencia_s') or {}).get('p95')}s"\n            )\n            registrar_evento_encerramento(\n                self.diretorio, "resumo_impresso", componente="roteiro",\n            )\n        except Exception as erro:\n            registrar_evento_encerramento(\n                self.diretorio, "relatorio_final_falhou", componente="roteiro",\n                erro_tipo=type(erro).__name__,\n            )\n            self.log(\n                "⚠️ [ROTEIRO:RELATORIO] relatório final indisponível "\n                f"| tipo={type(erro).__name__}"\n            )\n\n        registrar_evento_encerramento(\n            self.diretorio, "log_final_iniciado", componente="roteiro",\n        )\n        self.log(\n            f"🧪 [ROTEIRO] {estado} | conversa={self.conversa_path} "\n            f"checkpoint={self.checkpoint_path}"\n        )\n        registrar_evento_encerramento(\n            self.diretorio, "log_final_concluido", componente="roteiro",\n        )\n        if callable(self.ao_finalizar):\n            registrar_evento_encerramento(\n                self.diretorio, "callback_iniciado", componente="roteiro",\n            )\n            self.ao_finalizar(sucesso_total)\n            registrar_evento_encerramento(\n                self.diretorio, "callback_concluido", componente="roteiro",\n            )\n        return sucesso_total\n'''.replace('\\n','\n')
    texto = substituir_uma_vez(texto, antigo, novo, "finalização roteiro")
    alteracoes[ARQUIVO_ROTEIRO] = texto

    # laylay ------------------------------------------------------------
    texto = (raiz / ARQUIVO_LAYLAY).read_text(encoding="utf-8")
    antigo = '''from mente_laylay.integracao.roteiro_teste_conversa import (\n    RoteiroTesteConversaRuntime as _RoteiroTesteConversaRuntime,\n    carregar_configuracao_roteiro as _carregar_configuracao_roteiro,\n    instalar_espelho_terminal as _instalar_espelho_terminal_roteiro,\n    preparar_diretorio_resultado as _preparar_diretorio_resultado_roteiro,\n)\n'''.replace('\\n','\n')
    novo = '''from mente_laylay.integracao.roteiro_teste_conversa import (\n    RoteiroTesteConversaRuntime as _RoteiroTesteConversaRuntime,\n    carregar_configuracao_roteiro as _carregar_configuracao_roteiro,\n    instalar_espelho_terminal as _instalar_espelho_terminal_roteiro,\n    preparar_diretorio_resultado as _preparar_diretorio_resultado_roteiro,\n)\nfrom mente_laylay.integracao.diagnostico_encerramento import (\n    criar_sentinela_encerramento as _criar_sentinela_encerramento,\n)\n'''.replace('\\n','\n')
    texto = substituir_uma_vez(texto, antigo, novo, "import sentinela laylay")
    texto = substituir_uma_vez(
        texto,
        '''    configuracao_roteiro = None\n    diretorio_resultado_roteiro = None\n    espelhos_terminal: tuple[Any, Any] = ()\n    if caminho_roteiro:\n'''.replace('\\n','\n'),
        '''    configuracao_roteiro = None\n    diretorio_resultado_roteiro = None\n    espelhos_terminal: tuple[Any, Any] = ()\n    sentinela_encerramento = None\n    if caminho_roteiro:\n'''.replace('\\n','\n'),
        "variável sentinela",
    )
    texto = substituir_uma_vez(
        texto,
        '''            espelhos_terminal = _instalar_espelho_terminal_roteiro(\n                diretorio_resultado_roteiro,\n            )\n            print(\n                "🧪 [ROTEIRO] persistência ativada antes dos testes | "\n                f"pasta={diretorio_resultado_roteiro}"\n            )\n'''.replace('\\n','\n'),
        '''            espelhos_terminal = _instalar_espelho_terminal_roteiro(\n                diretorio_resultado_roteiro,\n            )\n            # P0_DIAGNOSTICO_SENTINELA_LAYLAY_V1_20260815\n            sentinela_encerramento = _criar_sentinela_encerramento(\n                diretorio_resultado_roteiro, componente="laylay",\n            )\n            os.environ["LAYLAY_DIAGNOSTICO_DIR"] = str(diretorio_resultado_roteiro)\n            sentinela_encerramento.marcar(\n                "roteiro_persistencia_ativa",\n                encerrar_ao_final=bool(configuracao_roteiro.encerrar_ao_final),\n            )\n            print(\n                "🧪 [ROTEIRO] persistência ativada antes dos testes | "\n                f"pasta={diretorio_resultado_roteiro}"\n            )\n'''.replace('\\n','\n'),
        "criação sentinela",
    )
    texto = substituir_uma_vez(
        texto,
        '''    _inicializacao_runtime.manter_ativo(\n        fala_pronta="",\n        ao_encerrar=_encerrar_laylay,\n        deve_encerrar=lambda: bool(\n'''.replace('\\n','\n'),
        '''    if sentinela_encerramento is not None:\n        sentinela_encerramento.marcar("manter_ativo_entrada")\n    _inicializacao_runtime.manter_ativo(\n        fala_pronta="",\n        ao_encerrar=_encerrar_laylay,\n        deve_encerrar=lambda: bool(\n'''.replace('\\n','\n'),
        "entrada manter_ativo",
    )
    texto = substituir_uma_vez(
        texto,
        '''    )\n    if _reinicio_aplicacao_solicitado.is_set():\n        argumentos = construir_argumentos_reinicio(\n'''.replace('\\n','\n'),
        '''    )\n    if sentinela_encerramento is not None:\n        sentinela_encerramento.marcar(\n            "manter_ativo_retorno",\n            reinicio=bool(_reinicio_aplicacao_solicitado.is_set()),\n            roteiro_finalizado=bool(roteiro_finalizado.is_set()),\n        )\n    if _reinicio_aplicacao_solicitado.is_set():\n        argumentos = construir_argumentos_reinicio(\n'''.replace('\\n','\n'),
        "retorno manter_ativo",
    )
    texto = substituir_uma_vez(
        texto,
        '''    for espelho in espelhos_terminal:\n        fechar = getattr(espelho, "fechar", None)\n        if callable(fechar):\n            fechar()\nif __name__ == "__main__":\n'''.replace('\\n','\n'),
        '''    for espelho in espelhos_terminal:\n        fechar = getattr(espelho, "fechar", None)\n        if callable(fechar):\n            fechar()\n    if sentinela_encerramento is not None:\n        sentinela_encerramento.marcar("main_retorno")\nif __name__ == "__main__":\n'''.replace('\\n','\n'),
        "main retorno",
    )
    alteracoes[ARQUIVO_LAYLAY] = texto
    return alteracoes


def validar_python(alteracoes: dict[Path, str]) -> None:
    for relativo, texto in alteracoes.items():
        if relativo.suffix == ".py":
            try:
                ast.parse(texto, filename=str(relativo))
            except SyntaxError as erro:
                raise RuntimeError(f"AST inválida em {relativo}: {erro}") from erro


def criar_backup(raiz: Path, caminhos: Iterable[Path]) -> Path:
    destino = raiz / "backups" / "p0_diagnostico_encerramento_v1" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    for relativo in caminhos:
        origem = raiz / relativo
        if origem.is_file():
            alvo = destino / relativo
            alvo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origem, alvo)
    return destino


def restaurar(raiz: Path, backup: Path, existentes: set[Path], caminhos: Iterable[Path]) -> None:
    for relativo in caminhos:
        alvo = raiz / relativo
        copia = backup / relativo
        if relativo in existentes and copia.is_file():
            alvo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(copia, alvo)
        elif relativo not in existentes and alvo.exists():
            alvo.unlink()


def escrever(raiz: Path, alteracoes: dict[Path, str]) -> None:
    for relativo, texto in alteracoes.items():
        caminho = raiz / relativo
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(texto, encoding="utf-8", newline="\n")


def executar_testes(raiz: Path) -> None:
    resultado = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(ARQUIVO_TESTE)],
        cwd=str(raiz), text=True, capture_output=True,
    )
    if resultado.stdout:
        print(resultado.stdout.rstrip())
    if resultado.stderr:
        print(resultado.stderr.rstrip(), file=sys.stderr)
    if resultado.returncode != 0:
        raise RuntimeError(f"pytest focado falhou com código {resultado.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raiz", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sem-testes", action="store_true")
    args = parser.parse_args()

    raiz = localizar_raiz(args.raiz)
    print(f"Raiz: {raiz}")
    if validar_estado_inicial(raiz):
        print("✅ P0 diagnóstico de encerramento v1 já está aplicado por completo.")
        return 0

    alteracoes = construir_alteracoes(raiz)
    validar_python(alteracoes)
    print("Arquivos planejados:")
    for relativo in alteracoes:
        print(f"  - {'criar' if not (raiz / relativo).exists() else 'alterar'}: {relativo}")

    if args.dry_run:
        print("✅ Dry-run: âncoras e AST validadas; nada foi escrito.")
        return 0

    existentes = {rel for rel in alteracoes if (raiz / rel).is_file()}
    backup = criar_backup(raiz, alteracoes.keys())
    print(f"Backup: {backup}")
    try:
        escrever(raiz, alteracoes)
        for relativo in alteracoes:
            if relativo.suffix == ".py":
                ast.parse((raiz / relativo).read_text(encoding="utf-8"), filename=str(relativo))
        if not args.sem_testes:
            executar_testes(raiz)
        if not validar_estado_inicial(raiz):
            raise RuntimeError("marcadores finais não reconhecidos")
    except Exception as erro:
        print(f"❌ Falha: {type(erro).__name__}: {erro}")
        print("↩️ Restaurando...")
        restaurar(raiz, backup, existentes, alteracoes.keys())
        print("✅ Rollback concluído.")
        return 1

    print("✅ P0 diagnóstico de encerramento v1 aplicado.")
    print("Nenhuma política de encerramento foi alterada.")
    print("Próximo roteiro produzirá:")
    print("  pasta do teste/diagnostico_encerramento.log")
    print("  pasta do teste/falhas_nativas.log")
    print("  pasta do teste/terminal_cliente.log")
    print("  resultados_testes/executor_roteiro_exit.log")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
