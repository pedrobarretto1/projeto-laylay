"""Espelhamento local de uma janela escolhida pelo usuário, sem ponte com a IA.

Não extrai URLs, não grava mídia e não controla o navegador. O áudio continua
na origem. Cada sessão só fica ao vivo depois de receber um frame válido.
"""
from __future__ import annotations

from time import monotonic
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, QRectF, Qt, QTimer, QUrl, Signal, QEvent
from PySide6.QtGui import QColor, QDesktopServices, QFont, QImage, QKeySequence, QPainter, QPainterPath, QShortcut
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget, QBoxLayout, QScrollArea,
)
from cliente.terminal_2.theme import PALETA
from cliente.terminal_2.streaming_fontes import FontesStreaming, calcular_recorte, medir_margens_nativas


class CapturaStreaming(QObject):
    imagem_recebida = Signal(QImage)
    estado_alterado = Signal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._geracao = 0
        self._captura = self._sessao = self._sink = None
        self._ultimo_frame = 0.0
        self._confirmada = False
        self.estado = "parado"
        self._prazo = QTimer(self)
        self._prazo.setSingleShot(True)
        self._prazo.setInterval(8000)
        self._prazo.timeout.connect(lambda: self._falhar(
            "Nenhuma imagem recebida. Mantenha a janela aberta e tente novamente."
        ))
        self._vigia = QTimer(self)
        self._vigia.setInterval(1500)
        self._vigia.timeout.connect(self._verificar_origem)

    @staticmethod
    def janelas_disponiveis() -> list:
        from PySide6.QtMultimedia import QWindowCapture
        return [janela for janela in QWindowCapture.capturableWindows() if janela.isValid()]

    def _estado(self, estado: str, mensagem: str) -> None:
        self.estado = estado
        self.estado_alterado.emit(estado, mensagem)

    def iniciar(self, janela: object) -> None:
        self.parar()
        # isValid consulta a janela nativa. Wrappers de enumerações distintas
        # não preservam igualdade no binding PySide6 instalado.
        if janela is None or not janela.isValid():
            self._estado("erro", "A janela não está mais disponível. Atualize a lista.")
            return
        from PySide6.QtMultimedia import QMediaCaptureSession, QVideoSink, QWindowCapture
        self._captura = QWindowCapture(self)
        self._sessao = QMediaCaptureSession(self)
        self._sink = QVideoSink(self)
        geracao = self._geracao
        self._sink.videoFrameChanged.connect(
            lambda frame: self._receber_frame(geracao, frame)
        )
        self._captura.errorOccurred.connect(
            lambda erro, texto: self._erro_nativo(geracao, erro, texto)
        )
        self._sessao.setWindowCapture(self._captura)
        self._sessao.setVideoSink(self._sink)
        self._captura.setWindow(janela)
        self._estado("iniciando", "Conectando à janela…")
        self._prazo.start()
        self._vigia.start()
        self._captura.start()

    def _erro_nativo(self, geracao: int, erro: object, texto: str) -> None:
        from PySide6.QtMultimedia import QWindowCapture
        if geracao == self._geracao and erro != QWindowCapture.Error.NoError:
            self._falhar(f"Não foi possível capturar a janela: {texto}")

    def _receber_frame(self, geracao: int, frame: object) -> None:
        if geracao != self._geracao or self._captura is None or not frame.isValid():
            return
        agora = monotonic()
        if self._confirmada and agora - self._ultimo_frame < 1 / 30:
            return
        imagem = frame.toImage()
        if imagem.isNull():
            return
        self._ultimo_frame = agora
        self.imagem_recebida.emit(imagem)
        if not self._confirmada:
            self._confirmada = True
            self._prazo.stop()
            self._estado("transmitindo", "Espelhando a janela selecionada")

    def _verificar_origem(self) -> None:
        if self._captura is not None and not self._captura.window().isValid():
            self._falhar("A janela de origem foi fechada. Escolha outra janela.")

    def _falhar(self, mensagem: str) -> None:
        self.parar()
        self._estado("erro", mensagem)

    def parar(self) -> None:
        # Invalida inclusive callbacks já enfileirados de uma sessão anterior.
        self._geracao += 1
        self._prazo.stop()
        self._vigia.stop()
        captura, sessao, sink = self._captura, self._sessao, self._sink
        self._captura = self._sessao = self._sink = None
        self._confirmada = False
        self._ultimo_frame = 0.0
        if captura is not None:
            captura.stop()
        if sessao is not None:
            sessao.setWindowCapture(None)
            sessao.setVideoSink(None)
        for objeto in (captura, sessao, sink):
            if objeto is not None:
                objeto.deleteLater()
        self._estado("parado", "Escolha uma janela e clique em Transmitir")


class VisorStreaming(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(240, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAccessibleName("Vídeo espelhado do navegador")
        self.imagem = QImage()

    def receber_imagem(self, imagem: QImage) -> None:
        self.imagem = imagem
        self.update()

    def limpar(self) -> None:
        self.imagem = QImage()
        self.update()

    def _origem(self) -> QRectF:
        return QRectF(0, 0, self.imagem.width(), self.imagem.height())

    def _destino(self) -> QRectF:
        origem = self._origem()
        if origem.isEmpty():
            return QRectF()
        fator = min(self.width() / origem.width(), self.height() / origem.height())
        largura, altura = origem.width() * fator, origem.height() * fator
        return QRectF((self.width() - largura) / 2, (self.height() - altura) / 2, largura, altura)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        moldura = QPainterPath()
        moldura.addRoundedRect(QRectF(self.rect()), 16, 16)
        painter.fillPath(moldura, QColor("#080B12"))
        painter.setClipPath(moldura)
        if self.imagem.isNull():
            painter.setPen(QColor("#8993AB"))
            painter.drawText(self.rect(), Qt.AlignCenter, "▷\n\nSeu próximo vídeo começa aqui")
            return
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawImage(self._destino(), self.imagem, self._origem())


class PaginaStreaming(QWidget):
    def __init__(self, parent: QWidget | None = None, *, expandir_no_host: Callable[[bool], None] | None = None) -> None:
        super().__init__(parent)
        self._host_rolagem = parent if isinstance(parent, QScrollArea) else None
        self._expandir_no_host = expandir_no_host
        self._host_ampliado = False
        self._visibilidade_integrada: list = []
        self.setObjectName("streamingPage")
        self.setFont(QFont('Segoe UI', 10))
        p = PALETA
        self.setStyleSheet(f"""
            #streamingPage {{ font-family: 'Segoe UI'; font-size: 12px; }}
            #streamingPage QPushButton {{
                background: {p['elevada']}; color: {p['texto']};
                border: 1px solid {p['borda']}; border-radius: 8px;
                padding: 6px 12px; min-height: 22px;
            }}
            #streamingPage QPushButton:hover {{ background: {p['hover']}; }}
            #streamingPage QPushButton:focus {{ border-color: {p['rosa']}; }}
            #streamingPage QPushButton#streamingStart {{
                background: #7856D8; border-color: #7856D8; font-weight: 600;
            }}
            #streamingPage QPushButton:disabled,
            #streamingPage QPushButton#streamingStart:disabled {{
                background: {p['superficie']}; color: {p['apagado']};
                border-color: {p['borda']};
            }}
            #streamingPage QComboBox {{
                background: {p['superficie']}; color: {p['texto']};
                border: 1px solid {p['borda']}; border-radius: 8px;
                padding: 6px 10px; min-height: 22px;
            }}
            #streamingPage QComboBox:disabled {{ color: {p['secundario']}; }}
        """)
        self.captura = CapturaStreaming(self)
        self.fontes = FontesStreaming(self)
        self._conexao_demora = False
        self._janelas: list = []
        self._chave_ativa = ""
        self._assinatura_fontes: tuple = ()
        self._margens = (0, 0, 0, 0)
        self._viewport_nativo: tuple = ()
        self._titulo_nativo = ""
        self._popup: QDialog | None = None
        self._titulo_origem = ""
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(20, 16, 20, 18)
        raiz.setSpacing(12)
        titulo = QLabel("Streaming")
        titulo.setStyleSheet("font-size: 24px; font-weight: 700; color: #EEEAFB;")
        raiz.addWidget(titulo)
        subtitulo = QLabel("Só o vídeo. Enquadramento automático, no seu ritmo.")
        subtitulo.setWordWrap(True)
        subtitulo.setStyleSheet("color: #A8AFC4; font-size: 13px;")
        raiz.addWidget(subtitulo)
        origem = QHBoxLayout()
        self._origem_layout = origem
        origem.setSpacing(8)
        self.janelas = QComboBox()
        self.janelas.setMinimumWidth(140)
        self.janelas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.janelas.setAccessibleName("Vídeo encontrado no navegador")
        self.janelas.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.janelas.setMinimumContentsLength(15)
        self.atualizar = QPushButton("Atualizar")
        self.transmitir = QPushButton("Transmitir")
        self.transmitir.setObjectName("streamingStart")
        self.parar = QPushButton("Parar")
        for widget in (self.janelas, self.atualizar, self.transmitir, self.parar):
            origem.addWidget(widget, 1 if widget is self.janelas else 0)
        raiz.addLayout(origem)
        self.estado = QLabel()
        self.estado.setWordWrap(True)
        self.estado.setTextFormat(Qt.PlainText)
        raiz.addWidget(self.estado)
        self.visor = VisorStreaming(self)
        self._visor_layout = QVBoxLayout()
        self._visor_layout.setContentsMargins(0, 0, 0, 0)
        self._visor_layout.addWidget(self.visor)
        raiz.addLayout(self._visor_layout, 1)
        controles = QHBoxLayout()
        self._controles_layout = controles
        self.automatico = QLabel("✦ Enquadramento automático")
        self.automatico.setWordWrap(True)
        self.automatico.setStyleSheet(f"color: {p['violeta']}; font-weight: 600;")
        self.flutuante = QPushButton("Janela flutuante")
        self.tela_cheia = QPushButton("Tela cheia")
        if expandir_no_host is not None:
            self.flutuante.setText('Ampliar no painel')
            self.tela_cheia.setText('Só o vídeo')
        controles.addWidget(self.automatico)
        controles.addStretch()
        for botao in (self.flutuante, self.tela_cheia):
            controles.addWidget(botao)
        raiz.addLayout(controles)
        ajuda = QLabel(
            "Abra um vídeo, selecione-o acima e transmita. O tamanho acompanha o player automaticamente.\n"
            "O áudio e os controles continuam no navegador. Mantenha a aba de origem visível, sem minimizar. "
            "Conteúdo protegido pode bloquear a imagem."
        )
        ajuda.setWordWrap(True)
        ajuda.setStyleSheet("color: #8993AB; font-size: 12px;")
        raiz.addWidget(ajuda)
        self.extensao = QPushButton("Atualizar extensão da Laylay")
        self.extensao.setAccessibleName('Atualizar extensão da Laylay')
        self.extensao.setToolTip("chrome://extensions → Recarregar a extensão Laylay existente")
        self.extensao.clicked.connect(self.abrir_extensao)
        raiz.addWidget(self.extensao, 0, Qt.AlignLeft)
        self.atualizar.clicked.connect(self.atualizar_janelas)
        self.transmitir.clicked.connect(self.iniciar)
        self.parar.clicked.connect(self.encerrar)
        self.flutuante.clicked.connect(lambda: self.abrir_player(False))
        self.tela_cheia.clicked.connect(lambda: self.abrir_player(True))
        self.captura.imagem_recebida.connect(self._receber_video)
        self.captura.estado_alterado.connect(self._aplicar_estado)
        self.fontes.alteradas.connect(self.atualizar_janelas)
        self._aplicar_estado("parado", "Aguardando vídeos do navegador…")
        self.atualizar_janelas()
        self._prazo_conexao = QTimer(self)
        self._prazo_conexao.setSingleShot(True)
        self._prazo_conexao.setInterval(6000)
        self._prazo_conexao.timeout.connect(self._conexao_ausente)
        self._prazo_conexao.start()
        self._atalho_integrado = QShortcut(QKeySequence('Escape'), self, activated=lambda: self._expandir_no_host(False) if self._expandir_no_host is not None else None)
        self._atalho_integrado.setEnabled(False)
        if self._host_rolagem is not None:
            self._host_rolagem.viewport().installEventFilter(self)
        QTimer.singleShot(0, self._ajustar_layout_responsivo)

    def resizeEvent(self, evento) -> None:  # noqa: N802
        super().resizeEvent(evento)
        self._ajustar_layout_responsivo()

    def eventFilter(self, objeto, evento) -> bool:  # noqa: N802
        if self._host_rolagem is not None and objeto is self._host_rolagem.viewport() and evento.type() == QEvent.Resize:
            self._ajustar_layout_responsivo(evento.size().width())
        return super().eventFilter(objeto, evento)

    def _ajustar_layout_responsivo(self, largura: int | None = None) -> None:
        # O sizeHint horizontal não pode ser o juiz da própria responsividade:
        # ele impedia a página de ficar estreita e, portanto, de trocar direção.
        if largura is None:
            largura = self._host_rolagem.viewport().width() if self._host_rolagem is not None else self.width()
        direcao = QBoxLayout.TopToBottom if largura < 620 else QBoxLayout.LeftToRight
        rotulo_extensao = 'Atualizar extensão' if largura < 620 else 'Atualizar extensão da Laylay'
        if self.extensao.text() != rotulo_extensao:
            self.extensao.setText(rotulo_extensao)
            self.updateGeometry()
        if self._origem_layout.direction() != direcao:
            self._origem_layout.setDirection(direcao)
            self._controles_layout.setDirection(direcao)
            self.updateGeometry()

    def ampliar_integrado(self, ativo: bool) -> None:
        """Enquadramento interno; não destaca o visor em outra janela."""
        if self._expandir_no_host is None or ativo == self._host_ampliado:
            return
        self._host_ampliado = ativo
        self._atalho_integrado.setEnabled(ativo)
        if ativo:
            self._visibilidade_integrada = [(w, not w.isHidden()) for w in self.findChildren(QWidget, options=Qt.FindDirectChildrenOnly) if w is not self.visor]
            for widget, _visivel in self._visibilidade_integrada:
                widget.hide()
        else:
            for widget, visivel in self._visibilidade_integrada:
                widget.setVisible(visivel)
            self._visibilidade_integrada.clear()
        self.visor.show()

    def _conexao_ausente(self) -> None:
        self._conexao_demora = True
        self.atualizar_janelas()

    def atualizar_janelas(self) -> None:
        indice = self.janelas.currentIndex()
        escolhida = self._janelas[indice].chave if 0 <= indice < len(self._janelas) else ""
        self._janelas = sorted(self.fontes.fontes.values(), key=lambda fonte: (not fonte.reproduzindo, fonte.titulo, fonte.chave))
        if self._chave_ativa and self._chave_ativa not in self.fontes.fontes:
            self.encerrar()
            self._aplicar_estado("erro", "Vídeo indisponível. Volte à aba de origem para reconectar.")
        assinatura = tuple((fonte.chave, fonte.titulo, fonte.rotulo, fonte.reproduzindo) for fonte in self._janelas)
        if assinatura != self._assinatura_fontes:
            self._assinatura_fontes = assinatura
            self.janelas.blockSignals(True)
            self.janelas.clear()
            for i, fonte in enumerate(self._janelas):
                rotulo = f"{'▶' if fonte.reproduzindo else 'Ⅱ'} {fonte.titulo} · {fonte.rotulo}"
                self.janelas.addItem(rotulo)
                self.janelas.setItemData(i, rotulo, Qt.ToolTipRole)
            self.janelas.setCurrentIndex(-1)
            for i, fonte in enumerate(self._janelas):
                if fonte.chave == escolhida:
                    self.janelas.setCurrentIndex(i)
            self.janelas.blockSignals(False)
        self.janelas.setPlaceholderText("Escolha um vídeo…" if self._janelas else
                                       "Nenhum vídeo visível nesta aba" if self.fontes.conectada else
                                       "Extensão da Laylay não conectada")
        self.extensao.setVisible(not self.fontes.conectada and not self._host_ampliado)
        self.transmitir.setEnabled(bool(self._janelas) and self.captura.estado in {"parado", "erro"})
        if not self.fontes.disponivel:
            self._aplicar_estado("erro", "Canal local ocupado. Feche a outra aba Streaming e reabra o Terminal.")
        elif not self._janelas and self.captura.estado == "parado":
            if self.fontes.conectada:
                self._aplicar_estado("parado", "Extensão conectada · nenhum vídeo visível. Abra um vídeo numa aba ativa do navegador.")
            elif self._conexao_demora:
                self._aplicar_estado("erro", "Extensão não conectada. Recarregue a extensão Laylay em chrome://extensions e mantenha o navegador aberto.")
            else:
                self._aplicar_estado("parado", "Aguardando conexão da extensão Laylay…")

    def iniciar(self) -> None:
        indice = self.janelas.currentIndex()
        if indice < 0 or indice >= len(self._janelas):
            self._aplicar_estado("erro", "Selecione um vídeo encontrado no navegador.")
            return
        self.visor.limpar()
        fonte = self._janelas[indice]
        self._titulo_origem = fonte.titulo
        self._chave_ativa = fonte.chave
        try:
            candidatos = [janela for janela in self.captura.janelas_disponiveis()
                          if janela.description() == fonte.titulo
                          or janela.description().startswith(fonte.titulo + " - ")
                          or janela.description().startswith(fonte.titulo + " — ")
                          or janela.description().startswith(fonte.titulo + ": ")]
            if len(candidatos) != 1:
                self._chave_ativa = ""
                self._aplicar_estado("erro", "Não foi possível identificar uma janela única. Feche cópias da mesma página e tente novamente.")
                return
            self._titulo_nativo = candidatos[0].description()
            self._margens = medir_margens_nativas(self._titulo_nativo)
            self._viewport_nativo = fonte.viewport
            self.captura.iniciar(candidatos[0])
        except (ImportError, RuntimeError) as erro:
            self.captura._falhar(f"Captura indisponível: {erro}")

    def _receber_video(self, imagem: QImage) -> None:
        fonte = self.fontes.fontes.get(self._chave_ativa)
        if fonte and self._titulo_nativo and fonte.viewport != self._viewport_nativo:
            try:
                self._margens = medir_margens_nativas(self._titulo_nativo)
                self._viewport_nativo = fonte.viewport
            except RuntimeError:
                self.visor.limpar()
                self._aplicar_estado("iniciando", "Aguardando limites atuais da janela…")
                return
        recorte = calcular_recorte(fonte, imagem.width(), imagem.height(), monotonic(), self._margens) if fonte else None
        if recorte is None or recorte.isEmpty():
            self.visor.limpar()
            self._aplicar_estado("iniciando", "Ajustando o enquadramento do vídeo…")
            return
        # Somente a imagem do vídeo chega ao widget de exibição.
        self.visor.receber_imagem(imagem.copy(recorte))
        self._titulo_origem = fonte.titulo
        self._aplicar_estado("transmitindo", "Vídeo ao vivo · ajuste automático")

    def abrir_extensao(self) -> None:
        pasta = Path(__file__).resolve().parents[2] / "extençao_google"
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pasta)))
        QMessageBox.information(self, "Atualizar extensão da Laylay",
            "No Chrome ou Brave, abra chrome://extensions. No Edge, abra edge://extensions.\n\n"
            "No cartão Laylay Chrome Extension, clique em Recarregar. O streaming faz parte dessa extensão.\n\n"
            "Se ainda não estiver instalada: Modo do desenvolvedor → Carregar sem compactação → escolha a pasta extençao_google.\n\n"
            "Desative a antiga Laylay Streaming Local, se estiver instalada. Depois, volte à página do vídeo.")

    def _aplicar_estado(self, estado: str, mensagem: str) -> None:
        ativo = estado in {"iniciando", "transmitindo"}
        confirmado = estado == "transmitindo" and not self.visor.imagem.isNull()
        if estado == "transmitindo" and not confirmado:
            mensagem = "Aguardando enquadramento válido do vídeo…"
        cor = "#73D9BD" if confirmado else "#F0A3AD" if estado == "erro" else "#A8AFC4"
        self.estado.setStyleSheet(f"color: {cor};")
        if confirmado:
            mensagem = f"● {mensagem} · {self._titulo_origem}"
        self.estado.setText(mensagem)
        self.janelas.setEnabled(not ativo)
        self.atualizar.setEnabled(not ativo)
        self.transmitir.setEnabled(not ativo and bool(self._janelas))
        self.parar.setEnabled(ativo)
        for botao in (self.flutuante, self.tela_cheia):
            botao.setEnabled(confirmado)
        if not ativo:
            self.visor.limpar()
            if self._popup is not None:
                self._popup.close()

    def abrir_player(self, tela_cheia: bool = False) -> None:
        if self.captura.estado != "transmitindo" or self._popup is not None:
            return
        if self._expandir_no_host is not None:
            self._expandir_no_host(tela_cheia)
            return
        popup = QDialog(self)
        popup.setWindowTitle("Streaming Laylay")
        popup.resize(960, 580)
        popup.setStyleSheet("background: #080B12; color: #EEEAFB;")
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(0, 0, 0, 0)
        self._visor_layout.removeWidget(self.visor)
        layout.addWidget(self.visor)
        dica = QLabel("Esc para voltar à aba · Reprodução e áudio no navegador")
        dica.setAlignment(Qt.AlignCenter)
        layout.addWidget(dica)
        QShortcut(QKeySequence("Escape"), popup, activated=popup.close)
        popup.finished.connect(self._restaurar_player)
        self._popup = popup
        if tela_cheia:
            popup.showFullScreen()
        else:
            popup.show()

    def _restaurar_player(self, resultado: int = 0) -> None:
        popup, self._popup = self._popup, None
        if popup is not None:
            popup.layout().removeWidget(self.visor)
            self._visor_layout.addWidget(self.visor)
            self.visor.show()
            popup.deleteLater()

    def encerrar(self) -> None:
        self._chave_ativa = ""
        self.captura.parar()

    def fechar(self) -> None:
        self._prazo_conexao.stop()
        self.encerrar()
        self.fontes.encerrar()

    def hideEvent(self, event) -> None:  # noqa: N802
        self.encerrar()
        super().hideEvent(event)
