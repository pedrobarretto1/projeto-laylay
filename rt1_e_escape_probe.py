# -*- coding: utf-8 -*-
"""
R1-RT1-E — probe causal do escape de repetição tipada no runtime real.

Regra:
    produção inteira acima da infraestrutura;
    dublê somente onde o mundo físico começa.

Este driver NÃO importa planner/coordenador/árbitro da Laylay.
Cada cenário entra por:
    laylay.py --roteiro
        -> RoteiroTesteConversaRuntime
        -> entrada canônica
        -> RespostaIARuntime
        -> ComposicaoTurnoRuntime
        -> comandos prioritários
        -> CicloComandosRuntime
        -> RoteadorIntencao
        -> executor real

Isolamento:
- o checkout atual é copiado para um snapshot descartável;
- memoria/, credenciais, resultados, .git e venvs não são copiados;
- cada cenário recebe USERPROFILE/HOME próprios;
- IoT usa o ProtocoloSimulado oficial;
- Gmail usa GmailMental real, trocando somente imaplib.IMAP4_SSL;
- voz é silenciada pelo modo oficial de roteiro.

O script NÃO executa git pull/reset/checkout e NÃO altera o R1-V1.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


NOME = "R1-RT1-E-ESCAPE-PROBE"
ARQUIVO_LAYLAY = "laylay.py"
TIMEOUT_CENARIO_S = 180

MUTACOES_INCOMPATIVEIS_COM_LER = {
    "IOT_CONTROL",
    "DELETE_ITEM",
    "CONFIRM_DELETE_ITEM",
    "FILE_TRANSACTION",
    "CREATE_FILE",
    "CREATE_FOLDER",
    "MOVE_ITEM",
    "APP_OPEN",
    "CLOSE_APP",
    "OPEN_URL",
    "MEDIA_CONTROL",
}

IGNORAR_GLOBAL = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    ".venv314",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "runtime_llm",
    "modelos",
}

IGNORAR_RAIZ = {
    "memoria",
    "resultados_testes",
    "resultados_rt1_r1",
    ".r1_v1_backup_pre_candidato",
    "configuracao.env",
    ".env",
    "playlists.json",
}


@dataclass(frozen=True)
class Cenario:
    codigo: str
    descricao: str
    comandos: tuple[str, ...]
    gmail_fake: bool = False


CENARIOS = (
    Cenario(
        "E",
        "ESCAPE PROBE: IOT_CONTROL -> Leia de novo",
        (
            "Liga a lâmpada.",
            "Leia de novo.",
        ),
    ),
)


@dataclass
class ResultadoCenario:
    codigo: str
    descricao: str
    estado: str = "INFRA"
    fronteira: str = ""
    detalhes: list[str] | None = None
    returncode: int | None = None
    resultado_runtime: str = ""
    terminal_log: str = ""
    physical_log: str = ""

    def __post_init__(self) -> None:
        if self.detalhes is None:
            self.detalhes = []


def achar_raiz() -> Path:
    candidatos = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    for candidato in candidatos:
        if (candidato / ARQUIVO_LAYLAY).is_file():
            return candidato
    raise SystemExit(
        f"❌ {ARQUIVO_LAYLAY} não encontrado. "
        "Coloque este arquivo na raiz do projeto e execute de lá."
    )


PROJETO = achar_raiz()
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
SAIDA = PROJETO / "resultados_rt1_r1" / f"r1_rt1e-{STAMP}"
SAIDA.mkdir(parents=True, exist_ok=True)


def run_texto(args: list[str], *, cwd: Path) -> str:
    try:
        p = subprocess.run(
            args,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        return (p.stdout or "").strip()
    except Exception as exc:
        return f"<indisponivel:{type(exc).__name__}>"


def selecionar_python() -> Path:
    candidatos = (
        PROJETO / ".venv314" / "Scripts" / "python.exe",
        PROJETO / ".venv" / "Scripts" / "python.exe",
        Path(sys.executable),
    )
    for candidato in candidatos:
        if candidato.is_file():
            return candidato.resolve()
    return Path(sys.executable).resolve()


PYTHON = selecionar_python()


def descobrir_userbase_runtime() -> str:
    """Preserva somente a base de pacotes do usuário do Python real.

    O RT1 troca APPDATA/HOME/USERPROFILE para isolar dados da aplicação.
    No Windows, porém, isso também mudaria o user site-packages e esconderia
    dependências instaladas em AppData\\Roaming\\Python. Consultamos o
    interpretador escolhido antes do sandbox e fixamos PYTHONUSERBASE.
    """
    try:
        p = subprocess.run(
            [
                str(PYTHON),
                "-c",
                "import site; print(site.getuserbase() or '')",
            ],
            cwd=str(PROJETO),
            env=dict(os.environ),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
        if p.returncode == 0:
            valor = (p.stdout or "").strip().splitlines()
            if valor:
                caminho = valor[-1].strip()
                if caminho:
                    return caminho
    except Exception:
        pass
    return ""


PYTHON_USERBASE = descobrir_userbase_runtime()


def registrar_proveniencia() -> dict[str, Any]:
    head = run_texto(["git", "rev-parse", "HEAD"], cwd=PROJETO)
    branch = run_texto(["git", "branch", "--show-current"], cwd=PROJETO)
    status = run_texto(["git", "status", "--short"], cwd=PROJETO)
    dados = {
        "teste": NOME,
        "criado_em": time.time(),
        "projeto": str(PROJETO),
        "python_driver": sys.executable,
        "python_runtime": str(PYTHON),
        "python_userbase_preservado": PYTHON_USERBASE,
        "git_head": head,
        "git_branch": branch,
        "git_status_short": status.splitlines() if status else [],
        "nota": "Nenhum pull/reset/checkout foi executado pelo RT1.",
    }
    (SAIDA / "proveniencia.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return dados


def _ignore_copy(src: str, names: list[str]) -> set[str]:
    src_path = Path(src).resolve()
    ignorados: set[str] = set()

    for nome in names:
        if nome in IGNORAR_GLOBAL:
            ignorados.add(nome)
        elif nome.endswith((".pyc", ".pyo")):
            ignorados.add(nome)

    try:
        relativo = src_path.relative_to(PROJETO)
    except ValueError:
        relativo = None

    if relativo == Path("."):
        for nome in names:
            if nome in IGNORAR_RAIZ or nome.startswith("resultados_rt1_r1"):
                ignorados.add(nome)

    return ignorados


def criar_snapshot() -> tuple[Path, Path]:
    raiz_temp = Path(tempfile.mkdtemp(prefix="laylay_r1_rt1_")).resolve()
    snapshot = raiz_temp / "repo"
    print(f"📦 Snapshot descartável: {snapshot}")
    shutil.copytree(
        PROJETO,
        snapshot,
        ignore=_ignore_copy,
        copy_function=shutil.copy2,
    )
    return raiz_temp, snapshot


SITE_CUSTOMIZE = r"""
from __future__ import annotations
import json
import os
import time
import sys
import threading

def _log(tipo, **dados):
    caminho = str(os.environ.get("LAYLAY_RT1_PHYSICAL_LOG") or "").strip()
    if not caminho:
        return
    try:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "a", encoding="utf-8") as f:
            f.write(json.dumps(
                {"ts": time.time(), "tipo": tipo, **dados},
                ensure_ascii=False,
                default=str,
            ) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


_log("sitecustomize_ready")

def _trace(tipo, **dados):
    caminho = str(os.environ.get("LAYLAY_RT1_TRACE_LOG") or "").strip()
    if not caminho:
        return
    try:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "a", encoding="utf-8") as f:
            f.write(json.dumps(
                {"ts": time.time(), "tipo": tipo, **dados},
                ensure_ascii=False,
                default=str,
            ) + "\n")
            f.flush()
    except Exception:
        pass

def _receipts(estado):
    try:
        continuidade = dict((estado or {}).get("continuidade_geral") or {})
        brutos = dict(continuidade.get("operacoes_reexecutaveis") or {})
        saida = {}
        for chave, valor in brutos.items():
            item = dict(valor or {}) if isinstance(valor, dict) else {}
            saida[str(chave)] = {
                "intent": str(item.get("intent") or ""),
                "dominio": str(item.get("dominio") or ""),
                "alvo": str(item.get("alvo") or ""),
                "params": dict(item.get("params") or {}) if isinstance(item.get("params"), dict) else {},
                "status": str(item.get("status") or ""),
                "origem": str(item.get("origem") or ""),
                "id_solicitacao": str(item.get("id_solicitacao") or ""),
                "reexecutavel": item.get("reexecutavel"),
                "ts": item.get("ts"),
            }
        return saida
    except Exception:
        return {}

def _estado_diag(estado):
    try:
        continuidade = dict((estado or {}).get("continuidade_geral") or {})
        return {
            "dominio_ativo": str(continuidade.get("dominio_ativo") or ""),
            "receipts": _receipts(estado),
            "ultima_acao_intent": str((estado or {}).get("ultima_acao_intent") or ""),
            "ultima_acao_status": str((estado or {}).get("ultima_acao_status") or ""),
            "ultima_acao_reexecutavel": (estado or {}).get("ultima_acao_reexecutavel"),
        }
    except Exception:
        return {"receipts": {}}

_ALVOS_EXATOS = {
    ("compatibilidade_contexto.py", "resolver_repeticao_ultima_acao"),
    ("continuidade_geral.py", "selecionar_operacao_reexecutavel_compativel"),
    ("orquestrador_deterministico.py", "detectar_intencao_deterministica_mente"),
    ("orquestrador_deterministico.py", "detectar"),
    ("contexto_imediato.py", "resolver"),
    ("contexto_imediato.py", "resolver_iot"),
    ("contexto_imediato.py", "resolver_acao_geral"),
    ("contexto_imediato.py", "resolver_semantico"),
    ("contexto_imediato.py", "resolver_comando_contextual"),
    ("contexto_imediato.py", "resolver_comando_acao_geral_contextual"),
    ("coordenador_intencao.py", "resolver_intencao"),
    ("coordenador_intencao.py", "_resolver_decisao_canonica"),
    ("coordenador_intencao.py", "resolver_comando_natural"),
    ("coordenador_intencao.py", "executar_intencao"),
    ("roteador_intencao.py", "executar_intencao"),
    ("arbitro_turno.py", "arbitrar_turno"),
    ("comandos_imediatos.py", "processar_prioritarios"),
}

def _compactar(valor, profundidade=0):
    if profundidade > 4:
        return "<depth>"
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    if isinstance(valor, dict):
        saida = {}
        for chave, item in list(valor.items())[:40]:
            saida[str(chave)] = _compactar(item, profundidade + 1)
        return saida
    if isinstance(valor, (list, tuple, set)):
        return [_compactar(item, profundidade + 1) for item in list(valor)[:40]]
    try:
        return str(valor)
    except Exception:
        return f"<{type(valor).__name__}>"

def _contem_intent(valor, procurado="IOT_CONTROL"):
    alvo = str(procurado or "").upper()
    if isinstance(valor, dict):
        intent = str(valor.get("intent") or valor.get("acao") or "").upper().strip()
        if intent == alvo:
            return True
        return any(_contem_intent(v, alvo) for v in valor.values())
    if isinstance(valor, (list, tuple, set)):
        return any(_contem_intent(v, alvo) for v in valor)
    return False

def _primeiro_intent(valor):
    if isinstance(valor, dict):
        intent = str(valor.get("intent") or valor.get("acao") or "").upper().strip()
        if intent:
            return intent
        for item in valor.values():
            achado = _primeiro_intent(item)
            if achado:
                return achado
    elif isinstance(valor, (list, tuple, set)):
        for item in valor:
            achado = _primeiro_intent(item)
            if achado:
                return achado
    return ""

def _texto_local(loc):
    for chave in (
        "texto", "texto_normalizado", "texto_original", "texto_detector",
        "texto_detector_deterministico", "texto_norm", "bruto", "t",
    ):
        valor = loc.get(chave)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()[:300]
    return ""

def _entrada_operacional(loc):
    for chave in (
        "resultado", "candidato", "candidato_imediato", "intent_deterministica",
        "intent_contextual", "intent_repeticao", "resultado_resolvido",
    ):
        valor = loc.get(chave)
        if isinstance(valor, (dict, list, tuple)):
            return _compactar(valor)
    return None

def _eh_alvo(caminho, arquivo, funcao):
    if (arquivo, funcao) in _ALVOS_EXATOS:
        return True
    # Captura o detector IoT real sem depender do nome exato do módulo/classe.
    caminho_norm = caminho.replace("\\", "/").casefold()
    if "/iot/" in caminho_norm and funcao in {"detectar", "detect"}:
        return True
    return False

def _profile(frame, event, arg):
    if event not in {"call", "return"}:
        return
    try:
        caminho = str(frame.f_code.co_filename or "").replace("\\", "/")
        arquivo = caminho.rsplit("/", 1)[-1]
        funcao = str(frame.f_code.co_name or "")
        if not _eh_alvo(caminho, arquivo, funcao):
            return

        loc = frame.f_locals
        texto = _texto_local(loc)

        if event == "call":
            entrada = _entrada_operacional(loc)
            dados = {
                "arquivo": arquivo,
                "caminho_tail": "/".join(caminho.split("/")[-4:]),
                "funcao": funcao,
                "texto": texto,
                "entrada": entrada,
                "entrada_contem_iot": _contem_intent(entrada),
                "entrada_intent": _primeiro_intent(entrada),
            }
            if arquivo == "compatibilidade_contexto.py" and funcao == "resolver_repeticao_ultima_acao":
                dados["estado_antes"] = _estado_diag(loc.get("estado_atual"))
            _trace("rota_call", **dados)
            return

        retorno = _compactar(arg)
        dados = {
            "arquivo": arquivo,
            "caminho_tail": "/".join(caminho.split("/")[-4:]),
            "funcao": funcao,
            "texto": texto,
            "retorno": retorno,
            "retorno_contem_iot": _contem_intent(arg),
            "retorno_intent": _primeiro_intent(arg),
        }

        if arquivo == "compatibilidade_contexto.py" and funcao == "resolver_repeticao_ultima_acao":
            rep = loc.get("repeticao")
            dados["classificacao"] = (
                dict(rep or {}) if isinstance(rep, dict) else {}
            )
            dados["permitidos"] = [str(x) for x in (loc.get("permitidos") or ())]
            dados["oficial_tipado"] = (
                dict(loc.get("oficial_tipado") or {})
                if isinstance(loc.get("oficial_tipado"), dict)
                else {}
            )

        if arquivo == "continuidade_geral.py" and funcao == "selecionar_operacao_reexecutavel_compativel":
            dados["permitidos"] = [str(x) for x in (loc.get("permitidos") or loc.get("intents_permitidos") or ())]
            dados["candidatos"] = _compactar(loc.get("candidatos") or [])

        if arquivo == "arbitro_turno.py" and funcao == "arbitrar_turno":
            dados["candidatos"] = _compactar(loc.get("candidatos") or [])

        _trace("rota_return", **dados)
    except Exception:
        return

sys.setprofile(_profile)
threading.setprofile(_profile)
_trace("escape_probe_ready")

# Observa o protocolo simulado sem substituir seu comportamento.
try:
    from mente_laylay.iot.protocolos.simulado import ProtocoloSimulado

    _orig_consultar = ProtocoloSimulado.consultar_estado
    _orig_definir = ProtocoloSimulado.definir_estado
    _orig_parametros = ProtocoloSimulado.definir_parametros

    def _consultar(self, dispositivo):
        retorno = _orig_consultar(self, dispositivo)
        _log(
            "iot_consultar_estado",
            dispositivo=getattr(dispositivo, "nome", str(dispositivo)),
            sucesso=getattr(retorno, "sucesso", None),
            estado=getattr(retorno, "estado", None),
            confirmado=getattr(retorno, "confirmado", None),
        )
        return retorno

    def _definir(self, dispositivo, ligado):
        retorno = _orig_definir(self, dispositivo, ligado)
        _log(
            "iot_definir_estado",
            dispositivo=getattr(dispositivo, "nome", str(dispositivo)),
            ligado=bool(ligado),
            sucesso=getattr(retorno, "sucesso", None),
            estado=getattr(retorno, "estado", None),
            confirmado=getattr(retorno, "confirmado", None),
        )
        return retorno

    def _parametros(self, dispositivo, acao, parametros):
        retorno = _orig_parametros(self, dispositivo, acao, parametros)
        _log(
            "iot_definir_parametros",
            dispositivo=getattr(dispositivo, "nome", str(dispositivo)),
            acao=str(acao),
            sucesso=getattr(retorno, "sucesso", None),
            estado=getattr(retorno, "estado", None),
            confirmado=getattr(retorno, "confirmado", None),
        )
        return retorno

    ProtocoloSimulado.consultar_estado = _consultar
    ProtocoloSimulado.definir_estado = _definir
    ProtocoloSimulado.definir_parametros = _parametros
except Exception as exc:
    _log("iot_observer_install_error", erro=type(exc).__name__)

# Gmail: substitui somente a fronteira IMAP externa.
if str(os.environ.get("LAYLAY_RT1_FAKE_IMAP") or "") == "1":
    try:
        import imaplib

        _CABECALHO = (
            b"From: Banco RT1 <alerta@rt1.example>\r\n"
            b"Subject: Urgente RT1\r\n"
            b"Reply-To: alerta@rt1.example\r\n"
            b"Return-Path: <alerta@rt1.example>\r\n"
            b"Authentication-Results: mx.rt1.example; "
            b"spf=pass smtp.mailfrom=rt1.example; "
            b"dkim=pass header.d=rt1.example; "
            b"dmarc=pass header.from=rt1.example\r\n"
            b"\r\n"
        )

        class FakeIMAP4SSL:
            def __init__(self, host, port=993, *args, **kwargs):
                self.host = host
                self.port = port
                _log("imap_connect", host=str(host), port=int(port))

            def login(self, usuario, senha):
                _log("imap_login", usuario=str(usuario), senha_exposta=False)
                return "OK", [b"LOGIN completed"]

            def select(self, mailbox="INBOX", readonly=False):
                _log("imap_select", mailbox=str(mailbox), readonly=bool(readonly))
                return "OK", [b"1"]

            def uid(self, comando, *args):
                nome = str(comando or "").upper()
                if nome == "SEARCH":
                    _log("imap_search", args=[str(x) for x in args])
                    return "OK", [b"101"]
                if nome == "FETCH":
                    _log("imap_fetch", args=[str(x) for x in args])
                    meta = (
                        b"101 (UID 101 BODY[HEADER.FIELDS "
                        b"(FROM SUBJECT REPLY-TO AUTHENTICATION-RESULTS RETURN-PATH)] "
                        + str(len(_CABECALHO)).encode("ascii")
                        + b")"
                    )
                    return "OK", [(meta, _CABECALHO)]
                _log("imap_uid_outro", comando=nome, args=[str(x) for x in args])
                return "OK", [b""]

            def logout(self):
                _log("imap_logout")
                return "BYE", [b"LOGOUT completed"]

            def close(self):
                _log("imap_close")
                return "OK", [b"CLOSE completed"]

        imaplib.IMAP4_SSL = FakeIMAP4SSL
        _log("imap_fake_instalado")
    except Exception as exc:
        _log("imap_fake_install_error", erro=type(exc).__name__)
"""


def escrever_hook(raiz_temp: Path) -> Path:
    hook = raiz_temp / "rt1_hook"
    hook.mkdir(parents=True, exist_ok=True)
    (hook / "sitecustomize.py").write_text(
        textwrap.dedent(SITE_CUSTOMIZE),
        encoding="utf-8",
    )
    return hook


def limpar_estado_snapshot(snapshot: Path) -> None:
    for nome in ("memoria", "logs", "resultados_testes"):
        shutil.rmtree(snapshot / nome, ignore_errors=True)
    alvo = snapshot / "playlists.json"
    try:
        if alvo.exists():
            alvo.unlink()
    except OSError:
        pass


def criar_home(cenario_dir: Path) -> Path:
    home = cenario_dir / "home"
    for nome in ("Downloads", "Desktop", "Documents", "Pictures"):
        (home / nome).mkdir(parents=True, exist_ok=True)
    (home / "AppData" / "Roaming").mkdir(parents=True, exist_ok=True)
    (home / "AppData" / "Local").mkdir(parents=True, exist_ok=True)
    (home / "Temp").mkdir(parents=True, exist_ok=True)
    return home


def escrever_roteiro(cenario_dir: Path, cenario: Cenario) -> Path:
    roteiro = cenario_dir / f"roteiro_r1_rt1_{cenario.codigo.lower()}.py"
    texto = "\n".join(
        [
            "# gerado por rt1_r1_runtime_real.py",
            f"COMANDOS = {repr(list(cenario.comandos))}",
            "ATRASO_INICIAL_S = 0.0",
            "TIMEOUT_RESPOSTA_S = 90.0",
            "TIMEOUT_VOZ_S = 30.0",
            "INTERVALO_ENTRE_COMANDOS_S = 0.05",
            "PARAR_SEM_RESPOSTA = True",
            "ENCERRAR_AO_FINAL = True",
            "SILENCIAR_VOZ_DURANTE_TESTE = True",
            "AGUARDAR_CONFIRMACAO_EXECUCAO = True",
            "EXPECTATIVAS_SEMANTICAS = {}",
            "",
        ]
    )
    roteiro.write_text(texto, encoding="utf-8")
    return roteiro


def ambiente_cenario(
    *,
    home: Path,
    hook: Path,
    snapshot: Path,
    cenario_dir: Path,
    gmail_fake: bool,
) -> dict[str, str]:
    env = dict(os.environ)
    drive, tail = os.path.splitdrive(str(home))

    env.update(
        {
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            # APPDATA/HOME ficam isolados, mas os pacotes já instalados no
            # user site do Python real permanecem importáveis.
            "PYTHONUSERBASE": PYTHON_USERBASE,
            "USERPROFILE": str(home),
            "HOME": str(home),
            "HOMEDRIVE": drive or env.get("HOMEDRIVE", ""),
            "HOMEPATH": tail or str(home),
            "APPDATA": str(home / "AppData" / "Roaming"),
            "LOCALAPPDATA": str(home / "AppData" / "Local"),
            "TEMP": str(home / "Temp"),
            "TMP": str(home / "Temp"),
            "LAYLAY_IOT_MODO": "simulado",
            "IOT_CONTROLE_FISICO_AUTORIZADO": "NAO",
            "LAYLAY_TERMINAL_2": "0",
            "LAYLAY_PREAQUECER_LLM": "0",
            "LAYLAY_FALAS_INICIAIS": "0",
            "LAYLAY_BRIEFING_INICIAL": "0",
            "LAYLAY_MODO_JOGO_AUTO": "0",
            "LAYLAY_OVERLAY_JOGO_BORDERLESS": "0",
            "LAYLAY_LOG_MODE": "limpo",
            "LAYLAY_LOG_VERBOSE": "0",
            "LAYLAY_RT1_PHYSICAL_LOG": str(cenario_dir / "physical.jsonl"),
            "LAYLAY_RT1_TRACE_LOG": str(cenario_dir / "trace_receipts.jsonl"),
            "LAYLAY_RT1_FAKE_IMAP": "1" if gmail_fake else "0",
            "GMAIL_USER": "rt1@example.test" if gmail_fake else "",
            "GMAIL_APP_PASSWORD": "rt1-fake-password" if gmail_fake else "",
            "GMAIL_INTERVALO_S": "86400",
            "GMAIL_MAX_LIDOS": "5",
            # A R1 deve ser resolvida antes da conversa livre. Uma porta local
            # recusada evita carregar Ollama/llama-server no fail-closed.
            "LAYLAY_LLM_BACKEND": "remoto",
            "LAYLAY_LLM_BASE_URL": "http://127.0.0.1:9/v1",
            "LAYLAY_LLM_API_KEY": "rt1-local",
            "OPENROUTER_API_KEY": "",
            "GROQ_API_KEY": "",
        }
    )

    antigo = str(env.get("PYTHONPATH") or "").strip()
    partes = [str(hook), str(snapshot)]
    if antigo:
        partes.append(antigo)
    env["PYTHONPATH"] = os.pathsep.join(partes)
    return env


def ler_jsonl(caminho: Path) -> list[dict[str, Any]]:
    saida: list[dict[str, Any]] = []
    if not caminho.is_file():
        return saida
    for linha in caminho.read_text(encoding="utf-8", errors="replace").splitlines():
        linha = linha.strip()
        if not linha:
            continue
        try:
            item = json.loads(linha)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            saida.append(item)
    return saida


def ultimo_resultado_runtime(resultado_raiz: Path) -> Path | None:
    if not resultado_raiz.is_dir():
        return None
    dirs = [p for p in resultado_raiz.iterdir() if p.is_dir()]
    return max(dirs, key=lambda p: p.stat().st_mtime) if dirs else None


def planos_por_indice(resultado_runtime: Path | None) -> dict[int, dict[str, Any]]:
    if resultado_runtime is None:
        return {}
    saida: dict[int, dict[str, Any]] = {}
    for registro in ler_jsonl(resultado_runtime / "planos.jsonl"):
        try:
            indice = int(registro.get("indice"))
        except (TypeError, ValueError):
            continue
        plano = registro.get("plano")
        if isinstance(plano, dict):
            saida[indice] = dict(plano)
    return saida


def comandos_plano(plano: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(plano, dict):
        return []
    return [
        dict(x)
        for x in list(plano.get("comandos") or [])
        if isinstance(x, dict)
    ]


def intents(plano: dict[str, Any] | None) -> list[str]:
    return [
        str(x.get("intent") or "").upper().strip()
        for x in comandos_plano(plano)
        if str(x.get("intent") or "").strip()
    ]


def comando_intent(
    plano: dict[str, Any] | None,
    intent: str,
) -> dict[str, Any] | None:
    alvo = intent.upper()
    for comando in comandos_plano(plano):
        if str(comando.get("intent") or "").upper().strip() == alvo:
            return comando
    return None


def procurar_chave(obj: Any, chave: str) -> Any:
    if isinstance(obj, dict):
        if chave in obj:
            return obj[chave]
        for valor in obj.values():
            achado = procurar_chave(valor, chave)
            if achado is not None:
                return achado
    elif isinstance(obj, list):
        for valor in obj:
            achado = procurar_chave(valor, chave)
            if achado is not None:
                return achado
    return None


def repeticao_operacional(plano: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(plano, dict):
        return {}
    valor = plano.get("repeticao_operacional")
    if isinstance(valor, dict):
        return dict(valor)
    valor = procurar_chave(plano, "repeticao_operacional")
    return dict(valor) if isinstance(valor, dict) else {}


def params_de(obj: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(obj, dict):
        return {}
    params = obj.get("params")
    return dict(params) if isinstance(params, dict) else {}


def alvo_arquivo(obj: dict[str, Any] | None) -> str:
    if not isinstance(obj, dict):
        return ""
    params = params_de(obj)
    return str(
        params.get("caminho")
        or params.get("alvo")
        or obj.get("alvo")
        or ""
    ).strip()


def termina_com(caminho: str, nome: str) -> bool:
    normal = str(caminho or "").replace("\\", "/").casefold()
    return normal.endswith("/" + nome.casefold()) or Path(str(caminho or "")).name.casefold() == nome.casefold()


def valor_bool_profundo(obj: Any, chave: str) -> bool | None:
    valor = procurar_chave(obj, chave)
    return valor if isinstance(valor, bool) else None


def status_profundo(obj: Any) -> str:
    valor = procurar_chave(obj, "status")
    return str(valor or "").strip()


def physical_events(caminho: Path) -> list[dict[str, Any]]:
    return ler_jsonl(caminho)


def tem_evento(events: Iterable[dict[str, Any]], *tipos: str) -> bool:
    tipos_norm = {str(x) for x in tipos}
    return any(str(evento.get("tipo") or "") in tipos_norm for evento in events)


def adicionar_falha(
    resultado: ResultadoCenario,
    fronteira: str,
    texto: str,
) -> None:
    if resultado.estado != "RED":
        resultado.estado = "RED"
        resultado.fronteira = fronteira
    resultado.detalhes.append(texto)


def validar_precondicao(
    resultado: ResultadoCenario,
    planos: dict[int, dict[str, Any]],
    indice: int,
    esperado: str,
) -> dict[str, Any] | None:
    plano = planos.get(indice)
    cmd = comando_intent(plano, esperado)
    if cmd is None:
        adicionar_falha(
            resultado,
            "precondicao_rt1",
            f"turno {indice + 1}: esperado {esperado}; observado intents={intents(plano)}",
        )
    return cmd


def validar_repeticao_esperada(
    resultado: ResultadoCenario,
    plano: dict[str, Any] | None,
    *,
    intent_esperado: str,
    arquivo_esperado: str = "",
    urgentes: bool | None = None,
) -> None:
    rep = repeticao_operacional(plano)
    rep_intent = str(rep.get("intent") or "").upper().strip()

    if rep_intent != intent_esperado:
        adicionar_falha(
            resultado,
            "planejamento/repeticao_operacional",
            f"repeticao_operacional={rep!r}; esperado intent={intent_esperado}",
        )
        return

    if arquivo_esperado:
        alvo = alvo_arquivo(rep)
        if not termina_com(alvo, arquivo_esperado):
            adicionar_falha(
                resultado,
                "fidelidade_parametros_planejamento",
                f"repetição aponta para {alvo!r}; esperado {arquivo_esperado}",
            )
            return

    if urgentes is not None:
        observado = params_de(rep).get("urgentes")
        if bool(observado) is not bool(urgentes):
            adicionar_falha(
                resultado,
                "fidelidade_parametros_planejamento",
                f"urgentes no recibo/repetição={observado!r}; esperado {urgentes}",
            )
            return

    cmd = comando_intent(plano, intent_esperado)
    if cmd is None:
        adicionar_falha(
            resultado,
            "ciclo/roteamento",
            f"planejamento correto, mas comandos finais={intents(plano)}",
        )
        return

    if arquivo_esperado:
        alvo = alvo_arquivo(cmd)
        if not termina_com(alvo, arquivo_esperado):
            adicionar_falha(
                resultado,
                "fidelidade_parametros_execucao",
                f"executor recebeu {alvo!r}; esperado {arquivo_esperado}",
            )
            return

    if urgentes is not None:
        observado = params_de(cmd).get("urgentes")
        if bool(observado) is not bool(urgentes):
            adicionar_falha(
                resultado,
                "fidelidade_parametros_execucao",
                f"urgentes na execução={observado!r}; esperado {urgentes}",
            )


def validar_cenario(
    cenario: Cenario,
    *,
    planos: dict[int, dict[str, Any]],
    cenario_dir: Path,
    physical: list[dict[str, Any]],
    resultado: ResultadoCenario,
) -> None:
    if resultado.returncode not in (0, None):
        resultado.estado = "INFRA"
        resultado.fronteira = "processo_runtime"
        resultado.detalhes.append(f"laylay.py encerrou com código {resultado.returncode}")
        return

    trace = ler_jsonl(cenario_dir / "trace_receipts.jsonl")
    if not trace:
        resultado.estado = "INFRA"
        resultado.fronteira = "captura_rota"
        resultado.detalhes.append("trace_receipts.jsonl vazio ou ausente")
        return

    if len(planos) < len(cenario.comandos):
        resultado.estado = "INFRA"
        resultado.fronteira = "captura_roteiro"
        resultado.detalhes.append(
            f"planos capturados={sorted(planos)}; esperados={list(range(len(cenario.comandos)))}"
        )
        return

    def eh_leia(ev: dict[str, Any]) -> bool:
        return "leia de novo" in str(ev.get("texto") or "").casefold()

    repeticoes = [
        x for x in trace
        if str(x.get("tipo") or "") == "rota_return"
        and str(x.get("arquivo") or "") == "compatibilidade_contexto.py"
        and str(x.get("funcao") or "") == "resolver_repeticao_ultima_acao"
        and eh_leia(x)
    ]
    if not repeticoes:
        resultado.estado = "INFRA"
        resultado.fronteira = "captura_repeticao_tipada"
        resultado.detalhes.append(
            "não capturei resolver_repeticao_ultima_acao('Leia de novo')"
        )
        return

    primeira_rep = repeticoes[0]
    classificacao = dict(primeira_rep.get("classificacao") or {})
    if (
        str(classificacao.get("tipo") or "") != "tipada"
        or str(classificacao.get("acao_semantica") or "").upper() != "LER"
    ):
        resultado.estado = "RED"
        resultado.fronteira = "classificacao_repeticao_tipificada"
        resultado.detalhes.append(
            f"'Leia de novo' chegou ao resolvedor com classificação {classificacao!r}"
        )
        return

    if bool(primeira_rep.get("retorno_contem_iot")):
        resultado.estado = "RED"
        resultado.fronteira = "seletor_repeticao_tipificada"
        resultado.detalhes.append(
            "o próprio resolvedor tipado LER devolveu IOT_CONTROL"
        )
        return

    retorno_rep = primeira_rep.get("retorno")
    if retorno_rep not in (None, {}, []):
        resultado.estado = "RED"
        resultado.fronteira = "seletor_repeticao_tipificada"
        resultado.detalhes.append(
            f"sem FILE_READ/EMAIL_READ disponível, o resolvedor deveria falhar fechado; retornou {retorno_rep!r}"
        )
        return

    t0 = float(primeira_rep.get("ts") or 0.0)

    # Depois do fail-closed da repetição, procura a PRIMEIRA função local que
    # devolveu um objeto contendo IOT_CONTROL. Propagadores externos ao recorte
    # são deixados para depois; a ordem de timestamps manda.
    retornos_iot = [
        x for x in trace
        if str(x.get("tipo") or "") == "rota_return"
        and float(x.get("ts") or 0.0) >= t0
        and bool(x.get("retorno_contem_iot"))
    ]
    retornos_iot.sort(key=lambda x: float(x.get("ts") or 0.0))

    # Calls do executor funcionam como sink: se IOT só aparece aqui, sabemos
    # que nasceu antes, mas não fingimos saber em qual função.
    calls_executor_iot = [
        x for x in trace
        if str(x.get("tipo") or "") == "rota_call"
        and float(x.get("ts") or 0.0) >= t0
        and bool(x.get("entrada_contem_iot"))
        and str(x.get("funcao") or "") == "executar_intencao"
    ]
    calls_executor_iot.sort(key=lambda x: float(x.get("ts") or 0.0))

    plano_t2 = planos.get(1, {})
    intents_t2 = [str(x).upper() for x in intents(plano_t2)]
    materializou_iot = "IOT_CONTROL" in intents_t2

    if retornos_iot:
        primeiro = retornos_iot[0]
        arquivo = str(primeiro.get("arquivo") or "")
        funcao = str(primeiro.get("funcao") or "")
        mapa = {
            ("orquestrador_deterministico.py", "detectar_intencao_deterministica_mente"):
                "detector_deterministico",
            ("orquestrador_deterministico.py", "detectar"):
                "detector_deterministico_runtime",
            ("contexto_imediato.py", "resolver_iot"):
                "contexto_iot",
            ("contexto_imediato.py", "resolver"):
                "contexto_imediato_agregador",
            ("contexto_imediato.py", "resolver_acao_geral"):
                "contexto_acao_geral",
            ("contexto_imediato.py", "resolver_comando_contextual"):
                "contexto_agregador_puro",
            ("contexto_imediato.py", "resolver_comando_acao_geral_contextual"):
                "contexto_acao_geral_puro",
            ("arbitro_turno.py", "arbitrar_turno"):
                "arbitro_turno",
            ("coordenador_intencao.py", "resolver_intencao"):
                "coordenador_intencao",
            ("coordenador_intencao.py", "_resolver_decisao_canonica"):
                "coordenador_decisao_canonica",
            ("coordenador_intencao.py", "resolver_comando_natural"):
                "coordenador_comando_natural",
        }
        fronteira = mapa.get((arquivo, funcao))
        if not fronteira and "/iot/" in str(primeiro.get("caminho_tail") or "").casefold():
            fronteira = "detector_iot_real"
        if not fronteira:
            fronteira = f"retorno_iot:{arquivo}:{funcao}"

        resultado.estado = "RED"
        resultado.fronteira = fronteira
        resultado.detalhes.append(
            "repetição tipada LER falhou fechado corretamente; "
            f"a primeira função observada a devolver IOT_CONTROL depois disso foi {arquivo}:{funcao}"
        )
        resultado.detalhes.append(
            f"retorno inicial incompatível={primeiro.get('retorno')!r}"
        )
        return

    if calls_executor_iot:
        primeiro = calls_executor_iot[0]
        resultado.estado = "RED"
        resultado.fronteira = "origem_iot_antes_executor_nao_capturada"
        resultado.detalhes.append(
            "IOT_CONTROL chegou ao executor depois do fail-closed LER, "
            "mas nenhum resolvedor instrumentado o devolveu antes; ampliar observabilidade, não patchar."
        )
        resultado.detalhes.append(
            f"entrada do executor={primeiro.get('entrada')!r}"
        )
        return

    if materializou_iot:
        resultado.estado = "INFRA"
        resultado.fronteira = "materializacao_iot_sem_trace"
        resultado.detalhes.append(
            "o plano final contém IOT_CONTROL, mas o trace não capturou nem sua origem nem a entrada do executor"
        )
        return

    resultado.estado = "PASS"
    resultado.detalhes.append(
        "'Leia de novo' foi classificado como LER, o seletor falhou fechado "
        "e nenhum IOT_CONTROL reapareceu até o fim do turno."
    )

def executar_cenario(
    cenario: Cenario,
    *,
    snapshot: Path,
    hook: Path,
) -> ResultadoCenario:
    print()
    print("=" * 78)
    print(f"RT1-{cenario.codigo} — {cenario.descricao}")
    print("=" * 78)

    limpar_estado_snapshot(snapshot)

    cenario_dir = SAIDA / f"cenario_{cenario.codigo.lower()}"
    cenario_dir.mkdir(parents=True, exist_ok=True)
    home = criar_home(cenario_dir)
    roteiro = escrever_roteiro(cenario_dir, cenario)
    resultado_raiz = cenario_dir / "runtime_results"
    resultado_raiz.mkdir(parents=True, exist_ok=True)
    terminal_log = cenario_dir / "subprocess_terminal.log"
    physical_log = cenario_dir / "physical.jsonl"

    env = ambiente_cenario(
        home=home,
        hook=hook,
        snapshot=snapshot,
        cenario_dir=cenario_dir,
        gmail_fake=cenario.gmail_fake,
    )

    cmd = [
        str(PYTHON),
        str(snapshot / ARQUIVO_LAYLAY),
        "--roteiro",
        str(roteiro),
        "--resultado-raiz",
        str(resultado_raiz),
    ]

    resultado = ResultadoCenario(
        codigo=cenario.codigo,
        descricao=cenario.descricao,
        terminal_log=str(terminal_log),
        physical_log=str(physical_log),
    )

    print("Entrada:", " ".join(cmd[:2]), "--roteiro", roteiro.name)
    print("HOME  :", home)
    print("IoT   : simulado")
    print("Gmail :", "IMAP fake na fronteira física" if cenario.gmail_fake else "desativado")

    try:
        with terminal_log.open("w", encoding="utf-8") as log:
            proc = subprocess.run(
                cmd,
                cwd=str(snapshot),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=TIMEOUT_CENARIO_S,
                check=False,
            )
        resultado.returncode = int(proc.returncode)
    except subprocess.TimeoutExpired:
        resultado.returncode = -999
        resultado.estado = "INFRA"
        resultado.fronteira = "timeout_runtime"
        resultado.detalhes.append(
            f"runtime excedeu timeout de segurança ({TIMEOUT_CENARIO_S}s)"
        )
    except Exception as exc:
        resultado.returncode = -998
        resultado.estado = "INFRA"
        resultado.fronteira = "subprocess"
        resultado.detalhes.append(f"{type(exc).__name__}: {exc}")

    runtime_dir = ultimo_resultado_runtime(resultado_raiz)
    if runtime_dir:
        resultado.resultado_runtime = str(runtime_dir)
    planos = planos_por_indice(runtime_dir)
    physical = physical_events(physical_log)
    receipt_trace = ler_jsonl(cenario_dir / "trace_receipts.jsonl")

    validar_cenario(
        cenario,
        planos=planos,
        cenario_dir=cenario_dir,
        physical=physical,
        resultado=resultado,
    )

    diagnostico = {
        "cenario": asdict(cenario),
        "resultado": asdict(resultado),
        "planos": planos,
        "physical_events": physical,
        "receipt_trace": receipt_trace,
    }
    (cenario_dir / "diagnostico_rt1e.json").write_text(
        json.dumps(diagnostico, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    simbolo = {"PASS": "✅", "RED": "🔴", "INFRA": "⚠️"}.get(
        resultado.estado, "?"
    )
    print(f"{simbolo} RT1-{cenario.codigo}: {resultado.estado}")
    if resultado.fronteira:
        print("   primeira fronteira:", resultado.fronteira)
    for detalhe in resultado.detalhes:
        print("   -", detalhe)

    for indice, _comando in enumerate(cenario.comandos):
        plano = planos.get(indice, {})
        rep = repeticao_operacional(plano)
        rep_txt = f"{rep.get('intent')} {params_de(rep)}" if rep else "-"
        print(
            f"   T{indice + 1}: intents={intents(plano)} "
            f"| repeticao_operacional={rep_txt}"
        )

    print("   Trace causal:", cenario_dir / "trace_receipts.jsonl")
    eventos_t2 = [
        x for x in receipt_trace
        if "leia de novo" in str(x.get("texto") or "").casefold()
        or (
            str(x.get("tipo") or "") in {"rota_call", "rota_return"}
            and (
                bool(x.get("entrada_contem_iot"))
                or bool(x.get("retorno_contem_iot"))
            )
        )
    ]
    for ev in eventos_t2:
        tipo = str(ev.get("tipo") or "")
        arquivo = str(ev.get("arquivo") or "")
        funcao = str(ev.get("funcao") or "")
        texto_ev = str(ev.get("texto") or "")
        if tipo == "rota_call":
            print(
                f"      CALL   {arquivo}:{funcao} "
                f"texto={texto_ev!r} entrada_intent={ev.get('entrada_intent') or '-'}"
            )
        else:
            extra = ""
            if arquivo == "compatibilidade_contexto.py" and funcao == "resolver_repeticao_ultima_acao":
                extra = f" classificacao={ev.get('classificacao')}"
            print(
                f"      RETURN {arquivo}:{funcao} "
                f"texto={texto_ev!r} intent={ev.get('retorno_intent') or '-'}"
                f" iot={bool(ev.get('retorno_contem_iot'))}{extra}"
            )

    return resultado


def gerar_conclusao(
    resultados: list[ResultadoCenario],
    proveniencia: dict[str, Any],
) -> dict[str, Any]:
    r = resultados[0] if resultados else ResultadoCenario("E", "sem resultado")
    return {
        "veredito": f"R1_RT1E_{r.estado}",
        "conclusao": (
            "RT1-E rastreou o escape após a repetição tipada sem aplicar patch."
            if r.estado in {"RED", "PASS"}
            else "RT1-E ficou inconclusivo por infraestrutura/observabilidade."
        ),
        "primeira_fronteira_red_ou_infra": r.fronteira,
        "resultados": [asdict(x) for x in resultados],
        "proveniencia": proveniencia,
    }


def main() -> int:
    print()
    print("R1-RT1-E — ESCAPE PROBE / RUNTIME REAL")
    print("=" * 78)
    print("Projeto :", PROJETO)
    print("Python  :", PYTHON)
    print("Saída   :", SAIDA)
    print()
    print("⚠️ Feche outra instância da Laylay antes do RT1 para evitar disputa")
    print("   por portas/recursos externos.")
    print()

    proveniencia = registrar_proveniencia()
    print("HEAD    :", proveniencia["git_head"])
    print("Branch  :", proveniencia["git_branch"] or "<detached/indisponível>")
    print("Dirty   :", "SIM" if proveniencia["git_status_short"] else "NÃO")
    if proveniencia["git_status_short"]:
        for item in proveniencia["git_status_short"]:
            print("         ", item)

    raiz_temp: Path | None = None
    resultados: list[ResultadoCenario] = []

    try:
        raiz_temp, snapshot = criar_snapshot()
        hook = escrever_hook(raiz_temp)

        (SAIDA / "snapshot.json").write_text(
            json.dumps(
                {
                    "snapshot": str(snapshot),
                    "memoria_original_copiada": False,
                    "credenciais_copiadas": False,
                    "git_copiado": False,
                    "nota": "Snapshot temporário removido ao final.",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        for cenario in CENARIOS:
            resultados.append(
                executar_cenario(
                    cenario,
                    snapshot=snapshot,
                    hook=hook,
                )
            )

    finally:
        if raiz_temp is not None:
            shutil.rmtree(raiz_temp, ignore_errors=True)

    relatorio = gerar_conclusao(resultados, proveniencia)
    relatorio_path = SAIDA / "rt1e_report.json"
    relatorio_path.write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print("=" * 78)
    print("CONCLUSÃO RT1-E")
    print("=" * 78)
    for r in resultados:
        simbolo = {"PASS": "✅", "RED": "🔴", "INFRA": "⚠️"}.get(r.estado, "?")
        linha = f"{simbolo} RT1-{r.codigo:<2} {r.estado:<5}"
        if r.fronteira:
            linha += f" | primeira fronteira: {r.fronteira}"
        print(linha)

    print()
    print("VEREDITO:", relatorio["veredito"])
    print(relatorio["conclusao"])
    if relatorio["primeira_fronteira_red_ou_infra"]:
        print(
            "Primeira fronteira que manda no diagnóstico:",
            relatorio["primeira_fronteira_red_ou_infra"],
        )
    print("Relatório:", relatorio_path)

    if relatorio["veredito"] == "R1_RT1E_PASS":
        print("✅ E não reproduziu escape incompatível neste runtime.")
        return 0
    if relatorio["veredito"] == "R1_RT1E_RED":
        print("🔎 RED causal localizado. Não faça patch antes de estudar/falsificar a fronteira indicada.")
        return 1

    print("⚠️ RT1-E inconclusivo: corrigir só infraestrutura/observabilidade do probe, não a R1.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
