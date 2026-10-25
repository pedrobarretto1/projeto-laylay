"""Finalidade explícita não pode ser substituída por consulta ao player."""
import pytest
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.arbitro_turno import arbitrar_turno, CandidatoDecisao
from mente_laylay.autonomia.orquestrador_deterministico import detectar_intencao_deterministica_mente


def retrato(texto, *, tipo='album', nome='Nevermind', id=12):
    turno = {**classificar_modalidade_turno(texto), 'id': id}
    r, _ = construir_retrato_turno(texto, turno=turno,
        mente={'entidades_recentes': {tipo: {'tipo': tipo, 'nome': nome,
            'origem': 'nome_explicito', 'ts': 100}}}, contexto_perceptivo={}, agora=101)
    return turno, r


@pytest.mark.parametrize('texto', ['pode colocar ele para mim ouvir',
    'coloca ele pra eu ouvir', 'poderia colocar isso para eu escutar?',
    'coloque ela para mim escutar'])
def test_pedido_de_reproducao_nao_aceita_status_como_substituto(texto):
    turno, r = retrato(texto)
    assert r['operacao_explicita'] == 'reproduzir_referente'
    assert r['intents_permitidos'] == ['MUSIC_SEARCH']
    erro = arbitrar_turno(texto, [CandidatoDecisao('comando_explicito',
        {'intent': 'MUSIC_STATUS', 'params': {'album': 'Nevermind'}}, 'ia', .99)], turno=turno, retrato=r)
    assert erro['decisao'] is None
    ctx = {'mente_integrada_estado': {'turno_atual': turno, 'retrato_turno_atual': r}}
    candidato = detectar_intencao_deterministica_mente(texto, ctx)
    assert candidato['intent'] == 'MUSIC_SEARCH'
    assert candidato['params']['query'] == 'Nevermind'
    assert candidato['params']['formato'] == 'album'


@pytest.mark.parametrize('texto', ['não coloca ele para mim ouvir',
    'talvez colocar ele para mim ouvir', 'como colocar ele para mim ouvir?',
    'você sabe como colocar ele para mim ouvir?', 'coloca ele em foco'])
def test_outra_finalidade_nao_materializa_reproducao(texto):
    turno, r = retrato(texto)
    assert r['operacao_explicita'] != 'reproduzir_referente'
    proposta = detectar_intencao_deterministica_mente(texto, {'mente_integrada_estado': {'turno_atual': turno,
        'retrato_turno_atual': r}})
    assert not proposta or proposta['intent'] != 'MUSIC_SEARCH'


@pytest.mark.parametrize('tipo,nome,intent,campo', [('artista', 'Tim Maia', 'MUSIC_SEARCH', 'query'),
    ('playlist', 'rock', 'PLAYLIST_PLAY', 'nome_playlist')])
def test_mesma_operacao_conserva_tipo_e_identidade_do_referente(tipo,nome,intent,campo):
    texto = 'pode colocar ele para mim ouvir'
    turno, r = retrato(texto, tipo=tipo, nome=nome)
    p = detectar_intencao_deterministica_mente(texto, {'mente_integrada_estado': {'turno_atual': turno, 'retrato_turno_atual': r}})
    assert p['intent'] == intent and p['params'][campo] == nome


@pytest.mark.parametrize('alteracao', ['id_divergente', 'sem_id', 'outra_fala'])
def test_retrato_de_outro_pedido_nao_materializa_alvo_contextual(alteracao):
    texto = 'pode colocar ele para mim ouvir'
    turno, r = retrato(texto)
    if alteracao == 'id_divergente': turno['id'] = 13
    elif alteracao == 'sem_id':
        turno.pop('id')
        r.pop('id')
    else: texto = 'pode colocar isso para eu escutar'
    p = detectar_intencao_deterministica_mente(texto, {'mente_integrada_estado': {'turno_atual': turno, 'retrato_turno_atual': r}})
    assert not p or p.get('params', {}).get('query') != 'Nevermind'


def test_detector_instanciado_consume_o_estado_canonico_real():
    from mente_laylay.autonomia.orquestrador_deterministico import DeteccaoDeterministicaRuntime
    texto = 'pode colocar ele para mim ouvir'
    turno, r = retrato(texto)
    runtime = DeteccaoDeterministicaRuntime(namespace_getter=lambda: {},
        estado_getter=lambda: {'turno_atual': turno, 'retrato_turno_atual': r},
        sites_diretos={}, apps_map={})
    p = runtime.detectar(texto)
    assert p['intent'] == 'MUSIC_SEARCH'
    assert p['params']['query'] == 'Nevermind'
    assert p['params']['formato'] == 'album'


def test_tipo_album_nao_e_outro_dominio_na_admissao_compartilhada():
    from mente_laylay.memoria_mental.contexto_imediato import _normalizar_dominio_referencia, _resultado_compativel_com_dominio
    assert _normalizar_dominio_referencia('album') == 'musica'
    assert _resultado_compativel_com_dominio({'intent': 'MUSIC_SEARCH'}, 'album')
    assert not _resultado_compativel_com_dominio({'intent': 'APP_OPEN'}, 'album')


def test_instalacao_preserva_operacao_tipo_e_alvo_sem_depender_da_proposta_llm(tmp_path):
    import os, sys, subprocess, textwrap
    from pathlib import Path
    codigo = textwrap.dedent(r'''
        import sys
        from pathlib import Path
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        root = preparar_instalacao_isolada(Path(sys.argv[1]))
        from mente_laylay.autonomia import coordenador_intencao
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM
        root._voz_runtime.falar = lambda *a, **k: False
        executores = []
        coordenador_intencao.executar_intencao = lambda p, *a, **k: executores.append(p) or False
        def modelo(*a, **k): raise AssertionError('detector com fonte não depende de proposta da IA')
        RegistroModeloLLM.executar = modelo
        root._iniciar_planejamento_turno('nunca escutei o álbum Nevermind')
        pedido = 'pode colocar ele para mim ouvir'
        root._iniciar_planejamento_turno(pedido)
        mental = root._estado_compartilhado_runtime.mental
        assert mental['retrato_turno_atual']['referencia_resolvida']['nome'] == 'Nevermind'
        assert mental['retrato_turno_atual']['operacao_explicita'] == 'reproduzir_referente'
        proposta = root.detectar_intencao_deterministica(pedido)
        assert proposta['intent'] == 'MUSIC_SEARCH', proposta
        assert proposta['params']['query'] == 'Nevermind', proposta
        assert proposta['params']['formato'] == 'album', proposta
        assert root._comandos_imediatos_runtime.processar_prioritarios(pedido), 'admissão perdeu candidato já resolvido'
        assert len(executores) == 1 and executores[0]['params']['formato'] == 'album', executores
    ''')
    p = subprocess.run([sys.executable, '-c', codigo, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, encoding='utf8',
        env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'), timeout=60)
    assert p.returncode == 0, p.stdout[-4500:] + p.stderr[-2500:]
