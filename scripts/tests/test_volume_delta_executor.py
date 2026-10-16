"""Delta explícito preservado pelo executor; portas de áudio são fixtures.

Nenhum áudio físico, PC remoto ou voz é acionado por estes contratos locais.
"""
from __future__ import annotations

from copy import deepcopy

import pytest

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_audio import (
    DependenciasExecutorAudio,
    executar_intencao_audio,
)


def _dependencias(eventos: list[tuple]) -> DependenciasExecutorAudio:
    return DependenciasExecutorAudio(
        marcar_resultado=lambda status, **dados: eventos.append(("resultado", status, dados)),
        falar_por_status=lambda status, fala, **dados: eventos.append(("fala_status", status, fala, dados)),
    )


@pytest.mark.parametrize("acao,sinal,status", [
    ("up", 1, "volume_aumentado"), ("down", -1, "volume_baixado"),
])
@pytest.mark.parametrize("delta", [5, 25, 100])
def test_delta_local_preserva_magnitude_direcao_e_releitura(acao, sinal, status, delta):
    eventos, chamadas = [], []
    observado = {"volume": 40}
    esperado = max(0, min(100, 40 + sinal * delta))

    def ler():
        chamadas.append(("leitura", observado["volume"]))
        return observado["volume"]

    def ajustar(valor):
        chamadas.append(("ajuste", valor))
        observado["volume"] = max(0, min(100, observado["volume"] + valor))

    params = {"acao": acao, "delta": delta}
    antes = deepcopy(params)
    retorno = executar_intencao_audio("VOLUME", params, "pc_a", {
        "obter_volume_sistema": ler, "ajustar_volume_sistema_relativo": ajustar,
    }, _dependencias(eventos))

    assert retorno == ResultadoDespacho.concluido()
    assert chamadas == [("leitura", 40), ("ajuste", sinal * delta), ("leitura", esperado)]
    assert eventos[0][0:2] == ("resultado", status)
    assert eventos[0][2]["executou"] is True
    assert eventos[0][2]["confirmado"] is True
    assert eventos[0][2]["contexto_resultado"]["volume_observado"] == esperado
    assert params == antes


@pytest.mark.parametrize("acao", ["up", "down"])
def test_delta_local_nao_confirma_releitura_divergente(acao):
    eventos, deltas = [], []
    leituras = iter([40, 80])

    executar_intencao_audio("VOLUME", {"acao": acao, "delta": 5}, "pc_a", {
        "obter_volume_sistema": lambda: next(leituras),
        "ajustar_volume_sistema_relativo": deltas.append,
    }, _dependencias(eventos))

    assert deltas == ([5] if acao == "up" else [-5])
    assert eventos[0][0:2] == ("resultado", "falha_execucao")
    assert eventos[0][2]["executou"] is True
    assert eventos[0][2]["confirmado"] is False
    assert f"esperado {45 if acao == 'up' else 35}%" in eventos[0][2]["detalhe"]


@pytest.mark.parametrize("acao,action", [("up", "volume_up"), ("down", "volume_down")])
@pytest.mark.parametrize("delta", [5, 25, 100])
def test_delta_remoto_preserva_payload_e_receipt_sem_leitura_local(acao, action, delta):
    eventos, payloads = [], []

    def enviar(payload):
        payloads.append(deepcopy(payload))
        return {"status": "success", "executed": True, "confirmed": True,
            "volume": 75, "requestId": "fixture-volume-remoto", "error": ""}

    executar_intencao_audio("VOLUME", {"acao": acao, "delta": delta}, "pc_b", {
        "_enviar_pc_b_detalhado": enviar,
        "obter_volume_sistema": lambda: pytest.fail("destino remoto não lê volume local"),
        "ajustar_volume_sistema_relativo": lambda *_: pytest.fail("destino remoto não ajusta local"),
    }, _dependencias(eventos))

    assert payloads == [{"action": action, "delta": delta}]
    assert eventos[0][0:2] == ("resultado", "volume_aumentado" if acao == "up" else "volume_baixado")
    assert eventos[0][2]["executou"] is True
    assert eventos[0][2]["confirmado"] is True
    assert eventos[0][2]["contexto_resultado"]["request_id_remoto"] == "fixture-volume-remoto"
    assert eventos[0][2]["contexto_resultado"]["volume_observado"] == 75


@pytest.mark.parametrize("confirmado", [False, None])
def test_delta_remoto_nao_promove_confirmacao_ausente(confirmado):
    eventos, payloads = [], []

    def enviar(payload):
        payloads.append(payload)
        return {"status": "error" if confirmado is False else "pending", "executed": True,
            "confirmed": confirmado, "requestId": "fixture-incerta", "error": ""}

    executar_intencao_audio("VOLUME", {"acao": "up", "delta": 5}, "pc_b", {
        "_enviar_pc_b_detalhado": enviar,
    }, _dependencias(eventos))

    assert payloads == [{"action": "volume_up", "delta": 5}]
    assert eventos[0][2]["executou"] is True
    assert eventos[0][2].get("confirmado") is confirmado
    assert eventos[0][1] == ("falha_execucao" if confirmado is False else "volume_aumentado")


@pytest.mark.parametrize("acao,sinal", [("up", 1), ("down", -1), ("aumentar", 1), ("baixar", -1)])
@pytest.mark.parametrize("destino", ["pc_a", "pc_b"])
def test_ausencia_delta_preserva_passo_legado_de_dez(acao, sinal, destino):
    eventos, deltas, remotos = [], [], []
    executar_intencao_audio("VOLUME", {"acao": acao}, destino, {
        "ajustar_volume_sistema_relativo": deltas.append,
        "_enviar_pc_b": lambda payload: remotos.append(payload) or True,
    }, _dependencias(eventos))

    assert deltas == ([sinal * 10] if destino == "pc_a" else [])
    assert remotos == ([{"action": "volume_up" if sinal > 0 else "volume_down", "delta": 10}]
                       if destino == "pc_b" else [])
    assert eventos[0][2] == {"executou": True}


@pytest.mark.parametrize("acao,sinal", [("aumentar", 1), ("aumenta", 1),
    ("baixar", -1), ("baixa", -1)])
def test_alias_relativo_preserva_delta_explicito_sem_trocar_direcao(acao, sinal):
    eventos, deltas = [], []
    executar_intencao_audio("VOLUME", {"acao": acao, "delta": 5}, "pc_a", {
        "ajustar_volume_sistema_relativo": deltas.append,
    }, _dependencias(eventos))
    assert deltas == [sinal * 5]
    assert eventos[0][2] == {"executou": True}


INVALIDOS = [True, False, "5", 5.0, None, 0, -5, 101, float("nan"), float("inf")]


@pytest.mark.parametrize("delta", INVALIDOS)
@pytest.mark.parametrize("acao", ["up", "down"])
@pytest.mark.parametrize("destino", ["pc_a", "pc_b"])
def test_delta_invalido_e_recusado_antes_de_leitura_ou_efeito(delta, acao, destino):
    _assert_recusa_antes_das_portas({"acao": acao, "delta": delta}, destino)


def _assert_recusa_antes_das_portas(params, destino="pc_a"):
    eventos, chamadas, falas = [], [], []

    def porta(nome):
        def chamar(*args):
            chamadas.append((nome, args))
            return True
        return chamar

    retorno = executar_intencao_audio("VOLUME", params, destino, {
        "obter_volume_sistema": porta("leitura"),
        "ajustar_volume_sistema_relativo": porta("relativo"),
        "ajustar_volume_sistema": porta("absoluto"),
        "definir_mudo_sistema": porta("mudo"),
        "_enviar_pc_b": porta("remoto"),
        "_enviar_pc_b_detalhado": porta("remoto_detalhado"),
        "falar_com_lipsync": lambda *fala: falas.append(fala),
    }, _dependencias(eventos))

    assert retorno == ResultadoDespacho.concluido()
    assert chamadas == [], "contrato inválido alcançou percepção/efeito"
    assert eventos[0] == ("resultado", "acao_invalida", {"executou": False, "confirmado": False})
    assert falas or any(e[0] == "fala_status" for e in eventos), "recusa consumida sem conclusão"


@pytest.mark.parametrize("campo,valor", [("nivel_volume", 30), ("value", 30),
    ("nivel_volume", None), ("value", None)])
@pytest.mark.parametrize("destino", ["pc_a", "pc_b"])
def test_delta_nao_coexiste_com_valor_absoluto(campo, valor, destino):
    _assert_recusa_antes_das_portas({"acao": "up", "delta": 5, campo: valor}, destino)


@pytest.mark.parametrize("acao", ["set", "mute", "unmute", "", "aumento_inventado"])
@pytest.mark.parametrize("destino", ["pc_a", "pc_b"])
def test_delta_nao_e_ignorado_por_outra_acao(acao, destino):
    _assert_recusa_antes_das_portas({"acao": acao, "delta": 5}, destino)


@pytest.mark.parametrize("unidade", ["db", "dB", "decibeis", "minutos", "%", 5, None])
def test_delta_nao_aceita_unidade_incompativel(unidade):
    _assert_recusa_antes_das_portas({"acao": "up", "delta": 5, "unidade": unidade})


@pytest.mark.parametrize("unidade", ["pontos_percentuais", "pontos percentuais"])
def test_delta_em_pontos_percentuais_explicito_preserva_magnitude(unidade):
    eventos, deltas = [], []
    executar_intencao_audio("VOLUME", {"acao": "up", "delta": 5, "unidade": unidade}, "pc_a", {
        "ajustar_volume_sistema_relativo": deltas.append,
    }, _dependencias(eventos))
    assert deltas == [5]
    assert eventos[0] == ("resultado", "volume_aumentado", {"executou": True})


def test_excecao_no_ajuste_delta_nao_publica_sucesso():
    eventos, chamadas = [], []

    def falhar(delta):
        chamadas.append(delta)
        raise RuntimeError("fixture de indisponibilidade")

    executar_intencao_audio("VOLUME", {"acao": "up", "delta": 5}, "pc_a", {
        "obter_volume_sistema": lambda: 40,
        "ajustar_volume_sistema_relativo": falhar,
    }, _dependencias(eventos))

    assert chamadas == [5]
    assert eventos[0] == ("resultado", "falha_execucao", {"executou": False, "confirmado": False})
