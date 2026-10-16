"""Gramáticas operacionais estreitas compartilhadas pela cognição da Laylay.

Este módulo somente reconhece formas linguísticas explícitas. Ele não resolve
contexto, não escolhe executor e não concede autoridade por conta própria.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico, remover_conector_discursivo_inicial


_TIPOS_RECURSO_NOMINAL = {
    "email": "email", "rascunho": "email",
    "musica": "musica", "música": "musica", "faixa": "musica", "cancao": "musica", "canção": "musica",
    "playlist": "playlist", "video": "video", "vídeo": "video",
    "app": "app", "aplicativo": "app", "programa": "app", "janela": "app",
    "site": "site", "pagina": "site", "página": "site", "aba": "site",
    "arquivo": "arquivo", "documento": "arquivo", "pasta": "arquivo",
    "diretorio": "arquivo", "diretório": "arquivo",
    "lampada": "iot", "lâmpada": "iot", "luz": "iot", "tomada": "iot", "ventilador": "iot",
    "dispositivo": "iot", "aparelho": "iot",
}


def tipo_recurso_pedido_direto(texto: str) -> str:
    """Lê somente o núcleo nominal do pedido, nunca palavras dentro do nome.

    Não resolve entidade ou concede autorização. Molduras polidas reutilizam
    o leitor canônico; pedidos mistos são interpretados pelos seus atos.
    """
    from mente_laylay.cognicao.modalidade_turno import (
        classificar_modalidade_turno, extrair_nucleo_pedido_operacional,
    )
    bruto = str(texto or "").strip()
    turno = classificar_modalidade_turno(bruto)
    if turno.get("modalidade_geral") == "misto":
        return ""
    base = extrair_nucleo_pedido_operacional(bruto) or bruto
    return tipo_recurso_nucleo_operacional(base)


def tipo_recurso_nucleo_operacional(texto: str) -> str:
    """Projeção nominal sem modalidade: não concede permissão nem resolve alvo.

    A segmentação pode consultar a oração negada para distinguir recursos,
    sem reclassificá-la como pedido nem recursar no leitor de turno misto.
    """
    m = re.match(
        r"^(?:abre|abra|abrir|fecha|feche|fechar|coloca|coloque|colocar|"
        r"toca|toque|tocar|escuta|escute|escutar|cria|crie|criar|"
        r"liga|ligue|ligar|desliga|desligue|desligar|apaga|apague|apagar|"
        r"remove|remova|remover|pausa|pause|pausar|retoma|retome|retomar|"
        r"mostra|mostre|mostrar|pesquisa|pesquise|pesquisar|procura|procure|procurar)\s+"
        r"(?:(?:o|a|os|as|um|uma|esse|essa|este|esta)\s+)?(?P<tipo>\w+)\b",
        str(texto or "").strip(), flags=re.IGNORECASE,
    )
    return _TIPOS_RECURSO_NOMINAL.get(m.group("tipo").casefold(), "") if m else ""


def candidato_respeita_tipo_recurso(candidato: dict, tipo: str) -> bool:
    """Compatibilidade do tipo explícito com a capacidade, não prova do alvo.

    Um candidato mais confiante não pode apagar o tipo dito pelo usuário.
    Sem evidência nominal, a arbitragem existente conserva sua responsabilidade.
    """
    if not tipo:
        return True
    from mente_laylay.especialistas.capacidades import consultar_capacidade
    intent = str(candidato.get("intent") or "").upper()
    dominio = consultar_capacidade(intent).get("dominio")
    esperado = {"musica": "musica", "playlist": "musica", "video": "navegador",
        "app": "sistema", "site": "navegador", "arquivo": "arquivos", "iot": "iot", "email": "email"}.get(tipo)
    # MEDIA_CONTROL também controla vídeo, mas nunca materializa a busca de
    # um vídeo nomeado. VOLUME é parâmetro de áudio, não operação de aplicativo.
    if tipo == "video" and intent == "MEDIA_CONTROL":
        return True
    return dominio == esperado and not (tipo == "app" and intent == "VOLUME")


def nivel_ajuste_extremo_volume(texto: str) -> int | None:
    """Lê um ajuste inteiro, não uma palavra extrema dentro de outro pedido.

    Sem parâmetro nomeado, a forma exige verbo e pertence à resolução
    contextual qualificada. A gramática não escolhe a fonte nem autoriza ação.
    """
    t = re.sub(r"\s+", " ", remover_conector_discursivo_inicial(texto)).strip().casefold().rstrip(".!?")
    ajuste = re.fullmatch(
        r"(?:(?P<verbo>coloca|coloque|deixa|deixe|bota|bote|poe|põe|"
        r"aumenta|aumente|sobe|abaixa|abaixe|baixa|diminui|diminua)\s+)?"
        r"(?:(?:o\s+)?(?P<parametro>volume|som)\s+)?"
        r"(?:(?:em|ao|no|na|para|pra|pro)\s+(?:(?:o|a)\s+)?)?"
        r"(?P<nivel>maximo|máximo|minimo|mínimo|talo)", t,
    )
    if not ajuste or not (ajuste.group("verbo") or ajuste.group("parametro")):
        return None
    return 0 if ajuste.group("nivel") in {"minimo", "mínimo"} else 100


@dataclass(frozen=True, slots=True)
class RelacaoValorAjuste:
    """Papel do número na fala; não escolhe recurso, referente ou executor."""

    modo: str
    valor: int
    direcao: str = ""
    unidade: str = ""


_INTEIROS_PEQUENOS = {
    "zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3,
    "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9,
    "dez": 10, "onze": 11, "doze": 12, "treze": 13, "catorze": 14, "quatorze": 14,
    "quinze": 15, "dezesseis": 16, "dezasseis": 16, "dezessete": 17, "dezassete": 17,
    "dezoito": 18, "dezenove": 19, "dezanove": 19,
}
_DEZENAS = {"vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50,
    "sessenta": 60, "setenta": 70, "oitenta": 80, "noventa": 90}
_CENTENAS = {"duzentos": 200, "trezentos": 300, "quatrocentos": 400,
    "quinhentos": 500, "seiscentos": 600, "setecentos": 700, "oitocentos": 800,
    "novecentos": 900}


def interpretar_inteiro_literal(texto: str) -> int | None:
    """Lê um literal inteiro0–999, sem arredondar, resolver unidade ou executar.

    Não reescreve a frase. Conjunções precisam compor uma quantidade válida;
    frações, sinais e construções fora desta gramática ficam indeterminados.
    """
    if not isinstance(texto, str):
        return None
    literal = normalizar_texto_basico(texto)
    if re.fullmatch(r"\d{1,3}", literal):
        return int(literal)
    simples = {**_INTEIROS_PEQUENOS, **_DEZENAS, **_CENTENAS, "cem": 100}
    if literal in simples:
        return simples[literal]
    partes = literal.split(" e ")
    if len(partes) == 2 and partes[0] in _DEZENAS and 1 <= _INTEIROS_PEQUENOS.get(partes[1], -1) <= 9:
        return _DEZENAS[partes[0]] + _INTEIROS_PEQUENOS[partes[1]]
    if 2 <= len(partes) <= 3 and partes[0] in {"cento", *_CENTENAS}:
        resto = interpretar_inteiro_literal(" e ".join(partes[1:]))
        if resto is not None and 1 <= resto <= 99:
            return (100 if partes[0] == "cento" else _CENTENAS[partes[0]]) + resto
    return None


_TOKEN_QUANTIDADE = r"\b(?:" + "|".join(sorted({
    *_INTEIROS_PEQUENOS, *_DEZENAS, *_CENTENAS, "três", "cem", "cento",
    "mil", "meio", "meia", "virgula", "vírgula", "ponto",
}, key=len, reverse=True)) + r")\b"
_LITERAL_QUANTIDADE = rf"(?:[+-]?\d+(?:[.,]\d+)?|{_TOKEN_QUANTIDADE}(?:\s+(?:e\s+)?{_TOKEN_QUANTIDADE})*)"


def localizar_quantidade_literal(texto: str, *, inicio: int = 0) -> tuple[int, int] | None:
    """Localiza forma quantitativa no início indicado, sem validar seu valor.

    Frações ou sequências malformadas podem possuir forma de quantidade sem
    admitir um inteiro. O chamador decide o papel no pedido; este intervalo
    não transforma artigo em medida, não escolhe domínio nem concede autoridade.
    """
    if not isinstance(texto, str) or type(inicio) is not int or not 0 <= inicio <= len(texto):
        return None
    trecho = texto[inicio:]
    marcador_fracao = r"(?:ponto|v[ií]rgula)\b"
    marcador = re.match(marcador_fracao, trecho, re.IGNORECASE)
    if marcador:
        numero = re.match(_LITERAL_QUANTIDADE, trecho[marcador.end():].lstrip(), re.IGNORECASE)
        if not numero or re.match(marcador_fracao, numero.group(), re.IGNORECASE):
            return None  # Separador sem número também pode pertencer a um nome.
    encontrado = re.match(_LITERAL_QUANTIDADE, trecho, re.IGNORECASE)
    return (inicio, inicio + encontrado.end()) if encontrado else None


def localizar_quantidade_ajuste(texto: str, *, apos_recurso: int) -> tuple[int, int] | None:
    """Localiza quantidade após relação explícita de um recurso já tipado.

    O chamador delimita o recurso. O intervalo literal, inclusive se inválido,
    segue ao leitor do valor: não truncar 'quarenta e onze' para quarenta nem
    transformar falha quantitativa em passo qualitativo. Não concede permissão.
    """
    if not isinstance(texto, str) or type(apos_recurso) is not int or not 0 <= apos_recurso <= len(texto):
        return None
    encontrado = re.search(rf"\b(?:em|para|pra|no)\s+(?P<valor>{_LITERAL_QUANTIDADE})", texto[apos_recurso:], re.IGNORECASE)
    if not encontrado or re.search(r"[;.!?\n]", texto[apos_recurso:apos_recurso + encontrado.start()]):
        return None
    inicio, fim = encontrado.span("valor")
    if (encontrado.group("valor").casefold() == "um"
            and re.match(r"\s+(?:pouco|pouquinho)\b", texto[apos_recurso + fim:], re.IGNORECASE)):
        return None  # Quantificador de intensidade, não cardinal da medida.
    return apos_recurso + inicio, apos_recurso + fim


_AJUSTE_NUMERICO_CONTEXTUAL = re.compile(
    # Direção com destino é atribuição absoluta ("sobe para 80"), não delta.
    # Exigir PARA/PRA nesta alternativa preserva "sobe em 10" e outros alvos.
    r"(?:(?P<verbo>coloca|coloque|bota|deixa|poe|põe|"
    r"(?:aumenta|aumente|sobe|suba|eleva|eleve|abaixa|abaixe|baixa|baixe|"
    r"diminui|diminua|reduz|reduza)(?=\s+(?:para|pra)\b))\s+)?"
    r"(?:o\s+)?(?:em|no|para|pra)?\s*(?P<nivel>.+?)\s*(?:%|por\s+cento)?"
)


def ler_nivel_atribuicao_contextual(texto: str, *, exigir_verbo: bool = False) -> int | None:
    """Lê o inteiro da moldura contextual, sem resolver recurso ou executar.

    Não reescrever sinais ou unidades para produzir um valor diferente. O
    domínio continua dono dos limites e do referente, não o leitor de números.
    """
    ajuste = _AJUSTE_NUMERICO_CONTEXTUAL.fullmatch(remover_conector_discursivo_inicial(texto).casefold().rstrip(".!?"))
    if not ajuste or exigir_verbo and not ajuste.group("verbo"):
        return None
    return interpretar_inteiro_literal(ajuste.group("nivel"))


def texto_pede_ajuste_numerico_contextual(texto: str) -> bool:
    """Forma de atribuição com inteiro legível; não escolhe habilidade."""
    return ler_nivel_atribuicao_contextual(texto, exigir_verbo=True) is not None


def texto_pede_ajuste_parametrico_contextual(texto: str) -> bool:
    """Forma paramétrica exige resolução, mesmo quando seu valor é inválido.

    Reconhecer a natureza não aceita valor/unidade nem fornece o referente.
    Títulos literais e artigos com complemento nominal não são medidas.
    """
    texto = remover_conector_discursivo_inicial(texto)
    if texto_pede_ajuste_numerico_contextual(texto):
        return True
    fonte = str(texto or "").strip().casefold().rstrip(".!?")
    ajuste = _AJUSTE_NUMERICO_CONTEXTUAL.fullmatch(fonte)
    if ajuste and ajuste.group("verbo"):
        intervalo = localizar_quantidade_literal(fonte, inicio=ajuste.start("nivel"))
        if intervalo:
            literal = fonte[slice(*intervalo)]
            if literal not in {"um", "uma"} or intervalo[1] == ajuste.end("nivel"):
                return True
    return bool(
        nivel_ajuste_extremo_volume(texto) is not None
        and not re.search(r"\b(?:volume|som)\b", str(texto or ""), flags=re.IGNORECASE)
    )


def interpretar_relacao_valor_ajuste(
    texto: str, *, intervalo_valor: tuple[int, int],
) -> RelacaoValorAjuste | None:
    """Distingue destino de magnitude no literal já localizado pelo domínio.

    EM com verbo direcional é variação; EM com atribuição continua destino.
    PARA/PRA sempre indica destino. O consumidor continua dono da unidade,
    limites, alvo, estado anterior, autorização e confirmação do efeito.
    Não transforma um delta em destino usando memória ou valor presumido.
    """
    if (not isinstance(texto, str) or not isinstance(intervalo_valor, tuple)
            or len(intervalo_valor) != 2 or any(type(i) is not int for i in intervalo_valor)):
        return None
    inicio, fim = intervalo_valor
    if not 0 <= inicio < fim <= len(texto):
        return None
    valor = interpretar_inteiro_literal(texto[inicio:fim])
    if valor is None:
        return None
    antes = texto[:inicio].casefold()
    relacao = re.search(r"\b(em|para|pra|no)\s*$", antes)
    verbos = re.findall(
        r"\b(aumenta|aumente|aumentar|sobe|suba|subir|eleva|eleve|elevar|"
        r"abaixa|abaixe|abaixar|baixa|baixe|baixar|diminui|diminua|diminuir|reduz|reduza|reduzir)\b",
        antes,
    )
    if len(verbos) > 1:
        return None  # Mais de uma operação exige os atos do owner, não adivinhação.
    direcao = ("aumentar" if verbos[0].startswith(("aument", "sob", "sub", "elev"))
               else "diminuir") if verbos else ""
    if direcao and relacao is None:
        return None  # Número sem relação não determina destino ou variação.
    if (inicio > 0 and texto[inicio - 1] in "-+.,"
            or re.match(r"[.,]\d", texto[fim:])):
        return None  # Não truncar sinais/frações para obter outro inteiro.
    sufixo = texto[fim:].casefold()
    if re.match(r"\s*e[+-]?\d", sufixo):
        return None  # Não truncar notação não inteira para outro valor.
    if re.match(rf"\s+(?:e\s+)?(?:\d|{_TOKEN_QUANTIDADE})", sufixo):
        return None  # Intervalo parcial não pode validar '40 e cinco' como40.
    unidade = re.match(r"\s*(%|por\s+cento\b|pontos\s+percentuais\b|[a-zà-ÿ]+)", sufixo)
    unidade_lida = re.sub(r"\s+", " ", unidade.group(1)) if unidade else ""
    if unidade_lida in {"e", "depois", "agora", "aqui", "no", "na", "por"}:
        unidade_lida = ""  # Complemento/discurso não é unidade da grandeza.
    modo = "relativo" if direcao and relacao and relacao.group(1) == "em" else "absoluto"
    return RelacaoValorAjuste(modo=modo, valor=valor, direcao=direcao, unidade=unidade_lida)


_PADRAO_AVANCO_MIDIA_EXPLICITO = (
    r"(?:"
    r"(?:vai|passa|passe|pula|pule)\s+"
    r"(?:(?:para|pra)\s+)?(?:a\s+)?"
    r"(?:proxima|próxima)\s+(?:musica|música|faixa)"
    r"|"
    r"(?:avanca|avança|avance)\s+(?:uma|a)\s+"
    r"(?:musica|música|faixa)"
    r")"
)

_PADRAO_AVANCO_MIDIA_CONTEXTUAL = (
    r"(?:troca|troque|muda|mude)\s+(?:para|pra)\s+"
    r"(?:a\s+)?(?:proxima|próxima)"
)

_PADRAO_CONTINUACAO_PLAYLIST_ATUAL = (
    r"(?:adiciona|adicione|salva|salve|acrescenta|acrescente)\s+"
    r"(?:essa|esta|isso|ela)"
    r"(?:\s+(?:musica|música|faixa))?"
    r"(?:\s+(?:tambem|também))?\s+"
    r"(?:na|nessa|nesta)\s+(?:playlist\s+)?.+"
)

_SEPARADOR_CADEIA_M1 = (
    r"(?:e\s+depois|depois|em\s+seguida|entao|então|e)"
)


def texto_pede_avanco_midia_via_vai(
    texto: str,
    *,
    permitir_cadeia: bool = False,
) -> bool:
    """Reconhece ``vai para a próxima faixa`` sem promover ``vai`` globalmente."""
    base = re.sub(r"\s+", " ", str(texto or "").strip())
    base = base.strip(" .,!?:;")
    if not base:
        return False

    if re.fullmatch(
        _PADRAO_AVANCO_MIDIA_EXPLICITO,
        base,
        flags=re.IGNORECASE,
    ):
        return True

    if not permitir_cadeia:
        return False

    return bool(re.fullmatch(
        r"(?:"
        + _PADRAO_AVANCO_MIDIA_EXPLICITO
        + r"|"
        + _PADRAO_AVANCO_MIDIA_CONTEXTUAL
        + r")"
        + r"\s+"
        + _SEPARADOR_CADEIA_M1
        + r"\s+"
        + _PADRAO_CONTINUACAO_PLAYLIST_ATUAL,
        base,
        flags=re.IGNORECASE,
    ))

def texto_pede_restauracao_contextual(texto: str) -> bool:
    """Reconhece pedido direto de restauração expresso na fala atual.

    Esta função reconhece somente a forma linguística. Ela não consulta
    contexto, não escolhe alvo e não concede execução por conta própria.
    """
    base = re.sub(r"\s+", " ", str(texto or "").strip())
    base = base.strip(" .,!?:;")
    if not base:
        return False

    return bool(re.fullmatch(
        r"(?:desfaz(?:er)?(?:\s+isso)?|"
        r"restaura(?:r)?(?:\s+o)?\s+(?:ultimo|último)?\s*(?:arquivo|item|pasta)?|"
        r"recupera(?:r)?(?:\s+o)?\s+(?:ultimo|último)?\s*(?:arquivo|item|pasta)?|"
        r"(?:eu\s+)?quero\s+(?:ele|ela|isso|o\s+arquivo|a\s+pasta)\s+de\s+volta|"
        r"traz\s+(?:ele|ela|isso|o\s+arquivo|a\s+pasta)\s+de\s+volta)",
        base,
        flags=re.IGNORECASE,
    ))
