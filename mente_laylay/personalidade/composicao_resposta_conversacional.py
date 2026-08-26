"""Composição tardia e filtrada da entrega conversacional da Laylay."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from mente_laylay.personalidade.resposta_conversacional_runtime import (
    criar_resposta_conversacional_runtime,
)


DEPENDENCIAS_RESPOSTA_CONVERSACIONAL = (
    "_normalizar_texto_curto",
    "_verificar_fala_do_turno",
    "falar_com_lipsync",
    "_registrar_mente_curta",
    "memoria_inteligente",
    "salvar_memoria",
    "_normalizar_texto_com_apelidos",
    "executar_intencao",
    "_registrar_resultado_execucao",
    "_registrar_autoaprimoramento",
)


class ComposicaoRespostaConversacionalRuntime:
    """Mantém a personalidade disponível antes de ligar integrações tardias."""

    def __init__(
        self,
        *,
        estado_runtime_getter: Callable[[], Any],
        fallback_fala: str,
        log: Callable[..., Any] = print,
        runtime_factory: Callable[..., Any] = criar_resposta_conversacional_runtime,
    ) -> None:
        self._servicos: dict[str, Any] = {}
        self._conectado = False
        self.runtime = runtime_factory(
            namespace_getter=self._snapshot,
            estado_runtime_getter=estado_runtime_getter,
            fallback_fala=fallback_fala,
            log=log,
        )

    def _snapshot(self) -> dict[str, Any]:
        if not self._conectado:
            raise RuntimeError(
                "resposta conversacional ainda não conectada às integrações"
            )
        return dict(self._servicos)

    def conectar(self, *, servicos: Mapping[str, Any]) -> Any:
        if self._conectado:
            return self.runtime
        ausentes = [
            nome for nome in DEPENDENCIAS_RESPOSTA_CONVERSACIONAL
            if nome not in servicos
        ]
        if ausentes:
            raise RuntimeError(
                "serviços ausentes na resposta conversacional: "
                + ", ".join(ausentes)
            )
        self._servicos = {
            nome: servicos[nome]
            for nome in DEPENDENCIAS_RESPOSTA_CONVERSACIONAL
        }
        self._conectado = True
        return self.runtime

    @property
    def conectado(self) -> bool:
        return self._conectado

    @property
    def servicos_registrados(self) -> tuple[str, ...]:
        return tuple(sorted(self._servicos))


def criar_composicao_resposta_conversacional_runtime(
    **kwargs: Any,
) -> ComposicaoRespostaConversacionalRuntime:
    return ComposicaoRespostaConversacionalRuntime(**kwargs)
