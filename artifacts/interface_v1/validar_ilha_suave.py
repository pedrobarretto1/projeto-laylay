"""Provas Windows de captura própria embutida e prazo real de20s, sem IA."""
from __future__ import annotations
import hashlib
import json
import time
from pathlib import Path


def validar_ilha_suave(janela, js, aguardar, foto, evidencias: Path | None = None) -> dict:
    from PySide6.QtCore import QPoint, QRect, Qt, QTimer, QUrl
    from PySide6.QtGui import QCursor, QPainter, QColor
    from PySide6.QtNetwork import QAbstractSocket
    from PySide6.QtWebSockets import QWebSocket
    from PySide6.QtWidgets import QWidget, QApplication, QDialog
    from PySide6.QtTest import QTest
    import cliente.terminal_2.streaming as streaming

    class VideoProprio(QWidget):
        def paintEvent(self, evento):
            pintor = QPainter(self)
            pintor.fillRect(self.rect(), QColor('#151d36'))
            instante = int(time.monotonic()*75)
            pintor.fillRect(instante % 340, 65, 80, 90, QColor.fromHsv(instante % 360, 150, 230))
            pintor.setPen(QColor('#e9def9'))
            pintor.drawText(18, 30, 'Captura local de uma janela de teste')
            pintor.drawText(18, 210, f'Quadro {instante}')
            pintor.end()

    fonte = VideoProprio(None, Qt.Window | Qt.FramelessWindowHint)
    fonte.setWindowTitle('Laylay prova local de Streaming ' + str(id(fonte)))
    area = janela.screen().availableGeometry()
    fonte.setGeometry(area.left()+25, area.bottom()-280, 420, 240)
    tick = QTimer(fonte)
    tick.setInterval(50)
    tick.timeout.connect(fonte.update)
    socket = QWebSocket('chrome-extension://'+'a'*32)
    mensagens = QTimer(fonte)
    mensagens.setInterval(100)
    original_fontes = streaming.FontesStreaming
    original_viewport = janela.definir_viewport_streaming
    trace = []
    atividade_original = janela.registrar_atividade_desktop
    ultima_atividade = [0.0]
    renovacoes = [0]
    def atividade_observada():
        ultima_atividade[0] = time.monotonic()
        renovacoes[0] += 1
        atividade_original()
    janela.registrar_atividade_desktop = atividade_observada
    def viewport_observado(dados):
        antes = janela._streaming_pagina.captura.estado if janela._streaming_pagina else None
        resposta = original_viewport(dados)
        depois = janela._streaming_pagina.captura.estado if janela._streaming_pagina else None
        trace.append({'tipo':'viewport','rect':json.loads(dados),'web':[janela.web.width(),janela.web.height()],
                      'aceito':resposta,'captura_antes':antes,'captura_depois':depois})
        return resposta
    janela.definir_viewport_streaming = viewport_observado
    # Porta efêmera somente nesta prova; não disputa a extensão do usuário.
    streaming.FontesStreaming = lambda parent=None: original_fontes(parent, porta=0)
    try:
        fonte.show()
        tick.start()
        js("LaylayInterface.goMode('desktop');LaylayInterface.goPage('streaming')")
        QTest.qWait(650)
        antes = set(QApplication.topLevelWidgets())
        js("document.querySelector('[data-tp-action=streaming-open]').click()")
        aguardar(lambda: janela._streaming_pagina is not None and janela._streaming_pagina.isVisible())
        pagina = janela._streaming_pagina
        pagina.captura.estado_alterado.connect(lambda estado,mensagem: trace.append({'tipo':'captura','estado':estado,'mensagem':mensagem}))
        assert pagina.window() is janela
        hwnd = int(janela.winId())
        porta = pagina.fontes._servidor.serverPort()
        assert porta > 0
        socket.open(QUrl(f'ws://127.0.0.1:{porta}'))
        aguardar(lambda: socket.state() == QAbstractSocket.ConnectedState)
        socket.sendTextMessage(json.dumps({'type':'streaming_hello','version':1}))

        def publicar_geometria():
            fator = fonte.devicePixelRatioF()
            dados = {'type':'videos','title':fonte.windowTitle(),'windowId':'prova','tabId':1,
                     'viewport':{'outerWidth':fonte.width(),'outerHeight':fonte.height(),
                                 'innerWidth':fonte.width(),'innerHeight':fonte.height(),'dpr':fator,'zoom':1},
                     'videos':[{'id':'local','label':'Janela própria animada','playing':True,
                                'x':0,'y':0,'width':fonte.width(),'height':fonte.height()}]}
            socket.sendTextMessage(json.dumps(dados))
        mensagens.timeout.connect(publicar_geometria)
        mensagens.start()
        publicar_geometria()
        aguardar(lambda: pagina.janelas.count() == 1)
        pagina.janelas.setCurrentIndex(0)
        QTest.mouseClick(pagina.transmitir, Qt.LeftButton)
        aguardar(lambda: pagina.captura.estado == 'transmitindo' and not pagina.visor.imagem.isNull(), 15)
        hashes = set()
        for _ in range(15):
            imagem = pagina.visor.imagem
            hashes.add(hashlib.sha256(bytes(imagem.constBits())).hexdigest())
            QTest.qWait(90)
        assert len(hashes) >= 6, 'Captura embutida não apresentou quadros diferentes'
        assert pagina.window() is janela and int(janela.winId()) == hwnd
        assert not any(isinstance(w,QDialog) and w.isVisible() for w in set(QApplication.topLevelWidgets())-antes)
        foto('desktop-streaming-integrado-ao-vivo')
        geometria_ampla = QRect(janela.geometry())
        janela.resize(390, 760)
        QTest.qWait(850)
        assert janela._streaming_host.horizontalScrollBar().maximum() == 0, 'Player nativo transbordou em390px'
        assert pagina.width() <= janela._streaming_host.viewport().width()
        assert pagina.captura.estado == 'transmitindo'
        foto('desktop-streaming-integrado-390')
        janela.setGeometry(geometria_ampla)
        QTest.qWait(850)
        assert pagina.captura.estado == 'transmitindo'
        for grande in (False, True):
            pagina.abrir_player(grande)
            QTest.qWait(450)
            assert pagina.visor.window() is janela and int(janela.winId()) == hwnd
            assert pagina._popup is None, 'Ampliar player criou janela separada'
            assert pagina.captura.estado == 'transmitindo' and not pagina.visor.imagem.isNull(), 'Ampliar perdeu a captura ativa'
            assert not any(isinstance(w,QDialog) and w.isVisible() for w in set(QApplication.topLevelWidgets())-antes)
            foto('desktop-streaming-ampliado-' + str(grande).lower())
            QTest.keyClick(pagina, Qt.Key_Escape)
            QTest.qWait(250)
            assert pagina.captura.estado == 'transmitindo', 'Retornar do vídeo ampliado interrompeu a captura'
        js("LaylayInterface.goPage('home')")
        aguardar(lambda: not pagina.isVisible() and pagina.captura.estado == 'parado')
        assert pagina.visor.imagem.isNull()
        js("LaylayInterface.goPage('chat')")
        QTest.qWait(600)
        janela.ativar_desktop()
        js("document.getElementById('composer-input').focus()")
        receptor = janela.web.focusProxy() or janela.web
        QTest.keyClicks(receptor, 'Rascunho preservado apos vinte segundos')
        aguardar(lambda: js("LaylayInterface.state.draft==='Rascunho preservado apos vinte segundos'"))
        js("LaylayInterface.goPage('streaming')")
        QTest.qWait(650)
        js("document.querySelector('[data-tp-action=streaming-open]').click()")
        aguardar(lambda: pagina.isVisible())
        pagina.janelas.setCurrentIndex(0)
        QTest.mouseClick(pagina.transmitir, Qt.LeftButton)
        aguardar(lambda: pagina.captura.estado == 'transmitindo' and not pagina.visor.imagem.isNull(), 15)
        QCursor.setPos(area.bottomRight()-QPoint(20,20))
        janela.registrar_atividade_desktop()
        inicio = time.monotonic()
        renovacoes_antes = renovacoes[0]
        # O usuário pode continuar usando o desktop durante a prova. O prazo
        # começa no último gesto real, e esse gesto precisa continuar valendo.
        # Ignorá-lo ou parar o observador do cursor criaria um verde artificial.
        while janela.estado_desktop == 'expanded' and time.monotonic()-inicio < 90:
            if time.monotonic()-ultima_atividade[0] < 19.5:
                assert pagina.captura.estado == 'transmitindo', 'Captura terminou antes do prazo'
            QTest.qWait(100)
        assert janela.estado_desktop == 'compact', 'Não houve 20s de inatividade confirmável durante a janela da prova'
        duracao = time.monotonic()-ultima_atividade[0]
        assert 19.9 <= duracao <= 22.5
        QTest.qWait(600)
        assert pagina.captura.estado == 'parado' and pagina.visor.imagem.isNull(), 'Recolhimento não encerrou a captura'
        foto('desktop-recolhido-apos-20s')
        assert js("LaylayInterface.state.draft==='Rascunho preservado apos vinte segundos'")
        janela.expandir_desktop(fixar=True)
        QTest.qWait(650)
        js("LaylayInterface.goPage('chat')")
        QTest.qWait(650)
        assert js("document.getElementById('composer-input').value==='Rascunho preservado apos vinte segundos'")
        return {'captura_nativa_de_janela_propria':True,'selecao_e_transmitir_caminho_real':True,
                'fonte_websocket_local_real':True,'quadros_distintos':len(hashes),
                'player_e_ampliacao_na_mesma_janela':True,'captura_para_ao_sair':True,
                'player_nativo_390_sem_overflow':True,
                'inatividade_real_segundos':round(duracao,3),'frames_ao_vivo_nao_renovam_prazo':True,'rascunho_preservado':True,
                'renovacoes_por_gesto_durante_espera':renovacoes[0]-renovacoes_antes,
                'mente_iniciada':False,'browser_real_nao_exercitado':True}
    finally:
        janela.registrar_atividade_desktop = atividade_original
        janela.definir_viewport_streaming = original_viewport
        if evidencias is not None:
            (evidencias/'trace_player.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
        streaming.FontesStreaming = original_fontes
        mensagens.stop()
        tick.stop()
        socket.close()
        janela.parar_streaming()
        # A fonte em porta efêmera pertence apenas à prova. A inspeção que
        # segue deve poder criar o player oficial com a porta normal da extensão.
        if janela._streaming_pagina is not None:
            janela._streaming_pagina.fechar()
            janela._streaming_host.deleteLater()
            janela._streaming_pagina = None
            janela._streaming_host = None
        fonte.close()
