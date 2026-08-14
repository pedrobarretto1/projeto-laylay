"""Contrato tipado das mutações locais de arquivos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PortaArquivosMutacao(Protocol):
    def resolver_caminho(self, valor: str) -> str: ...
    def criar_pasta(self, caminho: str) -> bool: ...
    def criar_arquivo(self, caminho: str, conteudo: str, modo: str = "w") -> bool: ...
    def escrever_texto_seguro(
        self, caminho: str, conteudo: str, *, sobrescrever: bool = False,
    ) -> dict[str, Any]: ...
    def mover_item(self, origem: str, destino: str) -> bool: ...
    def transacionar(self, params: dict[str, Any]) -> Any: ...
    def buscar_itens(self, alvo: str) -> list[str]: ...
    def solicitar_exclusao(self, caminho: str) -> Any: ...
    def confirmar_exclusao(self) -> Any: ...
    def cancelar_exclusao(self) -> None: ...
    def restaurar_ultimo(self, caminho_esperado: str = "") -> Any: ...
    def diagnostico(self) -> dict[str, Any]: ...


_OPERACOES_OBRIGATORIAS = (
    "resolver_caminho", "criar_pasta", "criar_arquivo",
    "escrever_texto_seguro", "mover_item", "transacionar", "buscar_itens",
    "solicitar_exclusao", "confirmar_exclusao", "cancelar_exclusao",
    "restaurar_ultimo", "diagnostico",
)
_CAMPOS_DIAGNOSTICO = {
    "somente_raizes_autorizadas", "escrita_segura_disponivel",
    "lixeira_reversivel", "confirmacao_exclusao_pendente",
}


@dataclass(frozen=True)
class RegistroArquivosMutacao:
    """Expõe mutações verificadas sem publicar callbacks no namespace geral."""

    servico: PortaArquivosMutacao = field(repr=False)

    @classmethod
    def criar(cls, servico: Any) -> "RegistroArquivosMutacao":
        ausentes = tuple(
            nome for nome in _OPERACOES_OBRIGATORIAS
            if not callable(getattr(servico, nome, None))
        )
        if ausentes:
            raise RuntimeError(
                "serviço de mutação de arquivos inválido na composição; "
                "operações ausentes: " + ", ".join(ausentes)
            )
        return cls(servico=servico)

    def resolver_caminho(self, valor: str) -> str:
        return str(self.servico.resolver_caminho(valor) or "")

    def criar_pasta(self, caminho: str) -> bool:
        return bool(self.servico.criar_pasta(caminho))

    def criar_arquivo(self, caminho: str, conteudo: str, modo: str = "w") -> bool:
        return bool(self.servico.criar_arquivo(caminho, conteudo, modo))

    def escrever_texto_seguro(
        self, caminho: str, conteudo: str, *, sobrescrever: bool = False,
    ) -> dict[str, Any]:
        retorno = dict(self.servico.escrever_texto_seguro(
            caminho, conteudo, sobrescrever=sobrescrever,
        ) or {})
        retorno.pop("conteudo", None)
        retorno.pop("conteudo_anterior", None)
        return retorno

    def mover_item(self, origem: str, destino: str) -> bool:
        return bool(self.servico.mover_item(origem, destino))

    def transacionar(self, params: dict[str, Any]) -> Any:
        return self.servico.transacionar(dict(params or {}))

    def buscar_itens(self, alvo: str) -> list[str]:
        return list(self.servico.buscar_itens(alvo) or ())

    def solicitar_exclusao(self, caminho: str) -> Any:
        return self.servico.solicitar_exclusao(caminho)

    def confirmar_exclusao(self) -> Any:
        return self.servico.confirmar_exclusao()

    def cancelar_exclusao(self) -> None:
        self.servico.cancelar_exclusao()

    def restaurar_ultimo(self, caminho_esperado: str = "") -> Any:
        if caminho_esperado:
            return self.servico.restaurar_ultimo(caminho_esperado)
        return self.servico.restaurar_ultimo()

    def diagnostico(self) -> dict[str, Any]:
        bruto = dict(self.servico.diagnostico() or {})
        return {chave: bruto[chave] for chave in _CAMPOS_DIAGNOSTICO if chave in bruto}


def registrar_arquivos_mutacao(servico: Any) -> RegistroArquivosMutacao:
    if isinstance(servico, RegistroArquivosMutacao):
        return servico
    return RegistroArquivosMutacao.criar(servico)
