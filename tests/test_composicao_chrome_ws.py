from __future__ import annotations

from mente_laylay.integracao.composicao_chrome_ws import ComposicaoChromeWsLaylayRuntime


class _ContextoFake:
    def contexto_usuario(self):
        return {"usuario": True}

    def aplicar_updates_usuario(self, _dados):
        return None

    def contexto_acao(self):
        return {"acao": True}

    def aplicar_updates_acao(self, _dados):
        return None

    def processar_pc_b(self, _dados):
        return None

    def processar_pagina(self, _dados):
        return {"pagina": True}

    def aplicar_updates_pagina(self, _dados):
        return None


class _EventosFake:
    def dispatch(self, _dados):
        return None


class _WsFake:
    async def handler(self, _websocket):
        return None


class _TransporteFake:
    def __init__(self):
        self.extensions = set()

    def contexto_conexoes(self):
        return {"connected_extensions": self.extensions}

    def definir_loop(self, _loop):
        return None


def test_composicao_chrome_liga_contexto_eventos_e_servidor() -> None:
    criacoes, execucoes = {}, []
    contexto, eventos, ws = _ContextoFake(), _EventosFake(), _WsFake()
    transporte = _TransporteFake()

    def contexto_factory(**kwargs):
        criacoes["contexto"] = kwargs
        return contexto

    def eventos_factory(**kwargs):
        criacoes["eventos"] = kwargs
        return eventos

    def ws_factory(**kwargs):
        criacoes["ws"] = kwargs
        return ws

    def servidor_runner(*args, **kwargs):
        execucoes.append((args, kwargs))

    runtime = ComposicaoChromeWsLaylayRuntime(
        namespace_getter=lambda: {"mente": "viva"},
        monitor_saude=object(),
        solicitacoes=object(),
        playlist_state={},
        yt_clean_url=lambda url: url,
        playlist_avancar_proxima=lambda: None,
        falar_com_lipsync=lambda *_args, **_kwargs: None,
        ws_transport=transporte,
        fechar_extensoes_anteriores=lambda *_args: None,
        stop_event=object(),
        env_getter=lambda nome, padrao="": {
            "LAYLAY_WS_HOST": "127.0.0.1",
            "LAYLAY_PC_B_TOKEN": " token-local ",
        }.get(nome, padrao),
        contexto_factory=contexto_factory,
        eventos_factory=eventos_factory,
        ws_factory=ws_factory,
        servidor_runner=servidor_runner,
    )

    conexao = criacoes["ws"]["contexto_getter"]()
    assert conexao["connected_extensions"] is transporte.extensions
    assert conexao["token_pc_b"] == "token-local"
    assert conexao["_ws_dispatch_data"] == eventos.dispatch
    assert conexao["_processar_mensagem_pc_b"] == contexto.processar_pc_b
    assert criacoes["eventos"]["user_context_getter"] == contexto.contexto_usuario

    runtime.executar_servidor()
    args, kwargs = execucoes[0]
    assert args == (ws.handler,)
    assert kwargs["set_loop"] == transporte.definir_loop
    assert kwargs["host"] == "127.0.0.1"


def test_composicao_chrome_preserva_host_padrao_e_nao_expoe_token() -> None:
    capturado = {}

    runtime = ComposicaoChromeWsLaylayRuntime(
        namespace_getter=dict,
        monitor_saude=None,
        solicitacoes=object(),
        playlist_state={},
        yt_clean_url=lambda url: url,
        playlist_avancar_proxima=lambda: None,
        falar_com_lipsync=lambda *_args: None,
        ws_transport=_TransporteFake(),
        fechar_extensoes_anteriores=lambda *_args: None,
        stop_event=object(),
        env_getter=lambda nome, padrao="": "" if nome == "LAYLAY_WS_HOST" else padrao,
        contexto_factory=lambda **_kwargs: _ContextoFake(),
        eventos_factory=lambda **_kwargs: _EventosFake(),
        ws_factory=lambda **_kwargs: _WsFake(),
        servidor_runner=lambda *args, **kwargs: capturado.update(kwargs),
    )

    runtime.executar_servidor()

    assert capturado["host"] == "0.0.0.0"


def test_composicao_chrome_filtra_e_congela_contexto() -> None:
    capturado = {}
    estado_inicial = object()

    def contexto_factory(**kwargs):
        capturado.update(kwargs)
        return _ContextoFake()

    runtime = ComposicaoChromeWsLaylayRuntime(
        servicos_iniciais={
            "_estado_compartilhado_runtime": estado_inicial,
            "SEGREDO": "não reter",
        },
        monitor_saude=None,
        solicitacoes=object(), playlist_state={},
        yt_clean_url=lambda url: url,
        playlist_avancar_proxima=lambda: None,
        falar_com_lipsync=lambda *_args: None,
        ws_transport=_TransporteFake(),
        fechar_extensoes_anteriores=lambda *_args: None,
        stop_event=object(),
        contexto_factory=contexto_factory,
        eventos_factory=lambda **_kwargs: _EventosFake(),
        ws_factory=lambda **_kwargs: _WsFake(),
    )
    assert capturado["namespace_getter"]() == {
        "_estado_compartilhado_runtime": estado_inicial,
    }

    estado_final = object()
    servicos = {
        "_estado_compartilhado_runtime": estado_final,
        "enviar_mensagem": object(),
        "SEGREDO": "não reter",
    }
    runtime.conectar_servicos(servicos)
    servicos["_estado_compartilhado_runtime"] = object()
    snapshot = capturado["namespace_getter"]()

    assert snapshot["_estado_compartilhado_runtime"] is estado_final
    assert "enviar_mensagem" in runtime.servicos_registrados
    assert "SEGREDO" not in runtime.servicos_registrados
