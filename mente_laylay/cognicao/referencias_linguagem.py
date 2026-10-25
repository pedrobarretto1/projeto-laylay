"""Leitura central de referências contextuais na linguagem natural."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
import unicodedata


def pedido_sentido_fala_propria(texto: str) -> bool:
    """Lê sujeito, predicado de significado e objeto deítico de uma pergunta.

    O complemento identifica a fala, sem transformar sentido em causa. Leitura
    atômica limitada: outro agente, citação e atos adicionais não são adotados.
    Não resolve ocorrência, comprova proposição nem concede autoridade.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico

    bruto = str(texto or '').strip()
    if re.search(r'["“”«»\']', bruto):
        return False
    base = normalizar_texto_basico(bruto)
    objeto = r'(?:isso|aquilo|essa (?:frase|parte|resposta|expressao|ideia)|esse trecho)'
    return bool(re.fullmatch(
        rf'o que (?:(?:voce|tu) )?(?:quis|quer) dizer(?: com {objeto})?[?!.]*', base))


def trecho_retificacao_do_enunciador(texto: str) -> str | None:
    """Objeto de uma retificação assertiva do usuário, não de pergunta/citação.

    Sujeito omitido só vale no início da declaração, com prefixo corretivo
    opcional. O verbo dentro de uma pergunta sobre outro ato não corrige alvo.
    """
    bruto = re.sub(r'\s+', ' ', str(texto or '')).strip()
    leitura = re.fullmatch(
        r'(?:[^?;"“”«»\']+[,;]\s*)?(?:(?:a|ah)\s+)?(?:n[aã]o(?: lay(?:lay)?)?\s+)?'
        r'(?:eu )?(?:quis|quero) dizer\s*[:,]?\s*(?P<objeto>[^?]+)?[.!]*',
        bruto, re.IGNORECASE)
    return str(leitura.group('objeto') or '').strip(' .!') if leitura else None


_PADRAO_TRECHO_CITADO = re.compile(r'"[^"\n]*"|“[^”\n]*”|«[^»\n]*»|\'[^\'\n]*\'|‘[^’\n]*’')


def intervalos_citados(texto: str) -> tuple[tuple[int, int], ...]:
    """Intervalos delimitados, incluindo aspas, sem interpretar seu conteúdo."""
    return tuple(m.span() for m in _PADRAO_TRECHO_CITADO.finditer(str(texto or '')))


def texto_fora_de_citacoes(texto: str) -> str:
    """Projeção para ler o ato externo; conteúdo citado continua sendo dado."""
    return _PADRAO_TRECHO_CITADO.sub(' [citacao] ', str(texto or ''))


def pedido_recapitulacao_dialogo(texto: str) -> bool:
    """Escopo retrospectivo explícito; não decide fatos, fontes ou ação.

    O objeto pertence à conversa compartilhada, em vez de um plano externo.
    A recuperação posterior continua limitada e preserva o intervalo inteiro.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico, texto_e_metalinguistico
    if texto_e_metalinguistico(texto):
        return False
    base = normalizar_texto_basico(texto_fora_de_citacoes(texto))
    return bool(re.search(
        r"\b(?:resuma|resume|recapitule|recapitula|relembre|relembra)\b.*"
        r"\b(?:noss[oa]s?|conversamos|conversa|combinamos|dissemos|falamos)\b|"
        r"\bcomo\s+(?:ficou|ficaram|esta|estao)\b.*\b(?:noss[oa]s?|combinad[oa]s?)\b",
        base,
    ))


def pedido_repeticao_literal_da_fala(texto: str) -> bool:
    """Pedido de reproduzir a fala, sem conceder autoridade a seu conteúdo."""
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    base=normalizar_texto_basico(texto_fora_de_citacoes(texto)).strip(' .!?')
    return bool(re.fullmatch(
        r"(?:repete|repita|reproduza|reproduz)\s+(?:literalmente\s+)?"
        r"(?:(?:a\s+)?(?:mesma|ultima|sua|tua)\s+)?(?:a\s+)?"
        r"(?:resposta|fala|frase)(?:\s+(?:anterior|literalmente|igual))?", base,
    ))


def pedido_consulta_fala_usuario(texto: str) -> bool:
    """Lê consulta retrospectiva ao dizer do enunciador, não ao tema citado.

    O pedido pode nomear uma categoria ausente da declaração literal. Isso
    justifica recuperar dados do diálogo, sem inferir sua categoria, resposta,
    verdade ou autorização. Declaração, terceiro e citação não são a consulta.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico, texto_e_metalinguistico

    if texto_e_metalinguistico(texto):
        return False
    if pedido_recapitulacao_dialogo(texto):
        return True
    base = normalizar_texto_basico(texto_fora_de_citacoes(texto)).strip()
    modificadores = r"(?:(?:nao|nunca|ja|antes|realmente|mesmo|tambem)\s+)*"
    preterito = r"(?:disse|falei|contei|comentei|mencionei|afirmei|declarei|expliquei)"
    composto = (r"(?:tinha|havia)\s+(?:dito|falado|contado|comentado|mencionado|"
                r"afirmado|declarado|explicado)")
    relato = (rf"(?:\beu\s+{modificadores}(?:{preterito}|{composto})\b|"
              r"\b(?:falei|contei|comentei|mencionei|afirmei|declarei|expliquei)\b)")
    abertura = re.sub(r"^(?:e|entao)\s+", "", base)
    ato = re.search(relato, abertura)
    if ato is None:
        return False
    prefixo = abertura[:ato.start()].strip()
    if not prefixo:
        return base.endswith('?')
    outro_relato = (rf"{preterito}|{composto}|(?:falou|contou|comentou|mencionou|afirmou|"
                    r"declarou|explicou|diz|fala|conta|comenta|menciona|afirma|declara|explica)")
    if re.search(rf"\b(?:{outro_relato})\b", prefixo):
        # Consultar quem relatou algo sobre o usuário não é consultar o
        # conteúdo do relato do próprio usuário encaixado nessa oração.
        return False
    # A lacuna perguntada deve ligar-se ao próprio verbo de relato. Não basta
    # encontrar uma interrogativa e um relato em orações independentes.
    consulta = re.fullmatch(
        r"(?P<tipo>o que|qual|quais|que|quem|onde|quando|quanto)"
        r"(?:\s+(?P<objeto>[a-z -]{1,120}))?", prefixo)
    if consulta:
        objeto = str(consulta['objeto'] or '')
        objeto = re.sub(r"^(?:(?:foi|era|e|sao|foram|eram)\s+)?", "", objeto)
        objeto = re.sub(r"\bque$", "", objeto).strip()
        if consulta['tipo'] in {'o que','quem','onde','quando'} and objeto:
            return False
        if consulta['tipo'] in {'onde','quando'} and not base.endswith('?'):
            return False
        # Preposição solta não fecha objeto nominal (ex.: comparação entre
        # expressões). Outro verbo de relato antes do enunciador é outro ato.
        return not bool(re.search(
            r"\b(?:entre|de|do|da|dos|das|sobre|com|por|para|pra)$", objeto))
    # A oração relativa explicita o objeto retrospectivo do resumo. A moldura
    # antiga de recapitulação compartilhada já foi tratada acima.
    return bool(re.fullmatch(
        r"(?:resuma|resume|recapitule|recapitula|relembre|relembra)\s+"
        r"[a-z -]{1,120}\s+que", prefixo))


@dataclass(frozen=True, slots=True)
class PerspectivaEnunciador:
    """Papéis do canal capturados pelo host, não prova do conteúdo relatado."""
    turno_id: str
    texto_usuario: str
    falante_entrada: str = field(default="usuario", init=False)
    autora_resposta: str = field(default="laylay", init=False)
    autoriza_execucao: bool = field(default=False, init=False)
    comprova_fato: bool = field(default=False, init=False)

    def vigente(self, texto_usuario: str, turno_id: object) -> bool:
        return bool(self.turno_id and self.texto_usuario
            and str(turno_id) == self.turno_id and texto_usuario == self.texto_usuario)

    def para_prompt(self) -> dict[str, object]:
        return {"falante_entrada": self.falante_entrada, "autora_resposta": self.autora_resposta,
                "origem": "papeis_do_canal", "autoriza_execucao": False, "comprova_fato": False}


def predicado_consulta_modo_pessoal(texto: str) -> str:
    """Lê modo de atividade do enunciador; não prova a atividade ou seus detalhes.

    O consumidor ainda precisa vincular um relato íntegro. Orientação modal,
    citação, metalinguagem e outros atos/agentes não fornecem esse vínculo.
    Não depende do verbo de uma habilidade ou do nome de um objeto.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico, texto_e_metalinguistico
    if intervalos_citados(texto) or texto_e_metalinguistico(texto):
        return ""
    base = normalizar_texto_basico(texto).strip(" .!?")
    m = re.fullmatch(r"(?:como|de que modo|de que maneira)\s+eu\s+(?P<predicado>[^.!?;]+)", base)
    if m is None or re.match(
        r"(?:posso|poderia|devo|deveria|consigo|conseguiria|vou|iria|faria|"
        r"faco|quero|gostaria)\b", m["predicado"],
    ):
        return ""
    return "eu " + m["predicado"]


def divergencias_perspectiva_enunciador(texto_usuario: str, fala: str) -> tuple[str, ...]:
    """Recorte lexical de posse, futuro com objeto e relato explicitamente 'eu'.

    Compara o mesmo núcleo nominal/predicado, sem reescrever texto. Aspas são
    conteúdo; metalinguagem e sujeitos concorrentes não autorizam atribuir uma
    pessoa única. Não resolve paráfrase, objeto implícito ou verdade factual.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico, texto_e_metalinguistico

    if texto_e_metalinguistico(texto_usuario):
        return ()
    entrada = normalizar_texto_basico(texto_fora_de_citacoes(texto_usuario))
    resposta = normalizar_texto_basico(texto_fora_de_citacoes(fala))
    if re.search(r"\b(?:eu\s+ou\s+(?:voce|tu)|(?:voce|tu)\s+ou\s+eu)\b", entrada):
        return ()
    divergencias = []

    def adocao_positiva(inicio: int, base: str = resposta) -> bool:
        prefixo = re.split(r"[.!?;,]", base[:inicio])[-1]
        return not re.search(
            r"\b(?:nao|nunca|jamais|nem)\s+(?:(?:e|era|sou|seria|sera)\s+)?(?:eu\s+que\s+)?$",
            prefixo,
        )

    # O mesmo nome com possuidores concorrentes não escolhe uma identidade.
    posses: dict[str, set[str]] = {}
    for m in re.finditer(r"\b(?P<pessoa>meu|minha|meus|minhas|seu|sua|seus|suas)\s+(?P<nucleo>[a-z]+)\b", entrada):
        posses.setdefault(m["nucleo"], set()).add("usuario" if m["pessoa"].startswith("m") else "outro")
    for m in re.finditer(r"\b(?:meu|minha|meus|minhas)\s+(?P<nucleo>[a-z]+)\b", resposta):
        if posses.get(m["nucleo"]) == {"usuario"} and adocao_positiva(m.start()):
            divergencias.append("posse:" + m["nucleo"])
    pergunta_futuro = re.compile(
        r"\b(?:qual|quais|que)\s+(?:(?:e|sao)\s+)?(?:(?:o|a|os|as)\s+)?"
        r"(?P<nucleo>[a-z]+)\s+(?:que\s+)?eu\s+vou\s+(?P<verbo>[a-z]+r)\b")
    for m in pergunta_futuro.finditer(entrada):
        # Não confundir 'vou usar seu exemplo' com assumir o caderno perguntado.
        predicado = (rf"\b(?:eu\s+)?vou\s+{re.escape(m['verbo'])}\s+"
                     rf"(?:(?:o|a|os|as|um|uma|uns|umas)\s+)?{re.escape(m['nucleo'])}\b")
        if any(adocao_positiva(a.start()) for a in re.finditer(predicado, resposta)):
            divergencias.append("plano:" + m["verbo"] + ":" + m["nucleo"])
    futuro_relato = (r"\b(?:eu\s+)?vou\s+(?P<verbo>[a-z]+r)\s+"
                     r"(?:(?:o|a|os|as|um|uma|uns|umas)\s+)?(?P<nucleo>[a-z]+)\b")
    for m in re.finditer(futuro_relato, entrada):
        # Determinante/preposição não é núcleo nominal. Sem objeto explícito
        # neste recorte, não presumir identidade entre os dois predicados.
        if (m['nucleo'] in {'meu','minha','meus','minhas','seu','sua','seus','suas',
                           'para','pra','de','do','da','em','com','por','ao'}
            or not adocao_positiva(m.start(), entrada)):
            continue
        predicado = (rf"\b(?:eu\s+)?vou\s+{re.escape(m['verbo'])}\s+"
                     rf"(?:(?:o|a|os|as|um|uma|uns|umas)\s+)?{re.escape(m['nucleo'])}\b")
        if any(adocao_positiva(a.start()) for a in re.finditer(predicado, resposta)):
            divergencias.append("plano:" + m["verbo"] + ":" + m["nucleo"])
    # Relato de fala: sujeito explícito evita decidir 'disse' elíptico (eu/ele).
    relato = (r"\beu\s+(?P<verbo>disse|falei|contei|comentei|mencionei|afirmei|declarei|expliquei)"
              r"\s+que\s+(?:(?:o|a|os|as|meu|minha|meus|minhas)\s+)?(?P<nucleo>[a-z]+)\b")
    for m in re.finditer(relato, entrada):
        predicado = (rf"\beu\s+{re.escape(m['verbo'])}\s+que\s+"
                     rf"(?:(?:o|a|os|as|meu|minha|meus|minhas|seu|sua)\s+)?{re.escape(m['nucleo'])}\b")
        if re.search(predicado, resposta):
            divergencias.append("relato:" + m["verbo"] + ":" + m["nucleo"])
    # Grupo coordenado explícito: preserva o mesmo parceiro e predicado,
    # sem decidir a referência de 'nós' isolado nem substituir pronomes.
    grupo = (r"\beu\s+e\s+(?:(?:o|a)\s+)?(?P<parceiro>[a-z]+(?:\s+[a-z]+){0,2}?)"
             r"\s+(?P<auxiliar>[a-z]+mos)\s+(?P<verbo>[a-z]+(?:ando|endo|indo))\b")
    for m in re.finditer(grupo, entrada):
        predicado = (rf"\beu\s+e\s+(?:(?:o|a)\s+)?{re.escape(m['parceiro'])}\s+"
                     rf"{re.escape(m['auxiliar'])}\s+{re.escape(m['verbo'])}\b")
        if any(adocao_positiva(a.start()) for a in re.finditer(predicado, resposta)):
            divergencias.append("grupo:" + m["parceiro"] + ":" + m["verbo"])
    return tuple(dict.fromkeys(divergencias))


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


def ids_ocorrencias_citadas(
    texto: str, ocorrencias: tuple[tuple[str,str],...], *, somente_referencia: bool = False,
) -> tuple[str, ...] | None:
    """None indica referência implícita; vazio, referência explícita sem fonte.

    Não substituir uma citação desconhecida pela última ocorrência disponível.
    A resolução é a mesma para qualquer owner, sem interpretar motivos/efeitos.
    """
    if somente_referencia:
        from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
        fora=re.sub(r'"[^"\n]*"|“[^”\n]*”', ' ',texto)
        for identidade,_ in ocorrencias:
            if identidade:fora=re.sub(rf'(?<!\w){re.escape(identidade)}(?!\w)',' ',fora)
        moldura=normalizar_texto_basico(fora).strip(' .,!?:;')
        if moldura not in {'','a alegacao','a afirmacao'}:return None
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


@dataclass(frozen=True, slots=True)
class ReferenciaNominalProposicao:
    """Restrições lexicais; nunca identidade resolvida, fonte ou autorização."""
    papeis: tuple[str, ...]
    grandeza: str = ""
    metodo: str = ""
    referencial: str = ""
    qualificador: str = ""


def papeis_referencia_proposicao(
    texto: str, *, exigir_deitico: bool = False, somente_nominal: bool = False,
) -> tuple[str, ...] | None:
    """Compatibilidade para consumidores que precisam somente do papel lexical."""
    leitura = referencia_nominal_proposicao(texto, exigir_deitico=exigir_deitico,
        somente_nominal=somente_nominal)
    return leitura.papeis if leitura is not None else None


def referencia_nominal_proposicao(
    texto: str, *, exigir_deitico: bool = False, somente_nominal: bool = False,
    permitir_elipse: bool = False,
) -> ReferenciaNominalProposicao | None:
    """Lê papel e grandeza nominal integral; o owner confere a própria fonte.

    None não declarou este recorte; papéis vazios declaram referência cuja
    moldura não resolvemos. Não resolve identidade, paráfrase, verdade ou ação.
    Grandeza, método e referencial são nomes integrais, sem aproximação.
    Elipse sem papel exige escopo estrito solicitado pelo owner; qualificador
    sem campo só pode ser conferido contra opções efetivamente apresentadas.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico

    fora_de_aspas = re.sub(r'"[^"\n]*"|“[^”\n]*”|«[^»\n]*»|\'[^\'\n]*\'', " ", str(texto or ""))
    base = normalizar_texto_basico(fora_de_aspas).strip(" .!?;:")
    papeis = {"meta": ("meta",), "objetivo": ("meta",),
        "medicao": ("medicao",), "medida": ("medicao",),
        "diferenca": ("comparacao",), "comparacao": ("comparacao",),
        "conclusao": ("comparacao",), "valor": ("meta", "medicao", "comparacao"),
        "numero": ("meta", "medicao", "comparacao")}
    determinantes = "esse|essa|este|esta|desse|dessa|deste|desta|nesse|nessa|neste|nesta|aquele|aquela|daquele|daquela"
    if not exigir_deitico:
        determinantes += "|o|a"
    molde = r"\b(?:" + determinantes + r")\s+"
    achados = list(re.finditer(molde + r"(?P<papel>" + "|".join(papeis) + r")\b", base))
    if not achados:
        if not (permitir_elipse and somente_nominal and not exigir_deitico):return None
        elipse=re.fullmatch(molde+r"(?:de|do|da)\s+([a-z0-9_]+(?:[ -][a-z0-9_]+)*)",base)
        if elipse and len(elipse[1])<=240:
            return ReferenciaNominalProposicao(('meta','medicao','comparacao'),qualificador=elipse[1])
        complemento=re.sub(r"^(?:"+determinantes+r")\s+",'',base,count=1)
        if not re.match(r"^(?:(?:pelo|por|com o) metodo|(?:no|com) referencial)\s+",complemento):return None
        escolhidos=('meta','medicao','comparacao')
    else:
        if len(achados) != 1:
            return ReferenciaNominalProposicao(())
        achado, = achados
        if somente_nominal and achado.start()!=0:
            return None
        complemento = base[achado.end():].strip()
        escolhidos = papeis[achado['papel']]
    if not complemento or complemento in {"aqui", "ai"}:
        return ReferenciaNominalProposicao(escolhidos)
    qualificadores = {"solicitado": ("meta",), "medido": ("medicao",),
        "da meta": ("meta",), "da medicao": ("medicao",), "da medida": ("medicao",),
        "da diferenca": ("comparacao",), "da comparacao": ("comparacao",)}
    if complemento in qualificadores:
        return ReferenciaNominalProposicao(tuple(p for p in escolhidos if p in qualificadores[complemento]))
    marcadores=list(re.finditer(r"(?:^|\s)(?:e\s+)?(?:(?P<metodo>(?:pelo|por|com o) metodo)|"
        r"(?P<referencial>(?:no|com) referencial))\s+",complemento))
    nomes={}
    prefixo=complemento[:marcadores[0].start()].strip() if marcadores else complemento
    if prefixo:
        grandeza=re.fullmatch(r"(?:de|do|da)\s+([a-z0-9_]+(?:[ -][a-z0-9_]+)*)",prefixo)
        if not grandeza:return ReferenciaNominalProposicao(())
        nomes['grandeza']=grandeza[1]
    for i,marcador in enumerate(marcadores):
        campo='metodo' if marcador['metodo'] else 'referencial'
        valor=complemento[marcador.end():marcadores[i+1].start() if i+1<len(marcadores) else len(complemento)].strip()
        if campo in nomes or not re.fullmatch(r"[a-z0-9_]+(?:[ -][a-z0-9_]+)*",valor):
            return ReferenciaNominalProposicao(())
        nomes[campo]=valor
    if nomes and all(len(v)<=240 for v in nomes.values()):
        return ReferenciaNominalProposicao(escolhidos,**nomes)
    # Não ignorar um complemento desconhecido para voltar ao último item.
    return ReferenciaNominalProposicao(())

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
