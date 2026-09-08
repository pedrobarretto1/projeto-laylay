"""Representação experimental sem perda: exterior e citações, sem resolver alvo.

Texto exterior não significa instrução; texto citado não significa entidade.
As regiões são observações sintáticas, nunca autorização ou rótulo de negação.
"""

from __future__ import annotations

import json
import re
import unicodedata

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion

from mente_laylay.arquivos.nome_natural import mapear_pares_aspas_globais
from .representacao_escopo_local import extrair_pistas_escopo_local


def representar_regioes_texto(texto: str) -> dict:
    """Particiona em spans contíguos, incluindo espaços, sem normalizar offsets."""
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("texto str não vazio é obrigatório")
    pares = mapear_pares_aspas_globais(texto)
    regioes = []
    cursor = 0
    if pares is not None:
        for inicio, fechamento in sorted(pares.items()):
            if inicio < cursor:  # Par aninhado permanece no conteúdo externo dele.
                continue
            if inicio > cursor:
                regioes.append({"tipo": "exterior", "inicio": cursor, "fim": inicio, "texto": texto[cursor:inicio]})
            fim = fechamento + 1
            regioes.append({"tipo": "citado", "inicio": inicio, "fim": fim, "texto": texto[inicio:fim]})
            cursor = fim
    if cursor < len(texto):
        regioes.append({"tipo": "exterior", "inicio": cursor, "fim": len(texto), "texto": texto[cursor:]})
    assert "".join(r["texto"] for r in regioes) == texto
    return {"texto_original": texto, "aspas_coerentes": pares is not None,
            "regioes": regioes, "autoriza_execucao": False, "resolve_alvo": False}


def extrair_pistas_regioes(texto: str) -> list[str]:
    """Mantém palavras internas, namespace e fronteiras, sem ligar duas citações."""
    leitura = representar_regioes_texto(texto)
    pistas = [json.dumps(["aspas_coerentes", leitura["aspas_coerentes"]])]
    for regiao in leitura["regioes"]:
        tipo = regiao["tipo"]
        conteudo = regiao["texto"][1:-1] if tipo == "citado" else regiao["texto"]
        normal = unicodedata.normalize("NFKD", conteudo.casefold())
        normal = "".join(c for c in normal if not unicodedata.combining(c))
        tokens = re.findall(r"\w+|[^\w\s]", normal)
        pistas.append(json.dumps([tipo, "regiao", "inicio_texto" if regiao["inicio"] == 0 else "interna",
                                  "fim_texto" if regiao["fim"] == len(texto) else "intermediaria"]))
        for n in range(1, min(4, len(tokens)) + 1):
            pistas.append(json.dumps([tipo, "inicio_regiao", tokens[:n]], ensure_ascii=False))
            pistas.append(json.dumps([tipo, "fim_regiao", tokens[-n:]], ensure_ascii=False))
            for i in range(len(tokens) - n + 1):
                pistas.append(json.dumps([tipo, "sequencia", tokens[i:i+n]], ensure_ascii=False))
    return pistas


def criar_extrator_regioes_texto() -> FeatureUnion:
    """Extrator NÃO ajustado. Mantém forma externa e conteúdo citado separados.

    Não injeta os marcadores globais antigos. Usar somente num treino novo,
    nunca como substituição de extrator com coeficientes já ajustados.
    """
    return FeatureUnion([
        ("forma", TfidfVectorizer(analyzer=extrair_pistas_escopo_local)),
        ("conteudo_regional", TfidfVectorizer(analyzer=extrair_pistas_regioes)),
    ])
