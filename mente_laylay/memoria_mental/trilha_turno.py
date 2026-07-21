"""Trilha curta e explicável do caminho de cada turno."""

from __future__ import annotations

import time
from typing import Any, Dict


def registrar_etapa_turno(
    historico: list | None,
    plano: Dict[str, Any] | None,
    *,
    fase: str,
    limite: int = 80,
) -> list:
    contrato = dict(plano or {})
    especialistas = dict(contrato.get("especialistas") or {})
    coordenacao = dict(especialistas.get("coordenacao") or {})
    operacional = dict(especialistas.get("operacional") or {})
    registro = {
        "turno_id": contrato.get("id"),
        "entrada": str(contrato.get("texto_usuario") or "")[:300],
        "fase": str(fase or contrato.get("fase") or ""),
        "modo": str(coordenacao.get("modo") or contrato.get("modo_coordenacao") or ""),
        "autoriza_execucao": operacional.get("autoriza_execucao"),
        "confiancas": dict(operacional.get("confiancas") or {}),
        "comandos": list(contrato.get("comandos") or []),
        "erros": list(contrato.get("erros") or []),
        "ts": time.time(),
    }
    itens = list(historico or [])
    if itens and itens[-1].get("turno_id") == registro["turno_id"] and itens[-1].get("fase") == registro["fase"]:
        itens[-1] = registro
    else:
        itens.append(registro)
    return itens[-max(1, int(limite)) :]
