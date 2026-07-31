"""Composição do IoT com memória, fala, emoção e resolução segura de cores."""

from __future__ import annotations

from typing import Any, Callable, Dict

from mente_laylay.iot.resolucao_cores import resolver_cor_por_ia
from mente_laylay.iot.runtime import criar_runtime_iot


class ComposicaoIoTLaylayRuntime:
    """Monta a fronteira IoT sem levar detalhes Tuya ao ponto de entrada."""

    def __init__(
        self,
        *,
        memoria_sqlite: Any,
        falar: Callable[[str, str, int], Any],
        estado_mental_getter: Callable[[], Dict[str, Any]],
        definir_emocao: Callable[[str, int, str], Any] | None,
        enviar_mensagem: Callable[..., Any],
        emitir_fala: bool = False,
        modo: str | None = None,
        runtime_factory: Callable[..., Any] = criar_runtime_iot,
        resolver_cor_fn: Callable[..., Any] = resolver_cor_por_ia,
        log: Callable[..., Any] = print,
    ) -> None:
        self._enviar_mensagem = enviar_mensagem
        self._resolver_cor_fn = resolver_cor_fn
        self.log = log

        argumentos = {
            "memoria_sqlite": memoria_sqlite,
            "falar": falar,
            "estado_mental_getter": estado_mental_getter,
            "definir_emocao": definir_emocao,
            "emitir_fala": bool(emitir_fala),
            "resolver_cor": self.resolver_cor,
            "log": log,
        }
        if modo is not None:
            argumentos["modo"] = str(modo)
        self.runtime = runtime_factory(**argumentos)

    def resolver_cor(self, nome: str) -> Any:
        return self._resolver_cor_fn(
            nome,
            enviar_mensagem=self._enviar_mensagem,
            log=self.log,
        )

    def detectar(self, texto: str, estado: Dict[str, Any] | None = None) -> Any:
        return self.runtime.detectar(texto, estado)

    def executar(self, resultado: dict, texto_original: str = "") -> Any:
        return self.runtime.executar(resultado, texto_original)


def criar_composicao_iot_laylay_runtime(**kwargs: Any) -> ComposicaoIoTLaylayRuntime:
    return ComposicaoIoTLaylayRuntime(**kwargs)
