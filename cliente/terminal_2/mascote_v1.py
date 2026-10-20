"""Rosto nativo da Laylay: apresentação local, sem acesso à mente ou executores.

O estado recebido descreve atividade/emoção. Animações, cursor e piscadas não
publicam eventos operacionais nem constituem confirmação de efeito.
"""

from __future__ import annotations

import math
import random
import time

from PySide6.QtCore import QEvent, QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import (
    QColor, QCursor, QLinearGradient, QPainter, QPainterPath, QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget


class MascoteLaylay(QWidget):
    """Mascote vetorial escalável com movimento subordinado à janela visível."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        tamanho: int = 112,
        reduzir_movimento: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("MascoteLaylayV1")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAccessibleName("Rosto da Laylay")
        self._tamanho = max(24, int(tamanho))
        self.setFixedSize(self._tamanho, round(self._tamanho * 104 / 112))
        self._atividade = "idle"
        self._emocao = "calma"
        self._conectado = True
        self._reduzir_movimento = bool(reduzir_movimento)
        self._encerrado = False
        self._olhar_x = 0.0
        self._olhar_y = 0.0
        self._fase = 0.0
        self._abertura = 1.0
        self._inicio_piscada: float | None = None
        self._proxima_piscada = 0.0
        self._ultimo_frame = time.monotonic()
        self._janela_observada: QWidget | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._animar)
        # Ativação é entregue antes de isActiveWindow refletir o novo estado.
        # O timer filho de disparo único aguarda a conclusão do evento Qt.
        self._sincronizador = QTimer(self)
        self._sincronizador.setSingleShot(True)
        self._sincronizador.timeout.connect(self._sincronizar_animacao)
        self.definir_estado("idle")

    def sizeHint(self) -> QSize:
        return QSize(self._tamanho, round(self._tamanho * 104 / 112))

    @property
    def posicao_olhar(self) -> tuple[float, float]:
        """Deslocamento visual em coordenadas proporcionais ao desenho 112×104."""
        return self._olhar_x, self._olhar_y

    @property
    def piscando(self) -> bool:
        return self._abertura < 0.8

    @property
    def animacao_ativa(self) -> bool:
        return self._timer.isActive()

    def definir_estado(
        self, atividade: str, emocao: str = "calma", conectado: bool = True,
    ) -> None:
        self._atividade = str(atividade or "idle").strip().casefold()
        self._emocao = str(emocao or "calma").strip().casefold()
        self._conectado = bool(conectado)
        self.setAccessibleDescription(
            f"Atividade: {self._atividade}. Emoção: {self._emocao}. "
            + ("Conectada." if self._conectado else "Sem conexão.")
        )
        self.update()

    def definir_reduzir_movimento(self, reduzir: bool) -> None:
        self._reduzir_movimento = bool(reduzir)
        self._sincronizar_animacao()

    def encerrar(self) -> None:
        """Finaliza a animação; chamadas repetidas são seguras."""
        self._encerrado = True
        self._parar()
        if self._janela_observada is not None:
            self._janela_observada.removeEventFilter(self)
            self._janela_observada = None

    def _pode_animar(self) -> bool:
        janela = self.window()
        return (
            not self._encerrado
            and not self._reduzir_movimento
            and self.isVisible()
            and janela.isVisible()
            and not janela.isMinimized()
            and janela.isActiveWindow()
        )

    def _parar(self) -> None:
        self._timer.stop()
        self._sincronizador.stop()
        self._olhar_x = self._olhar_y = self._fase = 0.0
        self._abertura = 1.0
        self._inicio_piscada = None
        self.update()

    def _sincronizar_animacao(self) -> None:
        if not self._pode_animar():
            self._parar()
        elif not self._timer.isActive():
            agora = time.monotonic()
            self._ultimo_frame = agora
            self._proxima_piscada = agora + random.uniform(2.6, 5.2)
            self._timer.start()

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        janela = self.window()
        if janela is not self._janela_observada:
            if self._janela_observada is not None:
                self._janela_observada.removeEventFilter(self)
            self._janela_observada = janela
            janela.installEventFilter(self)
        if not self._encerrado:
            self._sincronizador.start(0)

    def hideEvent(self, evento) -> None:
        self._parar()
        super().hideEvent(evento)

    def closeEvent(self, evento) -> None:
        self.encerrar()
        super().closeEvent(evento)

    def eventFilter(self, observado, evento) -> bool:
        if observado is self._janela_observada:
            tipo = evento.type()
            if tipo in (QEvent.Type.WindowDeactivate, QEvent.Type.Hide):
                self._parar()
            elif tipo in (QEvent.Type.WindowActivate, QEvent.Type.WindowStateChange):
                if not self._encerrado:
                    self._sincronizador.start(0)
            elif tipo == QEvent.Type.Close:
                self._parar()
        return super().eventFilter(observado, evento)

    def _animar(self) -> None:
        if not self._pode_animar():
            self._parar()
            return
        agora = time.monotonic()
        dt = min(0.1, max(0.0, agora - self._ultimo_frame))
        self._ultimo_frame = agora
        self._fase += dt
        cursor = self.mapFromGlobal(QCursor.pos())
        escala = max(0.01, min(self.width() / 112, self.height() / 104))
        dx = (cursor.x() - self.width() / 2) / escala
        dy = (cursor.y() - self.height() / 2) / escala
        distancia = math.hypot(dx, dy)
        fator = min(5.0 / max(distancia, 0.001), 0.036)
        suavizacao = 1.0 - math.exp(-dt * 9.0)
        self._olhar_x += (dx * fator - self._olhar_x) * suavizacao
        self._olhar_y += (dy * fator - self._olhar_y) * suavizacao
        if self._inicio_piscada is None and agora >= self._proxima_piscada:
            self._inicio_piscada = agora
        if self._inicio_piscada is not None:
            progresso = (agora - self._inicio_piscada) / 0.19
            self._abertura = max(0.07, abs(2.0 * progresso - 1.0))
            if progresso >= 1.0:
                self._abertura = 1.0
                self._inicio_piscada = None
                self._proxima_piscada = agora + random.uniform(2.6, 5.2)
        self.update()

    def paintEvent(self, evento) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        escala = min(self.width() / 112, self.height() / 104)
        p.translate(self.width() / 2, self.height() / 2)
        p.scale(escala, escala)
        animado = self.animacao_ativa
        flutuar = math.sin(self._fase * 1.8) * 0.85 if animado else 0.0
        p.translate(0, flutuar)
        p.rotate(-3)
        p.translate(-56, -52)

        corpo = QPainterPath()
        corpo.moveTo(43, 8)
        corpo.lineTo(71, 8)
        corpo.cubicTo(93, 8, 104, 21, 104, 42)
        corpo.lineTo(104, 65)
        corpo.cubicTo(104, 86, 92, 97, 72, 97)
        corpo.lineTo(40, 97)
        corpo.cubicTo(19, 97, 8, 85, 8, 65)
        corpo.lineTo(8, 42)
        corpo.cubicTo(8, 21, 20, 8, 43, 8)
        corpo.closeSubpath()

        if self._conectado:
            cores = ("#ead7ff", "#c5a4ee", "#a47cd4")
            if self._atividade in {"listening", "ouvindo"}:
                cores = ("#e4e3ff", "#bbadee", "#8fa4dd")
            elif self._atividade in {"error", "warning"}:
                cores = ("#f2dcf0", "#d6accc", "#b58aaa")
        else:
            cores = ("#d0c9dc", "#aba0bb", "#83758f")
        gradiente = QLinearGradient(20, 12, 95, 101)
        for posicao, cor in zip((0.0, 0.48, 1.0), cores):
            gradiente.setColorAt(posicao, QColor(cor))
        p.setPen(QPen(QColor("#e1c5ff" if self._conectado else "#aaa0b6"), 0.75))
        p.setBrush(gradiente)
        p.drawPath(corpo)
        p.save()
        p.setClipPath(corpo)
        luz = QRadialGradient(QPointF(30, 19), 80)
        luz.setColorAt(0.0, QColor(255, 255, 255, 38))
        luz.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillRect(QRectF(8, 8, 96, 89), luz)
        p.restore()

        p.save()
        p.translate(self._olhar_x, self._olhar_y)
        elevacao = -1.1 if self._emocao in {"curiosa", "curiosidade", "animada"} else 0
        altura = 11.4
        if self._atividade in {"listening", "ouvindo"}:
            altura = 13.0
        elif self._emocao in {"triste", "cansada", "sonolenta"}:
            altura = 8.0
        olhos = QColor("#4d315f" if self._conectado else "#5b5063")
        p.setPen(Qt.PenStyle.NoPen)
        for x in (38.5, 73.5):
            y = 51.0 + elevacao
            altura_olho = altura
            if self._atividade in {"thinking", "pensando"} and x > 56:
                altura_olho *= 0.78
            h = max(1.25, altura_olho * self._abertura)
            p.setBrush(olhos)
            p.drawEllipse(QRectF(x - 3.3, y - h / 2, 6.6, h))
            if self._abertura > 0.5:
                p.setBrush(QColor(255, 244, 255, 200))
                p.drawEllipse(QRectF(x - 1.95, y - h / 2 + 1.6, 1.75, 2.6 * self._abertura))
                p.setBrush(QColor(255, 244, 255, 55))
                p.drawEllipse(QRectF(x + 0.45, y + h / 2 - 2.5, 1.0, 1.1))
        if self._atividade in {"thinking", "pensando"}:
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor("#856299"), 0.85, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            sobrancelha = QPainterPath(QPointF(35.4, 40.0))
            sobrancelha.quadTo(38.8, 37.5, 42.0, 39.8)
            p.drawPath(sobrancelha)
        p.restore()

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor("#745283"), 1.1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        boca = QPainterPath()
        if not self._conectado or self._atividade in {"reconnecting", "error"}:
            boca.moveTo(53, 66)
            boca.quadTo(56, 65, 59, 66)
        elif self._atividade in {"speaking", "falando"}:
            pulso = math.sin(self._fase * 11) if animado else 0
            p.setBrush(QColor("#825d95"))
            p.drawEllipse(QRectF(53.2, 64, 5.6, 3.0 + (pulso + 1) * 1.5))
        elif self._emocao in {"triste", "preocupada"}:
            boca.moveTo(52.5, 67)
            boca.quadTo(56, 64, 59.5, 67)
        else:
            boca.moveTo(52, 65)
            boca.cubicTo(54, 67.8, 58, 67.8, 60, 65)
        p.drawPath(boca)
        p.end()
