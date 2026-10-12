"""Composição instalada com efeitos/modelo/voz isolados, não sessão main."""
import pytest

from scripts.analises.sonda_escopo_propostas_mistas import coletar


@pytest.fixture(scope="module")
def escopo_instalado():
    return coletar()


def test_composicao_instala_validador_e_dispatcher_com_a_mesma_mente(escopo_instalado):
    assert all(escopo_instalado["instalacao"].values())
    assert escopo_instalado["fontes_estaveis"]
    assert escopo_instalado["efeitos_externos_executados"] is False


@pytest.mark.parametrize("indice", range(10))
def test_admissao_e_porta_executor_conservam_escopo_exato(escopo_instalado, indice):
    resultado = escopo_instalado["resultados"][indice]
    assert resultado["falhas"] == []
    assert resultado["proposta_vinculada"] is True
    assert resultado["ocorrencia_vinculada"] is True
    assert resultado["recebidos_porta_executor"] == resultado["caso"]["esperados"]
    if indice < 6:
        assert resultado["validacao"]["atos_autorizados_vinculados"] == [0]
        assert len(resultado["validacao"]["rejeitados"]) == 1


@pytest.mark.parametrize("indice", range(3))
def test_pipeline_instalado_publica_so_pedido_valido_e_chega_a_conclusao(escopo_instalado, indice):
    resultado = escopo_instalado["pipelines_instalados"][indice]
    assert resultado["falhas"] == []
    # A API externa processar() retorna None por contrato. Conclusão se prova
    # pela publicação/porta de fala, não por um bool artificial no harness.
    assert resultado["plano"]["fase"] == "falha_execucao"
    assert len(resultado["recebidos"]) == 1
    assert len(resultado["plano"]["comandos"]) == 1
    assert resultado["falas_porta_isolada"]
    assert all(c["confirmado"] is not True for c in resultado["plano"]["comandos"])
