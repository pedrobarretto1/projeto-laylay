"""Composição do transporte e dos handlers WebSocket da extensão Chrome."""

from __future__ import annotations

import os
from functools import partial
from typing import Any, Callable, Mapping

from mente_laylay.integracao.chrome_ws_contexto import criar_chrome_ws_contexto_runtime
from mente_laylay.integracao.chrome_ws_contexto import ChromeWsContextoRuntime
from mente_laylay.integracao.chrome_ws_handlers import criar_chrome_ws_eventos_runtime
from mente_laylay.integracao.chrome_ws_server import (
    criar_chrome_ws_runtime,
    run_ws_server_in_thread,
)


class ComposicaoChromeWsLaylayRuntime:
    def __init__(
        self,
        *,
        monitor_saude: Any,
        solicitacoes: Any,
        playlist_state: Any,
        yt_clean_url: Callable[[str], str],
        playlist_avancar_proxima: Callable[[], Any],
        falar_com_lipsync: Callable[..., Any],
        ws_transport: Any,
        fechar_extensoes_anteriores: Callable[..., Any],
        stop_event: Any,
        servicos_iniciais: Mapping[str, Any] | None = None,
        namespace_getter: Callable[[], Mapping[str, Any]] | None = None,
        env_getter: Callable[[str, str], str] = os.getenv,
        contexto_factory: Callable[..., Any] = criar_chrome_ws_contexto_runtime,
        eventos_factory: Callable[..., Any] = criar_chrome_ws_eventos_runtime,
        ws_factory: Callable[..., Any] = criar_chrome_ws_runtime,
        servidor_runner: Callable[..., Any] = run_ws_server_in_thread,
    ) -> None:
        origem = dict(servicos_iniciais or {})
        if not origem and callable(namespace_getter):
            origem = dict(namespace_getter() or {})
        self._servicos = self._filtrar(origem)
        self.ws_transport = ws_transport
        self.env_getter = env_getter
        self.contexto = contexto_factory(
            namespace_getter=self._snapshot_servicos,
            monitor_saude=monitor_saude,
        )
        self.eventos = eventos_factory(
            solicitacoes=solicitacoes,
            playlist_state=playlist_state,
            yt_clean_url=yt_clean_url,
            playlist_avancar_proxima=playlist_avancar_proxima,
            falar_com_lipsync=falar_com_lipsync,
            user_context_getter=self.contexto.contexto_usuario,
            aplicar_user_updates=self.contexto.aplicar_updates_usuario,
            action_context_getter=self.contexto.contexto_acao,
            aplicar_action_updates=self.contexto.aplicar_updates_acao,
        )
        self.ws = ws_factory(contexto_getter=self._contexto_conexao)
        self.handler = self.ws.handler
        host = str(env_getter("LAYLAY_WS_HOST", "0.0.0.0") or "").strip() or "0.0.0.0"
        self.executar_servidor = partial(
            servidor_runner,
            self.handler,
            set_loop=ws_transport.definir_loop,
            host=host,
            stop_event=stop_event,
        )
        self.fechar_extensoes_anteriores = fechar_extensoes_anteriores

    @staticmethod
    def _filtrar(servicos: Mapping[str, Any]) -> dict[str, Any]:
        return {
            nome: servicos[nome]
            for nome in ChromeWsContextoRuntime.DEPENDENCIAS_COMPLETAS
            if nome in servicos
        }

    def _snapshot_servicos(self) -> dict[str, Any]:
        return dict(self._servicos)

    def conectar_servicos(self, servicos: Mapping[str, Any]) -> None:
        self._servicos = self._filtrar(servicos)

    @property
    def servicos_registrados(self) -> tuple[str, ...]:
        return tuple(sorted(self._servicos))

    def _contexto_conexao(self) -> dict[str, Any]:
        return {
            **dict(self.ws_transport.contexto_conexoes() or {}),
            "token_pc_b": str(self.env_getter("LAYLAY_PC_B_TOKEN", "") or "").strip(),
            "_ws_close_other_extensions": self.fechar_extensoes_anteriores,
            "_ws_dispatch_data": self.eventos.dispatch,
            "_processar_mensagem_pc_b": self.contexto.processar_pc_b,
            "_processar_page_data": self.contexto.processar_pagina,
            "_aplicar_page_updates": self.contexto.aplicar_updates_pagina,
        }

    @property
    def contexto_usuario(self) -> Callable[..., Any]:
        return self.contexto.contexto_usuario

    @property
    def aplicar_updates_usuario(self) -> Callable[..., Any]:
        return self.contexto.aplicar_updates_usuario

    @property
    def contexto_acao(self) -> Callable[..., Any]:
        return self.contexto.contexto_acao

    @property
    def aplicar_updates_acao(self) -> Callable[..., Any]:
        return self.contexto.aplicar_updates_acao

    @property
    def processar_pc_b(self) -> Callable[..., Any]:
        return self.contexto.processar_pc_b

    @property
    def processar_pagina(self) -> Callable[..., Any]:
        return self.contexto.processar_pagina

    @property
    def aplicar_updates_pagina(self) -> Callable[..., Any]:
        return self.contexto.aplicar_updates_pagina


def criar_composicao_chrome_ws_laylay_runtime(
    **kwargs: Any,
) -> ComposicaoChromeWsLaylayRuntime:
    return ComposicaoChromeWsLaylayRuntime(**kwargs)
