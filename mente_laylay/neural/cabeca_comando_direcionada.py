"""Adição isolada de command head por intent, sem retreinar o núcleo."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Iterable, Mapping

import joblib

from .modelo import (
    ModeloNeuralComandos,
    REPRESENTACOES_SEMANTICAS,
    _pipeline,
    enriquecer_texto_features_comando,
)


def adicionar_cabeca_comando_direcionada(
    modelo_base: ModeloNeuralComandos,
    exemplos: Iterable[Mapping[str, Any]],
    *,
    intent: str,
    caminho: str | Path | None = None,
    versao: str = "",
    somente_pos_extensao: bool = False,
) -> ModeloNeuralComandos:
    intent_alvo = str(intent or "").strip().upper()
    if not intent_alvo or intent_alvo == "NONE":
        raise ValueError("head direcionado exige intent operacional")
    atributo_heads = (
        "cabecas_comando_extensao_por_intent"
        if somente_pos_extensao
        else "cabecas_comando_por_intent"
    )
    if intent_alvo in (getattr(modelo_base, atributo_heads, {}) or {}):
        raise ValueError(f"head direcionado já existe: {intent_alvo}")
    itens = [dict(x) for x in exemplos]
    aplicaveis = [
        x for x in itens
        if x.get("training_heads") is None
        or "command" in {
            str(v or "").strip().casefold()
            for v in x.get("training_heads", ())
        }
    ]
    dominios = {
        str(x.get("domain") or "").strip().casefold()
        for x in aplicaveis
        if (
            str(x.get("command_head_intent") or "").strip().upper() == intent_alvo
            or (
                not str(x.get("command_head_intent") or "").strip()
                and str(x.get("intent") or "").strip().upper() == intent_alvo
            )
        )
        and str(x.get("domain") or "").strip()
    }
    selecionados = [
        x for x in aplicaveis
        if str(x.get("command_head_intent") or "").strip().upper() == intent_alvo
        or (
            not str(x.get("command_head_intent") or "").strip()
            and str(x.get("intent") or "").strip().upper() == intent_alvo
        )
        or (
            not str(x.get("command_head_intent") or "").strip()
            and not bool(x.get("is_command"))
            and str(x.get("domain") or "").strip().casefold() in dominios
        )
    ]
    textos = [str(x.get("text") or "").strip() for x in selecionados]
    rotulos = [bool(x.get("is_command")) for x in selecionados]
    if not textos or any(not x for x in textos):
        raise ValueError("head direcionado sem exemplos válidos")
    if len(set(rotulos)) < 2:
        raise ValueError("head direcionado exige positivos e negativos")

    rep_base = str(getattr(modelo_base, "representacao", "tfidf") or "tfidf").casefold()
    rep_gate = "tfidf_indicadores" if rep_base in REPRESENTACOES_SEMANTICAS else rep_base
    ngramas = (4, 6) if rep_base in {"tfidf_indicadores", *REPRESENTACOES_SEMANTICAS} else (3, 5)
    estrategia = str(getattr(modelo_base, "estrategia", "logistic") or "logistic").casefold()
    head = _pipeline(
        rotulos,
        estrategia=estrategia,
        representacao=rep_gate,
        preprocessador_indicadores=enriquecer_texto_features_comando,
        ngramas_caracteres=ngramas,
    ).fit(textos, rotulos)
    candidato = copy.copy(modelo_base)
    heads_atualizados = dict(getattr(modelo_base, atributo_heads, {}) or {})
    heads_atualizados[intent_alvo] = head
    setattr(candidato, atributo_heads, heads_atualizados)
    if str(versao or "").strip():
        candidato.versao = str(versao).strip()
    if caminho is not None:
        destino = Path(caminho)
        destino.parent.mkdir(parents=True, exist_ok=True)
        tmp = destino.with_suffix(destino.suffix + ".tmp")
        joblib.dump(candidato, tmp)
        tmp.replace(destino)
    return candidato
