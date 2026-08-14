"""Percepcao e manipulacao basica de janelas do sistema."""

from __future__ import annotations

import re
import math
import threading
import time
import unicodedata
import urllib.parse
from typing import Any, Callable, Iterable, List, Tuple

from mente_laylay.percepcao.planejamento_janelas import (
    MAPA_NOMES_JANELA,
    TITULOS_AUXILIARES_JANELA,
    TITULOS_JANELA_LIXO,
    _relatar_falha_janela,
    _titulo_janela,
    limpar_historico_atividade_janelas,
    normalizar_alvo_ambiente,
    pid_from_hwnd,
    planejar_organizacao_janelas,
    priorizar_janelas_visiveis,
    registrar_atividade_janela_ativa,
    snapshot_atividade_janelas,
)


PROCESSOS_POR_APP = {
    "steam": ["steam.exe", "steamwebhelper.exe"],
    "opera": ["opera.exe"],
    "chrome": ["chrome.exe"],
    "edge": ["msedge.exe"],
    "visual studio code": ["code.exe"],
    "spotify": ["spotify.exe"],
    "discord": ["discord.exe"],
}

def classificar_assunto(exe: str, title: str) -> str:
    """Classifica a atividade atual em um assunto mental simples."""
    e = str(exe or "").lower()
    t = str(title or "").lower()
    if "code.exe" in e or "visual studio code" in t:
        return "Programação"
    if any(item in t for item in (
        "udemy", "coursera", "khan academy", "aula", "curso", "material de estudo",
        "google classroom", "moodle", "anki",
    )) or any(item in e for item in ("anki.exe",)):
        return "Estudo"
    if any(item in e for item in (
        "winword.exe", "excel.exe", "powerpnt.exe", "libreoffice",
    )) or any(item in t for item in (
        "microsoft word", "microsoft excel", "powerpoint", "google docs",
        "google sheets", "notion",
    )):
        return "Trabalho"
    if "minecraft" in e or "minecraft" in t:
        return "Gaming"
    if "ultimaker-cura" in e or "cura" in e or "cura" in t or "prusa" in e or "slicer" in t:
        return "Impressão 3D"
    if "spotify" in e or "spotify" in t:
        return "Música"
    return ""


def capturar_janela_ativa(
    gw_mod: Any,
    psutil_mod: Any,
    pid_from_hwnd_cb: Callable[[Any], int] | None = None,
    classificar_assunto_cb: Callable[[str, str], str] | None = None,
) -> dict[str, Any]:
    """Monta um retrato consistente da janela ativa e de seu processo."""
    janela = None
    try:
        janela = gw_mod.getActiveWindow() if gw_mod is not None else None
    except Exception:
        janela = None

    titulo = ""
    hwnd = None
    if janela is not None:
        try:
            titulo = str(getattr(janela, "title", "") or "").strip()
        except Exception:
            titulo = ""
        try:
            hwnd = (
                getattr(janela, "_hWnd", None)
                or getattr(janela, "hWnd", None)
                or getattr(janela, "handle", None)
            )
        except Exception:
            hwnd = None

    executavel = ""
    caminho_processo = ""
    memoria_processo_mb = 0.0
    linha_comando_processo = ""
    pid = 0
    if hwnd and callable(pid_from_hwnd_cb) and psutil_mod is not None:
        try:
            pid = int(pid_from_hwnd_cb(hwnd) or 0)
            if pid:
                processo = psutil_mod.Process(pid)
                executavel = str(processo.name() or "").strip()
                try:
                    caminho_processo = str(processo.exe() or "").strip()
                except Exception:
                    caminho_processo = ""
                try:
                    memoria_processo_mb = float(processo.memory_info().rss or 0) / (1024 * 1024)
                except Exception:
                    memoria_processo_mb = 0.0
                try:
                    linha_comando_processo = " ".join(map(str, processo.cmdline() or []))[:1200]
                except Exception:
                    linha_comando_processo = ""
        except Exception:
            executavel = ""

    classificador = classificar_assunto_cb if callable(classificar_assunto_cb) else classificar_assunto
    try:
        assunto = str(classificador(executavel, titulo) or "")
    except Exception:
        assunto = ""

    registrar_atividade_janela_ativa(
        hwnd=hwnd,
        titulo=titulo,
        pid=pid,
        executavel=executavel,
    )

    return {
        "win": janela,
        "title": titulo,
        "hwnd": hwnd,
        "pid": pid,
        "exe": executavel,
        "process_path": caminho_processo,
        "process_memory_mb": memoria_processo_mb,
        "process_cmdline": linha_comando_processo,
        "assunto": assunto,
    }


def janela_em_tela_cheia(pyautogui_mod: Any, janela: Any, proporcao: float = 0.95) -> bool:
    """Detecta se a janela ocupa praticamente a tela inteira."""
    try:
        if not janela or pyautogui_mod is None:
            return False
        sw, sh = pyautogui_mod.size()
        largura = int(getattr(janela, "width", 0) or 0)
        altura = int(getattr(janela, "height", 0) or 0)
        return bool(sw > 0 and sh > 0 and largura >= int(sw * proporcao) and altura >= int(sh * proporcao))
    except Exception:
        return False


def detectar_gatilho_proativo_sistema(exe: str, title: str, assunto: str, fullscreen: bool) -> tuple[str, dict | None]:
    """Decide qual sugestão proativa faz sentido para a janela ativa."""
    exe_l = str(exe or "").lower()
    title_l = str(title or "").lower()

    if "code.exe" in exe_l or "visual studio code" in title_l:
        return "SYS_MODE_CODE", {
            "action": "combo_python",
            "clean_tabs": True,
            "music_query": "lofi focus",
            "clean_empty_tabs": True,
        }

    if "steam.exe" in exe_l or (assunto == "Gaming" and not fullscreen):
        return "SYS_MODE_GAMER", {
            "action": "combo_gamer",
            "pause_music": True,
            "close_study_tabs": True,
        }

    if "explorer.exe" in exe_l and ("downloads" in title_l or "transfer" in title_l):
        return "SYS_ORGANIZE_DOWNLOADS", {
            "action": "combo_organize",
            "open_downloads": True,
        }

    return "", None


def fala_gatilho_proativo_sistema(trigger_key: str) -> str:
    """Fala curta da Laylay para cada sugestão de sistema."""
    if trigger_key == "SYS_MODE_CODE":
        return "Ativo o Modo Code? Limpo abas vazias e coloco música de foco."
    if trigger_key == "SYS_MODE_GAMER":
        return "Modo Gamer? Pauso a música e fecho abas de estudo."
    if trigger_key == "SYS_ORGANIZE_DOWNLOADS":
        return "Quer que eu organize teus downloads?"
    return ""


def _pontuacao_correspondencia_janela(termo_busca: str, titulo: str) -> int:
    titulo_bruto = str(titulo or "").strip()
    if not termo_busca or not titulo_bruto:
        return -1

    titulo_norm = normalizar_alvo_ambiente(titulo_bruto)
    titulo_lower = titulo_bruto.lower()
    score = -1

    if titulo_norm == termo_busca:
        score = 120
    elif titulo_lower == termo_busca:
        score = 110
    elif termo_busca in titulo_norm:
        score = 80
    elif termo_busca in titulo_lower:
        score = 70

    if score < 0:
        return score

    # Evita priorizar janelas auxiliares quando existe a principal.
    if any(x in titulo_norm for x in ("helper", "service", "webhelper")) and titulo_norm != termo_busca:
        score -= 25
    return score


def buscar_janela(gw_mod: Any, nome_app: str) -> Tuple[Any, str]:
    termo_busca = normalizar_alvo_ambiente(nome_app)
    if not termo_busca or gw_mod is None:
        return None, termo_busca
    try:
        janelas = gw_mod.getAllWindows()
    except Exception:
        return None, termo_busca

    melhor_janela = None
    melhor_score = -1
    for janela in janelas:
        titulo = _titulo_janela(janela)
        score = _pontuacao_correspondencia_janela(termo_busca, titulo)
        if score > melhor_score:
            melhor_janela = janela
            melhor_score = score

    if melhor_janela is not None and melhor_score >= 0:
        return melhor_janela, termo_busca

    try:
        candidatos = gw_mod.getWindowsWithTitle(termo_busca)
    except Exception:
        candidatos = []
    for janela in candidatos or []:
        if _titulo_janela(janela):
            return janela, termo_busca
    return None, termo_busca


def _pids_por_nome_app(
    psutil_mod: Any,
    nome_app: str,
    registrar_falha: Callable[..., Any] | None = None,
) -> set[int]:
    termo = normalizar_alvo_ambiente(nome_app)
    nomes_proc = PROCESSOS_POR_APP.get(termo, [f"{termo}.exe", termo])
    nomes_proc = {str(n or "").lower() for n in nomes_proc if str(n or "").strip()}
    pids: set[int] = set()
    if psutil_mod is None:
        return pids
    try:
        for proc in psutil_mod.process_iter(["name", "pid"]):
            try:
                nome = str(proc.info.get("name") or "").lower()
                if nome in nomes_proc or any(n and n.replace(".exe", "") == nome.replace(".exe", "") for n in nomes_proc):
                    pids.add(int(proc.info.get("pid") or 0))
            except Exception:
                continue
    except Exception as erro:
        _relatar_falha_janela(registrar_falha, "enumeracao_processos", erro)
    return {pid for pid in pids if pid > 0}


def _buscar_hwnd_por_processo(
    psutil_mod: Any,
    nome_app: str,
    registrar_falha: Callable[..., Any] | None = None,
) -> tuple[int, str, int]:
    pids = _pids_por_nome_app(psutil_mod, nome_app, registrar_falha)
    if not pids:
        print(f"🪟 [JANELA:PROCESSO] nenhum PID encontrado para '{nome_app}'")
        return 0, "", 0
    try:
        import win32gui
        import win32process
    except Exception:
        return 0, "", 0

    candidatos: list[tuple[int, str, int, int, str]] = []

    def _enum(hwnd, _):
        try:
            if not win32gui.IsWindow(hwnd):
                return
            if not win32gui.IsWindowVisible(hwnd):
                return
            titulo = str(win32gui.GetWindowText(hwnd) or "").strip()
            if not titulo:
                return
            titulo_norm = normalizar_alvo_ambiente(titulo)
            if titulo_norm in TITULOS_AUXILIARES_JANELA:
                return
            if any(x in titulo_norm for x in ("sem titulo", "untitled", "hidden", "helper", "service", "webhelper")):
                return
            try:
                if win32gui.GetWindow(hwnd, 4):  # GW_OWNER: evita popups/filhas auxiliares.
                    return
            except Exception:
                pass
            try:
                import win32con
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                if ex_style & win32con.WS_EX_TOOLWINDOW:
                    return
            except Exception:
                pass
            try:
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                largura = max(0, int(right) - int(left))
                altura = max(0, int(bottom) - int(top))
                if largura < 180 or altura < 120:
                    return
            except Exception:
                largura = 0
                altura = 0
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if int(pid or 0) in pids:
                try:
                    proc_nome = str(psutil_mod.Process(int(pid)).name() or "").lower()
                except Exception:
                    proc_nome = ""
                candidatos.append((int(hwnd), titulo, largura, altura, proc_nome))
        except Exception:
            return

    try:
        win32gui.EnumWindows(_enum, None)
    except Exception:
        return 0, "", 0

    if not candidatos:
        print(f"🪟 [JANELA:PROCESSO] nenhum HWND principal encontrado para '{nome_app}' nos PIDs {sorted(pids)}")
        return 0, "", 0
    alvo_norm = normalizar_alvo_ambiente(nome_app)

    def _score(item: tuple[int, str, int, int, str]) -> int:
        _, titulo, largura, altura, proc_nome = item
        score = _pontuacao_correspondencia_janela(alvo_norm, titulo)
        area = largura * altura
        if score < 0:
            score = 5
        if proc_nome:
            proc_base = proc_nome.replace(".exe", "")
            if proc_base == alvo_norm or proc_base in alvo_norm or alvo_norm in proc_base:
                score += 55
        if alvo_norm == "steam" and proc_nome == "steam.exe":
            score += 80
        if alvo_norm == "steam" and proc_nome == "steamwebhelper.exe":
            titulo_norm = normalizar_alvo_ambiente(titulo)
            if "steam" in titulo_norm:
                score += 65
            else:
                score -= 120
        if alvo_norm == "opera" and proc_nome == "opera.exe":
            score += 60
        if area >= 300_000:
            score += 25
        elif area >= 90_000:
            score += 10
        if any(x in normalizar_alvo_ambiente(titulo) for x in ("notificacao", "notification", "overlay")):
            score -= 80
        return score

    candidatos.sort(key=_score, reverse=True)
    escolhido = candidatos[0]
    print(
        "🪟 [JANELA:PROCESSO] escolhido "
        f"hwnd={escolhido[0]} proc={escolhido[4] or '?'} titulo='{escolhido[1]}' "
        f"tam={escolhido[2]}x{escolhido[3]} score={_score(escolhido)}"
    )
    try:
        _, pid_escolhido = win32process.GetWindowThreadProcessId(escolhido[0])
    except Exception:
        pid_escolhido = 0
    return escolhido[0], escolhido[1], int(pid_escolhido or 0)


def _focar_hwnd_por_processo(
    psutil_mod: Any,
    pyautogui_mod: Any,
    nome_app: str,
    registrar_falha: Callable[..., Any] | None = None,
) -> bool:
    hwnd, titulo, pid_alvo = _buscar_hwnd_por_processo(
        psutil_mod, nome_app, registrar_falha,
    )
    if not hwnd:
        return False
    try:
        import win32con
        import win32gui
        import win32process
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.15)
            else:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        except Exception as erro:
            _relatar_falha_janela(registrar_falha, "preparacao_foco", erro)
        if pyautogui_mod is not None:
            pyautogui_mod.press("alt")
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            try:
                win32gui.BringWindowToTop(hwnd)
                win32gui.SetActiveWindow(hwnd)
            except Exception as erro:
                _relatar_falha_janela(registrar_falha, "ativacao_foco", erro)
        time.sleep(0.25)
        try:
            hwnd_frente = int(win32gui.GetForegroundWindow() or 0)
            _, pid_frente = win32process.GetWindowThreadProcessId(hwnd_frente)
            titulo_frente = str(win32gui.GetWindowText(hwnd_frente) or "").strip()
            if hwnd_frente != int(hwnd) and int(pid_frente or 0) != int(pid_alvo or -1):
                print(
                    "⚠️ [JANELA:PROCESSO] foco nao confirmou alvo "
                    f"esperado='{titulo}' frente='{titulo_frente}'"
                )
                return False
        except Exception as erro:
            _relatar_falha_janela(registrar_falha, "confirmacao_foco", erro)
        print(f"✅ Janela em foco por processo: '{titulo}'")
        return True
    except Exception as e:
        print(f"❌ Erro ao focar por processo: {e}")
        _relatar_falha_janela(registrar_falha, "foco_por_processo", e)
        return False


def focar_janela(
    gw_mod: Any,
    pyautogui_mod: Any,
    nome_app: str,
    psutil_mod: Any = None,
    registrar_falha: Callable[..., Any] | None = None,
) -> bool:
    janela, termo_busca = buscar_janela(gw_mod, nome_app)
    if not janela:
        if _focar_hwnd_por_processo(
            psutil_mod, pyautogui_mod, nome_app, registrar_falha,
        ):
            return True
        print(f"⚠️ Nenhuma janela encontrada para foco: {termo_busca}")
        return False
    try:
        if getattr(janela, "isMinimized", False):
            janela.restore()
            time.sleep(0.15)
        if pyautogui_mod is not None:
            pyautogui_mod.press("alt")
        janela.activate()
        time.sleep(0.2)
        print(f"✅ Janela em foco: '{_titulo_janela(janela)}'")
        return True
    except Exception as e:
        # Algumas APIs do Windows levantam exceção com código 0 mesmo depois
        # de ativarem a janela. Confirme pelo estado/processo antes de falhar.
        if _focar_hwnd_por_processo(
            psutil_mod, pyautogui_mod, nome_app, registrar_falha,
        ):
            return True
        if "error code from windows: 0" in str(e).lower():
            time.sleep(0.15)
            janela_atual, _ = buscar_janela(gw_mod, nome_app)
            if janela_atual and not getattr(janela_atual, "isMinimized", False):
                print(f"✅ Janela ativada apesar do retorno neutro do Windows: '{_titulo_janela(janela_atual)}'")
                return True
        print(f"❌ Erro ao focar a janela: {e}")
        _relatar_falha_janela(registrar_falha, "foco_janela", e)
        return False


def maximizar_janela(
    gw_mod: Any,
    pyautogui_mod: Any,
    nome_app: str,
    psutil_mod: Any = None,
    registrar_falha: Callable[..., Any] | None = None,
) -> bool:
    print(f"📺 [MAXIMIZAR JANELA] Tentando deixar '{nome_app}' em destaque normal...")
    janela, termo_busca = buscar_janela(gw_mod, nome_app)
    if not janela:
        if _focar_hwnd_por_processo(
            psutil_mod, pyautogui_mod, nome_app, registrar_falha,
        ):
            try:
                if pyautogui_mod is not None:
                    pyautogui_mod.hotkey("win", "up")
            except Exception as erro:
                _relatar_falha_janela(registrar_falha, "maximizacao_atalho", erro)
            time.sleep(0.25)
            janela_confirmada, _ = buscar_janela(gw_mod, nome_app)
            return bool(
                janela_confirmada
                and (
                    getattr(janela_confirmada, "isMaximized", False)
                    or janela_em_tela_cheia(pyautogui_mod, janela_confirmada)
                )
            )
        print(f"⚠️ Nenhuma janela encontrada para o app: {termo_busca}")
        return False
    try:
        if getattr(janela, "isMinimized", False):
            janela.restore()
            time.sleep(0.2)
        if pyautogui_mod is not None:
            pyautogui_mod.press("alt")
        janela.activate()
        time.sleep(0.35)
        try:
            janela.maximize()
        except Exception:
            if pyautogui_mod is not None and not getattr(janela, "isMaximized", False):
                pyautogui_mod.hotkey("win", "up")
        time.sleep(0.25)
        janela_confirmada, _ = buscar_janela(gw_mod, nome_app)
        janela_confirmada = janela_confirmada or janela
        maximizou = bool(
            getattr(janela_confirmada, "isMaximized", False)
            or janela_em_tela_cheia(pyautogui_mod, janela_confirmada)
        )
        if maximizou:
            print(f"✅ Janela maximizada: '{_titulo_janela(janela_confirmada)}'")
        else:
            print(
                "⚠️ A janela recebeu o comando, mas a maximização não foi "
                f"confirmada: '{_titulo_janela(janela_confirmada)}'"
            )
        return maximizou
    except Exception as e:
        print(f"❌ Erro ao manipular a janela: {e}")
        _relatar_falha_janela(registrar_falha, "maximizacao_janela", e)
        return False


def janela_esta_em_foco(gw_mod: Any, nome_app: str) -> bool:
    try:
        if gw_mod is None:
            return False
        termo_busca = normalizar_alvo_ambiente(nome_app)
        ativa = gw_mod.getActiveWindow()
        titulo = _titulo_janela(ativa).lower()
        return bool(titulo and termo_busca and termo_busca in titulo)
    except Exception:
        return False


_TITULOS_NAO_APRESENTAVEIS = {
    "",
    "program manager",
    "default ime",
    "msctfmonitor task window",
    "nvidia graphics card",
    "nvidia geforce overlay",
    "realtek",
    "settingsynchost",
    "applicationframehost",
    "windows input experience",
    "task switching",
    "desktopwindowxamlsource",
}

_PROCESSOS_RELEVANTES_APRESENTAVEIS = {
    "spotify": "Spotify",
    "discord": "Discord",
    "steam": "Steam",
    "whatsapp": "WhatsApp",
    "telegram": "Telegram",
    "obs": "OBS",
    "slack": "Slack",
    "zoom": "Zoom",
    "teams": "Teams",
    "minecraft": "Minecraft",
    "valorant": "Valorant",
    "figma": "Figma",
}


def _titulo_apresentavel_como_janela(titulo: str) -> bool:
    """Aceita somente títulos que representam uma janela útil para a pessoa."""
    texto = re.sub(r"\s+", " ", str(titulo or "")).strip()
    normalizado = normalizar_alvo_ambiente(texto)
    lixo = {
        normalizar_alvo_ambiente(item)
        for item in (*TITULOS_JANELA_LIXO, *TITULOS_AUXILIARES_JANELA)
    }
    if (
        not texto
        or normalizado in _TITULOS_NAO_APRESENTAVEIS
        or normalizado in lixo
        or len(texto) < 2
        or not any(c.isalpha() for c in texto)
    ):
        return False
    return not any(
        marcador in normalizado
        for marcador in (
            "overlay", "ime ui", "task window", "input experience",
            "desktopwindowxamlsource",
        )
    )


def fechar_janela_por_titulo(
    gw_mod: Any,
    titulo_ou_arquivo: str,
    registrar_falha: Callable[..., Any] | None = None,
    pyautogui_mod: Any = None,
) -> bool:
    """Fecha o documento identificado sem encerrar seu aplicativo hospedeiro.

    Editores como VS Code mantêm vários documentos numa única janela. Neles,
    ``Window.close()`` encerraria o processo inteiro. Quando há uma porta de
    teclado, confirmamos o foco do documento e usamos ``Ctrl+W``; somente o
    fallback legado de aplicativos dedicados pode fechar a janela de topo.
    """

    alvo = str(titulo_ou_arquivo or "").strip()
    janela, termo = buscar_janela(gw_mod, alvo)
    if janela is None:
        print(f"⚠️ Nenhuma janela de arquivo encontrada para fechar: {termo}")
        return False
    try:
        titulo_janela = _titulo_janela(janela)
        titulo_normalizado = normalizar_alvo_ambiente(titulo_janela)
        hospedeiro_multidocumento = any(
            marcador in titulo_normalizado
            for marcador in (
                "visual studio code", "visual studio", "notepad++",
                "pycharm", "intellij idea", "sublime text", "cursor",
            )
        )
        if pyautogui_mod is not None:
            if getattr(janela, "isMinimized", False):
                restaurar = getattr(janela, "restore", None)
                if callable(restaurar):
                    restaurar()
                    time.sleep(0.12)
            ativar = getattr(janela, "activate", None)
            if not callable(ativar):
                return False
            ativar()
            time.sleep(0.15)

            ativa = None
            obter_ativa = getattr(gw_mod, "getActiveWindow", None)
            if callable(obter_ativa):
                try:
                    ativa = obter_ativa()
                except Exception:
                    ativa = None
            foco_confirmado = bool(
                ativa is janela
                or (
                    ativa is not None
                    and normalizar_alvo_ambiente(alvo)
                    in normalizar_alvo_ambiente(_titulo_janela(ativa))
                )
                or getattr(janela, "isActive", False)
            )
            if not foco_confirmado:
                print(
                    "⚠️ Não enviei Ctrl+W porque o foco do documento não foi "
                    f"confirmado: '{alvo}'"
                )
                return False
            hotkey = getattr(pyautogui_mod, "hotkey", None)
            if not callable(hotkey):
                return False
            hotkey("ctrl", "w")
            for espera_s in (0.08, 0.14, 0.22, 0.32):
                time.sleep(espera_s)
                janela_restante, _ = buscar_janela(gw_mod, alvo)
                if janela_restante is None:
                    print(f"✅ Documento fechado sem encerrar o aplicativo: '{alvo}'")
                    return True
            print(f"⚠️ O documento recebeu Ctrl+W, mas continuou aberto: '{alvo}'")
            return False

        # Sem uma porta de teclado não existe operação segura para fechar uma
        # aba interna de um editor. Falhar é melhor que derrubar o VS Code e o
        # próprio processo que está executando o roteiro de testes.
        if hospedeiro_multidocumento:
            print(
                "⚠️ Não fechei o aplicativo inteiro ao tentar fechar o documento: "
                f"'{alvo}'"
            )
            return False
        fechar = getattr(janela, "close", None)
        if not callable(fechar):
            return False
        fechar()
        for espera_s in (0.08, 0.14, 0.22, 0.32):
            time.sleep(espera_s)
            janela_restante, _ = buscar_janela(gw_mod, alvo)
            if janela_restante is None:
                print(f"✅ Janela de arquivo fechada: '{alvo}'")
                return True
        print(f"⚠️ A janela recebeu o fechamento, mas continuou aberta: '{alvo}'")
        return False
    except Exception as erro:
        _relatar_falha_janela(registrar_falha, "fechar_janela_titulo", erro)
        return False


def observar_programas_abertos(gw_mod: Any, psutil_mod: Any) -> dict[str, List[str]]:
    """Separa janelas apresentáveis de processos relevantes sem janela.

    Processo em execução não é sinônimo de aplicativo visível. O retrato
    estruturado conserva essa diferença para que nenhuma resposta diga que um
    serviço ou overlay está "aberto na tela".
    """
    janelas_visiveis: set[str] = set()
    filtrados: set[str] = set()
    try:
        for janela in gw_mod.getAllWindows():
            titulo = _titulo_janela(janela)
            if not _titulo_apresentavel_como_janela(titulo):
                if titulo:
                    filtrados.add(titulo)
                continue
            janelas_visiveis.add(titulo)
    except Exception as e:
        print(f"⚠️ [VERIFICAR_PROGRAMAS] Erro com pygetwindow: {e}")

    processos_relevantes: set[str] = set()
    titulos_normalizados = " ".join(
        normalizar_alvo_ambiente(titulo) for titulo in janelas_visiveis
    )
    try:
        for proc in psutil_mod.process_iter(["name"]):
            try:
                nome = str(proc.info["name"] or "").lower()
                for app, apresentacao in _PROCESSOS_RELEVANTES_APRESENTAVEIS.items():
                    if app in nome:
                        if app not in titulos_normalizados:
                            processos_relevantes.add(apresentacao)
                        break
            except (psutil_mod.NoSuchProcess, psutil_mod.AccessDenied):
                continue
    except Exception as e:
        print(f"⚠️ [VERIFICAR_PROGRAMAS] Erro com psutil: {e}")

    retrato = {
        "janelas_visiveis": sorted(janelas_visiveis),
        "processos_segundo_plano": sorted(processos_relevantes),
        "componentes_filtrados": sorted(filtrados),
    }
    print(
        "📋 [VERIFICAR_PROGRAMAS] "
        f"janelas={retrato['janelas_visiveis']} "
        f"segundo_plano={retrato['processos_segundo_plano']} "
        f"filtrados={len(retrato['componentes_filtrados'])}"
    )
    return retrato


def listar_programas_abertos(gw_mod: Any, psutil_mod: Any) -> List[str]:
    """Compatibilidade: devolve somente janelas reais e apresentáveis."""
    return observar_programas_abertos(gw_mod, psutil_mod)["janelas_visiveis"]


def resolver_alvo_ambiente(
    nome: str,
    programas: Iterable[str],
    abas: Iterable[dict],
    foco_cb: Callable[[str], bool] | None = None,
) -> dict:
    def _host_sem_www(url: str) -> str:
        try:
            bruto = str(url or "").strip()
            if not bruto:
                return ""
            host = urllib.parse.urlparse(bruto).netloc.strip().lower()
            if host.startswith("www."):
                host = host[4:]
            return normalizar_alvo_ambiente(host)
        except Exception:
            return ""

    def _aba_combina_alvo(alvo_ref: str, titulo_ref: str, url_ref: str) -> bool:
        titulo_norm = normalizar_alvo_ambiente(titulo_ref)
        url_norm = normalizar_alvo_ambiente(url_ref)
        host_norm = _host_sem_www(url_ref)
        pistas = [p for p in {titulo_norm, url_norm, host_norm} if p]
        for pista in pistas:
            if alvo_ref == pista or alvo_ref in pista or pista in alvo_ref:
                return True
        return False

    alvo = str(nome or "").strip()
    alvo_norm = normalizar_alvo_ambiente(alvo)
    if not alvo_norm:
        return {"programa_aberto": False, "programa_em_foco": False, "aba_aberta": False, "preferido": "desconhecido", "url": "", "titulo": ""}

    def _processo_auxiliar(nome_bruto: str) -> bool:
        candidato = str(nome_bruto or "").strip().lower().replace(".exe", "")
        candidato = unicodedata.normalize("NFKD", candidato)
        candidato = "".join(c for c in candidato if not unicodedata.combining(c))
        candidato = re.sub(r"[^\w\s\.-]", " ", candidato)
        candidato = re.sub(r"\s+", " ", candidato).strip()
        if not candidato or candidato == alvo_norm:
            return False
        marcadores = (
            "service", "servico", "webhelper", "helper", "updater", "update",
            "crashhandler", "crashpad", "reporter", "background", "broker",
        )
        return alvo_norm in candidato and any(marcador in candidato for marcador in marcadores)

    programa_aberto = False
    for item in programas or []:
        item_bruto = str(item or "")
        if _processo_auxiliar(item_bruto):
            continue
        nome_prog = normalizar_alvo_ambiente(item_bruto)
        if nome_prog and (alvo_norm == nome_prog or alvo_norm in nome_prog or nome_prog in alvo_norm):
            programa_aberto = True
            break

    aba_aberta = False
    aba_url = ""
    aba_titulo = ""
    for aba in abas or []:
        if not isinstance(aba, dict):
            continue
        titulo = str(aba.get("titulo") or "").strip()
        url = str(aba.get("url") or "").strip()
        if _aba_combina_alvo(alvo_norm, titulo, url):
            aba_aberta = True
            aba_url = url
            aba_titulo = titulo
            break

    preferido = "desconhecido"
    if programa_aberto and not aba_aberta:
        preferido = "app"
    elif aba_aberta and not programa_aberto:
        preferido = "tab"
    elif programa_aberto and aba_aberta:
        preferido = "app"

    return {
        "programa_aberto": programa_aberto,
        "programa_em_foco": bool(programa_aberto and foco_cb and foco_cb(alvo)),
        "aba_aberta": aba_aberta,
        "preferido": preferido,
        "url": aba_url,
        "titulo": aba_titulo,
    }


def organizar_janelas(
    gw_mod: Any,
    pyautogui_mod: Any,
    ctypes_mod: Any,
    wintypes_mod: Any,
    app_esq: str = "",
    app_dir: str = "",
    abrir_app_cb: Callable[[str], Any] | None = None,
    registrar_falha: Callable[..., Any] | None = None,
    psutil_mod: Any = None,
    processos_audio_ativos_cb: Callable[[], Iterable[str]] | None = None,
) -> dict:
    """Posiciona uma ou duas janelas e relê a geometria final.

    Sem alvos explícitos, seleciona duas janelas visíveis do ambiente atual.
    Com apenas um alvo, move somente ele e preserva o restante da tela.
    """
    app_esq = str(app_esq or "").strip()
    app_dir = str(app_dir or "").strip()
    print(f"🪟 [ORGANIZE] Organizando: esquerda='{app_esq}' direita='{app_dir}'...")
    try:
        rect = wintypes_mod.RECT()
        ctypes_mod.windll.user32.SystemParametersInfoW(48, 0, ctypes_mod.byref(rect), 0)
        x_inicial = rect.left
        y_inicial = rect.top
        tela_largura = rect.right - rect.left
        tela_altura = rect.bottom - rect.top
        metade_largura = tela_largura // 2
    except Exception as e:
        print(f"❌ Erro real ao calcular área útil: {e}")
        _relatar_falha_janela(registrar_falha, "area_util", e)
        return {
            "ok": False, "executou": False, "confirmado": False,
            "status": "falha_area_util", "nome_esquerda": app_esq,
            "nome_direita": app_dir,
        }

    print(f"📐 Área Útil detectada: {tela_largura}x{tela_altura} (Sem barra de tarefas!)")

    janela_esq, nome_esq = buscar_janela(gw_mod, app_esq) if app_esq else (None, "")
    janela_dir, nome_dir = buscar_janela(gw_mod, app_dir) if app_dir else (None, "")

    if not app_esq and not app_dir:
        planejamento = planejar_organizacao_janelas(
            gw_mod,
            ctypes_mod=ctypes_mod,
            wintypes_mod=wintypes_mod,
            psutil_mod=psutil_mod,
            processos_audio_ativos_cb=processos_audio_ativos_cb,
            registrar_falha=registrar_falha,
        )
        janela_esq = planejamento.get("_janela_esquerda")
        janela_dir = planejamento.get("_janela_direita")
        nome_esq = str(planejamento.get("nome_esquerda") or "")
        nome_dir = str(planejamento.get("nome_direita") or "")
        resumo_ranking = list(planejamento.get("prioridades") or [])
        app_esq, app_dir = nome_esq, nome_dir
    else:
        resumo_ranking = []

    if not janela_esq and nome_esq and callable(abrir_app_cb):
        print(f"⏳ '{nome_esq}' não estava aberto! Tentando abrir...")
        try:
            abrir_app_cb(nome_esq)
        except Exception as erro:
            _relatar_falha_janela(registrar_falha, "abertura_janela_esquerda", erro)
        time.sleep(4)
        janela_esq, _ = buscar_janela(gw_mod, app_esq)

    if not janela_dir and nome_dir and callable(abrir_app_cb):
        print(f"⏳ '{nome_dir}' não estava aberto! Tentando abrir...")
        try:
            abrir_app_cb(nome_dir)
        except Exception as erro:
            _relatar_falha_janela(registrar_falha, "abertura_janela_direita", erro)
        time.sleep(4)
        janela_dir, _ = buscar_janela(gw_mod, app_dir)

    if app_esq and not janela_esq:
        print("❌ Desisto, não achei nada para a ESQUERDA.")
    if app_dir and not janela_dir:
        print("❌ Desisto, não achei nada para a DIREITA.")

    def moldar_janela(janela: Any, lado: str) -> tuple[bool, bool]:
        if not janela:
            return False, False
        try:
            if getattr(janela, "isMinimized", False) or getattr(janela, "isMaximized", False):
                janela.restore()
                time.sleep(0.3)
            if pyautogui_mod is not None:
                pyautogui_mod.press("alt")
            janela.activate()
            time.sleep(0.2)
            if lado == "esquerda":
                print(f"   📍 Moldando '{_titulo_janela(janela)[:30]}...' para esquerda...")
                janela.moveTo(x_inicial, y_inicial)
                janela.resizeTo(metade_largura, tela_altura)
            elif lado == "direita":
                print(f"   📍 Moldando '{_titulo_janela(janela)[:30]}...' para direita...")
                janela.moveTo(x_inicial + metade_largura, y_inicial)
                janela.resizeTo(metade_largura, tela_altura)
            time.sleep(0.12)
            esperado_x = x_inicial if lado == "esquerda" else x_inicial + metade_largura
            valores = (
                getattr(janela, "left", None), getattr(janela, "top", None),
                getattr(janela, "width", None), getattr(janela, "height", None),
            )
            tem_geometria = all(isinstance(valor, (int, float)) for valor in valores)
            confirmado = bool(
                tem_geometria
                and abs(int(valores[0]) - esperado_x) <= 24
                and abs(int(valores[1]) - y_inicial) <= 24
                and abs(int(valores[2]) - metade_largura) <= 32
                and abs(int(valores[3]) - tela_altura) <= 32
            )
            sufixo = "confirmada" if confirmado else "enviada sem confirmação geométrica"
            print(f"✅ '{_titulo_janela(janela)[:30]}...' na {lado.upper()} ({sufixo}).")
            return True, confirmado
        except Exception as e:
            print(f"❌ Erro ao posicionar: {e}")
            _relatar_falha_janela(registrar_falha, f"posicionamento_{lado}", e)
            return False, False

    pediu_esq = bool(app_esq)
    pediu_dir = bool(app_dir)
    ok_esq, confirmou_esq = moldar_janela(janela_esq, "esquerda") if pediu_esq else (False, False)
    if pediu_esq and pediu_dir:
        time.sleep(0.2)
    ok_dir, confirmou_dir = moldar_janela(janela_dir, "direita") if pediu_dir else (False, False)

    solicitadas = int(pediu_esq) + int(pediu_dir)
    executadas = int(ok_esq) + int(ok_dir)
    confirmadas = int(confirmou_esq) + int(confirmou_dir)
    ok = solicitadas > 0 and executadas == solicitadas
    confirmado = solicitadas > 0 and confirmadas == solicitadas
    if confirmado:
        status = "layout_confirmado"
    elif executadas == 0:
        status = "janela_nao_encontrada"
    elif executadas < solicitadas:
        status = "layout_parcial"
    else:
        status = "organizacao_nao_confirmada"
    if executadas:
        print(f"✅ Organização concluída: {executadas}/{solicitadas} janela(s); status={status}.")
    return {
        "ok": ok,
        "executou": executadas > 0,
        "confirmado": confirmado,
        "status": status,
        "nome_esquerda": str(nome_esq or app_esq).strip(),
        "nome_direita": str(nome_dir or app_dir).strip(),
        "solicitadas": solicitadas,
        "executadas": executadas,
        "confirmadas": confirmadas,
        "prioridades": resumo_ranking,
    }
