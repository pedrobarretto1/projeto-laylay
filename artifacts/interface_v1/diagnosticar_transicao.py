"""Amostras nativas de startup/layout; sem mente nem captura de apps do usuário."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import tempfile
import time

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
os.environ['QT_QPA_PLATFORM'] = 'windows'
os.environ['LAYLAY_REDUZIR_MOVIMENTO'] = '0'
from PySide6.QtCore import QSettings
from PySide6.QtGui import QCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEngineScript
from cliente import terminal_laylay_2 as terminal
from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1


def main() -> None:
    saida = RAIZ / 'artifacts/interface_v1/ilha_integrada_suave' / (sys.argv[1] if len(sys.argv)>1 else 'baseline')
    saida.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='laylay-motion-') as pref:
        terminal.QSettings = lambda *_: QSettings(str(Path(pref)/'ui.ini'), QSettings.IniFormat)
        app = QApplication([])
        worker = terminal.PonteWorker('127.0.0.1', 1, 'diagnostico-sem-conexao')
        janela = JanelaInterfaceWebV1(worker, RAIZ)
        probe = QWebEngineScript()
        probe.setInjectionPoint(QWebEngineScript.DocumentCreation)
        probe.setWorldId(QWebEngineScript.MainWorld)
        probe.setSourceCode("""window.__pinturasIniciais=[];function amostrar(t){__pinturasIniciais.push({t,modo:window.LaylayInterface?.state.mode||null,classe:document.body?.className||'',filhos:document.getElementById('workspace')?.childElementCount||0});if(__pinturasIniciais.length<75)requestAnimationFrame(amostrar)}requestAnimationFrame(amostrar);""")
        janela.pagina_web.scripts().insert(probe)
        janela.web.reload()
        QCursor.setPos(janela.screen().availableGeometry().bottomLeft())
        janela.apresentar('desktop')
        if hasattr(janela, 'iniciar_apresentacao'):
            janela.iniciar_apresentacao()
        else:
            janela.show()
        registro = {'plataforma':app.platformName(), 'startup':[], 'transicoes':[], 'mente_iniciada':False}
        inicial = time.monotonic()
        for i in range(55):
            registro['startup'].append({'ms':round((time.monotonic()-inicial)*1000), 'visivel':janela.isVisible(), 'opacidade':janela.windowOpacity(), 'web_visivel':janela.web.isVisible(), 'pronta':janela.ponte_web._pronta})
            if i in (0,2,5,12,25):janela.grab().save(str(saida/f'startup-{i:02}.png'))
            QTest.qWait(20)

        def js(codigo: str):
            retorno=[]
            janela.pagina_web.runJavaScript(codigo, retorno.append)
            limite=time.monotonic()+5
            while not retorno and time.monotonic()<limite:QTest.qWait(5)
            assert retorno
            return retorno[0]

        registro['pinturas_iniciais'] = json.loads(js('JSON.stringify(window.__pinturasIniciais||[])'))
        if sys.argv[1].startswith('player'):
            from validar_ilha_suave import validar_ilha_suave
            trace = []
            original_viewport = janela.definir_viewport_streaming
            def viewport_observado(dados):
                antes = janela._streaming_pagina.captura.estado if janela._streaming_pagina else None
                resposta = original_viewport(dados)
                depois = janela._streaming_pagina.captura.estado if janela._streaming_pagina else None
                trace.append({'rect':json.loads(dados),'web':[janela.web.width(),janela.web.height()],
                              'aceito':resposta,'captura_antes':antes,'captura_depois':depois})
                return resposta
            janela.definir_viewport_streaming = viewport_observado
            def aguardar(condicao, segundos=10):
                prazo=time.monotonic()+segundos
                while not condicao() and time.monotonic()<prazo:QTest.qWait(30)
                assert condicao(), 'Player não atingiu o estado esperado'
            def foto(nome):
                QTest.qWait(650)
                janela.grab().save(str(saida/(nome+'.png')))
            try:
                registro['player']=validar_ilha_suave(janela,js,aguardar,foto)
                print(json.dumps(registro['player'],ensure_ascii=False))
            finally:
                janela.definir_viewport_streaming=original_viewport
                (saida/'trace_viewport.json').write_text(json.dumps(trace,indent=2),encoding='utf-8')
                (saida/'resultado.json').write_text(json.dumps(registro,indent=2),encoding='utf-8')
                janela.close()
                app.processEvents()
            return
        hwnd=int(janela.winId())
        for nome in ('resumo','home','chat','resumo','compacta'):
            if nome=='resumo':janela.ponte_web.gesto_desktop('resumo')
            elif nome=='compacta':janela.recolher_desktop()
            else:janela.selecionar_pagina_desktop(nome)
            inicio=time.monotonic()
            for i in range(17):
                dom=json.loads(js("JSON.stringify((()=>{const n=document.querySelector('.desktop-expanded'),p=document.getElementById('page-content');return {modo:window.LaylayInterface?.state.mode,estado:window.LaylayInterface?.state.desktopState,view:window.LaylayInterface?.state.desktopView,largura:innerWidth,altura:innerHeight,display:n?getComputedStyle(n).display:null,layout:n?.getBoundingClientRect().toJSON(),pagina:p?.getBoundingClientRect().toJSON()}})())"))
                registro['transicoes'].append({'destino':nome,'ms':round((time.monotonic()-inicio)*1000),'hwnd':int(janela.winId()),'geometria':[janela.x(),janela.y(),janela.width(),janela.height()],'dom':dom})
                if i in (0,2,5,16):
                    captura=janela.grab()
                    captura.save(str(saida/f'{nome}-{len(registro["transicoes"]):03}.png'))
                    imagem=captura.toImage()
                    pontos=[imagem.pixelColor(x,y).alpha() for x in range(12,max(13,imagem.width()-12),25)
                            for y in range(12,max(13,imagem.height()-12),25)]
                    registro['transicoes'][-1]['amostras_alfa_interior']=pontos
                QTest.qWait(16)
        registro['mesmo_hwnd']=all(x['hwnd']==hwnd for x in registro['transicoes'])
        (saida/'resultado.json').write_text(json.dumps(registro,ensure_ascii=False,indent=2),encoding='utf-8')
        janela.close()
        app.processEvents()
        print(json.dumps({'saida':str(saida),'mesmo_hwnd':registro['mesmo_hwnd'],'primeiras_pinturas':registro['pinturas_iniciais'][:6],'primeiras_transicoes':registro['transicoes'][:3]},ensure_ascii=False))


if __name__=='__main__':main()
