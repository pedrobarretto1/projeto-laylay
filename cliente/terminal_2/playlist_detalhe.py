"""Detalhe nativo e sob demanda das playlists do Terminal 2."""

from __future__ import annotations

import uuid

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QInputDialog, QLineEdit, QMenu, QMessageBox,
    QProgressBar, QPushButton, QSizePolicy, QTableWidget, QTableWidgetItem,
    QToolButton, QVBoxLayout, QWidget,
)

from cliente.terminal_2.acabamento import CapaMusicaGenerica, icone_terminal


def _tempo(segundos: object) -> str:
    if not isinstance(segundos, (int, float)) or isinstance(segundos, bool) or segundos <= 0:
        return "—"
    total = int(segundos)
    minutos, segundo = divmod(total, 60)
    horas, minutos = divmod(minutos, 60)
    return f"{horas}:{minutos:02d}:{segundo:02d}" if horas else f"{minutos}:{segundo:02d}"


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
        self._player_observado = False
        self._compacto = False
        self._operacao_pendente = ""
        self._detalhe_requisicao_id = ""
        self.raiz = QVBoxLayout(self)
        self.raiz.setContentsMargins(28, 22, 28, 28)
        self.raiz.setSpacing(14)

        topo = QHBoxLayout()
        self.voltar = QToolButton()
        self.voltar.setObjectName("playlistBack")
        self.voltar.setIcon(icone_terminal("arrow-left"))
        self.voltar.setText("Voltar")
        self.voltar.setAccessibleName("Voltar à lista de playlists")
        self.voltar.setToolTip("Voltar à lista de playlists")
        self.voltar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.voltar.clicked.connect(self.voltar_solicitado)
        topo.addWidget(self.voltar)
        topo.addStretch()
        self.raiz.addLayout(topo)

        hero = QFrame()
        hero.setObjectName("playlistHero")
        self.hero_layout = QHBoxLayout(hero)
        self.hero_layout.setContentsMargins(18, 18, 18, 18)
        self.hero_layout.setSpacing(18)
        self.capa = CapaMusicaGenerica(144)
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
        self.raiz.addWidget(hero)

        self.acoes_layout = QGridLayout()
        self.acoes_layout.setHorizontalSpacing(8)
        self.acoes_layout.setVerticalSpacing(8)
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
        self._timer_busca = QTimer(self)
        self._timer_busca.setSingleShot(True)
        self._timer_busca.setInterval(220)
        self.busca.textChanged.connect(lambda _texto: self._timer_busca.start())
        self._timer_busca.timeout.connect(lambda: self.solicitar_detalhe(reiniciar=True))
        self.raiz.addWidget(self.busca)

        self.estado = QLabel("Selecione uma playlist para ver as faixas.")
        self.estado.setObjectName("playlistDetailState")
        self.raiz.addWidget(self.estado)
        self.tabela = QTableWidget(0, 6)
        self.tabela.setObjectName("playlistTracks")
        self.tabela.setHorizontalHeaderLabels(("#", "Faixa", "Canal", "Adicionada", "Tempo", ""))
        self.tabela.verticalHeader().hide()
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setShowGrid(False)
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        cabecalho.setSectionResizeMode(1, QHeaderView.Stretch)
        cabecalho.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        cabecalho.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        cabecalho.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        cabecalho.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.raiz.addWidget(self.tabela, 1)
        self.mais = QPushButton("Carregar mais")
        self.mais.clicked.connect(lambda: self.solicitar_detalhe(reiniciar=False))
        self.mais.hide()
        self.raiz.addWidget(self.mais, 0, Qt.AlignHCenter)

        self.player = QFrame()
        self.player.setObjectName("playlistObservedPlayer")
        self.player_layout = QGridLayout(self.player)
        self.player_layout.setContentsMargins(10, 8, 10, 8)
        self.player_layout.setHorizontalSpacing(8)
        self.player_layout.setVerticalSpacing(6)
        self.player_titulo = QLabel("Reprodução observada")
        self.player_progresso = QProgressBar()
        self.player_progresso.setObjectName("playlistObservedProgress")
        self.player_progresso.setRange(0, 1000)
        self.player_progresso.setTextVisible(False)
        self.player_anterior = QToolButton(); self.player_anterior.setIcon(icone_terminal("previous"))
        self.player_toggle = QToolButton(); self.player_toggle.setIcon(icone_terminal("play"))
        self.player_proxima = QToolButton(); self.player_proxima.setIcon(icone_terminal("next"))
        controles_player = (
            (self.player_anterior, "Faixa anterior", "Voltar para a faixa anterior"),
            (self.player_toggle, "Pausar ou continuar", "Pausar ou continuar a reprodução"),
            (self.player_proxima, "Próxima faixa", "Pular para a próxima faixa"),
        )
        for botao, nome_acessivel, dica in controles_player:
            botao.setAccessibleName(nome_acessivel)
            botao.setToolTip(dica)
        self.player_layout.addWidget(self.player_titulo, 0, 0)
        self.player_layout.addWidget(self.player_progresso, 0, 1)
        self.player_layout.setColumnStretch(1, 1)
        self.player_layout.addWidget(self.player_anterior, 0, 2)
        self.player_layout.addWidget(self.player_toggle, 0, 3)
        self.player_layout.addWidget(self.player_proxima, 0, 4)
        self.player.hide()
        self.raiz.addWidget(self.player)
        self.setStyleSheet("""
            #playlistDetail { background: #0D1115; color: #F7F1F4; }
            #playlistHero { background: #171B21; border: 1px solid #2C3038; border-radius: 12px; }
            #playlistEyebrow { color: #FF667E; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
            #playlistTitle { color: #FFF9FB; font-size: 28px; font-weight: 750; }
            #playlistMeta, #playlistDetailState { color: #AFA8AE; font-size: 12px; }
            #playlistBack, #playlistDetail QPushButton, #playlistDetail QToolButton {
                color: #F6F0F3; background: #1B2027; border: 1px solid #343943;
                border-radius: 7px; padding: 7px 10px;
            }
            #playlistBack:hover, #playlistDetail QPushButton:hover, #playlistDetail QToolButton:hover {
                background: #252B33; border-color: #5A4650;
            }
            #playlistBack:focus, #playlistDetail QPushButton:focus, #playlistDetail QToolButton:focus {
                border: 2px solid #FF7187; padding: 6px 9px;
            }
            #playlistPrimaryAction { background: #FF536D; color: #160B0E; border-color: #FF7187; font-weight: 700; }
            #playlistSearch { background: #151A20; color: #F7F1F4; border: 1px solid #313640;
                border-radius: 8px; padding: 9px 11px; selection-background-color: #8B3041; }
            #playlistSearch:focus { border-color: #FF6078; }
            #playlistTracks { background: #101419; alternate-background-color: #14191F; color: #EEE8EB;
                border: 1px solid #282D35; border-radius: 9px; gridline-color: transparent; }
            #playlistTracks::item { padding: 7px; border-bottom: 1px solid #242930; }
            #playlistTracks::item:selected { background: #38222A; color: #FFFFFF; }
            #playlistTracks QHeaderView::section { background: #151A20; color: #9D969C;
                border: 0; border-bottom: 1px solid #30353D; padding: 7px; font-weight: 650; }
            #playlistObservedPlayer { background: #151A20; border: 1px solid #3A3036; border-radius: 9px; }
            #playlistObservedProgress { background: #292E35; border: 0; border-radius: 2px; max-height: 4px; }
            #playlistObservedProgress::chunk { background: #FF536D; border-radius: 2px; }
        """)

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
        for linha, item in enumerate(self._itens):
            valores = {
                0: str(linha + 1),
                2: str(item.get("channel") or "—"),
                3: str(item.get("added_at") or "—"),
                4: _tempo(item.get("duration_seconds")),
            }
            for coluna, valor in valores.items():
                self.tabela.setItem(linha, coluna, QTableWidgetItem(valor))
            faixa_widget = QWidget()
            faixa_lay = QHBoxLayout(faixa_widget)
            faixa_lay.setContentsMargins(2, 2, 4, 2)
            faixa_lay.setSpacing(8)
            miniatura = CapaMusicaGenerica(32)
            miniatura.definir_titulo(str(item.get("title") or ""))
            miniatura.carregar(str(item.get("artwork_url") or ""))
            faixa_lay.addWidget(miniatura)
            titulo_faixa = QLabel(str(item.get("title") or "Faixa sem título"))
            titulo_faixa.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            titulo_faixa.setToolTip(titulo_faixa.text())
            faixa_lay.addWidget(titulo_faixa, 1)
            self.tabela.setCellWidget(linha, 1, faixa_widget)
            self.tabela.setRowHeight(linha, 42)
            menu = QToolButton()
            menu.setIcon(icone_terminal("more-horizontal"))
            menu.setAccessibleName(f"Opções para {item.get('title') or 'faixa'}")
            menu.setToolTip(f"Ações para {item.get('title') or 'esta faixa'}")
            menu.setPopupMode(QToolButton.InstantPopup)
            opcoes = QMenu(menu)
            menu.setMenu(opcoes)
            for texto, op in (("Tocar agora", "play_track"), ("Copiar para outra playlist", "copy_track"),
                              ("Mover para outra playlist", "move_track"), ("Remover", "remove_track")):
                acao = opcoes.addAction(texto)
                acao.triggered.connect(lambda _v=False, o=op, i=item: self._confirmar_e_requisitar(o, i))
            self.tabela.setCellWidget(linha, 5, menu)
        self.mais.setVisible(bool(resultado.get("has_more")))

    def aplicar_player_observado(self, musica: dict) -> None:
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
            self.player_titulo.setText(
                f"{musica.get('title') or 'Faixa observada'}  ·  {_tempo(musica.get('position_seconds'))} / {_tempo(musica.get('duration_seconds'))}"
            )
            self.player_toggle.setIcon(icone_terminal("pause" if estado == "playing" else "play"))

    def definir_compacto(self, compacto: bool) -> None:
        self._compacto = bool(compacto)
        self.raiz.setContentsMargins(
            14 if compacto else 28, 16 if compacto else 22,
            14 if compacto else 28, 18 if compacto else 28,
        )
        self.capa.setFixedSize(96 if compacto else 144, 96 if compacto else 144)
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
        for widget in (
            self.player_titulo, self.player_progresso, self.player_anterior,
            self.player_toggle, self.player_proxima,
        ):
            self.player_layout.removeWidget(widget)
        if compacto:
            self.player_layout.addWidget(self.player_titulo, 0, 0, 1, 5)
            self.player_layout.addWidget(self.player_progresso, 1, 0, 1, 2)
            self.player_layout.addWidget(self.player_anterior, 1, 2)
            self.player_layout.addWidget(self.player_toggle, 1, 3)
            self.player_layout.addWidget(self.player_proxima, 1, 4)
            self.player_layout.setColumnStretch(0, 1)
            self.player_layout.setColumnStretch(1, 1)
        else:
            self.player_layout.addWidget(self.player_titulo, 0, 0)
            self.player_layout.addWidget(self.player_progresso, 0, 1)
            self.player_layout.addWidget(self.player_anterior, 0, 2)
            self.player_layout.addWidget(self.player_toggle, 0, 3)
            self.player_layout.addWidget(self.player_proxima, 0, 4)
            self.player_layout.setColumnStretch(0, 0)
            self.player_layout.setColumnStretch(1, 1)
        self.tabela.setColumnHidden(2, compacto)
        self.tabela.setColumnHidden(3, compacto)
