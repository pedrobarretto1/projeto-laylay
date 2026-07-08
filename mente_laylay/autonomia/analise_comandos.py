"""Ferramentas leves para interpretar comandos da autonomia da Laylay."""

from __future__ import annotations

import re
from typing import List, Tuple


def separar_comandos_blindado(cmd: str) -> List[str]:
    """Separa comandos por | respeitando aspas e parênteses."""
    if not cmd:
        return []

    comandos = []
    atual = ""
    em_parenteses = 0
    em_aspas_simples = False
    em_aspas_duplas = False

    for char in str(cmd):
        if char == "'" and not em_aspas_duplas:
            em_aspas_simples = not em_aspas_simples
        elif char == '"' and not em_aspas_simples:
            em_aspas_duplas = not em_aspas_duplas
        elif char == "(" and not em_aspas_simples and not em_aspas_duplas:
            em_parenteses += 1
        elif char == ")" and not em_aspas_simples and not em_aspas_duplas:
            em_parenteses -= 1

        if char == "|" and em_parenteses == 0 and not em_aspas_simples and not em_aspas_duplas:
            trecho = atual.strip()
            if trecho:
                comandos.append(trecho)
            atual = ""
        else:
            atual += char

    trecho = atual.strip()
    if trecho:
        comandos.append(trecho)
    return comandos


def extrair_nome_e_args(comando: str) -> Tuple[str, str]:
    """Extrai nome e argumentos de um comando estilo NOME(args)."""
    texto = str(comando or "").strip()
    if not texto:
        return "", ""

    match = re.match(r"(\w+)\((.*)\)", texto, re.DOTALL)
    if match:
        return match.group(1).upper(), match.group(2).strip()
    return texto.upper(), ""

