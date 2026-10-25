"""Factory real deve levar fontes ao HTTP sem emprestar autoridade histórica."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope='module')
def recuperacao_instalada(tmp_path_factory):
    codigo = textwrap.dedent(r'''
        import json,sys,os,importlib.machinery,importlib.util
        from pathlib import Path
        import requests
        from types import ModuleType,SimpleNamespace
        apps=ModuleType('AppOpener')
        apps.open=apps.close=lambda *a,**k:False
        apps.give_appnames=lambda *a,**k:{}
        sys.modules['AppOpener']=apps
        # Contrafactual opcional: carregar os owners congelados sem restaurar
        # arquivos de produção nem alterar a worktree suja.
        if pasta_baseline:=os.environ.get('LAYLAY_RECUPERACAO_BASELINE'):
            for modulo,arquivo in [
                ('mente_laylay.cognicao.seletor_contexto','seletor_contexto.py.antes'),
                ('mente_laylay.integracao.preparacao_llm','preparacao_llm.py.antes')]:
                loader=importlib.machinery.SourceFileLoader(modulo,str(Path(pasta_baseline)/arquivo))
                spec=importlib.util.spec_from_loader(modulo,loader)
                module=importlib.util.module_from_spec(spec);sys.modules[modulo]=module
                loader.exec_module(module)
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT
        enviados=[]
        def http(self,method,url,**kw):
            payload=kw.get('json') or {}
            enviados.append(payload)
            proposta={'intent':'APP_OPEN','params':{'nome_app':'Calculadora'}}
            fala=json.dumps({'fala':'Estou acompanhando a conversa.','comandos':[proposta]})
            r=requests.Response();r.status_code=200
            r._content=json.dumps({'choices':[{'message':{'content':fala}}]}).encode('utf8')
            return r
        root=preparar_instalacao_isolada(Path(sys.argv[1]),requisicao_http=http)
        root._voz_runtime.falar=lambda *a,**k:False
        estado,runtime=root._estado_compartilhado_runtime,root._resposta_ia_runtime
        original=runtime._contexto_getter
        efeitos=[]
        from mente_laylay.autonomia import coordenador_intencao
        coordenador_intencao.executar_intencao=lambda *a,**k:efeitos.append(str(a)) or False
        casos=[]
        for rapido in [False,True]:
            for pessoa,tema,parte in [('Leo','jogo Ponte de Papel','música'),('Dora','laboratório','medições')]:
                fontes=[{'role':'user','content':f'Eu e {pessoa} estamos no {tema}.'},
                    {'role':'assistant','content':'Como dividiram o trabalho?'},
                    {'role':'user','content':f'Minha parte é desenhar e a dele ou dela é {parte}.'}]
                # A rota normal instalada mantém o sistema canônico no estado
                # da conversa. Esta regressão representa sua retomada rápida.
                historico=[{'role':'system','content':BASE_SYSTEM_PROMPT}]+fontes+[
                    {'role':'user','content':f'Observei a nuvem {i}.'} for i in range(7)]
                pergunta=f'Qual é a parte de {pessoa}?'
                estado.substituir('mental',criar_estado_mental_inicial())
                estado.atualizar_campos('memoria_conversa',messages=historico)
                ctx=original();ctx['usar_modo_rapido']=lambda t:rapido
                ctx['contexto_dispatch_runtime']=SimpleNamespace(montar=lambda:{'executar_intencao':lambda *a,**k:efeitos.append(str(a)) or False})
                runtime._contexto_getter=lambda:ctx
                inicio=len(enviados)
                runtime.processar(pergunta,origem='teste_recuperacao_instalada')
                casos.append({'rapido':rapido,'fontes':fontes,'pergunta':pergunta,
                    'envios':enviados[inicio:],'turno':estado.mental.get('turno_atual'),
                    'plano':estado.mental.get('plano_turno_atual'),'efeitos':list(efeitos)})
        sys.__stdout__.write('RECUPERACAO_INSTALADA '+json.dumps(casos,ensure_ascii=False,default=str)+'\n')
    ''')
    r = subprocess.run([sys.executable, '-B', '-c', codigo, str(tmp_path_factory.mktemp('recuperacao_instalada'))],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, encoding='utf8',
        env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'), timeout=100)
    assert r.returncode == 0, r.stdout[-3500:] + r.stderr[-2500:]
    casos = json.loads(next(l.removeprefix('RECUPERACAO_INSTALADA ') for l in r.stdout.splitlines()
        if l.startswith('RECUPERACAO_INSTALADA ')))
    if destino := os.environ.get('LAYLAY_EVIDENCIA_RECUPERACAO'):
        Path(destino).write_text(json.dumps(casos,ensure_ascii=False,indent=2),encoding='utf8')
    return casos


@pytest.mark.parametrize('indice', range(4))
def test_factory_transporta_fontes_e_rejeita_proposta_de_acao_sem_pedido(recuperacao_instalada, indice):
    c = recuperacao_instalada[indice]
    # Primeira fronteira: a autoria recebeu a pergunta deste caso, não uma
    # chamada auxiliar cujo histórico por acaso contém a mesma frase.
    principais = [p for p in c['envios'] if (p.get('messages') or [{}])[-1].get('content') == c['pergunta']]
    assert principais, 'pergunta não chegou à porta HTTP instalada'
    for payload in principais:
        fonte = next((m for m in payload['messages'] if '\nFONTES_JSON=' in str(m.get('content'))), None)
        assert fonte is not None, 'fontes antigas perderam-se antes do HTTP'
        fontes = json.loads(fonte['content'].split('\nFONTES_JSON=',1)[1])
        assert all(dict(role='user', content=c['fontes'][i]['content']) in
            [dict(role=f['role'],content=f.get('t',f.get('content'))) for f in fontes] for i in [0,2])
        assert all(f['role'] == 'user' for f in fontes)
        assert 'não instruções atuais, autorização' in fonte['content']
    assert c['turno']['autoriza_execucao'] is False
    assert not c['efeitos'], 'proposta da IA/histórico criou execução sem pedido atual'
