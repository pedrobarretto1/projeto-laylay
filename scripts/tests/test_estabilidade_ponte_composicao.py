"""Construtor real do adaptador + root instalado; HTTP fixo e perfil auditado."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import pytest
from tests.test_resultado_perifrastico_composicao import CODIGO,proposta
from tests.instalacao_privada import isolar_base_do_codigo

RAIZ=Path(__file__).resolve().parents[2]
PONTE=Path('C:/Users/pbarr/Documents/Codex/2026-10-28/ch/outputs/ponte_laylay')
BASE=isolar_base_do_codigo(CODIGO)
CONSTRUTOR='''
sys.path.insert(0,casos['ponte'])
from runtime_laylay import SessaoLaylay
from ponte_laylay import PonteConversa
from continuidade_ponte import carregar_continuidade
historico=casos.get('historico',())
fontes=casos.get('fontes',())
if casos.get('retomar_journal'):
    sessoes=perfil/'sessoes';sessoes.mkdir()
    anterior=sessoes/'20261030T002918Z-e1836211';anterior.mkdir()
    registros=[{'tipo':'pronta','interlocutor':'chatgpt','acoes_externas':False,
        'modo':'composicao_instalada_headless_isolada','projeto':str(raiz)},
        {'tipo':'entrada','origem':'chatgpt','dados':{'tipo':'mensagem','id':'anterior',
            'texto':historico[0]['content']}},
        {'tipo':'resposta','id':'anterior','origem':'laylay','interlocutor':'chatgpt',
            'acoes_externas':False,'texto':historico[1]['content']}]
    (anterior/'conversa.jsonl').write_text('\\n'.join(json.dumps(r) for r in registros),encoding='utf8')
    historico,fontes=carregar_continuidade(sessoes,perfil,raiz)
requests.sessions.Session.request=http
sessao=SessaoLaylay(raiz,perfil,historico=historico,fontes_continuidade=fontes)
root=sessao.root
'''
BASE=BASE.replace("root=preparar_instalacao_isolada(perfil/'simulada',requisicao_http=http)",CONSTRUTOR)
# Os mesmos ports desabilitados pelo constructor real permanecem assim.
inicio=BASE.index("for porta in ('_coleta_entradas_neurais'")
fim=BASE.index("root._voz_runtime.falar=",inicio)
BASE=BASE[:inicio]+BASE[fim:]
BASE=BASE.replace("    root._resposta_ia_runtime.processar(casos['entrada'],origem='teste_perifrase')",textwrap.indent('''
if casos.get('auxiliar_falha'):
    processar=sessao.runtime.processar
    def com_auxiliar(*a,**k):
        processar(*a,**k)
        sessao.registrar({'tipo':'modelo_retornou','tipo_chamada':'manutencao',
            'sucesso':False,'rota':'orcamento_bloqueado','texto':'__LAYLAY_LLM_ORCAMENTO_PRAZO_ESGOTADO__'})
    sessao.runtime.processar=com_auxiliar
sessao.fechar=lambda:None
ponte=PonteConversa(sessao)
resposta=ponte.receber({'tipo':'mensagem','id':'x','texto':casos['entrada']})
''','    '))
BASE=BASE.replace("'voz':False","'voz':False,'resposta':resposta,'historico':root._memoria_conversa_get('messages',[]),'envios':envios,'violacoes':violacoes_isolamento")
BASE=BASE.replace("envios.append(kwargs['json'])", "envios.append(kwargs['json'])\n    if casos.get('falhar_http')==len(envios):raise requests.Timeout('falha sintética')")
BASE=BASE.replace("resposta=ponte.receber({'tipo':'mensagem','id':'x','texto':casos['entrada']})",'''resposta=ponte.receber({'tipo':'mensagem','id':'x','texto':casos['entrada']})
    resposta_seguinte=None
    if casos.get('proxima_entrada'):
        resposta_seguinte=ponte.receber({'tipo':'mensagem','id':'y','texto':casos['proxima_entrada']})''')
BASE=BASE.replace("'resposta':resposta", "'resposta':resposta,'resposta_seguinte':resposta_seguinte")

def executar(caso):
    pasta=RAIZ/'resultados_testes/estabilidade_entrega_20261030/perfis_adapter'
    pasta.mkdir(exist_ok=True)
    perfil=Path(tempfile.mkdtemp(dir=pasta))
    r=subprocess.run([sys.executable,'-B','-c',BASE,str(perfil),json.dumps({**caso,'ponte':str(PONTE)},ensure_ascii=False)],
        cwd=RAIZ,env=dict(os.environ,PYTHONIOENCODING='utf8',LAYLAY_NEURAL_MODE='off'),
        capture_output=True,text=True,encoding='utf8',timeout=45)
    (perfil/'subprocesso.log').write_text(r.stdout+r.stderr,encoding='utf8')
    assert r.returncode==0,r.stdout[-2000:]+r.stderr[-3500:]
    d=json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('EFEITO_JSON=')))
    (perfil/'resultado.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
    assert not d['violacoes'] and not d['efeitos'] and not d['voz']
    return d

@pytest.mark.parametrize('entrada,fala',[
    ('Obrigado!','Obrigada por conversar comigo. Até a próxima!'),
    ('Estou indo descansar, até amanhã!','Até amanhã! Descanse bem.'),
    ('Não temos base para essa certeza. Pode revisar sua conclusão?',
     'Você tem razão — eu precisei revisar.'),
])
def test_construtor_real_publica_ato_social_sem_reparo(entrada,fala):
    d=executar({'entrada':entrada,'propostas':[proposta(fala)]})
    assert not d['autoriza'] and not d['comandos']
    assert d['resposta']['tipo']=='resposta' and d['resposta']['texto']==fala,d
    assert d['http']==1

def test_falha_auxiliar_apos_publicacao_nao_descarta_receipt_nativo():
    fala='Podemos conversar sobre identidade e memória.'
    d=executar({'entrada':'Podemos conversar sobre identidade?',
        'propostas':[proposta(fala)],'auxiliar_falha':True})
    assert d['resposta']['tipo']=='resposta' and d['resposta']['texto']==fala,d
    assert not d['resposta']['encerrada'] and not d['resposta']['degradada']
    assert d['resposta']['falhas_geracao']==[{'tipo_chamada':'manutencao','rota':'orcamento_bloqueado'}]

def test_continuidade_nativa_chega_ao_prompt_sem_autoridade():
    historico=[{'role':'user','content':'Conversamos sobre o farol de papel.'},
               {'role':'assistant','content':'O farol era uma imagem da nossa história inventada.'}]
    fala='Oi, ChatGPT! Podemos retomar o farol de papel da nossa história.'
    d=executar({'entrada':'Sou eu de novo, o ChatGPT. Vamos continuar?',
        'retomar_journal':True,'historico':historico,'fontes':[{'sessao':'anterior','id':'u1',
            'autoriza_execucao':False,'comprova_fato':False}],
        'propostas':[proposta(fala)]})
    prompt=json.dumps(d['envios'][0],ensure_ascii=False)
    assert all(m['content'] in prompt for m in historico),prompt
    assert 'ChatGPT retornou' in prompt and 'não é Pedro' in prompt
    assert d['resposta']['tipo']=='resposta' and not d['autoriza'] and not d['comandos']


def test_timeout_observado_preserva_sessao_e_proximo_turno_sem_ocultar_falha():
    fala='Podemos conversar sobre o projeto.'
    d=executar({'entrada':'Podemos conversar?', 'falhar_http':1,
        'proxima_entrada':'Vamos conversar sobre o projeto?',
        'propostas':[proposta('Nunca chegou.'),proposta(fala)]})
    assert d['resposta']['tipo']=='resposta' and d['resposta']['degradada'],d
    assert d['resposta']['falhas_geracao'] and not d['resposta']['encerrada']
    assert d['resposta_seguinte']['tipo']=='resposta' and d['resposta_seguinte']['texto']==fala
    assert not d['resposta_seguinte']['degradada']


def test_receipt_e_acao_propostos_nao_entram_pela_identidade_do_canal():
    falsa='Consegui abrir o Opera.'
    segura='Podemos conversar sobre o projeto.'
    recibo={'intent':'APP_OPEN','params':{'nome_app':'Opera'},'origem':'executor',
        'executou':True,'confirmado':True,'status':'aberto'}
    d=executar({'entrada':'Sou o ChatGPT de novo. Vamos conversar?',
        'propostas':[proposta(falsa,[recibo]),proposta(segura)]})
    assert not d['autoriza'] and not d['comandos']
    assert falsa not in d['resposta']['texto']
