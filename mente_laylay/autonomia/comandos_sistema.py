"""Autonomia e execução básica de comandos da Laylay."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
import unicodedata
from typing import Callable, Optional

import psutil

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
    return nome


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
    if alvo_limpo in _uri_map:
        uri = _uri_map[alvo_limpo]
        print(f"✅ [URI] Abrindo via URI do sistema: {uri}")
        try:
            subprocess.Popen(["cmd", "/c", "start", "", uri], shell=False)
            _falar(falar_cb, f"Abrindo {alvo}.", "calma", 1)
            return True
        except Exception as _e_uri:
            print(f"⚠️ URI falhou, tentando webbrowser: {_e_uri}")
            try:
                import webbrowser as _wb_uri
                _wb_uri.open(uri)
                _falar(falar_cb, f"Abrindo {alvo}.", "calma", 1)
                return True
            except Exception as _e_wb:
                print(f"❌ webbrowser também falhou: {_e_wb}")

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


def fechar_programa(nome_solicitado: str, falar_cb: Optional[Callable[[str, str, int], None]] = None) -> bool:
    """Fecha programa de forma segura."""
    alvo = str(nome_solicitado).strip()
    alvo_lower = alvo.lower().replace(".exe", "").strip()
    print(f"🚀 [FECHAR_PROGRAMA] Solicitado: {alvo_lower}")
    fechou_algo = False

    processos_protegidos = {
        "explorer", "svchost", "system", "winlogon", "csrss", "lsass",
        "services", "smss", "wininit", "dwm", "taskmgr", "python",
        "pythonw", "cmd", "powershell", "antigravity"
    }

    if alvo_lower in processos_protegidos:
        print(f"⚠️ [SEGURANÇA] '{alvo}' é um processo de sistema protegido. Operação cancelada.")
        raise Exception(f"Não posso fechar o processo protegido: {alvo}")

    if alvo_lower in ["google", "chrome", "google chrome"]:
        print("⚠️ [SEGURANÇA] Bloqueio de encerramento bruto do Chrome.")
        raise Exception("Use close_tab para fechar abas, não tente matar o Chrome inteiro por segurança.")

    nomes_canonicos: dict = {
        "steam": ["steam.exe"],
        "discord": ["discord.exe"],
        "spotify": ["spotify.exe"],
        "chrome": ["chrome.exe"],
        "opera": ["opera.exe", "launcher.exe"],
        "firefox": ["firefox.exe"],
        "edge": ["msedge.exe"],
        "brave": ["brave.exe"],
        "vscode": ["code.exe"],
        "vs code": ["code.exe"],
        "code": ["code.exe"],
        "minecraft": ["minecraft.exe", "javaw.exe"],
        "obs": ["obs64.exe"],
        "notepad": ["notepad.exe"],
        "paint": ["mspaint.exe"],
        "calculadora": ["calc.exe"],
        "word": ["winword.exe"],
        "excel": ["excel.exe"],
        "powerpoint": ["powerpnt.exe"],
        "epic": ["epicgameslauncher.exe"],
        "bloco de notas": ["notepad.exe"],
        "msstore": ["winstore.app.exe"],
        "ms-store": ["winstore.app.exe"],
        "microsoft store": ["winstore.app.exe"],
    }

    alvos_exatos = nomes_canonicos.get(alvo_lower)

    morto_pelo_titulo = False
    try:
        if gw is not None:
            import win32gui
            import win32process

            def _mata_janela(hwnd, _):
                nonlocal morto_pelo_titulo, fechou_algo
                if win32gui.IsWindowVisible(hwnd):
                    titulo = str(win32gui.GetWindowText(hwnd)).strip()
                    if titulo and alvo_lower in titulo.lower():
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        try:
                            proc = psutil.Process(pid)
                            if proc.name().lower() not in processos_protegidos:
                                proc.kill()
                                morto_pelo_titulo = True
                                fechou_algo = True
                                print(f"[PC A] Sniper de Janela matou: '{titulo}' via {proc.name()} (PID {pid})")
                        except Exception:
                            pass

            win32gui.EnumWindows(_mata_janela, None)
    except Exception as _ew:
        print(f"[PC A] Erro no Sniper de Janela: {_ew}")

    if not morto_pelo_titulo and APP_OPENER_AVAILABLE and close_app is not None:
        try:
            close_app(alvo, match_closest=True)
            fechou_algo = True
            print(f"✅ AppOpener fechou: {alvo}")
        except Exception as e_ao:
            print(f"ℹ️ AppOpener falhou ao fechar '{alvo}' ({e_ao}). Tentando via psutil...")

    for p in psutil.process_iter(["name", "pid"]):
        try:
            nome_proc = (p.info["name"] or "").lower()
            if alvos_exatos:
                if nome_proc in [a.lower() for a in alvos_exatos]:
                    p.kill()
                    fechou_algo = True
                    print(f"💀 Processo exato encerrado: {p.info['name']} (PID {p.info['pid']})")
            else:
                alvo_exe = alvo_lower + ".exe"
                if nome_proc == alvo_exe or nome_proc == alvo_lower:
                    p.kill()
                    fechou_algo = True
                    print(f"💀 Processo encerrado: {p.info['name']} (PID {p.info['pid']})")
        except Exception:
            pass

    if not fechou_algo:
        print(f"⚠️ Nenhum processo encontrado ou possível de fechar para: '{alvo}'")
        raise Exception(f"Não há nenhum programa aberto ou acessível com o nome '{nome_solicitado}'.")

    _falar(falar_cb, f"Pronto, {alvo} foi fechado.", "debochada", 2)
    return fechou_algo


def extrair_comando_rapido(texto: str, sites_directos: Optional[dict] = None):
    if not isinstance(texto, str):
        return None
    if not re.search(r"\b(toca|coloca|abre|abra)\b", texto, flags=re.IGNORECASE):
        return None
    t = texto.lower()
    t = re.sub(r"[,\.\!\?\:\;]+", " ", t)
    t = re.sub(r"\b(laylay)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    sites_directos = sites_directos or {}

    m_abre = re.search(r"\b(?:abre|abra)\b\s+(.*)$", t)
    if m_abre:
        alvo = (m_abre.group(1) or "").strip()
        alvo = re.sub(r"^(o|a|os|as|um|uma)\s+", "", alvo).strip()
        if not alvo:
            return None
        for site, url in sites_directos.items():
            if site in alvo:
                return ("OPEN_URL", url)
        return ("OPEN_APP", alvo)

    m_toca = re.search(r"\b(?:toca|coloca)\b\s+(.*)$", t)
    if m_toca:
        resto = (m_toca.group(1) or "").strip()
        if not resto:
            return None
        q = re.sub(r"\b(no|na)\s+youtube\b", " ", resto)
        q = re.sub(r"\byoutube\b", " ", q)
        q = re.sub(r"\s+", " ", q).strip()
        if not q:
            return None
        return ("YOUTUBE", q)
    return None
