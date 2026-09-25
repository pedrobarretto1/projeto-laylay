"""O proponente local não pode converter citação em prova semântica."""

import json

from scripts.analises.sonda_extracao_vinculo_ensino_v1 import (
    carregar_casos,
    conferir_proposta,
    medir_caso,
)


def _proposta(caso: dict[str, str]) -> dict:
    return {
        "tipo": "exemplo_direto",
        "relacao_def": "aciona",
        "relacao_ex": "aciona",
        "papeis_def": {"agente": "controlador", "alvo": "bomba"},
        "papeis_ex": {"agente": "controlador", "alvo": "bomba"},
        "condicoes_def": ["modo_auto"],
        "condicoes_ex": ["modo_auto"],
        "citacao_def": caso["definicao"],
        "citacao_ex": caso["exemplo"],
    }


def test_dataset_congelado_e_separado_por_dominio() -> None:
    dev = carregar_casos("dev")
    reserva = carregar_casos("reserva")
    assert len(dev) == len(reserva) == 8
    assert {item["dominio"] for item in dev} == {"irrigacao", "arquitetura"}
    assert {item["dominio"] for item in reserva} == {"programacao", "culinaria"}
    assert not ({item["id"] for item in dev} & {item["id"] for item in reserva})


def test_citacao_localizada_nao_aprova_anotacao_semantica() -> None:
    caso = carregar_casos("dev")[0]
    observado = conferir_proposta(_proposta(caso), caso)
    assert observado["valida"] is True
    assert observado["estrutura"] == "estrutura_compativel_revisao_pendente"
    assert observado["anotacao_semantica_revisada"] is False
    assert observado["aprovado_para_compor"] is False


def test_citacao_inventada_e_campo_ausente_falham_fechados() -> None:
    caso = carregar_casos("dev")[0]
    proposta = _proposta(caso)
    proposta["citacao_ex"] = "Uma frase inventada que nao estava na fonte."
    assert conferir_proposta(proposta, caso)["motivo"] == "citacao_ex_sem_recibo"
    proposta = _proposta(caso)
    del proposta["condicoes_ex"]
    assert conferir_proposta(proposta, caso)["motivo"] == "condicoes_ex_invalidas"


def test_falso_direto_com_condicao_inventada_na_anotacao_nao_e_publicavel() -> None:
    caso = next(item for item in carregar_casos("dev") if item["id"] == "IRR-02")
    proposta = _proposta(caso)
    assert caso["esperado"] == "condicao_omitida"
    # O texto não informa o modo, mas a anotação pode alegá-lo. A checagem
    # literal do trecho não certifica a semântica da anotação.
    observado = conferir_proposta(proposta, caso)
    assert observado["valida"] is True
    assert observado["estrutura"] == "estrutura_compativel_revisao_pendente"
    assert observado["aprovado_para_compor"] is False


def test_request_enviado_ao_modelo_nao_contem_gabarito() -> None:
    caso = carregar_casos("dev")[0]
    entradas = []

    class _Resposta:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"message": {"content": json.dumps(_proposta(caso))}}

    def post(_url: str, **kwargs):
        entradas.append(kwargs["json"])
        return _Resposta()

    resultado = medir_caso(caso, post=post)
    assert resultado["formal"]["valida"] is True
    assert resultado["formal"]["aprovado_para_compor"] is False
    assert caso["esperado"] not in entradas[0]["messages"][1]["content"]
    assert entradas[0]["model"] == "qwen3:4b-instruct"
    assert entradas[0]["format"]["properties"]["tipo"]["enum"]
