"""Páginas HTML com protocolo, catálogo e paginação dos owners reais."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import time

import pytest

pytest.importorskip("PySide6.QtWebEngineWidgets")


@pytest.fixture
def paginas_reais(monkeypatch, tmp_path, request):
    monkeypatch.setenv("QT_QPA_PLATFORM", os.environ.get("LAYLAY_UI_PLATFORM", "offscreen"))
    monkeypatch.setenv("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --no-sandbox")
    monkeypatch.delenv("LAYLAY_REDUZIR_MOVIMENTO", raising=False)
    from PySide6.QtCore import QSettings, QThread
    from PySide6.QtTest import QTest
    from PySide6.QtWebEngineCore import QWebEngineSettings
    from PySide6.QtWidgets import QApplication
    from cliente import terminal_laylay_2 as terminal
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1
    from mente_laylay.integracao.desktop_bridge import DesktopBridgeRuntime
    from mente_laylay.integracao.dev_console_runtime import DevConsoleRuntime
    from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime
    from mente_laylay.memoria_mental.operacoes_musicais_runtime import OperacoesMusicaisRuntime

    monkeypatch.setattr(terminal, "QSettings", lambda *_: QSettings(str(tmp_path / "ui.ini"), QSettings.IniFormat))
    arquivo = tmp_path / "playlists.json"
    arquivo.write_text(json.dumps({"Teste": [{
        "url": f"https://www.youtube.com/watch?v=TESTE{i:06d}",
        "titulo": f"Faixa {i + 1}", "canal": "Canal de validação",
        "data": "2026-10-20", "duracao_segundos": 120,
    } for i in range(125)]}), encoding="utf-8")
    playlists = PlaylistRuntime(
        state_file=str(arquivo), legacy_file=str(tmp_path / "legado.json"),
        cache={}, ultima_playlist_getter=lambda: "", playlist_state={},
        artwork_dir=str(tmp_path / "artwork"), log=lambda _: None,
    )
    playlists.load()
    operacoes = OperacoesMusicaisRuntime(
        playlists_usuario=playlists, playlists_laylay=None,
        musica_estado_getter=lambda _chave, padrao: padrao,
        musica_estado_setter=lambda *_: None, solicitar_aba_ativa=lambda **_: {},
        playlist_state={}, log=lambda *_: None,
    )
    dashboard = {"music": {
        "catalog": [{"name": "Teste", "count": 125}],
        "catalog_available": True, "catalog_observed_at": time.time(),
    }}
    hardware = None
    if os.environ.get("LAYLAY_UI_CAPTURE") == "1":
        import psutil
        from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
        hardware = DashboardTerminalRuntime(
            configuracao_getter=lambda: {}, llm_getter=lambda: {},
            interacao_getter=lambda: {"interaction_mode": "chat"},
            memoria_saude_getter=lambda: {}, agenda_getter=lambda: [],
            aprendizados_getter=lambda **_: [], estado_mental_getter=lambda: {},
            contexto_jogo_getter=lambda: {}, psutil_mod=psutil, intervalo_s=0.3,
            log=lambda _: None,
        )

    def retrato():
        return {**(hardware.snapshot() if hardware else {}), **dashboard}
    dev = DevConsoleRuntime()
    dev.registrar_linha("[SYSTEM] Validação visual da interface: catálogo temporário carregado.")
    dev.registrar_linha("✅ [SYSTEM] Receipt da leitura de playlist recebido pelo transporte autenticado.")
    dev.registrar_linha("⚠️ [SYSTEM] Instrumentação de validação: efeitos externos não foram solicitados.")
    ponte = DesktopBridgeRuntime(
        enviar_entrada=lambda _: False, historico_getter=lambda: [],
        estado_getter=lambda: {"activity": "idle", "interaction_mode": "chat"},
        conversas_getter=lambda: [{"id": "22222222222222222222222222222222", "titulo": "Validação temporária", "status": "ativa"}],
        conversa_ativa_getter=lambda: "22222222222222222222222222222222",
        configuracao_getter=lambda: {},
        dashboard_getter=retrato, playlist_operacoes=operacoes,
        dev_console_getter=dev.snapshot, dev_console_consultar=dev.consultar,
        log=lambda _: None,
    )
    app = QApplication.instance() or QApplication([])
    ponte.iniciar()
    worker = terminal.PonteWorker(*ponte.endereco, ponte.token, session_id=ponte.session_id)
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.executar)
    worker.terminou.connect(thread.quit)
    recebidas = []
    worker.mensagem.connect(recebidas.append)
    raiz_renderer = Path(__file__).parents[2]
    diretorio_renderer = None
    if getattr(request, "param", None) == "replay_inicial":
        # Executa os mesmos scripts/renderer/canal; apenas insere publicações
        # anteriores à inscrição das páginas para reproduzir a ordem do boot.
        destino = tmp_path / "renderer" / "cliente" / "terminal_2" / "web_v1"
        shutil.copytree(raiz_renderer / "cliente/terminal_2/web_v1", destino)
        indice = destino / "index.html"
        html = indice.read_text(encoding="utf-8")
        ancora = '<script defer src="paginas.js"></script>'
        assert html.count(ancora) == 1
        indice.write_text(html.replace(ancora, '<script defer src="publicacoes_anteriores.js"></script>\n' + ancora), encoding="utf-8")
        (destino / "publicacoes_anteriores.js").write_text("""
          window.publicacoesValidadas={inicio:!!window.LaylayInterface};
          for(let i=1;i<=30;i++)LaylayInterface.receiveEvent({type:'dashboard_state',dashboard:{system:{cpu_percent:{value:i,observed_at:i,freshness:'fresh'}}}});
          LaylayInterface.receiveEvent({type:'dashboard_state',dashboard:{system:{cpu_percent:{value:30,observed_at:30,freshness:'fresh'}}}});
          LaylayInterface.receiveEvent({type:'dashboard_state',dashboard:{system:{cpu_percent:{value:31,observed_at:31,freshness:'stale'}}}});
          window.publicacoesValidadas.final=LaylayInterface.state.dashboard.system.cpu_percent.value;
        """, encoding="utf-8")
        diretorio_renderer = destino
    janela = JanelaInterfaceWebV1(worker, raiz_renderer, session_id=ponte.session_id, diretorio_web=diretorio_renderer)
    janela.web.settings().setAttribute(QWebEngineSettings.AutoLoadImages, False)

    def esperar(condicao, segundos=8):
        limite = time.monotonic() + segundos
        while not condicao() and time.monotonic() < limite:
            QTest.qWait(20)
        assert condicao(), "HTML/canal/owner real não confirmou o estado esperado"

    def js(codigo):
        resultado = []
        janela.web.page().runJavaScript(codigo, resultado.append)
        esperar(lambda: bool(resultado))
        return resultado[0]

    js.janela = janela
    js.app = app
    js.dashboard = dashboard
    js.ponte = ponte
    js.dev = dev

    janela.show()
    thread.start()
    try:
        esperar(lambda: js("!!window.LaylayInterface?.state.connected"))
        yield js, esperar, recebidas
    finally:
        janela.close()
        worker.parar()
        ponte.parar()
        if hardware:
            hardware.parar()
        thread.quit()
        assert thread.wait(3000)
        app.processEvents()


def test_paginacao_acumulada_preserva_todas_as_faixas_e_numeracao(paginas_reais):
    js, esperar, recebidas = paginas_reais
    js("LaylayInterface.goPage('music')")
    esperar(lambda: js("!!document.querySelector('[data-tp-action=playlist-open]')"))
    js("document.querySelector('[data-tp-action=playlist-open]').click()")
    esperar(lambda: js("document.querySelectorAll('.tp-tracktable').length===50"))
    for quantidade in (100, 125):
        esperar(lambda: js("document.querySelector('[data-tp-action=playlist-more]')?.disabled===false"))
        js("document.querySelector('[data-tp-action=playlist-more]').click()")
        esperar(lambda: js(f"document.querySelectorAll('.tp-tracktable').length==={quantidade}"))
    assert js("Array.from(document.querySelectorAll('.tp-tracktable>small:first-child'),el=>Number(el.textContent)).every((n,i)=>n===i+1)")
    assert js("document.querySelector('[data-tp-action=playlist-more]')===null")
    assert [e["result"]["offset"] for e in recebidas if e.get("type") == "playlist_result"] == [0, 50, 100]


def test_receipt_real_antes_da_continuacao_js_nao_recria_pendencia(paginas_reais):
    js, esperar, recebidas = paginas_reais
    # Atrasa apenas a continuação JS. Canal, transporte e executor de leitura
    # continuam reais; o receipt canônico chega enquanto o await está suspenso.
    js("""window.pedidoOriginal=LaylayInterface.request;
      LaylayInterface.request=(kind,data,...rest)=>pedidoOriginal(kind,data,...rest)
        .then(id=>kind==='playlist'?new Promise(resolve=>{
          let unsubscribe,finished=false;
          unsubscribe=LaylayInterface.onEvent(event=>{
            if(event.type==='playlist_result'&&event.id===id){
              finished=true;if(unsubscribe)unsubscribe();setTimeout(()=>resolve(id),0);
            }
          });
          if(finished)unsubscribe();
        }):id);
      LaylayInterface.goPage('music');""")
    esperar(lambda: js("!!document.querySelector('[data-tp-action=playlist-open]')"))
    js("document.querySelector('[data-tp-action=playlist-open]').click()")
    esperar(lambda: any(e.get("type") == "playlist_result" for e in recebidas))
    esperar(lambda: js("document.querySelector('[data-tp-action=playlist-more]')?.disabled===false"))
    js("document.querySelector('[data-tp-action=playlist-more]').click()")
    esperar(lambda: js("document.querySelectorAll('.tp-tracktable').length===100"))
    esperar(lambda: js("document.querySelector('[data-tp-action=playlist-more]')?.disabled===false"))


def test_historico_usa_24_posicoes_e_ignora_replay_e_metricas_antigas(paginas_reais):
    js, _esperar, _recebidas = paginas_reais
    js("""LaylayInterface.goPage('system');
      for(let i=1;i<=30;i++)LaylayInterface.receiveEvent({type:'dashboard_state',dashboard:{system:{cpu_percent:{value:i,observed_at:i,freshness:'fresh'}}}});
      LaylayInterface.receiveEvent({type:'dashboard_state',dashboard:{system:{cpu_percent:{value:30,observed_at:30,freshness:'fresh'}}}});
      LaylayInterface.receiveEvent({type:'dashboard_state',dashboard:{system:{cpu_percent:{value:31,observed_at:31,freshness:'stale'}}}});
      LaylayInterface.render();""")
    assert js("document.querySelector('.tp-chart svg').getAttribute('aria-label')") == "CPU: 24 de 24 posições, agora à direita"
    assert js("document.querySelector('.tp-chart polyline').getAttribute('points').split(' ').length") == 24
    assert js("document.querySelector('.tp-chart polyline').getAttribute('points').split(' ')[23].startsWith('235,')")


@pytest.mark.parametrize("paginas_reais", ["replay_inicial"], indirect=True)
def test_historico_inicial_conserva_cada_publicacao_antes_da_inscricao(paginas_reais):
    js, esperar, _recebidas = paginas_reais
    assert js("JSON.stringify(window.publicacoesValidadas)") == '{"inicio":true,"final":31}'
    js("LaylayInterface.goPage('system')")
    esperar(lambda: js("!!document.querySelector('.tp-chart svg')"))
    assert js("document.querySelector('.tp-chart svg').getAttribute('aria-label')") == "CPU: 24 de 24 posições, agora à direita"
    assert js("document.querySelector('.tp-chart polyline').getAttribute('points').split(' ').length") == 24
    pontos = json.loads(js("JSON.stringify(document.querySelector('.tp-chart polyline').getAttribute('points').split(' ').map(p=>p.split(',').map(Number)))"))
    # Janela efetiva 7..30: nem cópias do estado final nem a amostra stale 31.
    assert pontos[0][1] == pytest.approx(65 - 7 / 100 * 65)
    assert pontos[-1][1] == pytest.approx(65 - 30 / 100 * 65)


def test_navegacao_refinada_movel_nomeia_todas_abas_e_fecha_com_escape(paginas_reais):
    js, esperar, _recebidas = paginas_reais
    js.janela.resize(375, 812)
    esperar(lambda: js("innerWidth<=400"))
    assert js("!!document.querySelector('.pr-mobile-nav')"), "Falta o acesso às nove abas na janela estreita"
    js("document.querySelector('.pr-mobile-nav').click()")
    assert js("document.querySelector('.pr-mobile-nav').getAttribute('aria-expanded')") == "true"
    assert js("[...document.querySelectorAll('.nav [data-page]')].every(n=>n.getAttribute('aria-label')&&n.getBoundingClientRect().width>100)")
    assert js("document.querySelectorAll('.nav [data-page]').length") == 9
    js("document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))")
    assert js("document.querySelector('.pr-mobile-nav').getAttribute('aria-expanded')") == "false"


def test_refinamento_preserva_rolagem_entre_abas_e_streaming_real(paginas_reais):
    js, esperar, _recebidas = paginas_reais
    js.janela.resize(900, 650)
    js("LaylayInterface.goPage('system')")
    esperar(lambda: js("document.getElementById('page-content').scrollHeight>document.getElementById('page-content').clientHeight+300"))
    js("document.getElementById('page-content').scrollTop=300;LaylayInterface.goPage('memory');LaylayInterface.goPage('system')")
    assert js("document.getElementById('page-content').scrollTop") == 300
    js("LaylayInterface.goPage('streaming')")
    assert js("!!document.querySelector('[data-tp-action=streaming-open]')&&!!document.querySelector('#streaming-viewport')"), "CTA real precisa usar o viewport integrado da nova composição"
    assert js("!document.querySelector('.pr-preview-player,[data-tp-action=streaming-crop],[data-tp-action=streaming-float],.pr-preview-bar')")
    assert js("typeof window.LaylayPreviewBridge==='undefined'")


def test_cta_streaming_refinado_abre_owner_nativo_sem_pedido_para_mente(paginas_reais):
    from PySide6.QtTest import QSignalSpy

    js, esperar, _recebidas = paginas_reais
    js("LaylayInterface.goPage('streaming')")
    envios = QSignalSpy(js.janela.controlador.enviar_json)
    js("document.querySelector('[data-tp-action=streaming-open]').click()")
    esperar(lambda: js.janela._streaming_pagina is not None and js.janela._streaming_pagina.isVisible())
    from cliente.terminal_2.streaming import PaginaStreaming
    assert isinstance(js.janela._streaming_pagina, PaginaStreaming)
    assert js.janela._streaming_pagina.window() is js.janela, "Player local deve ficar na mesma janela oficial"
    assert envios.count() == 0, "Abrir o player local não deve enviar comando à mente"
    assert js("!document.querySelector('.pr-preview-player')")
    js("document.querySelector('[data-tp-action=streaming-stop]').click()")
    esperar(lambda: not js.janela._streaming_pagina.isVisible())
    assert envios.count() == 0


def test_painel_nativo_conserva_medidas_da_previa_quando_cabe_na_tela(paginas_reais):
    js, esperar, _recebidas = paginas_reais
    disponivel = js.janela.screen().availableGeometry()
    if disponivel.width() < 650 or disponivel.height() < 720:
        pytest.skip("A especificação desktop do painel requer área disponível suficiente")
    js("LaylayInterface.goMode('quick')")
    esperar(lambda: js.janela.modo_apresentacao == "quick")
    assert (js.janela.width(), js.janela.height()) == (425, 720)
    esperar(lambda: js("getComputedStyle(document.querySelector('.quick-greeting h2')).fontSize==='22px'"))
    assert js("getComputedStyle(document.querySelector('.quick-greeting')).paddingLeft") == "23px"
    assert js("getComputedStyle(document.querySelector('.quick-history')).paddingLeft") == "22px"


def test_playlist_tem_botao_play_visivel_em_cada_faixa(paginas_reais):
    js, esperar, _recebidas = paginas_reais
    js("LaylayInterface.goPage('music')")
    esperar(lambda: js("!!document.querySelector('[data-tp-action=playlist-open]')"))
    js("document.querySelector('[data-tp-action=playlist-open]').click()")
    esperar(lambda: js("document.querySelectorAll('.tp-tracktable').length===50"))
    assert js("document.querySelectorAll('.tp-tracktable .tp-track-play svg').length") == 50
    assert js("Array.from(document.querySelectorAll('.tp-track-play')).every(el=>el.dataset.video&&el.getAttribute('aria-label').startsWith('Tocar '))")


def test_devconsole_preserva_nivel_success_e_saida_comando_em_terminal(paginas_reais):
    js, esperar, _recebidas = paginas_reais
    js("LaylayInterface.goPage('dev')")
    esperar(lambda: js("document.querySelectorAll('.tp-console-line').length>=3"))
    assert js("getComputedStyle(document.querySelector('.tp-console-line .tp-level')).whiteSpace") == "nowrap"
    assert js("document.querySelector('.tp-dev-metrics')===null")
    assert js("!!document.querySelector('.tp-terminal .tp-console')")
    assert js("document.querySelector('.tp-console-line .tp-level').getBoundingClientRect().width>=60")
    js("document.getElementById('tp-dev-input').value='status';document.getElementById('tp-dev-input').dispatchEvent(new Event('input',{bubbles:true}));document.getElementById('tp-dev-command').requestSubmit();")
    esperar(lambda: js("!!document.querySelector('.tp-command-result pre')"))
    assert js("document.querySelector('.tp-command-result pre').textContent.includes('LAYLAY STATUS')")
    assert js("document.querySelector('.tp-command-title').textContent.includes('receipt confirmado')")


def test_vigia_de_sensores_nao_se_torna_receipt_de_autorizacao_corporal(paginas_reais):
    js, esperar, _recebidas = paginas_reais
    js.dev.configurar_corpo_getter(lambda: {"transporte": {"sensores": {"recente": True, "protecao": {"vigia_ativa": True}}}})
    js.dev.atualizar_corpo()
    js("LaylayInterface.goPage('dev')")
    esperar(lambda: js("document.querySelector('.tp-dev-details').textContent.includes('Vigia de sensoresAtiva')"))
    assert not js("document.querySelector('.tp-dev-details').textContent.includes('Renovada na placa')")
    assert not js("document.querySelector('.tp-dev-details').textContent.includes('Autorização corporal')")


def test_medidor_reage_so_ao_video_observado_e_para_em_pausa_e_movimento_reduzido(paginas_reais):
    from PySide6.QtTest import QTest

    js, esperar, _recebidas = paginas_reais
    js.janela.resize(1440, 1000)
    js("LaylayInterface.goPage('music');LaylayInterface.request('preferencia',{name:'reduzir_movimento',value:false})")
    assert js("document.querySelector('.tp-music-content aside')===null")
    assert js("document.querySelectorAll('.tp-music-content input[data-tp-change=volume]').length") == 1
    assert not js("['Modo de audição','Rotinas & agenda','Luzes RGB','Equalizador','Som ambiente'].some(label=>document.querySelector('.tp-music-content').textContent.includes(label))")
    assert js("Math.abs(document.querySelector('.tp-player').getBoundingClientRect().width-document.querySelector('.tp-music-content').getBoundingClientRect().width)<2")
    js.dashboard["music"].update({
        "state": "playing", "freshness": "fresh", "observed_at": time.time(),
        "video_id": "TESTE000000", "title": "Faixa 1 · observação de validação",
        "channel": "Catálogo temporário", "playlist": "Teste",
        "position_seconds": 32, "duration_seconds": 120,
    })
    esperar(lambda: js("LaylayInterface.state.dashboard.music?.state==='playing'"))
    esperar(lambda: js("LaylayInterface.state.preferences.reduced===false"))
    assert js.ponte.publicar_medidor_musica({"tab_id": 1, "video_id": "TESTE000000", "levels": [0.2, 0.5, 0.9], "energy": 0.5, "observed_at": time.time()})
    esperar(lambda: js("document.querySelector('[data-music-meter] i')?.style.height==='8.8px'"))
    js("window.medidorOriginal=document.querySelector('[data-music-meter]')")
    assert js.ponte.publicar_medidor_musica({"tab_id": 1, "video_id": "TESTE000000", "levels": [0.8, 0.4, 0.1], "energy": 0.4, "observed_at": time.time()})
    esperar(lambda: js("document.querySelector('[data-music-meter] i')?.style.height==='23.2px'"))
    assert js("medidorOriginal===document.querySelector('[data-music-meter]')")
    # O ID diferente não pode movimentar o medidor da faixa atual.
    assert js.ponte.publicar_medidor_musica({"tab_id": 2, "video_id": "TESTE000001", "levels": [1, 1, 1], "energy": 1, "observed_at": time.time()})
    QTest.qWait(100)
    assert js("document.querySelector('[data-music-meter] i').style.height") == "23.2px"
    if os.environ.get("LAYLAY_UI_CAPTURE") == "1":
        destino = Path(__file__).parents[2] / "artifacts/interface_v1"
        destino.mkdir(parents=True, exist_ok=True)
        def foto(nome):
            js.janela.raise_()
            js.janela.activateWindow()
            js.janela.web.setFocus()
            js("window.capturaPronta=false;requestAnimationFrame(()=>requestAnimationFrame(()=>window.capturaPronta=true))")
            esperar(lambda: js("window.capturaPronta===true"))
            QTest.qWait(650)
            assert js.janela.grab().save(str(destino / nome))
        esperar(lambda: js("!!LaylayInterface.state.dashboard.system?.cpu_percent?.observed_at"))
        foto("web-musica-animacao.png")
        foto("web-music.png")
        js("document.querySelector('[data-tp-action=playlist-open]').click()")
        esperar(lambda: js("document.querySelectorAll('.tp-tracktable').length===50"))
        foto("web-musica-playlist.png")
        assert js("document.querySelectorAll('.tp-tracktable').length") == 50
        assert js("document.querySelectorAll('.tp-track-play svg').length") == 50
        js("LaylayInterface.goPage('dev');document.getElementById('tp-dev-input').value='status';document.getElementById('tp-dev-input').dispatchEvent(new Event('input',{bubbles:true}));document.getElementById('tp-dev-command').requestSubmit();")
        esperar(lambda: js("!!document.querySelector('.tp-command-result pre')"))
        foto("web-dev-terminal.png")
        (destino / "resultado_paginas_web.json").write_text(json.dumps({
            "plataforma": js.app.platformName(),
            "monitor": js.janela.windowHandle().screen().name(),
            "origem_playlist": "PlaylistRuntime e OperacoesMusicaisRuntime reais, 125 faixas temporarias",
            "origem_logs": "DevConsoleRuntime real, linhas de instrumentacao da validacao",
            "origem_metricas": "DashboardTerminalRuntime com psutil real, somente leitura",
            "origem_playing_e_meter": "fixture declarada e publicada no protocolo autenticado; nao houve reproducao externa",
            "mente_iniciada": False, "efeitos_externos": False,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        js("LaylayInterface.goPage('music')")
        js("document.querySelector('[data-tp-action=playlist-back]')?.click()")
    js.dashboard["music"].update(state="paused", observed_at=time.time())
    esperar(lambda: js("LaylayInterface.state.dashboard.music?.state==='paused'"))
    esperar(lambda: js("Array.from(document.querySelectorAll('[data-music-meter] i')).every(el=>el.style.height==='4px')"))
    js("LaylayInterface.request('preferencia',{name:'reduzir_movimento',value:true})")
    esperar(lambda: js("LaylayInterface.state.preferences.reduced===true"))
    js.dashboard["music"].update(state="playing", observed_at=time.time())
    esperar(lambda: js("LaylayInterface.state.dashboard.music?.state==='playing'"))
    assert js.ponte.publicar_medidor_musica({"tab_id": 1, "video_id": "TESTE000000", "levels": [1, 1, 1], "energy": 1, "observed_at": time.time()})
    QTest.qWait(150)
    assert js("Array.from(document.querySelectorAll('[data-music-meter] i')).every(el=>el.style.height==='4px')")
    assert js("getComputedStyle(document.querySelector('[data-music-meter] i')).transitionDuration") == "0s"
