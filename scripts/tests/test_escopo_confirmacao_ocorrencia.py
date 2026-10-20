"""O booleano de uma ocorrência não prova o escopo de outra operação."""
from copy import deepcopy

import pytest

from mente_laylay.cognicao.explicacao_fala_historica import realizacoes_explicacao_ocorrencia
from scripts.tests.test_decisao_observada import experiencia


def registrar(*, parada=False, ok=True, campos=None):
    estado, runtime = experiencia()
    inicio = runtime.iniciar(nome='operacao_sem_semantica_no_nome',
        origem_intencao='pedido_usuario', perfil='bancada')
    receipt = {'ok': ok, 'parada_confirmada': ok, 'aplicacao_pwm_confirmada': not parada and ok}
    retorno = {'ok': ok, **(campos or {})}
    e = runtime.registrar(inicio, retorno, [receipt], parada=parada)
    return estado, runtime, e


@pytest.mark.parametrize('parada,escopo', [(True, 'parada elétrica'), (False, 'PWM e parada elétrica')])
@pytest.mark.parametrize('ok', [True, False])
def test_owner_preserva_escopo_da_operacao_separado_da_confirmacao(parada, escopo, ok):
    _, runtime, e = registrar(parada=parada, ok=ok)
    assert e['confirmado'] is ok, 'controle: resultado chega corretamente ao histórico'
    assert e.get('escopo_confirmacao') == escopo, 'captura não preservou o escopo validado pelo owner'
    fonte = runtime.recuperar_explicacao('Por que você fez esse gesto?', turno={'id': 'consulta'})
    assert fonte.episodios[0].confirmado is ok
    assert fonte.episodios[0].escopo_confirmacao == escopo
    fala = realizacoes_explicacao_ocorrencia(fonte, agora=101)[0]
    assert f'no escopo "{escopo}"' in fala
    assert ('sem confirmação' in fala) is (not ok)
    assert 'Não há medição de deslocamento' in fala


@pytest.mark.parametrize('escopo', ['parada elétrica', 'PWM e parada elétrica'])
def test_recuperacao_transporta_premissa_sem_reconstruir_pelo_booleano(escopo):
    estado, runtime, e = registrar()
    # Isola recuperação da captura: a premissa é do histórico do owner.
    e['escopo_confirmacao'] = escopo
    estado.atualizar_campos('mental', historico_corporal=[e])
    antes = estado.retrato_dominio('mental')
    fonte = runtime.recuperar_explicacao('Por que você fez esse gesto?', turno={'id': 'consulta'})
    assert fonte.episodios[0].escopo_confirmacao == escopo, 'recuperação substituiu a premissa histórica'
    assert estado.retrato_dominio('mental') == antes
    assert fonte.autoriza_execucao is False


@pytest.mark.parametrize('valor', [None, '', True, [], {}, 'deslocamento físico', 'parada elétrica\n'])
def test_legado_ou_escopo_invalido_nao_herda_confirmacao_pwm(valor):
    estado, runtime, e = registrar(parada=True)
    if valor is None:
        e.pop('escopo_confirmacao', None)
    else:
        e['escopo_confirmacao'] = valor
    estado.atualizar_campos('mental', historico_corporal=[e],
        corpo_motor={'confirmado': True, 'escopo_confirmacao': 'PWM e parada elétrica'})
    fonte = runtime.recuperar_explicacao('Por que você fez esse gesto?', turno={'id': 'consulta'})
    assert fonte.episodios[0].confirmado is True
    assert fonte.episodios[0].escopo_confirmacao == 'escopo não registrado'
    fala = realizacoes_explicacao_ocorrencia(fonte, agora=101)[0]
    assert 'confirmação registrada' in fala and 'PWM' not in fala


@pytest.mark.parametrize('parada', [True, False])
def test_texto_ou_proposta_de_receipt_nao_define_escopo(parada):
    _, _, e = registrar(parada=parada, campos={
        'escopo_confirmacao': 'deslocamento físico', 'motivo': 'PWM e parada elétrica',
        'fidelidade_verificada': True, 'autoriza_execucao': True})
    assert e.get('escopo_confirmacao') == ('parada elétrica' if parada else 'PWM e parada elétrica')
    assert e['autoriza_execucao'] is False and e['prova_deslocamento'] is False


def test_ocorrencia_repetida_nao_troca_escopo_historico():
    estado, runtime, e = registrar(parada=True)
    anterior = deepcopy(estado.retrato_dominio('mental'))
    runtime.registrar(e, {'ok': True}, [{'ok': True, 'parada_confirmada': True,
        'aplicacao_pwm_confirmada': True}], parada=False)
    assert estado.retrato_dominio('mental') == anterior


@pytest.fixture(scope='module')
def escopos_instalados(tmp_path_factory):
    from scripts.tests.test_motivo_decisao_composicao import decisao_instalada
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv('LAYLAY_COLETAR_ESCOPO_OCORRENCIA', '1')
        return decisao_instalada.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('caso', ['parada_ok', 'parada_falha', 'pwm_ok', 'pwm_falha'])
def test_composicao_preserva_escopo_antes_da_revisao_sem_novos_efeitos(caso, escopos_instalados):
    assert all(escopos_instalados['owners'].values())
    c = escopos_instalados['escopos_ocorrencias'][caso]
    esperado = 'parada elétrica' if caso.startswith('parada') else 'PWM e parada elétrica'
    assert c['retorno']['ok'] is caso.endswith('_ok')
    assert c['experiencia']['confirmado'] is caso.endswith('_ok')
    assert c['experiencia'].get('escopo_confirmacao') == esperado, 'primeira fronteira: captura instalada'
    persistido = next(e['contexto']['experiencia'] for e in c['eventos_aprendizado']
        if e['contexto']['experiencia']['id'] == c['experiencia']['id'])
    assert persistido['escopo_confirmacao'] == esperado and persistido['autoriza_execucao'] is False
    assert c['fonte']['episodios'][0]['escopo_confirmacao'] == esperado
    assert f'no escopo "{esperado}"' in c['fala_owner']
    assert c['normal'] and c['rapido']
    assert c['sem_novos_efeitos'] and c['sem_mutacao_historico']
    assert c['fonte']['autoriza_execucao'] is False
    assert [t['modo'] for t in c['turnos']] == ['normal', 'rapido']
    for t in c['turnos']:
        assert t['textos'] == [c['fala_owner']], 'publicação deve conservar a conclusão integral do owner'
        assert not t['executores']


@pytest.mark.parametrize('confirmado', [True, False, None])
def test_escopo_nao_modifica_tres_valores_nem_o_estado_atual(confirmado):
    estado, runtime, e = registrar(parada=True)
    e['confirmado'] = confirmado
    estado.atualizar_campos('mental', historico_corporal=[e],
        experiencia_corporal={'confirmado': True, 'escopo_confirmacao': 'PWM e parada elétrica'})
    fonte = runtime.recuperar_explicacao('Por que você fez esse gesto?', turno={'id': 'consulta'})
    assert fonte.episodios[0].confirmado is confirmado
    assert fonte.episodios[0].escopo_confirmacao == 'parada elétrica'
    runtime.clock = lambda: 1002
    assert runtime.recuperar_explicacao('Por que você fez esse gesto?', turno={'id': 'consulta'}).referencia == 'ausente'


def test_escopo_eletrico_nao_substitui_nem_amplia_medida_de_giro():
    _, runtime, e = registrar(campos={'prova_rotacao': True, 'rotacao_medida_graus': 90})
    assert e['resultado'] == 'giro_relativo_confirmado'
    assert e['prova_rotacao'] is True and e['rotacao_medida_graus'] == 90
    assert e['escopo_confirmacao'] == 'PWM e parada elétrica'
    fonte = runtime.recuperar_explicacao('Por que você fez esse gesto?', turno={'id': 'consulta'})
    assert 'Não há medição de deslocamento' in realizacoes_explicacao_ocorrencia(fonte, agora=101)[0]
