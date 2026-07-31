"""Contrato comum para executores de dominios do roteador de intencoes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResultadoDespacho:
    """Informa se um executor reconheceu a intencao e qual retorno produziu."""

    tratado: bool
    retorno: bool = False

    @classmethod
    def nao_tratado(cls) -> "ResultadoDespacho":
        return cls(tratado=False, retorno=False)

    @classmethod
    def concluido(cls, retorno: bool = True) -> "ResultadoDespacho":
        return cls(tratado=True, retorno=bool(retorno))
