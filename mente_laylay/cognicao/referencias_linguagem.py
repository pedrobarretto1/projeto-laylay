"""Leitura central de referências contextuais na linguagem natural."""

from __future__ import annotations

import re
import unicodedata


def agente_explicacao_causal(texto: str) -> tuple[str, bool]:
    """Qualifica o agente explícito da ação perguntada, não participantes citados.

    Leitura limitada de oração causal e causativa. Agente e passado são
    dimensões separadas: reconhecer "eu" não prova um episódio histórico.
    Não identifica
    pessoas por nome, resolve elipses ou demonstra que a ação aconteceu.
    Os papéis são relativos à fala do usuário, nunca à voz da resposta.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico, texto_e_metalinguistico

    if texto_e_metalinguistico(texto):
        return "", False
    fora_de_aspas = re.sub(r'"[^"\n]*"|“[^”\n]*”|«[^»\n]*»|\'[^\'\n]*\'', " [citacao] ", str(texto or ""))
    base = normalizar_texto_basico(fora_de_aspas)
    papeis = {"eu": "enunciador", "me": "enunciador", "voce": "destinatario", "tu": "destinatario",
              "te": "destinatario", "laylay": "destinatario", "a laylay": "destinatario",
              "ele": "terceiro", "ela": "terceiro", "eles": "terceiro", "elas": "terceiro",
              "nos": "grupo", "a gente": "grupo"}
    sujeitos = r"a gente|a laylay|laylay|voce|tu|eu|ele|ela|eles|elas|nos"
    causa = re.search(rf"\bpor\s*que\s+(?P<agente>{sujeitos})\s+"
                     r"(?:(?:nao|ja|tambem|mesmo|so|ontem)\s+)*(?P<verbo>[a-z]+)\b", base)
    if causa:
        verbo = causa["verbo"]
        passado = re.fullmatch(
            r"(?:fez|fiz|fizemos|fizeram|disse|dissemos|disseram|quis|quisemos|quiseram|"
            r"foi|fui|fomos|foram|teve|tive|tivemos|tiveram|deu|dei|demos|deram|"
            r"viu|vi|vimos|viram|veio|vim|viemos|vieram|pos|pus|pusemos|puseram|"
            r"[a-z]+(?:ou|eu|iu|ei|amos|emos|imos|aram|eram|iram|aste|este|iste))", verbo)
        # Irregulares presentes compartilham terminações com o pretérito;
        # a terminação isolada não basta para classificá-los como passado.
        presente = verbo in {"sou", "estou", "vou", "dou", "sei", "estamos", "vamos",
                             "sabemos", "temos", "podemos", "queremos"}
        return papeis[causa["agente"]], bool(passado and not presente
            and not re.search(r"(?:aremos|eremos|iremos|oremos)$", verbo))
    if re.search(r"\b(?:o que|motivo|razao|causa)\b", base):
        causativa = re.search(rf"\b(?:(?P<pronome>me|te)\s+levou|levou\s+(?P<agente>{sujeitos}))\s+a\b", base)
        if causativa:
            return papeis[causativa["pronome"] or causativa["agente"]], True
    return "", False


def agente_explicacao_retrospectiva(texto: str) -> str:
    """Projeção temporal da mesma leitura, sem outro parser de agente."""
    agente, retrospectiva = agente_explicacao_causal(texto)
    return agente if retrospectiva else ""


def referencia_explicacao_historica(texto: str) -> str:
    """A obrigação não confunde agente perguntado com o dono da fonte própria."""
    agente = agente_explicacao_retrospectiva(texto)
    if agente and agente != "destinatario":
        return "outro_agente"
    return referencia_explicacao_propria(texto)


def referencia_explicacao_propria(texto: str) -> str:
    """Lê a obrigação retrospectiva, sem resolver ocorrência nem escolher owner.

    A construção causal e o interlocutor são necessários. Flexão passada,
    causativa passada ou posse da decisão/fala qualificam o pedido; o nome da
    habilidade e a presença de um receipt não participam. Retorna ``fala``,
    ``ocorrencia`` ou vazio; não atribui um ID. É leitura limitada
    de linguagem, não prova semântica universal nem autorização operacional.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico, texto_e_metalinguistico

    if texto_e_metalinguistico(texto):
        return ""
    # Conteúdo citado pode ser alvo da consulta, mas não enuncia a consulta.
    fora_de_aspas = re.sub(r'"[^"\n]*"|“[^”\n]*”|«[^»\n]*»|\'[^\'\n]*\'', " ", str(texto or ""))
    base = normalizar_texto_basico(fora_de_aspas)
    if (re.search(r"\b(?:hipoteticamente|(?:se|caso)\s+(?:voce|tu))\b", base)
            or not re.search(r"\b(?:por\s*que|motivo|motivou|razao|causa|levou|explique|explica)\b", base)):
        return ""
    passada = re.search(
        r"\b(?:voce|tu)\s+(?:(?:nao|ja|nunca|ontem)\s+)*"
        r"(?:[a-z]+(?:ou|eu|iu)|fez|disse|quis|foi|teve|deu|pos|viu|veio)\b", base)
    causativa = re.search(r"\b(?:te\s+levou|levou\s+(?:voce|a\s+voce))\s+a\b", base)
    propria = re.search(r"\bsua\s+(?:decisao|escolha|acao|reacao|resposta|fala)\b", base)
    nominal = propria and not re.search(
        r"\b(?:futura|futuro|faria|seria|fara|vai|ira|pretende)\b", base)
    if not (passada or causativa or nominal):
        return ""
    fala = re.search(
        r"\b(?:voce|tu)\s+(?:(?:nao|ja|nunca|ontem)\s+)*"
        r"(?:disse|falou|respondeu|afirmou|explicou)\b|"
        r"\bsua\s+(?:resposta|fala)\b|\ba\s+(?:dizer|falar|responder|afirmar|explicar)\b", base)
    return "fala" if fala else "ocorrencia"


def referencia_explicacao_ocorrencia(texto: str, *, entidades: tuple[str, ...]) -> str:
    """Qualifica retrospectiva de uma entidade, sem decidir fonte ou autoridade.

    Owners fornecem substantivos do seu domínio; a gramática da consulta é
    compartilhada. Uma pergunta geral, futura ou citada não escolhe ocorrência.
    """
    agente, _ = agente_explicacao_causal(texto)
    if agente and agente != "destinatario":
        return ""
    def normalizar(valor: str) -> str:
        return " ".join("".join(c for c in unicodedata.normalize("NFKD", valor.casefold())
                               if not unicodedata.combining(c)).split())
    base = normalizar(str(texto or ""))
    if (re.search(r"\b(?:traduza|tradu[cz]ir|cite|citacao|hipoteticamente|se voce|vai fazer|fara)\b", base)
            or not re.search(r"\b(?:por\s*que|motivo|motivou|razao|causa|explique|explica)\b", base)
            or not any(re.search(rf"\b{re.escape(normalizar(e))}\b", base) for e in entidades)
            or not re.search(r"\b(?:ess[ea]|dess[ea]|daquel[ea]|aquel[ea]|ultim[oa]|anterior|voce fez|voce escolheu|sua decisao)\b", base)):
        return ""
    return "ultima" if re.search(r"\bultim[oa]\b", base) else "referida"


def ids_ocorrencias_citadas(texto: str, ocorrencias: tuple[tuple[str, str], ...]) -> tuple[str, ...] | None:
    """None indica referência implícita; vazio, referência explícita sem fonte.

    Não substituir uma citação desconhecida pela última ocorrência disponível.
    A resolução é a mesma para qualquer owner, sem interpretar motivos/efeitos.
    """
    nomes = {s.casefold().replace("_", " ") for grupo in re.findall(r'"([^"\n]+)"|“([^”\n]+)”', texto)
             for s in grupo if s}
    ids = set(re.findall(r"(?<!\w)[0-9a-f]{32}(?!\w)", texto, flags=re.I))
    ids.update(identidade for identidade, _ in ocorrencias
               if re.search(rf"(?<!\w){re.escape(identidade)}(?!\w)", texto))
    if not ids and not nomes:
        return None
    conhecidos = {identidade for identidade, _ in ocorrencias}
    nomes_conhecidos = {nome.casefold().replace("_", " ") for _, nome in ocorrencias}
    if not ids <= conhecidos or not nomes <= nomes_conhecidos:
        return ()
    return tuple(identidade for identidade, nome in ocorrencias
        if (not ids or identidade in ids) and (not nomes or nome.casefold().replace("_", " ") in nomes))

_PRONOMES = (
    r"ele|ela|eles|elas|isso|isto|aquilo|esse|essa|esses|essas|este|esta|"
    r"estes|estas|aquele|aquela|aqueles|aquelas|desse|dessa|desses|dessas|"
    r"dele|dela|deles|delas|nele|nela|neles|nelas|aqui|ali"
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


def qualificador_referencia_nominal(texto: str) -> tuple[str, str]:
    """Lê tipo e qualificador ditos agora, sem resolver a entidade.

    Em "esse sensor do ar", o foco antigo só é compatível se contiver
    literalmente o tipo e o qualificador. Ausência de ambos não veta a
    continuidade usual. Esta leitura nunca concede autorização operacional.
    """
    achado = re.search(
        r"\b(?:esse|essa|este|esta|esses|essas|estes|estas|"
        r"aquele|aquela|o|a|os|as)\s+"
        r"(?P<tipo>[^\W\d_]+)\s+(?:de|do|da|dos|das)\s+"
        r"(?P<qualificador>[^\W\d_]+"
        r"(?:\s+(?:de|do|da|dos|das)\s+[^\W\d_]+){0,3})\b",
        str(texto or "").casefold(), flags=re.UNICODE,
    )
    if not achado:
        return "", ""
    return achado.group("tipo"), achado.group("qualificador")


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


def separar_tipo_e_alvo_nomeado(valor: str, tipos: tuple[str, ...]) -> tuple[str, str, bool]:
    """Lê uma moldura nominal externa uma vez, preservando o conteúdo do nome.

    O chamador fornece os tipos do domínio, não a decisão/autoridade. Aspas
    completas delimitam um nome literal; palavras internas nunca são limpas.
    Retorna alvo, tipo externo (se houver) e literalidade.
    """
    alvo = re.sub(r"\s+", " ", str(valor or "")).strip()
    tipo = ""
    pares = {'"': '"', "'": "'", "“": "”", "«": "»"}

    def literal(trecho: str) -> bool:
        return bool(len(trecho) >= 2 and trecho[0] in pares
                    and trecho[-1] == pares[trecho[0]]
                    and pares[trecho[0]] not in trecho[1:-1])

    if literal(alvo):
        return alvo[1:-1], tipo, True
    nomes_tipo = "|".join(re.escape(t) for t in tipos if t)
    moldura = re.fullmatch(
        rf"(?:(?:a|o|as|os|uma|um|essa|esse)\s+)?(?P<tipo>{nomes_tipo})"
        r"(?:\s+(?P<alvo>.+))?", alvo, flags=re.IGNORECASE,
    ) if nomes_tipo else None
    # Uma relação nominal ("som do silêncio", "música para estudar") não
    # é prova de um nome que começa depois do tipo. Conservá-la é preferível
    # a perder o núcleo da expressão; aspas já tornam um nome inequívoco.
    relacao_nominal = bool(moldura and re.match(
        r"^(?:de|do|da|dos|das|para|pra|pro)\s+", str(moldura.group("alvo") or ""),
        flags=re.IGNORECASE,
    ))
    if moldura and not relacao_nominal:
        tipo = moldura.group("tipo").casefold()
        alvo = str(moldura.group("alvo") or "").strip()
    else:
        alvo = re.sub(r"^(?:a|o|as|os|uma|um|essa|esse)\s+", "", alvo, flags=re.IGNORECASE)
    if literal(alvo):
        return alvo[1:-1], tipo, True
    return alvo, tipo, False


def separar_alvo_e_repeticao(valor: str) -> tuple[str, bool]:
    """Separa repetição terminal do operando, somente na leitura de comando.

    Nomes integralmente delimitados são literais, mesmo quando terminam em
    ``de novo``. Retira delimitadores completos, não palavras internas.
    Não limpa nomes armazenados, resolve entidades ou autoriza execução.
    """
    alvo = re.sub(r"\s+", " ", str(valor or "")).strip().rstrip(".!?").strip()
    pares = {'"': '"', "'": "'", "“": "”", "«": "»"}

    def literal_completo(trecho: str) -> bool:
        return bool(len(trecho) >= 2 and trecho[0] in pares
                    and trecho[-1] == pares[trecho[0]]
                    and pares[trecho[0]] not in trecho[1:-1])

    if literal_completo(alvo):
        return alvo[1:-1].strip(), False
    match = re.fullmatch(
        r"(?P<alvo>.+?)\s+(?P<repeticao>de\s+novo|novamente|outra\s+vez|mais\s+uma\s+vez)",
        alvo, flags=re.IGNORECASE,
    )
    if not match:
        return alvo, False
    nome = match.group("alvo").strip()
    # Um delimitador aberto impede tratar o final como moldura externa.
    if any(alvo.count(abre) != alvo.count(fecha) for abre, fecha in pares.items() if abre != fecha):
        return alvo, False
    if alvo.count('"') % 2 or alvo.count("'") % 2:
        return alvo, False
    return (nome[1:-1].strip() if literal_completo(nome) else nome), True


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
        r"le|leia|ler|"
        r"selecione|escolhe|escolher|escolha|usa|usar|use|toca|tocar|toque|"
        r"executa|executar|execute)\b|"
        r"\b(?:resultado|resultados|opcao|opcoes|item|itens|arquivo|arquivos|email|e-mail|rascunho)\b",
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


def extrair_indice_fechamento_ordinal_aba(texto: str) -> int | None:
    """Extrai ordinal apenas do fechamento elíptico de uma aba.

    ``Fecha a primeira`` depende de uma sequência causal de abas abertas. A
    função reconhece somente essa moldura; ``primeira janela`` e ``primeiro
    resultado`` continuam pertencendo a outros contratos.
    """
    bruto = str(texto or "").strip()
    base = unicodedata.normalize("NFKD", bruto.casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"\s+", " ", base).strip()
    encontrado = re.fullmatch(
        r"(?:fecha|feche|fechar|encerra|encerre|encerrar)\s+"
        r"(?:(?:a|o)\s+)?"
        r"(?P<ordinal>primeir[oa]|segund[oa]|terceir[oa]|quart[oa]|"
        r"quint[oa]|sext[oa]|setim[oa]|oitav[oa]|non[oa]|decim[oa]|"
        r"\d{1,2}(?:\s*[oa])?)"
        r"(?:\s+(?:aba|guia))?[ .,!?:;]*",
        base,
    )
    if not encontrado:
        return None
    valor = encontrado.group("ordinal")
    numero_texto = re.fullmatch(r"(?P<numero>\d{1,2})(?:\s*[oa])?", valor)
    if numero_texto:
        numero = int(numero_texto.group("numero"))
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


def operando_inicia_com_referencia_contextual(valor: str) -> bool:
    """Lê o núcleo referencial, mesmo quando há modificadores depois dele.

    ``ela à esquerda`` não é um nome materializado. A função não resolve o
    pronome, não escolhe domínio nem concede autoridade. O consumidor fornece
    o operando estrutural, ANTES de apagar suas aspas. Nomes literais completos,
    inclusive dentro de uma moldura nominal, não são referências pronominais.
    """
    bruto = re.sub(r"\s+", " ", str(valor or "")).strip().rstrip(".!?")
    if not bruto:
        return False
    _, _, literal = separar_tipo_e_alvo_nomeado(bruto, tuple(_NOMES_GENERICOS.split("|")))
    if literal:
        return False
    return bool(re.match(
        rf"^(?:(?:o|a|os|as|um|uma)\s+)?(?:{_PRONOMES})\b",
        bruto, flags=re.IGNORECASE,
    ))
