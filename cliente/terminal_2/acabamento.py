"""Acabamento visual do Terminal 3 sem criar comportamento de domínio."""

from __future__ import annotations

from collections import deque
from pathlib import Path
import re

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import QSizePolicy, QWidget


PASTA_ICONES = Path(__file__).resolve().parent / "assets" / "icons"


def variantes_capa_youtube(url: str) -> tuple[str, ...]:
    """Gera fallbacks seguros sem aceitar uma URL arbitrária da rede."""
    encontrado = re.fullmatch(
        r"https://i\.ytimg\.com/vi/([A-Za-z0-9_-]{11})/"
        r"(?:maxresdefault|hqdefault|mqdefault|0)\.jpg",
        str(url or "").strip(),
    )
    if not encontrado:
        return ()
    video_id = encontrado.group(1)
    nomes = ("maxresdefault", "hqdefault", "mqdefault", "0")
    primario = str(url).rsplit("/", 1)[-1].removesuffix(".jpg")
    ordem = (primario, *(nome for nome in nomes if nome != primario))
    return tuple(
        f"https://i.ytimg.com/vi/{video_id}/{nome}.jpg" for nome in ordem
    )


def icone_terminal(nome: str) -> QIcon:
    """Carrega somente SVGs locais e retorna um ícone vazio se ausente."""
    caminho = PASTA_ICONES / f"{str(nome or '').strip()}.svg"
    return QIcon(str(caminho)) if caminho.is_file() else QIcon()


def tamanho_icone() -> QSize:
    return QSize(19, 19)


class FormaOndaMicrofone(QWidget):
    """Waveform efêmero alimentado pelo RMS observado no ouvido canônico."""

    def __init__(self, *, reduzir_movimento: bool = False) -> None:
        super().__init__()
        self.setObjectName("microphoneWaveform")
        self.setMinimumHeight(34)
        self.setMaximumHeight(44)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._alvo = 0.0
        self._nivel = 0.0
        self._ativo = False
        self._reduzir_movimento = bool(reduzir_movimento)
        self._fase = 0
        self._amostras: deque[float] = deque([0.0] * 31, maxlen=31)
        self._timer = QTimer(self)
        self._timer.setInterval(45)
        self._timer.timeout.connect(self._avancar)
        self._timer.start()
        self.setAccessibleName("Nível do microfone")
        self.setToolTip("Nível observado pelo microfone da Laylay; não grava áudio na interface")

    def definir_nivel(self, nivel: object, *, ativo: bool) -> None:
        try:
            valor = float(nivel)
        except (TypeError, ValueError):
            valor = 0.0
        self._alvo = max(0.0, min(1.0, valor)) if ativo else 0.0
        self._ativo = bool(ativo)

    def _avancar(self) -> None:
        if self._reduzir_movimento:
            self._nivel = self._alvo
            self._amostras.clear()
            self._amostras.extend([self._nivel] * 31)
            self.update()
            return
        self._nivel += (self._alvo - self._nivel) * 0.34
        if abs(self._nivel) < 0.003 and self._alvo == 0:
            self._nivel = 0.0
        self._fase = (self._fase + 1) % 31
        self._amostras.append(self._nivel)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        centro = self.height() / 2.0
        largura = max(1.0, self.width() - 8.0)
        passo = largura / max(1, len(self._amostras) - 1)
        cor_base = QColor("#63313B" if not self._ativo else "#FF536D")
        painter.setPen(QPen(cor_base, 1.3, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(4, int(centro), self.width() - 4, int(centro))
        for indice, amostra in enumerate(self._amostras):
            distancia = abs(indice - (len(self._amostras) - 1) / 2)
            envelope = max(0.22, 1.0 - distancia / 18.0)
            variacao = (0.55 + ((indice * 7 + self._fase) % 9) / 20.0)
            altura = max(1.2, min(self.height() * 0.42, amostra * 24.0 * envelope * variacao))
            x = 4.0 + indice * passo
            painter.drawLine(QRectF(x, centro - altura, 0.1, altura * 2).topLeft(),
                             QRectF(x, centro - altura, 0.1, altura * 2).bottomLeft())


class CapaMusicaGenerica(QWidget):
    """Thumbnail observada, com disco decorativo somente como fallback."""

    def __init__(self, tamanho: int = 68) -> None:
        super().__init__()
        self.setFixedSize(tamanho, tamanho)
        self._titulo = ""
        self._artwork_url = ""
        self._pixmap = QPixmap()
        self._candidatas: tuple[str, ...] = ()
        self._indice_candidata = -1
        self._rede = QNetworkAccessManager(self)
        self._rede.finished.connect(self._imagem_recebida)
        self.setAccessibleName("Thumbnail da música")

    def definir_titulo(self, titulo: str) -> None:
        self._titulo = str(titulo or "")
        self.update()

    def carregar(self, url: str) -> None:
        """Carrega apenas a URL já validada pela ponte do dashboard."""
        url = str(url or "").strip()
        if url == self._artwork_url:
            return
        self._artwork_url = url
        self._pixmap = QPixmap()
        self._candidatas = variantes_capa_youtube(url)
        self._indice_candidata = -1
        self.update()
        self._tentar_proxima_capa()

    def _tentar_proxima_capa(self) -> None:
        self._indice_candidata += 1
        if self._indice_candidata >= len(self._candidatas):
            return
        self._rede.get(QNetworkRequest(QUrl(
            self._candidatas[self._indice_candidata],
        )))

    def _imagem_recebida(self, resposta: QNetworkReply) -> None:
        try:
            esperado = (
                self._candidatas[self._indice_candidata]
                if 0 <= self._indice_candidata < len(self._candidatas) else ""
            )
            if resposta.url().toString() != esperado:
                return
            if resposta.error() != QNetworkReply.NoError:
                self._tentar_proxima_capa()
                return
            pixmap = QPixmap()
            if pixmap.loadFromData(bytes(resposta.readAll())):
                self._pixmap = pixmap
                self.update()
            else:
                self._tentar_proxima_capa()
        finally:
            resposta.deleteLater()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        retangulo = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        if not self._pixmap.isNull():
            caminho = QPainterPath()
            caminho.addRoundedRect(retangulo, 9, 9)
            painter.setClipPath(caminho)
            imagem = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            x = (self.width() - imagem.width()) // 2
            y = (self.height() - imagem.height()) // 2
            painter.drawPixmap(x, y, imagem)
            painter.setClipping(False)
            painter.setPen(QPen(QColor("#55313B"), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(retangulo, 9, 9)
            return
        painter.setPen(QPen(QColor("#55313B"), 1))
        painter.setBrush(QColor("#251A20"))
        painter.drawRoundedRect(retangulo, 9, 9)
        painter.setPen(QPen(QColor("#FF5C73"), 2.2, Qt.SolidLine, Qt.RoundCap))
        centro = self.width() / 2
        painter.drawEllipse(QRectF(centro - 17, centro - 17, 34, 34))
        painter.drawEllipse(QRectF(centro - 4, centro - 4, 8, 8))
        painter.drawLine(int(centro + 15), int(centro - 15), int(centro + 24), int(centro - 23))
