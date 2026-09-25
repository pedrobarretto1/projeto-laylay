"""O alinhador cobre todos os slots e não transforma spans em autorização."""

from scripts.analises.sonda_alinhamento_requisitos_ensino import (
    conferir_saida, requisitos_do_caso,
)
from scripts.analises.sonda_extracao_vinculo_ensino_v1 import carregar_casos


def _caso(id_caso: str) -> dict[str, str]:
    return next(item for item in carregar_casos("dev") if item["id"] == id_caso)


def test_alinhamento_incompleto_nao_passa() -> None:
    caso = _caso("IRR-01")
    assert conferir_saida({"alinhamentos": [{"id": "modo", "trecho_exemplo": "modo automático"}]},
                          caso, requisitos_do_caso(caso["id"]))["estado"] == "cobertura_invalida"


def test_alinhamento_literalmente_inventado_nao_passa() -> None:
    caso = _caso("ARQ-02")
    bruto = {"alinhamentos": [
        {"id": requisito.id, "trecho_exemplo": "planta baixa"}
        for requisito in requisitos_do_caso(caso["id"])
    ]}
    resultado = conferir_saida(bruto, caso, requisitos_do_caso(caso["id"]))
    assert resultado["estado"] == "alinhamento_invalido"
    assert resultado["aprovado_para_compor"] is False


def test_a_reserva_nao_tem_requisitos_curados_por_esse_experimento() -> None:
    import pytest

    with pytest.raises(ValueError, match="desenvolvimento"):
        requisitos_do_caso("CACHE-01")
