"""Contrato estruturado da observação ambiental no modo jogo."""

from __future__ import annotations

import json
import math
import re
from typing import Any

from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
from mente_laylay.personalidade.higiene_fala import (
    remover_fragmento_final_incompleto,
)


MARCADOR_PRESENCA = "PRESENCA_JOGO_JSON:"


def criar_contrato_saida_presenca_visual() -> ContratoSaidaEstruturada:
    """Negocia a estrutura da proposta; a cognição conserva os gates semânticos."""
    categorias = ["motivacao", "celebracao", "dica", "musica",
                  "companhia", "curiosidade", "nenhuma"]
    texto = {"type": "string", "maxLength": 360}
    propriedades_reacao = {
        "foco_evidencia": dict(texto), "trecho_ancora": dict(texto),
        "humor": {"type": "boolean"}, "fala": dict(texto),
    }
    propriedades = {
        "evidencias": {"type": "array", "maxItems": 5,
                       "items": {**texto, "minLength": 1}},
        "foco_evidencia": dict(texto),
        "proposta_reacao": {"anyOf": [
            {"type": "null"},
            {"type": "object", "properties": propriedades_reacao,
             "required": list(propriedades_reacao), "additionalProperties": False},
        ]},
        "relevante": {"type": "boolean"},
        "categoria": {"type": "string", "enum": categorias},
        "fala": dict(texto), "motivo": {"type": "string", "maxLength": 180},
        "confianca": {"type": "number", "minimum": 0, "maximum": 1},
        "momento_seguro": {"type": "boolean"},
        "clima_musical": {"type": "string", "maxLength": 40},
    }

    def validar(dados: dict[str, Any]) -> None:
        if set(dados) != set(propriedades):
            raise ValueError("campos de presença não correspondem ao contrato")
        for chave, limite in (("foco_evidencia", 360), ("fala", 360),
                              ("motivo", 180), ("clima_musical", 40)):
            if not isinstance(dados[chave], str) or len(dados[chave]) > limite:
                raise ValueError("texto de presença inválido")
        if type(dados["relevante"]) is not bool or type(dados["momento_seguro"]) is not bool:
            raise ValueError("flag de presença deve ser booleana")
        if dados["categoria"] not in categorias:
            raise ValueError("categoria de presença inválida")
        confianca = dados["confianca"]
        if (type(confianca) not in (int, float) or not math.isfinite(confianca)
                or not 0 <= confianca <= 1):
            raise ValueError("confiança de presença inválida")
        evidencias = dados["evidencias"]
        if (not isinstance(evidencias, list) or len(evidencias) > 5
                or any(not isinstance(item, str) or not item.strip()
                       or len(item) > 360 for item in evidencias)):
            raise ValueError("lista de evidências inválida")
        reacao = dados["proposta_reacao"]
        if reacao is not None:
            if not isinstance(reacao, dict) or set(reacao) != set(propriedades_reacao):
                raise ValueError("campos de reação não correspondem ao contrato")
            if type(reacao["humor"]) is not bool or any(
                not isinstance(reacao[chave], str) or len(reacao[chave]) > 360
                for chave in ("foco_evidencia", "trecho_ancora", "fala")
            ):
                raise ValueError("estrutura de reação inválida")

    return ContratoSaidaEstruturada(
        nome="presenca_jogo_v1", marcador=MARCADOR_PRESENCA,
        esquema={"type": "object", "properties": propriedades,
                 "required": list(propriedades), "additionalProperties": False},
        validar=validar,
    )


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
        str(item).strip() for item in evidencias if str(item).strip()
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
    if "foco_evidencia" in dados:
        # A cognição confere o vínculo literal; o parser não decide relevância.
        evento["foco_evidencia"] = dados["foco_evidencia"]
    if "proposta_reacao" in dados or categoria in {"companhia", "curiosidade"}:
        # Papel autoral separado dos fatos; validação pertence à cognição.
        evento["proposta_reacao"] = dados.get("proposta_reacao")
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
