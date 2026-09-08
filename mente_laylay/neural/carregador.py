"""Carregamento tardio para não aumentar a inicialização da Laylay."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any


def resolver_caminho_modelo_neural(
    *,
    raiz: str | Path,
    pasta_memoria: str | Path,
    configurado: str | Path | None,
    modo: str = "shadow",
    candidato_shadow: str | Path | None = None,
) -> Path:
    """Seleciona artefato explícito sem mudar o caminho estável padrão."""
    valor = str(configurado or "").strip()
    if valor:
        caminho = Path(valor)
        return caminho if caminho.is_absolute() else Path(raiz) / caminho
    candidato = Path(candidato_shadow) if candidato_shadow else None
    if (
        str(modo or "").strip().casefold() == "shadow"
        and candidato is not None
        and candidato.is_file()
    ):
        return candidato
    return Path(pasta_memoria) / "neural" / "modelo_ativo.joblib"


class ModeloNeuralPreguicoso:
    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho)
        self._modelo: Any = None
        self._lock = threading.RLock()

    @property
    def versao(self) -> str:
        return str(getattr(self._modelo, "versao", self.caminho.stem))

    def _obter(self) -> Any:
        with self._lock:
            if self._modelo is None:
                if not self.caminho.is_file():
                    raise FileNotFoundError(self.caminho)
                from .modelo import carregar_modelo

                self._modelo = carregar_modelo(self.caminho)
            return self._modelo

    def prever(self, texto: str) -> dict[str, Any]:
        return self._obter().prever(texto)

    def precarregar(self) -> bool:
        modelo = self._obter()
        precarregar_modelo = getattr(modelo, "precarregar", None)
        if callable(precarregar_modelo):
            return bool(precarregar_modelo())
        return True
