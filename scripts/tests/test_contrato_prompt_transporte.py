"""O orçamento corta contexto opcional, nunca a instrução do ato atual."""

import threading
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime, preparar_contexto_resposta_ia
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
from mente_laylay.integracao.llm_http import compactar_payload_llm_local, post_chat_llm
from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT, BASE_SYSTEM_PROMPT_RAPIDO


CONTRATO = "--- CONTRATO SEMÂNTICO DA FALA ---\n" + "regra necessária; " * 100 + "FIM_CONTRATO_ATUAL"
EVIDENCIA = "--- EVIDÊNCIA FACTUAL EFÊMERA DO TURNO ---\nfonte confirmada: alvo B, resultado parcial."
USUARIO = "Ontem pedi para abrir o Opera; estou só relatando."


def pacote():
    mensagens, _ = preparar_contexto_resposta_ia(
        {"retrato_mente_integrada": "--- MENTE INTEGRADA ---\n" + "contexto opcional " * 600,
         "contexto_contrato_fala": CONTRATO, "contexto_fundamentacao_prioritaria": EVIDENCIA},
        USUARIO, [], 0, BASE_SYSTEM_PROMPT,
    )
    mensagens.append({"role": "user", "content": USUARIO})
    return preparar_payload_llm(mensagens, model="qwen3:4b-instruct", max_tokens=224, endpoint_local=True)


@pytest.mark.parametrize("limite", [128, 224, 360, 800])
def test_preparador_e_transporte_preservam_contrato_e_receipt_inteiros(limite):
    original = pacote()
    original["max_tokens"] = limite
    compacto = compactar_payload_llm_local(original)
    for payload in (original, compacto, compactar_payload_llm_local(compacto)):
        mensagens = payload["messages"]
        atual = next(i for i, m in enumerate(mensagens) if m["role"] == "user" and m["content"] == USUARIO)
        assert mensagens[atual - 1]["role"] == "system"
        assert CONTRATO in mensagens[atual - 1]["content"]
        assert EVIDENCIA in mensagens[atual - 1]["content"]
        assert sum(m["content"].count("FIM_CONTRATO_ATUAL") for m in mensagens) == 1
    assert len(compacto["messages"][0]["content"]) < len(original["messages"][0]["content"])


def test_turno_atomico_pode_ultrapassar_orcamento_sem_perder_fim_da_fala():
    instrucao = "contrato " * 1000 + "NAO_EXECUTAR"
    entrada = "texto atual " * 1000 + "APENAS_RELATO"
    payload = {"max_tokens": 128, "messages": [
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
        {"role": "system", "content": instrucao},
        {"role": "user", "content": entrada},
    ]}
    saida = compactar_payload_llm_local(payload)["messages"]
    assert saida[-2:] == payload["messages"][-2:]


def test_retry_http_nao_desfaz_protecao_do_turno():
    enviados = []
    def post(url, **kwargs):
        enviados.append(kwargs["json"])
        return SimpleNamespace(status_code=400 if len(enviados) == 1 else 200, text="diagnóstico")
    resultado, _ = post_chat_llm(
        {}, pacote(), base_url="http://localhost:11434/v1", local_timeout=30,
        remote_timeout=30, bad_request_until=0, lock=threading.Lock(),
        requests_post=post, print_fn=lambda *args: None,
    )
    assert resultado.status_code == 200
    assert len(enviados) == 2
    for payload in enviados:
        assert CONTRATO in payload["messages"][-2]["content"]
        assert EVIDENCIA in payload["messages"][-2]["content"]
        assert payload["messages"][-1]["content"] == USUARIO


def test_entrada_repetida_nao_duplica_instrucao_do_turno():
    payload = {"max_tokens": 800, "messages": [
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
        {"role": "user", "content": "repete"},
        {"role": "assistant", "content": "qual parte?"},
        {"role": "system", "content": CONTRATO},
        {"role": "user", "content": "repete"},
    ]}
    compacto = compactar_payload_llm_local(payload)
    assert sum(m["content"].count("FIM_CONTRATO_ATUAL") for m in compacto["messages"]) == 1
    assert compacto["messages"][-2]["content"] == CONTRATO


def test_prompt_rapido_pede_json_tambem_no_contrato_de_transporte():
    payload = preparar_payload_llm(
        [
            {"role": "system", "content": BASE_SYSTEM_PROMPT_RAPIDO},
            {"role": "user", "content": "Estou muito feliz porque terminei um projeto."},
        ],
        model="qwen3:4b-instruct", modo_rapido=True,
        max_tokens=256, endpoint_local=True,
    )

    assert payload["response_format"] == {"type": "json_object"}


@pytest.mark.parametrize("limite", [128, 224, 360, 800])
@pytest.mark.parametrize("base", [BASE_SYSTEM_PROMPT, BASE_SYSTEM_PROMPT_RAPIDO], ids=["normal", "rapido"])
def test_compactacao_nao_corta_protocolo_permanente_de_saida(base, limite):
    payload = {"max_tokens": limite, "messages": [
        {"role": "system", "content": base + "\n" + "contexto opcional " * 900},
        {"role": "user", "content": "oi"},
    ]}
    for _ in range(2):
        payload = compactar_payload_llm_local(payload)
        assert payload["messages"][0]["content"].startswith(base)
        assert "Retorne somente JSON válido" in payload["messages"][0]["content"]


def _pacote_capacidade(texto, intent, disponivel, rapido):
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is False
    plano = planejar_turno(texto, turno=turno, mente={})
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente={})
    mapa = MapaHabilidadesRuntime(operacional_getter=lambda: {
        "capacidades": {intent: {
            "estado": "disponivel" if disponivel else "indisponivel",
            "motivo": "" if disponivel else "precondicao_operacional_ausente",
        }},
    })
    evidencia = mapa.contexto_para_prompt(texto, turno=turno)
    if not disponivel:
        assert f"Indisponíveis agora: {intent}" in evidencia
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None,
        resumo_mente_integrada=lambda _: "--- MENTE INTEGRADA ---\n" + "contexto opcional " * 600,
        formatar_playlists=lambda: "", get_status_humor_prompt=lambda: "",
        base_system_prompt=BASE_SYSTEM_PROMPT,
        estado_getter=lambda: {"turno_atual": turno, "contrato_fala_atual": contrato},
        mapa_habilidades_prompt=mapa.contexto_para_prompt,
    )
    if rapido:
        mensagens = [{"role": "system", "content": BASE_SYSTEM_PROMPT},
                     {"role": "system", "content": runtime.preparar_instrucao_rapida(texto)}]
    else:
        mensagens = list(runtime.preparar_pacote(texto).mensagens)
    mensagens.append({"role": "user", "content": texto})
    payload = preparar_payload_llm(mensagens, model="qwen3:4b-instruct", modo_rapido=rapido,
                                  max_tokens=256, endpoint_local=True)
    return payload, evidencia


@pytest.mark.parametrize("texto,intent", [
    ("como eu poderia pausar a música?", "MEDIA_CONTROL"),
    ("como pausar a música", "MEDIA_CONTROL"),
    ("como eu poderia ajustar o volume?", "VOLUME"),
    ("como eu poderia ligar a lâmpada?", "IOT_CONTROL"),
])
@pytest.mark.parametrize("disponivel", [True, False], ids=["disponivel", "indisponivel"])
@pytest.mark.parametrize("rapido", [False, True], ids=["normal", "rapido"])
def test_capacidade_viva_relevante_sobrevive_ao_orcamento_sem_virar_autorizacao(texto, intent, disponivel, rapido):
    payload, evidencia = _pacote_capacidade(texto, intent, disponivel, rapido)
    # A montagem precisa selecionar a fonte antes de testar o transporte.
    assert evidencia in "\n".join(m["content"] for m in payload["messages"])
    for _ in range(2):
        payload = compactar_payload_llm_local(payload)
        assert payload["messages"][-1] == {"role": "user", "content": texto}
        assert evidencia in payload["messages"][-2]["content"]
        assert sum(m["content"].count(evidencia) for m in payload["messages"]) == 1
        assert "não autoriza ações" in payload["messages"][-2]["content"]


def test_retry_http_preserva_capacidade_indisponivel_sem_converte_la_em_promessa():
    payload, evidencia = _pacote_capacidade("como eu poderia pausar a música?", "MEDIA_CONTROL", False, False)
    enviados = []
    def post(url, **kwargs):
        enviados.append(kwargs["json"])
        return SimpleNamespace(status_code=400 if len(enviados) == 1 else 200, text="diagnóstico")
    resultado, _ = post_chat_llm(
        {}, payload, base_url="http://localhost:11434/v1", local_timeout=30,
        remote_timeout=30, bad_request_until=0, lock=threading.Lock(),
        requests_post=post, print_fn=lambda *args: None,
    )
    assert resultado.status_code == 200
    assert len(enviados) == 2
    assert all(evidencia in item["messages"][-2]["content"] for item in enviados)
