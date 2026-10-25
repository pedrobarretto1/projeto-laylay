"""Preview não identifica fala; entrega observada não confirma efeito externo."""
from copy import deepcopy
import time

import pytest

from mente_laylay.memoria_mental.contexto_compartilhado import registrar_mente_curta
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada, recuperar_evidencia_da_fala
from mente_laylay.cognicao.seletor_contexto import selecionar_contexto_turno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala


CURTA = 'Acho importante terminar os exercícios, porque isso ajuda a praticar.'
LONGA = CURTA + ' Conferir cada etapa permite localizar dúvidas e acompanhar o raciocínio.' * 10


def mente_com_fala(fala, *, entrega=True):
    mente = registrar_mente_curta({}, texto_usuario='o que você acha disso?',
        resposta_ia=fala, log=lambda *_: None)
    if entrega:
        mente['registro_semantico'] = registrar_fala_observada(None,
            ocorrencia_id='observada', turno_id='origem', fala=fala,
            resultados=(), canal='texto_publicado')
    mente['turno_atual'] = classificar_modalidade_turno('como assim?')
    return mente


@pytest.mark.parametrize('fala', [CURTA, LONGA], ids=['curta', 'longa'])
def test_preview_preserva_identidade_na_selecao_e_conteudo_na_recuperacao(fala):
    mente = mente_com_fala(fala)
    antes = deepcopy(mente)
    selecao = selecionar_contexto_turno('como assim?', turno=mente['turno_atual'], mente=mente)
    item = next(i for i in selecao['selecionados'] if i['origem'] == 'ultima_fala')
    evidencia = recuperar_evidencia_da_fala('como assim?', mente)
    assert evidencia and evidencia['falas'][0]['id'] == 'observada', 'primeira fronteira: identidade perdida'
    assert item.get('ocorrencia_fala_id') == 'observada'
    assert len(item['conteudo']) <= 500 and len(mente['ultima_resposta']) <= 180
    assert evidencia['falas'][0]['fala'] == fala
    assert evidencia['autoriza_execucao'] is False and mente == antes


@pytest.mark.parametrize('fala', [CURTA, LONGA], ids=['curta', 'longa'])
def test_revisao_de_esclarecimento_rejeita_copia_integral_sem_aumentar_preview(fala):
    mente = mente_com_fala(fala)
    turno = mente['turno_atual']
    plano = {'id': turno['id'], 'texto_usuario': 'como assim?', 'requer_execucao': False, 'comandos': []}
    contrato = construir_contrato_semantico_fala('como assim?', turno=turno, plano=plano, mente=mente)
    assert 'esclarecimento' in contrato['atos']
    assert len(contrato['fala_anterior_relevante']) <= 500
    assert 'evidencia_fala_historica' not in contrato
    revisao = validar_aderencia_contrato_fala('como assim?', fala,
        contrato_fala=contrato, turno_id=turno['id'])
    assert 'esclarecimento_sem_explicacao' in revisao['problemas']


@pytest.mark.parametrize('texto', ['como assim?', 'qual sua cor preferida?'])
def test_preview_sem_entrega_nao_cria_fonte(texto):
    assert not recuperar_evidencia_da_fala(texto, mente_com_fala(LONGA, entrega=False))


def test_citacao_de_textos_iguais_conserva_ambiguidade_e_reentrega_conserva_ts():
    agora = time.time()
    registro = None
    for ident in ('primeira', 'segunda'):
        registro = registrar_fala_observada(registro, ocorrencia_id=ident,
            turno_id='origem', fala=CURTA, resultados=(), canal='texto_publicado', agora=agora)
    antes = deepcopy(registro['falas_observadas'])
    registro = registrar_fala_observada(registro, ocorrencia_id='primeira',
        turno_id='origem', fala=CURTA, resultados=(), canal='audio_reproducao_confirmada', agora=agora+1)
    assert [(f['id'], f['ts']) for f in antes] == [(f['id'], f['ts']) for f in registro['falas_observadas']]
    evidencia = recuperar_evidencia_da_fala(f'Explique "{CURTA}"', {'registro_semantico': registro}, agora=agora+2)
    assert evidencia['referencia_ambigua'] is True
    assert not recuperar_evidencia_da_fala(f'Explique "{CURTA}"', {'registro_semantico': registro}, agora=agora+901)


def runtime_com_estado_real():
    from tests.test_orquestrador_fala_registro import _runtime_de_fala
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
    runtime, antigo, voz, logs = _runtime_de_fala()
    estado = EstadoCompartilhadoRuntime(mental={**antigo.mental, 'sessao_conversa_ts': 1})
    runtime.conectar_servicos({**runtime._servicos, '_estado_compartilhado_runtime': estado,
        '_registrar_entrega_comunicativa': lambda **_: None})
    return runtime, estado, voz


def test_audio_antigo_entregue_depois_nao_substitui_referencia_recente():
    runtime, estado, voz = runtime_com_estado_real()
    runtime.falar('Primeira mensagem sobre exercícios.')
    callback_antigo = voz.falas[-1][1]['_ao_concluir_entrega']
    runtime.registrar_observador_texto_final(lambda *a, **k: True)
    runtime.falar('Segunda mensagem sobre a aula.')
    callback_antigo(True, 'Primeira mensagem sobre exercícios.')
    evidencia = recuperar_evidencia_da_fala('como assim?', dict(estado.mental))
    assert evidencia['falas'][0]['fala'] == 'Segunda mensagem sobre a aula.'
    historico = estado.mental['registro_semantico']['falas_observadas']
    assert len({f['id'] for f in historico}) == 2
    assert {f['turno_id'] for f in historico} == {'turno-1'}


def test_duas_emissoes_com_texto_igual_tem_identidade_propria_na_selecao():
    runtime, estado, voz = runtime_com_estado_real()
    runtime.registrar_observador_texto_final(lambda *a, **k: True)
    runtime.falar(CURTA)
    runtime.falar(CURTA)
    historico = estado.mental['registro_semantico']['falas_observadas']
    assert len(historico) == 2 and historico[0]['id'] != historico[1]['id']
    evidencia = recuperar_evidencia_da_fala('como assim?', dict(estado.mental))
    assert evidencia['falas'][0]['id'] == historico[1]['id']
    assert not evidencia['referencia_ambigua']


@pytest.mark.parametrize('evento', ['negada', 'conteudo_divergente', 'nova_sessao'])
def test_entrega_invalida_nao_cria_referencia_observada(evento):
    runtime, estado, voz = runtime_com_estado_real()
    runtime.falar(LONGA)
    callback = voz.falas[-1][1]['_ao_concluir_entrega']
    if evento == 'nova_sessao':
        estado.mental['sessao_conversa_ts'] = 2
    callback(evento != 'negada', 'outra fala' if evento == 'conteudo_divergente' else LONGA)
    assert not recuperar_evidencia_da_fala('como assim?', dict(estado.mental))


def test_finais_distintos_com_mesmo_preview_nao_emprestam_identidade():
    runtime, estado, voz = runtime_com_estado_real()
    runtime.registrar_observador_texto_final(lambda *a, **k: True)
    runtime.falar(LONGA + ' Primeira conclusão.')
    runtime.falar(LONGA + ' Outra conclusão.')
    mente = registrar_mente_curta(dict(estado.mental), resposta_ia=LONGA+' Outra conclusão.', log=lambda *_: None)
    evidencia = recuperar_evidencia_da_fala('como assim?', mente)
    assert evidencia and evidencia['falas'][0]['fala'].endswith('Outra conclusão.')
    assert len(evidencia['falas']) == 1


def test_aceite_da_fila_nao_substitui_referencia_ja_observada():
    runtime, estado, voz = runtime_com_estado_real()
    runtime.registrar_observador_texto_final(lambda *a, **k: True)
    runtime.falar(CURTA)
    runtime._observadores_texto_final.clear()
    runtime.falar('Proposta ainda não entregue sobre outro assunto.')
    assert recuperar_evidencia_da_fala('como assim?', dict(estado.mental))['falas'][0]['fala'] == CURTA


@pytest.mark.parametrize('mudanca', ['json', 'turno', 'texto', 'expirada'])
def test_referencia_de_consulta_nao_e_substituida_por_proposta_ou_outra_consulta(mudanca):
    from dataclasses import asdict, replace
    mente = mente_com_fala(LONGA)
    turno = mente['turno_atual']
    c = construir_contrato_semantico_fala('como assim?', turno=turno,
        plano={'id': turno['id'], 'texto_usuario': 'como assim?'}, mente=mente)
    fonte = c.get('referencia_fala_observada')
    assert fonte is not None
    if mudanca == 'json': fonte = asdict(fonte)
    elif mudanca == 'turno': fonte = replace(fonte, turno_consulta='outra-consulta')
    elif mudanca == 'texto': fonte = replace(fonte, texto_consulta='outra pergunta')
    else: fonte = replace(fonte, ts=time.time()-901)
    c['referencia_fala_observada'] = fonte
    revisao = validar_aderencia_contrato_fala('como assim?', LONGA,
        contrato_fala=c, turno_id=turno['id'])
    assert 'referencia_fala_observada_invalida' in revisao['problemas']


def test_observador_reentrante_nao_inverte_ordem_das_emissoes():
    runtime, estado, voz = runtime_com_estado_real()
    def observador(fala, *a, **k):
        if fala == 'Primeira mensagem.': runtime.falar('Segunda mensagem.')
        return True
    runtime.registrar_observador_texto_final(observador)
    runtime.falar('Primeira mensagem.')
    evidencia = recuperar_evidencia_da_fala('como assim?', dict(estado.mental))
    assert evidencia['falas'][0]['fala'] == 'Segunda mensagem.'


@pytest.mark.parametrize('campo,valor', [('canais', ['proposta']), ('ts', float('nan')),
    ('autoriza_execucao', True), ('id', 'desconhecido')])
def test_referencia_invalida_nao_se_autentica_pelo_preview(campo, valor):
    mente = mente_com_fala(LONGA)
    mente['registro_semantico']['falas_observadas'][0][campo] = valor
    assert not recuperar_evidencia_da_fala('como assim?', mente)


@pytest.mark.parametrize('texto', ['como assim?', 'como  assim?', 'como\nassim?'])
@pytest.mark.parametrize('proposta_json', [False, True])
def test_juiz_real_preserva_consulta_e_bloqueia_copia_ou_fonte_invalida(texto, proposta_json):
    from dataclasses import asdict
    from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
    mente = mente_com_fala(LONGA)
    turno = classificar_modalidade_turno(texto)
    mente['turno_atual'] = turno
    plano = {'id': turno['id'], 'texto_usuario': texto, 'comandos': [], 'requer_execucao': False}
    c = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    fonte = c.get('referencia_fala_observada')
    assert fonte is not None
    if proposta_json: c['referencia_fala_observada'] = asdict(fonte)
    plano['contrato_fala'] = c
    revisao = avaliar_qualidade_comunicacao(texto, LONGA, plano=plano)
    assert not revisao['aceita'], revisao
    assert ('referencia_fala_observada_invalida' if proposta_json else 'esclarecimento_sem_explicacao') in revisao['problemas_bloqueantes']
