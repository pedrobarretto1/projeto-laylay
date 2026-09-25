"""Índices preservam a fonte, mas não concedem aprovação semântica."""

import json

from scripts.analises.sonda_extracao_vinculo_ensino_v1 import carregar_casos
from scripts.analises.sonda_indices_requisitos_ensino import (
    conferir_indices,
    medir_definicao,
    segmentar_clausulas,
)


def _caso(identificador: str) -> dict[str, str]:
    return next(item for item in carregar_casos("dev") if item["id"] == identificador)


def test_clausulas_conservam_offsets_e_condicao_inicial() -> None:
    definicao = _caso("IRR-01")["definicao"]
    clausulas = segmentar_clausulas(definicao)
    assert [item["trecho"] for item in clausulas] == [
        "No modo automático",
        "se a umidade do solo cair abaixo de 20%",
        "o controlador liga a bomba",
    ]
    assert all(definicao[item["inicio"]:item["fim"]] == item["trecho"]
               for item in clausulas)


def test_indice_omitido_revela_primeiro_requisito_faltante() -> None:
    caso = _caso("IRR-01")
    clausulas = segmentar_clausulas(caso["definicao"])
    resultado = conferir_indices({"indices_requisitos": [1, 2]}, caso, clausulas)
    assert resultado["estado"] == "cobertura_incompleta"
    assert resultado["requisitos_nao_cobertos"] == ["modo"]
    assert resultado["aprovado_para_compor"] is False


def test_indice_inventado_ou_repetido_nao_passa() -> None:
    caso = _caso("ARQ-01")
    clausulas = segmentar_clausulas(caso["definicao"])
    for indices in ([0, 99], [0, 0], [True], ["0"]):
        assert conferir_indices({"indices_requisitos": indices}, caso, clausulas)[
            "estado"] == "indices_invalidos"


def test_modelo_ve_somente_definicao_e_indices_sem_gabarito() -> None:
    caso = _caso("ARQ-04")
    enviado = {}

    class Resposta:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"message": {"content": json.dumps({"indices_requisitos": [0, 1]})}}

    def post(_url: str, **kwargs):
        enviado.update(kwargs)
        return Resposta()

    resultado = medir_definicao(caso, post=post)
    entrada = enviado["json"]["messages"][1]["content"]
    assert caso["exemplo"] not in entrada
    assert caso["esperado"] not in entrada
    assert "requisitos_curados" not in entrada
    assert resultado["conferencia"]["estado"] == "fonte_coberta_revisao_pendente"
    assert resultado["conferencia"]["requisitos_nao_cobertos"] == []
    assert resultado["conferencia"]["aprovado_para_compor"] is False
