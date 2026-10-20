"""Três apresentações locais para a mesma sessão nativa da Laylay.

Este controlador não conhece o transporte nem envia ações. Feed, composer,
pendências e páginas continuam pertencendo à única JanelaLaylay.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QStackedWidget, QToolButton, QVBoxLayout, QWidget

from cliente.terminal_2.mascote_v1 import MascoteLaylay

if TYPE_CHECKING:
    from cliente.terminal_laylay_2 import JanelaLaylay


class ApresentacaoLaylayV1(QObject):
    MODOS = ("completa", "painel", "ilha")

    def __init__(self, janela: JanelaLaylay) -> None:
        super().__init__(janela)
        self.janela = janela
        self.modo = "completa"
        self.botoes: list[QToolButton] = []
        self._arrasto: QPoint | None = None
        self._geometria_completa = QRect(janela.geometry())
        self._estado_completo = janela.windowState()
        self._flags_completa = janela.windowFlags()
        self._pagina_completa = (0, "inicio", "inicio")
        self._encerrado = False

        # Só o recipiente raiz muda de pai. Feed/composer permanecem nos seus
        # layouts originais durante toda a vida da sessão.
        self.superficie_completa = janela.takeCentralWidget()
        self.pilha = QStackedWidget(janela)
        self.pilha.setObjectName("v1PresentationStack")
        janela.setCentralWidget(self.pilha)
        self.pilha.addWidget(self.superficie_completa)
        self.ilha = QFrame(objectName="v1Island")
        self.ilha.setAccessibleName("Ilha da Laylay")
        lay = QHBoxLayout(self.ilha)
        lay.setContentsMargins(12, 6, 10, 6)
        lay.setSpacing(8)
        self.mascote_ilha = MascoteLaylay(self.ilha, tamanho=54, reduzir_movimento=janela._reduzir_movimento)
        lay.addWidget(self.mascote_ilha)
        textos = QVBoxLayout()
        textos.setSpacing(2)
        self.rotulo_titulo = QLabel("Laylay", self.ilha)
        self.rotulo_titulo.setObjectName("v1IslandTitle")
        self.rotulo_estado = QLabel(janela.status.text(), self.ilha)
        self.rotulo_estado.setObjectName("v1IslandStatus")
        self.rotulo_estado.setWordWrap(True)
        textos.addWidget(self.rotulo_titulo)
        textos.addWidget(self.rotulo_estado)
        lay.addLayout(textos, 1)
        lay.addWidget(self.criar_controles(self.ilha, incluir_atual=False))
        self.pilha.addWidget(self.ilha)
        self.ilha.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ilha.customContextMenuRequested.connect(self._menu_ilha)
        for widget in (janela.topbar, self.ilha, self.rotulo_titulo, self.rotulo_estado):
            widget.installEventFilter(self)
        for indice, modo in enumerate(self.MODOS, 1):
            QShortcut(QKeySequence(f"Ctrl+Alt+{indice}"), janela,
                      activated=lambda destino=modo: self.definir_modo(destino))

    def criar_controles(self, parent: QWidget, *, incluir_atual: bool = True) -> QFrame:
        controles = QFrame(parent, objectName="v1PresentationControls")
        lay = QHBoxLayout(controles)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)
        for modo, texto, titulo in (
            ("completa", "↗", "Interface completa"),
            ("painel", "▣", "Painel rápido"),
            ("ilha", "−", "Recolher para a ilha"),
        ):
            if not incluir_atual and modo == "ilha":
                continue
            botao = QToolButton(controles)
            botao.setText(texto)
            botao.setProperty("presentationMode", modo)
            botao.setFixedSize(30, 30)
            botao.setCheckable(True)
            botao.setChecked(modo == self.modo)
            botao.setToolTip(f"{titulo} · Ctrl+Alt+{self.MODOS.index(modo) + 1}")
            botao.setAccessibleName(titulo)
            botao.clicked.connect(lambda _v=False, destino=modo: self.definir_modo(destino))
            lay.addWidget(botao)
            self.botoes.append(botao)
        return controles

    def definir_modo(self, modo: str) -> None:
        if modo not in self.MODOS:
            raise ValueError(f"Apresentação desconhecida: {modo}")
        if modo == self.modo or self._encerrado:
            return
        janela = self.janela
        estava_visivel = janela.isVisible()
        foco = janela.focusWidget()
        if self.modo == "completa":
            self._geometria_completa = QRect(janela.normalGeometry() if janela.isMaximized() else janela.geometry())
            self._estado_completo = janela.windowState()
            self._flags_completa = janela.windowFlags()
            self._pagina_completa = (janela.paginas.currentIndex(), janela._pagina_visual_ativa, janela._pagina_principal)
        janela._encerrar_transicao_pagina()
        self.modo = modo
        # setWindowFlags pode ocultar a janela: só repomos a visibilidade que já
        # existia, sem produzir outra janela ou interromper worker/microfone.
        flags = self._flags_completa
        if modo != "completa":
            flags = flags | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        if janela.windowFlags() != flags:
            janela.setWindowFlags(flags)
        janela.setWindowState(Qt.WindowNoState)
        janela.setProperty("presentationMode", modo)
        self.pilha.setCurrentWidget(self.ilha if modo == "ilha" else self.superficie_completa)
        if modo == "completa":
            janela.setMinimumSize(375, 620)
            indice, nome, principal = self._pagina_completa
            janela.paginas.setCurrentIndex(indice)
            janela._pagina_visual_ativa = nome
            janela._pagina_principal = principal
            janela._atualizar_cabecalho_chat()
            janela.setGeometry(self._geometria_limitada(self._geometria_completa))
        else:
            janela.setMinimumSize(250, 70) if modo == "ilha" else janela.setMinimumSize(320, 420)
            if modo == "painel":
                janela.paginas.setCurrentIndex(0)
                janela._pagina_visual_ativa = "conversa"
                janela._pagina_principal = "conversa"
                janela._atualizar_cabecalho_chat()
            janela.setGeometry(self._geometria_compacta(modo))
        janela._assinatura_responsividade = None
        janela._aplicar_responsividade()
        self._sincronizar_botoes()
        if estava_visivel:
            if modo == "completa" and self._estado_completo & Qt.WindowMaximized:
                janela.showMaximized()
            else:
                janela.show()
            if modo != "ilha" and foco is not None and foco.isVisible():
                foco.setFocus(Qt.OtherFocusReason)
        janela._ajustar_grid_home()

    def _geometria_limitada(self, desejada: QRect) -> QRect:
        disponivel = self.janela.screen().availableGeometry()
        largura = min(desejada.width(), disponivel.width())
        altura = min(desejada.height(), disponivel.height())
        x = min(max(desejada.x(), disponivel.left()), disponivel.right() - largura + 1)
        y = min(max(desejada.y(), disponivel.top()), disponivel.bottom() - altura + 1)
        return QRect(x, y, largura, altura)

    def _geometria_compacta(self, modo: str) -> QRect:
        disponivel = self.janela.screen().availableGeometry()
        tamanho = QSize(302, 76) if modo == "ilha" else QSize(450, 700)
        largura, altura = min(tamanho.width(), disponivel.width()), min(tamanho.height(), disponivel.height())
        return QRect(disponivel.center().x() - largura // 2,
                     disponivel.top() + min(12, max(0, disponivel.height() - altura)), largura, altura)

    def aplicar_responsividade_compacta(self) -> bool:
        if self.modo == "completa":
            return False
        janela = self.janela
        for widget in (janela.sidebar, janela.inspector_shell, janela.central_inteligente,
                       janela.painel_lateral, janela.chip_modelo, janela.chip_memoria,
                       janela.chip_microfone, janela.menu_compacto, janela.voltar,
                       janela.avancar, janela.titulo_header, janela.chat_cabecalho,
                       janela.presenca_pill):
            widget.hide()
        pagina = janela.paginas.widget(0)
        pagina.layout().setContentsMargins(6, 4, 6, 8)
        janela.topbar.layout().setContentsMargins(12, 7, 12, 7)
        return True

    def atualizar_estado(self, atividade: str, emocao: str, conectado: bool, rotulo: str) -> None:
        self.rotulo_estado.setText(rotulo)
        for mascote in (self.mascote_ilha, self.janela.mascote_inicio, self.janela.mascote_cabecalho,
                       self.janela.avatar_side, self.janela.avatar_profile):
            mascote.definir_estado(atividade, emocao, conectado=conectado)

    def _sincronizar_botoes(self) -> None:
        for botao in self.botoes:
            botao.setChecked(botao.property("presentationMode") == self.modo)

    def _menu_ilha(self, ponto: QPoint) -> None:
        menu = QMenu(self.ilha)
        menu.addAction("Interface completa", lambda: self.definir_modo("completa"))
        menu.addAction("Painel rápido", lambda: self.definir_modo("painel"))
        menu.addSeparator()
        menu.addAction("Fechar a interface", self.janela.close)
        menu.exec(self.ilha.mapToGlobal(ponto))

    def eventFilter(self, objeto, evento) -> bool:  # noqa: N802
        if self.modo == "completa":
            return super().eventFilter(objeto, evento)
        if evento.type() == QEvent.MouseButtonDblClick and evento.button() == Qt.LeftButton:
            self.definir_modo("painel" if self.modo == "ilha" else "completa")
            return True
        if evento.type() == QEvent.MouseButtonPress and evento.button() == Qt.LeftButton:
            handle = self.janela.windowHandle()
            if handle is not None and handle.startSystemMove():
                return True
            self._arrasto = evento.globalPosition().toPoint() - self.janela.pos()
        elif evento.type() == QEvent.MouseMove and self._arrasto is not None and evento.buttons() & Qt.LeftButton:
            self.janela.move(evento.globalPosition().toPoint() - self._arrasto)
            return True
        elif evento.type() == QEvent.MouseButtonRelease:
            self._arrasto = None
        return super().eventFilter(objeto, evento)

    def encerrar(self) -> None:
        self._encerrado = True
        for mascote in self.janela.findChildren(MascoteLaylay):
            mascote.encerrar()
