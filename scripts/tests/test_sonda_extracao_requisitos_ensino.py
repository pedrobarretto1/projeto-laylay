"""A definição é a única entrada da proposta e spans sem origem não passam."""

import json

from scripts.analises.sonda_extracao_requisitos_ensino import (
    conferir_extracao,
    medir_definicao,
)
from scripts.analises.sonda_extracao_vinculo_ensino_v1 import carregar_casos


def _caso():
    return next(item for item in carregar_casos("dev") if item["id"] == "IRR-01")


def test_rejeita_trecho_inventado_e_definicao_inteira():
    definicao = _caso()["definicao"]
    assert conferir_extracao({"requisitos": [
        {"tipo": "entidade", "trecho_definicao": "controlador"},
        {"tipo": "acao", "trecho_definicao": "teletransporta"},
        {"tipo": "objeto", "trecho_definicao": "bomba"},
    ]}, definicao)["motivo"] == "trecho_sem_recibo"
    assert conferir_extracao({"requisitos": [
        {"tipo": "entidade", "trecho_definicao": "controlador"},
        {"tipo": "acao", "trecho_definicao": definicao},
        {"tipo": "objeto", "trecho_definicao": "bomba"},
    ]}, definicao)["motivo"] == "trecho_sem_recibo"


def test_modelo_recebe_so_definicao_e_cobertura_nao_aprova_producao():
    caso = _caso()
    enviado = {}

    class Resposta:
        def raise_for_status(self):
            return None

        def json(self):
            return {"message": {"content": json.dumps({"requisitos": [
                {"tipo": "condicao", "trecho_definicao": "modo automático"},
                {"tipo": "limiar", "trecho_definicao": "abaixo de 20%"},
                {"tipo": "entidade", "trecho_definicao": "controlador"},
                {"tipo": "objeto", "trecho_definicao": "bomba"},
                {"tipo": "acao", "trecho_definicao": "liga"},
            ]})}}

    def post(_url, **kwargs):
        enviado.update(kwargs)
        return Resposta()

    resultado = medir_definicao(caso, post=post)
    mensagens = enviado["json"]["messages"]
    assert mensagens[1]["content"] == caso["definicao"]
    assert caso["exemplo"] not in json.dumps(mensagens, ensure_ascii=False)
    assert caso["esperado"] not in json.dumps(mensagens, ensure_ascii=False)
    assert resultado["formal"]["valida"] is True
    assert resultado["requisitos_nao_cobertos"] == []
    assert resultado["aprovado_para_producao"] is False


def test_falta_de_qualificador_e_detectada_por_curadoria_diagnostica():
    caso = _caso()

    class Resposta:
        def raise_for_status(self):
            return None

        def json(self):
            return {"message": {"content": json.dumps({"requisitos": [
                {"tipo": "limiar", "trecho_definicao": "abaixo de 20%"},
                {"tipo": "entidade", "trecho_definicao": "controlador"},
                {"tipo": "objeto", "trecho_definicao": "bomba"},
                {"tipo": "acao", "trecho_definicao": "liga"},
            ]})}}

    resultado = medir_definicao(caso, post=lambda *_args, **_kwargs: Resposta())
    assert resultado["requisitos_nao_cobertos"] == ["modo"]
