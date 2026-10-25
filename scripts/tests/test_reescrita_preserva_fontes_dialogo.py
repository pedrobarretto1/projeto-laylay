"""Reparo de formato não pode perder a fonte que o principal já tinha."""
import json
import pytest
from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala


def test_reparo_de_formato_recebe_as_mesmas_fontes_do_dialogo():
    texto='quem vai levar o livro azul?'
    turno=classificar_modalidade_turno(texto)
    plano=planejar_turno(texto,turno=turno)
    plano['contrato_fala']=construir_contrato_semantico_fala(texto,turno=turno,plano=plano)
    fonte='A Bia vai levar um livro azul.'
    historico=[{'role':'user','content':fonte},
        *[{'role':'user','content':f'Observei uma nuvem {i}.'}for i in range(7)],
        {'role':'user','content':texto}]
    chamadas=[]
    def enviar(mensagens,**kwargs):
        chamadas.append((mensagens,kwargs))
        return json.dumps({'fala':'A Bia vai levar o livro azul.','comandos':[]})
    preparada=preparar_resposta_para_execucao(texto,'{"fala":',enviar_mensagem_cb=enviar,
        limpar_texto_fala_cb=lambda f:f,fallback_fala='fallback',memoria_sqlite=None,
        contexto_comunicacao={'plano_turno':plano,'mensagens':historico},log=lambda *a:None)
    assert chamadas,'não alcançou a fronteira de reparo'
    for mensagens,kw in chamadas:
        fontes=[]
        for m in mensagens:
            if '\nFONTES_JSON='in str(m.get('content')):
                fontes+=json.JSONDecoder().raw_decode(m['content'].split('\nFONTES_JSON=',1)[1])[0]
        assert any(f.get('t',f.get('content'))==fonte and f['role']=='user'for f in fontes), 'fonte perdida entre autoria e reparo'
    assert preparada['fala']=='A Bia vai levar o livro azul.'
    assert not preparada['comandos']


def test_factory_transporta_fonte_original_ao_reparo_de_formato(tmp_path):
    import os
    from pathlib import Path
    import subprocess
    import sys
    import textwrap
    codigo=textwrap.dedent(r'''
        import json,sys
        from pathlib import Path
        from types import ModuleType
        import requests
        apps=ModuleType('AppOpener');apps.open=apps.close=lambda *a,**k:False
        apps.give_appnames=lambda *a,**k:{};sys.modules['AppOpener']=apps
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT
        enviados=[];respostas=[];efeitos=[]
        fonte='A Bia vai levar um livro azul.'
        pergunta='quem vai levar o livro azul?'
        fala='A Bia vai levar o livro azul.'
        def http(self,method,url,**k):
            enviados.append(k['json'])
            bruto='{"fala":' if len(enviados)==1 else json.dumps({'comandos':[],
                'suporte_proposicoes':[{'texto':fala,'fontes':[]}]})
            r=requests.Response();r.status_code=200
            r._content=json.dumps({'choices':[{'message':{'content':bruto}}]}).encode('utf8')
            return r
        root=preparar_instalacao_isolada(Path(sys.argv[1]),requisicao_http=http)
        root._voz_runtime.falar=lambda *a,**k:False
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda f,*a,**k:respostas.append(f)or True)
        from mente_laylay.autonomia import coordenador_intencao,roteador_intencao
        coordenador_intencao.executar_intencao=roteador_intencao.executar_intencao=lambda *a,**k:efeitos.append(a)or False
        root._estado_compartilhado_runtime.atualizar_campos('memoria_conversa',messages=[
            {'role':'system','content':BASE_SYSTEM_PROMPT},{'role':'user','content':fonte},
            *[{'role':'user','content':f'Observei uma nuvem {i}.'}for i in range(7)]])
        root._resposta_ia_runtime.processar(pergunta,origem='teste_recuperacao_fontes')
        assert enviados[0]['messages'][-1]['content']==pergunta
        assert len(enviados)>=2
        fontes_principais=[]
        for m in enviados[0]['messages']:
            if '\nFONTES_JSON='in str(m.get('content')):
                fontes_principais+=json.JSONDecoder().raw_decode(m['content'].split('\nFONTES_JSON=',1)[1])[0]
        assert fontes_principais
        for pedido in enviados[1:]:
            fontes=[]
            for m in pedido['messages']:
                if '\nFONTES_JSON='in str(m.get('content')):
                    fontes+=json.JSONDecoder().raw_decode(m['content'].split('\nFONTES_JSON=',1)[1])[0]
            assert any(f.get('t',f.get('content'))==fonte and f['role']=='user'for f in fontes),enviados
            assert fontes==fontes_principais,'reparo mudou a identidade das ocorrências selecionadas'
        assert respostas==[fala],respostas
        assert not efeitos
        sys.__stdout__.write('RECUPERACAO_FONTES_OK\n')
    ''')
    r=subprocess.run([sys.executable,'-B','-c',codigo,str(tmp_path)],capture_output=True,text=True,
        encoding='utf8',cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ,PYTHONIOENCODING='utf-8',LAYLAY_NEURAL_MODE='off'),timeout=90)
    assert r.returncode==0,r.stdout[-3500:]+r.stderr[-2000:]


@pytest.mark.parametrize('limite', ['turno_divergente', 'intervalo_excessivo', 'pacote_fechado'])
def test_reparo_nao_reutiliza_fontes_sem_vinculo_ou_admissao(limite, monkeypatch):
    from mente_laylay.autonomia import processamento_resposta_ia as processamento
    texto='quem vai levar o livro azul?'
    plano=planejar_turno(texto,turno=classificar_modalidade_turno(texto))
    if limite=='turno_divergente':
        plano['texto_usuario']='outra pergunta'
    fonte='A Bia vai levar um livro azul.'
    if limite=='intervalo_excessivo':
        fonte+=' Detalhe adicional.'*300
    historico=[{'role':'user','content':fonte},
        *[{'role':'user','content':f'Observei uma nuvem {i}.'}for i in range(7)],
        {'role':'user','content':texto}]
    chamadas=[]
    def enviar(mensagens,**kwargs):
        chamadas.append(mensagens)
        return json.dumps({'fala':'A Bia vai levar o livro azul.','comandos':[]})
    if limite=='pacote_fechado':
        def corrigir(texto, bruto, callback):
            return callback([{'role':'system','content':'contrato fechado'},
                {'role':'user','content':texto}],_tipo_chamada='reparo_json',_contexto_fechado=True)
        monkeypatch.setattr(processamento,'corrigir_saida_malformada_da_ia',corrigir)
    preparada=preparar_resposta_para_execucao(texto,'{"fala":',enviar_mensagem_cb=enviar,
        limpar_texto_fala_cb=lambda f:f,fallback_fala='fallback',memoria_sqlite=None,
        contexto_comunicacao={'plano_turno':plano,'mensagens':historico},log=lambda *a:None)
    assert chamadas
    assert all('FONTES_JSON=' not in str(mensagens) for mensagens in chamadas)
    assert not preparada['comandos']
