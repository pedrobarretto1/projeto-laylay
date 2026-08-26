"""Processadores conversacionais do domínio musical no pré-fluxo."""

from __future__ import annotations

from typing import Any, Dict, Tuple

from mente_laylay.autonomia.base_pre_fluxo import _get
from mente_laylay.cognicao.modalidade_turno import turno_tem_veto_execucao


def _turno_atual(ctx: Dict[str, Any]) -> Dict[str, Any]:
    mente = _get(ctx, "mente_integrada_estado", {})
    turno = mente.get("turno_atual") if isinstance(mente, dict) else {}
    return dict(turno or {}) if isinstance(turno, dict) else {}

def processar_confirmacao_musical_pendente(
    ctx: Dict[str, Any], texto_usuario: str,
) -> Tuple[bool, str]:
    if turno_tem_veto_execucao(_turno_atual(ctx)):
        return False, ""
    processar_confirmacao_sugestao_musical = _get(ctx, "_processar_confirmacao_sugestao_musical")
    t = str(texto_usuario or "").strip()

    if callable(processar_confirmacao_sugestao_musical) and processar_confirmacao_sugestao_musical(t):
        return True, "confirmacao_sugestao_musical"
    return False, ""

def processar_pedido_direcao_musical(
    ctx: Dict[str, Any], texto_usuario: str,
) -> Tuple[bool, str]:
    texto_pede_direcao_musical_generica = _get(ctx, "_texto_pede_direcao_musical_generica")
    responder_pedido_direcao_musical_generica = _get(ctx, "_responder_pedido_direcao_musical_generica")
    t = str(texto_usuario or "").strip()

    if callable(texto_pede_direcao_musical_generica) and texto_pede_direcao_musical_generica(t):
        if callable(responder_pedido_direcao_musical_generica):
            ok = bool(responder_pedido_direcao_musical_generica(t))
            return ok, "direcao_musical_generica" if ok else ""
        return True, "direcao_musical_generica"

    return False, ""

def processar_fluxo_musical_generico(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    """Compatibilidade local; produção separa confirmação de pedido novo."""
    confirmado = processar_confirmacao_musical_pendente(ctx, texto_usuario)
    if confirmado[0]:
        return confirmado
    return processar_pedido_direcao_musical(ctx, texto_usuario)

def processar_opiniao_musica_atual(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    detectar = _get(ctx, "_texto_pede_opiniao_musica_atual")
    responder = _get(ctx, "_responder_opiniao_musica_atual")
    if not callable(detectar) or not callable(responder):
        return False, ""
    try:
        if not detectar(texto_usuario):
            return False, ""
        return bool(responder(texto_usuario)), "opiniao_musica_atual"
    except Exception as erro:
        print(f"⚠️ [MÚSICA:OPINIÃO] falha no fluxo conversacional: {erro}")
        return False, ""
