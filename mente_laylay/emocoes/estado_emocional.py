"""Estado emocional temporal compartilhado da Laylay."""

from __future__ import annotations

import math
import time
from typing import Any, Dict, Mapping

from mente_laylay.emocoes.contrato_causal import (
    evento_esta_ativo,
    evento_pode_alterar_estado,
)


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


def retrato_emocional_expressavel(
    estado: Mapping[str, Any] | None, *, agora: float | None = None,
) -> tuple[str, int]:
    """Seleciona a mesma emoção causal vigente para voz e representação visual."""
    dados = estado if isinstance(estado, Mapping) else {}
    emocao = str(dados.get("current_emotion") or "calma").strip().casefold()
    if emocao == "calma":
        return "calma", 1
    episodio = dados.get("episodio_emocional")
    if not isinstance(episodio, Mapping):
        return "calma", 1
    try:
        instante = float(time.time() if agora is None else agora)
        nivel = int(dados.get("emotion_level") or 1)
        nivel_evento = int(episodio.get("nivel") or 0)
        inicio = float(dados.get("emotion_started_at") or 0.0)
        duracao = float(dados.get("emotion_duration_s") or 0.0)
        restantes = int(dados.get("emotion_interactions_left") or 0)
    except (TypeError, ValueError, OverflowError):
        return "calma", 1
    if (
        not evento_pode_alterar_estado(episodio, agora=instante)
        or str(episodio.get("emocao") or "").strip().casefold() != emocao
        or not 1 <= nivel <= nivel_evento <= 3
        or not math.isfinite(inicio) or not math.isfinite(duracao)
        or inicio <= 0.0 or duracao <= 0.0
        or instante >= inicio + duracao or restantes <= 0
    ):
        return "calma", 1
    return emocao, nivel


def restaurar_estado_emocional_persistido(
    dados: Mapping[str, Any] | None, *, agora: float | None = None,
) -> Dict[str, Any]:
    """Reidrata apenas um episódio cuja causa ainda pode ser expressa."""
    estado = dict(dados or {})
    instante = float(time.time() if agora is None else agora)
    try:
        humor = max(-3, min(3, int(estado.get("humor_level") or 0)))
        ultimo_humor = float(estado.get("humor_last_update") or 0.0)
    except (TypeError, ValueError, OverflowError):
        humor, ultimo_humor = 0, 0.0
    if not math.isfinite(ultimo_humor) or ultimo_humor <= 0.0:
        humor, ultimo_humor = 0, instante
    estado["humor_level"] = humor
    estado["humor_last_update"] = ultimo_humor
    emocao, _nivel = retrato_emocional_expressavel(estado, agora=instante)
    if emocao == "calma":
        estado = aplicar_estado_emocional(
            estado, "calma", causa="episódio persistido sem causa vigente",
            agora=instante,
        )
        restaurado, _ = decair_estado_emocional(
            estado, agora=instante, consumir_interacao=False,
        )
        return restaurado
    restaurado, _ = decair_estado_emocional(
        estado, agora=instante, consumir_interacao=False,
    )
    return restaurado


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
    anterior = str(estado.get("current_emotion") or "calma")
    transicao = {"de": anterior, "para": emo, "ts": instante}

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
            "episodio_emocional": {},
            "transicao_emocional": transicao,
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
        "episodio_emocional": {},
        "transicao_emocional": transicao,
    })
    return estado


def aplicar_evento_emocional(
    estado_atual: Dict[str, Any] | None,
    evento: Mapping[str, Any] | None,
    *,
    agora: float | None = None,
) -> Dict[str, Any]:
    """Abre episódio temporário apenas a partir de causa publicada e vigente."""
    estado = dict(estado_atual or {})
    instante = float(time.time() if agora is None else agora)
    if not evento_pode_alterar_estado(evento, agora=instante):
        return estado
    dados = dict(evento or {})
    episodio_anterior = dict(estado.get("episodio_emocional") or {})
    if (
        episodio_anterior == dados
        and evento_esta_ativo(episodio_anterior, agora=instante)
    ):
        return estado
    emocao = str(dados.get("emocao") or "calma")
    if emocao == "calma":
        return estado
    try:
        nivel_novo = int(dados.get("nivel") or 1)
        relevancia_nova = float(dados.get("relevancia") or 0.0)
        relevancia_anterior = float(episodio_anterior.get("relevancia") or 0.0)
        confianca_nova = float(dados.get("confianca") or 0.0)
    except (TypeError, ValueError, OverflowError):
        return estado
    emocao_anterior, nivel_anterior = retrato_emocional_expressavel(
        estado, agora=instante,
    )
    recuperacao_confirmada = bool(
        emocao_anterior in {"irritada", "brava", "triste"}
        and emocao == "acalmando-se"
        and dados.get("arco") == "alivio"
        and dados.get("origem") == episodio_anterior.get("origem") == "resultado_operacional"
        and dados.get("natureza_evidencia") == "fato_observado"
        and str(dados.get("alvo") or "").casefold()
        == str(episodio_anterior.get("alvo") or "").casefold()
        and confianca_nova >= 0.90
    )
    manter_episodio = bool(
        emocao_anterior != "calma"
        and (
            nivel_novo < nivel_anterior
            or (nivel_novo == nivel_anterior and relevancia_nova < relevancia_anterior)
        )
        and not recuperacao_confirmada
    )
    if manter_episodio:
        novo = estado
    else:
        novo = aplicar_estado_emocional(
            estado, emocao, nivel_novo,
            causa=str(dados.get("causa") or ""), agora=instante,
        )
        novo["episodio_emocional"] = dados
    referencia = str(dados.get("evidencia_ref") or "")
    if referencia != str(estado.get("humor_ultimo_evento_ref") or ""):
        delta = (
            -1 if emocao in {"irritada", "brava", "triste"}
            else 1 if emocao in {"alegre", "acalmando-se"}
            else 0
        )
        novo["humor_level"] = max(
            -3, min(3, int(estado.get("humor_level") or 0) + delta),
        )
        novo["humor_last_update"] = instante
        novo["humor_ultimo_evento_ref"] = referencia
    return novo


def decair_estado_emocional(
    estado_atual: Dict[str, Any] | None,
    *,
    agora: float | None = None,
    consumir_interacao: bool = True,
    contexto: str = "",
) -> tuple[Dict[str, Any], bool]:
    """Reduz intensidade sem trocar a emoção abruptamente."""
    estado = dict(estado_atual or {})
    instante = float(agora if agora is not None else time.time())
    humor = int(estado.get("humor_level") or 0)
    ultimo_humor = float(estado.get("humor_last_update") or instante)
    passos_humor = max(0, int((instante - ultimo_humor) // 300.0))
    alterou_humor = bool(humor and passos_humor)
    if alterou_humor:
        estado["humor_level"] = humor - min(humor, passos_humor) if humor > 0 else humor + min(-humor, passos_humor)
        estado["humor_last_update"] = ultimo_humor + passos_humor * 300.0
    if str(contexto or "").casefold() in {
        "correcao", "desabafo", "inseguranca", "decepcao", "frustracao",
    } and str(estado.get("current_emotion") or "").casefold() in {
        "brava", "irritada", "debochada",
    }:
        novo = aplicar_estado_emocional(
            estado, "calma", causa="contexto pede escuta ou autorreparo", agora=instante,
        )
        novo["humor_level"] = max(0, int(novo.get("humor_level") or 0))
        novo["humor_last_update"] = instante
        return novo, True
    emo = str(estado.get("current_emotion") or "calma").strip().lower()
    if emo == "calma":
        return estado, alterou_humor

    if str(contexto or "").casefold() == "mudanca_assunto":
        return aplicar_estado_emocional(
            estado, "calma", causa="assunto do episódio encerrado", agora=instante,
        ), True

    episodio = estado.get("episodio_emocional")
    if isinstance(episodio, Mapping) and episodio and not evento_esta_ativo(
        episodio, agora=instante,
    ):
        return aplicar_estado_emocional(
            estado, "calma", causa="causa do episódio expirou", agora=instante,
        ), True
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
    if (
        str(contexto or "").casefold() == "pedido_desculpas"
        and isinstance(episodio, Mapping)
        and episodio.get("arco") == "bronca_brincalhona"
        and episodio.get("responsabilidade") == "usuario"
    ):
        novo_nivel = max(1, min(novo_nivel, nivel - 1))
    alterou = alterou_humor or novo_nivel != nivel or restantes != int(estado.get("emotion_interactions_left") or total)
    estado["emotion_level"] = novo_nivel
    if novo_nivel != nivel:
        estado["transicao_emocional"] = {
            "de": emo, "para": emo, "nivel_de": nivel,
            "nivel_para": novo_nivel, "ts": instante,
        }
    estado["emotion_interactions_left"] = restantes
    estado["emotion_last_decay_at"] = instante
    return estado, alterou
