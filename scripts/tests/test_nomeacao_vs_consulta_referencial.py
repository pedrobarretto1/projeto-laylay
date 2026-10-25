"""Tipo solicitado e oração relativa não são declaração de um nome próprio."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno, extrair_entidade_explicita
from mente_laylay.cognicao.fundamentacao_factual import extrair_tema_fundamentacao


@pytest.mark.parametrize('texto',[
    'e qual banda eu falei que gosto, lá no começo?',
    'qual livro eu mencionei ontem?',
    'qual álbum você indicou?',
    'qual é mesmo o nome do jogo que eu e o Leo estamos montando?',
    'lembra do filme que nós assistimos?',
    'quais séries você comentou?',
])
def test_categoria_consultada_nao_nomeia_a_oracao_como_entidade(texto):
    retrato,_=construir_retrato_turno(texto,turno=classificar_modalidade_turno(texto),
        mente={},contexto_perceptivo={},agora=100)
    assert not retrato['entidades_explicitas'],'primeira fronteira: oração virou nome explícito'
    assert not extrair_entidade_explicita(texto)
    assert not extrair_tema_fundamentacao(texto,retrato=retrato)


@pytest.mark.parametrize('texto,nome',[
    ('conheço a banda Banda do Mar','Banda do Mar'),
    ('li o livro O Cantor e o Livro','O Cantor e o Livro'),
    ('qual livro "Eu Falei Que Gosto" você leu?','Eu Falei Que Gosto'),
    ('conhece o filme chamado Que Eu Vi Ontem?','Que Eu Vi Ontem'),
    ('o jogo chamado que eu e o Leo estamos montando','que eu e o Leo estamos montando'),
])
def test_nome_literal_ou_designacao_explicita_preservados(texto,nome):
    assert extrair_entidade_explicita(texto)['nome']==nome


def test_composicao_preserva_resposta_correta_sem_tema_inventado(tmp_path):
    codigo=textwrap.dedent(r'''
        import json,sys
        from pathlib import Path
        from types import ModuleType
        import requests
        apps=ModuleType('AppOpener');apps.open=apps.close=lambda *a,**k:False
        apps.give_appnames=lambda *a,**k:{};sys.modules['AppOpener']=apps
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        from mente_laylay.memoria_mental.registro_semantico import registrar_interacao_semantica
        respostas=[]
        def http(self,method,url,**k):
            r=requests.Response();r.status_code=200
            r._content=json.dumps({'choices':[{'message':{'content':json.dumps({'comandos':[],
                'suporte_proposicoes':[{'texto':fala,'fontes':[]}]})}}]}).encode('utf8')
            return r
        root=preparar_instalacao_isolada(Path(sys.argv[1]),requisicao_http=http)
        root._voz_runtime.falar=lambda *a,**k:False
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda f,*a,**k:respostas.append(f)or True)
        estado=root._estado_compartilhado_runtime
        casos=[]
        for fonte,pergunta,fala in [
            ('pra descansar eu gosto de rock, principalmente Nirvana','e qual banda eu falei que gosto, lá no começo?',
             'Lá no começo, você falou que gostava de rock, especialmente Nirvana.'),
            ('o jogo que estou fazendo se chama Ponte de Papel','qual é mesmo o nome do jogo que eu e o Leo estamos montando?',
             'Você disse que o jogo se chama Ponte de Papel.')]:
            estado.substituir('mental',criar_estado_mental_inicial())
            estado.atualizar_campos('mental',registro_semantico=registrar_interacao_semantica({},texto_usuario=fonte.replace(',','').lower()))
            estado.atualizar_campos('memoria_conversa',messages=[{'role':'system','content':BASE_SYSTEM_PROMPT},
                {'role':'user','content':fonte}])
            inicio=len(respostas)
            root._resposta_ia_runtime.processar(pergunta,origem='teste_nomeacao_referencial')
            t=estado.mental['turno_atual'];p=estado.mental['plano_turno_atual']
            assert not t['retrato_id'] is None
            assert not estado.mental['retrato_turno_atual']['entidades_explicitas']
            assert any(r.get('texto')==fonte and r.get('origem')=='historico_conversa'for r in p.get('relatos_usuario',[]))
            assert respostas[inicio:]==[fala],respostas[inicio:]
            assert not t['autoriza_execucao']
        sys.__stdout__.write('NOMEACAO_OK\n')
    ''')
    r=subprocess.run([sys.executable,'-B','-c',codigo,str(tmp_path)],capture_output=True,text=True,encoding='utf8',
        cwd=Path(__file__).resolve().parents[2],env=dict(os.environ,PYTHONIOENCODING='utf-8',LAYLAY_NEURAL_MODE='off'),timeout=90)
    assert r.returncode==0,r.stdout[-3000:]+r.stderr[-2000:]
