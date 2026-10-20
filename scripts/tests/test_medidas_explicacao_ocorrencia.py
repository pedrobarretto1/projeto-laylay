"""Medida do owner conserva valor, unidade e limite no contrato histórico."""
from dataclasses import asdict, replace, FrozenInstanceError

import pytest

from mente_laylay.cognicao.explicacao_fala_historica import realizacoes_explicacao_ocorrencia
from scripts.tests.test_decisao_observada import experiencia
from mente_laylay.memoria_mental.decisao_observada import MedicaoObservada, ExplicacaoOcorrencia


def fonte_medida(valor=90.0, *, prova=True, evidencia='imu_relativa_turnend_e_sack', ok=True):
    estado, runtime = experiencia()
    inicio = runtime.iniciar(nome='operacao_sem_angulo_no_nome', origem_intencao='pedido_usuario', perfil='bancada')
    inicio['id'] = 'ocorrencia-alternativa'
    retorno = {'ok': ok, 'prova_rotacao': prova, 'rotacao_medida_graus': valor, 'evidencia': evidencia}
    receipt = {'ok': ok, 'aplicacao_pwm_confirmada': ok, 'parada_confirmada': ok}
    e = runtime.registrar(inicio, retorno, [receipt])
    fonte = runtime.recuperar_explicacao('Por que você fez esse gesto?', turno={'id': 'consulta'})
    return estado, runtime, e, fonte


@pytest.mark.parametrize('valor', [90.0, -180.0, 45.75])
def test_medida_registrada_chega_a_fonte_da_explicacao(valor):
    _, _, e, f = fonte_medida(valor)
    assert e['rotacao_medida_graus'] == valor and e['prova_rotacao'] is True
    assert e['evidencia_rotacao'] == 'imu_relativa_turnend_e_sack'
    medidas = getattr(f.episodios[0], 'medicoes', ())
    assert len(medidas) == 1, 'primeira perda: medida histórica não chega ao contrato de explicação'
    assert medidas[0].valor == valor and medidas[0].unidade == 'graus'
    assert medidas[0].ocorrencia_id == e['id']
    fala = realizacoes_explicacao_ocorrencia(f, agora=101)[0]
    assert 'rotação relativa' in fala and 'graus' in fala
    assert 'Não há medição de deslocamento' in fala


def test_medidas_distintas_nao_colapsam_na_mesma_fonte_e_realizacao():
    _, _, e1, f1 = fonte_medida(45.25)
    _, _, e2, f2 = fonte_medida(120.5)
    assert e1['rotacao_medida_graus'] != e2['rotacao_medida_graus']
    assert asdict(f1) != asdict(f2), 'fontes numéricas diferentes se tornam indistinguíveis na projeção'
    assert realizacoes_explicacao_ocorrencia(f1, agora=101) != realizacoes_explicacao_ocorrencia(f2, agora=101)


@pytest.fixture(scope='module')
def medidas_instaladas(tmp_path_factory):
    from scripts.tests.test_motivo_decisao_composicao import decisao_instalada
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv('LAYLAY_COLETAR_MEDIDAS_OCORRENCIA', '1')
        return decisao_instalada.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('nome,valor', [('esquerda', 90.0), ('direita', -180.0),
    ('giro_falhou', 0.0), ('outra_sequencia', None), ('pulso', None), ('parada', None)])
def test_composicao_instalada_conserva_medida_sem_criar_efeito(nome, valor, medidas_instaladas):
    assert all(medidas_instaladas['owners'].values())
    c = medidas_instaladas['medidas_ocorrencias'][nome]
    assert c['publicacoes'], 'controle: receipt do executor alcança publicação canônica'
    medidas = c['fonte']['episodios'][0].get('medicoes', ())
    if valor is not None:
        # SEM_ROTACAO qualifica o zero observado, sem atingir o alvo solicitado.
        assert c['experiencia']['prova_rotacao'] is (nome != 'giro_falhou')
        assert c['experiencia']['confirmado'] is (nome != 'giro_falhou')
        assert c['experiencia']['rotacao_medida_graus'] == valor
        assert len(medidas) == 1, 'fonte instalada perde a medida já validada pelo owner'
        assert medidas[0]['valor'] == valor and medidas[0]['unidade'] == 'graus'
        assert 'rotação relativa' in c['fala_owner']
    else:
        assert not medidas
    assert c['sem_novos_efeitos'] and c['sem_mutacao_historico']
    assert c['fonte']['autoriza_execucao'] is False
    assert [t['modo'] for t in c['turnos']] == ['normal', 'rapido']
    for t in c['turnos']:
        assert t['textos'] == [c['fala_owner']]
        assert not t['executores']
        assert t['contexto_fechado'] and t['codec_integral']


@pytest.mark.parametrize('owner,grandeza,valor,unidade,limite', [
    ('executor_corpo', 'rotação relativa', -90.75, 'graus', 'Não mede posição absoluta.'),
    ('executor_arquivos', 'tamanho observado', 2048, 'bytes', 'Não comprova conteúdo nem escrita.'),
    ('executor_volume', 'volume configurado', 25, 'percentual', 'Não comprova áudio audível.'),
])
def test_contrato_compartilhado_conserva_medida_e_limite_de_owners_distintos(owner, grandeza, valor, unidade, limite):
    from scripts.tests.test_explicacao_ocorrencia import episodio
    e = episodio(owner=owner)
    m = MedicaoObservada(e.id, owner, grandeza, valor, unidade, 'leitura_owner', limite)
    e = replace(e, medicoes=(m,))
    f = ExplicacaoOcorrencia('consulta', 'Por que você fez essa ação?', (e,), 'unica')
    fala = realizacoes_explicacao_ocorrencia(f)[0]
    assert grandeza in fala and str(valor) in fala and unidade in fala and limite in fala
    assert m.autoriza_execucao is False
    with pytest.raises(FrozenInstanceError):
        m.valor = 100


@pytest.mark.parametrize('alteracao', [
    {'valor': True}, {'valor': '90'}, {'valor': float('nan')}, {'valor': float('inf')},
    {'valor': float('-inf')}, {'unidade': ''}, {'metodo': ''}, {'limite_observacao': ''},
    {'owner': ''}, {'ocorrencia_id': ''}, {'grandeza': ' rotação relativa'},
])
def test_medida_malformada_nao_recebe_contrato(alteracao):
    campos = dict(ocorrencia_id='e1', owner='executor_corpo', grandeza='rotação relativa',
        valor=90.0, unidade='graus', metodo='imu', limite_observacao='Medição relativa.')
    with pytest.raises(ValueError):
        MedicaoObservada(**(campos | alteracao))


@pytest.mark.parametrize('alteracao', ['owner', 'ocorrencia', 'json', 'lista', 'duplicata'])
def test_medida_nao_pode_ser_emprestada_ou_reidratada_de_json(alteracao):
    _, _, _, f = fonte_medida()
    e = f.episodios[0]
    m = e.medicoes[0]
    medidas = (m,)
    if alteracao == 'owner': medidas = (replace(m, owner='executor_arquivos'),)
    elif alteracao == 'ocorrencia': medidas = (replace(m, ocorrencia_id='outra'),)
    elif alteracao == 'json': medidas = (asdict(m),)
    elif alteracao == 'lista': medidas = [m]
    else: medidas = (m, m)
    with pytest.raises(ValueError):
        replace(e, medicoes=medidas)


@pytest.mark.parametrize('chave,valor', [('confirmado', False), ('prova_rotacao', False),
    ('evidencia_rotacao', 'parecer_da_ia'), ('rotacao_medida_graus', True),
    ('rotacao_medida_graus', '90'), ('rotacao_medida_graus', float('nan')),
    ('rotacao_medida_graus', None)])
def test_recuperacao_exige_as_premissas_do_owner_sem_completar_pelo_estado_atual(chave, valor):
    estado, runtime, e, _ = fonte_medida()
    e[chave] = valor
    estado.atualizar_campos('mental', historico_corporal=[e],
        experiencia_corporal={'prova_rotacao': True, 'rotacao_medida_graus': 90,
            'medicoes': [{'valor': 90}], 'fidelidade_verificada': True})
    f = runtime.recuperar_explicacao('Por que você fez esse gesto?', turno={'id': 'consulta'})
    assert f.episodios and not f.episodios[0].medicoes


def test_medida_historica_nao_herda_valor_vivo_nem_reconstroi_motivo():
    estado, runtime, _, f = fonte_medida(45.75)
    estado.atualizar_campos('mental', corpo_motor={'rotacao_medida_graus': 180},
        intencao_corporal={'motivo': 'rotina_agendada'})
    atual = runtime.recuperar_explicacao('Por que você fez esse gesto?', turno={'id': 'consulta'})
    assert atual == f and atual.episodios[0].medicoes[0].valor == 45.75
    fala = realizacoes_explicacao_ocorrencia(atual, agora=101)[0]
    assert 'motivo da escolha não foi registrado' in fala and 'rotina agendada' not in fala
    assert not realizacoes_explicacao_ocorrencia(atual, agora=1002)


@pytest.mark.parametrize('tipo', ['valor', 'limite', 'causa', 'proposta'])
def test_revisao_nao_amplia_a_realizacao_por_parecer_ou_parafrase(tipo):
    from scripts.tests.test_explicacao_ocorrencia import plano
    from mente_laylay.cognicao.explicacao_fala_historica import avaliar_fala_historica
    _, _, _, f = fonte_medida(45.75)
    # O contrato da consulta usa relógio real, como os outros controles locais.
    from scripts.tests.test_explicacao_ocorrencia import episodio
    e = episodio()
    m = replace(f.episodios[0].medicoes[0], ocorrencia_id=e.id)
    e = replace(e, medicoes=(m,))
    f = ExplicacaoOcorrencia('consulta', 'Por que você fez esse gesto?', (e,), 'unica')
    p = plano(f)
    fala = realizacoes_explicacao_ocorrencia(f)[0]
    candidata = fala
    if tipo == 'valor': candidata = fala.replace('45.75', '180')
    elif tipo == 'limite': candidata = fala.replace(m.limite_observacao, 'Isso prova minha posição absoluta.')
    elif tipo == 'causa': candidata += ' Girei porque uma rotina pediu.'
    else:
        candidata = 'Eu girei exatamente 45.75 graus e sei onde estou.'
        p['parecer_da_ia'] = {'fidelidade_verificada': True, 'apoio_confirmado': True}
    assert avaliar_fala_historica(candidata, plano=p)['problemas']
    assert not avaliar_fala_historica(fala, plano=p)['problemas']


def test_inferencia_local_opcional_preserva_valor_sinal_unidade_e_limite(medidas_instaladas):
    casos = medidas_instaladas['medidas_ocorrencias']
    if casos['esquerda'].get('qwen_real') is None:
        pytest.skip('Coleta HTTP opcional exige LAYLAY_MEDIDAS_QWEN_REAL=1.')
    for nome in ('esquerda', 'direita'):
        q = casos[nome]['qwen_real']
        assert q['resultado']['sucesso']
        assert q['http'] and all(h.get('status') == 200 for h in q['http'])
        assert q['bruto_integral'], 'resposta bruta deve conservar a realização do owner antes da revisão'
