"""Leitura social e respostas afetivas da conversa natural."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict

from mente_laylay.personalidade.base_conversa import _get, _normalizar_apelidos




def _normalizar_reconhecimento(texto: str) -> str:
    bruto = unicodedata.normalize("NFKD", str(texto or "").casefold())
    return "".join(ch for ch in bruto if not unicodedata.combining(ch))


def tipo_reconhecimento_afetivo(texto_usuario: str) -> str:
    """Distingue gratidão pela ajuda de elogio dirigido à personalidade."""
    t = _normalizar_reconhecimento(texto_usuario)
    elogios_pessoais = (
        "voce e incrivel", "voce e maravilhosa", "voce e maravilhoso",
        "voce e linda", "voce e lindo", "voce e adoravel", "voce e uma fofa",
        "voce e fofo", "voce e legal", "voce e bem legal", "voce e muito legal",
        "gosto de voce", "te acho legal", "amo voce", "te amo",
        "estou te elogiando", "apenas um elogio", "so um elogio",
        "laylay e incrivel", "a laylay e incrivel", "laylay e maravilhosa",
        "a laylay e maravilhosa", "laylay e legal", "gosto da laylay",
    )
    if any(sinal in t for sinal in elogios_pessoais):
        return "elogio_pessoal"
    if any(sinal in t for sinal in ("obrigad", "brigad", "valeu", "valew", "vlw")):
        return "agradecimento"
    return "elogio_resultado"




def parece_elogio_ou_agradecimento_curto(ctx: Dict[str, Any], texto_usuario: str) -> bool:
    bruto = _normalizar_reconhecimento(texto_usuario)
    correcao_para_agradecimento = bool(re.search(
        r"\b(?:quer\s+dizer|quis\s+dizer|corrigindo)\b.{0,35}\b"
        r"(?:obrigad[oa]|valeu|vlw)\b",
        bruto,
    ))
    # Uma correção dirigida à Laylay pode herdar uma leitura semântica antiga
    # de agradecimento. A intenção explícita do texto atual sempre prevalece.
    if texto_parece_correcao_conversacional(bruto) and not correcao_para_agradecimento:
        return False
    # Uma avaliação dirigida a uma terceira pessoa não é elogio recebido pela
    # Laylay. Esta proteção vem antes do normalizador personalizado porque uma
    # correção fonética pode aproximar "gosto" de "gostei".
    if (
        re.search(r"\b(?:dele|dela|deles|delas)\b", bruto)
        and not re.search(r"\b(?:obrigad|brigad|valeu|vlw)\b", bruto)
        and not re.search(r"\b(?:lay|laylay|voce|você|te)\b", bruto)
    ):
        return False
    t = _normalizar_apelidos(ctx, texto_usuario)
    if not t:
        return False
    if any(p in t for p in ("nao gostei", "não gostei", "nao ficou bom", "não ficou bom")):
        return False
    if "?" in str(texto_usuario or "") and any(
        p in t for p in ("qual", "como", "quando", "onde", "porque", "por que", "quanto")
    ):
        return False
    variantes = [
        "obrigado", "obrigada", "brigado", "brigada", "orbigado", "orbrigado",
        "obigado", "obridago", "valeu", "valew", "vlw", "perfeito", "amei",
        "gostei", "maravilhoso", "maravilhosa", "lindo", "linda", "fofo",
        "fofa", "incrivel", "incrível", "estou te elogiando", "to te elogiando",
        "apenas um elogio", "so um elogio", "só um elogio",
        "voce e legal", "voce e bem legal", "voce e muito legal",
        "você é legal", "você é bem legal", "você é muito legal",
        "vc e legal", "vc e bem legal", "te acho legal", "gosto de voce",
        "gosto de você", "voce e incrivel", "você é incrível",
        "voce e adoravel", "você é adorável", "vc e adoravel",
        "voce e uma fofa", "você é uma fofa", "voce e fofo", "você é fofo",
        "laylay e incrivel", "a laylay e incrivel", "laylay e maravilhosa",
        "a laylay e maravilhosa", "laylay e legal", "a laylay e legal",
        "gosto da laylay", "amo a laylay",
    ]
    return any(x in t for x in variantes)


def parece_pedido_para_acalmar(ctx: Dict[str, Any], texto_usuario: str) -> bool:
    t = _normalizar_apelidos(ctx, texto_usuario)
    if not t:
        return False
    if any(p in t for p in [
        "nao precisa ficar brava",
        "não precisa ficar brava",
        "nao fica brava",
        "não fica brava",
        "se acalme",
        "calma lay",
        "fica calma",
        "ta brava",
        "tá brava",
    ]):
        return True
    emocao = str(_get(ctx, "current_emotion", "") or "").strip().lower()
    return t in {"que isso", "que isso lay"} and emocao in {"brava", "irritada", "nervosa", "raivosa"}


def _parece_confirmacao_curta(t: str) -> bool:
    return bool(re.fullmatch(
        r"^(sim|isso|isso mesmo|claro|claro que sim|aham|uhum|humrum|pode|pode sim|e sim|é sim|foi sim|veio sim|veiuo sim|pode ser|bora|vai|manda|fechou|fechado)$",
        t,
    ))


def _parece_correcao_conversa(t: str) -> bool:
    padroes = [
        r"^(nao|não)\s+lay.*$",
        r"^(nao|não)\s+(?:e|é|eh)\s+isso\s+lay.*$",
        r"^(a\s+nao|ah\s+nao|ah\s+n[aã]o)\s+lay.*$",
        r"^eu\s+quis\s+dizer\s+.+$",
        r"^eu\s+tava\s+falando\s+de\s+.+$",
        r"^eu\s+estava\s+falando\s+de\s+.+$",
        r"^to\s+falando\s+de\s+.+$",
        r"^estou\s+falando\s+de\s+.+$",
        r"^na\s+verdade\s+.+$",
        r"^(?:so|só)\s+(?:to|tô|estou)\s+falando\s+.+$",
    ]
    return any(re.fullmatch(p, t) for p in padroes)


def texto_parece_correcao_conversacional(texto: str) -> bool:
    """Reconhece correções explícitas antes de qualquer atalho social."""
    return _parece_correcao_conversa(_normalizar_reconhecimento(texto))
