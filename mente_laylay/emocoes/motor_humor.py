"""Motor de humor e gatilhos instintivos da Laylay."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional, Tuple


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def ajustar_humor(ctx: Dict[str, Any], delta: int, motivo: str = "desconhecido") -> int:
    humor_level = int(_get(ctx, "humor_level", 0))
    humor_last_update = float(_get(ctx, "humor_last_update", time.time()))
    humor_history = list(_get(ctx, "humor_history", []) or [])

    humor_level = max(-10, min(10, humor_level + int(delta)))
    humor_last_update = time.time()

    humor_history.append(f"{time.strftime('%H:%M')} → {motivo} ({delta:+}) → humor={humor_level}")
    if len(humor_history) > 10:
        humor_history = humor_history[-10:]

    ctx["humor_level"] = humor_level
    ctx["humor_last_update"] = humor_last_update
    ctx["humor_history"] = humor_history

    print(f"😤 [MOTOR DE HUMOR] {motivo} → humor agora = {humor_level}")
    return humor_level


def get_humor_prompt(ctx: Dict[str, Any]) -> str:
    humor_level = int(_get(ctx, "humor_level", 0))
    if humor_level >= 7:
        return "extasiada, carinhosa e cheia de energia"
    if humor_level >= 4:
        return "feliz, debochada e bem-humorada"
    if humor_level >= 1:
        return "calma e confiante"
    if humor_level >= -3:
        return "levemente irritada, sarcástica"
    if humor_level >= -7:
        return "irritada, impaciente e afiada"
    return "muito brava, curta e direta, sem paciência"


def montar_status_humor_prompt(
    contexto: Dict[str, Any] | None,
    percepcao: Dict[str, Any] | None,
    *,
    humor_fallback: int = 0,
    emocao_fallback: str = "calma",
    periodo_fallback: str = "",
    descricao_emocao_cb: Callable[[str], str],
    perfil_comportamento_cb: Callable[[str], str],
) -> str:
    """Combina emoção e percepção em um único retrato para o prompt."""
    ctx = contexto if isinstance(contexto, dict) else {}
    leitura = percepcao if isinstance(percepcao, dict) else {}
    humor = int(ctx["humor"] if ctx else humor_fallback)
    emocao = str(ctx["emocao"] if ctx else emocao_fallback).strip()
    periodo = str(ctx["periodo"] if ctx else periodo_fallback).strip()

    if humor <= -5:
        base = "está muito irritada, sarcástica e impaciente"
    elif humor <= -2:
        base = "está levemente irritada e debochada"
    elif humor >= 5:
        base = "está muito fofa, carinhosa e prestativa"
    elif humor >= 2:
        base = "está feliz, bem-humorada e debochada"
    else:
        base = "está neutra e calma"

    extras = []
    if periodo in {"madrugada", "noite"}:
        extras.append("o contexto pede baixo ritmo")
    if leitura:
        extras.append(
            f"leitura contextual: {leitura['conclusao']} "
            f"(confianca={leitura['confianca']})"
        )
        extras.append(f"interpretacao: {leitura['interpretacao']}")
    if emocao:
        extras.append(f"emoção percebida: {emocao}")
        extras.append(f"identidade emocional: {descricao_emocao_cb(emocao)}")
        extras.append(f"comportamento esperado: {perfil_comportamento_cb(emocao)}")
    if ctx.get("topico_ativo"):
        extras.append(f"tópico ativo: {ctx['topico_ativo']}")
    if extras:
        return base + "; " + "; ".join(extras)
    return base


def detectar_gatilhos_instintivos(
    ctx: Dict[str, Any],
    texto: str,
    normalizar_cb: Callable[[str], str] = None,
) -> Tuple[Optional[str], Optional[int]]:
    """Reações automáticas sem passar pela IA.

    Args:
        ctx: dicionário de contexto com estado atual.
        texto: texto do usuário.
        normalizar_cb: função de normalização de texto (opcional).
            Se não fornecida, usa lower() simples como fallback.
    """
    if normalizar_cb is not None:
        lower = normalizar_cb(texto)
    else:
        lower = texto.lower()

    is_speaking = bool(_get(ctx, "is_speaking", False))
    interrupt_event = _get(ctx, "interrupt_event")
    barge_in_count = int(_get(ctx, "barge_in_count", 0))
    barge_in_window = float(_get(ctx, "barge_in_window", 5.0))
    humor_last_update = float(_get(ctx, "humor_last_update", time.time()))

    if is_speaking and interrupt_event is not None and getattr(interrupt_event, "is_set", lambda: False)():
        barge_in_count += 1
        ctx["barge_in_count"] = barge_in_count
        if barge_in_count >= 3 and (time.time() - humor_last_update) < barge_in_window:
            ajustar_humor(ctx, -3, "múltiplas interrupções seguidas")
            ctx["barge_in_count"] = 0
            return "irritada", 3
        return None, None

    if any(word in lower for word in ["cala boca", "cala a boca", "shut up", "quieta"]):
        ajustar_humor(ctx, -4, "mandou calar a boca")
        return "brava", 3

    if any(
        word in lower
        for word in [
            "obrigado",
            "obrigada",
            "valeu",
            "vlw",
            "muito bom",
            "te amo",
            "gostei",
            "amei",
            "lindo",
            "linda",
            "perfeito",
            "maravilhoso",
            "maravilhosa",
            "fofa",
            "fofo",
            "bonita",
            "bonito",
            "você é incrível",
            "voce e incrivel",
        ]
    ):
        ajustar_humor(ctx, +2, "usuário elogiou")
        return "envergonhada", 2

    return None, None
