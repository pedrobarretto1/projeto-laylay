"""Contratos tipados para percepção e análise da visão de jogo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class PortaVisaoJogoLeitura(Protocol):
    """Estado perceptivo; observar não concede autorização para analisar."""

    def em_andamento(self) -> bool: ...
    def tem_analise_recente(self, max_idade_s: float = 900.0) -> bool: ...
    def observar_texto_usuario(self, texto: str) -> dict[str, Any]: ...
    def perfil_atual(self) -> dict[str, Any]: ...
    def diagnostico(self) -> dict[str, Any]: ...


@runtime_checkable
class PortaVisaoJogoAnalise(Protocol):
    """Solicitações nomeadas de análise; não expõe captura nem modelo bruto."""

    def executar(self, params: Mapping[str, Any] | None) -> bool: ...
    def aplicar_referencia_item(self, texto: str) -> bool: ...
    def continuar_analise_recente(self, texto: str) -> bool: ...
    def continuar_pendencia(
        self, texto: str, pendencia: Mapping[str, Any] | None,
    ) -> bool: ...
    def processar_atualizacao_perfil(self, texto: str) -> bool: ...
    def diagnostico(self) -> dict[str, Any]: ...


_LEITURAS = (
    "em_andamento", "tem_analise_recente", "observar_texto_usuario",
    "perfil_atual", "diagnostico",
)
_ANALISES = (
    "executar", "aplicar_referencia_item", "continuar_analise_recente",
    "continuar_pendencia", "processar_atualizacao_perfil", "diagnostico",
)
_DIAGNOSTICO_LEITURA = {
    "habilitado", "credencial_disponivel", "em_andamento",
    "analise_recente", "contexto_jogo_ativo", "captura_persistida",
    "imagem_exposta", "autoriza_execucao",
}
_DIAGNOSTICO_ANALISE = {
    "analise_disponivel", "continuidade_disponivel", "solicitacoes",
    "aceitas", "recusadas", "falhas", "captura_exposta",
    "prompt_exposto", "autoriza_execucao",
}


def _validar(servico: Any, operacoes: tuple[str, ...], dominio: str) -> None:
    ausentes = tuple(
        nome for nome in operacoes if not callable(getattr(servico, nome, None))
    )
    if ausentes:
        raise RuntimeError(
            f"serviço de {dominio} da visão de jogo inválido na composição; "
            "operações ausentes: " + ", ".join(ausentes)
        )


@dataclass(frozen=True)
class RegistroVisaoJogoLeitura:
    servico: PortaVisaoJogoLeitura = field(repr=False)

    @classmethod
    def criar(cls, servico: Any) -> "RegistroVisaoJogoLeitura":
        _validar(servico, _LEITURAS, "leitura")
        return cls(servico=servico)

    def em_andamento(self) -> bool:
        return bool(self.servico.em_andamento())

    def tem_analise_recente(self, max_idade_s: float = 900.0) -> bool:
        return bool(self.servico.tem_analise_recente(max_idade_s=max_idade_s))

    def observar_texto_usuario(self, texto: str) -> dict[str, Any]:
        return dict(self.servico.observar_texto_usuario(texto) or {})

    def perfil_atual(self) -> dict[str, Any]:
        return dict(self.servico.perfil_atual() or {})

    def diagnostico(self) -> dict[str, Any]:
        bruto = dict(self.servico.diagnostico() or {})
        return {chave: bruto[chave] for chave in _DIAGNOSTICO_LEITURA if chave in bruto}


@dataclass(frozen=True)
class RegistroVisaoJogoAnalise:
    servico: PortaVisaoJogoAnalise = field(repr=False)

    @classmethod
    def criar(cls, servico: Any) -> "RegistroVisaoJogoAnalise":
        _validar(servico, _ANALISES, "análise")
        return cls(servico=servico)

    def executar(self, params: Mapping[str, Any] | None) -> bool:
        return bool(self.servico.executar(params))

    def aplicar_referencia_item(self, texto: str) -> bool:
        return bool(self.servico.aplicar_referencia_item(texto))

    def continuar_analise_recente(self, texto: str) -> bool:
        return bool(self.servico.continuar_analise_recente(texto))

    def continuar_pendencia(
        self, texto: str, pendencia: Mapping[str, Any] | None,
    ) -> bool:
        return bool(self.servico.continuar_pendencia(texto, pendencia))

    def processar_atualizacao_perfil(self, texto: str) -> bool:
        return bool(self.servico.processar_atualizacao_perfil(texto))

    def diagnostico(self) -> dict[str, Any]:
        bruto = dict(self.servico.diagnostico() or {})
        return {chave: bruto[chave] for chave in _DIAGNOSTICO_ANALISE if chave in bruto}


def registrar_visao_jogo_leitura(servico: Any) -> RegistroVisaoJogoLeitura:
    if isinstance(servico, RegistroVisaoJogoLeitura):
        return servico
    return RegistroVisaoJogoLeitura.criar(servico)


def registrar_visao_jogo_analise(servico: Any) -> RegistroVisaoJogoAnalise:
    if isinstance(servico, RegistroVisaoJogoAnalise):
        return servico
    return RegistroVisaoJogoAnalise.criar(servico)
