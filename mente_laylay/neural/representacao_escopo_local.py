"""Pistas locais ordenadas e tipadas; não classifica escopo nem autoriza ações."""

from __future__ import annotations

import json
import re
import unicodedata

from sklearn.base import clone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline

from mente_laylay.arquivos.nome_natural import mapear_pares_aspas_globais


_TOKEN = re.compile(r"\w+(?:[._/\\-]\w+)*|[^\w\s]", re.UNICODE)


def segmentar_estrutura_local(texto: str) -> dict:
    """Offsets apontam para a entrada original, inclusive acentos e aspas.

    Trecho entre aspas é apenas citação, não prova de filename ou de permissão.
    Aspas incoerentes não ocultam texto. Nomes sem aspas não são adivinhados.
    """
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("texto str não vazio é obrigatório")
    pares = mapear_pares_aspas_globais(texto)
    partes = []
    pos = 0
    while pos < len(texto):
        if pares is not None and pos in pares:
            fim = pares[pos] + 1
            partes.append({"tipo": "citado", "inicio": pos, "fim": fim, "texto": texto[pos:fim]})
            pos = fim
            continue
        token = _TOKEN.match(texto, pos)
        if token is None:
            pos += 1
            continue
        valor = token.group()
        tipo = "numero" if valor.isdecimal() else "palavra" if re.match(r"\w", valor) else "pontuacao"
        partes.append({"tipo": tipo, "inicio": pos, "fim": token.end(), "texto": valor})
        pos = token.end()
    return {"texto_original": texto, "aspas_coerentes": pares is not None, "partes": partes}


def extrair_pistas_escopo_local(texto: str) -> list[str]:
    estrutura = segmentar_estrutura_local(texto)
    tokens = []
    for parte in estrutura["partes"]:
        tipo = parte["tipo"]
        valor = "" if tipo in {"citado", "numero"} else parte["texto"]
        valor = unicodedata.normalize("NFKD", valor.casefold())
        valor = "".join(c for c in valor if not unicodedata.combining(c))
        tokens.append((tipo, valor))
    # JSON evita colisão entre nomes digitados e categorias internas.
    pistas = [json.dumps(["aspas_coerentes", estrutura["aspas_coerentes"]])]
    for n in range(1, min(5, len(tokens)) + 1):
        pistas.append(json.dumps(["inicio", tokens[:n]], ensure_ascii=False))
        pistas.append(json.dumps(["fim", tokens[-n:]], ensure_ascii=False))
        for i in range(len(tokens) - n + 1):
            pistas.append(json.dumps(["sequencia", tokens[i:i+n]], ensure_ascii=False))
    return pistas


def criar_prototipo_escopo_local(cabeca) -> Pipeline:
    """Adição isolada ao extrator lexical; parâmetros antigos ficam intactos."""
    canais = cabeca.named_steps["features"].transformer_list
    if [nome for nome, _ in canais] != ["palavras", "caracteres"]:
        raise ValueError("experimento exige a cabeça lexical de referência")
    return Pipeline([
        ("features", FeatureUnion([
            *((nome, clone(transformador)) for nome, transformador in canais),
            ("escopo_local", TfidfVectorizer(analyzer=extrair_pistas_escopo_local)),
        ])),
        ("classifier", clone(cabeca.named_steps["classifier"])),
    ])
