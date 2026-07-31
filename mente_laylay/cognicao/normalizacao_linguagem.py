"""Normalizacao textual compartilhada da mente da Laylay."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


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
    "muscia": "musica",
    "muisca": "musica",
    "lampda": "lampada",
    "lanpada": "lampada",
    "dispostivo": "dispositivo",
    "dispositvo": "dispositivo",
    "arquvio": "arquivo",
    "arqivo": "arquivo",
    "emial": "email",
}

_ERROS_VERBAIS_EXPLICITOS = {
    "colcoa": "coloca",
    "coloac": "coloca",
    "orgniza": "organiza",
    "oragniza": "organiza",
    "pesqisa": "pesquisa",
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
    "liag", "lgia",
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
        correto = _CORRECOES_TERMOS_OPERACIONAIS.get(token)
        if not correto:
            continue
        anteriores = tokens_exatos[:indice]
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
        tokens_exatos[indice] = correto
        eventos.append({
            "de": token,
            "para": correto,
            "tipo": "termo_operacional",
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
        if (
            candidato_explicito
            and token in _ERROS_VERBAIS_QUE_EXIGEM_DOMINIO
            and not tem_dominio_explicito
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
