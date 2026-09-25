"""Requisitos rastreáveis não viram verdade sem prova por slot."""

from scripts.analises.contrato_requisitos_ensino import (
    Alinhamento,
    Requisito,
    conferir_requisitos,
)
from scripts.analises.sonda_extracao_vinculo_ensino_v1 import carregar_casos


def _caso(id_caso: str) -> dict[str, str]:
    return next(c for c in carregar_casos("dev") if c["id"] == id_caso)


def _irrigacao() -> tuple[Requisito, ...]:
    return (
        Requisito("modo", "condicao_textual", "modo automático"),
        Requisito("limiar", "menor_que", "abaixo de 20%"),
        Requisito("agente", "literal", "controlador"),
        Requisito("alvo", "literal", "bomba"),
        Requisito("acao", "parafrase", "liga"),
    )


def test_exemplo_positivo_fica_pendente_na_flexao_que_codigo_nao_prova() -> None:
    caso = _caso("IRR-01")
    alinhamentos = (
        Alinhamento("modo", "modo automático"),
        Alinhamento("limiar", "15%"),
        Alinhamento("agente", "controlador"),
        Alinhamento("alvo", "bomba"),
        Alinhamento("acao", "ligou"),
    )
    resultado = conferir_requisitos(caso["definicao"], caso["exemplo"],
                                   _irrigacao(), alinhamentos)
    assert resultado["estado"] == "revisao_semantica_pendente"
    assert resultado["slots"]["modo"] == "condicao_semantica_pendente"
    assert resultado["slots"]["limiar"] == "comparacao_numerica_confirmada"
    assert resultado["slots"]["acao"] == "parafrase_pendente"
    assert resultado["aprovado_para_compor"] is False


def test_falso_direto_sem_modo_nao_fica_coberto_por_mencao_a_modo() -> None:
    caso = _caso("IRR-02")
    alinhamentos = (
        Alinhamento("modo", "modo não foi informado"),
        Alinhamento("limiar", "15%"),
        Alinhamento("agente", "controlador"),
        Alinhamento("alvo", "bomba"),
        Alinhamento("acao", "ligou"),
    )
    resultado = conferir_requisitos(caso["definicao"], caso["exemplo"],
                                   _irrigacao(), alinhamentos)
    assert resultado["slots"]["modo"] == "requisito_nao_demonstrado"
    assert resultado["estado"] == "requisito_faltante"


def test_outra_relacao_nao_e_prova_de_planta_baixa() -> None:
    caso = _caso("ARQ-02")
    requisitos = (
        Requisito("artefato", "literal", "planta baixa"),
        Requisito("perspectiva", "parafrase", "visto de cima"),
    )
    resultado = conferir_requisitos(caso["definicao"], caso["exemplo"], requisitos,
                                   (Alinhamento("artefato", "corte vertical"),
                                    Alinhamento("perspectiva", "vertical")))
    assert resultado["slots"]["artefato"] == "requisito_nao_demonstrado"
    assert resultado["estado"] == "requisito_faltante"


def test_numero_nao_satisfaz_condicao_invertida() -> None:
    caso = _caso("IRR-01")
    exemplo = caso["exemplo"].replace("15%", "25%")
    resultado = conferir_requisitos(caso["definicao"], exemplo,
                                   (Requisito("limiar", "menor_que", "abaixo de 20%"),),
                                   (Alinhamento("limiar", "25%"),))
    assert resultado["slots"]["limiar"] == "condicao_violada"


def test_requisito_sem_origem_literal_invalida_lote() -> None:
    caso = _caso("IRR-01")
    resultado = conferir_requisitos(caso["definicao"], caso["exemplo"],
                                   (Requisito("fantasma", "literal", "modo noturno"),),
                                   (Alinhamento("fantasma", "modo automático"),))
    assert resultado["estado"] == "requisito_origem_invalida"


def test_condicao_citada_dentro_de_negacao_nao_e_confirmacao() -> None:
    caso = _caso("ARQ-04")
    resultado = conferir_requisitos(
        caso["definicao"], caso["exemplo"],
        (Requisito("travessia", "condicao_textual", "atravessa a escada"),),
        (Alinhamento("travessia", "sem informar se atravessa a escada"),),
    )
    assert resultado["slots"]["travessia"] == "condicao_semantica_pendente"
    assert resultado["estado"] == "revisao_semantica_pendente"
    assert resultado["aprovado_para_compor"] is False
