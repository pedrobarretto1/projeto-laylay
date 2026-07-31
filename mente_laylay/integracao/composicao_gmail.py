"""Composição da integração Gmail sem expor credenciais no ponto de entrada."""

from __future__ import annotations

import os
from typing import Any, Callable, Iterable

from mente_laylay.integracao.gmail_mental import (
    DEFAULT_GMAIL_PALAVRAS_URGENTES,
    DEFAULT_GMAIL_PRIORITARIOS,
    criar_gmail_runtime,
)


class ComposicaoGmailLaylayRuntime:
    def __init__(
        self,
        *,
        arquivo_estado: str,
        continuidades_set: Callable[[str, object], None],
        agendar_fala_proativa: Callable[[str, str, str, int], None],
        is_speaking_getter: Callable[[], bool],
        modo_jogo_getter: Callable[[], bool],
        centralizar_notificacoes_cb: Callable[[Iterable[dict]], object] | None = None,
        stop_event: Any,
        registrar_falha: Callable[..., Any] | None = None,
        env_getter: Callable[[str, str], str] = os.getenv,
        prioritarios: Iterable[str] = DEFAULT_GMAIL_PRIORITARIOS,
        palavras_urgentes: Iterable[str] = DEFAULT_GMAIL_PALAVRAS_URGENTES,
        gmail_factory: Callable[..., Any] = criar_gmail_runtime,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.env_getter = env_getter
        self.registrar_falha = registrar_falha
        self.log = log
        intervalo = self._inteiro_env("GMAIL_INTERVALO_S", 300, minimo=15, maximo=86400)
        max_lidos = self._inteiro_env("GMAIL_MAX_LIDOS", 5, minimo=1, maximo=50)
        self.runtime = gmail_factory(
            arquivo_estado=arquivo_estado,
            usuario=str(env_getter("GMAIL_USER", "") or "").strip(),
            app_password=str(env_getter("GMAIL_APP_PASSWORD", "") or "").strip(),
            intervalo_s=intervalo,
            max_lidos=max_lidos,
            prioritarios=list(prioritarios),
            palavras_urgentes=list(palavras_urgentes),
            continuidades_set=continuidades_set,
            agendar_fala_proativa=agendar_fala_proativa,
            is_speaking_getter=is_speaking_getter,
            modo_jogo_getter=modo_jogo_getter,
            centralizar_notificacoes_cb=centralizar_notificacoes_cb,
            registrar_falha=registrar_falha,
            log=log,
            stop_event=stop_event,
        )

    def _relatar(self, codigo: str, erro: BaseException) -> None:
        if callable(self.registrar_falha):
            self.registrar_falha("composicao_gmail", codigo, erro=erro)

    def _inteiro_env(self, nome: str, padrao: int, *, minimo: int, maximo: int) -> int:
        bruto = self.env_getter(nome, str(padrao))
        try:
            valor = int(str(bruto or padrao).strip())
            if not minimo <= valor <= maximo:
                raise ValueError("fora do intervalo")
            return valor
        except (TypeError, ValueError) as erro:
            self.log(f"⚠️ [GMAIL] {nome} inválida; usando {padrao}.")
            self._relatar(f"configuracao_{nome.casefold()}", erro)
            return int(padrao)

    @property
    def nao_lidos_cache(self) -> list:
        return self.runtime.nao_lidos_cache

    def silenciar_remetente(self, remetente: str) -> bool:
        return bool(self.runtime.silenciar_remetente(remetente))

    def configurado(self) -> bool:
        return bool(self.runtime.configurado())

    def buscar_nao_lidos(self) -> list:
        return self.runtime.buscar_nao_lidos()

    def falar_resumo_estiloso(self, *args: Any, **kwargs: Any) -> Any:
        return self.runtime.falar_resumo_estiloso(*args, **kwargs)

    def daemon(self) -> None:
        self.runtime.daemon()

    def encerrar(self) -> None:
        self.runtime.encerrar()


def criar_composicao_gmail_laylay_runtime(**kwargs: Any) -> ComposicaoGmailLaylayRuntime:
    return ComposicaoGmailLaylayRuntime(**kwargs)
