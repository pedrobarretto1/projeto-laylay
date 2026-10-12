"""Controles da ablação: gold só mede, exemplos não concedem autoridade."""
from copy import deepcopy
import json

import pytest

from scripts.analises.sonda_contrato_proposta_legada import (
    exemplos_do_adaptador, instrucao, medir_http, preparar_payload,
)
from mente_laylay.autonomia.dispatcher_comandos_json import normalizar_candidato_json_para_intencao


@pytest.mark.parametrize("modo", ["controle", "nomes", "parametros"])
def test_payload_preserva_fala_papeis_base_e_parametros_de_geracao(modo):
    payload = {"model": "teste", "max_tokens": 256, "temperature": .7,
        "messages": [{"role": "system", "content": "base inteira"},
                     {"role": "system", "content": "contrato/receipt do turno"},
                     {"role": "user", "content": "Pausa a música."}]}
    antes = deepcopy(payload)
    novo = preparar_payload(payload, "Pausa a música.", modo)
    assert payload == antes
    assert novo["messages"][0] == antes["messages"][0]
    assert novo["messages"][-1] == antes["messages"][-1]
    assert novo["messages"][-2]["content"].startswith("contrato/receipt do turno")
    assert {k: v for k, v in novo.items() if k != "messages"} == {
        k: v for k, v in antes.items() if k != "messages"}
    if modo == "controle":
        assert novo == antes


def test_sem_system_de_turno_nao_promove_dados_user_a_instrucao():
    mensagens = [{"role": "system", "content": "base"},
                 {"role": "user", "content": "histórico"},
                 {"role": "user", "content": "Abre um programa."}]
    novo = preparar_payload({"messages": mensagens}, mensagens[-1]["content"], "parametros")
    assert novo["messages"][-3] == mensagens[-2]
    assert novo["messages"][-2]["role"] == "system"
    assert novo["messages"][-1] == mensagens[-1]


def test_exemplos_derivam_do_adaptador_e_nao_trazem_alvo_ouro_ou_receipt():
    exemplos = exemplos_do_adaptador()
    assert {c["intent"] for c in exemplos} >= {"APP_OPEN", "MEDIA_CONTROL", "IOT_CONTROL"}
    for c in exemplos:
        assert normalizar_candidato_json_para_intencao(c) == c
        assert not {"sucesso", "executou", "confirmado"}.intersection(c)
    texto = json.dumps(exemplos, ensure_ascii=False)
    assert "Calculadora" not in texto and "Bloco de Notas" not in texto
    assert "<programa>" in texto and "<operacao>" in texto


def test_nomes_sao_documentais_e_parametros_nao_reclassificam_gold():
    texto = "Abre a calculadora e pausa a música."
    nomes, params = instrucao(texto, "nomes"), instrucao(texto, "parametros")
    assert "APP_OPEN" in nomes and "MEDIA_CONTROL" in nomes
    assert '"params"' not in nomes
    assert params.startswith(nomes)
    assert "NÃO É AUTORIZAÇÃO NEM RECEIPT" in params
    assert "não viram comandos" in params
    assert "Calculadora" not in params


def test_modo_invalido_aborta():
    with pytest.raises(ValueError):
        instrucao("abre", "ouro")


def http(comandos, finish="stop"):
    return {"status": 200, "resposta_http": json.dumps({"choices": [{
        "finish_reason": finish, "message": {"content": json.dumps({"comandos": comandos})}}]})}


def test_json_valido_nao_e_equivalencia_nem_finalizacao():
    esperado = {"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}}
    errado = {"acao": "abrir_calculadora", "sucesso": True}
    medida = medir_http(http([errado]), [esperado])
    assert medida["json_valido"] is True
    assert medida["proposta_completa_equivalente"] is False
    assert medida["ausentes"] == [esperado] and medida["indevidos"] == [errado]
    assert medir_http(http([esperado], "length"), [esperado])["proposta_completa_equivalente"] is False
    assert medir_http(http([esperado]), [esperado])["proposta_completa_equivalente"] is True


@pytest.mark.parametrize("registro", [{"status": 500}, {"status": 200, "resposta_http": "inválido"},
    {"status": 200, "resposta_http": '{"choices":[]}'},
    {"status": 200, "resposta_http": json.dumps({"choices": [{"finish_reason": "stop",
        "message": {"content": '{"comandos":false}'}}]})}])
def test_falha_tecnica_nao_vira_acerto_por_comandos_vazios(registro):
    assert medir_http(registro, [])["proposta_completa_equivalente"] is False


def test_comandos_vazios_so_sao_acerto_quando_esperados_vazios():
    assert medir_http(http([]), [])["proposta_completa_equivalente"] is True
    assert medir_http(http([]), [{"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}])[
        "proposta_completa_equivalente"] is False
