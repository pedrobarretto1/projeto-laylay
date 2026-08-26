"""Estado compacto e explícito do assunto conversacional atual."""

from __future__ import annotations

import re
import time
from typing import Any, Dict


def atualizar_assunto_estruturado(
    estado_anterior: Dict[str, Any] | None,
    texto: str,
    *,
    turno: Dict[str, Any] | None,
    retrato: Dict[str, Any] | None,
    encerramento: str = "",
    agora: float | None = None,
) -> Dict[str, Any]:
    instante = float(agora if agora is not None else time.time())
    anterior = dict(estado_anterior or {})
    if str(encerramento or "") == "topico":
        anterior.update(status="encerrado", encerrado_ts=instante, atualizado_ts=instante)
        return anterior

    leitura = dict(turno or {})
    snapshot = dict(retrato or {})
    referencia = dict(snapshot.get("referencia_resolvida") or {})
    texto_social = str(leitura.get("texto_conversacional") or "").strip()
    if not texto_social and str(leitura.get("ato_principal") or "") != "comando":
        texto_social = str(texto or "").strip()

    nome = str(referencia.get("nome") or "").strip()
    dominio = str(referencia.get("tipo") or "conversa").strip()
    origem = "referencia_resolvida" if nome else "fala_atual"
    if not nome and texto_social:
        nome = re.sub(r"\s+", " ", texto_social).strip(" .,!?:;")[:160]
    if not nome:
        return anterior

    entidades = [
        {"tipo": str(item.get("tipo") or chave), "nome": str(item.get("nome") or "")}
        for chave, item in dict(snapshot.get("entidades") or {}).items()
        if isinstance(item, dict) and str(item.get("nome") or "").strip()
    ]
    mesmo = str(anterior.get("titulo") or "").casefold() == nome.casefold()
    iniciado_ts = float(anterior.get("iniciado_ts") or instante) if mesmo else instante
    return {
        "id": str(anterior.get("id") or int(instante * 1000)) if mesmo else str(int(instante * 1000)),
        "titulo": nome,
        "dominio": dominio,
        "status": "ativo",
        "origem": origem,
        "entidades": entidades[-12:],
        "iniciado_ts": iniciado_ts,
        "atualizado_ts": instante,
    }
