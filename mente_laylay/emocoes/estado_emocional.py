"""Estado emocional temporal compartilhado da Laylay."""

from __future__ import annotations

import math
import time
from typing import Any, Dict


PERFIS_DURACAO = {
    "envergonhada": (45.0, 2),
    "surpresa": (45.0, 2),
    "alegre": (120.0, 4),
    "debochada": (120.0, 4),
    "irritada": (150.0, 4),
    "brava": (210.0, 5),
    "triste": (240.0, 6),
    "acalmando-se": (75.0, 2),
}


def aplicar_estado_emocional(
    estado_atual: Dict[str, Any] | None,
    emocao: str,
    nivel: int = 1,
    *,
    causa: str = "",
    agora: float | None = None,
    duracao_s: float | None = None,
    interacoes: int | None = None,
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    emo = str(emocao or "calma").strip().lower() or "calma"
    nivel_limpo = max(1, min(3, int(nivel or 1)))
    instante = float(agora if agora is not None else time.time())

    if emo == "calma":
        estado.update({
            "current_emotion": "calma",
            "emotion_level": 1,
            "emotion_cause": str(causa or "voltou ao equilíbrio").strip(),
            "emotion_started_at": instante,
            "emotion_duration_s": 0.0,
            "emotion_interactions_total": 0,
            "emotion_interactions_left": 0,
            "emotion_last_decay_at": instante,
        })
        return estado

    duracao_padrao, interacoes_padrao = PERFIS_DURACAO.get(emo, (120.0, 3))
    duracao = max(15.0, float(duracao_s if duracao_s is not None else duracao_padrao))
    total_interacoes = max(1, int(interacoes if interacoes is not None else interacoes_padrao))
    estado.update({
        "current_emotion": emo,
        "emotion_level": nivel_limpo,
        "emotion_cause": str(causa or "reação contextual").strip()[:160],
        "emotion_started_at": instante,
        "emotion_duration_s": duracao,
        "emotion_interactions_total": total_interacoes,
        "emotion_interactions_left": total_interacoes,
        "emotion_last_decay_at": instante,
    })
    return estado


def decair_estado_emocional(
    estado_atual: Dict[str, Any] | None,
    *,
    agora: float | None = None,
    consumir_interacao: bool = True,
) -> tuple[Dict[str, Any], bool]:
    """Reduz intensidade sem trocar a emoção abruptamente."""
    estado = dict(estado_atual or {})
    emo = str(estado.get("current_emotion") or "calma").strip().lower()
    if emo == "calma":
        return estado, False

    instante = float(agora if agora is not None else time.time())
    inicio = float(estado.get("emotion_started_at") or instante)
    duracao = max(1.0, float(estado.get("emotion_duration_s") or PERFIS_DURACAO.get(emo, (120.0, 3))[0]))
    total = max(1, int(estado.get("emotion_interactions_total") or PERFIS_DURACAO.get(emo, (120.0, 3))[1]))
    restantes = max(0, int(estado.get("emotion_interactions_left") if estado.get("emotion_interactions_left") is not None else total))
    nivel = max(1, min(3, int(estado.get("emotion_level") or 1)))

    if consumir_interacao:
        restantes = max(0, restantes - 1)

    progresso_tempo = max(0.0, (instante - inicio) / duracao)
    progresso_interacao = 1.0 - (restantes / total)
    progresso = max(progresso_tempo, progresso_interacao)

    if progresso >= 1.0 or restantes <= 0:
        novo = aplicar_estado_emocional(
            estado,
            "calma",
            1,
            causa=f"{emo} passou naturalmente",
            agora=instante,
        )
        return novo, True

    nivel_alvo = max(1, min(3, int(math.ceil((1.0 - progresso) * 3))))
    novo_nivel = min(nivel, nivel_alvo)
    alterou = novo_nivel != nivel or restantes != int(estado.get("emotion_interactions_left") or total)
    estado["emotion_level"] = novo_nivel
    estado["emotion_interactions_left"] = restantes
    estado["emotion_last_decay_at"] = instante
    return estado, alterou

