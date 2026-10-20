"""A projeção periódica preserva nós, animação e entrega da conversa real."""
from __future__ import annotations

import json
from pathlib import Path
import time

import pytest

pytest.importorskip("PySide6.QtWebEngineWidgets")


@pytest.fixture
def conversa_web(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --no-sandbox")
    monkeypatch.delenv("LAYLAY_REDUZIR_MOVIMENTO", raising=False)
    from PySide6.QtCore import QSettings, QThread
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    import cliente.terminal_laylay_2 as terminal
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1
    from mente_laylay.integracao.desktop_bridge import DesktopBridgeRuntime

    monkeypatch.setattr(terminal, "QSettings", lambda *_: QSettings(str(tmp_path / "ui.ini"), QSettings.IniFormat))
    app = QApplication.instance() or QApplication([])
    entradas = []
    ponte = DesktopBridgeRuntime(enviar_entrada=entradas.append, historico_getter=lambda: [],
        estado_getter=lambda: {"activity": "idle", "interaction_mode": "chat"},
        conversas_getter=lambda: [{"id": "11111111111111111111111111111111", "titulo": "Conversa estável", "status": "ativa"}],
        conversa_ativa_getter=lambda: "11111111111111111111111111111111", configuracao_getter=lambda: {}, log=lambda _: None)
    ponte.iniciar()
    worker = terminal.PonteWorker(*ponte.endereco, ponte.token, session_id=ponte.session_id)
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.executar)
    worker.terminou.connect(thread.quit)
    janela = JanelaInterfaceWebV1(worker, Path(__file__).parents[2], session_id=ponte.session_id)

    def aguardar(condicao):
        limite = time.monotonic() + 8
        while not condicao() and time.monotonic() < limite:
            QTest.qWait(20)
        assert condicao(), "O caminho real da conversa não chegou ao estado esperado"

    def js(codigo):
        resposta = []
        janela.web.page().runJavaScript(codigo, resposta.append)
        aguardar(lambda: bool(resposta))
        return resposta[0]

    try:
        janela.show()
        thread.start()
        aguardar(lambda: js("!!window.LaylayInterface?.state.connected"))
        js("LaylayInterface.goPage('chat')")
        yield janela, ponte, entradas, js, aguardar
    finally:
        janela.close()
        worker.parar()
        ponte.parar()
        thread.quit()
        assert thread.wait(3000)
        app.processEvents()


def test_ticks_preservam_identidade_feed_compositor_mascote_e_animacao(conversa_web):
    janela, ponte, entradas, js, aguardar = conversa_web
    from PySide6.QtTest import QTest

    js("LaylayInterface.request('texto',{text:'Uma mensagem pelo transporte real'})")
    aguardar(lambda: entradas == ["Uma mensagem pelo transporte real"])
    assert ponte.publicar_fala_final("Esta resposta deve permanecer parada.")
    aguardar(lambda: js("!!document.querySelector('.message:not(.user)')"))
    js("""(() => {
      const input=document.getElementById('composer-input');input.value='Rascunho com cursor';
      input.dispatchEvent(new Event('input',{bubbles:true}));input.focus();input.setSelectionRange(5,8);
      window.prova={feed:document.getElementById('chat-history'),input,
        message:document.querySelector('.message:not(.user)'),avatar:document.querySelector('.message:not(.user) .avatar')};
      prova.animation=prova.message.getAnimations()[0];prova.clock=prova.animation?.currentTime;
      return true;
    })()""")
    for indice in range(6):
        # Fixtures de observação: não autorizam efeitos e acompanham uma mensagem realmente transportada.
        eventos = [
            {"type": "dashboard_state", "dashboard": {"system": {"cpu": indice + 12}, "music": {"state": "playing", "title": "Observação", "position_seconds": indice}}},
            {"type": "state", "activity": "idle", "activity_label": "Pronta", "emotion": "calma", "voice_available": True},
            {"type": "music_meter", "available": True, "rms": .25, "peak": .5, "sequence": indice},
            {"type": "dev_events", "events": [{"id": str(indice), "category": "SYSTEM", "level": "info", "message": "Observação periódica"}]},
        ]
        js("(" + json.dumps(eventos) + ").forEach(LaylayInterface.receiveEvent)")
        QTest.qWait(80)
    observado = json.loads(js("""JSON.stringify((() => ({
      feed:prova.feed===document.getElementById('chat-history'),
      input:prova.input===document.getElementById('composer-input'),
      message:prova.message===document.querySelector('.message:not(.user)'),
      avatar:prova.avatar===document.querySelector('.message:not(.user) .avatar'),
      animation:!!prova.animation&&prova.animation===prova.message.getAnimations()[0],
      advanced:!!prova.animation&&prova.animation.currentTime>=prova.clock,
      draft:prova.input.value,cursor:[prova.input.selectionStart,prova.input.selectionEnd],focused:document.activeElement===prova.input,
      status:document.querySelector('.titlebar .status').textContent
    }))())"""))
    assert observado["feed"] and observado["message"], observado
    assert observado["input"] and observado["avatar"], observado
    assert observado["animation"] and observado["advanced"], observado
    assert observado["draft"] == "Rascunho com cursor"
    assert observado["cursor"] == [5, 8] and observado["focused"]
    assert "Pronta" in observado["status"]


def test_snapshot_preserva_entrega_falha_resposta_e_retry(conversa_web):
    _janela, _ponte, _entradas, js, aguardar = conversa_web
    mensagens = [{"id": "falhou", "role": "user", "text": "Entrada recusada", "status": "failed"},
                 {"id": "respondeu", "role": "user", "text": "Entrada respondida", "status": "responded"},
                 {"id": "respondeu", "role": "assistant", "text": "Resposta confirmada", "status": "accepted"}]
    evento = {"type": "snapshot", "messages": mensagens, "state": {"activity": "idle"}}
    js("LaylayInterface.receiveEvent(" + json.dumps(evento) + ")")
    aguardar(lambda: js("document.querySelectorAll('.message').length===3"))
    assert js("LaylayInterface.state.messages.find(m=>m.id==='falhou').delivery") == "failed"
    assert js("!!document.querySelector('[data-retry=falhou]')")
    assert js("LaylayInterface.state.messages.find(m=>m.id==='respondeu'&&m.role==='user').delivery") == "responded"


def test_receipts_append_e_stream_preservam_mensagens_anteriores_e_scroll(conversa_web):
    _janela, _ponte, _entradas, js, aguardar = conversa_web
    from PySide6.QtTest import QTest

    messages = [{"id": str(i), "role": "assistant", "text": "Uma mensagem anterior, com conteúdo para ocupar o histórico. " * 8} for i in range(14)]
    js("LaylayInterface.receiveEvent(" + json.dumps({"type": "snapshot", "messages": messages, "state": {"activity": "idle"}}) + ")")
    aguardar(lambda: js("document.querySelectorAll('.message').length===14"))
    js("""window.primeira=document.querySelector('.message');window.feed=document.getElementById('chat-history');
      feed.scrollTop=40;window.posicao=feed.scrollTop;
      LaylayInterface.receiveEvent({type:'pedido_enviado',id:'novo',kind:'texto',text:'Pedido novo'});""")
    aguardar(lambda: js("document.querySelectorAll('.message').length===15"))
    js("window.enviada=document.querySelector('.message.user');LaylayInterface.receiveEvent({type:'input_ack',id:'novo',accepted:true})")
    QTest.qWait(40)
    assert js("enviada===document.querySelector('.message.user')&&enviada.textContent.includes('Recebida pela mente')")
    js("LaylayInterface.receiveEvent({type:'assistant_message',id:'novo',text:'Primeiro trecho'})")
    aguardar(lambda: js("document.querySelectorAll('.message').length===16"))
    js("window.resposta=document.querySelector('.message:last-child');LaylayInterface.receiveEvent({type:'assistant_message',id:'novo',text:'Primeiro trecho atualizado'})")
    QTest.qWait(40)
    assert js("primeira===document.querySelector('.message')&&enviada===document.querySelector('.message.user')")
    assert js("resposta===document.querySelector('.message:last-child')&&resposta.textContent.includes('atualizado')")
    assert js("feed.scrollTop===posicao")
    assert js("enviada.textContent.includes('Resposta recebida')")
    assert js("!!resposta.getAnimations()[0]")
    # IDs iguais em outra conversa não reutilizam a bolha da conversa anterior.
    outra = {"type": "conversations_state", "success": True, "action": "select", "conversations": {"active_id": "22222222222222222222222222222222", "items": [], "messages": [{"id": "novo", "role": "assistant", "content": "Outra conversa"}]}}
    js("LaylayInterface.receiveEvent(" + json.dumps(outra) + ")")
    aguardar(lambda: js("document.querySelectorAll('.message').length===1"))
    assert js("resposta!==document.querySelector('.message')&&document.querySelector('.message').textContent.includes('Outra conversa')")
    js("LaylayInterface.goPage('home')")
    assert js("!!document.querySelector('.presence .avatar')&&!document.querySelector('.chat-history')")
    js("LaylayInterface.goPage('chat');LaylayInterface.goMode('quick')")
    assert js("!!document.querySelector('.quick-window')&&document.querySelectorAll('.message').length===1")


def test_inicio_preserva_mascote_piscada_olhar_play_e_reatividade(conversa_web):
    _janela, _ponte, _entradas, js, aguardar = conversa_web
    from PySide6.QtTest import QTest

    dashboard = {"music": {"state": "playing", "title": "Faixa observada", "channel": "Canal", "freshness": "fresh", "controls_available": True, "duration_seconds": 180, "position_seconds": 20}}
    js("LaylayInterface.goPage('home');LaylayInterface.receiveEvent(" + json.dumps({"type": "dashboard_state", "dashboard": dashboard}) + ")")
    QTest.qWait(40)
    js("""window.inicio={page:document.getElementById('page-content'),mascot:document.querySelector('.presence .avatar'),
      eye:document.querySelector('.presence .eye'),smile:document.querySelector('.presence .smile'),play:document.querySelector('.music-play')};
      inicio.animation=inicio.mascot.getAnimations()[0];inicio.clock=inicio.animation.currentTime;
      inicio.mascot.style.setProperty('--look-x','3.500px');inicio.mascot.style.setProperty('--look-y','1.250px');
      inicio.mascot.classList.add('is-blinking');inicio.top=inicio.page.scrollTop;
      window.scrollCalls=0;window.scrollOriginal=Element.prototype.scrollIntoView;
      Element.prototype.scrollIntoView=function(...args){scrollCalls++;return scrollOriginal.apply(this,args)};
    """)
    for _ in range(4):
        js("LaylayInterface.receiveEvent({type:'state',activity:'idle',activity_label:'Pronta'});LaylayInterface.receiveEvent({type:'dev_events',events:[]});")
        QTest.qWait(60)
    assert js("inicio.mascot===document.querySelector('.presence .avatar')&&inicio.eye===document.querySelector('.presence .eye')&&inicio.smile===document.querySelector('.presence .smile')")
    assert js("inicio.animation===inicio.mascot.getAnimations()[0]&&inicio.animation.currentTime>inicio.clock")
    assert js("inicio.mascot.classList.contains('is-blinking')&&inicio.mascot.style.getPropertyValue('--look-x')==='3.500px'")
    assert js("inicio.play===document.querySelector('.music-play')&&inicio.page.scrollTop===inicio.top&&scrollCalls===0")
    dashboard["music"].update(state="paused", title="Estado novo confirmado", position_seconds=45)
    js("LaylayInterface.receiveEvent(" + json.dumps({"type": "dashboard_state", "dashboard": dashboard}) + ")")
    aguardar(lambda: js("document.querySelector('.music-info h3').textContent==='Estado novo confirmado'"))
    assert js("inicio.play===document.querySelector('.music-play')&&inicio.play.getAttribute('aria-label')==='Continuar música'")
    assert js("document.querySelector('.music-card .progress span').style.width==='25%'")
    js("Element.prototype.scrollIntoView=scrollOriginal")


@pytest.mark.parametrize("pagina", ["music", "system", "dev", "memory", "settings", "lamp", "streaming"])
def test_paginas_compartilham_projecao_estavel_e_preservam_dialogo(conversa_web, pagina):
    _janela, _ponte, _entradas, js, aguardar = conversa_web
    from PySide6.QtTest import QTest

    js("LaylayInterface.goPage(" + json.dumps(pagina) + ")")
    aguardar(lambda: js("!!document.querySelector('#page-content .page-heading')"))
    js("""window.pagina={root:document.querySelector('#page-content'),first:document.querySelector('#page-content').firstElementChild,
      button:document.querySelector('#page-content button'),input:document.querySelector('#page-content input:not([type=range]):not([type=checkbox])')};
      pagina.root.scrollTop=31;pagina.scrolls=[['antes_foco',pagina.root.scrollTop]];
      if(pagina.input){pagina.input.focus();pagina.input.value='Texto local ainda em edição';pagina.input.dispatchEvent(new Event('input',{bubbles:true}));}
      pagina.scrolls.push(['depois_foco',pagina.root.scrollTop]);
      LaylayInterface.confirm('Confirmação de teste','Este diálogo não executa nenhuma ação.',()=>{});
      window.dialog=document.querySelector('#confirm-dialog');
      pagina.scrolls.push(['depois_modal',pagina.root.scrollTop]);
      // Focar o prompt pode rolar legitimamente para revelá-lo. O contrato começa
      // após o gesto do usuário, antes das publicações periódicas do runtime.
      pagina.top=pagina.root.scrollTop;
    """)
    for indice in range(3):
        js("LaylayInterface.receiveEvent(" + json.dumps({"type": "dev_events", "events": [{"id": "test:"+str(indice), "category": "SYSTEM", "depth": "normal", "level": "info", "message": "Evento de observação"}]}) + ");LaylayInterface.receiveEvent({type:'state',activity:'idle'})")
        QTest.qWait(50)
        js("pagina.scrolls.push(['tick',pagina.root.scrollTop])")
        assert js("pagina.root.scrollTop===pagina.top"), js("JSON.stringify(pagina.scrolls)")
    assert js("pagina.root===document.querySelector('#page-content')&&pagina.first===pagina.root.firstElementChild")
    assert js("!pagina.button||pagina.button===document.querySelector('#page-content button')")
    assert js("!pagina.input||(pagina.input===document.querySelector('#page-content input:not([type=range]):not([type=checkbox])')&&pagina.input.value==='Texto local ainda em edição')")
    assert js("dialog===document.querySelector('#confirm-dialog')&&dialog.open&&pagina.root.scrollTop===pagina.top"), js("JSON.stringify(pagina.scrolls)")
    js("dialog.close()")


def test_receipt_configuracao_atualiza_valor_controlado_sem_recriar_input(conversa_web):
    _janela, ponte, _entradas, js, aguardar = conversa_web

    # A abertura dispara settings_get no transporte real: aguardar essa leitura
    # evita que uma resposta vazia antiga concorra com o receipt da edição abaixo.
    ponte.configuracao_getter = lambda: {"provider": "ollama", "model": "antigo"}
    js("LaylayInterface.goPage('settings')")
    aguardar(lambda: js("LaylayInterface.state.settings.model==='antigo'"))
    aguardar(lambda: js("document.querySelector('[data-tp-input=model]')?.getAttribute('value')==='antigo'"))
    assert js("document.querySelector('[data-tp-input=model]').value") == "antigo"
    js("""window.modelInput=document.querySelector('[data-tp-input=model]');modelInput.value='Rascunho sem envio';
      modelInput.dispatchEvent(new Event('input',{bubbles:true}));modelInput.blur();
      LaylayInterface.receiveEvent({type:'state',activity:'idle',activity_label:'Pronta'});
      LaylayInterface.receiveEvent({type:'dashboard_state',dashboard:{system:{cpu_percent:{value:42}}}});
      LaylayInterface.receiveEvent({type:'settings_state',settings:{provider:'ollama',model:'leitura durante edição'}});
    """)
    aguardar(lambda: js("LaylayInterface.state.settings.model==='leitura durante edição'"))
    assert js("modelInput===document.querySelector('[data-tp-input=model]')&&modelInput.value==='Rascunho sem envio'")
    js("LaylayInterface.receiveEvent({type:'settings_result',saved:true,settings:{provider:'ollama',model:'novo-confirmado'}})")
    aguardar(lambda: js("document.querySelector('[data-tp-input=model]').value==='novo-confirmado'"))
    assert js("modelInput===document.querySelector('[data-tp-input=model]')")
    # Atributos iguais não tornam um campo editado equivalente ao valor confirmado.
    js("modelInput.value='Outro rascunho';LaylayInterface.receiveEvent({type:'settings_result',saved:true,settings:{provider:'ollama',model:'novo-confirmado'}})")
    aguardar(lambda: js("modelInput.value==='novo-confirmado'"))
    assert js("modelInput===document.querySelector('[data-tp-input=model]')")


def test_observacoes_em_burst_nao_renderizam_sincronamente_nem_bloqueiam_receipt(conversa_web):
    _janela, _ponte, _entradas, js, aguardar = conversa_web
    from PySide6.QtTest import QTest

    # Uma conversa longa já carregada não precisa ser reprojectada para exibir logs em outra página.
    messages = [{"id": str(i), "role": "assistant", "text": "Histórico de conversa para validar o custo das observações."} for i in range(200)]
    js("LaylayInterface.receiveEvent(" + json.dumps({"type": "snapshot", "messages": messages}) + ")")
    QTest.qWait(50)
    js("""window.templateCount=0;window.originalCreate=document.createElement.bind(document);
      document.createElement=function(name,...args){if(name==='template')templateCount++;return originalCreate(name,...args)};
      for(let i=0;i<30;i++){
        LaylayInterface.receiveEvent({type:'music_meter',levels:[.2,.3,.4],video_id:'abcdefghijk',observed_at:Date.now()/1000});
        LaylayInterface.receiveEvent({type:'dev_events',events:[{id:'burst:'+i,category:'SYSTEM',level:'info',message:'Log ao vivo'}]});
      }
      window.synchronousTemplates=templateCount;
    """)
    assert js("synchronousTemplates") == 0
    QTest.qWait(50)
    assert js("templateCount") == 0
    # O estado crítico é consumido imediatamente mesmo entre observações; só a pintura é agrupada.
    js("""LaylayInterface.receiveEvent({type:'pedido_enviado',id:'critico',kind:'texto',text:'Pedido de teste'});
      LaylayInterface.receiveEvent({type:'assistant_message',id:'critico',text:'Receipt observado sem espera'});
      window.criticalImmediate=LaylayInterface.state.messages.some(m=>m.id==='critico'&&m.role==='assistant');
    """)
    assert js("criticalImmediate")
    aguardar(lambda: js("document.querySelector('.chat-history').textContent.includes('Receipt observado sem espera')"))
    assert js("templateCount") == 1
    js("document.createElement=originalCreate;LaylayInterface.goPage('dev')")
    assert js("document.querySelector('.tp-console').textContent.includes('Log ao vivo')")


def test_invalidacoes_visiveis_sao_agrupadas_em_um_frame_sem_perder_ultima_leitura(conversa_web):
    _janela, _ponte, _entradas, js, aguardar = conversa_web
    from PySide6.QtTest import QTest

    js("LaylayInterface.goPage('dev')")
    QTest.qWait(40)
    js("""window.templateCount=0;window.originalCreate=document.createElement.bind(document);
      document.createElement=function(name,...args){if(name==='template')templateCount++;return originalCreate(name,...args)};
      for(let i=0;i<25;i++){
        LaylayInterface.receiveEvent({type:'dev_events',events:[{id:'visible:'+i,category:'SYSTEM',level:'info',message:'Evento '+i}]});
        LaylayInterface.receiveEvent({type:'dashboard_state',dashboard:{system:{cpu_percent:{value:i,freshness:'fresh',observed_at:1000+i}}}});
      }
      window.synchronousTemplates=templateCount;
    """)
    assert js("synchronousTemplates") == 0
    aguardar(lambda: js("templateCount>0&&document.querySelector('.tp-console').textContent.includes('Evento 24')"))
    assert js("templateCount") == 1
    assert js("LaylayInterface.state.dashboard.system.cpu_percent.value") == 24
    assert js("document.querySelector('.tp-console').textContent.includes('Evento 24')")
    js("document.createElement=originalCreate")
