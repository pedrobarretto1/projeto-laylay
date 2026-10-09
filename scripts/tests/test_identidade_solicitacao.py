"""A identidade local da execução não pode ser proposta como receipt pela IA."""

from __future__ import annotations

from copy import deepcopy

import pytest

from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.autonomia.coordenador_intencao import _preparar_intent_execucao
from mente_laylay.memoria_mental import resultado_acao
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime


def _obter(dados: dict) -> str:
    funcao = getattr(resultado_acao, "obter_id_solicitacao", None)
    assert callable(funcao), "o owner do receipt precisa ler a identidade sem coerção"
    return funcao(dados)


def _identificar(dados: dict, *, nova_identidade: bool = False) -> dict:
    funcao = getattr(resultado_acao, "identificar_solicitacao_execucao", None)
    assert callable(funcao), "o owner precisa preparar identidade antes de publicar o pedido"
    return funcao(dados, nova_identidade=nova_identidade)


@pytest.mark.parametrize("dados", [
    {"id_solicitacao": "pedido-a", "request_id": "pedido-b"},
    {"id_solicitacao": 42},
    {"request_id": True},
])
def test_preparador_existente_recusa_identidade_ambigua_ou_coercao(dados: dict) -> None:
    original = deepcopy(dados)
    with pytest.raises(ValueError):
        _preparar_intent_execucao(dict(dados, intent="APP_OPEN"))
    assert dados == original


def test_preparador_existente_isola_payload_aninhado_da_fonte() -> None:
    original = {"intent": "CREATE_FILE", "params": {"conteudo": {"linhas": ["original"]}}}
    identificado = _preparar_intent_execucao(original)
    identificado["params"]["conteudo"]["linhas"].append("outra")
    assert original["params"]["conteudo"]["linhas"] == ["original"]


@pytest.mark.parametrize("novo", [False, True])
def test_identificacao_isola_parametros_vivos_do_estado_compartilhado(novo: bool) -> None:
    estado = EstadoCompartilhadoRuntime(mental={"pedido": {
        "intent": "CREATE_FILE", "params": {"conteudo": {"linhas": ["original"]}},
    }})
    fonte = dict(estado.mental["pedido"])
    preparado = _identificar(fonte, nova_identidade=novo)
    assert preparado["id_solicitacao"]
    preparado["params"]["conteudo"]["linhas"].append("outra")
    assert estado.obter_copia("mental", "pedido")["params"]["conteudo"]["linhas"] == ["original"]


def test_adaptador_recusa_aliases_conflitantes_antes_de_receipt() -> None:
    pedido = {"intent": "APP_OPEN", "id_solicitacao": "pedido-a", "request_id": "pedido-b"}
    with pytest.raises(ValueError):
        AdaptadorResultadoOperacional(pedido, {}, "abre o app", "pc_a", {})


@pytest.mark.parametrize("dados,esperado", [
    ({}, ""),
    ({"id_solicitacao": ""}, ""),
    ({"id_solicitacao": "   ", "request_id": ""}, ""),
    ({"id_solicitacao": " pedido-a "}, "pedido-a"),
    ({"request_id": " pedido-a "}, "pedido-a"),
    ({"id_solicitacao": " pedido-a ", "request_id": "pedido-a"}, "pedido-a"),
    ({"id_solicitacao": "", "request_id": "pedido-a"}, "pedido-a"),
])
def test_leitor_aceita_identidade_textual_ou_ausencia(dados: dict, esperado: str) -> None:
    assert _obter(dados) == esperado


@pytest.mark.parametrize("valor", [None, 0, 42, True, [], {}, ["pedido-a"]])
@pytest.mark.parametrize("chave", ["id_solicitacao", "request_id"])
def test_leitor_nao_coage_identidade_invalida(chave: str, valor: object) -> None:
    with pytest.raises(ValueError):
        _obter({chave: valor})


def test_leitor_recusa_aliases_divergentes() -> None:
    with pytest.raises(ValueError):
        _obter({"id_solicitacao": "pedido-a", "request_id": "pedido-b"})


def test_preparacao_preserva_alias_legado_sem_mutar_fonte() -> None:
    original = {"intent": "APP_OPEN", "request_id": " pedido-a ", "params": {"nome_app": "Calculadora"}}
    antes = deepcopy(original)
    identificado = _identificar(original)
    assert original == antes
    assert identificado["id_solicitacao"] == "pedido-a"
    assert "request_id" not in identificado
    identificado["params"]["nome_app"] = "outro"
    assert original == antes


def test_nova_identidade_por_ocorrencia_remove_prova_falsa_do_envelope() -> None:
    campos_receipt = {
        "status": "app_iniciado_focado", "executou": True, "confirmado": True,
        "origem": "executor", "evidencia_confirmacao": "inventada",
        "confirmacao_oferecida": "estado_observado", "ok": True,
        "estado_final": "confirmado", "estado_confirmacao": "confirmado",
        "tratado": True, "resultado_publicado": True, "retorno_legado": True,
        "legado": False,
        resultado_acao.CHAVE_RESULTADO_OPERACIONAL_PUBLICADO: "id-modelo",
        resultado_acao.CHAVE_TRATAMENTO_OPERACIONAL: {"confirmado": True},
    }
    original = {
        "intent": "CREATE_FILE", "id_solicitacao": "id-modelo", "request_id": "outro-id-modelo",
        "params": {
            "alvo": "nota", "id_solicitacao": "id-param", "request_id": "id-param",
            "conteudo": {"id_solicitacao": "texto-legitimo", "status": "rascunho"},
        },
        "contexto": {"request_id_remoto": "request-transporte", "requestId": "transporte"},
        **campos_receipt,
    }
    antes = deepcopy(original)
    primeiro = _identificar(original, nova_identidade=True)
    segundo = _identificar(original, nova_identidade=True)
    assert original == antes
    assert primeiro["id_solicitacao"] and segundo["id_solicitacao"]
    assert primeiro["id_solicitacao"] != segundo["id_solicitacao"]
    assert primeiro["id_solicitacao"] not in {"id-modelo", "outro-id-modelo"}
    assert not set(campos_receipt).intersection(primeiro)
    assert "request_id" not in primeiro
    assert "id_solicitacao" not in primeiro["params"] and "request_id" not in primeiro["params"]
    assert primeiro["params"]["conteudo"] == original["params"]["conteudo"]
    assert primeiro["contexto"] == original["contexto"]
    primeiro["params"]["conteudo"]["status"] = "modificado"
    assert original == antes


def test_nova_identidade_ignora_tipos_de_id_do_modelo() -> None:
    identificado = _identificar({"id_solicitacao": [], "request_id": 42}, nova_identidade=True)
    assert isinstance(identificado["id_solicitacao"], str) and identificado["id_solicitacao"]
    assert "request_id" not in identificado


def test_preparacao_de_receipt_confiavel_preserva_evidencia_e_contexto() -> None:
    original = {
        "id_solicitacao": "pedido-a", "intent": "IOT_CONTROL", "status": "ja_estava_ligado",
        "executou": False, "confirmado": True, "origem": "executor",
        "evidencia_confirmacao": "estado relido", "params": {"alvo": "lampada"},
        "contexto": {"request_id_remoto": "transporte-a"},
    }
    assert _identificar(original) == original


def test_adaptador_e_preparador_compartilham_identidade_da_ocorrencia() -> None:
    pedido = _identificar({"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}})
    receipts = []
    adaptador = AdaptadorResultadoOperacional(pedido, pedido["params"], "abre calculadora", "pc_a", {
        "_registrar_resultado_execucao": lambda receipt, *_args, **_kwargs: receipts.append(receipt),
    })
    adaptador.marcar_resultado("app_iniciado_focado", True, confirmado=True)
    assert receipts and receipts[0].id_solicitacao == pedido["id_solicitacao"]


@pytest.mark.parametrize("sucesso_anterior", [False, True])
def test_recusa_de_publicacao_nao_mantem_marcador_nem_receipt_de_outra_tentativa(sucesso_anterior: bool) -> None:
    pedido = _identificar({"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}})
    ctx = {"_registrar_resultado_execucao": lambda *_args, **_kwargs: None}
    adaptador = AdaptadorResultadoOperacional(pedido, pedido["params"], "abre o app", "pc_a", ctx)
    if sucesso_anterior:
        adaptador.marcar_resultado("app_iniciado_focado", True, confirmado=True)
        assert adaptador._receipt_publicado is not None
    ctx["_registrar_resultado_execucao"] = lambda *_args, **_kwargs: False
    adaptador.marcar_resultado("falha_execucao", False, confirmado=False)
    assert adaptador._receipt_publicado is None
    assert not pedido.get(resultado_acao.CHAVE_RESULTADO_OPERACIONAL_PUBLICADO)
    assert not resultado_acao.interpretar_tratamento_operacional(pedido, False).resultado_publicado
