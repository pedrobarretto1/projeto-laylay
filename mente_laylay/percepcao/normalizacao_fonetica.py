"""Normalização fonética conservadora para entradas vindas do microfone."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Iterable, Mapping


def normalizar_fonetico(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"[^a-z0-9\s_-]", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def chave_fonetica(texto: str) -> str:
    """Chave leve para português e nomes estrangeiros; não decide sozinha."""
    t = normalizar_fonetico(texto).replace(" ", "")
    trocas = (
        ("ph", "f"), ("th", "t"), ("sh", "x"), ("ch", "x"),
        ("lh", "li"), ("nh", "ni"), ("y", "i"), ("w", "u"),
        ("qu", "k"), ("ck", "k"), ("c", "k"), ("q", "k"),
        ("z", "s"), ("ge", "je"), ("gi", "ji"),
    )
    for origem, destino in trocas:
        t = t.replace(origem, destino)
    t = re.sub(r"(.)\1+", r"\1", t)
    return t


def extrair_ensino_pronuncia(texto: str) -> tuple[str, str] | None:
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip(" .!?\"'")
    padroes = (
        r"^(?:quando eu falar|quando eu disser)\s+(.+?)\s+(?:quero dizer|significa|e|é)\s+(.+)$",
        r"^(?:na minha voz|na minha pronuncia|na minha pronúncia)\s+(.+?)\s+(?:quer dizer|significa|e|é)\s+(.+)$",
    )
    for padrao in padroes:
        achou = re.match(padrao, bruto, flags=re.IGNORECASE)
        if not achou:
            continue
        ouvido, correto = (parte.strip(" .!?\"'") for parte in achou.groups())
        if (
            ouvido and correto and normalizar_fonetico(ouvido) != normalizar_fonetico(correto)
            and len(ouvido.split()) <= 5 and len(correto.split()) <= 5
        ):
            return ouvido, correto
    return None


def corrigir_entrada_fonetica(
    texto: str,
    *,
    entidades: Iterable[str] = (),
    pronuncias: Mapping[str, str] | None = None,
    limiar: float = 0.84,
) -> tuple[str, list[dict[str, str | float]]]:
    """Corrige aliases confirmados e aproxima apenas entidades conhecidas."""
    resultado = re.sub(r"\s+", " ", str(texto or "")).strip()
    alteracoes: list[dict[str, str | float]] = []
    if not resultado:
        return resultado, alteracoes

    for ouvido, correto in sorted(dict(pronuncias or {}).items(), key=lambda item: len(item[0]), reverse=True):
        alias = normalizar_fonetico(ouvido)
        if not alias or not str(correto or "").strip():
            continue
        padrao = rf"(?<!\w){re.escape(alias)}(?!\w)"
        normalizado = normalizar_fonetico(resultado)
        if re.search(padrao, normalizado):
            resultado = re.sub(padrao, str(correto).strip(), normalizado, flags=re.IGNORECASE)
            alteracoes.append({"original": ouvido, "corrigido": str(correto), "motivo": "pronuncia_aprendida", "score": 1.0})

    tokens = resultado.split()
    entidades_limpas = []
    for entidade in entidades or ():
        exibicao = re.sub(r"\s+", " ", str(entidade or "")).strip()
        norm = normalizar_fonetico(exibicao)
        if len(norm) >= 4 and norm not in {item[1] for item in entidades_limpas}:
            entidades_limpas.append((exibicao, norm))

    melhor: tuple[float, int, int, str, str] | None = None
    for inicio in range(len(tokens)):
        for tamanho in range(1, min(4, len(tokens) - inicio) + 1):
            trecho = " ".join(tokens[inicio:inicio + tamanho])
            trecho_norm = normalizar_fonetico(trecho)
            if len(trecho_norm) < 4:
                continue
            for exibicao, entidade_norm in entidades_limpas:
                if trecho_norm == entidade_norm:
                    continue
                score_texto = SequenceMatcher(None, trecho_norm, entidade_norm).ratio()
                score_fonetico = SequenceMatcher(
                    None, chave_fonetica(trecho_norm), chave_fonetica(entidade_norm)
                ).ratio()
                score = max(score_texto, score_fonetico)
                # Comprimentos muito diferentes são o principal sinal de uma
                # aproximação perigosa em frases comuns.
                proporcao = min(len(trecho_norm), len(entidade_norm)) / max(len(trecho_norm), len(entidade_norm))
                if score >= limiar and proporcao >= 0.72:
                    candidato = (score, inicio, tamanho, exibicao, trecho)
                    if melhor is None or candidato[0] > melhor[0]:
                        melhor = candidato
    if melhor is not None:
        score, inicio, tamanho, exibicao, trecho = melhor
        tokens[inicio:inicio + tamanho] = [exibicao]
        resultado = " ".join(tokens)
        alteracoes.append({
            "original": trecho, "corrigido": exibicao,
            "motivo": "entidade_conhecida", "score": round(score, 3),
        })
    return resultado.strip(), alteracoes

