"""Página Música M1 do Terminal 3.

A M1 define a composição visual definitiva, mas mantém uma fronteira simples:
somente o player observado e seus três controles atuais ficam ativos. Os demais
módulos exibem honestamente que ainda aguardam seus contratos de integração.
"""

from __future__ import annotations

from bisect import bisect_right
import html
import math
import os
import time

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSizePolicy,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from cliente.terminal_2.acabamento import CapaMusicaGenerica, icone_terminal


def _tempo(segundos: object) -> str:
    try:
        total = max(0, int(float(segundos)))
    except (TypeError, ValueError):
        total = 0
    minutos, segundo = divmod(total, 60)
    horas, minutos = divmod(minutos, 60)
    return f"{horas}:{minutos:02d}:{segundo:02d}" if horas else f"{minutos}:{segundo:02d}"


class OndaMusical(QWidget):
    """Movimento decorativo ligado apenas ao estado observado de reprodução."""

    def __init__(self, *, reduzir_movimento: bool = False) -> None:
        super().__init__()
        self.setObjectName("musicWaveform")
        self.setMinimumHeight(58)
        self.setMaximumHeight(72)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._tocando = False
        self._reduzir_movimento = bool(reduzir_movimento)
        self._fase = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(90)
        self._timer.timeout.connect(self._avancar)
        self._timer.start()
        self.setAccessibleName("Visual decorativo da reprodução musical")

    def definir_tocando(self, tocando: bool) -> None:
        self._tocando = bool(tocando)
        self.update()

    def _avancar(self) -> None:
        if self._tocando and not self._reduzir_movimento:
            self._fase = (self._fase + 0.22) % (math.pi * 2)
            self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        centro = self.height() / 2
        quantidade = max(30, min(70, self.width() // 7))
        passo = self.width() / max(1, quantidade)
        painter.setPen(QPen(QColor("#FF536D" if self._tocando else "#63313B"), 2))
        for indice in range(quantidade):
            onda = abs(math.sin(indice * 0.51 + self._fase))
            envelope = 0.35 + 0.65 * abs(math.sin(indice * 0.13 + 1.2))
            altura = 3.0 + onda * envelope * (centro - 7)
            x = indice * passo + passo / 2
            painter.drawLine(int(x), int(centro - altura), int(x), int(centro + altura))


class MiniEqualizadorFila(QWidget):
    """Cinco barras animadas usadas no destaque da primeira faixa da fila."""

    def __init__(self, *, reduzir_movimento: bool = False) -> None:
        super().__init__()

        self.setFixedSize(18, 20)
        self._reduzir_movimento = bool(reduzir_movimento)
        self._fase = 0.0
        self._ativo = False

        self._timer = QTimer(self)
        self._timer.setInterval(85)
        self._timer.timeout.connect(self._avancar)

    def definir_ativo(self, ativo: bool) -> None:
        self._ativo = bool(ativo)

        if self._ativo and not self._reduzir_movimento:
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()

        self.update()

    def _avancar(self) -> None:
        self._fase = (self._fase + 0.32) % (math.pi * 2)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(
            QPen(
                QColor("#FF5C73"),
                2,
                Qt.SolidLine,
                Qt.RoundCap,
            )
        )

        centro = self.height() / 2
        alturas = []

        for indice in range(5):
            if self._reduzir_movimento:
                altura = (4, 9, 6, 11, 7)[indice]
            else:
                onda = math.sin(
                    self._fase
                    + indice * 1.15
                )

                altura = 4 + abs(onda) * 10

            alturas.append(altura)

        espacamento = 3.2
        inicio = 2.5

        for indice, altura in enumerate(alturas):
            x = inicio + indice * espacamento

            painter.drawLine(
                int(x),
                int(centro - altura / 2),
                int(x),
                int(centro + altura / 2),
            )

class CartaoPlaylist(QPushButton):
    """Preset compacto de playlist para a sessão musical."""

    def __init__(self, indice: int) -> None:
        super().__init__()

        tom = str(indice % 6)

        self.setObjectName("musicPreset")
        self.setProperty("presetTone", tom)

        self.setFixedHeight(52)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(7, 6, 10, 6)
        layout.setSpacing(9)

        # Quadradinho colorido
        self.icone_caixa = QFrame()
        self.icone_caixa.setObjectName("musicPresetIconBox")
        self.icone_caixa.setProperty("presetTone", tom)
        self.icone_caixa.setFixedSize(36, 36)
        self.icone_caixa.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True,
        )

        icone_layout = QHBoxLayout(self.icone_caixa)
        icone_layout.setContentsMargins(0, 0, 0, 0)

        self.icone = QLabel("♫")
        self.icone.setObjectName("musicPresetIcon")
        self.icone.setAlignment(Qt.AlignCenter)
        self.icone.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True,
        )

        icone_layout.addWidget(self.icone)

        # Nome + quantidade
        textos = QVBoxLayout()
        textos.setContentsMargins(0, 0, 0, 0)
        textos.setSpacing(1)

        self.titulo = QLabel("Playlist")
        self.titulo.setObjectName("musicPresetTitle")
        self.titulo.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True,
        )

        self.quantidade = QLabel("0 faixas")
        self.quantidade.setObjectName("musicPresetCount")
        self.quantidade.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True,
        )

        textos.addWidget(self.titulo)
        textos.addWidget(self.quantidade)

        layout.addWidget(self.icone_caixa)
        layout.addLayout(textos, 1)

    def definir(
        self,
        nome: str,
        quantidade: int,
        *,
        ativo: bool = False,
    ) -> None:
        self.titulo.setText(nome)

        self.quantidade.setText(
            f"{quantidade} faixa"
            if quantidade == 1
            else f"{quantidade} faixas"
        )

        self.setProperty("activePlaylist", ativo)
        self.titulo.setProperty("activePlaylist", ativo)

        for widget in (self, self.titulo):
            widget.style().unpolish(widget)
            widget.style().polish(widget)


class CartaoMusica(QFrame):
    def __init__(self, titulo: str, *, detalhe: str = "") -> None:
        super().__init__()
        self.setObjectName("musicModule")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.conteudo = QVBoxLayout(self)
        self.conteudo.setContentsMargins(
            13, 12, 13, 12
        )
        self.conteudo.setSpacing(8)
        topo = QHBoxLayout()
        nome = QLabel(titulo)
        nome.setObjectName("musicModuleTitle")
        topo.addWidget(nome)
        topo.addStretch()
        if detalhe:
            hint = QLabel(detalhe)
            hint.setObjectName("musicModuleHint")
            topo.addWidget(hint)
        self.conteudo.addLayout(topo)


class VisualizadorLetra(QTextBrowser):
    """Leitor rolável que mantém compatibilidade com o antigo QLabel."""

    def __init__(self) -> None:
        super().__init__()

        self._conteudo_html = ""
        self._permitir_scroll_interno = False

        self.setObjectName("musicLyricsText")
        self.setReadOnly(True)
        self.setOpenExternalLinks(False)
        self.setOpenLinks(False)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.document().setDocumentMargin(0)
        self.verticalScrollBar().valueChanged.connect(
        self._travar_scroll_compacto
        )
    def _travar_scroll_compacto(self, valor: int) -> None:
        if not self._permitir_scroll_interno and valor != 0:
            self.verticalScrollBar().setValue(0)

    def definir_scroll_interno(self, permitir: bool) -> None:
        self._permitir_scroll_interno = bool(permitir)

        # No modo karaokê compacto, o QTextBrowser não recebe eventos
        # do mouse. A rodinha passa direto para a página principal.
        self.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            not permitir,
        )

        if not permitir:
            self.verticalScrollBar().setValue(0)

    def wheelEvent(self, event) -> None:  # noqa: N802
        if not self._permitir_scroll_interno:
            # Não deixa o QTextBrowser mover a letra dentro da caixa.
            # O evento continua para o scroll principal da página.
            event.ignore()
            return

        super().wheelEvent(event)

    def setText(self, texto: str) -> None:  # noqa: N802
        self._conteudo_html = str(texto or "")
        self.setHtml(self._conteudo_html)

    def text(self) -> str:
        return self._conteudo_html

    def clear(self) -> None:
        self._conteudo_html = ""
        super().clear()


def _estado_futuro(texto: str) -> QLabel:
    rotulo = QLabel(texto)
    rotulo.setObjectName("musicFutureState")
    rotulo.setWordWrap(True)
    rotulo.setMinimumWidth(0)
    rotulo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
    return rotulo


def _metrica_dashboard(metrica: object, *, uptime: bool = False) -> str:
    if not isinstance(metrica, dict) or metrica.get("value") is None:
        return "—"
    try:
        valor = float(metrica["value"])
    except (TypeError, ValueError):
        return "—"
    if uptime:
        total = max(0, int(valor))
        dias, resto = divmod(total, 86_400)
        horas, resto = divmod(resto, 3_600)
        minutos = resto // 60
        return f"{dias}d {horas}h" if dias else f"{horas}h {minutos}m"
    unidade = str(metrica.get("unit") or "")
    numero = str(int(valor)) if valor.is_integer() else f"{valor:.1f}".replace(".", ",")
    return f"{numero}{unidade}"


class PaginaMusicaM1(QWidget):
    """Sessão musical visualmente completa, baseada somente em dados reais."""

    acao_solicitada = Signal(str, str)
    acao_fila_solicitada = Signal(str, str, dict)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("musicPage")
        self._conectada = False
        self._controles_disponiveis = False
        self._estado_observado = "unavailable"
        self._posicao_base = 0.0
        self._duracao_base = 0.0
        self._observado_em = 0.0
        self._artwork_url = ""
        self._modo_compacto = False
        self._fila_fonte = ""
        self._fila_frescor = "unavailable"
        self._fila_pendente = False
        self._catalogo_expandido = False
        self._catalogo: list[dict] = []
        self._catalogo_pode_tocar = False
        self._playlist_ativa = ""
        self._playlist_pendente = False
        self._repeat_disponivel = False
        self._repeat_ativo = False
        self._shuffle_disponivel = False
        self._volume_disponivel = False
        self._volume_arrastando = False
        self._ultimo_retrato_musica: dict = {}
        self._letra_retrato: dict = {}
        self._letra_expandida = False
        self._linha_letra_atual = -2
        self._reduzir_movimento = os.environ.get(
            "LAYLAY_REDUZIR_MOVIMENTO", "0",
        ).strip().casefold() in {"1", "true", "sim", "yes"}
        self._animacao_letra: QPropertyAnimation | None = None
        self._animacao_rolagem_letra: QPropertyAnimation | None = None
        self._versao_render_letra = 0

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        self.rolagem = QScrollArea()
        self.rolagem.setObjectName("musicScroll")
        self.rolagem.setWidgetResizable(True)
        self.rolagem.setFrameShape(QFrame.NoFrame)
        self.rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.corpo = QWidget()
        self.corpo.setObjectName("musicPageBody")
        self.grade = QGridLayout(self.corpo)
        self.grade.setSizeConstraint(QLayout.SetNoConstraint)
        self.grade.setContentsMargins(28, 24, 28, 32)
        self.grade.setHorizontalSpacing(14)
        self.grade.setVerticalSpacing(14)
        self.rolagem.setWidget(self.corpo)
        raiz.addWidget(self.rolagem)

        self._construir_cabecalho()
        self._construir_player()
        self._construir_fila()
        self._construir_acoes()
        self._construir_modulos()
        self._construir_barra_lateral()
        self._organizar(False)

        self._relogio = QTimer(self)
        self._relogio.setInterval(1000)
        self._relogio.timeout.connect(self._atualizar_relogio)
        self._relogio.start()

    def _construir_cabecalho(self) -> None:
        self.cabecalho = QWidget()
        layout = QHBoxLayout(self.cabecalho)
        layout.setContentsMargins(4, 0, 4, 4)
        textos = QVBoxLayout()
        titulo = QLabel("Sessão de música  ✦")
        titulo.setObjectName("musicPageTitle")
        descricao = QLabel("Sua trilha sonora, do seu jeito.")
        descricao.setObjectName("musicPageDescription")
        textos.addWidget(titulo)
        textos.addWidget(descricao)
        layout.addLayout(textos)
        layout.addStretch()
        self.tela_cheia = QPushButton("Tela cheia")
        self.tela_cheia.setObjectName("musicHeaderButton")
        self.tela_cheia.setIcon(icone_terminal("maximize"))
        self.tela_cheia.clicked.connect(self._alternar_tela_cheia)
        mais = QToolButton()
        mais.setObjectName("musicMoreButton")
        mais.setText("•••")
        mais.setEnabled(False)
        mais.setToolTip("Mais opções aguardam integração")
        layout.addWidget(self.tela_cheia)
        layout.addWidget(mais)

    def _construir_player(self) -> None:
        self.player = QFrame()
        self.player.setObjectName("musicHero")
        self.player.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        layout = QHBoxLayout(self.player)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(24)
        self.capa = CapaMusicaGenerica(230)
        layout.addWidget(self.capa, 0, Qt.AlignTop)

        informacoes = QVBoxLayout()
        informacoes.setSpacing(7)
        linha_status = QHBoxLayout()
        self.selo = QLabel("PLAYER NÃO OBSERVADO")
        self.selo.setObjectName("musicNowBadge")
        self.volume = QLabel("VOLUME\n—")
        self.volume.setObjectName("musicVolumeReadout")
        self.volume.setAlignment(Qt.AlignRight | Qt.AlignTop)
        linha_status.addWidget(self.selo)
        linha_status.addStretch()
        linha_status.addWidget(self.volume)
        informacoes.addLayout(linha_status)
        self.titulo = QLabel("Nenhuma faixa confirmada")
        self.titulo.setObjectName("musicHeroTitle")
        self.titulo.setWordWrap(True)
        self.titulo.setMinimumWidth(0)
        self.titulo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.canal = QLabel("Aguardando o player observado pela extensão")
        self.canal.setObjectName("musicHeroSubtitle")
        self.canal.setMinimumWidth(0)
        self.canal.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        informacoes.addWidget(self.titulo)
        informacoes.addWidget(self.canal)
        self.onda = OndaMusical(reduzir_movimento=self._reduzir_movimento)
        informacoes.addWidget(self.onda)
        self.progresso = QProgressBar()
        self.progresso.setObjectName("musicHeroProgress")
        self.progresso.setRange(0, 1000)
        self.progresso.setValue(0)
        self.progresso.setTextVisible(False)
        informacoes.addWidget(self.progresso)
        tempos = QHBoxLayout()
        self.tempo_atual = QLabel("0:00")
        self.tempo_total = QLabel("0:00")
        self.tempo = QLabel("0:00 / 0:00")
        self.tempo.hide()  # compatibilidade de testes; tempos visuais ficam separados.
        for item in (self.tempo_atual, self.tempo_total):
            item.setObjectName("musicTime")
        tempos.addWidget(self.tempo_atual)
        tempos.addStretch()
        tempos.addWidget(self.tempo_total)
        informacoes.addLayout(tempos)

        controles = QHBoxLayout()
        controles.setSpacing(11)
        controles.addStretch()
        self.botoes: dict[str, QPushButton] = {}
        for acao_id, icone, dica in (
            ("playlist_shuffle", "", "Tocar a playlist atual em ordem aleatória"),
            ("media_previous", "previous", "Faixa anterior"),
            ("media_toggle", "play", "Pausar ou continuar"),
            ("media_next", "next", "Próxima faixa"),
            ("media_repeat", "", "Ativar ou desativar a repetição da faixa"),
        ):
            botao = QPushButton()
            botao.setObjectName(
                "musicPrimaryControl" if acao_id == "media_toggle"
                else "musicTransportControl"
            )
            if icone:
                botao.setIcon(icone_terminal(icone))
            else:
                botao.setText("⇄" if acao_id == "playlist_shuffle" else "↻")
            botao.setIconSize(QSize(28, 28))
            botao.setToolTip(dica)
            botao.setAccessibleName(dica)
            botao.setEnabled(False)
            botao.clicked.connect(lambda _v=False, aid=acao_id: self._solicitar(aid))
            self.botoes[acao_id] = botao
            controles.addWidget(botao)
        controles.addStretch()
        informacoes.addLayout(controles)
        self.estado = QLabel("Indisponível")
        self.estado.setObjectName("musicObservedState")
        self.estado.setAlignment(Qt.AlignCenter)
        informacoes.addWidget(self.estado)
        layout.addLayout(informacoes, 1)

        volume_lateral = QVBoxLayout()
        volume_lateral.setSpacing(7)
        self.volume_slider = QSlider(Qt.Vertical)
        self.volume_slider.setObjectName("musicVolumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(0)
        self.volume_slider.setEnabled(False)
        self.volume_slider.setAccessibleName("Volume mestre do sistema")
        self.volume_slider.setToolTip(
            "Volume mestre observado; a mudança só é confirmada pela mente da Laylay"
        )
        self.volume_slider.sliderPressed.connect(
            lambda: setattr(self, "_volume_arrastando", True),
        )
        self.volume_slider.sliderReleased.connect(self._solicitar_volume)
        volume_lateral.addWidget(self.volume_slider, 1, Qt.AlignHCenter)
        self.volume_muted = QLabel("")
        self.volume_muted.setObjectName("musicModuleHint")
        self.volume_muted.setAlignment(Qt.AlignCenter)
        volume_lateral.addWidget(self.volume_muted)
        layout.addLayout(volume_lateral)

    def _construir_fila(self) -> None:
        self.fila = CartaoMusica("Próximas faixas", detalhe="observada")
        self.fila.setObjectName("musicQueue")
        self.fila.setMinimumWidth(315)
        self.fila.setMaximumWidth(390)
        self.fila.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.fila_estado = _estado_futuro(
            "Aguardando a fila observada do YouTube."
        )
        self.fila.conteudo.addWidget(self.fila_estado)

        # Área rolável da fila
        self.fila_scroll = QScrollArea()
        self.fila_scroll.setObjectName("musicQueueScroll")
        self.fila_scroll.setWidgetResizable(True)
        self.fila_scroll.setFrameShape(QFrame.NoFrame)
        self.fila_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.fila_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 5 músicas de 58px + espaços entre elas
        self.fila_scroll.setFixedHeight(322)
        self.fila_lista = QWidget()
        self.fila_lista.setObjectName("musicQueueList")

        self.fila_lista_layout = QVBoxLayout(self.fila_lista)
        self.fila_lista_layout.setContentsMargins(0, 2, 0, 2)
        self.fila_lista_layout.setSpacing(2)
        self.fila_lista_layout.setAlignment(Qt.AlignTop)

        self.fila_scroll.setWidget(self.fila_lista)
        self.fila.conteudo.addWidget(self.fila_scroll)

        self.fila_linhas: list[dict[str, object]] = []
        self._garantir_linhas_fila(5)

    def _garantir_linhas_fila(self, quantidade: int) -> None:
        while len(self.fila_linhas) < max(0, quantidade):
            indice = len(self.fila_linhas) + 1

            linha = QPushButton()
            linha.setObjectName("musicQueueItem")
            linha.setFixedHeight(54)
            linha.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            linha.setCursor(Qt.PointingHandCursor)
            linha.setEnabled(False)
            linha.clicked.connect(
                lambda _v=False, pos=indice - 1: self._acionar_fila(pos),
            )

            lay = QHBoxLayout(linha)
            lay.setContentsMargins(5, 4, 7, 4)
            lay.setSpacing(9)

            marcador = QWidget()
            marcador.setFixedWidth(20)

            marcador_layout = QHBoxLayout(marcador)
            marcador_layout.setContentsMargins(0, 0, 0, 0)
            marcador_layout.setSpacing(0)

            numero = QLabel(str(indice))
            numero.setObjectName("musicQueueNumber")
            numero.setAlignment(Qt.AlignCenter)

            equalizador = MiniEqualizadorFila(
                reduzir_movimento=self._reduzir_movimento
            )
            equalizador.hide()

            marcador_layout.addWidget(numero)
            marcador_layout.addWidget(equalizador)

            capa = CapaMusicaGenerica(36)

            textos = QVBoxLayout()
            textos.setSpacing(0)

            titulo = QLabel("Aguardando faixa observada")
            titulo.setObjectName("musicQueueText")
            titulo.setWordWrap(True)

            detalhe = QLabel("")
            detalhe.setObjectName("musicQueueDetail")

            textos.addWidget(titulo)
            textos.addWidget(detalhe)

            duracao = QLabel("—")
            duracao.setObjectName("musicQueueDuration")
            duracao.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            duracao.setFixedWidth(34)

            lay.addWidget(marcador)
            lay.addWidget(capa)
            lay.addLayout(textos, 1)
            lay.addWidget(duracao)

            linha.hide()
            self.fila_lista_layout.addWidget(linha)

            self.fila_linhas.append({
                "widget": linha,
                "number": numero,
                "equalizer": equalizador,
                "cover": capa,
                "title": titulo,
                "detail": detalhe,
                "duration": duracao,
                "item_id": "",
            })

    def _construir_acoes(self) -> None:
        self.acoes = QWidget()
        self.acoes.setObjectName("musicSessionActions")
        self.acoes.setMinimumHeight(46)
        self.acoes.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        self.acoes_layout = QGridLayout(
            self.acoes
        )
        self.acoes_layout.setContentsMargins(
            0, 0, 0, 0
        )
        self.acoes_layout.setSpacing(8)

        definicoes = (
            (
                "Tocar playlist",
                "playlist_play",
                "primary",
                145,
                "play",
                "",
            ),
            (
                "Pausar",
                "media_toggle",
                "primary",
                105,
                "pause",
                "",
            ),
            (
                "Próxima faixa",
                "media_next",
                "primary",
                125,
                "next",
                "",
            ),
            (
                "Volume —",
                "volume_set",
                "utility",
                115,
                "",
                "◖",
            ),
            (
                "Aleatório",
                "playlist_shuffle",
                "utility",
                100,
                "",
                "⇄",
            ),
            (
                "Repetição",
                "media_repeat",
                "utility",
                105,
                "",
                "↻",
            ),
            (
                "Sincronizar luzes",
                "lights_sync",
                "future",
                140,
                "",
                "✦",
            ),
        )

        self.acoes_sessao: dict[
            str,
            QPushButton,
        ] = {}

        self._botoes_sessao: list[
            QPushButton
        ] = []

        for (
            texto,
            acao_id,
            papel,
            largura,
            icone,
            simbolo,
        ) in definicoes:

            texto_visual = (
                f"{simbolo}  {texto}"
                if simbolo
                else texto
            )

            botao = QPushButton(
                texto_visual
            )

            botao.setObjectName(
                "musicSessionAction"
            )

            botao.setProperty(
                "actionRole",
                papel,
            )

            botao.setProperty(
                "actionId",
                acao_id,
            )

            botao.setProperty(
                "wideWidth",
                largura,
            )

            botao.setFixedHeight(36)

            botao.setSizePolicy(
                QSizePolicy.Ignored,
                QSizePolicy.Fixed,
            )

            # Ícones SVG que já existem no projeto
            if icone:
                botao.setIcon(
                    icone_terminal(icone)
                )
                botao.setIconSize(
                    QSize(15, 15)
                )

            botao.setEnabled(False)

            if acao_id == "media_toggle":
                botao.clicked.connect(
                    lambda:
                    self._solicitar(
                        "media_toggle"
                    )
                )

            elif acao_id == "media_next":
                botao.clicked.connect(
                    lambda:
                    self._solicitar(
                        "media_next"
                    )
                )

            elif acao_id == "playlist_play":
                botao.clicked.connect(
                    lambda:
                    self._solicitar_playlist(
                        self._playlist_ativa
                    )
                )

            elif acao_id == "playlist_shuffle":
                botao.clicked.connect(
                    self._solicitar_shuffle
                )

            elif acao_id == "media_repeat":
                botao.clicked.connect(
                    lambda:
                    self._solicitar(
                        "media_repeat"
                    )
                )

            elif acao_id == "volume_set":
                botao.clicked.connect(
                    self._focar_volume
                )

            else:
                botao.setToolTip(
                    "A lâmpada está separada do player; "
                    "sincronização contínua ainda não "
                    "tem executor."
                )

            # IMPORTANTE:
            # a chave continua sem símbolos.
            self.acoes_sessao[
                texto
            ] = botao

            self._botoes_sessao.append(
                botao
            )

    def _construir_modulos(self) -> None:
        # =========================================================
        # PLAYLISTS
        # =========================================================
        self.playlists = CartaoMusica(
            "Playlists",
            detalhe="catálogo real",
        )

        self.playlists_grade = QGridLayout()
        self.playlists_grade.setSpacing(7)

        self.preset_botoes: list[CartaoPlaylist] = []
        self._garantir_botoes_playlist(6)

        self.playlists.conteudo.addLayout(
            self.playlists_grade
        )

        rodape_playlists = QHBoxLayout()

        self.playlists_estado = QLabel(
            "Aguardando o catálogo salvo."
        )
        self.playlists_estado.setObjectName(
            "musicCatalogState"
        )

        self.ver_playlists = QPushButton(
            "Ver todas"
        )
        self.ver_playlists.setObjectName(
            "musicFutureButton"
        )
        self.ver_playlists.setEnabled(False)
        self.ver_playlists.clicked.connect(
            self._alternar_catalogo
        )

        rodape_playlists.addWidget(
            self.playlists_estado
        )
        rodape_playlists.addStretch()
        rodape_playlists.addWidget(
            self.ver_playlists
        )

        self.playlists.conteudo.addLayout(
            rodape_playlists
        )

        # =========================================================
        # CONTEXTO MUSICAL
        # =========================================================
        self.contexto = CartaoMusica(
            "Contexto musical  ✦ Laylay",
            detalhe="fundamentado",
        )
        self.contexto.conteudo.setSpacing(8)

        # Resumo principal
        self.contexto_estado = QLabel(
            "Aguardando horário e sessão musical observados."
        )
        self.contexto_estado.setObjectName(
            "musicContextSummary"
        )
        self.contexto_estado.setWordWrap(True)
        self.contexto_estado.setMinimumWidth(0)

        self.contexto.conteudo.addWidget(
            self.contexto_estado
        )

        # Recomendação da Laylay
        self.contexto_sugestao = QLabel(
            "Nenhuma recomendação fundamentada neste momento."
        )
        self.contexto_sugestao.setObjectName(
            "musicSuggestion"
        )
        self.contexto_sugestao.setWordWrap(True)
        self.contexto_sugestao.setMinimumWidth(0)

        self.contexto.conteudo.addWidget(
            self.contexto_sugestao
        )

        # Chips que mostram em que a recomendação se baseou
        self.contexto_bases = QWidget()
        self.contexto_bases.setObjectName(
            "musicContextChips"
        )

        self.contexto_bases_layout = QHBoxLayout(
            self.contexto_bases
        )
        self.contexto_bases_layout.setContentsMargins(
            0, 0, 0, 0
        )
        self.contexto_bases_layout.setSpacing(5)

        self.contexto_chips: list[QLabel] = []

        for _ in range(3):
            chip = QLabel("")
            chip.setObjectName(
                "musicContextChip"
            )
            chip.hide()

            self.contexto_bases_layout.addWidget(
                chip
            )
            self.contexto_chips.append(
                chip
            )

        self.contexto_bases_layout.addStretch()

        self.contexto_bases.hide()

        self.contexto.conteudo.addWidget(
            self.contexto_bases
        )

        # =========================================================
        # SAÍDA DE ÁUDIO
        # =========================================================
        self.audio = CartaoMusica(
            "Saída de áudio",
            detalhe="observada",
        )
        self.audio.conteudo.setSpacing(7)

        # Linha do dispositivo atualmente observado
        self.audio_dispositivo = QFrame()
        self.audio_dispositivo.setObjectName(
            "musicAudioDevice"
        )
        self.audio_dispositivo.setProperty(
            "available",
            False,
        )

        audio_layout = QHBoxLayout(
            self.audio_dispositivo
        )
        audio_layout.setContentsMargins(
            8, 7, 9, 7
        )
        audio_layout.setSpacing(9)

        # Ícone em uma caixinha
        self.audio_icone_caixa = QFrame()
        self.audio_icone_caixa.setObjectName(
            "musicAudioIconBox"
        )
        self.audio_icone_caixa.setFixedSize(
            36, 36
        )

        icone_layout = QHBoxLayout(
            self.audio_icone_caixa
        )
        icone_layout.setContentsMargins(
            0, 0, 0, 0
        )

        self.audio_icone = QLabel("♪")
        self.audio_icone.setObjectName(
            "musicAudioDeviceIcon"
        )
        self.audio_icone.setAlignment(
            Qt.AlignCenter
        )

        icone_layout.addWidget(
            self.audio_icone
        )

        # Nome + origem
        audio_textos = QVBoxLayout()
        audio_textos.setContentsMargins(
            0, 0, 0, 0
        )
        audio_textos.setSpacing(1)

        self.audio_saida = QLabel(
            "Aguardando saída de áudio"
        )
        self.audio_saida.setObjectName(
            "musicAudioOutput"
        )
        self.audio_saida.setWordWrap(False)
        self.audio_saida.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        self.audio_origem = QLabel(
            "Aguardando o Windows"
        )
        self.audio_origem.setObjectName(
            "musicAudioOutputMeta"
        )
        self.audio_origem.setWordWrap(False)

        audio_textos.addWidget(
            self.audio_saida
        )
        audio_textos.addWidget(
            self.audio_origem
        )

        # Indicador de dispositivo selecionado
        self.audio_selecionado = QLabel("—")
        self.audio_selecionado.setObjectName(
            "musicAudioSelected"
        )
        self.audio_selecionado.setAlignment(
            Qt.AlignCenter
        )
        self.audio_selecionado.setFixedSize(
            24, 24
        )

        audio_layout.addWidget(
            self.audio_icone_caixa
        )
        audio_layout.addLayout(
            audio_textos,
            1,
        )
        audio_layout.addWidget(
            self.audio_selecionado
        )

        self.audio.conteudo.addWidget(
            self.audio_dispositivo
        )

        # Botão inferior discreto
        self.audio_gerenciar = QPushButton(
            "Gerenciar dispositivos  ›"
        )
        self.audio_gerenciar.setObjectName(
            "musicAudioManage"
        )
        self.audio_gerenciar.setEnabled(False)
        self.audio_gerenciar.setFixedHeight(28)

        self.audio.conteudo.addWidget(
            self.audio_gerenciar
        )

        # =========================================================
        # MODO DE AUDIÇÃO
        # =========================================================
        self.audicao = CartaoMusica(
            "Modo de audição",
            detalhe="M3",
        )

        self.audicao_estado = _estado_futuro(
            "Volume mestre aguardando observação. "
            "Equalizador e som ambiente ainda não têm executor."
        )

        self.audicao.conteudo.addWidget(
            self.audicao_estado
        )

        # =========================================================
        # SINCRONIZAÇÃO DE LUZES
        # =========================================================
        self.luzes = CartaoMusica(
            "Sincronização de luzes",
            detalhe="M3",
        )

        self.luzes_estado = _estado_futuro(
            "A lâmpada existe, mas sincronização musical ainda não. "
            "O IoT permanece desligado deste painel."
        )

        self.luzes.conteudo.addWidget(
            self.luzes_estado
        )

        # =========================================================
        # LETRA / KARAOKÊ
        # =========================================================
        self.letra = CartaoMusica(
            "Letra",
            detalhe="LRCLIB",
        )
        self.letra.setObjectName(
            "musicLyrics"
        )

        self.letra_estado = _estado_futuro(
            "Aguardando uma faixa observada para procurar a letra."
        )

        self.letra.conteudo.addWidget(
            self.letra_estado
        )

        self.letra_texto = VisualizadorLetra()

        self._configurar_expansao_letra()

        self._efeito_letra: (
            QGraphicsOpacityEffect | None
        ) = None

        self.letra_texto.hide()

        self.letra.conteudo.addWidget(
            self.letra_texto
        )

        # Progresso da linha atual
        self.letra_progresso = QProgressBar()
        self.letra_progresso.setObjectName(
            "musicLyricsProgress"
        )
        self.letra_progresso.setRange(
            0, 1000
        )
        self.letra_progresso.setValue(0)
        self.letra_progresso.setTextVisible(
            False
        )
        self.letra_progresso.setFixedHeight(
            3
        )
        self.letra_progresso.hide()

        self.letra.conteudo.addWidget(
            self.letra_progresso
        )

        # Rodapé da letra
        rodape_letra = QHBoxLayout()

        self.letra_fonte = QLabel("")
        self.letra_fonte.setObjectName(
            "musicLyricsSource"
        )

        self.letra_expandir = QPushButton(
            "Ver letra completa"
        )
        self.letra_expandir.setObjectName(
            "musicFutureButton"
        )
        self.letra_expandir.clicked.connect(
            self._alternar_letra
        )
        self.letra_expandir.hide()

        rodape_letra.addWidget(
            self.letra_fonte
        )
        rodape_letra.addStretch()
        rodape_letra.addWidget(
            self.letra_expandir
        )

        self.letra.conteudo.addLayout(
            rodape_letra
        )

    def _garantir_botoes_playlist(self, quantidade: int) -> None:
        while len(self.preset_botoes) < max(0, quantidade):
            indice = len(self.preset_botoes)

            botao = CartaoPlaylist(indice)
            botao.setEnabled(False)
            botao.hide()

            botao.clicked.connect(
                lambda _v=False, pos=indice:
                self._acionar_playlist(pos),
            )

            self.playlists_grade.addWidget(
                botao,
                indice // 2,
                indice % 2,
            )

            self.preset_botoes.append(botao)

    def _construir_barra_lateral(self) -> None:
        self.barra_lateral = QWidget()
        self.barra_lateral.setObjectName("musicSideRail")
        self.barra_lateral.setMinimumWidth(265)
        self.barra_lateral.setMaximumWidth(310)

        layout = QVBoxLayout(self.barra_lateral)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # =========================================================
        # SISTEMA
        # =========================================================
        self.sistema = CartaoMusica(
            "Sistema",
            detalhe="observado",
        )
        self.sistema.conteudo.setSpacing(7)

        self.sistema_valores: dict[str, QLabel] = {}
        self.sistema_barras: dict[str, QProgressBar] = {}

        metricas = (
            ("cpu_percent", "CPU"),
            ("ram_percent", "RAM"),
            ("temperature_c", "Temperatura"),
            ("disk_percent", "Disco"),
        )

        for chave, nome in metricas:
            bloco = QWidget()
            bloco.setObjectName("musicSystemMetric")

            bloco_layout = QVBoxLayout(bloco)
            bloco_layout.setContentsMargins(0, 0, 0, 0)
            bloco_layout.setSpacing(3)

            topo = QHBoxLayout()
            topo.setContentsMargins(0, 0, 0, 0)

            rotulo = QLabel(nome)
            rotulo.setObjectName("musicSideLabel")

            valor = QLabel("—")
            valor.setObjectName("musicSideValue")
            valor.setAlignment(
                Qt.AlignRight | Qt.AlignVCenter
            )

            topo.addWidget(rotulo)
            topo.addStretch()
            topo.addWidget(valor)

            barra = QProgressBar()
            barra.setObjectName("musicSystemBar")
            barra.setRange(0, 100)
            barra.setValue(0)
            barra.setTextVisible(False)
            barra.setProperty("available", False)

            bloco_layout.addLayout(topo)
            bloco_layout.addWidget(barra)

            self.sistema_valores[chave] = valor
            self.sistema_barras[chave] = barra

            self.sistema.conteudo.addWidget(bloco)

        # Tempo ligado separado
        uptime_linha = QHBoxLayout()

        uptime_rotulo = QLabel("Tempo ligado")
        uptime_rotulo.setObjectName("musicSideLabel")

        uptime_valor = QLabel("—")
        uptime_valor.setObjectName("musicSideValue")

        uptime_linha.addWidget(uptime_rotulo)
        uptime_linha.addStretch()
        uptime_linha.addWidget(uptime_valor)

        self.sistema_valores["uptime_seconds"] = uptime_valor

        self.sistema.conteudo.addLayout(
            uptime_linha
        )

        # =========================================================
        # MODO DE AUDIÇÃO
        # =========================================================
        self.audicao = CartaoMusica(
            "Modo de audição",
            detalhe="M3",
        )
        self.audicao.conteudo.setSpacing(5)

        # Volume
        self.audicao_volume = QFrame()
        self.audicao_volume.setObjectName(
            "musicListeningRow"
        )

        volume_layout = QHBoxLayout(
            self.audicao_volume
        )
        volume_layout.setContentsMargins(
            8, 7, 8, 7
        )

        volume_icone = QLabel("♪")
        volume_icone.setObjectName(
            "musicListeningIcon"
        )
        volume_icone.setFixedWidth(22)
        volume_icone.setAlignment(Qt.AlignCenter)

        volume_nome = QLabel("Volume mestre")
        volume_nome.setObjectName(
            "musicListeningName"
        )

        self.audicao_volume_valor = QLabel("—")
        self.audicao_volume_valor.setObjectName(
            "musicListeningValue"
        )

        volume_layout.addWidget(volume_icone)
        volume_layout.addWidget(volume_nome)
        volume_layout.addStretch()
        volume_layout.addWidget(
            self.audicao_volume_valor
        )

        self.audicao.conteudo.addWidget(
            self.audicao_volume
        )

        # Equalizador
        equalizador = QFrame()
        equalizador.setObjectName(
            "musicListeningRow"
        )

        eq_layout = QHBoxLayout(equalizador)
        eq_layout.setContentsMargins(
            8, 7, 8, 7
        )

        eq_icone = QLabel("≋")
        eq_icone.setObjectName(
            "musicListeningIcon"
        )
        eq_icone.setFixedWidth(22)
        eq_icone.setAlignment(Qt.AlignCenter)

        eq_nome = QLabel("Equalizador")
        eq_nome.setObjectName(
            "musicListeningName"
        )

        eq_estado = QLabel("Em breve")
        eq_estado.setObjectName(
            "musicListeningFuture"
        )

        eq_layout.addWidget(eq_icone)
        eq_layout.addWidget(eq_nome)
        eq_layout.addStretch()
        eq_layout.addWidget(eq_estado)

        self.audicao.conteudo.addWidget(
            equalizador
        )

        # Som ambiente
        ambiente = QFrame()
        ambiente.setObjectName(
            "musicListeningRow"
        )

        ambiente_layout = QHBoxLayout(ambiente)
        ambiente_layout.setContentsMargins(
            8, 7, 8, 7
        )

        ambiente_icone = QLabel("◌")
        ambiente_icone.setObjectName(
            "musicListeningIcon"
        )
        ambiente_icone.setFixedWidth(22)
        ambiente_icone.setAlignment(
            Qt.AlignCenter
        )

        ambiente_nome = QLabel("Som ambiente")
        ambiente_nome.setObjectName(
            "musicListeningName"
        )

        ambiente_estado = QLabel("Em breve")
        ambiente_estado.setObjectName(
            "musicListeningFuture"
        )

        ambiente_layout.addWidget(
            ambiente_icone
        )
        ambiente_layout.addWidget(
            ambiente_nome
        )
        ambiente_layout.addStretch()
        ambiente_layout.addWidget(
            ambiente_estado
        )

        self.audicao.conteudo.addWidget(
            ambiente
        )

        # Mantemos por compatibilidade
        self.audicao_estado = QLabel("")
        self.audicao_estado.hide()

        # =========================================================
        # ROTINAS
        # =========================================================
        self.rotinas = CartaoMusica(
            "Rotinas",
            detalhe="agenda",
        )
        self.rotinas.conteudo.setSpacing(4)

        self.rotinas_estado = QLabel(
            "Nenhuma rotina recorrente observada."
        )
        self.rotinas_estado.setObjectName(
            "musicRoutineEmpty"
        )
        self.rotinas_estado.setWordWrap(True)

        self.rotinas.conteudo.addWidget(
            self.rotinas_estado
        )

        self.rotinas_linhas: list[dict[str, object]] = []

        for _ in range(3):
            linha = QFrame()
            linha.setObjectName("musicRoutineRow")
            linha.hide()

            linha_layout = QHBoxLayout(linha)
            linha_layout.setContentsMargins(
                8, 6, 8, 6
            )
            linha_layout.setSpacing(7)

            marcador = QLabel("●")
            marcador.setObjectName(
                "musicRoutineDot"
            )
            marcador.setFixedWidth(12)

            nome = QLabel("Rotina")
            nome.setObjectName(
                "musicRoutineName"
            )

            horario = QLabel("—")
            horario.setObjectName(
                "musicRoutineTime"
            )

            linha_layout.addWidget(marcador)
            linha_layout.addWidget(nome, 1)
            linha_layout.addWidget(horario)

            self.rotinas.conteudo.addWidget(
                linha
            )

            self.rotinas_linhas.append({
                "widget": linha,
                "name": nome,
                "time": horario,
            })

        # =========================================================
        # LUZES
        # =========================================================
        self.luzes = CartaoMusica(
            "Sincronização de luzes",
            detalhe="M3",
        )
        self.luzes.conteudo.setSpacing(6)

        self.luzes_dispositivo = QFrame()
        self.luzes_dispositivo.setObjectName(
            "musicLightsDevice"
        )
        self.luzes_dispositivo.setProperty(
            "configured",
            False,
        )

        luz_layout = QHBoxLayout(
            self.luzes_dispositivo
        )
        luz_layout.setContentsMargins(
            8, 7, 8, 7
        )
        luz_layout.setSpacing(8)

        self.luzes_icone = QLabel("●")
        self.luzes_icone.setObjectName(
            "musicLightsIcon"
        )
        self.luzes_icone.setFixedWidth(18)
        self.luzes_icone.setAlignment(
            Qt.AlignCenter
        )

        luz_textos = QVBoxLayout()
        luz_textos.setContentsMargins(
            0, 0, 0, 0
        )
        luz_textos.setSpacing(1)

        self.luzes_nome = QLabel(
            "Lâmpada RGB"
        )
        self.luzes_nome.setObjectName(
            "musicLightsName"
        )

        self.luzes_estado = QLabel(
            "Aguardando dispositivo"
        )
        self.luzes_estado.setObjectName(
            "musicLightsState"
        )

        luz_textos.addWidget(
            self.luzes_nome
        )
        luz_textos.addWidget(
            self.luzes_estado
        )

        self.luzes_status = QLabel(
            "—"
        )
        self.luzes_status.setObjectName(
            "musicLightsBadge"
        )

        luz_layout.addWidget(
            self.luzes_icone
        )
        luz_layout.addLayout(
            luz_textos,
            1,
        )
        luz_layout.addWidget(
            self.luzes_status
        )

        self.luzes.conteudo.addWidget(
            self.luzes_dispositivo
        )

        # =========================================================
        # ADICIONA NO PAINEL
        # =========================================================
        for cartao in (
            self.sistema,
            self.audicao,
            self.rotinas,
            self.luzes,
        ):
            layout.addWidget(cartao)

        layout.addStretch()
    def _organizar(self, compacto: bool) -> None:
        widgets = (
            self.cabecalho, self.player, self.fila, self.acoes, self.playlists,
            self.contexto, self.audio, self.barra_lateral, self.letra,
        )
        for widget in widgets:
            self.grade.removeWidget(widget)
        for botao in self._botoes_sessao:
            self.acoes_layout.removeWidget(botao)
        for coluna in range(10):
            self.acoes_layout.setColumnStretch(coluna, 0)

        for indice, botao in enumerate(self._botoes_sessao):
            if compacto:
                botao.setMinimumWidth(0)
                botao.setMaximumWidth(16777215)
                botao.setSizePolicy(
                    QSizePolicy.Expanding,
                    QSizePolicy.Fixed,
                )

                self.acoes_layout.addWidget(
                    botao,
                    indice // 2,
                    indice % 2,
                )

            else:
                largura = int(botao.property("wideWidth") or 110)

                botao.setMinimumWidth(largura)
                botao.setMaximumWidth(largura)
                botao.setSizePolicy(
                    QSizePolicy.Fixed,
                    QSizePolicy.Fixed,
                )

                self.acoes_layout.addWidget(
                    botao,
                    0,
                    indice + 1,
                    Qt.AlignCenter,
                )

        if compacto:
            self.acoes_layout.setColumnStretch(0, 1)
            self.acoes_layout.setColumnStretch(1, 1)
        else:
            # espaço flexível dos dois lados = grupo centralizado
            self.acoes_layout.setColumnStretch(0, 1)
            self.acoes_layout.setColumnStretch(
                len(self._botoes_sessao) + 1,
                1,
            )
        if compacto:
            linha = 0
            for widget in widgets:
                self.grade.addWidget(widget, linha, 0)
                linha += 1
            self.grade.setColumnStretch(0, 1)
            self.grade.setColumnStretch(1, 0)
            self.grade.setColumnStretch(2, 0)
        else:
            self.grade.addWidget(self.cabecalho, 0, 0, 1, 4)
            self.grade.addWidget(self.player, 1, 0, 1, 2)
            self.grade.addWidget(self.fila, 1, 2)
            self.grade.addWidget(self.barra_lateral, 1, 3, 5, 1)
            self.grade.addWidget(self.acoes, 2, 0, 1, 3)
            self.grade.addWidget(
                self.playlists,
                3,
                0,
                Qt.AlignTop,
            )

            self.grade.addWidget(
                self.contexto,
                3,
                1,
                Qt.AlignTop,
            )

            self.grade.addWidget(
                self.audio,
                3,
                2,
                Qt.AlignTop,
            )
            self.grade.addWidget(
                self.letra,
                4,
                0,
                1,
                3,
                Qt.AlignTop,
            )
            self.grade.setColumnStretch(0, 1)
            self.grade.setColumnStretch(1, 1)
            self.grade.setColumnStretch(2, 1)
            self.grade.setColumnStretch(3, 0)
        self._modo_compacto = compacto

    def _alternar_tela_cheia(self) -> None:
        janela = self.window()
        if janela.isFullScreen():
            janela.showNormal()
            self.tela_cheia.setText("Tela cheia")
        else:
            janela.showFullScreen()
            self.tela_cheia.setText("Sair da tela cheia")

    def _solicitar(self, acao_id: str) -> None:
        pedidos = {
            "media_previous": "volta para a música anterior",
            "media_next": "vai para a próxima música",
            "media_toggle": (
                "pausa a música" if self._estado_observado == "playing"
                else "continua a música"
            ),
            "media_repeat": "alterna a repetição da música",
        }
        pedido = pedidos.get(acao_id)
        if pedido:
            self.acao_solicitada.emit(acao_id, pedido)

    def _solicitar_shuffle(self) -> None:
        nome = " ".join(self._playlist_ativa.replace('"', "").split())[:80]
        if nome and self._shuffle_disponivel:
            self.acao_solicitada.emit(
                "playlist_shuffle",
                f"toca a playlist {nome} em modo aleatório",
            )

    def _solicitar_volume(self) -> None:
        self._volume_arrastando = False
        if not self._volume_disponivel:
            return
        nivel = int(self.volume_slider.value())
        self.acao_solicitada.emit(
            "volume_set", f"deixa o volume em {nivel} por cento",
        )

    def _focar_volume(self) -> None:
        if self._volume_disponivel:
            self.volume_slider.setFocus(Qt.MouseFocusReason)

    def _aplicar_fila(self, musica: dict) -> None:
        self._ultimo_retrato_musica = dict(musica or {})
        fila = list(musica.get("queue") or ()) if isinstance(musica, dict) else []
        observada = str(musica.get("queue_freshness") or "unavailable")
        self._fila_frescor = observada
        self._fila_fonte = str(musica.get("queue_source") or "")
        self._garantir_linhas_fila(len(fila))

        for indice, linha in enumerate(self.fila_linhas):
            widget = linha["widget"]

            if indice >= len(fila):
                widget.hide()
                continue
            item = fila[indice] if isinstance(fila[indice], dict) else {}
            item_id = str(item.get("item_id") or "").strip()
            linha["item_id"] = item_id

            primeira = indice == 0

            numero = linha["number"]
            equalizador = linha["equalizer"]

            numero.setText(str(indice + 1))
            numero.setVisible(not primeira)

            equalizador.setVisible(primeira)
            equalizador.definir_ativo(primeira)

            if widget.property("queueTop") != primeira:
                widget.setProperty("queueTop", primeira)
                widget.style().unpolish(widget)
                widget.style().polish(widget)

            linha["title"].setText(str(item.get("title") or "Faixa sem título"))
            linha["detail"].setText(str(item.get("channel") or "Canal não informado"))
            duracao = float(item.get("duration_seconds") or 0.0)
            linha["duration"].setText(_tempo(duracao) if duracao > 0 else "—")
            linha["cover"].definir_titulo(str(item.get("title") or ""))
            linha["cover"].carregar(str(item.get("artwork_url") or ""))
            widget.setAccessibleName(
                f"Tocar {linha['title'].text()}, posição {indice + 1} da fila"
            )
            widget.setToolTip(
                "Tocar esta faixa agora" if item_id else
                "Esta faixa não possui uma identidade observada para reprodução"
            )
            widget.show()
        if observada == "unavailable":
            self.fila_estado.setText("Nenhuma fila foi observada nesta reprodução.")
            self.fila_estado.show()
        elif not fila:
            self.fila_estado.setText("A fila observada não tem próximas faixas.")
            self.fila_estado.show()
        else:
            origem = str(musica.get("queue_source") or "")
            if origem == "laylay_playlist":
                self.fila_estado.setText("Ordem mantida pela playlist da Laylay.")
                self.fila_estado.show()
            else:
                self.fila_estado.hide()
        self._atualizar_botoes()

    def _acionar_fila(self, indice: int) -> None:
        if not 0 <= indice < len(self.fila_linhas) or self._fila_pendente:
            return
        linha = self.fila_linhas[indice]
        item_id = str(linha.get("item_id") or "").strip()
        titulo = str(linha["title"].text() or "faixa").strip()
        if (
            self._fila_fonte != "youtube"
            or self._fila_frescor != "fresh"
            or not item_id
        ):
            return
        self.acao_fila_solicitada.emit(
            "queue_play",
            f"toca {titulo} da fila",
            {"item_id": item_id, "queue_index": indice},
        )

    def _alternar_catalogo(self) -> None:
        self._catalogo_expandido = not self._catalogo_expandido
        self._renderizar_catalogo()

    def _aplicar_catalogo(self, musica: dict) -> None:
        disponivel = bool(musica.get("catalog_available") is True)
        self._catalogo = [
            dict(item) for item in list(musica.get("catalog") or ())
            if isinstance(item, dict)
        ] if disponivel else []
        self._garantir_botoes_playlist(len(self._catalogo))
        self._catalogo_pode_tocar = bool(
            musica.get("catalog_play_available") is True,
        )
        self._playlist_ativa = str(musica.get("playlist") or "").strip()
        self._renderizar_catalogo()

    def _renderizar_catalogo(self) -> None:
        limite = len(self._catalogo) if self._catalogo_expandido else 6
        for indice, botao in enumerate(self.preset_botoes):
            if indice >= len(self._catalogo) or indice >= limite:
                botao.hide()
                continue
            item = self._catalogo[indice]
            nome = str(item.get("name") or "Playlist")
            nome_visual = nome.capitalize() if nome.islower() else nome
            quantidade = max(0, int(item.get("count") or 0))
            ativo = (
                nome.casefold()
                == self._playlist_ativa.casefold()
            )

            botao.definir(
                nome_visual,
                quantidade,
                ativo=ativo,
            )

            botao.setToolTip(
                f'Tocar a playlist "{nome}" pela mente da Laylay'
            )

            botao.setAccessibleName(
                f"Playlist {nome}, "
                f"{quantidade} faixa"
                f"{'s' if quantidade != 1 else ''}"
            )
            botao.show()
        total = len(self._catalogo)
        self.playlists_estado.setText(
            f"{total} playlist{'s' if total != 1 else ''} no catálogo"
            if total else "Nenhuma playlist salva."
        )
        self.ver_playlists.setVisible(total > 6)
        self.ver_playlists.setEnabled(total > 6)
        self.ver_playlists.setText(
            "Mostrar menos" if self._catalogo_expandido else "Ver todas"
        )
        self._atualizar_botoes()

    def _acionar_playlist(self, indice: int) -> None:
        if 0 <= indice < len(self._catalogo):
            self._solicitar_playlist(str(self._catalogo[indice].get("name") or ""))

    def _solicitar_playlist(self, nome: str) -> None:
        nome = " ".join(str(nome or "").replace('"', "").split())[:80]
        if not nome or self._playlist_pendente:
            return
        self.acao_solicitada.emit(
            "playlist_play", f"toca a playlist {nome}",
        )

    def _aplicar_contexto_musical(
        self,
        musica: dict,
    ) -> None:
        contexto = musica.get("context_music")
        contexto = (
            contexto
            if isinstance(contexto, dict)
            else {}
        )

        frescor = str(
            contexto.get("freshness")
            or "unavailable"
        )

        resumo = str(
            contexto.get("summary") or ""
        ).strip()

        sugestao = str(
            contexto.get("recommendation") or ""
        ).strip()

        bases = [
            str(item)
            for item in list(
                contexto.get("basis") or ()
            )
        ]

        nomes_base = {
            "horario_local":
                "◷ Horário local",

            "playlist_ativa":
                "♫ Playlist escolhida",

            "catalogo_real":
                "▦ Catálogo real",

            "regra_de_horario":
                "◷ Regra de horário",

            "preferencia_confirmada":
                "♥ Preferência",

            "clima_observado":
                "☁ Clima",
        }

        if (
            frescor == "unavailable"
            or not resumo
        ):
            self.contexto_estado.setText(
                "Ainda não tenho contexto "
                "musical suficiente."
            )

            self.contexto_sugestao.setText(
                "✦ Nenhuma sugestão agora — "
                "melhor isso do que inventar."
            )

            self.contexto_bases.hide()

            for chip in self.contexto_chips:
                chip.hide()

            return

        # Resumo
        texto_resumo = resumo

        if frescor == "stale":
            texto_resumo += "  ·  dados antigos"

        self.contexto_estado.setText(
            texto_resumo
        )

        # Recomendação
        if sugestao:
            self.contexto_sugestao.setText(
                f"✦ {sugestao}"
            )
        else:
            self.contexto_sugestao.setText(
                "✦ Sem sugestão agora — "
                "melhor isso do que inventar "
                "uma playlist."
            )

        # Bases visíveis
        bases_visiveis = [
            nomes_base[item]
            for item in bases
            if item in nomes_base
        ][:3]

        for indice, chip in enumerate(
            self.contexto_chips
        ):
            if indice < len(bases_visiveis):
                chip.setText(
                    bases_visiveis[indice]
                )
                chip.show()
            else:
                chip.hide()

        self.contexto_bases.setVisible(
            bool(bases_visiveis)
        )

    def _alternar_letra(self) -> None:
        self._letra_expandida = not self._letra_expandida
        self.letra_expandir.setText(
            "Recolher letra" if self._letra_expandida else "Ver letra completa"
        )
        self._configurar_expansao_letra()
        self._linha_letra_atual = -2
        self._renderizar_letra(self._posicao_estimada())

    def _configurar_expansao_letra(self) -> None:
        if self._letra_expandida:
            self.letra_texto.definir_scroll_interno(True)
            self.letra_texto.setMinimumHeight(250)
            self.letra_texto.setMaximumHeight(360)
            self.letra_texto.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            return
        if self._animacao_rolagem_letra is not None:
            self._animacao_rolagem_letra.stop()
            self._animacao_rolagem_letra.deleteLater()
            self._animacao_rolagem_letra = None
        self.letra_texto.definir_scroll_interno(False)
        self.letra_texto.verticalScrollBar().setValue(0)
        self.letra_texto.setMinimumHeight(132)
        self.letra_texto.setMaximumHeight(132)
        self.letra_texto.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def _aplicar_letra(self, musica: dict) -> None:
        letra = musica.get("lyrics")
        letra = dict(letra) if isinstance(letra, dict) else {}
        if letra != self._letra_retrato:
            self._letra_retrato = letra
            self._letra_expandida = False
            self._linha_letra_atual = -2
            self.letra_expandir.setText("Ver letra completa")
            self._configurar_expansao_letra()
        status = str(letra.get("status") or "idle")
        mensagens = {
            "idle": "Aguardando uma faixa observada para procurar a letra.",
            "loading": "Procurando a letra na LRCLIB…",
            "instrumental": "A LRCLIB identifica esta faixa como instrumental.",
            "not_found": "A LRCLIB não encontrou uma letra compatível com esta faixa.",
            "rate_limited": "A LRCLIB pediu uma pausa. Vou respeitar o limite antes de consultar de novo.",
            "error": "Não consegui consultar a LRCLIB agora; o player continua funcionando normalmente.",
        }
        disponivel = status == "available" and bool(
            letra.get("lines") or str(letra.get("plain_text") or "").strip()
        )
        sincronizada = bool(
            disponivel
            and letra.get("synced") is True
            and letra.get("lines")
        )

        self.letra_progresso.setVisible(sincronizada)

        if not sincronizada:
            self.letra_progresso.setValue(0)
        self.letra_estado.setText(
            "Letra sincronizada com o tempo observado do player."
            if disponivel and letra.get("synced") is True else
            "Letra encontrada; esta versão não possui sincronização."
            if disponivel else mensagens.get(status, mensagens["error"])
        )
        self.letra_texto.setVisible(disponivel)
        self.letra_expandir.setVisible(disponivel)
        self.letra_fonte.setText("Letras fornecidas pela LRCLIB" if disponivel else "")
        if disponivel:
            self._renderizar_letra(self._posicao_estimada())

    def _renderizar_letra(self, posicao: float) -> None:
        letra = self._letra_retrato
        if str(letra.get("status") or "") != "available":
            return
        linhas = [
            item for item in list(letra.get("lines") or ())
            if isinstance(item, dict) and str(item.get("text") or "").strip()
        ]
        if linhas:
            tempos = [float(item.get("time_seconds") or 0.0) for item in linhas]
            atual = bisect_right(tempos, max(0.0, float(posicao))) - 1
            # Progresso dentro da linha atual
            if 0 <= atual < len(linhas):
                inicio_linha = tempos[atual]

                if atual + 1 < len(tempos):
                    fim_linha = tempos[atual + 1]
                else:
                    fim_linha = max(
                        inicio_linha + 4.0,
                        self._duracao_base,
                    )

                duracao_linha = max(
                    0.1,
                    fim_linha - inicio_linha,
                )

                progresso_linha = (
                    float(posicao) - inicio_linha
                ) / duracao_linha

                progresso_linha = max(
                    0.0,
                    min(1.0, progresso_linha),
                )

                self.letra_progresso.setValue(
                    int(progresso_linha * 1000)
                )
            else:
                self.letra_progresso.setValue(0)
            if atual == self._linha_letra_atual:
                return
            self._linha_letra_atual = atual
            indices = range(len(linhas)) if self._letra_expandida else range(
                max(0, atual - 1), min(len(linhas), max(2, atual + 3)),
            )
            blocos: list[str] = []

            for indice in indices:
                texto = html.escape(
                    str(linhas[indice].get("text") or "")
                )

                distancia = indice - atual

                # Linha sendo cantada agora
                if distancia == 0:
                    blocos.append(
                        f'<div style="'
                        f'color:#FF647B;'
                        f'font-size:20px;'
                        f'font-weight:700;'
                        f'margin:10px 0 11px 0;'
                        f'text-align:center;'
                        f'">{texto}</div>'
                    )

                # Linha anterior
                elif distancia == -1:
                    blocos.append(
                        f'<div style="'
                        f'color:#565D66;'
                        f'font-size:12px;'
                        f'margin:3px 0;'
                        f'text-align:center;'
                        f'">{texto}</div>'
                    )

                # Próxima linha
                elif distancia == 1:
                    blocos.append(
                        f'<div style="'
                        f'color:#A6ABB2;'
                        f'font-size:14px;'
                        f'font-weight:550;'
                        f'margin:5px 0;'
                        f'text-align:center;'
                        f'">{texto}</div>'
                    )

                # Linha que vem depois
                elif distancia == 2:
                    blocos.append(
                        f'<div style="'
                        f'color:#656C75;'
                        f'font-size:12px;'
                        f'margin:3px 0;'
                        f'text-align:center;'
                        f'">{texto}</div>'
                    )

                # Quando a letra completa está aberta
                else:
                    blocos.append(
                        f'<div style="'
                        f'color:#666D75;'
                        f'font-size:12px;'
                        f'margin:4px 0;'
                        f'text-align:center;'
                        f'">{texto}</div>'
                    )
            self._trocar_texto_letra(
                "".join(blocos), linha_ativa=atual, total_linhas=len(linhas),
            )
            return
        linhas_simples = [
            linha.strip() for linha in str(letra.get("plain_text") or "").splitlines()
            if linha.strip()
        ]
        visiveis = linhas_simples if self._letra_expandida else linhas_simples[:8]
        self._trocar_texto_letra(
            '<div style="color:#C9C5C8;font-size:13px;text-align:center;'
            'line-height:1.55;">'
            + "<br>".join(html.escape(linha) for linha in visiveis)
            + "</div>"
        )

    def _trocar_texto_letra(
        self,
        conteudo: str,
        *,
        linha_ativa: int | None = None,
        total_linhas: int = 0,
    ) -> None:
        if self.letra_texto.text() == conteudo:
            return

        rolagem_anterior = self.letra_texto.verticalScrollBar().value()

        self._versao_render_letra += 1
        versao = self._versao_render_letra

        # Interrompe qualquer transição anterior.
        if self._animacao_letra is not None:
            self._animacao_letra.stop()
            self._animacao_letra.deleteLater()
            self._animacao_letra = None

        # Remove qualquer efeito antigo antes de atualizar o texto.
        if self.letra_texto.graphicsEffect() is not None:
            self.letra_texto.setGraphicsEffect(None)

        self._efeito_letra = None

        self.letra_texto.setText(conteudo)

        if self._letra_expandida and linha_ativa is not None:
            QTimer.singleShot(
                0,
                lambda: self._acompanhar_linha_ativa(
                    linha_ativa,
                    total_linhas,
                    rolagem_anterior,
                    versao,
                ),
            )

        # Sem animação: o QTextBrowser fica completamente normal.
        if self._reduzir_movimento or not self.letra_texto.isVisible():
            return

        inicio = 0.68 if self._letra_expandida else 0.35

        efeito = QGraphicsOpacityEffect(self.letra_texto)
        efeito.setOpacity(inicio)

        self.letra_texto.setGraphicsEffect(efeito)
        self._efeito_letra = efeito

        animacao = QPropertyAnimation(
            efeito,
            b"opacity",
            self.letra_texto,
        )

        animacao.setDuration(
            260 if self._letra_expandida else 340
        )

        animacao.setStartValue(inicio)
        animacao.setKeyValueAt(
            0.35,
            0.86 if self._letra_expandida else 0.78,
        )
        animacao.setEndValue(1.0)
        animacao.setEasingCurve(QEasingCurve.OutCubic)

        self._animacao_letra = animacao

        def finalizar() -> None:
            if self._animacao_letra is animacao:
                self._animacao_letra = None

            # Parte importante:
            # terminou a animação -> remove totalmente o QGraphicsEffect.
            if self.letra_texto.graphicsEffect() is efeito:
                self.letra_texto.setGraphicsEffect(None)

            if self._efeito_letra is efeito:
                self._efeito_letra = None

            animacao.deleteLater()

        animacao.finished.connect(finalizar)
        animacao.start()

    def _acompanhar_linha_ativa(
        self,
        linha_ativa: int,
        total_linhas: int,
        rolagem_anterior: int,
        versao: int,
    ) -> None:
        if versao != self._versao_render_letra or not self._letra_expandida:
            return
        barra = self.letra_texto.verticalScrollBar()
        maximo = max(0, barra.maximum())
        inicio = max(0, min(maximo, int(rolagem_anterior)))
        divisor = max(1, int(total_linhas) - 1)
        destino = round(maximo * max(0, min(divisor, int(linha_ativa))) / divisor)
        barra.setValue(inicio)
        if abs(destino - inicio) <= 2:
            barra.setValue(destino)
            return
        if self._animacao_rolagem_letra is not None:
            self._animacao_rolagem_letra.stop()
            self._animacao_rolagem_letra.deleteLater()
        if self._reduzir_movimento:
            self._animacao_rolagem_letra = None
            barra.setValue(destino)
            return
        animacao = QPropertyAnimation(barra, b"value", self.letra_texto)
        animacao.setDuration(420)
        animacao.setStartValue(inicio)
        animacao.setEndValue(destino)
        animacao.setEasingCurve(QEasingCurve.InOutCubic)
        self._animacao_rolagem_letra = animacao
        animacao.start()

    def aplicar_dashboard(self, dashboard: dict) -> None:
        musica = dashboard.get("music")
        musica = musica if isinstance(musica, dict) else {}
        self._aplicar_catalogo(musica)
        self._aplicar_fila(musica)
        self._aplicar_contexto_musical(musica)
        self._estado_observado = str(musica.get("state") or "unknown")
        self._controles_disponiveis = bool(musica.get("controls_available"))
        self._repeat_disponivel = bool(musica.get("repeat_available") is True)
        self._repeat_ativo = bool(musica.get("repeat_enabled") is True)
        self._shuffle_disponivel = bool(musica.get("shuffle_available") is True)
        volume_sistema = musica.get("volume_percent")
        self.audicao_volume_valor.setText(
            f"{volume_sistema}%"
            if volume_sistema is not None
            else "—"
        )

        self.audicao_volume.setProperty(
            "available",
            volume_sistema is not None,
        )

        self.audicao_volume.style().unpolish(
            self.audicao_volume
        )
        self.audicao_volume.style().polish(
            self.audicao_volume
        )
        try:
            volume_sistema = max(0, min(100, round(float(volume_sistema))))
        except (TypeError, ValueError):
            volume_sistema = None
        self._volume_disponivel = volume_sistema is not None
        if volume_sistema is not None and not self._volume_arrastando:
            self.volume_slider.setValue(volume_sistema)
        self.volume.setText(
            f"VOLUME\n{volume_sistema}%" if volume_sistema is not None
            else "VOLUME\n—"
        )
        self.acoes_sessao["Volume —"].setText(
            f"◖  Volume {volume_sistema}%"
            if volume_sistema is not None
            else "◖  Volume —"
        )
        self.volume_muted.setText(
            "player mudo" if musica.get("muted") is True else ""
        )
        self.botoes["media_repeat"].setProperty(
            "activeControl", self._repeat_ativo,
        )
        self.botoes["media_repeat"].style().unpolish(
            self.botoes["media_repeat"],
        )
        self.botoes["media_repeat"].style().polish(
            self.botoes["media_repeat"],
        )
        self.acoes_sessao["Repetição"].setText(
            "↻  Repetição ligada"
            if self._repeat_ativo
            else "↻  Repetição"
        )
        audio = musica.get("audio_output")
        audio = audio if isinstance(audio, dict) else {}
        audio_disponivel = (
            audio.get("available") is True
            and bool(str(audio.get("name") or "").strip())
        )

        if audio_disponivel:
            self.audio_saida.setText(
                str(audio.get("name") or "Saída de áudio")
            )

            origem = str(
                audio.get("source") or "Padrão do sistema"
            ).strip()

            self.audio_origem.setText(
                origem.capitalize()
            )

        else:
            self.audio_saida.setText(
                "Nenhuma saída observada"
            )
            self.audio_origem.setText(
                "Aguardando o Windows"
            )
            self.audio_selecionado.setText(
                "✓" if audio_disponivel else "—"
            )

            self.audio_selecionado.setProperty(
                "selected",
                audio_disponivel,
            )

            self.audio_icone_caixa.setProperty(
                "available",
                audio_disponivel,
            )

            for widget in (
                self.audio_selecionado,
                self.audio_icone_caixa,
            ):
                widget.style().unpolish(widget)
                widget.style().polish(widget)

        if self.audio_dispositivo.property("available") != audio_disponivel:
            self.audio_dispositivo.setProperty(
                "available",
                audio_disponivel,
            )
            self.audio_dispositivo.style().unpolish(
                self.audio_dispositivo
            )
            self.audio_dispositivo.style().polish(
                self.audio_dispositivo
            )
        self.audicao_estado.setText(
            (
                f"Volume mestre observado em {volume_sistema}%. "
                "Equalizador e som ambiente ainda não têm executor."
            ) if volume_sistema is not None else (
                "Volume mestre indisponível. Equalizador e som ambiente ainda não têm executor."
            )
        )
        luzes = musica.get("lights")
        luzes = luzes if isinstance(luzes, dict) else {}
        luzes = musica.get("lights")
        luzes = (
            luzes
            if isinstance(luzes, dict)
            else {}
        )

        configurada = (
            luzes.get("configured") is True
        )

        self.luzes_estado.setText(
            "Configurada para a Laylay"
            if configurada
            else "Nenhuma lâmpada confirmada"
        )

        self.luzes_status.setText(
            "Pronta"
            if configurada
            else "—"
        )

        self.luzes_dispositivo.setProperty(
            "configured",
            configurada,
        )

        self.luzes_status.setProperty(
            "configured",
            configurada,
        )

        for widget in (
            self.luzes_dispositivo,
            self.luzes_status,
        ):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        if musica.get("freshness") == "unavailable":
            self.invalidar("Player não observado")
            self._aplicar_lateral(dashboard)
            return
        titulo = str(musica.get("title") or "Faixa sem título")
        self.titulo.setText(titulo)
        self.capa.definir_titulo(titulo)
        self._artwork_url = str(musica.get("artwork_url") or "")
        self.capa.carregar(self._artwork_url)
        canal = str(musica.get("channel") or "Canal não informado")
        playlist = str(musica.get("playlist") or "").strip()
        self.canal.setText(canal + (f"  •  {playlist}" if playlist else ""))
        self._posicao_base = float(musica.get("position_seconds") or 0.0)
        self._duracao_base = float(musica.get("duration_seconds") or 0.0)
        self._observado_em = float(musica.get("observed_at") or 0.0)
        self.selo.setText(
            "TOCANDO AGORA" if self._estado_observado == "playing"
            else "PAUSADA" if self._estado_observado == "paused"
            else "PLAYER OBSERVADO"
        )
        self.onda.definir_tocando(self._estado_observado == "playing")
        sufixo = " · dados antigos" if musica.get("freshness") == "stale" else ""
        self.estado.setText(
            {
                "playing": "Tocando · estado observado",
                "paused": "Pausada · estado observado",
                "ended": "Finalizada · estado observado",
                "unknown": "Reprodução ainda não confirmada",
            }.get(self._estado_observado, "Indisponível") + sufixo
        )
        self.botoes["media_toggle"].setIcon(icone_terminal(
            "pause" if self._estado_observado == "playing" else "play"
        ))
        botao_toggle = self.acoes_sessao[
            "Pausar"
        ]

        tocando = (
            self._estado_observado
            == "playing"
        )

        botao_toggle.setText(
            "Pausar"
            if tocando
            else "Continuar"
        )

        botao_toggle.setIcon(
            icone_terminal(
                "pause"
                if tocando
                else "play"
            )
        )
        self._aplicar_letra(musica)
        self._renderizar_tempo(self._posicao_estimada())
        self._atualizar_botoes()
        self._aplicar_lateral(dashboard)

    def _aplicar_lateral(self, dashboard: dict) -> None:
        sistema = dashboard.get("system")
        sistema = sistema if isinstance(sistema, dict) else {}
        for chave, valor in self.sistema_valores.items():
            valor.setText(_metrica_dashboard(
                sistema.get(chave), uptime=chave == "uptime_seconds",
            ))
            barra = self.sistema_barras.get(chave)
            if barra is not None:
                metrica = sistema.get(chave)
                numero = (
                    metrica.get("value") if isinstance(metrica, dict) else None
                )
                try:
                    disponivel = numero is not None
                    barra.setValue(max(0, min(100, round(float(numero or 0)))))
                except (TypeError, ValueError):
                    disponivel = False
                    barra.setValue(0)
                barra.setProperty("available", disponivel)
                barra.style().unpolish(barra)
                barra.style().polish(barra)
        rotinas = dashboard.get("routines")
        itens = (
            list(rotinas.get("items") or ())
            if isinstance(rotinas, dict) and rotinas.get("freshness") != "unavailable"
            else []
        )
        rotinas = dashboard.get("routines")

        itens = (
            list(rotinas.get("items") or ())
            if (
                isinstance(rotinas, dict)
                and rotinas.get("freshness") != "unavailable"
            )
            else []
        )

        itens_validos = [
            item
            for item in itens[:3]
            if isinstance(item, dict)
        ]

        self.rotinas_estado.setVisible(
            not bool(itens_validos)
        )

        for indice, linha in enumerate(
            self.rotinas_linhas
        ):
            widget = linha["widget"]

            if indice >= len(itens_validos):
                widget.hide()
                continue

            item = itens_validos[indice]

            linha["name"].setText(
                str(
                    item.get("name")
                    or "Rotina"
                )
            )

            linha["time"].setText(
                str(
                    item.get("time")
                    or "—"
                )
            )

            widget.show()

    def _renderizar_tempo(self, posicao: float) -> None:
        if self._duracao_base > 0:
            posicao = min(max(0.0, posicao), self._duracao_base)
            valor = int((posicao / self._duracao_base) * 1000)
        else:
            posicao, valor = max(0.0, posicao), 0
        self.progresso.setValue(max(0, min(1000, valor)))
        self.tempo_atual.setText(_tempo(posicao))
        self.tempo_total.setText(_tempo(self._duracao_base))
        self.tempo.setText(f"{_tempo(posicao)} / {_tempo(self._duracao_base)}")

    def _posicao_estimada(self, agora: float | None = None) -> float:
        posicao = self._posicao_base
        instante = time.time() if agora is None else float(agora)
        if self._estado_observado == "playing" and self._observado_em > 0:
            posicao += max(0.0, instante - self._observado_em)
        if self._duracao_base > 0:
            posicao = min(posicao, self._duracao_base)
        return max(0.0, posicao)

    def _atualizar_relogio(self) -> None:
        if self._estado_observado == "unavailable":
            return
        idade = max(0.0, time.time() - self._observado_em)
        posicao = self._posicao_estimada()
        self._renderizar_tempo(posicao)
        self._renderizar_letra(posicao)
        if idade > 12.0 and self._controles_disponiveis:
            self._controles_disponiveis = False
            self._atualizar_botoes()

    def definir_conectada(self, conectada: bool) -> None:
        self._conectada = bool(conectada)
        self._atualizar_botoes()

    def _atualizar_botoes(self) -> None:
        habilitar = self._conectada and self._controles_disponiveis
        for botao in self.botoes.values():
            botao.setEnabled(habilitar)
        self.acoes_sessao["Pausar"].setEnabled(habilitar)
        self.acoes_sessao["Próxima faixa"].setEnabled(habilitar)
        repeat_habilitado = bool(self._conectada and self._repeat_disponivel)
        self.botoes["media_repeat"].setEnabled(repeat_habilitado)
        self.acoes_sessao["Repetição"].setEnabled(repeat_habilitado)
        shuffle_habilitado = bool(
            self._conectada and self._shuffle_disponivel
            and self._playlist_ativa and not self._playlist_pendente
        )
        self.botoes["playlist_shuffle"].setEnabled(shuffle_habilitado)
        self.acoes_sessao["Aleatório"].setEnabled(shuffle_habilitado)
        volume_habilitado = bool(self._conectada and self._volume_disponivel)
        self.volume_slider.setEnabled(volume_habilitado)
        self.acoes_sessao["Volume —"].setEnabled(volume_habilitado)
        habilitar_playlist = bool(
            self._conectada and self._catalogo_pode_tocar
            and not self._playlist_pendente
        )
        for indice, botao in enumerate(self.preset_botoes):
            botao.setEnabled(habilitar_playlist and indice < len(self._catalogo))
        fila_habilitada = bool(
            self._conectada and self._controles_disponiveis
            and self._fila_fonte == "youtube"
            and self._fila_frescor == "fresh"
            and not self._fila_pendente
        )
        for linha in self.fila_linhas:
            linha["widget"].setEnabled(
                fila_habilitada and bool(str(linha.get("item_id") or "")),
            )
        self.acoes_sessao["Tocar playlist"].setEnabled(
            habilitar_playlist and bool(self._playlist_ativa),
        )

    def definir_estado_acao(self, acao_id: str, estado: str, resumo: str = "") -> None:
        if acao_id == "queue_play":
            self._fila_pendente = estado in {"sending", "received", "executing"}
            self._atualizar_botoes()
            if resumo:
                self.fila_estado.setText(resumo)
                self.fila_estado.show()
            return
        if acao_id in {"playlist_play", "playlist_shuffle"}:
            self._playlist_pendente = estado in {"sending", "received", "executing"}
            self._atualizar_botoes()
            if resumo:
                self.playlists_estado.setText(resumo)
            return
        pendente = estado in {"sending", "received", "executing"}
        if acao_id == "volume_set":
            self.volume_slider.setEnabled(
                not pendente and self._conectada and self._volume_disponivel
            )
            self.acoes_sessao["Volume —"].setEnabled(
                not pendente and self._conectada and self._volume_disponivel
            )
            if resumo:
                self.estado.setText(resumo)
            return
        botao = self.botoes.get(str(acao_id or ""))
        if botao is not None:
            botao.setEnabled(
                not pendente and self._conectada and self._controles_disponiveis
            )
        if acao_id == "media_repeat":
            self.acoes_sessao["Repetição"].setEnabled(
                not pendente and self._conectada and self._repeat_disponivel
            )
        if resumo:
            self.estado.setText(resumo)

    def invalidar(self, texto: str = "Aguardando estado observado do player") -> None:
        self._controles_disponiveis = False
        self._repeat_disponivel = False
        self._repeat_ativo = False
        self._shuffle_disponivel = False
        self._fila_frescor = "unavailable"
        self._fila_fonte = ""
        self._fila_pendente = False
        self._estado_observado = "unavailable"
        self.titulo.setText("Nenhuma faixa confirmada")
        self.canal.setText("Aguardando o player observado pela extensão")
        self._artwork_url = ""
        self.capa.definir_titulo("")
        self.capa.carregar("")
        self.selo.setText("PLAYER NÃO OBSERVADO")
        self.onda.definir_tocando(False)
        self.estado.setText(texto)
        self._posicao_base = 0.0
        self._duracao_base = 0.0
        self._observado_em = 0.0
        self._renderizar_tempo(0.0)
        self.volume_muted.setText("")
        for valor in self.sistema_valores.values():
            valor.setText("—")
        self.rotinas_estado.setText("Aguardando a agenda observada.")
        self._letra_retrato = {}
        self._letra_expandida = False
        self._linha_letra_atual = -2
        self._configurar_expansao_letra()
        self.letra_estado.setText(
            "Aguardando uma faixa observada para procurar a letra."
        )
        self.letra_texto.clear()
        self.letra_texto.hide()
        self.letra_fonte.clear()
        self.letra_expandir.hide()
        self.contexto_estado.setText(
            "Ainda não tenho contexto musical suficiente."
        )

        self.contexto_sugestao.setText(
            "✦ Nenhuma sugestão agora — "
            "melhor isso do que inventar."
        )

        for chip in self.contexto_chips:
            chip.clear()
            chip.hide()

        self.contexto_bases.hide()
        self._atualizar_botoes()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        compacto = self.width() < 1080
        if compacto != self._modo_compacto:
            self._organizar(compacto)


PaginaMusica = PaginaMusicaM1
