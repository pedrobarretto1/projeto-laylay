"""Coerencia entre o relogio atual, correcoes do usuario e a fala final."""

from __future__ import annotations

import re


def periodo_humano(periodo: str) -> str:
    periodo_norm = str(periodo or "").strip().casefold()
    return {
        "manha": "manhã",
        "tarde": "tarde",
        "noite": "noite",
        "madrugada": "madrugada",
    }.get(periodo_norm, "dia")


def detectar_correcao_temporal(texto: str) -> bool:
    t = re.sub(r"\s+", " ", str(texto or "")).strip().casefold()
    return bool(
        re.search(r"\b(?:ainda\s+)?(?:ta|tá|esta|está|e|é)\s+de\s+(?:dia|tarde|manha|manhã)\b", t)
        or re.search(r"\b(?:nao|não)\s+(?:e|é|ta|tá|esta|está)\s+(?:de\s+)?(?:noite|madrugada)\b", t)
        or re.search(r"\bvoce\s+(?:falou|disse)\s+(?:noite|manha|manhã|tarde)\b", t)
    )


def responder_correcao_temporal(texto: str, periodo: str) -> str:
    if not detectar_correcao_temporal(texto):
        return ""
    atual = periodo_humano(periodo)
    if atual == "madrugada":
        return "Você fez bem em me corrigir. Pelo relógio, já é madrugada; eu não devia ter tratado isso como noite comum."
    if atual == "noite":
        return "Entendi a correção. Pelo meu relógio, já entrou no período da noite; se o horário local estiver diferente, eu preciso conferir essa fonte antes de insistir."
    return f"Você tem razão: ainda é {atual}. Eu me adiantei ao falar em noite."


def ajustar_fala_ao_periodo(fala: str, periodo: str) -> str:
    """Remove contradições temporais óbvias de respostas não factuais."""
    texto = str(fala or "").strip()
    periodo_norm = str(periodo or "").strip().casefold()
    if not texto or periodo_norm in {"", "noite", "madrugada"}:
        return texto
    atual = periodo_humano(periodo_norm)
    substituicoes = (
        (r"\bessa noite\b", f"esta {atual}"),
        (r"\bnessa noite\b", f"nesta {atual}"),
        (r"\ba noite\b", f"a {atual}"),
        (r"\bda noite\b", f"da {atual}"),
        (r"\bpra noite\b", f"pra {atual}"),
        (r"\bpara a noite\b", f"para a {atual}"),
        (r"\bresto da noite\b", f"resto da {atual}"),
    )
    for padrao, novo in substituicoes:
        texto = re.sub(padrao, novo, texto, flags=re.IGNORECASE)
    return texto
