"""Âncoras, fidelidade no fragmento e inferência livre são provas diferentes."""
from copy import deepcopy
from itertools import permutations, product
import json

import pytest

from scripts.analises.sonda_fidelidade_premissas import (
    painel, pedido_publico, proposta_de_controle, conferir_ancoras,
    conferir_fidelidade, conferir_revisor,
)


@pytest.mark.parametrize('caso', painel(), ids=lambda c: c['id'])
def test_ancoras_e_fonte_integrais_nao_provam_os_papeis_ou_o_escopo(caso):
    fiel = proposta_de_controle(caso)
    troca = proposta_de_controle(caso, trocar=True)
    assert conferir_ancoras(caso, fiel) and conferir_ancoras(caso, troca)
    assert set(fiel[p] for p in ('atributo','entidade','valor')) == set(troca[p] for p in ('atributo','entidade','valor'))
    # A fonte inteira e todas as âncoras são iguais; só os papéis mudaram.
    assert fiel['fonte_integral'] == troca['fonte_integral']
    assert conferir_fidelidade(caso, troca)['derivacao'] is None
    controle = conferir_fidelidade(caso, fiel)
    assert (controle['derivacao'] is not None) is caso['fragmento_esperado']
    assert controle['prova_semantica_livre'] is controle['pertinencia_verificada'] is False
    assert controle['pode_confirmar_fato_externo'] is controle['autoriza_execucao'] is False
    revisao = conferir_revisor(caso, troca)['revisao']
    assert revisao['proposicoes'][0]['estado'] == 'apoio_semantico_pendente'
    assert revisao['semantica_verificada'] is revisao['prova_implicacao'] is revisao['autoriza_execucao'] is False


@pytest.mark.parametrize('caso', [c for c in painel() if c['fragmento_esperado']], ids=lambda c: c['id'])
def test_owner_consegue_refutar_todas_as_permutacoes_sem_confiar_no_parecer(caso):
    proposta = proposta_de_controle(caso)
    corretos = tuple(proposta[k] for k in ('atributo','entidade','valor'))
    for arranjo in permutations(corretos):
        candidato = {**proposta, **dict(zip(('atributo','entidade','valor'),arranjo)),
            'semantica_verificada':True,'autoriza_execucao':True,'certificado':'autoatribuido'}
        assert conferir_ancoras(caso,candidato)
        conferencia = conferir_fidelidade(caso,candidato)
        assert (conferencia['derivacao'] is not None) is (arranjo == corretos)
        assert conferencia['autoriza_execucao'] is False
    revisao = conferir_revisor(caso,proposta)['revisao']
    assert revisao['proposicoes'][0]['estado'] == 'parafrase_estrutural_conferida'


@pytest.mark.parametrize('alteracao', ['hash','fonte','id','ancora','duplicada'])
def test_snapshots_estrangeiros_ou_ancoras_invalidas_nao_validam_fidelidade(alteracao):
    caso = painel()[0]
    p = proposta_de_controle(caso)
    if alteracao == 'hash': p['fonte_sha256'] = '0' * 64
    elif alteracao == 'fonte': p['fonte_integral'] += ' Só no ensaio.'
    elif alteracao == 'id': p['id'] = 'outra'
    elif alteracao == 'ancora': p['entidade'] = 'a99'
    else: p['entidade'] = p['atributo']
    assert not conferir_ancoras(caso,p)
    assert conferir_fidelidade(caso,p)['derivacao'] is None


def test_mudanca_de_conteudo_invalida_a_proposta_ancorada_anterior():
    caso = painel()[0]
    proposta = proposta_de_controle(caso)
    alterado = deepcopy(caso)
    alterado['fonte'] = caso['fonte'].replace('íntegro','alterado')
    assert not conferir_ancoras(alterado,proposta)


def test_painel_e_reserva_nao_expoem_resultado_esperado_ao_modelo():
    casos = painel()
    assert len(casos) == 27 and sum(c['reserva'] for c in casos) == 9
    assert sum(c['fragmento_esperado'] for c in casos) == 9
    assert all(set(c) == {'id','fonte','ancoras'} for c in pedido_publico(casos))
    def entidade(c):
        return next(a['texto'] for a in c['ancoras'] if a['id'] == c['papeis_controle']['entidade'])
    entidades_base = {entidade(c) for c in casos if not c['reserva']}
    entidades_reserva = {entidade(c) for c in casos if c['reserva']}
    assert not entidades_base.intersection(entidades_reserva)


def test_termo_opaco_sobre_autorizacao_nao_vira_concessao_operacional():
    caso = next(c for c in painel() if c['tipo_controle'] == 'integral' and 'não concedida' in c['fonte'])
    conferencia = conferir_fidelidade(caso,proposta_de_controle(caso))
    assert conferencia['derivacao'] and conferencia['autoriza_execucao'] is False


def test_schema_da_sonda_nao_promete_combinacao_que_validator_recusa():
    from scripts.analises.sonda_fidelidade_premissas import criar_contrato_analise
    caso = painel()[0]
    codec = criar_contrato_analise([caso])
    item = codec.response_format['json_schema']['schema']['properties']['analises']['items']
    prometidas, recusadas = [], []
    # Enumeração exaustiva do subconjunto usado pelo schema da sonda.
    for ramo in item.get('anyOf', [item]):
        propriedades = ramo['properties']
        chaves = list(propriedades)
        for valores in product(*(propriedades[k]['enum'] for k in chaves)):
            proposta = dict(zip(chaves,valores))
            prometidas.append(proposta)
            try: codec.decodificar_json(json.dumps({'analises':[proposta]}))
            except ValueError: recusadas.append(proposta)
    assert not recusadas, 'primeira fronteira: schema promete combinações entre estado e papéis que o host recusa'
    assert len(prometidas) == 7  # seis permutações válidas em forma e um limite sem papéis


def test_schema_conserva_todas_as_permutacoes_sem_escolher_semantica_pelo_modelo():
    from scripts.analises.sonda_fidelidade_premissas import criar_contrato_analise
    caso = painel()[0]
    codec = criar_contrato_analise([caso])
    for ids in permutations(['a0','a1','a2']):
        p = {'id':caso['id'], 'estado':'atribuicao_integral', **dict(zip(('atributo','entidade','valor'),ids))}
        assert codec.decodificar_json(json.dumps({'analises':[p]}))['analises'] == [p]
    p = {'id':caso['id'],'estado':'fora_fragmento','atributo':None,'entidade':None,'valor':None}
    assert codec.decodificar_json(json.dumps({'analises':[p]}))['analises'] == [p]
