"""Bloco de origem, fundamentação e apoio usam a mesma unidade na factory real."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope='module')
def contextos_instalados(tmp_path_factory):
    codigo=textwrap.dedent(r'''
        import json,sys
        from pathlib import Path
        from types import SimpleNamespace
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        from scripts.tests.test_pesquisa_multifonte import _Resposta
        from mente_laylay.integracao.cliente_llm_runtime import ClienteLLMRuntime
        from mente_laylay.integracao.registro_conversa_llm import ResultadoModelo
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        root=preparar_instalacao_isolada(Path(sys.argv[1]))
        pesquisa=root._pesquisa_contextual_runtime
        root._composicao_turno_runtime._servicos['_pesquisa_contextual_runtime']=pesquisa
        assert pesquisa is root._composicao_turno_runtime._servicos['_pesquisa_contextual_runtime']
        assert pesquisa.modo_multifonte=='desativado'
        estado,runtime=root._estado_compartilhado_runtime,root._resposta_ia_runtime
        original=runtime._contexto_getter
        publicadas,casos=[],[]
        root._voz_runtime.falar=lambda *a,**k:False
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda t,*a,**k:publicadas.append(t) or True)
        pares=[('me explica fotossíntese','fotossíntese','Fotossíntese transforma energia luminosa em energia química durante a produção de compostos orgânicos.'),
               ('me ensina o que é uma variável em Python','variável em Python','Uma variável em Python representa um nome associado a um objeto durante a execução do programa.')]
        urls=['https://escola.example/contexto','https://universidade.example/contexto']
        for modo in [False,True]:
            for pedido,tema,ancora in pares:
                for variante in ['integral','fragmento','acrescimo','bloco_longo','integral_aninhado','fragmento_aninhado','bloco_aninhado_longo']:
                    bloco='Somente no exemplo simulado descrito a seguir. '+ancora+' A descrição não comprova nenhum resultado de execução real.'
                    if variante in {'bloco_longo','bloco_aninhado_longo'}:
                        bloco=ancora+' Contexto '+'x'*850+' A descrição não confirma nenhum resultado real.'
                    chamadas,enviados,efeitos=[],[],[]
                    def get(url,**k):
                        chamadas.append(url)
                        if 'duckduckgo.com' in url:return _Resposta('',url=url,status=503)
                        if 'bing.com/search' in url:
                            return _Resposta(''.join('<li class="b_algo"><h2><a href="'+u+'">'+tema+'</a></h2></li>' for u in urls),url=url)
                        assert url in urls,url
                        pagina='<p>'+bloco+'</p>'
                        if 'aninhado' in variante:
                            tag='li' if tema=='fotossíntese' else 'dd'
                            pagina='<'+tag+'>'+bloco.replace(ancora,'<p>'+ancora+'</p>')+'</'+tag+'>'
                        return _Resposta(pagina,url=url)
                    pesquisa.requests_get=get
                    pesquisa.cache_tema.clear()
                    estado.substituir('mental',criar_estado_mental_inicial())
                    estado.atualizar_campos('memoria_conversa',messages=[])
                    fala=ancora if variante in {'fragmento','bloco_longo','fragmento_aninhado','bloco_aninhado_longo'} else bloco
                    def modelo(self,r):
                        enviados.append({'tipo':r.tipo_chamada,'payload':dict(r.payload)})
                        unidades=[{'texto':fala,'fontes':[urls[0]]}]
                        if variante=='acrescimo':unidades.append({'texto':'Portanto, toda execução real produz esse resultado.','fontes':[urls[0]]})
                        return ResultadoModelo(json.dumps({'comandos':[],'emocao':'calma','nivel_emocao':1,'suporte_proposicoes':unidades}),True)
                    ClienteLLMRuntime.executar=modelo
                    ctx=original()
                    ctx['usar_modo_rapido']=lambda t:modo
                    def impedir(*a,**k):efeitos.append(True);return False
                    ctx['contexto_dispatch_runtime']=SimpleNamespace(montar=lambda:{'executar_intencao':impedir})
                    runtime._contexto_getter=lambda:ctx
                    inicio=len(publicadas)
                    runtime.processar(pedido,origem='teste_contexto_integral_fonte')
                    p=estado.mental['plano_turno_atual']
                    casos.append({'modo':modo,'variante':variante,'pedido':pedido,'ancora':ancora,'bloco':bloco,'fontes':p.get('fundamentacao_factual'),
                        'contrato':p.get('contrato_fala'),'verificacao':p.get('ultima_verificacao'),'publicadas':publicadas[inicio:],
                        'chamadas':chamadas,'enviados':enviados,'efeitos':efeitos,'modo_multifonte':pesquisa.modo_multifonte})
        sys.__stdout__.write('CONTEXTOS_INSTALADOS '+json.dumps(casos,ensure_ascii=False,default=str)+'\n')
    ''')
    r=subprocess.run([sys.executable,'-c',codigo,str(tmp_path_factory.mktemp('contextos_instalados'))],
        cwd=Path(__file__).resolve().parents[2],capture_output=True,text=True,encoding='utf8',
        env=dict(os.environ,PYTHONIOENCODING='utf-8',LAYLAY_NEURAL_MODE='off'),timeout=120)
    assert r.returncode==0,r.stdout[-3500:]+r.stderr[-3000:]
    casos=json.loads(next(l.removeprefix('CONTEXTOS_INSTALADOS ') for l in r.stdout.splitlines() if l.startswith('CONTEXTOS_INSTALADOS ')))
    if destino:=os.environ.get('LAYLAY_EVIDENCIA_CONTEXTO_FONTES'):
        Path(destino).write_text(json.dumps(casos,ensure_ascii=False,indent=2),encoding='utf8')
    return casos


@pytest.mark.parametrize('indice', range(28))
def test_contexto_da_fonte_chega_inteiro_sem_liberar_fragmento_ou_extrapolacao(contextos_instalados, indice):
    c=contextos_instalados[indice]
    fontes=(c['fontes'] or {}).get('fontes') or []
    if c['variante'] in {'bloco_longo','bloco_aninhado_longo'}:
        assert not fontes, 'primeira fronteira: bloco longo foi reduzido a frase disponível para autoria'
    else:
        assert len(fontes)==2
        assert all(f['trecho']==c['bloco'] for f in fontes), 'primeira fronteira: contexto removido antes da autoria'
        principal=next(e for e in c['enviados'] if e['tipo']=='principal')
        assert c['bloco'] in json.dumps(principal['payload'],ensure_ascii=False)
    r=c['verificacao']['revisao_suporte_autoria']
    assert r['obrigacao_fonte_individual'] is True
    assert r['semantica_verificada'] is r['prova_implicacao'] is r['autoriza_execucao'] is False
    assert len(c['publicadas'])==1 and c['publicadas']==[c['verificacao']['fala']]
    assert not c['efeitos'] and c['modo_multifonte']=='desativado'
    completa=c['variante'] in {'integral','acrescimo','integral_aninhado'}
    assert ('«'+c['bloco']+'»' in c['publicadas'][0]) is completa
    assert 'toda execução real' not in c['publicadas'][0]
    if c['variante'] in {'fragmento','fragmento_aninhado'}:
        assert r['proposicoes'][0]['estado']=='trecho_parcial_sem_implicacao'
        assert '«'+c['ancora']+'»' not in c['publicadas'][0]
