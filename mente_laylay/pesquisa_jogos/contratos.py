"""Contrato entre leitura visual, pesquisa e síntese da mente única."""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Mapping


MARCADOR_ITEM = "DADOS_ITEM_JSON:"


def _normalizar_chave(valor: Any) -> str:
    base = unicodedata.normalize("NFKD", str(valor or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", base).strip()


def _mecanica_atributo(atributo: str) -> str:
    texto = _texto(atributo, 180)
    normal = _normalizar_chave(texto)
    regras = (
        (r"movement speed|velocidade de movimento", "Movement Speed"),
        (r"fire resistance|resistencia a fogo", "Fire Resistance"),
        (r"cold resistance|resistencia a gelo|resistencia ao frio", "Cold Resistance"),
        (r"lightning resistance|resistencia eletrica|resistencia a raio", "Lightning Resistance"),
        (r"chaos resistance|resistencia a caos", "Chaos Resistance"),
        (r"maximum life|vida maxima", "Life"),
        (r"maximum mana|mana maxima", "Mana"),
        (r"evasion|evasao", "Evasion"),
        (r"energy shield|escudo de energia", "Energy Shield"),
        (r"armour|armor|armadura", "Armour"),
        (r"intelligence|inteligencia", "Intelligence"),
        (r"dexterity|destreza", "Dexterity"),
        (r"strength|forca", "Strength"),
        (r"critical|critico", "Critical Strike"),
        (r"attack speed|velocidade de ataque", "Attack Speed"),
        (r"cast speed|velocidade de conjuracao", "Cast Speed"),
    )
    for padrao, termo in regras:
        if re.search(padrao, normal):
            return termo
    limpo = re.sub(r"\b\d+(?:[.,]\d+)?\b|[%+\-]", " ", texto)
    limpo = re.sub(
        r"(?i)\b(?:increased|reduced|more|less|adicional|aumentad[ao]s?|"
        r"reduzid[ao]s?|ganha|concede|de|da|do|para|ao|a)\b",
        " ", limpo,
    )
    return re.sub(r"\s+", " ", limpo).strip(" ,.;:")[:80]


def planejar_pesquisa_item(item: Mapping[str, Any] | None) -> dict[str, Any]:
    """Escolhe consultas que correspondem ao tipo real de evidência do item."""
    dados = normalizar_item_visual(item)
    raridade = _normalizar_chave(dados.get("raridade"))
    if raridade in {"unique", "unico", "unica"}:
        estrategia = "item_unico"
    elif raridade in {"rare", "raro", "rara", "magic", "magico", "magica"}:
        estrategia = "base_e_modificadores"
    elif raridade in {"normal", "common", "comum"}:
        estrategia = "item_base"
    else:
        estrategia = "identidade_incerta"

    consultas: list[dict[str, Any]] = []

    def adicionar(termo: Any, tipo: str, prioridade: int) -> None:
        valor = _texto(termo, 100)
        if len(valor) < 2:
            return
        chave = _normalizar_chave(valor)
        if any(_normalizar_chave(item["termo"]) == chave for item in consultas):
            return
        consultas.append({"termo": valor, "tipo": tipo, "prioridade": prioridade})

    if estrategia == "item_unico":
        adicionar(dados.get("nome"), "nome_unico", 100)
        adicionar(dados.get("base"), "base", 80)
    elif estrategia == "base_e_modificadores":
        # O nome de raro/mágico costuma ser procedural e não é evidência pesquisável.
        adicionar(dados.get("base"), "base", 100)
        adicionar(dados.get("categoria"), "categoria", 55)
    elif estrategia == "item_base":
        adicionar(dados.get("base") or dados.get("nome"), "base", 100)
        adicionar(dados.get("categoria"), "categoria", 50)
    else:
        adicionar(dados.get("base"), "base_candidata", 90)
        adicionar(dados.get("nome"), "nome_candidato", 70)
        adicionar(dados.get("categoria"), "categoria", 45)

    # O modelo visual pode fornecer o nome inglês da base quando a interface
    # está traduzida. Ele é um alias, nunca prova do nome exato de um raro.
    for termo in dados.get("termos_pesquisa") or []:
        if (
            estrategia == "base_e_modificadores"
            and _normalizar_chave(termo) == _normalizar_chave(dados.get("nome"))
        ):
            continue
        adicionar(termo, "alias_visual", 85 if estrategia == "base_e_modificadores" else 75)

    for atributo in dados.get("atributos") or []:
        adicionar(_mecanica_atributo(atributo), "mecanica", 65)
    consultas.sort(key=lambda item: int(item.get("prioridade") or 0), reverse=True)
    return {
        "estrategia": estrategia,
        "consultas": consultas[:5],
        "nome_procedural_ignorado": bool(
            estrategia == "base_e_modificadores" and dados.get("nome")
        ),
    }


def _texto(valor: Any, limite: int) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()[:limite]


def normalizar_item_visual(item: Mapping[str, Any] | None) -> dict[str, Any]:
    dados = dict(item or {})
    try:
        confianca = max(0.0, min(1.0, float(dados.get("confianca") or 0.0)))
    except (TypeError, ValueError):
        confianca = 0.0
    try:
        nivel = int(dados.get("nivel_item")) if dados.get("nivel_item") is not None else None
    except (TypeError, ValueError):
        nivel = None
    atributos = [
        _texto(valor, 180) for valor in list(dados.get("atributos") or [])[:12]
        if _texto(valor, 180)
    ]
    termos = [
        _texto(valor, 100) for valor in list(dados.get("termos_pesquisa") or [])[:5]
        if _texto(valor, 100)
    ]
    item_limpo = {
        "nome": _texto(dados.get("nome"), 120),
        "base": _texto(dados.get("base"), 120),
        "categoria": _texto(dados.get("categoria"), 60),
        "raridade": _texto(dados.get("raridade"), 40),
        "nivel_item": nivel,
        "atributos": atributos,
        "termos_pesquisa": list(dict.fromkeys(termos)),
        "confianca": round(confianca, 3),
        "slot": _texto(dados.get("slot"), 60),
        "estado": _texto(dados.get("estado"), 40),
        "equipado": bool(dados.get("equipado")),
    }
    if not item_limpo["termos_pesquisa"]:
        item_limpo["termos_pesquisa"] = list(dict.fromkeys(filter(None, (
            item_limpo["base"], item_limpo["nome"], item_limpo["categoria"],
        ))))
    return item_limpo


def extrair_item_da_resposta_visual(resposta: str) -> tuple[str, dict[str, Any]]:
    """Remove o bloco técnico da fala e devolve somente JSON estritamente válido."""
    original = str(resposta or "").strip()
    marcador = re.search(re.escape(MARCADOR_ITEM), original, flags=re.IGNORECASE)
    if not marcador:
        return original, {}
    # O marcador é um limite de confiança: tudo depois dele é metadado, mesmo
    # quando o modelo truncou ou quebrou o JSON. Nunca pronunciamos essa cauda.
    fala = original[:marcador.start()].rstrip(" \t\r\n,;:-")
    cauda = original[marcador.end():].lstrip()
    try:
        bruto, _fim = json.JSONDecoder().raw_decode(cauda)
    except (TypeError, ValueError, json.JSONDecodeError):
        return fala, {}
    if not isinstance(bruto, dict):
        return fala, {}
    return fala, normalizar_item_visual(bruto)
