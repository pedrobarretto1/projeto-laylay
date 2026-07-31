"""Contrato estruturado da observação ambiental no modo jogo."""

from __future__ import annotations

import json
import re
from typing import Any

from mente_laylay.personalidade.higiene_fala import (
    remover_fragmento_final_incompleto,
)


MARCADOR_PRESENCA = "PRESENCA_JOGO_JSON:"


def _normalizar_evidencia(texto: str) -> str:
    base = str(texto or "").casefold()
    base = re.sub(r"[^a-z0-9à-ÿ]+", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def _remover_nome_musical_sem_evidencia(
    fala: str,
    evidencias: list[str],
) -> str:
    """Impede que a visão transforme um nome raro em artista conhecido.

    A fala continua livre, mas um nome ligado a música ou playlist só
    sobrevive quando a lista estruturada de evidências repete literalmente o
    que foi lido. Sem esse apoio, preservamos o comentário e retiramos apenas
    a atribuição nominal insegura.
    """
    texto = str(fala or "").strip()
    if not re.search(r"\b(?:playlist|m[uú]sica|faixa|som)\b", texto, re.I):
        return texto
    evidencias_literais = [
        item for item in evidencias
        if re.search(
            r"\b(?:texto\s+exato(?:\s+vis[ií]vel)?|nome\s+leg[ií]vel|artista\s+leg[ií]vel)\b",
            _normalizar_evidencia(item),
        )
    ]
    base_evidencias = _normalizar_evidencia(" ".join(evidencias_literais))
    padrao = re.compile(
        r"(?P<prefixo>\b(?:playlist|m[uú]sica|faixa|som)\b[^.!?]{0,70}?)"
        r"(?P<atribuicao>\s+(?:do|da|de|por)\s+"
        r"(?P<nome>[A-ZÀ-Ý][\wÀ-ÿ'’-]*"
        r"(?:\s+(?:e|&|[A-ZÀ-Ý][\wÀ-ÿ'’-]*)){0,6}))"
    )

    def substituir(achado: re.Match[str]) -> str:
        nome = _normalizar_evidencia(achado.group("nome"))
        if nome and nome in base_evidencias:
            return achado.group(0)
        return achado.group("prefixo").rstrip()

    return re.sub(r"\s+([.!?,;:])", r"\1", padrao.sub(substituir, texto)).strip()


def extrair_presenca_visual(resposta: str) -> tuple[str, dict[str, Any]]:
    texto = str(resposta or "").strip()
    padrao = re.compile(r"(?:^|\n)\s*PRESENCA_JOGO_JSON:\s*(\{.*?\})\s*$", re.I | re.S)
    achado = padrao.search(texto)
    if not achado:
        return texto, {}
    fala_natural = texto[:achado.start()].strip()
    try:
        dados = json.loads(achado.group(1))
    except (TypeError, ValueError, json.JSONDecodeError):
        return fala_natural, {}
    if not isinstance(dados, dict):
        return fala_natural, {}
    categoria = str(dados.get("categoria") or "nenhuma").strip().casefold()
    if categoria not in {
        "motivacao", "celebracao", "dica", "musica",
        "companhia", "curiosidade", "nenhuma",
    }:
        categoria = "nenhuma"
    evidencias = dados.get("evidencias")
    if not isinstance(evidencias, list):
        evidencias = []
    try:
        confianca = max(0.0, min(1.0, float(dados.get("confianca") or 0.0)))
    except (TypeError, ValueError):
        confianca = 0.0
    evidencias_limpas = [
        str(item).strip()[:180] for item in evidencias if str(item).strip()
    ][:5]
    fala_evento = remover_fragmento_final_incompleto(
        str(dados.get("fala") or fala_natural).strip()[:360]
    )
    fala_evento = _remover_nome_musical_sem_evidencia(
        fala_evento, evidencias_limpas,
    )
    evento = {
        "relevante": bool(dados.get("relevante")) and categoria != "nenhuma",
        "categoria": categoria,
        "fala": fala_evento,
        "motivo": str(dados.get("motivo") or "").strip()[:180],
        "evidencias": evidencias_limpas,
        "confianca": confianca,
        "momento_seguro": bool(dados.get("momento_seguro")),
        "clima_musical": str(dados.get("clima_musical") or "").strip().casefold()[:40],
    }
    if not fala_evento:
        evento.update(relevante=False, categoria="nenhuma")
    fala_norm = evento["fala"].casefold()
    observacao_generica = bool(re.search(
        r"momento de pausa|bom momento para respirar|perfeito para uma pausa|"
        r"parado num cantinho|ambiente (?:esta|está) calmo|"
        r"menu (?:esta|está) aberto.{0,80}respirar",
        fala_norm,
    ))
    if evento["categoria"] in {"companhia", "curiosidade"} and observacao_generica:
        evento.update(relevante=False, categoria="nenhuma", fala="")
    return fala_natural, evento
