"""Contrato dinâmico do inventário observado dentro de cada jogo."""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Mapping


MARCADOR_INVENTARIO = "DADOS_INVENTARIO_JSON:"
MARCADOR_SUGESTAO = "SUGESTAO_PROATIVA_JSON:"


def _texto(valor: Any, limite: int = 120) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()[:limite]


def _chave(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", _texto(valor, 80).casefold())
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")[:60]


def _confianca(valor: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(valor))), 3)
    except (TypeError, ValueError):
        return 0.0


def normalizar_inventario(dados: Mapping[str, Any] | None) -> dict[str, Any]:
    bruto = dict(dados or {})
    esquema: dict[str, dict[str, Any]] = {}
    slots_brutos = bruto.get("slots") or bruto.get("esquema") or []
    if isinstance(slots_brutos, Mapping):
        slots_brutos = [dict(valor or {}, slot=nome) for nome, valor in slots_brutos.items()]
    for entrada in list(slots_brutos or [])[:40]:
        if not isinstance(entrada, Mapping):
            continue
        slot = _chave(entrada.get("slot") or entrada.get("nome"))
        if not slot:
            continue
        try:
            quantidade = max(1, min(8, int(entrada.get("quantidade") or 1)))
        except (TypeError, ValueError):
            quantidade = 1
        esquema[slot] = {
            "nome": _texto(entrada.get("nome") or entrada.get("slot"), 80) or slot,
            "categoria": _chave(entrada.get("categoria")),
            "quantidade": quantidade,
            "confianca": _confianca(entrada.get("confianca")),
        }

    equipados: dict[str, list[dict[str, Any]]] = {}
    equipados_brutos = bruto.get("equipados") or []
    if isinstance(equipados_brutos, Mapping):
        equipados_brutos = [
            {**dict(item or {}), "slot": slot}
            for slot, valor in equipados_brutos.items()
            for item in (valor if isinstance(valor, list) else [valor])
            if isinstance(item, Mapping)
        ]
    for entrada in list(equipados_brutos or [])[:40]:
        if not isinstance(entrada, Mapping):
            continue
        slot = _chave(entrada.get("slot"))
        if not slot:
            continue
        item = {
            "nome": _texto(entrada.get("nome"), 120),
            "categoria": _chave(entrada.get("categoria")),
            "raridade": _texto(entrada.get("raridade"), 40),
            "atributos": [
                _texto(item, 180) for item in list(entrada.get("atributos") or [])[:16]
                if _texto(item, 180)
            ],
            "confianca": _confianca(entrada.get("confianca")),
        }
        equipados.setdefault(slot, []).append(item)
        esquema.setdefault(slot, {
            "nome": slot.replace("_", " "), "categoria": item["categoria"],
            "quantidade": 1, "confianca": item["confianca"],
        })
    return {
        "tela_inventario_ativa": bool(bruto.get("tela_inventario_ativa", True)),
        "personagem": _texto(bruto.get("personagem"), 100) or "padrao",
        "esquema": esquema,
        "equipados": equipados,
        "confianca": _confianca(bruto.get("confianca")),
        "ambiguidades": [
            _texto(item, 180) for item in list(bruto.get("ambiguidades") or [])[:8]
            if _texto(item, 180)
        ],
    }


def normalizar_sugestao(dados: Mapping[str, Any] | None) -> dict[str, Any]:
    bruto = dict(dados or {})
    return {
        "relevante": bool(bruto.get("relevante")),
        "fala": _texto(bruto.get("fala"), 420),
        "motivo": _texto(bruto.get("motivo"), 180),
        "slot": _chave(bruto.get("slot")),
        "item": _texto(bruto.get("item"), 120),
        "prioridade": _chave(bruto.get("prioridade")) or "normal",
        "confianca": _confianca(bruto.get("confianca")),
    }


def _extrair_marcador(texto: str, marcador: str) -> tuple[str, dict[str, Any]]:
    padrao = re.compile(
        rf"(?:^|\n)\s*{re.escape(marcador)}\s*(\{{[^\n]*\}})\s*",
        re.IGNORECASE,
    )
    achado = padrao.search(texto)
    if not achado:
        return texto, {}
    limpo = (texto[:achado.start()] + texto[achado.end():]).strip()
    try:
        dados = json.loads(achado.group(1))
    except (TypeError, ValueError, json.JSONDecodeError):
        return limpo, {}
    return limpo, dict(dados) if isinstance(dados, Mapping) else {}


def extrair_dados_inventario(resposta: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
    fala, sugestao = _extrair_marcador(str(resposta or "").strip(), MARCADOR_SUGESTAO)
    fala, inventario = _extrair_marcador(fala, MARCADOR_INVENTARIO)
    return fala, normalizar_inventario(inventario) if inventario else {}, normalizar_sugestao(sugestao) if sugestao else {}

