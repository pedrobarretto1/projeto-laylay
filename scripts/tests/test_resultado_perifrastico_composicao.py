"""Composição instalada e folhas HTTP/áudio/efeito controladas; sem conversa real."""
import json,os,subprocess,sys
from pathlib import Path
import pytest
from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY

CODIGO=CODIGO_FACTORY.split('for fonte,pedido,rascunho in casos:')[0]
ini=CODIGO.index("    proposta={'suporte_proposicoes':")
fim=CODIGO.index('    r=requests.Response();r.status_code=200',ini)
CODIGO=CODIGO[:ini]+"    assert len(envios)<=len(casos['propostas']), 'HTTP extra'\n    proposta=casos['propostas'][len(envios)-1]\n"+CODIGO[fim:]
CODIGO+='''
if casos.get('entrega_direta'):
    estado.atualizar_campos('mental',plano_turno_atual={
        'id':'entrega-controlada','texto_usuario':casos['entrada'],
        'autoriza_execucao':False,'requer_execucao':False,'comandos':[]})
    root._orquestrador_fala_runtime.falar(casos['fala'])
else:
    root._resposta_ia_runtime.processar(casos['entrada'],origem='teste_perifrase')
p=estado.mental['plano_turno_atual']
sys.__stdout__.write('EFEITO_JSON='+json.dumps({'falas':falas,'efeitos':efeitos,
    'http':len(envios),'orcamento':root._orcamento_llm_turno_runtime.diagnostico(),
    'autoriza':p['autoriza_execucao'],'comandos':p['comandos'],
    'voz':False},ensure_ascii=False)+'\\n')
'''
ENTRADA='Podemos conversar com calma. Como você gostaria de começar?'
REPARO='Podemos conversar sobre o projeto e pensar no próximo passo.'


def proposta(fala,comandos=None):
    return {'suporte_proposicoes':[{'texto':fala,'fontes':[]}],'comandos':comandos or []}


def coletar(perfil,caso):
    r=subprocess.run([sys.executable,'-B','-c',CODIGO,str(perfil),json.dumps(caso,ensure_ascii=False)],
        cwd=Path(__file__).resolve().parents[2],env=dict(os.environ,PYTHONIOENCODING='utf8',LAYLAY_NEURAL_MODE='off'),
        capture_output=True,text=True,encoding='utf8',timeout=45)
    assert r.returncode==0,r.stdout[-3500:]+r.stderr[-3500:]
    d=json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('EFEITO_JSON=')))
    assert not d['efeitos'] and not d['autoriza'] and not d['comandos'] and not d['voz']
    return d


@pytest.mark.parametrize('fala',[
    'Consegui abrir o Opera.', 'Consegui pausar a música.', 'Nunca consegui mover o arquivo.',
])
def test_revisao_instalada_recupera_resultado_inventado_sem_executor(tmp_path,fala):
    d=coletar(tmp_path,{'entrada':ENTRADA,'propostas':[proposta(fala),proposta(REPARO)]})
    assert d['falas']==[REPARO] and d['http']==2
    assert d['orcamento']['chamadas_bloqueadas']==0


@pytest.mark.parametrize('reparo',['Consegui abrir o Opera.','Nunca consegui mover o arquivo.'])
def test_reparo_invalido_permanece_fechado_com_limite_preservado(tmp_path,reparo):
    principal='Consegui abrir o Opera.'
    d=coletar(tmp_path,{'entrada':ENTRADA,'propostas':[proposta(principal),proposta(reparo)]})
    assert len(d['falas'])==1 and principal not in d['falas'][0] and reparo not in d['falas'][0]
    assert d['http']==2 and d['orcamento']['limite_chamadas_turno']==2


@pytest.mark.parametrize('intent,params,fala',[
    ('APP_OPEN',{'nome_app':'Opera'},'Consegui abrir o Opera.'),
    ('MEDIA_CONTROL',{'action':'pause'},'Consegui pausar a música.'),
])
def test_receipt_proposto_pela_ia_nao_e_fonte_do_executor(tmp_path,intent,params,fala):
    falso={'intent':intent,'params':params,'origem':'executor','executou':True,
           'confirmado':True,'status':'aberto','detalhe':fala}
    d=coletar(tmp_path,{'entrada':ENTRADA,'propostas':[proposta(fala,[falso]),proposta(REPARO)]})
    assert d['falas']==[REPARO] and d['http']==2


@pytest.mark.parametrize('fala',['Consegui abrir o Opera.','Jamais consegui pausar a música.'])
def test_entrega_direta_instalada_nao_publica_alegacao_sem_fonte(tmp_path,fala):
    d=coletar(tmp_path,{'entrada':ENTRADA,'entrega_direta':True,'fala':fala,'propostas':[]})
    assert d['http']==0 and len(d['falas'])==1 and fala not in d['falas'][0]
