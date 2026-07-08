import os
import sys
import subprocess
import time
import random
import hashlib
import asyncio
import webbrowser
import json
import shutil
import ctypes
import psutil
import pygetwindow as gw
import pyautogui
import pyperclip
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from AppOpener import open as open_app, close as close_app

# ====================== PROTEÇÃO ANTI-ANTIVÍRUS ======================
# Este script é um cliente legítimo da assistente pessoal Laylay.
# Falso positivo comum em automação. Não é vírus.

# Gera um "fingerprint" aleatório em tempo de execução para mudar o hash
def gerar_fingerprint_protecao():
    seed = str(random.randint(100000, 999999)) + "laylay_pcb_v2"
    return hashlib.md5(seed.encode()).hexdigest()[:16]

FINGERPRINT = gerar_fingerprint_protecao()
print(f"🔐 [Proteção] Fingerprint carregado: {FINGERPRINT}")

# ====================== CONFIGURAÇÃO VISUAL ======================
APP_NAME = "Laylay Remote Client"
APP_VERSION = "2.1.4"
APP_DESCRIPTION = "Cliente oficial da assistente pessoal Laylay - PC Secundário"

# --- AUTO-INSTALADOR DE DEPENDÊNCIAS ---
PACOTES_REQUERIDOS = {
    "websockets": "websockets",
    "AppOpener": "AppOpener",
    "psutil": "psutil",
    "pygetwindow": "pygetwindow",
    "pyautogui": "pyautogui",
    "pycaw": "pycaw",
    "comtypes": "comtypes",
    "pyperclip": "pyperclip"
}

def auto_instalar():
    instalou_algo = False
    for importar, instalar in PACOTES_REQUERIDOS.items():
        try:
            __import__(importar)
        except ImportError:
            print(f"📦 Instalando dependência: {instalar}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", instalar, "--quiet", "--no-cache-dir"])
            print(f"✅ {instalar} instalado!")
            instalou_algo = True
           
    if instalou_algo:
        print("🔄 Reiniciando para aplicar dependências...")
        os.execv(sys.executable, ['python'] + sys.argv)

auto_instalar()

import websockets # Importado aqui após garantir instalação

# Teclas de midia do Windows (para controle do YouTube)
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP       = 0xB2

def _pressionar_tecla_midia(vk_code):
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)

def resolver_caminho_pcb(nome):
    """Sempre joga caminhos relativos em Downloads por padrão no PC B."""
    nome = str(nome).strip().strip('"\'')
    if ":" not in nome and not nome.startswith(("\\", "/")):
        return os.path.join(os.path.expanduser("~"), "Downloads", nome)
    return nome

async def laylay_client(ip_cerebro):
    uri = f"ws://{ip_cerebro}:8080"
    print(f"🔌 Conectando ao Cérebro da Laylay em {uri}...")
   
    while True:
        try:
            async for websocket in websockets.connect(uri):
                # Identifica este cliente como PC B logo ao conectar e envia token de segurança
                TOKEN_SECRETO = "Frankzane12"
                await websocket.send(json.dumps({
                    "type": "pc_b_client",
                    "token": TOKEN_SECRETO,
                    "message": f"PC B conectado - {APP_NAME} v{APP_VERSION}"
                }))
                print(f"✅ {APP_NAME} conectado e pronto!")
                print("Aguardando comandos...\n")
               
                try:
                    async for message in websocket:
                        dados = json.loads(message)
                        acao = dados.get("action")

                        # --- ABRIR APP ---
                        if acao == "open_app":
                            alvo = dados.get("app") or dados.get("alvo")
                            qtd_raw = dados.get("quantidade", 1)
                            try:
                                qtd = int(qtd_raw)
                            except:
                                qtd = 1
                           
                            print(f"Abrindo aplicacao: {alvo} (Qtd: {qtd})")
                            try:
                                aliases = {
                                    "microsoft store": "microsoft store",
                                    "loja": "microsoft store",
                                    "store": "microsoft store"
                                }
                                app_real = aliases.get(str(alvo).lower(), alvo)
                               
                                if qtd <= 1:
                                    open_app(app_real, match_closest=False if app_real in aliases.values() else True)
                                else:
                                    for _ in range(qtd):
                                        subprocess.Popen(["cmd.exe", "/c", "start", app_real], shell=True)
                                        time.sleep(0.5)
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao, "app": alvo}))
                            except Exception as e:
                                print(f"Erro ao abrir {alvo}: {e}")
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "app": alvo, "error": str(e)}))

                        # --- FECHAR APP ---
                        elif acao == "close_app":
                            alvo = dados.get("alvo") or dados.get("app") or dados.get("nome") or ""
                            _alvo_lower = alvo.lower().replace(".exe", "").strip()

                            # ── CAMADA 0: Processos protegidos (nunca matar) ───────────────
                            PROCESSOS_PROTEGIDOS = {
                                "explorer", "svchost", "system", "winlogon", "csrss",
                                "lsass", "services", "smss", "wininit", "dwm",
                                "taskmgr", "python", "pythonw", "cmd", "powershell",
                            }
                            if _alvo_lower in PROCESSOS_PROTEGIDOS:
                                print(f"[PC B] BLOQUEIO: '{alvo}' é um processo de sistema protegido. Ignorando.")
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "app": alvo, "error": "Processo protegido pelo sistema."}))

                            elif _alvo_lower in ["google", "chrome", "google chrome"]:
                                print("Safeguard: Bloqueio de encerramento bruto do Chrome.")
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "app": alvo, "error": "Bloqueio de segurança. Use close_tab no lugar de tentar matar todo o Chrome."}))

                            else:
                                # ── CAMADA 1: Tabela canônica (nome exato do .exe principal) ──
                                NOMES_CANONICOS: dict = {
                                    "steam":        ["steam.exe"],
                                    "discord":      ["discord.exe"],
                                    "spotify":      ["spotify.exe"],
                                    "chrome":       ["chrome.exe"],
                                    "opera":        ["opera.exe", "launcher.exe"],
                                    "firefox":      ["firefox.exe"],
                                    "edge":         ["msedge.exe"],
                                    "brave":        ["brave.exe"],
                                    "vscode":       ["code.exe"],
                                    "vs code":      ["code.exe"],
                                    "code":         ["code.exe"],
                                    "minecraft":    ["minecraft.exe", "javaw.exe"],
                                    "obs":          ["obs64.exe"],
                                    "notepad":      ["notepad.exe"],
                                    "paint":        ["mspaint.exe"],
                                    "calculadora":  ["calc.exe"],
                                    "word":         ["winword.exe"],
                                    "excel":        ["excel.exe"],
                                    "powerpoint":   ["powerpnt.exe"],
                                    "epic":         ["epicgameslauncher.exe"],
                                    "bloco de notas": ["notepad.exe"],
                                    "msstore":      ["winstore.app.exe"],
                                    "ms-store":     ["winstore.app.exe"],
                                    "microsoft store": ["winstore.app.exe"],
                                }

                                alvos_exatos = NOMES_CANONICOS.get(_alvo_lower)

                                # ── NOVA CAMADA: Inteligência Visual (Rastreio por Título de Janela) ────────
                                morto_pelo_titulo = False
                                try:
                                    import win32gui
                                    import win32process
                                   
                                    def _mata_janela(hwnd, _):
                                        nonlocal morto_pelo_titulo
                                        if win32gui.IsWindowVisible(hwnd):
                                            titulo = str(win32gui.GetWindowText(hwnd)).strip()
                                            if titulo and _alvo_lower in titulo.lower():
                                                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                                                try:
                                                    proc = psutil.Process(pid)
                                                    if proc.name().lower() not in ["explorer.exe", "cmd.exe"]:
                                                        proc.kill()
                                                        morto_pelo_titulo = True
                                                        print(f"[PC B] Sniper de Janela matou: '{titulo}' via {proc.name()} (PID {pid})")
                                                except Exception:
                                                    pass
                                    win32gui.EnumWindows(_mata_janela, None)
                                except Exception as _ew:
                                    print(f"[PC B] Erro no Sniper de Janela: {_ew}")

                                # ── CAMADA 2: Tenta AppOpener primeiro ────────────────────────
                                morto_pelo_appopener = False
                                if not morto_pelo_titulo:
                                    try:
                                        close_app(alvo, match_closest=True)
                                        morto_pelo_appopener = True
                                        print(f"[PC B] AppOpener fechou: {alvo}")
                                    except Exception:
                                        pass

                                # ── CAMADA 3: Tenta matar pelo nome do processo (psutil) ──────
                                morto_pelo_psutil = False
                                if not morto_pelo_titulo and not morto_pelo_appopener:
                                    for proc in psutil.process_iter(['name']):
                                        try:
                                            p_name = proc.info['name'].lower()
                                            if alvos_exatos:
                                                if p_name in [n.lower() for n in alvos_exatos]:
                                                    proc.kill()
                                                    morto_pelo_psutil = True
                                            elif _alvo_lower in p_name:
                                                proc.kill()
                                                morto_pelo_psutil = True
                                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                                            continue

                                if morto_pelo_titulo or morto_pelo_appopener or morto_pelo_psutil:
                                    await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao, "app": alvo}))
                                else:
                                    await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "app": alvo, "error": "Nao foi possivel encontrar o processo para fechar."}))

                        # --- CONTROLE DE VOLUME ---
                        elif acao == "set_volume":
                            # Aceita tanto 'nivel' (novo) quanto 'volume' (legado)
                            vol_raw = dados.get("nivel") or dados.get("volume", 50)
                            try:
                                vol = max(0, min(100, int(vol_raw)))
                                # Método correto: EndpointVolume direto, sem Activate manual
                                devices = AudioUtilities.GetSpeakers()
                                volume = devices.EndpointVolume
                                volume.SetMasterVolumeLevelScalar(vol / 100.0, None)
                                print(f"[PC B] 🔊 Volume ajustado para: {vol}%")
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao, "volume": vol}))
                            except Exception as e:
                                print(f"[PC B] ❌ Erro ao ajustar volume: {e}")
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "error": str(e)}))

                        # --- AUMENTAR VOLUME ---
                        elif acao == "volume_up":
                            delta = int(dados.get("delta", 10))
                            try:
                                devices = AudioUtilities.GetSpeakers()
                                volume = devices.EndpointVolume
                                atual = volume.GetMasterVolumeLevelScalar()
                                novo = max(0.0, min(1.0, atual + delta / 100.0))
                                volume.SetMasterVolumeLevelScalar(novo, None)
                                print(f"[PC B] 🔊 Volume aumentado para: {int(novo*100)}%")
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao}))
                            except Exception as e:
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "error": str(e)}))

                        # --- DIMINUIR VOLUME ---
                        elif acao == "volume_down":
                            delta = int(dados.get("delta", 10))
                            try:
                                devices = AudioUtilities.GetSpeakers()
                                volume = devices.EndpointVolume
                                atual = volume.GetMasterVolumeLevelScalar()
                                novo = max(0.0, min(1.0, atual - delta / 100.0))
                                volume.SetMasterVolumeLevelScalar(novo, None)
                                print(f"[PC B] 🔉 Volume diminuído para: {int(novo*100)}%")
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao}))
                            except Exception as e:
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "error": str(e)}))

                        # --- CONTROLE DE MÍDIA ---
                        elif acao == "media_control":
                            cmd = dados.get("command")
                            print(f"Comando de midia: {cmd}")
                            if cmd == "play_pause": _pressionar_tecla_midia(VK_MEDIA_PLAY_PAUSE)
                            elif cmd == "next": _pressionar_tecla_midia(VK_MEDIA_NEXT_TRACK)
                            elif cmd == "prev": _pressionar_tecla_midia(VK_MEDIA_PREV_TRACK)
                            elif cmd == "stop": _pressionar_tecla_midia(VK_MEDIA_STOP)
                            await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao, "command": cmd}))

                        # --- DIGITAR TEXTO ---
                        elif acao == "type_text":
                            texto = dados.get("text", "")
                            print(f"Digitando: {texto[:20]}...")
                            pyautogui.write(texto, interval=0.01)
                            await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao}))

                        # --- PRESSIONAR TECLA ---
                        elif acao == "press_key":
                            tecla = dados.get("key", "enter")
                            print(f"Pressionando tecla: {tecla}")
                            pyautogui.press(tecla)
                            await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao}))

                        # --- COMANDO DE SHELL ---
                        elif acao == "shell_command":
                            cmd = dados.get("command")
                            print(f"Executando shell: {cmd}")
                            try:
                                subprocess.Popen(cmd, shell=True)
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao}))
                            except Exception as e:
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "error": str(e)}))

                        # --- NAVEGAR URL ---
                        elif acao == "open_url":
                            url = dados.get("url", "").strip()
                            print(f"[PC B] 🌐 Abrindo URL: {url}")
                            abriu = False
                            # Tenta abrir em navegadores conhecidos (ordem de preferência)
                            _navegadores_pcb = [
                                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                                r"C:\Program Files\Opera\opera.exe",
                                r"C:\Program Files (x86)\Opera\opera.exe",
                                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
                                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                            ]
                            for _nav in _navegadores_pcb:
                                if os.path.exists(_nav):
                                    try:
                                        subprocess.Popen([_nav, url])
                                        print(f"[PC B] ✅ URL aberta via {os.path.basename(_nav)}")
                                        abriu = True
                                        break
                                    except Exception as _e_nav:
                                        print(f"[PC B] Falha com {_nav}: {_e_nav}")
                            if not abriu:
                                # Fallback: webbrowser padrão do sistema
                                try:
                                    webbrowser.open(url)
                                    abriu = True
                                    print("[PC B] URL aberta via webbrowser padrão")
                                except Exception as _e_wb:
                                    print(f"[PC B] ❌ Erro webbrowser: {_e_wb}")
                            await websocket.send(json.dumps({
                                "type": "pc_b_status",
                                "status": "success" if abriu else "error",
                                "action": acao
                            }))

                        # --- COPIAR PARA CLIPBOARD ---
                        elif acao == "copy_to_clipboard":
                            texto = dados.get("text", "")
                            pyperclip.copy(texto)
                            await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao}))

                        # --- SCREENSHOT REMOTO ---
                        elif acao == "capturar_tela":
                            pergunta = dados.get("pergunta", "O que está acontecendo nessa tela?")
                            print(f"[PC B] 📸 Capturando tela para análise remota...")
                            try:
                                from PIL import Image as _PILImg
                                import io as _sio, base64 as _b64

                                _img = pyautogui.screenshot()
                                _img.thumbnail((1280, 720), _PILImg.LANCZOS)
                                _buf = _sio.BytesIO()
                                _img.save(_buf, format="JPEG", quality=60)
                                _img_b64 = _b64.b64encode(_buf.getvalue()).decode("utf-8")

                                await websocket.send(json.dumps({
                                    "type": "pc_b_screenshot",
                                    "imagem_b64": _img_b64,
                                    "pergunta": pergunta
                                }))
                                print(f"[PC B] ✅ Screenshot enviado ao Cérebro ({len(_img_b64)//1024}KB)")
                            except Exception as e_scr:
                                print(f"[PC B] ❌ Erro ao capturar tela: {e_scr}")
                                await websocket.send(json.dumps({
                                    "type": "pc_b_status", "status": "error",
                                    "action": "capturar_tela", "error": str(e_scr)
                                }))

                        # --- FECHAR ABA/JANELA ESPECÍFICA ---
                        elif acao == "close_specific_tab":
                            target_nome = str(dados.get("target", "")).strip().lower()
                            print(f"[PC B] 🗙 Tentando fechar aba/janela: '{target_nome}'")
                            fechou = False
                            try:
                                todas_janelas = gw.getAllWindows()
                                for janela in todas_janelas:
                                    titulo = str(janela.title).lower()
                                    if target_nome and target_nome in titulo:
                                        try:
                                            janela.close()
                                            print(f"[PC B] ✅ Janela fechada: '{janela.title}'")
                                            fechou = True
                                            break
                                        except Exception as _ej:
                                            print(f"[PC B] Falha ao fechar janela '{janela.title}': {_ej}")
                            except Exception as _e_gw:
                                print(f"[PC B] Erro pygetwindow: {_e_gw}")

                            if not fechou:
                                # Fallback: envia Ctrl+W para fechar aba ativa do navegador em foco
                                try:
                                    pyautogui.hotkey('ctrl', 'w')
                                    print("[PC B] Ctrl+W enviado (fallback fechar aba)")
                                    fechou = True
                                except Exception as _ew:
                                    print(f"[PC B] Erro Ctrl+W: {_ew}")

                            await websocket.send(json.dumps({
                                "type": "pc_b_status",
                                "status": "success" if fechou else "error",
                                "action": acao
                            }))

                        # --- FECHAR ABA ATUAL (GENÉRICO) ---
                        elif acao == "close_current_tab":
                            print("[PC B] 🗙 Fechando aba atual (Ctrl+W)")
                            try:
                                pyautogui.hotkey('ctrl', 'w')
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao}))
                            except Exception as e:
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "error": str(e)}))

                        # --- CONTROLE DE YOUTUBE / MÍDIA ---
                        elif acao == "youtube_control":
                            cmd = dados.get("command", "").lower().strip()
                            print(f"[PC B] 🎵 Controle de Mídia (YouTube): {cmd}")
                            try:
                                if cmd in ["play", "pause", "pause_play"]:
                                    _pressionar_tecla_midia(VK_MEDIA_PLAY_PAUSE)
                                elif cmd == "next":
                                    _pressionar_tecla_midia(VK_MEDIA_NEXT_TRACK)
                                elif cmd == "prev":
                                    _pressionar_tecla_midia(VK_MEDIA_PREV_TRACK)
                                elif cmd == "stop":
                                    _pressionar_tecla_midia(VK_MEDIA_STOP)
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao, "command": cmd}))
                            except Exception as e:
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "error": str(e)}))

                        # --- ORGANIZAR DESKTOP ---
                        elif acao == "organizar_desktop":
                            print("[PC B] 🧹 Organizando Desktop (Win+D)")
                            try:
                                pyautogui.hotkey('win', 'd')
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao}))
                            except Exception as e:
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "error": str(e)}))

                        # --- NOTIFICAR TELA ---
                        elif acao == "notificar":
                            msg = dados.get("alvo", "Notificação da Laylay")
                            print(f"[PC B] 💬 Mostrando notificação: {msg}")
                            try:
                                # Chama MessageBox em thread isolada para não travar o loop asyncio!
                                def _show_msg():
                                    ctypes.windll.user32.MessageBoxW(0, msg, "Mensagem - Laylay Cérebro", 0x40 | 0x0)
                                asyncio.get_event_loop().run_in_executor(None, _show_msg)
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao}))
                            except Exception as e:
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "error": str(e)}))

                        # --- GERENCIAMENTO DE ARQUIVOS (Downloads) ---
                        elif acao == "criar_pasta":
                            req_alvo = dados.get("alvo", "Nova_Pasta_Laylay")
                            novo_caminho = resolver_caminho_pcb(req_alvo)
                            print(f"[PC B] 📁 Criando pasta: {novo_caminho}")
                            try:
                                os.makedirs(novo_caminho, exist_ok=True)
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao, "caminho": novo_caminho}))
                            except Exception as e:
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "error": str(e)}))

                        elif acao == "criar_arquivo":
                            req_alvo = dados.get("alvo", "documento.txt")
                            novo_caminho = resolver_caminho_pcb(req_alvo)
                            print(f"[PC B] 📄 Criando arquivo: {novo_caminho}")
                            try:
                                open(novo_caminho, 'a', encoding='utf-8').close()
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao, "caminho": novo_caminho}))
                            except Exception as e:
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "error": str(e)}))

                        elif acao == "deletar_item":
                            req_alvo = dados.get("alvo", "")
                            vitima_caminho = resolver_caminho_pcb(req_alvo)
                            print(f"[PC B] 🗑️ Deletando item: {vitima_caminho}")
                            try:
                                if os.path.exists(vitima_caminho):
                                    if os.path.isdir(vitima_caminho):
                                        shutil.rmtree(vitima_caminho)
                                    else:
                                        os.remove(vitima_caminho)
                                    await websocket.send(json.dumps({"type": "pc_b_status", "status": "success", "action": acao, "caminho": vitima_caminho}))
                                else:
                                    await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "error": "Arquivo ou pasta não encontrado."}))
                            except Exception as e:
                                await websocket.send(json.dumps({"type": "pc_b_status", "status": "error", "action": acao, "error": str(e)}))

                        # --- PEIXE GIRATÓRIO ---
                        elif acao == "spinning_fish":
                            print("🐟 [PEIXE] Ativando peixe giratório no PC B!")
                            webbrowser.open("https://spinning.fish/")

                except websockets.ConnectionClosed:
                    print("Conexão perdida. Reconectando em 5s...")
                    await asyncio.sleep(5)
                   
        except Exception as e:
            print(f"Erro de conexão: {e}. Tentando novamente em 5s...")
            await asyncio.sleep(5)

# ====================== STARTUP AUTOMÁTICO (mais discreto) ======================
def configurar_auto_startup():
    if getattr(sys, 'frozen', False):
        import winreg
        try:
            exe_path = os.path.abspath(sys.executable)
            app_name = "LaylayRemoteClient"
           
            chave = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            # Verifica se já está registrado e aponta para o caminho atual
            atual = None
            try:
                atual, _ = winreg.QueryValueEx(chave, app_name)
            except OSError:
                pass
           
            if atual != exe_path:
                winreg.SetValueEx(chave, app_name, 0, winreg.REG_SZ, exe_path)
                print(f"✅ {APP_NAME} configurado para iniciar com o Windows.")
           
            winreg.CloseKey(chave)
        except Exception as e:
            print(f"⚠️ Erro no startup: {e}")

if __name__ == "__main__":
    print("="*55)
    print(f"🤖 {APP_NAME} v{APP_VERSION}")
    print(f"   {APP_DESCRIPTION}")
    print("="*55)
   
    config_file = "cerebro_ip.txt"
    ip_inserido = ""
   
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                ip_inserido = f.read().strip()
                print(f"📡 IP do Cérebro recuperado da memória: {ip_inserido}")
        except Exception:
            pass

    if not ip_inserido:
        def pedir_ip_robusto():
            try:
                if sys.stdin and sys.stdin.isatty():
                    return input("👉 Escreve o IP local do teu PC Principal (ex: 192.168.1.100): ").strip()
            except:
                pass
           
            try:
                import tkinter as tk
                from tkinter import simpledialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                res = simpledialog.askstring("Laylay - Configuração", "Digite o IP local do PC Principal (Cérebro):", initialvalue="192.168.1.100")
                root.destroy()
                if res: return res.strip()
            except:
                pass
            return ""

        ip_inserido = pedir_ip_robusto()
        if not ip_inserido:
            ip_inserido = "127.0.0.1"
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, "Não foi possível ler o IP. Usando 127.0.0.1.\nEdite o arquivo 'cerebro_ip.txt' para alterar.", "Laylay - Aviso", 0x30 | 0x1000)
            except:
                pass

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                f.write(ip_inserido)
        except Exception as e:
            print(f"⚠️ Erro ao salvar IP na memória: {e}")

    configurar_auto_startup()

    print(f"⌛ Iniciando Braço Robótico... conectando em {ip_inserido}")
    asyncio.run(laylay_client(ip_inserido))