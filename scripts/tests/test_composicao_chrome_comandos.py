from __future__ import annotations

import asyncio

import pytest

from mente_laylay.integracao.composicao_chrome_comandos import (
    ComposicaoChromeComandosLaylayRuntime,
)


class _TransporteFake:
    def __init__(self):
        self.extensions = {"extensao"}
        self.loop = object()

    def obter_loop(self):
        return self.loop

    def obter_extensoes(self):
        return self.extensions


class _SolicitacoesFake:
    def __init__(self):
        self.ultimo_resultado_comando = {"status": "ok"}

    def enviar_confirmado(self, *_args, **_kwargs):
        return True

    def executar_confirmado(self, *_args, **_kwargs):
        return True

    def solicitar_aba_ativa(self, *_args, **_kwargs):
        return {"tabId": 1}

    def solicitar_tab_reciclagem(self, *_args, **_kwargs):
        return None


def test_composicao_chrome_compartilha_transporte_e_contexto_dinamico() -> None:
    criacoes, broadcasts = {}, []
    transporte = _TransporteFake()
    solicitacoes = _SolicitacoesFake()
    executor = object()

    def solicitacoes_factory(**kwargs):
        criacoes["solicitacoes"] = kwargs
        return solicitacoes

    async def broadcast_fn(ctx, mensagem):
        broadcasts.append((ctx, mensagem))
        return 1

    def executor_factory(**kwargs):
        criacoes["executor"] = kwargs
        return executor

    runtime = ComposicaoChromeComandosLaylayRuntime(
        ws_transport=transporte,
        solicitacoes_factory=solicitacoes_factory,
        broadcast_fn=broadcast_fn,
        log=lambda *_: None,
    )
    criado = runtime.conectar_executor(
        allowed_actions={"open_url"},
        formatar_url_ou_busca=lambda texto, **_kwargs: texto,
        is_valid_url=lambda _url: True,
        atualizar_contexto_por_url=lambda *_: None,
        atualizar_contexto=lambda *_: None,
        buscar_primeiro_video_youtube=lambda *_: None,
        modo_jogo_ativo=lambda: False,
        executor_factory=executor_factory,
    )

    assert criado is executor
    assert runtime.executor is executor
    contexto = criacoes["executor"]["contexto_getter"]()
    assert contexto["ws_loop"] is transporte.loop
    assert contexto["connected_extensions"] is transporte.extensions
    assert contexto["enviar_chrome_confirmado"] == solicitacoes.enviar_confirmado
    assert contexto["solicitar_tab_reciclagem"] == solicitacoes.solicitar_tab_reciclagem
    assert contexto["ultimo_resultado_chrome"]() == {"status": "ok"}

    assert asyncio.run(runtime.broadcast_command("mensagem")) == 1
    assert broadcasts == [(
        {"connected_extensions": transporte.extensions}, "mensagem",
    )]


def test_composicao_chrome_cria_solicitacoes_antes_do_executor() -> None:
    transporte = _TransporteFake()
    capturado = {}
    solicitacoes = _SolicitacoesFake()

    runtime = ComposicaoChromeComandosLaylayRuntime(
        ws_transport=transporte,
        solicitacoes_factory=lambda **kwargs: capturado.update(kwargs) or solicitacoes,
        broadcast_fn=lambda *_args: None,
        log=lambda *_: None,
    )

    assert capturado["obter_loop"] == transporte.obter_loop
    assert capturado["obter_extensoes"] == transporte.obter_extensoes
    assert capturado["transmitir"] == runtime.broadcast_command
    with pytest.raises(RuntimeError, match="ainda não conectado"):
        _ = runtime.executor
