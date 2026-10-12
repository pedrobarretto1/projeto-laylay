"""Geometria efêmera enviada pela extensão local; nunca pela mente da Laylay."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from time import monotonic

from PySide6.QtCore import QObject, QRect, QTimer, Signal
from PySide6.QtNetwork import QHostAddress
from PySide6.QtWebSockets import QWebSocketServer


@dataclass(frozen=True)
class FonteVideo:
    chave: str
    titulo: str
    rotulo: str
    reproduzindo: bool
    video: tuple[float, float, float, float]
    viewport: tuple[float, float, float, float, float, float]
    recebido_em: float


def decodificar_fontes(texto: str, conexao: str, agora: float) -> list[FonteVideo]:
    if len(texto) > 32_768:
        raise ValueError("Mensagem muito grande")
    dados = json.loads(texto)
    if dados.get("type") != "videos" or not isinstance(dados.get("videos"), list):
        raise ValueError("Protocolo desconhecido")
    titulo = str(dados.get("title") or "").strip()[:240]
    if not titulo:
        raise ValueError("Sem identidade da janela")
    viewport = dados.get("viewport") or {}
    valores = tuple(float(viewport[nome]) for nome in (
        "outerWidth", "outerHeight", "innerWidth", "innerHeight", "dpr", "zoom"
    ))
    if not all(math.isfinite(n) and 0 < n < 32768 for n in valores) or not .25 <= valores[5] <= 5:
        raise ValueError("Viewport inválido")
    fontes = []
    for video in dados["videos"][:20]:
        retangulo = tuple(float(video[n]) for n in ("x", "y", "width", "height"))
        x, y, w, h = retangulo
        if not all(math.isfinite(n) for n in retangulo) or x < 0 or y < 0 or w < 1 or h < 1:
            continue
        if x + w > valores[2] + 1 or y + h > valores[3] + 1:
            continue
        identidade = str(video.get("id") or "")[:160]
        if not identidade:
            continue
        chave = f"{conexao}:{dados.get('windowId')}:{dados.get('tabId')}:{identidade}"
        fontes.append(FonteVideo(chave, titulo, str(video.get("label") or "Vídeo")[:100],
                                 video.get("playing") is True, retangulo, valores, agora))
    return fontes


def medir_margens_nativas(titulo: str) -> tuple[int, int, int, int]:
    """Desconta bordas invisíveis do Windows que o Qt não inclui no frame."""
    import ctypes
    from ctypes import wintypes
    import sys
    if sys.platform != "win32":
        return (0, 0, 0, 0)
    user32, dwm = ctypes.windll.user32, ctypes.windll.dwmapi
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    dwm.DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    encontrados = []

    def verificar(hwnd, _param):
        buffer = ctypes.create_unicode_buffer(user32.GetWindowTextLengthW(hwnd) + 1)
        user32.GetWindowTextW(hwnd, buffer, len(buffer))
        if buffer.value == titulo:
            encontrados.append(hwnd)
        return True

    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.EnumWindows(callback_type(verificar), 0)
    if len(encontrados) != 1:
        raise RuntimeError("Janela nativa ambígua ou fechada")
    janela, quadro = wintypes.RECT(), wintypes.RECT()
    if not user32.GetWindowRect(encontrados[0], ctypes.byref(janela)) or dwm.DwmGetWindowAttribute(
        encontrados[0], 9, ctypes.byref(quadro), ctypes.sizeof(quadro)
    ) != 0:
        raise RuntimeError("Limites nativos da janela indisponíveis")
    return (quadro.left - janela.left, quadro.top - janela.top,
            janela.right - quadro.right, janela.bottom - quadro.bottom)


def calcular_recorte(fonte: FonteVideo, largura: int, altura: int, agora: float,
                     margens: tuple[int, int, int, int] = (0, 0, 0, 0)) -> QRect:
    """Converte CSS/zoom/DPI para a janela capturada, sem fallback de tela inteira."""
    if agora - fonte.recebido_em > .8 or agora < fonte.recebido_em:
        return QRect()
    ow, oh, iw, ih, dpr, zoom = fonte.viewport
    escala_dpi = dpr / zoom
    ml, mt, mr, mb = margens
    if abs(largura - (ow * escala_dpi - ml - mr)) > 2 or abs(altura - (oh * escala_dpi - mt - mb)) > 2:
        return QRect()  # Resize nativo chegou antes da geometria DOM correspondente.
    borda = max(0, (ow - iw * zoom) / 2)
    topo = max(0, oh - ih * zoom - borda)
    x, y, w, h = fonte.video
    left, top = math.ceil((borda + x * zoom) * escala_dpi - ml), math.ceil((topo + y * zoom) * escala_dpi - mt)
    right, bottom = math.floor((borda + (x + w) * zoom) * escala_dpi - ml), math.floor((topo + (y + h) * zoom) * escala_dpi - mt)
    return QRect(left, top, right - left, bottom - top).intersected(QRect(0, 0, largura, altura))


class FontesStreaming(QObject):
    alteradas = Signal()
    falha = Signal(str)

    def __init__(self, parent: QObject | None = None, *, porta: int = 19769) -> None:
        super().__init__(parent)
        self.fontes: dict[str, FonteVideo] = {}
        self._sockets: list = []
        self._confirmadas: set[str] = set()
        self._encerrado = False
        self._servidor = QWebSocketServer("Laylay Streaming Local", QWebSocketServer.NonSecureMode, self)
        self._servidor.newConnection.connect(self._conectar)
        self.disponivel = self._servidor.listen(QHostAddress(QHostAddress.LocalHost), porta)
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._expirar)
        self._timer.start()

    @property
    def conectada(self) -> bool:
        return bool(self._confirmadas)

    def _conectar(self) -> None:
        socket = self._servidor.nextPendingConnection()
        if not re.fullmatch(r"chrome-extension://[a-p]{32}", socket.origin()):
            socket.close()
            socket.deleteLater()
            return
        self._sockets.append(socket)
        conexao = str(id(socket))
        socket.textMessageReceived.connect(lambda texto: self._receber(conexao, texto))
        socket.disconnected.connect(lambda: self._desconectar(socket, conexao))

    def _receber(self, conexao: str, texto: str) -> None:
        try:
            if len(texto) > 32_768:
                return
            dados = json.loads(texto)
            if dados.get("type") == "streaming_hello" and dados.get("version") == 1:
                if conexao not in self._confirmadas:
                    self._confirmadas.add(conexao)
                    self.alteradas.emit()
                return
            novas = decodificar_fontes(texto, conexao, monotonic())
        except (ValueError, KeyError, TypeError, AttributeError, OverflowError):
            return
        # Cada snapshot substitui somente o tab que o produziu; os demais expiram.
        self._confirmadas.add(conexao)
        prefixo = f"{conexao}:{dados.get('windowId')}:{dados.get('tabId')}:"
        self.fontes = {chave: fonte for chave, fonte in self.fontes.items() if not chave.startswith(prefixo)}
        self.fontes.update({fonte.chave: fonte for fonte in novas})
        self.alteradas.emit()

    def _expirar(self) -> None:
        antigas = [chave for chave, fonte in self.fontes.items() if monotonic() - fonte.recebido_em > .8]
        if antigas:
            for chave in antigas:
                self.fontes.pop(chave)
            self.alteradas.emit()

    def _desconectar(self, socket: object, conexao: str) -> None:
        if socket in self._sockets:
            self._sockets.remove(socket)
        self._confirmadas.discard(conexao)
        self.fontes = {chave: fonte for chave, fonte in self.fontes.items() if not chave.startswith(conexao + ":")}
        self.alteradas.emit()
        socket.deleteLater()

    def encerrar(self) -> None:
        if self._encerrado:
            return
        self._encerrado = True
        self._timer.stop()
        self._servidor.newConnection.disconnect(self._conectar)
        self._servidor.close()
        for socket in list(self._sockets):
            # A desconexão pode ser emitida durante a destruição dos filhos Qt.
            # Remova as closures antes de invalidar o QObject que elas usam.
            socket.textMessageReceived.disconnect()
            socket.disconnected.disconnect()
            socket.close()
            socket.deleteLater()
        self._sockets.clear()
        self.fontes.clear()
        self._confirmadas.clear()
