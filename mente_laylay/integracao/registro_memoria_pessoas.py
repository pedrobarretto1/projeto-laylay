"""Contrato tipado para a memória de pessoas da aplicação.

Este é o primeiro domínio retirado do namespace genérico. O registro valida a
capacidade na composição e expõe somente as operações públicas necessárias;
detalhes de persistência e configuração permanecem privados no runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PortaMemoriaPessoas(Protocol):
    """Operações que os consumidores podem usar sem conhecer a implementação."""

    def processar(self, texto: str) -> bool: ...

    def contexto_para_prompt(self, texto: str) -> str: ...

    def diagnostico(self) -> dict[str, Any]: ...

    def retrato_para_mente(self, texto: str = "") -> dict[str, Any]: ...

    def reexecutar(self, resultado: dict[str, Any], texto: str) -> bool: ...


_OPERACOES_OBRIGATORIAS = (
    "processar",
    "contexto_para_prompt",
    "diagnostico",
    "retrato_para_mente",
    "reexecutar",
)


@dataclass(frozen=True)
class RegistroMemoriaPessoas:
    """Referência validada e segura ao serviço de memória de pessoas."""

    servico: PortaMemoriaPessoas = field(repr=False)

    @classmethod
    def criar(cls, servico: Any) -> "RegistroMemoriaPessoas":
        ausentes = tuple(
            nome for nome in _OPERACOES_OBRIGATORIAS
            if not callable(getattr(servico, nome, None))
        )
        if ausentes:
            lista = ", ".join(ausentes)
            raise RuntimeError(
                "memória de pessoas inválida na composição; "
                f"operações ausentes: {lista}"
            )
        return cls(servico=servico)

    def processar(self, texto: str) -> bool:
        return bool(self.servico.processar(texto))

    def contexto_para_prompt(self, texto: str) -> str:
        return str(self.servico.contexto_para_prompt(texto) or "")

    def diagnostico(self) -> dict[str, Any]:
        return dict(self.servico.diagnostico() or {})

    def retrato_para_mente(self, texto: str = "") -> dict[str, Any]:
        return dict(self.servico.retrato_para_mente(texto) or {})

    def reexecutar(self, resultado: dict[str, Any], texto: str) -> bool:
        return bool(self.servico.reexecutar(resultado, texto))


def registrar_memoria_pessoas(servico: Any) -> RegistroMemoriaPessoas:
    """Cria o registro ou devolve o registro já validado."""
    if isinstance(servico, RegistroMemoriaPessoas):
        return servico
    return RegistroMemoriaPessoas.criar(servico)
