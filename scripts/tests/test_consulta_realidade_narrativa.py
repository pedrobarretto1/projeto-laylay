"""Perguntar pelo estatuto de uma história não pede mais metáforas."""
import json,time
from copy import deepcopy

import pytest

from scripts.tests.test_finalidade_ficcional_revisao import preparar
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao

ORIGEM='Estamos criando uma história em que uma biblioteca tem um gato bibliotecário e um relógio que apaga lembranças.'
FICCAO='Na história, um espelho guarda as lembranças do gato.'
PERGUNTA='Isso aconteceu de verdade no meu computador ou é parte da história?'
ERRADA='O que importa não é o que aconteceu no seu computador, mas o que você sente. Talvez faça parte da história.'


def plano_consulta(texto=PERGUNTA):
    anterior=preparar(ORIGEM,fala=FICCAO)
    estado={'ultima_entrada':ORIGEM,'ultima_entrada_ts':time.time(),
        'ultima_resposta':FICCAO,'contrato_fala_atual':anterior['contrato_fala']}
    return preparar(texto,mente=estado,fala=ERRADA)


def test_moldura_narrativa_explicita_na_declaracao_tambem_tem_owner():
    p=preparar(ORIGEM,fala=FICCAO)
    assert p['contrato_fala'].get('criacao_ficcional') is not None


@pytest.mark.parametrize('texto',[PERGUNTA,'Isso é real ou ficção?',
    'Aconteceu de verdade ou foi só uma história?',
    'Essa cena aconteceu na realidade ou faz parte da ficção?'])
def test_consulta_de_realidade_resolve_o_escopo_sem_inventar_receipt(texto):
    p=plano_consulta(texto)
    c=p['contrato_fala']
    assert c.get('consulta_realidade_narrativa') is not None
    assert not c.get('criacao_ficcional')
    a=avaliar_qualidade_comunicacao(texto,ERRADA,plano=p)
    assert a['aceita'] is False
    assert 'escopo_narrativo_nao_respondido' in a['problemas_bloqueantes']
    fonte=c['consulta_realidade_narrativa']
    assert fonte.autoriza_execucao is False and fonte.pode_confirmar_fato_externo is False
    for fala in fonte.realizacoes():
        q=avaliar_qualidade_comunicacao(texto,fala,plano=p)
        assert q['aceita'] and not q.get('problemas_bloqueantes')
        final=verificar_fala_turno(fala,plano=p)
        assert final['aceita'] and final['fala']==fala
        assert not p['comandos'] and not p['autoriza_execucao']


@pytest.mark.parametrize('texto',[
    'Isso abriu de verdade a calculadora?',
    'Como essa tecnologia funciona na realidade?',
    'Na história, o gato pergunta se isso é real ou ficção.',
    'Abre a calculadora e diga se isso é real ou ficção.',
    'Isso é real ou ficção? Também explica o motor elétrico.',
])
def test_consulta_independente_citacao_ou_efeito_nao_herda_fonte_narrativa(texto):
    p=plano_consulta(texto)
    assert p['contrato_fala'].get('consulta_realidade_narrativa') is None


@pytest.mark.parametrize('alteracao',['expirada','outro_texto','json','sem_anterior'])
def test_consulta_nao_e_provada_por_contexto_sem_identidade(alteracao):
    anterior=preparar(ORIGEM,fala=FICCAO)
    estado={'ultima_entrada':ORIGEM,'ultima_entrada_ts':time.time(),
        'ultima_resposta':FICCAO,'contrato_fala_atual':anterior['contrato_fala']}
    if alteracao=='expirada':estado['ultima_entrada_ts']-=500
    elif alteracao=='outro_texto':estado['ultima_entrada']='Oi, como vai?'
    elif alteracao=='json':estado['contrato_fala_atual']['criacao_ficcional']={'ficcao':True}
    else:estado['contrato_fala_atual']={}
    p=preparar(PERGUNTA,mente=estado,fala=ERRADA)
    assert not p['contrato_fala'].get('consulta_realidade_narrativa')


def test_fonte_narrativa_de_outra_ocorrencia_nao_aprova_resposta():
    p=plano_consulta()
    fonte=p['contrato_fala'].get('consulta_realidade_narrativa')
    assert fonte is not None
    fala=fonte.realizacoes()[0]
    outro=deepcopy(p);outro['id']+=1
    q=avaliar_qualidade_comunicacao(PERGUNTA,fala,plano=outro)
    assert q.get('estado')!='escopo_narrativo_conferido'


def test_autoria_ficcional_negocia_a_moldura_que_o_revisor_exige():
    from mente_laylay.autonomia.contexto_resposta_ia import negociar_autoria_com_fontes
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    p=preparar(ORIGEM,fala=FICCAO)
    pacote=negociar_autoria_com_fontes(PacotePrompt(({'role':'user','content':ORIGEM},)),None,plano_autoria=p)
    codec=pacote.contrato_saida
    with pytest.raises(ValueError):
        codec.decodificar_json(json.dumps({'suporte_proposicoes':[
            {'texto':'Um espelho guarda as lembranças do gato.','fontes':[]}]}))
    d=codec.decodificar_json(json.dumps({'suporte_proposicoes':[{'texto':FICCAO,'fontes':[]}]}))
    assert d['fala']==FICCAO
    assert 'Na história,' in str(pacote.mensagens)


@pytest.mark.parametrize('unidades',[[False],[{}],[{'texto':False,'fontes':[]}],
    [{'texto':'Na história, abri o navegador de verdade.','fontes':[]}],
    [{'texto':'Na história, algo acontece.','fontes':['fonte:inventada']}],
    [{'texto':'Na história, algo acontece.','fontes':[]}, {'texto':'Depois algo mudou.','fontes':[]}],
])
def test_moldura_nao_admite_proposta_malformada_referencia_ou_efeito_real(unidades):
    from mente_laylay.autonomia.contexto_resposta_ia import negociar_autoria_com_fontes
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    p=preparar(ORIGEM,fala=FICCAO)
    pacote=negociar_autoria_com_fontes(PacotePrompt(({'role':'user','content':ORIGEM},)),None,plano_autoria=p)
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps({'suporte_proposicoes':unidades}))


def test_moldura_preserva_autoria_longa_integral_e_renegociacao_do_codec():
    from mente_laylay.autonomia.contexto_resposta_ia import negociar_autoria_com_fontes
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
    p=preparar(ORIGEM,fala=FICCAO)
    pacote=negociar_autoria_com_fontes(PacotePrompt(({'role':'user','content':ORIGEM},)),None,plano_autoria=p)
    assert exigir_suporte_no_pacote_autoral(pacote) is pacote
    longa='Na história, '+('o gato escolhe um livro e lê uma carta. '*25).strip()
    d=pacote.contrato_saida.decodificar_json(json.dumps({'suporte_proposicoes':[{'texto':longa,'fontes':[]}]}))
    assert d['fala']==longa
