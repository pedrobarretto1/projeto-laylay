"""Leitura central de referências contextuais na linguagem natural."""

from __future__ import annotations

import re
import unicodedata


_PRONOMES = (
    r"ele|ela|eles|elas|isso|isto|aquilo|esse|essa|esses|essas|este|esta|"
    r"estes|estas|aquele|aquela|aqueles|aquelas|desse|dessa|desses|dessas|"
    r"dele|dela|deles|delas|aqui|ali"
)
_NOMES_GENERICOS = (
    r"app|aplicativo|programa|janela|aba|site|pagina|página|arquivo|pasta|"
    r"documento|item|dispositivo|aparelho|luz|lampada|lâmpada|playlist|"
    r"musica|música|faixa|jogo|coisa|negocio|negócio"
)

_PADRAO_ABA_ANTERIOR_EXPLICITA = (
    r"(?:volta|volte|retorna|retorne|vai)\s+"
    r"(?:(?:para|pra)\s+)?(?:a\s+)?aba\s+anterior"
)
_PADRAO_ABA_ANTERIOR_ELIPSE_SITE = (
    r"(?:volta|volte)\s+"
    r"(?:(?:para|pra)\s+)?(?:a\s+)?anterior"
)

_PEDIDO_ABA_ANTERIOR_EXPLICITO = re.compile(
    rf"^{_PADRAO_ABA_ANTERIOR_EXPLICITA}[.!?]*$",
    re.IGNORECASE,
)
_INICIO_PEDIDO_ABA_ANTERIOR_EXPLICITO = re.compile(
    rf"^{_PADRAO_ABA_ANTERIOR_EXPLICITA}"
    r"(?:[.!?]*$|\s+(?:e\s+depois|depois|em\s+seguida|entao|então)\b)",
    re.IGNORECASE,
)
_PEDIDO_ABA_ANTERIOR_ELIPSE_SITE = re.compile(
    rf"^{_PADRAO_ABA_ANTERIOR_ELIPSE_SITE}[.!?]*$",
    re.IGNORECASE,
)


def texto_pede_aba_anterior(
    texto: str,
    *,
    permitir_cadeia: bool = False,
    contexto_site_confirmado: bool = False,
) -> bool:
    """Reconhece a operação linguística de voltar à aba anterior.

    A forma explícita exige ``aba anterior`` e pode ser usada por classificação,
    P0 e detector determinístico. A elipse sem ``aba`` só é aceita quando o
    chamador já provou que a referência viva pertence ao domínio ``site``.

    A função identifica semântica; não resolve contexto e não concede
    autorização. ``permitir_cadeia`` vale apenas para a forma explícita.
    """
    base = re.sub(r"\s+", " ", str(texto or "").strip())
    if not base:
        return False

    padrao_explicito = (
        _INICIO_PEDIDO_ABA_ANTERIOR_EXPLICITO
        if permitir_cadeia
        else _PEDIDO_ABA_ANTERIOR_EXPLICITO
    )
    if padrao_explicito.match(base):
        return True

    return bool(
        contexto_site_confirmado
        and _PEDIDO_ABA_ANTERIOR_ELIPSE_SITE.match(base)
    )


_REFERENCIA_NO_TEXTO = re.compile(
    rf"\b(?:{_PRONOMES}|tambem|também)\b|\b(?:de novo|mais (?:um|uma))\b",
    re.IGNORECASE,
)

_ORDINAIS_REFERENCIA = {
    "primeiro": 0, "primeira": 0,
    "segundo": 1, "segunda": 1,
    "terceiro": 2, "terceira": 2,
    "quarto": 3, "quarta": 3,
    "quinto": 4, "quinta": 4,
    "sexto": 5, "sexta": 5,
    "setimo": 6, "setima": 6,
    "oitavo": 7, "oitava": 7,
    "nono": 8, "nona": 8,
    "decimo": 9, "decima": 9,
}


def separar_alvo_e_complemento_foco(valor: str) -> tuple[str, bool]:
    """Separa o referente de um complemento que somente solicita foco.

    Não escolhe domínio, não resolve o pronome e não autoriza execução. Serve
    igualmente para arquivos, aplicativos e outras entidades que possam ser
    abertas por uma habilidade proprietária.
    """
    alvo = re.sub(r"\s+", " ", str(valor or "").strip())
    if not alvo:
        return "", False
    encontrado = re.match(
        r"^(?P<alvo>.+?)\s+"
        r"(?:e\s+)?(?:depois\s+)?(?:"
        r"(?:deixa|deixe|coloca|coloque|bota|bote|traz|traga|mantem|mantém|mantenha)"
        r"(?:\s+(?:ele|ela|isso|esse|essa|a\s+janela|o\s+programa|o\s+app|o\s+aplicativo))?"
        r"\s+(?:em\s+foco|na\s+frente|pra\s+frente|para\s+frente|em\s+primeiro\s+plano)"
        r"|(?:foca|foque)(?:\s+(?:ele|ela|isso|esse|essa))?"
        r")\s*$",
        alvo,
        flags=re.IGNORECASE,
    )
    if not encontrado:
        return alvo, False
    alvo_limpo = str(encontrado.group("alvo") or "").strip(" .,!?:;\"'")
    return alvo_limpo, bool(alvo_limpo)


def extrair_indice_referencia_ordinal(texto: str) -> int | None:
    """Extrai uma seleção ordinal contextual em índice baseado em zero.

    O ordinal só vale quando a frase contém uma ação de seleção ou menciona
    resultado/opção. Isso evita interpretar frases narrativas como "foi meu
    primeiro jogo" como comandos contextuais.
    """
    bruto = str(texto or "").strip()
    base = unicodedata.normalize("NFKD", bruto.casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"\s+", " ", base).strip()
    if not base:
        return None
    tem_selecao = bool(re.search(
        r"\b(?:abre|abrir|abra|mostra|mostrar|mostre|seleciona|selecionar|"
        r"selecione|escolhe|escolher|escolha|usa|usar|use|toca|tocar|toque|"
        r"executa|executar|execute)\b|"
        r"\b(?:resultado|resultados|opcao|opcoes|item|itens|arquivo|arquivos)\b",
        base,
    ))
    if not tem_selecao:
        return None
    encontrado = re.search(
        r"\b(primeir[oa]|segund[oa]|terceir[oa]|quart[oa]|quint[oa]|"
        r"sext[oa]|setim[oa]|oitav[oa]|non[oa]|decim[oa]|\d{1,2})(?:\s*[ºª])?\b",
        base,
    )
    if not encontrado:
        return None
    valor = encontrado.group(1)
    if valor.isdigit():
        numero = int(valor)
        return numero - 1 if numero >= 1 else None
    return _ORDINAIS_REFERENCIA.get(valor)
_REPARO_DO_TURNO_ANTERIOR = re.compile(
    r"^\s*(?:n[aã]o\s+(?:entendi|compreendi|acompanhei)|"
    r"n[aã]o\s+ficou\s+claro|como\s+assim|por\s+qu[eê]|"
    r"(?:agora\s+)?explica(?:\s+(?:isso|aquilo|essa parte))?\s+(?:de\s+novo|melhor|com\s+mais\s+detalhes|mais\s+detalhadamente)|"
    r"repete(?:\s+isso)?|refaz(?:\s+isso)?|mais\s+devagar)\s*[.!?]*\s*$",
    re.IGNORECASE,
)
_VALOR_REFERENCIAL = re.compile(
    rf"^(?:(?:o|a|os|as|um|uma)\s+)?(?:"
    rf"(?:{_PRONOMES})(?:\s+(?:aqui|ali|ai|aí))?|"
    rf"(?:esse|essa|esses|essas|este|esta|estes|estas|aquele|aquela|aqueles|aquelas)"
    rf"(?:\s+(?:aqui|ali|ai|aí))?\s+(?:{_NOMES_GENERICOS})"
    rf")$",
    re.IGNORECASE,
)


def texto_tem_referencia_contextual(texto: str) -> bool:
    """Detecta referência nominal ou reparo que depende do turno anterior."""
    bruto = str(texto or "").strip()
    return bool(
        _REFERENCIA_NO_TEXTO.search(bruto)
        or _REPARO_DO_TURNO_ANTERIOR.search(bruto)
        or re.fullmatch(
            r"\s*(?:e\s+)?(?:o\s+que\s+mais|tem\s+mais|mostra\s+mais|"
            r"me\s+fala\s+mais|(?:de|do|da|dos|das)\s+.+?)\s*[.!?]*\s*",
            bruto,
            flags=re.IGNORECASE,
        )
        or extrair_indice_referencia_ordinal(bruto) is not None
    )


def valor_e_referencia_contextual(valor: str) -> bool:
    """Diz se um parâmetro ainda é um pronome/alvo genérico não resolvido."""
    limpo = re.sub(r"\s+", " ", str(valor or "").strip(" .,!?:;\"'"))
    ordinal_solto = bool(re.fullmatch(
        r"(?:(?:o|a)\s+)?(?:primeir[oa]|segund[oa]|terceir[oa]|quart[oa]|"
        r"quint[oa]|sext[oa]|s[eé]tim[oa]|oitav[oa]|non[oa]|d[eé]cim[oa]|"
        r"\d{1,2}(?:\s*[ºª])?)(?:\s+(?:resultado|op[cç][aã]o|item|arquivo))?",
        limpo,
        flags=re.IGNORECASE,
    ))
    return not limpo or bool(_VALOR_REFERENCIAL.fullmatch(limpo)) or ordinal_solto
