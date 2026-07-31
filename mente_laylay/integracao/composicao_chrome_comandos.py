"""Composição em duas fases das solicitações e comandos da extensão Chrome."""

from __future__ import annotations

from typing import Any, Callable, Iterable

from mente_laylay.integracao.chrome_comandos import criar_chrome_comandos_runtime
from mente_laylay.integracao.chrome_ws_transport import (
    ChromeSolicitacoesRuntime,
    broadcast_command,
)


class ComposicaoChromeComandosLaylayRuntime:
    def __init__(
        self,
        *,
        ws_transport: Any,
        registrar_falha: Callable[..., Any] | None = None,
        solicitacoes_factory: Callable[..., Any] = ChromeSolicitacoesRuntime,
        broadcast_fn: Callable[..., Any] = broadcast_command,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.ws_transport = ws_transport
        self.broadcast_fn = broadcast_fn
        self.log = log
        self.solicitacoes = solicitacoes_factory(
            obter_loop=ws_transport.obter_loop,
            obter_extensoes=ws_transport.obter_extensoes,
            transmitir=self.broadcast_command,
            log=log,
            registrar_falha=registrar_falha,
        )
        self._executor: Any = None

    async def broadcast_command(self, mensagem: str) -> int:
        return int(await self.broadcast_fn(
            {"connected_extensions": self.ws_transport.extensions},
            mensagem,
        ))

    def conectar_executor(
        self,
        *,
        allowed_actions: Iterable[str],
        formatar_url_ou_busca: Callable[..., str],
        is_valid_url: Callable[[str], bool],
        atualizar_contexto_por_url: Callable[..., Any],
        atualizar_contexto: Callable[..., Any],
        buscar_primeiro_video_youtube: Callable[..., Any],
        modo_jogo_ativo: Callable[[], bool],
        executor_factory: Callable[..., Any] = criar_chrome_comandos_runtime,
    ) -> Any:
        if self._executor is not None:
            return self._executor
        solicitacoes = self.solicitacoes
        self._executor = executor_factory(contexto_getter=lambda: {
            "ALLOWED_ACTIONS": set(allowed_actions or ()),
            "connected_extensions": self.ws_transport.extensions,
            "ws_loop": self.ws_transport.obter_loop(),
            "broadcast_command": self.broadcast_command,
            "enviar_chrome_confirmado": solicitacoes.enviar_confirmado,
            "executar_chrome_confirmado": solicitacoes.executar_confirmado,
            "solicitar_aba_ativa": solicitacoes.solicitar_aba_ativa,
            "ultimo_resultado_chrome": lambda: dict(
                solicitacoes.ultimo_resultado_comando,
            ),
            "formatar_url_ou_busca": formatar_url_ou_busca,
            "is_valid_url": is_valid_url,
            "atualizar_contexto_por_url": atualizar_contexto_por_url,
            "atualizar_contexto": atualizar_contexto,
            "_buscar_primeiro_video_youtube": buscar_primeiro_video_youtube,
            "solicitar_tab_reciclagem": solicitacoes.solicitar_tab_reciclagem,
            "modo_jogo_ativo": modo_jogo_ativo,
        })
        return self._executor

    @property
    def executor(self) -> Any:
        if self._executor is None:
            raise RuntimeError("executor Chrome ainda não conectado ao contexto")
        return self._executor


def criar_composicao_chrome_comandos_laylay_runtime(
    **kwargs: Any,
) -> ComposicaoChromeComandosLaylayRuntime:
    return ComposicaoChromeComandosLaylayRuntime(**kwargs)
