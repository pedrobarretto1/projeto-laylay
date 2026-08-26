"""Normalizacao segura de nomes de arquivo vindos de linguagem natural.

O modulo remove somente molduras linguisticas inequívocas (por exemplo,
``um arquivo chamado``) e preserva o nome escolhido pelo usuario. Ele tambem
recupera extensoes comuns que tenham perdido o ponto durante a normalizacao do
turno, sem tentar adivinhar caminhos ou autorizar qualquer mutacao.
"""

from __future__ import annotations

import os
import re


EXTENSOES_TEXTUAIS_RENOMEAVEIS = frozenset({
    ".txt", ".md", ".markdown", ".log", ".csv", ".json", ".yaml", ".yml",
    ".py", ".js", ".ts", ".html", ".css",
})

ASPAS_ABERTURA_PARA_FECHAMENTO = {'"': '"', "'": "'", "“": "”"}
CARACTERES_ASPAS = frozenset({'"', "'", "“", "”"})

_EXTENSOES_FALADAS = tuple(
    sorted((extensao.removeprefix(".") for extensao in EXTENSOES_TEXTUAIS_RENOMEAVEIS),
           key=len, reverse=True)
)


def mapear_pares_aspas_globais(texto: str) -> dict[int, int] | None:
    """Mapeia abertura->fechamento ou falha se qualquer aspa for incoerente."""
    pilha: list[tuple[str, int]] = []
    pares: dict[int, int] = {}
    for indice, caractere in enumerate(str(texto or "")):
        if caractere not in CARACTERES_ASPAS:
            continue
        if caractere == "”":
            if not pilha or pilha[-1][0] != "”":
                return None
            _, abertura = pilha.pop()
            pares[abertura] = indice
            continue
        if caractere in {'"', "'"} and pilha and pilha[-1][0] == caractere:
            _, abertura = pilha.pop()
            pares[abertura] = indice
            continue
        esperado = ASPAS_ABERTURA_PARA_FECHAMENTO.get(caractere)
        if not esperado:
            return None
        pilha.append((esperado, indice))
    return None if pilha else pares


def aspas_globalmente_coerentes(texto: str) -> bool:
    """Confirma que não existem aspas órfãs, invertidas ou cruzadas."""
    return mapear_pares_aspas_globais(texto) is not None


def regex_atomo_filename_negativo() -> re.Pattern[str]:
    """Compila ``nao.<ext>`` apenas com extensões canônicas de produção."""
    extensoes = sorted(
        (item.removeprefix(".") for item in EXTENSOES_TEXTUAIS_RENOMEAVEIS),
        key=len,
        reverse=True,
    )
    return re.compile(
        rf"\b(?P<atom>(?:nao|não)\.(?:{'|'.join(re.escape(x) for x in extensoes)}))\b",
        re.IGNORECASE,
    )


def marcador_negacao_em_filename_literal(
    texto: str,
    inicio: int,
    fim: int,
) -> tuple[bool, str]:
    """Prova o átomo literal no slot de filename e no mapa global de aspas."""
    bruto = str(texto or "")
    if bruto[inicio:fim].casefold().replace("ã", "a") != "nao":
        return False, ""
    atomo = regex_atomo_filename_negativo().match(bruto, inicio)
    if not atomo:
        return False, ""
    pares = mapear_pares_aspas_globais(bruto)
    if pares is None:
        return False, ""
    slot = re.search(
        r"\b(?:arquivo|documento)(?:\s+de\s+(?:texto|txt))?\b"
        r"(?:\s+(?:chamado|chamada|de\s+nome|com\s+nome))?"
        r"\s*(?P<quote>[\"'“”]?)\s*$",
        bruto[:inicio],
        flags=re.IGNORECASE,
    )
    if not slot:
        return False, ""
    abertura = str(slot.group("quote") or "")
    indice_depois = atomo.end()
    while indice_depois < len(bruto) and bruto[indice_depois].isspace():
        indice_depois += 1
    depois = bruto[indice_depois] if indice_depois < len(bruto) else ""
    if abertura:
        indice_abertura = slot.start("quote")
        esperado = ASPAS_ABERTURA_PARA_FECHAMENTO.get(abertura)
        if not esperado or depois != esperado or pares.get(indice_abertura) != indice_depois:
            return False, ""
    elif depois in CARACTERES_ASPAS:
        return False, ""
    return True, str(atomo.group("atom") or "")


def desembrulhar_filename_literal(valor: str) -> str:
    """Remove somente um par orientado de aspas que englobe o valor inteiro."""
    limpo = str(valor or "").strip()
    if not limpo:
        return ""
    primeiro, ultimo = limpo[0], limpo[-1]
    if primeiro in CARACTERES_ASPAS or ultimo in CARACTERES_ASPAS:
        esperado = ASPAS_ABERTURA_PARA_FECHAMENTO.get(primeiro)
        if not esperado or ultimo != esperado or len(limpo) < 3:
            return ""
        return limpo[1:-1].strip()
    return limpo


def _restaurar_extensao_falada(nome: str) -> str:
    """Recoloca o ponto apenas para uma extensao textual conhecida no fim."""
    valor = str(nome or "").strip()
    if not valor or os.path.splitext(valor)[1]:
        return valor
    alternativas = "|".join(re.escape(item) for item in _EXTENSOES_FALADAS)
    encontrado = re.match(
        rf"^(?P<base>.+?)\s+(?P<ext>{alternativas})$",
        valor,
        flags=re.IGNORECASE,
    )
    if not encontrado:
        return valor
    return f"{encontrado.group('base').rstrip()}.{encontrado.group('ext').casefold()}"


def limpar_nome_arquivo_natural(valor: str) -> str:
    """Extrai o nome real sem incorporar artigos ou a palavra ``chamado``."""
    nome = re.sub(r"\s+", " ", str(valor or "").strip()).strip(" \t\r\n,;:!?\"'")
    if not nome:
        return ""

    # Respostas a "qual nome?" frequentemente chegam como "um chamado X" ou
    # "um arquivo de texto chamado X". Removemos somente essa moldura completa;
    # um nome legitimo que comece com "Um" continua intacto quando nao houver
    # o marcador chamado/nome.
    molduras = (
        r"^(?:(?:o|a)\s+)?(?:(?:um|uma)\s+)?"
        r"(?:(?:arquivo|documento)(?:\s+de\s+(?:texto|txt|markdown|md))?\s+|"
        r"de\s+(?:texto|txt|markdown|md)\s+)?"
        r"(?:chamado|chamada|com\s+nome|de\s+nome)\s+",
        r"^(?:o\s+nome\s+(?:e|é)\s+|nome\s+(?:e|é)\s+)",
    )
    for padrao in molduras:
        limpo = re.sub(padrao, "", nome, count=1, flags=re.IGNORECASE).strip()
        if limpo != nome:
            nome = limpo
            break

    nome = nome.strip(" \t\r\n,;:!?\"'")
    return _restaurar_extensao_falada(nome)


def tipo_arquivo_pelo_nome(nome: str, padrao: str = "") -> str:
    """Alinha metadados ao sufixo explicito, sem converter o conteudo."""
    extensao = os.path.splitext(str(nome or "").strip())[1].casefold()
    if extensao == ".txt":
        return "texto"
    if extensao in {".md", ".markdown"}:
        return "markdown"
    if extensao:
        return extensao.removeprefix(".")
    return str(padrao or "").strip().casefold()


def nome_com_nova_extensao_textual(nome_atual: str, extensao: str) -> str:
    """Troca somente extensoes textuais conhecidas e retorna vazio se inseguro."""
    nome = os.path.basename(str(nome_atual or "").strip())
    destino = str(extensao or "").strip().casefold()
    if not nome or not destino:
        return ""
    if not destino.startswith("."):
        destino = f".{destino}"
    if destino not in EXTENSOES_TEXTUAIS_RENOMEAVEIS:
        return ""
    origem = os.path.splitext(nome)[1].casefold()
    if origem and origem not in EXTENSOES_TEXTUAIS_RENOMEAVEIS:
        return ""
    raiz = os.path.splitext(nome)[0] if origem else nome
    return f"{raiz}{destino}"
