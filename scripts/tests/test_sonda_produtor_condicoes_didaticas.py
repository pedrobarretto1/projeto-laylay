"""Proponente não recebe gabarito nem vira autoridade sobre a fala."""

from scripts.analises.sonda_produtor_condicoes_didaticas import (
    carregar_painel, conferir_proposta, preparar_entrada_modelo,
)


CASOS, GABARITO = carregar_painel()
POR_ID = {item["id"]: item for item in CASOS}


def _proposta(id_caso, condicoes, conectivo, implicacao, *, representavel=True):
    return conferir_proposta(POR_ID[id_caso], GABARITO[id_caso], {
        "representavel": representavel,
        "condicoes": condicoes,
        "conectivo_condicoes": conectivo,
        "direcao_implicacao": implicacao,
    })


def test_painel_novo_tem_seis_casos_e_gabarito_nao_vaza_ao_modelo():
    assert len(CASOS) == len(GABARITO) == 6
    assert set(POR_ID) == set(GABARITO)
    entrada = preparar_entrada_modelo(POR_ID["LOGIN_ONLY"])
    assert set(entrada) == {"fonte", "referentes", "efeito"}
    assert "somente quando" in entrada["fonte"]
    assert "condicoes_necessarias" not in str(entrada)


def test_proposta_exata_ainda_nao_esta_autorizada_para_fala():
    ouro = GABARITO["PINTURA_E"]
    resultado = _proposta(
        "PINTURA_E", ouro["condicoes"], ouro["conectivo_condicoes"],
        ouro["direcao_implicacao"],
    )
    assert resultado["estado"] == "slots_e_relacao_alinhados_revisao_pendente"
    assert resultado["aprovado_para_producao"] is False
    assert resultado["autoriza_efeito"] is False


def test_citacao_fabricada_falha_antes_da_comparacao():
    ouro = GABARITO["PINTURA_E"]
    condicoes = [dict(item) for item in ouro["condicoes"]]
    condicoes[0]["citacao"] = "parede pintada de ouro"
    resultado = _proposta(
        "PINTURA_E", condicoes, "e", "condicoes_suficientes",
    )
    assert resultado["estado"] == "proposta_invalida"
    assert resultado["motivo"] == "citacao_invalida"


def test_somente_quando_trocado_por_se_eh_divergencia():
    ouro = GABARITO["LOGIN_ONLY"]
    resultado = _proposta(
        "LOGIN_ONLY", ouro["condicoes"], "e", "condicoes_suficientes",
    )
    assert resultado["estado"] == "implicacao_divergente"
    assert resultado["aprovado_para_producao"] is False


def test_conectivo_trocado_sem_omitir_condicao_eh_divergencia():
    ouro = GABARITO["ALARME_OR"]
    resultado = _proposta(
        "ALARME_OR", ouro["condicoes"], "e", "condicoes_suficientes",
    )
    assert resultado["estado"] == "conectivo_divergente"


def test_recusa_da_arvore_mista_eh_abstencao_compativel():
    resultado = _proposta(
        "ALERTA_MISTO", [], "indeterminado", "indeterminado",
        representavel=False,
    )
    assert resultado["estado"] == "abstencao_compativel"
    assert resultado["aprovado_para_producao"] is False


def test_forcar_regra_plana_sobre_arvore_mista_eh_erro():
    resultado = _proposta(
        "ALERTA_MISTO", GABARITO["ALARME_OR"]["condicoes"],
        "ou", "condicoes_suficientes",
    )
    assert resultado["estado"] == "forcou_regra_nao_representavel"


def test_recusa_de_caso_representavel_fica_visivel():
    resultado = _proposta(
        "PINTURA_E", [], "indeterminado", "indeterminado",
        representavel=False,
    )
    assert resultado["estado"] == "abstencao_em_regra_representavel"


def test_gabarito_ausente_nao_transforma_recusa_em_acerto():
    resultado = conferir_proposta(POR_ID["ALERTA_MISTO"], {}, {
        "representavel": False, "condicoes": [],
        "conectivo_condicoes": "indeterminado",
        "direcao_implicacao": "indeterminado",
    })
    assert resultado["estado"] == "entrada_invalida"
    assert resultado["aprovado_para_producao"] is False


def test_campos_inesperados_e_operador_conectivo_sao_recusados():
    ouro = GABARITO["PINTURA_E"]
    condicoes = [dict(item) for item in ouro["condicoes"]]
    condicoes[0]["operador"] = "e"
    resultado = _proposta("PINTURA_E", condicoes, "e", "condicoes_suficientes")
    assert resultado["estado"] == "proposta_invalida"
    assert resultado["motivo"] == "regra_invalida"
    resultado = conferir_proposta(POR_ID["PINTURA_E"], ouro, {
        "representavel": True, "condicoes": ouro["condicoes"],
        "conectivo_condicoes": "e",
        "direcao_implicacao": "condicoes_suficientes", "autorizar": True,
    })
    assert resultado["estado"] == "entrada_invalida"
    assert resultado["autoriza_efeito"] is False
