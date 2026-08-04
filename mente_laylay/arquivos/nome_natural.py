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

_EXTENSOES_FALADAS = tuple(
    sorted((extensao.removeprefix(".") for extensao in EXTENSOES_TEXTUAIS_RENOMEAVEIS),
           key=len, reverse=True)
)


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
