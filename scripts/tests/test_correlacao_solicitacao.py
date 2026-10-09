"""A ocorrência do pedido limita a mescla de evidência operacional."""

from __future__ import annotations

from copy import deepcopy
import time

import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.orquestrador_turno_runtime import atualizar_planejamento_turno
from mente_laylay.cognicao.plano_turno import atualizar_plano_turno, planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.memoria_mental.correlacao_solicitacao import mesclar_solicitacoes
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.trilha_turno import registrar_etapa_turno


def _receipt(**campos: object) -> dict:
    receipt = {
        "id_solicitacao": "req-a", "intent": "APP_OPEN", "alvo": "Calculadora.exe",
        "params": {"nome_app": "Calculadora.exe", "target": "pc_a"},
        "origem": "executor", "status": "app_iniciado_focado", "executou": True,
        "confirmado": True, "evidencia_confirmacao": "janela observada",
    }
    receipt.update(campos)
    return receipt


def _estado(comandos: list[dict]) -> EstadoCompartilhadoRuntime:
    texto = "abre a Calculadora e o Bloco de Notas"
    turno = classificar_modalidade_turno(texto)
    retrato, _ = construir_retrato_turno(texto, turno=turno, mente={}, contexto_perceptivo={})
    turno["retrato_id"] = retrato["id"]
    plano = atualizar_plano_turno(planejar_turno(texto, turno=turno, mente={}), fase="executado", comandos=comandos)
    return EstadoCompartilhadoRuntime(mental={
        "turno_atual": turno, "retrato_turno_atual": retrato, "plano_turno_atual": plano,
    })


def _publicar(estado: EstadoCompartilhadoRuntime, comandos: list[dict]) -> dict:
    return atualizar_planejamento_turno(lambda: {
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": atualizar_plano_turno,
        "_registrar_etapa_turno_mente": registrar_etapa_turno,
        "time": time, "print": lambda *_args: None,
    }, "executado", comandos=comandos)


@pytest.mark.parametrize("proposta", [
    {"id_solicitacao": "req-a", "acao": "open_app", "alvo": "Calculadora"},
    {"request_id": "req-a", "intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}},
])
def test_republicacao_planejada_preserva_receipt_e_resolucao_do_executor(proposta: dict) -> None:
    estado = _estado([_receipt()])
    anterior = estado.obter_copia("mental", "plano_turno_atual")["comandos"]
    fonte = deepcopy(proposta)
    publicado = _publicar(estado, [proposta])
    assert publicado["comandos"] == anterior
    assert proposta == fonte


@pytest.mark.parametrize("comando", [
    {"id_solicitacao": "req-a", "intent": "CLOSE_APP"},
    {"id_solicitacao": "req-a", "request_id": "req-b", "intent": "APP_OPEN"},
])
def test_conflito_de_identidade_ou_intencao_recusa_publicacao_atomica(comando: dict) -> None:
    estado = _estado([_receipt()])
    antes = estado.snapshot()
    publicado = _publicar(estado, [comando])
    assert publicado == {}, "conflito não pode materializar outra execução na mesma ocorrência"
    assert estado.snapshot() == antes


def test_receipt_de_falha_substitui_faceta_sem_herdar_confirmacao_ou_evidencia() -> None:
    estado = _estado([_receipt()])
    publicado = _publicar(estado, [{
        "id_solicitacao": "req-a", "intent": "APP_OPEN", "origem": "executor",
        "status": "falha_execucao", "executou": False, "confirmado": False,
    }])
    assert len(publicado["comandos"]) == 1
    receipt = publicado["comandos"][0]
    assert receipt["status"] == "falha_execucao" and receipt["executou"] is False
    assert receipt["confirmado"] is False
    assert not receipt["evidencia_confirmacao"]


def test_falha_explicita_sem_confirmacao_nao_preserva_true_anterior() -> None:
    estado = _estado([_receipt()])
    publicado = _publicar(estado, [{
        "id_solicitacao": "req-a", "intent": "APP_OPEN", "origem": "executor",
        "status": "falha_execucao", "executou": False,
    }])
    receipt = publicado["comandos"][0]
    assert receipt["confirmado"] is None
    assert not receipt["evidencia_confirmacao"]


def test_novo_envio_sem_confirmacao_nao_herda_receipt_confirmado() -> None:
    estado = _estado([_receipt()])
    publicado = _publicar(estado, [{
        "id_solicitacao": "req-a", "intent": "APP_OPEN", "origem": "executor",
        "status": "comando_enviado", "executou": True, "confirmado": None,
    }])
    receipt = publicado["comandos"][0]
    assert receipt["status"] == "comando_enviado" and receipt["executou"] is True
    assert receipt["confirmado"] is None
    assert not receipt["evidencia_confirmacao"]


@pytest.mark.parametrize("anterior", [
    {"id_solicitacao": "req-a", "acao": "open_app", "alvo": "Calculadora"},
    {"request_id": " req-a ", "intent": "open_app", "params": {}},
    {"id_solicitacao": "req-a", "intent": "APP_OPEN", "acao": "APP_OPEN", "params": {}},
])
def test_receipt_canonico_complementa_representacoes_compativeis_do_pedido(anterior: dict) -> None:
    fontes = deepcopy([anterior])
    resultado = mesclar_solicitacoes([anterior], [_receipt()])
    assert len(resultado) == 1
    assert resultado[0]["intent"] == "APP_OPEN" and resultado[0]["confirmado"] is True
    assert resultado[0]["alvo"] == "Calculadora.exe"
    assert resultado[0]["params"] == _receipt()["params"]
    assert "request_id" not in resultado[0] and "acao" not in resultado[0]
    assert [anterior] == fontes


@pytest.mark.parametrize("conflitante", [
    _receipt(intent="CLOSE_APP"),
    _receipt(intent="APP_OPEN", acao="close_app"),
    _receipt(request_id="req-b"),
])
def test_duplicata_de_identidade_conflitante_recusa_toda_mescla(conflitante: dict) -> None:
    fontes = [_receipt(), conflitante]
    antes = deepcopy(fontes)
    with pytest.raises(ValueError):
        mesclar_solicitacoes(fontes, [])
    assert fontes == antes


@pytest.mark.parametrize("identidade", [None, 42, True, {}, []])
def test_identidade_malformada_nao_cria_correlacao_por_coercao(identidade: object) -> None:
    with pytest.raises(ValueError):
        mesclar_solicitacoes([_receipt()], [{"id_solicitacao": identidade, "intent": "APP_OPEN"}])


def test_mescla_isola_params_e_contexto_aninhados_sem_alterar_as_fontes() -> None:
    fonte = _receipt(contexto={"observacoes": [{"janela": "Calc"}]})
    resultado = mesclar_solicitacoes([fonte], [{"request_id": "req-a", "intent": "APP_OPEN"}])
    resultado[0]["params"]["nome_app"] = "outro"
    resultado[0]["contexto"]["observacoes"][0]["janela"] = "outra"
    assert fonte["params"]["nome_app"] == "Calculadora.exe"
    assert fonte["contexto"]["observacoes"][0]["janela"] == "Calc"


def test_legados_identicos_continuam_ocorrencias_independentes_sem_receipt_transferido() -> None:
    anterior = _receipt(id_solicitacao="")
    nova = {"intent": "APP_OPEN", "alvo": "Calculadora.exe", "params": anterior["params"]}
    resultado = mesclar_solicitacoes([anterior], [nova, nova])
    assert len(resultado) == 3
    assert resultado[0]["confirmado"] is True
    assert all("confirmado" not in item and "status" not in item for item in resultado[1:])


def test_republicacao_nao_reordena_receipt_atualizado_entre_pedidos_independentes() -> None:
    anteriores = [_receipt(), _receipt(id_solicitacao="req-b", alvo="Bloco de Notas")]
    resultado = mesclar_solicitacoes(anteriores, [_receipt(status="comando_enviado", confirmado=None)])
    assert [item["id_solicitacao"] for item in resultado] == ["req-a", "req-b"]
    assert resultado[0]["confirmado"] is None
    assert resultado[1] == anteriores[1]


def test_alias_condicional_reutiliza_normalizador_sem_resolver_novamente_o_alvo() -> None:
    anterior = {"id_solicitacao": "req-a", "acao": "fechar", "alvo": "Calculadora"}
    receipt = _receipt(intent="CLOSE_APP", alvo="Calculadora.exe", status="app_fechado")
    resultado = mesclar_solicitacoes([anterior], [receipt])
    assert len(resultado) == 1 and resultado[0]["intent"] == "CLOSE_APP"
    assert resultado[0]["alvo"] == "Calculadora.exe" and resultado[0]["confirmado"] is True
