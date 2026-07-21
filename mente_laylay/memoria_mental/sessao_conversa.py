"""Limites de sessão para impedir que contexto encerrado volte como conversa atual."""

from __future__ import annotations

import re
import time
from typing import Any, Dict, Iterable

from mente_laylay.memoria_mental.registro_semantico import renovar_registro_semantico_sessao


def texto_encerra_conversa(texto: str) -> bool:
    t = re.sub(r"\s+", " ", str(texto or "").casefold()).strip(" .!?")
    if not t:
        return False
    padroes = (
        r"(?:tchau|até mais|ate mais|falou|fui|boa noite),?(?: lay| laylay)?",
        r"(?:por hoje|por agora) (?:é|e) só",
        r"(?:era|é|e) só isso(?: mesmo)?",
        r"(?:obrigado|obrigada|valeu),? (?:era|é|e) só isso",
        r"(?:vamos|a gente) (?:parar|encerra|encerrar) por aqui",
        r"(?:encerra|encerre|finaliza|finalize) (?:a )?conversa",
        r"depois (?:a gente|nós|nos) conversa",
        r"vou (?:sair|dormir|embora),?(?: até mais| ate mais)?",
    )
    return any(re.fullmatch(padrao, t, flags=re.IGNORECASE) for padrao in padroes)


def _limpar_campos(estado: Dict[str, Any], campos: Iterable[str], prefixos: Iterable[str] = ()) -> Dict[str, Any]:
    novo = dict(estado or {})
    alvos = set(campos)
    prefixos = tuple(prefixos)
    alvos.update(chave for chave in novo if any(chave.startswith(prefixo) for prefixo in prefixos))
    for chave in alvos:
        valor = novo.get(chave)
        if chave.endswith("_ts") or chave.endswith("_at"):
            novo[chave] = 0.0
        elif isinstance(valor, list):
            novo[chave] = []
        elif isinstance(valor, dict):
            novo[chave] = {}
        elif isinstance(valor, bool):
            novo[chave] = False
        else:
            novo[chave] = ""
    return novo


def renovar_contexto_sessao(
    mental: Dict[str, Any] | None,
    conversacional: Dict[str, Any] | None,
    mensagens: list | None,
    *,
    motivo: str,
    ativa: bool,
    agora: float | None = None,
) -> tuple[Dict[str, Any], Dict[str, Any], list]:
    """Limpa somente memória transitória; fatos e aprendizados permanecem."""
    instante = float(agora if agora is not None else time.time())
    mental_novo = _limpar_campos(
        dict(mental or {}),
        (
            "ultima_entrada", "ultimas_entradas", "ultima_entrada_ts", "ultima_resposta",
            "direcao_fala_atual", "historico_direcao_fala",
            "ultima_intencao", "ultimo_alvo", "ultimo_escopo", "ultima_habilidade",
            "pendencia_atual", "ultima_pendencia_encerrada", "oferta_pendente",
            "ultimo_resumo_pagina", "capacidade_futura", "foco_vivo", "focos_por_dominio",
            "conteudo_atual", "turno_atual", "plano_turno_atual", "ultima_decisao_semantica",
            "retrato_turno_atual", "especialistas_turno_atual", "assunto_estruturado_atual",
            "identidade_turno_atual", "identidade_turno_resumo", "funcao_comunicativa_atual",
            "ultima_correcao_conversacional", "ultima_correcao_conversacional_ts",
        ),
        prefixos=(
            "pergunta_aberta_", "ultima_promessa_", "foco_conversacional_",
            "foco_operacional_", "topico_explicito_", "ultima_acao_",
        ),
    )
    mental_novo.update({
        "registro_semantico": renovar_registro_semantico_sessao(
            (mental or {}).get("registro_semantico") if isinstance(mental, dict) else {},
            motivo=motivo,
            agora=instante,
        ),
        "sessao_conversa_ativa": bool(ativa),
        "sessao_conversa_motivo": str(motivo or "renovacao"),
        "sessao_conversa_ts": instante,
    })

    conversa_nova = dict(conversacional or {})
    conversa_nova.update({
        "current_emotion": "calma",
        "emotion_level": 1,
        "emotion_cause": "nova sessão de conversa",
        "emotion_started_at": instante,
        "emotion_duration_s": 0.0,
        "emotion_interactions_total": 0,
        "emotion_interactions_left": 0,
        "ultimo_topico_conversa": "",
        "ultimo_topico_ts": 0.0,
        "topicos_conversa_recente": [],
        "sessao_conversa_ativa": bool(ativa),
        "sessao_conversa_motivo": str(motivo or "renovacao"),
        "sessao_conversa_ts": instante,
    })

    sistemas = [
        dict(mensagem) for mensagem in list(mensagens or [])
        if isinstance(mensagem, dict) and str(mensagem.get("role") or "").casefold() == "system"
    ]
    return mental_novo, conversa_nova, sistemas[:1]
