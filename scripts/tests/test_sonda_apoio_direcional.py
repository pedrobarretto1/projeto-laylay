"""Contraprovas do estudo sem promover similaridade/parecer a autorização."""
import pytest

from scripts.analises.sonda_apoio_direcional import painel, pedido_publico, conferir_revisor


def test_painel_esconde_curadoria_do_pedido_ao_modelo():
    casos = painel()
    publicos = pedido_publico(casos)
    assert len(casos) == 24 and len({c['id'] for c in casos}) == 24
    assert all(set(p) == {'id', 'fonte', 'proposicao', 'pergunta'} for p in publicos)
    assert all(type(c['apoio_esperado']) is type(c['pertinencia_esperada']) is bool for c in casos)


@pytest.mark.parametrize('ida,volta', [('limite_ida', 'limite_volta'), ('disjuncao_ida', 'disjuncao_volta')])
def test_painel_contem_pares_identicos_com_direcao_de_apoio_diferente(ida, volta):
    casos = {c['mecanismo']: c for c in painel()}
    a, b = casos[ida], casos[volta]
    assert a['fonte'] == b['proposicao'] and a['proposicao'] == b['fonte']
    assert a['apoio_esperado'] is True and b['apoio_esperado'] is False


def test_painel_separa_apoio_de_pertinencia_com_mesmo_par_textual():
    casos = {c['mecanismo']: c for c in painel()}
    a, b = casos['relato_iot'], casos['parafrase_irrelevante']
    assert (a['fonte'], a['proposicao']) == (b['fonte'], b['proposicao'])
    assert a['pergunta'] != b['pergunta']
    assert a['apoio_esperado'] is b['apoio_esperado'] is True
    assert a['pertinencia_esperada'] is True and b['pertinencia_esperada'] is False


@pytest.fixture(scope='module')
def revisoes():
    return conferir_revisor(painel())


@pytest.mark.parametrize('indice', range(24))
def test_revisor_atual_nao_usa_parecer_llm_inventado_como_prova(revisoes, indice):
    c, r = painel()[indice], revisoes[indice]
    revisao = r['revisao']
    unidade = revisao['proposicoes'][0]
    esperado = ('literal_integral_na_fonte' if c['mecanismo'] in {'literal', 'literal_irrelevante'}
                else 'parafrase_estrutural_conferida' if c['mecanismo'] == 'estrutural'
                else 'apoio_semantico_pendente')
    assert unidade['estado'] == esperado
    assert revisao['semantica_verificada'] is revisao['prova_implicacao'] is revisao['autoriza_execucao'] is False
    assert unidade['pode_confirmar_fato_externo'] is False
    if c['apoio_esperado'] is False:
        assert c['proposicao'] not in r['fala_realizada']
