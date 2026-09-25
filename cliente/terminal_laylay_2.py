"""Terminal Laylay 3.0 — cliente PySide6 da mente canônica."""

from __future__ import annotations

from datetime import datetime
import os
import re
from pathlib import Path
import sys
import time
import unicodedata
import uuid


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from cliente.terminal_2.transporte import TransporteDesktopCliente

try:
    from shiboken6 import isValid as objeto_qt_valido
    from PySide6.QtCore import (
        QEasingCurve, QObject, QParallelAnimationGroup, QPoint,
        QPropertyAnimation, QRect, QSequentialAnimationGroup, QSettings, QSize,
        QThread, QTimer, Qt, Signal,
    )
    from PySide6.QtGui import (
        QAction, QColor, QFont, QFontDatabase, QKeySequence, QPainter, QPainterPath,
        QPen, QPixmap, QShortcut,
    )
    from PySide6.QtWidgets import (
        QApplication, QBoxLayout, QButtonGroup, QCheckBox, QComboBox, QFileDialog,
        QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QLayout, QLineEdit,
        QInputDialog, QMainWindow, QMenu, QMessageBox, QPushButton, QScrollArea,
        QSizePolicy, QStackedWidget, QTextEdit,
        QToolButton, QVBoxLayout, QWidget,
    )
except ImportError as erro:  # pragma: no cover
    raise SystemExit(
        "O Terminal Laylay 3.0 precisa de PySide6. Instale com: pip install PySide6"
    ) from erro


def _objeto_qt_esta_vivo(objeto: object) -> bool:
    """Confere o wrapper e o objeto C++ antes de callbacks assíncronos."""
    try:
        return objeto is not None and bool(objeto_qt_valido(objeto))
    except (RuntimeError, TypeError):
        return False

from cliente.terminal_2.dashboard import (
    ChipEstado,
    PaginaAutomacao,
    PaginaMemoria,
    PaginaMusica,
    PaginaSistema,
    PainelCentralInteligente,
    PainelLateralDashboard,
)
from cliente.terminal_2.acabamento import (
    FormaOndaMicrofone,
    icone_terminal,
    tamanho_icone,
)
from cliente.terminal_2.volume_mestre_windows import (
    DefinidorVolumeMestreWindows,
)
from cliente.terminal_2.desenvolvedor import PaginaDesenvolvedor
from cliente.terminal_2.theme import (
    PALETA,
    qss_automation_components,
    qss_chat_components,
    qss_chrome_components,
    qss_context_components,
    qss_home_refresh,
    qss_live_presence,
    qss_memory_refresh,
    qss_product_polish,
    qss_settings_refresh,
    qss_system_components,
    qss_tabs_refresh,
)

# Mantém a leitura confortável em janelas desktop sem transformar cada fala em
# uma faixa de ponta a ponta. Em viewports menores, o QScrollArea e os stretches
# das linhas continuam comprimindo os balões naturalmente.
LARGURA_MAXIMA_MENSAGEM_LAYLAY = 560
LARGURA_MAXIMA_MENSAGEM_USUARIO = 520


def carregar_fontes_interface() -> str:
    """Registra fontes do Windows também no plugin Qt offscreen."""
    fontes = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    carregadas: list[str] = []
    for nome in (
        "SegUIVar.ttf", "segoeui.ttf", "segoeuib.ttf", "seguisym.ttf",
        "arial.ttf", "CascadiaCode.ttf",
    ):
        caminho = fontes / nome
        if not caminho.is_file():
            continue
        identificador = QFontDatabase.addApplicationFont(str(caminho))
        if identificador >= 0:
            carregadas.extend(QFontDatabase.applicationFontFamilies(identificador))
    return next(
        (nome for nome in carregadas if "Segoe UI Variable" in nome),
        next((nome for nome in carregadas if nome == "Segoe UI"), "Arial"),
    )


class PonteWorker(QObject):
    mensagem = Signal(dict)
    conectado = Signal(bool)
    falha = Signal(str)
    terminou = Signal()

    def __init__(
        self, host: str, port: int, token: str, *, session_id: str = "",
    ) -> None:
        super().__init__()
        self.transporte = TransporteDesktopCliente(
            host, port, token,
            ao_mensagem=self.mensagem.emit,
            ao_conexao=self.conectado.emit,
            ao_falha=self.falha.emit,
            session_id=session_id,
        )

    def parar(self) -> None:
        self.transporte.parar()

    def enfileirar(self, mensagem: dict) -> bool:
        return self.transporte.enfileirar(mensagem)

    def executar(self) -> None:
        self.transporte.executar()
        self.terminou.emit()


class AroPresenca(QWidget):
    """Avatar compacto: presença forte sem virar painel decorativo."""

    def __init__(self, raiz: Path, tamanho: int = 42) -> None:
        super().__init__()
        self.raiz = raiz
        self._tamanho = tamanho
        self._fase = 0.0
        self._cor = QColor(PALETA["violeta"])
        self._pixmap = QPixmap()
        self._ativo = False
        self._reduzir_movimento = False
        self.setFixedSize(tamanho, tamanho)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animar)
        self.atualizar("idle", "calma")

    def _avatar_path(self, emocao: str) -> Path:
        mapa = {
            "calma": ("calma", "laylay_calma_512_transparente_real_corrigida.png"),
            "feliz": ("feliz", "laylay_feliz_boca_fechada_512_RGBA.png"),
            "animada": ("animada", "laylay_animada_512_transparente_real.png"),
            "irritada": ("brava", "laylay_brava_512_transparente_real.png"),
            "brava": ("brava", "laylay_brava_512_transparente_real.png"),
            "triste": ("triste", "laylay_triste_512_transparente_real.png"),
            "surpresa": ("surpresa", "laylay_surpresa_512_transparente_real.png"),
            "envergonhada": ("envergonhada", "laylay_envergonhada_512_transparente.png"),
        }
        pasta, nome = mapa.get(emocao, mapa["calma"])
        return self.raiz / "avatar" / pasta / nome

    def atualizar(self, atividade: str, emocao: str) -> None:
        cores_emocao = {
            "feliz": PALETA["rosa"], "animada": PALETA["rosa"],
            "irritada": PALETA["erro"], "brava": PALETA["erro"],
            "curiosa": PALETA["ciano"], "triste": "#8290D6",
        }
        cores_atividade = {
            "listening": PALETA["ciano"],
            "thinking": PALETA["violeta"],
            "executing": PALETA["aviso"],
            "speaking": PALETA["rosa"],
            "reconnecting": PALETA["erro"],
        }
        self._cor = QColor(
            cores_atividade.get(
                str(atividade or "idle"),
                cores_emocao.get(emocao, PALETA["violeta"]),
            )
        )
        self._ativo = atividade in {
            "thinking", "executing", "speaking", "listening", "reconnecting",
        }
        pix = QPixmap(str(self._avatar_path(emocao)))
        self._pixmap = pix.scaled(
            self._tamanho - 8, self._tamanho - 8,
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        ) if not pix.isNull() else QPixmap()
        if self._ativo and not self._reduzir_movimento and not self.timer.isActive():
            self.timer.start(90)
        elif not self._ativo or self._reduzir_movimento:
            self.timer.stop()
            self._fase = 0.0
        self.update()

    def definir_reduzir_movimento(self, reduzir: bool) -> None:
        self._reduzir_movimento = bool(reduzir)
        if self._reduzir_movimento:
            self.timer.stop()
            self._fase = 0.0
        elif self._ativo and not self.timer.isActive():
            self.timer.start(90)
        self.update()

    def _animar(self) -> None:
        self._fase = (self._fase + 0.06) % 1.0
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cor = QColor(self._cor)
        cor.setAlpha(205 if not self._ativo else int(135 + 90 * abs(0.5 - self._fase) * 2))
        painter.setPen(QPen(cor, 2))
        painter.setBrush(QColor(PALETA["elevada"]))
        painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)
        if not self._pixmap.isNull():
            x = (self.width() - self._pixmap.width()) // 2
            y = (self.height() - self._pixmap.height()) // 2
            painter.drawPixmap(x, y, self._pixmap)


class AvatarUsuario(QWidget):
    # Avatar local do usuário, independente da mente.

    def __init__(
        self,
        caminho: str = "",
        tamanho: int = 38,
    ) -> None:
        super().__init__()
        self._tamanho = int(tamanho)
        self._pixmap = QPixmap()

        self.setFixedSize(
            self._tamanho,
            self._tamanho,
        )

        self.definir_imagem(caminho)

    def definir_imagem(
        self,
        caminho: str,
    ) -> None:
        caminho = str(
            caminho or ""
        ).strip()

        if (
            caminho
            and Path(caminho).is_file()
        ):
            self._pixmap = QPixmap(
                caminho
            )
        else:
            self._pixmap = QPixmap()

        self.update()

    def paintEvent(
        self,
        _event,
    ) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.Antialiasing
        )

        area = self.rect().adjusted(
            2, 2, -2, -2
        )

        painter.setPen(
            QPen(
                QColor("#7D3A48"),
                2,
            )
        )
        painter.setBrush(
            QColor("#1C2026")
        )
        painter.drawEllipse(area)

        if not self._pixmap.isNull():
            imagem = self._pixmap.scaled(
                area.width(),
                area.height(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )

            recorte = QPainterPath()
            recorte.addEllipse(area)

            painter.save()
            painter.setClipPath(
                recorte
            )

            x = (
                self.width()
                - imagem.width()
            ) // 2
            y = (
                self.height()
                - imagem.height()
            ) // 2

            painter.drawPixmap(
                x,
                y,
                imagem,
            )
            painter.restore()

            painter.setPen(
                QPen(
                    QColor("#7D3A48"),
                    2,
                )
            )
            painter.setBrush(
                Qt.NoBrush
            )
            painter.drawEllipse(area)
            return

        painter.setPen(Qt.NoPen)
        painter.setBrush(
            QColor("#A9A2A7")
        )

        cx = self.width() // 2
        cy = self.height() // 2

        cabeca = max(
            6,
            self._tamanho // 5,
        )

        painter.drawEllipse(
            cx - cabeca // 2,
            cy - cabeca,
            cabeca,
            cabeca,
        )

        corpo_largura = max(
            12,
            self._tamanho // 2,
        )
        corpo_altura = max(
            7,
            self._tamanho // 4,
        )

        painter.drawEllipse(
            cx - corpo_largura // 2,
            cy + 1,
            corpo_largura,
            corpo_altura,
        )


class MensagemWidget(QFrame):
    reenviar = Signal(str, str)

    def __init__(
        self, papel: str, texto: str, horario: str | None = None,
        *, mensagem_id: str = "", status: str = "accepted",
    ) -> None:
        super().__init__()
        self.papel = papel
        self.mensagem_id = mensagem_id
        self.texto = texto
        self.setObjectName("messageUser" if papel == "user" else "messageLaylay")
        self.setMaximumWidth(
            LARGURA_MAXIMA_MENSAGEM_LAYLAY
            if papel == "assistant"
            else LARGURA_MAXIMA_MENSAGEM_USUARIO
        )
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(
            16, 11, 16, 10
        )
        lay.setSpacing(5)
        self.horario = str(horario or "")

        self.corpo = QLabel(texto)
        self.corpo.setObjectName("messageText")
        self.corpo.setWordWrap(True)
        self.corpo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.corpo.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Metadados de entrega da mensagem:
        # Só o texto fica dentro do balão.
        lay.addWidget(self.corpo)
        self.status = QLabel()
        self.status.setObjectName("messageStatus")
        self.retry = QPushButton("Tentar novamente")
        self.retry.setObjectName("retryButton")
        self.retry.clicked.connect(lambda: self.reenviar.emit(self.mensagem_id, self.texto))
        self.retry.hide()
        if papel == "user":
            self.definir_status(status)
        else:
            self.status.hide()
            self.retry.hide()
        natural = super().sizeHint().width()
        self.largura_preferida = min(
            self.maximumWidth(), max(natural, 180 + min(680, len(self.texto) * 3)),
        )

    def atualizar_texto(self, texto: str) -> None:
        texto = str(texto or "").strip()
        if not texto or texto == self.texto:
            return
        self.texto = texto
        self.corpo.setText(texto)
        self.largura_preferida = min(
            self.maximumWidth(), max(180, 180 + min(680, len(texto) * 3)),
        )
        self.updateGeometry()

    def definir_status(self, status: str, detalhe: str = "") -> None:
        mapa = {
            "pending": "Pendente · esperando a mente",
            "accepted": "Recebida pela mente",
            "failed": detalhe or "Não chegou à mente",
        }
        self.status.setText(mapa.get(status, mapa["accepted"]))
        self.status.setProperty("delivery", status)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

        self.status.setVisible(
            status in {"pending", "failed"}
        )
        self.retry.setVisible(
            status == "failed"
        )


class IndicadorPensando(QFrame):
    """Presença visual efêmera; nunca entra no histórico nem na porta de fala."""

    def __init__(
        self,
        *,
        reduzir_movimento: bool = False,
        atividade: str = "thinking",
    ) -> None:
        super().__init__()
        self.setObjectName("thinkingIndicator")
        self.setMaximumWidth(220)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 9, 14, 9)
        lay.setSpacing(8)
        meta = QLabel("LAYLAY")
        meta.setObjectName("thinkingMeta")
        lay.addWidget(meta)
        self.estado = QLabel()
        self.estado.setObjectName("thinkingState")
        lay.addWidget(self.estado)
        pontos_box = QFrame(self)
        pontos_lay = QHBoxLayout(pontos_box)
        pontos_lay.setContentsMargins(0, 0, 0, 0)
        pontos_lay.setSpacing(3)
        self.pontos: list[QLabel] = []
        self._efeitos_pontos: list[QGraphicsOpacityEffect] = []
        for indice in range(3):
            ponto = QLabel("●", pontos_box)
            ponto.setObjectName("thinkingDots")
            ponto.setFixedWidth(8)
            ponto.setAlignment(Qt.AlignCenter)
            efeito = QGraphicsOpacityEffect(ponto)
            efeito.setOpacity(1.0 if reduzir_movimento or indice == 0 else 0.24)
            ponto.setGraphicsEffect(efeito)
            pontos_lay.addWidget(ponto)
            self.pontos.append(ponto)
            self._efeitos_pontos.append(efeito)
        lay.addWidget(pontos_box)
        self.definir_estado(atividade)
        self._grupo_pontos: QSequentialAnimationGroup | None = None
        if not reduzir_movimento:
            grupo = QSequentialAnimationGroup(self)
            for fase in range(3):
                pulso = QParallelAnimationGroup(grupo)
                for indice, efeito in enumerate(self._efeitos_pontos):
                    animacao = QPropertyAnimation(efeito, b"opacity", pulso)
                    animacao.setDuration(210)
                    animacao.setEndValue(1.0 if indice == fase else 0.24)
                    animacao.setEasingCurve(QEasingCurve.InOutSine)
                    pulso.addAnimation(animacao)
                grupo.addAnimation(pulso)
            grupo.setLoopCount(-1)
            self._grupo_pontos = grupo
            grupo.start()

    def definir_estado(self, atividade: str) -> None:
        atividade = str(atividade or "thinking").casefold()
        if atividade not in {"thinking", "executing"}:
            atividade = "thinking"
        self.setProperty("activity", atividade)
        self.estado.setText(
            "Executando" if atividade == "executing" else "Pensando"
        )
        self.estado.setProperty("activity", atividade)
        for widget in (self, self.estado):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def parar(self) -> None:
        grupo = self._grupo_pontos
        if grupo is not None:
            grupo.stop()
            self._grupo_pontos = None


class AlternadorModo(QFrame):
    modo_solicitado = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("modeSwitch")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(3, 3, 3, 3)
        lay.setSpacing(2)
        self.grupo = QButtonGroup(self)
        self.grupo.setExclusive(True)
        self.botoes: dict[str, QPushButton] = {}
        for modo, texto in (("chat", "Chat"), ("voice", "Voz")):
            botao = QPushButton(texto)
            botao.setCheckable(True)
            botao.setAccessibleName(f"Ativar modo {texto.casefold()}")
            botao.setProperty("segment", True)
            botao.clicked.connect(lambda _v=False, m=modo: self.modo_solicitado.emit(m))
            self.grupo.addButton(botao)
            self.botoes[modo] = botao
            lay.addWidget(botao)
        self.definir("chat")

    def definir(self, modo: str, *, pendente: bool = False, voz_disponivel: bool = True) -> None:
        modo = modo if modo in self.botoes else "chat"
        self.botoes[modo].setChecked(True)
        self.botoes["chat"].setEnabled(not pendente)
        self.botoes["voice"].setEnabled(not pendente and voz_disponivel)
        self.botoes["voice"].setToolTip(
            "Usar o ouvido da Laylay" if voz_disponivel
            else "O ouvido não está disponível agora"
        )


class Composer(QFrame):
    enviar = Signal(str)
    alternar_voz = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("composer")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(
            8, 7, 8, 6
        )
        lay.setSpacing(3)

        linha = QHBoxLayout()
        linha.setSpacing(8)
        self.microfone = QPushButton()
        self.microfone.setObjectName("composerMic")
        self.microfone.setIcon(icone_terminal("microphone"))
        self.microfone.setIconSize(QSize(21, 21))
        self.microfone.setFixedSize(46, 46)
        self.microfone.setToolTip("Alternar entre conversa escrita e voz")
        self.microfone.setAccessibleName("Alternar modo de voz")
        self.microfone.clicked.connect(self.alternar_voz.emit)
        self.editor = QTextEdit()
        self.editor.setObjectName("composerEdit")
        self.editor.setPlaceholderText("Mensagem para a Laylay")
        self.editor.setAccessibleName("Mensagem para a Laylay")
        self.editor.setAcceptRichText(False)
        self.editor.setFixedHeight(44)
        self.editor.installEventFilter(self)
        self.botao = QPushButton()
        self.botao.setObjectName("sendButton")
        self.botao.setIcon(icone_terminal("send"))
        self.botao.setIconSize(QSize(18, 18))
        self.botao.setFixedSize(42, 42)
        self.botao.setToolTip("Enviar mensagem")
        self.botao.setAccessibleName("Enviar mensagem")
        self.botao.clicked.connect(self._emitir)
        linha.addWidget(self.microfone)
        linha.addWidget(self.editor, 1)
        linha.addWidget(self.botao, 0, Qt.AlignVCenter)
        lay.addLayout(linha)
        self.ajuda = QLabel("Enter para enviar  ·  Shift + Enter para nova linha")
        self.ajuda.setObjectName("composerHint")
        lay.addWidget(self.ajuda, 0, Qt.AlignHCenter)

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if obj is self.editor and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
                self._emitir()
                return True
        return super().eventFilter(obj, event)

    def _emitir(self) -> None:
        texto = self.editor.toPlainText().strip()
        if texto and self.editor.isEnabled():
            self.editor.clear()
            self.enviar.emit(texto)

    def definir_estado(self, *, conectado: bool, modo: str) -> None:
        chat = modo == "chat"
        self.editor.setEnabled(conectado and chat)
        self.botao.setEnabled(conectado and chat)
        self.microfone.setEnabled(conectado)
        if not conectado:
            texto = "Reconectando — a conversa continua na mente"
        elif chat:
            texto = "Mensagem para a Laylay"
        else:
            texto = "Modo voz ativo — fale com a Laylay pelo ouvido existente"
        self.editor.setPlaceholderText(texto)


class PaginaConfiguracoes(QWidget):
    salvar = Signal(dict)
    reiniciar = Signal()
    avatar_alterado = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("settingsPage")
        self._estado: dict = {}
        self._modelos_por_provedor: dict[str, str] = {}
        self._provedor_atual = ""
        self._preenchendo = False
        externo = QVBoxLayout(self)
        externo.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        self.scroll = scroll
        scroll.setObjectName("settingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        conteudo = QWidget()
        self.conteudo = conteudo
        conteudo.setObjectName("settingsContent")
        conteudo.setMaximumWidth(1080)
        conteudo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.conteudo_lay = QVBoxLayout(conteudo)
        lay = self.conteudo_lay
        lay.setContentsMargins(36, 32, 36, 44)
        lay.setSpacing(12)
        kicker = QLabel("CONFIGURAÇÕES")
        kicker.setObjectName("eyebrow")
        titulo = QLabel("O motor por trás da conversa")
        titulo.setObjectName("pageTitle")
        titulo.setWordWrap(True)
        intro = QLabel(
            "Escolha onde a Laylay pensa. A configuração é salva com segurança e "
            "passa a valer quando você reiniciar o aplicativo."
        )
        intro.setObjectName("pageDescription")
        intro.setWordWrap(True)
        lay.addWidget(kicker)
        lay.addWidget(titulo)
        lay.addWidget(intro)
        lay.addSpacing(20)

        sec_modelo = QLabel("Modelo de linguagem")
        sec_modelo.setObjectName("sectionTitle")
        lay.addWidget(sec_modelo)
        self.provider_group = QButtonGroup(self)
        self.provider_group.setExclusive(True)
        self.linha_provider = QHBoxLayout()
        self.linha_provider.setSpacing(8)
        self.providers: dict[str, QPushButton] = {}
        for chave, nome, detalhe in (
            ("ollama", "Local", "Ollama"),
            ("portatil", "Portátil", "llama.cpp"),
            ("openrouter", "OpenRouter", "API protegida"),
        ):
            botao = QPushButton(f"{nome}\n{detalhe}")
            botao.setCheckable(True)
            botao.setProperty("provider", True)
            botao.clicked.connect(self._provedor_alterado)
            self.provider_group.addButton(botao)
            self.providers[chave] = botao
            self.linha_provider.addWidget(botao, 1)
        lay.addLayout(self.linha_provider)

        label_modelo = QLabel("Modelo")
        label_modelo.setObjectName("fieldLabel")
        self.modelo = QLineEdit()
        self.modelo.setObjectName("settingsField")
        self.modelo.setPlaceholderText("Nome local ou ID do modelo")
        label_url = QLabel("Endpoint")
        label_url.setObjectName("fieldLabel")
        self.url = QLineEdit()
        self.url.setObjectName("settingsField")
        self.url.setReadOnly(True)
        lay.addSpacing(10)
        lay.addWidget(label_modelo)
        lay.addWidget(self.modelo)
        lay.addWidget(label_url)
        lay.addWidget(self.url)

        self.bloco_chave = QFrame()
        chave_lay = QVBoxLayout(self.bloco_chave)
        chave_lay.setContentsMargins(0, 8, 0, 0)
        chave_lay.setSpacing(8)
        self.linha_estado_chave = QHBoxLayout()
        chave_titulo = QLabel("Credencial OpenRouter")
        chave_titulo.setObjectName("fieldLabel")
        self.chave_estado = QLabel("Não configurada")
        self.chave_estado.setObjectName("keyState")
        self.linha_estado_chave.addWidget(chave_titulo)
        self.linha_estado_chave.addStretch()
        self.linha_estado_chave.addWidget(self.chave_estado)
        self.acao_chave = QComboBox()
        self.acao_chave.setObjectName("settingsField")
        self.acao_chave.addItem("Manter credencial atual", "preserve")
        self.acao_chave.addItem("Substituir credencial", "replace")
        self.acao_chave.addItem("Remover credencial", "remove")
        self.acao_chave.currentIndexChanged.connect(self._acao_chave_alterada)
        self.chave = QLineEdit()
        self.chave.setObjectName("settingsField")
        self.chave.setEchoMode(QLineEdit.Password)
        self.chave.setPlaceholderText("Cole uma nova chave; ela nunca será exibida novamente")
        chave_lay.addLayout(self.linha_estado_chave)
        chave_lay.addWidget(self.acao_chave)
        chave_lay.addWidget(self.chave)
        lay.addWidget(self.bloco_chave)

        self.banner = QLabel("")
        self.banner.setObjectName("settingsBanner")
        self.banner.setWordWrap(True)
        self.banner.hide()
        self.salvar_botao = QPushButton("Salvar configuração")
        self.salvar_botao.setObjectName("primaryButton")
        self.salvar_botao.clicked.connect(self._salvar)
        self.reiniciar_botao = QPushButton("↻  Reiniciar Laylay")
        self.reiniciar_botao.setObjectName("secondaryButton")
        self.reiniciar_botao.setToolTip(
            "Reinicia a Laylay com segurança e aplica as configurações salvas."
        )
        self.reiniciar_botao.setEnabled(False)
        self.reiniciar_botao.clicked.connect(self._reiniciar)
        acoes = QHBoxLayout()
        acoes.setSpacing(8)
        acoes.addWidget(self.salvar_botao)
        acoes.addWidget(self.reiniciar_botao)
        acoes.addStretch()
        lay.addSpacing(8)
        lay.addWidget(self.banner)
        lay.addLayout(acoes)

        lay.addSpacing(28)
        voz_titulo = QLabel("Voz")
        voz_titulo.setObjectName("sectionTitle")
        self.voz_estado = QLabel("Consultando o ouvido da Laylay…")
        self.voz_estado.setObjectName("settingsNote")
        self.voz_estado.setWordWrap(True)
        lay.addWidget(voz_titulo)
        lay.addWidget(self.voz_estado)

        lay.addSpacing(22)

        perfil_titulo = QLabel("Perfil")
        perfil_titulo.setObjectName(
            "sectionTitle"
        )
        lay.addWidget(perfil_titulo)

        self.perfil_card = QFrame()
        self.perfil_card.setObjectName(
            "settingsProfileCard"
        )

        perfil_lay = QHBoxLayout(
            self.perfil_card
        )
        perfil_lay.setContentsMargins(
            14, 12, 14, 12
        )
        perfil_lay.setSpacing(12)

        self.avatar_usuario_preview = AvatarUsuario(
            "",
            58,
        )

        perfil_textos = QVBoxLayout()
        perfil_textos.setContentsMargins(
            0, 0, 0, 0
        )
        perfil_textos.setSpacing(3)

        perfil_nome = QLabel(
            "Seu avatar"
        )
        perfil_nome.setObjectName(
            "settingsProfileTitle"
        )

        perfil_hint = QLabel(
            "Usado ao lado das suas mensagens."
        )
        perfil_hint.setObjectName(
            "settingsProfileHint"
        )
        perfil_hint.setWordWrap(True)

        perfil_textos.addWidget(
            perfil_nome
        )
        perfil_textos.addWidget(
            perfil_hint
        )

        self.trocar_avatar_botao = QPushButton(
            "Trocar foto"
        )
        self.trocar_avatar_botao.setObjectName(
            "profileAvatarButton"
        )
        self.trocar_avatar_botao.clicked.connect(
            self._selecionar_avatar
        )

        perfil_lay.addWidget(
            self.avatar_usuario_preview
        )
        perfil_lay.addLayout(
            perfil_textos,
            1,
        )
        perfil_lay.addWidget(
            self.trocar_avatar_botao
        )

        lay.addWidget(
            self.perfil_card
        )

        lay.addSpacing(22)
        interface_titulo = QLabel("Interface")
        interface_titulo.setObjectName("sectionTitle")
        self.manter_sidebar = QCheckBox("Manter a barra lateral expandida")
        self.manter_sidebar.setChecked(True)
        self.mostrar_mascote = QCheckBox("Mostrar mascote da Laylay")
        self.mostrar_mascote.setChecked(False)
        self.mostrar_mascote.setToolTip(
            "Abre o mascote junto da Laylay após reiniciar o aplicativo."
        )
        lay.addWidget(interface_titulo)
        lay.addWidget(self.manter_sidebar)
        lay.addWidget(self.mostrar_mascote)
        lay.addStretch()
        scroll.setWidget(conteudo)
        externo.addWidget(scroll)
        self._acao_chave_alterada()

    def definir_compacto(self, compacto: bool, *, estreito: bool = False) -> None:
        self.conteudo_lay.setContentsMargins(
            16 if estreito else 22 if compacto else 36,
            20 if estreito else 24 if compacto else 32,
            16 if estreito else 22 if compacto else 36,
            26 if estreito else 32 if compacto else 44,
        )
        self.providers["openrouter"].setText(
            "OpenRouter\nAPI" if compacto else "OpenRouter\nAPI protegida"
        )
        self.linha_provider.setDirection(
            QBoxLayout.TopToBottom if estreito else QBoxLayout.LeftToRight
        )
        self.linha_estado_chave.setDirection(
            QBoxLayout.TopToBottom if estreito else QBoxLayout.LeftToRight
        )

    def _provedor_selecionado(self) -> str:
        for chave, botao in self.providers.items():
            if botao.isChecked():
                return chave
        return "ollama"

    def _provedor_alterado(self) -> None:
        provedor = self._provedor_selecionado()
        if not self._preenchendo:
            if self._provedor_atual:
                self._modelos_por_provedor[self._provedor_atual] = self.modelo.text().strip()
            if provedor != self._provedor_atual:
                self.modelo.setText(self._modelos_por_provedor.get(provedor, ""))
        self._provedor_atual = provedor
        self.url.setText({
            "ollama": "http://localhost:11434/v1",
            "portatil": "Gerenciada pelo runtime portátil",
            "openrouter": "https://openrouter.ai/api/v1",
        }[provedor])
        self.bloco_chave.setVisible(provedor == "openrouter")

    def _acao_chave_alterada(self) -> None:
        substituir = self.acao_chave.currentData() == "replace"
        self.chave.setVisible(substituir)
        if not substituir:
            self.chave.clear()

    def preencher(self, estado: dict) -> None:
        self._estado = dict(estado or {})
        modelos = self._estado.get("models_by_provider")
        self._modelos_por_provedor = (
            {str(k): str(v or "") for k, v in modelos.items()}
            if isinstance(modelos, dict) else {}
        )
        provedor = str(self._estado.get("provider") or "ollama")
        self._modelos_por_provedor[provedor] = str(self._estado.get("model") or "")
        self._preenchendo = True
        self.providers.get(provedor, self.providers["ollama"]).setChecked(True)
        self._provedor_atual = provedor
        self.modelo.setText(self._modelos_por_provedor.get(provedor, ""))
        self.chave_estado.setText(
            "Chave configurada" if self._estado.get("api_key_configured")
            else "Não configurada"
        )
        self.acao_chave.setCurrentIndex(0)
        self._provedor_alterado()
        self._preenchendo = False
        self._acao_chave_alterada()
        self.mostrar_mascote.setChecked(bool(self._estado.get("mascot_enabled", False)))
        if self._estado.get("restart_required"):
            self.banner.setText(
                "Alterações salvas. Use ‘Reiniciar Laylay’ para aplicar agora."
            )
            self.banner.setProperty("kind", "success")
            self.banner.show()

    def definir_avatar_usuario(
        self,
        caminho: str,
    ) -> None:
        self.avatar_usuario_preview.definir_imagem(
            str(caminho or "")
        )

    def _selecionar_avatar(self) -> None:
        caminho, _filtro = QFileDialog.getOpenFileName(
            self,
            "Escolher foto de perfil",
            "",
            (
                "Imagens (*.png *.jpg *.jpeg *.webp *.bmp);;"
                "Todos os arquivos (*.*)"
            ),
        )

        if not caminho:
            return

        imagem = QPixmap(caminho)

        if imagem.isNull():
            self.banner.setText(
                "Não consegui abrir essa imagem."
            )
            self.banner.setProperty(
                "kind",
                "error",
            )
            self.banner.show()
            return

        destino = (
            Path.home()
            / ".laylay"
            / "terminal"
            / "avatar_usuario.png"
        )

        destino.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not imagem.save(
            str(destino),
            "PNG",
        ):
            self.banner.setText(
                "Não consegui salvar a foto de perfil."
            )
            self.banner.setProperty(
                "kind",
                "error",
            )
            self.banner.show()
            return

        caminho_final = str(destino)

        self.definir_avatar_usuario(
            caminho_final
        )

        self.avatar_alterado.emit(
            caminho_final
        )

        self.banner.setText(
            "Foto de perfil atualizada."
        )
        self.banner.setProperty(
            "kind",
            "success",
        )
        self.banner.style().unpolish(
            self.banner
        )
        self.banner.style().polish(
            self.banner
        )
        self.banner.show()

    def definir_voz(self, disponivel: bool) -> None:
        self.voz_estado.setText(
            "O ouvido está disponível. O seletor Chat/Voz usa a mesma captura da Laylay; "
            "esta janela não abre um segundo microfone."
            if disponivel else
            "O ouvido está indisponível agora. O modo Chat continua funcionando normalmente."
        )

    def _salvar(self) -> None:
        acao = str(self.acao_chave.currentData() or "preserve")
        payload = {
            "provider": self._provedor_selecionado(),
            "model": self.modelo.text().strip(),
            "api_key_action": acao,
            "api_key": self.chave.text() if acao == "replace" else "",
            "mascot_enabled": self.mostrar_mascote.isChecked(),
        }
        self.salvar_botao.setEnabled(False)
        self.banner.setText("Salvando sem expor sua credencial…")
        self.banner.setProperty("kind", "info")
        self.banner.show()
        self.salvar.emit(payload)

    def _reiniciar(self) -> None:
        if not self.reiniciar_botao.isEnabled():
            return
        self.reiniciar_botao.setEnabled(False)
        self.salvar_botao.setEnabled(False)
        self.banner.setText("Encerrando os serviços com cuidado para reiniciar…")
        self.banner.setProperty("kind", "info")
        self.banner.style().unpolish(self.banner)
        self.banner.style().polish(self.banner)
        self.banner.show()
        self.reiniciar.emit()

    def definir_conectada(self, conectada: bool) -> None:
        self.reiniciar_botao.setEnabled(bool(conectada))

    def resultado_reinicio(self, msg: dict) -> None:
        aceito = bool(msg.get("accepted"))
        self.banner.setText(str(msg.get("message") or (
            "Reiniciando…" if aceito else "Não consegui reiniciar."
        )))
        self.banner.setProperty("kind", "success" if aceito else "error")
        self.banner.style().unpolish(self.banner)
        self.banner.style().polish(self.banner)
        self.banner.show()
        if not aceito:
            self.salvar_botao.setEnabled(True)
            self.reiniciar_botao.setEnabled(True)

    def resultado(self, msg: dict) -> None:
        self.salvar_botao.setEnabled(True)
        self.chave.clear()
        self.acao_chave.setCurrentIndex(0)
        salvo = bool(msg.get("saved"))
        self.banner.setText(str(msg.get("message") or ("Configuração salva." if salvo else "Não consegui salvar.")))
        self.banner.setProperty("kind", "success" if salvo else "error")
        self.banner.style().unpolish(self.banner)
        self.banner.style().polish(self.banner)
        self.banner.show()
        if isinstance(msg.get("settings"), dict):
            self.preencher(msg["settings"])


class PaginaAdiada(QFrame):
    """Superfície leve exibida antes da materialização de uma aba pesada."""

    def __init__(self, titulo: str) -> None:
        super().__init__()
        self.setObjectName("lazyPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.addStretch()

        card = QFrame()
        card.setObjectName("lazyCard")
        card.setMaximumWidth(520)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(20, 18, 20, 20)
        card_lay.setSpacing(10)

        linha = QHBoxLayout()
        ponto = QLabel("●")
        ponto.setObjectName("lazyDot")
        estado = QLabel(f"Preparando {titulo}…")
        estado.setObjectName("lazyTitle")
        linha.addWidget(ponto)
        linha.addWidget(estado)
        linha.addStretch()
        card_lay.addLayout(linha)

        detalhe = QLabel(
            "Carregando somente os componentes necessários desta aba."
        )
        detalhe.setObjectName("lazyText")
        detalhe.setWordWrap(True)
        card_lay.addWidget(detalhe)
        card_lay.addSpacing(4)

        for largura in (100, 82, 62):
            barra = QFrame()
            barra.setObjectName("lazySkeleton")
            barra.setFixedHeight(9)
            barra.setMaximumWidth(int(440 * largura / 100))
            card_lay.addWidget(barra)

        layout.addWidget(card, 0, Qt.AlignHCenter)
        layout.addStretch()


class JanelaLaylay(QMainWindow):
    enviar_json = Signal(dict)

    def __init__(
        self,
        worker: PonteWorker,
        raiz: Path,
        *,
        session_id: str = "",
        parent_pid: int = 0,
    ) -> None:
        super().__init__()
        self.worker = worker
        self.raiz = raiz
        self._session_id = str(session_id or "").strip()[:8]
        self._parent_pid = max(0, int(parent_pid or 0))
        self.preferencias = QSettings("Laylay", "Terminal2")
        self._avatar_usuario_path = str(
            self.preferencias.value(
                "user_avatar_path",
                "",
            )
            or ""
        )
        self._ultima_mensagem: tuple[str, str, float] = ("", "", 0.0)
        self._envios: dict[str, MensagemWidget] = {}
        self._acoes_por_envio: dict[str, str] = {}
        self._conversa_ativa_id = ""
        self._conversas: list[dict] = []
        self._filtro_conversas = ""
        self._mostrar_arquivadas = False
        self._botoes_conversas: dict[str, QPushButton] = {}
        self._menus_conversas: dict[str, QToolButton] = {}
        self._envio_conversa: dict[str, str] = {}
        self._requisicao_conversa_id = ""
        self._indicador_pensando: IndicadorPensando | None = None
        self._container_indicador: QWidget | None = None
        self._animacoes: list[QParallelAnimationGroup] = []
        self._animacao_entrada_pensando: QParallelAnimationGroup | None = None
        self._animacao_saida_pensando: QParallelAnimationGroup | None = None
        self._container_saida_pensando: QWidget | None = None
        self._animacao_troca_conversa: QParallelAnimationGroup | None = None
        self._efeito_troca_conversa: QGraphicsOpacityEffect | None = None
        self._animacoes_conversas: list[QParallelAnimationGroup] = []
        self._micro_animacoes: dict[
            int,
            tuple[QWidget, QGraphicsOpacityEffect, QSequentialAnimationGroup],
        ] = {}
        self._assinatura_microestado = ""
        self._modo_visual_anterior = ""
        self._animacao_scroll: QPropertyAnimation | None = None
        self._pulso_presenca: QSequentialAnimationGroup | None = None
        self._efeito_presenca: QGraphicsOpacityEffect | None = None
        self._atividade_visual_atual = "idle"
        self._interface_animavel = False
        self._efeitos_inicio: list[
            tuple[str, QWidget, QGraphicsOpacityEffect]
        ] = []
        self._animacao_inicio_grupo: QParallelAnimationGroup | None = None
        self._pagina_visual_ativa = ""
        self._animacao_pagina_grupo: QParallelAnimationGroup | None = None
        self._efeito_pagina: QGraphicsOpacityEffect | None = None
        self._pagina_em_transicao: QWidget | None = None
        self._animacao_indicador_nav: QPropertyAnimation | None = None
        self._assinatura_responsividade: tuple[object, ...] | None = None
        self._ultima_largura_responsiva = -1
        self._dashboard_mais_recente: dict = {}
        self._estado_mais_recente: dict = {}
        self._paginas_carregadas: dict[str, QWidget] = {}
        self._paginas_adiadas: dict[str, PaginaAdiada] = {}
        self._carregamentos_pendentes: set[str] = set()
        self._estados_acoes_ui: dict[str, tuple[str, str]] = {}
        self._medidor_musica_mais_recente: dict = {}
        self._resultados_playlist_pendentes: list[
            tuple[str, dict, str, str]
        ] = []
        self._eventos_desenvolvedor: list[dict] = []
        self._ids_eventos_desenvolvedor: set[str] = set()
        self._nav: dict[str, QPushButton] = {}
        self._conectado = False
        self._modo = "chat"
        self._voz_disponivel = False
        self._modo_pendente = False
        self._reinicio_requisicao_id = ""
        self._timeouts_envio: dict[str, QTimer] = {}
        self._fases_envio: dict[str, str] = {}
        self._feed_em_espera = True
        self._ultima_atividade_evento = ""
        self._feedback_vivo_seq = 0
        self._estado_vivo_atual = "reconnecting"
        self._limiar_auto_scroll = 96
        self._pagina_principal = "inicio"
        self._provedor_modelo = ""
        self._dashboard_recebido = False
        self._nivel_microfone = 0.0
        self._reduzir_movimento = os.environ.get(
            "LAYLAY_REDUZIR_MOVIMENTO", "0",
        ).casefold() in {"1", "true", "sim", "yes", "on"}
        self._sidebar_expandida = bool(self.preferencias.value("sidebar_expandida", True, type=bool))
        titulo_sessao = f" · {self._session_id}" if self._session_id else ""
        self.setWindowTitle(f"Laylay — Terminal 3.0{titulo_sessao}")
        self.setMinimumSize(375, 620)
        self.resize(1680, 940)
        self._montar()
        self._atalhos()
        self._estilizar()
        self._aplicar_sidebar()
        self._aplicar_responsividade()
        self._registrar_feedback_botoes()

        # Inicialização modular: adia superfícies pesadas após a primeira pintura.
        # Pequeno respiro antes de começar a carregar os módulos.
        self._preparar_animacao_inicio()
        QTimer.singleShot(
            180,
            self._iniciar_animacao_inicio,
        )

        worker.mensagem.connect(self.receber)
        worker.conectado.connect(self.estado_conexao)
        worker.falha.connect(self.falha_conexao)
        self.enviar_json.connect(worker.enfileirar, Qt.DirectConnection)

    def _montar(self) -> None:
        raiz = QWidget(objectName="root")
        self.setCentralWidget(raiz)
        geral = QHBoxLayout(raiz)
        geral.setContentsMargins(0, 0, 0, 0)
        geral.setSpacing(0)

        self.sidebar = QFrame(objectName="sidebar")
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(10, 10, 10, 12)
        side.setSpacing(5)

        # ======================================================
        # Sidebar — marca compacta no mesmo eixo do topbar
        # ======================================================
        self.sidebar_topo = QFrame(objectName="sidebarBrandBar")
        topo = QHBoxLayout(self.sidebar_topo)
        topo.setContentsMargins(5, 3, 2, 7)
        topo.setSpacing(8)

        self.avatar_side = AroPresenca(
            self.raiz,
            34,
        )
        self.avatar_side.definir_reduzir_movimento(
            self._reduzir_movimento
        )

        marca_box = QVBoxLayout()
        marca_box.setContentsMargins(
            0, 0, 0, 0
        )
        marca_box.setSpacing(0)

        self.marca = QLabel("Laylay ✦")
        self.marca.setObjectName("brand")

        self.marca_status = QLabel(
            "companheira local"
        )
        self.marca_status.setObjectName(
            "brandCaption"
        )
        self.marca_status.hide()

        marca_box.addWidget(self.marca)
        marca_box.addWidget(
            self.marca_status
        )

        self.nova = QPushButton("Novo chat", self.sidebar)
        self.nova.setObjectName(
            "newChatButton"
        )
        self.nova.setProperty(
            "nav",
            True,
        )
        self.nova.setProperty(
            "label",
            "Novo chat",
        )
        self.nova.setAccessibleName(
            "Criar novo chat"
        )
        self.nova.setIcon(
            icone_terminal("compose")
        )
        self.nova.setIconSize(
            QSize(19, 19)
        )
        self.nova.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        self.nova.setToolTip(
            "Criar um novo chat"
        )
        self.nova.clicked.connect(
            self.nova_conversa
        )

        self.recolher = QToolButton(
            text="‹"
        )
        self.recolher.setObjectName(
            "collapseButton"
        )
        self.recolher.setToolTip(
            "Recolher barra lateral"
        )
        self.recolher.setAccessibleName(
            "Recolher ou expandir navegação"
        )
        self.recolher.clicked.connect(
            self.alternar_sidebar
        )

        topo.addWidget(self.avatar_side)
        topo.addLayout(marca_box, 1)
        topo.addWidget(self.recolher)

        side.addWidget(self.sidebar_topo)
        side.addSpacing(8)
        side.addWidget(self.nova)
        side.addSpacing(5)

        self.nav_label = QLabel(
            "NAVEGAÇÃO",
            self.sidebar,
        )
        self.nav_label.setObjectName(
            "sideSection"
        )
        self.nav_label.hide()

        for nome, icone, texto in (
            ("inicio", "home", "Início"),
            ("conversa", "chat", "Conversa"),
            (
                "automacao",
                "automation",
                "Automação",
            ),
            ("musica", "music", "Música"),
            ("memoria", "memory", "Memória"),
            ("sistema", "system", "Sistema"),
            ("desenvolvedor", "developer", "Dev Console"),
            (
                "configuracoes",
                "settings",
                "Configurações",
            ),
        ):
            botao = QPushButton(texto)
            botao.setIcon(
                icone_terminal(icone)
            )
            botao.setIconSize(
                QSize(19, 19)
            )
            botao.setCheckable(True)
            botao.setProperty(
                "nav",
                True,
            )
            botao.setProperty(
                "glyph",
                icone,
            )
            botao.setProperty(
                "label",
                texto,
            )
            botao.setAccessibleName(
                texto
            )
            botao.clicked.connect(
                lambda _v=False, n=nome:
                self.selecionar_pagina(n)
            )
            self._nav[nome] = botao
            side.addWidget(botao)

        self.indicador_navegacao = QFrame(self.sidebar)
        self.indicador_navegacao.setObjectName("navIndicator")
        self.indicador_navegacao.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True,
        )
        self.indicador_navegacao.hide()

        self._nav["inicio"].setChecked(
            True
        )

        self.recentes_label = QLabel(
            "CONVERSAS",
            self.sidebar,
        )
        self.recentes_label.setObjectName(
            "sideSection"
        )
        self.recentes_label.hide()

        self.conversa_atual = QPushButton(
            "Conversa atual",
            self.sidebar,
        )
        self.conversa_atual.setObjectName(
            "recentItem"
        )
        self.conversa_atual.setToolTip(
            "Título efêmero desta sessão visual"
        )
        self.conversa_atual.clicked.connect(
            lambda:
            self.selecionar_pagina(
                "conversa"
            )
        )
        self.conversa_atual.hide()

        self.ferramentas_conversas = QFrame(self.sidebar)
        self.ferramentas_conversas.setObjectName("conversationTools")
        ferramentas_lay = QHBoxLayout(self.ferramentas_conversas)
        ferramentas_lay.setContentsMargins(0, 0, 0, 2)
        ferramentas_lay.setSpacing(4)
        self.busca_conversas = QLineEdit(self.ferramentas_conversas)
        self.busca_conversas.setObjectName("conversationSearch")
        self.busca_conversas.setPlaceholderText("Buscar chats")
        self.busca_conversas.setClearButtonEnabled(True)
        self.busca_conversas.setAccessibleName("Buscar conversas")
        self.busca_conversas.textChanged.connect(self._filtrar_conversas)
        self.botao_arquivadas = QToolButton(self.ferramentas_conversas)
        self.botao_arquivadas.setObjectName("archivedConversationsButton")
        self.botao_arquivadas.setText("▣")
        self.botao_arquivadas.setCheckable(True)
        self.botao_arquivadas.setToolTip("Mostrar conversas arquivadas")
        self.botao_arquivadas.setAccessibleName(
            "Mostrar conversas arquivadas"
        )
        self.botao_arquivadas.toggled.connect(
            self._alternar_conversas_arquivadas,
        )
        ferramentas_lay.addWidget(self.busca_conversas, 1)
        ferramentas_lay.addWidget(self.botao_arquivadas)
        self.ferramentas_conversas.hide()

        self.conversas_scroll = QScrollArea(self.sidebar)
        self.conversas_scroll.setObjectName("conversationList")
        self.conversas_scroll.setWidgetResizable(True)
        self.conversas_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.conversas_scroll.setFrameShape(QFrame.NoFrame)
        self.conversas_scroll.setMinimumHeight(80)
        self.conversas_scroll.setMaximumHeight(230)
        self.conversas_container = QWidget()
        self.conversas_container.setObjectName("conversationListContent")
        self.conversas_lay = QVBoxLayout(self.conversas_container)
        self.conversas_lay.setContentsMargins(0, 0, 0, 0)
        self.conversas_lay.setSpacing(3)
        self.conversas_lay.addStretch(1)
        self.conversas_scroll.setWidget(self.conversas_container)
        self.conversas_scroll.hide()

        side.addWidget(self.recentes_label)
        side.addWidget(self.ferramentas_conversas)
        side.addWidget(self.conversas_scroll)

        self.status_mente = QLabel(
            "●  Reconectando",
            self.sidebar,
        )
        self.status_mente.setObjectName(
            "mindStatus"
        )
        self.status_mente.hide()

        self.config_rodape = QPushButton(
            "Ajustes da Laylay",
            self.sidebar,
        )
        self.config_rodape.setObjectName(
            "footerSettings"
        )
        self.config_rodape.setIcon(
            icone_terminal("settings")
        )
        self.config_rodape.setIconSize(
            tamanho_icone()
        )
        self.config_rodape.clicked.connect(
            lambda:
            self.selecionar_pagina(
                "configuracoes"
            )
        )
        self.config_rodape.hide()

        side.addStretch()

        self.profile_card = QFrame(
            objectName="sidebarProfile"
        )
        profile_lay = QVBoxLayout(
            self.profile_card
        )
        profile_lay.setContentsMargins(
            9, 9, 9, 8
        )
        profile_lay.setSpacing(6)

        profile_top = QHBoxLayout()
        profile_top.setContentsMargins(
            0, 0, 0, 0
        )
        profile_top.setSpacing(8)

        self.avatar_profile = AroPresenca(
            self.raiz,
            34,
        )
        self.avatar_profile.definir_reduzir_movimento(
            self._reduzir_movimento
        )

        profile_textos = QVBoxLayout()
        profile_textos.setContentsMargins(
            0, 0, 0, 0
        )
        profile_textos.setSpacing(1)

        self.profile_nome = QLabel(
            "Laylay"
        )
        self.profile_nome.setObjectName(
            "profileName"
        )

        self.profile_status = QLabel(
            "●  Reconectando"
        )
        self.profile_status.setObjectName(
            "profileStatus"
        )
        self.profile_status.setProperty(
            "state",
            "offline",
        )

        profile_textos.addWidget(
            self.profile_nome
        )
        profile_textos.addWidget(
            self.profile_status
        )

        self.profile_heart = QLabel("♥")
        self.profile_heart.setObjectName(
            "profileHeart"
        )
        self.profile_heart.setAlignment(
            Qt.AlignCenter
        )

        profile_top.addWidget(
            self.avatar_profile
        )
        profile_top.addLayout(
            profile_textos,
            1,
        )
        profile_top.addWidget(
            self.profile_heart
        )

        self.profile_version = QLabel(
            "Terminal 3.0"
        )
        self.profile_version.setObjectName(
            "profileVersion"
        )

        profile_lay.addLayout(profile_top)
        profile_lay.addWidget(
            self.profile_version
        )

        side.addWidget(self.profile_card)
        geral.addWidget(self.sidebar)
        centro = QFrame(objectName="mainSurface")
        centro_lay = QVBoxLayout(centro)
        centro_lay.setContentsMargins(0, 0, 0, 0)
        centro_lay.setSpacing(0)
        header = QFrame(objectName="topbar")
        self.topbar = header
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(24, 9, 24, 9)
        hlay.setSpacing(8)
        self.menu_compacto = QToolButton(text="☰")
        self.menu_compacto.setToolTip("Mostrar ou ocultar navegação")
        self.menu_compacto.setAccessibleName("Mostrar ou ocultar navegação")
        self.menu_compacto.clicked.connect(self._alternar_sidebar_compacta)
        self.menu_compacto.hide()
        # Estes controles permanecem como atributos por compatibilidade, mas
        # pertencem explicitamente ao cabeçalho. Sem pai e fora do layout, o
        # Qt os promovia a janelas independentes quando a responsividade
        # chamava setVisible(), criando os "mini terminais" no Alt+Tab.
        self.voltar = QToolButton(header)
        self.voltar.setText("←")
        self.voltar.setEnabled(False)
        self.voltar.setToolTip("Sem conversa anterior nesta versão")
        self.avancar = QToolButton(header)
        self.avancar.setText("→")
        self.avancar.setEnabled(False)
        self.avancar.setToolTip("Sem conversa seguinte nesta versão")
        self.titulo_header = QLabel("Início", header)
        self.titulo_header.setObjectName("headerTitle")
        hlay.addWidget(self.menu_compacto)
        self.voltar.hide()
        self.avancar.hide()
        self.titulo_header.hide()

        # Os dois lados usam o mesmo fator para preservar o centro visual.
        # Isso mantém o conjunto do topo centralizado.
        hlay.addStretch(1)

        self.chip_modelo = ChipEstado("Modelo", "Aguardando")
        self.chip_microfone = ChipEstado("Microfone", "Aguardando")
        self.chip_memoria = ChipEstado("Memória", "Aguardando")
        for chip in (
            self.chip_modelo, self.chip_microfone, self.chip_memoria,
        ):
            chip.estado_alterado.connect(
                lambda alvo=chip: self._animar_microinteracao(alvo)
            )
        hlay.addWidget(self.chip_modelo)
        hlay.addWidget(self.chip_microfone)
        hlay.addWidget(self.chip_memoria)
        hlay.addSpacing(4)
        self.alternador = AlternadorModo()
        self.alternador.modo_solicitado.connect(self.solicitar_modo)
        hlay.addWidget(self.alternador)
        self.presenca_pill = QFrame(objectName="presencePill")
        self.presenca_pill.setProperty("activity", "reconnecting")
        presenca_lay = QHBoxLayout(self.presenca_pill)
        presenca_lay.setContentsMargins(10, 6, 11, 6)
        presenca_lay.setSpacing(7)
        self.ponto = QLabel("●")
        self.ponto.setObjectName("connectionDot")
        self.ponto.setProperty("activity", "reconnecting")
        self.status = QLabel("Reconectando")
        self.status.setObjectName("statusLabel")
        self.status.setProperty("activity", "reconnecting")
        presenca_lay.addWidget(self.ponto)
        presenca_lay.addWidget(self.status)
        hlay.addSpacing(8)
        hlay.addWidget(self.presenca_pill)
        hlay.addStretch(1)
        centro_lay.addWidget(header)

        self.paginas = QStackedWidget()
        conversa = QWidget()
        conversa_lay = QHBoxLayout(conversa)
        conversa_lay.setContentsMargins(
            14, 12, 14, 16
        )
        conversa_lay.setSpacing(12)
        self.chat_surface = QFrame(objectName="chatSurface")
        chat_lay = QVBoxLayout(
            self.chat_surface
        )
        chat_lay.setContentsMargins(
            16, 14, 16, 12
        )
        chat_lay.setSpacing(0)
        self.chat_cabecalho = QFrame(objectName="chatHeader")
        self.chat_cabecalho.setMaximumWidth(920)
        self.chat_cabecalho.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred,
        )
        chat_head_lay = QVBoxLayout(self.chat_cabecalho)
        chat_head_lay.setContentsMargins(
            16, 14, 16, 13
        )
        chat_head_lay.setSpacing(4)
        hora = datetime.now().hour
        saudacao = "Bom dia" if hora < 12 else "Boa tarde" if hora < 18 else "Boa noite"
        self._saudacao_inicio = f"{saudacao}!  ✦"
        self._subtitulo_inicio = "Como posso te ajudar hoje?"
        self.chat_saudacao = QLabel(self._saudacao_inicio)
        self.chat_saudacao.setObjectName("chatGreeting")
        self.chat_subtitulo = QLabel(self._subtitulo_inicio)
        self.chat_subtitulo.setObjectName("chatGreetingSub")
        chat_head_lay.addWidget(self.chat_saudacao)
        chat_head_lay.addWidget(self.chat_subtitulo)
        chat_lay.addWidget(self.chat_cabecalho, 0, Qt.AlignHCenter)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.feed = QWidget()
        self.feed.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.feed_lay = QVBoxLayout(self.feed)
        # O contrato de tamanho precisa acompanhar inserções dinâmicas. Sem esta
        # restrição o QScrollArea conserva a altura do viewport e deixa mensagens
        # reais fora da geometria rolável até uma invalidação posterior.
        self.feed_lay.setSizeConstraint(QLayout.SetMinAndMaxSize)
        self.feed_lay.setContentsMargins(
            24, 28, 24, 22
        )
        self.feed_lay.setSpacing(16)
        self.vazio = QFrame(objectName="emptyState")
        self.vazio.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Minimum)
        vazio_lay = QVBoxLayout(self.vazio)
        vazio_lay.setContentsMargins(32, 50, 32, 50)
        vazio_lay.setSpacing(10)
        vazio_t = QLabel("◕‿◕")
        vazio_t.setObjectName("emptyMark")
        vazio_t.setAlignment(Qt.AlignCenter)
        vazio_h = QLabel("Pode chegar. A mente está do outro lado.")
        vazio_h.setObjectName("emptyTitle")
        vazio_h.setAlignment(Qt.AlignCenter)
        vazio_h.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        vazio_p = QLabel("Converse, peça alguma coisa ou traga aquela bagunça que você chama de ideia.")
        vazio_p.setObjectName("emptyCopy")
        vazio_p.setAlignment(Qt.AlignCenter)
        vazio_p.setWordWrap(True)
        vazio_p.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        vazio_lay.addWidget(vazio_t)
        vazio_lay.addWidget(vazio_h)
        vazio_lay.addWidget(vazio_p)
        self.feed_lay.addStretch()
        self.feed_lay.addWidget(self.vazio)
        self.feed_lay.addStretch()
        self.scroll.setWidget(self.feed)
        self.scroll.verticalScrollBar().sliderPressed.connect(
            self._encerrar_rolagem_suave,
        )
        self._timer_auto_scroll = QTimer(self)
        self._timer_auto_scroll.setSingleShot(True)
        self._timer_auto_scroll.timeout.connect(self._rolar_ao_final)
        chat_lay.addWidget(self.scroll, 1)
        self.voice_surface = QFrame(objectName="voiceSurface")
        voice_lay = QHBoxLayout(self.voice_surface)
        voice_lay.setContentsMargins(18, 12, 18, 12)
        self.voice_dot = QLabel("◉")
        self.voice_dot.setObjectName("voiceDot")
        self.voice_text = QLabel("Ouvindo pelo microfone da Laylay")
        self.voice_text.setObjectName("voiceText")
        voice_lay.addWidget(self.voice_dot)
        voice_lay.addWidget(self.voice_text)
        voice_lay.addStretch()
        self.voice_surface.hide()
        chat_lay.addWidget(self.voice_surface)
        self.waveform = FormaOndaMicrofone(
            reduzir_movimento=self._reduzir_movimento,
        )
        chat_lay.addWidget(self.waveform)
        self.composer = Composer()
        self.composer.setMaximumWidth(920)
        self.composer.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred,
        )
        self.composer.enviar.connect(self.enviar_texto)
        self.composer.enviar.connect(
            lambda _texto: self._animar_microinteracao(
                self.composer.botao,
                opacidade_minima=0.35,
                duracao_retorno=180,
            )
        )
        self.composer.alternar_voz.connect(
            lambda: self.solicitar_modo("voice" if self._modo == "chat" else "chat")
        )
        chat_lay.addWidget(self.composer, 0, Qt.AlignHCenter)
        conversa_lay.addWidget(self.chat_surface, 1)
        self.central_inteligente = PainelCentralInteligente()
        self.central_inteligente.acao_solicitada.connect(
            self.enviar_acao_rapida,
        )
        self.painel_lateral = PainelLateralDashboard()
        self.painel_lateral.acao_solicitada.connect(self.enviar_acao_painel)

        self.inspector_shell = QFrame(objectName="inspectorShell")
        self.inspector_shell.setMinimumWidth(320)
        self.inspector_shell.setMaximumWidth(360)
        inspector_lay = QVBoxLayout(self.inspector_shell)
        inspector_lay.setContentsMargins(14, 16, 14, 14)
        inspector_lay.setSpacing(10)

        inspector_header = QFrame(objectName="inspectorHeader")
        inspector_header_lay = QHBoxLayout(inspector_header)
        inspector_header_lay.setContentsMargins(2, 0, 2, 4)
        inspector_header_lay.setSpacing(8)
        inspector_textos = QVBoxLayout()
        inspector_textos.setContentsMargins(0, 0, 0, 0)
        inspector_textos.setSpacing(2)
        inspector_titulo = QLabel("LAYLAY")
        inspector_titulo.setObjectName("inspectorTitle")
        inspector_subtitulo = QLabel("Contexto em tempo real")
        inspector_subtitulo.setObjectName("inspectorSubtitle")
        inspector_textos.addWidget(inspector_titulo)
        inspector_textos.addWidget(inspector_subtitulo)
        inspector_header_lay.addLayout(inspector_textos)
        inspector_header_lay.addStretch()
        self.inspector_status = QLabel("●")
        self.inspector_status.setObjectName("connectionDot")
        inspector_header_lay.addWidget(self.inspector_status)
        inspector_lay.addWidget(inspector_header)

        self.inspector_scroll = QScrollArea()
        self.inspector_scroll.setObjectName("inspectorScroll")
        self.inspector_scroll.setWidgetResizable(True)
        self.inspector_scroll.setFrameShape(QFrame.NoFrame)
        self.inspector_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inspector_conteudo = QWidget()
        inspector_conteudo.setObjectName("inspectorContent")
        inspector_conteudo_lay = QVBoxLayout(inspector_conteudo)
        inspector_conteudo_lay.setContentsMargins(0, 0, 0, 0)
        inspector_conteudo_lay.setSpacing(10)
        self.central_inteligente.setMinimumWidth(0)
        self.central_inteligente.setMaximumWidth(320)
        self.painel_lateral.setMinimumWidth(0)
        self.painel_lateral.setMaximumWidth(320)
        titulo_central = self.central_inteligente.findChild(
            QLabel, "intelligenceTitle",
        )
        if titulo_central is not None:
            titulo_central.hide()
        self.central_inteligente.estado.hide()
        self.central_inteligente.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Maximum,
        )
        self.painel_lateral.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Maximum,
        )
        inspector_conteudo_lay.addWidget(self.central_inteligente)
        inspector_conteudo_lay.addWidget(self.painel_lateral)
        inspector_conteudo_lay.addStretch()
        self.inspector_scroll.setWidget(inspector_conteudo)
        inspector_lay.addWidget(self.inspector_scroll, 1)
        conversa_lay.addWidget(self.inspector_shell)
        self.paginas.addWidget(conversa)

        atividade = QWidget()
        atividade_lay = QVBoxLayout(atividade)
        atividade_lay.setContentsMargins(54, 42, 68, 50)
        atividade_lay.setSpacing(10)
        ak = QLabel("ATIVIDADE")
        ak.setObjectName("eyebrow")
        at = QLabel("O que acabou de acontecer")
        at.setObjectName("pageTitle")
        ad = QLabel("Eventos úteis desta sessão, sem despejar o ruído interno da mente.")
        ad.setObjectName("pageDescription")
        self.eventos = QTextEdit(readOnly=True)
        self.eventos.setObjectName("eventLog")
        # O painel de atividade é observacional. Um histórico ilimitado faz o
        # QTextDocument relayoutar uma quantidade crescente de HTML a cada
        # evento e degrada a interface depois de sessões longas.
        self.eventos.document().setMaximumBlockCount(240)
        self.eventos.setPlaceholderText("Tudo quieto por enquanto.")
        atividade_lay.addWidget(ak)
        atividade_lay.addWidget(at)
        atividade_lay.addWidget(ad)
        atividade_lay.addSpacing(12)
        atividade_lay.addWidget(self.eventos, 1)
        self.paginas.addWidget(atividade)

        diagnostico = QWidget()
        diag_lay = QVBoxLayout(diagnostico)
        diag_lay.setContentsMargins(54, 42, 68, 50)
        diag_lay.setSpacing(12)
        dk = QLabel("DIAGNÓSTICO")
        dk.setObjectName("eyebrow")
        dt = QLabel("Uma janela limpa para a mente")
        dt.setObjectName("pageTitle")
        dd = QLabel("Aqui só aparecem estados sanitizados. O diagnóstico completo continua sendo produzido pela Laylay.")
        dd.setObjectName("pageDescription")
        dd.setWordWrap(True)
        self.diag_conexao = QLabel("Ponte\nReconectando")
        self.diag_conexao.setObjectName("diagnosticValue")
        self.diag_atividade = QLabel("Atividade\n—")
        self.diag_atividade.setObjectName("diagnosticValue")
        self.diag_modo = QLabel("Interação\nChat")
        self.diag_modo.setObjectName("diagnosticValue")
        pedir = QPushButton("Pedir diagnóstico completo")
        pedir.setObjectName("secondaryButton")
        pedir.clicked.connect(lambda: self.enviar_texto("/diagnostico mente"))
        diag_lay.addWidget(dk)
        diag_lay.addWidget(dt)
        diag_lay.addWidget(dd)
        diag_lay.addSpacing(18)
        for valor in (self.diag_conexao, self.diag_atividade, self.diag_modo):
            diag_lay.addWidget(valor)
        diag_lay.addSpacing(8)
        diag_lay.addWidget(pedir, 0, Qt.AlignLeft)
        diag_lay.addStretch()
        self.paginas.addWidget(diagnostico)

        self.configuracoes = PaginaConfiguracoes()
        self.configuracoes.salvar.connect(self.salvar_configuracoes)
        self.configuracoes.reiniciar.connect(self.reiniciar_laylay)
        self.configuracoes.avatar_alterado.connect(
            self._definir_avatar_usuario
        )
        self.configuracoes.definir_avatar_usuario(
            self._avatar_usuario_path
        )
        self.configuracoes.manter_sidebar.toggled.connect(self._preferencia_sidebar)
        self.paginas.addWidget(self.configuracoes)
        for nome, titulo in (
            ("automacao", "Automação"),
            ("musica", "Música"),
            ("memoria", "Memória"),
            ("sistema", "Sistema"),
            ("desenvolvedor", "Dev Console"),
        ):
            pagina_adiada = PaginaAdiada(titulo)
            self._paginas_adiadas[nome] = pagina_adiada
            self.paginas.addWidget(pagina_adiada)
        centro_lay.addWidget(self.paginas, 1)
        geral.addWidget(centro, 1)
        self.selecionar_pagina("inicio")

    @property
    def pagina_automacao(self) -> PaginaAutomacao:
        return self._garantir_pagina_carregada("automacao")

    @property
    def pagina_musica(self) -> PaginaMusica:
        return self._garantir_pagina_carregada("musica")

    @property
    def pagina_memoria(self) -> PaginaMemoria:
        return self._garantir_pagina_carregada("memoria")

    @property
    def pagina_sistema(self) -> PaginaSistema:
        return self._garantir_pagina_carregada("sistema")

    @property
    def pagina_desenvolvedor(self) -> PaginaDesenvolvedor:
        return self._garantir_pagina_carregada("desenvolvedor")

    def _criar_pagina_adiada(self, nome: str) -> QWidget:
        if nome == "automacao":
            pagina = PaginaAutomacao()
            pagina.acao_solicitada.connect(self.enviar_acao_painel)
            pagina.acao_dados_solicitada.connect(
                self.enviar_acao_painel_com_dados
            )
            return pagina
        if nome == "musica":
            pagina = PaginaMusica(
                definidor_volume_local=DefinidorVolumeMestreWindows(),
            )
            pagina.acao_solicitada.connect(self.enviar_acao_painel)
            pagina.acao_fila_solicitada.connect(
                self.enviar_acao_painel_com_dados,
            )
            pagina.acao_playlist_solicitada.connect(
                self.enviar_requisicao_playlist,
            )
            return pagina
        if nome == "memoria":
            return PaginaMemoria()
        if nome == "sistema":
            pagina = PaginaSistema()
            pagina.acao_solicitada.connect(self.enviar_acao_rapida)
            return pagina
        if nome == "desenvolvedor":
            pagina = PaginaDesenvolvedor()
            pagina.consulta_solicitada.connect(
                self.enviar_consulta_desenvolvedor
            )
            pagina.controle_solicitado.connect(
                self.enviar_controle_desenvolvedor
            )
            pagina.definir_conectada(self._conectado)
            for evento in self._eventos_desenvolvedor:
                pagina.registrar_evento(**evento)
            return pagina
        raise KeyError(f"Página adiada desconhecida: {nome}")

    def _garantir_pagina_carregada(self, nome: str) -> QWidget:
        pagina_existente = self._paginas_carregadas.get(nome)
        if pagina_existente is not None:
            return pagina_existente
        marcador = self._paginas_adiadas.get(nome)
        if marcador is None:
            raise KeyError(f"Página sem marcador de carregamento: {nome}")

        pagina = self._criar_pagina_adiada(nome)
        indice = self.paginas.indexOf(marcador)
        era_atual = self.paginas.currentWidget() is marcador
        self._paginas_carregadas[nome] = pagina
        self._paginas_adiadas.pop(nome, None)
        self._carregamentos_pendentes.discard(nome)
        self.paginas.insertWidget(indice, pagina)
        self.paginas.removeWidget(marcador)
        marcador.deleteLater()
        if era_atual:
            self.paginas.setCurrentWidget(pagina)

        definir_conectada = getattr(pagina, "definir_conectada", None)
        if callable(definir_conectada):
            definir_conectada(self._conectado)
        if self._dashboard_mais_recente:
            aplicar_dashboard = getattr(pagina, "aplicar_dashboard", None)
            if callable(aplicar_dashboard):
                aplicar_dashboard(self._dashboard_mais_recente)
        if nome == "sistema" and self._estado_mais_recente:
            pagina.definir_estado_audio(
                self._modo,
                self._voz_disponivel,
                self._nivel_microfone,
            )
        definir_estado_acao = getattr(pagina, "definir_estado_acao", None)
        if callable(definir_estado_acao):
            for acao_id, (estado, resumo) in self._estados_acoes_ui.items():
                definir_estado_acao(acao_id, estado, resumo)
        if nome == "musica":
            if self._medidor_musica_mais_recente:
                pagina.aplicar_medidor_musica(self._medidor_musica_mais_recente)
            for operacao, resultado, playlist, request_id in (
                self._resultados_playlist_pendentes
            ):
                pagina.detalhe_playlist.aplicar_resultado(
                    operacao,
                    resultado,
                    playlist=playlist,
                    request_id=request_id,
                )
            self._resultados_playlist_pendentes.clear()
        self._registrar_feedback_botoes()
        return pagina

    def _agendar_pagina_ativa(self, nome: str) -> None:
        if nome in self._paginas_carregadas or nome in self._carregamentos_pendentes:
            return
        if nome not in self._paginas_adiadas:
            return
        self._carregamentos_pendentes.add(nome)

        def materializar() -> None:
            self._carregamentos_pendentes.discard(nome)
            if nome != self._pagina_visual_ativa:
                return
            self._garantir_pagina_carregada(nome)

        # Um pequeno intervalo garante que o clique e o indicador lateral sejam
        # compostos antes da construção, especialmente nos 25–42 ms da Música.
        QTimer.singleShot(16, materializar)


    # =====================================================
    # Inicialização visual modular
    # =====================================================

    def _preparar_animacao_inicio(self) -> None:
        if self._reduzir_movimento:
            self._interface_animavel = True
            QTimer.singleShot(
                0,
                lambda: self._sincronizar_indicador_navegacao(
                    self._pagina_visual_ativa,
                    animar=False,
                ),
            )
            return

        self._etapas_inicio = (
            ("Navegação", self.sidebar),
            ("Barra superior", self.topbar),
            ("Chat", self.chat_surface),
            ("Inspector", self.inspector_shell),
        )

        self._efeitos_inicio = []

        for nome, widget in self._etapas_inicio:
            efeito = QGraphicsOpacityEffect(widget)
            efeito.setOpacity(0.08)
            widget.setGraphicsEffect(efeito)
            self._efeitos_inicio.append(
                (nome, widget, efeito)
            )

        self._animacao_inicio_grupo = None

    def _iniciar_animacao_inicio(self) -> None:
        if self._reduzir_movimento:
            return

        efeitos = getattr(
            self,
            "_efeitos_inicio",
            None,
        )

        if not efeitos:
            return

        grupo = QParallelAnimationGroup(self)
        self._animacao_inicio_grupo = grupo

        posicoes_finais: list[tuple[QWidget, QPoint]] = []
        for indice, (_nome, widget, efeito) in enumerate(efeitos):
            posicao_final = widget.pos()
            posicoes_finais.append((widget, posicao_final))
            deslocamento = (
                QPoint(-10, 0)
                if widget is self.sidebar
                else QPoint(0, -8)
                if widget is self.topbar
                else QPoint(0, 12)
            )
            widget.move(posicao_final + deslocamento)

            etapa = QSequentialAnimationGroup(grupo)
            etapa.addPause(indice * 45)
            movimentos = QParallelAnimationGroup(etapa)

            opacidade = QPropertyAnimation(efeito, b"opacity", movimentos)
            opacidade.setDuration(365)
            opacidade.setStartValue(0.08)
            opacidade.setEndValue(1.0)
            opacidade.setEasingCurve(QEasingCurve.OutCubic)

            posicao = QPropertyAnimation(widget, b"pos", movimentos)
            posicao.setDuration(365)
            posicao.setStartValue(posicao_final + deslocamento)
            posicao.setEndValue(posicao_final)
            posicao.setEasingCurve(QEasingCurve.OutCubic)

            movimentos.addAnimation(opacidade)
            movimentos.addAnimation(posicao)
            etapa.addAnimation(movimentos)
            grupo.addAnimation(etapa)

        def finalizar_inicio() -> None:
            for widget, posicao_final in posicoes_finais:
                widget.move(posicao_final)
            for _nome, widget, efeito in list(
                self._efeitos_inicio
            ):
                efeito.setOpacity(1.0)

                if widget.graphicsEffect() is efeito:
                    widget.setGraphicsEffect(None)

            self._efeitos_inicio.clear()
            self._interface_animavel = True
            self._atualizar_pulso_presenca(self._atividade_visual_atual)
            self._sincronizar_indicador_navegacao(
                self._pagina_visual_ativa,
                animar=False,
            )

            if self._animacao_inicio_grupo is grupo:
                self._animacao_inicio_grupo = None

            grupo.deleteLater()

        grupo.finished.connect(
            finalizar_inicio
        )
        grupo.start()

    def _encerrar_transicao_pagina(self) -> None:
        grupo = self._animacao_pagina_grupo
        if grupo is not None:
            grupo.stop()
            grupo.deleteLater()
            self._animacao_pagina_grupo = None
        efeito = self._efeito_pagina
        if efeito is not None:
            pagina = self._pagina_em_transicao
            if pagina is not None and pagina.graphicsEffect() is efeito:
                pagina.setGraphicsEffect(None)
            self._efeito_pagina = None
        self._pagina_em_transicao = None

    def _encerrar_microinteracao_por_id(
        self,
        identificador: int,
        *,
        remover_efeito: bool = True,
        grupo_esperado: QSequentialAnimationGroup | None = None,
    ) -> None:
        registro = self._micro_animacoes.get(identificador)
        if registro is None:
            return
        if grupo_esperado is not None and registro[2] is not grupo_esperado:
            return
        self._micro_animacoes.pop(identificador, None)
        alvo, efeito, grupo = registro
        if _objeto_qt_esta_vivo(grupo):
            grupo.stop()
        if remover_efeito and _objeto_qt_esta_vivo(alvo):
            try:
                if alvo.graphicsEffect() is efeito:
                    alvo.setGraphicsEffect(None)
            except RuntimeError:
                pass
        if _objeto_qt_esta_vivo(grupo):
            grupo.deleteLater()

    def _encerrar_microinteracao(self, widget: QWidget) -> None:
        self._encerrar_microinteracao_por_id(id(widget))

    def _animar_microinteracao(
        self,
        widget: QWidget,
        *,
        opacidade_minima: float = 0.58,
        duracao_retorno: int = 240,
    ) -> None:
        """Dá retorno visual sem deslocar widgets controlados pelo layout."""
        if (
            self._reduzir_movimento
            or not self._interface_animavel
            or widget is None
            or not widget.isVisible()
            or not widget.isEnabled()
        ):
            return
        self._encerrar_microinteracao(widget)
        efeito = QGraphicsOpacityEffect(widget)
        efeito.setOpacity(1.0)
        widget.setGraphicsEffect(efeito)
        grupo = QSequentialAnimationGroup(self)
        descida = QPropertyAnimation(efeito, b"opacity", grupo)
        descida.setDuration(75)
        descida.setStartValue(1.0)
        descida.setEndValue(max(0.25, min(0.9, opacidade_minima)))
        descida.setEasingCurve(QEasingCurve.OutCubic)
        retorno = QPropertyAnimation(efeito, b"opacity", grupo)
        retorno.setDuration(max(100, int(duracao_retorno)))
        retorno.setStartValue(max(0.25, min(0.9, opacidade_minima)))
        retorno.setEndValue(1.0)
        retorno.setEasingCurve(QEasingCurve.OutCubic)
        grupo.addAnimation(descida)
        grupo.addAnimation(retorno)
        identificador = id(widget)
        self._micro_animacoes[identificador] = (widget, efeito, grupo)
        widget.destroyed.connect(
            lambda *_args, chave=identificador, animacao=grupo:
            self._encerrar_microinteracao_por_id(
                chave,
                remover_efeito=False,
                grupo_esperado=animacao,
            )
        )

        def finalizar() -> None:
            self._encerrar_microinteracao_por_id(
                identificador,
                grupo_esperado=grupo,
            )

        grupo.finished.connect(finalizar)
        grupo.start()

    def _encerrar_microinteracoes(self) -> None:
        for identificador in list(self._micro_animacoes):
            self._encerrar_microinteracao_por_id(identificador)

    def _registrar_feedback_botao(self, botao: QWidget) -> None:
        if bool(botao.property("a4FeedbackLigado")):
            return
        if not hasattr(botao, "clicked"):
            return
        botao.setProperty("a4FeedbackLigado", True)
        botao.clicked.connect(
            lambda _marcado=False, alvo=botao: self._animar_microinteracao(
                alvo,
                opacidade_minima=0.78,
                duracao_retorno=110,
            )
        )

    def _registrar_feedback_botoes(self) -> None:
        """Liga feedback aos controles existentes sem alterar sua geometria."""
        for botao in self.findChildren(QWidget):
            if not isinstance(botao, (QPushButton, QToolButton)):
                continue
            if botao is self.composer.botao:
                # O envio já recebe um pulso próprio na A3.
                continue
            self._registrar_feedback_botao(botao)

    def _aplicar_estado_vivo(
        self,
        atividade: str,
        rotulo: str = "",
        emocao: str = "calma",
        *,
        animar: bool = True,
        atualizar_avatar: bool = True,
    ) -> None:
        atividade = str(atividade or "idle").strip().casefold()
        permitidos = {
            "idle", "listening", "thinking", "executing", "speaking",
            "reconnecting", "success", "warning", "error",
        }
        if atividade not in permitidos:
            atividade = "idle"
        rotulos_padrao = {
            "idle": "Pronta",
            "listening": "Ouvindo",
            "thinking": "Pensando",
            "executing": "Executando",
            "speaking": "Falando",
            "reconnecting": "Reconectando",
            "success": "Concluído",
            "warning": "Atenção",
            "error": "Falha",
        }
        texto = str(rotulo or rotulos_padrao[atividade]).strip()
        mudou = atividade != self._estado_vivo_atual or self.status.text() != texto
        self._estado_vivo_atual = atividade

        for widget in (self.presenca_pill, self.ponto, self.status):
            widget.setProperty("activity", atividade)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self.status.setText(texto)
        self.presenca_pill.setToolTip(
            f"{texto} · emoção {str(emocao or 'calma')}"
        )

        self.profile_status.setText(f"●  {texto}")
        self.profile_status.setProperty("state", atividade)
        self.profile_status.style().unpolish(self.profile_status)
        self.profile_status.style().polish(self.profile_status)
        self.marca_status.setText(
            f"{texto.casefold()} · {str(emocao or 'calma')}"
        )

        if atualizar_avatar:
            self.avatar_side.atualizar(atividade, emocao)
            self.avatar_profile.atualizar(atividade, emocao)
            self._atualizar_pulso_presenca(atividade)

        if mudou and animar:
            self._animar_microinteracao(
                self.presenca_pill,
                opacidade_minima=0.62,
                duracao_retorno=180,
            )

    def _restaurar_estado_vivo(self, sequencia: int) -> None:
        if sequencia != self._feedback_vivo_seq:
            return
        if not self._conectado:
            self._aplicar_estado_vivo(
                "reconnecting", "Reconectando", "calma",
                animar=True,
            )
            return
        estado = dict(self._estado_mais_recente or {})
        self._aplicar_estado_vivo(
            str(estado.get("activity") or "idle"),
            str(estado.get("activity_label") or "Pronta"),
            str(estado.get("emotion") or "calma"),
            animar=True,
        )

    def _mostrar_feedback_vivo(
        self,
        atividade: str,
        rotulo: str,
        *,
        duracao_ms: int = 1500,
    ) -> None:
        self._feedback_vivo_seq += 1
        sequencia = self._feedback_vivo_seq
        self._aplicar_estado_vivo(
            atividade,
            rotulo,
            str(self._estado_mais_recente.get("emotion") or "calma"),
            animar=True,
            atualizar_avatar=False,
        )
        QTimer.singleShot(
            max(500, int(duracao_ms)),
            lambda seq=sequencia: self._restaurar_estado_vivo(seq),
        )

    def _parar_pulso_presenca(self) -> None:
        grupo = self._pulso_presenca
        if grupo is not None:
            grupo.stop()
            grupo.deleteLater()
            self._pulso_presenca = None
        efeito = self._efeito_presenca
        if efeito is not None:
            if self.ponto.graphicsEffect() is efeito:
                self.ponto.setGraphicsEffect(None)
            self._efeito_presenca = None

    def _atualizar_pulso_presenca(self, atividade: str) -> None:
        self._atividade_visual_atual = str(atividade or "idle")
        atividades_vivas = {
            "listening", "thinking", "executing", "speaking", "reconnecting",
        }
        if (
            self._reduzir_movimento
            or not self._interface_animavel
            or self._atividade_visual_atual not in atividades_vivas
            or self.isMinimized()
        ):
            self._parar_pulso_presenca()
            return
        if self._pulso_presenca is not None:
            return
        efeito = QGraphicsOpacityEffect(self.ponto)
        efeito.setOpacity(1.0)
        self.ponto.setGraphicsEffect(efeito)
        grupo = QSequentialAnimationGroup(self)
        descer = QPropertyAnimation(efeito, b"opacity", grupo)
        descer.setDuration(620)
        descer.setStartValue(1.0)
        descer.setEndValue(0.34)
        descer.setEasingCurve(QEasingCurve.InOutSine)
        subir = QPropertyAnimation(efeito, b"opacity", grupo)
        subir.setDuration(620)
        subir.setStartValue(0.34)
        subir.setEndValue(1.0)
        subir.setEasingCurve(QEasingCurve.InOutSine)
        grupo.addAnimation(descer)
        grupo.addAnimation(subir)
        grupo.setLoopCount(-1)
        self._efeito_presenca = efeito
        self._pulso_presenca = grupo
        grupo.start()

    def _animar_transicao_pagina(self, pagina: QWidget, direcao: int) -> None:
        """Finaliza a troca sem rasterizar a superfície inteira da página.

        O indicador lateral já oferece continuidade espacial. Aplicar
        QGraphicsOpacityEffect e animar ``pos`` em widgets grandes controlados
        por layout força composição de uma textura do dashboard inteiro e é
        justamente percebido como uma pequena congelada em GPUs mais modestas.
        """
        del direcao
        self._encerrar_transicao_pagina()
        pagina.update()

    def _geometria_indicador_navegacao(self, botao: QPushButton) -> QRect:
        ponto = botao.mapTo(self.sidebar, QPoint(0, 0))
        altura = max(24, min(32, botao.height() - 12))
        topo = ponto.y() + max(0, (botao.height() - altura) // 2)
        return QRect(0, topo, 3, altura)

    def _sincronizar_indicador_navegacao(
        self,
        nome: str,
        *,
        animar: bool,
    ) -> None:
        botao = self._nav.get(nome)
        if botao is None or not botao.isVisible():
            self.indicador_navegacao.hide()
            return
        destino = self._geometria_indicador_navegacao(botao)
        self.indicador_navegacao.raise_()
        if (
            self._reduzir_movimento
            or not animar
            or not self.indicador_navegacao.isVisible()
        ):
            self.indicador_navegacao.setGeometry(destino)
            self.indicador_navegacao.show()
            return
        anterior = self._animacao_indicador_nav
        if anterior is not None:
            anterior.stop()
            anterior.deleteLater()
        movimento = QPropertyAnimation(
            self.indicador_navegacao,
            b"geometry",
            self,
        )
        movimento.setDuration(230)
        movimento.setStartValue(self.indicador_navegacao.geometry())
        movimento.setEndValue(destino)
        movimento.setEasingCurve(QEasingCurve.OutCubic)
        self._animacao_indicador_nav = movimento

        def finalizar() -> None:
            self.indicador_navegacao.setGeometry(destino)
            if self._animacao_indicador_nav is movimento:
                self._animacao_indicador_nav = None
            movimento.deleteLater()

        movimento.finished.connect(finalizar)
        movimento.start()

    def _atalhos(self) -> None:
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self.composer.editor.setFocus)
        QShortcut(QKeySequence("Ctrl+,"), self, activated=lambda: self.selecionar_pagina("configuracoes"))
        QShortcut(QKeySequence("Ctrl+B"), self, activated=self.alternar_sidebar)
        for indice, pagina in enumerate((
            "inicio", "conversa", "automacao", "musica", "memoria", "sistema",
            "configuracoes",
        ), start=1):
            QShortcut(
                QKeySequence(f"Ctrl+{indice}"), self,
                activated=lambda nome=pagina: self.selecionar_pagina(nome),
            )
        ordem_foco = [
            self.nova,
            *self._nav.values(),
            self.config_rodape,
            self.alternador.botoes["chat"],
            self.alternador.botoes["voice"],
            self.composer.microfone,
            self.composer.editor,
            self.composer.botao,
        ]
        for atual, proximo in zip(ordem_foco, ordem_foco[1:]):
            QWidget.setTabOrder(atual, proximo)

    def _estilizar(self) -> None:
        self.setStyleSheet(
            qss_chrome_components()
            + qss_chat_components()
            + qss_system_components()
            + qss_context_components()
            + qss_automation_components()
            + qss_home_refresh()
            + qss_tabs_refresh()
            + qss_settings_refresh()
            + qss_memory_refresh()
            + qss_product_polish()
            + qss_live_presence()
        )

    @staticmethod
    def _horario(instante: object) -> str | None:
        if instante in (None, ""):
            return None
        try:
            if isinstance(instante, (int, float)) or str(instante).replace(".", "", 1).isdigit():
                return datetime.fromtimestamp(float(instante)).strftime("%H:%M")
            return datetime.fromisoformat(str(instante).replace("Z", "+00:00")).astimezone().strftime("%H:%M")
        except (ValueError, TypeError, OSError):
            return None

    def adicionar_mensagem(
        self, papel: str, texto: str, *, timestamp: object = None,
        mensagem_id: str = "", status: str = "accepted",
        rolar_ao_final: bool | None = None, animar: bool = True,
    ) -> MensagemWidget | None:
        texto = str(texto or "").strip()
        if not texto:
            return None
        if mensagem_id:
            for existente in self.feed.findChildren(MensagemWidget):
                if (
                    existente.papel == papel
                    and existente.mensagem_id == mensagem_id
                ):
                    existente.atualizar_texto(texto)
                    self._ultima_mensagem = (papel, texto, time.monotonic())
                    QTimer.singleShot(0, self._ajustar_larguras_mensagens)
                    if rolar_ao_final is not False and self._esta_perto_do_final():
                        self._agendar_rolagem_final()
                    return existente
        agora = time.monotonic()
        anterior_papel, anterior_texto, anterior_ts = self._ultima_mensagem
        if not mensagem_id and papel == anterior_papel and texto == anterior_texto and agora - anterior_ts < 1.5:
            return None
        self._ultima_mensagem = (papel, texto, agora)
        deve_rolar = (
            papel == "user" or self._esta_perto_do_final()
            if rolar_ao_final is None
            else bool(rolar_ao_final)
        )
        if self._feed_em_espera:
            while self.feed_lay.count():
                item = self.feed_lay.takeAt(0)
                self._descartar_item_feed(item)
            self.feed_lay.addStretch()
            self._feed_em_espera = False
        horario_mensagem = self._horario(timestamp)

        mensagem = MensagemWidget(
            papel, texto, horario_mensagem,
            mensagem_id=mensagem_id, status=status,
        )
        mensagem.reenviar.connect(self.reenviar_texto)
        linha_container = QWidget(self.feed)
        linha_container.setObjectName("messageRow")
        linha_container.setProperty(
            "entryDirection",
            "right" if papel == "user" else "left",
        )
        linha_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        linha = QHBoxLayout(linha_container)
        linha.setContentsMargins(0, 0, 0, 0)
        if papel == "user":
            coluna_mensagem = QVBoxLayout()
            coluna_mensagem.setContentsMargins(
                0, 0, 0, 0
            )
            coluna_mensagem.setSpacing(3)

            coluna_mensagem.addWidget(
                mensagem
            )

            if horario_mensagem:
                horario_label = QLabel(
                    horario_mensagem
                )
                horario_label.setObjectName(
                    "messageTime"
                )
                horario_label.setProperty(
                    "owner",
                    "user",
                )
                coluna_mensagem.addWidget(
                    horario_label,
                    0,
                    Qt.AlignRight,
                )

            coluna_mensagem.addWidget(
                mensagem.status,
                0,
                Qt.AlignRight,
            )
            coluna_mensagem.addWidget(
                mensagem.retry,
                0,
                Qt.AlignRight,
            )

            avatar_usuario = AvatarUsuario(
                self._avatar_usuario_path,
                38,
            )

            linha.addStretch(1)
            linha.addLayout(
                coluna_mensagem
            )
            linha.addSpacing(5)
            linha.addWidget(
                avatar_usuario,
                0,
                Qt.AlignTop,
            )

            if self.conversa_atual.text() == "Conversa atual":
                titulo = texto[:34] + ("…" if len(texto) > 34 else "")
                self.conversa_atual.setText(titulo)
                if self._pagina_principal == "conversa":
                    self.titulo_header.setText(titulo)
                    self._atualizar_cabecalho_chat()
        else:
            avatar = AroPresenca(self.raiz, 38)
            avatar.atualizar("idle", "calma")

            coluna_mensagem = QVBoxLayout()
            coluna_mensagem.setContentsMargins(0, 0, 0, 0)
            coluna_mensagem.setSpacing(3)
            coluna_mensagem.addWidget(mensagem)

            if horario_mensagem:
                horario_label = QLabel(horario_mensagem)
                horario_label.setObjectName("messageTime")
                coluna_mensagem.addWidget(
                    horario_label,
                    0,
                    Qt.AlignLeft,
                )

            linha.addWidget(avatar, 0, Qt.AlignTop)
            linha.addSpacing(5)
            linha.addLayout(coluna_mensagem)
            linha.addStretch(1)
        self.feed_lay.insertWidget(
            max(0, self.feed_lay.count() - 1), linha_container,
        )
        self.feed_lay.invalidate()
        self.feed.updateGeometry()
        QTimer.singleShot(0, self._ajustar_larguras_mensagens)
        if animar:
            self._animar_entrada(mensagem, linha_container)
        if deve_rolar:
            self._agendar_rolagem_final()
        return mensagem

    def _ajustar_larguras_mensagens(self) -> None:
        margens = self.feed_lay.contentsMargins()
        disponivel = max(
            180,
            self.scroll.viewport().width() - margens.left() - margens.right() - 4,
        )
        for mensagem in self.feed.findChildren(MensagemWidget):
            # Agora os dois papéis dividem a linha com avatar.
            # Reserva o mesmo espaço dos dois lados para evitar estouro.
            limite_papel = max(
                140,
                disponivel - 60,
            )
            largura = min(int(mensagem.largura_preferida), limite_papel)
            if mensagem.width() != largura:
                mensagem.setFixedWidth(largura)
                mensagem.updateGeometry()
            altura_minima = mensagem.minimumSizeHint().height()
            if mensagem.minimumHeight() != altura_minima:
                mensagem.setMinimumHeight(altura_minima)
        self.feed_lay.invalidate()
        self.feed.updateGeometry()

    def _ajustar_grid_home(self) -> None:
        """Mantém cabeçalho, feed e composer no mesmo eixo em qualquer janela."""
        area = max(0, self.chat_surface.width())
        if area <= 0:
            return

        if area >= 1600:
            alvo = 920
        elif area >= 1250:
            alvo = 880
        elif area >= 1050:
            alvo = 840
        elif area >= 850:
            alvo = 760
        elif area >= 650:
            alvo = area - 80
        else:
            alvo = area - 28
        alvo = max(280, min(920, alvo, area - 16))

        for widget in (
            self.chat_cabecalho,
            self.voice_surface,
            self.waveform,
            self.composer,
        ):
            widget.setFixedWidth(alvo)
            self.chat_surface.layout().setAlignment(widget, Qt.AlignHCenter)

        viewport = max(0, self.scroll.viewport().width())
        largura_feed = min(alvo, max(260, viewport - 16))
        margem = max(8, (viewport - largura_feed) // 2)
        vertical_topo = 18 if self.width() < 760 else 28
        vertical_base = 18 if self.width() < 760 else 22
        self.feed_lay.setContentsMargins(
            margem, vertical_topo, margem, vertical_base,
        )
        self._ajustar_larguras_mensagens()

    def _atualizar_cabecalho_chat(self) -> None:
        """Distingue a Home da conversa sem duplicar a superfície de chat."""
        if self._pagina_principal == "inicio":
            titulo = self._saudacao_inicio
            subtitulo = self._subtitulo_inicio
            modo_conversa = False
        else:
            titulo = str(self.conversa_atual.text() or "").strip()
            if titulo in {"", "Conversa atual", "Nova conversa", "Nenhuma conversa"}:
                titulo = "Conversa"
            subtitulo = "Continue de onde parou com a Laylay."
            modo_conversa = True

        self.chat_saudacao.setText(titulo)
        self.chat_subtitulo.setText(subtitulo)
        self.chat_cabecalho.setProperty("conversationMode", modo_conversa)
        self.chat_cabecalho.style().unpolish(self.chat_cabecalho)
        self.chat_cabecalho.style().polish(self.chat_cabecalho)

    def _esta_perto_do_final(self) -> bool:
        barra = self.scroll.verticalScrollBar()
        return barra.maximum() - barra.value() <= self._limiar_auto_scroll

    def _agendar_rolagem_final(self) -> None:
        """Agrupa relayouts sucessivos e ancora somente uma vez no fim."""
        self._timer_auto_scroll.start(0)

    def _encerrar_rolagem_suave(self) -> None:
        animacao = self._animacao_scroll
        if animacao is None:
            return
        animacao.stop()
        animacao.deleteLater()
        self._animacao_scroll = None

    def _rolar_ao_final(self) -> None:
        barra = self.scroll.verticalScrollBar()
        destino = barra.maximum()
        if (
            self._reduzir_movimento
            or not self._interface_animavel
            or destino <= barra.value() + 2
        ):
            self._encerrar_rolagem_suave()
            barra.setValue(destino)
            return
        self._encerrar_rolagem_suave()
        animacao = QPropertyAnimation(barra, b"value", self)
        animacao.setDuration(190)
        animacao.setStartValue(barra.value())
        animacao.setEndValue(destino)
        animacao.setEasingCurve(QEasingCurve.OutCubic)
        self._animacao_scroll = animacao

        def finalizar() -> None:
            if self._animacao_scroll is animacao:
                self._animacao_scroll = None
                barra.setValue(barra.maximum())
            animacao.deleteLater()

        animacao.finished.connect(finalizar)
        animacao.start()

    def _animar_entrada(
        self,
        mensagem: MensagemWidget,
        container: QWidget,
    ) -> None:
        if (
            self._reduzir_movimento
            or self.feed.graphicsEffect() is not None
        ):
            # QGraphicsEffect em um ancestral e em seu filho força duas
            # composições do mesmo backing store. Durante a transição de
            # conversa, o feed inteiro já está animado; o balão entra junto
            # com ele sem precisar de um segundo efeito concorrente.
            return
        self.feed_lay.activate()
        efeito = QGraphicsOpacityEffect(container)
        efeito.setOpacity(0.10)
        container.setGraphicsEffect(efeito)

        grupo = QParallelAnimationGroup(self)
        opacidade = QPropertyAnimation(efeito, b"opacity", grupo)
        opacidade.setDuration(230)
        opacidade.setStartValue(0.10)
        opacidade.setEndValue(1.0)
        opacidade.setEasingCurve(QEasingCurve.OutCubic)
        grupo.addAnimation(opacidade)
        self._animacoes.append(grupo)

        def finalizar() -> None:
            if grupo in self._animacoes:
                self._animacoes.remove(grupo)
            # Efeitos gráficos persistentes obrigam o Qt a recompor dezenas de
            # pixmaps durante a rolagem e eram a origem do piscar no histórico.
            if container.graphicsEffect() is efeito:
                container.setGraphicsEffect(None)
            grupo.deleteLater()

        grupo.finished.connect(finalizar)
        grupo.start()

    def enviar_texto(self, texto: str) -> None:
        self._enviar_pedido(texto, tipo="chat", acao_id="")

    def enviar_acao_rapida(self, acao_id: str, texto: str) -> None:
        self._enviar_pedido(texto, tipo="quick_action", acao_id=acao_id)

    def enviar_acao_painel(self, acao_id: str, texto: str) -> None:
        self._enviar_pedido(texto, tipo="panel_action", acao_id=acao_id)

    def enviar_acao_painel_com_dados(
        self, acao_id: str, texto: str, payload: dict,
    ) -> None:
        self._enviar_pedido(
            texto, tipo="panel_action", acao_id=acao_id,
            payload_acao=dict(payload or {}),
        )

    def enviar_requisicao_playlist(self, payload: dict) -> None:
        mensagem = {"type": "playlist_request", "id": uuid.uuid4().hex, **dict(payload or {})}
        if not self.worker.enfileirar(mensagem):
            pagina = self._paginas_carregadas.get("musica")
            if pagina is not None:
                pagina.detalhe_playlist.aplicar_resultado(
                    str(payload.get("operation") or ""),
                    {"ok": False, "status": "bridge_unavailable"},
                )

    def _definir_estado_acao_ui(
        self, acao_id: str, estado: str, resumo: str = "",
    ) -> None:
        self._estados_acoes_ui[str(acao_id or "")] = (
            str(estado or ""),
            str(resumo or ""),
        )
        self.central_inteligente.definir_estado_acao(acao_id, estado, resumo)
        self.painel_lateral.definir_estado_acao(acao_id, estado, resumo)
        for nome in ("musica", "automacao"):
            pagina = self._paginas_carregadas.get(nome)
            if pagina is not None:
                pagina.definir_estado_acao(acao_id, estado, resumo)

    def _enviar_pedido(
        self,
        texto: str,
        *,
        tipo: str,
        acao_id: str,
        payload_acao: dict | None = None,
    ) -> None:
        mensagem_id = uuid.uuid4().hex
        acao_direta = tipo == "panel_action"
        if not acao_direta:
            # Um novo pedido reposiciona a única presença efêmera sempre depois
            # da mensagem mais recente, sem acumular indicadores no feed.
            self._remover_indicador_pensando()
            mensagem = self.adicionar_mensagem(
                "user", texto, timestamp=time.time(), mensagem_id=mensagem_id,
                status="pending",
            )
            if mensagem is not None:
                self._envios[mensagem_id] = mensagem
                self._envio_conversa[mensagem_id] = self._conversa_ativa_id
            self._mostrar_indicador_pensando()
        payload = {
            "type": "input_submit", "id": mensagem_id, "text": texto,
            "kind": tipo,
        }
        if not acao_direta and self._conversa_ativa_id:
            payload["conversation_id"] = self._conversa_ativa_id
        if tipo in {"quick_action", "panel_action"}:
            payload["action"] = str(acao_id or "")
            if tipo == "panel_action":
                payload["payload"] = (
                    dict(payload_acao) if payload_acao is not None
                    else self._payload_acao_painel(acao_id, texto)
                )
            self._acoes_por_envio[mensagem_id] = str(acao_id or "")
            self._definir_estado_acao_ui(
                acao_id, "sending", "Enviando para a mente canônica",
            )
        enviado = bool(self.worker.enfileirar(payload))
        if not enviado:
            self._falhar_envio(
                mensagem_id,
                "A ponte ainda não estava pronta para receber a mensagem.",
            )
            return
        if not acao_direta:
            self._armar_timeout_envio(mensagem_id, fase="ack", intervalo_ms=3_500)
        self.adicionar_evento(
            "Mensagem enviada à ponte",
            "Aguardando a confirmação de recebimento da mente.",
            "info",
        )

    @staticmethod
    def _payload_acao_painel(acao_id: str, texto: str) -> dict:
        acao = str(acao_id or "")
        if acao == "media_toggle":
            return {"command": "pause" if str(texto).casefold().startswith("pausa") else "play"}
        if acao in {"playlist_play", "playlist_shuffle"}:
            nome = re.sub(
                r"(?i)^toca\s+a\s+playlist\s+|\s+em\s+modo\s+aleat[oó]rio$",
                "", str(texto or "").strip(),
            ).strip()
            return {"playlist": nome}
        if acao == "volume_set":
            encontrado = re.search(r"\b(\d{1,3})\b", str(texto or ""))
            return {"level": int(encontrado.group(1)) if encontrado else -1}
        return {}

    def _armar_timeout_envio(
        self, mensagem_id: str, *, fase: str, intervalo_ms: int,
    ) -> None:
        self._encerrar_timeout_envio(mensagem_id)
        timeout = QTimer(self)
        timeout.setSingleShot(True)
        timeout.setInterval(max(100, int(intervalo_ms)))
        timeout.timeout.connect(
            lambda mid=mensagem_id: self._expirar_envio(mid)
        )
        self._timeouts_envio[mensagem_id] = timeout
        self._fases_envio[mensagem_id] = str(fase)
        timeout.start()

    def _encerrar_timeout_envio(self, mensagem_id: str) -> None:
        timeout = self._timeouts_envio.pop(str(mensagem_id or ""), None)
        if timeout is not None:
            timeout.stop()
            timeout.deleteLater()
        self._fases_envio.pop(str(mensagem_id or ""), None)

    def _falhar_envio(self, mensagem_id: str, detalhe: str) -> None:
        self._encerrar_timeout_envio(mensagem_id)
        mensagem = self._envios.pop(mensagem_id, None)
        self._envio_conversa.pop(mensagem_id, None)
        if mensagem is not None:
            mensagem.definir_status("failed", detalhe)
        acao_id = self._acoes_por_envio.pop(mensagem_id, "")
        if acao_id:
            self._definir_estado_acao_ui(acao_id, "failed", detalhe)
        self._remover_indicador_pensando()
        self.adicionar_evento("Mensagem não entregue", detalhe, "error")
        self._mostrar_feedback_vivo(
            "error",
            "Falha no envio",
            duracao_ms=1700,
        )

    def _expirar_envio(self, mensagem_id: str) -> None:
        if mensagem_id not in self._envios:
            return
        fase = self._fases_envio.get(mensagem_id)
        self._falhar_envio(
            mensagem_id,
            (
                "A ponte não confirmou o recebimento. Tente novamente."
                if fase == "ack"
                else "A resposta demorou além do limite. Você pode tentar novamente."
            ),
        )

    def _mostrar_indicador_pensando(
        self,
        atividade: str = "thinking",
    ) -> None:
        if self._indicador_pensando is not None:
            self._indicador_pensando.definir_estado(atividade)
            return
        self._encerrar_saida_pensando()
        indicador = IndicadorPensando(
            reduzir_movimento=self._reduzir_movimento,
            atividade=atividade,
        )
        container = QWidget()
        container.setObjectName("thinkingRow")
        linha = QHBoxLayout(container)
        linha.setContentsMargins(0, 0, 0, 0)
        linha.addWidget(indicador)
        linha.addStretch(1)
        self._indicador_pensando = indicador
        self._container_indicador = container
        self.feed_lay.insertWidget(max(0, self.feed_lay.count() - 1), container)
        self.feed_lay.invalidate()
        self.feed.updateGeometry()
        if (
            not self._reduzir_movimento
            and self.feed.graphicsEffect() is None
        ):
            # A troca de conversa pode estar animando o feed inteiro. Não
            # empilhamos um segundo QGraphicsEffect no indicador filho.
            self.feed_lay.activate()
            efeito = QGraphicsOpacityEffect(container)
            efeito.setOpacity(0.12)
            container.setGraphicsEffect(efeito)
            grupo = QParallelAnimationGroup(self)
            opacidade = QPropertyAnimation(efeito, b"opacity", grupo)
            opacidade.setDuration(180)
            opacidade.setStartValue(0.12)
            opacidade.setEndValue(1.0)
            opacidade.setEasingCurve(QEasingCurve.OutCubic)
            grupo.addAnimation(opacidade)
            self._animacao_entrada_pensando = grupo

            def finalizar_entrada() -> None:
                if container.graphicsEffect() is efeito:
                    container.setGraphicsEffect(None)
                if self._animacao_entrada_pensando is grupo:
                    self._animacao_entrada_pensando = None
                grupo.deleteLater()

            grupo.finished.connect(finalizar_entrada)
            grupo.start()
        self._agendar_rolagem_final()

    def _encerrar_saida_pensando(self) -> None:
        grupo = self._animacao_saida_pensando
        container = self._container_saida_pensando
        if grupo is not None:
            grupo.stop()
            grupo.deleteLater()
        self._animacao_saida_pensando = None
        self._container_saida_pensando = None
        if container is not None:
            self.feed_lay.removeWidget(container)
            container.hide()
            container.deleteLater()

    def _remover_indicador_pensando(self, *, animar: bool = False) -> None:
        indicador = self._indicador_pensando
        container = self._container_indicador
        entrada = self._animacao_entrada_pensando
        if entrada is not None:
            entrada.stop()
            entrada.deleteLater()
            self._animacao_entrada_pensando = None
        if container is not None and _objeto_qt_esta_vivo(container):
            # Se a resposta chega antes do fade-in terminar, o grupo é parado,
            # mas o efeito continuava preso ao indicador. Um segundo efeito no
            # balão novo fazia o Qt tentar pintar o mesmo feed duas vezes.
            try:
                if container.graphicsEffect() is not None:
                    container.setGraphicsEffect(None)
            except RuntimeError:
                pass
        self._indicador_pensando = None
        self._container_indicador = None
        if indicador is not None:
            indicador.parar()
        if container is not None:
            if animar and not self._reduzir_movimento and container.isVisible():
                self._encerrar_saida_pensando()
                altura_inicial = max(1, container.height())
                grupo = QParallelAnimationGroup(self)
                altura = QPropertyAnimation(container, b"maximumHeight", grupo)
                altura.setDuration(150)
                altura.setStartValue(altura_inicial)
                altura.setEndValue(0)
                altura.setEasingCurve(QEasingCurve.OutCubic)
                grupo.addAnimation(altura)
                self._animacao_saida_pensando = grupo
                self._container_saida_pensando = container

                def finalizar_saida() -> None:
                    if self._animacao_saida_pensando is grupo:
                        self._animacao_saida_pensando = None
                    if self._container_saida_pensando is container:
                        self._container_saida_pensando = None
                    self.feed_lay.removeWidget(container)
                    container.hide()
                    container.deleteLater()
                    self.feed_lay.invalidate()
                    self.feed.updateGeometry()
                    grupo.deleteLater()

                grupo.finished.connect(finalizar_saida)
                grupo.start()
            else:
                self.feed_lay.removeWidget(container)
                container.hide()
                container.deleteLater()
                self.feed_lay.invalidate()
                self.feed.updateGeometry()

    def reenviar_texto(self, mensagem_id: str, texto: str) -> None:
        anterior = self._envios.pop(mensagem_id, None)
        if anterior is not None:
            anterior.retry.hide()
            anterior.status.setText("Substituída por uma nova tentativa")
        self.enviar_texto(texto)

    def solicitar_modo(self, modo: str) -> None:
        if self._modo_pendente or modo == self._modo:
            self.alternador.definir(self._modo, voz_disponivel=self._voz_disponivel)
            return
        self._modo_pendente = True
        self.alternador.definir(modo, pendente=True, voz_disponivel=self._voz_disponivel)
        self.status.setText("Trocando modo…")
        self.enviar_json.emit({"type": "mode_set", "id": uuid.uuid4().hex, "mode": modo})

    def _definir_avatar_usuario(
        self,
        caminho: str,
    ) -> None:
        caminho = str(
            caminho or ""
        ).strip()

        self._avatar_usuario_path = caminho

        self.preferencias.setValue(
            "user_avatar_path",
            caminho,
        )
        self.preferencias.sync()

        self.configuracoes.definir_avatar_usuario(
            caminho
        )

        for avatar in self.feed.findChildren(
            AvatarUsuario
        ):
            avatar.definir_imagem(
                caminho
            )

    def salvar_configuracoes(self, settings: dict) -> None:
        self.enviar_json.emit({
            "type": "settings_update", "id": uuid.uuid4().hex,
            "settings": settings,
        })

    def _atualizar_status_configuracao(self, settings: dict) -> None:
        provedor = str(settings.get("provider") or "").strip().casefold()
        modelo = str(settings.get("model") or "").strip()
        nomes = {
            "ollama": "Local",
            "portatil": "Portátil",
            "openrouter": "OpenRouter",
        }
        origem = nomes.get(provedor, provedor or "Aguardando")
        self._provedor_modelo = origem
        valor = f"{origem} configurado" if modelo else origem
        if not self._dashboard_recebido:
            self.chip_modelo.definir(
                valor,
                estado="pending" if self._conectado else "error",
            )
            self.central_inteligente.definir_contexto("modo", origem)

    def reiniciar_laylay(self) -> None:
        requisicao_id = uuid.uuid4().hex
        self._reinicio_requisicao_id = requisicao_id
        self.enviar_json.emit({
            "type": "restart_request", "id": requisicao_id,
        })

    def enviar_consulta_desenvolvedor(self, comando: str) -> None:
        pagina = self._paginas_carregadas.get("desenvolvedor")
        if pagina is None:
            return
        requisicao_id = uuid.uuid4().hex
        pagina.registrar_consulta_enviada(requisicao_id, comando)
        self.enviar_json.emit({
            "type": "dev_query",
            "id": requisicao_id,
            "command": str(comando or ""),
        })

    def enviar_controle_desenvolvedor(self, comando: str) -> None:
        pagina = self._paginas_carregadas.get("desenvolvedor")
        if pagina is None:
            return
        comando_limpo = str(comando or "").strip().casefold()
        requisicao_id = uuid.uuid4().hex
        pagina.registrar_controle_enviado(requisicao_id, comando_limpo)
        self.enviar_json.emit({
            "type": "dev_control",
            "id": requisicao_id,
            "command": comando_limpo,
            "authorized": (
                comando_limpo == "tests cancel"
                or comando_limpo.startswith("tests run ")
            ),
        })

    def _receber_eventos_desenvolvedor(self, eventos: object) -> None:
        if not isinstance(eventos, (list, tuple)):
            return
        pagina = self._paginas_carregadas.get("desenvolvedor")
        for bruto in eventos:
            if not isinstance(bruto, dict):
                continue
            evento_id = str(bruto.get("id") or "")
            if evento_id and evento_id in self._ids_eventos_desenvolvedor:
                continue
            if evento_id:
                self._ids_eventos_desenvolvedor.add(evento_id)
            try:
                ocorrido_em = datetime.fromtimestamp(float(bruto.get("timestamp") or 0))
            except (OSError, OverflowError, TypeError, ValueError):
                ocorrido_em = datetime.now()
            evento = {
                "titulo": str(bruto.get("message") or "Evento DEV"),
                "detalhe": "",
                "nivel": str(bruto.get("level") or "info"),
                "categoria": str(bruto.get("category") or "SYSTEM"),
                "ocorrido_em": ocorrido_em,
                "profundidade": str(bruto.get("depth") or "normal"),
                "trace_id": str(bruto.get("trace_id") or ""),
                "origem": str(bruto.get("source") or "runtime"),
                "duracao_ms": bruto.get("duration_ms"),
            }
            self._eventos_desenvolvedor.append(evento)
            if pagina is not None:
                pagina.registrar_evento(**evento)
        del self._eventos_desenvolvedor[:-500]
        if len(self._ids_eventos_desenvolvedor) > 1_000:
            self._ids_eventos_desenvolvedor = {
                str(item.get("id") or "")
                for item in list(eventos)[-500:]
                if isinstance(item, dict) and item.get("id")
            }

    def receber(self, msg: dict) -> None:
        tipo = msg.get("type")
        if tipo == "snapshot":
            mensagens = list(msg.get("messages", []))
            if isinstance(msg.get("conversations"), dict):
                if not str(
                    msg["conversations"].get("active_id") or ""
                ).strip():
                    # A lista pode conter chats antigos, mas nenhum deles foi
                    # escolhido nesta sessão. Não reidrate o histórico legado.
                    mensagens = []
                self._aplicar_retrato_conversas(
                    msg["conversations"], substituir_historico=False,
                )
            elif self._conectado:
                # Compatibilidade com uma ponte antiga. Na ponte C2 o próprio
                # snapshot já é autoritativo; pedir de novo causava uma segunda
                # hidratação do mesmo histórico durante a abertura.
                self.enviar_json.emit({
                    "type": "conversations_get", "id": uuid.uuid4().hex,
                })
            self._substituir_historico(mensagens)
            for evento in msg.get("events", []):
                self.adicionar_evento(evento.get("title", "Evento"), evento.get("detail", ""), evento.get("level", "info"))
            dev_console = msg.get("dev_console")
            if isinstance(dev_console, dict):
                self._receber_eventos_desenvolvedor(
                    dev_console.get("events") or []
                )
            self._atualizar_estado(msg.get("state") or {})
            if isinstance(msg.get("dashboard"), dict):
                self._atualizar_dashboard(msg["dashboard"])
            if isinstance(msg.get("settings"), dict):
                self.configuracoes.preencher(msg["settings"])
                self._atualizar_status_configuracao(msg["settings"])
            self.enviar_json.emit({"type": "ready", "id": uuid.uuid4().hex})
        elif tipo == "assistant_message":
            mensagem_id = str(msg.get("id") or "")
            if mensagem_id not in self._envios and len(self._envios) == 1:
                mensagem_id = next(iter(self._envios))
            conversa_id = str(
                msg.get("conversation_id")
                or self._envio_conversa.get(mensagem_id)
                or self._conversa_ativa_id
            )
            if mensagem_id:
                self._encerrar_timeout_envio(mensagem_id)
                self._envios.pop(mensagem_id, None)
                self._envio_conversa.pop(mensagem_id, None)
            envios_ativos = any(
                cid == self._conversa_ativa_id
                for cid in self._envio_conversa.values()
            )
            if not envios_ativos:
                self._remover_indicador_pensando(animar=True)
            if not conversa_id or conversa_id == self._conversa_ativa_id:
                self.adicionar_mensagem(
                    "assistant", str(msg.get("text") or ""),
                    timestamp=msg.get("timestamp"),
                    mensagem_id=str(msg.get("id") or mensagem_id),
                )
            emocao_resposta = str(msg.get("emotion") or "calma")
            atividade_avatar = str(
                self._estado_mais_recente.get("activity") or "idle"
            )
            self.avatar_side.atualizar(atividade_avatar, emocao_resposta)
            self.avatar_profile.atualizar(atividade_avatar, emocao_resposta)
            self.adicionar_evento(
                "Resposta entregue",
                (
                    "A fala final chegou à conversa."
                    if not conversa_id or conversa_id == self._conversa_ativa_id
                    else "A resposta foi guardada no chat em que o pedido começou."
                ),
                "success",
                categoria="IA",
            )
        elif tipo == "input_ack":
            mensagem_id = str(msg.get("id") or "")
            aceito = bool(msg.get("accepted"))
            if not aceito:
                self._remover_indicador_pensando()
            mensagem = self._envios.get(mensagem_id)
            if mensagem is not None:
                if aceito:
                    mensagem.definir_status("accepted")
                    self._armar_timeout_envio(
                        mensagem_id, fase="resposta", intervalo_ms=75_000,
                    )
                    self.adicionar_evento(
                        "Pedido recebido",
                        "A mente confirmou a entrada e está processando.",
                        "success",
                    )
                else:
                    self._falhar_envio(
                        mensagem_id, str(msg.get("message") or "Pedido recusado."),
                    )
        elif tipo == "state":
            self._atualizar_estado(msg)
            if isinstance(msg.get("event"), dict):
                ev = msg["event"]
                self.adicionar_evento(ev.get("title", "Evento"), ev.get("detail", ""), ev.get("level", "info"))
        elif tipo == "dashboard_state":
            if isinstance(msg.get("dashboard"), dict):
                self._atualizar_dashboard(
                    msg["dashboard"], somente_visivel=True,
                )
        elif tipo == "dev_events":
            self._receber_eventos_desenvolvedor(msg.get("events") or [])
        elif tipo == "dev_query_result":
            pagina_desenvolvedor = self._paginas_carregadas.get("desenvolvedor")
            if pagina_desenvolvedor is not None:
                pagina_desenvolvedor.aplicar_resultado_consulta(msg)
        elif tipo == "dev_control_result":
            pagina_desenvolvedor = self._paginas_carregadas.get("desenvolvedor")
            if pagina_desenvolvedor is not None:
                pagina_desenvolvedor.aplicar_resultado_controle(msg)
        elif tipo == "music_meter":
            self._medidor_musica_mais_recente = dict(msg)
            pagina = self._paginas_carregadas.get("musica")
            if pagina is not None:
                pagina.aplicar_medidor_musica(msg)
        elif tipo == "playlist_result":
            resultado = msg.get("result")
            retrato_resultado = (
                dict(resultado) if isinstance(resultado, dict) else {"ok": False}
            )
            dados_resultado = (
                str(msg.get("operation") or ""),
                retrato_resultado,
                str(msg.get("playlist") or ""),
                str(msg.get("id") or ""),
            )
            pagina = self._paginas_carregadas.get("musica")
            if pagina is not None:
                pagina.detalhe_playlist.aplicar_resultado(
                    dados_resultado[0],
                    dados_resultado[1],
                    playlist=dados_resultado[2],
                    request_id=dados_resultado[3],
                )
            else:
                self._resultados_playlist_pendentes.append(dados_resultado)
                del self._resultados_playlist_pendentes[:-8]
        elif tipo == "conversations_state":
            requisicao_id = str(msg.get("id") or "")
            if requisicao_id == self._requisicao_conversa_id:
                self._requisicao_conversa_id = ""
            sucesso = bool(msg.get("success"))
            retrato = msg.get("conversations")
            if isinstance(retrato, dict):
                self._aplicar_retrato_conversas(
                    retrato,
                    substituir_historico=(
                        sucesso and str(msg.get("action") or "")
                        in {"create", "select", "delete", "list"}
                    ),
                )
            self._definir_controles_conversa(True)
            if sucesso:
                if str(msg.get("action") or "") in {"create", "select", "delete"}:
                    self.selecionar_pagina("conversa")
                    self.composer.editor.setFocus()
                self.adicionar_evento(
                    "Conversas sincronizadas",
                    "A alteração foi confirmada pela memória da Laylay.",
                    "success",
                )
            else:
                self.adicionar_evento(
                    "Conversa não alterada",
                    str(msg.get("message") or "A mente não confirmou a alteração."),
                    "warning",
                )
        elif tipo == "action_state":
            mensagem_id = str(msg.get("id") or "")
            acao_id = str(
                msg.get("action") or self._acoes_por_envio.get(mensagem_id) or ""
            )
            estado_acao = str(msg.get("state") or "")
            resumo = str(msg.get("summary") or "")
            if acao_id:
                self._definir_estado_acao_ui(acao_id, estado_acao, resumo)
            if estado_acao in {
                "awaiting_confirmation", "confirmed", "partial", "failed",
            }:
                self._acoes_por_envio.pop(mensagem_id, None)
                if msg.get("direct") is True:
                    self._encerrar_timeout_envio(mensagem_id)
                    self._envios.pop(mensagem_id, None)
                    if not self._envios:
                        self._remover_indicador_pensando()
                niveis = {
                    "confirmed": "success", "partial": "warning",
                    "failed": "error", "awaiting_confirmation": "info",
                }
                titulos = {
                    "confirmed": "Ação confirmada",
                    "partial": "Ação parcialmente concluída",
                    "failed": "Ação não confirmada",
                    "awaiting_confirmation": "Confirmação necessária",
                }
                self.adicionar_evento(
                    titulos[estado_acao], resumo, niveis[estado_acao],
                    atividade_confirmada=estado_acao == "confirmed",
                    categoria="AUTONOMY",
                )
                feedbacks = {
                    "confirmed": ("success", "Ação concluída"),
                    "partial": ("warning", "Ação parcial"),
                    "failed": ("error", "Ação falhou"),
                    "awaiting_confirmation": ("warning", "Confirmação necessária"),
                }
                feedback_atividade, feedback_rotulo = feedbacks[estado_acao]
                self._mostrar_feedback_vivo(
                    feedback_atividade,
                    feedback_rotulo,
                    duracao_ms=1900 if estado_acao == "awaiting_confirmation" else 1400,
                )
        elif tipo == "mode_state":
            self._modo_pendente = False
            self._modo = str(msg.get("mode") or self._modo)
            self._voz_disponivel = bool(msg.get("voice_available", self._voz_disponivel))
            self._aplicar_modo()
            if not bool(msg.get("success")):
                self.adicionar_evento("Modo mantido", str(msg.get("message") or "A troca não foi confirmada."), "warning")
        elif tipo == "settings_state":
            if isinstance(msg.get("settings"), dict):
                self.configuracoes.preencher(msg["settings"])
                self._atualizar_status_configuracao(msg["settings"])
        elif tipo == "settings_result":
            self.configuracoes.resultado(msg)
            if isinstance(msg.get("settings"), dict):
                self._atualizar_status_configuracao(msg["settings"])
            self.adicionar_evento(
                "Configuração salva" if msg.get("saved") else "Configuração recusada",
                str(msg.get("message") or ""), "success" if msg.get("saved") else "error",
            )
        elif tipo == "restart_result":
            self._reinicio_requisicao_id = ""
            self.configuracoes.resultado_reinicio(msg)
            self.adicionar_evento(
                "Reinício solicitado" if msg.get("accepted") else "Reinício recusado",
                str(msg.get("message") or ""),
                "success" if msg.get("accepted") else "error",
            )
        elif tipo == "error":
            self._remover_indicador_pensando()
            if self._modo_pendente:
                self._modo_pendente = False
                self._aplicar_modo()
            mensagem_id = str(msg.get("id") or "")
            if mensagem_id and mensagem_id == self._reinicio_requisicao_id:
                self._reinicio_requisicao_id = ""
                self.configuracoes.resultado_reinicio({
                    "accepted": False,
                    "message": str(msg.get("message") or "Não consegui enviar o reinício."),
                })
            mensagem = self._envios.get(mensagem_id)
            if mensagem is not None:
                self._falhar_envio(
                    mensagem_id, str(msg.get("message") or "Erro desconhecido"),
                )
            self.adicionar_evento("A ponte recusou uma ação", str(msg.get("message") or "Erro desconhecido"), "error")

    def _atualizar_dashboard(
        self,
        dashboard: dict,
        *,
        somente_visivel: bool = False,
    ) -> None:
        if dashboard.get("schema_version") != 1:
            return
        self._dashboard_mais_recente = dict(dashboard)
        self._dashboard_recebido = True
        saude = dashboard.get("health")
        if not isinstance(saude, dict):
            saude = {}
        llm = saude.get("llm") if isinstance(saude.get("llm"), dict) else {}
        estado_llm = str(llm.get("state") or "unavailable")
        provedor = str(llm.get("provider_label") or self._provedor_modelo or "Modelo")
        rotulo_llm = str(llm.get("label") or "Indisponível")
        frescor_llm = str(llm.get("freshness") or "unavailable")
        if frescor_llm == "stale":
            rotulo_llm += " · antigo"
        cor_llm = {
            "online": "online",
            "ready": "pending",
            "degraded": "error",
            "unavailable": "unavailable",
        }.get(estado_llm, "pending")
        if frescor_llm == "stale":
            cor_llm = "pending"
        elif frescor_llm == "unavailable":
            cor_llm = "unavailable"
        self.chip_modelo.definir(f"{provedor} · {rotulo_llm}", estado=cor_llm)
        modelo = str(llm.get("model") or "").strip()
        self.chip_modelo.setToolTip(
            f"Modelo observado: {modelo}" if modelo else "Modelo não informado pelo runtime"
        )

        memoria = (
            saude.get("memory") if isinstance(saude.get("memory"), dict) else {}
        )
        estado_memoria = str(memoria.get("state") or "unavailable")
        rotulo_memoria = str(memoria.get("label") or "Indisponível")
        frescor_memoria = str(memoria.get("freshness") or "unavailable")
        if frescor_memoria == "stale":
            rotulo_memoria += " · antiga"
        cor_memoria = {
            "online": "online",
            "degraded": "error",
            "unavailable": "unavailable",
        }.get(estado_memoria, "pending")
        if frescor_memoria == "stale":
            cor_memoria = "pending"
        elif frescor_memoria == "unavailable":
            cor_memoria = "unavailable"
        self.chip_memoria.definir(rotulo_memoria, estado=cor_memoria)

        microfone = (
            saude.get("microphone")
            if isinstance(saude.get("microphone"), dict) else {}
        )
        estado_microfone = str(microfone.get("state") or "unavailable")
        rotulo_microfone = str(microfone.get("label") or "Indisponível")
        frescor_microfone = str(
            microfone.get("freshness") or "unavailable"
        )
        if frescor_microfone == "stale":
            rotulo_microfone += " · antigo"
        cor_microfone = {
            "online": "online",
            "paused": "pending",
            "degraded": "error",
            "unavailable": "unavailable",
        }.get(estado_microfone, "pending")
        if frescor_microfone == "stale":
            cor_microfone = "pending"
        elif frescor_microfone == "unavailable":
            cor_microfone = "unavailable"
        self.chip_microfone.definir(rotulo_microfone, estado=cor_microfone)
        if somente_visivel:
            self._aplicar_dashboard_pagina(
                self._pagina_visual_ativa,
                dashboard,
            )
            return
        for nome in (
            "inicio", "automacao", "musica", "memoria", "sistema",
            "desenvolvedor",
        ):
            self._aplicar_dashboard_pagina(nome, dashboard)

    def _aplicar_dashboard_pagina(
        self,
        nome: str,
        dashboard: dict,
    ) -> None:
        if nome == "inicio":
            self.central_inteligente.aplicar_dashboard(dashboard)
            self.painel_lateral.aplicar_dashboard(dashboard)
            return
        pagina = self._paginas_carregadas.get(nome)
        if pagina is not None:
            pagina.aplicar_dashboard(dashboard)
        elif nome == self._pagina_visual_ativa:
            self._agendar_pagina_ativa(nome)

    def _aplicar_dashboard_pagina_se_ativa(self, nome: str) -> None:
        if nome != self._pagina_visual_ativa:
            return
        if self._dashboard_mais_recente:
            self._aplicar_dashboard_pagina(
                nome,
                self._dashboard_mais_recente,
            )

    def _atualizar_estado(self, estado: dict) -> None:
        self._estado_mais_recente = dict(estado or {})
        atividade = str(estado.get("activity") or "idle")
        rotulo = str(estado.get("activity_label") or "Pronta")
        emocao = str(estado.get("emotion") or "calma")
        self._modo = str(estado.get("interaction_mode") or self._modo)
        self._voz_disponivel = bool(estado.get("voice_available", False))
        try:
            self._nivel_microfone = float(estado.get("microphone_level") or 0.0)
        except (TypeError, ValueError):
            self._nivel_microfone = 0.0

        pagina_sistema = self._paginas_carregadas.get("sistema")
        if pagina_sistema is not None:
            pagina_sistema.definir_estado_audio(
                self._modo,
                self._voz_disponivel,
                self._nivel_microfone,
            )

        if not self._dashboard_recebido:
            if not self._voz_disponivel:
                self.chip_microfone.definir("Indisponível", estado="unavailable")
            elif self._modo == "voice":
                self.chip_microfone.definir("Ativo", estado="online")
            else:
                self.chip_microfone.definir("Pausado no chat", estado="pending")
        self._feedback_vivo_seq += 1
        self._assinatura_microestado = f"{atividade}:{rotulo}"
        self._aplicar_estado_vivo(
            atividade,
            rotulo,
            emocao,
            animar=True,
        )
        self.diag_atividade.setText(f"Atividade\n{rotulo} · emoção {emocao}")
        if atividade in {"thinking", "executing"} and self._envios:
            self._mostrar_indicador_pensando(atividade)
        assinatura_atividade = f"{atividade}:{rotulo}:{emocao}"
        if (
            atividade in {"thinking", "executing", "speaking", "listening", "reconnecting"}
            and assinatura_atividade != self._ultima_atividade_evento
        ):
            self._ultima_atividade_evento = assinatura_atividade
            categorias_atividade = {
                "thinking": "IA",
                "speaking": "IA",
                "executing": "AUTONOMY",
                "listening": "EVENTS",
                "reconnecting": "SYSTEM",
            }
            self.adicionar_evento(
                rotulo,
                f"Estado da mente · emoção {emocao}.",
                "info",
                categoria=categorias_atividade.get(atividade, "SYSTEM"),
            )
        self.configuracoes.definir_voz(self._voz_disponivel)
        self._aplicar_modo()

    def _aplicar_modo(self) -> None:
        self.alternador.definir(
            self._modo, pendente=self._modo_pendente,
            voz_disponivel=self._voz_disponivel,
        )
        modo_visual = f"{self._modo}:{self._modo_pendente}:{self._voz_disponivel}"
        if self._modo_visual_anterior and modo_visual != self._modo_visual_anterior:
            self._animar_microinteracao(
                self.alternador,
                opacidade_minima=0.48,
                duracao_retorno=220,
            )
        self._modo_visual_anterior = modo_visual
        self.composer.definir_estado(conectado=self._conectado, modo=self._modo)
        self.waveform.definir_nivel(
            self._nivel_microfone,
            ativo=self._conectado and self._voz_disponivel and self._modo == "voice",
        )
        self.voice_surface.setVisible(self._modo == "voice")
        self.voice_text.setText(
            "Ouvindo pelo microfone da Laylay" if self._voz_disponivel
            else "Ouvido indisponível — volte ao Chat para continuar"
        )
        if not self._conectado:
            self.chip_microfone.definir("Sem ponte", estado="unavailable")
        elif not self._dashboard_recebido:
            if not self._voz_disponivel:
                self.chip_microfone.definir("Indisponível", estado="unavailable")
            elif self._modo == "voice":
                self.chip_microfone.definir("Ativo", estado="online")
            else:
                self.chip_microfone.definir("Pausado no chat", estado="pending")
        self.diag_modo.setText(
            f"Interação\n{'Voz' if self._modo == 'voice' else 'Chat'} · "
            f"ouvido {'disponível' if self._voz_disponivel else 'indisponível'}"
        )

    def estado_conexao(self, conectado: bool) -> None:
        self._conectado = conectado
        if not conectado:
            self._requisicao_conversa_id = ""
        self._definir_controles_conversa(conectado)
        self.central_inteligente.definir_conectada(conectado)
        self.painel_lateral.definir_conectada(conectado)
        for nome in ("automacao", "musica", "desenvolvedor"):
            pagina = self._paginas_carregadas.get(nome)
            if pagina is not None:
                pagina.definir_conectada(conectado)
        self.configuracoes.definir_conectada(conectado)
        cor_conexao = PALETA["sucesso"] if conectado else PALETA["erro"]
        self.inspector_status.setStyleSheet(f"color: {cor_conexao};")
        self.status_mente.setText("●  Mente conectada" if conectado else "●  Reconectando")
        self._feedback_vivo_seq += 1
        if conectado:
            estado_vivo = dict(self._estado_mais_recente or {})
            self._aplicar_estado_vivo(
                str(estado_vivo.get("activity") or "idle"),
                str(estado_vivo.get("activity_label") or "Pronta"),
                str(estado_vivo.get("emotion") or "calma"),
                animar=True,
            )
        else:
            self._aplicar_estado_vivo(
                "reconnecting",
                "Reconectando",
                "calma",
                animar=True,
            )
        if conectado and not self._dashboard_recebido:
            self.chip_modelo.definir(
                f"{self._provedor_modelo} configurado"
                if self._provedor_modelo else "Aguardando estado",
                estado="pending",
            )
        else:
            if not conectado:
                self._dashboard_recebido = False
                self._dashboard_mais_recente = {}
                self._medidor_musica_mais_recente = {}
                self.chip_modelo.definir("Sem ponte", estado="error")
                self.chip_memoria.definir("Reconectando", estado="unavailable")
                self.central_inteligente.invalidar_dashboard()
                self.painel_lateral.invalidar_dashboard()
                for nome, pagina in self._paginas_carregadas.items():
                    if nome == "musica":
                        pagina.invalidar("Reconectando ao player")
                    else:
                        pagina.invalidar()
        if conectado and not self._dashboard_recebido:
            self.chip_memoria.definir("Aguardando", estado="pending")
        identidade = (
            f" · sessão {self._session_id} · PID {self._parent_pid}"
            if self._session_id else ""
        )
        self.diag_conexao.setText(
            ("Ponte\nConectada e autenticada" if conectado else "Ponte\nReconectando")
            + identidade
        )
        self._aplicar_modo()
        if conectado:
            self.adicionar_evento("Mente conectada", "A interface e o núcleo estão sincronizados.", "success")
            self.enviar_json.emit({"type": "settings_get", "id": uuid.uuid4().hex})
        else:
            self._remover_indicador_pensando()
            self.adicionar_evento("Reconectando", "A interface perdeu a ponte temporariamente.", "warning")
            for mensagem_id in tuple(self._envios):
                self._falhar_envio(
                    mensagem_id,
                    "A conexão caiu antes de confirmar o recebimento.",
                )

    def falha_conexao(self, detalhe: str) -> None:
        self.adicionar_evento("Conexão interrompida", detalhe, "warning")

    def adicionar_evento(
        self,
        titulo: str,
        detalhe: str = "",
        nivel: str = "info",
        *,
        atividade_confirmada: bool = False,
        categoria: str = "",
    ) -> None:
        evento_desenvolvedor = {
            "titulo": str(titulo or ""),
            "detalhe": str(detalhe or ""),
            "nivel": str(nivel or "info"),
            "categoria": str(categoria or ""),
            "ocorrido_em": datetime.now(),
        }
        self._eventos_desenvolvedor.append(evento_desenvolvedor)
        del self._eventos_desenvolvedor[:-500]
        pagina_desenvolvedor = self._paginas_carregadas.get("desenvolvedor")
        if pagina_desenvolvedor is not None:
            pagina_desenvolvedor.registrar_evento(**evento_desenvolvedor)
        cores = {"error": PALETA["erro"], "warning": PALETA["rosa"], "success": PALETA["sucesso"], "info": PALETA["ciano"]}
        self.eventos.append(
            f'<span style="color:{cores.get(nivel, PALETA["ciano"])}">{time.strftime("%H:%M")}  {titulo}</span>'
            f'<br><span style="color:{PALETA["secundario"]}">{detalhe}</span><br>'
        )
        if atividade_confirmada:
            self.central_inteligente.registrar_evento(titulo)

    @classmethod
    def _descartar_item_feed(cls, item) -> None:
        """Remove recursivamente linhas antigas, inclusive layouts sem contêiner."""
        widget = item.widget()
        if widget is not None:
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()
            return
        layout = item.layout()
        if layout is None:
            return
        while layout.count():
            cls._descartar_item_feed(layout.takeAt(0))
        layout.invalidate()
        layout.deleteLater()

    def _encerrar_animacoes_mensagens(self) -> None:
        for grupo in list(self._animacoes):
            grupo.stop()
            grupo.deleteLater()
        self._animacoes.clear()

    def _encerrar_transicao_conversa(self) -> None:
        grupo = self._animacao_troca_conversa
        if grupo is not None:
            grupo.stop()
            grupo.deleteLater()
            self._animacao_troca_conversa = None
        efeito = self._efeito_troca_conversa
        if efeito is not None and self.feed.graphicsEffect() is efeito:
            self.feed.setGraphicsEffect(None)
        self._efeito_troca_conversa = None

    def _animar_entrada_conversa(self) -> None:
        if self._reduzir_movimento or not self._interface_animavel:
            return
        self._encerrar_transicao_conversa()
        self.feed_lay.activate()
        efeito = QGraphicsOpacityEffect(self.feed)
        efeito.setOpacity(0.10)
        self.feed.setGraphicsEffect(efeito)
        grupo = QParallelAnimationGroup(self)
        opacidade = QPropertyAnimation(efeito, b"opacity", grupo)
        opacidade.setDuration(230)
        opacidade.setStartValue(0.10)
        opacidade.setEndValue(1.0)
        opacidade.setEasingCurve(QEasingCurve.OutCubic)
        grupo.addAnimation(opacidade)
        self._animacao_troca_conversa = grupo
        self._efeito_troca_conversa = efeito

        def finalizar() -> None:
            if self.feed.graphicsEffect() is efeito:
                self.feed.setGraphicsEffect(None)
            if self._animacao_troca_conversa is grupo:
                self._animacao_troca_conversa = None
            if self._efeito_troca_conversa is efeito:
                self._efeito_troca_conversa = None
            grupo.deleteLater()

        grupo.finished.connect(finalizar)
        grupo.start()

    def _limpar_historico_visual(self) -> None:
        self._encerrar_animacoes_mensagens()
        self._encerrar_transicao_conversa()
        self._remover_indicador_pensando()
        self._encerrar_saida_pensando()
        while self.feed_lay.count():
            item = self.feed_lay.takeAt(0)
            self._descartar_item_feed(item)
        self._ultima_mensagem = ("", "", 0.0)

    def _mostrar_conversa_vazia(self) -> None:
        self._limpar_historico_visual()
        self.vazio = QFrame(objectName="emptyState")
        self.vazio.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Minimum)
        lay = QVBoxLayout(self.vazio)
        titulo = QLabel("◕‿◕  Conversa nova, memória global intacta.")
        titulo.setObjectName("emptyTitle")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        texto = QLabel("Este chat começa sem referências nem assunto anterior.")
        texto.setObjectName("emptyCopy")
        texto.setAlignment(Qt.AlignCenter)
        texto.setWordWrap(True)
        texto.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        lay.addWidget(titulo)
        lay.addWidget(texto)
        self.feed_lay.addStretch()
        self.feed_lay.addWidget(self.vazio)
        self.feed_lay.addStretch()
        self._feed_em_espera = True

    def _substituir_historico(
        self,
        mensagens: list[dict],
        *,
        animar: bool = False,
    ) -> None:
        self._limpar_historico_visual()
        self._feed_em_espera = True
        validas = [item for item in mensagens if isinstance(item, dict)]
        if not validas:
            self._mostrar_conversa_vazia()
            if animar:
                self._animar_entrada_conversa()
            return
        for item in validas:
            self.adicionar_mensagem(
                str(item.get("role") or "assistant"),
                str(item.get("content") or ""),
                timestamp=item.get("timestamp"),
                rolar_ao_final=False,
                animar=False,
            )
        self._agendar_rolagem_final()
        if animar:
            self._animar_entrada_conversa()

    def _encerrar_animacoes_conversas(self) -> None:
        for grupo in list(self._animacoes_conversas):
            grupo.stop()
            grupo.deleteLater()
        self._animacoes_conversas.clear()

    def _animar_nova_conversa_lateral(self, linha: QWidget) -> None:
        if self._reduzir_movimento or not self._interface_animavel:
            return
        self.conversas_lay.activate()
        altura_final = max(34, linha.sizeHint().height())
        efeito = QGraphicsOpacityEffect(linha)
        efeito.setOpacity(0.08)
        linha.setGraphicsEffect(efeito)
        linha.setMaximumHeight(0)
        grupo = QParallelAnimationGroup(self)
        opacidade = QPropertyAnimation(efeito, b"opacity", grupo)
        opacidade.setDuration(210)
        opacidade.setStartValue(0.08)
        opacidade.setEndValue(1.0)
        opacidade.setEasingCurve(QEasingCurve.OutCubic)
        altura = QPropertyAnimation(linha, b"maximumHeight", grupo)
        altura.setDuration(250)
        altura.setStartValue(0)
        altura.setEndValue(altura_final)
        altura.setEasingCurve(QEasingCurve.OutCubic)
        grupo.addAnimation(opacidade)
        grupo.addAnimation(altura)
        self._animacoes_conversas.append(grupo)

        def finalizar() -> None:
            linha.setMaximumHeight(16_777_215)
            if linha.graphicsEffect() is efeito:
                linha.setGraphicsEffect(None)
            if grupo in self._animacoes_conversas:
                self._animacoes_conversas.remove(grupo)
            grupo.deleteLater()

        grupo.finished.connect(finalizar)
        grupo.start()

    def _definir_controles_conversa(self, habilitados: bool) -> None:
        ativo = bool(habilitados and self._conectado)
        self.nova.setEnabled(ativo)
        for conversa_id, botao in self._botoes_conversas.items():
            conversa = next(
                (
                    item for item in self._conversas
                    if str(item.get("id") or "") == conversa_id
                ),
                {},
            )
            botao.setEnabled(
                ativo and str(conversa.get("status") or "active") == "active"
            )
        for botao in self._menus_conversas.values():
            botao.setEnabled(ativo)

    @staticmethod
    def _normalizar_busca_conversa(texto: object) -> str:
        bruto = unicodedata.normalize("NFKD", str(texto or "").casefold())
        sem_acentos = "".join(
            caractere for caractere in bruto
            if not unicodedata.combining(caractere)
        )
        return re.sub(r"\s+", " ", sem_acentos).strip()

    def _filtrar_conversas(self, texto: str) -> None:
        self._filtro_conversas = self._normalizar_busca_conversa(texto)
        self._renderizar_lista_conversas()

    def _alternar_conversas_arquivadas(self, mostrar: bool) -> None:
        self._mostrar_arquivadas = bool(mostrar)
        self.botao_arquivadas.setToolTip(
            "Ocultar conversas arquivadas"
            if mostrar else "Mostrar conversas arquivadas"
        )
        self._renderizar_lista_conversas()

    def _adicionar_secao_conversas(self, texto: str) -> None:
        rotulo = QLabel(texto, self.conversas_container)
        rotulo.setObjectName("conversationSection")
        self.conversas_lay.addWidget(rotulo)

    def _renderizar_lista_conversas(
        self,
        *,
        ids_anteriores: set[str] | None = None,
    ) -> None:
        ids_anteriores = set(ids_anteriores or {
            str(item.get("id") or "") for item in self._conversas
            if isinstance(item, dict)
        })
        ativa = self._conversa_ativa_id
        consulta = self._filtro_conversas
        filtradas = [
            conversa for conversa in self._conversas
            if not consulta or consulta in self._normalizar_busca_conversa(
                conversa.get("title"),
            )
        ]
        ativas = [
            conversa for conversa in filtradas
            if str(conversa.get("status") or "active") == "active"
        ]
        fixadas = [conversa for conversa in ativas if conversa.get("pinned")]
        recentes = [conversa for conversa in ativas if not conversa.get("pinned")]
        arquivadas = [
            conversa for conversa in filtradas
            if str(conversa.get("status") or "") == "archived"
            and (self._mostrar_arquivadas or bool(consulta))
        ]

        self._encerrar_animacoes_conversas()
        for botao in (
            *self._botoes_conversas.values(),
            *self._menus_conversas.values(),
        ):
            self._encerrar_microinteracao_por_id(id(botao))
        while self.conversas_lay.count():
            item_layout = self.conversas_lay.takeAt(0)
            if item_layout.widget() is not None:
                item_layout.widget().deleteLater()
        self._botoes_conversas.clear()
        self._menus_conversas.clear()

        grupos = (
            ("FIXADAS", fixadas),
            ("RECENTES", recentes),
            ("ARQUIVADAS", arquivadas),
        )
        exibidas = 0
        for secao, conversas in grupos:
            if not conversas:
                continue
            self._adicionar_secao_conversas(secao)
            for conversa in conversas:
                conversa_id = str(conversa.get("id") or "")
                titulo = str(conversa.get("title") or "Nova conversa")
                arquivada = str(conversa.get("status") or "") == "archived"
                fixada = bool(conversa.get("pinned"))
                linha = QFrame(self.conversas_container)
                linha.setObjectName("conversationRow")
                linha.setProperty("active", conversa_id == ativa)
                linha.setProperty("archived", arquivada)
                lay = QHBoxLayout(linha)
                lay.setContentsMargins(2, 1, 2, 1)
                lay.setSpacing(2)
                botao = QPushButton(
                    f"★  {titulo}" if fixada and not arquivada else titulo,
                    linha,
                )
                botao.setObjectName("conversationItem")
                botao.setProperty("archived", arquivada)
                botao.setCheckable(True)
                botao.setChecked(conversa_id == ativa)
                botao.setToolTip(
                    f"{titulo} · arquivada" if arquivada else titulo
                )
                botao.setAccessibleName(
                    f"Conversa arquivada {titulo}"
                    if arquivada else f"Abrir conversa {titulo}"
                )
                botao.setEnabled(not arquivada)
                botao.clicked.connect(
                    lambda _v=False, cid=conversa_id:
                    self.selecionar_conversa(cid)
                )
                menu = QToolButton(linha)
                menu.setObjectName("conversationMenu")
                menu.setText("⋯")
                menu.setToolTip(f"Opções de {titulo}")
                menu.setAccessibleName(f"Opções da conversa {titulo}")
                menu.clicked.connect(
                    lambda _v=False, cid=conversa_id, nome=titulo,
                    dados=dict(conversa), origem=menu:
                    self._abrir_menu_conversa(cid, nome, dados, origem)
                )
                self._registrar_feedback_botao(botao)
                self._registrar_feedback_botao(menu)
                lay.addWidget(botao, 1)
                lay.addWidget(menu)
                self.conversas_lay.addWidget(linha)
                self._botoes_conversas[conversa_id] = botao
                self._menus_conversas[conversa_id] = menu
                exibidas += 1
                if conversa_id not in ids_anteriores:
                    self._animar_nova_conversa_lateral(linha)
        if not exibidas:
            vazio = QLabel(
                "Nenhuma conversa encontrada"
                if consulta else "Nenhuma conversa nesta seção",
                self.conversas_container,
            )
            vazio.setObjectName("conversationEmpty")
            self.conversas_lay.addWidget(vazio)
        self.conversas_lay.addStretch(1)
        visivel = self._sidebar_expandida and bool(self._conversas)
        self.recentes_label.setVisible(visivel)
        self.ferramentas_conversas.setVisible(visivel)
        self.conversas_scroll.setVisible(visivel)
        self._definir_controles_conversa(not self._requisicao_conversa_id)

    def _aplicar_retrato_conversas(
        self,
        retrato: dict,
        *,
        substituir_historico: bool,
    ) -> None:
        if not isinstance(retrato, dict) or not retrato.get("available"):
            return
        ids_anteriores = {
            str(item.get("id") or "") for item in self._conversas
            if isinstance(item, dict)
        }
        ativa = str(retrato.get("active_id") or "")
        itens = [
            dict(item) for item in list(retrato.get("items") or [])
            if isinstance(item, dict) and str(item.get("id") or "")
        ]
        self._conversa_ativa_id = ativa
        self._conversas = itens
        titulo_ativo = "Nenhuma conversa" if not ativa else "Nova conversa"
        for conversa in itens:
            if str(conversa.get("id") or "") == ativa:
                titulo_ativo = str(conversa.get("title") or "Nova conversa")
                break
        self._renderizar_lista_conversas(ids_anteriores=ids_anteriores)
        self.conversa_atual.setText(titulo_ativo)
        if self._pagina_principal == "conversa":
            self.titulo_header.setText(titulo_ativo)
            self._atualizar_cabecalho_chat()
        if substituir_historico and isinstance(retrato.get("messages"), list):
            self._substituir_historico(
                list(retrato["messages"]),
                animar=True,
            )

    def _enviar_requisicao_conversa(self, tipo: str, **dados: object) -> None:
        if not self._conectado or self._requisicao_conversa_id:
            return
        requisicao_id = uuid.uuid4().hex
        self._requisicao_conversa_id = requisicao_id
        self._definir_controles_conversa(False)
        self.enviar_json.emit({"type": tipo, "id": requisicao_id, **dados})

    def nova_conversa(self) -> None:
        self._enviar_requisicao_conversa(
            "conversation_create", title="Nova conversa",
        )

    def selecionar_conversa(self, conversa_id: str) -> None:
        identificador = str(conversa_id or "")
        if not identificador or identificador == self._conversa_ativa_id:
            self.selecionar_pagina("conversa")
            return
        self._enviar_requisicao_conversa(
            "conversation_select", conversation_id=identificador,
        )

    def fixar_conversa(self, conversa_id: str, fixada: bool) -> None:
        self._enviar_requisicao_conversa(
            "conversation_pin",
            conversation_id=str(conversa_id or ""),
            pinned=bool(fixada),
        )

    def arquivar_conversa(self, conversa_id: str) -> None:
        self._enviar_requisicao_conversa(
            "conversation_archive",
            conversation_id=str(conversa_id or ""),
        )

    def restaurar_conversa(self, conversa_id: str) -> None:
        self._enviar_requisicao_conversa(
            "conversation_unarchive",
            conversation_id=str(conversa_id or ""),
        )

    def _abrir_menu_conversa(
        self,
        conversa_id: str,
        titulo: str,
        conversa: dict,
        origem: QWidget,
    ) -> None:
        menu = QMenu(self)
        arquivada = str(conversa.get("status") or "active") == "archived"
        fixada = bool(conversa.get("pinned"))
        if arquivada:
            restaurar = QAction("Restaurar conversa", menu)
            restaurar.triggered.connect(
                lambda: self.restaurar_conversa(conversa_id)
            )
            menu.addAction(restaurar)
        else:
            fixar = QAction("Desafixar" if fixada else "Fixar", menu)
            fixar.triggered.connect(
                lambda: self.fixar_conversa(conversa_id, not fixada)
            )
            menu.addAction(fixar)
        renomear = QAction("Renomear", menu)
        arquivar = QAction("Arquivar", menu)
        excluir = QAction("Excluir", menu)
        renomear.triggered.connect(
            lambda: self._pedir_renomeacao_conversa(conversa_id, titulo)
        )
        arquivar.triggered.connect(
            lambda: self.arquivar_conversa(conversa_id)
        )
        excluir.triggered.connect(
            lambda: self._pedir_exclusao_conversa(conversa_id, titulo)
        )
        menu.addAction(renomear)
        if not arquivada:
            menu.addAction(arquivar)
        menu.addSeparator()
        menu.addAction(excluir)
        menu.exec(origem.mapToGlobal(origem.rect().bottomLeft()))

    def _pedir_renomeacao_conversa(self, conversa_id: str, titulo: str) -> None:
        novo, aceito = QInputDialog.getText(
            self, "Renomear conversa", "Novo título:", text=titulo,
        )
        novo = re.sub(r"\s+", " ", str(novo or "")).strip()
        if aceito and novo and novo != titulo:
            self._enviar_requisicao_conversa(
                "conversation_rename",
                conversation_id=conversa_id,
                title=novo[:120],
            )

    def _pedir_exclusao_conversa(self, conversa_id: str, titulo: str) -> None:
        resposta = QMessageBox.question(
            self,
            "Excluir conversa",
            f'Excluir "{titulo}" e todo o contexto deste chat?\n\n'
            "Suas memórias globais e ações já executadas serão preservadas.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resposta == QMessageBox.Yes:
            self._enviar_requisicao_conversa(
                "conversation_delete", conversation_id=conversa_id,
            )

    def excluir_conversa_confirmada(self, conversa_id: str) -> None:
        """Porta testável; a interface pública continua pedindo confirmação."""
        self._enviar_requisicao_conversa(
            "conversation_delete", conversation_id=str(conversa_id or ""),
        )

    def abrir_conversa_ativa(self) -> None:
        self.selecionar_pagina("conversa")
        self.composer.editor.setFocus()

    def selecionar_pagina(self, nome: str) -> None:
        mapa = {
            "inicio": 0,
            "conversa": 0,
            "atividade": 1,
            "diagnostico": 2,
            "sistema": 7,
            "desenvolvedor": 8,
            "configuracoes": 3,
            "automacao": 4,
            "musica": 5,
            "memoria": 6,
        }
        indice_anterior = self.paginas.currentIndex()
        nome_anterior = self._pagina_visual_ativa
        indice_destino = mapa.get(nome, 0)
        mudou = nome != nome_anterior
        self.paginas.setCurrentIndex(indice_destino)
        if nome in {"inicio", "conversa"}:
            self._pagina_principal = nome
            self._atualizar_cabecalho_chat()
        titulos = {
            "inicio": "Início",
            "conversa": self.conversa_atual.text(),
            "atividade": "Atividade",
            "diagnostico": "Diagnóstico",
            "sistema": "Sistema",
            "desenvolvedor": "Dev Console",
            "configuracoes": "Configurações",
            "automacao": "Automação",
            "musica": "Música",
            "memoria": "Memória",
        }
        self.titulo_header.setText(titulos.get(nome, "Laylay"))
        for chave, botao in self._nav.items():
            botao.setChecked(chave == nome)
        if nome == "configuracoes" and self._conectado:
            self.enviar_json.emit({"type": "settings_get", "id": uuid.uuid4().hex})
        self._aplicar_responsividade()
        self._pagina_visual_ativa = nome
        self._agendar_pagina_ativa(nome)
        if mudou:
            if self._dashboard_mais_recente:
                QTimer.singleShot(
                    0,
                    lambda destino=nome:
                    self._aplicar_dashboard_pagina_se_ativa(destino),
                )
            direcao = 1 if indice_destino >= indice_anterior else -1
            pagina = self.paginas.currentWidget()
            if pagina is not None:
                QTimer.singleShot(
                    0,
                    lambda alvo=pagina, sentido=direcao:
                    self._animar_transicao_pagina(alvo, sentido),
                )
        QTimer.singleShot(
            0,
            lambda destino=nome: self._sincronizar_indicador_navegacao(
                destino,
                animar=mudou and self._interface_animavel,
            ),
        )

    def alternar_sidebar(self) -> None:
        self._sidebar_expandida = not self._sidebar_expandida
        self.preferencias.setValue("sidebar_expandida", self._sidebar_expandida)
        self.configuracoes.manter_sidebar.blockSignals(True)
        self.configuracoes.manter_sidebar.setChecked(self._sidebar_expandida)
        self.configuracoes.manter_sidebar.blockSignals(False)
        self._aplicar_sidebar()

    def _preferencia_sidebar(self, expandida: bool) -> None:
        self._sidebar_expandida = bool(expandida)
        self.preferencias.setValue("sidebar_expandida", self._sidebar_expandida)
        self._aplicar_sidebar()

    def _aplicar_sidebar(self) -> None:
        self.sidebar.setFixedWidth(198 if self._sidebar_expandida else 68)
        self.marca.setVisible(self._sidebar_expandida)
        self.marca_status.hide()
        self.nav_label.hide()
        self.recentes_label.setVisible(
            self._sidebar_expandida and bool(self._conversas)
        )
        self.ferramentas_conversas.setVisible(
            self._sidebar_expandida and bool(self._conversas)
        )
        self.conversas_scroll.setVisible(
            self._sidebar_expandida and bool(self._conversas)
        )
        self.conversa_atual.hide()
        self.status_mente.hide()
        self.config_rodape.hide()
        self.profile_card.setVisible(
            self._sidebar_expandida
        )
        self.recolher.setText(
            "‹" if self._sidebar_expandida else "›"
        )
        self.nova.show()
        self.nova.setText(
            "Novo chat" if self._sidebar_expandida else ""
        )
        for botao in self._nav.values():
            texto = str(botao.property("label"))
            botao.setText(texto if self._sidebar_expandida else "")
        self.configuracoes.manter_sidebar.blockSignals(True)
        self.configuracoes.manter_sidebar.setChecked(self._sidebar_expandida)
        self.configuracoes.manter_sidebar.blockSignals(False)

    def _alternar_sidebar_compacta(self) -> None:
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def _sidebar_compacta_visual(self) -> None:
        self.sidebar.setFixedWidth(68)
        for widget in (
            self.marca,
            self.marca_status,
            self.nav_label,
            self.recentes_label,
            self.ferramentas_conversas,
            self.conversas_scroll,
            self.conversa_atual,
            self.status_mente,
            self.config_rodape,
            self.profile_card,
        ):
            widget.hide()
        self.recolher.setText("›")
        self.nova.setText("")
        for botao in self._nav.values():
            botao.setText("")

    def _aplicar_responsividade(self) -> None:
        largura = self.width()
        estreita = largura < 760
        compacta = largura < 1080
        inicio_ativo = (
            self.paginas.currentIndex() == 0
            and self._pagina_principal == "inicio"
        )
        mostrar_inspector = inicio_ativo and largura >= 1480
        assinatura = (
            estreita,
            compacta,
            largura >= 980,
            largura >= 1160,
            largura >= 1420,
            mostrar_inspector,
            inicio_ativo,
            self._sidebar_expandida,
            bool(self._conversas),
        )
        largura_mudou = largura != self._ultima_largura_responsiva
        self._ultima_largura_responsiva = largura
        if mostrar_inspector:
            largura_inspector = max(300, min(360, int(largura * 0.19)))
            self.inspector_shell.setFixedWidth(largura_inspector)
        if assinatura == self._assinatura_responsividade:
            if largura_mudou:
                QTimer.singleShot(0, self._ajustar_grid_home)
            return
        self._assinatura_responsividade = assinatura
        self.inspector_shell.setVisible(mostrar_inspector)
        self.central_inteligente.setVisible(True)
        self.painel_lateral.setVisible(True)
        self.chip_memoria.setVisible(largura >= 1420)
        self.chip_modelo.setVisible(largura >= 1160)
        self.chip_microfone.setVisible(largura >= 980)
        self.menu_compacto.setVisible(estreita)
        # A navegação histórica não é usada no topo. Mantê-los sempre
        # ocultos também impede que um resize os reexiba fora da composição.
        self.voltar.hide()
        self.avancar.hide()
        self.titulo_header.hide()
        self.status.setVisible(not compacta)
        if estreita:
            self._sidebar_compacta_visual()
            self.sidebar.hide()
        elif compacta:
            self._sidebar_compacta_visual()
            self.sidebar.show()
        else:
            self.sidebar.show()
            self._aplicar_sidebar()
        margem = 6 if estreita else 14
        pagina_conversa = self.paginas.widget(0)
        if pagina_conversa is not None and pagina_conversa.layout() is not None:
            pagina_conversa.layout().setContentsMargins(
                margem,
                6 if estreita else 12,
                margem,
                12 if estreita else 16,
            )
        self.configuracoes.definir_compacto(compacta, estreito=estreita)
        QTimer.singleShot(0, self._ajustar_grid_home)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._aplicar_responsividade()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() != event.Type.WindowStateChange:
            return
        if self.isMinimized():
            self._parar_pulso_presenca()
        else:
            QTimer.singleShot(
                0,
                lambda: self._atualizar_pulso_presenca(
                    self._atividade_visual_atual,
                ),
            )

    def closeEvent(self, event) -> None:  # noqa: N802
        self._timer_auto_scroll.stop()
        self._encerrar_rolagem_suave()
        self._parar_pulso_presenca()
        self._encerrar_microinteracoes()
        self._encerrar_animacoes_mensagens()
        self._encerrar_animacoes_conversas()
        self._encerrar_transicao_conversa()
        self._encerrar_transicao_pagina()
        self._remover_indicador_pensando(animar=False)
        self._encerrar_saida_pensando()

        grupo_inicio = self._animacao_inicio_grupo
        if grupo_inicio is not None:
            grupo_inicio.stop()
            grupo_inicio.deleteLater()
            self._animacao_inicio_grupo = None
        for _nome, widget, efeito in list(self._efeitos_inicio):
            if _objeto_qt_esta_vivo(widget):
                try:
                    if widget.graphicsEffect() is efeito:
                        widget.setGraphicsEffect(None)
                except RuntimeError:
                    pass
        self._efeitos_inicio.clear()

        movimento_nav = self._animacao_indicador_nav
        if movimento_nav is not None:
            movimento_nav.stop()
            movimento_nav.deleteLater()
            self._animacao_indicador_nav = None

        for timeout in list(self._timeouts_envio.values()):
            timeout.stop()
            timeout.deleteLater()
        self._timeouts_envio.clear()
        self._fases_envio.clear()

        # Defesa final de ciclo de vida: nenhum efeito de um filho fechado
        # deve sobreviver e tentar pintar no QApplication compartilhado.
        for widget in self.feed.findChildren(QWidget):
            try:
                if widget.graphicsEffect() is not None:
                    widget.setGraphicsEffect(None)
            except RuntimeError:
                pass
        self.worker.parar()
        event.accept()


def configuracao_ponte() -> tuple[str, int, str]:
    host = os.environ.get("LAYLAY_DESKTOP_HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("LAYLAY_DESKTOP_PORT", "0"))
    except ValueError:
        port = 0
    token = os.environ.get("LAYLAY_DESKTOP_TOKEN", "")
    if host not in {"127.0.0.1", "localhost", "::1"} or not port or not token:
        raise RuntimeError("O Terminal 3.0 deve ser iniciado pela Laylay para receber uma sessão segura.")
    return host, port, token


def processo_esta_ativo(pid: int) -> bool:
    """Verifica o pai sem alterar seu estado.

    No Windows, ``os.kill(pid, 0)`` não é um probe POSIX seguro: a chamada
    passa pelo mecanismo de encerramento de processos e pode matar justamente
    o núcleo que abriu o Terminal. Consultamos apenas o código de saída com o
    menor direito de acesso necessário. Uma recusa de acesso ainda significa
    que existe um processo naquele PID.
    """
    try:
        pid = int(pid or 0)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return True

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        error_access_denied = 5
        still_active = 259
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        open_process = kernel32.OpenProcess
        open_process.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        open_process.restype = wintypes.HANDLE
        get_exit_code = kernel32.GetExitCodeProcess
        get_exit_code.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        get_exit_code.restype = wintypes.BOOL
        close_handle = kernel32.CloseHandle
        close_handle.argtypes = (wintypes.HANDLE,)
        close_handle.restype = wintypes.BOOL

        ctypes.set_last_error(0)
        handle = open_process(process_query_limited_information, False, pid)
        if not handle:
            return ctypes.get_last_error() == error_access_denied
        try:
            codigo_saida = wintypes.DWORD()
            if not get_exit_code(handle, ctypes.byref(codigo_saida)):
                # Uma falha transitória de leitura não autoriza fechar a UI.
                return True
            return codigo_saida.value == still_active
        finally:
            close_handle(handle)

    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


def main() -> int:
    host, port, token = configuracao_ponte()
    session_id = os.environ.get("LAYLAY_DESKTOP_SESSION", "").strip()
    try:
        parent_pid = int(os.environ.get("LAYLAY_PARENT_PID", "0") or 0)
    except ValueError:
        parent_pid = 0
    raiz = Path(os.environ.get("LAYLAY_PROJECT_ROOT") or Path(__file__).resolve().parents[1]).resolve()
    app = QApplication(sys.argv)
    app.setApplicationName("Laylay Terminal 3.0")
    app.setOrganizationName("Laylay")
    familia = carregar_fontes_interface()
    app.setFont(QFont(familia, 10))
    worker = PonteWorker(host, port, token, session_id=session_id)
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.executar)
    worker.terminou.connect(thread.quit)
    janela = JanelaLaylay(
        worker, raiz, session_id=session_id, parent_pid=parent_pid,
    )
    janela.show()
    monitor_pai = QTimer(app)
    monitor_pai.setInterval(1_500)

    def encerrar_se_orfao() -> None:
        if parent_pid and not processo_esta_ativo(parent_pid):
            print(
                "⚠️ [TERMINAL 2:CLIENTE] processo pai encerrou; "
                f"fechando sessão={session_id[:8]}"
            )
            janela.close()
            app.quit()

    monitor_pai.timeout.connect(encerrar_se_orfao)
    monitor_pai.start()
    thread.start()
    codigo = app.exec()
    worker.parar()
    thread.quit()
    thread.wait(1500)
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
