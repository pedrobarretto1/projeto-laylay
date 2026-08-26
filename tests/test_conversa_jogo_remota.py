from __future__ import annotations

from mente_laylay.integracao.conversa_jogo_remota import (
    ConversaJogoRemotaRuntime,
    _mensagens_minimas,
)


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
