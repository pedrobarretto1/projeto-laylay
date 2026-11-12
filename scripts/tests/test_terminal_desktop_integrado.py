"""Uma única superfície desktop muda apresentação sem criar autoridade mental."""
from __future__ import annotations

from pathlib import Path
import json
import pytest

pytest.importorskip("PySide6.QtWebEngineWidgets")

from scripts.tests.test_terminal_interface_web_v1 import interface_web
from scripts.tests.test_terminal_web_v1_estabilidade import conversa_web
from scripts.tests.test_terminal_web_v1_paginas import paginas_reais


def test_aba_conversa_nao_reserva_faixa_vazia_para_atalho_de_conversas(conversa_web):
    _janela, _ponte, _entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: js("LaylayInterface.state.mode==='desktop'"))
    medida = json.loads(js("""JSON.stringify((()=>{
      const page=document.querySelector('.desktop-page');
      const context=page.querySelector('.context-bar').getBoundingClientRect();
      const shortcut=page.querySelector('.desktop-conversations');
      const content=page.querySelector('.desktop-page-content').getBoundingClientRect();
      return {
        visible:!shortcut.hidden&&getComputedStyle(shortcut).display!=='none',
        position:getComputedStyle(shortcut).position,
        contentGap:content.top-context.bottom
      };
    })())"""))
    assert medida["visible"]
    assert medida["position"] == "absolute"
    assert abs(medida["contentGap"]) < 1


def test_posicao_inicial_da_ilha_libera_a_faixa_das_abas_do_navegador(interface_web):
    _app, _worker, janela, enviadas, _eventos = interface_web
    janela.apresentar('desktop')
    tela = janela.screen()
    area = tela.availableGeometry()
    assert janela.geometry().top() == area.top(), "A ilha deve encostar no topo da área utilizável, abaixo de barras reservadas"
    assert abs(janela.geometry().center().x()-area.center().x()) <= 1
    assert enviadas == []


def test_posicao_inicial_nao_fica_atras_da_barra_reservada_no_topo(interface_web, monkeypatch):
    from PySide6.QtCore import QRect

    _app, _worker, janela, enviadas, _eventos = interface_web

    class TelaComBarraSuperior:
        def geometry(self):
            return QRect(0, 0, 1920, 1080)

        def availableGeometry(self):
            return QRect(0, 48, 1920, 1032)

    monkeypatch.setattr(janela, "_resolver_tela_desktop", lambda: TelaComBarraSuperior())
    monkeypatch.setattr(janela, "_observar_tela_desktop", lambda _tela: None)
    janela.apresentar("desktop")

    assert janela.geometry().top() == 48
    assert enviadas == []


def test_mascara_da_ilha_preserva_o_centro_da_borda_superior():
    from PySide6.QtCore import QPoint
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1, _PERFIL_ILHA_DESKTOP

    mascara = JanelaInterfaceWebV1._regiao_desktop(272, 36, compacta=True)
    mascara_expandida = JanelaInterfaceWebV1._regiao_desktop(272, 36)

    assert mascara.contains(QPoint(136, 0))
    assert mascara.contains(QPoint(136, 18))
    assert mascara.contains(QPoint(136, 35))
    assert not mascara.contains(QPoint(9, 8))
    assert mascara.contains(QPoint(10, 8)), "A curva superior deve começar cedo e se afastar gradualmente"
    assert not mascara.contains(QPoint(13, 18))
    assert mascara.contains(QPoint(14, 18))
    assert not mascara.contains(QPoint(13, 24))
    assert mascara.contains(QPoint(14, 24)), "A lateral deve permanecer quase vertical, sem voltar para fora"
    assert not mascara.contains(QPoint(17, 35)), "O canto inferior arredondado deve abranger vários pixels"
    assert mascara.contains(QPoint(18, 35))
    assert mascara.contains(QPoint(20, 35)), "O fundo central deve permanecer reto"
    assert not mascara.contains(QPoint(262, 8))
    assert mascara.contains(QPoint(261, 8))
    assert not mascara.contains(QPoint(258, 18))
    assert mascara.contains(QPoint(257, 18))
    assert not mascara.contains(QPoint(258, 24))
    assert mascara.contains(QPoint(257, 24))
    assert mascara.contains(QPoint(251, 35))
    for y in range(36):
        esquerda = next(x for x in range(136) if mascara.contains(QPoint(x, y)))
        direita = next(x for x in range(271, 135, -1) if mascara.contains(QPoint(x, y)))
        assert abs(esquerda + direita - 271) <= 2
    assert mascara_expandida.contains(QPoint(16, 35)), "O recorte do painel expandido não deve mudar"

    def verificar_tangente(vetor_entrada, vetor_saida):
        x1, y1 = vetor_entrada
        x2, y2 = vetor_saida
        assert x1 * y2 - y1 * x2 == 0
        assert x1 * x2 + y1 * y2 > 0

    primeiro_vetor = ultimo_vetor = None
    atual = None
    for comando, *pontos in _PERFIL_ILHA_DESKTOP:
        if comando == "M":
            atual = tuple(pontos)
        elif comando == "L":
            destino = tuple(pontos)
            vetor = (destino[0] - atual[0], destino[1] - atual[1])
            if ultimo_vetor is None:
                primeiro_vetor = vetor
            else:
                verificar_tangente(ultimo_vetor, vetor)
            ultimo_vetor, atual = vetor, destino
        elif comando == "C":
            controle1 = tuple(pontos[:2])
            controle2 = tuple(pontos[2:4])
            destino = tuple(pontos[4:6])
            vetor_inicio = (controle1[0] - atual[0], controle1[1] - atual[1])
            vetor_fim = (destino[0] - controle2[0], destino[1] - controle2[1])
            if ultimo_vetor is None:
                primeiro_vetor = vetor_inicio
            else:
                verificar_tangente(ultimo_vetor, vetor_inicio)
            ultimo_vetor, atual = vetor_fim, destino
    verificar_tangente(ultimo_vetor, primeiro_vetor)


def test_expansao_em_tela_baixa_preserva_faixa_livre_do_navegador():
    from PySide6.QtCore import QRect
    from cliente.terminal_2.apresentacao_desktop import geometria_desktop

    area = QRect(0, 0, 1280, 680)
    for pagina in ('home', 'chat', 'music', 'system', 'settings', 'memory', 'lamp', 'dev', 'streaming'):
        retangulo = geometria_desktop(area, expandida=True, pagina=pagina)
        assert retangulo.top() == area.top()
        assert area.contains(retangulo)
        assert retangulo.height() >= 320


def test_geometria_integrada_respeita_area_util_sem_espaco_superfluo():
    from PySide6.QtCore import QRect
    from cliente.terminal_2.apresentacao_desktop import geometria_desktop

    area_util = QRect(-1920, 40, 1920, 1000)
    compacta = geometria_desktop(area_util)
    expandida = geometria_desktop(area_util, expandida=True)
    assert compacta.top() == expandida.top() == area_util.top()
    assert compacta.height() == 36
    assert area_util.contains(compacta) and area_util.contains(expandida)
    assert area_util.bottom() >= expandida.bottom()
    assert area_util.left() <= expandida.left() and expandida.right() <= area_util.right()


@pytest.mark.parametrize('area_xywh', [(0,0,1920,1080),(-1920,-40,1920,1080),(0,0,390,680)])
def test_geometria_permanece_fixada_no_centro_superior_em_todos_os_tamanhos(area_xywh):
    from PySide6.QtCore import QRect
    from cliente.terminal_2.apresentacao_desktop import geometria_desktop

    area = QRect(*area_xywh)
    compacta = geometria_desktop(area)
    for pagina in ('home','chat','music','dev'):
        expandida = geometria_desktop(area, expandida=True, pagina=pagina)
        assert area.contains(expandida)
        assert expandida.top() == area.top()
        assert abs(expandida.center().x() - area.center().x()) <= 1
        assert geometria_desktop(area, recolhida=True).size().width() == 48
        assert geometria_desktop(area, recolhida=True).size().height() == 4
        assert geometria_desktop(area) == compacta
    assert abs(compacta.center().x() - area.center().x()) <= 1
    assert compacta.top() == area.top()


def test_ilha_fica_fixa_ignora_posicao_salva_e_nao_aceita_arrasto(interface_web):
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1

    _app, worker, janela, enviadas, _eventos = interface_web
    registro = json.dumps({
        'version': 1,
        'screen': {'name': 'monitor-antigo', 'manufacturer': '', 'model': '', 'serial': ''},
        'offsets': {'center_x': 120, 'top_y': 240},
    })
    janela.preferencias.setValue('v1/desktop_posicao', registro)
    reaberta = JanelaInterfaceWebV1(worker, Path(__file__).parents[2], diretorio_web=janela.diretorio_web)
    try:
        reaberta.apresentar('desktop')
        area = reaberta.screen().availableGeometry()
        assert reaberta.geometry().top() == area.top()
        assert abs(reaberta.geometry().center().x() - area.center().x()) <= 1
        geometria_fixa = reaberta.geometry()
        assert reaberta.geometry() == geometria_fixa
        assert not hasattr(reaberta.ponte_web, 'arrastar_desktop')
        assert not hasattr(reaberta.ponte_web, 'finalizar_arrasto_desktop')
        assert reaberta.preferencias.value('v1/desktop_posicao') == registro
    finally:
        reaberta.close()
    assert enviadas == []


def test_timer_de_recolhimento_e_independente_do_prazo_de_entrada(interface_web, monkeypatch):
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QCursor

    _app, _worker, janela, enviadas, _eventos = interface_web
    monkeypatch.setattr(QCursor, 'pos', lambda: QPoint(-10000, -10000))
    janela.show()
    janela.apresentar('desktop')
    assert janela.geometry().size().width() == 272
    assert janela.geometry().size().height() == 36
    assert janela._recolher_ilha_timer.isActive()
    assert janela._recolher_ilha_timer.interval() == 5000
    assert janela._recolher_ilha_timer is not janela._prazo_entrada

    destinos = []
    monkeypatch.setattr(janela, '_animar_geometria_desktop', lambda: destinos.append(janela._desktop_recolhida))
    janela._prazo_entrada.start()
    assert janela._prazo_entrada.isActive()
    assert janela._recolher_ilha_timer.isActive()
    janela._prazo_entrada.stop()
    assert janela._recolher_ilha_timer.isActive()
    janela._recolher_ilha_por_inatividade()
    assert janela._desktop_recolhida
    assert destinos == [True]
    janela.estado_desktop = 'expanded'
    janela._desktop_recolhida = False
    janela._recolher_ilha_por_inatividade()
    assert not janela._desktop_recolhida
    assert enviadas == []


def test_timer_nao_recolhe_sob_cursor_e_hover_revela_a_ilha(interface_web, monkeypatch):
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QCursor

    _app, _worker, janela, enviadas, _eventos = interface_web
    janela.show()
    janela.apresentar('desktop')
    cursor = [janela.mapToGlobal(janela.rect().center())]
    monkeypatch.setattr(QCursor, 'pos', lambda: QPoint(cursor[0]))
    destinos = []
    monkeypatch.setattr(janela, '_animar_geometria_desktop', lambda: destinos.append(janela._desktop_recolhida))
    janela._recolher_ilha_por_inatividade()
    assert not janela._desktop_recolhida
    assert janela._desktop_dentro

    janela._desktop_recolhida = True
    from cliente.terminal_2.apresentacao_desktop import geometria_desktop
    janela.setGeometry(geometria_desktop(janela.screen().availableGeometry(), recolhida=True))
    janela._atualizar_mascara_desktop()
    cursor[0] = janela.mapToGlobal(janela.rect().center())
    janela._observar_cursor_desktop()
    assert not janela._desktop_recolhida
    assert destinos == [False]
    assert enviadas == []
    assert janela.screen().availableGeometry().contains(janela.geometry())
    assert janela.estado_desktop == 'compact'
    assert enviadas == []


@pytest.mark.parametrize('fracao_x', [0.2, 0.5, 0.8])
def test_clique_do_mouse_na_superficie_compacta_expande_painel(conversa_web, fracao_x):
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest

    janela, _ponte, entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == 'desktop' and janela._desktop_fase == 'idle')
    ponto = QPoint(round(janela.web.width() * fracao_x), janela.web.height() // 2)
    alvo = js(f"document.elementFromPoint({ponto.x()},{ponto.y()})?.closest('button')?.dataset.desktop || ''")
    assert alvo == 'expandir', 'A superfície visível deve entregar o clique ao botão de expansão'
    QTest.mouseClick(janela.web.focusProxy(), Qt.LeftButton, pos=ponto)
    aguardar(lambda: janela.estado_desktop == 'expanded' and janela._desktop_fase == 'idle')
    assert janela.height() > 36
    assert entradas == [], 'Expandir a interface não autoriza comandos para a mente'


@pytest.mark.parametrize('reduzir_movimento', [False, True])
def test_entrada_compacta_confirma_renderer_e_libera_opacidade_antes_do_clique(conversa_web, reduzir_movimento):
    from PySide6.QtTest import QTest

    janela, _ponte, entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela._desktop_fase == 'idle')
    janela.definir_preferencia('reduzir_movimento', reduzir_movimento)
    janela.iniciar_apresentacao()
    QTest.qWait(600)
    assert not janela._entrada_pendente, 'O renderer compacto deve confirmar a entrada sem esperar o timeout'
    assert janela.windowOpacity() == 1
    assert janela._erro_entrada is None
    assert entradas == []


def test_hover_mantem_ilha_recolhida_e_clique_abre_painel(conversa_web, monkeypatch):
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QCursor
    from PySide6.QtTest import QTest

    janela, _ponte, entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == 'desktop')
    compacta = janela.geometry()
    cursor = [janela.mapToGlobal(janela.rect().center())]
    monkeypatch.setattr(QCursor, 'pos', lambda: cursor[0])
    janela._observar_cursor_desktop()
    QTest.qWait(350)
    assert janela.estado_desktop == 'compact', 'Hover não deve abrir a janela nativa'
    assert janela.geometry() == compacta
    assert js("LaylayInterface.state.desktopState==='compact'")
    assert not hasattr(janela, '_abrir_desktop_timer')

    js("document.querySelector('.desktop-compact').click()")
    aguardar(lambda: janela.estado_desktop == 'expanded' and janela._desktop_fase == 'idle')
    assert js("LaylayInterface.state.desktopState==='expanded'")
    assert janela.desktop_fixado
    assert entradas == [], 'Abrir pelo clique não pode enviar um comando'


def test_recolhimento_automatico_publica_barra_preta_hover_e_clique(conversa_web, monkeypatch):
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QCursor

    janela, _ponte, entradas, js, aguardar = conversa_web
    fora = QPoint(-10000, -10000)
    cursor = [fora]
    monkeypatch.setattr(QCursor, 'pos', lambda: QPoint(cursor[0]))
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == 'desktop')
    aguardar(lambda: janela._desktop_fase == 'idle')
    assert janela.geometry().width() == 272 and janela.geometry().height() == 36
    assert janela._recolher_ilha_timer.isActive()
    assert janela._recolher_ilha_timer.interval() == 5000

    import cliente.terminal_2.interface_web_v1 as modulo
    monkeypatch.setattr(modulo, 'TEMPO_RECOLHIMENTO_ILHA_MS', 100)
    janela._reiniciar_recolhimento_ilha()
    aguardar(lambda: janela._desktop_recolhida and js('LaylayInterface.state.desktopDocked===true'))
    aguardar(lambda: janela._desktop_fase == 'idle')
    barra = json.loads(js("""JSON.stringify((()=>{
      const shell=document.querySelector('.desktop-island'),style=getComputedStyle(shell);
      return {
        size:[shell.getBoundingClientRect().width,shell.getBoundingClientRect().height],
        black:style.backgroundColor==='rgb(0, 0, 0)',
        pure:shell.children.length===1&&shell.firstElementChild.classList.contains('desktop-docked-trigger'),
        decoration:getComputedStyle(shell,'::before').content==='none'&&getComputedStyle(shell,'::after').content==='none'
      };
    })())"""))
    assert barra == {'size': [48, 4], 'black': True, 'pure': True, 'decoration': True}

    cursor[0] = janela.mapToGlobal(janela.rect().center())
    ponto_barra = janela.mapFromGlobal(cursor[0])
    assert janela.rect().contains(ponto_barra)
    assert janela.mask().contains(ponto_barra)
    janela._observar_cursor_desktop()
    aguardar(lambda: not janela._desktop_recolhida and js('LaylayInterface.state.desktopDocked===false'))
    aguardar(lambda: js("document.querySelector('.desktop-compact')!==null"))
    monkeypatch.setattr(modulo, 'TEMPO_RECOLHIMENTO_ILHA_MS', 5000)
    js("document.querySelector('.desktop-compact').click()")
    aguardar(lambda: janela.estado_desktop == 'expanded' and js("LaylayInterface.state.desktopState==='expanded'"))
    js("document.querySelector('[data-desktop=\"recolher\"]').click()")
    aguardar(lambda: janela.estado_desktop == 'compact' and js("LaylayInterface.state.desktopState==='compact'"))

    cursor[0] = fora
    janela._observar_cursor_desktop()
    assert janela._recolher_ilha_timer.isActive()
    assert janela._recolher_ilha_timer.remainingTime() > 4500

    monkeypatch.setattr(modulo, 'TEMPO_RECOLHIMENTO_ILHA_MS', 100)
    janela._reiniciar_recolhimento_ilha()
    aguardar(lambda: janela._desktop_recolhida and js('LaylayInterface.state.desktopDocked===true'))
    aguardar(lambda: janela._desktop_fase == 'idle')
    cursor[0] = janela.mapToGlobal(janela.rect().center())
    js("document.querySelector('.desktop-docked-trigger').click()")
    aguardar(lambda: janela.estado_desktop == 'expanded' and js("LaylayInterface.state.desktopState==='expanded'"))
    js("document.querySelector('[data-desktop=\"recolher\"]').click()")
    aguardar(lambda: janela.estado_desktop == 'compact' and js("LaylayInterface.state.desktopState==='compact'"))
    assert entradas == []


def test_recolhimento_da_ilha_anima_ate_a_barra_sem_aplicar_mascara_antecipada(conversa_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation, QPoint
    from PySide6.QtGui import QCursor

    janela, _ponte, entradas, js, aguardar = conversa_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    monkeypatch.setattr(QCursor, 'pos', lambda: QPoint(-10000, -10000))
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == 'desktop' and janela._desktop_fase == 'idle')
    janela._recolher_ilha_por_inatividade()
    aguardar(lambda: janela._desktop_fase == 'resizing')

    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration() // 2)

    centro = janela.rect().center()
    assert janela.width() > 48 and janela.height() > 4
    assert janela.mask().contains(centro), "A máscara deve acompanhar a cápsula durante a animação"
    assert janela._transicao_cobertura is None, "A cobertura só pertence ao painel expandido"
    aguardar(lambda: js("document.querySelector('.desktop-compact')!==null"))
    movimento = json.loads(js("""JSON.stringify((()=>{
      const shell=document.querySelector('.desktop-island'),compact=shell.querySelector('.desktop-compact');
      const animations=compact.getAnimations();
      return {motion:shell.dataset.dockMotion,duration:animations[0]?.effect.getTiming().duration,
        count:animations.length,transition:getComputedStyle(shell).transitionDuration};
    })())"""))
    assert movimento == {
        'motion': 'closing', 'duration': janela._animacao_desktop.duration(),
        'count': 1, 'transition': '0.36s',
    }
    assert entradas == []


def test_hover_reverte_animacao_da_barra_sem_salto_de_mascara(conversa_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation, QPoint
    from PySide6.QtGui import QCursor

    janela, _ponte, entradas, js, aguardar = conversa_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    cursor = [QPoint(-10000, -10000)]
    monkeypatch.setattr(QCursor, 'pos', lambda: QPoint(cursor[0]))
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == 'desktop' and janela._desktop_fase == 'idle')
    janela._recolher_ilha_por_inatividade()
    aguardar(lambda: janela._desktop_fase == 'resizing')
    aguardar(lambda: js("document.querySelector('.desktop-island').dataset.dockMotion==='closing'"))
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration() // 2)

    largura_antes_do_hover = janela.width()
    cursor[0] = janela.mapToGlobal(janela.rect().center())
    janela._observar_cursor_desktop()
    aguardar(lambda: js("document.querySelector('.desktop-island').dataset.dockMotion==='opening'"))
    assert js("document.querySelector('.desktop-compact').getAnimations()[0].playbackRate<0")
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    assert janela.width() >= largura_antes_do_hover, "A reversão deve partir da geometria intermediária atual"
    centro = janela.rect().center()
    assert janela.width() > 48 and janela.height() > 4
    assert janela.mask().contains(centro), "O hover deve revelar a cápsula junto com a geometria"
    assert janela._transicao_cobertura is None
    assert js("document.querySelector('.desktop-compact')!==null")
    aguardar(lambda: janela._desktop_fase == 'idle')
    assert not janela._desktop_recolhida
    assert entradas == []


def test_ativar_movimento_reduzido_durante_recolhimento_conclui_geometria(conversa_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation, QPoint
    from PySide6.QtGui import QCursor

    janela, _ponte, entradas, js, aguardar = conversa_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    monkeypatch.setattr(QCursor, 'pos', lambda: QPoint(-10000, -10000))
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == 'desktop' and janela._desktop_fase == 'idle')

    janela._recolher_ilha_por_inatividade()
    aguardar(lambda: janela._desktop_fase == 'resizing')
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration() // 2)
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running

    janela.definir_preferencia('reduzir_movimento', True)

    assert janela._animacao_desktop.state() == QAbstractAnimation.Stopped
    assert janela.geometry().size().width() == 48
    assert janela.geometry().size().height() == 4
    aguardar(lambda: janela._desktop_fase == 'idle' and js('LaylayInterface.state.desktopDocked===true'))
    assert entradas == []


def test_movimento_reduzido_mantem_dock_sem_animacao_web(conversa_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation, QPoint
    from PySide6.QtGui import QCursor

    janela, _ponte, entradas, js, aguardar = conversa_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '1')
    monkeypatch.setattr(QCursor, 'pos', lambda: QPoint(-10000, -10000))
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == 'desktop' and janela._desktop_fase == 'idle')
    js("LaylayInterface.state.preferences.reduced=true")

    janela._recolher_ilha_por_inatividade()
    aguardar(lambda: janela._desktop_fase == 'idle' and js('LaylayInterface.state.desktopDocked===true'))

    assert janela.geometry().size().width() == 48
    assert janela.geometry().size().height() == 4
    assert janela._animacao_desktop.state() == QAbstractAnimation.Stopped
    assert js("document.querySelector('.desktop-docked-trigger')!==null")
    assert js("document.querySelector('.desktop-island').getAnimations().length===0")
    assert entradas == []


def test_fechamento_manual_nao_reabre_por_hover_e_click_abre(interface_web, monkeypatch):
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QCursor
    from PySide6.QtTest import QTest

    _app, _worker, janela, enviadas, _eventos = interface_web
    fora = QPoint(-10000, -10000)
    cursor = [QPoint(0, 0)]
    monkeypatch.setattr(QCursor, 'pos', lambda: cursor[0])
    janela.show()
    janela.apresentar('desktop')
    centro = janela.rect().center()

    cursor[0] = janela.mapToGlobal(centro)
    janela._observar_cursor_desktop()
    QTest.qWait(310)
    assert janela.estado_desktop == 'compact'
    janela.ponte_web.gesto_desktop('recolher')
    QTest.qWait(310)
    assert janela.estado_desktop == 'compact', 'Fechar sob o cursor não pode reabrir a ilha'

    cursor[0] = fora
    janela._observar_cursor_desktop()
    cursor[0] = janela.mapToGlobal(centro)
    janela._observar_cursor_desktop()
    QTest.qWait(310)
    assert janela.estado_desktop == 'compact', 'Uma nova entrada do mouse deve somente animar o mascote'
    janela.ponte_web.gesto_desktop('expandir')
    QTest.qWait(310)
    assert janela.estado_desktop == 'expanded', 'O gesto de clique deve abrir a ilha'
    janela.ponte_web.edicao_desktop(True)
    cursor[0] = fora
    janela._observar_cursor_desktop()
    QTest.qWait(850)
    assert janela.estado_desktop == 'expanded', 'Sair com edição em andamento deve preservar o painel'
    janela.ponte_web.gesto_desktop('interagir')
    janela.ponte_web.edicao_desktop(False)
    QTest.qWait(850)
    assert janela.estado_desktop == 'expanded', 'Interagir deve preservar o painel aberto'
    assert enviadas == []


def test_rascunho_guardado_persiste_ao_abrir_painel_por_click(conversa_web, monkeypatch):
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QCursor
    from PySide6.QtTest import QTest

    janela, _ponte, entradas, js, aguardar = conversa_web
    fora = QPoint(-10000, -10000)
    cursor = [fora]
    monkeypatch.setattr(QCursor, 'pos', lambda: cursor[0])
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: js("LaylayInterface.state.mode==='desktop' && LaylayInterface.state.desktopPhase==='idle'"))
    cursor[0] = janela.mapToGlobal(janela.geometry().center())
    janela._observar_cursor_desktop()
    QTest.qWait(350)
    assert janela.estado_desktop == 'compact'
    js("document.querySelector('.desktop-compact').click()")
    aguardar(lambda: js("LaylayInterface.state.desktopState==='expanded' && LaylayInterface.state.desktopPhase==='idle'"))
    js("LaylayInterface.goPage('chat')")
    aguardar(lambda: js("LaylayInterface.state.page==='chat'"))
    js("LaylayInterface.state.draft='Rascunho guardado'; LaylayInterface.invalidate()")
    assert js("LaylayInterface.state.draft") == 'Rascunho guardado'

    cursor[0] = fora
    janela._observar_cursor_desktop()
    QTest.qWait(850)
    aguardar(lambda: js("LaylayInterface.state.desktopState==='expanded' && LaylayInterface.state.desktopPhase==='idle'"))
    assert js('LaylayInterface.state.draft') == 'Rascunho guardado'
    js("document.querySelector('[data-desktop=\"recolher\"]').click()")
    aguardar(lambda: js("LaylayInterface.state.desktopState==='compact' && LaylayInterface.state.desktopPhase==='idle'"))
    js("document.querySelector('.desktop-compact').click()")
    aguardar(lambda: js("LaylayInterface.state.desktopState==='expanded' && LaylayInterface.state.desktopPhase==='idle'"))
    assert js("LaylayInterface.state.draft") == 'Rascunho guardado'
    assert entradas == []


def test_player_streaming_e_filho_da_mesma_janela_sem_dialogo(interface_web):
    from PySide6.QtWidgets import QApplication, QDialog

    app, _worker, janela, enviadas, _eventos = interface_web
    janela.show()
    janela.apresentar("desktop")
    janela.selecionar_pagina_desktop("streaming")
    antes = set(QApplication.topLevelWidgets())
    janela.abrir_streaming()
    app.processEvents()
    assert janela._streaming_pagina is not None
    assert janela._streaming_pagina.window() is janela, "Streaming precisa compartilhar a janela da ilha"
    assert not any(isinstance(w, QDialog) and w.isVisible() for w in set(QApplication.topLevelWidgets()) - antes)
    janela.parar_streaming()
    assert enviadas == [], "Player/captura não podem gerar comando para a mente"


def test_prazo_de_inatividade_e_vinte_segundos_e_telemetria_nao_renova(interface_web, monkeypatch):
    from PySide6.QtGui import QCursor
    from PySide6.QtTest import QTest

    _app, worker, janela, enviadas, _eventos = interface_web
    janela.show()
    janela.apresentar("desktop")
    monkeypatch.setattr(QCursor, "pos", lambda: janela.mapToGlobal(janela.rect().bottomRight()) + janela.rect().bottomRight())
    janela.expandir_desktop(fixar=True)
    timer = janela._inatividade_desktop_timer
    assert timer.interval() == 20_000 and timer.isActive()
    QTest.qWait(80)
    restante = timer.remainingTime()
    for _ in range(4):
        worker.mensagem.emit({"type": "state", "activity": "idle"})
        janela._observar_cursor_desktop()
    assert 0 < timer.remainingTime() <= restante + 5, "Observação passiva não é interação"
    janela.registrar_atividade_desktop()
    assert timer.remainingTime() > restante
    assert enviadas == []


def test_foco_fala_e_transmissao_protegem_desktop_e_troca_de_app_recolhe(interface_web, monkeypatch):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    _app, _worker, janela, enviadas, _eventos = interface_web
    janela.show()
    janela.apresentar('desktop')
    janela.expandir_desktop(fixar=True)
    janela._desktop_fase = 'idle'  # O fixture não possui renderer para confirmar o ACK visual.
    janela._foco_desktop_observado = True
    timer = janela._inatividade_desktop_timer
    monkeypatch.setattr(janela, '_desktop_em_foco', lambda: True)
    timer.setInterval(160)
    timer.start()
    QTest.qWait(90)
    QTest.keyClick(janela.web.focusProxy() or janela.web, Qt.Key_A)
    QTest.qWait(90)
    assert janela.estado_desktop == 'expanded'
    assert timer.remainingTime() > 19_000

    # Mesmo quando o prazo antigo termina, a janela em foco não recolhe.
    timer.timeout.emit()
    assert janela.estado_desktop == 'expanded'

    # Fora de foco, ela espera a frase terminar.
    monkeypatch.setattr(janela, '_desktop_em_foco', lambda: False)
    monkeypatch.setattr(janela, '_fala_em_andamento', lambda: True)
    janela._recolher_por_perda_de_foco()
    assert janela.estado_desktop == 'expanded'
    assert janela._recolher_foco_timer.isActive()

    # Uma transmissão em andamento também não pode ser encerrada por troca de app.
    monkeypatch.setattr(janela, '_fala_em_andamento', lambda: False)
    monkeypatch.setattr(janela, '_streaming_em_transmissao', lambda: True)
    janela._recolher_por_perda_de_foco()
    assert janela.estado_desktop == 'expanded'

    # Depois da fala/transmissão, mudar de aplicativo recolhe.
    monkeypatch.setattr(janela, '_streaming_em_transmissao', lambda: False)
    janela._recolher_por_perda_de_foco()
    assert janela.estado_desktop == 'compact'
    assert not janela._recolher_foco_timer.isActive()
    assert enviadas == []


def test_perda_de_foco_nao_interrompe_animacao_de_expansao(conversa_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation, QEvent
    from PySide6.QtWidgets import QApplication

    janela, _ponte, entradas, js, aguardar = conversa_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    js("LaylayInterface.goMode('desktop');LaylayInterface.state.preferences.reduced=false")
    aguardar(lambda: janela.modo_apresentacao == 'desktop' and janela._desktop_fase == 'idle')
    janela.expandir_desktop(fixar=True)
    aguardar(lambda: janela._desktop_fase == 'resizing'
             and js("LaylayInterface.state.desktopPhase==='resizing'"))

    janela._foco_desktop_observado = True
    monkeypatch.setattr(janela, '_desktop_em_foco', lambda: False)
    QApplication.sendEvent(janela, QEvent(QEvent.WindowDeactivate))
    assert janela._recolher_foco_timer.isActive()
    janela._recolher_foco_timer.timeout.emit()

    assert janela.estado_desktop == 'expanded'
    assert janela._desktop_fase == 'resizing'
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    assert entradas == []


def test_ativacao_e_desativacao_armam_recolhimento_de_foco(interface_web):
    from PySide6.QtCore import QEvent
    from PySide6.QtWidgets import QApplication

    _app, _worker, janela, enviadas, _eventos = interface_web
    janela.show()
    janela.apresentar('desktop')
    janela.expandir_desktop(fixar=True)
    QApplication.sendEvent(janela, QEvent(QEvent.WindowActivate))
    assert janela._foco_desktop_observado
    QApplication.sendEvent(janela, QEvent(QEvent.WindowDeactivate))
    assert janela._recolher_foco_timer.isActive()
    QApplication.sendEvent(janela, QEvent(QEvent.WindowActivate))
    assert not janela._recolher_foco_timer.isActive()
    assert janela.estado_desktop == 'expanded'
    assert enviadas == []


def test_streaming_viewport_invalido_ou_atrasado_nao_sobrepoe_outra_aba(interface_web):
    _app, _worker, janela, enviadas, _eventos = interface_web
    janela.show()
    janela.apresentar("desktop")
    janela.selecionar_pagina_desktop("streaming")
    janela.abrir_streaming()
    for dados in ({}, [], {"x":0,"y":90,"width":float("nan"),"height":200},
                  {"x":0,"y":90,"width":400,"height":float("inf")},
                  {"x":900000,"y":900000,"width":400,"height":200}):
        janela.ponte_web.viewport_streaming(json.dumps(dados))
        assert not janela._streaming_pagina.isVisible(), "Viewport sem área válida deve ocultar player"
    janela.selecionar_pagina_desktop("chat")
    janela.ponte_web.viewport_streaming('{"x":10,"y":90,"width":400,"height":350}')
    assert not janela._streaming_pagina.isVisible(), "Callback antigo do Streaming não pode cobrir o chat"
    assert janela._streaming_pagina.captura.estado == "parado"
    assert enviadas == []


def test_cursor_imovel_e_resize_nao_renovam_prazo_mas_movimento_real_dentro_sim(interface_web, monkeypatch):
    from PySide6.QtGui import QCursor
    from PySide6.QtCore import QPoint
    from PySide6.QtTest import QTest

    _app, _worker, janela, enviadas, _eventos = interface_web
    janela.show()
    janela.apresentar("desktop")
    janela.expandir_desktop(fixar=True)
    ponto = [janela.mapToGlobal(janela.rect().center())]
    monkeypatch.setattr(QCursor, "pos", lambda: ponto[0])
    janela._observar_cursor_desktop()
    QTest.qWait(100)
    timer = janela._inatividade_desktop_timer
    restante = timer.remainingTime()
    janela.resize(janela.width()-2, janela.height()-2)
    janela._observar_cursor_desktop()
    assert timer.remainingTime() <= restante+5, "Resize sob cursor parado não é interação"
    ponto[0] += QPoint(3, 0)
    janela._observar_cursor_desktop()
    assert timer.remainingTime() > restante, "Movimento real dentro da ilha precisa renovar20s"
    QTest.qWait(100)
    restante = timer.remainingTime()
    ponto[0] = QPoint(-10000, -10000)
    janela._observar_cursor_desktop()
    assert timer.remainingTime() <= restante+5, "Mover fora da ilha não renova prazo"
    assert enviadas == []


def test_confirmacao_visual_antiga_nao_conclui_transicao_nova(interface_web, monkeypatch):
    from PySide6.QtTest import QTest

    app, _worker, janela, enviadas, _eventos = interface_web
    janela.show()
    janela.apresentar('desktop')
    QTest.qWait(80)
    janela.ponte_web.pronto()
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    janela.selecionar_pagina_desktop('music')
    antiga = janela.apresentacao_publica()['desktop_transition']
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration()//2)
    janela.ponte_web.gesto_desktop('resumo')
    nova = janela.apresentacao_publica()['desktop_transition']
    assert nova > antiga
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    app.processEvents()
    assert janela.apresentacao_publica()['desktop_phase'] == 'committing'
    janela.ponte_web.transicao_pronta(antiga, janela.web.width(), janela.web.height())
    assert janela.apresentacao_publica()['desktop_phase'] == 'committing'
    janela.ponte_web.transicao_pronta(nova, 1, 1)
    assert janela.apresentacao_publica()['desktop_phase'] == 'committing'
    janela.ponte_web.transicao_pronta(nova, janela.web.width(), janela.web.height())
    assert janela.apresentacao_publica()['desktop_phase'] == 'idle'
    janela.ponte_web.transicao_pronta(antiga, janela.web.width(), janela.web.height())
    assert janela.apresentacao_publica()['desktop_transition'] == nova
    assert enviadas == []


@pytest.mark.parametrize('largura', [360, 390])
def test_controles_streaming_integrados_cabem_no_viewport_estreito(interface_web, largura):
    from PySide6.QtWidgets import QScrollArea
    from PySide6.QtTest import QTest
    from cliente.terminal_2.streaming import PaginaStreaming

    _app, _worker, _janela, enviadas, _eventos = interface_web
    host = QScrollArea()
    host.setWidgetResizable(True)
    host.resize(largura, 540)
    pagina = PaginaStreaming(host, expandir_no_host=lambda _: None)
    host.setWidget(pagina)
    try:
        host.show()
        QTest.qWait(100)
        assert host.horizontalScrollBar().maximum() == 0, "O hint mínimo não pode impedir o layout estreito"
        assert pagina.width() <= host.viewport().width()
        for controle in (pagina.janelas, pagina.transmitir, pagina.parar):
            assert controle.geometry().left() >= 0 and controle.geometry().right() < pagina.width()
        host.resize(900, 600)
        QTest.qWait(100)
        assert host.horizontalScrollBar().maximum() == 0
        assert pagina.width() <= host.viewport().width()
        assert enviadas == []
    finally:
        pagina.fechar()
        host.close()


def test_desktop_expande_recolhe_e_restaura_mesma_superficie_sem_enviar_comandos(interface_web):
    from PySide6.QtCore import QRect, Qt
    from PySide6.QtTest import QTest

    app, worker, janela, enviadas, eventos = interface_web
    # O monitor offscreen mede800×800; a posição original precisa caber nele.
    janela.resize(700, 700)
    janela.move(20, 20)
    janela.show()
    app.processEvents()
    original = QRect(janela.geometry())
    identidades = (janela.web, janela.pagina_web, janela.canal, janela.ponte_web, janela.controlador)
    janela.ponte_web.pronto()
    janela.apresentar("desktop")
    app.processEvents()
    assert janela.modo_apresentacao == "desktop", "Falta a apresentação desktop no owner nativo"
    assert janela.estado_desktop == "compact"
    assert janela.windowFlags() & Qt.FramelessWindowHint
    assert janela.windowFlags() & Qt.WindowStaysOnTopHint
    compacta = QRect(janela.geometry())
    assert compacta.height() == 36
    assert compacta.width() <= 330 and compacta.height() <= 90
    janela.expandir_desktop(fixar=True)
    QTest.qWait(30)  # Fixture reduz movimento: geometria final deve ser imediata.
    assert janela.estado_desktop == "expanded" and janela.desktop_fixado
    assert janela.apresentacao_publica()["desktop_state"] == "expanded"
    assert janela.width() > compacta.width() and janela.height() > compacta.height()
    assert abs(janela.geometry().center().x() - compacta.center().x()) <= 1
    assert janela.geometry().top() == compacta.top()
    assert janela.screen().availableGeometry().contains(janela.geometry())
    janela.recolher_desktop()
    app.processEvents()
    assert janela.estado_desktop == "compact"
    assert janela.geometry() == compacta
    janela.apresentar("full")
    app.processEvents()
    assert janela.geometry() == original
    assert identidades == (janela.web, janela.pagina_web, janela.canal, janela.ponte_web, janela.controlador)
    assert janela.controlador.worker is worker
    assert enviadas == [], "Apresentação desktop não autoriza nenhuma ação"
    assert any(e.get("desktop_state") == "expanded" for e in eventos)
    assert janela.ponte_web._ultimos['apresentacao'][1]['mode'] == 'full', "Replay deve projetar a apresentação mais recente"


def test_pedido_pendente_e_emocao_recebida_sobrevivem_a_recolhimento_e_reabertura(interface_web):
    _app, worker, janela, enviadas, _eventos = interface_web
    worker.conectado.emit(True)
    janela.ponte_web.pronto()
    worker.mensagem.emit({"type": "state", "activity": "thinking", "emotion": "curiosa", "emotion_level": 2})
    pedido = janela.ponte_web.solicitar("texto", '{"text":"Continua me explicando a ideia"}')
    assert pedido in janela.ponte_web._pendentes
    antes = list(enviadas)
    janela.apresentar("desktop")
    assert janela.modo_apresentacao == "desktop"
    janela.expandir_desktop()
    janela.recolher_desktop()
    assert pedido in janela.ponte_web._pendentes
    worker.mensagem.emit({"type": "input_ack", "id": pedido, "accepted": True})
    assert pedido in janela.ponte_web._pendentes, "Recebimento não confirma conclusão"
    worker.mensagem.emit({"type": "assistant_message", "id": pedido, "text": "Resposta realmente recebida.", "emotion": "alegre", "emotion_level": 3})
    assert pedido not in janela.ponte_web._pendentes
    janela.expandir_desktop()
    assert janela.ponte_web._retrato_atual()["messages"][-1]["text"] == "Resposta realmente recebida."
    assert enviadas == antes


@pytest.mark.parametrize("tela", [(-1920, -40, 1920, 1080), (0, 0, 390, 680), (20, 80, 160, 90)])
def test_geometria_desktop_respeita_origem_tela_pequena_e_ancora(tela):
    from PySide6.QtCore import QRect
    from cliente.terminal_2.apresentacao_desktop import geometria_desktop

    disponivel = QRect(*tela)
    compacta = geometria_desktop(disponivel, expandida=False)
    expandida = geometria_desktop(disponivel, expandida=True)
    for geometria in (compacta, expandida):
        assert disponivel.contains(geometria)
        assert geometria.top() == disponivel.top()
        assert abs(geometria.center().x() - disponivel.center().x()) <= 1
    assert expandida.width() >= compacta.width()
    assert expandida.height() >= compacta.height()


def test_animacao_desktop_inverte_do_ponto_atual_e_reduced_aplica_destino(interface_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QRect
    from cliente.terminal_2.apresentacao_desktop import geometria_desktop

    app, _worker, janela, enviadas, _eventos = interface_web
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "0")
    janela.show()
    app.processEvents()
    janela.apresentar("desktop")
    janela.expandir_desktop()
    animacao = janela._animacao_desktop
    assert animacao.state() == QAbstractAnimation.Running
    assert animacao.duration() == 480
    assert animacao.easingCurve().type() == QEasingCurve.BezierSpline
    assert 0 < animacao.easingCurve().valueForProgress(.1) < .2
    duracao_abertura = animacao.duration()
    area = janela.screen().availableGeometry()
    for percentual in (10, 35, 60, 90):
        animacao.setCurrentTime(duracao_abertura * percentual // 100)
        assert area.contains(janela.geometry()), 'A expansão deve caber na área útil em todo quadro'
    animacao.setCurrentTime(animacao.duration() // 2)
    intermediaria = QRect(janela.geometry())
    janela.recolher_desktop()
    assert janela._animacao_desktop is animacao
    assert animacao.startValue() == intermediaria
    assert animacao.duration() == 360
    assert animacao.easingCurve().type() == QEasingCurve.InCubic
    assert 0 < animacao.duration() < duracao_abertura, 'Recolher deve ser mais rápido que expandir'
    janela.apresentar("full")
    assert animacao.state() == QAbstractAnimation.Stopped
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "1")
    janela.apresentar("desktop")
    janela.expandir_desktop()
    assert animacao.state() == QAbstractAnimation.Stopped
    assert janela.geometry() == geometria_desktop(janela.screen().availableGeometry(), expandida=True)
    assert enviadas == []


def test_shell_desktop_integrado_mantem_notch_superficies_e_controles(conversa_web):
    janela, _ponte, entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == 'desktop')
    aguardar(lambda: js("!!document.querySelector('.desktop-island')"))
    js("""(()=>{
      window.__desktopShell=document.querySelector('.desktop-island');
      window.__desktopControls=[...document.querySelectorAll(
        '.desktop-compact,.desktop-expanded,.desktop-tabs,.desktop-overview,.desktop-page,'+
        '[id],[data-action],[data-desktop],[data-page],[data-voice],[data-composer]'
      )].map(node=>node.tagName+':'+node.className+':'+
        ['id','data-action','data-desktop','data-page','data-voice','data-composer']
          .map(name=>node.getAttribute(name)||'').join('|'));
    })()""")

    janela.expandir_desktop(fixar=True)
    aguardar(lambda: janela.estado_desktop == 'expanded' and janela._desktop_fase == 'idle')
    visual = json.loads(js("""JSON.stringify((()=>{
      const shell=document.querySelector('.desktop-island');
      const notch=getComputedStyle(shell,'::before');
      const presence=getComputedStyle(shell.querySelector('.desktop-presence'));
      const context=getComputedStyle(shell.querySelector('.desktop-context'));
      const page=getComputedStyle(shell.querySelector('.desktop-page'));
      const compactCursor=getComputedStyle(shell.querySelector('.desktop-compact')).cursor;
      const toolbarCursor=getComputedStyle(shell.querySelector('.desktop-toolbar')).cursor;
      return {
          sameShell:shell===window.__desktopShell,
          noDragAffordance:document.querySelector('[data-desktop-drag]')===null,
          clickAffordance:compactCursor==='pointer'&&toolbarCursor==='default',
          notch:notch.content!=='none'&&notch.width==='136px'&&notch.height==='7px',
        surfaces:[presence,context].every(style=>
          style.backgroundColor==='rgba(0, 0, 0, 0)'&&style.borderWidth==='0px'),
        pageSurface:page.backgroundColor==='rgba(0, 0, 0, 0)',
        controls:window.__desktopControls.join('\\n')===[...document.querySelectorAll(
          '.desktop-compact,.desktop-expanded,.desktop-tabs,.desktop-overview,.desktop-page,'+
          '[id],[data-action],[data-desktop],[data-page],[data-voice],[data-composer]'
        )].map(node=>node.tagName+':'+node.className+':'+
          ['id','data-action','data-desktop','data-page','data-voice','data-composer']
            .map(name=>node.getAttribute(name)||'').join('|')).join('\\n')
      };
    })())"""))
    assert visual == {
        "sameShell": True, "noDragAffordance": True, "clickAffordance": True,
        "notch": True, "surfaces": True,
        "pageSurface": True, "controls": True,
    }, visual

    janela.recolher_desktop()
    aguardar(lambda: janela.estado_desktop == 'compact' and janela._desktop_fase == 'idle')
    assert js("document.querySelector('.desktop-island')===window.__desktopShell")
    assert entradas == []


def test_ilha_compacta_preserva_36px_e_perfil_suave_nas_pontas(conversa_web):
    import os
    from PySide6.QtTest import QTest
    from PySide6.QtCore import QPoint
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1

    janela, _ponte, _entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == "desktop")
    aguardar(lambda: janela.estado_desktop == "compact")
    aguardar(lambda: js("""(()=>{
      const shell=document.querySelector('.desktop-island');
      return shell&&getComputedStyle(shell).maskImage!=='none'&&
        shell.getBoundingClientRect().width===window.innerWidth;
    })()"""))

    silhueta = json.loads(js("""JSON.stringify((()=>{
      const shell=document.querySelector('.desktop-island');
      const compact=shell.querySelector('.desktop-compact');
      const shellStyle=getComputedStyle(shell);
      const rect=node=>{
        const r=node.getBoundingClientRect();
        return {x:r.x,y:r.y,width:r.width,height:r.height};
      };
      return {
        shellHeight:shell.getBoundingClientRect().height,
        shellWidth:shell.getBoundingClientRect().width,
        shellMask:shellStyle.maskImage,
        maskVariable:shell.style.getPropertyValue('--desktop-island-mask-image'),
        shellMaskSize:shellStyle.maskSize,
        contentRects:Object.fromEntries(['.desktop-miniature','.desktop-compact-copy',
          '.desktop-signal','.desktop-expand-icon'].map(selector=>[
            selector,rect(shell.querySelector(selector))
          ]))
      };
    })())"""))

    assert janela.geometry().height() == 36
    assert silhueta["shellWidth"] == janela.geometry().width()
    mascara_css = janela.apresentacao_publica()["desktop_mask"]
    assert silhueta == {
        "shellHeight": 36,
        "shellWidth": janela.geometry().width(),
        "shellMask": f'url("{mascara_css}")',
        "maskVariable": f'url("{mascara_css}")',
        "shellMaskSize": "100% 100%",
        "contentRects": silhueta["contentRects"],
    }, silhueta
    mascara_nativa = JanelaInterfaceWebV1._regiao_desktop(272, 36, compacta=True)
    escala_x = 272 / silhueta["shellWidth"]
    escala_y = 36 / silhueta["shellHeight"]
    for retangulo in silhueta["contentRects"].values():
        esquerda = round(retangulo["x"] * escala_x)
        direita = round((retangulo["x"] + retangulo["width"] - 1) * escala_x)
        topo = round(retangulo["y"] * escala_y)
        base = round((retangulo["y"] + retangulo["height"] - 1) * escala_y)
        for x, y in ((esquerda, topo), (direita, topo), (esquerda, base), (direita, base)):
            assert mascara_nativa.contains(QPoint(x, y)), (
                "Conteúdo compacto deve permanecer inteiramente dentro da máscara nativa",
                retangulo, (x, y),
            )
    capture = os.environ.get("LAYLAY_COCOU_CURVE_CAPTURE")
    if capture:
        QTest.qWait(180)
        assert janela.grab().save(capture), f"Não foi possível salvar a captura runtime em {capture}"


def test_hierarquia_da_ilha_compacta_prioriza_nome_e_status_legivel(conversa_web):
    janela, _ponte, _entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == "desktop")
    aguardar(lambda: janela.estado_desktop == "compact")

    visual = json.loads(js("""JSON.stringify((()=>{
      const compact=document.querySelector('.desktop-island .desktop-compact');
      const nome=compact.querySelector('.desktop-compact-copy strong');
      const status=compact.querySelector('.desktop-compact-copy small');
      const nomeStyle=getComputedStyle(nome);
      const statusStyle=getComputedStyle(status);
      return {
        tag:compact.tagName,
        label:compact.getAttribute('aria-label'),
        ordem:[...compact.children].map(element=>element.classList[0]),
        direcao:getComputedStyle(compact.querySelector('.desktop-compact-copy')).flexDirection,
        nomeTamanho:parseFloat(nomeStyle.fontSize),
        statusTamanho:parseFloat(statusStyle.fontSize),
        linhas:parseFloat(nomeStyle.lineHeight)+parseFloat(statusStyle.lineHeight),
        statusReticencias:statusStyle.textOverflow==='ellipsis'&&statusStyle.whiteSpace==='nowrap'
      };
    })())"""))

    assert visual["tag"] == "BUTTON"
    assert visual["label"].startswith("Expandir Laylay")
    assert visual["ordem"] == [
        "desktop-miniature", "desktop-compact-copy", "desktop-signal",
        "desktop-expand-icon",
    ]
    assert visual["direcao"] == "column"
    assert visual["nomeTamanho"] >= 10.5
    assert visual["statusTamanho"] >= 8.5
    assert visual["nomeTamanho"] > visual["statusTamanho"]
    assert visual["linhas"] <= 28
    assert visual["statusReticencias"]


def test_rascunho_e_resposta_recebida_na_ilha_permanecem_no_painel_real(conversa_web):
    janela, ponte, entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == "desktop")
    identidades = (janela.web, janela.pagina_web, janela.canal, janela.controlador)
    janela.expandir_desktop(fixar=True)
    aguardar(lambda: js("LaylayInterface.state.desktopState==='expanded'"))
    js("(()=>{const campo=document.getElementById('composer-input');campo.value='Um rascunho ainda não enviado';campo.dispatchEvent(new Event('input',{bubbles:true}))})()")
    assert js("LaylayInterface.state.draft") == "Um rascunho ainda não enviado"
    janela.recolher_desktop()
    assert ponte.publicar_fala_final("Cheguei enquanto a janela estava pequena.", "alegre", 2)
    aguardar(lambda: js("LaylayInterface.state.messages.some(m=>m.text==='Cheguei enquanto a janela estava pequena.')"))
    janela.expandir_desktop(fixar=True)
    aguardar(lambda: js("document.getElementById('composer-input').value==='Um rascunho ainda não enviado'"))
    assert js("document.querySelector('.desktop-island').textContent.includes('Cheguei enquanto a janela estava pequena.')")
    assert identidades == (janela.web, janela.pagina_web, janela.canal, janela.controlador)
    assert entradas == [], "Rascunho e gestos da ilha não podem virar comandos"
    js("document.querySelector('[data-composer]').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))")
    aguardar(lambda: entradas == ["Um rascunho ainda não enviado"])
    aguardar(lambda: js("Object.values(LaylayInterface.state.pending).some(p=>p.state==='accepted')"))
    assert not js("LaylayInterface.state.messages.some(m=>m.role==='assistant'&&m.text==='Um rascunho ainda não enviado')")
    janela.worker.conectado.emit(False)
    aguardar(lambda: js("LaylayInterface.state.connected===false"))
    js("LaylayInterface.state.draft='Pedido sem conexão';document.querySelector('[data-composer]').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))")
    assert entradas == ["Um rascunho ainda não enviado"], "Desconectado deve falhar fechado"


def test_gestos_desconhecidos_pin_e_encerramento_nao_executam_efeitos(interface_web):
    app, _worker, janela, enviadas, _eventos = interface_web
    janela.apresentar("desktop")
    antes = janela.apresentacao_publica()
    janela.ponte_web.gesto_desktop("apaga tudo")
    assert janela.apresentacao_publica() == antes
    janela.expandir_desktop(fixar=True)
    janela._desktop_dentro = False
    janela._recolher_desktop_transitorio()
    assert janela.estado_desktop == "expanded"
    janela.desktop_fixado = False
    janela._desktop_transitorio = True
    janela.ponte_web.edicao_desktop(True)
    janela._recolher_desktop_transitorio()
    assert janela.estado_desktop == "expanded", "Edição não pode ser interrompida por saída do mouse"
    janela.ponte_web.edicao_desktop(False)
    janela._recolher_desktop_transitorio()
    assert janela.estado_desktop == "compact"
    janela.close()
    app.processEvents()
    assert not janela._cursor_desktop_timer.isActive()
    assert not janela._recolher_desktop_timer.isActive()
    assert enviadas == []


def test_abas_abrem_dentro_da_ilha_sem_mudar_hwnd_canal_ou_ancora(conversa_web):
    from PySide6.QtCore import QRect, Qt

    janela, _ponte, entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == "desktop")
    janela.expandir_desktop(fixar=True)
    aguardar(lambda: js("LaylayInterface.state.desktopState==='expanded'"))
    hwnd = int(janela.winId())
    identidades = (janela.web, janela.pagina_web, janela.canal, janela.controlador, janela.worker)
    ancoragem = QRect(janela.geometry())
    for pagina in ("home", "chat", "music", "system", "settings", "memory", "lamp", "dev", "streaming"):
        js("LaylayInterface.goPage('" + pagina + "')")
        aguardar(lambda: js("LaylayInterface.state.page==='" + pagina + "'"))
        assert js("LaylayInterface.state.mode") == "desktop", "Navegar na ilha não deve restaurar a janela comum"
        assert janela.modo_apresentacao == "desktop"
        assert int(janela.winId()) == hwnd
        assert identidades == (janela.web, janela.pagina_web, janela.canal, janela.controlador, janela.worker)
        assert janela.windowFlags() & Qt.FramelessWindowHint
        assert janela.geometry().top() == ancoragem.top()
        assert abs(janela.geometry().center().x() - ancoragem.center().x()) <= 1
        assert js("!!document.querySelector('.desktop-island #page-content')")
    assert entradas == [], "Abrir uma aba não deve enviar uma fala nem executar ação"


def test_conversas_reabrem_na_mesma_ilha_e_links_preservam_rascunho(conversa_web):
    janela, ponte, entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == "desktop")
    janela.expandir_desktop(fixar=True)
    js("LaylayInterface.goPage('music');LaylayInterface.state.draft='Um rascunho entre abas'")
    for acao in ("create", "select", "delete"):
        assert ponte._publicar({"type": "conversations_state", "action": acao, "success": True,
            "conversations": {"active_id": "11111111111111111111111111111111", "items": [], "messages": []}})
        aguardar(lambda: js("LaylayInterface.state.page==='chat'"))
        assert js("LaylayInterface.state.mode") == "desktop"
        assert janela.modo_apresentacao == "desktop"
        assert js("document.getElementById('composer-input').value") == "Um rascunho entre abas"
        js("LaylayInterface.goPage('music')")
    assert entradas == []


def test_rolagem_da_conversa_desktop_sobrevive_a_troca_de_aba(paginas_reais):
    js, aguardar, _entradas = paginas_reais
    js("LaylayInterface.goMode('desktop');LaylayInterface.goPage('chat')")
    mensagens = [{"id": str(i), "role": "assistant", "text": "Uma mensagem anterior do histórico. " * 12} for i in range(24)]
    js("LaylayInterface.receiveEvent(" + json.dumps({"type": "snapshot", "messages": mensagens}) + ")")
    aguardar(lambda: js("document.querySelectorAll('.message').length===24"))
    js("document.getElementById('chat-history').scrollTop=40;window.rolagemGuardada=document.getElementById('chat-history').scrollTop")
    assert js("rolagemGuardada") == 40
    js("LaylayInterface.goPage('music');LaylayInterface.goPage('chat')")
    aguardar(lambda: js("document.querySelectorAll('.message').length===24"))
    assert js("document.getElementById('chat-history').scrollTop") == 40


def test_paginas_animam_na_mesma_ancora_e_resumo_recolhe_sem_trocar_hwnd(interface_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation, QRect
    from cliente.terminal_2.apresentacao_desktop import geometria_desktop

    app, _worker, janela, enviadas, _eventos = interface_web
    janela.show()
    app.processEvents()
    janela.apresentar("desktop")
    hwnd = int(janela.winId())
    janela.selecionar_pagina_desktop("music")
    assert janela.desktop_pagina == "music"
    assert janela.geometry() == geometria_desktop(janela.screen().availableGeometry(), expandida=True, pagina="music")
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "0")
    janela.ponte_web.gesto_desktop('resumo')
    animacao = janela._animacao_desktop
    assert animacao.state() == QAbstractAnimation.Running
    animacao.setCurrentTime(animacao.duration() // 2)
    intermediaria = QRect(janela.geometry())
    janela.selecionar_pagina_desktop("dev")
    assert janela._animacao_desktop is animacao and animacao.startValue() == intermediaria
    janela.ponte_web.gesto_desktop("resumo")
    assert janela.desktop_pagina is None
    assert animacao.endValue() == geometria_desktop(janela.screen().availableGeometry(), expandida=True)
    janela.recolher_desktop()
    assert animacao.endValue() == geometria_desktop(janela.screen().availableGeometry())
    assert int(janela.winId()) == hwnd
    assert enviadas == []


@pytest.mark.parametrize("pagina", ["home", "chat", "lamp", "music", "streaming", "memory", "system", "dev", "settings"])
def test_geometria_de_cada_aba_cabe_em_tela_estreita_e_monitor_negativo(pagina):
    from PySide6.QtCore import QRect
    from cliente.terminal_2.apresentacao_desktop import geometria_desktop

    for tela in (QRect(-1920, -40, 1920, 1080), QRect(0, 0, 390, 680)):
        destino = geometria_desktop(tela, expandida=True, pagina=pagina)
        assert tela.contains(destino)
        assert destino.top() == tela.top()
        assert abs(destino.center().x() - tela.center().x()) <= 1


@pytest.mark.parametrize("iniciar_desktop", [True, False])
def test_entrypoint_oficial_respeita_preferencia_com_ponte_real(tmp_path, iniciar_desktop):
    import os
    import subprocess
    import sys

    codigo = r'''
import os, sys
from pathlib import Path
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication
from mente_laylay.integracao.desktop_bridge import DesktopBridgeRuntime
from cliente import terminal_laylay_2 as terminal
from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1
resultado = {"verificado":False}
preferencias = QSettings(os.environ['LAYLAY_TEST_DESKTOP_INI'], QSettings.IniFormat)
preferencias.setValue('v1/iniciar_no_desktop', os.environ['LAYLAY_TEST_DESKTOP_START']=='1')
terminal.QSettings = lambda *_: preferencias
class AplicacaoInspecionada(QApplication):
    def __init__(self, argumentos):
        super().__init__(argumentos)
        QTimer.singleShot(3000, self.verificar)
        QTimer.singleShot(7000, self.resgatar)
    def resgatar(self):
        resultado['precisou_quit_forcado']=True
        self.quit()
    def verificar(self):
        try:
            janelas = [j for j in self.topLevelWidgets() if isinstance(j, JanelaInterfaceWebV1)]
            assert len(janelas)==1
            janela=janelas[0]
            assert janela.modo_apresentacao==os.environ['LAYLAY_TEST_DESKTOP_MODO']
            assert janela.controlador._conectado
            assert janela.controlador.worker is janela.worker
            assert not janela._entrada_pendente, 'Entrada oficial deve confirmar o renderer antes do timeout'
            assert janela.windowOpacity()==1
            assert janela._erro_entrada is None
            resultado['verificado']=True
            janela.close()
        except BaseException as erro:
            resultado['erro']=repr(erro)
            self.quit()
terminal.QApplication=AplicacaoInspecionada
ponte=DesktopBridgeRuntime(enviar_entrada=lambda _:None, historico_getter=lambda:[], estado_getter=lambda:{'activity':'idle'}, log=lambda _:None)
ponte.iniciar()
os.environ.update(LAYLAY_DESKTOP_HOST=ponte.endereco[0],LAYLAY_DESKTOP_PORT=str(ponte.endereco[1]),LAYLAY_DESKTOP_TOKEN=ponte.token,LAYLAY_DESKTOP_SESSION=ponte.session_id,LAYLAY_PARENT_PID='0')
sys.argv=['terminal_laylay_2.py']
try:
    assert terminal.main()==0
    assert resultado['verificado'], resultado
    assert not resultado.get('precisou_quit_forcado'), resultado
finally:
    ponte.parar()
print('ENTRYPOINT_DESKTOP_OK')
'''
    ambiente = dict(os.environ, QT_QPA_PLATFORM="offscreen", QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --no-sandbox",
        LAYLAY_TEST_DESKTOP_INI=str(tmp_path / "entrada.ini"), LAYLAY_TEST_DESKTOP_START="1" if iniciar_desktop else "0",
        LAYLAY_TEST_DESKTOP_MODO="desktop" if iniciar_desktop else "full")
    resultado = subprocess.run([sys.executable, "-c", codigo], cwd=Path(__file__).parents[2], env=ambiente,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "ENTRYPOINT_DESKTOP_OK" in resultado.stdout


def test_material_fluent_fica_na_mesma_ilha_e_respeita_estados_reais(conversa_web):
    janela, _ponte, entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == 'desktop')
    aguardar(lambda: js("!!document.querySelector('.desktop-island .desktop-compact-copy')"))
    material = janela.apresentacao_publica()['desktop_material']
    assert material in {'acrylic', 'mica', 'fallback'}
    aguardar(lambda: js("document.querySelector('.desktop-island')?.dataset.desktopMaterial") == material)
    assert js("document.querySelector('.desktop-compact .desktop-expand-icon svg')!==null")
    assert js("document.querySelector('.desktop-compact .desktop-miniature .avatar')!==null")
    assert js("document.querySelector('.desktop-compact').getAttribute('aria-label').includes('Laylay')")
    assert js("getComputedStyle(document.querySelector('.desktop-compact-copy')).flexDirection==='column'")
    assert js("getComputedStyle(document.querySelector('.desktop-island')).maskImage!=='none'")
    assert js("document.querySelector('.desktop-island').style.getPropertyValue('--desktop-island-mask-image').startsWith('url(\"data:image/svg+xml,')")
    assert js("(()=>{const e=document.querySelector('.desktop-island');return e.scrollWidth<=e.clientWidth+1})()")
    import os
    if os.environ.get('LAYLAY_FLUENT_CAPTURE') == '1':
        from pathlib import Path
        path = Path(os.environ['TEMP']) / 'laylay_fluent_test_20261023.png'
        assert janela.grab().save(str(path))
    handle=int(janela.winId())
    js("LaylayInterface.receiveEvent({type:'state',activity:'speaking',activity_label:'Falando'})")
    aguardar(lambda: js("document.querySelector('.desktop-island')?.dataset.activity==='speaking'"))
    assert js("document.querySelector('.desktop-compact-copy small').textContent.includes('Falando')")
    janela.expandir_desktop(fixar=True)
    assert int(janela.winId()) == handle
    janela.recolher_desktop()
    assert int(janela.winId()) == handle
    assert entradas == []

def test_painel_expandido_tem_canvas_opaco_sem_pontos_transparentes(interface_web):
    """Isola o compositor do desktop enquanto a janela maior está visível."""
    from PySide6.QtTest import QTest

    app, _worker, janela, enviados, _eventos = interface_web
    janela.show()
    janela.apresentar('desktop')
    assert janela.estado_desktop == 'compact'
    assert janela.pagina_web.backgroundColor().alpha() == 0
    assert janela._fundo_desktop_opaco is False
    hwnd = int(janela.winId())
    for pagina in ('home', 'music', 'system', 'chat'):
        janela.selecionar_pagina_desktop(pagina)
        assert janela.estado_desktop == 'expanded'
        assert janela._fundo_desktop_opaco is True
        assert janela.pagina_web.backgroundColor().alpha() == 255
        assert janela.pagina_web.backgroundColor().name() == '#0b0c10'
        app.processEvents()
        QTest.qWait(30)
        assert int(janela.winId()) == hwnd
        assert janela._fundo_desktop_opaco is True

    janela.recolher_desktop()
    assert janela.estado_desktop == 'compact'
    # A camada opaca fica até o último frame do encolhimento ser confirmado.
    assert janela.pagina_web.backgroundColor().alpha() == 255
    assert janela._desktop_fase == 'committing'
    janela.confirmar_transicao_desktop(janela._desktop_sequencia, janela.web.width(), janela.web.height())
    assert janela.pagina_web.backgroundColor().alpha() == 0
    assert janela._fundo_desktop_opaco is False
    assert int(janela.winId()) == hwnd
    assert enviados == []


def test_ao_sair_do_desktop_canvas_transparente_e_ponte_sao_preservados(interface_web):
    app, worker, janela, enviados, _eventos = interface_web
    janela.show()
    janela.apresentar('desktop')
    janela.expandir_desktop(fixar=True)
    assert janela.pagina_web.backgroundColor().alpha() == 255
    html_page, canal, web = janela.pagina_web, janela.canal, janela.web
    janela.apresentar('full')
    app.processEvents()
    assert janela.pagina_web.backgroundColor().alpha() == 0
    assert not janela._fundo_desktop_opaco
    assert (janela.pagina_web, janela.canal, janela.web)==(html_page, canal, web)
    assert enviados == []


def test_m2_entrada_expansao_abas_e_recolhimento_preservam_hwnd_e_glitch_guard(conversa_web):
    from PySide6.QtCore import QAbstractAnimation
    from PySide6.QtTest import QTest
    janela, _ponte, entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == 'desktop')
    js("LaylayInterface.state.preferences.reduced=false")
    hwnd = int(janela.winId())
    assert janela._animacao_entrada.state() == QAbstractAnimation.Stopped
    assert janela.estado_desktop == 'compact'
    assert janela.pagina_web.backgroundColor().alpha() == 0
    import os
    from pathlib import Path
    if os.environ.get('LAYLAY_M2_CAPTURE') == '1':
        aguardar(lambda: js("document.querySelector('.desktop-island')?.dataset.desktopState==='compact'"))
        QTest.qWait(60)
        assert janela.grab().save(str(Path(os.environ['TEMP']) / 'laylay_motion_m2_compact.png'))

    janela.expandir_desktop(fixar=True)
    aguardar(lambda: janela.estado_desktop == 'expanded' and janela._desktop_fase == 'idle')
    aguardar(lambda: js("LaylayInterface.motionStats().desktopState") == 'expanded')
    initial=js("LaylayInterface.motionStats().count")
    assert initial == 0, 'A expansão não deve animar conteúdo depois do ACK da geometria'
    assert janela.pagina_web.backgroundColor().alpha() == 255
    assert int(janela.winId()) == hwnd
    assert js("!!document.querySelector('.desktop-island .desktop-page-content')")
    if os.environ.get('LAYLAY_M2_CAPTURE') == '1':
        QTest.qWait(230)
        assert janela.grab().save(str(Path(os.environ['TEMP']) / 'laylay_motion_m2_expanded.png'))

    janela.selecionar_pagina_desktop('music')
    aguardar(lambda: janela._desktop_fase == 'idle' and js("LaylayInterface.state.page") == 'music')
    aguardar(lambda: js("LaylayInterface.motionStats().location") == 'desktop:page:music')
    second=js("LaylayInterface.motionStats().count")
    assert second == initial + 1
    assert js("document.querySelector('.desktop-island').getAttribute('data-desktop-state')==='expanded'")

    # Telemetria e redraws recorrentes não devem repetir o movimento.
    js("LaylayInterface.receiveEvent({type:'state',activity:'thinking',activity_label:'Pensando'})")
    QTest.qWait(60)
    assert js("LaylayInterface.motionStats().count") == second

    janela.selecionar_pagina_desktop('system')
    aguardar(lambda: janela._desktop_fase == 'idle' and js("LaylayInterface.motionStats().location") == 'desktop:page:system')
    assert js("LaylayInterface.motionStats().count") == second + 1
    assert int(janela.winId()) == hwnd
    assert janela.pagina_web.backgroundColor().alpha() == 255

    janela.recolher_desktop()
    aguardar(lambda: janela.estado_desktop == 'compact' and janela._desktop_fase == 'idle')
    aguardar(lambda: js("LaylayInterface.motionStats().desktopState") == 'compact')
    assert janela.pagina_web.backgroundColor().alpha() == 0
    assert int(janela.winId()) == hwnd
    assert entradas == []


def test_m2_pref_reduzido_impede_efeitos_de_apresentacao(conversa_web):
    janela, _ponte, entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == 'desktop')
    js("LaylayInterface.state.preferences.reduced=true")
    before=js("LaylayInterface.motionStats().count")
    janela.expandir_desktop(fixar=True)
    aguardar(lambda: janela.estado_desktop == 'expanded' and janela._desktop_fase == 'idle')
    janela.selecionar_pagina_desktop('music')
    aguardar(lambda: janela._desktop_fase == 'idle' and js("LaylayInterface.state.page") == 'music')
    assert js("LaylayInterface.motionStats().count") == before
    assert js("getComputedStyle(document.body).getPropertyValue('--none') !== 'garbage'")
    janela.recolher_desktop()
    aguardar(lambda: janela.estado_desktop == 'compact' and janela._desktop_fase == 'idle')
    assert js("LaylayInterface.motionStats().count") == before
    assert entradas == []


@pytest.mark.parametrize('visualizacao', ['overview', 'page'])
def test_entrada_do_resumo_e_coordenada_com_o_resize_qt(conversa_web, monkeypatch, visualizacao):
    import time
    from PySide6.QtCore import QAbstractAnimation

    janela, _ponte, entradas, js, aguardar = conversa_web
    acknowledgements = []
    confirmar = janela.confirmar_transicao_desktop

    def registrar_ack(sequencia, largura, altura):
        acknowledgements.append({
            'sequence': sequencia, 'size': [largura, altura],
            'phase': janela._desktop_fase,
            'web': [janela.web.width(), janela.web.height()],
            'animation_state': janela._animacao_desktop.state().name,
        })
        confirmar(sequencia, largura, altura)

    monkeypatch.setattr(janela, 'confirmar_transicao_desktop', registrar_ack)
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: js("LaylayInterface.state.desktopPhase==='idle'"))
    if visualizacao == 'page':
        janela.selecionar_pagina_desktop('home')
    else:
        janela.expandir_desktop(fixar=True)
    aguardar(lambda: js("document.body.classList.contains('desktop-resizing')"))
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    assert janela._transicao_cobertura is None
    from PySide6.QtTest import QTest
    QTest.qWait(70)
    janela._animacao_desktop.pause()
    tempo_intermediario = janela._animacao_desktop.currentTime()
    assert 0 < tempo_intermediario < janela._animacao_desktop.duration()
    aguardar(lambda: js(
        f"innerWidth==={janela.web.width()}&&innerHeight==={janela.web.height()}"))
    no_meio = json.loads(js(f"""JSON.stringify((()=>{{
      const seletores=['.desktop-toolbar','.desktop-overview','.desktop-page',
        '.desktop-portrait .avatar','.desktop-overview .desktop-presence-copy',
        '.desktop-wordmark','.desktop-page-content'];
      const superficies=seletores.map(seletor=>{{
        const elemento=document.querySelector(seletor);
        const estilo=getComputedStyle(elemento);
        for(const animation of elemento.getAnimations())
          if(animation.animationName?.startsWith('desktop-'))animation.currentTime={tempo_intermediario};
        return {{seletor,opacity:estilo.opacity,transform:estilo.transform,
          transition:estilo.transitionProperty,
          animations:elemento.getAnimations().map(animation=>({{
            name:animation.animationName||'',
            finite:Number.isFinite(animation.effect.getTiming().iterations),
            properties:[...new Set(animation.effect.getKeyframes().flatMap(frame=>Object.keys(frame)))]
              .filter(property=>['opacity','transform'].includes(property))
          }}))}};
      }});
      return {{phase:LaylayInterface.state.desktopPhase,
        viewport:[innerWidth,innerHeight],island:(()=>{{
          const r=document.querySelector('.desktop-island').getBoundingClientRect();
          return [r.left,r.top,r.width,r.height];
        }})(),superficies}};
    }})())"""))
    assert no_meio['viewport'] == [janela.web.width(), janela.web.height()], no_meio
    assert no_meio['island'] == [0, 0, janela.web.width(), janela.web.height()], no_meio
    efeitos_independentes = [
        (item['seletor'], animation)
        for item in no_meio['superficies']
        for animation in item['animations']
        if animation['properties'] and animation['finite']
    ]
    assert efeitos_independentes == [], no_meio
    assert all(item['opacity'] == '1' for item in no_meio['superficies']), no_meio
    assert all(item['transform'] == 'none' for item in no_meio['superficies']
               if item['seletor'] != '.desktop-portrait .avatar'), no_meio
    assert js("LaylayInterface.motionStats().count") == 0, 'Não deve iniciar uma segunda entrada após o ACK'

    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    aguardar(lambda: janela._desktop_fase == 'idle')
    aguardar(lambda: js("LaylayInterface.state.desktopPhase==='idle'"))
    depois_do_ack = json.loads(js("""JSON.stringify((()=>{
      const seletores=['.desktop-overview .desktop-presence-copy','.desktop-wordmark',
        '.desktop-page .context-bar','.desktop-page-content'];
      return seletores.map(seletor=>{
        const elemento=document.querySelector(seletor);
        return {seletor,opacity:getComputedStyle(elemento).opacity,
          transform:getComputedStyle(elemento).transform,
          animations:elemento.getAnimations().map(animation=>({
            name:animation.animationName||'',
            finite:Number.isFinite(animation.effect.getTiming().iterations),
            properties:[...new Set(animation.effect.getKeyframes().flatMap(frame=>Object.keys(frame)))]
              .filter(property=>['opacity','transform'].includes(property))
          }))};
      });
    })())"""))
    efeitos_apos_ack = [(item['seletor'], animation) for item in depois_do_ack
                       for animation in item['animations']
                       if animation['properties'] and animation['finite']]
    assert efeitos_apos_ack == [], depois_do_ack
    assert all(item['opacity'] == '1'
               for item in depois_do_ack), depois_do_ack

    janela.recolher_desktop()
    aguardar(lambda: janela._desktop_fase == 'resizing'
             and js("LaylayInterface.state.desktopPhase==='resizing'"))
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration() // 3)
    geometria_reversa = janela.geometry()
    janela.expandir_desktop(fixar=True)
    assert janela._desktop_fase == 'starting'
    assert janela._animacao_desktop.state() != QAbstractAnimation.Running
    aguardar(lambda: janela._desktop_fase == 'resizing'
             and js("LaylayInterface.state.desktopPhase==='resizing'"))
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    assert janela._animacao_desktop.startValue() == geometria_reversa
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration() // 2)
    janela._animacao_desktop.pause()
    assert janela._animacao_desktop.state() == QAbstractAnimation.Paused
    inicio_espera_viewport = time.monotonic()
    try:
        aguardar(lambda: json.loads(js("JSON.stringify([innerWidth,innerHeight])"))
                 == [janela.web.width(), janela.web.height()])
    except AssertionError as erro:
        animacao = janela._animacao_desktop
        amostras = []
        for _ in range(6):
            resultado = []
            janela.web.page().runJavaScript("""JSON.stringify((()=>({
              viewport:[innerWidth,innerHeight],
              phase:LaylayInterface.state.desktopPhase,
              state:LaylayInterface.state.desktopState,
              transition:LaylayInterface.state.desktopTransition,
              target:[LaylayInterface.state.desktopTargetWidth,LaylayInterface.state.desktopTargetHeight],
              documentVisible:document.visibilityState
            }))())""", resultado.append)
            limite_callback = time.monotonic() + .5
            while not resultado and time.monotonic() < limite_callback:
                QTest.qWait(10)
            browser = json.loads(resultado[0]) if resultado else {'js_callback': 'timeout'}
            janela_atual = janela.geometry()
            browser['qt'] = {
                'phase': janela._desktop_fase,
                'state': janela.estado_desktop,
                'sequence': janela._desktop_sequencia,
                'animation_state': animacao.state().name,
                'animation_time': animacao.currentTime(),
                'animation_duration': animacao.duration(),
                'window': [janela_atual.width(), janela_atual.height()],
                'web': [janela.web.width(), janela.web.height()],
                'target': [janela._desktop_destino.width(), janela._desktop_destino.height()],
                'acknowledgements': acknowledgements[-6:],
            }
            amostras.append(browser)
            QTest.qWait(20)
        amostra = {
            'wait_elapsed_s': time.monotonic() - inicio_espera_viewport,
            'samples': amostras,
        }
        amostra['predicate_after_failure'] = js(
            f"innerWidth==={janela.web.width()}&&innerHeight==={janela.web.height()}")
        pytest.fail(f"{erro}; viewport não convergiu após reversão: {amostra}")
    reversao = json.loads(js("""JSON.stringify((()=>{
      const seletores=['.desktop-toolbar','.desktop-overview','.desktop-page',
        '.desktop-portrait .avatar','.desktop-page-content'];
      return seletores.flatMap(seletor=>document.querySelector(seletor).getAnimations()
        .filter(animation=>Number.isFinite(animation.effect.getTiming().iterations))
        .map(animation=>({seletor,name:animation.animationName||'',
          properties:[...new Set(animation.effect.getKeyframes().flatMap(frame=>Object.keys(frame)))]
            .filter(property=>['opacity','transform'].includes(property))})));
    })())"""))
    assert reversao == [], reversao
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    aguardar(lambda: janela._desktop_fase == 'idle'
             and js("LaylayInterface.state.desktopPhase==='idle'"))
    assert js("LaylayInterface.motionStats().count") == 0
    ack_reversao = [ack for ack in acknowledgements
                    if ack['sequence'] == janela._desktop_sequencia]
    assert ack_reversao, {
        'sequence': janela._desktop_sequencia,
        'qt_phase': janela._desktop_fase,
        'qt_geometry': [janela.width(), janela.height()],
        'web_size': [janela.web.width(), janela.web.height()],
        'acks': acknowledgements[-8:],
    }
    assert ack_reversao[-1]['phase'] == 'committing'
    assert ack_reversao[-1]['size'] == ack_reversao[-1]['web'] == [
        janela._desktop_destino.width(), janela._desktop_destino.height()
    ]
    assert entradas == []


def test_expansao_mantem_elementos_alinhados_a_geometria_intermediaria(conversa_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation
    from PySide6.QtWidgets import QApplication

    janela, _ponte, entradas, js, aguardar = conversa_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    js("LaylayInterface.goMode('desktop');LaylayInterface.state.preferences.reduced=false")
    aguardar(lambda: janela.modo_apresentacao == 'desktop' and janela._desktop_fase == 'idle')
    janela.expandir_desktop(fixar=True)
    aguardar(lambda: janela._desktop_fase == 'resizing' and js("LaylayInterface.state.desktopPhase==='resizing'"))
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running

    from PySide6.QtTest import QTest
    QTest.qWait(75)
    janela._animacao_desktop.pause()
    tempo_intermediario = janela._animacao_desktop.currentTime()
    assert 0 < tempo_intermediario < janela._animacao_desktop.duration()
    aguardar(lambda: js(
        f"innerWidth==={janela.web.width()}&&innerHeight==={janela.web.height()}"))
    amostra = json.loads(js(f"""JSON.stringify((()=>{{
      const nomes=['.desktop-toolbar','.desktop-overview','.desktop-page','.desktop-portrait .avatar'];
      for(const seletor of nomes)for(const animation of document.querySelector(seletor)?.getAnimations()||[])
        if(animation.animationName?.startsWith('desktop-'))animation.currentTime={tempo_intermediario};
      const measure=()=>Object.fromEntries(nomes.map(seletor=>{{
        const element=document.querySelector(seletor),rect=element.getBoundingClientRect();
        return [seletor,{{top:rect.top,left:rect.left,right:rect.right,bottom:rect.bottom,
          transform:getComputedStyle(element).transform}}];
      }}));
      return {{viewport:[innerWidth,innerHeight],
        compactVisibility:getComputedStyle(document.querySelector('.desktop-compact')).visibility,
        expandedVisibility:getComputedStyle(document.querySelector('.desktop-expanded')).visibility,
        island:(()=>{{
        const r=document.querySelector('.desktop-island').getBoundingClientRect();
        return [r.left,r.top,r.width,r.height];
      }})(),native:measure()}};
    }})())"""))
    assert amostra['viewport'] == [janela.web.width(), janela.web.height()]
    assert amostra['island'] == [0, 0, janela.web.width(), janela.web.height()]
    if amostra['expandedVisibility'] == 'visible':
        # O avatar mantém sua animação de flutuação contínua, alheia à expansão.
        assert all(item['transform'] == 'none' for seletor, item in amostra['native'].items()
                   if seletor != '.desktop-portrait .avatar'), amostra
        assert all(
            0 <= item['left'] <= item['right'] <= amostra['viewport'][0]
            and 0 <= item['top'] <= item['bottom'] <= amostra['viewport'][1]
            for item in amostra['native'].values()
        ), amostra
    else:
        assert amostra['compactVisibility'] == 'visible', amostra
    assert js("getComputedStyle(document.querySelector('.desktop-page-content')).opacity") == '1'

    QApplication.instance().processEvents()
    janela._animacao_desktop.resume()
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    aguardar(lambda: janela._desktop_fase == 'committing')
    aguardar(lambda: janela._desktop_fase == 'idle' and js("LaylayInterface.state.desktopPhase==='idle'"))
    assert janela.estado_desktop == 'expanded'
    assert janela.geometry() == janela._desktop_destino
    assert js("getComputedStyle(document.querySelector('.desktop-page-content')).opacity") == '1'
    aguardar(lambda: js("LaylayInterface.motionStats().desktopState==='expanded'"))
    assert json.loads(js("""JSON.stringify([
      '.desktop-overview .desktop-presence-copy',
      '.desktop-page .context-bar',
      '.desktop-wordmark'
    ].map(selector=>getComputedStyle(document.querySelector(selector)).transform))""")) == [
        'none', 'none', 'none'
    ]

    janela.recolher_desktop()
    aguardar(lambda: janela._desktop_fase == 'resizing')
    janela._animacao_desktop.setCurrentTime(tempo_intermediario)
    QApplication.instance().processEvents()
    geometria_interrompida = janela.geometry()
    janela.expandir_desktop(fixar=True)
    assert janela._desktop_fase == 'starting'
    assert janela._animacao_desktop.state() != QAbstractAnimation.Running
    aguardar(lambda: janela._desktop_fase == 'resizing'
             and js("LaylayInterface.state.desktopPhase==='resizing'"))
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    assert janela._animacao_desktop.startValue() == geometria_interrompida
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    aguardar(lambda: janela._desktop_fase == 'committing')
    aguardar(lambda: janela._desktop_fase == 'idle')
    assert janela.estado_desktop == 'expanded'
    assert janela.geometry() == janela._desktop_destino
    aguardar(lambda: js("LaylayInterface.motionStats().desktopState==='expanded'"))
    assert json.loads(js("""JSON.stringify([
      '.desktop-overview .desktop-presence-copy',
      '.desktop-page .context-bar',
      '.desktop-wordmark'
    ].map(selector=>getComputedStyle(document.querySelector(selector)).transform))""")) == [
        'none', 'none', 'none'
    ]
    assert entradas == []


def test_expansao_preserva_ilha_ate_viewport_util_e_confirma_ack(conversa_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    janela, _ponte, entradas, js, aguardar = conversa_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    js("LaylayInterface.goMode('desktop');LaylayInterface.state.preferences.reduced=false")
    aguardar(lambda: janela.modo_apresentacao == 'desktop' and janela._desktop_fase == 'idle')

    acknowledgements = []
    confirmar = janela.confirmar_transicao_desktop

    def registrar_ack(sequencia, largura, altura):
        acknowledgements.append({
            'sequence': sequencia, 'size': [largura, altura],
            'phase': janela._desktop_fase,
            'web': [janela.web.width(), janela.web.height()],
        })
        confirmar(sequencia, largura, altura)

    monkeypatch.setattr(janela, 'confirmar_transicao_desktop', registrar_ack)
    janela.expandir_desktop(fixar=True)
    aguardar(lambda: janela._desktop_fase == 'resizing'
             and js("LaylayInterface.state.desktopPhase==='resizing'"))
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running

    janela._animacao_desktop.pause()
    janela._animacao_desktop.setCurrentTime(0)
    QTest.qWait(20)
    aguardar(lambda: js(
        f"innerWidth==={janela.web.width()}&&innerHeight==={janela.web.height()}"))
    quadro_minimo = json.loads(js("""JSON.stringify((()=>{
      const island=document.querySelector('.desktop-island');
      const compact=island.querySelector('.desktop-compact');
      const expanded=island.querySelector('.desktop-expanded');
      return {
        phase:LaylayInterface.state.desktopPhase,
        viewport:[innerWidth,innerHeight],
        compact:{display:getComputedStyle(compact).display,
          visibility:getComputedStyle(compact).visibility},
        expanded:{display:getComputedStyle(expanded).display,
          visibility:getComputedStyle(expanded).visibility,
          pointerEvents:getComputedStyle(expanded).pointerEvents}
      };
    })())"""))
    assert quadro_minimo['phase'] == 'resizing', quadro_minimo
    assert quadro_minimo['viewport'][1] < 220, quadro_minimo
    assert quadro_minimo['compact'] == {
        'display': 'flex', 'visibility': 'visible'
    }, quadro_minimo
    assert quadro_minimo['expanded']['visibility'] == 'hidden', quadro_minimo
    assert quadro_minimo['expanded']['pointerEvents'] == 'none', quadro_minimo

    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration() // 2)
    QTest.qWait(20)
    aguardar(lambda: js(
        f"innerHeight>={240}&&innerWidth==={janela.web.width()}&&innerHeight==={janela.web.height()}"))
    quadro_util = json.loads(js("""JSON.stringify((()=>{
      const island=document.querySelector('.desktop-island');
      const expanded=island.querySelector('.desktop-expanded');
      const toolbar=expanded.querySelector('.desktop-toolbar');
      const controls=toolbar.querySelector('.desktop-toolbar-actions');
      const rect=controls.getBoundingClientRect();
      return {
        phase:LaylayInterface.state.desktopPhase,
        viewport:[innerWidth,innerHeight],
        expandedVisibility:getComputedStyle(expanded).visibility,
        controlsVisibility:getComputedStyle(controls).visibility,
        controlsHeight:rect.height,
        controlsWidth:rect.width
      };
    })())"""))
    assert quadro_util['phase'] == 'resizing', quadro_util
    assert quadro_util['viewport'][1] >= 240, quadro_util
    assert quadro_util['expandedVisibility'] == 'visible', quadro_util
    assert quadro_util['controlsVisibility'] == 'visible', quadro_util
    assert quadro_util['controlsHeight'] > 0 and quadro_util['controlsWidth'] > 0, quadro_util

    QApplication.instance().processEvents()
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    aguardar(lambda: janela._desktop_fase == 'idle'
             and js("LaylayInterface.state.desktopPhase==='idle'"))
    assert janela.estado_desktop == 'expanded'
    assert janela.geometry() == janela._desktop_destino
    ack_confirmado = next((ack for ack in reversed(acknowledgements)
                           if ack['phase'] == 'committing'), None)
    assert ack_confirmado, {
        'sequence': janela._desktop_sequencia,
        'geometry': [janela.width(), janela.height()],
        'web': [janela.web.width(), janela.web.height()],
        'acknowledgements': acknowledgements,
    }
    assert ack_confirmado['size'] == ack_confirmado['web'] == [
        janela._desktop_destino.width(), janela._desktop_destino.height()
    ]
    assert entradas == []


def test_expansao_tem_aceleracao_progressiva_e_aguarda_ack_do_viewport(conversa_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    janela, _ponte, entradas, js, aguardar = conversa_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    js("LaylayInterface.goMode('desktop');LaylayInterface.state.preferences.reduced=false")
    aguardar(lambda: janela.modo_apresentacao == 'desktop' and janela._desktop_fase == 'idle')
    origem = janela.geometry()
    janela.expandir_desktop(fixar=True)
    aguardar(lambda: janela._desktop_fase == 'resizing')
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    duracao = janela._animacao_desktop.duration()
    janela._animacao_desktop.pause()
    janela._animacao_desktop.setCurrentTime(duracao // 10)
    QTest.qWait(20)
    aguardar(lambda: js(
        f"innerWidth==={janela.web.width()}&&innerHeight==={janela.web.height()}"))
    fracao_inicio = (
        (janela.width() - origem.width()) / (janela._desktop_destino.width() - origem.width()),
        (janela.height() - origem.height()) / (janela._desktop_destino.height() - origem.height()),
    )
    assert all(.13 <= fracao <= .19 for fracao in fracao_inicio), {
        'duration_ms': duracao, 'time_ms': duracao // 10, 'fraction': fracao_inicio,
    }

    janela._animacao_desktop.setCurrentTime(duracao // 4)
    QTest.qWait(20)
    QApplication.instance().processEvents()
    aguardar(lambda: js(
        f"innerWidth==={janela.web.width()}&&innerHeight==={janela.web.height()}"))
    fracao_largura = (janela.width() - origem.width()) / (
        janela._desktop_destino.width() - origem.width())
    fracao_altura = (janela.height() - origem.height()) / (
        janela._desktop_destino.height() - origem.height())
    meio = json.loads(js("""JSON.stringify({
      viewport:[innerWidth,innerHeight],
      island:[document.querySelector('.desktop-island').getBoundingClientRect().width,
        document.querySelector('.desktop-island').getBoundingClientRect().height],
      phase:LaylayInterface.state.desktopPhase
    })"""))
    assert meio['phase'] == 'resizing'
    assert meio['viewport'] == [janela.web.width(), janela.web.height()], meio
    assert meio['island'] == meio['viewport'], meio
    assert .40 <= fracao_largura <= .48 and .40 <= fracao_altura <= .48, {
        'duration_ms': duracao, 'time_ms': duracao // 4,
        'fraction': [fracao_largura, fracao_altura],
    }

    janela._animacao_desktop.setCurrentTime(3 * duracao // 4)
    QTest.qWait(20)
    aguardar(lambda: js(
        f"innerWidth==={janela.web.width()}&&innerHeight==={janela.web.height()}"))
    fracao_tres_quartos = (
        (janela.width() - origem.width()) / (janela._desktop_destino.width() - origem.width()),
        (janela.height() - origem.height()) / (janela._desktop_destino.height() - origem.height()),
    )
    assert all(.92 <= fracao <= .98 for fracao in fracao_tres_quartos), {
        'duration_ms': duracao, 'time_ms': 3 * duracao // 4,
        'fraction': fracao_tres_quartos,
    }

    janela._animacao_desktop.resume()
    aguardar(lambda: janela._desktop_fase == 'idle')
    aguardar(lambda: js("LaylayInterface.state.desktopPhase==='idle'"))
    assert janela.geometry() == janela._desktop_destino
    assert js(f"innerWidth==={janela.web.width()}&&innerHeight==={janela.web.height()}")
    assert js("""(()=>{
      const rect=document.querySelector('.desktop-island').getBoundingClientRect();
      return rect.width===innerWidth&&rect.height===innerHeight;
    })()""")
    assert entradas == []


def test_expansao_espera_renderer_aplicar_conteudo_antes_de_animar_janela(conversa_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation

    janela, _ponte, entradas, js, aguardar = conversa_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    js("LaylayInterface.goMode('desktop');LaylayInterface.state.preferences.reduced=false")
    aguardar(lambda: janela.modo_apresentacao == 'desktop' and janela._desktop_fase == 'idle')

    janela.expandir_desktop(fixar=True)
    assert janela._desktop_fase == 'starting'
    assert janela._animacao_desktop.state() != QAbstractAnimation.Running
    aguardar(lambda: janela._desktop_fase == 'resizing'
             and js("LaylayInterface.state.desktopPhase==='resizing'"))
    assert js("document.querySelector('.desktop-island').dataset.desktopState==='expanded'")
    assert js("getComputedStyle(document.querySelector('.desktop-expanded')).display!=='none'")
    aguardar(lambda: js("innerHeight>=220"))
    assert js("getComputedStyle(document.querySelector('.desktop-expanded')).visibility!=='hidden'")
    assert float(js("document.querySelector('.desktop-expanded').getBoundingClientRect().height")) > 0
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    assert entradas == []


def test_reducao_de_movimento_do_sistema_para_geometria_qt_ativa(conversa_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation
    from cliente.terminal_2.apresentacao_desktop import geometria_desktop

    janela, _ponte, entradas, js, aguardar = conversa_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    janela.show()
    janela.apresentar('desktop')
    janela.definir_movimento_reduzido_sistema(False)
    janela.expandir_desktop(fixar=True)
    assert janela._desktop_fase == 'starting'
    aguardar(lambda: janela._desktop_fase == 'resizing'
             and js("LaylayInterface.state.desktopPhase==='resizing'"))
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    janela.definir_movimento_reduzido_sistema(True)
    assert janela._animacao_desktop.state() == QAbstractAnimation.Stopped
    assert janela.geometry() == geometria_desktop(
        janela.screen().availableGeometry(), expandida=True,
    )
    assert janela.web.updatesEnabled()
    assert entradas == []


def test_m2_animacao_real_usada_apos_mudanca_de_aba(conversa_web):
    """Captura chamadas reais ao Web Animations API, sem depender de polling de frames."""
    janela, _ponte, entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao == 'desktop')
    js("LaylayInterface.state.preferences.reduced=false")
    janela.selecionar_pagina_desktop('music')
    aguardar(lambda: janela._desktop_fase == 'idle' and js("LaylayInterface.motionStats().desktopState") == 'expanded')
    js("""(()=>{
        window.__m2observed=[];
        const native=Element.prototype.animate;
        Element.prototype.animate=function(frames,options){
            if(this.matches('.desktop-page-content,.desktop-tabs,.desktop-overview,.context-bar,.page-heading'))
                window.__m2observed.push({className:this.className,frames:JSON.stringify(frames),
                  duration:options.duration,playState:'called'});
            return native.call(this,frames,options);
        };
    })()""")
    janela.selecionar_pagina_desktop('system')
    aguardar(lambda: janela._desktop_fase == 'idle' and js("LaylayInterface.motionStats().location") == 'desktop:page:system')
    aguardar(lambda: js("window.__m2observed.some(a=>String(a.className).includes('context-bar'))"))
    records=json.loads(js("JSON.stringify(window.__m2observed)"))
    assert any(a['duration']==215 and '17px' in a['frames'] for a in records),records
    assert not any('desktop-page-content' in a['className'] for a in records),records
    assert janela.pagina_web.backgroundColor().alpha() == 255
    assert entradas == []


def test_m2_entrada_visivel_com_css_de_chegada(conversa_web):
    janela, _ponte, entradas, js, aguardar = conversa_web
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: janela.modo_apresentacao=='desktop')
    aguardar(lambda: js("!!document.querySelector('.desktop-miniature .avatar')"))
    js("LaylayInterface.state.preferences.reduced=false; LaylayInterface.state.desktopEntry=true; LaylayInterface.invalidate()")
    aguardar(lambda: js("document.body.classList.contains('desktop-entering')"))
    animation=json.loads(js("""JSON.stringify((()=>{
      const island=document.querySelector('.desktop-island');
      const mascot=island.querySelector('.desktop-miniature .avatar');
      const css=getComputedStyle(island);
      const mascotCss=getComputedStyle(mascot);
      return {name:css.animationName,duration:css.animationDuration,
        keyframes:island.getAnimations().map(a=>a.effect.getKeyframes()),
        mascotTag:mascot.tagName,mascotHasFace:Boolean(mascot.querySelector('.mascot-figure .face .eye')),
        mascotAnimation:mascotCss.animationName,
        islandTransform:css.transform};
    })())"""))
    assert 'laylay-m2-arrive' in animation['name'],animation
    assert '0.47s' in animation['duration'],animation
    assert animation['mascotTag']=='DIV' and animation['mascotHasFace'],animation
    assert 'laylay-m2-mascot' in animation['mascotAnimation'],animation
    assert animation['islandTransform']=='none',animation
    assert all(not any(prop in frame for prop in ('transform','width','height'))
               for frames in animation['keyframes'] for frame in frames),animation
    js("document.body.classList.add('reduced')")
    assert js("getComputedStyle(document.querySelector('.desktop-island')).animationName")=='none'
    assert js("getComputedStyle(document.querySelector('.desktop-miniature .avatar')).animationName")=='none'
    js("LaylayInterface.state.desktopEntry=false; LaylayInterface.invalidate()")
    assert entradas==[]


def test_transicao_suave_coordena_conteudo_snapshot_e_geometria(interface_web, monkeypatch):
    """A expansão revela o renderer real; o recolhimento preserva o snapshot opaco."""
    from PySide6.QtCore import QAbstractAnimation

    app, _worker, janela, entradas, _eventos = interface_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    janela.show()
    janela.apresentar('desktop')
    janela.ponte_web.pronto()
    janela.expandir_desktop(fixar=True)
    assert janela._transicao_cobertura is None
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    assert janela._web_pintura_congelada is False
    assert janela.web.updatesEnabled()
    hwnd = int(janela.winId())

    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration() // 2)
    app.processEvents()
    assert janela._transicao_cobertura is None
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    app.processEvents()
    assert janela._web_pintura_congelada is False
    assert janela.web.updatesEnabled()
    assert janela._transicao_cobertura is None
    assert janela._desktop_fase == 'committing'
    assert int(janela.winId()) == hwnd

    janela.ponte_web.transicao_pronta(
        janela._desktop_sequencia, janela.web.width(), janela.web.height())
    assert janela._desktop_fase == 'idle'
    assert janela._transicao_cobertura is None

    janela.recolher_desktop()
    assert janela._transicao_cobertura is not None
    assert '#0b0c10' in janela._transicao_cobertura.styleSheet()
    assert not janela._web_pintura_congelada
    janela.apresentar('full')  # Interrupção segura: a pintura permanece ativa.
    assert not janela._web_pintura_congelada
    assert janela.web.updatesEnabled()
    assert entradas == []


def test_conteudo_desktop_fica_visivel_durante_expandir_e_commit(conversa_web):
    janela, _ponte, entradas, js, aguardar = conversa_web
    js("laylay.transicao_pronta=()=>{}")
    janela.apresentar('desktop')
    aguardar(lambda: js("LaylayInterface.state.mode==='desktop'"))
    janela.expandir_desktop(fixar=True)
    aguardar(lambda: js("LaylayInterface.state.desktopPhase==='resizing'"))
    assert janela._transicao_cobertura is None
    assert js("getComputedStyle(document.querySelector('.desktop-page-content')).opacity") == '1'

    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    aguardar(lambda: janela._desktop_fase == 'committing')
    aguardar(lambda: js("LaylayInterface.state.desktopPhase==='committing'"))
    aguardar(lambda: not js("document.body.classList.contains('desktop-resizing')"))
    assert js("getComputedStyle(document.querySelector('.desktop-page-content')).opacity") == '1'
    assert float(js("getComputedStyle(document.querySelector('.desktop-page')).opacity")) > 0
    assert janela._transicao_cobertura is None
    assert entradas == []

    janela.confirmar_transicao_desktop(
        janela._desktop_sequencia, janela.web.width(), janela.web.height())
    assert janela._desktop_fase == 'idle'
    assert janela._transicao_cobertura is None


def test_transicao_suave_e_interrompida_por_nova_navegacao(interface_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation
    app, _worker, janela, entradas, _eventos = interface_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    janela.show()
    janela.apresentar('desktop')
    janela.ponte_web.pronto()
    janela.expandir_desktop(fixar=True)
    assert not janela._web_pintura_congelada
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    app.processEvents()
    janela.recolher_desktop()
    assert janela._transicao_cobertura is not None
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    assert not janela._web_pintura_congelada
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    app.processEvents()
    assert janela.web.updatesEnabled()
    assert not janela._web_pintura_congelada
    assert entradas == []


def test_expansao_revela_renderer_e_recolhimento_limpa_cobertura(interface_web, monkeypatch):
    """A expansão usa o conteúdo vivo; a proteção opaca permanece no recolhimento."""
    from PySide6.QtCore import QAbstractAnimation, QPoint
    app, _worker, janela, comandos, _eventos = interface_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    janela.show()
    janela.apresentar('desktop')
    janela.ponte_web.pronto()
    origem = janela.geometry()
    hwnd = int(janela.winId())

    assert not hasattr(janela, '_animacao_recorte')
    assert not hasattr(janela, '_usar_recorte_desktop')
    janela.expandir_desktop(fixar=True)
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    assert janela._transicao_cobertura is None
    assert not janela._web_pintura_congelada
    assert janela.web.updatesEnabled()
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    app.processEvents()
    assert janela.web.updatesEnabled()
    janela.ponte_web.transicao_pronta(
        janela._desktop_sequencia, janela.web.width(), janela.web.height())
    assert janela._desktop_fase == 'idle'
    assert janela._transicao_cobertura is None
    assert janela.pagina_web.backgroundColor().alpha() == 255
    assert janela.mask().contains(janela.rect().center())
    assert janela.mask().contains(QPoint(0, 0))
    assert not janela.mask().contains(QPoint(0, janela.height()-1))

    janela.recolher_desktop()
    assert janela._animacao_desktop.state() == QAbstractAnimation.Running
    assert janela._transicao_cobertura is not None
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    app.processEvents()
    janela.ponte_web.transicao_pronta(
        janela._desktop_sequencia, janela.web.width(), janela.web.height())
    assert janela._desktop_fase == 'idle'
    assert janela.geometry() == origem
    assert janela._transicao_cobertura is None
    assert janela.web.updatesEnabled()
    assert janela.pagina_web.backgroundColor().alpha() == 0
    assert int(janela.winId()) == hwnd
    assert comandos == []


def test_enfeites_css_nao_animam_em_paralelo_ao_resize_nativo(conversa_web, monkeypatch):
    from PySide6.QtCore import QPoint

    janela, _ponte, _entradas, js, aguardar = conversa_web
    monkeypatch.setenv('LAYLAY_REDUZIR_MOVIMENTO', '0')
    js("LaylayInterface.goMode('desktop')")
    aguardar(lambda: js("LaylayInterface.state.mode==='desktop'"))
    aguardar(lambda: js("LaylayInterface.state.desktopPhase==='idle'"))

    def verificar_enfeites_suspensos():
        aguardar(lambda: js("document.body.classList.contains('desktop-resizing')"))
        estilos = json.loads(js("""JSON.stringify((()=>{
          const ilha=document.querySelector('.desktop-island');
          const aba=document.querySelector('.desktop-tabs button.active');
          const seletores=[
            ['friso',ilha,'::before'],
            ['contorno',ilha,'::after'],
            ['aba',aba,null],
            ['indicador',aba,'::before'],
            ['painel',ilha.querySelector('.desktop-compact'),null],
            ['avatar',ilha.querySelector('.desktop-miniature .avatar'),null],
            ['resumo',document.querySelector('.desktop-overview'),null],
            ['conteudo',document.querySelector('.desktop-page-content'),null]
          ];
          return seletores.map(([nome,elemento,pseudo])=>{
            const estilo=pseudo?getComputedStyle(elemento,pseudo):getComputedStyle(elemento);
            return {nome,transicao:estilo.transitionProperty,animacao:estilo.animationName};
          });
        })())"""))
        assert all(item['transicao'] == 'none' and item['animacao'] == 'none'
                   for item in estilos), estilos

    janela.expandir_desktop(fixar=True)
    verificar_enfeites_suspensos()
    assert janela.mask().boundingRect() == janela.rect()
    assert janela.mask().contains(janela.rect().center())
    assert janela.mask().contains(QPoint(0, 0))
    assert not janela.mask().contains(QPoint(0, janela.height()-1))
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    aguardar(lambda: janela._desktop_fase == 'idle')
    aguardar(lambda: js("LaylayInterface.state.desktopPhase==='idle'"))
    assert js("getComputedStyle(document.querySelector('.desktop-overview')).transitionProperty") == 'opacity'
    assert js("getComputedStyle(document.querySelector('.desktop-page-content')).transitionProperty") == 'opacity'

    janela.recolher_desktop()
    verificar_enfeites_suspensos()
    janela._animacao_desktop.setCurrentTime(janela._animacao_desktop.duration())
    aguardar(lambda: janela._desktop_fase == 'idle')
    aguardar(lambda: js("LaylayInterface.state.desktopPhase==='idle'"))
    assert js("getComputedStyle(document.querySelector('.desktop-overview')).transitionProperty") == 'opacity'
    assert js("getComputedStyle(document.querySelector('.desktop-page-content')).transitionProperty") == 'opacity'
