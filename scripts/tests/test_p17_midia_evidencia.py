from __future__ import annotations

from typing import Any

from mente_laylay.autonomia.controle_midia import executar_media_control
from mente_laylay.autonomia.executor_musical import (
    DependenciasExecutorMusical,
    executar_intencao_musical,
)
from mente_laylay.cognicao.refinamento_pesquisa import refinar_consulta_musical
from mente_laylay.integracao.chrome_comandos import ChromeComandosRuntime
from mente_laylay.integracao.navegador_runtime import NavegadorOperacoesRuntime
from mente_laylay.memoria_mental.busca_musical_runtime import BuscaMusicalRuntime
from tests.fakes_navegador import NavegadorLeituraFake


def _deps(
    eventos: list[tuple[str, dict[str, Any]]],
    abrir,
    falas: list[tuple] | None = None,
) -> DependenciasExecutorMusical:
    falas = falas if falas is not None else []
    return DependenciasExecutorMusical(
        marcar_resultado=lambda status, **kwargs: eventos.append((status, kwargs)),
        abrir_url_musical=abrir,
        falar_por_status=lambda status, fala, **kwargs: falas.append(
            (status, fala, kwargs)
        ),
    )


def test_pedido_de_trabalho_percorre_refinamento_selecao_execucao_e_fala() -> None:
    eventos: list[tuple[str, dict[str, Any]]] = []
    falas: list[tuple] = []
    consultas: list[tuple[str, str]] = []
    params: dict[str, Any] = {
        "query": "musica boa para trabalhar programando",
        "atividade": "programando",
    }

    def resolver_video(consulta: str, *, tipo_resultado: str) -> dict[str, str]:
        consultas.append((consulta, tipo_resultado))
        return {
            "url": "https://www.youtube.com/watch?v=tychoawake1",
            "title": "Tycho - Awake (Official Audio)",
            "channel": "Tycho",
        }

    resultado = executar_intencao_musical(
        "MUSIC_SEARCH",
        params,
        "coloca uma música boa para trabalhar programando",
        {
            "_autonomia_permite_execucao_musical": lambda *_a, **_k: True,
            "_normalizar_query_musical": lambda texto: texto,
            "_resolver_query_musical_por_estilo": refinar_consulta_musical,
            "_resolver_primeiro_video_youtube": resolver_video,
        },
        _deps(
            eventos,
            lambda *_a, **_k: {
                "ok": True,
                "confirmado": True,
                "status": "playing_confirmed",
            },
            falas,
        ),
    )

    assert resultado.retorno is True
    assert consultas == [("Tycho - Awake official audio", "faixa")]
    assert params["consulta_pedida"] == "musica boa para trabalhar programando"
    assert params["consulta_resolvida"] == "Tycho - Awake official audio"
    assert params["alvo_executado"] == "Tycho - Awake (Official Audio)"
    assert params["alvo_apresentado"] == "Tycho - Awake"
    assert eventos == [(
        "musica_reproduzindo",
        {"executou": True, "confirmado": True, "detalhe": "playing_confirmed"},
    )]
    assert falas[0][2]["alvo"] == "Tycho - Awake"


def test_pesquisa_sem_video_concreto_nao_abre_pagina_de_resultados() -> None:
    eventos: list[tuple[str, dict[str, Any]]] = []
    aberturas: list[tuple] = []
    params: dict[str, Any] = {"query": "uma faixa impossível"}

    def registrar_abertura(*args: Any, **kwargs: Any) -> bool:
        aberturas.append((args, kwargs))
        return True

    resultado = executar_intencao_musical(
        "MUSIC_SEARCH",
        params,
        "toca uma faixa impossível",
        {
            "_autonomia_permite_execucao_musical": lambda *_a, **_k: True,
            "_normalizar_query_musical": lambda texto: texto,
            "_resolver_primeiro_video_youtube": lambda *_a, **_k: {},
        },
        _deps(
            eventos,
            registrar_abertura,
        ),
    )

    assert resultado.retorno is False
    assert aberturas == []
    assert params["alvo_executado"] == ""
    assert eventos == [(
        "musica_nao_resolvida",
        {
            "executou": False,
            "confirmado": False,
            "detalhe": "nenhum_video_reproduzivel",
        },
    )]


def test_runtime_de_busca_preserva_identidade_do_video_resolvido() -> None:
    runtime = BuscaMusicalRuntime(
        extrair_resultados_youtube=lambda *_a, **_k: [{
            "url": "https://www.youtube.com/watch?v=abc12345678",
            "title": "C418 - Sweden",
            "channel": "C418",
            "score": 91,
        }],
        abrir_url=lambda _url: True,
        log=lambda _linha: None,
    )

    resultado = runtime.resolver_primeiro_video("C418 Sweden")

    assert resultado["title"] == "C418 - Sweden"
    assert resultado["channel"] == "C418"
    link = runtime.buscar_primeiro_video("C418 Sweden")
    assert link is not None and link.endswith("abc12345678")


class _ComandosDetalhadosFake:
    def __init__(self, retorno: dict[str, Any]) -> None:
        self.retorno = dict(retorno)
        self.chamadas: list[tuple[str, dict[str, Any]]] = []

    def enviar_detalhado(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.chamadas.append((action, dict(payload)))
        return dict(self.retorno)


def test_navegador_preserva_aba_e_evidencia_do_player() -> None:
    comandos = _ComandosDetalhadosFake({
        "ok": True,
        "confirmado": True,
        "status": "success",
        "evidence": {"paused": True},
        "tab": {"id": 27, "url": "https://youtube.com/watch?v=abc"},
    })
    navegador = NavegadorOperacoesRuntime(
        comandos=comandos,
        ambiente=object(),
    )

    resultado = navegador.controlar_youtube_detalhado("pause", tab_id=27)

    assert resultado["confirmado"] is True
    assert resultado["evidence"] == {"paused": True}
    assert comandos.chamadas == [(
        "youtube_control", {"command": "pause", "target_tab_id": 27},
    )]


def test_timeout_do_player_falha_uma_vez_sem_anunciar_sucesso() -> None:
    falas: list[str] = []
    resultados: list[tuple] = []
    chamadas: list[tuple] = []

    class _Navegador:
        def controlar_youtube_detalhado(self, comando, *, tab_id=None):
            chamadas.append((comando, tab_id))
            return {
                "ok": False,
                "confirmado": False,
                "status": "navigation_timeout",
                "message": "O player não respondeu a tempo",
            }

    ok = executar_media_control(
        {"acao": "play", "platform": "music"},
        "continua a música",
        "local",
        {
            "falar_com_lipsync": lambda fala, *_a: falas.append(fala),
            "_registro_navegador_operacoes_runtime": _Navegador(),
            "_registro_navegador_leitura_runtime": NavegadorLeituraFake(aba={
                "url": "https://youtube.com/watch?v=abc",
                "title": "Faixa - YouTube",
                "tabId": 41,
            }),
        },
        marcar_resultado=lambda status, executou=None, confirmado=None, **kwargs: (
            resultados.append((status, executou, confirmado, kwargs))
        ),
        falar_por_status=lambda *_a, **_k: None,
        ctx_fala=lambda: {},
    )

    assert ok is False
    assert chamadas == [("play", 41)]
    assert resultados == [(
        "falha_execucao", False, False,
        {"detalhe": "O player não respondeu a tempo"},
    )]
    assert falas
    assert "não repeti" in falas[-1].casefold()
    assert "retomei" not in falas[-1].casefold()


def test_chrome_runtime_expoe_resultado_observavel_sem_reinterpretar() -> None:
    ultimo = {
        "requestId": "req-17",
        "action": "youtube_control",
        "ok": True,
        "status": "success",
        "evidence": {"playing": False, "paused": True},
        "tab": {"id": 9, "url": "https://youtube.com/watch?v=abc"},
    }
    runtime = ChromeComandosRuntime(contexto_getter=lambda: {
        "ALLOWED_ACTIONS": {"youtube_control"},
        "connected_extensions": {object()},
        "ws_loop": object(),
        "broadcast_command": lambda _msg: None,
        "executar_chrome_confirmado": lambda _msg, timeout_s: True,
        "ultimo_resultado_chrome": lambda: ultimo,
    })

    resultado = runtime.enviar_detalhado(
        "youtube_control", {"command": "pause", "target_tab_id": 9},
    )

    assert resultado["ok"] is True
    assert resultado["confirmado"] is True
    assert resultado["evidence"] == {"playing": False, "paused": True}
    assert resultado["tab"]["id"] == 9


def test_refinador_cobre_estudo_treino_e_descanso() -> None:
    estudo = refinar_consulta_musical(
        "música para estudar", "coloca uma música para estudar", cursores={},
    )
    treino = refinar_consulta_musical(
        "música para academia", "coloca música para academia", cursores={},
    )
    descanso = refinar_consulta_musical(
        "música para relaxar", "coloca música para relaxar", cursores={},
    )

    assert estudo["contexto"] == "estudo" and estudo["tipo_resultado"] == "faixa"
    assert treino["contexto"] == "academia" and treino["tipo_resultado"] == "faixa"
    assert descanso["contexto"] == "relaxar" and descanso["tipo_resultado"] == "faixa"
