"""Categoria perguntada e preferência pessoal exigem apoios distintos."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.tests.test_retomada_usuario_preserva_autoria import plano_com_fonte
from mente_laylay.cognicao.fundamentacao_factual import avaliar_nucleo_retomada_usuario
from mente_laylay.cognicao.plano_turno import verificar_fala_turno


CASOS = [
    ('eu prefiro Firefox', 'eu prefiro rock', 'qual aplicativo eu prefiro'),
    ('eu gosto de rock', 'eu gosto de Firefox', 'qual gênero eu gosto'),
    ('eu prefiro Firefox', 'eu prefiro rock', 'qual aplicativo eu tinha dito preferir'),
    ('eu gosto de rock', 'eu gosto de Firefox', 'qual gênero eu disse gostar'),
]


def plano_duas_fontes(fonte, distrator, pedido):
    plano = plano_com_fonte(fonte, pedido, f'Você contou: «{distrator}».')
    plano['relatos_usuario'].append({'id': 'dialogo:usuario:3:' + hashlib.sha256(distrator.encode()).hexdigest(),
        'texto': distrator, 'autor': 'usuario', 'origem': 'historico_conversa', 'status': 'relatado_pelo_usuario'})
    return plano


@pytest.mark.parametrize('fonte,distrator,pedido', CASOS)
def test_consulta_de_categoria_nao_admite_preferencia_de_outra_categoria(fonte, distrator, pedido):
    plano = plano_duas_fontes(fonte, distrator, pedido)
    ruim = f'Você contou: «{distrator}».'
    r = avaliar_nucleo_retomada_usuario(ruim, plano=plano)
    assert r is not None, 'pergunta pessoal implícita ficou fora da conferência compartilhada'
    assert not r['admissivel'], 'existência da preferência foi usada como prova da categoria perguntada'
    assert verificar_fala_turno(ruim, plano=plano)['fala'] != ruim


def coletar_factory(perfil: Path, positivo: bool) -> dict:
    from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY
    casos = [(f, p, f'Você contou: «{d}».') for f, d, p in CASOS]
    codigo = CODIGO_FACTORY
    assert codigo.count("'audio_gerado':False") == 1
    codigo = codigo.replace("'audio_gerado':False", "'audio_gerado':False,'catalogo_compartilhado':root._composicao_turno_runtime._servicos.get('_catalogo_aplicativos_runtime') is root._catalogo_aplicativos_runtime")
    bloco = "historico=[{'role':'user','content':fonte},"
    assert codigo.count(bloco) == 1
    codigo = codigo.replace(bloco, bloco + "{'role':'user','content':" + repr({p: d for _, d, p in CASOS}) + ".get(pedido,'')},")
    if positivo:
        folha = "proposta={'suporte_proposicoes':[{'texto':rascunho,'fontes':[]}],'comandos':[]}"
        assert codigo.count(folha) == 1
        codigo = codigo.replace(folha, "texto_proposto=rascunho\n"
            "    try:tarefa=json.loads(kwargs['json']['messages'][-1]['content'])\n"
            "    except (ValueError,TypeError):tarefa={}\n"
            "    if isinstance(tarefa,dict) and 'retomada_usuario_sem_nucleo_conferido' in tarefa.get('problemas',[]):\n"
            "        texto_proposto=" + repr({p: f'Você contou: «{f}».' for f, _, p in CASOS}) + ".get(tarefa.get('mensagem_atual'),rascunho)\n"
            "    proposta={'suporte_proposicoes':[{'texto':texto_proposto,'fontes':[]}],'comandos':[]}")
    r = subprocess.run([sys.executable, '-B', '-c', codigo, str(perfil), json.dumps(casos)],
        cwd=Path(__file__).resolve().parents[2], env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=100)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    return json.loads(next(l.split('=', 1)[1] for l in r.stdout.splitlines() if l.startswith('MODO_PESSOAL_JSON=')))


@pytest.mark.parametrize('positivo', [False, True])
def test_factory_liga_pergunta_implicita_a_categoria_sem_executar_nada(positivo, tmp_path):
    d = coletar_factory(tmp_path, positivo)
    assert not d['efeitos'] and not d['audio_gerado']
    assert d['catalogo_compartilhado'], 'composição filtrada perdeu o owner do catálogo de aplicativos'
    for c, (fonte, distrator, _) in zip(d['casos'], CASOS):
        assert any(f['texto'] == fonte for f in c['plano']['relatos_usuario'])
        assert any(f['texto'] == distrator for f in c['plano']['relatos_usuario'])
        assert len(c['respostas']) == 1
        assert c['plano']['cooperacao_categoria_preferencia']['publicado']
        assert not c['plano']['cooperacao_categoria_preferencia']['autoriza_execucao']
        assert c['respostas'] != [f'Você contou: «{distrator}».'], 'composição publicou categoria errada'
        if positivo: assert c['respostas'] == [f'Você contou: «{fonte}».']
        assert not c['plano']['autoriza_execucao'] and not c['plano']['comandos']


@pytest.mark.parametrize('longo', [False, True])
def test_pesquisa_publica_fonte_individual_integral_em_vez_de_resumo_truncado(longo):
    from mente_laylay.cognicao.pesquisa_contextual import pesquisar_contexto_tema
    from types import SimpleNamespace
    texto = 'Produto Teste é um aplicativo para organizar anotações e documentos.'
    if longo: texto += ' detalhe' * 120 + '.'
    def http(_url, **kw):
        params = kw.get('params', {})
        if params.get('list') == 'search':
            dados = {'query': {'search': [{'title': 'Produto Teste', 'snippet': 'Produto Teste app'}]}}
        elif params.get('titles') == 'Produto Teste app':
            dados = {'query': {'pages': {'-1': {'missing': ''}}}}
        else:
            dados = {'query': {'pages': {'42': {'pageid': 42, 'title': 'Produto Teste', 'extract': texto}}}}
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: dados)
    resultado = pesquisar_contexto_tema('Produto Teste app', requests_get=http, clock=lambda: 1000)
    assert resultado['ok']
    assert 'fontes' in resultado, 'pesquisa perdeu a identidade da página e só entregou resumo agregado'
    if longo:
        assert resultado['fontes'] == [], 'prefixo de parágrafo longo foi promovido a fonte integral'
    else:
        assert resultado['fontes'][0]['trecho'] == texto
        assert resultado['fontes'][0]['url'] == 'https://pt.wikipedia.org/wiki/Produto_Teste'


def plano_com_apoio(pedido='qual aplicativo eu prefiro', *, fonte='eu prefiro Firefox', trecho=None):
    import time
    from mente_laylay.cognicao.categoria_preferencia import montar_apoios_categoria_preferencia
    from mente_laylay.integracao.catalogo_aplicativos import CatalogoAplicativosRuntime
    from mente_laylay.cognicao.pesquisa_contextual import PesquisaContextualRuntime
    plano = plano_com_fonte(fonte, pedido, f'Você contou: «{fonte}».')
    catalogo = CatalogoAplicativosRuntime(apps_map={'firefox': 'firefox'})
    chamadas_externas = []
    def http_proibido(*args, **kwargs):
        chamadas_externas.append((args, kwargs))
        raise AssertionError('negativo de prosa não pode consultar rede')
    pesquisa = PesquisaContextualRuntime(requests_get=http_proibido)
    if trecho is not None:
        consulta = fonte.removeprefix('eu prefiro ') + ' app'
        agora = time.time()
        pesquisa.cache_tema[consulta.casefold()] = {'ts': agora, 'ttl_s': 1800, 'data': {
            'ok': True, 'resumo': trecho, 'fonte': 'pagina_lida', 'confianca': .95,
            'evidencia_obtida_em': agora, 'evidencia_validade_s': 1800,
            'fontes': [{'titulo': 'Produto Teste', 'url': 'https://example.org/produto', 'trecho': trecho}]}}
    plano['apoios_categoria_preferencia'] = montar_apoios_categoria_preferencia(
        plano, catalogo_aplicativos=catalogo, pesquisa=pesquisa if trecho is not None else None)
    assert not chamadas_externas, 'a fixture de prosa deve ser inteiramente local'
    return plano


@pytest.mark.parametrize('pedido', ['qual gênero eu não disse gostar', 'qual gênero eu nunca disse gostar'])
def test_negacao_do_dizer_nao_se_transforma_em_preferencia_positiva(pedido):
    plano = plano_com_apoio(pedido, fonte='eu gosto de rock')
    r = avaliar_nucleo_retomada_usuario('Você contou: «eu gosto de rock».', plano=plano)
    assert r is not None and not r['admissivel'], 'negação do ato foi apagada antes da conferência'


@pytest.mark.parametrize('trecho', [
    'Produto Teste é um aplicativo? Essa alegação é falsa.',
    'Produto Teste é um aplicativo. Essa alegação é falsa.',
    'Produto Teste é um aplicativo, ou melhor, um mineral.',
    'Produto Teste é um aplicativo apenas neste exemplo fictício.',
    'Produto Teste é um aplicativo caso os rumores sejam confirmados.',
    'Produto Teste é um aplicativo segundo uma hipótese ainda em investigação.',
    'Produto Teste é um aplicativo. Essa hipótese carece de comprovação.',
])
def test_pergunta_refutacao_ou_exemplo_na_pagina_nao_comprovam_categoria(trecho):
    plano = plano_com_apoio(fonte='eu prefiro Produto Teste', trecho=trecho)
    r = avaliar_nucleo_retomada_usuario('Você contou: «eu prefiro Produto Teste».', plano=plano)
    assert not r['admissivel'], 'prefixo positivo ocultou modalidade/ressalva da fonte'


@pytest.mark.parametrize('falha', ['', 'classe', 'nome', 'entidade', 'deprecated', 'qualificador'])
def test_pesquisa_de_categoria_le_declaracao_estruturada_da_entidade(falha):
    from types import SimpleNamespace
    from mente_laylay.cognicao.pesquisa_contextual import PesquisaContextualRuntime
    consultados = []
    def http(url, **kw):
        consultados.append((url, kw))
        if 'Special:EntityData' in url:
            nome = 'Outro Produto' if falha == 'nome' else 'Produto Teste'
            claim = {'id': 'Q999$claim', 'rank': 'deprecated' if falha == 'deprecated' else 'normal',
                'mainsnak': {'snaktype': 'value', 'property': 'P31', 'datatype': 'wikibase-item',
                    'datavalue': {'type': 'wikibase-entityid', 'value': {'id': 'Q7' if falha == 'classe' else 'Q40056', 'entity-type': 'item'}}}}
            if falha == 'qualificador': claim['qualifiers'] = {'P585': []}
            entidade = {'id': 'Q998' if falha == 'entidade' else 'Q999',
                'labels': {'pt': {'value': nome}}, 'claims': {'P31': [claim]}}
            dados = {'entities': {'Q999': entidade}}
        else:
            params = kw.get('params', {})
            if params.get('list') == 'search':
                dados = {'query': {'search': [{'title': 'Produto Teste', 'snippet': 'Produto Teste app'}]}}
            elif params.get('titles') == 'produto teste app':
                dados = {'query': {'pages': {'-1': {'missing': ''}}}}
            else:
                dados = {'query': {'pages': {'42': {'pageid': 42, 'title': 'Produto Teste',
                    'extract': 'Produto Teste possui informações públicas para esta consulta.',
                    'pageprops': {'wikibase_item': 'Q999'}}}}}
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: dados)
    pesquisa = PesquisaContextualRuntime(requests_get=http)
    metodo = getattr(pesquisa, 'pesquisar_categoria_entidade', None)
    assert callable(metodo), 'não existe leitura de categoria com identidade e relação estruturada'
    prova = metodo('produto teste', 'app')
    if falha:
        assert prova is None, 'categoria foi admitida sem classe, identidade ou validade da declaração'
    else:
        assert prova is not None and prova.classe_id == 'Q40056' and prova.entidade_id == 'Q999'
        antes = len(consultados)
        assert metodo('produto teste', 'app') == prova and len(consultados) == antes


@pytest.mark.parametrize('invalido', ['outro_turno', 'dict_ia', 'texto_fonte', 'contestado'])
def test_apoio_de_categoria_nao_sobrevive_a_divergencia_da_fonte_ou_ocorrencia(invalido):
    from dataclasses import replace
    plano = plano_com_apoio()
    boa = 'Você contou: «eu prefiro Firefox».'
    assert avaliar_nucleo_retomada_usuario(boa, plano=plano)['admissivel']
    if invalido == 'outro_turno':
        plano['apoios_categoria_preferencia'] = replace(plano['apoios_categoria_preferencia'], turno_id='outra')
    elif invalido == 'dict_ia':
        plano['apoios_categoria_preferencia'] = plano['apoios_categoria_preferencia'].dados.como_dict()
    elif invalido == 'texto_fonte':
        plano['relatos_usuario'][0]['texto'] = 'eu prefiro rock'
    else: plano['relatos_usuario'][0]['status'] = 'contestado'
    assert not avaliar_nucleo_retomada_usuario(boa, plano=plano)['admissivel']
