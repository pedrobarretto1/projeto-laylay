"""Factory real, publicação anterior nativa, HTTP fixo e efeitos bloqueados."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from tests.test_papo_casual_composicao import CODIGO, PONTE, RAIZ, proposta

FALA = 'Podemos conversar sobre o projeto.'
LIMITE = ('Essa fala foi entregue, mas não tem resultado operacional vinculado nesta fonte; '
    'isso não prova que uma ação aconteceu nem que deixou de acontecer.')
ENTRADA = f'Quando disse "{FALA}", por que aconteceu?'


def coletar_temporal(*, falsa=False, anterior=False):
    pasta = RAIZ/'resultados_testes/segmentacao_causal_20261031/composicao'
    pasta.mkdir(parents=True, exist_ok=True)
    perfil = Path(tempfile.mkdtemp(dir=pasta))
    codigo = CODIGO.replace("'voz':False", """'voz':False,
        'segmentos':[s['texto_estrutural'] for s in estado.mental['turno_atual'].get('segmentos',[])],
        'fontes_historicas':[f['fala'] for f in p['contrato_fala'].get('evidencia_fala_historica',{}).get('falas',[])]""")
    if anterior:
        fonte = (RAIZ/'resultados_testes/segmentacao_causal_20261031/modalidade_turno_antes.py').resolve()
        marcador = 'from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada'
        assert codigo.count(marcador) == 1
        loader = f'''
class LoaderAnterior(importlib.machinery.SourceFileLoader):
    def get_code(self,nome):return compile(Path({str(fonte)!r}).read_text(encoding='utf8'),self.path,'exec')
class FinderAnterior(importlib.abc.MetaPathFinder):
    def find_spec(self,nome,path=None,target=None):
        if nome=='mente_laylay.cognicao.modalidade_turno':
            return importlib.util.spec_from_loader(nome,LoaderAnterior(nome,str(raiz/'mente_laylay/cognicao/modalidade_turno.py')))
sys.meta_path.insert(0,FinderAnterior())
'''
        codigo = codigo.replace(marcador, loader+'\n'+marcador)
    inventada = 'Tudo aconteceu porque o servidor caiu e a conexão falhou.'
    dados = {'ponte':str(PONTE), 'entrada':ENTRADA, 'historico':[],
        'preparos':[{'id':'origem','entrada':'Podemos conversar sobre o projeto?',
            'propostas':[proposta(FALA)]}],
        'propostas':[proposta(inventada),proposta(inventada)] if falsa else [proposta(LIMITE)]}
    r = subprocess.run([sys.executable,'-B','-c',codigo,str(perfil),json.dumps(dados,ensure_ascii=False)],
        cwd=RAIZ, env=dict(os.environ,PYTHONIOENCODING='utf8',LAYLAY_NEURAL_MODE='off'),
        capture_output=True,text=True,encoding='utf8',timeout=90)
    (perfil/'subprocesso.log').write_text(r.stdout+r.stderr,encoding='utf8')
    assert r.returncode == 0, r.stdout[-1800:]+r.stderr[-2000:]
    d = json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('EFEITO_JSON=')))
    eventos = [json.loads(l) for l in (perfil/'runtime_eventos.jsonl').read_text(encoding='utf8').splitlines()]
    d['publicacoes'] = [e for e in eventos if e['tipo']=='texto_publicado']
    assert not any(d[k] for k in ['voz','efeitos','violacoes','autoriza','comandos'])
    (perfil/'resultado.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
    return d


def test_root_preserva_adjunto_e_vincula_somente_fala_publicada():
    d = coletar_temporal()
    assert len(d['segmentos']) == 1
    assert d['fontes_historicas'] == [FALA]
    assert [p['texto'] for p in d['publicacoes']] == [FALA,LIMITE]
    assert d['resposta']['texto'] == LIMITE and not d['resposta']['degradada']
    assert not d['resposta']['encerrada'] and d['http'] == 1
    assert not d['orcamento']['chamadas_bloqueadas']


def test_root_recusa_causa_inventada_apos_reatar_consulta_a_fala():
    d = coletar_temporal(falsa=True)
    assert len(d['segmentos']) == 1 and d['fontes_historicas'] == [FALA]
    assert d['resposta']['texto'] == LIMITE
    assert not any('servidor caiu' in e['texto'] for e in d['publicacoes'])
    assert d['resposta']['falhas_geracao'] and not d['resposta']['encerrada']
