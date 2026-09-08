"""Catálogo read-only usado para provar que um alvo pertence ao domínio app."""

from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping

from mente_laylay.percepcao.planejamento_janelas import (
    normalizar_alvo_ambiente,
    variantes_alvo_aplicativo,
)


def _nome_catalogavel(valor: Any) -> str:
    bruto = str(valor or "").strip()
    if not bruto or "://" in bruto or bruto.casefold().endswith(":"):
        return ""
    return normalizar_alvo_ambiente(bruto)


def _variantes_alvo(nome: str) -> tuple[str, ...]:
    return variantes_alvo_aplicativo(nome)


class CatalogoAplicativosRuntime:
    """Mantém nomes conhecidos; não abre, fecha nem autoriza aplicativos."""

    def __init__(
        self,
        *,
        apps_map: Mapping[str, Any] | None,
        nomes_instalados_getter: Callable[[], Iterable[Any]] | None = None,
    ) -> None:
        self._apps_map = dict(apps_map or {})
        self._nomes_instalados_getter = nomes_instalados_getter
        self._nomes: set[str] = set()
        self._falhas_descoberta = 0
        self.atualizar()

    def atualizar(self) -> tuple[str, ...]:
        nomes: set[str] = set()
        for chave, destino in self._apps_map.items():
            for valor in (chave, destino):
                nome = _nome_catalogavel(valor)
                if nome:
                    nomes.update(_variantes_alvo(nome))
        if callable(self._nomes_instalados_getter):
            try:
                descobertos = self._nomes_instalados_getter() or ()
                for valor in descobertos:
                    nome = _nome_catalogavel(valor)
                    if nome:
                        nomes.update(_variantes_alvo(nome))
            except Exception:
                self._falhas_descoberta += 1
        self._nomes = nomes
        return tuple(sorted(self._nomes))

    def validar(
        self,
        nome: str,
        *,
        estado: Mapping[str, Any] | None = None,
    ) -> bool:
        retrato = dict(estado or {})
        if bool(retrato.get("programa_aberto")):
            return True
        return any(variante in self._nomes for variante in _variantes_alvo(nome))

    def diagnostico(self) -> dict[str, Any]:
        return {
            "disponivel": True,
            "nomes": len(self._nomes),
            "falhas_descoberta": self._falhas_descoberta,
            "somente_leitura": True,
            "autoriza_execucao": False,
        }


def criar_catalogo_aplicativos_runtime(**kwargs: Any) -> CatalogoAplicativosRuntime:
    return CatalogoAplicativosRuntime(**kwargs)
