# -*- coding: utf-8 -*-
"""
R1-RT1 — prova pelo runtime real da Laylay.

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


NOME = "R1-RT1"
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
        "A",
        "FILE_READ(A) -> IoT -> Leia de novo -> FILE_READ(A)",
        (
            "Cria um arquivo de texto chamado rt1_a.txt e dentro dele escreva ALFA_RT1_A.",
            "Leia o arquivo rt1_a.txt.",
            "Liga a lâmpada.",
            "Leia de novo.",
        ),
    ),
    Cenario(
        "B",
        "FILE_READ(A) -> CREATE_FILE(B) -> Leia de novo -> FILE_READ(A)",
        (
            "Cria um arquivo de texto chamado rt1_b_a.txt e dentro dele escreva ALFA_RT1_B_A.",
            "Leia o arquivo rt1_b_a.txt.",
            "Cria um arquivo de texto chamado rt1_b_b.txt e dentro dele escreva BETA_RT1_B_B.",
            "Leia de novo.",
        ),
    ),
    Cenario(
        "C",
        "EMAIL_READ(urgentes=True) -> IoT -> Leia de novo -> EMAIL_READ(urgentes=True)",
        (
            "Leia meus emails urgentes.",
            "Liga a lâmpada.",
            "Leia de novo.",
        ),
        gmail_fake=True,
    ),
    Cenario(
        "D",
        "EMAIL_READ -> IoT -> de novo -> IOT_CONTROL",
        (
            "Leia meus emails.",
            "Liga a lâmpada.",
            "de novo",
        ),
        gmail_fake=True,
    ),
    Cenario(
        "E",
        "IoT -> Leia de novo -> fail closed",
        (
            "Liga a lâmpada.",
            "Leia de novo.",
        ),
    ),
    Cenario(
        "F1",
        "DELETE_ITEM falho -> Leia de novo -> não repetir DELETE_ITEM",
        (
            "Apaga o arquivo rt1_inexistente.txt.",
            "Leia de novo.",
        ),
    ),
    Cenario(
        "F2",
        "DELETE_ITEM falho -> tenta de novo -> repetir DELETE_ITEM",
        (
            "Apaga o arquivo rt1_inexistente.txt.",
            "tenta de novo",
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
SAIDA = PROJETO / "resultados_rt1_r1" / f"r1_rt1-{STAMP}"
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
        # Timeout/subprocess são infraestrutura, nunca RED da R1.
        if resultado.estado != "INFRA":
            resultado.estado = "INFRA"
        if not resultado.fronteira:
            resultado.fronteira = "processo_runtime"
        resultado.detalhes.append(f"laylay.py encerrou com código {resultado.returncode}")
        return

    if len(planos) < len(cenario.comandos):
        resultado.estado = "INFRA"
        resultado.fronteira = "captura_roteiro"
        resultado.detalhes.append(
            f"planos capturados={sorted(planos)}; esperados={list(range(len(cenario.comandos)))}"
        )
        return

    resultado.estado = "PASS"
    downloads = cenario_dir / "home" / "Downloads"

    if cenario.codigo == "A":
        validar_precondicao(resultado, planos, 0, "CREATE_FILE")
        validar_precondicao(resultado, planos, 1, "FILE_READ")
        validar_precondicao(resultado, planos, 2, "IOT_CONTROL")
        validar_repeticao_esperada(
            resultado,
            planos[3],
            intent_esperado="FILE_READ",
            arquivo_esperado="rt1_a.txt",
        )
        alvo = downloads / "rt1_a.txt"
        if not alvo.is_file() or "ALFA_RT1_A" not in alvo.read_text(
            encoding="utf-8", errors="replace"
        ):
            adicionar_falha(
                resultado,
                "executor/filesystem",
                "arquivo A não existe ou conteúdo físico não foi confirmado na sandbox",
            )
        if not tem_evento(physical, "iot_consultar_estado", "iot_definir_estado"):
            adicionar_falha(
                resultado,
                "executor/iot",
                "nenhuma chamada ao ProtocoloSimulado foi observada",
            )

    elif cenario.codigo == "B":
        validar_precondicao(resultado, planos, 0, "CREATE_FILE")
        validar_precondicao(resultado, planos, 1, "FILE_READ")
        validar_precondicao(resultado, planos, 2, "CREATE_FILE")
        validar_repeticao_esperada(
            resultado,
            planos[3],
            intent_esperado="FILE_READ",
            arquivo_esperado="rt1_b_a.txt",
        )
        rep = repeticao_operacional(planos[3])
        if termina_com(alvo_arquivo(rep), "rt1_b_b.txt"):
            adicionar_falha(
                resultado,
                "fidelidade_seletor",
                "CREATE_FILE(B) sequestrou o alvo da repetição de leitura",
            )
        for nome, marcador in (
            ("rt1_b_a.txt", "ALFA_RT1_B_A"),
            ("rt1_b_b.txt", "BETA_RT1_B_B"),
        ):
            alvo = downloads / nome
            if not alvo.is_file() or marcador not in alvo.read_text(
                encoding="utf-8", errors="replace"
            ):
                adicionar_falha(
                    resultado,
                    "executor/filesystem",
                    f"{nome} não foi materializado corretamente",
                )

    elif cenario.codigo == "C":
        primeiro = validar_precondicao(resultado, planos, 0, "EMAIL_READ")
        validar_precondicao(resultado, planos, 1, "IOT_CONTROL")
        if primeiro is not None and params_de(primeiro).get("urgentes") is not True:
            adicionar_falha(
                resultado,
                "precondicao_rt1",
                f"EMAIL_READ inicial perdeu urgentes=True: {params_de(primeiro)!r}",
            )
        validar_repeticao_esperada(
            resultado,
            planos[2],
            intent_esperado="EMAIL_READ",
            urgentes=True,
        )
        if not tem_evento(physical, "imap_search", "imap_fetch"):
            adicionar_falha(
                resultado,
                "executor/gmail_transporte",
                "GmailMental não alcançou o transporte IMAP fake",
            )
        if not tem_evento(physical, "iot_consultar_estado", "iot_definir_estado"):
            adicionar_falha(
                resultado,
                "executor/iot",
                "IoT intermediário não alcançou o simulador",
            )

    elif cenario.codigo == "D":
        validar_precondicao(resultado, planos, 0, "EMAIL_READ")
        validar_precondicao(resultado, planos, 1, "IOT_CONTROL")
        validar_repeticao_esperada(
            resultado,
            planos[2],
            intent_esperado="IOT_CONTROL",
        )
        if not tem_evento(physical, "imap_search", "imap_fetch"):
            adicionar_falha(
                resultado,
                "executor/gmail_transporte",
                "EMAIL_READ inicial não alcançou o IMAP fake",
            )
        if not tem_evento(physical, "iot_consultar_estado", "iot_definir_estado"):
            adicionar_falha(
                resultado,
                "executor/iot",
                "IoT não alcançou o simulador",
            )

    elif cenario.codigo == "E":
        validar_precondicao(resultado, planos, 0, "IOT_CONTROL")
        plano = planos[1]
        rep = repeticao_operacional(plano)
        rep_intent = str(rep.get("intent") or "").upper().strip()
        if rep_intent:
            adicionar_falha(
                resultado,
                "planejamento/repeticao_operacional",
                f"fail-closed violado: repeticao_operacional={rep!r}",
            )
        incompat = sorted(set(intents(plano)) & MUTACOES_INCOMPATIVEIS_COM_LER)
        if incompat:
            adicionar_falha(
                resultado,
                "ciclo/roteamento",
                f"'Leia de novo' materializou intents incompatíveis: {incompat}",
            )
        if not tem_evento(physical, "iot_consultar_estado", "iot_definir_estado"):
            adicionar_falha(
                resultado,
                "precondicao_rt1",
                "IoT inicial não alcançou o simulador",
            )

    elif cenario.codigo == "F1":
        delete = validar_precondicao(resultado, planos, 0, "DELETE_ITEM")
        if delete is not None:
            executou = valor_bool_profundo(delete, "executou")
            confirmado = valor_bool_profundo(delete, "confirmado")
            status = status_profundo(delete)
            if executou is True and confirmado is True:
                adicionar_falha(
                    resultado,
                    "precondicao_rt1",
                    f"DELETE_ITEM deveria falhar, mas confirmou: status={status!r}",
                )
        plano = planos[1]
        rep = repeticao_operacional(plano)
        if str(rep.get("intent") or "").upper().strip() == "DELETE_ITEM":
            adicionar_falha(
                resultado,
                "planejamento/repeticao_operacional",
                f"repetição tipada caiu no DELETE_ITEM falho: {rep!r}",
            )
        if "DELETE_ITEM" in intents(plano):
            adicionar_falha(
                resultado,
                "ciclo/roteamento",
                "'Leia de novo' reexecutou DELETE_ITEM",
            )

    elif cenario.codigo == "F2":
        delete = validar_precondicao(resultado, planos, 0, "DELETE_ITEM")
        if delete is not None:
            executou = valor_bool_profundo(delete, "executou")
            confirmado = valor_bool_profundo(delete, "confirmado")
            status = status_profundo(delete)
            if executou is True and confirmado is True:
                adicionar_falha(
                    resultado,
                    "precondicao_rt1",
                    f"DELETE_ITEM deveria falhar, mas confirmou: status={status!r}",
                )
        validar_repeticao_esperada(
            resultado,
            planos[1],
            intent_esperado="DELETE_ITEM",
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
    }
    (cenario_dir / "diagnostico_rt1.json").write_text(
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

    return resultado


def gerar_conclusao(
    resultados: list[ResultadoCenario],
    proveniencia: dict[str, Any],
) -> dict[str, Any]:
    reds = [r for r in resultados if r.estado == "RED"]
    infra = [r for r in resultados if r.estado == "INFRA"]
    passes = [r for r in resultados if r.estado == "PASS"]

    if reds:
        veredito = "R1_RT1_RED"
        primeira = reds[0].fronteira
        conclusao = (
            "Há RED semântico/arquitetural no RT1. "
            "A primeira fronteira indicada deve comandar a próxima investigação."
        )
    elif infra:
        veredito = "R1_RT1_INCONCLUSIVO"
        primeira = infra[0].fronteira
        conclusao = (
            "Não há RED arquitetural provado, mas pelo menos um cenário ficou "
            "inconclusivo por infraestrutura/captura. Não fechar a R1 ainda."
        )
    else:
        veredito = "R1_RT1_GREEN"
        primeira = ""
        conclusao = (
            "Todos os cenários atravessaram o runtime de produção pela entrada "
            "canônica e respeitaram a semântica da repetição. A R1 sobreviveu ao RT1."
        )

    return {
        "veredito": veredito,
        "conclusao": conclusao,
        "primeira_fronteira_red_ou_infra": primeira,
        "pass": [r.codigo for r in passes],
        "red": [r.codigo for r in reds],
        "infra": [r.codigo for r in infra],
        "resultados": [asdict(r) for r in resultados],
        "proveniencia": proveniencia,
        "proximo_passo_se_green": (
            "chaos dirigido R1; depois reclassificação/chaos global"
            if veredito == "R1_RT1_GREEN"
            else ""
        ),
    }


def main() -> int:
    print()
    print("R1-RT1 V2 — RUNTIME REAL / REPETIÇÃO TIPADA")
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
    relatorio_path = SAIDA / "rt1_report.json"
    relatorio_path.write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print("=" * 78)
    print("CONCLUSÃO RT1")
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

    if relatorio["veredito"] == "R1_RT1_GREEN":
        print("✅ Próxima escada: chaos dirigido da R1.")
        return 0
    if relatorio["veredito"] == "R1_RT1_RED":
        print("🔴 Não faça patch ainda: primeiro estudar a primeira fronteira RED.")
        return 1

    print("⚠️ RT1 inconclusivo: corrigir só infraestrutura do teste, não a R1.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
