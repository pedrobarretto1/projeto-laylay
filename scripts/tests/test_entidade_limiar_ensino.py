"""A grandeza citada deve ter rótulo rastreável; contexto implícito fica aberto."""

from scripts.analises.contrato_requisitos_ensino import (
    Requisito,
    comparar_rotulo_da_medida,
)
from scripts.analises.sonda_extracao_vinculo_ensino_v1 import carregar_casos


UMIDADE = Requisito(
    "limiar", "menor_que", "se a umidade do solo cair abaixo de 20%",
)


def _caso(identificador: str) -> dict[str, str]:
    return next(item for item in carregar_casos("dev") if item["id"] == identificador)


def test_rotulo_explicito_igual_e_apenas_alinhamento_textual() -> None:
    resultado = comparar_rotulo_da_medida(
        UMIDADE, "O sensor leu 15% de umidade do solo.",
    )
    assert resultado["estado"] == "rotulo_literal_igual_revisao_pendente"
    assert resultado["entidade_requerida"] == "umidade do solo"
    assert resultado["entidade_exemplo"] == "umidade do solo"
    assert resultado["entidade_verificada"] is False
    assert resultado["aprovado_para_compor"] is False


def test_caso_provisorio_positivo_nao_comprova_qualificador_solo() -> None:
    resultado = comparar_rotulo_da_medida(UMIDADE, _caso("IRR-01")["exemplo"])
    assert resultado["estado"] == "qualificador_ausente"
    assert resultado["entidade_exemplo"] == "umidade"
    assert resultado["entidade_verificada"] is False


def test_umidade_do_ar_e_desconto_nao_sao_umidade_do_solo() -> None:
    assert comparar_rotulo_da_medida(
        UMIDADE, "O sensor leu 15% de umidade do ar.",
    )["estado"] == "qualificador_divergente"
    assert comparar_rotulo_da_medida(
        UMIDADE, "A loja anunciou 15% de desconto.",
    )["estado"] == "rotulo_diferente"


def test_valor_sem_rotulo_e_multiplo_valor_falham_fechado() -> None:
    assert comparar_rotulo_da_medida(UMIDADE, "O sensor leu 15%.")[
        "estado"] == "rotulo_exemplo_ausente"
    assert comparar_rotulo_da_medida(
        UMIDADE, "Leu 15% de umidade do solo e 30% de umidade do ar.",
    )["estado"] == "valores_ambiguos"


def test_nao_resolve_negacao_ou_definicao_sem_entidade_explicita() -> None:
    assert comparar_rotulo_da_medida(
        UMIDADE, "O sensor não leu 15% de umidade do solo.",
    )["estado"] == "negacao_ou_escopo_pendente"
    assert comparar_rotulo_da_medida(
        Requisito("limiar", "menor_que", "abaixo de 20%"),
        "O sensor leu 15% de umidade do solo.",
    )["estado"] == "entidade_origem_indeterminada"


def test_nao_e_regra_exclusiva_de_umidade() -> None:
    temperatura = Requisito(
        "temperatura", "menor_que", "se a temperatura da água ficar abaixo de 5°C",
    )
    assert comparar_rotulo_da_medida(
        temperatura, "O termômetro marcou 3°C de temperatura da água.",
    )["estado"] == "rotulo_literal_igual_revisao_pendente"
