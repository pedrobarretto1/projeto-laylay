"""Leitura atual usa cache e coordenação existentes, sem influência irrestrita."""
import threading

import pytest

from mente_laylay.cognicao.pesquisa_contextual import PesquisaContextualRuntime
from mente_laylay.cognicao.pesquisa_multifonte import consulta_didatica_autossuficiente
from scripts.tests.test_pesquisa_multifonte import _Resposta


@pytest.mark.parametrize('consulta', ['fotossíntese', 'variável em Python', 'pressão atmosférica'])
def test_tema_conceitual_autossuficiente_pode_ser_lido(consulta):
    assert consulta_didatica_autossuficiente(consulta)


@pytest.mark.parametrize('consulta,foco', [('', ''), ('minha senha', ''), ('o que você falou', ''),
    ('esta frase', ''), ('fotossíntese', 'minha planta'), ('o meu email x@y.com', ''),
    ('diferença entre eu e mim', ''), ('C:\\privado\\texto', '')])
def test_referencia_contextual_nao_e_resolvida_por_busca_publica(consulta, foco):
    chamadas=[]
    runtime=PesquisaContextualRuntime(requests_get=lambda *a,**k:chamadas.append(a))
    r=runtime.pesquisar_apoio_explicacao(consulta,foco=foco)
    assert r['ok'] is False and r['motivo']=='consulta_contextual_nao_resolvida'
    assert chamadas==[]


def http_conceito(chamadas, *, liberar=None, relevante=True):
    urls=['https://escola.example/tema','https://universidade.example/tema']
    def get(url,**k):
        chamadas.append((url,k.get('params')))
        if 'duckduckgo.com' in url:
            return _Resposta('',url=url,status=503)
        if 'bing.com/search' in url:
            return _Resposta(''.join('<li class="b_algo"><h2><a href="'+u+'">Fotossíntese</a></h2></li>' for u in urls),url=url)
        assert url in urls
        if liberar is not None:
            assert liberar.wait(timeout=3), 'o teste precisa liberar a leitura'
        trecho=('Fotossíntese transforma energia luminosa em energia química durante a produção de compostos orgânicos.'
                if relevante else 'Este documento descreve o funcionamento do serviço administrativo da biblioteca.')
        return _Resposta('<p>'+trecho+'</p>',url=url)
    return get


def test_apoio_reutiliza_cache_sem_ligar_modo_amplo_e_sem_resumo_legado():
    chamadas=[]
    instante=[100.0]
    runtime=PesquisaContextualRuntime(requests_get=http_conceito(chamadas),clock=lambda:instante[0])
    runtime.cache_tema['fotossintese']={'ts':100.,'ttl_s':1800.,'data':{'ok':True,'resumo':'resumo legado sem páginas'}}
    r=runtime.pesquisar_apoio_explicacao('fotossíntese')
    assert r['ok'] is True and len(r['fontes'])==2
    assert runtime.modo_multifonte=='desativado'
    antes=len(chamadas)
    cache=runtime.pesquisar_apoio_explicacao('fotossíntese')
    assert cache['fontes']==r['fontes'] and cache['evidencia_cache'] is True
    assert len(chamadas)==antes
    instante[0]=1901.
    assert runtime.pesquisar_apoio_explicacao('fotossíntese')['ok'] is True
    assert len(chamadas)>antes


def test_sem_paginas_pertinentes_nao_empresta_confianca_ao_modelo():
    chamadas=[]
    runtime=PesquisaContextualRuntime(requests_get=http_conceito(chamadas,relevante=False))
    r=runtime.pesquisar_apoio_explicacao('fotossíntese')
    assert r['ok'] is False and r['fontes']==[] and r['resumo']==''


def test_leitura_tardia_reutiliza_trabalho_e_nao_contamina_outra_consulta():
    chamadas=[]
    liberar=threading.Event()
    runtime=PesquisaContextualRuntime(requests_get=http_conceito(chamadas,liberar=liberar),orcamento_interativo_s=0)
    try:
        primeiro=runtime.pesquisar_apoio_explicacao('fotossíntese')
        assert primeiro['ok'] is False and primeiro['pesquisa_pendente'] is True
        assert len(runtime._pesquisas_em_andamento)==1
        evento=next(iter(runtime._pesquisas_em_andamento.values()))[0]
        segundo=runtime.pesquisar_apoio_explicacao('fotossíntese')
        assert segundo['pesquisa_pendente'] is True and len(runtime._pesquisas_em_andamento)==1
        assert runtime.pesquisar_evidencias_multifonte('outro assunto',somente_cache=True)=={}
        assert runtime.pesquisar_evidencias_multifonte('fotossíntese',foco='outro foco',somente_cache=True)=={}
    finally:
        liberar.set()
    assert evento.wait(timeout=3)
    final=runtime.pesquisar_apoio_explicacao('fotossíntese')
    assert final['ok'] is True and len(final['fontes'])==2 and final['evidencia_cache'] is True
