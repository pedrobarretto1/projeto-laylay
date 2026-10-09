"""Contratos da troca de provedor sem perder imagens ou autoridade."""

from __future__ import annotations

import threading

import pytest

from mente_laylay.integracao.composicao_inteligencia_externa import (
    ComposicaoInteligenciaExternaRuntime,
)
from mente_laylay.integracao.llm_http import (
    LLMHttpRuntime, RespostaLLMFallback, compactar_payload_llm_local,
)


class Resposta:
    status_code = 200
    text = ""

    def __init__(self, dados):
        self.dados = dados

    def json(self):
        return self.dados


def _compor(ambiente=None, *, capacidades=None):
    chamadas = []

    def post(url, **kwargs):
        chamadas.append((url, kwargs))
        if url.endswith("/api/show"):
            return Resposta({"capabilities": capacidades if capacidades is not None else ["vision", "completion"]})
        return Resposta({"choices": [{"message": {"content": "Um quadrado azul."}}]})

    runtime = ComposicaoInteligenciaExternaRuntime(
        base_url="http://localhost:11434/v1", model="qwen3-vl:4b",
        api_key="local", http_referer="http://localhost", app_title="Laylay",
        normalizar_texto_curto=str.casefold, requests_get=lambda *_a, **_k: None,
        requests_post=post, ao_finalizar_conversa_modo_jogo=lambda: None,
        env_getter=lambda chave, padrao="": dict(ambiente or {}).get(chave, padrao),
        log=lambda *_: None,
    )
    return runtime, chamadas


def test_compactacao_preserva_partes_visuais_e_pergunta_sem_stringificar_pixels():
    partes = [
        {"type": "text", "text": "O que aparece?"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + "A" * 12000}},
    ]
    original = {"model": "qwen3-vl:4b", "messages": [{"role": "user", "content": partes}], "max_tokens": 512}

    compacto = compactar_payload_llm_local(original)

    assert compacto["messages"][0]["content"] == partes
    assert original["messages"][0]["content"] == partes


@pytest.mark.parametrize("rota", ["analisar_imagem", "analisar_imagem_jogo"])
def test_composicao_local_usa_ollama_sem_chave_groq_nas_duas_rotas(rota):
    runtime, chamadas = _compor({"LAYLAY_VISAO_BACKEND": "ollama"})

    assert runtime.credencial_visual_disponivel is True
    descricao = getattr(runtime, rota)("YWJj", "O que aparece?")

    assert descricao == "Um quadrado azul."
    assert chamadas[-1][0] == "http://localhost:11434/v1/chat/completions"
    assert chamadas[-1][1]["json"]["model"] == "qwen3-vl:4b-instruct"
    assert all("groq.com" not in url for url, _ in chamadas)


def test_selecao_local_desativa_conversa_remota_jogo_mesmo_com_chave_groq():
    runtime, _ = _compor({"LAYLAY_VISAO_BACKEND": "ollama", "LAYLAY_CONVERSA_JOGO_REMOTA_ATIVA": "0", "GROQ_API_KEY": "segredo"})

    assert runtime.conversa_jogo.disponivel is False


def test_sintese_cooperativa_preserva_porta_de_uma_entrada_no_modelo_local():
    runtime, chamadas = _compor({"LAYLAY_VISAO_BACKEND": "ollama"})

    assert runtime.sintetizar_pesquisa_jogo("Resuma somente os fatos fornecidos: um quadrado azul.") == "Um quadrado azul."
    assert chamadas[-1][1]["json"]["model"] == "qwen3-vl:4b-instruct"
    assert all("groq.com" not in url for url, _ in chamadas)


def test_compactacao_preserva_partes_textuais_da_sintese_com_fontes_longas():
    partes = [{"type": "text", "text": "Resuma os dados."}, {"type": "text", "text": "Fonte: " + "x" * 11000}]

    compacto = compactar_payload_llm_local({"messages": [{"role": "user", "content": partes}], "max_tokens": 512})

    assert compacto["messages"][0]["content"] == partes


def test_catalogo_local_nao_afirma_visao_quando_modelo_nao_tem_capacidade_visual():
    runtime, chamadas = _compor({"LAYLAY_VISAO_BACKEND": "ollama"}, capacidades=["completion"])

    assert runtime.credencial_visual_disponivel is False
    assert runtime.analisar_imagem("YWJj", "O que aparece?").startswith("Falha visual:")
    assert not any(url.endswith("/chat/completions") for url, _ in chamadas)


@pytest.mark.parametrize("url", ["https://exemplo.invalid/v1", "http://[invalido/v1"])
def test_endpoint_visual_local_nao_envia_imagem_a_url_remota_ou_invalida(url):
    runtime, chamadas = _compor({"LAYLAY_VISAO_BACKEND": "ollama", "LAYLAY_VISAO_OLLAMA_BASE_URL": url})

    assert runtime.credencial_visual_disponivel is False
    assert runtime.analisar_imagem("YWJj", "O que aparece?").startswith("Falha visual:")
    assert chamadas == []


def test_percepcao_local_em_jogo_preserva_pixels_e_economia_das_tarefas_secundarias():
    chamadas = []
    http = LLMHttpRuntime(
        base_url="http://localhost:11434/v1", local_timeout=45, remote_timeout=30,
        requests_post=lambda url, **kwargs: chamadas.append(kwargs["json"]) or Resposta({}),
        print_fn=lambda *_: None,
    )
    http.definir_modo_jogo(True)
    partes = [{"type": "text", "text": "Leia"}, {"type": "image_url", "image_url": {"url": "data:image/png;base64," + "A" * 12000}}]
    bloqueado = http.post({}, {"messages": [{"role": "user", "content": "secundária"}]})

    assert isinstance(bloqueado, RespostaLLMFallback)
    http.post({}, {"model": "qwen3-vl:4b", "messages": [{"role": "user", "content": partes}], "max_tokens": 512, "_laylay_percepcao_visual": True}, timeout=45)

    assert chamadas[0]["messages"][0]["content"] == partes
    assert chamadas[0]["max_tokens"] == 512
    assert "_laylay_percepcao_visual" not in chamadas[0]
    http.definir_modo_jogo(False)


def test_visao_ocupada_nao_bloqueia_conversa_nem_vira_evidencia():
    runtime, chamadas = _compor({"LAYLAY_VISAO_BACKEND": "ollama"})
    assert runtime.credencial_visual_disponivel
    adquirido = threading.Event()
    liberar = threading.Event()

    def ocupar():
        with runtime.http._request_lock:
            adquirido.set()
            liberar.wait(5)

    worker = threading.Thread(target=ocupar)
    worker.start()
    assert adquirido.wait(2)
    try:
        assert runtime.analisar_imagem_jogo("YWJj", "O que aparece?").startswith("Falha visual:")
        assert not any(url.endswith("/chat/completions") for url, _ in chamadas)
    finally:
        liberar.set()
        worker.join(2)
