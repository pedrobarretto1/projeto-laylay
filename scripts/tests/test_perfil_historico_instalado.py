"""Uma retomada precisa passar pelo perfil que admite suas fontes integrais."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope='module')
def perfis_instalados(tmp_path_factory):
    codigo=textwrap.dedent(r'''
        import json,sys,os,importlib.machinery,importlib.util
        from pathlib import Path
        from types import ModuleType,SimpleNamespace
        import requests
        apps=ModuleType('AppOpener');apps.open=apps.close=lambda *a,**k:False
        apps.give_appnames=lambda *a,**k:{};sys.modules['AppOpener']=apps
        if pasta:=os.environ.get('LAYLAY_PERFIL_BASELINE'):
            for modulo in ['mente_laylay.integracao.registro_conversa_llm','mente_laylay.integracao.preparacao_llm',
                           'mente_laylay.autonomia.contexto_resposta_ia','mente_laylay.autonomia.resposta_ia_runtime']:
                loader=importlib.machinery.SourceFileLoader(modulo,str(Path(pasta)/(modulo.rsplit('.',1)[1]+'.py.antes')))
                spec=importlib.util.spec_from_loader(modulo,loader)
                module=importlib.util.module_from_spec(spec);sys.modules[modulo]=module;loader.exec_module(module)
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM
        enviados,pedidos,efeitos=[],[],[]
        def http(self,method,url,**kw):
            enviados.append(kw.get('json')or{})
            proposta={'intent':'APP_OPEN','params':{'nome_app':'Calculadora'}}
            r=requests.Response();r.status_code=200
            r._content=json.dumps({'choices':[{'message':{'content':json.dumps({
                'fala':'Estou acompanhando a conversa.','comandos':[proposta]})}}]}).encode('utf8')
            return r
        root=preparar_instalacao_isolada(Path(sys.argv[1]),requisicao_http=http)
        root._voz_runtime.falar=lambda *a,**k:False
        estado,runtime=root._estado_compartilhado_runtime,root._resposta_ia_runtime
        original_contexto=runtime._contexto_getter
        executar=RegistroModeloLLM.executar
        def registrar(self,pedido):
            pedidos.append({'tipo':pedido.tipo_chamada,'modo_rapido':pedido.modo_rapido,
                'mensagens':list(pedido.mensagens)})
            return executar(self,pedido)
        RegistroModeloLLM.executar=registrar
        from mente_laylay.autonomia import coordenador_intencao
        coordenador_intencao.executar_intencao=lambda *a,**k:efeitos.append(str(a)) or False
        casos=[]
        for assunto,pergunta,fonte in [
            ('telescópio','Qual é o modelo do meu telescópio?','Meu telescópio é o modelo Azul.'),
            ('congresso','Qual é o local do congresso?','O congresso será na biblioteca Aurora.')]:
            for tamanho,n in [('curto',3),('medio',18),('grande',45)]:
                historico=[{'role':'system','content':BASE_SYSTEM_PROMPT},
                    {'role':'user','content':fonte}, {'role':'assistant','content':'Entendi.'},
                    {'role':'user','content':'Corrigindo: é Âmbar.' if assunto=='telescópio' else 'Corrigindo: será na escola Horizonte.'}]
                historico += [{'role':'user','content':f'Hoje observei a nuvem número {i}, perto da janela da sala.'} for i in range(n)]
                estado.substituir('mental',criar_estado_mental_inicial())
                estado.atualizar_campos('memoria_conversa',messages=historico)
                ctx=original_contexto()
                candidato_rapido=ctx['usar_modo_rapido'](pergunta)
                ctx['contexto_dispatch_runtime']=SimpleNamespace(montar=lambda:{'executar_intencao':lambda *a,**k:efeitos.append(str(a)) or False})
                runtime._contexto_getter=lambda:ctx
                ini,ip=len(enviados),len(pedidos)
                runtime.processar(pergunta,origem='teste_perfil_historico')
                casos.append({'assunto':assunto,'tamanho':tamanho,'pergunta':pergunta,'fonte':fonte,
                    'correcao':historico[3]['content'],'candidato_rapido':candidato_rapido,
                    'pedidos':pedidos[ip:],'envios':enviados[ini:],
                    'autorizacao':estado.mental['turno_atual']['autoriza_execucao'],'efeitos':list(efeitos)})
        sys.__stdout__.write('PERFIS_INSTALADOS '+json.dumps(casos,ensure_ascii=False,default=str)+'\n')
    ''')
    r=subprocess.run([sys.executable,'-B','-c',codigo,str(tmp_path_factory.mktemp('perfis_instalados'))],
        cwd=Path(__file__).resolve().parents[2],capture_output=True,text=True,encoding='utf8',
        env=dict(os.environ,PYTHONIOENCODING='utf-8',LAYLAY_NEURAL_MODE='off'),timeout=100)
    assert r.returncode==0,r.stdout[-3000:]+r.stderr[-2500:]
    casos=json.loads(next(l.removeprefix('PERFIS_INSTALADOS ')for l in r.stdout.splitlines()if l.startswith('PERFIS_INSTALADOS ')))
    if destino:=os.environ.get('LAYLAY_EVIDENCIA_PERFIL_HISTORICO'):
        Path(destino).write_text(json.dumps(casos,ensure_ascii=False,indent=2),encoding='utf8')
    return casos


@pytest.mark.parametrize('indice',range(6))
def test_perfil_admite_fontes_sem_emprestar_autorizacao(perfis_instalados,indice):
    c=perfis_instalados[indice]
    assert c['candidato_rapido'] is True
    principais=[p for p in c['pedidos'] if p['tipo']=='principal'
        and p['mensagens'] and p['mensagens'][-1].get('content')==c['pergunta']]
    assert principais,'não alcançou autoria atual'
    normal=c['tamanho']=='medio'
    assert all(p['modo_rapido'] is (not normal) for p in principais), 'primeira fronteira: modo ignorou o contexto recuperável'
    envios=[p for p in c['envios'] if p.get('messages') and p['messages'][-1].get('content')==c['pergunta']]
    assert envios
    for p in envios:
        pacotes=[m for m in p['messages'] if m.get('role')=='system' and '\nFONTES_JSON=' in str(m.get('content'))]
        if c['tamanho']=='grande':
            assert not pacotes,'pacote acima dos dois perfis deve continuar recusado inteiro'
        else:
            assert pacotes,'modo selecionado perdeu a recuperação'
            fontes=json.loads(pacotes[0]['content'].split('\nFONTES_JSON=',1)[1])
            assert c['fonte'] in [f.get('t',f.get('content'))for f in fontes]
            assert c['correcao'] in [f.get('t',f.get('content'))for f in fontes]
            assert all(f['role']=='user' for f in fontes)
    assert not c['autorizacao'] and not c['efeitos']
