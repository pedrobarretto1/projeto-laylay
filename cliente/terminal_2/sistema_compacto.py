"""Card compacto e canônico de telemetria do Terminal 3.0.

O componente recebe apenas a projeção pública e sanitizada do dashboard. Ele
não coleta telemetria, não cria timers e não executa ações: sua única função é
apresentar, com o mesmo vocabulário visual, o estado já observado pela mente.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


_METRICAS = (
    ("cpu", "cpu_percent", "CPU", "cpu"),
    ("ram", "ram_percent", "RAM", "ram"),
    ("gpu", "gpu_percent", "GPU", "gpu"),
    ("vram", "vram_percent", "VRAM", "vram"),
    ("disk", "disk_percent", "Disco", "disk"),
    ("network", "network_percent", "Rede", "network"),
    ("temperature", "temperature_c", "Temp.", "temperature"),
)

_ALIAS_HOME = {
    "cpu": "cpu",
    "ram": "ram",
    "gpu": "gpu",
    "vram": "vram",
    "disco": "disk",
    "rede": "network",
    "temperatura": "temperature",
}


def _bloco_sistema(retrato: Mapping[str, object] | object) -> Mapping[str, object]:
    if not isinstance(retrato, Mapping):
        return {}
    sistema = retrato.get("system")
    return sistema if isinstance(sistema, Mapping) else retrato


def _numero_metrica(metrica: object) -> float | None:
    if not isinstance(metrica, Mapping) or metrica.get("value") is None:
        return None
    try:
        return float(metrica["value"])
    except (TypeError, ValueError):
        return None


def _texto_metrica(
    metrica: object,
    *,
    uptime: bool = False,
    unidade_padrao: str = "",
) -> str:
    numero = _numero_metrica(metrica)
    if numero is None or not isinstance(metrica, Mapping):
        return "—"
    if uptime:
        total = max(0, int(numero))
        dias, resto = divmod(total, 86_400)
        horas, resto = divmod(resto, 3_600)
        minutos = resto // 60
        texto = f"{dias}d {horas}h" if dias else f"{horas}h {minutos}m"
    else:
        unidade = str(metrica.get("unit") or unidade_padrao)
        valor = str(int(numero)) if numero.is_integer() else f"{numero:.1f}".replace(".", ",")
        texto = f"{valor}{unidade}"
    if str(metrica.get("freshness") or "") == "stale":
        texto += " · antigo"
    return texto


class GraficoSistemaCompacto(QWidget):
    """Sparkline leve que também preserva a API mínima das barras antigas."""

    CORES = {
        "cpu": "#EA4F67",
        "ram": "#E38E31",
        "gpu": "#63C878",
        "vram": "#A65BE0",
        "disk": "#58A1E3",
        "network": "#43BDCA",
        "temperature": "#E49B43",
    }

    def __init__(self, tom: str, *, object_name_legado: str = "") -> None:
        super().__init__()
        self._tom = tom if tom in self.CORES else "cpu"
        self._valores: tuple[float, ...] = ()
        self._valor = 0
        self.setObjectName(object_name_legado or "compactSystemGraph")
        self.setProperty("compactSystemGraph", True)
        self.setProperty("metricTone", self._tom)
        self.setProperty("available", False)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumWidth(58)
        self.setFixedHeight(18)

    def definir(self, valores: object) -> None:
        limpos: list[float] = []
        for valor in tuple(valores or ())[-24:]:
            try:
                limpos.append(max(0.0, min(100.0, float(valor))))
            except (TypeError, ValueError):
                continue
        self._valores = tuple(limpos)
        self.update()

    @property
    def valores(self) -> tuple[float, ...]:
        return self._valores

    # API de compatibilidade com QProgressBar usada pelos consumidores antigos.
    def setRange(self, _minimo: int, _maximo: int) -> None:  # noqa: N802
        return

    def setTextVisible(self, _visivel: bool) -> None:  # noqa: N802
        return

    def setValue(self, valor: int) -> None:  # noqa: N802
        self._valor = max(0, min(100, int(valor)))

    def value(self) -> int:
        return self._valor

    def setText(self, texto: str) -> None:  # noqa: N802
        if str(texto or "").strip() == "—":
            self._valores = ()
            self.update()

    def text(self) -> str:
        return "" if self._valores else "—"

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        area = QRectF(self.rect()).adjusted(1.0, 3.0, -1.0, -3.0)
        if area.width() <= 2 or area.height() <= 2:
            return

        painter.setPen(QPen(QColor("#2A323A"), 1))
        painter.drawLine(area.bottomLeft(), area.bottomRight())
        if not self._valores:
            return

        cor = QColor(self.CORES[self._tom])
        if self._tom in {"ram", "vram"}:
            passo = area.width() / max(1, len(self._valores))
            largura = max(1.4, min(3.0, passo * 0.64))
            gradiente = QLinearGradient(0, area.top(), 0, area.bottom())
            topo, base = QColor(cor), QColor(cor)
            topo.setAlpha(230)
            base.setAlpha(80)
            gradiente.setColorAt(0.0, topo)
            gradiente.setColorAt(1.0, base)
            painter.setPen(Qt.NoPen)
            painter.setBrush(gradiente)
            for indice, valor in enumerate(self._valores):
                altura = max(1.0, valor / 100.0 * area.height())
                x = area.left() + indice * passo + (passo - largura) / 2
                painter.drawRect(QRectF(x, area.bottom() - altura, largura, altura))
            return

        passo = area.width() / max(1, len(self._valores) - 1)
        pontos = [
            QPointF(
                area.left() + indice * passo,
                area.bottom() - valor / 100.0 * area.height(),
            )
            for indice, valor in enumerate(self._valores)
        ]
        if len(pontos) == 1:
            pontos.insert(0, QPointF(area.left(), pontos[0].y()))
        caminho = QPainterPath(pontos[0])
        for ponto in pontos[1:]:
            caminho.lineTo(ponto)
        preenchimento = QPainterPath(caminho)
        preenchimento.lineTo(pontos[-1].x(), area.bottom())
        preenchimento.lineTo(pontos[0].x(), area.bottom())
        preenchimento.closeSubpath()
        gradiente = QLinearGradient(0, area.top(), 0, area.bottom())
        topo, base = QColor(cor), QColor(cor)
        topo.setAlpha(48)
        base.setAlpha(2)
        gradiente.setColorAt(0.0, topo)
        gradiente.setColorAt(1.0, base)
        painter.fillPath(preenchimento, gradiente)
        painter.setPen(QPen(cor, 1.25))
        painter.drawPath(caminho)


class LinhaSistemaCompacta(QFrame):
    def __init__(self, titulo: str, tom: str, *, object_name_legado: str = "") -> None:
        super().__init__()
        self.setObjectName("compactSystemMetric")
        self.setProperty("metricTone", tom)
        self.setProperty("state", "unavailable")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        self.nome = QLabel(titulo)
        self.nome.setObjectName("compactSystemMetricName")
        self.valor = QLabel("—")
        self.valor.setObjectName("compactSystemMetricValue")
        self.valor.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.valor.setMinimumWidth(52)
        self.grafico = GraficoSistemaCompacto(
            tom,
            object_name_legado=object_name_legado,
        )
        layout.addWidget(self.nome)
        layout.addStretch(1)
        layout.addWidget(self.valor)
        layout.addWidget(self.grafico, 1)


class CardSistemaCompacto(QFrame):
    """Projeção universal do sistema para os rails de Início, Música e Sistema."""

    def __init__(self, *, legado: str = "") -> None:
        super().__init__()
        self.setObjectName("compactSystemCard")
        self.setProperty("legacyConsumer", legado or "system")
        self.setMinimumWidth(250)
        self.setMaximumWidth(310)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(11, 9, 11, 9)
        layout.setSpacing(1)

        cabecalho = QHBoxLayout()
        cabecalho.setContentsMargins(0, 0, 0, 2)
        self.titulo = QLabel("Sistema")
        self.titulo.setObjectName("compactSystemTitle")
        self.subtitulo = QLabel("tempo real")
        self.subtitulo.setObjectName("compactSystemHint")
        self.subtitulo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        cabecalho.addWidget(self.titulo)
        cabecalho.addStretch()
        cabecalho.addWidget(self.subtitulo)
        layout.addLayout(cabecalho)

        object_name = {
            "inicio": "railSystemProgress",
            "musica": "musicSystemBar",
        }.get(legado, "compactSystemGraph")
        self.linhas: dict[str, LinhaSistemaCompacta] = {}
        self._historico = {
            chave: deque(maxlen=24)
            for chave, _campo, _titulo, _tom in _METRICAS
        }
        self._assinaturas: dict[str, tuple[object, float] | None] = {
            chave: None for chave in self._historico
        }
        for chave, _campo, titulo, tom in _METRICAS:
            linha = LinhaSistemaCompacta(
                titulo,
                tom,
                object_name_legado=object_name,
            )
            self.linhas[chave] = linha
            layout.addWidget(linha)

        self.uptime = QLabel("—", self)
        self.uptime.setObjectName("compactSystemUptime")
        self.uptime.hide()

        # Aliases públicos preservados durante a migração dos consumidores.
        self.metricas = {
            alias: self.linhas[chave].valor for alias, chave in _ALIAS_HOME.items()
        }
        self.metricas["uptime"] = self.uptime
        self.barras_metricas = {
            alias: self.linhas[chave].grafico for alias, chave in _ALIAS_HOME.items()
        }
        self.metricas_linhas = {
            alias: self.linhas[chave] for alias, chave in _ALIAS_HOME.items()
        }
        self.metricas_linhas["uptime"] = self.uptime
        self.sistema_valores = {
            campo: self.linhas[chave].valor
            for chave, campo, _titulo, _tom in _METRICAS
        }
        self.sistema_valores["uptime_seconds"] = self.uptime
        self.sistema_barras = {
            campo: self.linhas[chave].grafico
            for chave, campo, _titulo, _tom in _METRICAS
        }

    def aplicar_sistema(self, retrato: Mapping[str, object] | object) -> None:
        sistema = _bloco_sistema(retrato)
        estados: list[str] = []
        for chave, campo, _titulo, _tom in _METRICAS:
            metrica = sistema.get(campo)
            numero = _numero_metrica(metrica)
            frescor = (
                str(metrica.get("freshness") or "unavailable")
                if isinstance(metrica, Mapping)
                else "unavailable"
            )
            estado = (
                "stale" if numero is not None and frescor == "stale"
                else "fresh" if numero is not None
                else "unavailable"
            )
            estados.append(estado)
            linha = self.linhas[chave]
            linha.valor.setText(
                _texto_metrica(
                    metrica,
                    unidade_padrao="°C" if chave == "temperature" else "%",
                )
            )
            linha.setProperty("state", estado)
            linha.valor.setProperty("state", estado)
            linha.grafico.setProperty("available", numero is not None)
            linha.grafico.setValue(round(numero) if numero is not None else 0)

            if numero is not None and frescor == "fresh":
                observado = (
                    metrica.get("observed_at")
                    if isinstance(metrica, Mapping)
                    else None
                )
                assinatura = (observado, numero)
                if assinatura != self._assinaturas[chave]:
                    self._historico[chave].append(max(0.0, min(100.0, numero)))
                    self._assinaturas[chave] = assinatura
            linha.grafico.definir(self._historico[chave])
            for widget in (linha, linha.valor, linha.grafico):
                widget.style().unpolish(widget)
                widget.style().polish(widget)

        self.uptime.setText(_texto_metrica(sistema.get("uptime_seconds"), uptime=True))
        if any(estado == "fresh" for estado in estados):
            texto_estado = "tempo real"
        elif any(estado == "stale" for estado in estados):
            texto_estado = "dados antigos"
        else:
            texto_estado = "indisponível"
        self.subtitulo.setText(texto_estado)
        self.subtitulo.setProperty("state", texto_estado.replace(" ", "_"))
        self.subtitulo.style().unpolish(self.subtitulo)
        self.subtitulo.style().polish(self.subtitulo)

        download = _texto_metrica(sistema.get("download_mbps"))
        upload = _texto_metrica(sistema.get("upload_mbps"))
        self.linhas["network"].setToolTip(f"Download: {download}\nUpload: {upload}")

    def invalidar(self) -> None:
        for chave, linha in self.linhas.items():
            linha.valor.setText("—")
            linha.setProperty("state", "unavailable")
            linha.valor.setProperty("state", "unavailable")
            linha.grafico.setValue(0)
            linha.grafico.setProperty("available", False)
            linha.grafico.definir(self._historico[chave])
            for widget in (linha, linha.valor, linha.grafico):
                widget.style().unpolish(widget)
                widget.style().polish(widget)
        self.uptime.setText("—")
        self.subtitulo.setText("indisponível")
        self.subtitulo.setProperty("state", "indisponível")
        self.subtitulo.style().unpolish(self.subtitulo)
        self.subtitulo.style().polish(self.subtitulo)


__all__ = [
    "CardSistemaCompacto",
    "GraficoSistemaCompacto",
    "LinhaSistemaCompacta",
]
