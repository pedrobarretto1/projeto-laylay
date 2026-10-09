"""Contrato compartilhado para impedir ataques pessoais explícitos na fala."""

from __future__ import annotations

import re

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico


_INTENSIDADE = r"(?:(?:muito|tao|completamente|totalmente|absolutamente)\s+)*"
_ATAQUE_PESSOAL = re.compile(
    r"\b(?:seu|sua)\s+(?:idiota|burr[oa]|incapaz|inutil)\b|"
    r"\b(?:voce|tu)\s+(?:e|eh|foi|parece|seria)\s+"
    r"(?:(?:um|uma)\s+(?:pessoa\s+)?)?" + _INTENSIDADE
    + r"(?:idiota|burr[oa]|incapaz|inutil|fracass[oa]|fracassad[oa]|fei[oa])\b|"
    r"\b(?:sua|seu)\s+(?:inteligencia|aparencia|identidade|valor)\s+"
    r"(?:e|eh|parece)\s+" + _INTENSIDADE
    + r"(?:ridicul[oa]|inutil|desprezivel|limitad[oa])\b|"
    r"\b(?:voce|tu)\s+nao\s+(?:vale|serve)\s+(?:nada|para nada)\b|"
    r"\bninguem\s+(?:te|lhe)\s+(?:aguenta|suporta|quer)\b"
)
_NEGACAO_PROPOSICAO = re.compile(
    r"\bnao\s+(?:acho|penso|acredito|considero)\s+que\s*$"
)
_CITACAO = re.compile(r'"[^"\n]+"|“[^”\n]+”|\x27[^\x27\n]+\x27|‘[^’\n]+’')
_MOLDURA_MENCAO = re.compile(r"\b(?:frase|expressao|citacao|termo|palavras)\b")
_QUALIFICACAO_CRITICA = re.compile(
    r"^\s*(?:e|eh|foi|seria)\s+(?:(?:um|uma)\s+)?"
    r"(?:ofensiv[ao]|insulto|ataque|depreciativ[ao]|inadequad[ao]|agressiv[ao])\b"
)
_ENDOSSO_CITACAO = re.compile(
    r"\b(?:mas|porem|contudo|entretanto|e)\s+"
    r"(?:(?:tambem|realmente|ainda)\s+)*(?:e|eh)\s+"
    r"(?:verdade|verdadeir[oa]|corret[oa])\b"
)


def _citacao_critica(base: str, inicio: int, fim: int) -> bool:
    for citacao in _CITACAO.finditer(base):
        if citacao.start() <= inicio and fim <= citacao.end():
            antes = base[max(0, citacao.start() - 50):citacao.start()]
            depois = base[citacao.end():citacao.end() + 80]
            return bool(
                _MOLDURA_MENCAO.search(antes)
                and _QUALIFICACAO_CRITICA.search(depois)
                and not _ENDOSSO_CITACAO.search(depois)
            )
    return False


def contem_ataque_pessoal(fala: str) -> bool:
    """Detecta depreciação direta da pessoa sem vetar crítica a seu ato."""
    base = normalizar_texto_basico(fala)
    return any(
        not _NEGACAO_PROPOSICAO.search(base[:ataque.start()])
        and not _citacao_critica(base, ataque.start(), ataque.end())
        for ataque in _ATAQUE_PESSOAL.finditer(base)
    )
