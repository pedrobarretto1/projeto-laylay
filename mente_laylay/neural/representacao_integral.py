"""Representação experimental v1, isolada de treino e configuração do runtime.

Preserva texto integral em um canal separado dos indicadores estruturais.
Não interpreta intenções, não resolve referentes e não concede autoridade.
Preservar a entrada não garante que um vocabulário ajustado retenha tudo:
OOV, ponderação e acurácia precisam de avaliação posterior.
"""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion

from .modelo import enriquecer_texto_estrutura_pontuacao


def preservar_texto_integral_v1(texto: str) -> str:
    """Valida sem truncar, remover acentos, pontuação ou espaços do original."""
    if not isinstance(texto, str):
        raise TypeError("representação integral exige texto str")
    if not texto.strip():
        raise ValueError("representação integral exige texto não vazio")
    return texto


def extrair_estrutura_v1(texto: str) -> str:
    """Reutiliza indicadores existentes sem colocá-los no canal lexical."""
    return enriquecer_texto_estrutura_pontuacao(preservar_texto_integral_v1(texto))


def representar_texto_integral_v1(texto: str) -> dict[str, str]:
    """Expõe os dois canais para inspeção antes de qualquer ajuste estatístico."""
    return {
        "texto_integral": preservar_texto_integral_v1(texto),
        "estrutura": extrair_estrutura_v1(texto),
    }


def criar_extrator_texto_integral_v1() -> FeatureUnion:
    """Cria extrator NÃO ajustado; não carrega modelos ou executa fit.

N-gramas preservam relações locais, não uma compreensão global da sequência.
Os canais separados evitam confundir palavras literais com metadados.
"""
    return FeatureUnion([
        ("palavras_integrais", TfidfVectorizer(
            preprocessor=preservar_texto_integral_v1,
            lowercase=False, strip_accents=None,
            token_pattern=r"(?u)\b\w+\b", ngram_range=(1, 2),
        )),
        ("caracteres_integrais", TfidfVectorizer(
            preprocessor=preservar_texto_integral_v1,
            lowercase=False, strip_accents=None,
            analyzer="char", ngram_range=(1, 5),
        )),
        ("estrutura", TfidfVectorizer(
            preprocessor=extrair_estrutura_v1,
            lowercase=False, ngram_range=(1, 1),
        )),
    ])
