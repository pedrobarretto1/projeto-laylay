"""Bancada Windows do renderer oficial, com preferências isoladas e sem mente.

Mantém a janela disponível para um arrasto físico e registra geometria/âncora.
Comandos locais de diagnóstico: foto, aba, recolher, encerrar. Não é launcher.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--saida', type=Path, required=True)
    parser.add_argument('--automatico', action='store_true', help='Prova integrada com eventos Qt sintéticos, sem mente.')
    args = parser.parse_args()
    saida = args.saida.resolve()
    saida.mkdir(parents=True, exist_ok=True)
    from PySide6.QtCore import QSettings, QTimer, Qt
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication
    import cliente.terminal_laylay_2 as terminal
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1

    app = QApplication([])
    app.setFont(QFont(terminal.carregar_fontes_interface(), 10))
    preferencias = QSettings(str(saida/'preferencias-isoladas.ini'), QSettings.IniFormat)
    terminal.QSettings = lambda *_: preferencias
    worker = terminal.PonteWorker('127.0.0.1', 1, 'bancada-local-sem-conexao')
    enviadas = []
    worker.enfileirar = lambda mensagem: enviadas.append(mensagem) or False
    janela = JanelaInterfaceWebV1(worker, RAIZ)
    janela.setWindowTitle('Laylay — prova de posição arrastável, sem mente')
    janela.apresentar('desktop')
    janela.show()
    identidade = [id(janela.web), id(janela.pagina_web), id(janela.canal), id(janela.controlador)]
    historico = []
    ultimo = [None]
    inicio = time.monotonic()

    def estado():
        ret = janela.geometry()
        area = janela.screen().availableGeometry()
        ancora = janela.ancora_desktop
        return {
            'geometry': [ret.x(), ret.y(), ret.width(), ret.height()],
            'workarea': [area.x(), area.y(), area.width(), area.height()],
            'anchor': [ancora.x(), ancora.y()],
            'phase': janela.estado_desktop,
            'transition_phase': janela._desktop_fase,
            'saved_position': preferencias.value('v1/desktop_posicao'),
            'hwnd': int(janela.winId()),
            'same_objects': identidade == [id(janela.web), id(janela.pagina_web), id(janela.canal), id(janela.controlador)],
            'renderer_ready': janela.ponte_web._pronta,
            'window_title': janela.windowTitle(), 'visible': janela.isVisible(),
            'enviadas': len(enviadas), 'mente_iniciada': False,
        }

    def foto(nome):
        janela.grab().save(str(saida/(nome+'.png')))

    def registrar():
        atual = estado()
        if atual != ultimo[0]:
            historico.append({'t': round(time.monotonic()-inicio, 3), **atual})
            ultimo[0] = atual
            temporario = saida/'estado.tmp'
            temporario.write_text(json.dumps({'current': atual, 'history': historico}, ensure_ascii=False, indent=2), encoding='utf-8')
            temporario.replace(saida/'estado.json')
        comando = saida/'comando.json'
        if comando.exists():
            pedido = json.loads(comando.read_text(encoding='utf-8-sig'))
            comando.unlink()
            acao = pedido.get('action')
            if acao == 'aba' and pedido.get('page') in ('home','chat','music','system','settings','memory','lamp','dev','streaming'):
                janela.selecionar_pagina_desktop(pedido['page'])
            elif acao == 'recolher':
                janela.recolher_desktop()
            elif acao == 'foto':
                nome = str(pedido.get('name', 'captura'))
                if nome.replace('-', '').replace('_', '').isalnum():
                    foto(nome)
            elif acao == 'inspecionar':
                janela.pagina_web.runJavaScript("JSON.stringify({phase:LaylayInterface.state.desktopPhase,seq:LaylayInterface.state.desktopTransition,classes:document.body.className,width:innerWidth,height:innerHeight,overview:getComputedStyle(document.querySelector('.desktop-overview')).opacity})", lambda valor: (saida/'dom.json').write_text(str(valor), encoding='utf-8'))
            elif acao == 'encerrar':
                foto('ultimo-estado')
                janela.close()
                app.quit()

    timer = QTimer()
    timer.timeout.connect(registrar)
    timer.start(100)
    QTimer.singleShot(1300, lambda: foto('inicio'))
    if args.automatico:
        def prova_integrada():
            from PySide6.QtCore import QPoint
            from PySide6.QtGui import QCursor
            from PySide6.QtTest import QTest
            import cliente.terminal_2.interface_web_v1 as modulo

            def aguardar(condicao, segundos=8):
                limite = time.monotonic()+segundos
                while not condicao() and time.monotonic() < limite:
                    QTest.qWait(20)
                assert condicao(), 'A fronteira esperada não foi atingida'

            def js(codigo):
                resposta = []
                janela.pagina_web.runJavaScript(codigo, resposta.append)
                aguardar(lambda: bool(resposta))
                return resposta[0]

            pressionado = [False]
            original = modulo.botao_esquerdo_pressionado
            modulo.botao_esquerdo_pressionado = lambda: pressionado[0]
            resultado = {'tipo': 'integração QtWebEngine/QWebChannel com entrada sintética Qt; sem prova Sky', 'mente_iniciada': False}
            try:
                aguardar(lambda: janela.ponte_web._pronta)
                inicial = estado()
                ret = json.loads(js("JSON.stringify((()=>{const r=document.querySelector('.desktop-compact').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})())"))
                receptor = janela.web.focusProxy() or janela.web
                ponto = QPoint(round(ret['x']), round(ret['y']))
                origem = janela.mapToGlobal(ponto)
                QCursor.setPos(origem)
                pressionado[0] = True
                QTest.mousePress(receptor, Qt.LeftButton, Qt.NoModifier, ponto)
                QTest.qWait(100)
                QCursor.setPos(origem+QPoint(160, 85))
                QTest.mouseMove(receptor, ponto+QPoint(160,85))
                aguardar(lambda: janela._arrastando_desktop)
                QTest.qWait(150)
                QTest.mouseRelease(receptor, Qt.LeftButton, Qt.NoModifier, janela.mapFromGlobal(QCursor.pos()))
                pressionado[0] = False
                aguardar(lambda: not janela._arrastando_desktop)
                aguardar(lambda: janela._desktop_fase == 'idle')
                QTest.qWait(180)
                arrastada = estado()
                assert arrastada['geometry'][:2] != inicial['geometry'][:2]
                assert arrastada['saved_position'] and arrastada['phase'] == 'compact', 'Arrasto não deve expandir'
                foto('arrastada')
                destino = janela.geometry()
                QTest.mouseClick(receptor, Qt.LeftButton, Qt.NoModifier, janela.rect().center())
                aguardar(lambda: janela.estado_desktop == 'expanded')
                aguardar(lambda: janela._desktop_fase == 'idle')
                aguardar(lambda: js("getComputedStyle(document.querySelector('.desktop-overview')).opacity==='1'"))
                foto('clique-apos-arrasto')
                for pagina in ('home','chat','music','lamp','streaming','memory','system','dev','settings'):
                    js('LaylayInterface.goPage('+json.dumps(pagina)+')')
                    aguardar(lambda: janela._desktop_fase == 'idle')
                    aguardar(lambda: js("getComputedStyle(document.querySelector('.desktop-page-content')).opacity==='1'"))
                    assert int(janela.winId()) == inicial['hwnd']
                    assert estado()['same_objects']
                    if pagina == 'settings':
                        foto('configuracoes-posicao')
                    janela.recolher_desktop()
                    aguardar(lambda: janela._desktop_fase == 'idle')
                    assert janela.geometry() == destino
                    assert preferencias.value('v1/desktop_posicao') == arrastada['saved_position']
                assert not enviadas
                resultado.update(ok=True, inicial=inicial, arrastada=arrastada, final=estado(), abas=9)
            except Exception as erro:
                resultado.update(ok=False, erro=repr(erro), final=estado())
                print('RED '+repr(erro), flush=True)
            finally:
                pressionado[0] = False
                modulo.botao_esquerdo_pressionado = original
                (saida/'resultado-integrado.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
                registrar()
                janela.close()
                app.quit()
        QTimer.singleShot(1800, prova_integrada)
    QTimer.singleShot(15*60*1000, app.quit)
    print('Bancada disponível; INI isolado em '+str(saida), flush=True)
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
