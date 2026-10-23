"""Renderer oficial/ponte autenticada/SQLite temporário; sem iniciar a mente.

Os receipts instrumentados são dados da bancada, não usos reais do usuário.
Nenhum executor externo é chamado. Capturas e preferências ficam isoladas.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--saida', type=Path, required=True)
    parser.add_argument('--inspecionar', action='store_true')
    parser.add_argument('--streaming', action='store_true')
    parser.add_argument('--exportar-browser', action='store_true')
    args = parser.parse_args()
    args.saida.mkdir(parents=True, exist_ok=True)
    import psutil
    from PySide6.QtCore import QSettings, QThread, QTimer
    from PySide6.QtGui import QFont
    from PySide6.QtTest import QTest
    from PySide6.QtWebEngineCore import QWebEngineScript
    from PySide6.QtWidgets import QApplication
    import cliente.terminal_laylay_2 as terminal
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1
    from memoria_sqlite import MemoriaSQLite
    from mente_laylay.memoria_mental.motor_aprendizado import MotorAprendizadoRuntime
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    from mente_laylay.memoria_mental.uso_confirmado_runtime import criar_uso_confirmado_runtime
    from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
    from mente_laylay.integracao.desktop_bridge import DesktopBridgeRuntime

    with tempfile.TemporaryDirectory(prefix='laylay-refino-oficial-') as temporario:
        pasta = Path(temporario)
        app = QApplication([])
        app.setFont(QFont(terminal.carregar_fontes_interface(), 10))
        preferencias = QSettings(str(pasta/'ui.ini'), QSettings.IniFormat)
        terminal.QSettings = lambda *_: preferencias
        memoria = MemoriaSQLite(str(pasta/'uso.sqlite'))
        motor = MotorAprendizadoRuntime(memoria_sqlite=memoria, contexto_getter=lambda: {}, log=lambda _: None)
        agora = time.time()
        fila = {'name': 'Trilha de validação', 'tab_id': 8,
                'last_url': 'https://www.youtube.com/watch?v=abcdefghijk'}
        uso = criar_uso_confirmado_runtime(motor_aprendizado=motor, memoria_sqlite=memoria,
            playlist_state_getter=lambda: fila,
            capacidade_getter=lambda _: {'disponivel': True, 'estado': 'disponivel'}, log=lambda _: None)
        uso.observar_resultado(ResultadoAcao(intent='APP_OPEN', origem='executor', executou=True,
            confirmado=True, status='app_aberto', id_solicitacao='bancada-app-1',
            params={'nome_app': 'Visual Studio Code'}, inicio_execucao=agora-1))
        uso.observar_resultado(ResultadoAcao(intent='PLAYLIST_PLAY', origem='executor', executou=True,
            confirmado=None, status='playlist_enviada_sem_confirmacao', id_solicitacao='bancada-playlist-1',
            params={'nome_playlist': fila['name']}, alvo=fila['name'], inicio_execucao=agora-1))
        uso.observar_player({'state':'playing','tab_id':8,'video_id':'abcdefghijk',
            'observed_at':agora,'_source_observed_at':agora*1000,'is_ad':False}, fila)
        entradas = []
        estado = {'activity':'idle','interaction_mode':'chat','voice_available':False}
        dashboard = DashboardTerminalRuntime(configuracao_getter=lambda: {}, llm_getter=lambda: {},
            interacao_getter=lambda: estado, memoria_saude_getter=lambda: {}, agenda_getter=lambda: [],
            aprendizados_getter=lambda **_: [], estado_mental_getter=lambda: {}, contexto_jogo_getter=lambda: {},
            uso_confirmado_getter=uso.snapshot, playlists_getter=lambda: [{'name':fila['name'],'count':1}],
            musica_getter=lambda: {},
            psutil_mod=psutil, intervalo_s=0.3, log=lambda _: None)
        ponte = DesktopBridgeRuntime(enviar_entrada=entradas.append, historico_getter=lambda: [],
            estado_getter=lambda: estado, dashboard_getter=dashboard.snapshot,
            conversas_getter=lambda: [{'id':'11111111111111111111111111111111','titulo':'Validação isolada','status':'ativa'}],
            conversa_ativa_getter=lambda: '11111111111111111111111111111111', configuracao_getter=lambda: {},
            dashboard_interval_s=0.3, log=lambda _: None)
        ponte.iniciar()
        worker = terminal.PonteWorker(*ponte.endereco, ponte.token, session_id=ponte.session_id)
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.executar)
        worker.terminou.connect(thread.quit)
        janela = JanelaInterfaceWebV1(worker, RAIZ, session_id=ponte.session_id)
        probe = QWebEngineScript()
        probe.setInjectionPoint(QWebEngineScript.DocumentCreation)
        probe.setWorldId(QWebEngineScript.MainWorld)
        probe.setSourceCode("window.__frames=[];function f(t){const e=document.querySelector('.desktop-island');__frames.push({t,mode:window.LaylayInterface?.state.mode,entry:window.LaylayInterface?.state.desktopEntry,width:innerWidth,opacity:e?getComputedStyle(e).opacity:null,classes:document.body?.className});if(__frames.length<120)requestAnimationFrame(f)}requestAnimationFrame(f)")
        janela.pagina_web.scripts().insert(probe)

        def aguardar(condicao, segundos=12):
            limite = time.monotonic()+segundos
            while not condicao() and time.monotonic()<limite:
                QTest.qWait(20)
            assert condicao(), 'Fronteira esperada não foi confirmada no renderer oficial'

        def js(codigo):
            resposta = []
            janela.pagina_web.runJavaScript(codigo, resposta.append)
            aguardar(lambda: bool(resposta))
            return resposta[0]

        def foto(nome):
            QTest.qWait(230)
            assert janela.grab().save(str(args.saida/(nome+'.png')))

        resultado = {'mente_iniciada':False,'dados_instrumentados':True,'entradas_externas':0}
        amostras_entrada = []
        entrada_probe = QTimer(janela)
        entrada_probe.setInterval(20)
        entrada_probe.timeout.connect(lambda: amostras_entrada.append({
            'opacity':janela.windowOpacity(), 'entry':janela._desktop_entrada_ativa,
            'visible':janela.isVisible(), 'phase':janela._desktop_fase}))
        try:
            janela.apresentar('desktop')
            entrada_probe.start()
            janela.iniciar_apresentacao()
            thread.start()
            aguardar(lambda: janela._entrada_exibida and janela.controlador._conectado)
            aguardar(lambda: js("!!LaylayInterface.state.dashboard.home?.periods?.['30']"))
            QTest.qWait(900)
            entrada_probe.stop()
            resultado['startup_native'] = amostras_entrada
            assert any(0 < item['opacity'] < 1 and item['entry'] for item in amostras_entrada)
            assert janela.windowOpacity() == 1 and not janela._desktop_entrada_ativa
            assert janela.estado_desktop == 'compact' and janela.width() == 272
            foto('compacta-oficial')
            resultado['startup_frames'] = json.loads(js('JSON.stringify(window.__frames)'))
            hwnd = int(janela.winId())
            objetos = (janela.web,janela.pagina_web,janela.canal,janela.controlador,janela.worker)
            janela.ponte_web.gesto_desktop('expandir')
            aguardar(lambda: janela.desktop_pagina=='home' and janela._desktop_fase=='idle')
            aguardar(lambda: js("!!document.querySelector('.home-inteligente')"))
            resultado['home'] = json.loads(js('JSON.stringify(LaylayInterface.state.dashboard.home)'))
            assert resultado['home']['periods']['30']['playlists'][0]['confirmed_plays'] == 1
            if args.exportar_browser:
                # Cópia de inspeção sem canal Qt, token, executor ou persistência.
                destino = args.saida/'browser-qa'
                shutil.copytree(RAIZ/'cliente/terminal_2/web_v1', destino, dirs_exist_ok=True)
                indice = destino/'index.html'
                html = indice.read_text(encoding='utf-8')
                ancora = '<script defer src="qrc:///qtwebchannel/qwebchannel.js"></script>'
                assert html.count(ancora) == 1
                html = html.replace(ancora, '').replace('</head>', '<script defer src="qa-readonly.js"></script></head>')
                indice.write_text(html,encoding='utf-8')
                publico = json.loads(js('JSON.stringify({dashboard:LaylayInterface.state.dashboard,settings:LaylayInterface.state.settings,dev_console:LaylayInterface.state.devConsole})'))
                (destino/'qa-readonly.js').write_text("// Dados da bancada isolada; nenhum backend exposto.\nwindow.addEventListener('DOMContentLoaded',()=>{const p=LaylayInterface;p.receiveEvent("+json.dumps({'type':'snapshot','state':{'activity':'idle','emotion':'calma'},**publico},ensure_ascii=False)+");p.receiveEvent({type:'conexao',connected:true});p.state.nativeWindow=false;p.goMode('full');document.getElementById('toast').classList.remove('show');document.title='Laylay — inspeção visual isolada';});",encoding='utf-8')
            resultado['pages'] = []
            for pagina in ('home','chat','lamp','music','streaming','memory','system','dev','settings'):
                js('LaylayInterface.goPage('+json.dumps(pagina)+')')
                aguardar(lambda: janela._desktop_fase=='idle')
                QTest.qWait(300)
                medida = json.loads(js("JSON.stringify((()=>{const p=document.getElementById('page-content');return {page:LaylayInterface.state.page,width:innerWidth,height:innerHeight,overflow:p.scrollWidth>p.clientWidth+1,text:p.textContent.length}})())"))
                assert medida['page']==pagina and not medida['overflow'], medida
                assert int(janela.winId())==hwnd
                assert objetos==(janela.web,janela.pagina_web,janela.canal,janela.controlador,janela.worker)
                resultado['pages'].append(medida)
                foto('oficial-'+pagina)
            if args.streaming:
                from artifacts.interface_v1.validar_ilha_suave import validar_ilha_suave
                import traceback
                atividade_original = janela.registrar_atividade_desktop
                atividades = []
                def atividade_observada():
                    atividades.append({'t':time.monotonic(),'stack':traceback.format_stack(limit=5),
                        'cursor':[janela.mapFromGlobal(__import__('PySide6.QtGui',fromlist=['QCursor']).QCursor.pos()).x(),janela.mapFromGlobal(__import__('PySide6.QtGui',fromlist=['QCursor']).QCursor.pos()).y()]})
                    atividade_original()
                janela.registrar_atividade_desktop = atividade_observada
                try:
                    resultado['streaming_e_inatividade'] = validar_ilha_suave(janela, js, aguardar, foto, args.saida)
                finally:
                    janela.registrar_atividade_desktop = atividade_original
                    resultado['atividade_trace'] = atividades
            janela.recolher_desktop()
            aguardar(lambda: janela._desktop_fase=='idle')
            assert not entradas
            resultado.update(ok=True,same_hwnd=True,renderer='QtWebEngine oficial + ponte autenticada + SQLite temporário')
            if args.inspecionar:
                limite = time.monotonic()+900
                while not janela._fechada and not (args.saida/'encerrar').exists() and time.monotonic()<limite:
                    QTest.qWait(100)
        except Exception as erro:
            resultado.update(ok=False,error=repr(erro))
            foto('falha')
            raise
        finally:
            (args.saida/'resultado.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding='utf-8')
            janela.close()
            worker.parar()
            ponte.parar()
            dashboard.parar()
            thread.quit()
            assert thread.wait(4000)
            app.processEvents()
        print(json.dumps({'ok':resultado.get('ok'),'saida':str(args.saida),'pages':len(resultado.get('pages',[]))},ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
