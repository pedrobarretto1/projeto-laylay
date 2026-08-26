"""Motor de humor e gatilhos instintivos da Laylay."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict


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
        if ctx.get("emocao_causa"):
            extras.append(f"causa emocional: {ctx.get('emocao_causa')}")
        if emocao != "calma" and ctx.get("emocao_interacoes_restantes") is not None:
            extras.append(
                f"persistência emocional: {int(ctx.get('emocao_interacoes_restantes') or 0)} interações restantes"
            )
    if ctx.get("topico_ativo"):
        extras.append(f"tópico ativo: {ctx['topico_ativo']}")
    if extras:
        return base + "; " + "; ".join(extras)
    return base
