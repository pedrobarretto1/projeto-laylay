"""Replay de texto histórico não pode escolher outra rota/modelo nem executar."""
from copy import deepcopy
import json

import pytest

from scripts.analises import sonda_latencia_autoria_local as sonda


@pytest.fixture
def replay():
    selecao = {"LAYLAY_LLM_MODEL": "qwen3:4b-instruct",
        "LAYLAY_LLM_BASE_URL": "http://localhost:11434/v1", "LAYLAY_LLM_BACKEND": "ollama"}
    dados = {"autoria": "real", "chamadas": [{"receipts": [{"id_solicitacao": "fixture-1"}]}],
        "transportes_autoria": [{"url": "http://localhost:11434/v1/chat/completions", "payload": {
            "model": selecao["LAYLAY_LLM_MODEL"], "messages": [
                {"role": "system", "content": "Contrato de autoria da fixture"},
                {"role": "user", "content": json.dumps({"resultados": [{"id_solicitacao": "fixture-1"}]})}],
            "max_tokens": 512, "temperature": 0.7}}]}
    return dados, selecao


def test_replay_preserva_payload_sem_expor_mutacoes(replay):
    dados, selecao = replay
    antes = deepcopy(dados)
    url, payload = sonda.preparar_replay(dados, selecao)
    assert url == dados["transportes_autoria"][0]["url"]
    assert payload == dados["transportes_autoria"][0]["payload"]
    payload["messages"][0]["content"] = "mudou na copia"
    assert dados == antes


@pytest.mark.parametrize("violacao", ["modelo", "rota", "tools", "duplicada", "receipt", "controlada", "mensagens"])
def test_replay_divergente_recusa_antes_de_rede(monkeypatch, replay, violacao):
    dados, selecao = replay
    registro = dados["transportes_autoria"][0]
    if violacao == "modelo": registro["payload"]["model"] = "outro"
    if violacao == "rota": registro["url"] = "http://outro:11434/v1/chat/completions"
    if violacao == "tools": registro["payload"]["tools"] = []
    if violacao == "duplicada": dados["transportes_autoria"].append(deepcopy(registro))
    if violacao == "receipt": dados["chamadas"][0]["receipts"][0]["id_solicitacao"] = "outro"
    if violacao == "controlada": dados["autoria"] = "controlada"
    if violacao == "mensagens": registro["payload"]["messages"][1]["role"] = "assistant"
    def proibido(): raise AssertionError("rede/sessão alcançada antes da guarda")
    monkeypatch.setattr(sonda, "verificar_sessao", proibido)
    with pytest.raises(ValueError):
        sonda.coletar(dados, selecao)
    with pytest.raises(ValueError):
        sonda.coletar_autoria_instalada(dados, selecao)
    with pytest.raises(ValueError):
        sonda.coletar_corrida_startup(dados, selecao)


def test_destino_existente_nao_le_fonte_nem_inicia_sessao(monkeypatch, tmp_path):
    pasta = tmp_path / "resultados_testes"
    pasta.mkdir()
    destino = pasta / "resultado.json"
    destino.touch()
    monkeypatch.setattr(sonda, "RAIZ", tmp_path)
    monkeypatch.setattr("sys.argv", ["sonda", "--artefato", str(pasta / "ausente.json"), "--saida", str(destino)])
    def proibido(): raise AssertionError("sessão indevida")
    monkeypatch.setattr(sonda, "verificar_sessao", proibido)
    with pytest.raises(SystemExit) as erro:
        sonda.main()
    assert erro.value.code == 2 and destino.stat().st_size == 0


def test_destino_externo_recusado_antes_de_ler_fonte(monkeypatch, tmp_path):
    monkeypatch.setattr(sonda, "RAIZ", tmp_path)
    monkeypatch.setattr("sys.argv", ["sonda", "--artefato", str(tmp_path / "resultados_testes/fonte.json"),
        "--saida", str(tmp_path / "externo.json")])
    with pytest.raises(SystemExit) as erro:
        sonda.main()
    assert erro.value.code == 2


def test_modos_instalados_mutuamente_exclusivos_nao_iniciam_sessao(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", ["sonda", "--artefato", str(tmp_path / "ausente.json"),
        "--saida", str(tmp_path / "resultado.json"), "--corrida-startup", "--somente-instalada"])
    def proibido(): raise AssertionError("sessão não deve começar com modo ambíguo")
    monkeypatch.setattr(sonda, "verificar_sessao", proibido)
    with pytest.raises(SystemExit) as erro:
        sonda.main()
    assert erro.value.code == 2
