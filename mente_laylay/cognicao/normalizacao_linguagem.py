"""Normalizacao textual compartilhada da mente da Laylay."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


# Fronteira lexical compartilhada, sem atribuir intenção ou autoridade.
# Consumir o operador inteiro antes das alternativas curtas evita deixar
# "e" ou "depois" no núcleo cuja modalidade ainda será conferida pelo owner.
PADRAO_COORDENACAO_OPERACIONAL = (
    r"(?:e\s+(?:depois|em\s+seguida|ent[aã]o)|"
    r"em\s+seguida|depois|ent[aã]o|e)"
)


SAUDACOES_CONVERSACIONAIS = {
    "oi": "Oi! ", "ola": "Olá! ", "bom dia": "Bom dia! ",
    "boa tarde": "Boa tarde! ", "boa noite": "Boa noite! ", "e ai": "E aí! ",
}
SAUDACOES_TEMPORAIS = frozenset({"bom dia", "boa tarde", "boa noite"})


def separar_saudacao_inicial(texto: str) -> tuple[str, str]:
    """Separa a moldura lexical; não decide intenção, sessão ou autoridade.

    Preserva todo o restante, inclusive aspas, negação e interrogação, para
    que o owner confira o ato inteiro. A normalização não apaga pontuação.
    """
    normal = normalizar_texto_curto(texto)
    nucleos = '|'.join(re.escape(s) for s in SAUDACOES_CONVERSACIONAIS)
    abertura = re.match(rf"^(?P<saudacao>{nucleos})"
        r"(?:[ ,]+(?:laylay|lay))?(?:[,!. ]+|$)", normal)
    return ((abertura['saudacao'], normal[abertura.end():]) if abertura else ('', normal))


def separar_adjunto_pessoal_inicial(texto: str) -> tuple[str, str]:
    """Separa preposição e pronome da matriz, sem decidir sua modalidade.

    A vírgula liga o ponto de vista ou beneficiário à oração seguinte. O
    original permanece intacto no segmento; a matriz ainda pode ser ordem.
    Sem vírgula não há esta moldura, inclusive em pedidos de parada.
    """
    bruto = str(texto or "")
    nucleo = remover_conector_discursivo_inicial(bruto)
    adjunto = re.match(
        r"^\s*(?:para|pra)\s+(?:mim|ti|si|voc[eê]s?|n[oó]s|v[oó]s|eles?|elas?)\s*,\s*(?=\S)",
        nucleo, flags=re.IGNORECASE,
    )
    if not adjunto:
        return "", bruto
    # A fonte conserva também o conector e seus offsets. Segmentar e
    # classificar devem enxergar a mesma matriz em "e, para você, ...".
    fim = bruto.index(nucleo) + adjunto.end()
    return bruto[:fim], bruto[fim:]


def remover_conector_discursivo_inicial(texto: str) -> str:
    """Projeta a oração após 'e' inicial, sem classificar ou autorizar.

    Somente o token isolado fora de aspas: não tocar em nomes, 'é', e-mail,
    negação, condição ou conjunções internas. A fonte original fica no turno.
    """
    bruto = str(texto or "").strip()
    return re.sub(r"^e(?:\s*,\s*|\s+)", "", bruto, count=1, flags=re.IGNORECASE)


_MOLDURA_METALINGUISTICA_RE = re.compile(
    r"^(?:"
    r"como\s+(?:eu|voce|você)\s+"
    r"(?:perguntaria|diria|falaria|pediria|escreveria)\b|"
    r"(?:a|essa|esta)\s+(?:frase|palavra|express[aã]o|pergunta|forma)\b"
    r")",
    re.IGNORECASE,
)
_FALA_CITADA_RE = re.compile(
    r"^se\s+eu\s+(?:disser|falar|perguntar|escrever)\b.*"
    r"(?:\"[^\"]+\"|“[^”]+”|«[^»]+»)",
    re.IGNORECASE,
)
_EXEMPLO_METALINGUISTICO_RE = re.compile(
    r"\b(?:[ée]\s+(?:apenas|s[oó])\s+um\s+exemplo|"
    r"isso\s+[ée]\s+(?:uma?\s+)?(?:consulta|pergunta|frase|comando)|"
    r"quer\s+dizer\s+o\s+qu[eê])\b",
    re.IGNORECASE,
)
_CITACAO_INTEGRAL_RE = re.compile(
    r"^\s*(?:\"[^\"]+\"|“[^”]+”|«[^»]+»)(?:\s*[.!?])?\s*$",
    re.DOTALL,
)


def texto_delimita_relato_explicito(texto: str) -> bool:
    """Detecta uma moldura final de relato, não a intenção operacional.

    Só a declaração do próprio falante conta; citações e perguntas ficam fora.
    Outros atos já deliberados devem ser preservados pelo dono do contrato.
    """
    bruto = str(texto or "").strip()
    if "?" in bruto:
        return False
    return bool(re.search(
        r"(?:^|[.;!]\s*)(?:eu\s+)?(?:estou|t[oô])\s+(?:s[oó]|apenas)\s+"
        r"(?:relatando|contando)(?:\s+(?:isso|o\s+ocorrido))?[.!]?\s*$",
        bruto, flags=re.IGNORECASE,
    ))


TIPOS_REFERENCIA_TEXTUAL = frozenset({"relato", "texto", "pedido", "exemplo"})


def texto_discute_evidencia_textual(texto: str) -> bool:
    """Descreve a evidência de um texto como assunto, sem decidir autorização."""
    return bool(re.search(
        r"^(?:esse|este|o|meu|aquele)\s+(?:relato|pedido|exemplo|texto)\s+"
        r"(?:informa|prova|confirma|demonstra|mostra|significa)\b",
        str(texto or "").strip(), flags=re.IGNORECASE,
    ))


def tipo_transformacao_conversacional(texto: str) -> str:
    """Descreve um ato completo sobre a conversa, sem resolver sua fonte.

    O alvo precisa ser discursivo: resumir um arquivo/página/e-mail continua
    no domínio operacional. O match integral não absorve atos subsequentes;
    o classificador canônico permanece dono da segmentação e da autoridade.
    """
    t = re.sub(r"\s+", " ", str(texto or "")).strip().casefold()
    t = "".join(c for c in unicodedata.normalize("NFD", t) if not unicodedata.combining(c))
    prefixo = r"(?:(?:agora|por favor)[, ]+)*(?:(?:voce )?(?:pode|poderia|consegue) (?:me )?)?"
    resumo = (
        r"(?:resuma|resume|resumir|sintetize|sintetiza|sintetizar) "
        r"(?:(?:a ideia|o tema) d[ae] )?"
        r"(?:(?:a|essa|esta|nossa|sua|a nossa|a sua) )"
        r"(?:historia|conversa|distincao|resposta|explicacao|ideia)"
        r"(?: em (?:uma|duas|tres|poucas|\d+) (?:frases?|palavras?))?"
        r"(?:[, ]+sem consultar a tela)?[.!?]*"
    )
    citado = r'(?:"[^"\n]+"|“[^”\n]+”|«[^»\n]+»|\'[^\'\n]+\')'
    comparacao = (
        r"(?:compare|compara|comparar) (?:as |estas |essas )?(?:frases|expressoes) "
        + citado + r" (?:e|com) " + citado
        + r"(?:[, ]+sem executar (?:nenhuma|nada|nenhuma delas))?[.!?]*"
    )
    if re.fullmatch(prefixo + resumo, t):
        return "resumo"
    if re.fullmatch(prefixo + comparacao, t):
        return "comparacao"
    redacao = (
        r"(?:escreva|escreve|escrever|redija|redige|redigir|"
        r"formule|formula|formular|reescreva|reescreve|reescrever) "
        r"(?:a|o|uma|um|essa|esse|esta|este|sua|seu) "
        r"(?:frase|resposta|texto|exemplo|pergunta|explicacao)"
        r"(?: (?:breve|curta|curto|exata|exato))?"
        r"(?: em (?:uma|duas|tres|poucas|\d+) (?:frases?|palavras?))?"
        r"(?: (?:aqui|no chat|nesta conversa))?"
        r"(?:[, ]+sem (?:metafora|metaforas|rodeios))?[.!?]*"
    )
    if re.fullmatch(prefixo + redacao, t):
        return "redacao"
    adjetivo_forma = r"(?:breve|curta|objetiva|direta)"
    modificador_forma = (
        r"(?:em (?:uma?|duas?|tres|quatro|cinco|poucas?|\d+) "
        r"(?:frases?|palavras?|paragrafos?)|"
        rf"de (?:forma|maneira) {adjetivo_forma}(?: e {adjetivo_forma})*|"
        r"brevemente|objetivamente|diretamente|sem (?:metaforas?|rodeios))"
    )
    canal_atual = r"(?:aqui|no chat|nesta conversa)"
    ligacao_forma = r"(?:,\s*(?:e )?| e | )"
    formato = (
        r"(?:responda|responde|responder) "
        + rf"(?:{canal_atual}{ligacao_forma})*{modificador_forma}"
        + rf"(?:{ligacao_forma}(?:{modificador_forma}|{canal_atual}))*[.!?]*"
    )
    # Forma da resposta no canal atual, sem alvo externo. A correspondência
    # integral conserva a autoridade de destinos e de ordens independentes.
    if re.fullmatch(prefixo + formato, t):
        return "formato_resposta"
    return ""


def texto_e_citacao_integral(texto: str) -> bool:
    """Moldura literal integral, sem resolver conteúdo, alvo ou autoridade."""
    return bool(_CITACAO_INTEGRAL_RE.fullmatch(str(texto or "")))


def texto_e_metalinguistico(texto: str) -> bool:
    """Reconhece quando palavras/frases são o assunto, não seu conteúdo.

    A função apenas descreve a moldura discursiva. Ela não interpreta intenção,
    não autoriza execução e não decide qual domínio aparece dentro da citação.
    """
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not bruto:
        return False
    return bool(
        texto_e_citacao_integral(bruto)
        or _MOLDURA_METALINGUISTICA_RE.search(bruto)
        or _FALA_CITADA_RE.search(bruto)
        or _EXEMPLO_METALINGUISTICO_RE.search(bruto)
        or texto_discute_evidencia_textual(bruto)
        or tipo_transformacao_conversacional(bruto) == "comparacao"
    )


CORRECOES_FONETICAS = (
    (r"\bpaly\s*list\b", "playlist"),
    (r"\bplay\s*list\b", "playlist"),
    (r"\bpalylist\b", "playlist"),
    (r"\bplalyst\b", "playlist"),
    (r"\bplalist\b", "playlist"),
    (r"\bcamaitachi\b", "kamaitachi"),
    (r"\bkamaitaxi\b", "kamaitachi"),
    (r"\bkamaytachi\b", "kamaitachi"),
    (r"\byoutub\b", "youtube"),
    (r"\butube\b", "youtube"),
    (r"\bspotifi\b", "spotify"),
    (r"\binstgrm\b", "instagram"),
    (r"\binstagran\b", "instagram"),
)


# A tolerância operacional trabalha apenas sobre a moldura do pedido. Nomes de
# pessoas, músicas, arquivos, apps e playlists ficam fora deste vocabulário.
_VERBOS_OPERACIONAIS = (
    "abre", "abrir", "fecha", "fechar", "maximiza", "maximizar",
    "coloca", "colocar", "toca", "tocar", "pausa", "pausar",
    "continua", "continuar", "retoma", "retomar",
    "liga", "ligar", "desliga", "desligar",
    "cria", "criar", "apaga", "apagar", "remove", "remover",
    "deleta", "deletar", "exclui", "excluir",
    "pesquisa", "pesquisar", "busca", "buscar", "procura", "procurar",
    "encontra", "encontrar", "organiza", "organizar",
    "move", "mover", "renomeia", "renomear",
    "salva", "salvar", "guarda", "guardar", "adiciona", "adicionar",
    "lista", "listar", "mostra", "mostrar", "resume", "resumir",
    "explica", "explicar", "traduz", "traduzir", "cancela", "cancelar",
)

_MOLDURA_ANTES_DO_VERBO = {
    "ei", "lay", "laylay", "por", "favor", "pfv", "voce", "você",
    "pode", "poderia", "consegue", "conseguiria", "sera", "será", "que",
    "eu", "quero", "queria", "gostaria", "preciso", "de", "da", "pra",
    "para", "seria", "possivel", "possível", "tem", "como", "faz", "o",
}

_INTRODUCOES_DE_ENTIDADE = {
    "chamado", "chamada", "chamado", "nome", "intitulado", "intitulada",
}

_PADRAO_DOMINIO_OPERACIONAL = re.compile(
    r"\b(?:"
    r"musica|musicas|playlist|playlists|som|faixa|faixas|midia|volume|"
    r"luz|lampada|ventilador|tomada|dispositivo|aparelho|"
    r"arquivo|arquivos|pasta|pastas|diretorio|desktop|area de trabalho|"
    r"app|aplicativo|programa|janela|aba|navegador|site|pagina|"
    r"agenda|lembrete|compromisso|email|emails|mensagem|notificacao|"
    r"erro|codigo|texto|link|url|clima|tempo"
    r")\b",
    flags=re.IGNORECASE,
)

_CORRECOES_EXATAS_GERAIS = {
    "tduo": "tudo",
    "tdo": "tudo",
    "vc": "voce",
}

_CORRECOES_TERMOS_OPERACIONAIS = {
    "playlit": "playlist",
    "playlits": "playlists",
    "playlsit": "playlist",
    "plaulist": "playlist",
    "muscia": "musica",
    "muisca": "musica",
    "lampda": "lampada",
    "lanpada": "lampada",
    "dispostivo": "dispositivo",
    "dispositvo": "dispositivo",
    "arquvio": "arquivo",
    "arqivo": "arquivo",
    "emial": "email",
    "compromiso": "compromisso",
    "compromisos": "compromissos",
    "lembrente": "lembrete",
    "lenbrete": "lembrete",
    "temperatira": "temperatura",
    # Exceções fechadas e auditáveis para o teste de uso diário. ``Opera`` é
    # um app canônico da instalação, ``calculadora`` é o utilitário canônico
    # do Windows e ``janela`` é parte da moldura, não um nome livre fornecido
    # pelo usuário. A proteção de entidades nomeadas abaixo continua valendo.
    "operra": "opera",
    "calcuradora": "calculadora",
    "janlea": "janela",
}

# Vocabulário pequeno e deliberadamente sem nomes próprios. A aproximação só
# é aplicada quando um verbo ou marcador de consulta já provou que o token faz
# parte da moldura operacional. Argumentos livres continuam opacos.
_TERMOS_OPERACIONAIS_CANONICOS = (
    "playlist", "playlists", "musica", "musicas", "lampada", "lampadas",
    "dispositivo", "dispositivos", "arquivo", "arquivos", "codigo", "codigos",
    "email", "emails", "compromisso", "compromissos", "lembrete", "lembretes",
    "temperatura", "janela",
)

_ERROS_VERBAIS_EXPLICITOS = {
    "fexa": "fecha",
    "colcoa": "coloca",
    "coloac": "coloca",
    "orgniza": "organiza",
    "oragniza": "organiza",
    "pesqisa": "pesquisa",
    "pequisa": "pesquisa",
    "procuar": "procura",
    "encotra": "encontra",
    "adciona": "adiciona",
    "adicoina": "adiciona",
    "canecela": "cancela",
    "renomea": "renomeia",
    "deslgia": "desliga",
    "deslgiar": "desligar",
    "deslga": "desliga",
    "liag": "liga",
    "lgia": "liga",
    "apga": "apaga",
}

_ERROS_VERBAIS_QUE_EXIGEM_DOMINIO = {
    "liag", "lgia", "pequisa",
}


def _distancia_damerau_levenshtein(a: str, b: str) -> int:
    """Distância pequena com suporte a duas letras vizinhas invertidas."""
    a = str(a or "")
    b = str(b or "")
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    matriz = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        matriz[i][0] = i
    for j in range(len(b) + 1):
        matriz[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            custo = 0 if a[i - 1] == b[j - 1] else 1
            matriz[i][j] = min(
                matriz[i - 1][j] + 1,
                matriz[i][j - 1] + 1,
                matriz[i - 1][j - 1] + custo,
            )
            if (
                i > 1 and j > 1
                and a[i - 1] == b[j - 2]
                and a[i - 2] == b[j - 1]
            ):
                matriz[i][j] = min(matriz[i][j], matriz[i - 2][j - 2] + 1)
    return matriz[-1][-1]


def _verbo_operacional_proximo(token: str) -> str:
    token = str(token or "").strip()
    if len(token) < 6 or not token.isalpha():
        return ""
    limite = 1 if len(token) <= 5 else 2
    candidatos = sorted(
        (
            (_distancia_damerau_levenshtein(token, verbo), verbo)
            for verbo in _VERBOS_OPERACIONAIS
            if abs(len(token) - len(verbo)) <= limite
        ),
        key=lambda item: (item[0], len(item[1]), item[1]),
    )
    if not candidatos or candidatos[0][0] > limite:
        return ""
    # Empate entre verbos diferentes é ambiguidade, não autorização.
    if len(candidatos) > 1 and candidatos[1][0] == candidatos[0][0]:
        return ""
    return candidatos[0][1]


def _termo_operacional_proximo(token: str) -> str:
    """Corrige um único deslize inequívoco em substantivo operacional."""
    token = str(token or "").strip()
    if (
        len(token) < 5
        or not token.isalpha()
        or not token.isascii()
        or token in _TERMOS_OPERACIONAIS_CANONICOS
    ):
        return ""
    candidatos = sorted(
        (
            (_distancia_damerau_levenshtein(token, termo), termo)
            for termo in _TERMOS_OPERACIONAIS_CANONICOS
            if abs(len(token) - len(termo)) <= 1
        ),
        key=lambda item: (item[0], len(item[1]), item[1]),
    )
    if not candidatos or candidatos[0][0] > 1:
        return ""
    if len(candidatos) > 1 and candidatos[1][0] == candidatos[0][0]:
        return ""
    return candidatos[0][1]


def corrigir_erros_portugues_operacionais(
    texto: str,
) -> tuple[str, list[dict[str, Any]]]:
    """Corrige deslizes claros sem aproximar os argumentos do comando.

    A função não interpreta nem autoriza ações. Ela só devolve uma versão para
    classificação e metadados auditáveis sobre cada substituição. Aproximação
    ortográfica é aplicada somente ao verbo; termos de domínio exigem moldura
    gramatical explícita e nomes introduzidos por arquivo/pasta/app são opacos.
    """
    normalizado = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not normalizado:
        return "", []
    eventos: list[dict[str, Any]] = []

    for errado, correto in _CORRECOES_EXATAS_GERAIS.items():
        padrao = rf"\b{re.escape(errado)}\b"
        if re.search(padrao, normalizado, flags=re.IGNORECASE):
            normalizado = re.sub(padrao, correto, normalizado, flags=re.IGNORECASE)
            eventos.append({"de": errado, "para": correto, "tipo": "exata"})

    # Recupera um erro conversacional muito estreito somente quando ``vom``
    # ocupa sozinho o predicativo final de uma avaliação (``X é vom``). Não é
    # uma troca global: nomes, títulos e argumentos como ``arquivo vom`` ou
    # ``chamado vom`` continuam opacos.
    if re.fullmatch(r".+\s+(?:e|eh)\s+vom", normalizado, flags=re.IGNORECASE):
        corrigido = re.sub(
            r"\bvom$", "bom", normalizado,
            count=1, flags=re.IGNORECASE,
        )
        if corrigido != normalizado:
            normalizado = corrigido
            eventos.append({
                "de": "vom", "para": "bom", "tipo": "conversa_contextual",
            })

    # ``coloca essa música a playlist X`` é uma forma oral comum de
    # ``... na/à playlist X``. A correção é estreita: exige verbo de adição,
    # referência musical e a palavra playlist. Assim, o nome do destino fica
    # opaco e uma frase casual não ganha autorização operacional por engano.
    if (
        re.search(
            r"\b(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add)\b",
            normalizado,
            flags=re.IGNORECASE,
        )
        and re.search(
            r"\b(?:musica|música|faixa|canção|cancao)\b",
            normalizado,
            flags=re.IGNORECASE,
        )
        and re.search(r"\ba\s+playlist\b", normalizado, flags=re.IGNORECASE)
    ):
        corrigido = re.sub(
            r"\ba\s+(playlist\b)",
            r"na \1",
            normalizado,
            count=1,
            flags=re.IGNORECASE,
        )
        if corrigido != normalizado:
            normalizado = corrigido
            eventos.append({
                "de": "a playlist",
                "para": "na playlist",
                "tipo": "preposicao_operacional",
            })

    # Erro leve muito comum em controle de mídia. A correção só existe dentro
    # da construção completa de avanço, então nomes de faixa ou arquivo
    # chamados "proxma" continuam opacos em qualquer outro contexto.
    if re.search(
        r"\b(?:passa|pasa|pula|pule)(?:\s+(?:para|pra|pro))?\s+(?:a\s+)?"
        r"proxma(?:\s+(?:musica|música|faixa))?\b",
        normalizado,
        flags=re.IGNORECASE,
    ):
        corrigido = re.sub(
            r"\bproxma\b", "proxima", normalizado,
            count=1, flags=re.IGNORECASE,
        )
        if corrigido != normalizado:
            normalizado = corrigido
            eventos.append({
                "de": "proxma", "para": "proxima", "tipo": "termo_operacional",
            })

    tokens_exatos = normalizado.split()
    determinantes = {
        "a", "o", "as", "os", "um", "uma", "uns", "umas", "meu", "minha",
        "meus", "minhas", "seu", "sua", "seus", "suas", "essa", "esse",
        "essas", "esses", "na", "no", "da", "do",
    }
    marcadores_consulta = {"qual", "quais", "quantas", "quantos", "lista", "mostra"}
    nomes_de_estrutura = {
        "arquivo", "arquivos", "pasta", "pastas", "playlist", "playlists",
        "app", "aplicativo", "programa", "musica", "faixa",
    }
    for indice, token in enumerate(tokens_exatos):
        anteriores = tokens_exatos[:indice]
        moldura_forte = bool(
            any(item in marcadores_consulta for item in anteriores)
            or any(
                item in _VERBOS_OPERACIONAIS
                or item in _ERROS_VERBAIS_EXPLICITOS
                for item in anteriores
            )
        )
        correcao_termo = _CORRECOES_TERMOS_OPERACIONAIS.get(token)
        tipo_correcao = "termo_operacional"
        if not correcao_termo and moldura_forte:
            correcao_termo = _termo_operacional_proximo(token)
            tipo_correcao = "termo_operacional_aproximado"
        if not correcao_termo:
            continue
        if any(item in _INTRODUCOES_DE_ENTIDADE for item in anteriores):
            continue
        if indice and tokens_exatos[indice - 1] in nomes_de_estrutura:
            continue
        moldura_operacional = bool(
            (indice and tokens_exatos[indice - 1] in determinantes)
            or any(item in marcadores_consulta for item in anteriores)
            or any(
                item in _VERBOS_OPERACIONAIS
                or item in _ERROS_VERBAIS_EXPLICITOS
                for item in anteriores
            )
        )
        if not moldura_operacional:
            continue
        tokens_exatos[indice] = correcao_termo
        eventos.append({
            "de": token,
            "para": correcao_termo,
            "tipo": tipo_correcao,
        })
    normalizado = " ".join(tokens_exatos)

    # Repara apenas o primeiro token quando a saída assíncrona duplicou seu
    # começo: ``fecfecha`` -> ``fecha``. Não examina argumentos posteriores.
    partes = normalizado.split(" ", 1)
    primeiro = partes[0] if partes else ""
    for verbo in _VERBOS_OPERACIONAIS:
        if primeiro.endswith(verbo) and primeiro != verbo:
            prefixo = primeiro[:-len(verbo)]
            if prefixo and verbo.startswith(prefixo):
                partes[0] = verbo
                normalizado = " ".join(partes)
                eventos.append({"de": primeiro, "para": verbo, "tipo": "prefixo_duplicado"})
                break

    tokens = normalizado.split()
    if not tokens:
        return normalizado, eventos
    tem_dominio_explicito = bool(_PADRAO_DOMINIO_OPERACIONAL.search(normalizado))

    # Se já existe um verbo operacional claro na moldura, os demais tokens são
    # tratados como argumentos e permanecem literalmente como o usuário falou.
    for indice, token in enumerate(tokens[:8]):
        if token in _INTRODUCOES_DE_ENTIDADE:
            break
        if token in _VERBOS_OPERACIONAIS:
            return normalizado, eventos
        if indice and any(anterior not in _MOLDURA_ANTES_DO_VERBO for anterior in tokens[:indice]):
            break
        candidato_explicito = _ERROS_VERBAIS_EXPLICITOS.get(token)
        pesquisa_com_moldura_explicita = bool(
            token == "pequisa"
            and indice + 1 < len(tokens)
            and (
                tokens[indice + 1] in {"sobre", "por"}
                or tokens[indice + 1:indice + 3] == ["no", "google"]
            )
        )
        if (
            candidato_explicito
            and token in _ERROS_VERBAIS_QUE_EXIGEM_DOMINIO
            and not tem_dominio_explicito
            and not pesquisa_com_moldura_explicita
        ):
            candidato_explicito = ""
        candidato_aproximado = (
            _verbo_operacional_proximo(token)
            if tem_dominio_explicito
            else ""
        )
        candidato = candidato_explicito or candidato_aproximado
        if not candidato:
            continue
        tokens[indice] = candidato
        eventos.append({
            "de": token,
            "para": candidato,
            "tipo": "verbo_operacional",
        })
        return " ".join(tokens), eventos
    return normalizado, eventos


def remover_acentos(texto: str) -> str:
    try:
        normalizado = unicodedata.normalize("NFKD", str(texto or ""))
        return "".join(c for c in normalizado if not unicodedata.combining(c))
    except Exception:
        return str(texto or "")


def aplicar_correcao_fonetica(texto: str) -> str:
    t = str(texto or "").lower().strip()
    if not t:
        return ""
    t = re.sub(r"\s+", " ", t)
    for padrao, troca in CORRECOES_FONETICAS:
        t = re.sub(padrao, troca, t, flags=re.IGNORECASE)
    return t


def normalizar_texto(texto: str) -> str:
    t = remover_acentos(str(texto or "").lower())
    t = aplicar_correcao_fonetica(t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def normalizar_texto_curto(texto: str) -> str:
    """Normaliza caixa, acentos e espaços sem remover pontuação contextual."""
    bruto = str(texto or "").lower()
    sem_acento = unicodedata.normalize("NFKD", bruto)
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", sem_acento).strip()


def normalizar_texto_basico(texto: str) -> str:
    """Normaliza caixa Unicode, acentos e espaços, preservando pontuação.

    É o contrato básico compartilhado. Domínios que removem ou preservam
    conjuntos específicos de símbolos devem manter normalizadores próprios.
    """
    bruto = str(texto or "").casefold()
    sem_acento = unicodedata.normalize("NFKD", bruto)
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", sem_acento).strip()


def localizar_enunciacao_avaliativa(texto: str) -> re.Match[str] | None:
    """Confere perspectiva/juízo declarados, não conteúdo ou pertinência.

    Sujeito, matriz e complemento pertencem à mesma oração declarativa.
    Percepção sem qualificação, pergunta, relato e citação não bastam.
    Fatos, capacidades, efeitos e atendimento ao pedido continuam sob revisão.
    """
    from mente_laylay.arquivos.nome_natural import mapear_pares_aspas_globais
    bruto = str(texto or '')
    pares = mapear_pares_aspas_globais(bruto)
    if pares is None:return None
    projecao = list(bruto)
    for inicio,fim in pares.items():
        # Uma citação pode ocupar o complemento, mas nunca fornecer a matriz
        # ou o operador avaliativo da fala externa. Preservar os offsets.
        projecao[inicio:fim+1] = '\ufffc'*(fim+1-inicio)
    externo = ''.join(projecao)
    autora = r'(?:eu\s+)?(?:n[aã]o\s+)?'
    conteudo = r'[\w\ufffc][^.!?;\n]*'
    padroes = (
        autora+r'(?:vejo|veria|encaro|encararia|interpreto|interpretaria)\s+'
        +conteudo+r'\s+como\s+'+conteudo,
        autora+r'(?:considero|consideraria|julgo|julgaria|avalio|avaliaria|'
        r'entendo|entenderia|defendo|defenderia|sustento|sustentaria|penso|pensaria)\s+que\s+'+conteudo,
        autora+r'(?:considero|consideraria|julgo|julgaria|avalio|avaliaria)\s+'
        +conteudo+r'\s+(?:um|uma|uns|umas)\s+'+conteudo,
        r'(?:na\s+minha\s+(?:opini[aã]o|avalia[cç][aã]o|leitura|vis[aã]o)|'
        r'do\s+meu\s+ponto\s+de\s+vista|a\s+meu\s+ver|para\s+mim)\s*,?\s+'
        r'\S+(?:\s+\S+)+',
        autora+r'sou\s+(?:favor[aá]vel|contr[aá]ri[ao]|contra)\s+'+conteudo,
        autora+r'(?:concordo|discordo)\s+(?:com|de|que)\s+'+conteudo,
    )
    for clausula in re.finditer(r'[^.!?;\n]+(?:[.!?;]|$)',externo):
        inicio,fim = clausula.span()
        if clausula.group().endswith('?'):
            # Uma pergunta ao interlocutor pode suceder uma declaração na
            # mesma frase. A interrogação não transforma a matriz anterior
            # em pergunta; só aceitar uma nova oração explicitamente aberta.
            pausa = re.search(
                r',\s*(?:e\s+)?(?:voc[eê]|vc|tu|o\s+que|como|por\s+que|qual|quem)\b',
                externo[inicio:fim],re.I,
            )
            if pausa is None:continue
            fim = inicio+pausa.start()
        while inicio<fim and externo[inicio].isspace():inicio+=1
        while fim>inicio and (externo[fim-1].isspace() or externo[fim-1] in '.!;'):fim-=1
        inicios = [inicio]
        for pausa in re.finditer(r',\s*',externo[inicio:fim]):
            saudacao,resto = separar_saudacao_inicial(externo[inicio:inicio+pausa.start()])
            if saudacao and not resto:inicios.append(inicio+pausa.end())
        for comeco in inicios:
            for padrao in padroes:
                m = re.compile(padrao,re.I).fullmatch(externo,comeco,fim)
                if m:return m
    return None


def enunciacao_avaliativa_de_atividade(texto: str) -> bool:
    """Confere só juízo normativo fechado sobre atividade, sem fato externo.

    Um prefixo opinativo não basta. Relato finito/particípio, coordenação,
    números, causas e características independentes não entram nesta leitura.
    """
    m = localizar_enunciacao_avaliativa(texto)
    if m is None or str(texto or '').strip(' .!;\n') != m.group().strip():return False
    from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia
    valor = (r'(?:v[aá]lid[oa]|leg[ií]tim[oa]|aceit[aá]vel|corret[oa]|adequad[oa]|'
             r'prudente|sensat[oa]|razo[aá]vel|respons[aá]vel|prefer[ií]vel|importante|'
             r'[uú]til|necess[aá]ri[oa]|arriscad[oa])')
    r = re.fullmatch(
        r'(?:eu\s+)?(?:n[aã]o\s+)?(?:considero|julgo|avalio|entendo|defendo|sustento|penso)\s+que\s+'
        r'(?P<atividade>[^,;.!?\d]+?)\s+(?:[ée]|seria)\s+'
        r'(?:(?:um|uma)\s+(?:escolha|atitude|postura|decis[aã]o|op[cç][aã]o|possibilidade|passo)\s+)?'
        +valor,
        m.group(),re.I,
    )
    if r is None:return False
    palavras = re.findall(r'[^\W\d_]+',r['atividade'].casefold())
    if not palavras or len(palavras)>16:return False
    tipo_verbo = consultar_morfologia(palavras[0])
    if not tipo_verbo or not tipo_verbo&32 or not re.search(r'(?:ar|er|ir|or)$',palavras[0]):return False
    # A atividade pode ter um único argumento nominal não qualificado.
    # Não absorver adjetivos, apostos ou relações encaixadas como se fossem
    # parte comprovada da opinião: "clínica gratuita" exige sua própria base.
    artigos = {'o','a','os','as','um','uma','uns','umas'}
    preposicoes = {'ao','aos','à','às','de','do','da','dos','das','em','no','na','nos','nas','com','para','pra'}
    nucleo = False
    preposicao = False
    for palavra in palavras[1:]:
        if palavra in artigos:
            if nucleo:return False
            continue
        if palavra in preposicoes:
            if nucleo or preposicao:return False
            preposicao = True
            continue
        tipo = consultar_morfologia(palavra)
        if tipo is None or nucleo or (tipo!=0 and not tipo&1):return False
        nucleo = True
    return True


def texto_pede_opiniao(texto: str) -> bool:
    """Reconhece molduras de opinião sem autorizar uma ação operacional.

    ``acha`` é ambíguo em português: pode significar tanto ``encontre`` quanto
    ``qual é a sua opinião``. A camada compartilhada resolve apenas as formas
    inequivocamente conversacionais. Pedidos como ``acha o arquivo`` continuam
    disponíveis para o roteador de arquivos.
    """
    from mente_laylay.arquivos.nome_natural import mapear_pares_aspas_globais
    # O ato pertence à moldura externa, não a palavras dentro do nome de um
    # arquivo/aplicativo ou de uma citação. Reutilizar os pares canônicos;
    # não remover aspas nem reclassificar o conteúdo delimitado como pedido.
    bruto = str(texto or '')
    pares = mapear_pares_aspas_globais(bruto) or {}
    externo = list(bruto)
    for inicio, fim in pares.items():
        externo[inicio:fim + 1] = ' ' * (fim + 1 - inicio)
    t = normalizar_texto_basico(''.join(externo))
    if not t:
        return False
    from mente_laylay.cognicao.referencias_linguagem import consulta_opiniao_propria
    if consulta_opiniao_propria(texto) is not None:
        return True
    # Predicados de gosto dirigidos ao interlocutor são atos subjetivos,
    # independentemente do domínio do complemento. Não procurar o verbo
    # dentro de nomes, citações de comandos ou relatos de terceiros.
    sujeito = r"(?:voce|vc|tu|laylay|lay)"
    gosto = r"(?:gosta|curte|prefere|aprecia)"
    if (re.match(rf"^(?:e\s+)?(?:{sujeito}\s+)?(?:nao\s+)?{gosto}\b", t)
        or re.match(rf"^(?:de\s+que|do\s+que|o\s+que)\s+{sujeito}\s+{gosto}\b", t)
        or re.match(r"^qual\s+(?:e\s+)?(?:o\s+|a\s+)?(?:seu|sua)\s+"
                    r"[^?!.;]{0,100}\b(?:favorit[oa]|preferid[oa])\b", t)):
        return True
    return bool(re.search(
        r"(?:^|\b)(?:o\s+que|oque)\s+(?:voce\s+)?acha\b|"
        r"^(?:e\s+)?(?:voce\s+)?acha\s+(?:que\b|(?:de|do|da|dos|das|sobre)\b|"
        r"(?:legal|bom|boa|ruim|interessante)\b)|"
        r"\bqual\s+(?:e\s+)?(?:a\s+)?sua\s+opiniao\b|"
        r"\b(?:me\s+(?:da|diz)|quero)\s+(?:a\s+)?sua\s+opiniao\b|"
        r"\bo\s+que\s+(?:voce\s+)?pensa\s+(?:de|do|da|dos|das|sobre)\b",
        t,
    ))
