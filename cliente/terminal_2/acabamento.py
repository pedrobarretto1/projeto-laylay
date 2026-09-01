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


def definir_propriedades_visuais(widget: QWidget, **propriedades: object) -> bool:
    """Recalcula QSS somente quando uma propriedade dinâmica realmente muda."""
    alteradas = {
        nome: valor
        for nome, valor in propriedades.items()
        if widget.property(nome) != valor
    }
    if not alteradas:
        return False
    for nome, valor in alteradas.items():
        widget.setProperty(nome, valor)
    estilo = widget.style()
    estilo.unpolish(widget)
    estilo.polish(widget)
    widget.update()
    return True


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
        self.setAccessibleName("Nível do microfone")
        self.setToolTip("Nível observado pelo microfone da Laylay; não grava áudio na interface")

    def definir_nivel(self, nivel: object, *, ativo: bool) -> None:
        try:
            valor = float(nivel)
        except (TypeError, ValueError):
            valor = 0.0
        self._alvo = max(0.0, min(1.0, valor)) if ativo else 0.0
        self._ativo = bool(ativo)
        if self._reduzir_movimento:
            self._nivel = self._alvo
            self._amostras.clear()
            self._amostras.extend([self._nivel] * 31)
        self._sincronizar_timer()
        self.update()

    def _sincronizar_timer(self) -> None:
        animando = self._alvo > 0.001 or self._nivel > 0.003
        deve_animar = self.isVisible() and animando and not self._reduzir_movimento
        if deve_animar and not self._timer.isActive():
            self._timer.start()
        elif not deve_animar and self._timer.isActive():
            self._timer.stop()

    def _avancar(self) -> None:
        if not self.isVisible():
            self._timer.stop()
            return
        if self._reduzir_movimento:
            self._nivel = self._alvo
            self._amostras.clear()
            self._amostras.extend([self._nivel] * 31)
            self.update()
            self._timer.stop()
            return
        self._nivel += (self._alvo - self._nivel) * 0.34
        if abs(self._nivel) < 0.003 and self._alvo == 0:
            self._nivel = 0.0
        self._fase = (self._fase + 1) % 31
        self._amostras.append(self._nivel)
        self.update()
        if self._nivel == 0.0 and self._alvo == 0.0:
            self._timer.stop()

    def showEvent(self, event) -> None:  # noqa: N802 - contrato Qt
        super().showEvent(event)
        self._sincronizar_timer()

    def hideEvent(self, event) -> None:  # noqa: N802 - contrato Qt
        self._timer.stop()
        super().hideEvent(event)

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
        personalizado = re.fullmatch(
            r"laylay-playlist-artwork://([a-f0-9]{24}\.png)", url,
        )
        if personalizado:
            caminho = Path.home() / ".laylay" / "playlist_artwork" / personalizado.group(1)
            pixmap = QPixmap(str(caminho))
            if not pixmap.isNull():
                self._pixmap = pixmap
        self.update()
        if self._pixmap.isNull():
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
        lado = max(1.0, min(retangulo.width(), retangulo.height()))
        raio = max(2.0, min(9.0, lado * 0.14))
        if not self._pixmap.isNull():
            caminho = QPainterPath()
            caminho.addRoundedRect(retangulo, raio, raio)
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
            painter.drawRoundedRect(retangulo, raio, raio)
            return
        painter.setPen(QPen(QColor("#55313B"), 1))
        painter.setBrush(QColor("#251A20"))
        painter.drawRoundedRect(retangulo, raio, raio)
        espessura = max(1.1, min(2.2, lado * 0.052))
        painter.setPen(QPen(QColor("#FF5C73"), espessura, Qt.SolidLine, Qt.RoundCap))
        centro_x = self.width() / 2.0
        centro_y = self.height() / 2.0
        raio_disco = lado * 0.27
        raio_centro = max(1.5, lado * 0.065)
        painter.drawEllipse(QRectF(
            centro_x - raio_disco, centro_y - raio_disco,
            raio_disco * 2.0, raio_disco * 2.0,
        ))
        painter.drawEllipse(QRectF(
            centro_x - raio_centro, centro_y - raio_centro,
            raio_centro * 2.0, raio_centro * 2.0,
        ))
        haste_inicio = raio_disco * 0.82
        haste_fim = min(lado * 0.43, raio_disco * 1.42)
        painter.drawLine(
            int(centro_x + haste_inicio), int(centro_y - haste_inicio),
            int(centro_x + haste_fim), int(centro_y - haste_fim),
        )
