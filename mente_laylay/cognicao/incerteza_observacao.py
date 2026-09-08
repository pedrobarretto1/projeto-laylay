"""Ressalvas linguísticas de observação compartilhadas pelos validadores.

Reconhecer incerteza não prova que o conteúdo é verdadeiro, não confirma efeito
e não estabelece disponibilidade de uma capacidade. O guardião continua dono
da checagem de evidência e do alcance da ressalva sobre cada afirmação.
"""

from __future__ import annotations

import re


_NOME_OBSERVACAO = r"(?:leitura|consulta|verifica[cç][aã]o|observa[cç][aã]o|evid[eê]ncia|confirma[cç][aã]o)"
_VERBO_OBSERVACAO = r"(?:consultar|verificar|observar|confirmar)"
_RESSALVA = re.compile(
    rf"\bn[aã]o\s+(?:sei|consigo|tenho\s+como|consultei|verifiquei|observei|confirmei|"
    rf"consegui\s+{_VERBO_OBSERVACAO}|"
    rf"(?:posso|podemos|[ée]\s+poss[ií]vel)\s+(?:afirmar|confirmar|determinar)|"
    rf"(?:h[aá]|existe|tenho|temos)\s+(?:uma\s+)?{_NOME_OBSERVACAO})\b|"
    rf"\bsem\s+(?:{_VERBO_OBSERVACAO}|(?:uma\s+)?{_NOME_OBSERVACAO})\b|"
    rf"\bpreciso\s+(?:consultar|verificar)\b|"
    # A forma afirmativa "falta uma leitura" não inclui a dupla negação
    # "não há falta de leitura". Exigimos início de oração explícito.
    rf"(?:^|[.!?;]\s*)(?:ainda\s+)?falta\s+(?:uma\s+)?{_NOME_OBSERVACAO}\b",
    re.IGNORECASE,
)


def expressa_incerteza_observacao(texto: str) -> bool:
    """Detecta ressalva; chamadores delimitam o trecho a que ela se aplica."""
    return bool(_RESSALVA.search(str(texto or "").strip()))


_PEDIDO_INFORMACAO = re.compile(
    r"^(?:por\s+favor\s+)?(?:"
    r"me\s+(?:diga|informe|mostre)|"
    r"(?:se\s+)?(?:voc[eê]\s+)?(?:puder|pode|poderia)\s+me\s+(?:dizer|informar|mostrar)"
    r")\s+(?:se|qual|quais)\b",
    re.IGNORECASE,
)


def estado_sob_pedido_informacao(prefixo: str) -> bool:
    """Reconhece estado subordinado a um pedido de informação ao usuário.

    Não inclui "posso informar que", que seria uma afirmação da própria Laylay.
    Recebe só a oração local anterior ao estado, nunca o histórico do turno.
    """
    return bool(_PEDIDO_INFORMACAO.search(str(prefixo or "").strip()))
