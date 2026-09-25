"""Uma desigualdade verificável não substitui entidade, modo ou papéis."""

from scripts.analises.contrato_requisitos_ensino import Requisito, localizar_valor_para_limiar
from scripts.analises.sonda_extracao_vinculo_ensino_v1 import carregar_casos


LIMIAR = Requisito("limiar", "menor_que", "abaixo de 20%")


def _caso(identificador: str) -> dict[str, str]:
    return next(item for item in carregar_casos("dev") if item["id"] == identificador)


def test_valor_do_exemplo_positivo_e_localizado_sem_modelo() -> None:
    resultado = localizar_valor_para_limiar(LIMIAR, _caso("IRR-01")["exemplo"])
    assert resultado["estado"] == "numero_conferido_entidade_pendente"
    assert resultado["trecho_exemplo"] == "15%"
    assert resultado["comparacao_numerica"] is True
    assert resultado["entidade_verificada"] is False
    assert resultado["aprovado_para_compor"] is False


def test_mesma_conta_nao_confirma_modo_nem_papeis() -> None:
    for identificador in ("IRR-02", "IRR-03"):
        resultado = localizar_valor_para_limiar(LIMIAR, _caso(identificador)["exemplo"])
        assert resultado["comparacao_numerica"] is True
        assert resultado["modo_verificado"] is False
        assert resultado["papeis_verificados"] is False
        assert resultado["aprovado_para_compor"] is False


def test_valor_ausente_unidade_errada_e_limiar_violado() -> None:
    assert localizar_valor_para_limiar(LIMIAR, _caso("IRR-04")["exemplo"])[
        "estado"] == "valor_ausente"
    assert localizar_valor_para_limiar(LIMIAR, "O sensor leu 15°C.")[
        "estado"] == "unidade_incompativel"
    assert localizar_valor_para_limiar(LIMIAR, "O sensor leu 25% de umidade.")[
        "estado"] == "limiar_nao_satisfeito"


def test_multiplos_valores_e_negacao_falham_fechado() -> None:
    assert localizar_valor_para_limiar(LIMIAR, "Leu 15% do solo e 40% do ar.")[
        "estado"] == "valores_ambiguos"
    assert localizar_valor_para_limiar(LIMIAR, "O sensor não leu 15% de umidade.")[
        "estado"] == "negacao_ou_escopo_pendente"


def test_outro_objeto_com_mesmo_numero_nao_vira_prova_de_entidade() -> None:
    resultado = localizar_valor_para_limiar(LIMIAR, "O desconto foi de 15% na compra.")
    assert resultado["comparacao_numerica"] is True
    assert resultado["entidade_verificada"] is False
    assert resultado["aprovado_para_compor"] is False


def test_comparacao_nao_fica_especifica_a_porcentagem() -> None:
    temperatura = Requisito("temperatura", "menor_que", "abaixo de 5°C")
    massa = Requisito("massa", "menor_que", "abaixo de 2,5 kg")
    assert localizar_valor_para_limiar(temperatura, "O termômetro marcou 3°C.")[
        "comparacao_numerica"] is True
    assert localizar_valor_para_limiar(massa, "A balança marcou 1,5 kg.")[
        "comparacao_numerica"] is True


def test_operador_desconhecido_nao_e_tratado_como_abaixo() -> None:
    requisito = Requisito("temperatura", "menor_que", "acima de 5°C")
    assert localizar_valor_para_limiar(requisito, "Marcou 3°C.")[
        "estado"] == "limiar_nao_conferivel"
