"""Percepcao e manipulacao basica de janelas do sistema."""

from __future__ import annotations

import re
import time
import unicodedata
import urllib.parse
from typing import Any, Callable, Iterable, List, Tuple


MAPA_NOMES_JANELA = {
    "opera": "opera",
    "opera gx": "opera",
    "operagx": "opera",
    "opede": "opera",
    "opeditor": "opera",
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "edge",
    "microsoft edge": "edge",
    "whatsapp.root": "whatsapp",
    "whatsapp": "whatsapp",
    "vscode": "visual studio code",
    "vs code": "visual studio code",
    "code": "visual studio code",
    "visual studio code": "visual studio code",
    "steam": "steam",
    "steamservice": "steam",
    "steamwebhelper": "steam",
}

PROCESSOS_POR_APP = {
    "steam": ["steam.exe", "steamwebhelper.exe"],
    "opera": ["opera.exe"],
    "chrome": ["chrome.exe"],
    "edge": ["msedge.exe"],
    "visual studio code": ["code.exe"],
    "spotify": ["spotify.exe"],
    "discord": ["discord.exe"],
}

TITULOS_AUXILIARES_JANELA = {
    "default ime",
    "msctfime ui",
    "program manager",
    "dwm",
}


def normalizar_alvo_ambiente(nome: str) -> str:
    bruto = str(nome or "").strip().lower()
    bruto = unicodedata.normalize("NFKD", bruto)
    bruto = "".join(c for c in bruto if not unicodedata.combining(c))
    bruto = bruto.replace(".exe", "")
    bruto = re.sub(r"[^\w\s\.-]", " ", bruto)
    bruto = re.sub(r"\s+", " ", bruto).strip()
    return MAPA_NOMES_JANELA.get(bruto, bruto)


def _titulo_janela(janela: Any) -> str:
    try:
        return str(getattr(janela, "title", "") or "").strip()
    except Exception:
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


def _pids_por_nome_app(psutil_mod: Any, nome_app: str) -> set[int]:
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
    except Exception:
        pass
    return {pid for pid in pids if pid > 0}


def _buscar_hwnd_por_processo(psutil_mod: Any, nome_app: str) -> tuple[int, str, int]:
    pids = _pids_por_nome_app(psutil_mod, nome_app)
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


def _focar_hwnd_por_processo(psutil_mod: Any, pyautogui_mod: Any, nome_app: str) -> bool:
    hwnd, titulo, pid_alvo = _buscar_hwnd_por_processo(psutil_mod, nome_app)
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
        except Exception:
            pass
        if pyautogui_mod is not None:
            pyautogui_mod.press("alt")
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            try:
                win32gui.BringWindowToTop(hwnd)
                win32gui.SetActiveWindow(hwnd)
            except Exception:
                pass
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
        except Exception:
            pass
        print(f"✅ Janela em foco por processo: '{titulo}'")
        return True
    except Exception as e:
        print(f"❌ Erro ao focar por processo: {e}")
        return False


def focar_janela(gw_mod: Any, pyautogui_mod: Any, nome_app: str, psutil_mod: Any = None) -> bool:
    janela, termo_busca = buscar_janela(gw_mod, nome_app)
    if not janela:
        if _focar_hwnd_por_processo(psutil_mod, pyautogui_mod, nome_app):
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
        print(f"❌ Erro ao focar a janela: {e}")
        return False


def maximizar_janela(gw_mod: Any, pyautogui_mod: Any, nome_app: str, psutil_mod: Any = None) -> bool:
    print(f"📺 [MAXIMIZAR JANELA] Tentando deixar '{nome_app}' em destaque normal...")
    janela, termo_busca = buscar_janela(gw_mod, nome_app)
    if not janela:
        if _focar_hwnd_por_processo(psutil_mod, pyautogui_mod, nome_app):
            try:
                if pyautogui_mod is not None:
                    pyautogui_mod.hotkey("win", "up")
            except Exception:
                pass
            return True
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
        print(f"✅ Janela maximizada: '{_titulo_janela(janela)}'")
        return True
    except Exception as e:
        print(f"❌ Erro ao manipular a janela: {e}")
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


def listar_programas_abertos(gw_mod: Any, psutil_mod: Any) -> List[str]:
    nomes_ignorar = {
        "",
        "program manager",
        "default ime",
        "msctfmonitor task window",
        "nvidia graphics card",
        "realtek",
        "settingsynchost",
        "applicationframehost",
    }
    encontrados = set()
    try:
        for janela in gw_mod.getAllWindows():
            titulo = _titulo_janela(janela)
            if not titulo:
                continue
            if titulo.lower() in nomes_ignorar:
                continue
            if len(titulo) < 2:
                continue
            if not any(c.isalpha() for c in titulo):
                continue
            encontrados.add(titulo)
    except Exception as e:
        print(f"⚠️ [VERIFICAR_PROGRAMAS] Erro com pygetwindow: {e}")

    apps_relevantes = [
        "spotify",
        "discord",
        "steam",
        "whatsapp",
        "telegram",
        "obs",
        "slack",
        "zoom",
        "teams",
        "minecraft",
        "valorant",
        "figma",
    ]
    try:
        for proc in psutil_mod.process_iter(["name"]):
            try:
                nome = str(proc.info["name"] or "").lower()
                for app in apps_relevantes:
                    if app in nome:
                        encontrados.add(nome.replace(".exe", "").capitalize())
                        break
            except (psutil_mod.NoSuchProcess, psutil_mod.AccessDenied):
                continue
    except Exception as e:
        print(f"⚠️ [VERIFICAR_PROGRAMAS] Erro com psutil: {e}")

    resultado = sorted(encontrados)
    print(f"📋 [VERIFICAR_PROGRAMAS] Janelas encontradas: {resultado}")
    return resultado


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

    programa_aberto = False
    for item in programas or []:
        nome_prog = normalizar_alvo_ambiente(str(item or ""))
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
    app_esq: str,
    app_dir: str,
    abrir_app_cb: Callable[[str], Any] | None = None,
) -> bool:
    print(f"🪟 [ORGANIZE] Inteligência ativada para dividir: '{app_esq}' e '{app_dir}'...")
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
        return False

    print(f"📐 Área Útil detectada: {tela_largura}x{tela_altura} (Sem barra de tarefas!)")

    janela_esq, nome_esq = buscar_janela(gw_mod, app_esq)
    janela_dir, nome_dir = buscar_janela(gw_mod, app_dir)

    if not janela_esq and nome_esq and callable(abrir_app_cb):
        print(f"⏳ '{nome_esq}' não estava aberto! Tentando abrir...")
        try:
            abrir_app_cb(nome_esq)
        except Exception:
            pass
        time.sleep(4)
        janela_esq, _ = buscar_janela(gw_mod, app_esq)

    if not janela_dir and nome_dir and callable(abrir_app_cb):
        print(f"⏳ '{nome_dir}' não estava aberto! Tentando abrir...")
        try:
            abrir_app_cb(nome_dir)
        except Exception:
            pass
        time.sleep(4)
        janela_dir, _ = buscar_janela(gw_mod, app_dir)

    if not janela_dir:
        print("⚠️ Segunda janela falhou. Caçando navegador (Opera/Chrome) para preencher o buraco...")
        janela_dir, nome_dir = buscar_janela(gw_mod, "opera")
        if not janela_dir:
            janela_dir, nome_dir = buscar_janela(gw_mod, "chrome")

    if not janela_esq:
        print("❌ Desisto, não achei nada para a ESQUERDA.")
    if not janela_dir:
        print("❌ Desisto, não achei nada para a DIREITA.")

    def moldar_janela(janela: Any, lado: str) -> bool:
        if not janela:
            return False
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
            print(f"✅ '{_titulo_janela(janela)[:30]}...' colada na {lado.upper()}!")
            return True
        except Exception as e:
            print(f"❌ Erro ao posicionar: {e}")
            return False

    ok_esq = moldar_janela(janela_esq, "esquerda")
    time.sleep(0.2)
    ok_dir = moldar_janela(janela_dir, "direita")
    if ok_esq or ok_dir:
        print("✅ Área de trabalho dividida com inteligência máxima!")
    return bool(ok_esq and ok_dir)
