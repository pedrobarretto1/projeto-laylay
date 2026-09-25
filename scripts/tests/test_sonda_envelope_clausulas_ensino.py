"""A proposta de evidência não pode apagar exigências da definição."""

import json

from scripts.analises.sonda_envelope_clausulas_ensino import conferir_envelope, medir_caso
from scripts.analises.sonda_extracao_vinculo_ensino_v1 import carregar_casos


def _caso(identificador: str) -> dict[str, str]:
    return next(item for item in carregar_casos("dev") if item["id"] == identificador)


def test_clausula_omitida_pela_proposta_continua_obrigatoria() -> None:
    caso = _caso("IRR-02")
    bruto = {"alinhamentos": [
        {"indice": 0, "trecho_exemplo": ""},
        {"indice": 1, "trecho_exemplo": "15%"},
        {"indice": 2, "trecho_exemplo": "o controlador ligou a bomba"},
    ]}
    resultado = conferir_envelope(caso, bruto)
    assert resultado["clausulas_ativas"] == [0, 1, 2]
    assert resultado["clausulas_sem_evidencia"] == [0]
    assert resultado["estado"] == "sem_evidencia_em_clausulas"
    assert resultado["aprovado_para_compor"] is False


def test_exemplo_provisoriamente_direto_expoe_qualificador_implicito() -> None:
    caso = _caso("IRR-01")
    bruto = {"alinhamentos": [
        {"indice": 0, "trecho_exemplo": "No modo automático"},
        {"indice": 1, "trecho_exemplo": ""},
        {"indice": 2, "trecho_exemplo": "o controlador ligou a bomba"},
    ]}
    resultado = conferir_envelope(caso, bruto)
    assert resultado["clausulas_sem_evidencia"] == [1]
    assert resultado["estado"] == "sem_evidencia_em_clausulas"
    assert resultado["pistas_numericas"][1]["trecho_exemplo"] == "15%"
    assert resultado["pistas_numericas"][1]["entidade_verificada"] is False
    assert resultado["rotulos_medidas"][1]["estado"] == "qualificador_ausente"
    assert resultado["aprovado_para_compor"] is False


def test_envelope_distingue_rotulos_explicitos_sem_conceder_aprovacao() -> None:
    caso = _caso("IRR-01")
    vazio = {"alinhamentos": [
        {"indice": indice, "trecho_exemplo": ""} for indice in range(3)
    ]}
    for exemplo, esperado in (
        ("O sensor leu 15% de umidade do solo.", "rotulo_literal_igual_revisao_pendente"),
        ("O sensor leu 15% de umidade do ar.", "qualificador_divergente"),
        ("A loja anunciou 15% de desconto.", "rotulo_diferente"),
    ):
        resultado = conferir_envelope({**caso, "exemplo": exemplo}, vazio)
        assert resultado["rotulos_medidas"][1]["estado"] == esperado
        assert resultado["clausulas_ativas"] == [0, 1, 2]
        assert resultado["aprovado_para_compor"] is False


def test_falta_de_alinhamento_e_trecho_inventado_falham_fechado() -> None:
    caso = _caso("ARQ-01")
    incompleto = {"alinhamentos": [{"indice": 1, "trecho_exemplo": "vista superior"}]}
    assert conferir_envelope(caso, incompleto)["estado"] == "cobertura_de_indices_invalida"
    inventado = {"alinhamentos": [
        {"indice": 0, "trecho_exemplo": "planta baixa"},
        {"indice": 1, "trecho_exemplo": "visão lateral"},
    ]}
    assert conferir_envelope(caso, inventado)["estado"] == "trecho_exemplo_invalido"


def test_todos_os_trechos_presentes_ainda_nao_provam_relacao() -> None:
    caso = _caso("ARQ-04")
    bruto = {"alinhamentos": [
        {"indice": 0, "trecho_exemplo": "sem informar se atravessa a escada"},
        {"indice": 1, "trecho_exemplo": "mostra os degraus e suas alturas"},
    ]}
    resultado = conferir_envelope(caso, bruto)
    assert resultado["estado"] == "evidencia_literal_revisao_pendente"
    assert resultado["condicoes_verificadas"] is False
    assert resultado["aprovado_para_compor"] is False


def test_requisicao_nao_envia_rotulo_nem_requisitos_curados() -> None:
    caso = _caso("IRR-01")
    enviado = {}

    class Resposta:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"message": {"content": json.dumps({"alinhamentos": [
                {"indice": 0, "trecho_exemplo": "modo automático"},
                {"indice": 1, "trecho_exemplo": "15%"},
                {"indice": 2, "trecho_exemplo": "o controlador ligou a bomba"},
            ]})}}

    def post(_url: str, **kwargs):
        enviado.update(kwargs)
        return Resposta()

    resultado = medir_caso(caso, post=post)
    entrada = enviado["json"]["messages"][1]["content"]
    assert caso["definicao"] not in entrada  # apenas cláusulas com offsets
    assert caso["exemplo"] in entrada
    assert caso["esperado"] not in entrada
    assert "requisitos_curados" not in entrada
    assert resultado["conferencia"]["clausulas_ativas"] == [0, 1, 2]
    assert resultado["conferencia"]["aprovado_para_compor"] is False
