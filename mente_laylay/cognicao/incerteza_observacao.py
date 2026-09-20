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
    rf"(?:posso|podemos|[ée]\s+poss[ií]vel)\s+(?:afirmar|confirmar|determinar|saber)|"
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
    r")\s+(?P<objeto>.+)$",
    re.IGNORECASE,
)
_FRONTEIRA_PEDIDO_INFORMACAO = re.compile(
    r"[.!?,;:—]|\b(?:mas|por[eé]m|contudo|entretanto|porque|pois|"
    r"ent[aã]o|portanto|logo)\b",
    re.IGNORECASE,
)
_OBJETO_IDENTIFICADO = re.compile(
    # Objeto nominal com oração relativa: "o nome ... ou o app que ...".
    # Não admite "me diga que ...", uma instrução para afirmar um fato.
    r"(?:o|a|os|as|um|uma)\s+(?:(?!que\b)[\wÀ-ÿ'-]+\s+)+que\s*",
    re.IGNORECASE,
)


def estado_sob_pedido_informacao(prefixo: str) -> bool:
    """Reconhece estado subordinado a um pedido de informação ao usuário.

    Não inclui "posso informar que", que seria uma afirmação da própria Laylay.
    Recebe o prefixo anterior à ocorrência, depois da última alegação analisada,
    nunca o histórico. Assim "e/ou" pode ligar nomes no objeto solicitado, mas
    um pedido não empresta seu escopo a outro estado ou efeito narrado depois.
    """
    oracao = _FRONTEIRA_PEDIDO_INFORMACAO.split(str(prefixo or ""))[-1].strip()
    pedido = _PEDIDO_INFORMACAO.fullmatch(oracao)
    if not pedido:
        return False
    objeto = pedido.group("objeto").strip()
    return bool(
        re.match(r"(?:se|qual|quais)\b", objeto, re.IGNORECASE)
        or _OBJETO_IDENTIFICADO.fullmatch(objeto)
    )


def estado_sob_pergunta_referida(prefixo: str) -> bool:
    """Estado mencionado como objeto de pergunta não é afirmado pela Laylay.

    Recebe apenas o trecho anterior à ocorrência. Cada oração independente
    reinicia o escopo: mencionar uma pergunta não libera afirmações seguintes.
    Não comprova que a pergunta aconteceu e não concede autoridade de ação.
    Inclui a questão subordinada a uma consulta explicitamente recusada
    ("não vou verificar se ..."), que também não afirma sua resposta.
    """
    oracao = re.split(
        r"[.!?,;:—]|\b(?:mas|porém|porem|contudo|entretanto|porque|pois|"
        r"então|entao|portanto|logo)\b|(?<!\S)(?:e|ou)(?!\S)",
        str(prefixo or ""), flags=re.IGNORECASE,
    )[-1].strip()
    return bool(re.match(
        r"^(?:voc[eê]\s+(?:n[aã]o\s+)?perguntou|"
        r"(?:eu\s+)?n[aã]o\s+(?:vou|irei)\s+(?:verificar|conferir|consultar))\s+se\b",
        oracao, re.IGNORECASE,
    ))
