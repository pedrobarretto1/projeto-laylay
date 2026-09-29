"""Veto textual unilateral para fronteiras didáticas, sem parser ou LLM.

Ausência de veto não é prova de objeto composto. A função apenas reconhece
um padrão explícito que torna insegura uma prévia de agrupamento anterior.
"""

from __future__ import annotations

import hashlib
import re
from functools import lru_cache
from pathlib import Path
from typing import Mapping


_ARTIGOS = frozenset({"o", "a", "os", "as", "um", "uma", "uns", "umas"})
_PALAVRAS = re.compile(r"[^\W\d_]+", re.UNICODE)
_FLEXOES_PLURAIS = (
    "arem", "erem", "irem", "aram", "eram", "iram",
    "avam", "iam", "assem", "essem", "issem",
)
_SUJEITO_COMPOSTO_CURTO = re.compile(
    r"(?:o|a|os|as) [^\W\d_]+ e (?:o|a|os|as) [^\W\d_]+ "
    r"(?P<verbo>[^\W\d_]+)",
    re.IGNORECASE,
)
_SUJEITO_SIMPLES_CURTO = re.compile(
    r"(?P<artigo>o|a|os|as) [^\W\d_]+ (?P<verbo>[^\W\d_]+)",
    re.IGNORECASE,
)
_CAMINHO_INDICE_MORFOLOGICO = (
    Path(__file__).resolve().parent / "dados" /
    "portilexicon_futuro_subjuntivo_3p.tsv"
)
_SHA256_INDICE_MORFOLOGICO = (
    "a9a48993a3cfc8b2f957cf1a1d2315a5401e9b1d726ffeba08df7df00c6f35d6"
)


@lru_cache(maxsize=2)
def _carregar_indice_morfologico(caminho: Path) -> dict[str, str] | None:
    """Índice derivado e congelado; ausência/corrupção não vira evidência."""
    try:
        conteudo = caminho.read_bytes()
    except OSError:
        return None
    if hashlib.sha256(conteudo).hexdigest() != _SHA256_INDICE_MORFOLOGICO:
        return None
    formas: dict[str, str] = {}
    for linha in conteudo.decode("utf-8").splitlines():
        if linha.startswith("#"):
            continue
        colunas = linha.split("\t")
        if (len(colunas) != 2 or not colunas[0].isalpha()
                or colunas[1] not in {"S", "P", "PS"}
                or colunas[0] in formas):
            return None
        formas[colunas[0]] = colunas[1]
    return formas if len(formas) >= 10000 else None


def _trecho_literal(fonte: str, candidato: Mapping[str, object]) -> bool:
    inicio = candidato.get("inicio")
    fim = candidato.get("fim")
    citacao = candidato.get("citacao")
    return (type(inicio) is int and type(fim) is int
            and isinstance(citacao, str)
            and 0 <= inicio < fim <= len(fonte)
            and fonte[inicio:fim] == citacao)


def verificar_sujeito_composto_superficial(
    fonte: str, anterior: Mapping[str, object],
    meio: Mapping[str, object], seguinte: Mapping[str, object],
) -> dict[str, object]:
    """Veta só artigo + possível predicado plural na condição seguinte."""
    base = {"aprovado_para_producao": False, "autoriza_efeito": False}
    if (not isinstance(fonte, str)
            or not all(isinstance(item, Mapping) and _trecho_literal(fonte, item)
                       for item in (anterior, meio, seguinte))
            or not anterior["fim"] < meio["inicio"] < meio["fim"]
            < seguinte["inicio"]):
        return {**base, "estado": "entrada_invalida"}
    palavras_meio = _PALAVRAS.findall(meio["citacao"].casefold())
    palavras_seguinte = _PALAVRAS.findall(seguinte["citacao"].casefold())
    if (len(palavras_meio) >= 2 and palavras_meio[0] in _ARTIGOS
            and len(palavras_seguinte) >= 3
            and palavras_seguinte[0] in _ARTIGOS
            and any(len(palavra) >= 5
                    and palavra.endswith(_FLEXOES_PLURAIS)
                    for palavra in palavras_seguinte[2:])):
        return {**base, "estado": "sujeito_composto_possivel"}
    return {**base, "estado": "sem_veto_superficial"}


def sinal_plural_sujeito_composto(trecho: str) -> dict[str, object]:
    """Reconhece só dois SNs curtos e marcador verbal plural explícito.

    É uma contraprova superficial de uma alegação de erro de número, não
    validação de verbo, sintaxe completa, semântica ou leitura escolhida.
    """
    analise = conferir_numero_condicao_curta(trecho)
    base = {"aprovado_para_producao": False, "autoriza_efeito": False}
    if (analise["estado"] == "numero_convergente"
            and analise["tipo_sujeito"] == "composto"
            and analise["numero_verbo"] == "P"):
        return {**base, "estado": "indicio_plural_explicito",
                "marcador_verbal": analise["marcador_verbal"]}
    return {**base, "estado": "sem_sinal_plural_confiavel"}


def conferir_numero_condicao_curta(trecho: str) -> dict[str, object]:
    """Compara só número superficial de sujeito curto e verbo no léxico.

    Não autentica a análise sintática, o sentido ou a forma como um todo.
    """
    base = {"aprovado_para_producao": False, "autoriza_efeito": False}
    if not isinstance(trecho, str) or len(trecho) > 160:
        return {**base, "estado": "sem_analise"}
    composto = _SUJEITO_COMPOSTO_CURTO.fullmatch(trecho)
    simples = None if composto else _SUJEITO_SIMPLES_CURTO.fullmatch(trecho)
    if composto is None and simples is None:
        return {**base, "estado": "sem_analise"}
    indice = _carregar_indice_morfologico(_CAMINHO_INDICE_MORFOLOGICO)
    if indice is None:
        return {**base, "estado": "recurso_morfologico_indisponivel"}
    correspondencia = composto or simples
    assert correspondencia is not None
    verbo = correspondencia.group("verbo")
    numero_verbo = indice.get(verbo.casefold())
    if numero_verbo not in {"S", "P"}:
        return {**base, "estado": "sem_analise"}
    numero_sujeito = ("P" if composto or simples.group("artigo").casefold()
                      in {"os", "as"} else "S")
    return {**base, "estado": ("numero_convergente"
                               if numero_verbo == numero_sujeito
                               else "numero_divergente"),
            "tipo_sujeito": "composto" if composto else "simples",
            "numero_sujeito": numero_sujeito,
            "numero_verbo": numero_verbo,
            "marcador_verbal": verbo,
            "origem_morfologia": "PortiLexicon-UD"}
