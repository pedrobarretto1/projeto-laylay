"""Console de desenvolvimento observacional do Terminal Laylay 3.0.

A página recebe projeções públicas que a janela já possui. Ela não consulta
módulos internos, não concede autoridade e não executa efeitos no ambiente.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from html import escape
import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QBoxLayout,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from cliente.terminal_2.sistema_compacto import GraficoSistemaCompacto
from mente_laylay.integracao.eventos_dev import (
    CATEGORIAS_DEV,
    classificar_categoria_evento_dev,
)


CORES_CATEGORIA = {
    "SYSTEM": "#37db72",
    "IA": "#bc73f6",
    "ROUTER": "#b96af0",
    "PRESENCE": "#ef74bd",
    "EVENTS": "#ff566c",
    "AUTONOMY": "#9dda38",
    "ERRORS": "#ff4f64",
    "TRACE": "#57c9ee",
    "DEV/UI": "#ff7184",
}


@dataclass(frozen=True, slots=True)
class EventoDesenvolvedor:
    titulo: str
    detalhe: str
    nivel: str
    categoria: str
    ocorrido_em: datetime
    profundidade: str = "normal"
    trace_id: str = ""
    origem: str = "runtime"
    duracao_ms: float | None = None


def _categoria_evento(titulo: str, detalhe: str, nivel: str) -> str:
    """Classifica apenas para apresentação, sem reinterpretar a intenção."""
    return classificar_categoria_evento_dev(titulo, detalhe, nivel)


def _numero_metrica(metrica: object) -> float | None:
    if not isinstance(metrica, Mapping) or metrica.get("value") is None:
        return None
    try:
        return max(0.0, min(100.0, float(metrica["value"])))
    except (TypeError, ValueError):
        return None


class MetricaDevCompacta(QFrame):
    """Projeção compacta que reutiliza o gráfico canônico do Sistema."""

    def __init__(self, titulo: str, tom: str, *, com_grafico: bool = True) -> None:
        super().__init__()
        self.setObjectName("devTelemetryCell")
        self._historico: deque[float] = deque(maxlen=24)
        self._assinatura: tuple[object, float] | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(3)

        topo = QHBoxLayout()
        topo.setContentsMargins(0, 0, 0, 0)
        self.titulo = QLabel(titulo.upper())
        self.titulo.setObjectName("devTelemetryTitle")
        self.valor = QLabel("—")
        self.valor.setObjectName("devTelemetryValue")
        topo.addWidget(self.titulo)
        topo.addStretch()
        topo.addWidget(self.valor)
        layout.addLayout(topo)

        self.grafico = GraficoSistemaCompacto(tom)
        self.grafico.setFixedHeight(21)
        self.grafico.setVisible(com_grafico)
        layout.addWidget(self.grafico)

    def aplicar(self, metrica: object) -> None:
        numero = _numero_metrica(metrica)
        if numero is None:
            self.valor.setText("—")
            self.grafico.setProperty("available", False)
            self.grafico.definir(self._historico)
            return
        unidade = str(metrica.get("unit") or "%") if isinstance(metrica, Mapping) else "%"
        sufixo = (
            " · antigo"
            if isinstance(metrica, Mapping) and metrica.get("freshness") == "stale"
            else ""
        )
        valor = str(int(numero)) if numero.is_integer() else f"{numero:.1f}".replace(".", ",")
        self.valor.setText(f"{valor}{unidade}{sufixo}")
        self.grafico.setProperty("available", True)
        if isinstance(metrica, Mapping) and metrica.get("freshness") == "fresh":
            assinatura = (metrica.get("observed_at"), numero)
            if assinatura != self._assinatura:
                self._historico.append(numero)
                self._assinatura = assinatura
        self.grafico.definir(self._historico)

    def definir_texto(self, texto: str, *, disponivel: bool = True) -> None:
        self.valor.setText(str(texto or "—"))
        self.valor.setProperty("available", bool(disponivel))
        self.valor.style().unpolish(self.valor)
        self.valor.style().polish(self.valor)

    def invalidar(self) -> None:
        self.valor.setText("—")
        self.grafico.setProperty("available", False)
        self.grafico.definir(self._historico)


class CardManutencaoDev(QFrame):
    def __init__(self, icone: str, titulo: str) -> None:
        super().__init__()
        self.setObjectName("devMaintenanceCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(13, 11, 13, 11)
        layout.setSpacing(7)

        topo = QHBoxLayout()
        topo.setContentsMargins(0, 0, 0, 0)
        simbolo = QLabel(icone)
        simbolo.setObjectName("devMaintenanceIcon")
        nome = QLabel(titulo)
        nome.setObjectName("devMaintenanceTitle")
        topo.addWidget(simbolo)
        topo.addWidget(nome)
        topo.addStretch()
        layout.addLayout(topo)

        descricao = QLabel("Integração ainda não disponível neste runtime.")
        descricao.setObjectName("devMaintenanceDescription")
        descricao.setWordWrap(True)
        layout.addWidget(descricao)

        self.status = QPushButton("Em manutenção")
        self.status.setObjectName("devMaintenanceStatus")
        self.status.setEnabled(False)
        self.status.setAccessibleName(f"{titulo}: em manutenção")
        layout.addWidget(self.status)


class PaginaDesenvolvedor(QWidget):
    """Monitor DEV: logs reais, filtros locais e telemetria sanitizada."""

    consulta_solicitada = Signal(str)
    controle_solicitado = Signal(str)

    CATEGORIAS = (
        "ALL",
        "SYSTEM",
        "IA",
        "ROUTER",
        "PRESENCE",
        "EVENTS",
        "AUTONOMY",
        "ERRORS",
        "TRACE",
    )

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("developerPage")
        self._eventos: deque[EventoDesenvolvedor] = deque(maxlen=500)
        self._ao_vivo = True
        self._eventos_pendentes = 0
        self._categoria_ativa = "ALL"
        self._profundidade_ativa = "normal"
        self._conectada = False
        self._dashboard: dict = {}
        self._consulta_pendente = ""
        self._controle_pendente = ""
        self.botoes_categoria: dict[str, QPushButton] = {}
        self.botoes_nivel: dict[str, QPushButton] = {}
        self.cards_manutencao: dict[str, QPushButton] = {}
        self.telemetria: dict[str, MetricaDevCompacta] = {}

        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(13, 10, 13, 12)
        raiz.setSpacing(12)

        principal = QVBoxLayout()
        principal.setContentsMargins(0, 0, 0, 0)
        principal.setSpacing(9)

        principal.addWidget(self._criar_barra_controles())
        principal.addWidget(self._criar_console(), 1)
        principal.addWidget(self._criar_telemetria())
        raiz.addLayout(principal, 1)

        self.rail = self._criar_rail()
        raiz.addWidget(self.rail)
        self.setStyleSheet(self._estilo())

    @property
    def eventos_pendentes(self) -> int:
        return self._eventos_pendentes

    def _criar_barra_controles(self) -> QWidget:
        caixa = QFrame()
        caixa.setObjectName("devToolbar")
        externo = QVBoxLayout(caixa)
        externo.setContentsMargins(14, 9, 14, 9)
        externo.setSpacing(7)

        linha_titulo = QHBoxLayout()
        marca = QLabel("›_")
        marca.setObjectName("devPromptMark")
        titulo = QLabel("DEV CONSOLE")
        titulo.setObjectName("devTitle")
        self.estado_fonte = QLabel("●  MONITOR OBSERVACIONAL")
        self.estado_fonte.setObjectName("devObservedState")
        linha_titulo.addWidget(marca)
        linha_titulo.addWidget(titulo)
        linha_titulo.addStretch()
        linha_titulo.addWidget(self.estado_fonte)
        externo.addLayout(linha_titulo)

        linha = QHBoxLayout()
        linha.setContentsMargins(0, 0, 0, 0)
        linha.setSpacing(6)
        grupo_categoria = QButtonGroup(self)
        grupo_categoria.setExclusive(True)
        for categoria in self.CATEGORIAS:
            botao = QPushButton(categoria)
            botao.setObjectName("devFilterButton")
            botao.setCheckable(True)
            botao.setChecked(categoria == "ALL")
            botao.clicked.connect(
                lambda _marcado=False, valor=categoria: self._definir_categoria(valor)
            )
            grupo_categoria.addButton(botao)
            self.botoes_categoria[categoria] = botao
            linha.addWidget(botao)
        linha.addStretch()

        separador = QFrame()
        separador.setObjectName("devVerticalSeparator")
        separador.setFrameShape(QFrame.VLine)
        linha.addWidget(separador)

        nivel_rotulo = QLabel("NÍVEL")
        nivel_rotulo.setObjectName("devControlLabel")
        linha.addWidget(nivel_rotulo)
        grupo_nivel = QButtonGroup(self)
        grupo_nivel.setExclusive(True)
        for nivel, texto in (("normal", "NORMAL"), ("debug", "DEBUG"), ("trace", "TRACE")):
            botao = QPushButton(texto)
            botao.setObjectName("devLevelButton")
            botao.setCheckable(True)
            botao.setChecked(nivel == "normal")
            botao.clicked.connect(
                lambda _marcado=False, valor=nivel: self._definir_profundidade(valor)
            )
            grupo_nivel.addButton(botao)
            self.botoes_nivel[nivel] = botao
            linha.addWidget(botao)

        insane = QPushButton("INSANE")
        insane.setObjectName("devLevelButton")
        insane.setEnabled(False)
        insane.setToolTip("Em manutenção")
        linha.addWidget(insane)

        self.botao_live = QPushButton("●  LIVE")
        self.botao_live.setObjectName("devStateButton")
        self.botao_live.setCheckable(True)
        self.botao_live.setChecked(True)
        self.botao_live.clicked.connect(lambda: self.definir_ao_vivo(True))
        self.botao_pause = QPushButton("Ⅱ  PAUSED")
        self.botao_pause.setObjectName("devStateButton")
        self.botao_pause.setCheckable(True)
        self.botao_pause.clicked.connect(lambda: self.definir_ao_vivo(False))
        linha.addWidget(self.botao_live)
        linha.addWidget(self.botao_pause)
        externo.addLayout(linha)
        return caixa

    def _criar_console(self) -> QWidget:
        moldura = QFrame()
        moldura.setObjectName("devConsoleFrame")
        layout = QVBoxLayout(moldura)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.console = QTextEdit(readOnly=True)
        self.console.setObjectName("devConsole")
        self.console.document().setMaximumBlockCount(700)
        self.console.setPlaceholderText(
            "Aguardando eventos reais da sessão. Nenhuma amostra simulada será exibida."
        )
        layout.addWidget(self.console, 1)

        comando_caixa = QFrame()
        comando_caixa.setObjectName("devCommandBar")
        comando_lay = QHBoxLayout(comando_caixa)
        comando_lay.setContentsMargins(13, 7, 13, 7)
        comando_lay.setSpacing(8)
        prompt = QLabel("laylay.dev  ›")
        prompt.setObjectName("devCommandPrompt")
        self.comando = QLineEdit()
        self.comando.setObjectName("devCommandInput")
        self.comando.setPlaceholderText(
            "help · trace last · errors · status · perf · tests list/status/run/cancel"
        )
        self.comando.returnPressed.connect(self._executar_comando_local)
        comando_lay.addWidget(prompt)
        comando_lay.addWidget(self.comando, 1)
        layout.addWidget(comando_caixa)
        return moldura

    def _criar_telemetria(self) -> QWidget:
        faixa = QFrame()
        faixa.setObjectName("devTelemetryBar")
        layout = QHBoxLayout(faixa)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(0)
        for chave, titulo, tom, grafico in (
            ("cpu", "CPU", "cpu", True),
            ("ram", "RAM", "ram", True),
            ("vram", "VRAM", "vram", True),
            ("network", "REDE", "network", True),
            ("eventos", "EVENTOS", "cpu", False),
            ("ponte", "PONTE", "network", False),
        ):
            metrica = MetricaDevCompacta(titulo, tom, com_grafico=grafico)
            self.telemetria[chave] = metrica
            layout.addWidget(metrica, 1)
        self.telemetria["eventos"].definir_texto("0")
        self.telemetria["ponte"].definir_texto("OFFLINE", disponivel=False)
        return faixa

    def _criar_rail(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setObjectName("devRail")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(250)
        scroll.setMaximumWidth(278)
        conteudo = QWidget()
        conteudo.setObjectName("devRailContent")
        layout = QVBoxLayout(conteudo)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for icone, titulo in (
            ("⌁", "Sensor Health"),
            ("♙", "Presence State"),
            ("▣", "Evento Aberto"),
            ("◉", "World Model (Resumo)"),
            ("ϟ", "Autonomy Decision"),
            ("☷", "Recent Trace"),
            ("↻", "Restore Manager"),
        ):
            card = CardManutencaoDev(icone, titulo)
            self.cards_manutencao[titulo] = card.status
            layout.addWidget(card)
        layout.addStretch()
        scroll.setWidget(conteudo)
        return scroll

    def registrar_evento(
        self,
        titulo: str,
        detalhe: str = "",
        nivel: str = "info",
        *,
        categoria: str = "",
        ocorrido_em: datetime | None = None,
        profundidade: str = "normal",
        trace_id: str = "",
        origem: str = "runtime",
        duracao_ms: float | None = None,
    ) -> None:
        nivel = str(nivel or "info").casefold()
        categoria = classificar_categoria_evento_dev(
            titulo,
            detalhe,
            nivel,
            categoria_explicita=categoria,
        )
        if categoria not in CATEGORIAS_DEV:
            categoria = "SYSTEM"
        evento = EventoDesenvolvedor(
            titulo=str(titulo or "Evento sem título"),
            detalhe=str(detalhe or ""),
            nivel=nivel,
            categoria=categoria,
            ocorrido_em=ocorrido_em or datetime.now(),
            profundidade=(
                profundidade if profundidade in {"normal", "debug", "trace"} else "normal"
            ),
            trace_id=str(trace_id or "")[:72],
            origem=str(origem or "runtime")[:24],
            duracao_ms=duracao_ms,
        )
        self._eventos.append(evento)
        self.telemetria["eventos"].definir_texto(str(len(self._eventos)))
        if self._ao_vivo:
            if self._evento_visivel(evento):
                self._anexar_evento(evento)
        else:
            self._eventos_pendentes += 1
            self._atualizar_rotulo_pausa()

    def definir_ao_vivo(self, ao_vivo: bool) -> None:
        self._ao_vivo = bool(ao_vivo)
        self.botao_live.setChecked(self._ao_vivo)
        self.botao_pause.setChecked(not self._ao_vivo)
        if self._ao_vivo:
            self._eventos_pendentes = 0
            self._renderizar_eventos()
        self._atualizar_rotulo_pausa()

    def definir_conectada(self, conectada: bool) -> None:
        self._conectada = bool(conectada)
        self.telemetria["ponte"].definir_texto(
            "ONLINE" if conectada else "OFFLINE",
            disponivel=conectada,
        )
        self.estado_fonte.setText(
            "●  MONITOR OBSERVACIONAL" if conectada else "●  AGUARDANDO PONTE"
        )
        self.estado_fonte.setProperty("connected", conectada)
        self.estado_fonte.style().unpolish(self.estado_fonte)
        self.estado_fonte.style().polish(self.estado_fonte)

    def aplicar_dashboard(self, dashboard: dict) -> None:
        self._dashboard = dict(dashboard or {})
        sistema = dashboard.get("system") if isinstance(dashboard.get("system"), dict) else {}
        for chave, campo in (
            ("cpu", "cpu_percent"),
            ("ram", "ram_percent"),
            ("vram", "vram_percent"),
            ("network", "network_percent"),
        ):
            self.telemetria[chave].aplicar(sistema.get(campo))

    def invalidar(self) -> None:
        self._dashboard = {}
        for chave in ("cpu", "ram", "vram", "network"):
            self.telemetria[chave].invalidar()

    def registrar_consulta_enviada(self, requisicao_id: str, comando: str) -> None:
        self._consulta_pendente = str(requisicao_id or "")
        self.registrar_evento(
            f"laylay.dev › {comando}",
            "Consulta somente leitura enviada ao núcleo.",
            "info",
            categoria="DEV/UI",
        )

    def registrar_controle_enviado(self, requisicao_id: str, comando: str) -> None:
        self._controle_pendente = str(requisicao_id or "")
        self.estado_fonte.setText("●  CONTROL AUTORIZADO")
        self.registrar_evento(
            f"laylay.dev › {comando}",
            "Comando CONTROL enviado pelo canal dedicado.",
            "warning",
            categoria="DEV/UI",
        )

    def aplicar_resultado_consulta(self, mensagem: Mapping[str, object]) -> None:
        requisicao_id = str(mensagem.get("id") or "")
        if self._consulta_pendente and requisicao_id != self._consulta_pendente:
            return
        self._consulta_pendente = ""
        bruto = mensagem.get("result")
        resultado = dict(bruto) if isinstance(bruto, Mapping) else {}
        linhas = [str(item) for item in list(resultado.get("lines") or ())[:120]]
        tipo = str(resultado.get("kind") or "DEV/UI").casefold()
        categoria = {
            "trace": "TRACE",
            "errors": "ERRORS",
            "performance": "SYSTEM",
            "status": "SYSTEM",
            "inspect": "TRACE",
        }.get(tipo, "DEV/UI")
        self.registrar_evento(
            str(resultado.get("command") or "Consulta DEV"),
            "\n".join(linhas) or "Sem resultado observado.",
            "success" if resultado.get("ok") is True else "warning",
            categoria=categoria,
            profundidade="normal",
        )

    def aplicar_resultado_controle(self, mensagem: Mapping[str, object]) -> None:
        requisicao_id = str(mensagem.get("id") or "")
        if self._controle_pendente and requisicao_id != self._controle_pendente:
            return
        self._controle_pendente = ""
        self.estado_fonte.setText(
            "●  MONITOR OBSERVACIONAL" if self._conectada else "●  AGUARDANDO PONTE"
        )
        bruto = mensagem.get("result")
        resultado = dict(bruto) if isinstance(bruto, Mapping) else {}
        linhas = [str(item) for item in list(resultado.get("lines") or ())[:120]]
        status = str(resultado.get("status") or "erro")
        self.registrar_evento(
            str(resultado.get("command") or "CONTROL"),
            "\n".join(linhas) or f"status={status}",
            "success" if resultado.get("ok") is True else "error",
            categoria="TRACE",
            profundidade="normal",
        )

    def _evento_visivel(self, evento: EventoDesenvolvedor) -> bool:
        if self._categoria_ativa != "ALL" and evento.categoria != self._categoria_ativa:
            return False
        ordem = {"normal": 0, "debug": 1, "trace": 2}
        return ordem[evento.profundidade] <= ordem[self._profundidade_ativa]

    def _anexar_evento(self, evento: EventoDesenvolvedor) -> None:
        horario = evento.ocorrido_em.strftime("%H:%M:%S.%f")[:-3]
        cor = CORES_CATEGORIA.get(evento.categoria, "#57c9ee")
        detalhe = f"  {escape(evento.detalhe)}" if evento.detalhe else ""
        trace = (
            f'<span style="color:#7793a5;">[{escape(evento.trace_id)}]</span>  '
            if evento.trace_id else ""
        )
        self.console.append(
            '<div style="white-space:pre; margin:0;">'
            f'<span style="color:#7c858f;">{horario}</span>  '
            f'<span style="color:{cor}; font-weight:600;">[{escape(evento.categoria)}]</span>  '
            f'{trace}<span style="color:#d7dbe0;">{escape(evento.titulo)}{detalhe}</span>'
            "</div>"
        )
        barra = self.console.verticalScrollBar()
        barra.setValue(barra.maximum())

    def _renderizar_eventos(self) -> None:
        self.console.clear()
        for evento in self._eventos:
            if self._evento_visivel(evento):
                self._anexar_evento(evento)

    def _definir_categoria(self, categoria: str) -> None:
        self._categoria_ativa = categoria
        self._renderizar_eventos()

    def _definir_profundidade(self, profundidade: str) -> None:
        self._profundidade_ativa = profundidade
        self._renderizar_eventos()

    def _atualizar_rotulo_pausa(self) -> None:
        texto = "Ⅱ  PAUSED"
        if not self._ao_vivo and self._eventos_pendentes:
            texto += f"  +{self._eventos_pendentes}"
        self.botao_pause.setText(texto)

    def _executar_comando_local(self) -> None:
        comando = self.comando.text().strip().casefold()
        self.comando.clear()
        if not comando:
            return
        if comando == "clear":
            self.console.clear()
            return
        if comando == "pause":
            self.definir_ao_vivo(False)
            return
        if comando == "live":
            self.definir_ao_vivo(True)
            return
        if comando == "help":
            resposta = (
                "Locais: help, events, pause, live e clear. Núcleo: status, "
                "perf, errors, errors <componente>:<código>, trace last, "
                "trace turn <n>, inspect context, "
                "inspect pending, inspect action last, inspect receipt last, "
                "inspect memory used, inspect event <id>, tests list, "
                "tests status, tests run <suite_id> e tests cancel."
            )
        elif comando == "events":
            resposta = f"{len(self._eventos)} evento(s) observados nesta sessão."
        elif comando == "status" and not self._conectada:
            resposta = "Ponte offline; a consulta não foi enviada ao núcleo."
        elif comando.startswith("tests "):
            permitido = bool(re.fullmatch(
                r"tests (?:list|status|cancel|run [a-z0-9][a-z0-9_-]{0,47})",
                comando,
            ))
            if not permitido:
                resposta = "Comando CONTROL inválido; nenhum processo foi iniciado."
            elif self._conectada:
                self.estado_fonte.setText("●  CONTROL SOLICITADO")
                self.controle_solicitado.emit(comando)
                return
            else:
                resposta = "Ponte offline; o comando CONTROL não foi enviado."
        elif self._conectada:
            self.consulta_solicitada.emit(comando)
            return
        else:
            resposta = (
                "Consulta indisponível com a ponte offline; nenhum efeito foi executado."
            )
        self.registrar_evento(
            f"laylay.dev › {comando}",
            resposta,
            "info",
            categoria="DEV/UI",
        )

    def resizeEvent(self, event) -> None:  # noqa: N802 - contrato Qt
        super().resizeEvent(event)
        self.rail.setVisible(self.width() >= 1060)

    @staticmethod
    def _estilo() -> str:
        return """
        QWidget#developerPage {
            background: #0c1116;
            color: #dce1e6;
            font-family: "Segoe UI";
        }
        QFrame#devToolbar, QFrame#devTelemetryBar {
            background: #10171d;
            border: 1px solid #253039;
            border-radius: 11px;
        }
        QLabel#devPromptMark { color: #ff5268; font: 700 16px "Cascadia Code"; }
        QLabel#devTitle { color: #f4f6f8; font: 700 12px "Segoe UI"; }
        QLabel#devObservedState { color: #7d8790; font: 600 9px "Segoe UI"; }
        QLabel#devObservedState[connected="true"] { color: #5bd887; }
        QLabel#devControlLabel { color: #64707a; font: 600 8px "Segoe UI"; }
        QFrame#devVerticalSeparator { color: #38424a; max-width: 1px; }
        QPushButton#devFilterButton, QPushButton#devLevelButton,
        QPushButton#devStateButton {
            min-height: 25px;
            padding: 0 10px;
            border: 1px solid #2b3740;
            border-radius: 6px;
            background: #111820;
            color: #87919a;
            font: 600 8px "Segoe UI";
        }
        QPushButton#devFilterButton:hover, QPushButton#devLevelButton:hover,
        QPushButton#devStateButton:hover { border-color: #59636b; color: #e8ebee; }
        QPushButton#devFilterButton:checked, QPushButton#devLevelButton:checked {
            border-color: #b63c50;
            color: #ff6177;
            background: #28151b;
        }
        QPushButton#devStateButton:checked {
            border-color: #394752;
            color: #ff5b72;
            background: #172029;
        }
        QPushButton#devLevelButton:disabled { color: #48515a; border-color: #202a32; }
        QFrame#devConsoleFrame {
            background: #020405;
            border: 1px solid #354049;
            border-radius: 10px;
        }
        QTextEdit#devConsole {
            background: #020304;
            color: #d7dbe0;
            border: 0;
            border-radius: 9px 9px 0 0;
            padding: 12px 15px;
            selection-background-color: #713443;
            font: 10pt "Cascadia Code";
        }
        QFrame#devCommandBar {
            background: #070b0e;
            border: 0;
            border-top: 1px solid #1d272e;
            border-radius: 0 0 9px 9px;
        }
        QLabel#devCommandPrompt { color: #b8bec4; font: 10pt "Cascadia Code"; }
        QLineEdit#devCommandInput {
            color: #e3e7ea;
            background: transparent;
            border: 0;
            padding: 3px;
            font: 10pt "Cascadia Code";
        }
        QLineEdit#devCommandInput:focus { color: #ffffff; }
        QFrame#devTelemetryCell {
            background: transparent;
            border: 0;
            border-right: 1px solid #2b343c;
            border-radius: 0;
        }
        QLabel#devTelemetryTitle { color: #919ba4; font: 600 8px "Segoe UI"; }
        QLabel#devTelemetryValue { color: #d9dde1; font: 600 9px "Cascadia Code"; }
        QLabel#devTelemetryValue[available="false"] { color: #69737c; }
        QScrollArea#devRail { background: transparent; border: 0; }
        QWidget#devRailContent { background: transparent; }
        QFrame#devMaintenanceCard {
            background: #14171c;
            border: 1px solid #513039;
            border-radius: 11px;
        }
        QLabel#devMaintenanceIcon { color: #ff6277; font: 700 18px "Segoe UI Symbol"; }
        QLabel#devMaintenanceTitle { color: #eef0f2; font: 600 10px "Segoe UI"; }
        QLabel#devMaintenanceDescription { color: #7f878e; font: 8px "Segoe UI"; }
        QPushButton#devMaintenanceStatus:disabled {
            min-height: 22px;
            color: #c76775;
            background: #26171c;
            border: 1px solid #61313c;
            border-radius: 5px;
            font: 600 8px "Segoe UI";
        }
        QScrollBar:vertical { background: #090d10; width: 8px; margin: 0; }
        QScrollBar::handle:vertical { background: #34404a; min-height: 28px; border-radius: 4px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """


__all__ = ["EventoDesenvolvedor", "PaginaDesenvolvedor"]
