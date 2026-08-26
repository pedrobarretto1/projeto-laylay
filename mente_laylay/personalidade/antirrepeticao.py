"""Assinaturas leves para evitar que a personalidade vire um conjunto de bordões.

A camada observa somente a superfície da fala. Ela não altera fatos, comandos ou
memória e não exige outra chamada à LLM.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any


_FAMILIAS_ABERTURA = (
    ("validacao_positiva", re.compile(r"^(?:a[ií]\s+sim|boa|que\s+bom|bom\s+saber|[oó]timo)\b")),
    ("reconhecimento", re.compile(r"^(?:entendi|peguei|certo|t[aá]|beleza|claro)\b")),
    ("agradecimento", re.compile(r"^(?:imagina|de\s+nada|por\s+nada|que\s+nada)\b")),
    ("presenca", re.compile(r"^(?:t[oô]\s+aqui|eu\s+t[oô]\s+aqui|pode\s+falar)\b")),
    ("contraste", re.compile(r"^(?:mas|s[oó]\s+que|por[eé]m)\b")),
    ("pergunta", re.compile(r"^(?:como|qual|quais|por\s+qu[eê]|o\s+que|quem|onde|quando)\b")),
)
_PERGUNTA_DEVOLUCAO = re.compile(
    r"\b(?:e\s+voc[eê]|e\s+voc[eê],?\s+como\s+(?:est[aá]|vai)|o\s+que\s+voc[eê]\s+acha|"
    r"como\s+voc[eê]\s+t[aá])\s*[?]$",
)
_MARCADORES_HUMOR = re.compile(
    r"\b(?:kk+k*|pose|novela|criatura|milagre|dignidade|rebeld[ei]|"
    r"tirou\s+folga|evid[eê]ncia\s+contra|ca[cç]a\s+ao)\b",
)


def _normalizar(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or "").casefold())
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^a-z0-9.?!\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


@dataclass(frozen=True, slots=True)
class AssinaturaFala:
    abertura: str
    frases: int
    termina_pergunta: bool
    devolve_pergunta: bool
    tem_humor: bool
    molde: str

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)

    def compacta(self) -> str:
        pergunta = "devolve" if self.devolve_pergunta else "pergunta" if self.termina_pergunta else "fecha"
        humor = "humor" if self.tem_humor else "literal"
        return f"{self.abertura}/{self.frases}f/{pergunta}/{humor}/{self.molde}"


def assinatura_fala(texto: Any) -> AssinaturaFala:
    fala = _normalizar(texto)
    frases = [item for item in re.split(r"(?<=[.!?])\s+", fala) if item.strip()]
    if not frases and fala:
        frases = [fala]
    abertura = "livre"
    for nome, padrao in _FAMILIAS_ABERTURA:
        if padrao.search(fala):
            abertura = nome
            break
    palavras = re.findall(r"[a-z0-9]+", fala)
    compr = "curta" if len(palavras) <= 12 else "media" if len(palavras) <= 36 else "longa"
    molde = f"{compr}:{'conecta' if len(frases) > 1 else 'direta'}"
    return AssinaturaFala(
        abertura=abertura,
        frases=max(0, len(frases)),
        termina_pergunta=fala.endswith("?"),
        devolve_pergunta=bool(_PERGUNTA_DEVOLUCAO.search(fala)),
        tem_humor=bool(_MARCADORES_HUMOR.search(fala)),
        molde=molde,
    )


def assinaturas_recentes(
    mensagens: Iterable[Mapping[str, Any]] | None,
    *,
    limite: int = 6,
) -> list[str]:
    falas = [
        str(item.get("content") or "")
        for item in list(mensagens or [])
        if isinstance(item, Mapping)
        and str(item.get("role") or "").casefold() == "assistant"
        and str(item.get("content") or "").strip()
    ]
    resultado: list[str] = []
    for fala in falas[-max(1, int(limite or 6)):]:
        compacta = assinatura_fala(fala).compacta()
        if compacta not in resultado:
            resultado.append(compacta)
    return resultado


def repeticao_estrutural(texto: Any, anteriores: Iterable[Any] | None) -> bool:
    """Detecta o mesmo molde; fatos operacionais repetidos continuam permitidos."""
    atual = assinatura_fala(texto)
    if not str(texto or "").strip() or atual.frases == 0:
        return False
    for anterior in list(anteriores or []):
        outra = assinatura_fala(anterior)
        mesma_abertura = atual.abertura != "livre" and atual.abertura == outra.abertura
        mesma_saida = (
            atual.termina_pergunta == outra.termina_pergunta
            and atual.devolve_pergunta == outra.devolve_pergunta
        )
        # Uma frase social pode ser segmentada de forma um pouco diferente
        # pela pontuação e ainda repetir exatamente a mesma coreografia.
        mesmo_molde = atual.molde == outra.molde
        humor_repetido = atual.tem_humor and outra.tem_humor and mesma_abertura
        if mesma_abertura and mesma_saida and (mesmo_molde or humor_repetido):
            return True
    return False
