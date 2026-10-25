"""Contratos do refinamento aprovado sobre owners e dados reais."""
from __future__ import annotations

import json
import pytest

from scripts.tests.test_terminal_interface_web_v1 import interface_web
from scripts.tests.test_terminal_web_v1_paginas import paginas_reais


def test_primeiro_clique_da_ilha_abre_inicio_na_mesma_janela(interface_web):
    _app, _worker, janela, enviadas, _eventos = interface_web
    janela.apresentar('desktop')
    hwnd = int(janela.winId())
    janela.ponte_web.gesto_desktop('expandir')
    assert janela.desktop_pagina == 'home'
    assert int(janela.winId()) == hwnd
    assert enviadas == []


def test_geometria_oficial_reproduz_proporcoes_da_previa_sem_invadir_topo():
    from PySide6.QtCore import QRect
    from cliente.terminal_2.apresentacao_desktop import geometria_desktop
    area = QRect(0, 0, 1440, 960)
    compacta = geometria_desktop(area)
    assert (compacta.width(), compacta.height(), compacta.top()) == (272, 54, 120)
    for pagina in ('home','chat','lamp','music','streaming','memory','system','dev','settings'):
        ret = geometria_desktop(area, True, pagina)
        assert (ret.width(), ret.height(), ret.top()) == (1100, 730, 120)


def test_preferencia_do_inicio_persiste_sem_enviar_operacao_para_mente(interface_web):
    _app, _worker, janela, enviadas, _eventos = interface_web
    valor = {'version': 1, 'period_days': 7, 'pinned_ids': ['playlist:Teste'], 'hidden_ids': []}
    janela.definir_preferencia('inicio_inteligente', valor)
    assert janela.preferencias_publicas()['home'] == valor
    assert json.loads(janela.preferencias.value('v1/inicio_inteligente')) == valor
    assert enviadas == []


@pytest.mark.parametrize('valor', [
    {'version': True, 'period_days': 7, 'pinned_ids': [], 'hidden_ids': []},
    {'version': 1, 'period_days': 90, 'pinned_ids': [], 'hidden_ids': []},
    {'version': 1, 'period_days': 7, 'pinned_ids': ['shell:shutdown'], 'hidden_ids': []},
    {'version': 1, 'period_days': 7, 'pinned_ids': ['playlist:Teste\x00'], 'hidden_ids': []},
    {'version': 1, 'period_days': 7, 'pinned_ids': ['action:x']*33, 'hidden_ids': []},
    {'version': 1, 'period_days': 7, 'pinned_ids': [], 'hidden_ids': [], 'execute': True},
])
def test_preferencia_invalida_nao_grava_nem_executa(interface_web, valor):
    _app, _worker, janela, enviadas, _eventos = interface_web
    with pytest.raises(ValueError):
        janela.definir_preferencia('inicio_inteligente', valor)
    assert janela.preferencias.value('v1/inicio_inteligente') is None
    assert enviadas == []


def test_animacao_de_entrada_e_uma_ocorrencia_visual_sem_reinicio_por_feed(interface_web, monkeypatch):
    app, worker, janela, enviadas, _eventos = interface_web
    janela.preferencias.setValue('v1/reduzir_movimento', False)
    monkeypatch.delenv('LAYLAY_REDUZIR_MOVIMENTO', raising=False)
    janela.apresentar('desktop')
    janela.iniciar_apresentacao()
    app.processEvents()
    janela.confirmar_transicao_desktop(janela._desktop_sequencia, janela.web.width(), janela.web.height())
    assert janela.apresentacao_publica()['desktop_entry'] is True
    worker.mensagem.emit({'type': 'state', 'activity': 'idle'})
    assert janela.apresentacao_publica()['desktop_entry'] is True
    janela._entrada_visual_timer.timeout.emit()
    assert janela.apresentacao_publica()['desktop_entry'] is False
    janela.selecionar_pagina_desktop('home')
    janela.recolher_desktop()
    assert janela.apresentacao_publica()['desktop_entry'] is False
    assert enviadas == []


def test_inicio_oficial_expoe_personalizacao_com_estado_sem_historico_honesto(paginas_reais):
    js, esperar, _recebidas = paginas_reais
    js("LaylayInterface.goPage('home')")
    esperar(lambda: js("!!document.querySelector('.home-inteligente')"))
    assert js("document.getElementById('page-content').textContent.includes('Continuar de onde parou')")
    assert js("document.getElementById('page-content').textContent.includes('histórico')")
    assert not js("document.getElementById('page-content').textContent.includes('42 reproduções')")
    assert not js("document.getElementById('page-content').textContent.includes('Entre luzes baixas')")


def test_periodo_fixar_ocultar_e_restaurar_usam_preferencias_reais_sem_executar(paginas_reais):
    js, esperar, _recebidas = paginas_reais
    entradas = []
    js.ponte.enviar_entrada = entradas.append
    js.dashboard['home'] = {'freshness': 'fresh', 'observed_at': 1, 'periods': {
        '7': {'playlists': [{'name': 'Teste', 'confirmed_plays': 2}], 'actions': []},
        '30': {'playlists': [{'name': 'Teste', 'confirmed_plays': 5}], 'actions': []},
    }}
    js("LaylayInterface.goPage('home')")
    esperar(lambda: js("document.querySelector('.playlist-ranking')?.textContent.includes('5 reproduções')"))
    js("document.querySelector('[data-home-period=\"7\"]').click()")
    esperar(lambda: js("LaylayInterface.state.preferences.home.period_days===7&&document.querySelector('.playlist-ranking').textContent.includes('2 reproduções')"))
    assert js.janela.preferencias_publicas()['home']['period_days'] == 7
    js("document.querySelector('[data-home-pin=\"playlist:Teste\"]').click()")
    esperar(lambda: 'playlist:Teste' in js.janela.preferencias_publicas()['home']['pinned_ids'])
    js("document.querySelector('[data-home-hide=\"playlist:Teste\"]').click()")
    esperar(lambda: js("document.querySelectorAll('.playlist-ranking .playlist-card').length===0"))
    assert js.janela.preferencias_publicas()['home']['hidden_ids'] == ['playlist:Teste']
    js("document.querySelector('[data-home-restore]').click()")
    esperar(lambda: js("document.querySelectorAll('.playlist-ranking .playlist-card').length===1"))
    assert js.janela.preferencias_publicas()['home']['hidden_ids'] == []
    assert entradas == []


def test_sugestao_sem_alvo_reutilizavel_abre_controles_sem_repetir_efeito(paginas_reais):
    js, esperar, _recebidas = paginas_reais
    entradas = []
    js.ponte.enviar_entrada = entradas.append
    js.dashboard['home'] = {'freshness': 'fresh', 'observed_at': 1, 'periods': {
        str(dias): {'playlists': [], 'actions': [{'id': 'iot_power', 'title': 'Dispositivos', 'confirmed_uses': 3}]}
        for dias in (7, 30)
    }}
    js("LaylayInterface.goPage('home')")
    esperar(lambda: js("!!document.querySelector('[data-home-execute=\"action:iot_power\"]')"))
    js("document.querySelector('[data-home-execute=\"action:iot_power\"]').click()")
    esperar(lambda: js("LaylayInterface.state.page==='lamp'"))
    assert entradas == []


def test_nome_do_ranking_e_texto_sem_html_nem_acao_quando_catalogo_nao_confirma(paginas_reais):
    js, esperar, _recebidas = paginas_reais
    nome = '<img src=x onerror=window.injetado=true>'
    js.dashboard['home'] = {'freshness': 'fresh', 'observed_at': 1, 'periods': {
        str(dias): {'playlists': [{'name': nome, 'confirmed_plays': 1}], 'actions': []}
        for dias in (7, 30)
    }}
    js("LaylayInterface.goPage('home')")
    esperar(lambda: js("document.querySelector('.playlist-ranking')?.textContent.includes('onerror')"))
    assert js("window.injetado!==true&&document.querySelectorAll('.playlist-ranking img').length===0")
    assert js("document.querySelector('.playlist-ranking [data-tp-action=playlist-play]').disabled")


@pytest.mark.parametrize('largura', [1280, 390])
def test_biblioteca_preserva_cards_capas_e_play_sobreposto_apos_refinamento(paginas_reais, largura, tmp_path):
    import os
    from pathlib import Path
    from PySide6.QtGui import QColor, QImage, QPainter
    from PySide6.QtTest import QTest
    from PySide6.QtWebEngineCore import QWebEngineSettings
    js, esperar, _recebidas = paginas_reais
    js.janela.capas_locais.diretorio = tmp_path
    trace = []
    png_original = js.janela.capas_locais.png
    def png_observado(url):
        dados = png_original(url)
        trace.append(('png',url.toString(),len(dados)))
        return dados
    js.janela.capas_locais.png = png_observado
    permitido_original = js.janela.politica_recursos.permitido
    def permitido_observado(url, recurso):
        resultado = permitido_original(url, recurso)
        if 'artwork' in url.toString():
            trace.append(('recurso',url.toString(),resultado))
        return resultado
    js.janela.politica_recursos.permitido = permitido_observado
    js.janela.web.settings().setAttribute(QWebEngineSettings.AutoLoadImages, True)
    catalogo = []
    for indice, nome in enumerate(('Teste', 'Noite', 'Piano', 'Clássicos', 'Rock', 'Favoritas', 'Sem capa')):
        token = f'{indice:024x}.png'
        imagem = QImage(240, 240, QImage.Format_RGB32)
        imagem.fill(QColor.fromHsv(indice*45, 105, 145))
        pintor = QPainter(imagem)
        pintor.setPen(QColor('#eadfff'))
        pintor.drawEllipse(28, 28, 180, 180)
        pintor.drawText(28, 125, nome)
        pintor.end()
        assert imagem.save(str(tmp_path/token))
        catalogo.append({'name':nome,'count':125 if indice==0 else indice+2,
            'artwork_url':'laylay-playlist-artwork://'+token if indice<6 else ''})
    js.dashboard['music'].update(catalog=catalogo, playlist='Teste')
    js.janela.resize(largura, 900)
    js("LaylayInterface.goPage('music')")
    esperar(lambda: js("!!document.querySelector('.tp-playlist .tp-art')"))
    try:
        esperar(lambda: js("(()=>{const i=document.querySelector('.tp-playlist .tp-art img');return i?.complete&&i.naturalWidth>0})()"))
    except AssertionError:
        pytest.fail(str(trace)+str(js("JSON.stringify({html:document.querySelector('.tp-playlist')?.outerHTML,image:document.querySelector('.tp-playlist img')?.complete,width:document.querySelector('.tp-playlist img')?.naturalWidth})")))
    assert js("getComputedStyle(document.querySelector('.tp-playlists')).display==='grid'"), 'Biblioteca virou chips em vez dos cards anteriores'
    assert js("(()=>{const a=document.querySelector('.tp-playlist .tp-art');return getComputedStyle(a).display!=='none'&&a.clientWidth>70&&a.clientHeight>55})()"), 'Capa existente foi escondida pelo refinamento'
    assert js("getComputedStyle(document.querySelector('.tp-playlist-play')).position==='absolute'"), 'Play perdeu a posição sobre a capa'
    assert js("document.querySelector('.tp-playlist strong').textContent==='Teste'&&document.querySelector('.tp-playlist small').textContent.includes('125 faixas')")
    assert js("document.querySelector('.tp-playlist').classList.contains('active')")
    js("document.querySelector('[data-tp-action=catalog-all]').click()")
    esperar(lambda: js("document.querySelectorAll('.tp-playlist').length===7"))
    assert js("document.querySelectorAll('.tp-playlist .tp-art img').length===6&&document.querySelectorAll('.tp-playlist .tp-art>span').length===1")
    assert js("(()=>{const p=document.getElementById('page-content');return p.scrollWidth<=p.clientWidth+1})()")
    if os.environ.get('LAYLAY_PLAYLIST_CAPTURE') == '1':
        destino = Path('artifacts/interface_v1/refinamento_inteligente_oficial/playlist-restaurada')
        destino.mkdir(parents=True, exist_ok=True)
        js("document.querySelector('.tp-playlists').scrollIntoView({block:'start'})")
        QTest.qWait(350)
        assert js.janela.grab().save(str(destino/f'biblioteca-{largura}.png'))
    js("document.querySelector('[data-tp-action=catalog-all]').click()")
    esperar(lambda: js("document.querySelectorAll('.tp-playlist').length===6"))


@pytest.mark.parametrize('largura', [390, 1280])
def test_b1_exibe_capas_publicadas_sem_inventar_ranking(paginas_reais, largura, tmp_path):
    from pathlib import Path
    import tempfile
    from PySide6.QtGui import QColor, QImage
    from PySide6.QtTest import QTest
    from PySide6.QtWebEngineCore import QWebEngineSettings

    js, esperar, _recebidas = paginas_reais
    js.janela.capas_locais.diretorio = tmp_path
    js.janela.web.settings().setAttribute(QWebEngineSettings.AutoLoadImages, True)
    catalogo = []
    for indice, nome in enumerate(('alternativo', 'anime', 'brisa da madrugada')):
        entry = {'name': nome, 'count': indice + 5}
        if indice < 2:
            token = f'{indice + 8:024x}.png'
            image = QImage(240, 240, QImage.Format_RGB32)
            image.fill(QColor.fromHsv(210 + indice * 50, 105, 140))
            assert image.save(str(tmp_path / token))
            entry['artwork_url'] = 'laylay-playlist-artwork://' + token
        catalogo.append(entry)
    js.dashboard['music'].update(catalog=catalogo, catalog_available=True, catalog_play_available=False)
    js.dashboard['home'] = {
        'freshness': 'fresh', 'periods': {
            str(days): {'playlists': [], 'actions': []} for days in (7, 30)
        },
    }
    js.janela.resize(largura, 920)
    js("LaylayInterface.goPage('home')")
    esperar(lambda: js("document.querySelectorAll('.home-catalog-showcase .playlist-card').length===3"))
    assert js("document.querySelectorAll('.home-catalog-showcase .playlist-spotlight').length===1")
    assert js("document.querySelectorAll('.playlist-ranking .playlist-card').length===0")
    assert js("document.querySelector('.home-catalog-showcase').textContent.includes('Ainda sem reproduções confirmadas')")
    esperar(lambda: js("Array.from(document.querySelectorAll('.home-catalog-showcase .cover img')).length===2 && Array.from(document.querySelectorAll('.home-catalog-showcase .cover img')).every(img=>img.complete && img.naturalWidth>0)"))
    assert js("document.querySelectorAll('.home-catalog-showcase .cover:not(:has(img))').length===1")
    assert js("document.querySelector('.home-catalog-showcase .playlist-spotlight .playlist-info strong').textContent==='alternativo'")
    assert js("document.querySelector('.home-catalog-showcase').textContent.includes('5 faixas na biblioteca')")
    assert js("document.querySelectorAll('.home-catalog-showcase [data-tp-action=playlist-play]').length===0")
    assert js("(()=>{const p=document.getElementById('page-content');return p.scrollWidth<=p.clientWidth+1})()")
    js("document.querySelector('.home-catalog-showcase').scrollIntoView({block:'start'})")
    QTest.qWait(250)
    dest = Path(tempfile.gettempdir()) / 'laylay_home_b1_20261023'
    dest.mkdir(exist_ok=True)
    assert js.janela.grab().save(str(dest / f'home-catalogo-{largura}.png'))
    js("document.querySelector('.home-catalog-showcase [data-home-pin=\"playlist:alternativo\"]').click()")
    esperar(lambda: 'playlist:alternativo' in js.janela.preferencias_publicas()['home']['pinned_ids'])


def test_b1_ranking_evidencia_reproducoes_com_play_bloqueado_sem_catalogo(paginas_reais):
    js, esperar, _recebidas = paginas_reais
    js.dashboard['home'] = {'freshness': 'fresh', 'periods': {
        str(days): {'playlists': [
            {'name':'Trilha principal','confirmed_plays':9},
            {'name':'Outra trilha','confirmed_plays':4}
        ], 'actions': []} for days in (7,30)
    }}
    js.dashboard['music'].update(catalog=[], catalog_play_available=False)
    js("LaylayInterface.goPage('home')")
    # Publicação de teste, sem autorizar reprodução ou modificar a mente.
    js("LaylayInterface.receiveEvent(" + json.dumps({'type':'dashboard_state', 'dashboard':js.dashboard}) + ")")
    esperar(lambda: js("document.querySelectorAll('.playlist-ranking .playlist-card').length===2"))
    assert js("document.querySelector('.playlist-ranking .playlist-spotlight .playlist-info strong').textContent==='Trilha principal'")
    assert js("document.querySelector('.playlist-ranking').textContent.includes('9 reproduções iniciadas confirmadas')")
    assert js("Array.from(document.querySelectorAll('.playlist-ranking [data-tp-action=playlist-play]')).every(b=>b.disabled)")
    assert js("document.querySelectorAll('.playlist-ranking .cover img').length===0")
    assert js("!document.querySelector('.home-catalog-showcase')")


@pytest.mark.parametrize('largura', [390, 1280])
def test_f1_fixados_com_capa_real_e_desafixar_sem_executar(paginas_reais, largura, tmp_path):
    from pathlib import Path
    import tempfile
    from PySide6.QtGui import QColor, QImage
    from PySide6.QtTest import QTest
    from PySide6.QtWebEngineCore import QWebEngineSettings

    js, esperar, _eventos = paginas_reais
    js.janela.capas_locais.diretorio = tmp_path
    js.janela.web.settings().setAttribute(QWebEngineSettings.AutoLoadImages, True)
    image = QImage(240, 240, QImage.Format_RGB32)
    image.fill(QColor('#765c92'))
    token = '0000000000000000000000f1.png'
    assert image.save(str(tmp_path / token))
    js.dashboard['music'].update(catalog=[
        {'name':'alternativo','count':8,'artwork_url':'laylay-playlist-artwork://'+token},
        {'name':'anime','count':27}
    ], catalog_available=True, catalog_play_available=False)
    js.janela.resize(largura,900)
    js("LaylayInterface.goPage('home')")
    js("LaylayInterface.receiveEvent("+json.dumps({'type':'dashboard_state','dashboard':js.dashboard})+")")
    js.janela.definir_preferencia('inicio_inteligente', {
        'version':1,'period_days':30,'pinned_ids':['playlist:alternativo','playlist:anime'],
        'hidden_ids':[],
    })
    # Publicação das preferências, sem enviar comando para a mente.
    js("LaylayInterface.receiveEvent("+json.dumps({'type':'preferencias_ui',
        'preferences':js.janela.preferencias_publicas()})+")")
    esperar(lambda: js("document.querySelectorAll('.pinned-mini-list .pinned-mini-card').length===2"))
    esperar(lambda: js("(()=>{const img=document.querySelector('.pinned-mini-list img');return img?.complete&&img.naturalWidth>0})()"))
    assert js("document.querySelector('.pinned-mini-list .pinned-mini-card strong').textContent==='alternativo'")
    assert js("document.querySelectorAll('.pinned-mini-list img').length===1")
    assert js("document.querySelector('.pinned-mini-list').textContent.includes('8 faixas')")
    assert js("document.querySelector('.pinned-mini-list').textContent.includes('27 faixas')")
    assert js("document.querySelectorAll('.pinned-mini-list .pinned-card-remove').length===2")
    assert js("document.querySelectorAll('.pinned-mini-list [data-tp-action=playlist-play]').length===0")
    assert js("document.querySelectorAll('.pinned-mini-list [data-page=music]').length===2")
    js("document.querySelector('.pinned-mini-list').scrollIntoView({block:'start'})")
    QTest.qWait(180)
    dest=Path(tempfile.gettempdir())/'laylay_home_f1_20261023'
    dest.mkdir(exist_ok=True)
    assert js.janela.grab().save(str(dest/f'fixados-{largura}.png'))
    assert js("(()=>{const p=document.getElementById('page-content');return p.scrollWidth<=p.clientWidth+1})()")
    js("document.querySelector('[data-pinned-id=\"playlist:alternativo\"] [data-home-pin]').click()")
    esperar(lambda: js("document.querySelectorAll('.pinned-mini-card').length===1"))
    assert js.janela.preferencias_publicas()['home']['pinned_ids']==['playlist:anime']


def test_f1_fixado_sem_catalogo_e_atalho_continuam_visiveis_e_inertes(paginas_reais):
    js, esperar, _eventos=paginas_reais
    js.janela.definir_preferencia('inicio_inteligente', {
        'version':1,'period_days':30,
        'pinned_ids':['playlist:brisa da madrugada','action:briefing'],
        'hidden_ids':[],
    })
    js("LaylayInterface.goPage('home')")
    js("LaylayInterface.receiveEvent("+json.dumps({'type':'preferencias_ui',
        'preferences':js.janela.preferencias_publicas()})+")")
    esperar(lambda: js("document.querySelectorAll('.pinned-mini-card').length===2"))
    assert js("document.querySelector('[data-pinned-id=\"playlist:brisa da madrugada\"] strong').textContent==='brisa da madrugada'")
    assert js("document.querySelector('[data-pinned-id=\"playlist:brisa da madrugada\"] .pinned-card-copy').textContent.includes('indisponível')")
    assert js("document.querySelectorAll('.pinned-mini-list img').length===0")
    assert js("!!document.querySelector('[data-pinned-id=\"action:briefing\"]')")
    assert js("document.querySelector('[data-pinned-id=\"action:briefing\"] [data-home-execute]').disabled")
    assert js("document.querySelectorAll('.pinned-mini-list .pinned-card-remove').length===2")
