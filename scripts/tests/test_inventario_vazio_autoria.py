"""Atos discursivos não são fontes; inventário vazio precisa permanecer vazio."""
import json

import pytest

from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt


def pacote(referencias=()):
    return exigir_suporte_no_pacote_autoral(PacotePrompt(mensagens=(
        {'role':'system','content':'Você é Laylay.'},
        {'role':'user','content':'Vamos inventar uma história juntos?'})),referencias_disponiveis=referencias)


def test_sem_fontes_disponiveis_schema_nao_oferece_espaco_para_ids_inventados():
    p=pacote()
    esquema=p.contrato_saida.response_format['json_schema']['schema']
    fontes=esquema['properties']['suporte_proposicoes']['items']['properties']['fontes']
    assert fontes['maxItems']==0
    assert 'suporte_proposicoes' in esquema['required']


@pytest.mark.parametrize('referencia',['conversa','pergunta','opiniao','arquivo:inventado','https://inventado.example/fonte'])
def test_codec_sem_inventario_recusa_proposta_que_inventa_referencia(referencia):
    proposta={'suporte_proposicoes':[{'texto':'Eu inventaria um espelho que guarda lembranças.','fontes':[referencia]}]}
    with pytest.raises(ValueError,match='inventario|referencia'):
        pacote().contrato_saida.decodificar_json(json.dumps(proposta))


@pytest.mark.parametrize('texto',[
    'Oi! Vamos conversar.',
    'Que história você gostaria de criar?',
    'Eu inventaria um espelho que guarda lembranças.',
    'A biblioteca flutuaria entre duas nuvens, dentro dessa história.',
])
def test_sem_referencia_nao_proibe_autoria_social_pergunta_ou_ficcao(texto):
    p=pacote()
    resultado=p.contrato_saida.decodificar_json(json.dumps({'suporte_proposicoes':[{'texto':texto,'fontes':[]}]}))
    assert resultado['fala']==texto
    assert resultado['suporte_proposicoes'][0]['fontes']==[]
    assert 'semantica_verificada' not in resultado
    assert 'autoriza_execucao' not in resultado


def test_inventario_real_continua_exigindo_id_oferecido_ou_ausencia_explicita():
    p=pacote(('fonte-local:123',))
    codec=p.contrato_saida
    valido={'suporte_proposicoes':[{'texto':'Trecho proposto.','fontes':['fonte-local:123']}]}
    assert codec.decodificar_json(json.dumps(valido))['suporte_proposicoes'][0]['fontes']==['fonte-local:123']
    invalido={'suporte_proposicoes':[{'texto':'Trecho proposto.','fontes':['pergunta']}]}
    with pytest.raises(ValueError):codec.decodificar_json(json.dumps(invalido))
    sem_declaracao={'suporte_proposicoes':[{'texto':'Trecho proposto.','fontes':[]}]}
    with pytest.raises(ValueError):codec.decodificar_json(json.dumps(sem_declaracao))


def test_reuso_do_codec_preserva_obrigacao_autoral_e_restricao_de_referencias():
    p=pacote()
    novamente=exigir_suporte_no_pacote_autoral(p)
    assert novamente is p
    assert p.contrato_saida.response_format['json_schema']['schema']['properties']['suporte_proposicoes']['items']['properties']['fontes']['maxItems']==0
