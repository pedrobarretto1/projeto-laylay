"""Retrato temporário de uma entrega, separado do episódio emocional vivo."""

from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass
from typing import Any, Mapping
from uuid import uuid4

from mente_laylay.emocoes.estado_emocional import retrato_emocional_expressavel


@dataclass(frozen=True, slots=True)
class RetratoEntregaFala:
    mensagem_id: str
    emocao: str
    nivel: int
    evidencia_ref: str
    publicado_ts: float

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


def criar_retrato_entrega_fala(
    estado: Mapping[str, Any] | None,
    *,
    mensagem_id: str = "",
    agora: float | None = None,
) -> RetratoEntregaFala:
    """Congela só expressão já validada; não cria causa nem estende validade."""
    dados = dict(estado) if isinstance(estado, Mapping) else {}
    instante = float(time.time() if agora is None else agora)
    emocao, nivel = retrato_emocional_expressavel(dados, agora=instante)
    episodio = dados.get("episodio_emocional")
    episodio = dict(episodio) if isinstance(episodio, Mapping) else {}
    return RetratoEntregaFala(
        mensagem_id=str(mensagem_id or f"fala:{uuid4().hex}"),
        emocao=emocao,
        nivel=nivel,
        evidencia_ref=(
            str(episodio.get("evidencia_ref") or "") if emocao != "calma" else ""
        ),
        publicado_ts=instante,
    )


def ler_retrato_entrega_fala(dados: Any) -> RetratoEntregaFala | None:
    """Lê a projeção transitória da voz; um mapping incompleto não é retrato."""
    if not isinstance(dados, Mapping):
        return None
    try:
        mensagem_id = str(dados.get("mensagem_id") or "").strip()
        emocao = str(dados.get("emocao") or "").strip()
        nivel = int(dados.get("nivel") or 0)
        referencia = str(dados.get("evidencia_ref") or "")
        instante = float(dados.get("publicado_ts") or 0.0)
    except (TypeError, ValueError, OverflowError):
        return None
    if (
        not mensagem_id or not emocao or not 1 <= nivel <= 3
        or not math.isfinite(instante) or instante <= 0.0
        or (emocao != "calma" and not referencia)
        or (emocao == "calma" and nivel != 1)
    ):
        return None
    return RetratoEntregaFala(mensagem_id, emocao, nivel, referencia, instante)
