"""Medição da geração: não consultar a rede nem modificar produção."""
import pytest

from types import SimpleNamespace
import requests

from scripts.analises.sonda_escopo_geracao_real import (
    comparar_escopos, criar_guarda_http_local, selecao_local,
)

PAUSA = {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}
SELECAO = {"LAYLAY_LLM_BASE_URL": "http://localhost:11434/v1", "LAYLAY_LLM_MODEL": "teste"}


def test_guarda_requests_aceita_method_e_url_por_keyword_e_preserva_payload():
    recebidos, transportes = [], []
    def original(sessao, method, url, **opcoes):
        recebidos.append((method, url, opcoes))
        return SimpleNamespace(status_code=200, text='{"content":"real"}')
    guarda = criar_guarda_http_local(SELECAO, transportes, original)
    guarda(None, method="post", url="http://localhost:11434/v1/chat/completions", json={"model": "teste"})
    assert len(recebidos) == 1
    assert transportes[0]["status"] == 200
    assert transportes[0]["payload"] == {"model": "teste"}


@pytest.mark.parametrize("url,modelo", [
    ("http://example.com/v1/chat/completions", "teste"),
    ("http://localhost:11435/v1/chat/completions", "teste"),
    ("http://localhost:11434/v1/chat/completions", "outro"),
    ("http://localhost:11434/consulta", "teste"),
])
def test_guarda_nao_faz_chamada_fora_do_modelo_e_destino_autorizados(url, modelo):
    def proibido(*a, **k):
        pytest.fail("a guarda não bloqueou a chamada")
    transportes = []
    guarda = criar_guarda_http_local(SELECAO, transportes, proibido)
    with pytest.raises(requests.RequestException):
        guarda(None, method="POST", url=url, json={"model": modelo})
    assert transportes == []


def test_equivalencia_de_formato_nao_e_falso_bloqueio():
    assert comparar_escopos([PAUSA], [{"acao": "youtube_control", "alvo": "pause"}]) == {
        "indevidos": [], "ausentes": []}


def test_ausencia_e_proposta_indevida_sao_metricas_distintas():
    play = {"intent": "MEDIA_CONTROL", "params": {"acao": "play"}}
    assert comparar_escopos([PAUSA], [play]) == {"indevidos": [play], "ausentes": [PAUSA]}
    assert comparar_escopos([PAUSA], []) == {"indevidos": [], "ausentes": [PAUSA]}


def test_medicao_nao_perde_multiplicidade_da_autorizacao():
    assert comparar_escopos([PAUSA, PAUSA], [PAUSA])["ausentes"] == [PAUSA]
    assert comparar_escopos([PAUSA], [PAUSA, PAUSA])["indevidos"] == [PAUSA]


@pytest.mark.parametrize("url", ["https://example.com/v1", "http://localhost:11434/v1?x=1",
                                "http://usuario:senha@localhost:11434/v1"])
def test_selecao_bloqueia_provedor_remoto_ou_url_com_credencial(monkeypatch, url):
    monkeypatch.setattr("pathlib.Path.read_text", lambda *_a, **_k:
        f"LAYLAY_LLM_BACKEND=ollama\nLAYLAY_LLM_MODEL=teste\nLAYLAY_LLM_BASE_URL={url}")
    with pytest.raises(RuntimeError):
        selecao_local()
