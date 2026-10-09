"""Completar um resultado exige a identidade explícita da mesma ocorrência."""

from __future__ import annotations

from copy import deepcopy

import pytest

from mente_laylay.memoria_mental.contexto_compartilhado import registrar_resultado_execucao
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


DOMINIOS = (
    ("APP_OPEN", "nome_app", "app_iniciado_focado"),
    ("IOT_CONTROL", "alvo", "ligado"),
    ("PLAYLIST_CREATE", "nome_playlist", "playlist_criada"),
)


def _estado(intent: str, parametro: str, status: str, *, identidade: str = "pedido-a") -> dict:
    return registrar_resultado_execucao({}, ResultadoAcao(
        intent=intent, id_solicitacao=identidade, alvo="primeiro",
        params={parametro: "primeiro"}, status=status, executou=True,
        confirmado=True, origem="executor", detalhe="receipt real do primeiro",
        evidencia_confirmacao="observação exclusiva do primeiro",
    ), "executa os dois pedidos")


@pytest.mark.parametrize("intent,parametro,status", DOMINIOS)
@pytest.mark.parametrize("identidade", ["pedido-b", ""])
def test_novo_pedido_da_mesma_intent_e_texto_nao_herda_receipt(
    intent: str, parametro: str, status: str, identidade: str,
) -> None:
    estado = _estado(intent, parametro, status)
    antes = deepcopy(estado)
    novo = registrar_resultado_execucao(estado, {
        "intent": intent, "id_solicitacao": identidade, "params": {parametro: "segundo"},
    }, "executa os dois pedidos", True, origem="roteador")
    assert estado == antes
    contrato = novo["ultima_acao_contrato"]
    assert contrato["id_solicitacao"] == identidade
    assert contrato["status"] == "executado", "status é faceta da ocorrência, não da frase"
    assert contrato["confirmado"] is None
    assert contrato["alvo"] == "segundo"
    assert contrato["origem"] == "roteador"
    assert contrato["evidencia_confirmacao"] != "observação exclusiva do primeiro"
    assert novo["ultima_acao_detalhe"] == ""


@pytest.mark.parametrize("intent,parametro,status", DOMINIOS)
def test_complemento_da_mesma_ocorrencia_usa_id_e_aceita_texto_de_subetapa(
    intent: str, parametro: str, status: str,
) -> None:
    estado = _estado(intent, parametro, status)
    novo = registrar_resultado_execucao(estado, {
        "intent": intent, "request_id": "pedido-a", "params": {parametro: "primeiro"},
    }, "texto observado em outra subetapa", True, origem="roteador")
    contrato = novo["ultima_acao_contrato"]
    assert contrato["id_solicitacao"] == "pedido-a"
    assert contrato["status"] == status
    assert contrato["confirmado"] is True
    assert contrato["origem"] == "executor"
    assert contrato["evidencia_confirmacao"] == "observação exclusiva do primeiro"
    assert novo["ultima_acao_detalhe"] == "receipt real do primeiro"


def test_id_igual_nao_completa_receipt_de_intent_diferente() -> None:
    estado = _estado("APP_OPEN", "nome_app", "app_iniciado_focado")
    novo = registrar_resultado_execucao(estado, {
        "intent": "IOT_CONTROL", "id_solicitacao": "pedido-a", "params": {"alvo": "lampada"},
    }, "executa os dois pedidos", True)
    assert novo["ultima_acao_contrato"]["status"] == "executado"
    assert novo["ultima_acao_contrato"]["confirmado"] is None
    assert novo["ultima_acao_alvo"] == "lampada"


def test_resultados_legados_nao_se_identificam_pela_frase() -> None:
    estado = _estado("APP_OPEN", "nome_app", "app_iniciado_focado", identidade="")
    novo = registrar_resultado_execucao(estado, {
        "intent": "APP_OPEN", "params": {"nome_app": "segundo"},
    }, "executa os dois pedidos", True)
    assert novo["ultima_acao_contrato"]["id_solicitacao"] == ""
    assert novo["ultima_acao_contrato"]["confirmado"] is None
    assert novo["ultima_acao_status"] == "executado"
    assert novo["ultima_acao_alvo"] == "segundo"


@pytest.mark.parametrize("identidades", [
    {"id_solicitacao": "pedido-a", "request_id": "pedido-b"},
    {"id_solicitacao": 42},
    {"request_id": None},
])
def test_identidade_invalida_e_recusada_antes_de_publicar_contexto(identidades: dict) -> None:
    estado = _estado("APP_OPEN", "nome_app", "app_iniciado_focado")
    antes = deepcopy(estado)
    with pytest.raises(ValueError):
        registrar_resultado_execucao(estado, {
            "intent": "APP_OPEN", "params": {"nome_app": "segundo"}, **identidades,
        }, "executa os dois pedidos", True)
    assert estado == antes


def test_faceta_negativa_explicita_da_mesma_ocorrencia_nao_herda_confirmacao() -> None:
    estado = _estado("APP_OPEN", "nome_app", "app_iniciado_focado")
    novo = registrar_resultado_execucao(estado, {
        "intent": "APP_OPEN", "id_solicitacao": "pedido-a",
        "params": {"nome_app": "primeiro"}, "executou": False, "confirmado": False,
        "origem": "verificacao_negativa", "evidencia_confirmacao": "janela não observada",
    }, "executa os dois pedidos")
    assert novo["ultima_acao_confirmada"] is False
    assert novo["ultima_acao_ok"] is False
    assert novo["ultima_acao_contrato"]["origem"] == "verificacao_negativa"
    assert novo["ultima_acao_contrato"]["evidencia_confirmacao"] == "janela não observada"


def test_novo_status_da_mesma_ocorrencia_nao_herda_confirmacao_e_evidencia_anterior() -> None:
    estado = _estado("APP_OPEN", "nome_app", "app_iniciado_focado")
    novo = registrar_resultado_execucao(estado, {
        "intent": "APP_OPEN", "id_solicitacao": "pedido-a", "status": "comando_enviado",
        "params": {"nome_app": "primeiro"}, "executou": True, "confirmado": None,
        "origem": "nova_observacao", "evidencia_confirmacao": "estado final ainda não relido",
    }, "executa os dois pedidos")
    contrato = novo["ultima_acao_contrato"]
    assert contrato["status"] == "comando_enviado"
    assert contrato["confirmado"] is None
    assert novo["ultima_acao_confirmada"] is None
    assert contrato["origem"] == novo["ultima_acao_origem"] == "nova_observacao"
    assert contrato["evidencia_confirmacao"] == "estado final ainda não relido"
    assert novo["ultima_acao_detalhe"] == ""


def test_complemento_generico_da_falha_preserva_status_observado_da_mesma_ocorrencia() -> None:
    estado = registrar_resultado_execucao({}, ResultadoAcao(
        intent="PLAYLIST_ADD", id_solicitacao="pedido-falhou", status="faixa_atual_indisponivel",
        params={"nome_playlist": "lista"}, alvo="lista", executou=False, confirmado=False,
        origem="executor", detalhe="player sem faixa",
    ), "salva esta musica")
    novo = registrar_resultado_execucao(estado, {
        "intent": "PLAYLIST_ADD", "id_solicitacao": "pedido-falhou",
        "params": {"nome_playlist": "lista"},
    }, "salva esta musica", False, origem="roteador")
    assert novo["ultima_acao_status"] == "faixa_atual_indisponivel"
    assert novo["ultima_acao_confirmada"] is False
    assert novo["ultima_acao_ok"] is False
    assert novo["ultima_acao_detalhe"] == "player sem faixa"
    assert novo["ultima_acao_origem"] == novo["ultima_acao_contrato"]["origem"] == "executor"


def test_novo_pedido_nao_republica_efeito_reversivel_do_receipt_anterior() -> None:
    estado = registrar_resultado_execucao({}, ResultadoAcao(
        intent="DELETE_ITEM", id_solicitacao="exclusao-a", alvo="primeiro.txt",
        params={"alvo": "primeiro.txt"}, status="movido_para_lixeira", executou=True,
        confirmado=True, origem="executor", evidencia_confirmacao="arquivo relido na lixeira",
    ), "apaga os dois arquivos")
    receipts = deepcopy(estado["efeitos_reversiveis"]["recibos"])
    novo = registrar_resultado_execucao(estado, {
        "intent": "DELETE_ITEM", "id_solicitacao": "exclusao-b", "params": {"alvo": "segundo.txt"},
    }, "apaga os dois arquivos", True, origem="roteador")
    assert novo["ultima_acao_contrato"]["confirmado"] is None
    assert novo["ultima_acao_alvo"] == "segundo.txt"
    assert novo["efeitos_reversiveis"]["recibos"] == receipts
    assert novo["ultima_acao_reexecutavel"] is False
