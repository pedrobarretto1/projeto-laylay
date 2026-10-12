"""Streaming local deve existir mesmo sem conexão com a mente."""
from pathlib import Path

import pytest


@pytest.fixture
def janela(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "1")
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_laylay_2 import JanelaLaylay

    class Worker(QObject):
        mensagem = Signal(dict)
        conectado = Signal(bool)
        falha = Signal(str)

        def enfileirar(self, mensagem):
            return True

        def parar(self):
            pass

    app = QApplication.instance() or QApplication([])
    worker = Worker()
    tela = JanelaLaylay(worker, Path(__file__).parents[2])
    tela.show()
    app.processEvents()
    yield app, tela
    tela.close()
    app.processEvents()


def test_aba_streaming_tem_rota_propria_e_carrega_sem_ia(janela):
    from PySide6.QtTest import QTest
    app, tela = janela
    enviados = []
    tela.enviar_json.connect(enviados.append)
    assert not tela._conectado
    assert "streaming" not in tela._paginas_carregadas
    tela.selecionar_pagina("streaming")
    assert tela.titulo_header.text() == "Streaming"
    QTest.qWait(40)
    app.processEvents()
    assert tela.paginas.currentWidget() is tela._paginas_carregadas["streaming"]
    assert enviados == []


@pytest.mark.parametrize("dashboard", [
    {"schema_version": 1, "health": {}},
    {"schema_version": 1, "health": {}, "system": {
        "cpu_percent": {"value": 27, "unit": "%", "freshness": "fresh", "observed_at": 1000},
    }},
])
def test_dashboard_da_mente_nao_altera_aba_streaming_independente(janela, dashboard):
    app, tela = janela
    tela.selecionar_pagina("streaming")
    pagina = tela._garantir_pagina_carregada("streaming")
    estado_local = pagina.estado.text()
    geracao_local = pagina.captura._geracao
    assert not hasattr(pagina, "aplicar_dashboard")
    enviados = []
    tela.enviar_json.connect(enviados.append)
    # Mesmo handler conectado ao sinal do transporte real do Terminal.
    tela.receber({"type": "dashboard_state", "dashboard": dashboard})
    assert tela._dashboard_mais_recente == dashboard
    assert tela.paginas.currentWidget() is pagina
    assert pagina.estado.text() == estado_local
    assert pagina.captura._geracao == geracao_local
    assert enviados == []


def test_desconexao_da_mente_preserva_aba_streaming_independente(janela):
    app, tela = janela
    tela.selecionar_pagina("streaming")
    pagina = tela._garantir_pagina_carregada("streaming")
    estado_local = pagina.estado.text()
    geracao_local = pagina.captura._geracao
    assert not hasattr(pagina, "invalidar")
    tela.estado_conexao(False)
    assert tela.paginas.currentWidget() is pagina
    assert pagina.estado.text() == estado_local
    assert pagina.captura._geracao == geracao_local


def test_despacho_respeita_paginas_locais_sem_contrato_de_dashboard(janela):
    from PySide6.QtWidgets import QWidget
    app, tela = janela
    # Outro componente Qt real, sem assinatura de consumidor do dashboard.
    pagina_local = QWidget(tela)
    tela._paginas_carregadas["local_independente"] = pagina_local
    tela._aplicar_dashboard_pagina("local_independente", {"health": {}})
    tela.estado_conexao(False)
    assert pagina_local.parent() is tela


def test_dashboard_pela_ponte_real_preserva_streaming_e_desconexao(monkeypatch):
    import os
    import sys
    import time
    from PySide6.QtCore import QThread
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_laylay_2 import JanelaLaylay, PonteWorker
    from mente_laylay.integracao.desktop_bridge import DesktopBridgeRuntime

    nativo = os.environ.get("LAYLAY_TESTE_QT_NATIVO") == "1"
    if not nativo:
        monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "1")
    app = QApplication.instance() or QApplication([])
    if nativo:
        assert app.platformName() == "windows"
    erros_slots = []
    monkeypatch.setattr(sys, "excepthook", lambda tipo, erro, tb: erros_slots.append(erro))
    entradas = []
    mensagens = []
    cpu = [10]

    def dashboard():
        return {"schema_version": 1, "system": {
            "cpu_percent": {"value": cpu[0], "unit": "%", "freshness": "fresh",
                            "observed_at": time.time()},
        }}

    ponte = DesktopBridgeRuntime(
        enviar_entrada=entradas.append, historico_getter=lambda: [],
        estado_getter=lambda: {}, dashboard_getter=dashboard,
        dashboard_interval_s=0.25, log=lambda texto: None,
    )
    ponte.iniciar()
    worker = PonteWorker(*ponte.endereco, ponte.token, session_id=ponte.session_id)
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.executar)
    worker.terminou.connect(thread.quit)
    worker.mensagem.connect(mensagens.append)
    tela = JanelaLaylay(worker, Path(__file__).parents[2], session_id=ponte.session_id)

    def aguardar(condicao):
        prazo = time.monotonic() + 4
        while not condicao() and time.monotonic() < prazo:
            QTest.qWait(25)
        assert condicao(), "A ponte real não entregou o estado esperado"

    try:
        tela.show()
        tela.selecionar_pagina("streaming")
        pagina = tela._garantir_pagina_carregada("streaming")
        estado_local = pagina.estado.text()
        geracao_local = pagina.captura._geracao
        thread.start()
        aguardar(lambda: tela._conectado and any(
            msg.get("type") == "snapshot" for msg in mensagens
        ))
        # Publicações periódicas reais após o handshake, na rota do log do usuário.
        for valor in (27, 42):
            cpu[0] = valor
            aguardar(lambda: (tela._dashboard_mais_recente or {}).get(
                "system", {}
            ).get("cpu_percent", {}).get("value") == valor)
        assert sum(msg.get("type") == "dashboard_state" for msg in mensagens) >= 2
        ponte.parar()
        aguardar(lambda: not tela._conectado)
        assert tela.paginas.currentWidget() is pagina
        assert pagina.estado.text() == estado_local
        assert pagina.captura._geracao == geracao_local
        assert entradas == []
        assert erros_slots == []
    finally:
        worker.parar()
        ponte.parar()
        thread.quit()
        assert thread.wait(3000), "O worker de transporte não encerrou"
        tela.close()
        app.processEvents()


def test_selecao_e_botoes_locais_nao_publicam_comandos(janela):
    app, tela = janela
    enviados = []
    tela.enviar_json.connect(enviados.append)
    pagina = tela._garantir_pagina_carregada("streaming")
    assert pagina.captura._captura is None
    assert pagina.janelas.currentIndex() == -1
    pagina.iniciar()
    assert "Selecione" in pagina.estado.text()
    assert pagina.captura._captura is None
    assert pagina.visor.imagem.isNull()
    pagina.atualizar_janelas()
    pagina.encerrar()
    assert enviados == []


def test_alvo_invalido_nao_inicia_efeito_nativo(janela):
    from PySide6.QtMultimedia import QCapturableWindow
    from cliente.terminal_2.streaming import CapturaStreaming
    app, tela = janela
    runtime = CapturaStreaming(tela)
    runtime.iniciar(QCapturableWindow())
    assert runtime.estado == "erro"
    assert runtime._captura is None
    assert not runtime._prazo.isActive()


def test_refresh_exige_nova_selecao_sem_reautorizar_por_titulo(janela):
    app, tela = janela
    pagina = tela._garantir_pagina_carregada("streaming")
    if pagina.janelas.count():
        pagina.janelas.setCurrentIndex(0)
    pagina.atualizar_janelas()
    assert pagina.janelas.currentIndex() == -1
    assert pagina.captura._captura is None


def test_status_ao_vivo_exige_frame_real_e_ignora_sessao_anterior(janela):
    from PySide6.QtGui import QColor, QImage
    from PySide6.QtMultimedia import QVideoFrame, QWindowCapture
    from cliente.terminal_2.streaming import CapturaStreaming
    app, tela = janela
    runtime = CapturaStreaming(tela)
    imagens = []
    runtime.imagem_recebida.connect(imagens.append)
    # Componente nativo real; este contrato testa admissão de frames, não start().
    runtime._captura = QWindowCapture(runtime)
    runtime._estado("iniciando", "aguardando")
    runtime._receber_frame(runtime._geracao, QVideoFrame())
    assert runtime.estado == "iniciando"
    assert imagens == []
    imagem = QImage(80, 40, QImage.Format_RGB32)
    imagem.fill(QColor("#25CA85"))
    frame = QVideoFrame(imagem)
    runtime._receber_frame(runtime._geracao, frame)
    assert runtime.estado == "transmitindo"
    assert imagens[0].size() == imagem.size()
    antiga = runtime._geracao
    runtime.parar()
    runtime._receber_frame(antiga, frame)
    assert runtime.estado == "parado"
    assert len(imagens) == 1


def test_falha_ou_timeout_limpa_imagem_e_nao_confirma_sucesso(janela):
    from PySide6.QtGui import QImage
    app, tela = janela
    pagina = tela._garantir_pagina_carregada("streaming")
    pagina.visor.receber_imagem(QImage(64, 32, QImage.Format_RGB32))
    pagina.captura._prazo.timeout.emit()
    assert pagina.captura.estado == "erro"
    assert pagina.visor.imagem.isNull()
    assert not pagina.parar.isEnabled()
    assert not pagina.tela_cheia.isEnabled()
    assert "Nenhuma imagem" in pagina.estado.text()


def test_visor_ajusta_video_sem_distorcer_proporcao(janela):
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QImage
    from cliente.terminal_2.streaming import VisorStreaming
    app, tela = janela
    visor = VisorStreaming()
    visor.resize(400, 400)
    visor.receber_imagem(QImage(800, 400, QImage.Format_RGB32))
    visor.show()
    app.processEvents()
    assert visor._destino() == QRectF(0, 100, 400, 200)
    visor.resize(800, 400)
    assert visor._origem() == QRectF(0, 0, 800, 400)
    assert visor._destino() == QRectF(0, 0, 800, 400)
    visor.close()


def test_player_flutuante_retorna_a_aba_e_saida_encerra_captura(janela):
    from PySide6.QtGui import QImage
    app, tela = janela
    tela.selecionar_pagina("streaming")
    pagina = tela._garantir_pagina_carregada("streaming")
    pagina.visor.receber_imagem(QImage(80, 40, QImage.Format_RGB32))
    pagina.captura._estado("transmitindo", "frame recebido")
    pagina.abrir_player()
    app.processEvents()
    assert pagina._popup is not None
    assert pagina.visor.parent() is pagina._popup
    pagina._popup.close()
    assert pagina._popup is None
    assert pagina.visor.parent() is pagina
    pagina.abrir_player(True)
    tela.selecionar_pagina("conversa")
    app.processEvents()
    assert pagina._popup is None
    assert pagina.captura.estado == "parado"
    assert pagina.visor.imagem.isNull()


def _geometria(**trocas):
    dados = {"type": "videos", "title": "Player de teste", "windowId": 1, "tabId": 7,
             "viewport": {"outerWidth": 800, "outerHeight": 600, "innerWidth": 800,
                          "innerHeight": 520, "dpr": 1, "zoom": 1},
             "videos": [{"id": "video-a", "x": 100, "y": 100, "width": 320,
                         "height": 180, "playing": True, "label": "Vídeo"}]}
    dados.update(trocas)
    return dados


def test_apenas_video_chega_ao_visor_e_resize_e_automatico(janela):
    import json
    from PySide6.QtCore import QRect
    from PySide6.QtGui import QColor, QImage, QPainter
    app, tela = janela
    pagina = tela._garantir_pagina_carregada("streaming")
    dados = _geometria()
    pagina.fontes._receber("teste", json.dumps(dados))
    pagina.janelas.setCurrentIndex(0)
    pagina._chave_ativa = pagina._janelas[0].chave
    imagem = QImage(800, 600, QImage.Format_RGB32)
    imagem.fill(QColor("red"))
    painter = QPainter(imagem)
    painter.fillRect(QRect(100, 180, 320, 180), QColor("blue"))
    painter.end()
    pagina._receber_video(imagem)
    assert pagina.visor.imagem.width() == 320
    assert pagina.visor.imagem.height() == 180
    assert pagina.visor.imagem.pixelColor(0, 0) == QColor("blue")
    assert pagina.visor.imagem.pixelColor(319, 179) == QColor("blue")
    dados["videos"][0].update(width=160, height=90)
    pagina.fontes._receber("teste", json.dumps(dados))
    assert pagina.janelas.currentIndex() == 0
    pagina._receber_video(imagem)
    assert pagina.visor.imagem.width() == 160
    assert pagina.visor.imagem.height() == 90


def test_sem_geometria_valida_nunca_exibe_janela_inteira(janela):
    import json
    from dataclasses import replace
    from time import monotonic
    from PySide6.QtGui import QImage
    app, tela = janela
    pagina = tela._garantir_pagina_carregada("streaming")
    imagem = QImage(800, 600, QImage.Format_RGB32)
    pagina._receber_video(imagem)
    assert pagina.visor.imagem.isNull()
    pagina.fontes._receber("teste", json.dumps(_geometria()))
    pagina._chave_ativa = pagina._janelas[0].chave
    fonte = pagina.fontes.fontes[pagina._chave_ativa]
    pagina.fontes.fontes[fonte.chave] = replace(fonte, recebido_em=monotonic() - 2)
    pagina._receber_video(imagem)
    assert pagina.visor.imagem.isNull()
    assert not pagina.tela_cheia.isEnabled()


def test_geometria_invalida_e_dpi_incompativel_fecham_captura(janela):
    import json
    from time import monotonic
    from cliente.terminal_2.streaming_fontes import decodificar_fontes, calcular_recorte
    dados = _geometria()
    fonte = decodificar_fontes(json.dumps(dados), "teste", monotonic())[0]
    assert calcular_recorte(fonte, 1600, 1200, monotonic()).isEmpty()
    dados["viewport"]["dpr"] = float("nan")
    with pytest.raises(ValueError):
        decodificar_fontes(json.dumps(dados), "teste", monotonic())


def test_canal_local_rejeita_pagina_web_e_aceita_extensao(janela):
    import json
    from PySide6.QtCore import QUrl
    from PySide6.QtNetwork import QAbstractSocket
    from PySide6.QtTest import QTest
    from PySide6.QtWebSockets import QWebSocket
    from cliente.terminal_2.streaming_fontes import FontesStreaming
    app, tela = janela
    servidor = FontesStreaming(tela, porta=0)
    url = QUrl(f"ws://127.0.0.1:{servidor._servidor.serverPort()}")
    pagina_web = QWebSocket("http://site.example")
    pagina_web.open(url)
    QTest.qWait(120)
    assert pagina_web.state() == QAbstractSocket.UnconnectedState
    assert servidor.fontes == {}
    extensao = QWebSocket("chrome-extension://" + "a" * 32)
    extensao.open(url)
    QTest.qWait(120)
    assert extensao.state() == QAbstractSocket.ConnectedState
    extensao.sendTextMessage(json.dumps(_geometria()))
    QTest.qWait(120)
    assert len(servidor.fontes) == 1
    extensao.close()
    QTest.qWait(60)
    assert servidor.fontes == {}
    servidor.encerrar()


def test_extensao_existente_inclui_detector_e_isola_streaming_da_ia():
    import json
    raiz = Path(__file__).parents[2]
    pasta = raiz / "extençao_google"
    manifest = json.loads((pasta / "manifest.json").read_text(encoding="utf-8"))
    detectores = [item for item in manifest["content_scripts"]
                  if "streaming_detector.js" in item["js"]]
    assert len(detectores) == 1, "O vídeo deve ser descoberto pela extensão já instalada"
    assert detectores[0]["all_frames"] is True
    background = (pasta / "background.js").read_text(encoding="utf-8")
    assert 'importScripts("streaming_background.js")' in background
    # O handler da IA deve recusar esse envelope antes de montar outgoing.
    handler = background[background.index("chrome.runtime.onMessage.addListener"):]
    assert handler.index('request?.type === "LAYLAY_STREAMING_LOCAL"') < handler.index("const outgoing")


def test_conexao_da_extensao_sem_video_tem_diagnostico_observavel(janela):
    import json
    from PySide6.QtCore import QUrl
    from PySide6.QtTest import QTest
    from PySide6.QtWebSockets import QWebSocket
    from cliente.terminal_2.streaming_fontes import FontesStreaming
    app, tela = janela
    pagina = tela._garantir_pagina_carregada("streaming")
    pagina.fontes.encerrar()
    pagina.fontes = FontesStreaming(pagina, porta=0)
    pagina.fontes.alteradas.connect(pagina.atualizar_janelas)
    cliente = QWebSocket("chrome-extension://" + "b" * 32)
    try:
        cliente.open(QUrl(f"ws://127.0.0.1:{pagina.fontes._servidor.serverPort()}"))
        QTest.qWait(100)
        cliente.sendTextMessage(json.dumps({"type": "streaming_hello", "version": 1}))
        QTest.qWait(100)
        assert pagina.fontes.conectada
        assert "conectada" in pagina.estado.text().lower()
        assert "vídeo" in pagina.estado.text().lower()
        assert pagina.visor.imagem.isNull()
        assert not pagina.transmitir.isEnabled()
        cliente.close()
        QTest.qWait(60)
        assert not pagina.fontes.conectada
        assert "extensão" in pagina.estado.text().lower()
        assert pagina.visor.imagem.isNull()
    finally:
        cliente.close()
        pagina.fontes.encerrar()


def test_geometria_externa_vem_da_api_do_navegador_e_nao_da_pagina():
    import shutil
    import subprocess
    node = shutil.which("node")
    if not node:
        pytest.skip("Node necessário para executar o módulo real da extensão")
    programa = r'''
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const listeners = [], enviados = [], reinjecoes = [];
class WS {
  static OPEN = 1;
  constructor() { this.readyState = 1; }
  send(texto) { enviados.push(JSON.parse(texto)); }
}
const evento = () => ({addListener() {}});
const chrome = {
  runtime: {onMessage: {addListener(fn) {listeners.push(fn);}}},
  scripting: {executeScript: async dados => reinjecoes.push(dados)},
  tabs: {getZoom: async () => 1, query: async () => [{id: 7}],
         onActivated: evento(), onUpdated: evento(), onRemoved: evento()},
  windows: {get: async () => ({width: 1265, height: 1012, state: 'normal'})}
};
vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'), {
  chrome, WebSocket: WS, setInterval() {}, Date, Promise
});
listeners[0]({type: 'LAYLAY_STREAMING_LOCAL', videos: [], viewport: {
  outerWidth: 1250, outerHeight: 926, innerWidth: 1249, innerHeight: 923, dpr: 1
}}, {frameId: 0, tab: {active: true, id: 7, windowId: 3, title: 'Player'}});
setImmediate(() => {
  assert.equal(enviados[0].viewport.outerWidth, 1265);
  assert.equal(enviados[0].viewport.outerHeight, 1012);
  assert.equal(enviados[0].viewport.innerWidth, 1249);
});
'''
    resultado = subprocess.run([node, "-e", programa, str(
        Path(__file__).parents[2] / "extençao_google" / "streaming_background.js"
    )], capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stderr


def test_extensao_ausente_nao_deixa_espera_infinita(janela):
    from PySide6.QtTest import QTest
    from cliente.terminal_2.streaming_fontes import FontesStreaming
    app, tela = janela
    pagina = tela._garantir_pagina_carregada("streaming")
    pagina.fontes.encerrar()
    pagina.fontes = FontesStreaming(pagina, porta=0)
    pagina.atualizar_janelas()
    assert "Aguardando conexão" in pagina.estado.text()
    # Mesmo timer Qt da interface, com prazo reduzido apenas para esta prova.
    pagina._prazo_conexao.start(1)
    QTest.qWait(30)
    assert "Extensão não conectada" in pagina.estado.text()
    assert "Recarregue" in pagina.estado.text()
    assert not pagina.transmitir.isEnabled()
    assert pagina.visor.imagem.isNull()


@pytest.mark.parametrize("overflow_raiz,contain_corpo,container_vazio,y_video,esperado", [
    ("visible", "none", False, 68, 1),
    ("hidden", "none", False, 68, 0),
    ("visible", "layout", False, 68, 0),
    ("visible", "none", True, 68, 0),
    ("visible", "none", False, 800, 0),
])
def test_detector_respeita_overflow_do_viewport_e_recortes_reais(
    overflow_raiz, contain_corpo, container_vazio, y_video, esperado,
):
    import json
    import shutil
    import subprocess
    node = shutil.which("node")
    if not node:
        pytest.skip("Node necessário para executar o detector real")
    programa = r'''
const fs=require('fs'), vm=require('vm'), assert=require('assert');
const caso=JSON.parse(process.argv[2]), mensagens=[];
const estilo={visibility:'visible',opacity:'1',objectFit:'cover',objectPosition:'50% 50%',
  borderLeftWidth:'0',borderTopWidth:'0',paddingLeft:'0',paddingRight:'0',
  paddingTop:'0',paddingBottom:'0',transform:'none',overflowX:'visible',overflowY:'visible',contain:'none'};
function elemento(tag,x,y,w,h,css={}) {
  return {tagName:tag,parentElement:null,clientWidth:w,clientHeight:h,
    offsetWidth:w,offsetHeight:h,clientLeft:0,clientTop:0,isConnected:true,
    css:{...estilo,...css},getBoundingClientRect:()=>({x,y,width:w,height:h})};
}
const html=elemento('HTML',0,0,1280,720,{overflowX:caso[0],overflowY:caso[0]});
const body=elemento('BODY',0,0,1280,0,{overflowX:'auto',overflowY:'scroll',contain:caso[1]});
const video=elemento('VIDEO',16,caso[3],854,480);
video.videoWidth=854; video.videoHeight=480; video.paused=false; video.ended=false;
video.getAttribute=()=>null;
body.parentElement=html; video.parentElement=body;
if(caso[2]) {
  const container=elemento('DIV',0,0,1280,0,{overflowX:'hidden',overflowY:'hidden'});
  container.parentElement=body; video.parentElement=container;
}
const doc={visibilityState:'visible',body,documentElement:html,
  querySelectorAll:selector=>selector==='video'?[video]:[]};
const contexto={document:doc,innerWidth:1280,innerHeight:720,outerWidth:1296,outerHeight:850,
  devicePixelRatio:1,getComputedStyle:e=>e.css,performance:{now:()=>2000},
  crypto:{getRandomValues:a=>a.fill(1)},addEventListener(){},setInterval(){},
  chrome:{runtime:{sendMessage:m=>{mensagens.push(m);return Promise.resolve();}}}};
contexto.window=contexto; contexto.top=contexto;
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),contexto);
assert.equal(mensagens.length,1);
assert.equal(mensagens[0].videos.length,caso[4]);
if(caso[4]) assert.equal(mensagens[0].videos[0].height,480);
'''
    resultado = subprocess.run([node, "-e", programa, str(
        Path(__file__).parents[2] / "extençao_google" / "streaming_detector.js"
    ), json.dumps([overflow_raiz, contain_corpo, container_vazio, y_video, esperado])],
        capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stderr


def test_encerramento_desliga_callbacks_antes_de_destruir_canal(janela, monkeypatch):
    import sys
    import shiboken6
    from PySide6.QtCore import QUrl
    from PySide6.QtTest import QTest
    from PySide6.QtWebSockets import QWebSocket
    from PySide6.QtWidgets import QWidget
    from cliente.terminal_2.streaming_fontes import FontesStreaming
    app, tela = janela
    erros = []
    monkeypatch.setattr(sys, "excepthook", lambda tipo, erro, tb: erros.append(erro))
    dono = QWidget()
    servidor = FontesStreaming(dono, porta=0)
    cliente = QWebSocket("chrome-extension://" + "c" * 32)
    cliente.open(QUrl(f"ws://127.0.0.1:{servidor._servidor.serverPort()}"))
    QTest.qWait(100)
    assert len(servidor._sockets) == 1
    servidor.encerrar()
    shiboken6.delete(dono)
    QTest.qWait(100)
    cliente.close()
    assert erros == []


def test_recorte_compensa_zoom_dpi_e_bordas_invisiveis():
    import json
    from PySide6.QtCore import QRect
    from time import monotonic
    from cliente.terminal_2.streaming_fontes import decodificar_fontes, calcular_recorte
    dados = _geometria()
    dados["viewport"]["dpr"] = 2
    fonte = decodificar_fontes(json.dumps(dados), "teste", monotonic())[0]
    assert calcular_recorte(fonte, 1600, 1200, monotonic()) == QRect(200, 360, 640, 360)
    assert calcular_recorte(fonte, 1586, 1193, monotonic(), (7, 0, 7, 7)) == QRect(193, 360, 640, 360)
    dados["viewport"].update(dpr=2, zoom=2, innerWidth=400, innerHeight=260)
    dados["videos"][0].update(x=50, y=50, width=160, height=90)
    fonte = decodificar_fontes(json.dumps(dados), "teste", monotonic())[0]
    assert calcular_recorte(fonte, 800, 600, monotonic()) == QRect(100, 180, 320, 180)
