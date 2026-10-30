"""Leitura central de referências contextuais na linguagem natural."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
import unicodedata


_MOLDURA_NARRATIVA = re.compile(
    r'\b(?:na|nesta|nessa)\s+(?:(?:minha|nossa)\s+)?(?:hist[oó]ria|fic[cç][aã]o)\s*[:,]\s*(?=\S)', re.I)


def moldura_narrativa_inicial(texto: str) -> bool:
    """Adjunto explícito que governa a oração seguinte, antes de segmentá-la.

    Não reconhece nomes de arquivos ou histórias reais. A fronteira forte de
    outra oração continua pertencendo ao segmentador; não é veto do turno.
    """
    return bool(_MOLDURA_NARRATIVA.match(str(texto or '').lstrip()))


def contem_moldura_narrativa(texto: str) -> bool:
    """Mesma moldura no pedido; não decide o alcance de outro ato independente."""
    return bool(_MOLDURA_NARRATIVA.search(str(texto or '')))


def contem_agradecimento_autoral(texto: str) -> bool:
    """Gratidão enunciada não é particípio de obrigação nem conteúdo citado.

    A leitura é compartilhada pelos consumidores afetivos e comunicativos;
    não conclui que houve ajuda, execução ou resultado anterior.
    """
    from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia
    base = unicodedata.normalize('NFC', texto_fora_de_citacoes(texto)).casefold()
    for m in re.finditer(r'\b(?:obrigad[oa]?|brigad[oa]?|valeu|valew|vlw)\b', base):
        if 'brigad' in m[0]:
            antes = re.split(r'[.!?;,]', base[:m.start()])[-1]
            if re.search(r'\b(?:sou|somos|fui|foi|era|eram|serei|ser|sendo|estou|estava|sinto(?:-me)?)'
                         r'\s+(?:(?:muito|mesmo)\s+)?$', antes):
                continue
            complemento = re.match(r'\s+a\s+(.+)', base[m.end():])
            if complemento:
                dever = False
                for palavra in re.findall(r'[^\W\d_]+', complemento[1])[:3]:
                    if palavra in {'me','te','se','nos','vos'}:
                        continue
                    tipo = consultar_morfologia(palavra) or 0
                    if tipo&32 and re.fullmatch(r'[^\W\d_]*(?:ar|er|ir|or|ôr)', palavra):
                        dever = True
                        break
                    if not tipo&64:
                        break
                if dever:
                    continue
        return True
    return False


def agradecimento_sem_outro_conteudo(texto: str) -> bool:
    """A gratidão integral permite fechar; a presença do ato não fecha outros."""
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    if not contem_agradecimento_autoral(texto):
        return False
    base=normalizar_texto_basico(texto)
    # Uma coordenação pode introduzir outro predicado. Sem prova de escopo
    # nominal integral, não impor encerramento; a gratidão continua reconhecida.
    if re.search(r'\b(?:e|mas|porem|ou)\b',normalizar_texto_basico(texto_fora_de_citacoes(texto))):
        return False
    return bool(re.fullmatch(r'(?:muito\s+)?(?:obrigad[oa]?|brigad[oa]?|valeu|valew|vlw)'
        r'(?:[, ]+(?:lay|laylay))?(?:\s+(?:por|pel[oa]s?)\s+[^?!;.,]+)?[.! ]*',base))


def objeto_retificacao_assunto(texto: str) -> str | None:
    """Retificação nominal do próprio falante, sem reinterpretar o alvo como ação."""
    bruto = str(texto or '').strip()
    if intervalos_citados(bruto):
        return None
    m = re.fullmatch(r'(?:eu\s+)?(?:estou|t[oô])\s+falando\s+'
        r'(?:de|do|da|dos|das)\s+(?P<objeto>[\w]+(?:[ -][\w]+){0,5})[.!]*', bruto, re.I)
    return m['objeto'].strip() if m else None


def operando_opiniao_literal(valor: str) -> bool:
    """Recorte nominal compartilhado; não confunde uma oração com um nome.

    Referências de pessoa/posse e conectores de oração exigem outra resolução.
    Recusar esse recorte não decide a verdade da opinião ou da possível causa.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    return bool(re.fullmatch(r'[\w]+(?:[ -][\w]+){0,3}', valor)
        and not operando_inicia_com_referencia_contextual(valor)
        and not re.search(r'\b(?:eu|mim|me|nos|nosso|nossa|nossos|nossas|voce|vc|tu|ti|te|vos|'
            r'meu|minha|meus|minhas|seu|sua|seus|suas|teu|tua|teus|tuas|ou|'
            r'porque|pois|quando|embora|portanto|que|se)\b', normalizar_texto_basico(valor)))


# Vocabulário nominal e flexão, compartilhados pela leitura e pela autoria.
# Não é catálogo de obras, de gostos ou de capacidades disponíveis.
CATEGORIAS_PREFERENCIA = {
    'jogo': ('jogo', 'jogos', 'o'), 'filme': ('filme', 'filmes', 'o'),
    'livro': ('livro', 'livros', 'o'), 'musica': ('música', 'músicas', 'a'),
    'serie': ('série', 'séries', 'a'), 'cor': ('cor', 'cores', 'a'),
    'comida': ('comida', 'comidas', 'a'), 'animal': ('animal', 'animais', 'o'),
}


def consulta_adequacao_pessoal(texto: str) -> str | None:
    """Lê categoria e relação com o enunciador, sem decidir o que lhe convém.

    Recorte integral de pergunta nominal, inclusive com moldura de pedido de
    fala e vocativo. Outra oração, pessoa, tempo ou conteúdo citado não é
    absorvido; o nome da assistente não se torna identidade do usuário.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    from mente_laylay.cognicao.identidade_conversacional import IDENTIDADE_LAYLAY
    if intervalos_citados(texto):
        return None
    base = normalizar_texto_basico(texto)
    nomes = '|'.join(re.escape(n) for n in IDENTIDADE_LAYLAY['apelidos'])
    vocativo = rf'(?:{nomes})\s*[,;:]\s*'
    m = re.fullmatch(rf'(?:{vocativo})?(?:(?:me\s+)?(?:fala|fale|diz|diga|conta|conte)'
        rf'(?:\s*[,;:]\s*|\s+)(?:{vocativo})?)?(?:que|qual)\s+(?:[oa]\s+)?'
        r'(?P<categoria>[\w]+(?:[ -][\w]+){0,3}?)\s+(?:que\s+)?(?:mais\s+)?combina'
        r'(?:\s+mais)?\s+comigo[?!.]*', base)
    categoria = m['categoria'] if m else ''
    return categoria if categoria and operando_opiniao_literal(categoria) else None


def consulta_opiniao_propria(texto: str, *, explicativa: bool = False) -> dict[str, object] | None:
    """Lacuna subjetiva simples; não prova gosto, causa, experiência ou efeito."""
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    if intervalos_citados(texto):
        return None
    base = normalizar_texto_basico(texto)
    literal = re.sub(r'\s+', ' ', unicodedata.normalize('NFC', texto).casefold()).strip()
    # A moldura de esclarecimento preserva a pergunta subordinada integral;
    # não aproveita um fragmento de pergunta seguida por outra instrução.
    literal = re.sub(r'^(?:eu\s+)?(?:estou|t[oô])\s+(?:s[oó]|apenas)\s+perguntando\s+se\s+', '', literal)
    base = normalizar_texto_basico(literal)
    sujeito = r'(?:voc[eê]|vc|tu|laylay|lay)'
    nominal = r'[\w]+(?:[ -][\w]+){0,3}'

    # A moldura interrogativa não decide a categoria: as formas nominal e
    # existencial consultam o MESMO vocabulário, inclusive nomes compostos.
    # A leitura continua integral; capturar palavras não qualifica tipo novo.
    categoria_perguntada = re.fullmatch(
        rf'(?:e\s+)?(?:(?P<existencial>{sujeito}\s+tem\s+um[a]?)|'
        r'qual\s+(?:e\s+)?(?:[oa]\s+)?(?:seu|sua|teu|tua))\s+'
        r'(?P<categoria>[\w]+(?:\s+[\w]+){0,3}?)(?:\s+(?P<qualificador>favorit[oa]|preferid[oa]))?[?!.]*', base)
    if categoria_perguntada:
        categoria = categoria_perguntada['categoria']
        qualificador = categoria_perguntada['qualificador']
        if categoria in {'estilo musical', 'genero', 'genero musical'}:
            if qualificador or not categoria_perguntada['existencial']:
                return {'tipo': 'categoria', 'categoria': 'genero_musical'}
        elif qualificador and categoria in CATEGORIAS_PREFERENCIA:
            return {'tipo': 'favorito', 'categoria': categoria}
    # Espaço deslocado na preposição só é recuperado quando o operando
    # reconstruído tem tipo nominal conhecido. "d eminem" permanece ambíguo.
    deslocada = re.fullmatch(rf'(?P<inicio>(?:e\s+)?{sujeito}\s+(?:gosta|curte|aprecia))\s+d\s+e(?P<alvo>{nominal})[?!.]*', literal)
    if deslocada:
        from mente_laylay.memoria_mental.memoria_pessoas import classificar_gosto_explicito
        alvo = normalizar_texto_basico(deslocada['alvo'])
        if (alvo in CATEGORIAS_PREFERENCIA
            or classificar_gosto_explicito(alvo)[0] == 'genero_musical'):
            literal = deslocada['inicio'] + ' de ' + deslocada['alvo']
    existencial = re.fullmatch(rf'(?:e\s+)?{sujeito}\s+(?:gosta|curte|aprecia)\s+de\s+'
        r'(?:algu[mn]a?|algum[as]+)\s+(?P<categoria>[\w]+)[?!.]*', literal)
    if existencial:
        categoria = normalizar_texto_basico(existencial['categoria'])
        if categoria in CATEGORIAS_PREFERENCIA:
            return {'tipo': 'polar', 'alvo': CATEGORIAS_PREFERENCIA[categoria][1],
                    'predicado': 'gostar', 'negada': False}
    polar = re.fullmatch(rf'(?:e\s+)?{sujeito}\s+(?P<negacao>n[aã]o\s+)?(?:gosta|curte|aprecia)\s+'
        rf'(?:de|do|da|dos|das)\s+(?P<alvo>{nominal})[?!.]*', literal)
    if polar and operando_opiniao_literal(polar['alvo']):
        return {'tipo': 'polar', 'alvo': polar['alvo'], 'predicado': 'gostar', 'negada': bool(polar['negacao'])}
    escolha = re.fullmatch(rf'(?:e\s+)?{sujeito}\s+prefere\s+'
        rf'(?P<a>{nominal})\s+ou\s+(?P<b>{nominal})[?!.]*', literal)
    if escolha and all(operando_opiniao_literal(escolha[c]) for c in ('a', 'b')):
        return {'tipo': 'escolha', 'alternativas': (escolha['a'], escolha['b'])}
    if explicativa:
        preferencia = re.fullmatch(rf'{sujeito}\s+(?P<negacao>n[aã]o\s+)?prefere\s+(?P<alvo>{nominal})[?!.]*', literal)
        if preferencia and operando_opiniao_literal(preferencia['alvo']):
            return {'tipo': 'preferencia_nomeada', 'alvo': preferencia['alvo'],
                    'predicado': 'preferir', 'negada': bool(preferencia['negacao'])}
    return None


def consulta_explicacao_gosto(texto: str) -> dict[str, object] | None:
    """Pergunta de motivo de gosto presente; não seleciona fala nem comprova causa."""
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    if intervalos_citados(texto):
        return None
    base = re.sub(r'\s+', ' ', unicodedata.normalize('NFC', texto).casefold()).strip()
    m = re.fullmatch(r'(?:e\s+|mas\s+)?por\s*qu[eê](?:\s+(?P<corpo>[^?!.;]+))?[?!.]*', base)
    if not m:
        return None
    if not m['corpo']:
        return {'tipo': 'eliptica'}
    leitura = consulta_opiniao_propria(m['corpo'], explicativa=True)
    if leitura is None or leitura['tipo'] not in {'polar', 'preferencia_nomeada'}:
        return None
    return {'tipo': 'explicita', 'predicado': leitura['predicado'],
            'alvo': normalizar_texto_basico(str(leitura['alvo'])), 'negada': leitura['negada']}


def consulta_relacao_criterio_autoral(texto: str) -> bool:
    """Consulta atômica sobre critério próprio; não resolve fonte nem adequação.

    Sujeito deítico de informação e objeto avaliativo distinguem esta relação
    de causa/resultado de execução. Outra pessoa, citação ou complemento de
    operação exige seu próprio owner.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    if intervalos_citados(texto):
        return False
    base = normalizar_texto_basico(texto)
    criterio = r'(?:(?:o\s+)?(?:seu|teu)|esse|este|aquele)\s+criterio'
    informacao = r'(?:essa|esta|aquela)\s+(?:descricao|fonte|informacao)'
    return any(re.fullmatch(padrao+r'[?!.]*',base) for padrao in (
        rf'por\s*que\s+{criterio}',
        rf'{informacao}\s+(?:justifica|fundamenta|sustenta|comprova)\s+{criterio}',
        rf'qual\s+(?:e\s+)?a\s+relacao\s+entre\s+{informacao}\s+e\s+{criterio}',
        rf'como\s+{informacao}\s+se\s+relaciona\s+(?:a|ao|com)\s+{criterio}',
    ))


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


def enunciados_discursivos(texto: str) -> tuple[str, ...]:
    """Fronteiras fortes literais fora de aspas; não interpreta atos/intents.

    Um segmento do turno pode agrupar várias frases. A interrogação de uma
    delas não muda o valor enunciativo das demais. Preserva o conteúdo citado.
    """
    bruto = str(texto or '')
    citados = intervalos_citados(bruto)
    inicio = 0
    trechos = []
    for m in re.finditer(r'[.!?;]+(?=\s|$)', bruto):
        if any(a <= m.start() < b for a,b in citados):
            continue
        if trecho := bruto[inicio:m.end()].strip():
            trechos.append(trecho)
        inicio = m.end()
    if trecho := bruto[inicio:].strip():
        trechos.append(trecho)
    return tuple(trechos)


def declaracao_pessoal_de_estado(texto: str) -> str:
    """Complemento de predicado pessoal explícito, sem inferir um sentimento.

    Complementa estar+adjetivo dos leitores sociais; função afetiva, menção
    de terceira pessoa, citação e hipótese não fornecem essa declaração.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    for frase in enunciados_discursivos(texto_fora_de_citacoes(texto)):
        base=normalizar_texto_basico(frase).strip(' .!?;')
        m=re.match(r'^(?:eu\s+)?(?:me\s+sinto|sinto-me)\s+(?P<estado>[^?!;]+)$',base)
        if not m:
            m=re.match(r'^(?:eu\s+)?(?:estou|to)\s+com\s+'
                r'(?P<estado>medo|raiva|ansiedade|sono|fome)\b[^?!;]*$',base)
        if m:
            return m['estado'].strip()
    return ''


def texto_de_reproducao_solicitada(texto: str) -> str:
    """Objeto literal de reprodução no canal, sem autorizar efeito externo."""
    m=re.fullmatch(r'(?:(?:voce|voc[eê]|tu)\s+)?'
        r'(?:repita|repete|copie|copia|reproduza|reproduz)\s+'
        r'(?:(?:exatamente|literalmente)\s+)?(?:(?:a|o)\s+)?'
        r'(?:(?:este|esta|esse|essa|minha|meu|seguinte)\s+){0,2}'
        r'(?:texto|frase|trecho|mensagem)(?:\s+sem\s+alterar\s+(?:nenhuma|qualquer)\s+palavra)?'
        r'\s*:\s*(?P<objeto>[\s\S]+)',str(texto or '').strip(),re.I)
    if not m:
        return ''
    objeto=m['objeto'].strip()
    if intervalos_citados(objeto)==((0,len(objeto)),):
        objeto=objeto[1:-1]
    return objeto


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
        r"(?:(?:repete|repita|reproduza|reproduz)|"
        r"(?:(?:voce|tu)\s+)?(?:pode|poderia|consegue|conseguiria)\s+(?:repetir|reproduzir))\s+(?:literalmente\s+)?"
        r"(?:a\s+)?(?:(?:mesma|ultima|sua|tua)\s+){0,2}(?:a\s+)?"
        r"(?:resposta|fala|frase)(?:\s+(?:anterior|literalmente|igual))?", base,
    ))


def pedido_retomada_fala_assistente(texto: str) -> bool:
    """Reprodução ou consulta retrospectiva à fala da interlocutora.

    Isenta apenas o veto de texto repetido; não resolve qual fala responde à
    consulta, não certifica conteúdo e não autoriza repetir ações descritas.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    if pedido_repeticao_literal_da_fala(texto):
        return True
    base = normalizar_texto_basico(texto_fora_de_citacoes(texto)).strip(' .!?')
    return bool(re.fullmatch(
        r"(?:qual\s+foi\s+(?:exatamente\s+)?(?:a\s+)?(?:sua\s+)?(?:ultima\s+)?"
        r"(?:resposta|fala|frase|piada)(?:\s+que\s+(?:voce|tu)\s+acabou\s+de\s+"
        r"(?:contar|dizer|falar))?|o\s+que\s+(?:voce|tu)\s+acabou\s+de\s+(?:dizer|falar|contar))", base,
    ))


def _abertura_consulta_fala_usuario(texto: str) -> str:
    """Mesma abertura discursiva no detector e na leitura dos complementos."""
    return re.sub(r'^(?:e|ent[aã]o)\s+', '', texto, flags=re.I)


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
    abertura = _abertura_consulta_fala_usuario(base)
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


PREDICADOS_PREFERENCIA = {
    'gosto': 'gostar', 'gosta': 'gostar', 'gostava': 'gostar', 'gostar': 'gostar',
    'prefiro': 'preferir', 'prefere': 'preferir', 'preferia': 'preferir', 'preferir': 'preferir',
    'curto': 'curtir', 'curte': 'curtir', 'curtia': 'curtir', 'curtir': 'curtir',
    'adoro': 'adorar', 'adora': 'adorar', 'adorava': 'adorar', 'adorar': 'adorar',
}


def consulta_categoria_preferencia_usuario(texto: str) -> dict[str, object] | None:
    """Categoria da lacuna pessoal, sem inferir o tipo de nenhum nome."""
    from mente_laylay.cognicao.normalizacao_linguagem import texto_e_metalinguistico
    bruto = re.sub(r'\s+', ' ', str(texto or '')).strip()
    if intervalos_citados(bruto) or texto_e_metalinguistico(bruto):
        return None
    base = _abertura_consulta_fala_usuario(bruto)
    verbos = '|'.join(PREDICADOS_PREFERENCIA)
    m = re.fullmatch(
        r'(?:qual|que)\s+(?P<categoria>[\w -]{1,50}?)\s+(?:que\s+)?eu\s+'
        rf'(?P<relato>.*?)(?P<negacao>n[aã]o\s+)?(?P<predicado>{verbos})[?!.]*', base, re.I)
    if not m or (m['relato'].strip() and not pedido_consulta_fala_usuario(bruto)):
        return None
    return {'categoria': m['categoria'].strip(),
            'predicado': PREDICADOS_PREFERENCIA[m['predicado'].casefold()],
            'negada': bool(m['negacao']), 'retrospectiva': bool(m['relato'].strip()),
            'ato_relato_negado': bool(re.search(r'\b(?:n[aã]o|nunca|jamais)\b', m['relato'], re.I))}


def recorte_consulta_fala_usuario(texto: str) -> dict[str, str] | None:
    """Lê o conteúdo explícito consultado, sem escolher fonte ou validar resposta.

    O detector canônico decide antes se há consulta ao dizer do usuário. Aqui
    só se expõe o complemento de uma pergunta polar ou o tópico nominal de
    uma pergunta aberta. Categorias implícitas, elipses e comparação livre não
    recebem uma resolução inventada. Nenhum dado vem da proposta da LLM.
    """
    bruto = re.sub(r'\s+', ' ', str(texto or '')).strip()
    if not pedido_consulta_fala_usuario(bruto) or intervalos_citados(bruto):
        return None
    bruto = _abertura_consulta_fala_usuario(bruto)
    polar = re.fullmatch(
        r'eu\s+[^?!.;]+?\s+que\s+(?P<conteudo>[^?!.;]+?)[?!.]*', bruto, re.I)
    if polar:
        return {'tipo': 'proposicao_literal', 'conteudo': polar['conteudo'].strip()}
    aberta = re.fullmatch(
        r'(?:o que|que)\s+[^?!.;]+?\s+(?:sobre|a respeito de|acerca de)\s+'
        r'(?P<conteudo>[\w -]{1,120})[?!.]*', bruto, re.I)
    if aberta:
        return {'tipo': 'topico_literal', 'conteudo': aberta['conteudo'].strip()}
    return None


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


def natureza_predicado_pessoal(predicado: str) -> str:
    """Distingue posição avaliativa simples de atribuição pessoal não conferida.

    Lê o predicado inteiro, não uma frase histórica ou o tema da conversa.
    Concordância e discordância são posições do emissor no diálogo, não relatos
    de estado da pessoa. Complementos e circunstâncias saem deste recorte.
    O resultado classifica linguagem; não prova correção, verdade ou efeito.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    texto = normalizar_texto_basico(predicado).strip(' .!?')
    avaliativo = r'(?:cert|corret|incorret|errad|equivocad|enganad)[oa]'
    if re.fullmatch(rf'(?:(?:esta|ta)\s+{avaliativo}|tem\s+razao)', texto):
        return 'posicionamento_dialogico'
    modificada = re.fullmatch(rf'(?:esta|ta)\s+(?P<modificadores>(?:[a-z]+\s+){{1,2}}){avaliativo}',texto)
    if modificada:
        from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia
        if all((consultar_morfologia(p) or 0)&64 for p in modificada['modificadores'].split()):
            return 'posicionamento_dialogico'
    return 'atribuicao_pessoal_nao_conferida'


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


def pergunta_confirmatoria_eliptica(texto: str) -> bool:
    """Lê a pergunta dependente de uma proposição, sem dar consentimento.

    A cópula elidida ou com complemento deítico/avaliativo retoma o enunciado
    anterior. Uma pergunta com objeto próprio não herda aquele enunciado.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
    if not str(texto or '').rstrip().endswith('?') or intervalos_citados(texto):
        return False
    base = normalizar_texto_basico(texto).strip(' ?!.')
    avaliacao = r'(?:cert[oa]|corret[oa]|verdade)'
    return bool(re.fullmatch(
        rf'(?:ne|confere|procede|{avaliacao}|(?:nao\s+)?e'
        rf'(?:\s+(?:isso(?:\s+mesmo)?|{avaliacao}))?)', base))


def referencia_explicacao_propria(texto: str) -> str:
    """Lê a obrigação retrospectiva, sem resolver ocorrência nem escolher owner.

    A consulta retrospectiva e o interlocutor são necessários. Flexão passada,
    causativa passada ou posse da decisão/fala qualificam o pedido; o nome da
    habilidade e a presença de um receipt não participam. Retorna ``fala``,
    ``ocorrencia`` ou vazio; não atribui um ID. É leitura limitada
    de linguagem, não prova semântica universal nem autorização operacional.
    """
    from mente_laylay.cognicao.normalizacao_linguagem import (
        normalizar_texto_basico, texto_e_metalinguistico, remover_conector_discursivo_inicial,
    )

    if texto_e_metalinguistico(texto):
        return ""
    # Conteúdo citado pode ser alvo da consulta, mas não enuncia a consulta.
    fora_de_aspas = re.sub(r'"[^"\n]*"|“[^”\n]*”|«[^»\n]*»|\'[^\'\n]*\'', " ", str(texto or ""))
    unidades = [p.strip() for p in re.split(r'[.!?;]+', fora_de_aspas) if p.strip()]
    if len(unidades)>1:
        # Pergunta causal e atribuição passada precisam pertencer ao mesmo
        # recorte. Uma pergunta temática posterior não herda um "você disse"
        # de outra frase. A elipse causal explícita conserva seu antecedente.
        for i, unidade in enumerate(unidades):
            elipse = normalizar_texto_basico(remover_conector_discursivo_inicial(unidade))
            if i and re.fullmatch(
                r'(?:(?:(?:me\s+)?(?:explique|explica)\s+)?por\s+que|'
                r'(?:por\s+)?(?:qual|quais)\s+(?:(?:e|foi|sao|foram)\s+)?(?:(?:o|a|os|as)\s+)?'
                r'(?:motivos?|razao|razoes|causas?))', elipse):
                unidade = unidades[i-1] + ', ' + unidade
            referencia = referencia_explicacao_propria(unidade)
            if referencia:
                return referencia
        return ""
    base = normalizar_texto_basico(fora_de_aspas)
    if re.search(r"\b(?:hipoteticamente|(?:se|caso)\s+(?:voce|tu))\b", base):
        return ""
    # Uma consulta temporal pode pedir resultados, não só causas. A moldura
    # exige atribuição passada à própria fala e uma pergunta matriz fora da
    # citação; o literal sozinho não decide a finalidade nem prova o resultado.
    temporal = re.match(r'^quando\s+(?:(?:voce|tu)\s+)?(?:disse|falou|respondeu|afirmou|explicou)\b'
                r'[^,?]*,\s*(?P<matriz>(?:o que|qual|quais|como|quem|onde|quanto)\b.*)', base)
    # A fala citada é passada, mas a pergunta pode ser futura ou imaginativa.
    # Só a matriz retrospectiva qualifica esta consulta de resultados.
    if temporal and re.search(r'\b(?:estava|estavam|ficou|ficaram|foi|foram|houve|havia|haviam|ocorreu|aconteceu)\b', temporal['matriz']):
        return 'fala'
    if not re.search(
        r"\b(?:por\s+que|(?:qual|quais)\s+(?:(?:e|foi|sao|foram)\s+)?(?:(?:o|a|os|as)\s+)?"
        r"(?:motivos?|razoes|razao|causas?)|"
        r"o\s+que\s+(?:motivou|causou)|que\s+(?:motivo|razao|causa)\s+levou|"
        r"o\s+que\s+(?:(?:me|te)\s+levou|levou\s+(?:voce|tu))\s+a|"
        r"(?:explique|explica))\b", base):
        return ""
    passada = re.search(
        r"\b(?:voce|tu)\s+(?:(?:nao|ja|nunca|ontem)\s+)*"
        r"(?:[a-z]+(?:ou|eu|iu)|fez|disse|quis|foi|teve|deu|pos|viu|veio)\b", base)
    causativa = re.search(r"\b(?:te\s+levou|levou\s+(?:voce|a\s+voce))\s+a\b", base)
    propria = re.search(r"\bsua\s+(?:decisao|escolha|acao|reacao|resposta|fala)\b", base)
    nominal = propria and not re.search(
        r"\b(?:futura|futuro|faria|seria|fara|vai|ira|pretende)\b", base)
    # A atribuição passada também pode elidir o interlocutor: "quando disse
    # ... por quê?". A citação sozinha continua sem finalidade retrospectiva.
    elipse_fala = re.search(r"\bquando\s+(?:disse|falou|respondeu|afirmou|explicou)\b", base)
    motivo_fala = re.search(r"\b(?:motivo|razao|causa)\s+(?:de|para)\s+(?:voce|tu)\s+"
        r"(?:dizer|falar|responder|afirmar|explicar)\b", base)
    if not (passada or causativa or nominal or elipse_fala or motivo_fala):
        return ""
    fala = re.search(
        r"\b(?:voce|tu)\s+(?:(?:nao|ja|nunca|ontem)\s+)*"
        r"(?:disse|falou|respondeu|afirmou|explicou)\b|"
        r"\bsua\s+(?:resposta|fala)\b|\ba\s+(?:dizer|falar|responder|afirmar|explicar)\b", base)
    return "fala" if fala or elipse_fala or motivo_fala else "ocorrencia"


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
