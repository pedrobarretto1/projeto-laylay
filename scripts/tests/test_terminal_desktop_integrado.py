"""Uma única superfície desktop muda apresentação sem criar autoridade mental."""
from __future__ import annotations

from pathlib import Path
import json
import pytest

pytest.importorskip("PySide6.QtWebEngineWidgets")

from scripts.tests.test_terminal_interface_web_v1 import interface_web
from scripts.tests.test_terminal_web_v1_estabilidade import conversa_web
from scripts.tests.test_terminal_web_v1_paginas import paginas_reais


def test_posicao_inicial_da_ilha_libera_a_faixa_das_abas_do_navegador(interface_web):
    _app, _worker, janela, enviadas, _eventos = interface_web
    janela.apresentar('desktop')
    area = janela.screen().availableGeometry()
    assert janela.geometry().top() == area.top()+120, "A ilha não pode iniciar sobre as abas do navegador"
    assert abs(janela.geometry().center().x()-area.center().x()) <= 1
    assert enviadas == []


def test_expansao_em_tela_baixa_preserva_faixa_livre_do_navegador():
    from PySide6.QtCore import QRect
    from cliente.terminal_2.apresentacao_desktop import geometria_desktop

    area = QRect(0, 0, 1280, 680)
    for pagina in ('home', 'chat', 'music', 'system', 'settings', 'memory', 'lamp', 'dev', 'streaming'):
        retangulo = geometria_desktop(area, expandida=True, pagina=pagina)
        assert retangulo.top() == 120
        assert area.contains(retangulo)
        assert retangulo.height() >= 320


@pytest.mark.parametrize('area_xywh', [(0,0,1920,1080),(-1920,-40,1920,1080),(0,0,390,680)])
def test_geometria_usa_ancora_escolhida_e_recolhe_sem_adotar_clamp_do_painel(area_xywh):
    from PySide6.QtCore import QPoint, QRect
    from cliente.terminal_2.apresentacao_desktop import geometria_desktop

    area = QRect(*area_xywh)
    ancora = QPoint(area.right()-140, area.bottom()-60)
    compacta = geometria_desktop(area, ancora=ancora)
    for pagina in ('home','chat','music','dev'):
        expandida = geometria_desktop(area, expandida=True, pagina=pagina, ancora=ancora)
        assert area.contains(expandida)
        assert geometria_desktop(area, ancora=ancora) == compacta
    assert abs(compacta.center().x()-ancora.x()) <= 1
    assert compacta.top() == ancora.y()


def _arrastar_ilha_teste(janela, monkeypatch, dx=70, dy=80):
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QCursor
    import cliente.terminal_2.interface_web_v1 as modulo

    cursor = [janela.mapToGlobal(janela.rect().center())]
    monkeypatch.setattr(QCursor, 'pos', lambda: QPoint(cursor[0]))
    monkeypatch.setattr(modulo, 'botao_esquerdo_pressionado', lambda: True)
    janela.iniciar_arrasto_desktop()
    cursor[0] += QPoint(dx, dy)
    janela.atualizar_arrasto_desktop()
    janela.finalizar_arrasto_desktop()
    return janela.geometry()


def test_arrasto_salva_posicao_restaura_apos_abas_recolhimento_e_nova_janela(interface_web, monkeypatch):
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1

    _app, worker, janela, enviadas, _eventos = interface_web
    janela.show()
    janela.apresentar('desktop')
    hwnd = int(janela.winId())
    identidade = (janela.web, janela.pagina_web, janela.canal, janela.controlador)
    destino = _arrastar_ilha_teste(janela, monkeypatch)
    salva = janela.preferencias.value('v1/desktop_posicao')
    assert salva, "Posição só é durável depois de um arrasto confirmado"
    for pagina in ('home','chat','music','system','settings','memory','lamp','dev','streaming'):
        janela.selecionar_pagina_desktop(pagina)
        janela.recolher_desktop()
        assert janela.geometry() == destino
        assert janela.preferencias.value('v1/desktop_posicao') == salva
    assert int(janela.winId()) == hwnd
    assert identidade == (janela.web, janela.pagina_web, janela.canal, janela.controlador)
    reaberta = JanelaInterfaceWebV1(worker, Path(__file__).parents[2], diretorio_web=janela.diretorio_web)
    try:
        reaberta.apresentar('desktop')
        assert reaberta.geometry() == destino, "Nova instância deve restaurar a mesma posição salva"
        assert reaberta.preferencias.value('v1/desktop_posicao') == salva
    finally:
        reaberta.close()
    assert enviadas == []


def test_animacao_navegacao_e_reancoragem_nao_gravam_posicao_como_se_fossem_arrasto(interface_web):
    _app, _worker, janela, enviadas, _eventos = interface_web
    janela.apresentar('desktop')
    assert janela.preferencias.value('v1/desktop_posicao') is None
    for pagina in ('home','music','chat','dev'):
        janela.selecionar_pagina_desktop(pagina)
        janela._reancorar_desktop()
        janela.recolher_desktop()
        assert janela.preferencias.value('v1/desktop_posicao') is None
    assert enviadas == []


@pytest.mark.parametrize('offsets', [{'center_x': 90000, 'top_y': -90000}, {'center_x': True, 'top_y': []}])
def test_monitor_ausente_ou_preferencia_invalida_tem_fallback_visivel_sem_sobrescrever_escolha(interface_web, offsets):
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1

    _app, worker, janela, enviadas, _eventos = interface_web
    registro = json.dumps({'version': 1, 'screen': {'name': 'monitor-ausente'}, 'offsets': offsets})
    janela.preferencias.setValue('v1/desktop_posicao', registro)
    reaberta = JanelaInterfaceWebV1(worker, Path(__file__).parents[2], diretorio_web=janela.diretorio_web)
    try:
        reaberta.apresentar('desktop')
        for pagina in ('home','music','dev'):
            reaberta.selecionar_pagina_desktop(pagina)
            reaberta._reancorar_desktop()
            assert reaberta.screen().availableGeometry().contains(reaberta.geometry())
            reaberta.recolher_desktop()
        assert janela.preferencias.value('v1/desktop_posicao') == registro
    finally:
        reaberta.close()
    assert enviadas == []


def test_inatividade_nao_recolhe_durante_arrasto_e_reinicia_prazo_no_drop(interface_web, monkeypatch):
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QCursor
    import cliente.terminal_2.interface_web_v1 as modulo

    _app, _worker, janela, enviadas, _eventos = interface_web
    janela.show()
    janela.apresentar('desktop')
    janela.expandir_desktop(fixar=True)
    cursor = [janela.mapToGlobal(janela.rect().center())]
    monkeypatch.setattr(QCursor, 'pos', lambda: QPoint(cursor[0]))
    monkeypatch.setattr(modulo, 'botao_esquerdo_pressionado', lambda: True)
    janela.iniciar_arrasto_desktop()
    janela._recolher_por_inatividade()
    assert janela.estado_desktop == 'expanded'
    cursor[0] += QPoint(20, 20)
    janela.atualizar_arrasto_desktop()
    janela.finalizar_arrasto_desktop()
    assert janela._inatividade_desktop_timer.remainingTime() > 19_000
    assert enviadas == []


def test_soltura_fora_da_ilha_conclui_ultimo_deslocamento_e_salva_posicao_visivel(interface_web, monkeypatch):
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QCursor
    import cliente.terminal_2.interface_web_v1 as modulo

    _app, _worker, janela, enviadas, _eventos = interface_web
    janela.show()
    janela.apresentar('desktop')
    cursor = [janela.mapToGlobal(janela.rect().center())]
    pressionado = [True]
    monkeypatch.setattr(QCursor, 'pos', lambda: QPoint(cursor[0]))
    monkeypatch.setattr(modulo, 'botao_esquerdo_pressionado', lambda: pressionado[0])
    janela.iniciar_arrasto_desktop()
    cursor[0] = janela.screen().availableGeometry().bottomRight()+QPoint(500, 500)
    pressionado[0] = False
    janela.atualizar_arrasto_desktop()
    assert not janela._arrastando_desktop
    assert janela.preferencias.value('v1/desktop_posicao')
    assert janela.screen().availableGeometry().contains(janela.geometry())
    assert janela.estado_desktop == 'compact'
    assert enviadas == []


def test_passar_mouse_na_ilha_compacta_nao_expande_sem_clique(interface_web, monkeypatch):
    from PySide6.QtGui import QCursor
    from PySide6.QtTest import QTest

    app, _worker, janela, enviadas, _eventos = interface_web
    janela.show()
    janela.apresentar("desktop")
    app.processEvents()
    compacta = janela.geometry()
    monkeypatch.setattr(QCursor, "pos", lambda: janela.mapToGlobal(janela.rect().center()))
    janela._observar_cursor_desktop()
    QTest.qWait(400)
    assert janela.estado_desktop == "compact", "Hover observa o olhar; só clique pode expandir"
    assert janela.geometry() == compacta
    janela.ponte_web.gesto_desktop("expandir")
    assert janela.estado_desktop == "expanded"
    assert enviadas == []


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


def test_atividade_humana_renova_prazo_e_pin_nao_impede_recolher(interface_web, monkeypatch):
    from PySide6.QtCore import Qt, QPoint
    from PySide6.QtGui import QCursor
    from PySide6.QtTest import QTest

    _app, _worker, janela, enviadas, _eventos = interface_web
    janela.show()
    janela.apresentar("desktop")
    monkeypatch.setattr(QCursor, "pos", lambda: QPoint(-10000, -10000))
    janela.expandir_desktop(fixar=True)
    timer = janela._inatividade_desktop_timer
    timer.setInterval(160)
    timer.start()
    QTest.qWait(90)
    QTest.keyClick(janela.web.focusProxy() or janela.web, Qt.Key_A)
    QTest.qWait(90)
    assert janela.estado_desktop == "expanded", "Teclado deve renovar o prazo local"
    assert timer.remainingTime() > 19_000, "Interação humana sempre deve renovar20s"
    # Prova a ligação do timeout sem esperar20s em cada regressão. O validador
    # Windows mede o prazo real com vídeo vivo, heartbeat e rascunho.
    timer.timeout.emit()
    assert janela.estado_desktop == "compact", "Foco, pin ou rascunho não mantêm a ilha aberta indefinidamente"
    assert not timer.isActive()
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
        assert geometria.top() == disponivel.top()+min(120, max(0, disponivel.height()-geometria.height()))
        assert abs(geometria.center().x() - disponivel.center().x()) <= 1
    assert expandida.width() >= compacta.width()
    assert expandida.height() >= compacta.height()


def test_animacao_desktop_inverte_do_ponto_atual_e_reduced_aplica_destino(interface_web, monkeypatch):
    from PySide6.QtCore import QAbstractAnimation, QRect
    from cliente.terminal_2.apresentacao_desktop import geometria_desktop

    app, _worker, janela, enviadas, _eventos = interface_web
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "0")
    janela.show()
    app.processEvents()
    janela.apresentar("desktop")
    janela.expandir_desktop()
    animacao = janela._animacao_desktop
    assert animacao.state() == QAbstractAnimation.Running
    animacao.setCurrentTime(animacao.duration() // 2)
    intermediaria = QRect(janela.geometry())
    janela.recolher_desktop()
    assert janela._animacao_desktop is animacao
    assert animacao.startValue() == intermediaria
    janela.apresentar("full")
    assert animacao.state() == QAbstractAnimation.Stopped
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "1")
    janela.apresentar("desktop")
    janela.expandir_desktop()
    assert animacao.state() == QAbstractAnimation.Stopped
    assert janela.geometry() == geometria_desktop(janela.screen().availableGeometry(), expandida=True)
    assert enviadas == []


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
    assert not janela._abrir_desktop_timer.isActive()
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
        assert destino.top() == tela.top()+min(120, max(0, tela.height()-destino.height()))
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

