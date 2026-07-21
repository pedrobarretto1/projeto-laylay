"""Interpretação de atos sociais pela perspectiva da conversa.

Não executa comandos nem produz respostas. A decisão combina forma da frase,
papéis dos interlocutores e contexto recente, evitando que uma expressão
isolada determine sozinha se Pedro perguntou ou respondeu alguma coisa.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"[^a-z0-9?!,;:.\s]", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def _pergunta_anterior_sobre_pedro(mente: Dict[str, Any]) -> bool:
    anterior = _normalizar(str(mente.get("ultima_resposta") or ""))
    if not anterior or "?" not in anterior:
        return False
    return bool(re.search(
        r"\b(?:e voce|do teu lado|como voce|como foi seu dia|voce esta|voce ta)\b",
        anterior,
    ))


def analisar_ato_social(
    texto: str,
    *,
    mente: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Distingue pergunta de bem-estar, resposta pessoal e ambiguidade."""
    bruto = str(texto or "").strip()
    base = _normalizar(bruto)
    estado = dict(mente or {})
    if not base:
        return {}

    if re.search(r"[,;].+\?\s*$", base):
        return {
            "tipo": "COMPOSTO", "confianca": 0.98,
            "motivo": "afirmacao social seguida de pergunta nova",
            "evidencias": ["mais_de_um_ato"],
        }

    pergunta_estado_como = bool(re.search(
        r"^como\b.*\b(?:voce|tu|lay|laylay|a laylay)?\b.*\b(?:esta|ta)\b",
        base,
    ))
    vocabulario_estado = bool(re.search(
        r"\b(?:bem|mal|tranquil[oa]|de boa|suave|feliz|triste|cansad[oa]|"
        r"tudo certo|na paz|mais ou menos)\b",
        base,
    ))
    estrutura_estado = bool(re.search(
        r"\b(?:como\b.*\b(?:esta|ta)|tudo\b.*\bbem|(?:estou|esta|to|ta)\b.*\b(?:bem|mal|"
        r"tranquil[oa]|feliz|triste|cansad[oa]))\b",
        base,
    ))
    if not ((vocabulario_estado and estrutura_estado) or pergunta_estado_como):
        return {}

    pergunta_grafica = "?" in bruto
    inicio_interrogativo = bool(re.match(r"^(?:como|e voce|e tu)\b", base))
    referencia_laylay = bool(re.search(
        r"\b(?:voce|tu|lay|laylay|a laylay|com voce|do seu lado)\b",
        base,
    ))
    primeira_pessoa = bool(re.search(
        r"\b(?:eu|comigo|meu lado|por aqui|aqui comigo)\b|^(?:estou|to)\b",
        base,
    ))
    afirmacao_explicita = bool(re.search(
        r"\b(?:sim|por aqui|do meu lado|comigo|estou|eu to|eu estou)\b",
        base,
    ))
    contexto_resposta = _pergunta_anterior_sobre_pedro(estado)

    pontos_pergunta = 0.0
    pontos_resposta = 0.0
    evidencias: list[str] = []
    if pergunta_grafica:
        pontos_pergunta += 0.48
        evidencias.append("pontuacao_interrogativa")
        if not primeira_pessoa:
            pontos_pergunta += 0.16
    if inicio_interrogativo:
        pontos_pergunta += 0.34
        evidencias.append("forma_interrogativa")
    if referencia_laylay:
        pontos_pergunta += 0.34
        evidencias.append("estado_dirigido_a_laylay")
    if primeira_pessoa:
        pontos_resposta += 0.48
        evidencias.append("perspectiva_de_pedro")
    if afirmacao_explicita:
        pontos_resposta += 0.34
        evidencias.append("forma_afirmativa")
    if not pergunta_grafica:
        pontos_resposta += 0.14
    if contexto_resposta and not referencia_laylay and not pergunta_grafica:
        pontos_resposta += 0.34
        evidencias.append("responde_pergunta_anterior")

    diferenca = pontos_pergunta - pontos_resposta
    if pontos_pergunta >= 0.58 and diferenca >= 0.20:
        return {
            "tipo": "WELLBEING", "confianca": round(min(0.98, 0.66 + diferenca / 3), 2),
            "motivo": "pergunta dirigida ao estado da Laylay",
            "evidencias": evidencias,
        }
    if pontos_resposta >= 0.48 and diferenca <= -0.20:
        return {
            "tipo": "WELLBEING_REPLY", "confianca": round(min(0.98, 0.66 + abs(diferenca) / 3), 2),
            "motivo": "Pedro informa o proprio estado ou responde a pergunta anterior",
            "evidencias": evidencias,
        }
    return {
        "tipo": "AMBIGUO", "confianca": 0.42,
        "motivo": "perspectiva social insuficiente ou conflitante",
        "evidencias": evidencias,
    }
