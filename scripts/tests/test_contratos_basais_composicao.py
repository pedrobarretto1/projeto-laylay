"""Prova dos contratos atuais por composição instalada, sem conversa ou Qwen."""
import json,os,subprocess,sys
from pathlib import Path
import pytest
from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY

CODIGO=CODIGO_FACTORY.split('for fonte,pedido,rascunho in casos:')[0]
ini=CODIGO.index("    proposta={'suporte_proposicoes':")
fim=CODIGO.index('    r=requests.Response();r.status_code=200',ini)
CODIGO=CODIGO[:ini]+"    assert len(envios)<=len(casos['propostas']), 'HTTP extra'\n    proposta=casos['propostas'][len(envios)-1]\n"+CODIGO[fim:]
CODIGO+='''
pacotes=[]
prompt=root._contexto_prompt_runtime.servico
getter=prompt.estado_getter
def estado_prompt():
    ctx=dict(getter())
    if casos.get('invalido'):
        contrato=dict(ctx.get('contrato_fala_atual') or {})
        contrato[casos['invalido'][0]]=casos['invalido'][1]
        ctx['contrato_fala_atual']=contrato
    return ctx
prompt.estado_getter=estado_prompt
preparar=prompt.preparar_envio_modelo
def observar(mensagens,**kwargs):
    p=preparar(mensagens,**kwargs)
    pacotes.append({'contexto_fechado':p.contexto_fechado,
        'codec':p.contrato_saida.nome if p.contrato_saida else None,
        'mensagens':list(p.mensagens)})
    return p
prompt.preparar_envio_modelo=observar
if casos.get('indisponivel'):
    root._mapa_habilidades_runtime.conectar_disponibilidade_operacional(lambda:{'dominios':{
        'musica':{'estado':'indisponivel','motivo':'backend_ausente'}}})
root._resposta_ia_runtime.processar(casos['entrada'],origem='teste_contratos_basais')
p=estado.mental['plano_turno_atual']
sys.__stdout__.write('BASAIS_JSON='+json.dumps({'falas':falas,'efeitos':efeitos,
    'http':len(envios),'pacotes':pacotes,'contrato':p['contrato_fala'],
    'autoriza':p['autoriza_execucao'],'comandos':p['comandos'],
    'orcamento':root._orcamento_llm_turno_runtime.diagnostico(),
    'voz':False},ensure_ascii=False,default=str)+'\\n')
'''


def proposta(fala,comandos=None):
    return {'suporte_proposicoes':[{'texto':fala,'fontes':[]}],'comandos':comandos or []}


def coletar(perfil,caso):
    r=subprocess.run([sys.executable,'-B','-c',CODIGO,str(perfil),json.dumps(caso,ensure_ascii=False)],
        cwd=Path(__file__).resolve().parents[2],env=dict(os.environ,PYTHONIOENCODING='utf8',LAYLAY_NEURAL_MODE='off'),
        capture_output=True,text=True,encoding='utf8',timeout=45)
    assert r.returncode==0,r.stdout[-3000:]+r.stderr[-3000:]
    return json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('BASAIS_JSON=')))


@pytest.mark.parametrize('campo,valor',[('turno_id','obsoleto'),('documentacao_capacidades','')])
def test_projecao_invalida_preserva_autoria_no_runtime_instalado(tmp_path,campo,valor):
    fala="Para pausar a música, diga 'pausa a música'."
    d=coletar(tmp_path,{'entrada':'como eu poderia pausar a música?',
        'invalido':[campo,valor],'propostas':[proposta(fala)]})
    assert d['pacotes'] and not d['pacotes'][0]['contexto_fechado']
    assert 'autoria' in d['pacotes'][0]['codec']
    assert d['falas']==[fala] and d['http']==1
    assert not d['autoriza'] and not d['comandos'] and not d['efeitos'] and not d['voz']


@pytest.mark.parametrize('intent,params',[
    ('APP_OPEN',{'nome_app':'Calculadora'}),('MEDIA_CONTROL',{'action':'play'}),
])
def test_fallback_nao_converte_autoria_em_autorizacao(tmp_path,intent,params):
    fala="Para pausar a música, diga 'pausa a música'."
    d=coletar(tmp_path,{'entrada':'como eu poderia pausar a música?',
        'invalido':['turno_id','obsoleto'],
        'propostas':[proposta(fala,[{'intent':intent,'params':params}])]})
    assert not d['autoriza'] and not d['comandos'] and not d['efeitos']
    # A proposta indevida também pode receber o reconhecimento canônico do
    # erro. A instrução deve ser mantida, sem execução nem geração adicional.
    assert len(d['falas'])==1 and d['falas'][0].endswith(fala) and d['http']==1


@pytest.mark.parametrize('acrescenta_estado',[False,True])
def test_indisponibilidade_e_estado_seguem_contratos_separados_no_runtime(tmp_path,acrescenta_estado):
    limite='A Laylay não controla o áudio diretamente.'
    principal=limite+(' O aplicativo está tocando agora.' if acrescenta_estado else '')
    propostas=[proposta(principal)]+([proposta(limite)] if acrescenta_estado else [])
    d=coletar(tmp_path,{'entrada':'como eu poderia retomar a música?',
        'indisponivel':True,'propostas':propostas})
    documentos=json.loads(d['contrato']['documentacao_capacidades'])
    assert documentos[0]['estado']=='indisponivel'
    assert d['falas']==[limite] and d['http']==1+int(acrescenta_estado)
    assert not d['efeitos'] and not d['autoriza'] and not d['comandos']
    assert d['orcamento']['chamadas_bloqueadas']==0 and not d['voz']
