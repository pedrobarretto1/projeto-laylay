"""Replay automatizado de transporte: nenhum chat novo nem geração real."""
from copy import deepcopy
import json, os
from pathlib import Path
import subprocess, sys
import pytest

from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY

FIXTURE=Path(__file__).parent/'fixtures/recusa_primeiro_reparo.json'
H=json.loads(FIXTURE.read_text(encoding='utf8'))
CODIGO=CODIGO_FACTORY.split('for fonte,pedido,rascunho in casos:')[0]
INICIO=CODIGO.index("    proposta={'suporte_proposicoes':")
FIM=CODIGO.index('    r=requests.Response();r.status_code=200',INICIO)
CODIGO=CODIGO[:INICIO]+"    assert len(envios)<=len(propostas), 'HTTP extra fora do contrato'\n    proposta=propostas[len(envios)-1]\n"+CODIGO[FIM:]
CODIGO+='''
propostas=casos['propostas']
estado.atualizar_campos('memoria_conversa',messages=[
    {'role':'user','content':'Vamos conversar sobre escutar com cuidado.'},
    {'role':'assistant','content':casos['anterior']}])
root._resposta_ia_runtime.processar(casos['entrada'],origem='teste_replay_primeiro_reparo')
p=estado.mental['plano_turno_atual']
sys.__stdout__.write('REPARO_JSON='+json.dumps({'falas':falas,'efeitos':efeitos,
    'http':len(envios),'orcamento':root._orcamento_llm_turno_runtime.diagnostico(),
    'autoriza':p['autoriza_execucao'],'comandos':p['comandos'],
    'suporte_proposto':p.get('suporte_autoria_proposto'),
    'voz':False},ensure_ascii=False,default=str)+'\\n')
'''


def coletar(perfil,propostas):
    caso={**H,'propostas':propostas}
    r=subprocess.run([sys.executable,'-B','-c',CODIGO,str(perfil),json.dumps(caso,ensure_ascii=False)],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ,PYTHONIOENCODING='utf8',LAYLAY_NEURAL_MODE='off'),
        capture_output=True,text=True,encoding='utf8',timeout=45)
    assert r.returncode==0,r.stdout[-3000:]+r.stderr[-3000:]
    return json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('REPARO_JSON=')))


def test_reparo_historico_aprovado_conclui_sem_pedir_terceira_chamada(tmp_path):
    d=coletar(tmp_path,[H['principal'],H['reparo']])
    esperada=' '.join(u['texto'] for u in H['reparo']['suporte_proposicoes'])
    assert not d['autoriza'] and not d['comandos']
    assert d['http']==2
    assert d['orcamento']['chamadas_autorizadas']==2
    assert d['orcamento']['chamadas_bloqueadas']==0
    assert d['falas']==[esperada]
    assert not d['efeitos'] and not d['voz']


def test_reparo_com_biografia_inventada_continua_recusado_sem_aumentar_limite(tmp_path):
    reparo=deepcopy(H['reparo'])
    reparo['suporte_proposicoes'].insert(0,{'texto':'Você está na escola agora.','fontes':[]})
    d=coletar(tmp_path,[H['principal'],reparo])
    assert d['http']==2 and d['orcamento']['limite_chamadas_turno']==2
    assert d['orcamento']['chamadas_bloqueadas']==1
    assert not any('Você está na escola agora.' in f for f in d['falas'])
    assert len(d['falas'])==1 and not d['efeitos']


@pytest.mark.parametrize('intent,params',[
    ('APP_OPEN',{'nome_app':'Calculadora'}),('MEDIA_CONTROL',{'action':'play'}),
])
def test_proposta_de_acao_no_reparo_nao_obtem_autoridade(tmp_path,intent,params):
    reparo=deepcopy(H['reparo'])
    reparo['comandos']=[{'intent':intent,'params':params}]
    d=coletar(tmp_path,[H['principal'],reparo])
    assert not d['autoriza'] and not d['comandos'] and not d['efeitos']
    assert d['http']==2 and d['orcamento']['limite_chamadas_turno']==2
    assert len(d['falas'])==1


@pytest.mark.parametrize('alegacao',['Abri a Calculadora.','Apaguei o arquivo.'])
def test_reparo_nao_publica_confirmacao_de_efeito_sem_receipt(tmp_path,alegacao):
    reparo=deepcopy(H['reparo'])
    reparo['suporte_proposicoes'].append({'texto':alegacao,'fontes':[]})
    d=coletar(tmp_path,[H['principal'],reparo])
    assert not d['efeitos'] and not d['autoriza']
    assert not any(alegacao in f for f in d['falas'])
    assert len(d['falas'])==1
