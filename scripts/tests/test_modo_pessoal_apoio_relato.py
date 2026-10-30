"""Relato pessoal de atividade não comprova os detalhes propostos pela autora."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from scripts.tests.test_obrigacao_apoio_explicacao import plano_autoral
from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria


CASOS = [
    ('eu trabalho no laboratório', 'Como eu trabalho no laboratório',
     'Trabalho com experimentos que ajudam a entender o mundo.'),
    ('eu estudo à noite', 'Como eu estudo à noite',
     'Você estuda com cartões e revisa cada assunto durante trinta minutos.'),
    ('eu organizo minhas notas', 'De que maneira eu organizo minhas notas?',
     'Você usa etiquetas por cores e separa tudo por matéria.'),
]


def fonte_dialogo(texto: str, indice: int = 1) -> dict:
    return {'id': f'dialogo:usuario:{indice}:' + hashlib.sha256(texto.encode('utf8')).hexdigest(),
            'autor': 'usuario', 'origem': 'historico_conversa',
            'status': 'relatado_pelo_usuario', 'texto': texto}


def montar_plano(fonte, pedido, rascunho):
    plano = plano_autoral(pedido, rascunho)
    plano['relatos_usuario'] = [fonte_dialogo(fonte)]
    return plano


@pytest.mark.parametrize('fonte,pedido,rascunho', CASOS)
def test_atividade_relatada_nao_sustenta_descricao_livre_de_seu_modo(fonte, pedido, rascunho):
    plano = montar_plano(fonte, pedido, rascunho)
    anterior = deepcopy(plano['relatos_usuario'])
    r = revisar_suporte_autoria(rascunho, plano=plano)
    assert r is not None and r.aplicar_limite, 'primeira fronteira: detalhes propostos foram liberados sem apoio'
    assert r.fala_realizada != rascunho and fonte in r.fala_realizada
    d = r.como_dict()
    assert not any(d[k] for k in ['semantica_verificada', 'prova_implicacao', 'autoriza_execucao'])
    assert not d['pode_confirmar_fato_externo']
    assert plano['relatos_usuario'] == anterior


def test_limite_preserva_relato_com_detalhes_sem_aprovar_outros_acrescimos():
    fonte = 'eu estudo à noite seguindo uma lista de exercícios'
    pedido = 'Como eu estudo à noite'
    rascunho = 'Você usa um cronômetro e revisa tudo durante duas horas.'
    r = revisar_suporte_autoria(rascunho, plano=montar_plano(fonte, pedido, rascunho))
    assert r.aplicar_limite and fonte in r.fala_realizada
    assert 'cronômetro' not in r.fala_realizada and 'duas horas' not in r.fala_realizada


def test_realizacao_limitada_e_idempotente():
    fonte, pedido, rascunho = CASOS[0]
    plano = montar_plano(fonte, pedido, rascunho)
    primeira = revisar_suporte_autoria(rascunho, plano=plano)
    segunda = revisar_suporte_autoria(primeira.fala_realizada, plano=plano)
    assert primeira.aplicar_limite and segunda.fala_realizada == primeira.fala_realizada


@pytest.mark.parametrize('campo', ['requer_execucao', 'comandos'])
def test_receipt_ou_operacao_nao_e_substituido_por_relato_de_atividade(campo):
    fonte, pedido, fala = CASOS[0]
    plano = montar_plano(fonte, pedido, fala)
    plano[campo] = True if campo == 'requer_execucao' else [{'intent': 'APP_OPEN'}]
    r = revisar_suporte_autoria(fala, plano=plano)
    assert r is None or not any(f.get('id') == plano['relatos_usuario'][0]['id']
                               for f in r.como_dict()['fontes_lidas'])


@pytest.mark.parametrize('fonte,pedido', [
    ('eu trabalho no laboratório?', 'Como eu trabalho no laboratório'),
    ('eu trabalho no laboratório de informática e não no de química', 'Como eu trabalho no laboratório de química'),
])
def test_pergunta_e_outro_predicado_nao_emprestam_fonte(fonte, pedido):
    fala = 'Você faz experimentos químicos todos os dias.'
    plano = montar_plano(fonte, pedido, fala)
    r = revisar_suporte_autoria(fala, plano=plano)
    assert r is None or not r.como_dict()['fontes_lidas']


def test_citacao_preserva_condicao_sem_certificar_que_ela_foi_cumprida():
    fonte = 'eu trabalho no laboratório se você me chamar'
    pedido = 'Como eu trabalho no laboratório'
    fala = 'Você faz experimentos todos os dias.'
    r = revisar_suporte_autoria(fala, plano=montar_plano(fonte, pedido, fala))
    assert r.aplicar_limite and '«' + fonte + '»' in r.fala_realizada
    dados = r.como_dict()
    assert dados['fontes_lidas'][0]['modo_verificado'] is False
    assert dados['semantica_verificada'] is dados['prova_implicacao'] is dados['autoriza_execucao'] is False


@pytest.mark.parametrize('pedido', [
    'Como eu posso trabalhar no laboratório?',
    'Como eu poderia estudar à noite?',
    'Como você trabalha no laboratório?',
    'Como ela trabalha no laboratório?',
    'Explique a frase "como eu trabalho no laboratório".',
    'Repita literalmente "Como eu trabalho no laboratório".',
    'Como eu trabalho no hospital?',
])
def test_controles_de_orientacao_terceiro_citacao_e_outro_objeto_nao_herdam_relato(pedido):
    fala = 'Posso usar seu relato para organizar uma explicação.'
    plano = montar_plano(CASOS[0][0], pedido, fala)
    r = revisar_suporte_autoria(fala, plano=plano)
    # Explicação metalinguística já pode exigir fonte por outro contrato.
    assert r is None or not any(f.get('id') == plano['relatos_usuario'][0]['id']
                               for f in r.como_dict()['fontes_lidas'])


@pytest.mark.parametrize('invalido', ['assistente', 'hash', 'contestado', 'origem', 'outra_ocorrencia', 'dict_modelo'])
def test_fonte_alheia_ou_contrato_forjado_nao_ganha_conferencia_pessoal(invalido):
    fonte, pedido, fala = CASOS[0]
    plano = montar_plano(fonte, pedido, fala)
    f = plano['relatos_usuario'][0]
    if invalido == 'assistente': f['autor'] = 'laylay'
    elif invalido == 'hash': f['id'] = 'dialogo:usuario:1:' + '0' * 64
    elif invalido == 'contestado': f['status'] = 'contestado'
    elif invalido == 'origem': f['origem'] = 'proposta_llm'
    elif invalido == 'outra_ocorrencia':
        plano['contrato_fala']['perspectiva_enunciador'] = replace(
            plano['contrato_fala']['perspectiva_enunciador'], turno_id='outra')
    else:
        plano['contrato_fala']['perspectiva_enunciador'] = {'turno_id': plano['id'],
            'texto_usuario': pedido, 'falante_entrada': 'usuario', 'autora_resposta': 'laylay'}
    r = revisar_suporte_autoria(fala, plano=plano)
    assert r is None or not r.como_dict()['fontes_lidas']


CODIGO_FACTORY = textwrap.dedent(r'''
    import importlib.abc, importlib.machinery, importlib.util
    import json, sys
    from pathlib import Path
    from types import ModuleType
    import requests
    raiz=Path.cwd();perfil=Path(sys.argv[1]);casos=json.loads(sys.argv[2])
    apps=ModuleType('AppOpener');apps.open=apps.close=lambda *a,**k:False
    apps.give_appnames=lambda *a,**k:{};sys.modules['AppOpener']=apps
    codigo=(raiz/'laylay.py').read_bytes();bloco=b'PASTA_MEMORIA = os.path.join(_base_dir, "memoria")'
    assert codigo.count(bloco)==1
    codigo=codigo.replace(bloco,('PASTA_MEMORIA = '+repr(str(perfil/'raiz'))).encode())
    class Loader(importlib.machinery.SourceFileLoader):
        def get_code(self,nome):return compile(codigo,self.path,'exec')
    class Finder(importlib.abc.MetaPathFinder):
        def find_spec(self,nome,path=None,target=None):
            if nome=='laylay':return importlib.util.spec_from_loader(nome,Loader(nome,str(raiz/'laylay.py')))
    sys.meta_path.insert(0,Finder())
    from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
    from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
    from mente_laylay.autonomia import coordenador_intencao,roteador_intencao
    envios=[];efeitos=[];falas=[];rascunho=''
    def http(self,method,url,**kwargs):
        if not(str(method).upper()=='POST' and url=='http://localhost:11434/v1/chat/completions'):
            raise PermissionError('rede externa bloqueada')
        envios.append(kwargs['json'])
        proposta={'suporte_proposicoes':[{'texto':rascunho,'fontes':[]}],'comandos':[]}
        schema=kwargs['json'].get('response_format',{}).get('json_schema',{}).get('schema',{})
        if 'criterio_autoral' in schema.get('properties',{}):proposta['criterio_autoral']='nao_declarado'
        r=requests.Response();r.status_code=200
        r._content=json.dumps({'choices':[{'message':{'content':json.dumps(proposta)}}]}).encode()
        return r
    root=preparar_instalacao_isolada(perfil/'simulada',requisicao_http=http)
    for porta in ('_coleta_entradas_neurais','_especialista_neural_comandos_runtime',
                  '_interpretador_semantico_runtime','_pesquisa_contextual_runtime'):
        root._composicao_turno_runtime._servicos[porta]=getattr(root,porta)
    root._voz_runtime.falar=lambda *a,**k:False
    root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda f,*a,**k:falas.append(f)or True)
    coordenador_intencao.executar_intencao=roteador_intencao.executar_intencao=lambda *a,**k:efeitos.append(str(a))or False
    estado=root._estado_compartilhado_runtime;resultados=[]
    for fonte,pedido,rascunho in casos:
        estado.substituir('mental',criar_estado_mental_inicial())
        historico=[{'role':'user','content':fonte},
            {'role':'assistant','content':'Eu faço experimentos e uso cartões todos os dias.'}]
        for i in range(5):historico.extend([{'role':'user','content':f'Observei a nuvem {i}.'},
            {'role':'assistant','content':'Você inventou um método novo.'}])
        estado.atualizar_campos('memoria_conversa',messages=historico)
        ini=len(falas);ih=len(envios)
        root._resposta_ia_runtime.processar(pedido,origem='teste_modo_pessoal')
        p=estado.mental['plano_turno_atual']
        resultados.append({'fonte':fonte,'pedido':pedido,'rascunho':rascunho,
            'respostas':falas[ini:],'envios':envios[ih:],'plano':p,
            'historico':root._memoria_conversa_get('messages',[])})
    sys.__stdout__.write('MODO_PESSOAL_JSON='+json.dumps({'casos':resultados,'efeitos':efeitos,
        'audio_gerado':False},ensure_ascii=False,default=str)+'\n')
''')


def coletar_factory(perfil: Path) -> dict:
    r = subprocess.run([sys.executable, '-B', '-c', CODIGO_FACTORY, str(perfil), json.dumps(CASOS)],
        cwd=Path(__file__).resolve().parents[2], env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=90)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    return json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('MODO_PESSOAL_JSON=')))


def test_factory_limita_descricao_sem_fonte_em_dominios_distintos(tmp_path):
    d = coletar_factory(tmp_path)
    assert not d['efeitos'] and not d['audio_gerado']
    for c in d['casos']:
        assert any(f['texto'] == c['fonte'] for f in c['plano']['relatos_usuario'])
        assert len(c['respostas']) == 1
        assert c['respostas'][0] != c['rascunho'], 'autoria sem apoio foi publicada na composição'
        assert c['fonte'] in c['respostas'][0]
        assert not c['plano']['autoriza_execucao'] and not c['plano']['comandos']
