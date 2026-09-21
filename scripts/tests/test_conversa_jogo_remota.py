from __future__ import annotations

from mente_laylay.integracao.conversa_jogo_remota import (
    ConversaJogoRemotaRuntime,
    _mensagens_minimas,
)
from mente_laylay.integracao.preparador_requisicao_llm import (
    PreparadorRequisicaoLLMRuntime,
)
from mente_laylay.integracao.registro_conversa_llm import PedidoModelo
from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT_RAPIDO


class _Resposta:
    def __init__(self, texto: str = "Tô bem. E você?", status: int = 200) -> None:
        self.status_code = status
        self._texto = texto

    def json(self):
        return {"choices": [{"message": {"content": self._texto}}]}


def test_contexto_remoto_preserva_personalidade_e_so_o_fio_recente() -> None:
    mensagens = [
        {"role": "system", "content": "personalidade"},
        *[
            {"role": "user" if indice % 2 == 0 else "assistant", "content": f"turno {indice}"}
            for indice in range(10)
        ],
    ]

    compactadas = _mensagens_minimas({"messages": mensagens})

    assert compactadas[0] == {"role": "system", "content": "personalidade"}
    assert len(compactadas) == 7
    assert compactadas[1]["content"] == "turno 4"
    assert compactadas[-1]["content"] == "turno 9"


def test_contexto_remoto_preserva_evento_cognitivo_adicionado_apos_o_fio() -> None:
    mensagens = [
        {"role": "system", "content": "personalidade"},
        {"role": "user", "content": "continua"},
        {"role": "assistant", "content": "Claro."},
        {
            "role": "system",
            "content": (
                "EVENTO COGNITIVO ESTRUTURADO.\n"
                'DADOS: {"dominio":"jogo","observacao":"Forza Horizon aberto"}'
            ),
        },
    ]

    compactadas = _mensagens_minimas({"messages": mensagens})

    sistemas = [item["content"] for item in compactadas if item["role"] == "system"]
    assert any("Forza Horizon aberto" in conteudo for conteudo in sistemas)


def test_evento_sem_historico_recebe_consulta_tecnica_sem_virar_fala_de_pedro() -> None:
    chamadas = []

    def postar(_url, **kwargs):
        mensagens = list(kwargs["json"]["messages"])
        chamadas.append(mensagens)
        possui_consulta = any(item.get("role") == "user" for item in mensagens)
        return _Resposta(
            '{"fala":"Essa paisagem ficou bonita, hein.","comandos":[]}',
            status=200 if possui_consulta else 400,
        )

    runtime = ConversaJogoRemotaRuntime(
        api_key="segredo",
        model="qwen/qwen3.6-27b",
        requests_post=postar,
        log=lambda *_args: None,
    )

    resposta = runtime.enviar({
        "messages": [{
            "role": "system",
            "content": (
                "EVENTO COGNITIVO ESTRUTURADO. Isto descreve algo observado; "
                "não é fala de Pedro, pedido, confirmação nem permissão."
            ),
        }],
        "max_tokens": 120,
    })

    assert resposta.startswith('{"fala":')
    assert [item["role"] for item in chamadas[0]] == ["system", "user"]
    consulta = chamadas[0][-1]["content"]
    assert "SOLICITAÇÃO TÉCNICA INTERNA" in consulta
    assert "não é fala, pedido, confirmação ou autorização de Pedro" in consulta
    assert "não execute ações" in consulta


def test_preparador_real_nao_descarta_evento_sem_utterance_antes_da_groq() -> None:
    evento = (
        "EVENTO COGNITIVO ESTRUTURADO. Isto descreve algo observado; "
        "não é fala de Pedro, pedido, confirmação nem permissão."
    )
    preparador = PreparadorRequisicaoLLMRuntime(
        model="Qwen3:4b-instruct",
        endpoint_local_getter=lambda: True,
        resumo_do_dia_getter=lambda: "",
        data_atual_getter=lambda: "",
        normalizar_texto=lambda texto: texto,
        mapear_pastas=lambda: "",
        contexto_logs_getter=lambda: (),
        contexto_navegador_relevante=lambda _texto: False,
        contexto_sistema_getter=lambda: {},
        obter_contexto_paginas=lambda: "",
        resumo_mente_integrada=lambda _texto: "",
        log=lambda *_args: None,
    )
    requisicao = preparador.preparar(PedidoModelo.criar(
        [
            {"role": "system", "content": BASE_SYSTEM_PROMPT_RAPIDO},
            {"role": "system", "content": evento},
        ],
        max_tokens=180,
        modo_rapido=True,
        permitir_conversa_modo_jogo=True,
        tipo_chamada="presenca_evento",
    ))
    payload = requisicao.payload

    assert any(
        evento in str(item.get("content") or "")
        for item in payload["messages"]
    )
    mensagens_remotas = _mensagens_minimas(payload)
    assert mensagens_remotas[-1]["role"] == "user"
    assert "SOLICITAÇÃO TÉCNICA INTERNA" in mensagens_remotas[-1]["content"]


def test_preparador_nao_preserva_system_solto_em_conversa_comum() -> None:
    contexto_antigo = "CONTEXTO SYSTEM ANTIGO QUE NÃO PERTENCE AO TURNO"
    preparador = PreparadorRequisicaoLLMRuntime(
        model="Qwen3:4b-instruct",
        endpoint_local_getter=lambda: True,
        resumo_do_dia_getter=lambda: "",
        data_atual_getter=lambda: "",
        normalizar_texto=lambda texto: texto,
        mapear_pastas=lambda: "",
        contexto_logs_getter=lambda: (),
        contexto_navegador_relevante=lambda _texto: False,
        contexto_sistema_getter=lambda: {},
        obter_contexto_paginas=lambda: "",
        resumo_mente_integrada=lambda _texto: "",
        log=lambda *_args: None,
    )

    requisicao = preparador.preparar(PedidoModelo.criar(
        [
            {"role": "system", "content": BASE_SYSTEM_PROMPT_RAPIDO},
            {"role": "user", "content": "oi"},
            {"role": "assistant", "content": "oi, Pedro"},
            {"role": "system", "content": contexto_antigo},
        ],
        modo_rapido=True,
        tipo_chamada="conversa",
    ))

    assert all(
        contexto_antigo not in str(item.get("content") or "")
        for item in requisicao.payload["messages"]
    )


def test_conversa_remota_responde_sem_repassar_metadados_internos() -> None:
    chamadas = []
    logs = []

    def postar(url, **kwargs):
        chamadas.append((url, kwargs))
        return _Resposta()

    runtime = ConversaJogoRemotaRuntime(
        api_key="segredo",
        model="modelo-textual",
        requests_post=postar,
        log=logs.append,
    )
    resposta = runtime.enviar({
        "messages": [
            {"role": "system", "content": "Você é a Laylay."},
            {"role": "user", "content": "tudo bem com você?"},
        ],
        "max_tokens": 120,
        "_laylay_conversa_modo_jogo": True,
    })

    assert resposta == "Tô bem. E você?"
    assert chamadas[0][0].endswith("/chat/completions")
    enviado = chamadas[0][1]["json"]
    assert enviado["model"] == "modelo-textual"
    assert enviado["max_completion_tokens"] == 120
    assert "_laylay_conversa_modo_jogo" not in enviado
    assert any("resposta remota" in item for item in logs)


def test_falha_remota_abre_circuito_e_nao_cria_fila() -> None:
    chamadas = []
    agora = [10.0]

    def postar(*_args, **_kwargs):
        chamadas.append(True)
        raise TimeoutError("ocupado")

    runtime = ConversaJogoRemotaRuntime(
        api_key="segredo",
        model="modelo-textual",
        requests_post=postar,
        clock=lambda: agora[0],
        cooldown_s=30,
        log=lambda *_args: None,
    )
    payload = {"messages": [{"role": "user", "content": "oi"}]}

    assert runtime.enviar(payload) == ""
    assert runtime.enviar(payload) == ""
    assert chamadas == [True]

    agora[0] = 41.0
    assert runtime.enviar(payload) == ""
    assert chamadas == [True, True]


def test_sem_credencial_nao_tenta_requisicao() -> None:
    runtime = ConversaJogoRemotaRuntime(
        api_key="",
        model="modelo-textual",
        requests_post=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError()),
    )
    assert runtime.enviar({"messages": [{"role": "user", "content": "oi"}]}) == ""
