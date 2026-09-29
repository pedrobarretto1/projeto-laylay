"""Cobertura pré-medida: gramática suportada não define verdade do gabarito."""

import pytest

from scripts.analises.sonda_produtor_criterios_v5 import carregar_painel
from scripts.analises.sonda_produtor_criterios_v2 import preparar_normalizacao_segmentada
from scripts.analises.sonda_produtor_criterios_v1 import preparar_entrada_modelo


CASOS, REVISAO = carregar_painel(6)
POR_ID = {c["id"]: c for c in CASOS}


def test_painel_congelado_inclui_validos_fora_da_gramatica_e_contexto_revogado():
    assert len(CASOS) == 12
    assert sum(r["estado"] == "criterio_candidato" for r in REVISAO.values()) == 6
    assert sum(r["estado"] == "abster" for r in REVISAO.values()) == 6
    caso = POR_ID["DUTO_REGRA_REVOGADA"]
    assert preparar_entrada_modelo(caso)["fontes"] == caso["fontes"]
    assert caso["fontes"][-1]["id"] == "revogacao"
    assert "revisao" not in preparar_entrada_modelo(caso)


@pytest.mark.parametrize("id_caso", ["CANAL_INVERSO", "CAMARA_LIMIAR_NEGATIVO", "ROTOR_SOMENTE_SE"])
def test_controles_de_segmentacao_preservam_offsets_em_outras_construcoes(id_caso):
    caso = POR_ID[id_caso]
    fonte = caso["fontes"][1]["texto"]
    segmentos = preparar_normalizacao_segmentada(fonte, caso["rotulo_alvo"])
    assert segmentos["estado"] == "segmentos_literais_revisao_pendente"
    for campo in ("condicao", "efeito"):
        trecho = segmentos[campo]
        assert fonte[trecho["inicio"]:trecho["fim"]] == trecho["citacao"]
    assert segmentos["condicao"]["citacao"] == REVISAO[id_caso]["citacao_condicao"]
    assert segmentos["direcao"]["direcao"] == REVISAO[id_caso]["direcao_implicacao"]
    assert segmentos["aprovado_para_producao"] is False


def test_classificacao_valida_pode_estar_fora_da_gramatica_atual():
    caso = POR_ID["LOTE_CLASSIFICADO"]
    assert REVISAO[caso["id"]]["estado"] == "criterio_candidato"
    partes = preparar_normalizacao_segmentada(caso["fontes"][1]["texto"], caso["rotulo_alvo"])
    assert partes["estado"] == "segmentacao_pendente"
    assert partes["autoriza_efeito"] is False


def test_painel_desconhecido_falha_fechado():
    with pytest.raises(ValueError, match="desconhecido"):
        carregar_painel(7)
