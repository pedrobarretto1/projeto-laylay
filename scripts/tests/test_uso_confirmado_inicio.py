from __future__ import annotations

from dataclasses import replace
import time
from types import SimpleNamespace
from pathlib import Path
import json
import subprocess

import pytest

from memoria_sqlite import MemoriaSQLite
from mente_laylay.memoria_mental.motor_aprendizado import MotorAprendizadoRuntime
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


def test_receipt_tipado_alimenta_uso_antes_da_publicacao_contextual():
    from mente_laylay.integracao.adaptadores_aplicacao_runtime import AdaptadoresAplicacaoRuntime
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
    observados = []
    estado = EstadoCompartilhadoRuntime()
    servicos = {'_uso_confirmado_runtime': SimpleNamespace(observar_resultado=observados.append),
        '_estado_compartilhado_runtime': estado,
        '_registrar_resultado_execucao_base': lambda *a, **k: False, 'print': lambda _: None}
    adaptadores = AdaptadoresAplicacaoRuntime(namespace_getter=lambda: servicos)
    r = receipt()
    adaptadores.registrar_resultado_execucao(r, origem='executor', executou=True)
    assert observados == [r], 'receipt real se perdeu antes de alimentar o histórico factual'


def criar(tmp_path, **kwargs):
    from mente_laylay.memoria_mental.uso_confirmado_runtime import criar_uso_confirmado_runtime
    memoria = MemoriaSQLite(str(tmp_path / 'uso.sqlite'))
    motor = MotorAprendizadoRuntime(memoria_sqlite=memoria, contexto_getter=lambda: {}, log=lambda _: None)
    runtime = criar_uso_confirmado_runtime(motor_aprendizado=motor, memoria_sqlite=memoria,
        capacidade_getter=lambda _: {'disponivel': True, 'estado': 'disponivel'}, **kwargs)
    return runtime, memoria, motor


def receipt(identidade='acao-1', intent='APP_OPEN', **kwargs):
    campos = dict(intent=intent, origem='executor', executou=True, confirmado=True,
        status='app_aberto', id_solicitacao=identidade, params={'nome_app': 'Visual Studio Code'},
        inicio_execucao=time.time() - 1)
    campos.update(kwargs)
    if campos.get('origem') != 'executor' or not campos.get('id_solicitacao'):
        campos['inicio_execucao'] = None
    return ResultadoAcao(**campos)


def test_uso_confirmado_de_app_e_iot_e_persistido_sem_contar_replay(tmp_path):
    runtime, memoria, _ = criar(tmp_path)
    app = receipt()
    iot = receipt('iot-1', 'IOT_CONTROL', status='ligado', params={'acao': 'ligar', 'alvo': 'lampada_quarto'})
    for r in (app, iot, app, iot):
        assert runtime.observar_resultado(r)
    outro, _, _ = criar(tmp_path)
    itens = outro.snapshot()['periods']['30']['actions']
    assert {i['id']: i['confirmed_uses'] for i in itens} == {'open_vscode': 1, 'iot_power': 1}
    assert len(memoria.listar_eventos_aprendizado_tipo('uso_confirmado', desde=0)) == 2


@pytest.mark.parametrize('campos', [
    {'confirmado': None}, {'confirmado': False}, {'executou': False},
    {'origem': 'ia'}, {'origem': 'contexto'}, {'id_solicitacao': ''},
    {'status': 'falha_execucao'}, {'status': 'aguardando_confirmacao'},
])
def test_proposta_incerteza_falha_e_noop_nao_sao_uso(tmp_path, campos):
    runtime, _, _ = criar(tmp_path)
    assert not runtime.observar_resultado(receipt(**campos))
    assert runtime.snapshot()['periods']['7']['actions'] == []


def test_identidade_de_receipt_reutilizada_para_outro_alvo_e_recusada(tmp_path):
    runtime, _, _ = criar(tmp_path)
    assert runtime.observar_resultado(receipt('iot-1', 'IOT_CONTROL', status='ligado', params={'acao': 'ligar', 'alvo': 'lampada_quarto'}))
    assert not runtime.observar_resultado(receipt('iot-1', 'IOT_CONTROL', status='ligado', params={'acao': 'ligar', 'alvo': 'tomada'}))
    assert runtime.snapshot()['periods']['30']['actions'][0]['confirmed_uses'] == 1


def contexto_player(agora):
    return {'name': 'Minha trilha', 'tab_id': 8, 'last_url': 'https://www.youtube.com/watch?v=abcdefghijk',
        'player': {'state': 'playing', 'tab_id': 8, 'video_id': 'abcdefghijk',
            'observed_at': agora, '_source_observed_at': agora * 1000, 'is_ad': False}}


def playlist(agora):
    return receipt('playlist-1', 'PLAYLIST_PLAY', params={'nome_playlist': 'Minha trilha'},
        alvo='Minha trilha', status='playlist_enviada_sem_confirmacao', confirmado=None, inicio_execucao=agora - 1)


def test_playlist_exige_observacao_correlacionada_e_nao_conta_heartbeats(tmp_path):
    agora = time.time()
    estado = contexto_player(agora)
    estado['player']['state'] = 'paused'
    runtime, _, _ = criar(tmp_path, playlist_state_getter=lambda: estado)
    assert runtime.observar_resultado(playlist(agora))
    assert runtime.snapshot()['periods']['30']['playlists'] == []
    estado['player']['state'] = 'playing'
    for _ in range(20):
        runtime.observar_player(estado['player'], estado)
    itens = runtime.snapshot()['periods']['30']['playlists']
    assert len(itens) == 1 and itens[0]['confirmed_plays'] == 1
    runtime.observar_resultado(playlist(agora))
    runtime.observar_player(estado['player'], estado)
    assert runtime.snapshot()['periods']['30']['playlists'][0]['confirmed_plays'] == 1


@pytest.mark.parametrize('anuncio', [False, True])
def test_fonte_dom_real_publica_boolean_de_anuncio(anuncio):
    fonte = Path('extençao_google/background.js').read_text(encoding='utf-8')
    funcao = fonte[fonte.index('function inspectYouTubePlayerInPage()'):fonte.index('function inspectYouTubeDataInPage()')]
    codigo = '''
const video={paused:false,ended:false,muted:false,volume:1,readyState:4,currentTime:2,duration:200};
const classes={contains:x=>AD && x==='ad-showing'};
global.location={href:'https://www.youtube.com/watch?v=abcdefghijk'};
global.document={title:'Faixa - YouTube',body:{classList:classes},querySelectorAll:s=>s==='video'?[video]:[],
 querySelector:s=>s==='video.html5-main-video'?video:s.includes('html5-video-player')||s==='#movie_player'?{classList:classes}:null};
'''.replace('AD', str(anuncio).lower()) + funcao + '\nconsole.log(JSON.stringify(inspectYouTubePlayerInPage()));'
    retorno = subprocess.run(['node', '-e', codigo], capture_output=True, text=True, check=True)
    observado = json.loads(retorno.stdout)
    assert observado.get('isAd') is anuncio, 'fonte DOM não distingue anúncio de música em reprodução'


@pytest.mark.parametrize('campo,valor', [
    ('state', 'paused'), ('tab_id', 9), ('video_id', 'zzzzzzzzzzz'),
    ('observed_at', 0), ('_source_observed_at', 0), ('is_ad', True), ('is_ad', None),
])
def test_player_sem_correlacao_nao_inventa_playlist_ouvida(tmp_path, campo, valor):
    agora = time.time()
    estado = contexto_player(agora)
    estado['player'][campo] = valor
    runtime, _, _ = criar(tmp_path, playlist_state_getter=lambda: estado)
    runtime.observar_resultado(playlist(agora))
    runtime.observar_player(estado['player'], estado)
    assert runtime.snapshot()['periods']['30']['playlists'] == []


def test_player_antigo_antes_da_execucao_e_rejeitado(tmp_path):
    agora = time.time()
    estado = contexto_player(agora - 10)
    runtime, _, _ = criar(tmp_path, playlist_state_getter=lambda: estado)
    runtime.observar_resultado(playlist(agora))
    runtime.observar_player(estado['player'], estado)
    assert runtime.snapshot()['periods']['30']['playlists'] == []


def test_falha_de_persistencia_nao_confirma_uso(tmp_path, monkeypatch):
    runtime, _, motor = criar(tmp_path)
    monkeypatch.setattr(motor, 'registrar_evidencia', lambda **_: None)
    assert not runtime.observar_resultado(receipt())
    assert runtime.snapshot()['periods']['30']['actions'] == []


def test_catalogo_indisponivel_nao_expoe_atalho_como_ativo(tmp_path):
    runtime, _, _ = criar(tmp_path)
    runtime.observar_resultado(receipt())
    runtime.capacidade_getter = lambda _: {'disponivel': False, 'estado': 'indisponivel'}
    assert runtime.snapshot()['periods']['30']['actions'] == []


def test_porta_canonica_de_voz_chat_e_painel_observa_receipt(tmp_path):
    from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
    from mente_laylay.integracao.adaptadores_aplicacao_runtime import AdaptadoresAplicacaoRuntime
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
    runtime, _, _ = criar(tmp_path)
    estado = EstadoCompartilhadoRuntime()
    servicos = {'_uso_confirmado_runtime': runtime, '_estado_compartilhado_runtime': estado,
        '_registrar_resultado_execucao_base': lambda *a, **k: False, 'print': lambda _: None}
    adaptadores = AdaptadoresAplicacaoRuntime(namespace_getter=lambda: servicos)
    for canal in ('voz', 'chat', 'terminal_panel'):
        resultado = {'intent': 'APP_OPEN', 'id_solicitacao': canal, 'params': {'nome_app': 'Visual Studio Code'}}
        adaptador = AdaptadorResultadoOperacional(resultado, resultado['params'], 'abre o Visual Studio Code', '',
            {'_registrar_resultado_execucao': adaptadores.registrar_resultado_execucao})
        adaptador.marcar_resultado('app_aberto', executou=True, confirmado=True)
    assert runtime.snapshot()['periods']['30']['actions'][0]['confirmed_uses'] == 3


@pytest.mark.parametrize('player_antes_receipt', [False, True])
def test_executor_playlists_storage_adaptador_e_player_reais_correlacionam(tmp_path, player_antes_receipt):
    from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
    from mente_laylay.autonomia.executor_playlists import DependenciasExecutorPlaylists, executar_intencao_playlists
    from mente_laylay.integracao.adaptadores_aplicacao_runtime import AdaptadoresAplicacaoRuntime
    from mente_laylay.integracao.chrome_ws_handlers import ChromeWsEventosRuntime
    from mente_laylay.integracao.registro_musica import RegistroMusicaLeitura
    from mente_laylay.integracao.registro_operacoes_musicais import RegistroOperacoesMusicais
    from mente_laylay.memoria_mental.consulta_musical import ConsultaMusicalRuntime
    from mente_laylay.memoria_mental.operacoes_musicais_runtime import OperacoesMusicaisRuntime
    from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
    estado = {}
    runtime, _, _ = criar(tmp_path, playlist_state_getter=lambda: estado)
    chrome = ChromeWsEventosRuntime(solicitacoes=SimpleNamespace(), playlist_state=estado,
        yt_clean_url=lambda url: url, playlist_avancar_proxima=lambda: False,
        falar_com_lipsync=lambda *a, **k: None, user_context_getter=lambda: {},
        aplicar_user_updates=lambda _: None, action_context_getter=lambda: {},
        aplicar_action_updates=lambda _: None, player_observer=runtime.observar_player)
    def observar_play():
        chrome.dispatch({'type': 'PLAYER_EVENT', 'event': 'player_state', 'state': 'playing',
            'url': 'https://www.youtube.com/watch?v=abcdefghijk', 'videoId': 'abcdefghijk',
            'tabId': 8, 'isAd': False, 'observedAt': time.time() * 1000, 'currentTime': 1, 'duration': 200})
    def navegador_controlado(url, **kwargs):
        if player_antes_receipt:
            observar_play()
        return {'ok': True, 'confirmado': None, 'tab': {'id': 8}}
    playlists = PlaylistRuntime(state_file=str(tmp_path / 'playlists.json'), legacy_file=str(tmp_path / 'legacy.json'),
        cache={}, ultima_playlist_getter=lambda: '', playlist_state=estado, youtube_play=navegador_controlado,
        artwork_dir=str(tmp_path / 'artwork'), log=lambda _: None)
    assert playlists.save({'Minha trilha': [{'url': 'https://www.youtube.com/watch?v=abcdefghijk', 'titulo': 'Faixa'}]})
    operacoes = OperacoesMusicaisRuntime(playlists_usuario=playlists, playlists_laylay=None,
        musica_estado_getter=lambda chave, default=None: default, musica_estado_setter=lambda *a: None,
        solicitar_aba_ativa=lambda **k: {}, playlist_state=estado, log=lambda _: None)
    leitura = RegistroMusicaLeitura.criar(ConsultaMusicalRuntime(playlists_usuario=playlists,
        playlists_laylay=None, estado_getter=lambda: {'playlist_state': estado}))
    servicos = {'_uso_confirmado_runtime': runtime, '_estado_compartilhado_runtime': EstadoCompartilhadoRuntime(),
        '_registrar_resultado_execucao_base': lambda *a, **k: False, 'print': lambda _: None}
    adaptadores = AdaptadoresAplicacaoRuntime(namespace_getter=lambda: servicos)
    publicados = []
    def publicar(r, *a, **k):
        publicados.append(r)
        return adaptadores.registrar_resultado_execucao(r, *a, **k)
    pedido = {'intent': 'PLAYLIST_PLAY', 'id_solicitacao': 'selecao-real', 'params': {'nome_playlist': 'Minha trilha'}}
    adaptador = AdaptadorResultadoOperacional(pedido, pedido['params'], 'toca a playlist Minha trilha', 'pc_a',
        {'_registrar_resultado_execucao': publicar})
    deps = DependenciasExecutorPlaylists(marcar_resultado=adaptador.marcar_resultado,
        falar_por_status=lambda *a, **k: None, abrir_url_musical=lambda _: False,
        contexto_fala=lambda: {}, musica_leitura=leitura, musica_operacoes=RegistroOperacoesMusicais.criar(operacoes))
    executar_intencao_playlists('PLAYLIST_PLAY', pedido['params'], 'toca a playlist Minha trilha', 'pc_a', {}, deps)
    assert publicados and publicados[0].id_solicitacao == 'selecao-real'
    assert publicados[0].params['nome_playlist'] == 'Minha trilha'
    assert publicados[0].inicio_execucao > 0
    if not player_antes_receipt:
        assert runtime.snapshot()['periods']['30']['playlists'] == []
        observar_play()
    assert runtime.snapshot()['periods']['30']['playlists'][0]['confirmed_plays'] == 1


def test_janelas_sete_trinta_dias_e_projecao_publica_nao_expoem_receipt(tmp_path):
    from datetime import datetime
    from mente_laylay.integracao.desktop_bridge import sanitizar_dashboard_estado
    runtime, memoria, _ = criar(tmp_path)
    runtime.observar_resultado(receipt())
    runtime.observar_resultado(receipt('nova'))
    conn = memoria._conectar()
    try:
        conn.execute('UPDATE aprendizado_eventos SET criado_em=? WHERE id_evento=?',
            (datetime.fromtimestamp(time.time() - 10 * 86400).isoformat(' '), 'uso:acao:acao-1'))
        conn.commit()
    finally:
        conn.close()
    home = runtime.snapshot()
    assert home['periods']['7']['actions'][0]['confirmed_uses'] == 1
    assert home['periods']['30']['actions'][0]['confirmed_uses'] == 2
    publico = sanitizar_dashboard_estado({'home': home})['home']
    assert publico['periods']['30']['actions'][0]['confirmed_uses'] == 2
    assert publico['observed_since'] == pytest.approx(home['observed_since'], abs=0.1)
    assert all(chave not in json.dumps(publico) for chave in ('id_solicitacao', 'params', 'visual_studio_code'))


@pytest.mark.parametrize('pergunta', ['Como funciona o início inteligente?',
    'Por que aparecem ações frequentes no início?', 'A ilha mostra playlists mais ouvidas?'])
def test_catalogo_vivo_explica_inicio_sem_promessa_de_consulta_pelo_chat(pergunta):
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    mapa = MapaHabilidadesRuntime()
    contexto = mapa.contexto_para_prompt(pergunta)
    assert '7 ou 30 dias' in contexto
    assert 'reproduções iniciadas' in contexto
    assert 'não autoriza' in contexto
    assert 'não implica consulta desses rankings pelo chat' in contexto


def test_agregado_de_dois_dominios_preserva_falha_parcial(tmp_path):
    runtime, _, _ = criar(tmp_path)
    assert runtime.observar_resultado(receipt())
    assert not runtime.observar_resultado(receipt('iot-falhou', 'IOT_CONTROL', status='falha_execucao',
        confirmado=False, executou=False, params={'acao': 'ligar', 'alvo': 'lampada_quarto'}))
    itens = runtime.snapshot()['periods']['30']['actions']
    assert [(i['id'], i['confirmed_uses']) for i in itens] == [('open_vscode', 1)]


@pytest.mark.parametrize('is_ad', [False, True, None])
def test_background_preserva_conhecimento_de_anuncio_na_eleicao_canonica(is_ad):
    fonte = Path('extençao_google/background.js').read_text(encoding='utf-8')
    funcao = fonte[fonte.index('async function discoverExistingYouTubePlayback()'):fonte.index('function schedulePlayerDiscovery(')]
    codigo = '''
let playerDiscoveryRunning=false,playerDiscoveryQueued=false;
const findBestYouTubeCandidate=async()=>({tab:{id:8,url:'https://www.youtube.com/watch?v=abcdefghijk'},response:{ok:true,playing:true,videoId:'abcdefghijk',isAd:AD}});
const readYouTubeTabData=async()=>({response:{}});
const updateCanonicalMusicOwner=()=>{};
const youtubeVideoId=()=> 'abcdefghijk';
const sendWs=v=>{console.log(JSON.stringify(v));return true;};
'''.replace('AD', json.dumps(is_ad)) + funcao + '\ndiscoverExistingYouTubePlayback();'
    retorno = subprocess.run(['node', '-e', codigo], capture_output=True, text=True, check=True)
    assert json.loads(retorno.stdout)['isAd'] is is_ad


@pytest.mark.parametrize('anuncio', [False, True])
def test_content_script_probe_publica_estado_de_anuncio_do_dom(anuncio):
    fonte = Path('extençao_google/content_script.js').read_text(encoding='utf-8')
    helper = fonte[fonte.index('function _laylayYoutubeIsAd()'):fonte.index('chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {')]
    inicio = fonte.index('if (request.action === "PROBE_YT_PLAYER")')
    bloco = fonte[inicio:fonte.index('// --- COMANDOS ADICIONAIS', inicio)]
    codigo = '''
const video={paused:false,ended:false,muted:false,volume:1,readyState:4,currentTime:2,duration:200};
const classes={contains:x=>AD && x==='ad-showing'};
global.location={href:'https://www.youtube.com/watch?v=abcdefghijk'};global.window={location};
global.document={title:'Faixa - YouTube',body:{classList:classes},querySelectorAll:s=>s==='video'?[video]:[],
 querySelector:s=>s==='video.html5-main-video'?video:s.includes('html5-video-player')?{classList:classes}:null};
const _laylayYoutubeQueueSnapshot=()=>({observed:false,items:[]});const _laylayYoutubeChannelText=()=>'';
const sendResponse=v=>console.log(JSON.stringify(v));
'''.replace('AD', str(anuncio).lower()) + helper + '\nfunction probe(request){' + bloco + '}\nprobe({action:"PROBE_YT_PLAYER"});'
    retorno = subprocess.run(['node', '-e', codigo], capture_output=True, text=True, check=True)
    assert json.loads(retorno.stdout)['isAd'] is anuncio
