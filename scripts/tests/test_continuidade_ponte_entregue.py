"""Retomada limitada ao canal e a pares entregues, sem promover fala a prova."""
import hashlib
import json
from pathlib import Path
import pytest
from tests.test_conclusao_resposta_textual import carregar

def journal(base,projeto,*,pronta=None,saida=None,entrada=None,nome='20261030T002918Z-e1836211'):
    pasta=base/nome;pasta.mkdir(parents=True)
    r=[{'tipo':'pronta','interlocutor':'chatgpt','acoes_externas':False,
        'modo':'composicao_instalada_headless_isolada','projeto':str(projeto),**(pronta or {})},
       {'tipo':'entrada','origem':'chatgpt','dados':{'tipo':'mensagem','id':'x',
        'texto':'Nossa conversa tratava de identidade e memória.',**(entrada or {})}},
       {'tipo':'resposta','id':'x','origem':'laylay','interlocutor':'chatgpt',
        'acoes_externas':False,'texto':'Podemos mudar mantendo os limites claros.',**(saida or {})}]
    (pasta/'conversa.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in r)+'\n',encoding='utf8')
    return pasta,r

@pytest.fixture
def caminhos(tmp_path):
    projeto=tmp_path/'laylay';projeto.mkdir();(projeto/'laylay.py').write_text('pass',encoding='utf8')
    base=tmp_path/'sessoes';base.mkdir();return base,base/'atual',projeto

def test_primeira_sessao_nao_ganha_lembrancas_ou_temas_fixos(caminhos):
    m=carregar('continuidade_ponte')
    mensagens,fontes=m.carregar_continuidade(*caminhos)
    assert not mensagens and not fontes
    assert 'Não há registros anteriores' in m.contexto_reencontro(fontes)
    assert 'perdão' not in m.contexto_reencontro(fontes)

def test_par_integro_entregue_chega_ao_estado_com_proveniencia(caminhos):
    base,atual,projeto=caminhos
    _,r=journal(base,projeto)
    m=carregar('continuidade_ponte');historico,fontes=m.carregar_continuidade(*caminhos)
    assert historico==[{'role':'user','content':r[1]['dados']['texto']},
                      {'role':'assistant','content':r[2]['texto']}]
    assert fontes[0]['id']=='x' and not fontes[0]['autoriza_execucao'] and not fontes[0]['comprova_fato']
    assert 'ChatGPT retornou' in m.contexto_reencontro(fontes)

@pytest.mark.parametrize('pronta,saida,entrada',[
    ({'interlocutor':'pedro'},{},{}),
    ({'projeto':'outro-projeto'},{},{}),
    ({},{'interlocutor':'pedro'},{}),
    ({},{'tipo':'erro','codigo':'falha_modelo'},{}),
    ({},{'degradada':True},{}),
    ({},{'resposta_degradada':True},{}),
    ({},{'acoes_externas':True},{}),
    ({},{'id':'outro'},{}),
    ({},{},{'tipo':'comando'}),
])
def test_identidade_alheia_falha_e_resultado_nao_entregue_nao_viram_memoria(caminhos,pronta,saida,entrada):
    journal(caminhos[0],caminhos[2],pronta=pronta,saida=saida,entrada=entrada)
    assert carregar('continuidade_ponte').carregar_continuidade(*caminhos)==([],[])

def test_journal_antigo_exige_manifesto_da_composicao(caminhos):
    pasta,r=journal(caminhos[0],caminhos[2]);del r[0]['projeto']
    (pasta/'conversa.jsonl').write_text('\n'.join(json.dumps(x) for x in r),encoding='utf8')
    m=carregar('continuidade_ponte')
    assert m.carregar_continuidade(*caminhos)==([],[])
    (pasta/'fontes_sha256.json').write_text(json.dumps({'laylay.py':hashlib.sha256(
        (caminhos[2]/'laylay.py').read_bytes()).hexdigest()}),encoding='utf8')
    assert len(m.carregar_continuidade(*caminhos)[1])==1

def test_limite_preserva_pares_e_ordem_sem_cortar_negacoes(caminhos):
    for i in range(8):
        journal(caminhos[0],caminhos[2],nome=f'20261030T00{i:02}18Z-e1836211',
            entrada={'texto':f'Não autorizo ações. Tema {i}.'})
    mensagens,fontes=carregar('continuidade_ponte').carregar_continuidade(*caminhos)
    assert len(mensagens)==12 and len(fontes)==6
    assert mensagens[0]['content']=='Não autorizo ações. Tema 2.'
    assert mensagens[-2]['content']=='Não autorizo ações. Tema 7.'
