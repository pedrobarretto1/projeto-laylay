"""Detalhe nativo e sob demanda das playlists do Terminal 2."""

from __future__ import annotations

import uuid

from PySide6.QtCore import QSize, Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QInputDialog, QLineEdit, QMenu, QMessageBox,
    QProgressBar, QPushButton, QSizePolicy, QTableWidget,
    QStackedLayout, QToolButton, QVBoxLayout, QWidget,
)

from cliente.terminal_2.acabamento import CapaMusicaGenerica, icone_terminal


def _tempo(segundos: object) -> str:
    if not isinstance(segundos, (int, float)) or isinstance(segundos, bool) or segundos <= 0:
        return "—"
    total = int(segundos)
    minutos, segundo = divmod(total, 60)
    horas, minutos = divmod(minutos, 60)
    return f"{horas}:{minutos:02d}:{segundo:02d}" if horas else f"{minutos}:{segundo:02d}"


class RotuloElidido(QLabel):
    """Mantém o valor integral no tooltip e elide somente a apresentação."""

    def __init__(self, texto: str = "") -> None:
        super().__init__()
        self._texto_completo = ""
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.definir_texto(texto)

    @property
    def texto_completo(self) -> str:
        return self._texto_completo

    def definir_texto(self, texto: str) -> None:
        self._texto_completo = str(texto or "")
        self.setToolTip(self._texto_completo)
        self._atualizar()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._atualizar()

    def _atualizar(self) -> None:
        QLabel.setText(self, self.fontMetrics().elidedText(
            self._texto_completo, Qt.ElideRight,
            max(0, self.contentsRect().width()),
        ))


class FaixaPlaylistRow(QFrame):
    """Linha silenciosa em repouso, operável no hover, foco ou seleção."""

    tocar_solicitado = Signal(dict)
    acao_solicitada = Signal(str, dict)
    selecionada = Signal(int)

    def __init__(self, indice: int, item: dict) -> None:
        super().__init__()
        self.indice = indice
        self.item = item
        self._sob_mouse = False
        self._selecionada = False
        self._compacta = False
        self._modo_metadados = ""
        self.setObjectName("playlistTrackRow")
        self.setProperty("interactive", False)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setAccessibleName(
            f"Faixa {indice + 1}: {item.get('title') or 'sem título'}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(9)

        self.controle_slot = QWidget()
        self.controle_slot.setFixedSize(24, 24)
        controle = QStackedLayout(self.controle_slot)
        controle.setContentsMargins(0, 0, 0, 0)
        self.numero = QLabel(str(indice + 1))
        self.numero.setObjectName("playlistTrackNumber")
        self.numero.setAlignment(Qt.AlignCenter)
        self.play = QToolButton()
        self.play.setObjectName("playlistTrackPlay")
        self.play.setIcon(icone_terminal("play"))
        self.play.setIconSize(QSize(12, 12))
        self.play.setFixedSize(24, 24)
        self.play.setAccessibleName(
            f"Tocar {item.get('title') or 'esta faixa'}"
        )
        self.play.setToolTip(
            f"Tocar {item.get('title') or 'esta faixa'}"
        )
        self.play.clicked.connect(lambda: self.tocar_solicitado.emit(self.item))
        controle.addWidget(self.numero)
        controle.addWidget(self.play)
        self._controle = controle
        layout.addWidget(self.controle_slot)

        self.capa = CapaMusicaGenerica(30)
        self.capa.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.capa.definir_titulo(str(item.get("title") or ""))
        self.capa.carregar(str(item.get("artwork_url") or ""))
        layout.addWidget(self.capa)

        identidade = QVBoxLayout()
        identidade.setContentsMargins(0, 0, 0, 0)
        identidade.setSpacing(0)
        self.titulo = RotuloElidido(str(item.get("title") or "Faixa sem título"))
        self.titulo.setObjectName("playlistTrackTitle")
        self.titulo.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.meta = RotuloElidido("Vídeo do YouTube")
        self.meta.setObjectName("playlistTrackMeta")
        self.meta.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        identidade.addWidget(self.titulo)
        identidade.addWidget(self.meta)
        layout.addLayout(identidade, 1)

        self.canal = RotuloElidido(str(item.get("channel") or "—"))
        self.canal.setObjectName("playlistTrackChannel")
        self.canal.setMinimumWidth(0)
        self.canal.setMaximumWidth(220)
        self.canal.setAccessibleName(
            f"Canal: {item.get('channel') or 'não informado'}"
        )
        self.canal.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.canal, 0)

        self.adicionada = QLabel(str(item.get("added_at") or "—"))
        self.adicionada.setObjectName("playlistTrackAdded")
        self.adicionada.setMinimumWidth(76)
        self.adicionada.setMaximumWidth(88)
        self.adicionada.setToolTip(str(item.get("added_at") or "—"))
        self.adicionada.setAccessibleName(
            f"Adicionada em: {item.get('added_at') or 'não informado'}"
        )
        self.adicionada.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.adicionada)

        self.duracao = QLabel(_tempo(item.get("duration_seconds")))
        self.duracao.setObjectName("playlistTrackDuration")
        self.duracao.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.duracao.setFixedWidth(45)
        self.duracao.setToolTip(_tempo(item.get("duration_seconds")))
        self.duracao.setAccessibleName(
            f"Duração: {_tempo(item.get('duration_seconds'))}"
        )
        self.duracao.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.duracao)

        self.menu_slot = QWidget()
        self.menu_slot.setFixedSize(24, 24)
        menu_layout = QHBoxLayout(self.menu_slot)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        self.menu = QToolButton()
        self.menu.setObjectName("playlistTrackMenu")
        self.menu.setText("•••")
        self.menu.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.menu.setFixedSize(24, 24)
        self.menu.setAccessibleName(
            f"Opções para {item.get('title') or 'faixa'}"
        )
        self.menu.setToolTip(
            f"Ações para {item.get('title') or 'esta faixa'}"
        )
        self.menu.setPopupMode(QToolButton.InstantPopup)
        opcoes = QMenu(self.menu)
        self.menu.setMenu(opcoes)
        for texto, operacao in (
            ("Tocar agora", "play_track"),
            ("Copiar para outra playlist", "copy_track"),
            ("Mover para outra playlist", "move_track"),
            ("Remover", "remove_track"),
        ):
            acao = opcoes.addAction(texto)
            acao.triggered.connect(
                lambda _v=False, op=operacao:
                self.acao_solicitada.emit(op, self.item)
            )
        opcoes.aboutToShow.connect(lambda: self.selecionada.emit(self.indice))
        menu_layout.addWidget(self.menu)
        layout.addWidget(self.menu_slot)
        self._atualizar_interacao()
        self._atualizar_metadados_responsivos(self.width())

    def definir_compacta(self, compacta: bool) -> None:
        self._compacta = bool(compacta)
        self._atualizar_metadados_responsivos(self.width())

    def definir_largura_disponivel(self, largura: int) -> None:
        """Recebe a largura observada do viewport que realmente contém a linha."""
        self._atualizar_metadados_responsivos(max(0, int(largura)))

    def _atualizar_metadados_responsivos(self, largura: int) -> None:
        # A linha é a fronteira real de espaço: a data cede primeiro; depois o
        # canal migra para a sublinha sem competir com título, capa e duração.
        modo = (
            "completo" if largura >= 720
            else ("sem_data" if largura >= 540 else "essencial")
        )
        if modo == self._modo_metadados:
            return
        self._modo_metadados = modo
        self.adicionada.setVisible(modo == "completo")
        self.canal.setVisible(modo != "essencial")
        canal = str(self.item.get("channel") or "").strip()
        self.meta.definir_texto(
            f"Vídeo do YouTube  •  {canal}" if modo == "essencial" and canal
            else "Vídeo do YouTube"
        )

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._atualizar_metadados_responsivos(event.size().width())

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._atualizar_metadados_responsivos(self.width())

    def definir_selecionada(self, selecionada: bool) -> None:
        self._selecionada = bool(selecionada)
        self._atualizar_interacao()

    def enterEvent(self, event) -> None:  # noqa: N802
        self._sob_mouse = True
        self._atualizar_interacao()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._sob_mouse = False
        self._atualizar_interacao()
        super().leaveEvent(event)

    def focusInEvent(self, event) -> None:  # noqa: N802
        self.selecionada.emit(self.indice)
        super().focusInEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self.setFocus(Qt.MouseFocusReason)
            self.selecionada.emit(self.indice)
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.tocar_solicitado.emit(self.item)
            event.accept()
            return
        super().keyPressEvent(event)

    def _atualizar_interacao(self) -> None:
        interativa = self._sob_mouse or self._selecionada or self.hasFocus()
        self.setProperty("interactive", interativa)
        self._controle.setCurrentWidget(self.play if interativa else self.numero)
        self.menu.setVisible(interativa)
        self.style().unpolish(self)
        self.style().polish(self)


class PlaylistDetalhe(QWidget):
    voltar_solicitado = Signal()
    requisicao_solicitada = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("playlistDetail")
        self._nome = ""
        self._revisao = ""
        self._offset = 0
        self._itens: list[dict] = []
        self._catalogo: list[str] = []
        self._linhas_widgets: list[FaixaPlaylistRow] = []
        self._linha_selecionada = -1
        self._player_observado = False
        self._compacto = False
        self._altura_baixa = False
        self._operacao_pendente = ""
        self._detalhe_requisicao_id = ""
        self.raiz = QVBoxLayout(self)
        self.raiz.setContentsMargins(16, 14, 16, 16)
        self.raiz.setSpacing(9)

        topo = QHBoxLayout()
        self.voltar = QToolButton()
        self.voltar.setObjectName("playlistBack")
        self.voltar.setIcon(icone_terminal("arrow-left"))
        self.voltar.setText("Voltar")
        self.voltar.setAccessibleName("Voltar à lista de playlists")
        self.voltar.setToolTip("Voltar à lista de playlists")
        self.voltar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.voltar.setFixedHeight(30)
        self.voltar.clicked.connect(self.voltar_solicitado)
        topo.addWidget(self.voltar)
        topo.addStretch()
        self.raiz.addLayout(topo)

        self.hero = QFrame()
        self.hero.setObjectName("playlistHero")
        self.hero_layout = QHBoxLayout(self.hero)
        self.hero_layout.setContentsMargins(12, 12, 12, 12)
        self.hero_layout.setSpacing(12)
        self.capa = CapaMusicaGenerica(104)
        self.capa.setAccessibleName("Capa da playlist")
        self.hero_layout.addWidget(self.capa)
        identidade = QVBoxLayout()
        self.rotulo = QLabel("PLAYLIST")
        self.rotulo.setObjectName("playlistEyebrow")
        self.titulo = QLabel("Playlist")
        self.titulo.setObjectName("playlistTitle")
        self.titulo.setWordWrap(True)
        self.meta = QLabel("Carregando…")
        self.meta.setObjectName("playlistMeta")
        identidade.addStretch()
        identidade.addWidget(self.rotulo)
        identidade.addWidget(self.titulo)
        identidade.addWidget(self.meta)
        identidade.addStretch()
        self.hero_layout.addLayout(identidade, 1)
        self.raiz.addWidget(self.hero)

        self.acoes_layout = QGridLayout()
        self.acoes_layout.setHorizontalSpacing(6)
        self.acoes_layout.setVerticalSpacing(6)
        self.play = QPushButton("Tocar")
        self.play.setObjectName("playlistPrimaryAction")
        self.play.setIcon(icone_terminal("play"))
        self.shuffle = QPushButton("Aleatório")
        self.shuffle.setIcon(icone_terminal("shuffle"))
        self.adicionar = QPushButton("Adicionar URL")
        self.capa_trocar = QPushButton("Trocar capa")
        self.capa_restaurar = QPushButton("Restaurar capa")
        self._botoes_acoes = (
            self.play, self.shuffle, self.adicionar,
            self.capa_trocar, self.capa_restaurar,
        )
        nomes_acoes = (
            (self.play, "Tocar playlist", "Tocar a playlist desde o início"),
            (self.shuffle, "Tocar playlist em ordem aleatória", "Tocar esta playlist em ordem aleatória"),
            (self.adicionar, "Adicionar música por URL", "Adicionar um vídeo do YouTube a esta playlist"),
            (self.capa_trocar, "Trocar capa da playlist", "Escolher uma imagem para a capa desta playlist"),
            (self.capa_restaurar, "Restaurar capa automática", "Voltar a usar a capa automática da primeira faixa"),
        )
        for coluna, (botao, nome_acessivel, dica) in enumerate(nomes_acoes):
            botao.setAccessibleName(nome_acessivel)
            botao.setToolTip(dica)
            botao.setMinimumWidth(0)
            botao.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            botao.setFixedHeight(32)
            self.acoes_layout.addWidget(botao, 0, coluna)
        self.acoes_layout.setColumnStretch(5, 1)
        self.raiz.addLayout(self.acoes_layout)
        self.play.clicked.connect(lambda: self._requisitar("play_playlist"))
        self.shuffle.clicked.connect(lambda: self._requisitar("shuffle_playlist"))
        self.adicionar.clicked.connect(self._adicionar_url)
        self.capa_trocar.clicked.connect(self._trocar_capa)
        self.capa_restaurar.clicked.connect(lambda: self._requisitar("restore_artwork"))

        self.busca = QLineEdit()
        self.busca.setObjectName("playlistSearch")
        self.busca.setPlaceholderText("Pesquisar nesta playlist")
        self.busca.setFixedHeight(34)
        self._timer_busca = QTimer(self)
        self._timer_busca.setSingleShot(True)
        self._timer_busca.setInterval(220)
        self.busca.textChanged.connect(lambda _texto: self._timer_busca.start())
        self._timer_busca.timeout.connect(lambda: self.solicitar_detalhe(reiniciar=True))
        self.raiz.addWidget(self.busca)

        self.estado = QLabel("Selecione uma playlist para ver as faixas.")
        self.estado.setObjectName("playlistDetailState")
        self.estado.setMinimumWidth(0)
        self.estado.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.raiz.addWidget(self.estado)
        self.tabela = QTableWidget(0, 6)
        self.tabela.setObjectName("playlistTracks")
        self.tabela.horizontalHeader().hide()
        self.tabela.verticalHeader().hide()
        self.tabela.setSelectionMode(QAbstractItemView.NoSelection)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setShowGrid(False)
        self.tabela.setFrameShape(QFrame.NoFrame)
        self.tabela.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(0, QHeaderView.Stretch)
        for coluna in range(1, 6):
            self.tabela.setColumnHidden(coluna, True)
        self.raiz.addWidget(self.tabela, 1)
        self.mais = QPushButton("Carregar mais")
        self.mais.clicked.connect(lambda: self.solicitar_detalhe(reiniciar=False))
        self.mais.hide()
        self.raiz.addWidget(self.mais, 0, Qt.AlignHCenter)

        self.player = QFrame()
        self.player.setObjectName("playlistObservedPlayer")
        self.player_layout = QGridLayout(self.player)
        self.player_layout.setContentsMargins(10, 6, 10, 6)
        self.player_layout.setHorizontalSpacing(10)
        self.player_layout.setVerticalSpacing(4)
        self._modo_player = ""

        self.player_identidade = QWidget()
        self.player_identidade.setObjectName("playlistPlayerIdentity")
        self.player_identidade.setMinimumWidth(0)
        self.player_identidade.setSizePolicy(
            QSizePolicy.Ignored, QSizePolicy.Preferred,
        )
        self.player_identidade_layout = QHBoxLayout(self.player_identidade)
        self.player_identidade_layout.setContentsMargins(0, 0, 0, 0)
        self.player_identidade_layout.setSpacing(8)
        self.player_capa = CapaMusicaGenerica(42)
        self.player_capa.setAccessibleName("Capa da faixa observada")
        self.player_identidade_layout.addWidget(self.player_capa)
        textos_player = QVBoxLayout()
        textos_player.setContentsMargins(0, 0, 0, 0)
        textos_player.setSpacing(1)
        self.player_titulo = RotuloElidido("Reprodução observada")
        self.player_titulo.setObjectName("playlistPlayerTitle")
        self.player_canal = RotuloElidido("Canal não informado")
        self.player_canal.setObjectName("playlistPlayerChannel")
        textos_player.addStretch()
        textos_player.addWidget(self.player_titulo)
        textos_player.addWidget(self.player_canal)
        textos_player.addStretch()
        self.player_identidade_layout.addLayout(textos_player, 1)

        self.player_centro = QWidget()
        self.player_centro.setObjectName("playlistPlayerCenter")
        self.player_centro.setMinimumWidth(0)
        self.player_centro_layout = QVBoxLayout(self.player_centro)
        self.player_centro_layout.setContentsMargins(0, 0, 0, 0)
        self.player_centro_layout.setSpacing(3)
        transporte = QHBoxLayout()
        transporte.setContentsMargins(0, 0, 0, 0)
        transporte.setSpacing(8)
        transporte.addStretch()
        self.player_anterior = QToolButton()
        self.player_anterior.setObjectName("playlistPlayerPrevious")
        self.player_anterior.setIcon(icone_terminal("previous"))
        self.player_toggle = QToolButton()
        self.player_toggle.setObjectName("playlistPlayerToggle")
        self.player_toggle.setIcon(icone_terminal("play"))
        self.player_proxima = QToolButton()
        self.player_proxima.setObjectName("playlistPlayerNext")
        self.player_proxima.setIcon(icone_terminal("next"))
        transporte.addWidget(self.player_anterior)
        transporte.addWidget(self.player_toggle)
        transporte.addWidget(self.player_proxima)
        transporte.addStretch()
        self.player_centro_layout.addLayout(transporte)

        progresso = QHBoxLayout()
        progresso.setContentsMargins(0, 0, 0, 0)
        progresso.setSpacing(6)
        self.player_tempo_atual = QLabel("0:00")
        self.player_tempo_atual.setObjectName("playlistPlayerTime")
        self.player_tempo_atual.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.player_tempo_atual.setFixedWidth(34)
        self.player_progresso = QProgressBar()
        self.player_progresso.setObjectName("playlistObservedProgress")
        self.player_progresso.setRange(0, 1000)
        self.player_progresso.setTextVisible(False)
        self.player_tempo_total = QLabel("0:00")
        self.player_tempo_total.setObjectName("playlistPlayerTime")
        self.player_tempo_total.setFixedWidth(34)
        progresso.addWidget(self.player_tempo_atual)
        progresso.addWidget(self.player_progresso, 1)
        progresso.addWidget(self.player_tempo_total)
        self.player_centro_layout.addLayout(progresso)

        self.player_estado = QLabel("PAUSADA")
        self.player_estado.setObjectName("playlistPlayerState")
        self.player_estado.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.player_estado.setAccessibleName("Estado da reprodução observada")
        controles_player = (
            (self.player_anterior, "Faixa anterior", "Voltar para a faixa anterior"),
            (self.player_toggle, "Pausar ou continuar", "Pausar ou continuar a reprodução"),
            (self.player_proxima, "Próxima faixa", "Pular para a próxima faixa"),
        )
        for botao, nome_acessivel, dica in controles_player:
            botao.setAccessibleName(nome_acessivel)
            botao.setToolTip(dica)
        self.player_anterior.setFixedSize(28, 28)
        self.player_anterior.setIconSize(QSize(13, 13))
        self.player_toggle.setFixedSize(34, 34)
        self.player_toggle.setIconSize(QSize(15, 15))
        self.player_proxima.setFixedSize(28, 28)
        self.player_proxima.setIconSize(QSize(13, 13))
        self._organizar_player_responsivo(900)
        self.player.hide()
        self.raiz.addWidget(self.player)
        self.setStyleSheet("""
            #playlistDetail { background: #0D1115; color: #F7F1F4; }
            #playlistHero { background: #15191E; border: 1px solid #292E35; border-radius: 9px; }
            #playlistEyebrow { color: #FF667E; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
            #playlistTitle { color: #FFF9FB; font-size: 22px; font-weight: 700; }
            #playlistMeta, #playlistDetailState { color: #AFA8AE; font-size: 12px; }
            #playlistBack, #playlistDetail QPushButton, #playlistDetail QToolButton {
                color: #F6F0F3; background: #1B2027; border: 1px solid #343943;
                border-radius: 6px; padding: 4px 8px;
            }
            #playlistBack:hover, #playlistDetail QPushButton:hover, #playlistDetail QToolButton:hover {
                background: #252B33; border-color: #5A4650;
            }
            #playlistBack:focus, #playlistDetail QPushButton:focus, #playlistDetail QToolButton:focus {
                border: 1px solid #FF7187;
            }
            #playlistPrimaryAction { background: #24242A; color: #FFF6F8; border-color: #71404C; font-weight: 700; }
            #playlistPrimaryAction:hover { background: #29292F; border-color: #A64C5E; }
            #playlistSearch { background: #151A20; color: #F7F1F4; border: 1px solid #313640;
                border-radius: 7px; padding: 5px 9px; selection-background-color: #8B3041; }
            #playlistSearch:focus { border-color: #FF6078; }
            #playlistTracks { background: transparent; color: #EEE8EB; border: 0;
                border-radius: 7px; gridline-color: transparent; outline: 0; }
            #playlistTracks::item { padding: 0; border: 0; background: transparent; }
            #playlistTrackRow { background: transparent; border: 0; border-radius: 6px; }
            #playlistTrackRow[interactive="true"] { background: #20242A; }
            #playlistTrackNumber { color: #AFA8AE; font-size: 12px; }
            #playlistTrackTitle { color: #FFF9FB; font-size: 12px; font-weight: 650; }
            #playlistTrackMeta, #playlistTrackChannel, #playlistTrackAdded,
            #playlistTrackDuration { color: #AFA8AE; font-size: 10px; }
            #playlistDetail #playlistTrackPlay, #playlistDetail #playlistTrackMenu {
                background: transparent; border: 1px solid transparent;
                border-radius: 4px; padding: 0; margin: 0;
                min-width: 22px; max-width: 22px;
                min-height: 22px; max-height: 22px;
            }
            #playlistDetail #playlistTrackMenu { font-size: 7px; }
            #playlistDetail #playlistTrackPlay:hover,
            #playlistDetail #playlistTrackMenu:hover {
                background: #2B3037; border-color: #3D434C;
            }
            #playlistDetail #playlistTrackPlay:focus,
            #playlistDetail #playlistTrackMenu:focus {
                background: #2B3037; border-color: #A64C5E;
            }
            #playlistDetail #playlistTrackMenu::menu-indicator {
                image: none; width: 0; height: 0;
            }
            #playlistObservedPlayer { background: #090C0F; border: 1px solid #272C33; border-radius: 6px; }
            #playlistPlayerTitle { color: #FFF9FB; font-size: 11px; font-weight: 650; }
            #playlistPlayerChannel, #playlistPlayerTime, #playlistPlayerState {
                color: #9F989E; font-size: 9px;
            }
            #playlistPlayerState { font-weight: 700; letter-spacing: 1px; }
            #playlistDetail #playlistPlayerPrevious,
            #playlistDetail #playlistPlayerNext {
                background: transparent; border: 1px solid transparent;
                border-radius: 4px; padding: 0; margin: 0;
                min-width: 26px; max-width: 26px;
                min-height: 26px; max-height: 26px;
            }
            #playlistDetail #playlistPlayerPrevious:hover,
            #playlistDetail #playlistPlayerNext:hover {
                background: #20252B; border-color: #373D45;
            }
            #playlistDetail #playlistPlayerToggle {
                background: #FF536D; border: 1px solid #FF7187;
                border-radius: 17px; padding: 0; margin: 0;
                min-width: 32px; max-width: 32px;
                min-height: 32px; max-height: 32px;
            }
            #playlistDetail #playlistPlayerToggle:hover { background: #FF667E; }
            #playlistDetail #playlistPlayerPrevious:focus,
            #playlistDetail #playlistPlayerToggle:focus,
            #playlistDetail #playlistPlayerNext:focus { border-color: #FFD0D8; }
            #playlistObservedProgress { background: #292E35; border: 0; border-radius: 2px;
                min-height: 3px; max-height: 3px; }
            #playlistObservedProgress::chunk { background: #FF536D; border-radius: 2px; }
        """)
        # Começa comprimível antes do primeiro show; o resize real refina o modo.
        self.definir_compacto(True)

    def abrir(self, nome: str) -> None:
        self._nome = str(nome or "").strip()
        self.titulo.setText(self._nome or "Playlist")
        self.busca.clear()
        self._itens.clear()
        self.tabela.setRowCount(0)
        self.solicitar_detalhe(reiniciar=True)

    def definir_catalogo(self, nomes: list[str]) -> None:
        self._catalogo = list(dict.fromkeys(
            str(nome or "").strip() for nome in nomes if str(nome or "").strip()
        ))

    def solicitar_detalhe(self, *, reiniciar: bool) -> None:
        if not self._nome:
            return
        if reiniciar:
            self._offset = 0
            self._itens.clear()
        self.estado.setText("Carregando faixas…")
        self.estado.show()
        self._detalhe_requisicao_id = uuid.uuid4().hex
        self.requisicao_solicitada.emit({
            "id": self._detalhe_requisicao_id,
            "operation": "detail", "playlist": self._nome,
            "query": self.busca.text().strip(), "offset": self._offset, "limit": 50,
        })

    def _requisitar(self, operacao: str, **dados: object) -> None:
        payload = {"operation": operacao, "playlist": self._nome, **dados}
        if operacao not in {"detail", "add_url", "play_playlist", "shuffle_playlist"}:
            payload["revision"] = self._revisao
        if operacao in {
            "add_url", "play_track", "copy_track", "move_track",
            "remove_track", "set_artwork", "restore_artwork",
        }:
            self._operacao_pendente = operacao
            mensagens = {
                "add_url": "Confirmando vídeo e adicionando…",
                "play_track": "Abrindo a faixa selecionada…",
                "copy_track": "Copiando a faixa…",
                "move_track": "Movendo a faixa…",
                "remove_track": "Removendo a faixa…",
                "set_artwork": "Validando e salvando a nova capa…",
                "restore_artwork": "Restaurando a capa automática…",
            }
            self.estado.setText(mensagens[operacao])
            self.estado.show()
            self._definir_acoes_habilitadas(False)
        self.requisicao_solicitada.emit(payload)

    def _definir_acoes_habilitadas(self, habilitadas: bool) -> None:
        for botao in (*self._botoes_acoes, self.mais):
            botao.setEnabled(habilitadas)
        self.tabela.setEnabled(habilitadas)

    def _adicionar_url(self) -> None:
        url, ok = QInputDialog.getText(self, "Adicionar faixa", "URL do vídeo no YouTube:")
        if ok and url.strip():
            self._requisitar("add_url", url=url.strip())

    def _trocar_capa(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Escolher capa", "", "Imagens (*.png *.jpg *.jpeg *.webp)",
        )
        if caminho:
            self._requisitar("set_artwork", path=caminho)

    def _menu_faixa(self, linha: int) -> None:
        if not 0 <= linha < len(self._itens):
            return
        item = self._itens[linha]
        menu = self.sender().menu() if isinstance(self.sender(), QToolButton) else None
        del menu, item

    def _confirmar_e_requisitar(self, operacao: str, item: dict) -> None:
        dados: dict[str, object] = {"video_id": item.get("video_id", "")}
        destino = ""
        if operacao in {"copy_track", "move_track"}:
            destinos = [nome for nome in self._catalogo if nome.casefold() != self._nome.casefold()]
            if not destinos:
                QMessageBox.information(
                    self, "Sem playlist de destino",
                    "Crie outra playlist antes de copiar ou mover esta faixa.",
                )
                return
            destino, ok = QInputDialog.getItem(
                self, "Playlist de destino", "Escolha a playlist:", destinos, 0, False,
            )
            if not ok or not destino:
                return
            dados["destination"] = destino
        if operacao in {"remove_track", "move_track"}:
            verbo = "mover" if operacao == "move_track" else "remover"
            complemento = f" para “{destino}”" if destino else " desta playlist"
            if QMessageBox.question(
                self, "Confirmar alteração",
                f"Deseja {verbo} “{item.get('title') or 'faixa'}”{complemento}?",
            ) != QMessageBox.Yes:
                return
        self._requisitar(operacao, **dados)

    def aplicar_resultado(
        self,
        operacao: str,
        resultado: dict,
        *,
        playlist: str = "",
        request_id: str = "",
    ) -> None:
        if playlist and str(playlist).casefold() != self._nome.casefold():
            return
        if (
            operacao == "detail" and request_id
            and request_id != self._detalhe_requisicao_id
        ):
            return
        if operacao != "detail":
            self._operacao_pendente = ""
            self._definir_acoes_habilitadas(True)
            status = str(resultado.get("status") or "")
            mensagens_ok = {
                "track_started": "Faixa aberta.",
                "copied": "Faixa copiada para a playlist escolhida.",
                "already_present": "A faixa já existe na playlist escolhida; nenhuma cópia foi criada.",
                "moved": "Faixa movida para a playlist escolhida.",
                "removed": "Faixa removida desta playlist.",
                "added": "Faixa adicionada com metadados confirmados.",
                "artwork_updated": "Nova capa confirmada.",
                "artwork_restored": "Capa automática restaurada.",
            }
            mensagens_erro = {
                "revision_conflict": "A playlist mudou. Atualizei a lista para evitar alterar a faixa errada.",
                "metadata_mismatch": "Não consegui confirmar que a URL corresponde ao vídeo informado.",
                "save_failed": "A alteração não foi salva; a playlist original foi preservada.",
                "invalid_artwork": "A imagem não é uma capa válida.",
                "bridge_unavailable": "O terminal perdeu a conexão com a Laylay.",
            }
            self.estado.setText(
                mensagens_ok.get(status, "Alteração confirmada.")
                if resultado.get("ok")
                else mensagens_erro.get(status, "A alteração não foi confirmada.")
            )
            self.estado.show()
            if resultado.get("ok"):
                self.solicitar_detalhe(reiniciar=True)
            elif status == "revision_conflict":
                self.solicitar_detalhe(reiniciar=True)
            return
        if not resultado.get("ok"):
            self.estado.setText("Não consegui carregar esta playlist.")
            self.estado.show()
            return
        self._revisao = str(resultado.get("revision") or "")
        novos = [dict(item) for item in resultado.get("items", ()) if isinstance(item, dict)]
        self._itens = novos if int(resultado.get("offset") or 0) == 0 else self._itens + novos
        self._offset = len(self._itens)
        self.capa.definir_titulo(str(resultado.get("name") or ""))
        self.capa.carregar(str(resultado.get("artwork_url") or ""))
        total = int(resultado.get("total") or 0)
        duracao = _tempo(resultado.get("duration_seconds"))
        self.meta.setText(f"{total} faixa{'s' if total != 1 else ''}" + (f"  ·  {duracao}" if duracao != "—" else ""))
        self.estado.setText("Playlist vazia.")
        self.estado.setVisible(not self._itens)
        self.tabela.setRowCount(len(self._itens))
        self._linhas_widgets.clear()
        self._linha_selecionada = -1
        for linha, item in enumerate(self._itens):
            faixa = FaixaPlaylistRow(linha, item)
            faixa.definir_compacta(self._compacto)
            faixa.tocar_solicitado.connect(
                lambda faixa_item: self._confirmar_e_requisitar(
                    "play_track", faixa_item,
                ),
            )
            faixa.acao_solicitada.connect(self._confirmar_e_requisitar)
            faixa.selecionada.connect(self._selecionar_linha)
            self._linhas_widgets.append(faixa)
            self.tabela.setCellWidget(linha, 0, faixa)
            self.tabela.setRowHeight(linha, 38)
        self.mais.setVisible(bool(resultado.get("has_more")))
        QTimer.singleShot(0, self._sincronizar_largura_das_linhas)

    def _selecionar_linha(self, indice: int) -> None:
        self._linha_selecionada = indice
        for linha, widget in enumerate(self._linhas_widgets):
            widget.definir_selecionada(linha == indice)

    def _sincronizar_largura_das_linhas(self) -> None:
        largura = self.tabela.viewport().width()
        for faixa in self._linhas_widgets:
            faixa.definir_largura_disponivel(largura)

    def _organizar_player_responsivo(self, largura: int) -> None:
        modo = (
            "amplo" if largura >= 820
            else ("intermediario" if largura >= 520 else "estreito")
        )
        if modo == self._modo_player:
            return
        self._modo_player = modo
        for widget in (
            self.player_identidade, self.player_centro, self.player_estado,
        ):
            self.player_layout.removeWidget(widget)
        for coluna in range(3):
            self.player_layout.setColumnStretch(coluna, 0)
        for linha in range(2):
            self.player_layout.setRowStretch(linha, 0)

        amplo = modo == "amplo"
        estreito = modo == "estreito"
        self.player_capa.setVisible(not estreito)
        if not estreito:
            tamanho_capa = 42 if amplo else 38
            self.player_capa.setFixedSize(tamanho_capa, tamanho_capa)
        self.player_canal.setVisible(amplo)
        self.player_estado.setVisible(amplo)
        self.player_layout.setContentsMargins(
            6 if estreito else (10 if amplo else 8),
            5 if estreito else 6,
            6 if estreito else (10 if amplo else 8),
            5 if estreito else 6,
        )

        if amplo:
            self.player_layout.addWidget(self.player_identidade, 0, 0)
            self.player_layout.addWidget(self.player_centro, 0, 1)
            self.player_layout.addWidget(self.player_estado, 0, 2)
            self.player_layout.setColumnStretch(0, 1)
            self.player_layout.setColumnStretch(1, 2)
            self.player_layout.setColumnStretch(2, 1)
            self.player.setFixedHeight(72)
        elif modo == "intermediario":
            self.player_layout.addWidget(self.player_identidade, 0, 0)
            self.player_layout.addWidget(self.player_centro, 0, 1)
            self.player_layout.setColumnStretch(0, 1)
            self.player_layout.setColumnStretch(1, 2)
            self.player.setFixedHeight(70)
        else:
            self.player_layout.addWidget(self.player_identidade, 0, 0, 1, 3)
            self.player_layout.addWidget(self.player_centro, 1, 0, 1, 3)
            self.player_layout.setColumnStretch(0, 1)
            self.player_layout.setRowStretch(1, 1)
            self.player.setFixedHeight(94)

    def aplicar_player_observado(self, musica: dict) -> None:
        self._organizar_player_responsivo(self.width())
        estado = str(musica.get("state") or "")
        observado = estado in {"playing", "paused"} and musica.get("freshness") != "unavailable"
        self._player_observado = observado
        self.player.setVisible(observado)
        controles = bool(observado and musica.get("controls_available") is True)
        for botao in (self.player_anterior, self.player_toggle, self.player_proxima):
            botao.setEnabled(controles)
        if observado:
            posicao = float(musica.get("position_seconds") or 0.0)
            duracao = float(musica.get("duration_seconds") or 0.0)
            self.player_progresso.setValue(
                max(0, min(1000, int(posicao * 1000 / duracao))) if duracao > 0 else 0,
            )
            titulo = str(musica.get("title") or "Faixa observada")
            canal = str(musica.get("channel") or "Canal não informado")
            self.player_capa.definir_titulo(titulo)
            self.player_capa.carregar(str(musica.get("artwork_url") or ""))
            self.player_titulo.definir_texto(titulo)
            self.player_titulo.setAccessibleName(f"Faixa atual: {titulo}")
            self.player_canal.definir_texto(canal)
            self.player_canal.setAccessibleName(f"Canal atual: {canal}")
            tempo_atual = "0:00" if posicao <= 0 else _tempo(posicao)
            tempo_total = _tempo(duracao)
            self.player_tempo_atual.setText(tempo_atual)
            self.player_tempo_total.setText(tempo_total)
            self.player_tempo_atual.setAccessibleName(
                f"Tempo atual: {tempo_atual}",
            )
            self.player_tempo_total.setAccessibleName(
                f"Duração total: {tempo_total}",
            )
            self.player_estado.setText("TOCANDO" if estado == "playing" else "PAUSADA")
            self.player_toggle.setIcon(icone_terminal("pause" if estado == "playing" else "play"))

    def definir_compacto(self, compacto: bool) -> None:
        self._compacto = bool(compacto)
        self._altura_baixa = bool(0 < self.height() < 560)
        enxuto = self._compacto or self._altura_baixa
        margem_x = 9 if enxuto else 16
        margem_y = 7 if self._altura_baixa else (10 if self._compacto else 14)
        self.raiz.setContentsMargins(margem_x, margem_y, margem_x, margem_y)
        self.raiz.setSpacing(5 if self._altura_baixa else (7 if compacto else 9))
        tamanho_capa = 68 if self._altura_baixa else (80 if compacto else 104)
        self.capa.setFixedSize(tamanho_capa, tamanho_capa)
        margem_hero = 5 if self._altura_baixa else (7 if compacto else 11)
        self.hero_layout.setContentsMargins(
            margem_hero, margem_hero, margem_hero, margem_hero,
        )
        self.hero_layout.setSpacing(8 if enxuto else 12)
        self.hero.setFixedHeight(
            80 if self._altura_baixa else (96 if compacto else 128)
        )
        self.rotulo.setVisible(not self._altura_baixa)
        fonte_titulo = self.titulo.font()
        fonte_titulo.setPixelSize(20 if enxuto else 22)
        self.titulo.setFont(fonte_titulo)
        for botao in self._botoes_acoes:
            self.acoes_layout.removeWidget(botao)
        if compacto:
            for indice, botao in enumerate(self._botoes_acoes):
                self.acoes_layout.addWidget(botao, indice // 2, indice % 2)
            self.acoes_layout.setColumnStretch(0, 1)
            self.acoes_layout.setColumnStretch(1, 1)
            self.acoes_layout.setColumnStretch(5, 0)
        else:
            for coluna, botao in enumerate(self._botoes_acoes):
                self.acoes_layout.addWidget(botao, 0, coluna)
            self.acoes_layout.setColumnStretch(0, 0)
            self.acoes_layout.setColumnStretch(1, 0)
            self.acoes_layout.setColumnStretch(5, 1)
        self._organizar_player_responsivo(self.width())
        for faixa in self._linhas_widgets:
            faixa.definir_compacta(compacto)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        compacto = event.size().width() < 700
        altura_baixa = 0 < event.size().height() < 560
        if compacto != self._compacto or altura_baixa != self._altura_baixa:
            self.definir_compacto(compacto)
        self._organizar_player_responsivo(event.size().width())
        QTimer.singleShot(0, self._sincronizar_largura_das_linhas)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.definir_compacto(self.width() < 700)
        self._organizar_player_responsivo(self.width())
        QTimer.singleShot(0, self._sincronizar_largura_das_linhas)
