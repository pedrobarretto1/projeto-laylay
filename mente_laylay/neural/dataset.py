"""Validação e particionamento dos exemplos linguísticos neurais."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


FONTES_PERMITIDAS = frozenset(
    {
        "NORMAL_COMMAND",
        "REAL_FAILURE",
        "MANUAL_PARAPHRASE",
        "HARD_NEGATIVE",
        "COUNTERFACTUAL",
        "EXPLICIT_CORRECTION",
        "CURATED_RECEIPT",
    }
)
HEADS_TREINO_PERMITIDOS = frozenset(
    {"intent", "intent_gate", "action", "command", "negation"}
)


def validar_exemplo(
    exemplo: Mapping[str, Any],
    *,
    intents_permitidas: Iterable[str],
) -> dict[str, Any]:
    """Valida um exemplo antes que ele possa participar de treino ou avaliação."""
    if not isinstance(exemplo, Mapping):
        raise TypeError("exemplo deve ser um mapeamento")

    texto = " ".join(str(exemplo.get("text") or "").strip().split())
    if not texto:
        raise ValueError("exemplo sem text")
    if len(texto) > 500:
        raise ValueError("text excede 500 caracteres")

    permitidas = {
        str(item or "").strip().upper()
        for item in intents_permitidas
        if str(item or "").strip()
    }
    intent = str(exemplo.get("intent") or "").strip().upper()
    if intent not in permitidas | {"NONE"}:
        raise ValueError(f"intent fora do catálogo: {intent or '<vazia>'}")

    is_command = exemplo.get("is_command")
    negated = exemplo.get("negated")
    if not isinstance(is_command, bool) or not isinstance(negated, bool):
        raise ValueError("is_command e negated devem ser booleanos")
    if intent == "NONE" and is_command:
        raise ValueError("intent NONE não pode ser comando")

    action = str(exemplo.get("action") or "none").strip().casefold()
    family = str(exemplo.get("family") or "manual_sem_familia").strip().casefold()
    grupo_validacao_bruto = exemplo.get("validation_group")
    grupo_validacao = str(grupo_validacao_bruto or "").strip().casefold()
    source = str(exemplo.get("source") or "MANUAL_PARAPHRASE").strip().upper()
    domain = str(exemplo.get("domain") or "geral").strip().casefold()
    heads_brutos = exemplo.get("training_heads")
    heads_treino: list[str] | None = None
    if heads_brutos is not None:
        if not isinstance(heads_brutos, (list, tuple, set, frozenset)):
            raise ValueError("training_heads deve ser uma coleção")
        heads_treino = sorted({
            str(head or "").strip().casefold() for head in heads_brutos
        })
        if not heads_treino or any(
            head not in HEADS_TREINO_PERMITIDOS for head in heads_treino
        ):
            raise ValueError("training_heads contém head vazio ou desconhecido")
    alvo_head_comando_bruto = exemplo.get("command_head_intent")
    alvo_head_comando = str(alvo_head_comando_bruto or "").strip().upper()
    if alvo_head_comando_bruto is not None:
        if alvo_head_comando not in permitidas or alvo_head_comando == "NONE":
            raise ValueError("command_head_intent exige intent operacional do catálogo")
        if heads_treino is None or "command" not in heads_treino:
            raise ValueError(
                "command_head_intent exige o head command no escopo"
            )
    if not action or not family or not domain:
        raise ValueError("action, family e domain não podem ser vazios")
    if grupo_validacao_bruto is not None and not grupo_validacao:
        raise ValueError("validation_group informado não pode ser vazio")
    if source not in FONTES_PERMITIDAS:
        raise ValueError(f"source não confiável: {source}")

    validado = {
        "text": texto,
        "intent": intent,
        "is_command": is_command,
        "negated": negated,
        "action": action,
        "family": family,
        "source": source,
        "domain": domain,
    }
    if grupo_validacao_bruto is not None:
        validado["validation_group"] = grupo_validacao
    if heads_treino is not None:
        validado["training_heads"] = heads_treino
    if alvo_head_comando_bruto is not None:
        validado["command_head_intent"] = alvo_head_comando
    return validado


def separar_dataset_por_familia(
    exemplos: Iterable[Mapping[str, Any]],
    *,
    familias_frozen: Iterable[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Separa famílias inteiras, impedindo paráfrases irmãs de vazar ao teste."""
    congeladas = {
        str(item or "").strip().casefold()
        for item in familias_frozen
        if str(item or "").strip()
    }
    dev: list[dict[str, Any]] = []
    frozen: list[dict[str, Any]] = []
    for exemplo in exemplos:
        item = dict(exemplo)
        destino = frozen if str(item.get("family") or "").casefold() in congeladas else dev
        destino.append(item)
    return dev, frozen


def carregar_jsonl(
    caminho: str | Path,
    *,
    intents_permitidas: Iterable[str],
) -> list[dict[str, Any]]:
    """Carrega JSONL fail-closed: uma linha inválida rejeita o conjunto inteiro."""
    itens: list[dict[str, Any]] = []
    for numero, linha in enumerate(Path(caminho).read_text(encoding="utf-8").splitlines(), 1):
        if not linha.strip():
            continue
        try:
            bruto = json.loads(linha)
            itens.append(validar_exemplo(bruto, intents_permitidas=intents_permitidas))
        except Exception as erro:
            raise ValueError(f"dataset inválido na linha {numero}: {erro}") from erro
    if not itens:
        raise ValueError("dataset vazio")
    return itens


def experiencias_para_dataset(
    registros: Iterable[Mapping[str, Any]],
    *,
    intents_permitidas: Iterable[str],
    dominio_por_intent: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Converte apenas correções fortes; receipts isolados continuam fora do treino."""
    permitidas = {str(item).upper() for item in intents_permitidas}
    dominios = {str(k).upper(): str(v) for k, v in dict(dominio_por_intent or {}).items()}
    exemplos: list[dict[str, Any]] = []
    vistos: set[tuple[str, str]] = set()
    for registro in registros:
        item = dict(registro)
        intent = str(item.get("intent_correta") or "").strip().upper()
        texto = str(item.get("text") or "").strip()
        if (
            item.get("tipo") != "correcao_interpretacao"
            or item.get("apto_treino") is not True
            or float(item.get("label_confidence") or 0.0) < 1.0
            or intent not in permitidas
            or not texto
        ):
            continue
        chave = (" ".join(texto.casefold().split()), intent)
        if chave in vistos:
            continue
        vistos.add(chave)
        params = item.get("params_corretos") if isinstance(item.get("params_corretos"), Mapping) else {}
        exemplo = {
            "text": texto,
            "intent": intent,
            "is_command": True,
            "negated": False,
            "action": str(params.get("acao") or "none").casefold(),
            "family": f"correcao_{str(item.get('id') or len(exemplos)).casefold()}",
            "source": "EXPLICIT_CORRECTION",
            "domain": dominios.get(intent, "geral"),
        }
        exemplos.append(validar_exemplo(exemplo, intents_permitidas=permitidas))
    return exemplos
