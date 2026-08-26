"""Autonomia e execução básica de comandos da Laylay."""

from __future__ import annotations

import os
import re
import shutil
import unicodedata
import ctypes
from typing import Callable, Optional

import psutil

from mente_laylay.integracao.catalogo_steam import resolver_jogo_steam

try:
    import pygetwindow as gw
except Exception:  # pragma: no cover
    gw = None

try:
    import pyautogui
except Exception:  # pragma: no cover
    pyautogui = None

try:
    from AppOpener import open as open_app
    from AppOpener import close as close_app
    APP_OPENER_AVAILABLE = True
except Exception:
    open_app = None
    close_app = None
    APP_OPENER_AVAILABLE = False


def normalizar_nome_app(nome_solicitado: str) -> str:
    if not nome_solicitado:
        return ""
    nome = str(nome_solicitado).strip().strip('"\'')
    nome = os.path.splitext(nome)[0]
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join([c for c in nome if not unicodedata.combining(c)])
    nome = nome.lower().replace(".exe", "")
    nome = re.sub(r"\s+", " ", nome).strip()
    # "abre o Opera de novo" ainda se refere ao Opera. O modificador é uma
    # instrução de repetição/foco, nunca parte do nome do aplicativo. Removê-lo
    # aqui mantém todos os abridores e fechadores alinhados, sem uma regra
    # paralela em cada roteador.
    nome = re.sub(
        r"(?:\s+(?:de novo|novamente|outra vez|mais uma vez))+$",
        "",
        nome,
    ).strip()
    return nome


def _parece_uri(alvo: str) -> bool:
    texto = str(alvo or "").strip()
    if re.match(r"^[a-zA-Z]:[\\/]", texto):
        return False
    return bool(re.match(r"^[a-z][a-z0-9+.-]*:", texto, flags=re.IGNORECASE))


def abrir_uri_sistema(uri: str) -> bool:
    """Entrega um protocolo ao Shell do Windows sem trata-lo como aplicativo."""
    alvo = str(uri or "").strip()
    if not _parece_uri(alvo):
        return False
    try:
        codigo = ctypes.windll.shell32.ShellExecuteW(None, "open", alvo, None, None, 1)
        return int(codigo) > 32
    except Exception as erro_shell:
        print(f"⚠️ [URI] ShellExecute falhou para {alvo}: {erro_shell}")
    try:
        os.startfile(alvo)
        return True
    except Exception as erro_startfile:
        print(f"❌ [URI] O Windows recusou {alvo}: {erro_startfile}")
        return False


def buscar_executavel(nome_solicitado: str, roots=None) -> Optional[str]:
    """Procura um executável em diretórios comuns do Windows e em pastas de programas."""
    if not nome_solicitado:
        return None

    alvo = str(nome_solicitado).strip()
    alvo_limpo = normalizar_nome_app(alvo)
    if not alvo_limpo:
        return None

    candidatos = []
    for base in [alvo_limpo, alvo_limpo.replace(" ", ""), alvo_limpo.replace(" ", "-"), alvo_limpo.replace("-", "")]:
        candidatos.append(base)
        candidatos.append(base + ".exe")
        candidatos.append(base + ".lnk")
    candidatos = list(dict.fromkeys([c for c in candidatos if c]))

    for nome_cand in candidatos:
        encontrado = shutil.which(nome_cand)
        if encontrado and os.path.isfile(encontrado):
            return encontrado

    dirs = []
    if roots:
        dirs.extend([str(r) for r in roots if str(r)])

    for env_name in ["ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA", "USERPROFILE"]:
        valor = os.environ.get(env_name)
        if valor:
            dirs.append(valor)

    if os.environ.get("USERPROFILE"):
        dirs.extend([
            os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Programs"),
            os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs"),
            os.path.join(os.environ["USERPROFILE"], "Desktop"),
        ])

    if os.environ.get("ProgramData"):
        dirs.append(os.path.join(os.environ["ProgramData"], "Microsoft", "Windows", "Start Menu", "Programs"))

    dirs.extend([
        r"C:\Program Files (x86)\Steam",
        r"C:\Program Files\Steam",
        r"C:\Program Files",
        r"C:\Program Files (x86)",
    ])

    dirs = list(dict.fromkeys([d for d in dirs if d]))

    for base_dir in dirs:
        if not os.path.isdir(base_dir):
            continue

        for root, _, files in os.walk(base_dir):
            for filename in files:
                nome_arq = os.path.splitext(filename)[0].lower()
                nome_arquivo = filename.lower()
                if not nome_arquivo.endswith((".exe", ".lnk", ".bat", ".cmd")):
                    continue
                if nome_arq == alvo_limpo or nome_arq.startswith(alvo_limpo + "") or alvo_limpo in nome_arq or nome_arq.replace(" ", "") == alvo_limpo.replace(" ", ""):
                    caminho = os.path.join(root, filename)
                    if os.path.isfile(caminho):
                        return caminho

    return None


def _falar(falar_cb: Optional[Callable[[str, str, int], None]], texto: str, emocao: str = "calma", nivel: int = 1) -> None:
    try:
        if callable(falar_cb):
            falar_cb(texto, emocao, nivel)
    except Exception:
        pass


def abrir_programa(nome_solicitado: str, falar_cb: Optional[Callable[[str, str, int], None]] = None) -> bool:
    """Abre programas de forma inteligente, priorizando caminhos conhecidos e executáveis reais."""
    if not nome_solicitado:
        return False

    alvo = str(nome_solicitado).strip()
    alvo_limpo = normalizar_nome_app(alvo)

    print(f"🚀 [OPEN_APP] Tentando abrir: '{alvo}' (limpo: {alvo_limpo})")

    _uri_map = {
        "microsoft store": "ms-windows-store:",
        "store": "ms-windows-store:",
        "ms store": "ms-windows-store:",
        "loja microsoft": "ms-windows-store:",
        "loja": "ms-windows-store:",
    }
    uri = _uri_map.get(alvo_limpo) or (alvo if _parece_uri(alvo) else "")
    if uri:
        print(f"🚀 [URI] Entregando ao Shell do Windows: {uri}")
        if abrir_uri_sistema(uri):
            print(f"✅ [URI] Protocolo aceito pelo sistema: {uri}")
            _falar(falar_cb, f"Abrindo {alvo}.", "calma", 1)
            return True
        raise Exception(f"O protocolo do Windows '{uri}' não respondeu.")

    # O nome comercial de um jogo quase nunca coincide com o executável.
    # Os manifestos locais da Steam são uma fonte rápida e confiável para
    # resolver qualquer biblioteca instalada, inclusive em outros discos.
    jogo_steam = resolver_jogo_steam(alvo)
    if jogo_steam:
        uri_steam = f"steam://rungameid/{jogo_steam['appid']}"
        print(
            f"🎮 [STEAM] Encontrado: {jogo_steam['nome']} "
            f"(appid={jogo_steam['appid']}, confiança={jogo_steam['confianca']})"
        )
        if abrir_uri_sistema(uri_steam):
            _falar(falar_cb, f"Abrindo {jogo_steam['nome']}.", "feliz", 1)
            return True
        raise Exception(f"A Steam encontrou '{jogo_steam['nome']}', mas recusou a abertura.")

    caminhos_customizados = {
        "xampp": r"C:\xampp\xampp-control.exe",
        "xampp control": r"C:\xampp\xampp-control.exe",
        "xampp-control": r"C:\xampp\xampp-control.exe",
        "obs": r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
        "obs studio": r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
        "obs64": r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
        "steam": r"C:\Program Files (x86)\Steam\steam.exe",
        "steam.exe": r"C:\Program Files (x86)\Steam\steam.exe",
    }

    if alvo_limpo in caminhos_customizados:
        caminho = caminhos_customizados[alvo_limpo]
        print(f"💻 [CUSTOM] Abrindo pelo caminho absoluto: {caminho}")
        try:
            os.startfile(caminho)
            _falar(falar_cb, f"Abrindo {alvo}.", "calma", 1)
            return True
        except Exception as e:
            print(f"❌ Erro ao abrir caminho customizado: {e}")

    if alvo.lower().endswith((".exe", ".lnk", ".bat", ".cmd")) or os.path.exists(alvo):
        try:
            print(f"💻 [PATH] Tentando executar diretamente: {alvo}")
            os.startfile(alvo)
            _falar(falar_cb, f"Executando {alvo}.", "calma", 1)
            return True
        except Exception as e:
            print(f"❌ Falha ao executar caminho direto: {e}")

    executavel = buscar_executavel(alvo)
    if executavel:
        print(f"💻 [EXEC] Executável encontrado: {executavel}")
        try:
            os.startfile(executavel)
            _falar(falar_cb, f"Abrindo {alvo}.", "calma", 1)
            return True
        except Exception as e:
            print(f"❌ Falha ao abrir executável encontrado: {e}")

    if APP_OPENER_AVAILABLE and open_app is not None:
        try:
            res = open_app(alvo_limpo, match_closest=False)
            if res is not None and res is not False:
                print(f"✅ AppOpener abriu: {alvo_limpo}")
                _falar(falar_cb, f"Abrindo {alvo}.", "calma", 1)
                return True
        except Exception as e:
            print(f"⚠️ AppOpener falhou: {e}")

    raise Exception(f"Não consegui encontrar nenhum programa instalado chamado '{alvo}'.")


# P0_AUTOPRESERVACAO_EXECUTOR_20260814
# Invariante: nenhum resolvedor, LLM ou contexto pode conceder ao executor
# autoridade para encerrar a própria Laylay ou o processo que sustenta sua
# sessão. A proteção fica no nível mais baixo, imediatamente antes do kill.
_PROCESSOS_PROTEGIDOS_FECHAMENTO = frozenset({
    "explorer",
    "svchost",
    "system",
    "registry",
    "winlogon",
    "csrss",
    "lsass",
    "services",
    "smss",
    "wininit",
    "dwm",
    "taskmgr",
    "python",
    "pythonw",
    "python3",
    "py",
    "cmd",
    "powershell",
    "pwsh",
    "conhost",
    "windowsterminal",
    "openconsole",
    "antigravity",
    "laylay",
})


_NOMES_CANONICOS_FECHAMENTO = {
    "steam": ("steam.exe",),
    "discord": ("discord.exe",),
    "spotify": ("spotify.exe",),
    "chrome": ("chrome.exe",),
    # launcher.exe é genérico demais para uma operação destrutiva.
    "opera": ("opera.exe",),
    "firefox": ("firefox.exe",),
    "edge": ("msedge.exe",),
    "brave": ("brave.exe",),
    "vscode": ("code.exe",),
    "vs code": ("code.exe",),
    "code": ("code.exe",),
    "minecraft": ("minecraft.exe", "javaw.exe"),
    "obs": ("obs64.exe",),
    "notepad": ("notepad.exe",),
    "paint": ("mspaint.exe",),
    "calculadora": ("calc.exe", "calculator.exe", "calculatorapp.exe"),
    "word": ("winword.exe",),
    "excel": ("excel.exe",),
    "powerpoint": ("powerpnt.exe",),
    "epic": ("epicgameslauncher.exe",),
    "bloco de notas": ("notepad.exe",),
    "msstore": ("winstore.app.exe",),
    "ms-store": ("winstore.app.exe",),
    "microsoft store": ("winstore.app.exe",),
}


def _normalizar_nome_processo_fechamento(nome: str) -> str:
    """Normaliza um executável para comparação de segurança."""
    bruto = os.path.basename(str(nome or "").strip()).casefold()
    if bruto.endswith(".exe"):
        bruto = bruto[:-4]
    return bruto.strip()


def _pids_autoprotegidos_fechamento() -> set[int]:
    """PID da Laylay + ancestrais que mantêm a sessão viva."""
    pids: set[int] = {int(os.getpid())}
    try:
        atual = psutil.Process(os.getpid())
        for ancestral in atual.parents():
            try:
                pids.add(int(ancestral.pid))
            except Exception:
                continue
    except Exception:
        pass
    return pids


def _processo_protegido_fechamento(
    proc,
    *,
    pids_autoprotegidos: set[int] | None = None,
) -> tuple[bool, str]:
    """Decide fail-closed se um processo pode sequer chegar ao kill."""
    protegidos = (
        set(pids_autoprotegidos)
        if pids_autoprotegidos is not None
        else _pids_autoprotegidos_fechamento()
    )

    try:
        pid = int(getattr(proc, "pid"))
    except Exception:
        return True, "pid_indeterminado"

    if pid in protegidos:
        return True, "processo_da_laylay_ou_ancestral"

    try:
        nome = str(proc.name() or "")
    except Exception:
        return True, "nome_indeterminado"

    nome_norm = _normalizar_nome_processo_fechamento(nome)
    if not nome_norm:
        return True, "nome_vazio"
    if nome_norm in _PROCESSOS_PROTEGIDOS_FECHAMENTO:
        return True, f"processo_protegido:{nome_norm}"

    return False, ""


def _processo_corresponde_fechamento(proc, nomes_permitidos: set[str]) -> bool:
    """Fechamento destrutivo exige executável exato, nunca aproximação."""
    try:
        nome = str(proc.name() or "").casefold().strip()
    except Exception:
        return False
    permitidos = {str(item or "").casefold().strip() for item in nomes_permitidos}
    return bool(nome and nome in permitidos)


def _encerrar_processo_validado(
    proc,
    *,
    alvo: str,
    origem: str,
    pids_autoprotegidos: set[int],
) -> bool:
    """Único ponto autorizado a chamar kill() neste fluxo."""
    protegido, motivo = _processo_protegido_fechamento(
        proc,
        pids_autoprotegidos=pids_autoprotegidos,
    )
    if protegido:
        try:
            pid = int(getattr(proc, "pid"))
        except Exception:
            pid = -1
        try:
            nome = str(proc.name() or "?")
        except Exception:
            nome = "?"
        print(
            "🛡️ [AUTOPRESERVAÇÃO] encerramento bloqueado | "
            f"alvo={alvo!r} processo={nome!r} pid={pid} motivo={motivo}"
        )
        return False

    try:
        proc.kill()
    except Exception as erro:
        print(
            "⚠️ [FECHAR_PROGRAMA] falha ao encerrar processo validado | "
            f"alvo={alvo!r} origem={origem} erro={erro}"
        )
        return False

    try:
        pid = int(getattr(proc, "pid"))
    except Exception:
        pid = -1
    try:
        nome = str(proc.name() or "?")
    except Exception:
        nome = "?"

    print(
        "✅ [FECHAR_PROGRAMA] processo exato encerrado | "
        f"alvo={alvo!r} processo={nome!r} pid={pid} origem={origem}"
    )
    return True


def fechar_programa(
    nome_solicitado: str,
    falar_cb: Optional[Callable[[str, str, int], None]] = None,
) -> bool:
    """Fecha um programa somente por identidade exata e com autopreservação."""
    alvo = str(nome_solicitado or "").strip()
    alvo_lower = normalizar_nome_app(alvo)
    if not alvo_lower:
        raise Exception("Nome de programa vazio.")

    print(f"🚀 [FECHAR_PROGRAMA] Solicitado: {alvo_lower}")

    if alvo_lower in _PROCESSOS_PROTEGIDOS_FECHAMENTO:
        print(f"🛡️ [AUTOPRESERVAÇÃO] alvo protegido recusado: {alvo!r}")
        raise Exception(f"Não posso fechar o processo protegido: {alvo}")

    if alvo_lower in {"google", "chrome", "google chrome"}:
        print("⚠️ [SEGURANÇA] Bloqueio de encerramento bruto do Chrome.")
        raise Exception(
            "Use close_tab para fechar abas, não tente matar o Chrome inteiro "
            "por segurança."
        )

    canonicos = _NOMES_CANONICOS_FECHAMENTO.get(alvo_lower)
    if canonicos:
        nomes_permitidos = {
            str(nome or "").casefold().strip()
            for nome in canonicos
            if str(nome or "").strip()
        }
    else:
        base = alvo_lower.casefold().strip()
        nomes_permitidos = {base}
        if not base.endswith(".exe"):
            nomes_permitidos.add(base + ".exe")

    if not nomes_permitidos:
        raise Exception(f"Não existe executável seguro mapeado para '{alvo}'.")

    pids_autoprotegidos = _pids_autoprotegidos_fechamento()
    fechou_algo = False
    pids_processados: set[int] = set()

    # Título é só descoberta. O executável ainda precisa bater exatamente.
    try:
        if gw is not None:
            import win32gui
            import win32process

            def _avaliar_janela(hwnd, _):
                nonlocal fechou_algo
                if not win32gui.IsWindowVisible(hwnd):
                    return

                titulo = str(win32gui.GetWindowText(hwnd) or "").strip()
                if not titulo or alvo_lower not in titulo.casefold():
                    return

                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    pid = int(pid)
                except Exception:
                    return
                if pid in pids_processados:
                    return

                try:
                    proc = psutil.Process(pid)
                except Exception:
                    return

                if not _processo_corresponde_fechamento(proc, nomes_permitidos):
                    try:
                        nome_observado = str(proc.name() or "?")
                    except Exception:
                        nome_observado = "?"
                    print(
                        "🛡️ [AUTOPRESERVAÇÃO] título parecido ignorado | "
                        f"titulo={titulo!r} processo={nome_observado!r} pid={pid}"
                    )
                    return

                pids_processados.add(pid)
                if _encerrar_processo_validado(
                    proc,
                    alvo=alvo,
                    origem="janela_titulo_exato",
                    pids_autoprotegidos=pids_autoprotegidos,
                ):
                    fechou_algo = True

            win32gui.EnumWindows(_avaliar_janela, None)
    except Exception as erro_janela:
        print(f"[PC A] Erro ao inspecionar janelas: {erro_janela}")

    # Destruição não usa AppOpener.close(match_closest=...).
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            pid = int(proc.info.get("pid"))
        except Exception:
            try:
                pid = int(getattr(proc, "pid"))
            except Exception:
                continue

        if pid in pids_processados:
            continue

        try:
            nome_proc = str(proc.info.get("name") or proc.name() or "")
        except Exception:
            continue

        if nome_proc.casefold().strip() not in nomes_permitidos:
            continue

        pids_processados.add(pid)
        if _encerrar_processo_validado(
            proc,
            alvo=alvo,
            origem="processo_exato",
            pids_autoprotegidos=pids_autoprotegidos,
        ):
            fechou_algo = True

    if not fechou_algo:
        print(f"⚠️ Nenhum processo seguro e exato encontrado para fechar: {alvo!r}")
        raise Exception(
            f"Não há nenhum programa aberto e seguro com o nome '{nome_solicitado}'."
        )

    _falar(falar_cb, f"Pronto, {alvo} foi fechado.", "debochada", 2)
    return True
