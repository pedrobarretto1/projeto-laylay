"""Autoria natural para lembranças confiáveis da Laylay.

O conteúdo factual chega pronto do domínio de memória. Este módulo só organiza
e dá voz ao resultado; não consulta, corrige nem cria lembranças.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from mente_laylay.personalidade.falas_variadas import escolher


def _limpar_fato(texto: object) -> str:
    return re.sub(r"\s+", " ", str(texto or "")).strip().rstrip(".!?;: ")


def _lista_natural(itens: list[str]) -> str:
    itens = [item for item in itens if item]
    if len(itens) <= 1:
        return itens[0] if itens else ""
    if len(itens) == 2:
        return f"{itens[0]} e {itens[1]}"
    return f"{', '.join(itens[:-1])} e {itens[-1]}"


def _capitalizar(texto: str) -> str:
    return texto[:1].upper() + texto[1:] if texto else texto


def _consolidar_fatos(recortes: Iterable[str]) -> str:
    """Agrupa afinidades repetidas sem mudar seu sentido."""
    gostos: list[str] = []
    desgostos: list[str] = []
    outros: list[str] = []
    for recorte in recortes:
        fato = _limpar_fato(recorte)
        positivo = re.fullmatch(r"você gosta de (.+)", fato, flags=re.IGNORECASE)
        negativo = re.fullmatch(
            r"você não gosta de (.+)", fato, flags=re.IGNORECASE,
        )
        if positivo:
            gostos.append(positivo.group(1).strip())
        elif negativo:
            desgostos.append(negativo.group(1).strip())
        elif fato:
            outros.append(fato)

    frases: list[str] = []
    if gostos:
        afinidades = f"você gosta de {_lista_natural(gostos)}"
        if desgostos:
            afinidades += f", mas não gosta de {_lista_natural(desgostos)}"
            desgostos.clear()
        frases.append(afinidades)
    if desgostos:
        frases.append(f"você não gosta de {_lista_natural(desgostos)}")
    frases.extend(outros)
    return ". ".join(_capitalizar(frase) for frase in frases) + "."


def falar_lembrancas(
    recortes: Iterable[str],
    *,
    todos_confirmados: bool,
) -> str:
    """Mantém a proveniência e varia apenas a apresentação da lembrança."""
    fatos = [_limpar_fato(item) for item in recortes]
    fatos = [item for item in fatos if item]
    if not fatos:
        return "Ainda não tenho uma lembrança confiável para te devolver."
    nucleo = _consolidar_fatos(fatos)
    nucleo_depois_dois_pontos = nucleo[:1].lower() + nucleo[1:]

    if not todos_confirmados:
        return escolher([
            f"Tenho isso por aqui, com as ressalvas no lugar: {nucleo_depois_dois_pontos} Não vou promover palpite a certeza só pra parecer esperta.",
            f"Minha memória trouxe isto: {nucleo_depois_dois_pontos} Onde é padrão percebido, continua sendo padrão — não vou fantasiar palpite de certeza.",
            f"Achei estas lembranças, mas sem misturar fato com palpite: {nucleo_depois_dois_pontos}",
        ])

    if len(fatos) == 1:
        return escolher([
            f"Lembro, sim: {nucleo_depois_dois_pontos} Essa não escapou.",
            f"{nucleo} Essa eu tenho guardada direitinho.",
            f"Tá guardado aqui: {nucleo_depois_dois_pontos} Minha memória fez o dever de casa.",
        ])
    return escolher([
        f"Eu lembro, sim: {nucleo_depois_dois_pontos} Minha memória não está aqui só de decoração.",
        f"Tá tudo guardado: {nucleo_depois_dois_pontos} Você foi contando e eu fui prestando atenção.",
        f"Tenho um retrato bem claro: {nucleo_depois_dois_pontos} Nada mal para uma cabeça que mora num computador.",
    ])


def falar_nome_lembrado(nome: str) -> str:
    nome = re.sub(r"\s+", " ", str(nome or "")).strip()
    return escolher([
        f"Seu nome é {nome}. Essa eu tenho guardada direitinho.",
        f"Você se chama {nome}. Minha memória não vai bancar a desentendida agora.",
        f"{nome}. Sim, eu lembro — seria feio esquecer de novo.",
    ])
