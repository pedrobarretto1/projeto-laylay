"""Detalhe nativo e sob demanda das playlists do Terminal 2."""

from __future__ import annotations

import random
import re
import time
import uuid

from PySide6.QtCore import (
    QEasingCurve, Property, QParallelAnimationGroup, QPropertyAnimation,
    QSequentialAnimationGroup, QRectF, QSize, Qt, Signal, QTimer,
)
from PySide6.QtGui import QColor, QFontDatabase, QFontMetrics, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QInputDialog, QLineEdit, QMenu, QMessageBox,
    QGraphicsOpacityEffect, QListWidget, QListWidgetItem, QProgressBar,
    QPushButton, QSizePolicy, QTableWidget, QStackedLayout, QToolButton,
    QVBoxLayout, QWidget,
)

from cliente.terminal_2.acabamento import CapaMusicaGenerica, icone_terminal


def _tempo(segundos: object) -> str:
    if not isinstance(segundos, (int, float)) or isinstance(segundos, bool) or segundos <= 0:
        return "—"
    total = int(segundos)
    minutos, segundo = divmod(total, 60)
    horas, minutos = divmod(minutos, 60)
    return f"{horas}:{minutos:02d}:{segundo:02d}" if horas else f"{minutos}:{segundo:02d}"


def _titulo_comparavel(valor: object) -> str:
    """Normaliza o prefixo numérico que o player pode acrescentar ao título."""
    texto = re.sub(r"^\s*\(\s*\d+\s*\)\s*", "", str(valor or ""))
    return " ".join(texto.casefold().split())


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


class IndicadorFaixaTocando(QWidget):
    """Equalizador compacto que identifica a faixa atualmente reproduzida."""

    def __init__(
        self,
        *,
        reduzir_movimento: bool = False,
        semente: int | None = None,
    ) -> None:
        super().__init__()
        self._reduzir_movimento = bool(reduzir_movimento)
        self._aleatorio = random.Random(semente)
        self._alturas = [7.0, 13.0, 10.0]
        self._origens = list(self._alturas)
        self._alvos = list(self._alturas)
        self._progresso = [0, 0, 0]
        self._duracoes = [1, 1, 1]
        self._niveis_sincronizados: list[float] | None = None
        self._ultima_amostra_sincronizada = 0.0
        self._sincronizacao_ativa = False
        for indice in range(len(self._alturas)):
            self._sortear_alvo(indice)
        self.setFixedSize(24, 24)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAccessibleName("Faixa tocando")
        self._timer = QTimer(self)
        # 20 FPS são suficientes para este desenho de 24 px parecer contínuo,
        # sem manter o event loop ocupado como uma animação de alta frequência.
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._avancar)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if not self._reduzir_movimento:
            self._timer.start()

    def hideEvent(self, event) -> None:  # noqa: N802
        self._timer.stop()
        super().hideEvent(event)

    def _avancar(self) -> None:
        if (
            self._niveis_sincronizados is not None
            and time.monotonic() - self._ultima_amostra_sincronizada <= 0.35
        ):
            self._sincronizacao_ativa = True
            for indice, nivel in enumerate(self._niveis_sincronizados):
                alvo = 4.5 + nivel * 10.5
                self._alturas[indice] += (alvo - self._alturas[indice]) * 0.72
            self.update()
            return
        if self._sincronizacao_ativa:
            self._sincronizacao_ativa = False
            for indice in range(len(self._alturas)):
                self._sortear_alvo(indice)
        for indice in range(len(self._alturas)):
            self._progresso[indice] += 1
            duracao = self._duracoes[indice]
            progresso = min(1.0, self._progresso[indice] / duracao)
            suavizado = progresso * progresso * (3.0 - 2.0 * progresso)
            origem = self._origens[indice]
            alvo = self._alvos[indice]
            self._alturas[indice] = origem + (alvo - origem) * suavizado
            if self._progresso[indice] >= duracao:
                self._alturas[indice] = alvo
                self._sortear_alvo(indice)
        self.update()

    def aplicar_niveis(self, niveis: object) -> bool:
        if not isinstance(niveis, list) or len(niveis) != 3:
            return False
        limpos: list[float] = []
        for nivel in niveis:
            if isinstance(nivel, bool):
                return False
            try:
                limpos.append(max(0.0, min(1.0, float(nivel))))
            except (TypeError, ValueError):
                return False
        self._niveis_sincronizados = limpos
        self._ultima_amostra_sincronizada = time.monotonic()
        return True

    def _sortear_alvo(self, indice: int) -> None:
        origem = self._alturas[indice]
        alvo = origem
        for _tentativa in range(8):
            candidato = self._aleatorio.uniform(5.0, 15.0)
            if abs(candidato - origem) >= 2.75:
                alvo = candidato
                break
        if alvo == origem:
            alvo = 15.0 if origem < 10.0 else 5.0
        self._origens[indice] = origem
        self._alvos[indice] = alvo
        self._progresso[indice] = 0
        # Cada barra respira em uma duração própria (250–550 ms). Isso impede
        # que as três voltem a formar um ciclo visual reconhecível.
        self._duracoes[indice] = self._aleatorio.randint(5, 11)

    def _alturas_atuais(self) -> tuple[float, float, float]:
        return (
            round(self._alturas[0], 3),
            round(self._alturas[1], 3),
            round(self._alturas[2], 3),
        )

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#1ED760"))
        alturas = self._alturas_atuais()
        base = 18.0
        for indice, altura in enumerate(alturas):
            painter.drawRoundedRect(
                QRectF(6.0 + indice * 5.0, base - altura, 2.0, altura),
                1.0,
                1.0,
            )


class FaixaPlaylistRow(QFrame):
    """Linha silenciosa em repouso, operável no hover ou foco de teclado."""

    tocar_solicitado = Signal(dict)
    acao_solicitada = Signal(str, dict)
    selecionada = Signal(int)

    def __init__(
        self,
        indice: int,
        item: dict,
        *,
        reduzir_movimento: bool = False,
    ) -> None:
        super().__init__()
        self.indice = indice
        self.item = item
        self._sob_mouse = False
        self._selecionada = False
        self._foco_teclado = False
        self._tocando = False
        self._compacta = False
        self._modo_metadados = ""
        self._reduzir_movimento = bool(reduzir_movimento)
        self._intensidade_hover = 0.0
        self._intensidade_pulso = 0.0
        self._animacao_hover: QPropertyAnimation | None = None
        self._animacao_pulso: QPropertyAnimation | None = None
        self.setObjectName("playlistTrackRow")
        self.setProperty("interactive", False)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setAccessibleName(
            f"Faixa {indice + 1}: {item.get('title') or 'sem título'}"
        )

        layout = QHBoxLayout(self)
        self._layout_faixa = layout
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

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
        self.indicador_tocando = IndicadorFaixaTocando(
            reduzir_movimento=self._reduzir_movimento,
        )
        controle.addWidget(self.indicador_tocando)
        self._controle = controle
        layout.addWidget(self.controle_slot)

        self.capa = CapaMusicaGenerica(40)
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
        self.canal.setMaximumWidth(200)
        self.canal.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
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
        self.duracao.setFixedWidth(58)
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
            ("Adicionar a playlists", "copy_track"),
            ("Mover para playlists", "move_track"),
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
        tamanho_capa = 32 if self._compacta else 40
        self.capa.setFixedSize(tamanho_capa, tamanho_capa)
        margem_vertical = 4 if self._compacta else 6
        self._layout_faixa.setContentsMargins(
            6 if self._compacta else 8,
            margem_vertical,
            6 if self._compacta else 8,
            margem_vertical,
        )
        self._layout_faixa.setSpacing(8 if self._compacta else 10)
        self._atualizar_metadados_responsivos(self.width())

    def definir_largura_disponivel(self, largura: int) -> None:
        """Recebe a largura observada do viewport que realmente contém a linha."""
        self._atualizar_metadados_responsivos(max(0, int(largura)))

    def _atualizar_metadados_responsivos(self, largura: int) -> None:
        # A linha é a fronteira real de espaço: a data cede primeiro; depois o
        # canal migra para a sublinha sem competir com título, capa e duração.
        modo = (
            "essencial" if self._compacta or largura < 540
            else ("completo" if largura >= 720 else "sem_data")
        )
        if modo == self._modo_metadados:
            return
        self._modo_metadados = modo
        self.adicionada.setVisible(modo == "completo")
        self.canal.setVisible(modo != "essencial")
        if modo != "essencial":
            self.canal.setMaximumWidth(200 if modo == "completo" else 170)
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
        # A seleção continua existindo para ações contextuais, mas não mantém
        # uma segunda linha visualmente ativa depois que o mouse sai.
        self._selecionada = bool(selecionada)

    def definir_tocando(self, tocando: bool, *, pulsar: bool = False) -> None:
        tocando = bool(tocando)
        if tocando == self._tocando:
            return
        self._tocando = tocando
        self.setProperty("playing", tocando)
        self.titulo.setProperty("playing", tocando)
        self.setAccessibleName(
            f"Faixa {self.indice + 1}: {self.item.get('title') or 'sem título'}"
            + (", tocando" if tocando else "")
        )
        for widget in (self, self.titulo):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self._atualizar_interacao()
        if tocando and pulsar:
            self._iniciar_pulso()
        elif not tocando:
            self._encerrar_pulso()

    def enterEvent(self, event) -> None:  # noqa: N802
        self._sob_mouse = True
        self._atualizar_interacao()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._sob_mouse = False
        self._atualizar_interacao()
        super().leaveEvent(event)

    def focusInEvent(self, event) -> None:  # noqa: N802
        self._foco_teclado = event.reason() in {
            Qt.TabFocusReason,
            Qt.BacktabFocusReason,
            Qt.ShortcutFocusReason,
        }
        self.selecionada.emit(self.indice)
        super().focusInEvent(event)
        self._atualizar_interacao()

    def focusOutEvent(self, event) -> None:  # noqa: N802
        self._foco_teclado = False
        super().focusOutEvent(event)
        self._atualizar_interacao()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._foco_teclado = False
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
        interativa = self._sob_mouse or self._foco_teclado
        self.setProperty("interactive", interativa)
        controle = (
            self.play if interativa
            else (self.indicador_tocando if self._tocando else self.numero)
        )
        self._controle.setCurrentWidget(controle)
        self.menu.setVisible(interativa)
        self.style().unpolish(self)
        self.style().polish(self)
        self._animar_hover(1.0 if interativa else 0.0)

    def _ler_intensidade_hover(self) -> float:
        return self._intensidade_hover

    def _definir_intensidade_hover(self, valor: float) -> None:
        self._intensidade_hover = max(0.0, min(1.0, float(valor)))
        self.update()

    intensidadeHover = Property(  # noqa: N815
        float, _ler_intensidade_hover, _definir_intensidade_hover,
    )

    def _ler_intensidade_pulso(self) -> float:
        return self._intensidade_pulso

    def _definir_intensidade_pulso(self, valor: float) -> None:
        self._intensidade_pulso = max(0.0, min(1.0, float(valor)))
        self.update()

    intensidadePulso = Property(  # noqa: N815
        float, _ler_intensidade_pulso, _definir_intensidade_pulso,
    )

    def _animar_hover(self, destino: float) -> None:
        if self._animacao_hover is not None:
            self._animacao_hover.stop()
            self._animacao_hover.deleteLater()
            self._animacao_hover = None
        if self._reduzir_movimento or not self.isVisible():
            self._definir_intensidade_hover(destino)
            return
        if abs(self._intensidade_hover - destino) < 0.01:
            return
        animacao = QPropertyAnimation(self, b"intensidadeHover", self)
        animacao.setDuration(140)
        animacao.setStartValue(self._intensidade_hover)
        animacao.setEndValue(destino)
        animacao.setEasingCurve(QEasingCurve.OutCubic)
        self._animacao_hover = animacao

        def finalizar() -> None:
            if self._animacao_hover is animacao:
                self._animacao_hover = None
            animacao.deleteLater()

        animacao.finished.connect(finalizar)
        animacao.start()

    def _encerrar_pulso(self) -> None:
        if self._animacao_pulso is not None:
            self._animacao_pulso.stop()
            self._animacao_pulso.deleteLater()
            self._animacao_pulso = None
        self._definir_intensidade_pulso(0.0)

    def _iniciar_pulso(self) -> None:
        self._encerrar_pulso()
        if self._reduzir_movimento or not self.isVisible():
            return
        animacao = QPropertyAnimation(self, b"intensidadePulso", self)
        animacao.setDuration(440)
        animacao.setStartValue(0.0)
        animacao.setKeyValueAt(0.32, 1.0)
        animacao.setEndValue(0.0)
        animacao.setEasingCurve(QEasingCurve.OutCubic)
        self._animacao_pulso = animacao

        def finalizar() -> None:
            self._definir_intensidade_pulso(0.0)
            if self._animacao_pulso is animacao:
                self._animacao_pulso = None
            animacao.deleteLater()

        animacao.finished.connect(finalizar)
        animacao.start()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if self._intensidade_hover <= 0 and self._intensidade_pulso <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        area = self.rect().adjusted(0, 0, -1, -1)
        if self._intensidade_hover > 0:
            cor_hover = QColor("#18212B")
            cor_hover.setAlpha(round(238 * self._intensidade_hover))
            painter.setBrush(cor_hover)
            painter.drawRoundedRect(area, 7, 7)
        if self._intensidade_pulso > 0:
            cor_pulso = QColor("#1ED760")
            cor_pulso.setAlpha(round(30 * self._intensidade_pulso))
            painter.setBrush(cor_pulso)
            painter.drawRoundedRect(area, 7, 7)


class SeletorDestinosPlaylist(QFrame):
    """Etapa nativa, pesquisável e virtualizada para mutações em lote."""

    confirmado = Signal(str, dict, list)
    cancelado = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("playlistDestinationFlow")
        self._operacao = ""
        self._faixa: dict = {}

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(18, 18, 18, 16)
        raiz.setSpacing(12)

        topo = QHBoxLayout()
        textos = QVBoxLayout()
        textos.setSpacing(3)
        self.eyebrow = QLabel("ORGANIZAR FAIXA")
        self.eyebrow.setObjectName("playlistDestinationEyebrow")
        self.titulo = QLabel("Escolha os destinos")
        self.titulo.setObjectName("playlistDestinationTitle")
        self.subtitulo = QLabel()
        self.subtitulo.setObjectName("playlistDestinationSubtitle")
        self.subtitulo.setWordWrap(True)
        textos.addWidget(self.eyebrow)
        textos.addWidget(self.titulo)
        textos.addWidget(self.subtitulo)
        topo.addLayout(textos, 1)
        self.fechar = QToolButton()
        self.fechar.setObjectName("playlistDestinationClose")
        self.fechar.setText("×")
        self.fechar.setFixedSize(32, 32)
        self.fechar.setAccessibleName("Cancelar escolha de playlists")
        self.fechar.clicked.connect(self.cancelado)
        topo.addWidget(self.fechar, 0, Qt.AlignTop)
        raiz.addLayout(topo)

        faixa = QFrame()
        faixa.setObjectName("playlistDestinationTrack")
        faixa_layout = QHBoxLayout(faixa)
        faixa_layout.setContentsMargins(12, 9, 12, 9)
        faixa_layout.setSpacing(10)
        self.capa = CapaMusicaGenerica(42)
        faixa_layout.addWidget(self.capa)
        identidade = QVBoxLayout()
        identidade.setSpacing(1)
        self.faixa_titulo = RotuloElidido("Faixa")
        self.faixa_titulo.setObjectName("playlistDestinationTrackTitle")
        self.faixa_meta = RotuloElidido("Playlist de origem")
        self.faixa_meta.setObjectName("playlistDestinationTrackMeta")
        identidade.addWidget(self.faixa_titulo)
        identidade.addWidget(self.faixa_meta)
        faixa_layout.addLayout(identidade, 1)
        raiz.addWidget(faixa)

        ferramentas = QHBoxLayout()
        self.busca = QLineEdit()
        self.busca.setObjectName("playlistDestinationSearch")
        self.busca.setPlaceholderText("Pesquisar entre as playlists")
        self.busca.setClearButtonEnabled(True)
        self.busca.setAccessibleName("Pesquisar playlists de destino")
        self.busca.textChanged.connect(self._filtrar)
        ferramentas.addWidget(self.busca, 1)
        self.selecionar_visiveis = QPushButton("Selecionar visíveis")
        self.selecionar_visiveis.setObjectName("playlistDestinationUtility")
        self.selecionar_visiveis.clicked.connect(self._selecionar_todas_visiveis)
        ferramentas.addWidget(self.selecionar_visiveis)
        self.limpar = QPushButton("Limpar")
        self.limpar.setObjectName("playlistDestinationUtility")
        self.limpar.clicked.connect(self._limpar_selecao)
        ferramentas.addWidget(self.limpar)
        raiz.addLayout(ferramentas)

        self.lista = QListWidget()
        self.lista.setObjectName("playlistDestinationList")
        self.lista.setUniformItemSizes(True)
        self.lista.setAlternatingRowColors(False)
        self.lista.setSelectionMode(QAbstractItemView.NoSelection)
        self.lista.itemChanged.connect(lambda _item: self._atualizar_resumo())
        raiz.addWidget(self.lista, 1)

        rodape = QHBoxLayout()
        resumo = QVBoxLayout()
        resumo.setSpacing(1)
        self.contador = QLabel("Nenhuma playlist selecionada")
        self.contador.setObjectName("playlistDestinationCount")
        self.aviso = QLabel()
        self.aviso.setObjectName("playlistDestinationWarning")
        self.aviso.setWordWrap(True)
        resumo.addWidget(self.contador)
        resumo.addWidget(self.aviso)
        rodape.addLayout(resumo, 1)
        self.cancelar = QPushButton("Cancelar")
        self.cancelar.setObjectName("playlistDestinationCancel")
        self.cancelar.clicked.connect(self.cancelado)
        rodape.addWidget(self.cancelar)
        self.confirmar = QPushButton("Escolha uma playlist")
        self.confirmar.setObjectName("playlistDestinationConfirm")
        self.confirmar.setEnabled(False)
        self.confirmar.clicked.connect(self._confirmar)
        rodape.addWidget(self.confirmar)
        raiz.addLayout(rodape)

    def abrir(
        self,
        operacao: str,
        faixa: dict,
        origem: str,
        catalogo: list[dict],
    ) -> None:
        self._operacao = str(operacao or "")
        self._faixa = dict(faixa or {})
        movendo = self._operacao == "move_track"
        self.titulo.setText(
            "Mover para playlists" if movendo else "Adicionar a playlists"
        )
        self.subtitulo.setText(
            "Selecione quantos destinos quiser. A alteração será aplicada "
            "como uma única operação segura."
        )
        titulo = str(self._faixa.get("title") or "Faixa sem título")
        self.faixa_titulo.definir_texto(titulo)
        self.faixa_meta.definir_texto(f"Origem: {origem}")
        self.capa.definir_titulo(titulo)
        self.capa.carregar(str(self._faixa.get("artwork_url") or ""))
        self.busca.clear()
        self.lista.blockSignals(True)
        self.lista.clear()
        origem_chave = str(origem or "").casefold()
        for bruto in catalogo[:1_000]:
            item_catalogo = dict(bruto or {})
            nome = str(item_catalogo.get("name") or "").strip()
            if not nome or nome.casefold() == origem_chave:
                continue
            quantidade = max(0, int(item_catalogo.get("count") or 0))
            sufixo = f"{quantidade} faixa{'s' if quantidade != 1 else ''}"
            item = QListWidgetItem(f"{nome}\n{sufixo}")
            item.setData(Qt.UserRole, nome)
            item.setData(Qt.UserRole + 1, nome.casefold())
            item.setFlags(
                Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable
            )
            item.setCheckState(Qt.Unchecked)
            item.setSizeHint(QSize(0, 54))
            item.setToolTip(f"Selecionar {nome} como destino")
            self.lista.addItem(item)
        self.lista.blockSignals(False)
        self.aviso.setText(
            "A origem só será removida depois que todos os destinos forem "
            "gravados com sucesso."
            if movendo else
            "A faixa original continuará nesta playlist."
        )
        self._atualizar_resumo()
        self.show()
        self.busca.setFocus(Qt.OtherFocusReason)

    def destinos_selecionados(self) -> list[str]:
        return [
            str(self.lista.item(indice).data(Qt.UserRole) or "")
            for indice in range(self.lista.count())
            if self.lista.item(indice).checkState() == Qt.Checked
        ]

    def _filtrar(self, texto: str) -> None:
        consulta = " ".join(str(texto or "").casefold().split())
        for indice in range(self.lista.count()):
            item = self.lista.item(indice)
            item.setHidden(
                bool(consulta and consulta not in str(
                    item.data(Qt.UserRole + 1) or ""
                ))
            )

    def _selecionar_todas_visiveis(self) -> None:
        self.lista.blockSignals(True)
        for indice in range(self.lista.count()):
            item = self.lista.item(indice)
            if not item.isHidden():
                item.setCheckState(Qt.Checked)
        self.lista.blockSignals(False)
        self._atualizar_resumo()

    def _limpar_selecao(self) -> None:
        self.lista.blockSignals(True)
        for indice in range(self.lista.count()):
            self.lista.item(indice).setCheckState(Qt.Unchecked)
        self.lista.blockSignals(False)
        self._atualizar_resumo()

    def _atualizar_resumo(self) -> None:
        total = len(self.destinos_selecionados())
        self.contador.setText(
            "Nenhuma playlist selecionada" if total == 0
            else f"{total} playlist{'s' if total != 1 else ''} selecionada{'s' if total != 1 else ''}"
        )
        verbo = "Mover" if self._operacao == "move_track" else "Adicionar"
        self.confirmar.setText(
            "Escolha uma playlist" if total == 0
            else f"{verbo} para {total} playlist{'s' if total != 1 else ''}"
        )
        self.confirmar.setEnabled(total > 0)

    def _confirmar(self) -> None:
        destinos = self.destinos_selecionados()
        if destinos:
            self.confirmado.emit(self._operacao, self._faixa, destinos)


class PlaylistDetalhe(QWidget):
    voltar_solicitado = Signal()
    requisicao_solicitada = Signal(dict)

    def __init__(self, *, reduzir_movimento: bool = False) -> None:
        super().__init__()
        self.setObjectName("playlistDetail")
        self._nome = ""
        self._revisao = ""
        self._offset = 0
        self._itens: list[dict] = []
        self._catalogo: list[dict] = []
        self._linhas_widgets: list[FaixaPlaylistRow] = []
        self._linha_selecionada = -1
        self._player_observado = False
        self._video_id_tocando = ""
        self._titulo_tocando = ""
        self._compacto = False
        self._altura_baixa = False
        self._operacao_pendente = ""
        self._detalhe_requisicao_id = ""
        self._reduzir_movimento = bool(reduzir_movimento)
        self._entrada_pendente = False
        self._entrada_aguardando_show = False
        self._animacao_entrada: QParallelAnimationGroup | None = None
        self._efeitos_entrada: list[tuple[QWidget, QGraphicsOpacityEffect]] = []
        self._identidade_player = ""
        self._animacao_identidade_player: (
            QSequentialAnimationGroup | None
        ) = None
        self._efeito_identidade_player: QGraphicsOpacityEffect | None = None
        self._ocultacao_antes_destinos: list[tuple[QWidget, bool]] = []
        # Mantém a composição legível em monitores largos sem limitar a página
        # responsiva: o conteúdo cresce até 1260 px e permanece centralizado.
        self.pagina_layout = QHBoxLayout(self)
        self.pagina_layout.setContentsMargins(0, 0, 0, 0)
        self.pagina_layout.setSpacing(0)
        self.conteudo = QWidget()
        self.conteudo.setObjectName("playlistContent")
        self.conteudo.setMaximumWidth(1260)
        self.conteudo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pagina_layout.addStretch(1)
        self.pagina_layout.addWidget(self.conteudo, 100)
        self.pagina_layout.addStretch(1)
        self.raiz = QVBoxLayout(self.conteudo)
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
        self.voltar.clicked.connect(self._voltar_contextual)
        topo.addWidget(self.voltar)
        topo.addStretch()
        self.raiz.addLayout(topo)

        self.seletor_destinos = SeletorDestinosPlaylist()
        self.seletor_destinos.cancelado.connect(self._fechar_seletor_destinos)
        self.seletor_destinos.confirmado.connect(self._confirmar_destinos)
        self.seletor_destinos.hide()
        self.raiz.addWidget(self.seletor_destinos, 1)

        self.hero = QFrame()
        self.hero.setObjectName("playlistHero")
        # O sizeHint do hero amplo não pode impedir a janela de alcançar 375 px;
        # o resize troca capa/título para a densidade estreita antes de comprimir.
        self.hero.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.hero_layout = QHBoxLayout(self.hero)
        self.hero_layout.setContentsMargins(12, 12, 12, 12)
        self.hero_layout.setSpacing(12)
        self.capa = CapaMusicaGenerica(104)
        self.capa.setAccessibleName("Capa da playlist")
        self.hero_layout.addWidget(self.capa)
        self.identidade_layout = QVBoxLayout()
        self.identidade_layout.setContentsMargins(0, 0, 0, 0)
        self.identidade_layout.setSpacing(4)
        self.rotulo = QLabel("PLAYLIST")
        self.rotulo.setObjectName("playlistEyebrow")
        self.titulo = QLabel("Playlist")
        self.titulo.setObjectName("playlistTitle")
        self.titulo.setWordWrap(True)
        self.meta = QLabel("Carregando…")
        self.meta.setObjectName("playlistMeta")
        self.identidade_layout.addStretch()
        self.identidade_layout.addWidget(self.rotulo)
        self.identidade_layout.addWidget(self.titulo)
        self.identidade_layout.addWidget(self.meta)
        self.acoes_layout = QGridLayout()
        self.acoes_layout.setContentsMargins(0, 6, 0, 0)
        self.acoes_layout.setHorizontalSpacing(8)
        self.acoes_layout.setVerticalSpacing(6)
        self.play = QPushButton("Tocar")
        self.play.setObjectName("playlistPrimaryAction")
        self.play.setIcon(icone_terminal("play"))
        self.shuffle = QPushButton("Aleatório")
        self.shuffle.setObjectName("playlistSecondaryAction")
        self.shuffle.setIcon(icone_terminal("shuffle"))
        self.adicionar = QPushButton("Adicionar URL")
        self.capa_trocar = QPushButton("Trocar capa")
        self.capa_restaurar = QPushButton("Restaurar capa")
        self.mais_acoes = QToolButton()
        self.mais_acoes.setObjectName("playlistMoreActions")
        self.mais_acoes.setText("•••")
        self.mais_acoes.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.mais_acoes.setPopupMode(QToolButton.InstantPopup)
        self.mais_acoes.setFixedWidth(38)
        self.mais_acoes.setAccessibleName("Mais opções da playlist")
        self.mais_acoes.setToolTip("Adicionar faixa e gerenciar a capa")
        self.menu_acoes = QMenu(self.mais_acoes)
        self.mais_acoes.setMenu(self.menu_acoes)
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
            botao.setFixedHeight(34)
        # Os botões continuam sendo os pontos funcionais e acessíveis; as três
        # ações menos frequentes são expostas pelo menu sem duplicar contratos.
        for botao in (self.adicionar, self.capa_trocar, self.capa_restaurar):
            botao.hide()
            acao = self.menu_acoes.addAction(botao.text())
            acao.setToolTip(botao.toolTip())
            acao.triggered.connect(botao.click)
        self.acoes_layout.addWidget(self.play, 0, 0)
        self.acoes_layout.addWidget(self.shuffle, 0, 1)
        self.acoes_layout.addWidget(self.mais_acoes, 0, 2)
        self.acoes_layout.setColumnStretch(3, 1)
        self.identidade_layout.addLayout(self.acoes_layout)
        self.identidade_layout.addStretch()
        self.hero_layout.addLayout(self.identidade_layout, 1)
        self.raiz.addWidget(self.hero)
        self.play.clicked.connect(lambda: self._requisitar("play_playlist"))
        self.shuffle.clicked.connect(lambda: self._requisitar("shuffle_playlist"))
        self.adicionar.clicked.connect(self._adicionar_url)
        self.capa_trocar.clicked.connect(self._trocar_capa)
        self.capa_restaurar.clicked.connect(lambda: self._requisitar("restore_artwork"))

        self.busca = QLineEdit()
        self.busca.setObjectName("playlistSearch")
        self.busca.setPlaceholderText("Pesquisar faixas nesta playlist")
        self.busca.setAccessibleName("Pesquisar faixas nesta playlist")
        self.busca.setClearButtonEnabled(True)
        self.busca.setFixedHeight(38)
        self._timer_busca = QTimer(self)
        self._timer_busca.setSingleShot(True)
        self._timer_busca.setInterval(220)
        self.busca.textChanged.connect(lambda _texto: self._timer_busca.start())
        self._timer_busca.timeout.connect(lambda: self.solicitar_detalhe(reiniciar=True))
        self.raiz.addWidget(self.busca)

        self.cabecalho_faixas = QFrame()
        self.cabecalho_faixas.setObjectName("playlistTracksHeader")
        self.cabecalho_faixas.setMinimumWidth(0)
        self.cabecalho_faixas.setSizePolicy(
            QSizePolicy.Ignored, QSizePolicy.Fixed,
        )
        cabecalho_layout = QHBoxLayout(self.cabecalho_faixas)
        cabecalho_layout.setContentsMargins(8, 0, 8, 0)
        cabecalho_layout.setSpacing(10)
        self.cabecalho_numero = QLabel("#")
        self.cabecalho_numero.setFixedWidth(24)
        self.cabecalho_capa = QWidget()
        self.cabecalho_capa.setFixedWidth(40)
        self.cabecalho_faixa = QLabel("FAIXA")
        self.cabecalho_canal = QLabel("CANAL")
        self.cabecalho_canal.setFixedWidth(200)
        self.cabecalho_adicionada = QLabel("ADICIONADA")
        self.cabecalho_adicionada.setFixedWidth(88)
        self.cabecalho_duracao = QLabel("DURAÇÃO")
        self.cabecalho_duracao.setFixedWidth(58)
        self.cabecalho_duracao.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.cabecalho_menu = QWidget()
        self.cabecalho_menu.setFixedWidth(24)
        for rotulo_cabecalho in (
            self.cabecalho_numero, self.cabecalho_faixa,
            self.cabecalho_canal, self.cabecalho_adicionada,
            self.cabecalho_duracao,
        ):
            rotulo_cabecalho.setObjectName("playlistColumnLabel")
        cabecalho_layout.addWidget(self.cabecalho_numero)
        cabecalho_layout.addWidget(self.cabecalho_capa)
        cabecalho_layout.addWidget(self.cabecalho_faixa, 1)
        cabecalho_layout.addWidget(self.cabecalho_canal)
        cabecalho_layout.addWidget(self.cabecalho_adicionada)
        cabecalho_layout.addWidget(self.cabecalho_duracao)
        cabecalho_layout.addWidget(self.cabecalho_menu)
        self.cabecalho_faixas.setFixedHeight(24)
        self.raiz.addWidget(self.cabecalho_faixas)

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
            #playlistDetail { background: #0B0F13; color: #F5F7FA; }
            #playlistContent { background: transparent; }
            #playlistHero {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #18202A, stop:1 #121820);
                border: 1px solid #27313C; border-radius: 12px;
            }
            #playlistEyebrow {
                color: #FF536D; font-size: 11px; font-weight: 700;
                letter-spacing: 1.4px;
            }
            #playlistTitle { color: #F5F7FA; font-weight: 700; }
            #playlistMeta, #playlistDetailState { color: #909AA7; font-size: 11px; }
            #playlistBack, #playlistDetail QPushButton, #playlistDetail QToolButton {
                color: #F5F7FA; background: #18202A; border: 1px solid #27313C;
                border-radius: 7px; padding: 5px 10px;
            }
            #playlistBack { background: transparent; }
            #playlistBack:hover, #playlistDetail QPushButton:hover,
            #playlistDetail QToolButton:hover {
                background: #202A35; border-color: #3A4755;
            }
            #playlistBack:focus, #playlistDetail QPushButton:focus,
            #playlistDetail QToolButton:focus { border: 1px solid #FF7187; }
            #playlistDetail #playlistPrimaryAction {
                background: #FF536D; color: #11161C; border-color: #FF536D;
                font-weight: 700; padding-left: 14px; padding-right: 14px;
            }
            #playlistDetail #playlistPrimaryAction:hover { background: #FF667E; border-color: #FF7187; }
            #playlistDetail #playlistSecondaryAction { background: #1B2530; font-weight: 600; }
            #playlistDetail #playlistMoreActions { padding: 0; font-size: 8px; }
            #playlistDetail #playlistMoreActions::menu-indicator { image: none; width: 0; height: 0; }
            QMenu {
                background: #18202A; color: #F5F7FA; border: 1px solid #344150;
                border-radius: 7px; padding: 5px;
            }
            QMenu::item { padding: 7px 24px 7px 10px; border-radius: 4px; }
            QMenu::item:selected { background: #26313D; color: #FFFFFF; }
            QMenu::item:disabled { color: #66717E; }
            #playlistSearch {
                background: #121820; color: #F5F7FA; border: 1px solid #27313C;
                border-radius: 8px; padding: 6px 11px;
                selection-background-color: #A9354B;
            }
            #playlistSearch:hover { border-color: #344150; }
            #playlistSearch:focus { border-color: #FF536D; background: #151C25; }
            #playlistTracksHeader { background: transparent; border-bottom: 1px solid #202A34; }
            #playlistColumnLabel {
                color: #7F8A96; font-size: 10px; font-weight: 700;
                letter-spacing: 0.8px;
            }
            #playlistTracks {
                background: transparent; color: #E9EDF2; border: 0;
                border-radius: 8px; gridline-color: transparent; outline: 0;
            }
            #playlistTracks::item { padding: 0; border: 0; background: transparent; }
            #playlistTrackRow { background: transparent; border: 0; border-radius: 7px; }
            #playlistTrackRow[playing="true"] { background: #0E1814; }
            #playlistTrackRow[interactive="true"] { background: transparent; }
            #playlistTrackNumber { color: #7F8A96; font-size: 11px; }
            #playlistTrackTitle { color: #F5F7FA; font-size: 12px; font-weight: 650; }
            #playlistTrackTitle[playing="true"] { color: #1ED760; }
            #playlistTrackMeta, #playlistTrackChannel, #playlistTrackAdded,
            #playlistTrackDuration { color: #909AA7; font-size: 11px; }
            #playlistDetail #playlistTrackPlay, #playlistDetail #playlistTrackMenu {
                background: transparent; border: 1px solid transparent;
                border-radius: 4px; padding: 0; margin: 0;
                min-width: 22px; max-width: 22px;
                min-height: 22px; max-height: 22px;
            }
            #playlistDetail #playlistTrackMenu { font-size: 7px; }
            #playlistDetail #playlistTrackPlay:hover,
            #playlistDetail #playlistTrackMenu:hover {
                background: #26313D; border-color: #3A4755;
            }
            #playlistDetail #playlistTrackPlay:focus,
            #playlistDetail #playlistTrackMenu:focus {
                background: #26313D; border-color: #FF7187;
            }
            #playlistDetail #playlistTrackMenu::menu-indicator {
                image: none; width: 0; height: 0;
            }
            #playlistObservedPlayer {
                background: #10161D; border: 1px solid #27313C; border-radius: 10px;
            }
            #playlistPlayerTitle { color: #F5F7FA; font-size: 12px; font-weight: 650; }
            #playlistPlayerChannel, #playlistPlayerTime, #playlistPlayerState {
                color: #909AA7; font-size: 11px;
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
                background: #202A35; border-color: #3A4755;
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
            #playlistObservedProgress { background: #27313C; border: 0; border-radius: 2px;
                min-height: 3px; max-height: 3px; }
            #playlistObservedProgress::chunk { background: #FF536D; border-radius: 2px; }
            #playlistDestinationFlow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #141C25, stop:1 #10161D);
                border: 1px solid #2A3642; border-radius: 14px;
            }
            #playlistDestinationEyebrow {
                color: #FF536D; font-size: 10px; font-weight: 750;
                letter-spacing: 1.4px;
            }
            #playlistDestinationTitle {
                color: #F7F9FB; font-size: 18px; font-weight: 750;
            }
            #playlistDestinationSubtitle, #playlistDestinationTrackMeta,
            #playlistDestinationWarning { color: #909AA7; font-size: 11px; }
            #playlistDestinationTrack {
                background: #0E141B; border: 1px solid #25303B;
                border-radius: 9px;
            }
            #playlistDestinationTrackTitle {
                color: #F5F7FA; font-size: 12px; font-weight: 650;
            }
            #playlistDestinationSearch {
                background: #0E141B; color: #F5F7FA;
                border: 1px solid #2A3642; border-radius: 8px;
                padding: 7px 11px; min-height: 22px;
                selection-background-color: #A9354B;
            }
            #playlistDestinationSearch:focus { border-color: #FF536D; }
            #playlistDestinationList {
                background: #0B1016; color: #EFF3F7;
                border: 1px solid #25303B; border-radius: 10px;
                outline: 0; padding: 6px;
            }
            #playlistDestinationList::item {
                border: 1px solid transparent; border-radius: 7px;
                padding: 7px 10px; margin: 2px 1px;
            }
            #playlistDestinationList::item:hover {
                background: #18222D; border-color: #30404F;
            }
            #playlistDestinationList::indicator {
                width: 18px; height: 18px;
            }
            #playlistDestinationList::indicator:unchecked {
                background: #111820; border: 1px solid #44515F;
                border-radius: 5px;
            }
            #playlistDestinationList::indicator:checked {
                background: #FF536D; border: 1px solid #FF7187;
                border-radius: 5px;
            }
            #playlistDestinationList QScrollBar:vertical {
                background: transparent; width: 9px; margin: 5px 2px 5px 0;
            }
            #playlistDestinationList QScrollBar::handle:vertical {
                background: #35414D; min-height: 36px; border-radius: 4px;
            }
            #playlistDestinationList QScrollBar::handle:vertical:hover {
                background: #4A5866;
            }
            #playlistDestinationList QScrollBar::add-line:vertical,
            #playlistDestinationList QScrollBar::sub-line:vertical {
                height: 0; background: transparent;
            }
            #playlistDestinationList QScrollBar::add-page:vertical,
            #playlistDestinationList QScrollBar::sub-page:vertical {
                background: transparent;
            }
            #playlistDestinationCount {
                color: #F5F7FA; font-size: 12px; font-weight: 700;
            }
            #playlistDetail #playlistDestinationConfirm {
                background: #FF536D; color: #10151B;
                border-color: #FF7187; font-weight: 750;
                min-width: 170px; min-height: 28px;
            }
            #playlistDetail #playlistDestinationConfirm:disabled {
                background: #222B35; color: #6F7A86; border-color: #303A45;
            }
            #playlistDetail #playlistDestinationUtility,
            #playlistDetail #playlistDestinationCancel {
                background: transparent;
            }
            #playlistDetail #playlistDestinationClose {
                background: transparent; border-color: transparent;
                color: #A9B2BC; font-size: 19px; padding: 0;
            }
        """)
        self._garantir_fonte_legivel()
        # Começa comprimível antes do primeiro show; o resize real refina o modo.
        self.definir_compacto(True)

    def _garantir_fonte_legivel(self) -> None:
        """Preserva a fonte do app quando completa e usa fallback latino seguro."""
        fonte_atual = self.font()
        metricas = QFontMetrics(fonte_atual)
        amostra = "Laylay — ação, música, duração 0123456789"
        if all(metricas.inFontUcs4(ord(caractere)) for caractere in amostra):
            return
        familias = {
            familia.casefold(): familia for familia in QFontDatabase.families()
        }
        for candidata in ("Segoe UI", "Arial", "Noto Sans", "DejaVu Sans"):
            familia = familias.get(candidata.casefold())
            if not familia:
                continue
            fonte_segura = self.font()
            fonte_segura.setFamily(familia)
            self.setFont(fonte_segura)
            return

    def abrir(self, nome: str) -> None:
        self._fechar_seletor_destinos()
        self._encerrar_animacao_entrada()
        self._nome = str(nome or "").strip()
        self._entrada_pendente = True
        self._entrada_aguardando_show = False
        self.titulo.setText(self._nome or "Playlist")
        self.busca.clear()
        self._itens.clear()
        self.tabela.setRowCount(0)
        self.solicitar_detalhe(reiniciar=True)

    def definir_catalogo(self, catalogo: list[object]) -> None:
        unicos: dict[str, dict] = {}
        for bruto in catalogo[:1_000]:
            item = dict(bruto) if isinstance(bruto, dict) else {"name": bruto}
            nome = str(item.get("name") or "").strip()
            if nome and nome.casefold() not in unicos:
                unicos[nome.casefold()] = {**item, "name": nome}
        self._catalogo = list(unicos.values())

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
            "copy_track_many", "move_track_many",
            "remove_track", "set_artwork", "restore_artwork",
        }:
            self._operacao_pendente = operacao
            mensagens = {
                "add_url": "Confirmando vídeo e adicionando…",
                "play_track": "Abrindo a faixa selecionada…",
                "copy_track": "Copiando a faixa…",
                "move_track": "Movendo a faixa…",
                "copy_track_many": "Adicionando a faixa às playlists…",
                "move_track_many": "Movendo a faixa com segurança…",
                "remove_track": "Removendo a faixa…",
                "set_artwork": "Validando e salvando a nova capa…",
                "restore_artwork": "Restaurando a capa automática…",
            }
            self.estado.setText(mensagens[operacao])
            self.estado.show()
            self._definir_acoes_habilitadas(False)
        self.requisicao_solicitada.emit(payload)

    def _definir_acoes_habilitadas(self, habilitadas: bool) -> None:
        for botao in (*self._botoes_acoes, self.mais_acoes, self.mais):
            botao.setEnabled(habilitadas)
        for acao in self.menu_acoes.actions():
            acao.setEnabled(habilitadas)
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
        if operacao in {"copy_track", "move_track"}:
            self._abrir_seletor_destinos(operacao, item)
            return
        if operacao == "remove_track":
            if QMessageBox.question(
                self, "Confirmar alteração",
                f"Deseja remover “{item.get('title') or 'faixa'}” desta playlist?",
            ) != QMessageBox.Yes:
                return
        self._requisitar(operacao, **dados)

    def _widgets_conteudo_principal(self) -> tuple[QWidget, ...]:
        return (
            self.hero, self.busca, self.cabecalho_faixas, self.estado,
            self.tabela, self.mais, self.player,
        )

    def _voltar_contextual(self) -> None:
        if self.seletor_destinos.isVisible():
            self._fechar_seletor_destinos()
        else:
            self.voltar_solicitado.emit()

    def _abrir_seletor_destinos(self, operacao: str, item: dict) -> None:
        destinos = [
            catalogo for catalogo in self._catalogo
            if str(catalogo.get("name") or "").casefold()
            != self._nome.casefold()
        ]
        if not destinos:
            self.estado.setText(
                "Crie outra playlist para organizar esta faixa."
            )
            self.estado.show()
            return
        self._ocultacao_antes_destinos = [
            (widget, widget.isHidden())
            for widget in self._widgets_conteudo_principal()
        ]
        for widget, _oculto in self._ocultacao_antes_destinos:
            widget.hide()
        self.seletor_destinos.abrir(
            operacao, item, self._nome, destinos,
        )
        self.voltar.setText("Voltar à playlist")

    def _fechar_seletor_destinos(self) -> None:
        if hasattr(self, "seletor_destinos"):
            self.seletor_destinos.hide()
        for widget, oculto in self._ocultacao_antes_destinos:
            widget.setHidden(oculto)
        self._ocultacao_antes_destinos.clear()
        if hasattr(self, "voltar"):
            self.voltar.setText("Voltar")

    def _confirmar_destinos(
        self, operacao: str, item: dict, destinos: list[str],
    ) -> None:
        if not destinos:
            return
        self._fechar_seletor_destinos()
        self._requisitar(
            "move_track_many" if operacao == "move_track"
            else "copy_track_many",
            video_id=item.get("video_id", ""),
            destinations=destinos,
        )

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
                "copied_many": "Faixa adicionada às playlists selecionadas.",
                "already_present_all": "A faixa já estava em todas as playlists selecionadas.",
                "moved_many": "Faixa distribuída e removida da playlist de origem.",
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
                (
                    f"Faixa adicionada a {int(resultado.get('destination_count') or 0)} playlists."
                    if status == "copied_many"
                    else f"Faixa movida para {int(resultado.get('destination_count') or 0)} playlists."
                    if status == "moved_many"
                    else mensagens_ok.get(status, "Alteração confirmada.")
                )
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
        # Uma resposta nova pode substituir linhas enquanto a entrada anterior
        # ainda termina; solte efeitos antes que os cell widgets sejam trocados.
        self._encerrar_animacao_entrada()
        self.tabela.setRowCount(len(self._itens))
        self._linhas_widgets.clear()
        self._linha_selecionada = -1
        for linha, item in enumerate(self._itens):
            faixa = FaixaPlaylistRow(
                linha, item, reduzir_movimento=self._reduzir_movimento,
            )
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
            self.tabela.setRowHeight(linha, self._altura_linha())
        self._atualizar_faixa_tocando()
        self.mais.setVisible(bool(resultado.get("has_more")))
        QTimer.singleShot(0, self._sincronizar_largura_das_linhas)
        if int(resultado.get("offset") or 0) == 0 and self._entrada_pendente:
            if self.isVisible():
                QTimer.singleShot(0, self._iniciar_entrada_playlist)
            else:
                self._entrada_aguardando_show = True

    def _selecionar_linha(self, indice: int) -> None:
        self._linha_selecionada = indice
        for linha, widget in enumerate(self._linhas_widgets):
            widget.definir_selecionada(linha == indice)

    def _sincronizar_largura_das_linhas(self) -> None:
        largura = self.tabela.viewport().width()
        for faixa in self._linhas_widgets:
            faixa.definir_largura_disponivel(largura)
        self.cabecalho_faixas.setVisible(
            largura >= 720 and not self._compacto and not self._altura_baixa
        )

    def _altura_linha(self) -> int:
        return 44 if self._compacto or self._altura_baixa else 52

    def _atualizar_altura_linhas(self) -> None:
        altura = self._altura_linha()
        for linha in range(self.tabela.rowCount()):
            self.tabela.setRowHeight(linha, altura)

    def _atualizar_faixa_tocando(self, *, pulsar: bool = False) -> None:
        indices = {
            indice for indice, faixa in enumerate(self._linhas_widgets)
            if self._video_id_tocando
            and str(faixa.item.get("video_id") or "").strip()
            == self._video_id_tocando
        }
        if not indices and self._titulo_tocando:
            candidatos = {
                indice for indice, faixa in enumerate(self._linhas_widgets)
                if _titulo_comparavel(faixa.item.get("title"))
                == self._titulo_tocando
            }
            # O fallback textual só é aceito quando identifica uma única linha.
            indices = candidatos if len(candidatos) == 1 else set()
        for indice, faixa in enumerate(self._linhas_widgets):
            faixa.definir_tocando(indice in indices, pulsar=pulsar)

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
            tamanho_capa = 48 if amplo else 38
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
            self.player.setFixedHeight(78 if not self._altura_baixa else 72)
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
        tocando = observado and estado == "playing"
        video_id = str(musica.get("video_id") or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            capa = str(musica.get("artwork_url") or "")
            encontrado = re.search(r"/vi/([A-Za-z0-9_-]{11})/", capa)
            video_id = encontrado.group(1) if encontrado else ""
        titulo = str(musica.get("title") or "Faixa observada")
        canal = str(musica.get("channel") or "Canal não informado")
        identidade = (
            f"video:{video_id}" if video_id
            else f"titulo:{_titulo_comparavel(titulo)}|{_titulo_comparavel(canal)}"
        ) if observado else ""
        identidade_mudou = bool(
            observado and identidade and identidade != self._identidade_player
        )
        if observado and identidade:
            self._identidade_player = identidade
        self._video_id_tocando = video_id if tocando else ""
        self._titulo_tocando = (
            _titulo_comparavel(musica.get("title")) if tocando else ""
        )
        self._atualizar_faixa_tocando(pulsar=identidade_mudou and tocando)
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
            identidade_visual = (
                titulo, canal, str(musica.get("artwork_url") or ""),
            )
            if identidade_mudou:
                self._trocar_identidade_player(identidade_visual)
            elif self._animacao_identidade_player is None:
                self._aplicar_identidade_player(identidade_visual)
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

    def aplicar_medidor_musica(self, medidor: dict) -> bool:
        video_id = str(medidor.get("video_id") or "").strip()
        if not video_id or video_id != self._video_id_tocando:
            return False
        for linha in self._linhas_widgets:
            if (
                linha._tocando
                and str(linha.item.get("video_id") or "").strip() == video_id
            ):
                return linha.indicador_tocando.aplicar_niveis(
                    medidor.get("levels"),
                )
        return False

    def _aplicar_identidade_player(
        self, identidade_visual: tuple[str, str, str],
    ) -> None:
        titulo, canal, capa = identidade_visual
        self.player_capa.definir_titulo(titulo)
        self.player_capa.carregar(capa)
        self.player_titulo.definir_texto(titulo)
        self.player_titulo.setAccessibleName(f"Faixa atual: {titulo}")
        self.player_canal.definir_texto(canal)
        self.player_canal.setAccessibleName(f"Canal atual: {canal}")

    def _encerrar_crossfade_player(self) -> None:
        animacao = self._animacao_identidade_player
        if animacao is not None:
            animacao.stop()
            animacao.deleteLater()
            self._animacao_identidade_player = None
        efeito = self._efeito_identidade_player
        if efeito is not None and self.player_identidade.graphicsEffect() is efeito:
            self.player_identidade.setGraphicsEffect(None)
        self._efeito_identidade_player = None

    def _trocar_identidade_player(
        self, identidade_visual: tuple[str, str, str],
    ) -> None:
        self._encerrar_crossfade_player()
        if self._reduzir_movimento or not self.isVisible():
            self._aplicar_identidade_player(identidade_visual)
            return
        efeito = QGraphicsOpacityEffect(self.player_identidade)
        efeito.setOpacity(1.0)
        self.player_identidade.setGraphicsEffect(efeito)
        grupo = QSequentialAnimationGroup(self)
        saida = QPropertyAnimation(efeito, b"opacity", grupo)
        saida.setDuration(75)
        saida.setStartValue(1.0)
        saida.setEndValue(0.18)
        saida.setEasingCurve(QEasingCurve.OutCubic)
        entrada = QPropertyAnimation(efeito, b"opacity", grupo)
        entrada.setDuration(115)
        entrada.setStartValue(0.18)
        entrada.setEndValue(1.0)
        entrada.setEasingCurve(QEasingCurve.OutCubic)
        saida.finished.connect(
            lambda: self._aplicar_identidade_player(identidade_visual),
        )
        grupo.addAnimation(saida)
        grupo.addAnimation(entrada)
        self._efeito_identidade_player = efeito
        self._animacao_identidade_player = grupo

        def finalizar() -> None:
            if self._animacao_identidade_player is grupo:
                self._animacao_identidade_player = None
            if self.player_identidade.graphicsEffect() is efeito:
                self.player_identidade.setGraphicsEffect(None)
            if self._efeito_identidade_player is efeito:
                self._efeito_identidade_player = None
            grupo.deleteLater()

        grupo.finished.connect(finalizar)
        grupo.start()

    def _encerrar_animacao_entrada(self) -> None:
        grupo = self._animacao_entrada
        if grupo is not None:
            grupo.stop()
            grupo.deleteLater()
            self._animacao_entrada = None
        for widget, efeito in self._efeitos_entrada:
            try:
                if widget.graphicsEffect() is efeito:
                    widget.setGraphicsEffect(None)
            except RuntimeError:
                pass
        self._efeitos_entrada.clear()

    def _iniciar_entrada_playlist(self) -> None:
        if not self._entrada_pendente or not self.isVisible():
            return
        self._entrada_pendente = False
        self._entrada_aguardando_show = False
        self._encerrar_animacao_entrada()
        if self._reduzir_movimento:
            return
        grupo = QParallelAnimationGroup(self)
        alvos = [self.hero, *self._linhas_widgets[:10]]
        for indice, widget in enumerate(alvos):
            efeito = QGraphicsOpacityEffect(widget)
            efeito.setOpacity(0.0 if indice == 0 else 0.16)
            widget.setGraphicsEffect(efeito)
            self._efeitos_entrada.append((widget, efeito))
            etapa = QSequentialAnimationGroup(grupo)
            if indice:
                etapa.addPause(min(indice - 1, 9) * 25)
            opacidade = QPropertyAnimation(efeito, b"opacity", etapa)
            opacidade.setDuration(210 if indice == 0 else 165)
            opacidade.setStartValue(0.0 if indice == 0 else 0.16)
            opacidade.setEndValue(1.0)
            opacidade.setEasingCurve(QEasingCurve.OutCubic)
            etapa.addAnimation(opacidade)
            grupo.addAnimation(etapa)
        self._animacao_entrada = grupo

        def finalizar() -> None:
            if self._animacao_entrada is not grupo:
                return
            self._animacao_entrada = None
            for widget, efeito in self._efeitos_entrada:
                try:
                    if widget.graphicsEffect() is efeito:
                        widget.setGraphicsEffect(None)
                except RuntimeError:
                    pass
            self._efeitos_entrada.clear()
            grupo.deleteLater()

        grupo.finished.connect(finalizar)
        grupo.start()

    def definir_compacto(self, compacto: bool) -> None:
        self._compacto = bool(compacto)
        self._altura_baixa = bool(0 < self.height() < 560)
        enxuto = self._compacto or self._altura_baixa
        margem_x = 8 if enxuto else 16
        margem_y = 6 if self._altura_baixa else (9 if self._compacto else 14)
        self.raiz.setContentsMargins(margem_x, margem_y, margem_x, margem_y)
        self.raiz.setSpacing(5 if self._altura_baixa else (8 if compacto else 10))
        tamanho_capa = 64 if self._altura_baixa else (96 if compacto else 132)
        self.capa.setFixedSize(tamanho_capa, tamanho_capa)
        margem_hero = 8 if self._altura_baixa else (12 if compacto else 14)
        self.hero_layout.setContentsMargins(
            margem_hero, margem_hero, margem_hero, margem_hero,
        )
        self.hero_layout.setSpacing(12 if enxuto else 18)
        self.hero.setFixedHeight(
            80 if self._altura_baixa else (124 if compacto else 160)
        )
        self.rotulo.setVisible(not self._altura_baixa)
        self.meta.setVisible(not self._altura_baixa)
        self.busca.setFixedHeight(34 if self._altura_baixa else 38)
        self.identidade_layout.setSpacing(2 if self._altura_baixa else 4)
        fonte_titulo = self.titulo.font()
        fonte_titulo.setPixelSize(
            20 if self._altura_baixa else (22 if self._compacto else 28)
        )
        self.titulo.setFont(fonte_titulo)
        for botao in (self.play, self.shuffle, self.mais_acoes):
            self.acoes_layout.removeWidget(botao)
        for coluna, botao in enumerate((self.play, self.shuffle, self.mais_acoes)):
            botao.setFixedHeight(30 if self._altura_baixa else 34)
            self.acoes_layout.addWidget(botao, 0, coluna)
        for coluna in range(4):
            self.acoes_layout.setColumnStretch(coluna, 0)
        self.acoes_layout.setColumnStretch(3, 1)
        self.acoes_layout.setContentsMargins(
            0, 2 if self._altura_baixa else 6, 0, 0,
        )
        self._organizar_player_responsivo(self.width())
        for faixa in self._linhas_widgets:
            faixa.definir_compacta(enxuto)
        self._atualizar_altura_linhas()
        self._sincronizar_largura_das_linhas()

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
        if self._entrada_aguardando_show:
            QTimer.singleShot(0, self._iniciar_entrada_playlist)
