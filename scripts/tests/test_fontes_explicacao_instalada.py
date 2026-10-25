"""Recuperar páginas para o pedido atual não libera explicação sem apoio."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope='module')
def fontes_instaladas(tmp_path_factory):
    codigo = textwrap.dedent(r'''
        import json,sys
        from pathlib import Path
        from types import SimpleNamespace
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        from scripts.tests.test_pesquisa_multifonte import _Resposta
        from mente_laylay.cognicao.pesquisa_multifonte import pesquisar_evidencias_multifonte,extrair_consulta_didatica
        root=preparar_instalacao_isolada(Path(sys.argv[1]))
        from mente_laylay.integracao.cliente_llm_runtime import ClienteLLMRuntime
        from mente_laylay.integracao.registro_conversa_llm import ResultadoModelo
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        estado,runtime=root._estado_compartilhado_runtime,root._resposta_ia_runtime
        original=runtime._contexto_getter
        pesquisa=root._pesquisa_contextual_runtime
        root._composicao_turno_runtime._servicos['_pesquisa_contextual_runtime']=pesquisa
        assert root._composicao_turno_runtime._servicos['_pesquisa_contextual_runtime'] is root._pesquisa_contextual_runtime
        assert pesquisa.modo_multifonte=='desativado'
        publicadas,casos=[],[]
        root._voz_runtime.falar=lambda *a,**k:False
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda t,*a,**k:publicadas.append(t) or True)
        pares=[('me explica fotossíntese','fotossíntese','Fotossíntese transforma energia luminosa em energia química durante a produção de compostos orgânicos.'),
               ('me ensina o que é uma variável em Python','variável em Python','Uma variável em Python representa um nome associado a um objeto durante a execução do programa.'),
               ('me explica pressão atmosférica','pressão atmosférica','A pressão atmosférica representa a força exercida pelo ar por unidade de área de uma superfície.')]
        pares=[(*p,'literal') for p in pares]
        pares.extend([(pares[1][0],pares[1][1],pares[1][2],'parafrase'),
                      (pares[0][0],pares[0][1],pares[0][2],'sem_paginas'),
                      ('me explica minha senha','minha senha','Uma explicação inventada sobre o conteúdo pessoal.','contextual')])
        for modo in [False,True]:
            for pedido,tema,trecho,variante in pares:
                chamadas,efeitos,enviados=[],[],[]
                urls=['https://escola.example/conceito','https://universidade.example/conceito']
                def get(url,**k):
                    chamadas.append({'url':url,'params':k.get('params')})
                    if 'duckduckgo.com' in url:
                        return _Resposta('',url=url,status=503)
                    if 'bing.com/search' in url:
                        html=''.join('<li class="b_algo"><h2><a href="'+u+'">'+tema+'</a></h2></li>' for u in urls)
                        return _Resposta(html,url=url)
                    assert url in urls,url
                    conteudo=trecho if variante!='sem_paginas' else 'O documento descreve os horários e serviços de uma biblioteca municipal.'
                    return _Resposta('<p>'+conteudo+'</p>',url=url)
                # Controle no MESMO coletor: páginas e assunto são conferíveis.
                controle=pesquisar_evidencias_multifonte(extrair_consulta_didatica(pedido),requests_get=get) if variante!='contextual' else {}
                if variante in {'literal','parafrase'}:
                    assert controle['ok'] and len(controle['fontes'])==2,controle
                chamadas.clear()
                pesquisa.requests_get=get
                pesquisa.cache_tema.clear()
                estado.substituir('mental',criar_estado_mental_inicial())
                estado.atualizar_campos('memoria_conversa',messages=[])
                def modelo(self,r):
                    enviados.append(r.tipo_chamada)
                    proposta=trecho+(' Portanto, todas as outras situações seguem a mesma regra.' if variante=='parafrase' else '')
                    return ResultadoModelo(json.dumps({'comandos':[],'emocao':'calma','nivel_emocao':1,
                        'suporte_proposicoes':[{'texto':proposta,'fontes':[urls[0]]}]}),True)
                ClienteLLMRuntime.executar=modelo
                ctx=original()
                ctx['usar_modo_rapido']=lambda t:modo
                def impedir(*a,**k):
                    efeitos.append(True)
                    return False
                ctx['contexto_dispatch_runtime']=SimpleNamespace(montar=lambda:{'executar_intencao':impedir})
                runtime._contexto_getter=lambda:ctx
                inicio=len(publicadas)
                runtime.processar(pedido,origem='teste_fontes_explicacao')
                p=estado.mental['plano_turno_atual']
                casos.append({'pedido':pedido,'trecho':trecho,'modo':modo,'variante':variante,'chamadas':chamadas,'efeitos':efeitos,
                    'fontes':p.get('fundamentacao_factual'),'contrato':p.get('contrato_fala'),
                    'verificacao':p.get('ultima_verificacao'),'publicadas':publicadas[inicio:],'enviados':enviados,
                    'controle':controle,'modo_multifonte':pesquisa.modo_multifonte})
        sys.__stdout__.write('FONTES_INSTALADAS '+json.dumps(casos,ensure_ascii=False,default=str)+'\n')
    ''')
    p=subprocess.run([sys.executable,'-c',codigo,str(tmp_path_factory.mktemp('fontes_instaladas'))],
        cwd=Path(__file__).resolve().parents[2],capture_output=True,text=True,encoding='utf8',
        env=dict(os.environ,PYTHONIOENCODING='utf-8',LAYLAY_NEURAL_MODE='off'),timeout=90)
    assert p.returncode==0,p.stdout[-4000:]+p.stderr[-3000:]
    casos=json.loads(next(l.removeprefix('FONTES_INSTALADAS ') for l in p.stdout.splitlines() if l.startswith('FONTES_INSTALADAS ')))
    if destino:=os.environ.get('LAYLAY_EVIDENCIA_FONTES_EXPLICACAO'):
        Path(destino).write_text(json.dumps(casos,ensure_ascii=False,indent=2),encoding='utf8')
    return casos


@pytest.mark.parametrize('indice',[0,1,2,6,7,8])
def test_pedido_didatico_recupera_fontes_sem_liberar_influencia_irrestrita(fontes_instaladas,indice):
    c=fontes_instaladas[indice]
    assert c['controle']['ok'] is True
    assert c['contrato']['roteiro_concreto']['estrategia']=='explicacao_didatica'
    assert c['fontes'].get('fontes'), 'primeira fronteira: pedido didático não é encaminhado ao coletor existente'
    assert len(c['fontes']['fontes'])==2 and c['fontes']['pesquisa_didatica'] is True
    assert c['modo_multifonte']=='desativado'
    r=c['verificacao']['revisao_suporte_autoria']
    assert r['obrigacao_fonte_individual'] is True
    assert r['proposicoes'][0]['estado']=='literal_integral_na_fonte'
    assert r['semantica_verificada'] is r['prova_implicacao'] is r['autoriza_execucao'] is False
    assert len(c['publicadas'])==1 and '«'+c['trecho']+'»' in c['publicadas'][0]
    assert not c['efeitos']


@pytest.mark.parametrize('indice',[3,4,5,9,10,11])
def test_busca_nao_converte_pagina_ou_referencia_contextual_em_prova(fontes_instaladas,indice):
    c=fontes_instaladas[indice]
    assert len(c['publicadas'])==1 and not c['efeitos']
    r=c['verificacao']['revisao_suporte_autoria']
    assert r['obrigacao_fonte_individual'] is True
    assert r['semantica_verificada'] is r['prova_implicacao'] is r['autoriza_execucao'] is False
    if c['variante']=='parafrase':
        assert len(c['fontes']['fontes'])==2
        assert 'todas as outras situações' not in c['publicadas'][0]
        assert r['proposicoes'][0]['estado']=='apoio_semantico_pendente'
    else:
        assert not c['fontes'].get('fontes') and c['trecho'] not in c['publicadas'][0]
    if c['variante']=='contextual':
        assert c['chamadas']==[], 'consulta pessoal não é um assunto público resolvido'
