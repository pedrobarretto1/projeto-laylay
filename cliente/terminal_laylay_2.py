"""Terminal Laylay 2.1 — cliente PySide6 da mente canônica."""

from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import sys
import time
import uuid


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from cliente.terminal_2.transporte import TransporteDesktopCliente

try:
    from PySide6.QtCore import (
        QEasingCurve, QObject, QPropertyAnimation, QSettings, QThread, QTimer,
        Qt, Signal,
    )
    from PySide6.QtGui import (
        QColor, QFont, QFontDatabase, QKeySequence, QPainter, QPen, QPixmap,
        QShortcut,
    )
    from PySide6.QtWidgets import (
        QApplication, QBoxLayout, QButtonGroup, QCheckBox, QComboBox, QFrame,
        QGraphicsOpacityEffect, QHBoxLayout, QLabel, QLayout, QLineEdit, QMainWindow,
        QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QTextEdit,
        QToolButton, QVBoxLayout, QWidget,
    )
except ImportError as erro:  # pragma: no cover
    raise SystemExit(
        "O Terminal Laylay 2.1 precisa de PySide6. Instale com: pip install PySide6"
    ) from erro

from cliente.terminal_2.dashboard import (
    ChipEstado,
    PaginaModulo,
    PainelCentralInteligente,
    PainelLateralDashboard,
)


PALETA = {
    "fundo": "#0D1014",
    "sidebar": "#111419",
    "superficie": "#15191E",
    "elevada": "#1C2026",
    "hover": "#242A31",
    "borda": "#2C3239",
    "texto": "#F3F2F4",
    "secundario": "#B4B5BA",
    "apagado": "#777C84",
    "violeta": "#FF5C73",
    "ciano": "#FF7588",
    "rosa": "#FF5C73",
    "sucesso": "#68C79A",
    "erro": "#ED7888",
}

# Mantém a leitura confortável em janelas desktop sem transformar cada fala em
# uma faixa de ponta a ponta. Em viewports menores, o QScrollArea e os stretches
# das linhas continuam comprimindo os balões naturalmente.
LARGURA_MAXIMA_MENSAGEM_LAYLAY = 860
LARGURA_MAXIMA_MENSAGEM_USUARIO = 760


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
        cores = {
            "feliz": PALETA["rosa"], "animada": PALETA["rosa"],
            "irritada": PALETA["erro"], "brava": PALETA["erro"],
            "curiosa": PALETA["ciano"], "triste": "#8290D6",
        }
        self._cor = QColor(cores.get(emocao, PALETA["violeta"]))
        self._ativo = atividade in {"thinking", "executing", "speaking", "listening"}
        pix = QPixmap(str(self._avatar_path(emocao)))
        self._pixmap = pix.scaled(
            self._tamanho - 8, self._tamanho - 8,
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        ) if not pix.isNull() else QPixmap()
        if self._ativo and not self.timer.isActive():
            self.timer.start(65)
        elif not self._ativo:
            self.timer.stop()
            self._fase = 0.0
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
        lay.setContentsMargins(18, 13, 18, 12)
        lay.setSpacing(7)
        meta = QLabel(("VOCÊ" if papel == "user" else "LAYLAY") + (f"  ·  {horario}" if horario else ""))
        meta.setObjectName("messageMeta")
        self.corpo = QLabel(texto)
        self.corpo.setObjectName("messageText")
        self.corpo.setWordWrap(True)
        self.corpo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.corpo.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(meta)
        lay.addWidget(self.corpo)
        self.status = QLabel()
        self.status.setObjectName("messageStatus")
        self.retry = QPushButton("Tentar novamente")
        self.retry.setObjectName("retryButton")
        self.retry.clicked.connect(lambda: self.reenviar.emit(self.mensagem_id, self.texto))
        self.retry.hide()
        if papel == "user":
            lay.addWidget(self.status, 0, Qt.AlignRight)
            lay.addWidget(self.retry, 0, Qt.AlignRight)
            self.definir_status(status)
        else:
            self.status.hide()
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
        self.retry.setVisible(status == "failed")


class IndicadorPensando(QFrame):
    """Presença visual efêmera; nunca entra no histórico nem na porta de fala."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("thinkingIndicator")
        self.setMaximumWidth(150)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(9)
        meta = QLabel("LAYLAY")
        meta.setObjectName("thinkingMeta")
        self.pontos = QLabel("·  ")
        self.pontos.setObjectName("thinkingDots")
        self.pontos.setMinimumWidth(30)
        lay.addWidget(meta)
        lay.addWidget(self.pontos)
        self._fase = 0
        self._timer = QTimer(self)
        self._timer.setInterval(320)
        self._timer.timeout.connect(self._animar)
        self._timer.start()

    def _animar(self) -> None:
        self._fase = (self._fase + 1) % 3
        self.pontos.setText("·" * (self._fase + 1) + " " * (2 - self._fase))

    def parar(self) -> None:
        self._timer.stop()


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

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("composer")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 11, 10, 11)
        lay.setSpacing(10)
        self.editor = QTextEdit()
        self.editor.setObjectName("composerEdit")
        self.editor.setPlaceholderText("Mensagem para a Laylay")
        self.editor.setAcceptRichText(False)
        self.editor.setFixedHeight(58)
        self.editor.installEventFilter(self)
        self.botao = QPushButton("↑")
        self.botao.setObjectName("sendButton")
        self.botao.setFixedSize(42, 42)
        self.botao.setToolTip("Enviar mensagem")
        self.botao.clicked.connect(self._emitir)
        lay.addWidget(self.editor, 1)
        lay.addWidget(self.botao, 0, Qt.AlignBottom)

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

    def __init__(self) -> None:
        super().__init__()
        self._estado: dict = {}
        self._modelos_por_provedor: dict[str, str] = {}
        self._provedor_atual = ""
        self._preenchendo = False
        externo = QVBoxLayout(self)
        externo.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        conteudo = QWidget()
        self.conteudo_lay = QVBoxLayout(conteudo)
        lay = self.conteudo_lay
        lay.setContentsMargins(54, 42, 68, 52)
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
            18 if compacto else 54,
            24 if compacto else 42,
            18 if compacto else 68,
            30 if compacto else 52,
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
        self._ultima_mensagem: tuple[str, str, float] = ("", "", 0.0)
        self._envios: dict[str, MensagemWidget] = {}
        self._acoes_por_envio: dict[str, str] = {}
        self._indicador_pensando: IndicadorPensando | None = None
        self._container_indicador: QWidget | None = None
        self._animacoes: list[QPropertyAnimation] = []
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
        self._limiar_auto_scroll = 96
        self._pagina_principal = "inicio"
        self._provedor_modelo = ""
        self._dashboard_recebido = False
        self._sidebar_expandida = bool(self.preferencias.value("sidebar_expandida", True, type=bool))
        titulo_sessao = f" · {self._session_id}" if self._session_id else ""
        self.setWindowTitle(f"Laylay — Terminal 3.0 · P3{titulo_sessao}")
        self.setMinimumSize(375, 620)
        self.resize(1680, 940)
        self._montar()
        self._atalhos()
        self._estilizar()
        self._aplicar_sidebar()
        self._aplicar_responsividade()
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
        side.setContentsMargins(12, 14, 12, 14)
        side.setSpacing(5)
        topo = QHBoxLayout()
        self.avatar_side = AroPresenca(self.raiz, 40)
        marca_box = QVBoxLayout()
        self.marca = QLabel("Laylay")
        self.marca.setObjectName("brand")
        self.marca_status = QLabel("companheira local")
        self.marca_status.setObjectName("brandCaption")
        marca_box.addWidget(self.marca)
        marca_box.addWidget(self.marca_status)
        self.recolher = QToolButton(text="‹")
        self.recolher.setObjectName("collapseButton")
        self.recolher.setToolTip("Recolher barra lateral")
        self.recolher.clicked.connect(self.alternar_sidebar)
        topo.addWidget(self.avatar_side)
        topo.addLayout(marca_box, 1)
        topo.addWidget(self.recolher)
        side.addLayout(topo)
        side.addSpacing(16)

        self.nova = QPushButton("+   Nova conversa")
        self.nova.setObjectName("newChatButton")
        self.nova.clicked.connect(self.nova_conversa)
        side.addWidget(self.nova)
        side.addSpacing(12)
        self.nav_label = QLabel("NAVEGAÇÃO")
        self.nav_label.setObjectName("sideSection")
        side.addWidget(self.nav_label)
        for nome, simbolo, texto in (
            ("inicio", "⌂", "Início"),
            ("conversa", "▢", "Conversa"),
            ("automacao", "⌘", "Automação"),
            ("musica", "♫", "Música"),
            ("memoria", "▣", "Memória"),
            ("sistema", "▤", "Sistema"),
            ("configuracoes", "⚙", "Configurações"),
        ):
            botao = QPushButton(f"{simbolo}   {texto}")
            botao.setCheckable(True)
            botao.setProperty("nav", True)
            botao.setProperty("glyph", simbolo)
            botao.setProperty("label", texto)
            botao.clicked.connect(lambda _v=False, n=nome: self.selecionar_pagina(n))
            self._nav[nome] = botao
            side.addWidget(botao)
        self._nav["inicio"].setChecked(True)
        side.addSpacing(18)
        self.recentes_label = QLabel("RECENTES")
        self.recentes_label.setObjectName("sideSection")
        side.addWidget(self.recentes_label)
        self.conversa_atual = QPushButton("Conversa atual")
        self.conversa_atual.setObjectName("recentItem")
        self.conversa_atual.setToolTip("Título efêmero desta sessão visual")
        self.conversa_atual.clicked.connect(lambda: self.selecionar_pagina("conversa"))
        side.addWidget(self.conversa_atual)
        side.addStretch()
        self.status_mente = QLabel("●  Reconectando")
        self.status_mente.setObjectName("mindStatus")
        side.addWidget(self.status_mente)
        self.config_rodape = QPushButton("⚙   Ajustes da Laylay")
        self.config_rodape.setObjectName("footerSettings")
        self.config_rodape.clicked.connect(lambda: self.selecionar_pagina("configuracoes"))
        side.addWidget(self.config_rodape)
        geral.addWidget(self.sidebar)

        centro = QFrame(objectName="mainSurface")
        centro_lay = QVBoxLayout(centro)
        centro_lay.setContentsMargins(0, 0, 0, 0)
        centro_lay.setSpacing(0)
        header = QFrame(objectName="topbar")
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(20, 9, 22, 9)
        hlay.setSpacing(8)
        self.menu_compacto = QToolButton(text="☰")
        self.menu_compacto.setToolTip("Mostrar ou ocultar navegação")
        self.menu_compacto.clicked.connect(self._alternar_sidebar_compacta)
        self.menu_compacto.hide()
        self.voltar = QToolButton(text="←")
        self.voltar.setEnabled(False)
        self.voltar.setToolTip("Sem conversa anterior nesta versão")
        self.avancar = QToolButton(text="→")
        self.avancar.setEnabled(False)
        self.avancar.setToolTip("Sem conversa seguinte nesta versão")
        self.titulo_header = QLabel("Início")
        self.titulo_header.setObjectName("headerTitle")
        hlay.addWidget(self.menu_compacto)
        hlay.addWidget(self.voltar)
        hlay.addWidget(self.avancar)
        hlay.addSpacing(8)
        hlay.addWidget(self.titulo_header)
        hlay.addStretch()
        self.chip_modelo = ChipEstado("Modelo", "Aguardando")
        self.chip_microfone = ChipEstado("Microfone", "Aguardando")
        self.chip_memoria = ChipEstado("Memória", "Aguardando")
        hlay.addWidget(self.chip_modelo)
        hlay.addWidget(self.chip_microfone)
        hlay.addWidget(self.chip_memoria)
        hlay.addSpacing(4)
        self.alternador = AlternadorModo()
        self.alternador.modo_solicitado.connect(self.solicitar_modo)
        hlay.addWidget(self.alternador)
        self.ponto = QLabel("●")
        self.ponto.setObjectName("connectionDot")
        self.status = QLabel("Reconectando")
        self.status.setObjectName("statusLabel")
        hlay.addSpacing(10)
        hlay.addWidget(self.ponto)
        hlay.addWidget(self.status)
        centro_lay.addWidget(header)

        self.paginas = QStackedWidget()
        conversa = QWidget()
        conversa_lay = QHBoxLayout(conversa)
        conversa_lay.setContentsMargins(18, 10, 18, 18)
        conversa_lay.setSpacing(12)
        self.chat_surface = QFrame(objectName="chatSurface")
        chat_lay = QVBoxLayout(self.chat_surface)
        chat_lay.setContentsMargins(8, 0, 8, 0)
        chat_lay.setSpacing(0)
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
        self.feed_lay.setContentsMargins(22, 34, 22, 24)
        self.feed_lay.setSpacing(20)
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
        self.composer = Composer()
        self.composer.enviar.connect(self.enviar_texto)
        chat_lay.addWidget(self.composer)
        conversa_lay.addWidget(self.chat_surface, 1)
        self.central_inteligente = PainelCentralInteligente()
        self.central_inteligente.acao_solicitada.connect(
            self.enviar_acao_rapida,
        )
        self.painel_lateral = PainelLateralDashboard()
        conversa_lay.addWidget(self.central_inteligente)
        conversa_lay.addWidget(self.painel_lateral)
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
        self.configuracoes.manter_sidebar.toggled.connect(self._preferencia_sidebar)
        self.paginas.addWidget(self.configuracoes)
        self.pagina_automacao = PaginaModulo(
            "Automação",
            "Rotinas, ações rápidas e fluxos cooperativos aparecerão aqui com autorização e confirmação reais.",
            "P3",
        )
        self.pagina_musica = PaginaModulo(
            "Música",
            "Playlists, faixa atual e controles serão ligados ao estado observado do player, sem confundir vídeo aberto com áudio tocando.",
            "P4",
        )
        self.pagina_memoria = PaginaModulo(
            "Memória",
            "Fatos, relações, preferências e lembretes serão exibidos por uma projeção sanitizada da memória canônica.",
            "P2",
        )
        self.paginas.addWidget(self.pagina_automacao)
        self.paginas.addWidget(self.pagina_musica)
        self.paginas.addWidget(self.pagina_memoria)
        centro_lay.addWidget(self.paginas, 1)
        geral.addWidget(centro, 1)
        self.selecionar_pagina("inicio")

    def _atalhos(self) -> None:
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self.composer.editor.setFocus)
        QShortcut(QKeySequence("Ctrl+,"), self, activated=lambda: self.selecionar_pagina("configuracoes"))
        QShortcut(QKeySequence("Ctrl+B"), self, activated=self.alternar_sidebar)

    def _estilizar(self) -> None:
        self.setStyleSheet(f"""
            * {{ font-family: 'Segoe UI Variable', 'Segoe UI'; color: {PALETA['texto']}; font-size: 14px; }}
            #root, #mainSurface, QScrollArea, QScrollArea > QWidget > QWidget {{ background: {PALETA['fundo']}; }}
            #sidebar {{ background: {PALETA['sidebar']}; border-right: 1px solid {PALETA['borda']}; }}
            #brand {{ font-size: 18px; font-weight: 700; }}
            #brandCaption {{ color: {PALETA['apagado']}; font-size: 10px; }}
            #sideSection, #eyebrow {{ color: {PALETA['apagado']}; font-size: 10px; font-weight: 700; letter-spacing: 1.2px; }}
            #newChatButton {{ background: {PALETA['elevada']}; border: 1px solid {PALETA['borda']}; border-radius: 10px; text-align: left; padding: 11px 13px; font-weight: 600; }}
            #newChatButton:hover {{ background: {PALETA['hover']}; border-color: #51475A; }}
            QPushButton[nav="true"] {{ background: transparent; border: 0; border-radius: 8px; text-align: left; padding: 10px 12px; color: {PALETA['secundario']}; }}
            QPushButton[nav="true"]:hover {{ background: {PALETA['elevada']}; color: {PALETA['texto']}; }}
            QPushButton[nav="true"]:checked {{ background: #2A1C22; color: {PALETA['texto']}; border-left: 2px solid {PALETA['violeta']}; }}
            #recentItem {{ color: {PALETA['secundario']}; padding: 9px 12px; background: transparent; border: 0; border-radius: 8px; text-align: left; }}
            #recentItem:hover {{ color: {PALETA['texto']}; background: {PALETA['elevada']}; }}
            #mindStatus {{ color: {PALETA['apagado']}; padding: 8px; font-size: 11px; }}
            #footerSettings {{ background: transparent; border: 0; border-radius: 8px; text-align: left; padding: 10px; color: {PALETA['secundario']}; }}
            #footerSettings:hover {{ background: {PALETA['elevada']}; color: {PALETA['texto']}; }}
            #collapseButton, QToolButton {{ background: transparent; border: 1px solid transparent; border-radius: 7px; min-width: 34px; min-height: 32px; color: {PALETA['secundario']}; }}
            QToolButton:hover {{ background: {PALETA['elevada']}; border-color: {PALETA['borda']}; color: {PALETA['texto']}; }}
            #topbar {{ background: {PALETA['fundo']}; border-bottom: 1px solid #242127; }}
            #headerTitle {{ font-weight: 650; }}
            #statusChip {{ background: #11151A; border: 1px solid {PALETA['borda']}; border-radius: 9px; }}
            #statusChipText {{ color: {PALETA['secundario']}; font-size: 11px; }}
            #statusChipDot {{ color: {PALETA['apagado']}; font-size: 9px; }}
            #statusChipDot[state="online"] {{ color: {PALETA['sucesso']}; }}
            #statusChipDot[state="error"] {{ color: {PALETA['erro']}; }}
            #statusChipDot[state="unavailable"] {{ color: #9A7E4C; }}
            #connectionDot {{ color: {PALETA['erro']}; font-size: 9px; }}
            #statusLabel {{ color: {PALETA['apagado']}; font-size: 11px; }}
            #modeSwitch {{ background: {PALETA['superficie']}; border: 1px solid {PALETA['borda']}; border-radius: 9px; }}
            QPushButton[segment="true"] {{ background: transparent; border: 0; border-radius: 6px; padding: 6px 12px; color: {PALETA['apagado']}; font-size: 11px; font-weight: 650; }}
            QPushButton[segment="true"]:checked {{ background: {PALETA['elevada']}; color: {PALETA['texto']}; }}
            QPushButton[segment="true"]:disabled {{ color: #5E5763; }}
            #emptyState {{ background: transparent; }}
            #emptyMark {{ color: {PALETA['violeta']}; font-size: 28px; }}
            #emptyTitle {{ font-size: 23px; font-weight: 650; }}
            #emptyCopy {{ color: {PALETA['secundario']}; font-size: 14px; }}
            #messageLaylay {{ background: transparent; border-left: 2px solid #4D405C; }}
            #messageUser {{ background: {PALETA['elevada']}; border: 1px solid {PALETA['borda']}; border-radius: 11px; }}
            #messageMeta {{ color: {PALETA['apagado']}; font-size: 9px; font-weight: 700; letter-spacing: 1px; }}
            #messageText {{ font-size: 15px; line-height: 1.45; }}
            #messageStatus {{ color: {PALETA['apagado']}; font-size: 10px; }}
            #messageStatus[delivery="pending"] {{ color: {PALETA['ciano']}; }}
            #messageStatus[delivery="failed"] {{ color: {PALETA['erro']}; }}
            #thinkingIndicator {{ background: transparent; border-left: 2px solid {PALETA['ciano']}; }}
            #thinkingMeta {{ color: {PALETA['apagado']}; font-size: 9px; font-weight: 700; letter-spacing: 1px; }}
            #thinkingDots {{ color: {PALETA['ciano']}; font-size: 20px; font-weight: 700; }}
            #retryButton {{ background: transparent; border: 1px solid {PALETA['erro']}; color: {PALETA['erro']}; border-radius: 7px; padding: 5px 9px; font-size: 10px; }}
            #composer {{ background: {PALETA['superficie']}; border: 1px solid {PALETA['borda']}; border-radius: 13px; }}
            #composer:focus-within {{ border-color: #665677; }}
            #composerEdit {{ background: transparent; border: 0; selection-background-color: #5D497A; font-size: 15px; }}
            #sendButton {{ background: {PALETA['texto']}; color: {PALETA['fundo']}; border: 0; border-radius: 9px; font-size: 20px; font-weight: 700; }}
            #sendButton:hover {{ background: #DCD4E1; }}
            #sendButton:disabled {{ background: #49434D; color: #7D7482; }}
            #voiceSurface {{ background: #172123; border: 1px solid #2F5559; border-radius: 10px; }}
            #voiceDot {{ color: {PALETA['ciano']}; font-size: 17px; }}
            #voiceText {{ color: #B7DCE0; }}
            #pageTitle {{ font-size: 28px; font-weight: 650; }}
            #pageDescription {{ color: {PALETA['secundario']}; font-size: 14px; max-width: 700px; }}
            #sectionTitle {{ font-size: 17px; font-weight: 650; padding-top: 4px; }}
            #fieldLabel {{ color: {PALETA['secundario']}; font-size: 11px; font-weight: 650; }}
            QPushButton[provider="true"] {{ background: {PALETA['superficie']}; border: 1px solid {PALETA['borda']}; border-radius: 10px; padding: 13px 15px; text-align: left; color: {PALETA['secundario']}; }}
            QPushButton[provider="true"]:hover {{ background: {PALETA['elevada']}; }}
            QPushButton[provider="true"]:checked {{ background: #292332; border-color: {PALETA['violeta']}; color: {PALETA['texto']}; }}
            #settingsField {{ background: {PALETA['superficie']}; border: 1px solid {PALETA['borda']}; border-radius: 8px; padding: 10px 12px; selection-background-color: #5D497A; }}
            #settingsField:focus {{ border-color: {PALETA['violeta']}; }}
            #settingsField:read-only {{ color: {PALETA['apagado']}; background: #19171C; }}
            #keyState {{ color: {PALETA['ciano']}; font-size: 11px; }}
            #settingsBanner {{ background: #22202A; border-left: 3px solid {PALETA['ciano']}; padding: 11px 13px; color: {PALETA['secundario']}; }}
            #settingsBanner[kind="success"] {{ border-left-color: {PALETA['sucesso']}; }}
            #settingsBanner[kind="error"] {{ border-left-color: {PALETA['erro']}; }}
            #settingsNote {{ color: {PALETA['secundario']}; background: {PALETA['superficie']}; padding: 13px; border-radius: 8px; }}
            #primaryButton {{ background: {PALETA['violeta']}; color: #161219; border: 0; border-radius: 8px; padding: 10px 16px; font-weight: 700; }}
            #primaryButton:hover {{ background: #B99AF0; }}
            #secondaryButton {{ background: {PALETA['elevada']}; border: 1px solid {PALETA['borda']}; border-radius: 8px; padding: 10px 15px; font-weight: 600; }}
            #diagnosticValue {{ background: {PALETA['superficie']}; border-left: 2px solid {PALETA['ciano']}; padding: 12px 15px; font-family: 'Cascadia Code'; font-size: 12px; }}
            #eventLog {{ font-family: 'Cascadia Code'; background: {PALETA['superficie']}; border: 1px solid {PALETA['borda']}; border-radius: 9px; color: {PALETA['secundario']}; padding: 14px; font-size: 11px; }}
            #chatSurface {{ background: #0F1317; border: 1px solid #222830; border-radius: 13px; }}
            #intelligencePanel {{ background: #11151A; border: 1px solid #59313A; border-radius: 14px; }}
            #intelligenceTitle {{ font-size: 18px; font-weight: 700; }}
            #liveBadge {{ color: {PALETA['rosa']}; background: #301D23; border: 1px solid #5A303A; border-radius: 10px; padding: 4px 8px; font-size: 10px; }}
            #dashboardRail {{ background: transparent; }}
            #dashboardCard, #modulePlaceholder {{ background: {PALETA['superficie']}; border: 1px solid {PALETA['borda']}; border-radius: 12px; }}
            #dashboardCardTitle {{ font-size: 14px; font-weight: 700; }}
            #dashboardCardHint {{ color: {PALETA['apagado']}; font-size: 9px; }}
            #dashboardEmpty, #dashboardActivity {{ color: {PALETA['apagado']}; font-size: 11px; }}
            #dashboardMetricLabel {{ color: {PALETA['secundario']}; font-size: 11px; }}
            #dashboardMetricValue {{ color: {PALETA['texto']}; font-size: 11px; font-weight: 700; }}
            #contextItem {{ background: #1A1F25; border: 1px solid #2A3037; border-radius: 8px; }}
            #contextLabel {{ color: {PALETA['apagado']}; font-size: 9px; }}
            #contextValue {{ color: {PALETA['secundario']}; font-size: 10px; font-weight: 650; }}
            #musicTitle {{ font-size: 13px; font-weight: 700; }}
            #musicControlsPlaceholder {{ color: #5F646B; font-size: 15px; padding: 5px; }}
            QPushButton[dashboardAction="true"] {{ background: #1A1F25; border: 1px solid #30363E; border-radius: 9px; padding: 10px 8px; text-align: left; color: {PALETA['secundario']}; font-size: 10px; }}
            QPushButton[dashboardAction="true"]:hover {{ background: #262027; border-color: #74404C; color: {PALETA['texto']}; }}
            QPushButton[dashboardAction="true"]:disabled {{ background: #15191E; border-color: #242A30; color: #565B62; }}
            QPushButton[dashboardAction="true"][actionState="sending"],
            QPushButton[dashboardAction="true"][actionState="received"],
            QPushButton[dashboardAction="true"][actionState="executing"] {{ background: #241D22; border-color: #8B4352; color: {PALETA['rosa']}; }}
            QPushButton[dashboardAction="true"][actionState="confirmed"] {{ background: #16231F; border-color: #356E5A; color: {PALETA['sucesso']}; }}
            QPushButton[dashboardAction="true"][actionState="partial"] {{ background: #282219; border-color: #806233; color: #E5B965; }}
            QPushButton[dashboardAction="true"][actionState="failed"] {{ background: #28191C; border-color: #7A303B; color: {PALETA['erro']}; }}
            QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px; }}
            QScrollBar::handle:vertical {{ background: #49424F; min-height: 32px; border-radius: 4px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QComboBox QAbstractItemView {{ background: {PALETA['superficie']}; selection-background-color: {PALETA['elevada']}; border: 1px solid {PALETA['borda']}; }}
            QCheckBox {{ color: {PALETA['secundario']}; spacing: 8px; }}
        """)

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
                if item.widget():
                    item.widget().hide()
                    item.widget().deleteLater()
            self.feed_lay.addStretch()
            self._feed_em_espera = False
        mensagem = MensagemWidget(
            papel, texto, self._horario(timestamp),
            mensagem_id=mensagem_id, status=status,
        )
        mensagem.reenviar.connect(self.reenviar_texto)
        linha = QHBoxLayout()
        if papel == "user":
            linha.addStretch(1)
            linha.addWidget(mensagem)
            if self.conversa_atual.text() == "Conversa atual":
                titulo = texto[:34] + ("…" if len(texto) > 34 else "")
                self.conversa_atual.setText(titulo)
                if self._pagina_principal == "conversa":
                    self.titulo_header.setText(titulo)
        else:
            linha.addWidget(mensagem)
            linha.addStretch(1)
        self.feed_lay.insertLayout(max(0, self.feed_lay.count() - 1), linha)
        self.feed_lay.invalidate()
        self.feed.updateGeometry()
        QTimer.singleShot(0, self._ajustar_larguras_mensagens)
        if animar:
            self._animar_entrada(mensagem)
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
            largura = min(int(mensagem.largura_preferida), disponivel)
            if mensagem.width() != largura:
                mensagem.setFixedWidth(largura)
                mensagem.updateGeometry()
            altura_minima = mensagem.minimumSizeHint().height()
            if mensagem.minimumHeight() != altura_minima:
                mensagem.setMinimumHeight(altura_minima)
        self.feed_lay.invalidate()
        self.feed.updateGeometry()

    def _esta_perto_do_final(self) -> bool:
        barra = self.scroll.verticalScrollBar()
        return barra.maximum() - barra.value() <= self._limiar_auto_scroll

    def _agendar_rolagem_final(self) -> None:
        """Agrupa relayouts sucessivos e ancora somente uma vez no fim."""
        self._timer_auto_scroll.start(0)

    def _rolar_ao_final(self) -> None:
        barra = self.scroll.verticalScrollBar()
        barra.setValue(barra.maximum())

    def _animar_entrada(self, mensagem: MensagemWidget) -> None:
        efeito = QGraphicsOpacityEffect(mensagem)
        mensagem.setGraphicsEffect(efeito)
        animacao = QPropertyAnimation(efeito, b"opacity", mensagem)
        animacao.setDuration(150)
        animacao.setStartValue(0.25)
        animacao.setEndValue(1.0)
        animacao.setEasingCurve(QEasingCurve.OutCubic)
        self._animacoes.append(animacao)

        def finalizar() -> None:
            if animacao in self._animacoes:
                self._animacoes.remove(animacao)
            # Efeitos gráficos persistentes obrigam o Qt a recompor dezenas de
            # pixmaps durante a rolagem e eram a origem do piscar no histórico.
            if mensagem.graphicsEffect() is efeito:
                mensagem.setGraphicsEffect(None)
            animacao.deleteLater()

        animacao.finished.connect(finalizar)
        animacao.start()

    def enviar_texto(self, texto: str) -> None:
        self._enviar_pedido(texto, tipo="chat", acao_id="")

    def enviar_acao_rapida(self, acao_id: str, texto: str) -> None:
        self._enviar_pedido(texto, tipo="quick_action", acao_id=acao_id)

    def _enviar_pedido(
        self,
        texto: str,
        *,
        tipo: str,
        acao_id: str,
    ) -> None:
        # Um novo pedido reposiciona a única presença efêmera sempre depois da
        # mensagem mais recente, sem acumular indicadores no feed.
        self._remover_indicador_pensando()
        mensagem_id = uuid.uuid4().hex
        mensagem = self.adicionar_mensagem(
            "user", texto, timestamp=time.time(), mensagem_id=mensagem_id,
            status="pending",
        )
        if mensagem is not None:
            self._envios[mensagem_id] = mensagem
        self._mostrar_indicador_pensando()
        payload = {
            "type": "input_submit", "id": mensagem_id, "text": texto,
            "kind": tipo,
        }
        if tipo == "quick_action":
            payload["action"] = str(acao_id or "")
            self._acoes_por_envio[mensagem_id] = str(acao_id or "")
            self.central_inteligente.definir_estado_acao(
                acao_id, "sending", "Enviando para a mente canônica",
            )
        enviado = bool(self.worker.enfileirar(payload))
        if not enviado:
            self._falhar_envio(
                mensagem_id,
                "A ponte ainda não estava pronta para receber a mensagem.",
            )
            return
        self._armar_timeout_envio(mensagem_id, fase="ack", intervalo_ms=3_500)
        self.adicionar_evento(
            "Mensagem enviada à ponte",
            "Aguardando a confirmação de recebimento da mente.",
            "info",
        )

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
        if mensagem is not None:
            mensagem.definir_status("failed", detalhe)
        acao_id = self._acoes_por_envio.pop(mensagem_id, "")
        if acao_id:
            self.central_inteligente.definir_estado_acao(
                acao_id, "failed", detalhe,
            )
        self._remover_indicador_pensando()
        self.adicionar_evento("Mensagem não entregue", detalhe, "error")

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

    def _mostrar_indicador_pensando(self) -> None:
        if self._indicador_pensando is not None:
            return
        indicador = IndicadorPensando()
        container = QWidget()
        linha = QHBoxLayout(container)
        linha.setContentsMargins(0, 0, 0, 0)
        linha.addWidget(indicador)
        linha.addStretch(1)
        self._indicador_pensando = indicador
        self._container_indicador = container
        self.feed_lay.insertWidget(max(0, self.feed_lay.count() - 1), container)
        self.feed_lay.invalidate()
        self.feed.updateGeometry()
        self._agendar_rolagem_final()

    def _remover_indicador_pensando(self) -> None:
        indicador = self._indicador_pensando
        container = self._container_indicador
        self._indicador_pensando = None
        self._container_indicador = None
        if indicador is not None:
            indicador.parar()
        if container is not None:
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

    def receber(self, msg: dict) -> None:
        tipo = msg.get("type")
        if tipo == "snapshot":
            mensagens = list(msg.get("messages", []))
            for item in mensagens:
                self.adicionar_mensagem(
                    item.get("role", "assistant"), item.get("content", ""),
                    timestamp=item.get("timestamp"), rolar_ao_final=False,
                    animar=False,
                )
            if mensagens:
                self._agendar_rolagem_final()
            for evento in msg.get("events", []):
                self.adicionar_evento(evento.get("title", "Evento"), evento.get("detail", ""), evento.get("level", "info"))
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
            if mensagem_id:
                self._encerrar_timeout_envio(mensagem_id)
                self._envios.pop(mensagem_id, None)
            if not self._envios:
                self._remover_indicador_pensando()
            self.adicionar_mensagem(
                "assistant", str(msg.get("text") or ""),
                timestamp=msg.get("timestamp"),
                mensagem_id=str(msg.get("id") or mensagem_id),
            )
            self.avatar_side.atualizar("speaking", str(msg.get("emotion") or "calma"))
            self.adicionar_evento("Resposta entregue", "A fala final chegou à conversa.", "success")
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
                self._atualizar_dashboard(msg["dashboard"])
        elif tipo == "action_state":
            mensagem_id = str(msg.get("id") or "")
            acao_id = str(
                msg.get("action") or self._acoes_por_envio.get(mensagem_id) or ""
            )
            estado_acao = str(msg.get("state") or "")
            resumo = str(msg.get("summary") or "")
            if acao_id:
                self.central_inteligente.definir_estado_acao(
                    acao_id, estado_acao, resumo,
                )
            if estado_acao in {
                "awaiting_confirmation", "confirmed", "partial", "failed",
            }:
                self._acoes_por_envio.pop(mensagem_id, None)
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

    def _atualizar_dashboard(self, dashboard: dict) -> None:
        if dashboard.get("schema_version") != 1:
            return
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
        self.central_inteligente.aplicar_dashboard(dashboard)
        self.painel_lateral.aplicar_dashboard(dashboard)

    def _atualizar_estado(self, estado: dict) -> None:
        atividade = str(estado.get("activity") or "idle")
        rotulo = str(estado.get("activity_label") or "Pronta")
        emocao = str(estado.get("emotion") or "calma")
        self._modo = str(estado.get("interaction_mode") or self._modo)
        self._voz_disponivel = bool(estado.get("voice_available", False))
        if not self._dashboard_recebido:
            if not self._voz_disponivel:
                self.chip_microfone.definir("Indisponível", estado="unavailable")
            elif self._modo == "voice":
                self.chip_microfone.definir("Ativo", estado="online")
            else:
                self.chip_microfone.definir("Pausado no chat", estado="pending")
        self.status.setText(rotulo)
        self.marca_status.setText(f"{rotulo.casefold()} · {emocao}")
        self.diag_atividade.setText(f"Atividade\n{rotulo} · emoção {emocao}")
        self.avatar_side.atualizar(atividade, emocao)
        if atividade in {"thinking", "executing"} and self._envios:
            self._mostrar_indicador_pensando()
        assinatura_atividade = f"{atividade}:{rotulo}:{emocao}"
        if (
            atividade in {"thinking", "executing", "speaking", "listening", "reconnecting"}
            and assinatura_atividade != self._ultima_atividade_evento
        ):
            self._ultima_atividade_evento = assinatura_atividade
            self.adicionar_evento(rotulo, f"Estado da mente · emoção {emocao}.", "info")
        self.configuracoes.definir_voz(self._voz_disponivel)
        self._aplicar_modo()

    def _aplicar_modo(self) -> None:
        self.alternador.definir(
            self._modo, pendente=self._modo_pendente,
            voz_disponivel=self._voz_disponivel,
        )
        self.composer.definir_estado(conectado=self._conectado, modo=self._modo)
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
        self.central_inteligente.definir_conectada(conectado)
        self.configuracoes.definir_conectada(conectado)
        self.ponto.setStyleSheet(f"color: {PALETA['sucesso'] if conectado else PALETA['erro']};")
        self.status.setText("Pronta" if conectado else "Reconectando")
        self.status_mente.setText("●  Mente conectada" if conectado else "●  Reconectando")
        if conectado and not self._dashboard_recebido:
            self.chip_modelo.definir(
                f"{self._provedor_modelo} configurado"
                if self._provedor_modelo else "Aguardando estado",
                estado="pending",
            )
        else:
            if not conectado:
                self._dashboard_recebido = False
                self.chip_modelo.definir("Sem ponte", estado="error")
                self.chip_memoria.definir("Reconectando", estado="unavailable")
                self.central_inteligente.invalidar_dashboard()
                self.painel_lateral.invalidar_dashboard()
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
    ) -> None:
        cores = {"error": PALETA["erro"], "warning": PALETA["rosa"], "success": PALETA["sucesso"], "info": PALETA["ciano"]}
        self.eventos.append(
            f'<span style="color:{cores.get(nivel, PALETA["ciano"])}">{time.strftime("%H:%M")}  {titulo}</span>'
            f'<br><span style="color:{PALETA["secundario"]}">{detalhe}</span><br>'
        )
        if atividade_confirmada:
            self.central_inteligente.registrar_evento(titulo)

    def nova_conversa(self) -> None:
        self._remover_indicador_pensando()
        while self.feed_lay.count():
            item = self.feed_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            if item.layout():
                while item.layout().count():
                    filho = item.layout().takeAt(0)
                    if filho.widget():
                        filho.widget().deleteLater()
        self.vazio = QFrame(objectName="emptyState")
        self.vazio.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Minimum)
        lay = QVBoxLayout(self.vazio)
        titulo = QLabel("◕‿◕  Tela limpa. Memória intacta.")
        titulo.setObjectName("emptyTitle")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        texto = QLabel("Nova sessão visual; a mente da Laylay não esqueceu nada.")
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
        self._envios.clear()
        self._acoes_por_envio.clear()
        self.conversa_atual.setText("Conversa atual")
        self.selecionar_pagina("conversa")
        self.composer.editor.setFocus()
        self.adicionar_evento("Nova conversa visual", "O histórico canônico e a memória foram preservados.", "info")

    def selecionar_pagina(self, nome: str) -> None:
        mapa = {
            "inicio": 0,
            "conversa": 0,
            "atividade": 1,
            "diagnostico": 2,
            "sistema": 2,
            "configuracoes": 3,
            "automacao": 4,
            "musica": 5,
            "memoria": 6,
        }
        self.paginas.setCurrentIndex(mapa.get(nome, 0))
        if nome in {"inicio", "conversa"}:
            self._pagina_principal = nome
        titulos = {
            "inicio": "Início",
            "conversa": self.conversa_atual.text(),
            "atividade": "Atividade",
            "diagnostico": "Diagnóstico",
            "sistema": "Sistema",
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
        self.sidebar.setFixedWidth(254 if self._sidebar_expandida else 72)
        self.marca.setVisible(self._sidebar_expandida)
        self.marca_status.setVisible(self._sidebar_expandida)
        self.nav_label.setVisible(self._sidebar_expandida)
        self.recentes_label.setVisible(self._sidebar_expandida)
        self.conversa_atual.setVisible(self._sidebar_expandida)
        self.status_mente.setVisible(self._sidebar_expandida)
        self.recolher.setText("‹" if self._sidebar_expandida else "›")
        self.nova.setText("+   Nova conversa" if self._sidebar_expandida else "+")
        self.config_rodape.setText("⚙   Ajustes da Laylay" if self._sidebar_expandida else "⚙")
        for botao in self._nav.values():
            simbolo = str(botao.property("glyph"))
            texto = str(botao.property("label"))
            botao.setText(f"{simbolo}   {texto}" if self._sidebar_expandida else simbolo)
        self.configuracoes.manter_sidebar.blockSignals(True)
        self.configuracoes.manter_sidebar.setChecked(self._sidebar_expandida)
        self.configuracoes.manter_sidebar.blockSignals(False)

    def _alternar_sidebar_compacta(self) -> None:
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def _sidebar_compacta_visual(self) -> None:
        self.sidebar.setFixedWidth(72)
        for widget in (
            self.marca, self.marca_status, self.nav_label, self.recentes_label,
            self.conversa_atual, self.status_mente,
        ):
            widget.hide()
        self.recolher.setText("›")
        self.nova.setText("+")
        self.config_rodape.setText("⚙")
        for botao in self._nav.values():
            botao.setText(str(botao.property("glyph")))

    def _aplicar_responsividade(self) -> None:
        largura = self.width()
        estreita = largura < 760
        compacta = largura < 920
        inicio_ativo = (
            self.paginas.currentIndex() == 0
            and self._pagina_principal == "inicio"
        )
        self.central_inteligente.setVisible(inicio_ativo and largura >= 1450)
        self.painel_lateral.setVisible(inicio_ativo and largura >= 1650)
        self.chip_memoria.setVisible(largura >= 1420)
        self.chip_modelo.setVisible(largura >= 1160)
        self.chip_microfone.setVisible(largura >= 980)
        self.menu_compacto.setVisible(estreita)
        self.voltar.setVisible(not estreita)
        self.avancar.setVisible(not estreita)
        self.titulo_header.setVisible(not estreita)
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
        margem = 6 if estreita else 18
        pagina_conversa = self.paginas.widget(0)
        if pagina_conversa is not None and pagina_conversa.layout() is not None:
            pagina_conversa.layout().setContentsMargins(
                margem, 6 if estreita else 10, margem, 12 if estreita else 18,
            )
        self.feed_lay.setContentsMargins(
            4 if estreita else 22,
            18 if estreita else 34,
            4 if estreita else 22,
            18 if estreita else 24,
        )
        self.configuracoes.definir_compacto(compacta, estreito=estreita)
        QTimer.singleShot(0, self._ajustar_larguras_mensagens)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._aplicar_responsividade()

    def closeEvent(self, event) -> None:  # noqa: N802
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
        raise RuntimeError("O Terminal 2.1 deve ser iniciado pela Laylay para receber uma sessão segura.")
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
    app.setApplicationName("Laylay Terminal 2.1")
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
