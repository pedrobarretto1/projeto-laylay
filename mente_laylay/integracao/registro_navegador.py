"""Contratos tipados de leitura e operacoes do navegador da Laylay."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PortaNavegadorLeitura(Protocol):
    def conectado(self) -> bool: ...
    def aba_ativa(self, timeout_s: float = 4.0) -> dict[str, Any]: ...
    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]: ...
    def diagnostico(self) -> dict[str, Any]: ...


@runtime_checkable
class PortaNavegadorOperacoes(Protocol):
    def abrir_url(
        self, url: str, *, auto_click: bool = False, permitir_foco: bool = False,
    ) -> bool: ...
    def pesquisar_youtube(self, consulta: str, *, permitir_foco: bool = False) -> bool: ...
    def tocar_youtube(
        self, url: str, *, tab_id: int | None = None, permitir_foco: bool = False,
    ) -> bool: ...
    def tocar_youtube_detalhado(
        self, url: str, *, tab_id: int | None = None, permitir_foco: bool = False,
    ) -> dict[str, Any]: ...
    def controlar_youtube(self, comando: str) -> bool: ...
    def controlar_youtube_detalhado(
        self,
        comando: str,
        *,
        tab_id: int | None = None,
        queue_item_id: str = "",
        queue_index: int | None = None,
    ) -> dict[str, Any]: ...
    def fechar_aba(self, alvo: str) -> bool: ...
    def fechar_aba_atual(self) -> bool: ...
    def fechar_abas(self, ids: list[int]) -> bool: ...
    def focar_aba(self, tab_id: int) -> bool: ...
    def recarregar_url(self, url: str) -> bool: ...
    def fechar_aba_nativa(self, alvo: str = "") -> bool: ...
    def fechar_abas_vazias(self) -> bool: ...
    def abrir_primeiro_resultado(self, consulta: str = "") -> bool: ...
    def clicar(self, seletor: str) -> bool: ...
    def digitar(self, seletor: str, texto: str) -> bool: ...
    def pressionar(self, tecla: str) -> bool: ...
    def diagnostico(self) -> dict[str, Any]: ...


_LEITURAS = ("conectado", "aba_ativa", "listar_abas", "diagnostico")
_OPERACOES = (
    "abrir_url", "pesquisar_youtube", "tocar_youtube",
    "tocar_youtube_detalhado", "controlar_youtube",
    "fechar_aba", "fechar_aba_atual", "fechar_abas", "recarregar_url",
    "fechar_aba_nativa",
    "fechar_abas_vazias", "clicar", "digitar", "pressionar", "diagnostico",
)
_DIAGNOSTICO_LEITURA = {
    "conectado", "leitura_aba_disponivel", "listagem_disponivel",
}
_DIAGNOSTICO_OPERACOES = {
    "comandos_disponiveis", "navegacao_disponivel", "controle_pagina_disponivel",
    "fechamento_nativo_disponivel",
}


def _validar(servico: Any, operacoes: tuple[str, ...], dominio: str) -> None:
    ausentes = tuple(
        nome for nome in operacoes if not callable(getattr(servico, nome, None))
    )
    if ausentes:
        raise RuntimeError(
            f"servico de {dominio} do navegador invalido na composicao; "
            "operacoes ausentes: " + ", ".join(ausentes)
        )


@dataclass(frozen=True)
class RegistroNavegadorLeitura:
    """Publica percepcao do navegador sem conceder autorizacao de acao."""

    servico: PortaNavegadorLeitura = field(repr=False)

    @classmethod
    def criar(cls, servico: Any) -> "RegistroNavegadorLeitura":
        _validar(servico, _LEITURAS, "leitura")
        return cls(servico=servico)

    def conectado(self) -> bool:
        return bool(self.servico.conectado())

    def aba_ativa(self, timeout_s: float = 4.0) -> dict[str, Any]:
        bruto = dict(self.servico.aba_ativa(timeout_s=timeout_s) or {})
        return {
            "url": str(bruto.get("url") or "").strip(),
            "title": str(bruto.get("title") or bruto.get("titulo") or "").strip(),
            "canal": str(bruto.get("canal") or "").strip(),
            "tabId": bruto.get("tabId") if isinstance(bruto.get("tabId"), int) else None,
        }

    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        abas = self.servico.listar_abas(timeout_s=timeout_s) or []
        return [dict(aba) for aba in abas if isinstance(aba, dict)]

    def diagnostico(self) -> dict[str, Any]:
        bruto = dict(self.servico.diagnostico() or {})
        return {
            chave: bruto[chave]
            for chave in _DIAGNOSTICO_LEITURA
            if chave in bruto
        }


@dataclass(frozen=True)
class RegistroNavegadorOperacoes:
    """Expõe somente operacoes nomeadas; JavaScript arbitrario nao faz parte da porta."""

    servico: PortaNavegadorOperacoes = field(repr=False)

    @classmethod
    def criar(cls, servico: Any) -> "RegistroNavegadorOperacoes":
        _validar(servico, _OPERACOES, "operacoes")
        return cls(servico=servico)

    def abrir_url(self, url: str, *, auto_click: bool = False, permitir_foco: bool = False) -> bool:
        return bool(self.servico.abrir_url(
            url, auto_click=auto_click, permitir_foco=permitir_foco,
        ))

    def pesquisar_youtube(self, consulta: str, *, permitir_foco: bool = False) -> bool:
        return bool(self.servico.pesquisar_youtube(
            consulta, permitir_foco=permitir_foco,
        ))

    def tocar_youtube(
        self, url: str, *, tab_id: int | None = None, permitir_foco: bool = False,
    ) -> bool:
        return bool(self.servico.tocar_youtube(
            url, tab_id=tab_id, permitir_foco=permitir_foco,
        ))

    def tocar_youtube_detalhado(
        self, url: str, *, tab_id: int | None = None, permitir_foco: bool = False,
    ) -> dict[str, Any]:
        retorno = self.servico.tocar_youtube_detalhado(
            url, tab_id=tab_id, permitir_foco=permitir_foco,
        )
        return dict(retorno or {})

    def controlar_youtube(self, comando: str) -> bool:
        return bool(self.servico.controlar_youtube(comando))

    def controlar_youtube_detalhado(
        self,
        comando: str,
        *,
        tab_id: int | None = None,
        queue_item_id: str = "",
        queue_index: int | None = None,
    ) -> dict[str, Any]:
        detalhado = getattr(self.servico, "controlar_youtube_detalhado", None)
        if callable(detalhado):
            try:
                retorno = detalhado(
                    comando,
                    tab_id=tab_id,
                    queue_item_id=queue_item_id,
                    queue_index=queue_index,
                )
            except TypeError:
                if queue_item_id or queue_index is not None:
                    return {
                        "ok": False, "confirmado": False,
                        "status": "queue_select_unsupported",
                    }
                retorno = detalhado(comando, tab_id=tab_id)
            return dict(retorno or {})
        if queue_item_id or queue_index is not None:
            return {
                "ok": False, "confirmado": False,
                "status": "queue_select_unsupported",
            }
        ok = bool(self.servico.controlar_youtube(comando))
        return {
            "ok": ok, "confirmado": True if ok else False,
            "status": "success" if ok else "falha_execucao",
        }

    def fechar_aba(self, alvo: str) -> bool:
        return bool(self.servico.fechar_aba(alvo))

    def fechar_aba_atual(self) -> bool:
        return bool(self.servico.fechar_aba_atual())

    def fechar_abas(self, ids: list[int]) -> bool:
        return bool(self.servico.fechar_abas(ids))

    def focar_aba(self, tab_id: int) -> bool:
        focar = getattr(self.servico, "focar_aba", None)
        return bool(
            isinstance(tab_id, int)
            and not isinstance(tab_id, bool)
            and callable(focar)
            and focar(tab_id)
        )

    def recarregar_url(self, url: str) -> bool:
        return bool(self.servico.recarregar_url(url))

    def fechar_aba_nativa(self, alvo: str = "") -> bool:
        return bool(self.servico.fechar_aba_nativa(alvo))

    def fechar_abas_vazias(self) -> bool:
        return bool(self.servico.fechar_abas_vazias())

    def abrir_primeiro_resultado(self, consulta: str = "") -> bool:
        abrir = getattr(self.servico, "abrir_primeiro_resultado", None)
        return bool(callable(abrir) and abrir(str(consulta or "").strip()))

    def clicar(self, seletor: str) -> bool:
        return bool(self.servico.clicar(seletor))

    def digitar(self, seletor: str, texto: str) -> bool:
        return bool(self.servico.digitar(seletor, texto))

    def pressionar(self, tecla: str) -> bool:
        return bool(self.servico.pressionar(tecla))

    def diagnostico(self) -> dict[str, Any]:
        bruto = dict(self.servico.diagnostico() or {})
        return {
            chave: bruto[chave]
            for chave in _DIAGNOSTICO_OPERACOES
            if chave in bruto
        }


def registrar_navegador_leitura(servico: Any) -> RegistroNavegadorLeitura:
    if isinstance(servico, RegistroNavegadorLeitura):
        return servico
    return RegistroNavegadorLeitura.criar(servico)


def registrar_navegador_operacoes(servico: Any) -> RegistroNavegadorOperacoes:
    if isinstance(servico, RegistroNavegadorOperacoes):
        return servico
    return RegistroNavegadorOperacoes.criar(servico)
