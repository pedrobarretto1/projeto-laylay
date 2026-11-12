"""Interpretação compartilhada do receipt de reprodução do navegador.

Somente consumidores do executor usam este contrato; texto/modelo não é receipt.
``ok`` aqui representa entrega à página, não sucesso audível. O status original
e suas evidências permanecem disponíveis para a conclusão por aspectos.
"""
from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

from mente_laylay.memoria_mental.resultado_acao import AspectoResultado


def preservar_entrega_reproducao(retorno: dict[str, Any], url: str) -> dict[str, Any]:
    resultado = deepcopy(retorno)
    status = str(resultado.get("status") or "").strip()
    if status in {"autoplay_blocked", "playing_muted"}:
        evidencia = resultado.get("evidence")
        evidencia = evidencia if isinstance(evidencia, dict) else {}
        # Um receipt contraditório não sustenta a promoção a entrega parcial.
        if status == "playing_muted" and evidencia.get("playing") is False:
            resultado.update(ok=False, confirmado=False)
        else:
            resultado.update(
                ok=True, confirmado=None, status="video_aberto_sem_confirmacao",
                status_executor=status,
            )
            resultado.setdefault("message", "O vídeo abriu, mas o player não confirmou o áudio")
    resultado.setdefault("url", url)
    return resultado


def aspectos_entrega_reproducao(
    entrega: dict[str, Any], id_solicitacao: str,
) -> tuple[AspectoResultado, ...]:
    """Adapta apenas a entrega parcial observada da ocorrência do executor."""
    if (not id_solicitacao or entrega.get("ok") is not True
            or entrega.get("confirmado") is not None
            or entrega.get("status") != "video_aberto_sem_confirmacao"
            or entrega.get("status_executor") not in {"playing_muted", "autoplay_blocked"}):
        return ()
    evidencia = json.dumps({k: entrega.get(k) for k in
        ("status_executor", "request_id", "tab", "evidence")}, ensure_ascii=False)
    aspectos = [AspectoResultado(id_solicitacao, "abertura do vídeo", True, evidencia)]
    if entrega["status_executor"] == "playing_muted":
        aspectos.append(AspectoResultado(id_solicitacao, "início da reprodução do vídeo", True, evidencia))
    aspectos.append(AspectoResultado(id_solicitacao, "áudio audível", None, evidencia))
    return tuple(aspectos)
