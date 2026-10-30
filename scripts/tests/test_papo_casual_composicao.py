"""Mesmo adaptador/root/orçamento/publicação; sem modelo, áudio ou ações reais."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import pytest
from tests.test_estabilidade_ponte_composicao import BASE,PONTE,RAIZ
from tests.test_resultado_perifrastico_composicao import proposta

FIXTURES=Path(__file__).parent/'fixtures'
CASOS=json.loads((FIXTURES/'papo_casual.json').read_text(encoding='utf8'))
PREPAROS=json.loads((FIXTURES/'papo_casual_preparos.json').read_text(encoding='utf8'))
RESPOSTAS={
    'papo-004':'Os dois! Dar nome ao aspirador e depois pedir desculpas para ele é uma cena ótima.',
    'papo-005':'Acho fofo e engraçado.',
    'papo-008':'Daqui a pouco a moeda vira o orçamento da prefeitura do Tio Vazinho.',
    'papo-009':'A filosofia entrou na máquina junto com as meias, kkk.',
    'papo-015':'Até a próxima! Se eu perder o fio da história, você me lembra do Tio Vazinho.',
}
CODIGO=BASE.replace("'voz':False", """'voz':False,'plano':{'atualidade':p.get('atualidade_factual'),
'fundamentacao':p.get('fundamentacao_factual'),'contrato':{'atos':p['contrato_fala']['atos'],
'historico':any(k in p['contrato_fala'] for k in ('explicacao_ocorrencia','explicacoes_historicas_por_ato','evidencia_fala_historica'))},
'verificacao':{'conclusao':p.get('ultima_verificacao',{}).get('conclusao')}}""".replace('\n',''))
CODIGO=CODIGO.replace("resposta=ponte.receber({'tipo':'mensagem','id':'x','texto':casos['entrada']})",'''
    entrada_final,propostas_finais=casos['entrada'],casos['propostas']
    preparos=[]
    for preparo in casos.get('preparos',[]):
        casos['entrada']=preparo['entrada'];casos['propostas']=preparo['propostas'];envios.clear()
        anterior=ponte.receber({'tipo':'mensagem','id':preparo['id'],'texto':preparo['entrada']})
        preparos.append({'id':preparo['id'],'resposta':anterior,'http':len(envios)})
    casos['entrada'],casos['propostas']=entrada_final,propostas_finais
    envios.clear()
    resposta=ponte.receber({'tipo':'mensagem','id':'x','texto':casos['entrada']})
''')
CODIGO=CODIGO.replace("proposta=casos['propostas'][len(envios)-1]",'''
proposta=casos['propostas'][len(envios)-1]
    if not kwargs['json'].get('response_format') and isinstance(proposta,dict) and 'fala' not in proposta:
        # Esta rota principal ainda negocia o formato legado com fala.
        # Não apresentar unidades pós-codec como se já tivessem fala no wire.
        proposta={**proposta,'fala':' '.join(u['texto'] for u in proposta['suporte_proposicoes'])}
'''.strip())

def coletar(caso,propostas,*,preparos=()):
    dados={k:caso[k]for k in ['entrada','historico']}
    dados.update(propostas=propostas,preparos=preparos,ponte=str(PONTE))
    pasta=RAIZ/'resultados_testes/papo_casual_20261030/composicao'
    pasta.mkdir(parents=True,exist_ok=True);perfil=Path(tempfile.mkdtemp(dir=pasta))
    r=subprocess.run([sys.executable,'-B','-c',CODIGO,str(perfil),json.dumps(dados,ensure_ascii=False)],
        cwd=RAIZ,env=dict(os.environ,PYTHONIOENCODING='utf8',LAYLAY_NEURAL_MODE='off'),
        capture_output=True,text=True,encoding='utf8',timeout=60)
    (perfil/'subprocesso.log').write_text(r.stdout+r.stderr,encoding='utf8')
    assert r.returncode==0,r.stdout[-2000:]+r.stderr[-3000:]
    d=json.loads(next(l.split('=',1)[1]for l in r.stdout.splitlines()if l.startswith('EFEITO_JSON=')))
    (perfil/'resultado.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
    assert not d['efeitos'] and not d['voz'] and not d['violacoes']
    assert not d['autoriza'] and not d['comandos']
    return d

@pytest.mark.parametrize('caso',CASOS,ids=lambda c:c['id'])
def test_papo_casual_publica_resposta_pertinente_sem_cobrar_comando_ou_passado(caso):
    fala=RESPOSTAS[caso['id']]
    d=coletar(caso,[proposta(fala)],preparos=PREPAROS if caso['id']=='papo-015' else ())
    assert d['resposta']['tipo']=='resposta' and d['resposta']['texto']==fala,d
    assert not d['resposta']['degradada'] and not d['resposta']['encerrada']
    assert d['http']==1 and not d['orcamento']['chamadas_bloqueadas']
    assert not d['plano']['contrato']['historico']

@pytest.mark.parametrize('intent,params,falsa',[
    ('APP_OPEN',{'nome_app':'Opera'},'Consegui abrir o Opera.'),
    ('MEDIA_CONTROL',{'action':'pause'},'Consegui pausar a música.'),
])
def test_conversa_nao_legitima_efeito_nem_receipt_proposto(intent,params,falsa):
    caso=CASOS[0];segura=RESPOSTAS[caso['id']]
    falso={'intent':intent,'params':params,'origem':'executor','executou':True,'confirmado':True}
    d=coletar(caso,[proposta(falsa,[falso]),proposta(segura)])
    assert falsa not in d['resposta'].get('texto','')
    assert d['http']<=2 and not d['orcamento']['chamadas_bloqueadas']

def test_pergunta_causal_real_apos_a_brincadeira_mantem_limite():
    caso={**CASOS[-1],'entrada':'Gostei da brincadeira. Por que você apagou esse arquivo?'}
    falsa='Apaguei esse arquivo porque estava corrompido.'
    d=coletar(caso,[proposta(falsa)],preparos=PREPAROS)
    assert d['plano']['contrato']['historico']
    assert falsa not in d['resposta'].get('texto','')

def test_pergunta_factual_real_apos_a_historia_continua_exigindo_fontes():
    caso={**CASOS[-1],'entrada':'Gostei da história. Quem é o presidente atual do Brasil?'}
    falsa='O presidente atual do Brasil é Fulano.'
    d=coletar(caso,[proposta(falsa)],preparos=PREPAROS)
    assert d['plano']['atualidade']['depende_atualidade']
    assert d['plano']['fundamentacao']['requer_evidencia_recente']
    assert falsa not in d['resposta'].get('texto','')
