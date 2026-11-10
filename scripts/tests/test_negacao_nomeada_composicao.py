"""Planner e admissão do root; inferência/voz/efeitos externos bloqueados."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

from tests.test_resultado_perifrastico_composicao import CODIGO
from tests.instalacao_privada import isolar_base_do_codigo

RAIZ = Path(__file__).resolve().parents[2]
BASE = isolar_base_do_codigo(CODIGO).split("if casos.get('entrega_direta'):")[0]
PROVA = '''
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
turno=root._iniciar_planejamento_turno(casos['entrada'],origem='teste_negacao_nomeada')
principal=ContratoPropostaPrincipal(turno_id=turno['id'],texto_usuario=casos['entrada'],
    resposta_bruta='{"fala":"Vou conferir o pedido.","comandos":[]}')
resultado=root._validador_comandos_turno_runtime.validar_proposta(casos['propostas'],principal)
simulados=[{'pedido':c,'executou':False,'confirmado':False,'simulado':True} for c in resultado['comandos']]
assert not violacoes_isolamento and not efeitos and not envios
sys.__stdout__.write('NEGACAO_JSON='+json.dumps({
    'turno':{'segmentos':[{'texto':s.get('texto_estrutural',s.get('texto','')),'autoriza':s['autoriza_execucao'],
        'veto':s.get('veto_execucao_operacional')} for s in turno['segmentos']],
        'revisao':turno.get('revisao_intra_turno')},
    'admitidos':resultado['comandos'],'indices':resultado.get('atos_autorizados_vinculados',[]),
    'simulados':simulados,'efeitos':efeitos,'voz':False,'http':len(envios),
    'violacoes':violacoes_isolamento},ensure_ascii=False)+'\\n')
'''


def coletar_negacao(texto, propostas, *, anterior=False):
    pasta=RAIZ/'resultados_testes/negacao_musical_20261031/composicao'
    pasta.mkdir(parents=True,exist_ok=True)
    perfil=Path(tempfile.mkdtemp(dir=pasta))
    codigo=BASE
    if anterior:
        marcador='from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada'
        assert codigo.count(marcador)==1
        loader='''
class LoaderAnterior(importlib.machinery.SourceFileLoader):
    def get_code(self,nome):return compile(Path(casos['fontes_anteriores'][nome]).read_text(encoding='utf8'),self.path,'exec')
class FinderAnterior(importlib.abc.MetaPathFinder):
    def find_spec(self,nome,path=None,target=None):
        if nome in casos['fontes_anteriores']:
            return importlib.util.spec_from_loader(nome,LoaderAnterior(nome,str(raiz/(nome.replace('.','/')+'.py'))))
sys.meta_path.insert(0,FinderAnterior())
'''
        codigo=codigo.replace(marcador,loader+'\n'+marcador)
    dados={'entrada':texto,'propostas':propostas,'fontes_anteriores':{
        'mente_laylay.cognicao.'+nome:str((pasta.parent/(nome+'_antes.py')).resolve())
        for nome in ['modalidade_turno','gramatica_operacional']}}
    r=subprocess.run([sys.executable,'-B','-c',codigo+PROVA,str(perfil),json.dumps(dados,ensure_ascii=False)],
        cwd=RAIZ,env=dict(os.environ,PYTHONIOENCODING='utf8',LAYLAY_NEURAL_MODE='off'),
        capture_output=True,text=True,encoding='utf8',timeout=60)
    (perfil/'subprocesso.log').write_text(r.stdout+r.stderr,encoding='utf8')
    assert r.returncode==0,r.stdout[-1800:]+r.stderr[-2500:]
    d=json.loads(next(l.split('=',1)[1]for l in r.stdout.splitlines()if l.startswith('NEGACAO_JSON=')))
    (perfil/'resultado.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
    assert not d['voz'] and not d['efeitos'] and not d['http'] and not d['violacoes']
    return d


@pytest.mark.parametrize('negativo,errado',[
    ('não toca a música "Noite e Lua"',{'intent':'MUSIC_SEARCH','params':{'query':'Noite e Lua'}}),
    ('não abre a calculadora',{'intent':'APP_OPEN','params':{'nome_app':'calculadora'}}),
])
def test_root_admite_so_pedido_literal_e_simula_sem_efeito(negativo,errado):
    texto='Toca a música "Água e Sol"; '+negativo
    certo={'intent':'MUSIC_SEARCH','params':{'query':'Água e Sol'}}
    d=coletar_negacao(texto,[errado,certo,certo])
    assert len(d['turno']['segmentos'])==2
    assert d['turno']['segmentos'][0]['autoriza'] and d['turno']['segmentos'][1]['veto']
    assert not (d['turno']['revisao'] or {}).get('detectada')
    assert d['admitidos']==[certo] and d['indices']==[0]
    assert all(x['simulado'] and not x['executou'] and not x['confirmado'] for x in d['simulados'])


@pytest.mark.parametrize('negativo',['não toca a música "ÁGUA E SOL"','não toca nada','não toca isso'])
def test_root_cancelamento_ou_referencia_nao_admite_proposta(negativo):
    certo={'intent':'MUSIC_SEARCH','params':{'query':'Água e Sol'}}
    d=coletar_negacao('Toca a música "Água e Sol"; '+negativo,[certo])
    assert not d['admitidos'] and not d['simulados']
