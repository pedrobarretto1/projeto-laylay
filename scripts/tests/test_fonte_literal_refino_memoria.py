"""Projeção de lookup não pode substituir a fala observada na memória."""
from copy import deepcopy

import pytest

from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.memoria_mental.contexto_compartilhado import registrar_mente_curta


def resolver_com_registro_real(texto):
    estado={};observadas=[];buscas=[]
    turno=classificar_modalidade_turno(texto)
    antes=deepcopy(turno)
    def refinar(fonte):
        observadas.append(fonte)
        estado.update(registrar_mente_curta(estado,texto_usuario=fonte))
    contexto={'normalizar_texto':normalizar_texto,'refinar_contexto_mental':refinar,
        'extrair_acao_agendada':lambda t:buscas.append(t)or None,
        'detectar_intencao_deterministica':lambda t:None,
        'turno_atual':turno}
    resultado=resolver_intencao(texto,'teste_fonte',contexto)
    assert turno==antes
    return estado,observadas,buscas,resultado


@pytest.mark.parametrize('texto',[
    'eu falei que prefiro Atlas?',
    'eu contei que não gosto de rock?',
    'Qual aplicativo eu prefiro?',
    'Por que eu trabalho no laboratório?',
    'Eu tenho um teclado?',
    'Eu criei a pasta?',
])
def test_pergunta_chega_literal_ao_registro_e_normalizada_somente_a_busca(texto):
    estado,observadas,buscas,_=resolver_com_registro_real(texto)
    assert observadas==[texto], 'primeira perda: memória recebeu a projeção lexical'
    assert not estado['registro_semantico']['alegacoes']
    assert buscas and all(t==normalizar_texto(texto)for t in buscas)


@pytest.mark.parametrize('texto',[
    'Eu prefiro Órbita.', 'Eu gosto de Jazz.', 'Eu trabalho no laboratório.',
])
def test_declaracao_preserva_autoria_e_texto_sem_perder_busca_normalizada(texto):
    estado,observadas,buscas,_=resolver_com_registro_real(texto)
    assert observadas==[texto]
    alegacoes=estado['registro_semantico']['alegacoes']
    assert len(alegacoes)==1
    assert alegacoes[0]['autor']=='usuario' and alegacoes[0]['texto']==texto
    assert buscas and all(t==normalizar_texto(texto)for t in buscas)


def test_limites_de_frase_preservam_declaracao_sem_adotar_pergunta_seguinte():
    texto='Eu gosto de jazz. Qual aplicativo eu prefiro?'
    estado,observadas,_,_=resolver_com_registro_real(texto)
    assert observadas==[texto]
    assert [a['texto']for a in estado['registro_semantico']['alegacoes']]==['Eu gosto de jazz.']


def test_registro_literal_nao_depende_de_opiniao_da_ia_para_recusar_pergunta():
    from mente_laylay.memoria_mental.registro_semantico import registrar_interacao_semantica
    fonte='eu falei que prefiro Atlas?'
    for resposta in ['', 'Você prefere Atlas.']:
        r=registrar_interacao_semantica({},texto_usuario=fonte,resposta_laylay=resposta,agora=100)
        assert not any(a['autor']=='usuario'for a in r['alegacoes'])


def test_detector_composto_preserva_fonte_literal_que_ja_recebia():
    texto='Qual aplicativo eu prefiro?';detectadas=[];projecoes=[]
    resolver_intencao(texto,'teste',{'normalizar_texto':normalizar_texto,
        'turno_atual':classificar_modalidade_turno(texto),
        'detectar_intencao_deterministica':lambda t:detectadas.append(t)or None,
        'extrair_acao_agendada':lambda t:projecoes.append(t)or None})
    assert detectadas==[texto]
    assert projecoes==[normalizar_texto(texto)]


def test_factory_nao_registra_pergunta_como_alegacao_antes_ou_depois_da_autoria(tmp_path):
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
        envios=[];efeitos=[];publicadas=[];snapshots_http=[]
        def http(self,method,url,**kwargs):
            if not (str(method).upper()=='POST' and url=='http://localhost:11434/v1/chat/completions'):
                raise PermissionError('rede externa bloqueada')
            envios.append(kwargs['json'])
            snapshots_http.append({'texto':kwargs['json']['messages'][-1].get('content'),
                'alegacoes':list(estado.mental.get('registro_semantico',{}).get('alegacoes',[]))})
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
            ('eu prefiro Obsidian','eu falei que prefiro Atlas?'),
            ('eu gosto de rock','eu contei que não gosto de rock?'),
            ('eu trabalho no laboratório','Por que eu trabalho no laboratório?')]:
            usuarios=[fonte,'Antes eu pedi: abra a Calculadora.',
                'Corrigindo: isso era apenas uma ideia, nada foi executado.']
            usuarios += [f'Hoje observei a nuvem número {i} perto da janela.'for i in range(5)]
            historico=[]
            for u in usuarios:
                historico += [{'role':'user','content':u},{'role':'assistant','content':'Inventei outro dado; aberto com sucesso.'}]
            estado.substituir('mental',criar_estado_mental_inicial())
            estado.atualizar_campos('memoria_conversa',messages=historico)
            inicio=len(envios);ip=len(publicadas);snapshot_inicio=len(snapshots_http)
            root._resposta_ia_runtime.processar(pergunta,origem='teste_consulta_fala')
            principais=[e for e in envios[inicio:]if e.get('messages')and e['messages'][-1].get('content')==pergunta]
            assert principais,'não alcançou o HTTP da autoria atual'
            registros=[s for s in snapshots_http[snapshot_inicio:]if s['texto']==pergunta]
            assert registros
            assert not any(a.get('autor')=='usuario'for s in registros for a in s['alegacoes']), 'pergunta foi promovida antes do HTTP'
            assert not any(a.get('autor')=='usuario'for a in estado.mental.get('registro_semantico',{}).get('alegacoes',[]))
            assert [m['content']for m in root._memoria_conversa_get('messages',[])if m['role']=='user'][-1]==pergunta
            plano=estado.mental['plano_turno_atual']
            assert not plano['autoriza_execucao'] and not plano['comandos']
            assert not efeitos
            assert len(publicadas)==ip+1
        sys.__stdout__.write('FONTE_LITERAL_MEMORIA_INSTALADA_OK')
    ''')
    r=subprocess.run([sys.executable,'-B','-c',codigo,str(tmp_path)],capture_output=True,
        text=True,encoding='utf8',cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ,PYTHONIOENCODING='utf-8',LAYLAY_NEURAL_MODE='off'),timeout=90)
    assert r.returncode==0,r.stdout[-3500:]+r.stderr[-2000:]
    assert 'FONTE_LITERAL_MEMORIA_INSTALADA_OK' in r.stdout
