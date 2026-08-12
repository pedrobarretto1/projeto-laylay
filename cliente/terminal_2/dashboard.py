"""Componentes visuais do dashboard do Terminal Laylay 3.0.

Este módulo não consulta memória, sistema ou executores. Ele recebe projeções
sanitizadas da janela principal e encaminha ações disponíveis pelo mesmo canal
textual usado pela conversa.
"""

from __future__ import annotations

from collections import deque

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from mente_laylay.integracao.acoes_terminal import ACOES_RAPIDAS_TERMINAL


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
        self.setMinimumWidth(320)
        self.setMaximumWidth(370)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(13, 13, 13, 13)
        layout.setSpacing(11)

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
            texto = str(definicao["label"])
            comando = str(definicao.get("request") or "")
            botao = QPushButton(texto)
            botao.setProperty("dashboardAction", True)
            botao.setProperty("actionState", "idle")
            botao.setEnabled(False)
            if comando:
                botao.clicked.connect(
                    lambda _marcado=False, aid=acao_id, pedido=comando:
                    self.acao_solicitada.emit(aid, pedido)
                )
            self.acoes[texto] = botao
            self._acoes_por_id[acao_id] = botao
            self._rotulos_acoes[acao_id] = texto
            self._estado_disponibilidade[acao_id] = (
                "available" if comando else
                "requires_input" if definicao.get("intent") else "unavailable"
            )
            grade.addWidget(botao, indice // 2, indice % 2)
        acoes.layout_principal.addLayout(grade)
        layout.addWidget(acoes)

        contexto = CartaoDashboard("Contexto atual", subtitulo="sanitizado")
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

        memoria = CartaoDashboard("Memória recente")
        self.memoria_estado = QLabel(
            "Aguardando uma projeção segura da memória. Nenhum fato será inventado aqui."
        )
        self.memoria_estado.setObjectName("dashboardEmpty")
        self.memoria_estado.setWordWrap(True)
        memoria.layout_principal.addWidget(self.memoria_estado)
        layout.addWidget(memoria)

        atividade = CartaoDashboard("Atividade recente")
        self.atividade_itens = QLabel("Tudo quieto nesta sessão.")
        self.atividade_itens.setObjectName("dashboardActivity")
        self.atividade_itens.setWordWrap(True)
        atividade.layout_principal.addWidget(self.atividade_itens)
        layout.addWidget(atividade)
        layout.addStretch()
        self._eventos: deque[str] = deque(maxlen=3)
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

    def registrar_evento(self, titulo: str) -> None:
        titulo = str(titulo or "").strip()
        if not titulo:
            return
        if not self._eventos or self._eventos[-1] != titulo:
            self._eventos.append(titulo)
        self.atividade_itens.setText("\n".join(f"• {item}" for item in self._eventos))

    def aplicar_dashboard(self, dashboard: dict) -> None:
        contexto = dashboard.get("context")
        if isinstance(contexto, dict):
            frescor_contexto = str(
                contexto.get("freshness") or "unavailable"
            )
            contexto_disponivel = frescor_contexto in {"fresh", "stale"}
            sufixo_contexto = " · antigo" if frescor_contexto == "stale" else ""
            self.definir_contexto(
                "projeto",
                str(contexto.get("project") or "Laylay") + sufixo_contexto
                if contexto_disponivel else "Indisponível",
            )
            self.definir_contexto(
                "modo",
                str(contexto.get("mode") or "—") + sufixo_contexto
                if contexto_disponivel else "Indisponível",
            )
            self.definir_contexto(
                "cidade",
                str(contexto.get("city") or "—") + sufixo_contexto
                if contexto_disponivel else "Indisponível",
            )
            if not contexto_disponivel:
                jogo = "Indisponível"
            elif contexto.get("game_active") is True:
                jogo = str(contexto.get("game_name") or "Ativo")
            else:
                jogo = "Desativado"
            if frescor_contexto == "stale":
                jogo += " · antigo"
            self.definir_contexto("jogo", jogo)
        itens = dashboard.get("memory_recent")
        linhas: list[str] = []
        icones = {"reminder": "◷", "preference": "♡", "task": "✓"}
        if isinstance(itens, list):
            for item in itens[:3]:
                if not isinstance(item, dict):
                    continue
                resumo = str(item.get("summary") or "").strip()
                detalhe = str(item.get("detail") or "").strip()
                if not resumo:
                    continue
                icone = icones.get(str(item.get("kind") or ""), "•")
                linhas.append(f"{icone}  {resumo}" + (f"\n    {detalhe}" if detalhe else ""))
        saude = dashboard.get("health")
        memoria = (
            saude.get("memory")
            if isinstance(saude, dict) and isinstance(saude.get("memory"), dict)
            else {}
        )
        estado_memoria = str(memoria.get("state") or "unavailable")
        frescor_memoria = str(memoria.get("freshness") or "unavailable")
        if estado_memoria == "unavailable" or frescor_memoria == "unavailable":
            texto_memoria = "Memória indisponível; não há uma leitura confiável agora."
        elif linhas:
            texto_memoria = "\n\n".join(linhas)
            if frescor_memoria == "stale":
                texto_memoria = "Dados antigos\n\n" + texto_memoria
        elif frescor_memoria == "stale":
            texto_memoria = "A leitura recente da memória está desatualizada."
        elif estado_memoria == "degraded":
            texto_memoria = "Memória parcialmente disponível, sem cartões públicos agora."
        else:
            texto_memoria = "Nenhuma memória recente pública para mostrar."
        self.memoria_estado.setText(texto_memoria)
        self.aplicar_catalogo_acoes(dashboard.get("quick_actions"))
        status = str(dashboard.get("status") or "unavailable")
        self.estado.setText({
            "ok": "●  Vivo",
            "partial": "●  Parcial",
            "unavailable": "●  Sem dados",
        }.get(status, "●  Sem dados"))

    def invalidar_dashboard(self) -> None:
        self.estado.setText("●  Reconectando")
        self.definir_contexto("modo", "—")
        self.definir_contexto("cidade", "—")
        self.definir_contexto("jogo", "Não observado")
        self.memoria_estado.setText("Aguardando uma projeção segura da memória.")


class PainelLateralDashboard(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dashboardRail")
        self.setMinimumWidth(270)
        self.setMaximumWidth(305)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(11)

        sistema = CartaoDashboard("Sistema", subtitulo="P2")
        self.metricas: dict[str, QLabel] = {}
        for chave, rotulo in (
            ("cpu", "CPU"), ("ram", "RAM"), ("temperatura", "Temp."),
            ("disco", "Disco"), ("uptime", "Tempo ligado"),
        ):
            linha, valor = _linha_valor(rotulo)
            self.metricas[chave] = valor
            sistema.layout_principal.addWidget(linha)
        self.sistema_estado = QLabel("Aguardando telemetria real da mente.")
        self.sistema_estado.setObjectName("dashboardEmpty")
        self.sistema_estado.setWordWrap(True)
        sistema.layout_principal.addWidget(self.sistema_estado)
        layout.addWidget(sistema)

        musica = CartaoDashboard("Música", subtitulo="P4")
        self.musica_titulo = QLabel("Nenhuma faixa confirmada")
        self.musica_titulo.setObjectName("musicTitle")
        self.musica_detalhe = QLabel("O player será ligado ao estado observado da extensão.")
        self.musica_detalhe.setObjectName("dashboardEmpty")
        self.musica_detalhe.setWordWrap(True)
        controles = QLabel("↶     ◀     ▶     ▶|     ↷")
        controles.setObjectName("musicControlsPlaceholder")
        controles.setAlignment(Qt.AlignCenter)
        musica.layout_principal.addWidget(self.musica_titulo)
        musica.layout_principal.addWidget(self.musica_detalhe)
        musica.layout_principal.addWidget(controles)
        layout.addWidget(musica)

        rotinas = CartaoDashboard("Rotinas", subtitulo="P4")
        rotinas_estado = QLabel("Aguardando rotinas confirmadas pela agenda.")
        rotinas_estado.setObjectName("dashboardEmpty")
        rotinas_estado.setWordWrap(True)
        rotinas.layout_principal.addWidget(rotinas_estado)
        layout.addWidget(rotinas)

        jogo = CartaoDashboard("Modo jogo", subtitulo="P4")
        self.jogo_estado = QLabel("Estado ainda não exposto à interface")
        self.jogo_estado.setObjectName("dashboardEmpty")
        self.jogo_estado.setWordWrap(True)
        jogo.layout_principal.addWidget(self.jogo_estado)
        layout.addWidget(jogo)
        layout.addStretch()

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

    def invalidar_dashboard(self) -> None:
        for valor in self.metricas.values():
            valor.setText("—")
        self.sistema_estado.setText("Aguardando telemetria real da mente.")
        self.jogo_estado.setText("Estado indisponível durante a reconexão")


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
