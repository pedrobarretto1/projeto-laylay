"""Fechamento de topico sem apagar fatos ou encerrar toda a mente."""

from __future__ import annotations

import re
import time
from typing import Any, Dict

from mente_laylay.memoria_mental.sessao_conversa import texto_encerra_conversa


def classificar_encerramento_assunto(texto: str, estado_mental: Dict[str, Any] | None = None) -> str:
    bruto = str(texto or "").strip()
    t = re.sub(r"\s+", " ", bruto.casefold()).strip(" .!?")
    if not t:
        return ""
    if texto_encerra_conversa(bruto):
        return "sessao"
    if re.match(r"^(?:mudando de assunto|outro assunto|outra coisa|agora sobre)\b", t):
        return "topico"
    if "?" in bruto or re.search(r"\b(?:mas|e)\s+(?:qual|como|quando|onde|por que|porque|pode|faz|abre|liga|coloca)\b", t):
        return ""
    pendencia = (estado_mental or {}).get("pendencia_atual")
    if isinstance(pendencia, dict) and pendencia.get("status") == "ativa" and t in {
        "sim", "pode", "beleza", "ok", "certo", "fechado", "isso",
    }:
        return ""
    padroes = (
        r"(?:obrigado|obrigada|valeu|vlw)(?: lay| laylay)?",
        r"(?:beleza|ok|certo|fechado|perfeito)(?: entao| então)?",
        r"(?:entendi|ja entendi|já entendi|agora entendi)(?: lay| laylay)?",
        r"(?:deixa pra la|deixa pra lá|deixa quieto|esquece isso)",
        r"(?:resolvido|era isso|era isso mesmo|so queria saber isso|só queria saber isso)",
    )
    return "topico" if any(re.fullmatch(padrao, t, flags=re.IGNORECASE) for padrao in padroes) else ""


def encerrar_topico(
    mental: Dict[str, Any] | None,
    conversacional: Dict[str, Any] | None,
    *,
    motivo: str,
    agora: float | None = None,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    instante = float(agora if agora is not None else time.time())
    mente = dict(mental or {})
    conversa = dict(conversacional or {})
    topico = str(
        conversa.get("ultimo_topico_conversa")
        or mente.get("foco_conversacional_topico")
        or mente.get("topico_explicito_atual")
        or ""
    ).strip()
    historico = list(mente.get("assuntos_encerrados") or [])
    if topico:
        historico.append({"topico": topico, "motivo": str(motivo or "encerrado"), "ts": instante})
    mente.update({
        "assuntos_encerrados": historico[-20:],
        "ultimo_assunto_encerrado": topico,
        "ultimo_assunto_encerrado_ts": instante,
        "encerramento_assunto_pendente": "",
        "foco_conversacional_topico": "",
        "foco_conversacional_alvo": "",
        "foco_conversacional_tipo": "",
        "foco_conversacional_resposta": "",
        "foco_conversacional_ts": 0.0,
        "topico_explicito_atual": "",
        "topico_explicito_origem": "",
        "topico_explicito_ts": 0.0,
        "pergunta_aberta_texto": "",
        "pergunta_aberta_ts": 0.0,
        "pendencia_atual": {},
    })
    conversa.update({"ultimo_topico_conversa": "", "ultimo_topico_ts": 0.0})
    return mente, conversa
