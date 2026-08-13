"""Componentes visuais do dashboard do Terminal Laylay 3.0.

Este módulo não consulta memória, sistema ou executores. Ele recebe projeções
sanitizadas da janela principal e encaminha ações disponíveis pelo mesmo canal
textual usado pela conversa.
"""

from __future__ import annotations

from collections import deque
import time

from PySide6.QtCore import QSize, Qt, Signal, QTimer
from PySide6.QtCore import QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from mente_laylay.integracao.acoes_terminal import ACOES_RAPIDAS_TERMINAL
from cliente.terminal_2.acabamento import (
    CapaMusicaGenerica,
    icone_terminal,
)
from cliente.terminal_2.musica_m1 import PaginaMusica


class ChipEstado(QFrame):
    """Estado compacto do topo, sem inferir disponibilidade não observada."""

    def __init__(self, titulo: str, valor: str = "Aguardando") -> None:
        super().__init__()
        self.setObjectName("statusChip")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(11, 7, 11, 7)
        layout.setSpacing(7)
        self.ponto = QLabel("●")
        self.ponto.setObjectName("statusChipDot")
        self.texto = QLabel()
        self.texto.setObjectName("statusChipText")
        layout.addWidget(self.ponto)
        layout.addWidget(self.texto)
        self._titulo = str(titulo or "Estado")
        self.definir(valor, estado="pending")

    def definir(self, valor: str, *, estado: str = "pending") -> None:
        estado = estado if estado in {"online", "pending", "unavailable", "error"} else "pending"
        self.texto.setText(f"{self._titulo}: {str(valor or '—')}")
        self.setProperty("state", estado)
        self.ponto.setProperty("state", estado)
        for widget in (self, self.ponto):
            widget.style().unpolish(widget)
            widget.style().polish(widget)


def _texto_metrica(metrica: object, *, uptime: bool = False) -> str:
    if not isinstance(metrica, dict) or metrica.get("value") is None:
        return "—"
    try:
        valor = float(metrica["value"])
    except (TypeError, ValueError):
        return "—"
    if uptime:
        total = max(0, int(valor))
        dias, resto = divmod(total, 86_400)
        horas, minutos = divmod(resto, 3_600)
        minutos //= 60
        texto = f"{dias}d {horas}h" if dias else f"{horas}h {minutos}m"
    else:
        unidade = str(metrica.get("unit") or "")
        numero = str(int(valor)) if valor.is_integer() else f"{valor:.1f}".replace(".", ",")
        texto = f"{numero}{unidade}"
    if str(metrica.get("freshness") or "") == "stale":
        texto += " · antigo"
    return texto


class CartaoDashboard(QFrame):
    def __init__(self, titulo: str, *, subtitulo: str = "") -> None:
        super().__init__()
        self.setObjectName("dashboardCard")
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(15, 14, 15, 14)
        self.layout_principal.setSpacing(10)
        cabecalho = QHBoxLayout()
        titulo_label = QLabel(titulo)
        titulo_label.setObjectName("dashboardCardTitle")
        cabecalho.addWidget(titulo_label)
        cabecalho.addStretch()
        if subtitulo:
            detalhe = QLabel(subtitulo)
            detalhe.setObjectName("dashboardCardHint")
            cabecalho.addWidget(detalhe)
        self.layout_principal.addLayout(cabecalho)


def _linha_valor(rotulo: str, valor: str = "—") -> tuple[QWidget, QLabel]:
    linha = QWidget()
    layout = QHBoxLayout(linha)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    nome = QLabel(rotulo)
    nome.setObjectName("dashboardMetricLabel")
    dado = QLabel(valor)
    dado.setObjectName("dashboardMetricValue")
    dado.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    layout.addWidget(nome)
    layout.addStretch()
    layout.addWidget(dado)
    return linha, dado


class PainelCentralInteligente(QFrame):
    """Coluna de ações que encaminha pedidos, sem executar capacidades."""

    acao_solicitada = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("intelligencePanel")
        self.setMinimumWidth(360)
        self.setMaximumWidth(415)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            14, 15, 14, 15
        )
        layout.setSpacing(8)

        cabecalho = QHBoxLayout()
        titulo = QLabel("Central Inteligente")
        titulo.setObjectName("intelligenceTitle")
        self.estado = QLabel("P3 · conectando")
        self.estado.setObjectName("liveBadge")
        cabecalho.addWidget(titulo)
        cabecalho.addStretch()
        cabecalho.addWidget(self.estado)
        layout.addLayout(cabecalho)

        acoes = CartaoDashboard("Ações rápidas")
        acoes.setProperty(
        "centralSection",
        True,
        )
        grade = QGridLayout()
        grade.setContentsMargins(0, 0, 0, 0)
        grade.setSpacing(7)
        self.acoes: dict[str, QPushButton] = {}
        self._acoes_por_id: dict[str, QPushButton] = {}
        self._rotulos_acoes: dict[str, str] = {}
        self._estado_disponibilidade: dict[str, str] = {}
        self._conectada = False
        for indice, definicao in enumerate(ACOES_RAPIDAS_TERMINAL):
            acao_id = str(definicao["id"])
            texto = str(
                definicao["label"]
            )

            texto_visual = texto
            comando = str(definicao.get("request") or "")
            botao = QPushButton(texto_visual)
            botao.setProperty("dashboardAction", True)
            botao.setProperty("actionState", "idle")
            botao.setEnabled(False)
            if comando:
                botao.clicked.connect(
                    lambda _marcado=False, aid=acao_id, pedido=comando:
                    self.acao_solicitada.emit(aid, pedido)
                )
            self.acoes[texto_visual] = botao
            self._acoes_por_id[acao_id] = botao
            self._rotulos_acoes[acao_id] = texto_visual
            self._estado_disponibilidade[acao_id] = (
                "available" if comando else
                "requires_input" if definicao.get("intent") else "unavailable"
            )
            grade.addWidget(botao, indice // 2, indice % 2)
        acoes.layout_principal.addLayout(grade)
        layout.addWidget(acoes)

        contexto = CartaoDashboard("Contexto atual", subtitulo="sanitizado")
        contexto.setProperty(
        "centralSection",
        True,
        )
        contexto_grade = QGridLayout()
        contexto_grade.setContentsMargins(0, 0, 0, 0)
        contexto_grade.setSpacing(7)
        self.contexto_valores: dict[str, QLabel] = {}
        for indice, (chave, rotulo, valor) in enumerate((
            ("projeto", "Projeto", "Laylay"),
            ("modo", "Modo", "Aguardando"),
            ("cidade", "Cidade", "Aguardando"),
            ("jogo", "Jogo", "Não observado"),
        )):
            item = QFrame()
            item.setObjectName("contextItem")
            item_lay = QVBoxLayout(item)
            item_lay.setContentsMargins(9, 7, 9, 7)
            item_lay.setSpacing(2)
            nome = QLabel(rotulo)
            nome.setObjectName("contextLabel")
            dado = QLabel(valor)
            dado.setObjectName("contextValue")
            dado.setWordWrap(True)
            item_lay.addWidget(nome)
            item_lay.addWidget(dado)
            self.contexto_valores[chave] = dado
            contexto_grade.addWidget(item, indice // 3, indice % 3)
        contexto.layout_principal.addLayout(contexto_grade)
        layout.addWidget(contexto)

        memoria = CartaoDashboard(
            "Memória recente"
        )

        memoria.setProperty(
            "centralSection",
            True,
        )

        memoria.layout_principal.setContentsMargins(
            2, 8, 2, 10
        )
        memoria.layout_principal.setSpacing(6)


        # Estado vazio / indisponível
        self.memoria_estado = QLabel(
            "Aguardando uma projeção segura da memória."
        )
        self.memoria_estado.setObjectName(
            "dashboardEmpty"
        )
        self.memoria_estado.setWordWrap(True)

        memoria.layout_principal.addWidget(
            self.memoria_estado
        )


        # Até três cartões reais
        self.memoria_linhas: list[
            dict[str, object]
        ] = []

        for _ in range(3):
            cartao = QFrame()
            cartao.setObjectName(
                "memoryRecentCard"
            )
            cartao.setProperty(
                "memoryKind",
                "generic",
            )
            cartao.hide()

            cartao_layout = QHBoxLayout(
                cartao
            )
            cartao_layout.setContentsMargins(
                9, 8, 9, 8
            )
            cartao_layout.setSpacing(9)

            # Ícone
            icone = QLabel("•")
            icone.setObjectName(
                "memoryRecentIcon"
            )
            icone.setAlignment(
                Qt.AlignCenter
            )
            icone.setFixedSize(
                28, 28
            )

            # Texto
            textos = QVBoxLayout()
            textos.setContentsMargins(
                0, 0, 0, 0
            )
            textos.setSpacing(2)

            resumo = QLabel(
                "Memória"
            )
            resumo.setObjectName(
                "memoryRecentSummary"
            )
            resumo.setWordWrap(True)

            detalhe = QLabel("")
            detalhe.setObjectName(
                "memoryRecentDetail"
            )
            detalhe.setWordWrap(True)

            textos.addWidget(
                resumo
            )
            textos.addWidget(
                detalhe
            )

            cartao_layout.addWidget(
                icone,
                0,
                Qt.AlignTop,
            )
            cartao_layout.addLayout(
                textos,
                1,
            )

            memoria.layout_principal.addWidget(
                cartao
            )

            self.memoria_linhas.append({
                "widget": cartao,
                "icon": icone,
                "summary": resumo,
                "detail": detalhe,
            })

        layout.addWidget(memoria)

        # =========================================================
        # ATIVIDADE RECENTE
        # =========================================================
        atividade = CartaoDashboard(
            "Atividade recente"
        )

        atividade.setProperty(
            "centralSection",
            True,
        )

        atividade.layout_principal.setContentsMargins(
            2, 8, 2, 6
        )
        atividade.layout_principal.setSpacing(5)


        # Estado vazio
        self.atividade_estado = QLabel(
            "Tudo quieto nesta sessão."
        )
        self.atividade_estado.setObjectName(
            "activityRecentEmpty"
        )
        self.atividade_estado.setWordWrap(True)

        atividade.layout_principal.addWidget(
            self.atividade_estado
        )


        # Mantém compatibilidade com qualquer referência antiga
        self.atividade_itens = self.atividade_estado


        # Até três eventos recentes
        self.atividade_linhas: list[
            dict[str, object]
        ] = []

        for _ in range(3):
            linha = QFrame()
            linha.setObjectName(
                "activityRecentRow"
            )
            linha.hide()

            linha_layout = QHBoxLayout(
                linha
            )
            linha_layout.setContentsMargins(
                9, 7, 9, 7
            )
            linha_layout.setSpacing(8)

            ponto = QLabel("●")
            ponto.setObjectName(
                "activityRecentDot"
            )
            ponto.setAlignment(
                Qt.AlignCenter
            )
            ponto.setFixedWidth(12)

            texto = QLabel("Evento")
            texto.setObjectName(
                "activityRecentText"
            )
            texto.setWordWrap(True)

            horario = QLabel("—")
            horario.setObjectName(
                "activityRecentTime"
            )
            horario.setAlignment(
                Qt.AlignRight | Qt.AlignVCenter
            )

            linha_layout.addWidget(
                ponto
            )
            linha_layout.addWidget(
                texto,
                1,
            )
            linha_layout.addWidget(
                horario
            )

            atividade.layout_principal.addWidget(
                linha
            )

            self.atividade_linhas.append({
                "widget": linha,
                "dot": ponto,
                "text": texto,
                "time": horario,
            })


        layout.addWidget(
            atividade
        )

        layout.addStretch()


        # horário + descrição do evento
        self._eventos: deque[
            tuple[str, str]
        ] = deque(
            maxlen=3
        )

        self.definir_conectada(False)

    def definir_conectada(self, conectada: bool) -> None:
        self._conectada = bool(conectada)
        for acao_id, botao in self._acoes_por_id.items():
            disponibilidade = self._estado_disponibilidade.get(
                acao_id, "unavailable",
            )
            habilitada = self._conectada and disponibilidade in {
                "available", "degraded",
            }
            botao.setEnabled(habilitada)
            botao.setToolTip(
                "Enviar pela mente canônica"
                if habilitada
                else "Aguardando conexão autenticada com a mente"
                if not self._conectada
                else "Precisa de mais informação antes de enviar"
                if disponibilidade == "requires_input"
                else "Esta capacidade não está disponível agora"
            )

    def aplicar_catalogo_acoes(self, itens: object) -> None:
        if not isinstance(itens, list):
            return
        recebidas: set[str] = set()
        for item in itens:
            if not isinstance(item, dict):
                continue
            acao_id = str(item.get("id") or "")
            if acao_id not in self._acoes_por_id:
                continue
            estado = str(item.get("state") or "unavailable")
            if estado not in {
                "available", "degraded", "requires_input", "unavailable",
            }:
                estado = "unavailable"
            recebidas.add(acao_id)
            self._estado_disponibilidade[acao_id] = estado
            motivo = str(item.get("reason") or "").replace("_", " ").strip()
            if motivo:
                self._acoes_por_id[acao_id].setToolTip(motivo.capitalize())
        for acao_id in self._acoes_por_id:
            if acao_id not in recebidas:
                self._estado_disponibilidade[acao_id] = "unavailable"
        self.definir_conectada(self._conectada)

    def definir_estado_acao(
        self, acao_id: str, estado: str, resumo: str = "",
    ) -> None:
        botao = self._acoes_por_id.get(str(acao_id or ""))
        if botao is None:
            return
        estado = str(estado or "")
        marcadores = {
            "sending": "…", "received": "◌", "executing": "◉",
            "awaiting_confirmation": "?", "confirmed": "✓",
            "partial": "!", "failed": "×",
        }
        botao.setProperty("actionState", estado or "idle")
        texto_botao = (
            f"{self._rotulos_acoes.get(acao_id, botao.text())}  "
            f"{marcadores.get(estado, '')}"
        ).rstrip()
        botao.setText(texto_botao)
        if resumo:
            botao.setToolTip(str(resumo))
        if estado in {"sending", "received", "executing"}:
            botao.setEnabled(False)
        elif estado in {
            "awaiting_confirmation", "confirmed", "partial", "failed",
        }:
            disponibilidade = self._estado_disponibilidade.get(
                acao_id, "unavailable",
            )
            botao.setEnabled(
                self._conectada
                and disponibilidade in {"available", "degraded"}
            )
        botao.style().unpolish(botao)
        botao.style().polish(botao)

    def definir_contexto(self, chave: str, valor: str) -> None:
        destino = self.contexto_valores.get(str(chave or ""))
        if destino is not None:
            destino.setText(str(valor or "—"))

    def registrar_evento(
        self,
        titulo: str,
    ) -> None:
        titulo = str(
            titulo or ""
        ).strip()

        if not titulo:
            return

        # Evita repetir o mesmo evento consecutivamente
        if (
            self._eventos
            and self._eventos[-1][1] == titulo
        ):
            return

        horario = time.strftime(
            "%H:%M"
        )

        self._eventos.append(
            (
                horario,
                titulo,
            )
        )

        self._renderizar_atividade()

    def _renderizar_atividade(
        self,
    ) -> None:
        eventos = list(
            reversed(self._eventos)
        )

        self.atividade_estado.setVisible(
            not bool(eventos)
        )

        for indice, linha in enumerate(
            self.atividade_linhas
        ):
            widget = linha["widget"]

            if indice >= len(eventos):
                widget.hide()
                continue

            horario, titulo = eventos[
                indice
            ]

            linha["text"].setText(
                titulo
            )

            linha["time"].setText(
                horario
            )

            widget.show()

    def _aplicar_memoria_recente(
        self,
        dashboard: dict,
    ) -> None:
        itens = dashboard.get(
            "memory_recent"
        )

        itens_validos = []

        if isinstance(itens, list):
            for item in itens[:3]:
                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                resumo = str(
                    item.get("summary")
                    or ""
                ).strip()

                if not resumo:
                    continue

                itens_validos.append(
                    item
                )

        # Estado real da memória
        saude = dashboard.get(
            "health"
        )

        memoria_saude = (
            saude.get("memory")
            if (
                isinstance(saude, dict)
                and isinstance(
                    saude.get("memory"),
                    dict,
                )
            )
            else {}
        )

        estado_memoria = str(
            memoria_saude.get("state")
            or "unavailable"
        )

        frescor_memoria = str(
            memoria_saude.get(
                "freshness"
            )
            or "unavailable"
        )

        memoria_disponivel = (
            estado_memoria
            != "unavailable"
            and frescor_memoria
            != "unavailable"
        )

        # =========================================
        # MEMÓRIA INDISPONÍVEL
        # =========================================

        if not memoria_disponivel:
            self.memoria_estado.setText(
                "Memória indisponível; "
                "não há uma leitura "
                "confiável agora."
            )

            self.memoria_estado.show()

            for linha in (
                self.memoria_linhas
            ):
                linha[
                    "widget"
                ].hide()

            return

        # =========================================
        # SEM CARTÕES
        # =========================================

        if not itens_validos:
            if frescor_memoria == "stale":
                texto_estado = (
                    "A leitura recente da "
                    "memória está "
                    "desatualizada."
                )

            elif estado_memoria == "degraded":
                texto_estado = (
                    "Memória parcialmente "
                    "disponível, sem cartões "
                    "públicos agora."
                )

            else:
                texto_estado = (
                    "Nenhuma memória recente "
                    "pública para mostrar."
                )

            self.memoria_estado.setText(
                texto_estado
            )
            self.memoria_estado.show()

            for linha in (
                self.memoria_linhas
            ):
                linha[
                    "widget"
                ].hide()

            return

        # =========================================
        # CARTÕES REAIS
        # =========================================

        self.memoria_estado.hide()

        icones = {
            "reminder": "◷",
            "preference": "♡",
            "task": "✓",
        }

        for indice, linha in enumerate(
            self.memoria_linhas
        ):
            if indice >= len(
                itens_validos
            ):
                linha["widget"].hide()
                continue

            item = itens_validos[
                indice
            ]

            tipo = str(
                item.get("kind")
                or "generic"
            )

            resumo = str(
                item.get("summary")
                or "Memória"
            ).strip()

            detalhe = str(
                item.get("detail")
                or ""
            ).strip()

            if frescor_memoria == "stale":
                detalhe = (
                    f"{detalhe} · dados antigos"
                    if detalhe
                    else "Dados antigos"
                )

            linha["icon"].setText(
                icones.get(
                    tipo,
                    "•",
                )
            )

            linha["summary"].setText(
                resumo
            )

            linha["detail"].setText(
                detalhe
            )

            linha["detail"].setVisible(
                bool(detalhe)
            )

            widget = linha["widget"]

            widget.setProperty(
                "memoryKind",
                tipo,
            )

            widget.style().unpolish(
                widget
            )
            widget.style().polish(
                widget
            )

            widget.show()

    def aplicar_dashboard(
        self,
        dashboard: dict,
    ) -> None:
        contexto = dashboard.get(
            "context"
        )

        if isinstance(contexto, dict):
            frescor_contexto = str(
                contexto.get("freshness")
                or "unavailable"
            )

            contexto_disponivel = (
                frescor_contexto
                in {"fresh", "stale"}
            )

            sufixo_contexto = (
                " · antigo"
                if frescor_contexto == "stale"
                else ""
            )

            self.definir_contexto(
                "projeto",
                (
                    str(
                        contexto.get("project")
                        or "Laylay"
                    )
                    + sufixo_contexto
                    if contexto_disponivel
                    else "Indisponível"
                ),
            )

            self.definir_contexto(
                "modo",
                (
                    str(
                        contexto.get("mode")
                        or "—"
                    )
                    + sufixo_contexto
                    if contexto_disponivel
                    else "Indisponível"
                ),
            )

            self.definir_contexto(
                "cidade",
                (
                    str(
                        contexto.get("city")
                        or "—"
                    )
                    + sufixo_contexto
                    if contexto_disponivel
                    else "Indisponível"
                ),
            )

            if not contexto_disponivel:
                jogo = "Indisponível"

            elif contexto.get(
                "game_active"
            ) is True:
                jogo = str(
                    contexto.get("game_name")
                    or "Ativo"
                )

            else:
                jogo = "Desativado"

            if frescor_contexto == "stale":
                jogo += " · antigo"

            self.definir_contexto(
                "jogo",
                jogo,
            )

        else:
            self.definir_contexto(
                "projeto",
                "Indisponível",
            )

            self.definir_contexto(
                "modo",
                "Indisponível",
            )

            self.definir_contexto(
                "cidade",
                "Indisponível",
            )

            self.definir_contexto(
                "jogo",
                "Indisponível",
            )


        # Atualiza memória independentemente do contexto
        self._aplicar_memoria_recente(
            dashboard
        )


        # Atualiza catálogo das ações rápidas
        self.aplicar_catalogo_acoes(
            dashboard.get(
                "quick_actions"
            )
        )


        # Estado geral do painel
        status = str(
            dashboard.get("status")
            or "unavailable"
        )

        self.estado.setText({
            "ok": "●  Vivo",
            "partial": "●  Parcial",
            "unavailable": "●  Sem dados",
        }.get(
            status,
            "●  Sem dados",
        ))

    def invalidar_dashboard(self) -> None:
        self.estado.setText("●  Reconectando")
        self.definir_contexto("modo", "—")
        self.definir_contexto("cidade", "—")
        self.definir_contexto("jogo", "Não observado")
        self.memoria_estado.setText(
            "Aguardando uma projeção segura da memória."
        )
        self.memoria_estado.show()

        for linha in self.memoria_linhas:
            linha["widget"].hide()


class PainelLateralDashboard(QWidget):
    acao_solicitada = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dashboardRail")
        self.setMinimumWidth(286)
        self.setMaximumWidth(315)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(11)

        sistema = CartaoDashboard("Sistema", subtitulo="P2")
        self.metricas: dict[str, QLabel] = {}
        self.barras_metricas: dict[str, QProgressBar] = {}
        for chave, rotulo in (
            ("cpu", "CPU"), ("ram", "RAM"), ("temperatura", "Temp."),
            ("disco", "Disco"), ("uptime", "Tempo ligado"),
        ):
            linha, valor = _linha_valor(rotulo)
            self.metricas[chave] = valor
            sistema.layout_principal.addWidget(linha)
            if chave != "uptime":
                barra = QProgressBar()
                barra.setObjectName("railMetricProgress")
                barra.setRange(0, 100)
                barra.setValue(0)
                barra.setTextVisible(False)
                self.barras_metricas[chave] = barra
                sistema.layout_principal.addWidget(barra)
        self.sistema_estado = QLabel("Aguardando telemetria real da mente.")
        self.sistema_estado.setObjectName("dashboardEmpty")
        self.sistema_estado.setWordWrap(True)
        sistema.layout_principal.addWidget(self.sistema_estado)
        layout.addWidget(sistema)

        musica = CartaoDashboard("Música", subtitulo="P4")
        musica_topo = QHBoxLayout()
        musica_topo.setSpacing(11)
        self.musica_capa = CapaMusicaGenerica(68)
        musica_textos = QVBoxLayout()
        musica_textos.setSpacing(4)
        self.musica_titulo = QLabel("Nenhuma faixa confirmada")
        self.musica_titulo.setObjectName("musicTitle")
        self.musica_titulo.setWordWrap(True)
        self.musica_detalhe = QLabel("O player será ligado ao estado observado da extensão.")
        self.musica_detalhe.setObjectName("dashboardEmpty")
        self.musica_detalhe.setWordWrap(True)
        musica_textos.addWidget(self.musica_titulo)
        musica_textos.addWidget(self.musica_detalhe)
        musica_textos.addStretch()
        musica_topo.addWidget(self.musica_capa)
        musica_topo.addLayout(musica_textos, 1)
        self.musica_progresso = QProgressBar()
        self.musica_progresso.setRange(0, 1000)
        self.musica_progresso.setValue(0)
        self.musica_progresso.setTextVisible(False)
        tempos = QHBoxLayout()
        self.musica_posicao = QLabel("0:00")
        self.musica_duracao = QLabel("0:00")
        for tempo in (self.musica_posicao, self.musica_duracao):
            tempo.setObjectName("dashboardMetricLabel")
        tempos.addWidget(self.musica_posicao)
        tempos.addStretch()
        tempos.addWidget(self.musica_duracao)
        controles = QHBoxLayout()
        controles.addStretch()
        self.musica_botoes: dict[str, QPushButton] = {}
        for acao_id, icone, dica in (
            ("media_previous", "previous", "Faixa anterior"),
            ("media_toggle", "play", "Pausar ou continuar"),
            ("media_next", "next", "Próxima faixa"),
        ):
            botao = QPushButton()
            botao.setObjectName("railMusicControl")
            botao.setIcon(icone_terminal(icone))
            botao.setIconSize(QSize(20, 20))
            botao.setToolTip(dica)
            botao.setAccessibleName(dica)
            botao.setEnabled(False)
            botao.clicked.connect(
                lambda _v=False, aid=acao_id: self._solicitar_musica(aid)
            )
            self.musica_botoes[acao_id] = botao
            controles.addWidget(botao)
        controles.addStretch()
        musica.layout_principal.addLayout(musica_topo)
        musica.layout_principal.addWidget(self.musica_progresso)
        musica.layout_principal.addLayout(tempos)
        musica.layout_principal.addLayout(controles)
        layout.addWidget(musica)

        rotinas = CartaoDashboard("Rotinas", subtitulo="P4")
        self.rotinas_estado = QLabel("Aguardando rotinas confirmadas pela agenda.")
        self.rotinas_estado.setObjectName("dashboardEmpty")
        self.rotinas_estado.setWordWrap(True)
        rotinas.layout_principal.addWidget(self.rotinas_estado)
        layout.addWidget(rotinas)

        jogo = CartaoDashboard("Modo jogo", subtitulo="P4")
        self.jogo_estado = QLabel("Estado ainda não exposto à interface")
        self.jogo_estado.setObjectName("dashboardEmpty")
        self.jogo_estado.setWordWrap(True)
        jogo.layout_principal.addWidget(self.jogo_estado)
        layout.addWidget(jogo)
        layout.addStretch()
        self._conectada = False
        self._controles_musica = False
        self._estado_musica = "unavailable"
        self._musica_posicao_base = 0.0
        self._musica_duracao_base = 0.0
        self._musica_observada_em = 0.0
        self._relogio_musica = QTimer(self)
        self._relogio_musica.setInterval(1000)
        self._relogio_musica.timeout.connect(self._atualizar_relogio_musica)
        self._relogio_musica.start()

    def _solicitar_musica(self, acao_id: str) -> None:
        pedidos = {
            "media_previous": "volta para a música anterior",
            "media_next": "vai para a próxima música",
            "media_toggle": (
                "pausa a música" if self._estado_musica == "playing"
                else "continua a música"
            ),
        }
        pedido = pedidos.get(acao_id)
        if pedido:
            self.acao_solicitada.emit(acao_id, pedido)

    def definir_conectada(self, conectada: bool) -> None:
        self._conectada = bool(conectada)
        self._atualizar_controles_musica()

    def definir_estado_acao(self, acao_id: str, estado: str, _resumo: str = "") -> None:
        botao = self.musica_botoes.get(str(acao_id or ""))
        if botao is None:
            return
        pendente = estado in {"sending", "received", "executing"}
        botao.setEnabled(
            not pendente and self._conectada and self._controles_musica
        )

    def _atualizar_controles_musica(self) -> None:
        habilitar = self._conectada and self._controles_musica
        for botao in self.musica_botoes.values():
            botao.setEnabled(habilitar)

    def _atualizar_relogio_musica(self) -> None:
        if self._estado_musica == "unavailable":
            return
        idade = max(0.0, time.time() - self._musica_observada_em)
        posicao = self._musica_posicao_base
        if self._estado_musica == "playing" and self._musica_observada_em > 0:
            posicao += idade
        if self._musica_duracao_base > 0:
            posicao = min(posicao, self._musica_duracao_base)
        self.musica_progresso.setValue(
            max(0, min(1000, int((posicao / self._musica_duracao_base) * 1000)))
            if self._musica_duracao_base > 0 else 0
        )
        self.musica_posicao.setText(_tempo_player(posicao))
        if idade > 12.0 and self._controles_musica:
            self._controles_musica = False
            self._atualizar_controles_musica()

    def aplicar_dashboard(self, dashboard: dict) -> None:
        sistema = dashboard.get("system")
        if not isinstance(sistema, dict):
            sistema = {}
        campos = {
            "cpu": (sistema.get("cpu_percent"), False),
            "ram": (sistema.get("ram_percent"), False),
            "disco": (sistema.get("disk_percent"), False),
            "temperatura": (sistema.get("temperature_c"), False),
            "uptime": (sistema.get("uptime_seconds"), True),
        }
        for chave, (metrica, uptime) in campos.items():
            self.metricas[chave].setText(_texto_metrica(metrica, uptime=uptime))
            barra = self.barras_metricas.get(chave)
            if barra is not None:
                try:
                    valor_barra = float(metrica.get("value")) if isinstance(metrica, dict) else 0.0
                except (TypeError, ValueError):
                    valor_barra = 0.0
                barra.setValue(max(0, min(100, round(valor_barra))))
        disponiveis = sum(valor.text() != "—" for valor in self.metricas.values())
        self.sistema_estado.setText(
            "Telemetria observada pela mente. Alguns sensores não estão disponíveis."
            if 0 < disponiveis < len(self.metricas)
            else "Telemetria observada pela mente."
            if disponiveis
            else "Telemetria do sistema indisponível."
        )
        contexto = dashboard.get("context")
        frescor = (
            str(contexto.get("freshness") or "unavailable")
            if isinstance(contexto, dict) else "unavailable"
        )
        if frescor == "unavailable":
            self.jogo_estado.setText("Estado do jogo indisponível")
        elif isinstance(contexto, dict) and contexto.get("game_active") is True:
            nome = str(contexto.get("game_name") or "Jogo detectado")
            sufixo = " · dados antigos" if frescor == "stale" else ""
            self.jogo_estado.setText(f"Ativo · {nome}{sufixo}")
        else:
            self.jogo_estado.setText(
                "Desativado · dados antigos" if frescor == "stale"
                else "Desativado"
            )
        musica = dashboard.get("music")
        if not isinstance(musica, dict) or musica.get("freshness") == "unavailable":
            self._estado_musica = "unavailable"
            self._controles_musica = False
            self.musica_titulo.setText("Nenhuma faixa confirmada")
            self.musica_detalhe.setText("Player indisponível ou ainda não observado.")
            self.musica_capa.definir_titulo("")
            self.musica_capa.carregar("")
            self.musica_progresso.setValue(0)
            self.musica_posicao.setText("0:00")
            self.musica_duracao.setText("0:00")
            self._musica_posicao_base = 0.0
            self._musica_duracao_base = 0.0
            self._musica_observada_em = 0.0
        else:
            self._estado_musica = str(musica.get("state") or "unknown")
            self._controles_musica = bool(musica.get("controls_available"))
            titulo_musica = str(musica.get("title") or "Faixa sem título")
            self.musica_titulo.setText(titulo_musica)
            self.musica_capa.definir_titulo(titulo_musica)
            self.musica_capa.carregar(str(musica.get("artwork_url") or ""))
            estado = {
                "playing": "Tocando", "paused": "Pausada",
                "ended": "Finalizada", "unknown": "Estado não confirmado",
            }.get(str(musica.get("state") or ""), "Estado não confirmado")
            canal = str(musica.get("channel") or "").strip()
            antigo = " · dados antigos" if musica.get("freshness") == "stale" else ""
            self.musica_detalhe.setText(
                f"{estado}" + (f" · {canal}" if canal else "") + antigo
            )
            posicao = float(musica.get("position_seconds") or 0.0)
            duracao = float(musica.get("duration_seconds") or 0.0)
            self._musica_posicao_base = posicao
            self._musica_duracao_base = duracao
            self._musica_observada_em = float(musica.get("observed_at") or 0.0)
            self.musica_progresso.setValue(
                max(0, min(1000, int((posicao / duracao) * 1000)))
                if duracao > 0 else 0
            )
            self.musica_posicao.setText(_tempo_player(posicao))
            self.musica_duracao.setText(_tempo_player(duracao))
            self.musica_botoes["media_toggle"].setIcon(
                icone_terminal("pause" if self._estado_musica == "playing" else "play")
            )
        self._atualizar_controles_musica()
        rotinas = dashboard.get("routines")
        itens_rotina = (
            list(rotinas.get("items") or ())
            if isinstance(rotinas, dict) and rotinas.get("freshness") != "unavailable"
            else []
        )
        if itens_rotina:
            linhas = [
                f"• {item.get('name') or 'Rotina'} · {item.get('time') or '—'}"
                for item in itens_rotina[:3] if isinstance(item, dict)
            ]
            self.rotinas_estado.setText("\n".join(linhas))
        else:
            self.rotinas_estado.setText(
                "Nenhuma rotina recorrente confirmada."
                if isinstance(rotinas, dict) and rotinas.get("freshness") != "unavailable"
                else "Rotinas indisponíveis."
            )

    def invalidar_dashboard(self) -> None:
        for valor in self.metricas.values():
            valor.setText("—")
        for barra in self.barras_metricas.values():
            barra.setValue(0)
        self.sistema_estado.setText("Aguardando telemetria real da mente.")
        self.jogo_estado.setText("Estado indisponível durante a reconexão")
        self.musica_titulo.setText("Nenhuma faixa confirmada")
        self.musica_detalhe.setText("Aguardando estado observado do player.")
        self.musica_capa.carregar("")
        self._estado_musica = "unavailable"
        self._controles_musica = False
        self.musica_progresso.setValue(0)
        self.musica_posicao.setText("0:00")
        self.musica_duracao.setText("0:00")
        self._musica_posicao_base = 0.0
        self._musica_duracao_base = 0.0
        self._musica_observada_em = 0.0
        self._atualizar_controles_musica()
        self.rotinas_estado.setText("Aguardando rotinas confirmadas pela agenda.")


def _cabecalho_pagina(titulo: str, descricao: str) -> tuple[QLabel, QLabel, QLabel]:
    etapa = QLabel("TERMINAL 3.0 · P4")
    etapa.setObjectName("eyebrow")
    nome = QLabel(titulo)
    nome.setObjectName("pageTitle")
    texto = QLabel(descricao)
    texto.setObjectName("pageDescription")
    texto.setWordWrap(True)
    return etapa, nome, texto


def _tempo_player(segundos: object) -> str:
    try:
        total = max(0, int(float(segundos)))
    except (TypeError, ValueError):
        total = 0
    minutos, segundo = divmod(total, 60)
    horas, minutos = divmod(minutos, 60)
    return f"{horas}:{minutos:02d}:{segundo:02d}" if horas else f"{minutos}:{segundo:02d}"


class PaginaMusicaLegada(QWidget):
    """Player observado; nenhum botão altera o estado local por antecipação."""

    acao_solicitada = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._conectada = False
        self._controles_disponiveis = False
        self._estado_observado = "unavailable"
        self._posicao_base = 0.0
        self._duracao_base = 0.0
        self._observado_em = 0.0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(54, 36, 68, 46)
        layout.setSpacing(12)
        for widget in _cabecalho_pagina(
            "Música",
            "O que a extensão realmente observou no player — sem confundir uma aba aberta com áudio tocando.",
        ):
            layout.addWidget(widget)
        cartao = CartaoDashboard("Player observado", subtitulo="extensão")
        self.capa = QLabel("♫")
        self.capa.setObjectName("musicArtwork")
        self.capa.setAlignment(Qt.AlignCenter)
        self.capa.setFixedSize(176, 99)
        self._artwork_url = ""
        self._rede = QNetworkAccessManager(self)
        self._rede.finished.connect(self._capa_recebida)
        self.titulo = QLabel("Nenhuma faixa confirmada")
        self.titulo.setObjectName("pageTitle")
        self.canal = QLabel("Aguardando o player")
        self.canal.setObjectName("dashboardEmpty")
        self.progresso = QProgressBar()
        self.progresso.setObjectName("musicProgress")
        self.progresso.setRange(0, 1000)
        self.progresso.setValue(0)
        self.progresso.setTextVisible(False)
        self.tempo = QLabel("0:00 / 0:00")
        self.tempo.setObjectName("dashboardMetricLabel")
        self.estado = QLabel("Indisponível")
        self.estado.setObjectName("dashboardEmpty")
        controles = QHBoxLayout()
        self.botoes: dict[str, QPushButton] = {}
        for acao_id, texto in (
            ("media_previous", "◀  Anterior"),
            ("media_toggle", "▶  Continuar"),
            ("media_next", "Próxima  ▶|"),
        ):
            botao = QPushButton(texto)
            botao.setProperty("dashboardAction", True)
            botao.setEnabled(False)
            botao.clicked.connect(
                lambda _v=False, aid=acao_id: self._solicitar(aid)
            )
            self.botoes[acao_id] = botao
            controles.addWidget(botao)
        cartao.layout_principal.addWidget(self.capa, 0, Qt.AlignLeft)
        cartao.layout_principal.addWidget(self.titulo)
        cartao.layout_principal.addWidget(self.canal)
        cartao.layout_principal.addWidget(self.progresso)
        cartao.layout_principal.addWidget(self.tempo)
        cartao.layout_principal.addLayout(controles)
        cartao.layout_principal.addWidget(self.estado)
        layout.addSpacing(8)
        layout.addWidget(cartao)
        layout.addStretch()
        self._relogio = QTimer(self)
        self._relogio.setInterval(1000)
        self._relogio.timeout.connect(self._atualizar_relogio)
        self._relogio.start()

    def _solicitar(self, acao_id: str) -> None:
        pedidos = {
            "media_previous": "volta para a música anterior",
            "media_next": "vai para a próxima música",
            "media_toggle": (
                "pausa a música" if self._estado_observado == "playing"
                else "continua a música"
            ),
        }
        pedido = pedidos.get(acao_id)
        if pedido:
            self.acao_solicitada.emit(acao_id, pedido)

    def aplicar_dashboard(self, dashboard: dict) -> None:
        musica = dashboard.get("music")
        if not isinstance(musica, dict) or musica.get("freshness") == "unavailable":
            self.invalidar("Player não observado")
            return
        self._estado_observado = str(musica.get("state") or "unknown")
        self._controles_disponiveis = bool(musica.get("controls_available"))
        self.titulo.setText(str(musica.get("title") or "Faixa sem título"))
        canal = str(musica.get("channel") or "Canal não informado")
        playlist = str(musica.get("playlist") or "").strip()
        self.canal.setText(canal + (f" · playlist {playlist}" if playlist else ""))
        self._carregar_capa(str(musica.get("artwork_url") or ""))
        posicao = float(musica.get("position_seconds") or 0.0)
        duracao = float(musica.get("duration_seconds") or 0.0)
        self._posicao_base = posicao
        self._duracao_base = duracao
        self._observado_em = float(musica.get("observed_at") or 0.0)
        self.progresso.setValue(
            max(0, min(1000, int((posicao / duracao) * 1000))) if duracao > 0 else 0
        )
        self.tempo.setText(f"{_tempo_player(posicao)} / {_tempo_player(duracao)}")
        estados = {
            "playing": "Tocando · estado observado",
            "paused": "Pausada · estado observado",
            "ended": "Finalizada · estado observado",
            "unknown": "Player encontrado; reprodução não confirmada",
        }
        sufixo = " · dados antigos" if musica.get("freshness") == "stale" else ""
        self.estado.setText(estados.get(self._estado_observado, "Indisponível") + sufixo)
        self.botoes["media_toggle"].setText(
            "Ⅱ  Pausar" if self._estado_observado == "playing" else "▶  Continuar"
        )
        self._atualizar_botoes()

    def definir_conectada(self, conectada: bool) -> None:
        self._conectada = bool(conectada)
        self._atualizar_botoes()

    def _carregar_capa(self, url: str) -> None:
        if url == self._artwork_url:
            return
        self._artwork_url = url
        self.capa.setPixmap(QPixmap())
        self.capa.setText("♫")
        if not url.startswith("https://i.ytimg.com/vi/"):
            return
        pedido = QNetworkRequest(QUrl(url))
        self._rede.get(pedido)

    def _capa_recebida(self, resposta: QNetworkReply) -> None:
        try:
            if resposta.error() != QNetworkReply.NoError:
                return
            pixmap = QPixmap()
            if pixmap.loadFromData(bytes(resposta.readAll())):
                self.capa.setText("")
                self.capa.setPixmap(
                    pixmap.scaled(
                        self.capa.size(), Qt.KeepAspectRatioByExpanding,
                        Qt.SmoothTransformation,
                    )
                )
        finally:
            resposta.deleteLater()

    def _atualizar_botoes(self) -> None:
        habilitar = self._conectada and self._controles_disponiveis
        for botao in self.botoes.values():
            botao.setEnabled(habilitar)

    def _atualizar_relogio(self) -> None:
        if self._estado_observado == "unavailable":
            return
        idade = max(0.0, time.time() - self._observado_em)
        posicao = self._posicao_base
        if self._estado_observado == "playing" and self._observado_em > 0:
            posicao += idade
        if self._duracao_base > 0:
            posicao = min(posicao, self._duracao_base)
        self.progresso.setValue(
            max(0, min(1000, int((posicao / self._duracao_base) * 1000)))
            if self._duracao_base > 0 else 0
        )
        self.tempo.setText(
            f"{_tempo_player(posicao)} / {_tempo_player(self._duracao_base)}"
        )
        if idade > 12.0 and self._controles_disponiveis:
            self._controles_disponiveis = False
            self._atualizar_botoes()

    def definir_estado_acao(self, acao_id: str, estado: str, resumo: str = "") -> None:
        botao = self.botoes.get(str(acao_id or ""))
        if botao is None:
            return
        pendente = estado in {"sending", "received", "executing"}
        botao.setEnabled(not pendente and self._conectada and self._controles_disponiveis)
        if resumo:
            self.estado.setText(resumo)

    def invalidar(self, texto: str = "Aguardando estado observado do player") -> None:
        self._controles_disponiveis = False
        self._estado_observado = "unavailable"
        self.titulo.setText("Nenhuma faixa confirmada")
        self._carregar_capa("")
        self.canal.setText("Aguardando o player")
        self.progresso.setValue(0)
        self.tempo.setText("0:00 / 0:00")
        self.estado.setText(texto)
        self._posicao_base = 0.0
        self._duracao_base = 0.0
        self._observado_em = 0.0
        self._atualizar_botoes()


class PaginaAutomacao(QWidget):
    """Rotinas persistidas e modo jogo observado, sem toggles otimistas."""

    acao_solicitada = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._conectada = False
        self._rotinas: list[dict] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(54, 36, 68, 46)
        layout.setSpacing(12)
        for widget in _cabecalho_pagina(
            "Automação",
            "Rotinas recorrentes confirmadas pela agenda e modo jogo detectado pela própria Laylay.",
        ):
            layout.addWidget(widget)
        self.cartao_rotinas = CartaoDashboard("Rotinas", subtitulo="agenda")
        self.rotinas_estado = QLabel("Aguardando a agenda")
        self.rotinas_estado.setObjectName("dashboardEmpty")
        self.rotinas_estado.setWordWrap(True)
        self.cartao_rotinas.layout_principal.addWidget(self.rotinas_estado)
        self.rotina_botoes: list[QPushButton] = []
        for indice in range(6):
            botao = QPushButton()
            botao.setProperty("dashboardAction", True)
            botao.hide()
            botao.clicked.connect(
                lambda _v=False, i=indice: self._cancelar_rotina(i)
            )
            self.rotina_botoes.append(botao)
            self.cartao_rotinas.layout_principal.addWidget(botao)
        jogo = CartaoDashboard("Modo jogo", subtitulo="automático")
        self.jogo_estado = QLabel("Não observado")
        self.jogo_estado.setObjectName("dashboardMetricValue")
        self.jogo_detalhe = QLabel(
            "A detecção é automática; não existe um interruptor manual confiável nesta versão."
        )
        self.jogo_detalhe.setObjectName("dashboardEmpty")
        self.jogo_detalhe.setWordWrap(True)
        jogo.layout_principal.addWidget(self.jogo_estado)
        jogo.layout_principal.addWidget(self.jogo_detalhe)
        layout.addSpacing(8)
        layout.addWidget(self.cartao_rotinas)
        layout.addWidget(jogo)
        layout.addStretch()

    def _cancelar_rotina(self, indice: int) -> None:
        if not (0 <= indice < len(self._rotinas)):
            return
        nome = str(self._rotinas[indice].get("name") or "").strip()
        if nome:
            self.acao_solicitada.emit(
                "routine_cancel", f"cancela o agendamento {nome}",
            )

    def aplicar_dashboard(self, dashboard: dict) -> None:
        rotinas = dashboard.get("routines")
        frescor = str(rotinas.get("freshness") or "unavailable") if isinstance(rotinas, dict) else "unavailable"
        self._rotinas = [
            dict(item) for item in list(rotinas.get("items") or ())[:6]
            if isinstance(item, dict)
        ] if isinstance(rotinas, dict) and frescor != "unavailable" else []
        self.rotinas_estado.setText(
            "Nenhuma rotina recorrente confirmada."
            if not self._rotinas and frescor != "unavailable"
            else "Rotinas indisponíveis."
            if frescor == "unavailable"
            else "Dados antigos; alterações continuam exigindo confirmação."
            if frescor == "stale"
            else f"{len(self._rotinas)} rotina(s) ativa(s)."
        )
        for indice, botao in enumerate(self.rotina_botoes):
            if indice >= len(self._rotinas):
                botao.hide()
                continue
            item = self._rotinas[indice]
            dias = ", ".join(item.get("days") or ()) or "dias não informados"
            botao.setText(
                f"{item.get('name') or 'Rotina'} · {item.get('time') or '—'} · {dias}   ×"
            )
            botao.setEnabled(
                self._conectada and item.get("can_disable") is True
            )
            botao.show()
        contexto = dashboard.get("context")
        if not isinstance(contexto, dict) or contexto.get("freshness") == "unavailable":
            self.jogo_estado.setText("Indisponível")
        elif contexto.get("game_active") is True:
            self.jogo_estado.setText(
                f"Ativo · {contexto.get('game_name') or 'Jogo detectado'}"
            )
        else:
            self.jogo_estado.setText("Desativado")

    def definir_conectada(self, conectada: bool) -> None:
        self._conectada = bool(conectada)
        for indice, botao in enumerate(self.rotina_botoes):
            if indice < len(self._rotinas):
                botao.setEnabled(
                    self._conectada and self._rotinas[indice].get("can_disable") is True
                )

    def definir_estado_acao(self, acao_id: str, estado: str, resumo: str = "") -> None:
        if acao_id != "routine_cancel":
            return
        pendente = estado in {"sending", "received", "executing"}
        for botao in self.rotina_botoes:
            if botao.isVisible():
                botao.setEnabled(not pendente and self._conectada)
        if resumo:
            self.rotinas_estado.setText(resumo)

    def invalidar(self) -> None:
        self._rotinas = []
        self.rotinas_estado.setText("Aguardando a agenda")
        self.jogo_estado.setText("Indisponível")
        for botao in self.rotina_botoes:
            botao.hide()


class PaginaMemoria(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(54, 36, 68, 46)
        layout.setSpacing(12)
        for widget in _cabecalho_pagina(
            "Memória",
            "Uma projeção mínima da memória canônica, com origem explícita e sem expor dados sensíveis.",
        ):
            layout.addWidget(widget)
        self.estado = QLabel("Aguardando memória")
        self.estado.setObjectName("dashboardEmpty")
        self.itens = [CartaoDashboard("—") for _ in range(3)]
        layout.addWidget(self.estado)
        for cartao in self.itens:
            cartao.hide()
            layout.addWidget(cartao)
        layout.addStretch()

    def aplicar_dashboard(self, dashboard: dict) -> None:
        saude = dashboard.get("health") if isinstance(dashboard.get("health"), dict) else {}
        memoria = saude.get("memory") if isinstance(saude.get("memory"), dict) else {}
        disponivel = memoria.get("state") != "unavailable" and memoria.get("freshness") != "unavailable"
        itens = list(dashboard.get("memory_recent") or ())[:3] if disponivel else []
        self.estado.setText(
            str(memoria.get("label") or "Memória ativa")
            if disponivel else "Memória indisponível"
        )
        nomes = {"reminder": "Lembrete", "preference": "Preferência", "task": "Ação confirmada"}
        for indice, cartao in enumerate(self.itens):
            if indice >= len(itens) or not isinstance(itens[indice], dict):
                cartao.hide()
                continue
            item = itens[indice]
            titulo = cartao.layout_principal.itemAt(0).layout().itemAt(0).widget()
            titulo.setText(nomes.get(str(item.get("kind") or ""), "Memória"))
            while cartao.layout_principal.count() > 1:
                filho = cartao.layout_principal.takeAt(1)
                if filho.widget():
                    filho.widget().deleteLater()
            resumo = QLabel(str(item.get("summary") or ""))
            resumo.setWordWrap(True)
            detalhe = QLabel(str(item.get("detail") or ""))
            detalhe.setObjectName("dashboardEmpty")
            detalhe.setWordWrap(True)
            cartao.layout_principal.addWidget(resumo)
            cartao.layout_principal.addWidget(detalhe)
            cartao.show()

    def invalidar(self) -> None:
        self.estado.setText("Aguardando memória")
        for cartao in self.itens:
            cartao.hide()


class PaginaSistema(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._historico: dict[str, deque[float]] = {
            chave: deque(maxlen=24) for chave in ("cpu", "ram", "disk")
        }
        layout = QVBoxLayout(self)
        layout.setContentsMargins(54, 36, 68, 46)
        layout.setSpacing(12)
        for widget in _cabecalho_pagina(
            "Sistema",
            "Métricas locais observadas em segundo plano, sem bloquear a conversa.",
        ):
            layout.addWidget(widget)
        grade = QGridLayout()
        self.valores: dict[str, QLabel] = {}
        self.barras: dict[str, QProgressBar] = {}
        self.graficos: dict[str, QLabel] = {}
        for indice, (chave, titulo) in enumerate((
            ("cpu", "CPU"), ("ram", "Memória RAM"), ("disk", "Disco"),
        )):
            cartao = CartaoDashboard(titulo)
            valor = QLabel("—")
            valor.setObjectName("pageTitle")
            barra = QProgressBar()
            barra.setRange(0, 100)
            barra.setValue(0)
            barra.setTextVisible(False)
            grafico = QLabel("—")
            grafico.setObjectName("systemSparkline")
            cartao.layout_principal.addWidget(valor)
            cartao.layout_principal.addWidget(barra)
            cartao.layout_principal.addWidget(grafico)
            self.valores[chave] = valor
            self.barras[chave] = barra
            self.graficos[chave] = grafico
            grade.addWidget(cartao, 0, indice)
        layout.addLayout(grade)
        detalhes = CartaoDashboard("Outros sensores")
        self.temperatura = QLabel("Temperatura · —")
        self.uptime = QLabel("Tempo ligado · —")
        self.estado = QLabel("Aguardando telemetria")
        self.estado.setObjectName("dashboardEmpty")
        detalhes.layout_principal.addWidget(self.temperatura)
        detalhes.layout_principal.addWidget(self.uptime)
        detalhes.layout_principal.addWidget(self.estado)
        layout.addWidget(detalhes)
        layout.addStretch()

    @staticmethod
    def _sparkline(valores: deque[float]) -> str:
        blocos = "▁▂▃▄▅▆▇█"
        return "".join(blocos[min(7, max(0, int(v / 12.5)))] for v in valores) or "—"

    def aplicar_dashboard(self, dashboard: dict) -> None:
        sistema = dashboard.get("system") if isinstance(dashboard.get("system"), dict) else {}
        for chave, campo in (("cpu", "cpu_percent"), ("ram", "ram_percent"), ("disk", "disk_percent")):
            metrica = sistema.get(campo) if isinstance(sistema.get(campo), dict) else {}
            valor = metrica.get("value")
            if valor is None:
                self.valores[chave].setText("—")
                self.barras[chave].setValue(0)
                continue
            numero = max(0.0, min(100.0, float(valor)))
            if metrica.get("freshness") == "fresh":
                self._historico[chave].append(numero)
            sufixo = " · antigo" if metrica.get("freshness") == "stale" else ""
            self.valores[chave].setText(f"{numero:.0f}%{sufixo}")
            self.barras[chave].setValue(int(numero))
            self.graficos[chave].setText(self._sparkline(self._historico[chave]))
        self.temperatura.setText(
            f"Temperatura · {_texto_metrica(sistema.get('temperature_c'))}"
        )
        self.uptime.setText(
            f"Tempo ligado · {_texto_metrica(sistema.get('uptime_seconds'), uptime=True)}"
        )
        self.estado.setText(
            "Telemetria parcial; sensores ausentes aparecem como —."
            if any(valor.text() == "—" for valor in self.valores.values())
            else "Telemetria local atualizada."
        )

    def invalidar(self) -> None:
        for chave in self.valores:
            self.valores[chave].setText("—")
            self.barras[chave].setValue(0)
        self.temperatura.setText("Temperatura · —")
        self.uptime.setText("Tempo ligado · —")
        self.estado.setText("Aguardando telemetria")


class PaginaModulo(QWidget):
    """Página honesta para módulos que ganham implementação nas próximas fases."""

    def __init__(self, titulo: str, descricao: str, fase: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(54, 42, 68, 50)
        layout.setSpacing(11)
        etapa = QLabel(f"TERMINAL 3.0 · {fase}")
        etapa.setObjectName("eyebrow")
        nome = QLabel(titulo)
        nome.setObjectName("pageTitle")
        texto = QLabel(descricao)
        texto.setObjectName("pageDescription")
        texto.setWordWrap(True)
        estado = QFrame()
        estado.setObjectName("modulePlaceholder")
        estado_lay = QVBoxLayout(estado)
        estado_lay.setContentsMargins(20, 18, 20, 18)
        estado_titulo = QLabel("Aguardando integração real")
        estado_titulo.setObjectName("dashboardCardTitle")
        estado_texto = QLabel(
            "A estrutura visual já está reservada. Os dados e controles só serão "
            "ativados quando a mente puder observá-los e confirmar os resultados."
        )
        estado_texto.setObjectName("dashboardEmpty")
        estado_texto.setWordWrap(True)
        estado_lay.addWidget(estado_titulo)
        estado_lay.addWidget(estado_texto)
        layout.addWidget(etapa)
        layout.addWidget(nome)
        layout.addWidget(texto)
        layout.addSpacing(12)
        layout.addWidget(estado)
        layout.addStretch()
