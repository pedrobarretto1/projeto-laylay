"""Recusar uma resposta velha não elimina o contrato da pergunta atual."""
import json
from pathlib import Path
import pytest
from tests.test_continuidade_resposta_recente import plano_atual
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao,montar_mensagens_reparo_comunicacao

CASOS=json.loads((Path(__file__).parent/'fixtures/limites_tematicos.json').read_text(encoding='utf8'))

@pytest.mark.parametrize('caso',CASOS,ids=lambda c:c['id'])
def test_reuso_legitimamente_recusado_preserva_atos_e_limites_no_reparo(caso):
    texto=caso['entrada']
    anterior=tuple(m['content'] for m in caso['historico'] if m['role']=='assistant')
    p=plano_atual(texto,anterior[-3:])
    fala=' '.join(caso['propostas'][0]['suporte_proposicoes'][0]['partes'])
    a=avaliar_qualidade_comunicacao(texto,fala,plano=p)
    assert a['problemas_bloqueantes']==['resposta_repetida_literal'],a
    from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
    contrato=validar_aderencia_contrato_fala(texto,fala,contrato_fala=p['contrato_fala'],turno_id=p['id'])['contrato_reparo']
    assert a['contrato_reparo'].get('estrategia')==contrato['estrategia'],a
    assert a['contrato_reparo'].get('atos_obrigatorios')==contrato['atos_obrigatorios'],a
    assert a['contrato_reparo'].get('sequencia')==contrato['sequencia'],a
    pacote=montar_mensagens_reparo_comunicacao(texto,fala,a,mensagens=caso['historico'])
    payload=json.loads(pacote[-1]['content'])
    assert payload['mensagem_atual']==texto and payload['contrato_de_reparo']['max_frases']==contrato['max_frases']
    assert not payload['contrato_de_reparo']['autoriza_execucao']
    assert fala not in json.dumps(payload,ensure_ascii=False)

@pytest.mark.parametrize('texto',[
    'Qual nome você escolheria para o projeto?',
    'Estou feliz. Você acha melhor começar pelos arquivos ou pela música?',
])
def test_preservacao_independe_do_tema_sem_converter_contexto_em_acao(texto):
    anterior='A conversa contém uma resposta anterior que não atende ao pedido atual.'
    p=plano_atual(texto,(anterior,))
    a=avaliar_qualidade_comunicacao(texto,anterior,plano=p)
    assert 'resposta_repetida_literal' in a['problemas_bloqueantes']
    assert a['contrato_reparo'].get('atos_obrigatorios')==p['contrato_fala']['atos']
    assert not a['contrato_reparo']['autoriza_execucao']
