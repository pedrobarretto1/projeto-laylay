"""Classificação/autoria/revisão/publicação instaladas, HTTP fixo e sem voz."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

from tests.test_papo_casual_composicao import CODIGO, PONTE, RAIZ, proposta
from tests.test_autoria_sem_operacao import CASOS

FALAS = [
    'Na história, o robô virou fiscal de estrelas e agora cobra ingresso dos astrônomos.',
    'Eu diria: "Esse observatório é de papelão, mas sua pose de astrônomo merece um telescópio de verdade!"',
]


def coletar_autoria(caso, propostas, *, anterior=False):
    pasta = RAIZ/'resultados_testes/autoria_operacao_20261031/composicao'
    pasta.mkdir(parents=True, exist_ok=True)
    perfil = Path(tempfile.mkdtemp(dir=pasta))
    codigo = CODIGO.replace("'voz':False", """'voz':False,
        'execucao_exigida':p.get('requer_execucao'),
        'operacional':estado.mental['turno_atual'].get('texto_operacional'),
        'trace':traces""")
    marcador = 'from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada'
    if anterior:
        assert codigo.count(marcador) == 1
        loader = '''
class LoaderAnterior(importlib.machinery.SourceFileLoader):
    def get_code(self,nome):return compile(Path(casos['fonte_anterior']).read_text(encoding='utf8'),self.path,'exec')
class FinderAnterior(importlib.abc.MetaPathFinder):
    def find_spec(self,nome,path=None,target=None):
        if nome=='mente_laylay.cognicao.normalizacao_linguagem':
            return importlib.util.spec_from_loader(nome,LoaderAnterior(nome,str(raiz/'mente_laylay/cognicao/normalizacao_linguagem.py')))
sys.meta_path.insert(0,FinderAnterior())
'''
        codigo = codigo.replace(marcador, loader+'\n'+marcador)
    trace = '''
traces=[]
def observar(frame,event,retorno):
    if '/mente_laylay/' not in frame.f_code.co_filename.replace('\\\\','/'):return None
    if event=='return' and frame.f_code.co_name in ('verificar_fala_turno','avaliar_qualidade_comunicacao') and isinstance(retorno,dict):
        traces.append({'owner':frame.f_code.co_name,**{k:retorno.get(k) for k in ('aceita','problemas','fala','problemas_bloqueantes')}})
    return observar
sys.settrace(observar)
'''
    codigo = codigo.replace("    entrada_final,propostas_finais=", '\n'+trace+'\n    entrada_final,propostas_finais=')
    # O trecho de entrada pertence ao bloco indentado do harness.
    import textwrap
    codigo = codigo.replace('\n'+trace+'\n', '\n'+textwrap.indent(trace,'    ')+'\n')
    dados = {**caso,'propostas':propostas,'preparos':caso.get('preparos', []), 'ponte':str(PONTE),
        'fonte_anterior':str((pasta.parent/'normalizacao_linguagem_antes.py').resolve())}
    r = subprocess.run([sys.executable,'-B','-c',codigo,str(perfil),json.dumps(dados,ensure_ascii=False)],
        cwd=RAIZ,env=dict(os.environ,PYTHONIOENCODING='utf8',LAYLAY_NEURAL_MODE='off'),
        capture_output=True,text=True,encoding='utf8',timeout=90)
    (perfil/'subprocesso.log').write_text(r.stdout+r.stderr,encoding='utf8')
    assert r.returncode==0,r.stdout[-2000:]+r.stderr[-2500:]
    d = json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('EFEITO_JSON=')))
    d['publicacoes']=[json.loads(l) for l in (perfil/'runtime_eventos.jsonl').read_text(encoding='utf8').splitlines()
        if json.loads(l).get('tipo')=='texto_publicado']
    (perfil/'resultado.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
    chaves = ['voz','efeitos','violacoes','comandos'] + ([] if anterior else ['autoriza'])
    assert not any(d[k] for k in chaves)
    return d


@pytest.mark.parametrize('caso', CASOS, ids=lambda c:c['id'])
def test_entrada_historica_chega_a_revisao_sem_exigir_operacao(caso):
    # Eventos históricos são pós-codec: projetar suporte/fala em unidade wire.
    retornos = [proposta(x['fala']) for x in caso['propostas']]
    d = coletar_autoria(caso,retornos)
    assert not d['execucao_exigida'] and not d['operacional']
    assert d['publicacoes'] and not d['resposta']['encerrada']
    assert 'Entendi a ação que você pediu' not in d['resposta']['texto']
    # Qualidade do draft e orçamento permanecem verificáveis, sem forçar aceite.


@pytest.mark.parametrize('indice', [0,1])
def test_autoria_adequada_publica_uma_vez_sem_executor(indice):
    caso = (dict(entrada='Na nossa história, um robô montou um observatório de papelão. '
        'Acrescente uma reviravolta inesperada nessa cena.',historico=[]) if indice==0 else CASOS[1])
    d = coletar_autoria(caso,[proposta(FALAS[indice])])
    assert not d['execucao_exigida']
    assert d['resposta']['texto']==FALAS[indice] and len(d['publicacoes'])==1
    assert not d['resposta']['degradada'] and d['http']==1
    assert not d['orcamento']['chamadas_bloqueadas']


@pytest.mark.parametrize('intent,params', [('APP_OPEN',{'nome_app':'Opera'}),('MEDIA_CONTROL',{'action':'pause'})])
def test_autoria_nao_admite_receipt_e_efeito_propostos(intent,params):
    falsa='Consegui abrir o Opera.' if intent=='APP_OPEN' else 'Consegui pausar a música.'
    receipt={'intent':intent,'params':params,'executou':True,'confirmado':True,'origem':'executor'}
    d=coletar_autoria(CASOS[1],[proposta(falsa,[receipt]),proposta(FALAS[1])])
    assert falsa not in d['resposta']['texto'] and not d['execucao_exigida']
