"""Monitor central das conexoes entre os modulos da mente da Laylay."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Iterable, Mapping


class SaudeMenteRuntime:
    STATUS_VALIDOS = {"saudavel", "degradado", "indisponivel"}

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._modulos: Dict[str, Dict[str, Any]] = {}

    def registrar(
        self,
        modulo: str,
        status: str,
        *,
        detalhes: str = "",
        ausentes: Iterable[str] | None = None,
    ) -> Dict[str, Any]:
        nome = str(modulo or "desconhecido").strip().lower()
        estado = str(status or "indisponivel").strip().lower()
        if estado not in self.STATUS_VALIDOS:
            estado = "indisponivel"
        registro = {
            "status": estado,
            "detalhes": str(detalhes or "").strip(),
            "ausentes": sorted({str(item) for item in (ausentes or []) if str(item)}),
            "ts": time.time(),
        }
        with self._lock:
            self._modulos[nome] = registro
        return dict(registro)

    def validar_dependencias(
        self,
        modulo: str,
        namespace: Mapping[str, Any] | None,
        obrigatorias: Iterable[str],
        *,
        callables: Iterable[str] | None = None,
    ) -> Dict[str, Any]:
        dados = namespace if isinstance(namespace, Mapping) else {}
        ausentes = [nome for nome in obrigatorias if nome not in dados or dados.get(nome) is None]
        invalidas = [
            nome
            for nome in (callables or [])
            if nome in dados and dados.get(nome) is not None and not callable(dados.get(nome))
        ]
        problemas = [*ausentes, *(f"{nome}:nao_callable" for nome in invalidas)]
        status = "saudavel" if not problemas else "degradado"
        return self.registrar(
            modulo,
            status,
            detalhes="contrato completo" if not problemas else "dependencias incompletas",
            ausentes=problemas,
        )

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {nome: dict(registro) for nome, registro in self._modulos.items()}

    def resumo_terminal(self) -> str:
        snapshot = self.snapshot()
        if not snapshot:
            return "🩺 [MENTE:SAUDE] nenhum modulo auditado"
        partes = []
        for nome, registro in sorted(snapshot.items()):
            status = registro.get("status")
            faltas = registro.get("ausentes") or []
            sufixo = f" faltando={','.join(faltas)}" if faltas else ""
            partes.append(f"{nome}={status}{sufixo}")
        return "🩺 [MENTE:SAUDE] " + " | ".join(partes)


def criar_saude_mente_runtime() -> SaudeMenteRuntime:
    return SaudeMenteRuntime()
