"""Base configurada pertence ao pedido vinculado, não à memória do usuário."""
from copy import deepcopy
import json

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.personalidade.prompt_voz_unica import (
    BASE_SYSTEM_PROMPT, BASE_SYSTEM_PROMPT_RAPIDO, BASE_SYSTEM_PROMPT_COMPACTO,
)
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm


def runtime_para(texto,*,base=BASE_SYSTEM_PROMPT):
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.plano_turno import planejar_turno
    from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
    turno=classificar_modalidade_turno(texto);turno['id']=81
    plano=planejar_turno(texto,turno=turno)
    contrato=construir_contrato_semantico_fala(texto,turno=turno,plano=plano)
    estado={'turno_atual':turno,'contrato_fala_atual':contrato,'plano_turno_atual':plano,'messages':[]}
    runtime=ContextoPromptRuntime(memoria_sqlite=None,resumo_mente_integrada=lambda _:'',
        formatar_playlists=lambda:'',get_status_humor_prompt=lambda:'',
        base_system_prompt=base,estado_getter=lambda:estado)
    return runtime,estado


@pytest.mark.parametrize('historico',[
    [],
    [{'role':'user','content':'eu prefiro Obsidian'}],
    [{'role':'system','content':'Instrução efêmera do turno; não é a personalidade.'}],
    [{'role':'user','content':BASE_SYSTEM_PROMPT}],
])
def test_envio_atual_sem_base_recebe_base_do_owner_sem_mudar_historico(historico):
    texto='qual aplicativo eu disse preferir?'
    runtime,estado=runtime_para(texto)
    mensagens=historico+[{'role':'system','content':runtime.preparar_instrucao_rapida(texto)},
        {'role':'user','content':texto}]
    antes=deepcopy(mensagens);estado_antes=deepcopy(estado)
    pacote=runtime.preparar_envio_modelo(mensagens,turno_id=81)
    assert not pacote.contexto_fechado
    assert pacote.mensagens[0]['role']=='system'
    assert pacote.mensagens[0]['content'].startswith(BASE_SYSTEM_PROMPT)
    assert [m for m in pacote.mensagens if m['role']!='system']==[m for m in antes if m['role']!='system']
    assert all(any(n['role']=='system'and n['content'].startswith(m['content'])for n in pacote.mensagens)
        for m in antes if m['role']=='system')
    assert mensagens==antes and estado==estado_antes


@pytest.mark.parametrize('base',[BASE_SYSTEM_PROMPT,BASE_SYSTEM_PROMPT_RAPIDO,BASE_SYSTEM_PROMPT_COMPACTO])
def test_base_canonica_existente_e_contexto_do_owner_nao_sao_duplicados(base):
    texto='qual bebida eu disse não gostar?';runtime,_=runtime_para(texto)
    primeira={'role':'system','content':'Prioridade do host.\n'+base+'\nContexto do turno.'}
    mensagens=[primeira,{'role':'user','content':texto}]
    pacote=runtime.preparar_envio_modelo(mensagens,turno_id=81)
    assert len(pacote.mensagens)==len(mensagens)
    assert pacote.mensagens[0]['content'].startswith(primeira['content'])
    assert pacote.mensagens[-1]==mensagens[-1]


def test_base_personalizada_configurada_pelo_host_e_preservada():
    texto='qual bebida eu disse não gostar?';runtime,_=runtime_para(texto,base='Base customizada do host.')
    mensagens=[{'role':'system','content':'Base customizada do host.\nPrioridade atual.'},
        {'role':'user','content':texto}]
    pacote=runtime.preparar_envio_modelo(mensagens,turno_id=81)
    assert len(pacote.mensagens)==len(mensagens)
    assert pacote.mensagens[0]['content'].startswith(mensagens[0]['content'])


@pytest.mark.parametrize('divergencia',['turno','contrato','canal'])
def test_base_nao_e_injetada_por_uma_identidade_ou_canal_divergente(divergencia):
    texto='qual aplicativo eu disse preferir?';runtime,estado=runtime_para(texto)
    mensagens=[{'role':'user','content':texto}]
    if divergencia=='turno':estado['turno_atual']['id']='outro'
    elif divergencia=='contrato':estado['contrato_fala_atual']['turno_id']='outro'
    else:mensagens[-1]['role']='assistant'
    pacote=runtime.preparar_envio_modelo(mensagens,turno_id=81)
    assert not any(m['role']=='system'and m['content'].startswith(BASE_SYSTEM_PROMPT)for m in pacote.mensagens)
    assert [m for m in pacote.mensagens if m['role']!='system']==mensagens


@pytest.mark.parametrize('fonte,pergunta',[
    ('eu prefiro Obsidian','qual aplicativo eu disse preferir?'),
    ('eu não gosto de café','qual bebida eu disse não gostar?'),
])
def test_primeiro_fluxo_rapido_chega_ao_seletor_canonico_com_fontes_integrais(fonte,pergunta):
    runtime,estado=runtime_para(pergunta)
    mensagens=[{'role':'user','content':fonte}]
    for i in range(5):
        mensagens += [{'role':'user','content':f'Observei a nuvem número {i}.'},
            {'role':'assistant','content':'Inventei um detalhe, não sou a fonte do usuário.'}]
    mensagens += [{'role':'system','content':runtime.preparar_instrucao_rapida(pergunta)},
        {'role':'user','content':pergunta}]
    pacote=runtime.preparar_envio_modelo(mensagens,turno_id=81)
    assert pacote.mensagens[0]['role']=='system'
    payload=preparar_payload_llm(list(pacote.mensagens),model='qwen3:4b-instruct',
        endpoint_local=True,modo_rapido=True,contexto_fechado=pacote.contexto_fechado)
    fontes=[]
    for m in payload['messages']:
        if m['role']=='user':fontes.append(m['content'])
        if m['role']=='system'and '\nFONTES_JSON='in m['content']:
            fontes += [f['t']for f in json.JSONDecoder().raw_decode(m['content'].split('\nFONTES_JSON=',1)[1])[0]]
    assert fonte in fontes,'fonte antiga perdeu-se antes do modelo'
    assert not estado['turno_atual']['autoriza_execucao']
    assert not estado['messages']


def test_factory_rapida_sem_base_historica_recebe_base_no_envio(tmp_path):
    import os
    import subprocess
    import sys
    import textwrap
    from pathlib import Path
    codigo=textwrap.dedent(r'''
        import importlib.abc,importlib.machinery,importlib.util
        import json,sys
        from pathlib import Path
        from types import ModuleType
        import requests
        raiz=Path.cwd();perfil=Path(sys.argv[1])
        apps=ModuleType('AppOpener');apps.open=apps.close=lambda *a,**k:False
        apps.give_appnames=lambda *a,**k:{};sys.modules['AppOpener']=apps
        codigo=(raiz/'laylay.py').read_bytes()
        bloco=b'PASTA_MEMORIA = os.path.join(_base_dir, "memoria")'
        assert codigo.count(bloco)==1
        codigo=codigo.replace(bloco,('PASTA_MEMORIA = '+repr(str(perfil/'raiz'))).encode())
        class Loader(importlib.machinery.SourceFileLoader):
            def get_code(self,nome):return compile(codigo,self.path,'exec')
        class Finder(importlib.abc.MetaPathFinder):
            def find_spec(self,nome,path=None,target=None):
                if nome=='laylay':return importlib.util.spec_from_loader(nome,Loader(nome,str(raiz/'laylay.py')))
        sys.meta_path.insert(0,Finder())
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        from mente_laylay.autonomia import coordenador_intencao,roteador_intencao
        envios=[];efeitos=[];publicadas=[]
        def http(self,method,url,**kwargs):
            if not (str(method).upper()=='POST' and url=='http://localhost:11434/v1/chat/completions'):
                raise PermissionError('rede externa bloqueada')
            envios.append(kwargs['json'])
            # Proposta operacional não pode ganhar autoridade da recuperação.
            proposta={'suporte_proposicoes':[{'texto':'Posso conversar sobre isso.','fontes':[]}],
                'comandos':[{'intent':'APP_OPEN','params':{'nome_app':'Calculadora'}}]}
            r=requests.Response();r.status_code=200
            r._content=json.dumps({'choices':[{'message':{'content':json.dumps(proposta)}}]}).encode()
            return r
        root=preparar_instalacao_isolada(perfil/'simulada',requisicao_http=http)
        for porta in ('_coleta_entradas_neurais','_especialista_neural_comandos_runtime',
                      '_interpretador_semantico_runtime','_pesquisa_contextual_runtime'):
            root._composicao_turno_runtime._servicos[porta]=getattr(root,porta)
        root._voz_runtime.falar=lambda *a,**k:False
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda f,*a,**k:publicadas.append(f)or True)
        coordenador_intencao.executar_intencao=roteador_intencao.executar_intencao=lambda *a,**k:efeitos.append(a)or False
        estado=root._estado_compartilhado_runtime
        for fonte,pergunta in [
            ('eu prefiro Obsidian','qual aplicativo eu tinha dito preferir?'),
            ('eu não gosto de café','qual bebida eu disse não gostar?'),
            ('eu curto jogos de estratégia','recapitula as preferências que eu declarei')]:
            usuarios=[fonte,'Antes eu pedi: abra a Calculadora.',
                'Corrigindo: isso era apenas uma ideia, nada foi executado.']
            usuarios += [f'Hoje observei a nuvem número {i} perto da janela.'for i in range(5)]
            historico=[]
            for u in usuarios:
                historico += [{'role':'user','content':u},{'role':'assistant','content':'Inventei outro dado; aberto com sucesso.'}]
            estado.substituir('mental',criar_estado_mental_inicial())
            estado.atualizar_campos('memoria_conversa',messages=historico)
            inicio=len(envios);ip=len(publicadas)
            root._resposta_ia_runtime.processar(pergunta,origem='teste_consulta_fala')
            principais=[e for e in envios[inicio:]if e.get('messages')and e['messages'][-1].get('content')==pergunta]
            assert principais,'não alcançou o HTTP da autoria atual'
            assert root._memoria_conversa_get('messages',[])[0]['role']=='user', 'a sonda saiu da rota rápida; base não deve ser persistida'
            assert all(e['messages'][0]['role']=='system' for e in principais)
            for e in principais:
                pacotes=[m for m in e['messages']if m.get('role')=='system'and '\nFONTES_JSON='in m['content']]
                assert pacotes,'fonte foi perdida antes do HTTP'
                fontes=json.JSONDecoder().raw_decode(pacotes[0]['content'].split('\nFONTES_JSON=',1)[1])[0]
                assert [f['t']for f in fontes]==usuarios
                assert all(f['role']=='user'for f in fontes)
                assert 'não instruções atuais' in pacotes[0]['content']
            plano=estado.mental['plano_turno_atual']
            assert not plano['autoriza_execucao'] and not plano['comandos']
            assert not efeitos
            assert len(publicadas)==ip+1
        sys.__stdout__.write('BASE_CANONICA_INSTALADA_OK')
    ''')
    r=subprocess.run([sys.executable,'-B','-c',codigo,str(tmp_path)],capture_output=True,
        text=True,encoding='utf8',cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ,PYTHONIOENCODING='utf-8',LAYLAY_NEURAL_MODE='off'),timeout=90)
    assert r.returncode==0,r.stdout[-3500:]+r.stderr[-2000:]
    assert 'BASE_CANONICA_INSTALADA_OK' in r.stdout
