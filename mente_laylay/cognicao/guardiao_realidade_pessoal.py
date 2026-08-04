"""Detecta experiências pessoais impossíveis sem escrever a fala da Laylay."""

from __future__ import annotations

import re


_EXPERIENCIA_FISICA = re.compile(
    r"\b(?:eu\s+)?(?:t[oô]|estou|fico|fiquei)\s+"
    r"(?:comendo|bebendo|fumando|cozinhando|guardando)\b|"
    r"\b(?:eu\s+)?(?:t[oô]|estou)\s+(?:aqui|por\s+aqui)\b"
    r"[^.!?]{0,80}\b(?:s[oó]\s+)?"
    r"(?:comendo|bebendo|fumando|cozinhando|guardando)\b|"
    r"\beu\s+(?:comi|bebi|fumei|cozinhei|guardei|recebi)\b|"
    r"\beu\s+(?:j[aá]\s+)?fiz\s+(?:um|uma)\s+"
    r"(?:bolo|biscoito|comida|receita|caf[eé]|almo[cç]o|jantar)\b|"
    r"\beu\s+fui\s+(?:ao|a|na|no|pra|para\s+(?:a|o))\b",
    re.IGNORECASE,
)
_OBJETO_FISICO_RECEBIDO = re.compile(
    r"\b(?:voc[eê]|pedro)\s+(?:me\s+)?(?:deu|trouxe|entregou)\b|"
    r"\bque\s+(?:voc[eê]|pedro)\s+me\s+deu\b",
    re.IGNORECASE,
)
_PASSADO_COMPARTILHADO_FABRICADO = re.compile(
    r"\b(?:a gente|n[oó]s)\s+(?:foi|fomos|comeu|comemos|bebeu|bebemos|fumou|fumamos)\b|"
    r"\bdaquela\s+vez\s+que\s+(?:voc[eê]|a\s+gente)\b|"
    r"\b(?:voc[eê]|tu)\s+(?:disse|falou|riu)\b[^.!?]{0,180}"
    r"\beu\s+(?:disse|falei|respondi)\b",
    re.IGNORECASE,
)
_CORPO_OU_SENTIDOS_INVENTADOS = re.compile(
    r"\bmeu\s+(?:sistema\s+digestivo|est[oô]mago|paladar|corpo|nariz|boca)\b|"
    r"\b(?:eu\s+)?(?:t[oô]|estou)\s+com\s+(?:o\s+)?corpo\b|"
    r"\b(?:eu\s+)?(?:t[oô]|estou|fico|fiquei)\s+"
    r"(?:com\s+(?:fome|sede)|respirando|saboreando|mastigando|sentindo\s+o\s+cheiro|"
    r"com\s+vontade\s+de\s+(?:comer|beber|provar|experimentar))\b|"
    r"\b(?:eu\s+)?(?:t[oô]|estou)\s+(?:morrendo|quase\s+morrendo)\s+de\s+"
    r"(?:fome|sede|sono)\b|"
    r"\bme\s+(?:matando|deixando)\s+de\s+(?:fome|sede)\b|"
    r"\beu\s+(?:j[aá]\s+)?(?:vi|provei|experimentei|saboreei|cheirei)\b|"
    r"\bme\s+deix(?:a|ou|aria)\s+com\s+(?:os\s+)?olhos\b|"
    r"\bmeus?\s+olhos\b",
    re.IGNORECASE,
)
_RELACAO_PESSOAL_INVENTADA = re.compile(
    r"\b(?:meu|minha)\s+(?:irm[aã]o|irm[aã]|pai|m[aã]e|namorad[oa]|"
    r"marido|esposa|primo|prima|tio|tia|av[oó])\b",
    re.IGNORECASE,
)
_ACAO_FISICA_FUTURA = re.compile(
    r"\bse\s+(?:um\s+dia\s+)?eu\s+(?:fizer|cozinhar|assar|preparar|servir)\b|"
    r"\b(?:eu\s+)?(?:vou|posso)\s+(?:te\s+)?(?:fazer|cozinhar|assar|preparar|servir|"
    r"levar|trazer)\b[^.!?]{0,100}\b(?:pizza|bolo|caf[eé]|comida|receita|lanche|jantar|"
    r"almo[cç]o|queijo|p[aã]o\s+de\s+queijo)\b|"
    r"\beu\s+te\s+(?:fa[cç]o|sirvo|levo|trago)\b[^.!?]{0,100}\b"
    r"(?:pizza|bolo|caf[eé]|comida|lanche|queijo)\b",
    re.IGNORECASE,
)


def detectar_experiencia_pessoal_inventada(fala: str) -> list[str]:
    """Retorna categorias objetivas; não decide estilo nem cria resposta."""
    texto = re.sub(r"\s+", " ", str(fala or "")).strip()
    problemas: list[str] = []
    if _EXPERIENCIA_FISICA.search(texto):
        problemas.append("experiencia_fisica_inventada")
    if _OBJETO_FISICO_RECEBIDO.search(texto):
        problemas.append("objeto_fisico_recebido_inventado")
    if _PASSADO_COMPARTILHADO_FABRICADO.search(texto):
        problemas.append("passado_compartilhado_inventado")
    if _CORPO_OU_SENTIDOS_INVENTADOS.search(texto):
        problemas.append("corpo_ou_sentidos_inventados")
    if _ACAO_FISICA_FUTURA.search(texto):
        problemas.append("capacidade_fisica_futura_inventada")
    if _RELACAO_PESSOAL_INVENTADA.search(texto):
        problemas.append("relacao_pessoal_inventada")
    return problemas


def remover_trechos_de_realidade_inventada(fala: str) -> str:
    """Fallback conservador quando a reescrita da LLM também falha."""
    texto = re.sub(r"\s+", " ", str(fala or "")).strip()
    if not texto:
        return ""
    partes = [
        parte.strip()
        for parte in re.split(r"(?<=[.!?…])\s+", texto)
        if parte.strip()
    ]
    mantidas = [
        parte for parte in partes
        if not detectar_experiencia_pessoal_inventada(parte)
    ]
    return " ".join(mantidas).strip()
