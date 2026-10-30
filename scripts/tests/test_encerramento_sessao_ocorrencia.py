"""Sessão pode terminar sem invalidar a ocorrência que deve concluir a despedida."""
import pytest

from mente_laylay.autonomia.pre_fluxo_contextual import processar_encerramento_conversa
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.contratos_turno import ContratoOcorrenciaTurno, ContratoPropostaPrincipal
from mente_laylay.cognicao.decisao_turno import motivo_divergencia_ocorrencia_principal
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
from mente_laylay.memoria_mental.encerramento_assunto import classificar_encerramento_assunto
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada


def preparar(texto='boa noite, vou dormir'):
    turno = classificar_modalidade_turno(texto)
    turno['encerramento_assunto'] = classificar_encerramento_assunto(texto)
    retrato, _ = construir_retrato_turno(texto, turno=turno, mente={}, contexto_perceptivo={})
    turno['retrato_id'] = retrato['id']
    plano = planejar_turno(texto, turno=turno, mente={})
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente={})
    turno['contrato_fala'] = plano['contrato_fala'] = contrato
    mental = {'ultima_entrada': texto, 'ultima_entrada_ts': 100., 'turno_atual': turno,
        'plano_turno_atual': plano, 'contrato_fala_atual': contrato, 'retrato_turno_atual': retrato,
        'ultima_resposta': 'Antiga conversa sobre coxinha.',
        'pendencia_atual': {'id': 'antiga', 'status': 'ativa'},
        'pendencia_acao_canonica': {'id': 'antiga', 'status': 'ativa'},
        'ultima_acao_intent': 'DELETE_ITEM', 'ultima_acao_confirmada': True,
        'foco_operacional_alvo': 'arquivo antigo', 'memoria_fato_importante': 'Pedro estuda',
        'registro_semantico': registrar_fala_observada(None, ocorrencia_id='antiga', turno_id='anterior',
            fala='Antiga conversa sobre coxinha.', resultados=(), canal='texto_publicado')}
    estado = EstadoCompartilhadoRuntime(mental=mental,
        conversacional={'ultimo_topico_conversa': 'coxinha', 'current_emotion': 'alegre'},
        memoria_conversa={'messages': [{'role':'system','content':'identidade'},
            {'role':'user','content':'qual a receita?'}, {'role':'assistant','content':'Use farinha.'}]})
    runtime = EstadoContextoRuntime(namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado)
    return estado, runtime


def conferir_ocorrencia(mental, texto, tid):
    proposta = ContratoPropostaPrincipal(tid, texto, '{"fala":"Até mais!","comandos":[]}')
    return motivo_divergencia_ocorrencia_principal(proposta,
        turno=mental.get('turno_atual'), plano=mental.get('plano_turno_atual'), retrato=mental.get('retrato_turno_atual'))


@pytest.mark.parametrize('texto', ['boa noite, vou dormir', 'tchau', 'por hoje é só', 'até mais, Lay'])
def test_pre_fluxo_limpa_sessao_sem_apagar_ocorrencia_que_ainda_deve_responder(texto):
    estado, runtime = preparar(texto)
    antes = estado.snapshot()['mental']
    tid = antes['turno_atual']['id']
    assert not conferir_ocorrencia(antes, texto, tid)
    falas = []
    assert processar_encerramento_conversa({'_renovar_sessao_conversa': runtime.renovar_sessao_conversa,
        'falar_com_lipsync': lambda *a: falas.append(a)}, texto, emitir_fala=False) == (False, 'encerramento_conversa')
    depois = estado.snapshot()['mental']
    assert depois['sessao_conversa_ativa'] is False
    assert depois['turno_atual'] == antes['turno_atual'], 'primeira fronteira: reset apaga o turno antes da autoria'
    assert depois['plano_turno_atual'] == antes['plano_turno_atual']
    assert depois['contrato_fala_atual'] == antes['contrato_fala_atual']
    assert depois['retrato_turno_atual'] == antes['retrato_turno_atual']
    assert not conferir_ocorrencia(depois, texto, tid)
    assert conferir_ocorrencia(depois, texto, 'outra-ocorrencia')
    assert not depois['ultima_resposta'] and not depois['pendencia_atual']
    assert not depois['pendencia_acao_canonica'] and not depois['ultima_acao_intent']
    assert not depois['ultima_acao_confirmada'] and not depois['foco_operacional_alvo']
    assert depois['memoria_fato_importante'] == 'Pedro estuda'
    assert estado.snapshot()['memoria_conversa']['messages'] == [{'role':'system','content':'identidade'}]
    assert not falas


@pytest.mark.parametrize('mutacao', ['turno', 'plano', 'retrato', 'texto', 'contrato', 'operacional',
    'comandos', 'evento', 'concluido', 'decisao_operacional', 'sem_encerramento'])
def test_renovacao_nao_reanima_frame_antigo_ou_operacional(mutacao):
    estado, runtime = preparar()
    mental = estado.snapshot()['mental']
    if mutacao in {'turno', 'plano', 'retrato'}:
        chave = {'turno':'turno_atual', 'plano':'plano_turno_atual', 'retrato':'retrato_turno_atual'}[mutacao]
        mental[chave]['id'] = 'outro'
    elif mutacao == 'texto': mental['ultima_entrada'] = 'abre o navegador'
    elif mutacao == 'contrato': mental['contrato_fala_atual']['turno_id'] = 'outro'
    elif mutacao == 'operacional': mental['turno_atual']['autoriza_execucao'] = True
    elif mutacao == 'comandos': mental['plano_turno_atual']['comandos'] = [{'intent':'DELETE_ITEM'}]
    elif mutacao == 'evento': mental['turno_atual']['natureza_entrada'] = 'evento'
    elif mutacao == 'concluido': mental['plano_turno_atual']['fase'] = 'executado'
    elif mutacao == 'decisao_operacional': mental['plano_turno_atual']['decisao_turno']['permite_acao'] = True
    else: mental['turno_atual']['encerramento_assunto'] = ''
    estado.substituir('mental', mental)
    runtime.renovar_sessao_conversa('despedida_usuario', False)
    depois = estado.snapshot()['mental']
    assert not depois['turno_atual'] and not depois['plano_turno_atual']
    assert not depois['contrato_fala_atual']
    assert not depois['pendencia_atual']


@pytest.mark.parametrize('motivo,ativa', [('inicio_programa',True), ('inatividade',True),
    ('desativacao_chat',False), ('nova_sessao',True)])
def test_outros_resets_continuam_invalidando_ocorrencia_anterior(motivo, ativa):
    estado, runtime = preparar()
    runtime.renovar_sessao_conversa(motivo, ativa)
    assert not estado.snapshot()['mental']['turno_atual']


def test_limpeza_de_sessao_publica_os_tres_dominios_juntos(monkeypatch):
    estado, runtime = preparar()
    transacoes = []
    original = estado.atualizar_dominios
    def transacao(dominios, atualizar):
        transacoes.append(tuple(dominios))
        return original(dominios, atualizar)
    monkeypatch.setattr(estado, 'atualizar_dominios', transacao)
    runtime.renovar_sessao_conversa('despedida_usuario', False)
    assert transacoes == [('mental', 'conversacional', 'memoria_conversa')]


def test_frame_trocado_antes_da_transacao_nao_e_sobrescrito_por_snapshot_antigo(monkeypatch):
    estado, runtime = preparar()
    antigo = estado.snapshot()['mental']
    novo_estado, _ = preparar('tchau')
    novo = novo_estado.snapshot()['mental']
    original = estado.atualizar_dominios
    def transacao(dominios, atualizar):
        estado.substituir('mental', novo)
        return original(dominios, atualizar)
    monkeypatch.setattr(estado, 'atualizar_dominios', transacao)
    runtime.renovar_sessao_conversa('despedida_usuario', False)
    depois = estado.snapshot()['mental']
    assert depois['turno_atual']['id'] == novo['turno_atual']['id']
    assert not conferir_ocorrencia(depois, 'tchau', novo['turno_atual']['id'])
    assert conferir_ocorrencia(depois, 'boa noite, vou dormir', antigo['turno_atual']['id'])


def test_reset_repetido_nao_cria_identidade_nova_e_conclusao_nao_e_reanimada():
    estado, runtime = preparar('tchau')
    original = estado.snapshot()['mental']['turno_atual']
    runtime.renovar_sessao_conversa('despedida_usuario', False)
    runtime.renovar_sessao_conversa('despedida_usuario', False)
    assert estado.snapshot()['mental']['turno_atual'] == original
    estado.atualizar('mental', lambda atual: {**atual, 'plano_turno_atual': {
        **atual['plano_turno_atual'], 'fase': 'executado'}})
    runtime.renovar_sessao_conversa('despedida_usuario', False)
    assert not estado.snapshot()['mental']['turno_atual']


def test_ocorrencia_proposta_ou_estrangeira_nao_escapa_pela_api_pura():
    from mente_laylay.memoria_mental.sessao_conversa import renovar_contexto_sessao
    estado, _ = preparar('tchau')
    original = estado.snapshot()['mental']
    for ocorrencia in ({'turno_id':original['turno_atual']['id'], 'texto_usuario':'tchau'},
                       ContratoOcorrenciaTurno('outro', 'tchau')):
        depois, _, _ = renovar_contexto_sessao(original, {}, [], motivo='despedida_usuario',
            ativa=False, ocorrencia_em_conclusao=ocorrencia)
        assert not depois['turno_atual']


def test_api_pura_sem_ocorrencia_explicita_mantem_limpeza_integral():
    from mente_laylay.memoria_mental.sessao_conversa import renovar_contexto_sessao
    estado, _ = preparar('tchau')
    depois, _, _ = renovar_contexto_sessao(estado.snapshot()['mental'], {}, [],
        motivo='despedida_usuario', ativa=False)
    assert not depois['turno_atual'] and not depois['plano_turno_atual']
