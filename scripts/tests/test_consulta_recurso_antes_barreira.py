"""Fonte canônica de leitura vence barreira de mutação sem autorizar escrita."""
from types import SimpleNamespace
import pytest

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno, turno_tem_veto_execucao


def runtime(candidato, texto='quantas músicas tem na playlist rock?', veto=False):
    turno = classificar_modalidade_turno(texto)
    if veto: turno['veto_execucao_operacional'] = True
    chamados = []
    ns = {'_estado_compartilhado_runtime':SimpleNamespace(mental={'turno_atual':turno}),
          '_resolver_consulta_recurso_local':lambda _: candidato,
          'executar_intencao':lambda pedido, entrada: chamados.append((pedido, entrada)) or True}
    return ComandosImediatosRuntime(namespace_getter=lambda:ns, loop_getter=lambda:None), chamados


@pytest.mark.parametrize('intent', ['PLAYLIST_LIST', 'PEOPLE_LIST', 'FILE_READ'])
def test_consulta_canonica_somente_leitura_nao_exige_permissao_de_mutacao(intent):
    pedido = {'intent':intent,'params':{'alvo':'recurso_resolvido'}}
    r, chamados = runtime(pedido)
    assert r.processar_prioritarios('quantas músicas tem na playlist rock?')
    assert chamados == [(pedido, 'quantas músicas tem na playlist rock?')]


@pytest.mark.parametrize('candidato', [None, {'destino':'ia'},
    {'intent':'PLAYLIST_DELETE','params':{'nome_playlist':'rock'}},
    {'intent':'APP_OPEN','params':{'nome_app':'Opera'}}])
def test_resolvedor_nao_pode_promover_outra_operacao_a_leitura(candidato):
    r, chamados = runtime(candidato)
    assert not r.processar_prioritarios('quantas músicas tem na playlist rock?')
    assert chamados == []


def test_veto_explicito_nao_e_superado_pelo_catalogo_de_leitura():
    r, chamados = runtime({'intent':'PLAYLIST_LIST','params':{'nome_playlist':'rock'}}, veto=True)
    assert not r.processar_prioritarios('quantas músicas tem na playlist rock?')
    assert chamados == []


@pytest.mark.parametrize('texto', ['quantas músicas tem na playlist rock?', 'quais músicas tem em rock?'])
def test_guard_musical_nao_converte_consulta_em_veto_nem_permissao_mutante(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno['autoriza_execucao'] is False
    assert not turno_tem_veto_execucao(turno)
    assert turno['natureza_acao'] == 'consulta'


@pytest.mark.parametrize('falha', ['executor_ausente', 'recusa', 'excecao'])
def test_falha_de_leitura_nao_consumida_como_sucesso(falha):
    r, chamados = runtime({'intent':'PLAYLIST_LIST','params':{'nome_playlist':'rock'}})
    ns = r.namespace_getter()
    if falha == 'executor_ausente': ns.pop('executar_intencao')
    elif falha == 'recusa': ns['executar_intencao'] = lambda *a: False
    else:
        def falhar(*a): raise RuntimeError('falha controlada')
        ns['executar_intencao'] = falhar
    assert not r.processar_prioritarios('quantas músicas tem na playlist rock?')
    assert chamados == []


@pytest.mark.parametrize('intent, permitido', [
    ('LAYLAY_PLAYLIST_LIST', True),
    ('LAYLAY_PLAYLIST_PLAY', False),
    ('LAYLAY_PLAYLIST_COPY', False),
])
def test_proposta_de_curadoria_nao_concede_autoridade_a_pergunta(intent, permitido):
    texto = 'quais músicas tem na sua primeira playlist?'
    r, chamados = runtime(None, texto)
    pedido = {'intent': intent, 'params': {'ordinal': 1}}
    r.namespace_getter()['detectar_intencao_deterministica'] = lambda _: pedido
    assert r.processar_prioritarios(texto) is permitido
    assert chamados == ([(pedido, texto)] if permitido else [])


@pytest.mark.parametrize('porta, intent', [
    ('email', 'EMAIL_SEND'), ('notificacao', 'EMAIL_MODIFY'),
    ('deterministico', 'SEARCH'), ('natural', 'APP_OPEN'),
])
def test_consulta_sem_mutacao_nao_alcanca_portas_operacionais(porta, intent):
    texto = 'quais músicas tem na sua primeira playlist?'
    r, chamados = runtime(None, texto)
    ns = r.namespace_getter()
    pedido = {'intent': intent, 'params': {}}
    if porta == 'email': ns['_email_detectar'] = lambda _: pedido
    elif porta == 'notificacao':
        ns['_central_notificacoes_runtime'] = SimpleNamespace(detectar=lambda _: pedido)
    elif porta == 'deterministico': ns['detectar_intencao_deterministica'] = lambda _: pedido
    else: ns['resolver_comando_natural'] = lambda *a: (pedido, 'teste_adversarial')
    assert not r.processar_prioritarios(texto)
    assert chamados == []
