"""Leitura conservadora de provocações e cutucadas sociais curtas.

O módulo classifica somente a forma social da fala. Ele não produz comandos,
não decide intenção operacional e não transforma apelidos ou ofensas em fatos
de memória. A lista curta existe para dar contexto linguístico ao modelo e à
contingência quando uma fala isolada não contém um assunto convencional.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from typing import Any

from mente_laylay.personalidade.variacao_fala import escolher_variacao


_PROVOCACOES_LEVES = {
    "doida", "doido", "folgada", "folgado", "maluca", "maluco",
    "safada", "safado", "sem vergonha", "chata", "chato", "lerda", "lerdo",
}
_PROVOCACOES_OFENSIVAS = {
    "babaca", "boiola", "burra", "burro", "idiota", "imbecil", "otaria",
    "otario", "tapada", "tapado", "vagabunda", "vagabundo", "viado",
}


def _normalizar(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"[^a-z0-9\s]", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def classificar_provocacao_curta(texto: Any) -> dict[str, Any]:
    """Retorna uma leitura social segura para uma cutucada ou zoeira curta."""
    base = _normalizar(texto)
    palavras = base.split()
    if not base or len(palavras) > 8:
        return {}

    brincadeira_declarada = bool(re.fullmatch(
        r"(?:"
        r"(?:(?:eu\s+)?(?:tava|to|estava)\s+)?(?:so\s+)?"
        r"(?:tirando\s+uma\s+onda|zoando|brincando|de\s+brincadeira)"
        r"|(?:era|foi)\s+(?:so\s+)?(?:zoeira|brincadeira|uma\s+brincadeira)"
        r"|(?:so\s+)?(?:zoeira|brincadeira)"
        r")(?:\s+so)?",
        base,
    ))
    if brincadeira_declarada:
        return {
            "tipo": "brincadeira_declarada",
            "tom": "brincadeira",
            "marcador": base,
            "confianca": 0.98,
            "autoriza_execucao": False,
            "memorizar_como_fato": False,
        }

    sem_vocativo = re.sub(r"^(?:lay|laylay)\s+", "", base).strip()
    sem_moldura = re.sub(r"^(?:sua|seu|sua\s+cara\s+de)\s+", "", sem_vocativo).strip()
    candidatos = {base, sem_vocativo, sem_moldura}

    ofensiva = next(
        (item for item in _PROVOCACOES_OFENSIVAS if item in candidatos),
        "",
    )
    leve = next(
        (item for item in _PROVOCACOES_LEVES if item in candidatos),
        "",
    )
    marcador = ofensiva or leve
    if not marcador:
        return {}

    return {
        "tipo": "provocacao_curta",
        "tom": "limite_firme" if ofensiva else "brincadeira",
        "marcador": marcador,
        "confianca": 0.97 if ofensiva else 0.90,
        "autoriza_execucao": False,
        "memorizar_como_fato": False,
    }


def resposta_contingencia_provocacao(
    texto: Any,
    *,
    evitar: Iterable[str] = (),
) -> str:
    """Mantém a conversa viva se a geração e o reparo falharem juntos."""
    leitura = classificar_provocacao_curta(texto)
    if not leitura:
        return ""
    if leitura["tipo"] == "brincadeira_declarada":
        return escolher_variacao([
            "Eu saquei kkk. Você tava só me cutucando e eu quase levei a sério.",
            "Ah, era zoeira kkk. Eu já tava dando importância demais pra essa palhaçada.",
            "Tá explicado kkk. Você só queria me cutucar e eu quase abri uma investigação.",
        ], evitar=evitar)
    if leitura["tom"] == "limite_firme":
        return escolher_variacao([
            "Do nada? Se era provocação, capricha sem apelar pra isso.",
            "Essa foi a grande contribuição do turno? Dá pra provocar sem baixar o nível.",
            "A criatividade tirou folga hoje, né? Se vai provocar, tenta melhor.",
        ], evitar=evitar)
    return escolher_variacao([
        "Olha a intimidade kkk. Vai, desenvolve essa provocação aí.",
        "Ousadia chegou antes do argumento, né? Continua, quero ver onde isso vai dar.",
        "Tá se sentindo íntimo hoje kkk. Pelo menos melhora essa provocação.",
    ], evitar=evitar)
