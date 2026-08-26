"""Confirma leitura de item sem repetir toda a análise visual."""

from __future__ import annotations

import json
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Mapping

from mente_laylay.pesquisa_jogos.contratos import normalizar_item_visual


def _chave(valor: Any) -> str:
    base = unicodedata.normalize("NFKD", str(valor or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", base).strip()


def _equivalentes(a: Any, b: Any) -> bool:
    primeiro, segundo = _chave(a), _chave(b)
    if not primeiro or not segundo:
        return False
    return primeiro == segundo or SequenceMatcher(None, primeiro, segundo).ratio() >= 0.92


def precisa_confirmar_item(
    item: Mapping[str, Any] | None, *, multiplas_imagens: bool,
) -> bool:
    if not multiplas_imagens:
        return False
    dados = normalizar_item_visual(item)
    confianca = float(dados.get("confianca") or 0.0)
    return bool(
        not dados
        or confianca < 0.78
        or not (dados.get("nome") or dados.get("base"))
        or not dados.get("atributos")
    )


def montar_prompt_confirmacao_item(
    item: Mapping[str, Any] | None, *, jogo: str,
) -> str:
    leitura = normalizar_item_visual(item)
    return (
        f"Jogo confirmado pelo sistema: {str(jogo or 'jogo atual')}. "
        "Esta imagem é somente o recorte nativo do tooltip. Faça uma segunda leitura "
        "literal e independente: não complete letras, números ou atributos por conhecimento "
        "do jogo. Compare visualmente, mas não copie o rascunho quando a imagem discordar. "
        "Responda somente com DADOS_ITEM_JSON: seguido de JSON válido contendo nome, base, "
        "categoria, slot, estado, equipado, raridade, nivel_item, atributos, termos_pesquisa "
        "e confianca. Use vazio ou null no que não estiver legível.\n"
        "Primeira leitura, tratada apenas como candidato não confiável: "
        + json.dumps(leitura, ensure_ascii=False, separators=(",", ":"))
    )


def reconciliar_leituras_item(
    primeira: Mapping[str, Any] | None,
    segunda: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    a, b = normalizar_item_visual(primeira), normalizar_item_visual(segunda)
    if not b.get("nome") and not b.get("base") and not b.get("atributos"):
        return a, {"status": "segunda_leitura_vazia", "conflitos": []}
    if not a.get("nome") and not a.get("base") and not a.get("atributos"):
        recuperado = dict(b)
        recuperado["confianca"] = min(0.52, float(b.get("confianca") or 0.0))
        return normalizar_item_visual(recuperado), {
            "status": "recuperada_por_recorte", "conflitos": [],
        }

    resultado = dict(a)
    conflitos: list[str] = []
    confirmados: list[str] = []
    for campo in ("nome", "base", "categoria", "raridade", "slot", "estado"):
        av, bv = a.get(campo), b.get(campo)
        if av and bv:
            if _equivalentes(av, bv):
                confirmados.append(campo)
            elif campo in {"nome", "base"}:
                conflitos.append(campo)
                resultado[campo] = ""
        elif bv and not av:
            resultado[campo] = bv

    atributos_a = {_chave(valor): valor for valor in a.get("atributos") or [] if _chave(valor)}
    atributos_b = {_chave(valor): valor for valor in b.get("atributos") or [] if _chave(valor)}
    if atributos_a and atributos_b:
        comuns = [atributos_a[chave] for chave in atributos_a.keys() & atributos_b.keys()]
        if comuns:
            resultado["atributos"] = comuns
            confirmados.append("atributos")
        else:
            resultado["atributos"] = []
            conflitos.append("atributos")
    elif atributos_b and not atributos_a:
        resultado["atributos"] = list(atributos_b.values())

    if conflitos:
        resultado["confianca"] = min(0.44, float(a.get("confianca") or 0.0), float(b.get("confianca") or 0.0))
        status = "conflito"
    elif confirmados:
        media = (float(a.get("confianca") or 0.0) + float(b.get("confianca") or 0.0)) / 2
        resultado["confianca"] = min(0.96, max(0.78, media + 0.06))
        status = "confirmada"
    else:
        resultado["confianca"] = min(0.64, float(a.get("confianca") or 0.0))
        status = "parcial"
    return normalizar_item_visual(resultado), {
        "status": status,
        "conflitos": conflitos,
        "confirmados": confirmados,
    }
