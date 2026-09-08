"""Experimento: texto lexical separado de dois sinais canônicos de negação.

Não altera funções serializadas dos modelos antigos. A normalização lexical
reproduz o prefixo do extrator antigo; divergência futura aborta o experimento.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.pipeline import FeatureUnion

from .modelo import enriquecer_texto_features


MARCADORES = ("marcador_negacao_explicita", "marcador_negacao_exclusao")


def separar_texto_e_sinais(texto: str) -> tuple[str, tuple[bool, bool]]:
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("texto não vazio é obrigatório")
    base = unicodedata.normalize("NFKD", texto.casefold())
    base = "".join(c for c in base if not unicodedata.combining(c))
    base = re.sub(r"\s+", " ", base).strip()
    enriquecido = enriquecer_texto_features(texto)
    if enriquecido != base and not enriquecido.startswith(base + " "):
        raise ValueError("normalização divergiu do extrator canônico")
    anexados = enriquecido[len(base):].split()
    if any(m not in MARCADORES for m in anexados) or len(anexados) != len(set(anexados)):
        raise ValueError("contrato de marcadores mudou")
    return base, tuple(m in anexados for m in MARCADORES)


def texto_lexical_sem_metadados(texto: str) -> str:
    """Preserva ocorrências literais, removendo só o metadado anexado."""
    return separar_texto_e_sinais(texto)[0]


class SinaisNegacaoAtomicos(TransformerMixin, BaseEstimator):
    """Duas colunas fixas 0/1; sem vocabulário, IDF, labels ou autorização."""

    def fit(self, textos: Iterable[str], y=None):
        return self

    def transform(self, textos: Iterable[str]) -> csr_matrix:
        if isinstance(textos, str):
            raise ValueError("transform exige coleção de textos")
        sinais = [separar_texto_e_sinais(t)[1] for t in textos]
        return csr_matrix(np.asarray(sinais, dtype=float).reshape(-1, 2))

    def get_feature_names_out(self, input_features=None) -> np.ndarray:
        return np.asarray(MARCADORES, dtype=object)


def criar_extrator_sinais_atomicos(cabeca) -> FeatureUnion:
    """Clona parâmetros lexicais existentes sem copiar seus pesos ajustados."""
    original = cabeca.named_steps["features"]
    if [nome for nome, _ in original.transformer_list] != ["palavras", "caracteres"]:
        raise ValueError("experimento exige os dois canais lexicais conhecidos")
    canais = []
    for nome, extrator in original.transformer_list:
        if extrator.preprocessor is not enriquecer_texto_features:
            raise ValueError("preprocessador não corresponde à hipótese investigada")
        lexical = clone(extrator)
        lexical.set_params(preprocessor=texto_lexical_sem_metadados)
        canais.append((nome, lexical))
    canais.append(("sinais", SinaisNegacaoAtomicos()))
    return FeatureUnion(canais)
