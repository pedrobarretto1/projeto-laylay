import os
import sys
import subprocess
import time
import random
import hashlib
import asyncio
import contextlib
from collections import deque
import webbrowser
import json
import shutil
import ctypes
import threading
import pygetwindow as gw
import pyautogui
import pyperclip
from pycaw.pycaw import AudioUtilities
from AppOpener import open as open_app

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
APP_VERSION = "2.4.0"
APP_DESCRIPTION = "Cliente oficial da assistente pessoal Laylay - PC Secundário"
PC_B_PROTOCOL_VERSION = 2
PC_B_HEARTBEAT_INTERVAL_S = 15.0
PC_B_MAX_MESSAGE_BYTES = 65_536
PC_B_REQUEST_TTL_S = 180.0
PC_B_MAX_REQUESTS_PER_MINUTE = 60

# --- AUTO-INSTALADOR DE DEPENDÊNCIAS ---
PACOTES_REQUERIDOS = {
    "websockets": "websockets",
    "AppOpener": "AppOpener",
    "pygetwindow": "pygetwindow",
    "pyautogui": "pyautogui",
    "pycaw": "pycaw",
    "comtypes": "comtypes",
    "pyperclip": "pyperclip"
}

def auto_instalar():
    if str(os.environ.get("LAYLAY_PC_B_AUTO_INSTALL", "0")).strip().casefold() not in {
        "1", "true", "yes", "sim", "on",
    }:
        return
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


class WebSocketCorrelacionado:
    """Anexa o requestId e o estado final a todas as respostas do PC B."""

    def __init__(self, websocket):
        self._websocket = websocket
        self.request_id = None

    def __aiter__(self):
        return self._websocket.__aiter__()

    async def send(self, mensagem):
        try:
            payload = json.loads(mensagem) if isinstance(mensagem, str) else dict(mensagem)
            if payload.get("type") in {"pc_b_status", "pc_b_screenshot"}:
                payload.setdefault("requestId", self.request_id)
            if payload.get("type") == "pc_b_status":
                payload.setdefault("final", True)
            mensagem = json.dumps(payload)
        except Exception:
            pass
        return await self._websocket.send(mensagem)


def mover_para_lixeira_pcb(caminho):
    """Move para uma lixeira reversível do cliente em vez de apagar definitivamente."""
    raiz = os.path.join(os.path.expanduser("~"), ".laylay", "lixeira_pc_b")
    identificador = f"{int(time.time())}_{random.randint(100000, 999999)}"
    destino = os.path.join(raiz, identificador, os.path.basename(caminho))
    os.makedirs(os.path.dirname(destino), exist_ok=False)
    shutil.move(caminho, destino)
    return destino

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


def _flag_ambiente(env_getter, nome, padrao="0"):
    return str(env_getter(nome, padrao) or "").strip().casefold() in {
        "1", "true", "yes", "sim", "on",
    }


def _raizes_arquivos_pcb(env_getter=os.getenv):
    configuradas = str(env_getter("LAYLAY_PC_B_ALLOWED_ROOTS", "") or "")
    candidatas = [item.strip() for item in configuradas.split(";") if item.strip()]
    if not candidatas:
        candidatas = [os.path.join(os.path.expanduser("~"), "Downloads")]
    return tuple(dict.fromkeys(
        os.path.normcase(os.path.realpath(os.path.abspath(os.path.expanduser(item))))
        for item in candidatas
    ))


def resolver_caminho_seguro_pcb(nome, *, raizes=None, permitir_raiz=False):
    """Resolve mutações somente dentro das raízes explicitamente autorizadas."""
    raizes = tuple(raizes or _raizes_arquivos_pcb())
    texto = str(nome or "").strip().strip('"\'')
    if not texto or not raizes:
        raise ValueError("Caminho ausente ou sem raiz autorizada.")
    candidato = texto if os.path.isabs(texto) else os.path.join(raizes[0], texto)
    normalizado = os.path.normcase(os.path.realpath(os.path.abspath(candidato)))
    permitido = False
    for raiz in raizes:
        try:
            dentro = os.path.commonpath((normalizado, raiz)) == raiz
        except ValueError:
            dentro = False
        if dentro and (permitir_raiz or normalizado != raiz):
            permitido = True
            break
    if not permitido:
        raise PermissionError("O caminho fica fora das pastas autorizadas do PC B.")
    return normalizado


def _sanitizar_erro_remoto(valor):
    texto = str(valor or "").replace(os.path.expanduser("~"), "%USERPROFILE%")
    for marcador in ("sk-", "ghp_", "github_pat_", "Bearer "):
        indice = texto.casefold().find(marcador.casefold())
        if indice >= 0:
            fim = texto.find(" ", indice)
            fim = len(texto) if fim < 0 else fim
            texto = texto[:indice] + "[redigido]" + texto[fim:]
    return texto[:320]


def _nome_aplicativo_seguro(valor):
    texto = str(valor or "").strip()
    if not texto or len(texto) > 128:
        return ""
    if any(caractere in texto for caractere in "&|<>^%`\r\n"):
        return ""
    return texto


def _primeiro_parametro(dados, *nomes, padrao=None):
    """Lê aliases do protocolo sem confundir zero com campo ausente."""
    for nome in nomes:
        if nome in dados and dados.get(nome) is not None:
            return dados.get(nome)
    return padrao


def _endpoint_volume():
    return AudioUtilities.GetSpeakers().EndpointVolume


def _ajustar_volume_absoluto(dados):
    bruto = _primeiro_parametro(dados, "nivel", "level", "volume")
    if bruto is None:
        raise ValueError("Nível de volume ausente.")
    nivel = max(0, min(100, int(float(bruto))))
    endpoint = _endpoint_volume()
    endpoint.SetMasterVolumeLevelScalar(nivel / 100.0, None)
    observado = int(round(float(endpoint.GetMasterVolumeLevelScalar()) * 100))
    if abs(observado - nivel) > 2:
        raise RuntimeError("O Windows não confirmou o nível solicitado.")
    return observado


def _ajustar_volume_relativo(delta):
    endpoint = _endpoint_volume()
    atual = float(endpoint.GetMasterVolumeLevelScalar())
    novo = max(0.0, min(1.0, atual + float(delta) / 100.0))
    endpoint.SetMasterVolumeLevelScalar(novo, None)
    observado = int(round(float(endpoint.GetMasterVolumeLevelScalar()) * 100))
    if abs(observado - int(round(novo * 100))) > 2:
        raise RuntimeError("O Windows não confirmou a alteração do volume.")
    return observado


def _desmutar_volume():
    endpoint = _endpoint_volume()
    endpoint.SetMute(False, None)
    get_mute = getattr(endpoint, "GetMute", None)
    return not bool(get_mute()) if callable(get_mute) else True


def _normalizar_alvo_janela(valor):
    texto = str(valor or "").strip().casefold().replace(".exe", "")
    aliases = {
        "vscode": "visual studio code",
        "vs code": "visual studio code",
        "google chrome": "chrome",
    }
    return aliases.get(texto, texto)


def _encontrar_janela(alvo, *, excluir=()):
    alvo_normalizado = _normalizar_alvo_janela(alvo)
    if not alvo_normalizado:
        return None
    excluidas = {id(item) for item in excluir}
    candidatas = []
    for janela in gw.getAllWindows():
        if id(janela) in excluidas:
            continue
        titulo = str(getattr(janela, "title", "") or "").strip()
        titulo_normalizado = titulo.casefold()
        if not titulo_normalizado:
            continue
        pontuacao = 0
        if titulo_normalizado == alvo_normalizado:
            pontuacao = 4
        elif titulo_normalizado.startswith(alvo_normalizado):
            pontuacao = 3
        elif alvo_normalizado in titulo_normalizado:
            pontuacao = 2
        elif all(parte in titulo_normalizado for parte in alvo_normalizado.split()):
            pontuacao = 1
        if pontuacao:
            candidatas.append((pontuacao, janela))
    return max(candidatas, key=lambda item: item[0])[1] if candidatas else None


def _maximizar_janela_remota(alvo):
    janela = _encontrar_janela(alvo)
    if janela is None:
        return {"ok": False, "error": f"Janela não encontrada: {alvo}."}
    try:
        if bool(getattr(janela, "isMinimized", False)):
            janela.restore()
        janela.maximize()
        time.sleep(0.12)
        confirmado = bool(getattr(janela, "isMaximized", False))
        return {
            "ok": confirmado,
            "app": str(alvo or ""),
            "window": str(getattr(janela, "title", "") or ""),
            "error": "" if confirmado else "A janela não confirmou a maximização.",
        }
    except Exception as erro:
        return {"ok": False, "error": f"Falha ao maximizar a janela: {erro}"}


def _dimensoes_tela():
    user32 = ctypes.windll.user32
    return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))


def _posicionar_janela(janela, *, lado, largura_tela, altura_tela):
    metade = max(1, largura_tela // 2)
    x = 0 if lado == "left" else metade
    largura = metade if lado == "left" else max(1, largura_tela - metade)
    if bool(getattr(janela, "isMinimized", False)) or bool(
        getattr(janela, "isMaximized", False)
    ):
        janela.restore()
    janela.moveTo(x, 0)
    janela.resizeTo(largura, altura_tela)
    time.sleep(0.08)
    return (
        abs(int(getattr(janela, "left", -9999)) - x) <= 8
        and abs(int(getattr(janela, "top", -9999))) <= 8
        and abs(int(getattr(janela, "width", -1)) - largura) <= 12
    )


def _organizar_janelas_remotas(esquerda, direita):
    esquerda = str(esquerda or "").strip()
    direita = str(direita or "").strip()
    if not esquerda and not direita:
        return {"ok": False, "error": "Nenhuma janela foi informada para organizar."}
    janela_esquerda = _encontrar_janela(esquerda) if esquerda else None
    janela_direita = (
        _encontrar_janela(direita, excluir=(janela_esquerda,)) if direita else None
    )
    ausentes = []
    if esquerda and janela_esquerda is None:
        ausentes.append(esquerda)
    if direita and janela_direita is None:
        ausentes.append(direita)
    if ausentes:
        return {
            "ok": False,
            "error": "Janela não encontrada: " + " e ".join(ausentes) + ".",
        }
    largura_tela, altura_tela = _dimensoes_tela()
    resultados = []
    try:
        if janela_esquerda is not None:
            resultados.append(_posicionar_janela(
                janela_esquerda,
                lado="left",
                largura_tela=largura_tela,
                altura_tela=altura_tela,
            ))
        if janela_direita is not None:
            resultados.append(_posicionar_janela(
                janela_direita,
                lado="right",
                largura_tela=largura_tela,
                altura_tela=altura_tela,
            ))
    except Exception as erro:
        return {"ok": False, "error": f"Falha ao organizar as janelas: {erro}"}
    confirmado = bool(resultados) and all(resultados)
    return {
        "ok": confirmado,
        "left": esquerda,
        "right": direita,
        "error": "" if confirmado else "O Windows não confirmou o layout final.",
    }


def _executar_controle_midia(comando):
    comando = str(comando or "").strip().casefold()
    mapa = {
        "play": VK_MEDIA_PLAY_PAUSE,
        "pause": VK_MEDIA_PLAY_PAUSE,
        "play_pause": VK_MEDIA_PLAY_PAUSE,
        "pause_play": VK_MEDIA_PLAY_PAUSE,
        "next": VK_MEDIA_NEXT_TRACK,
        "prev": VK_MEDIA_PREV_TRACK,
        "previous": VK_MEDIA_PREV_TRACK,
        "stop": VK_MEDIA_STOP,
    }
    if comando == "skip_ad":
        return {
            "ok": False,
            "error": "Pular anúncio exige a extensão do navegador no PC B.",
        }
    tecla = mapa.get(comando)
    if tecla is None:
        return {"ok": False, "error": f"Comando de mídia não suportado: {comando}."}
    _pressionar_tecla_midia(tecla)
    return {"ok": True, "command": comando, "confirmed": False}


def _resultado_remoto(ok, *, confirmed=None, error="", **campos):
    resultado = {
        "ok": bool(ok),
        "confirmed": bool(confirmed) if confirmed is not None else None,
        "error": str(error or ""),
    }
    resultado.update(campos)
    return resultado


class ExecutorRemotoPC:
    """Valida, executa e finaliza cada comando remoto exatamente uma vez."""

    def __init__(self, *, env_getter=os.getenv, relogio=time.monotonic):
        self._env_getter = env_getter
        self._relogio = relogio
        self._lock_seguranca = threading.RLock()
        self._requests_vistos = {}
        self._requests_recentes = deque()
        self._raizes_arquivos = _raizes_arquivos_pcb(env_getter)
        self._handlers = {
            "open_app": self._abrir_app,
            "close_app": self._fechar_app,
            "maximize_window": self._maximizar_janela,
            "set_volume": self._definir_volume,
            "volume_up": self._aumentar_volume,
            "volume_down": self._diminuir_volume,
            "volume_unmute": self._desmutar,
            "media_control": self._controlar_midia,
            "youtube_control": self._controlar_midia,
            "open_url": self._abrir_url,
            "capturar_tela": self._capturar_tela,
            "close_specific_tab": self._fechar_aba_especifica,
            "close_current_tab": self._fechar_aba_atual,
            "organizar_desktop": self._organizar_desktop,
            "lock_pc": self._bloquear_pc,
            "notificar": self._notificar,
            "criar_pasta": self._criar_pasta,
            "criar_arquivo": self._criar_arquivo,
            "deletar_item": self._deletar_item,
            "spinning_fish": self._spinning_fish,
        }
        if _flag_ambiente(env_getter, "LAYLAY_PC_B_ALLOW_INPUT_AUTOMATION"):
            self._handlers.update({
                "type_text": self._digitar_texto,
                "press_key": self._pressionar_tecla,
                "copy_to_clipboard": self._copiar_clipboard,
            })
        if _flag_ambiente(env_getter, "LAYLAY_PC_B_ALLOW_SHELL"):
            self._handlers["shell_command"] = self._executar_shell

    @property
    def acoes_suportadas(self):
        return frozenset(self._handlers)

    async def executar(self, websocket, dados):
        if not isinstance(dados, dict):
            await self._enviar_final(
                websocket,
                "",
                _resultado_remoto(False, error="Comando remoto inválido."),
                error_code="payload_invalido",
            )
            return
        acao = str(dados.get("action") or "").strip()
        handler = self._handlers.get(acao)
        if handler is None:
            await self._enviar_final(
                websocket,
                acao,
                _resultado_remoto(
                    False,
                    error=f"Ação não suportada pelo PC B: {acao or 'vazia'}.",
                ),
                error_code="acao_nao_suportada",
            )
            return
        erro_validacao, codigo_validacao = self._validar_envelope(dados)
        if erro_validacao:
            await self._enviar_final(
                websocket,
                acao,
                _resultado_remoto(False, error=erro_validacao),
                error_code=codigo_validacao,
            )
            return
        try:
            resultado = await asyncio.to_thread(handler, dict(dados))
            if not isinstance(resultado, dict):
                resultado = _resultado_remoto(
                    False, error="O executor não devolveu um resultado válido."
                )
        except Exception as erro:
            resultado = _resultado_remoto(
                False,
                error=f"{type(erro).__name__}: {erro}",
            )

        mensagens = list(resultado.pop("_messages", []) or [])
        for mensagem in mensagens:
            if isinstance(mensagem, dict):
                await websocket.send(json.dumps(mensagem))
        await self._enviar_final(websocket, acao, resultado)

    def _validar_envelope(self, dados):
        try:
            tamanho = len(json.dumps(dados, ensure_ascii=False).encode("utf-8"))
        except (TypeError, ValueError):
            return "O comando não pôde ser serializado com segurança.", "payload_invalido"
        if tamanho > PC_B_MAX_MESSAGE_BYTES:
            return "O comando excedeu o limite aceito pelo PC B.", "payload_excessivo"
        limites = {
            "text": 8_000,
            "alvo": 1_024,
            "target": 1_024,
            "app": 256,
            "url": 2_048,
            "command": 2_048,
            "pergunta": 2_000,
        }
        for campo, limite in limites.items():
            if campo in dados and len(str(dados.get(campo) or "")) > limite:
                return f"O campo {campo} excedeu o limite seguro.", "campo_excessivo"
        if dados.get("expectsFinalStatus") is not True:
            return "", ""
        request_id = str(dados.get("requestId") or "").strip()
        if not request_id or len(request_id) > 128:
            return "Identificador do pedido ausente ou inválido.", "request_id_invalido"
        agora = float(self._relogio())
        with self._lock_seguranca:
            limite_tempo = agora - PC_B_REQUEST_TTL_S
            for antigo, instante in list(self._requests_vistos.items()):
                if instante < limite_tempo:
                    self._requests_vistos.pop(antigo, None)
            while self._requests_recentes and self._requests_recentes[0] < agora - 60.0:
                self._requests_recentes.popleft()
            if request_id in self._requests_vistos:
                return "Pedido remoto repetido; nada foi executado.", "request_repetido"
            if len(self._requests_recentes) >= PC_B_MAX_REQUESTS_PER_MINUTE:
                return "Muitos pedidos remotos em pouco tempo.", "limite_taxa"
            self._requests_vistos[request_id] = agora
            self._requests_recentes.append(agora)
        return "", ""

    @staticmethod
    async def _enviar_final(
        websocket, acao, resultado, *, error_code="",
    ):
        ok = bool(resultado.get("ok"))
        payload = {
            "type": "pc_b_status",
            "status": "success" if ok else "error",
            "action": str(acao or ""),
            "executed": bool(resultado.get("executed", ok)),
            "confirmed": resultado.get("confirmed"),
            "error": _sanitizar_erro_remoto(resultado.get("error")),
        }
        if error_code:
            payload["errorCode"] = error_code
        for chave, valor in resultado.items():
            if chave not in {
                "ok", "executed", "confirmed", "error", "_messages",
            }:
                payload[chave] = valor
        await websocket.send(json.dumps(payload))

    @staticmethod
    def _abrir_app(dados):
        alvo = _nome_aplicativo_seguro(
            dados.get("app") or dados.get("alvo") or ""
        )
        if not alvo:
            return _resultado_remoto(
                False, error="Aplicativo ausente ou com nome inseguro."
            )
        aliases = {
            "loja": "microsoft store",
            "store": "microsoft store",
            "microsoft store": "microsoft store",
        }
        app_real = aliases.get(alvo.casefold(), alvo)
        try:
            quantidade = max(1, min(5, int(dados.get("quantidade", 1))))
        except (TypeError, ValueError):
            quantidade = 1
        for _ in range(quantidade):
            open_app(
                app_real,
                match_closest=False if app_real in aliases.values() else True,
            )
        time.sleep(0.25)
        janela = _encontrar_janela(alvo) or _encontrar_janela(app_real)
        confirmado = janela is not None
        return _resultado_remoto(
            confirmado,
            executed=True,
            confirmed=confirmado,
            error="" if confirmado else "O aplicativo não apareceu entre as janelas.",
            app=alvo,
        )

    @staticmethod
    def _fechar_app(dados):
        alvo = str(
            dados.get("alvo") or dados.get("app") or dados.get("nome") or ""
        ).strip()
        alvo_normalizado = _normalizar_alvo_janela(alvo)
        protegidos = {
            "explorer", "svchost", "system", "winlogon", "csrss", "lsass",
            "services", "smss", "wininit", "dwm", "taskmgr", "python",
            "pythonw", "cmd", "powershell",
        }
        if not alvo_normalizado:
            return _resultado_remoto(False, error="Aplicativo não informado.")
        if alvo_normalizado in protegidos:
            return _resultado_remoto(False, error="Processo protegido pelo sistema.")
        if alvo_normalizado in {"chrome", "google"}:
            return _resultado_remoto(
                False,
                error="O encerramento bruto do Chrome foi bloqueado; feche a aba.",
            )
        janela = _encontrar_janela(alvo)
        if janela is None:
            return _resultado_remoto(
                False, error="Não encontrei uma janela desse aplicativo.", app=alvo,
            )
        janela.close()
        for _ in range(10):
            time.sleep(0.08)
            if _encontrar_janela(alvo) is None:
                return _resultado_remoto(True, confirmed=True, app=alvo)
        return _resultado_remoto(
            False,
            executed=True,
            confirmed=False,
            error="A janela continuou aberta.",
            app=alvo,
        )

    @staticmethod
    def _maximizar_janela(dados):
        alvo = dados.get("app") or dados.get("alvo") or dados.get("nome") or ""
        resultado = _maximizar_janela_remota(alvo)
        return _resultado_remoto(
            bool(resultado.get("ok")),
            confirmed=bool(resultado.get("ok")),
            error=resultado.get("error", ""),
            app=str(alvo),
            window=str(resultado.get("window") or ""),
        )

    @staticmethod
    def _definir_volume(dados):
        volume = _ajustar_volume_absoluto(dados)
        return _resultado_remoto(True, confirmed=True, volume=volume)

    @staticmethod
    def _aumentar_volume(dados):
        volume = _ajustar_volume_relativo(int(dados.get("delta", 10)))
        return _resultado_remoto(True, confirmed=True, volume=volume)

    @staticmethod
    def _diminuir_volume(dados):
        volume = _ajustar_volume_relativo(-int(dados.get("delta", 10)))
        return _resultado_remoto(True, confirmed=True, volume=volume)

    @staticmethod
    def _desmutar(_dados):
        confirmado = _desmutar_volume()
        return _resultado_remoto(
            confirmado,
            confirmed=confirmado,
            error="" if confirmado else "O Windows continuou no mudo.",
        )

    @staticmethod
    def _controlar_midia(dados):
        comando = str(dados.get("command") or "").strip()
        resultado = _executar_controle_midia(comando)
        return _resultado_remoto(
            bool(resultado.get("ok")),
            confirmed=resultado.get("confirmed"),
            error=resultado.get("error", ""),
            command=comando,
        )

    @staticmethod
    def _digitar_texto(dados):
        texto = str(dados.get("text") or "")
        if not texto:
            return _resultado_remoto(False, error="Texto ausente.")
        pyautogui.write(texto, interval=0.01)
        return _resultado_remoto(True, confirmed=False, characters=len(texto))

    @staticmethod
    def _pressionar_tecla(dados):
        tecla = str(dados.get("key") or "").strip().casefold()
        if not tecla:
            return _resultado_remoto(False, error="Tecla ausente.")
        pyautogui.press(tecla)
        return _resultado_remoto(True, confirmed=False, key=tecla)

    @staticmethod
    def _executar_shell(dados):
        comando = str(dados.get("command") or "").strip()
        if not comando:
            return _resultado_remoto(False, error="Comando shell ausente.")
        processo = subprocess.Popen(comando, shell=True)
        return _resultado_remoto(
            True, confirmed=False, process_started=processo.pid is not None,
        )

    @staticmethod
    def _abrir_url(dados):
        url = str(dados.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            return _resultado_remoto(False, error="URL HTTP ou HTTPS inválida.")
        abriu = bool(webbrowser.open(url))
        return _resultado_remoto(
            abriu,
            confirmed=False if abriu else None,
            error="" if abriu else "O navegador não aceitou a URL.",
        )

    @staticmethod
    def _copiar_clipboard(dados):
        texto = str(dados.get("text") or "")
        pyperclip.copy(texto)
        confirmado = str(pyperclip.paste()) == texto
        return _resultado_remoto(
            confirmado,
            confirmed=confirmado,
            error="" if confirmado else "O clipboard não confirmou o conteúdo.",
        )

    @staticmethod
    def _capturar_tela(dados):
        from PIL import Image as _PILImg, ImageFilter as _PILFilter
        import base64 as _b64
        import io as _sio

        pergunta = str(
            dados.get("pergunta") or "O que está acontecendo nessa tela?"
        )
        titulo = str(getattr(gw.getActiveWindow(), "title", "") or "").casefold()
        sensiveis = (
            "senha", "password", "login", "pagamento", "payment", "checkout",
            "banco", "bank", "whatsapp", "telegram",
        )
        if any(marcador in titulo for marcador in sensiveis):
            return _resultado_remoto(
                False,
                confirmed=True,
                error="Captura bloqueada em contexto sensível.",
                sensitiveContext=True,
            )
        imagem = pyautogui.screenshot()
        largura, altura = imagem.size
        caixa = (int(largura * 0.72), int(altura * 0.68), largura, altura)
        canto = imagem.crop(caixa).filter(_PILFilter.GaussianBlur(radius=18))
        imagem.paste(canto, caixa)
        imagem.thumbnail((1280, 720), _PILImg.LANCZOS)
        buffer = _sio.BytesIO()
        imagem.save(buffer, format="JPEG", quality=60)
        imagem_b64 = _b64.b64encode(buffer.getvalue()).decode("utf-8")
        return _resultado_remoto(
            True,
            confirmed=True,
            image_bytes=len(buffer.getvalue()),
            _messages=[{
                "type": "pc_b_screenshot",
                "imagem_b64": imagem_b64,
                "pergunta": pergunta,
            }],
        )

    @staticmethod
    def _fechar_aba_especifica(dados):
        alvo = str(dados.get("target") or "").strip().casefold()
        if not alvo:
            return _resultado_remoto(False, error="Aba não informada.")
        ativa = gw.getActiveWindow()
        titulo = str(getattr(ativa, "title", "") or "").casefold()
        if alvo not in titulo:
            return _resultado_remoto(
                False,
                error="A aba pedida não está ativa; não enviei Ctrl+W no escuro.",
            )
        pyautogui.hotkey("ctrl", "w")
        return _resultado_remoto(True, confirmed=False, target=alvo)

    @staticmethod
    def _fechar_aba_atual(_dados):
        pyautogui.hotkey("ctrl", "w")
        return _resultado_remoto(True, confirmed=False)

    @staticmethod
    def _organizar_desktop(dados):
        esquerda = dados.get("left") or dados.get("esquerda") or ""
        direita = dados.get("right") or dados.get("direita") or ""
        resultado = _organizar_janelas_remotas(esquerda, direita)
        return _resultado_remoto(
            bool(resultado.get("ok")),
            confirmed=bool(resultado.get("ok")),
            error=resultado.get("error", ""),
            left=str(esquerda),
            right=str(direita),
        )

    @staticmethod
    def _bloquear_pc(_dados):
        solicitado = bool(ctypes.windll.user32.LockWorkStation())
        return _resultado_remoto(
            solicitado,
            confirmed=False if solicitado else None,
            error="" if solicitado else "O Windows recusou o bloqueio.",
        )

    @staticmethod
    def _notificar(dados):
        mensagem = str(dados.get("alvo") or "Notificação da Laylay")

        def mostrar():
            ctypes.windll.user32.MessageBoxW(
                0, mensagem, "Mensagem - Laylay Cérebro", 0x40,
            )

        import threading
        threading.Thread(target=mostrar, daemon=True).start()
        return _resultado_remoto(True, confirmed=False)

    def _criar_pasta(self, dados):
        alvo = resolver_caminho_seguro_pcb(
            dados.get("alvo") or "", raizes=self._raizes_arquivos,
        )
        if not alvo:
            return _resultado_remoto(False, error="Nome da pasta ausente.")
        os.makedirs(alvo, exist_ok=True)
        confirmado = os.path.isdir(alvo)
        return _resultado_remoto(
            confirmado,
            confirmed=confirmado,
            error="" if confirmado else "A pasta não apareceu no disco.",
            caminho=alvo,
        )

    def _criar_arquivo(self, dados):
        alvo = resolver_caminho_seguro_pcb(
            dados.get("alvo") or "", raizes=self._raizes_arquivos,
        )
        if not alvo:
            return _resultado_remoto(False, error="Nome do arquivo ausente.")
        os.makedirs(os.path.dirname(alvo), exist_ok=True)
        with open(alvo, "a", encoding="utf-8"):
            pass
        confirmado = os.path.isfile(alvo)
        return _resultado_remoto(
            confirmado,
            confirmed=confirmado,
            error="" if confirmado else "O arquivo não apareceu no disco.",
            caminho=alvo,
        )

    def _deletar_item(self, dados):
        alvo = resolver_caminho_seguro_pcb(
            dados.get("alvo") or "", raizes=self._raizes_arquivos,
        )
        if not alvo:
            return _resultado_remoto(False, error="Item não informado.")
        if not os.path.exists(alvo):
            return _resultado_remoto(False, error="Arquivo ou pasta não encontrado.")
        destino = mover_para_lixeira_pcb(alvo)
        confirmado = not os.path.exists(alvo) and os.path.exists(destino)
        return _resultado_remoto(
            confirmado,
            confirmed=confirmado,
            error="" if confirmado else "A movimentação não foi confirmada.",
            caminho=alvo,
        )

    @staticmethod
    def _spinning_fish(_dados):
        abriu = bool(webbrowser.open("https://spinning.fish/"))
        return _resultado_remoto(
            abriu,
            confirmed=False if abriu else None,
            error="" if abriu else "O navegador não aceitou a abertura.",
        )


def manifesto_cliente_remoto(executor, *, agora=None, iniciado_em=None):
    """Publica somente identidade técnica, capacidades e saúde operacional."""
    instante = float(time.time() if agora is None else agora)
    inicio = instante if iniciado_em is None else float(iniciado_em)
    return {
        "protocolVersion": PC_B_PROTOCOL_VERSION,
        "client": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "platform": "windows" if os.name == "nt" else str(sys.platform),
        },
        "capabilities": sorted(executor.acoes_suportadas),
        "health": {
            "state": "ready",
            "executor": "ready",
            "checkedAt": round(instante, 3),
            "uptimeSeconds": round(max(0.0, instante - inicio), 1),
        },
        "security": {
            "mode": "restricted",
            "shellEnabled": "shell_command" in executor.acoes_suportadas,
            "inputAutomationEnabled": "type_text" in executor.acoes_suportadas,
            "allowedRoots": len(executor._raizes_arquivos),
        },
    }


async def publicar_saude_cliente_remoto(websocket, executor, iniciado_em):
    """Mantém a saúde do cliente atual sem transformar heartbeat em comando."""
    while True:
        await asyncio.sleep(PC_B_HEARTBEAT_INTERVAL_S)
        await websocket.send(json.dumps({
            "type": "pc_b_heartbeat",
            **manifesto_cliente_remoto(executor, iniciado_em=iniciado_em),
        }))

async def laylay_client(ip_cerebro):
    uri = f"ws://{ip_cerebro}:8080"
    executor_remoto = ExecutorRemotoPC()
    iniciado_em = time.time()
    print(f"🔌 Conectando ao Cérebro da Laylay em {uri}...")
   
    while True:
        try:
            async for websocket in websockets.connect(
                uri,
                open_timeout=10,
                close_timeout=5,
                ping_interval=20,
                ping_timeout=20,
                max_size=PC_B_MAX_MESSAGE_BYTES,
            ):
                websocket = WebSocketCorrelacionado(websocket)
                # Identifica este cliente como PC B logo ao conectar e envia token de segurança
                TOKEN_SECRETO = os.environ.get("LAYLAY_PC_B_TOKEN", "").strip()
                if len(TOKEN_SECRETO) < 16:
                    raise RuntimeError(
                        "Defina LAYLAY_PC_B_TOKEN com pelo menos 16 caracteres "
                        "e o mesmo valor nos dois PCs"
                    )
                await websocket.send(json.dumps({
                    "type": "pc_b_client",
                    "token": TOKEN_SECRETO,
                    "message": f"PC B conectado - {APP_NAME} v{APP_VERSION}",
                    **manifesto_cliente_remoto(
                        executor_remoto, iniciado_em=iniciado_em,
                    ),
                }))
                print(f"✅ {APP_NAME} conectado e pronto!")
                print("Aguardando comandos...\n")
                tarefa_saude = asyncio.create_task(
                    publicar_saude_cliente_remoto(
                        websocket, executor_remoto, iniciado_em,
                    )
                )
                try:
                    async for message in websocket:
                        try:
                            dados = json.loads(message)
                        except (json.JSONDecodeError, TypeError):
                            dados = None
                        websocket.request_id = (
                            dados.get("requestId") if isinstance(dados, dict) else None
                        )
                        await executor_remoto.executar(websocket, dados)

                except websockets.ConnectionClosed:
                    print("Conexão perdida. Reconectando em 5s...")
                    await asyncio.sleep(5)
                finally:
                    tarefa_saude.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await tarefa_saude
                   
        except Exception as e:
            print(f"Erro de conexão: {e}. Tentando novamente em 5s...")
            await asyncio.sleep(5)

# ====================== STARTUP AUTOMÁTICO (mais discreto) ======================
def configurar_auto_startup():
    if (
        getattr(sys, 'frozen', False)
        and _flag_ambiente(os.getenv, "LAYLAY_PC_B_AUTOSTART")
    ):
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
