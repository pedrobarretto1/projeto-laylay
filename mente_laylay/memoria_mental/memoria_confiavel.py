"""Contrato de procedencia para aprendizados gerados durante uma conversa."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, List


TIPOS_DURAVEIS = {
    "apelido", "correcao", "identidade", "permissao", "preferencia", "regra", "rotina"
}
_STOPWORDS = {
    "a", "ao", "as", "com", "como", "da", "das", "de", "do", "dos", "e", "em",
    "essa", "esse", "eu", "isso", "me", "meu", "minha", "na", "nao", "no", "o",
    "os", "para", "por", "que", "se", "ser", "sou", "um", "uma",
}
_SINAIS_EXPLICITOS = re.compile(
    r"\b(?:meu nome (?:e|eh)|me chama de|eu (?:gosto|amo|adoro|odeio|prefiro)|"
    r"nao gosto|lembra(?: de)? que|guarda(?: isso| que)?|anota(?: que)?|"
    r"quando eu|pode sempre|nao (?:abra|faca|toque|use)|na verdade|"
    r"corrigindo|nao e .+ e|isso significa)\b",
    re.IGNORECASE,
)


def normalizar_texto(texto: Any) -> str:
    bruto = unicodedata.normalize("NFD", str(texto or "").casefold())
    bruto = "".join(ch for ch in bruto if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", bruto)).strip()


def _tokens(texto: Any) -> set[str]:
    return {
        token for token in normalizar_texto(texto).split()
        if len(token) >= 3 and token not in _STOPWORDS
    }


def _texto_item(item: Any) -> str:
    if not isinstance(item, dict):
        return str(item or "").strip()
    return " ".join(
        str(item.get(chave) or "").strip()
        for chave in ("gatilho", "valor", "regra", "texto", "descricao")
        if str(item.get(chave) or "").strip()
    )


def _tipo_item(item: Any) -> str:
    if not isinstance(item, dict):
        return "regra"
    return normalizar_texto(item.get("tipo") or "regra").replace(" ", "_") or "regra"


def usuario_sustenta_aprendizado(texto_usuario: str, item: Any) -> bool:
    """Exige evidencia na fala atual; a saida criativa da IA nunca basta sozinha."""
    usuario = normalizar_texto(texto_usuario)
    memoria = normalizar_texto(_texto_item(item))
    if not usuario or not memoria:
        return False

    tipo = _tipo_item(item)
    tokens_usuario = _tokens(usuario)
    tokens_memoria = _tokens(memoria)
    compartilhados = tokens_usuario & tokens_memoria
    cobertura = len(compartilhados) / max(1, min(len(tokens_usuario), len(tokens_memoria)))
    sinal_explicito = bool(_SINAIS_EXPLICITOS.search(usuario))

    if tipo in {"preferencia", "identidade", "apelido"}:
        return bool(compartilhados) and (sinal_explicito or cobertura >= 0.6)
    if tipo in TIPOS_DURAVEIS:
        return sinal_explicito and bool(compartilhados)
    return sinal_explicito and cobertura >= 0.5


def preparar_aprendizados_confirmados(
    aprendizados: Iterable[Any], texto_usuario: str
) -> List[Dict[str, Any]]:
    """Converte apenas ensinamentos sustentados pelo usuario para o contrato duravel."""
    confirmados: List[Dict[str, Any]] = []
    evidencia = re.sub(r"\s+", " ", str(texto_usuario or "")).strip()[:500]
    for item in aprendizados or []:
        if not usuario_sustenta_aprendizado(evidencia, item):
            continue
        if isinstance(item, dict):
            memoria = dict(item)
        else:
            texto = str(item or "").strip()
            memoria = {"tipo": "regra", "gatilho": texto[:140], "regra": texto}
        memoria.update({
            "origem": "usuario",
            "evidencia": evidencia,
            "status": "ativo",
            "confirmado_usuario": True,
        })
        try:
            memoria["confianca"] = max(0.9, min(1.0, float(memoria.get("confianca") or 0.94)))
        except Exception:
            memoria["confianca"] = 0.94
        confirmados.append(memoria)
    return confirmados

