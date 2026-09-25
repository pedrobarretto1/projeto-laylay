"""Apoio offline à revisão humana de uma fala didática inteira.

Não julga implicação semântica e não é um portão de publicação no runtime.
Preserva cada caractere da fala para tornar omissões visíveis na auditoria.
"""

from __future__ import annotations

import re
from typing import Any, Mapping


_FIM_FRASE = re.compile(r"[.!?]+(?=\s|$)")
_CLASSES = frozenset({"amparada", "sem_prova", "contradita", "mista", "nao_factual"})


def segmentar_fala(fala: str) -> list[dict[str, Any]]:
    """Parte por pontuação sem apagar espaços, URLs ou caudas sem ponto."""
    partes: list[dict[str, Any]] = []
    inicio = 0
    for achado in _FIM_FRASE.finditer(fala):
        fim = achado.end()
        if fim > inicio:
            partes.append({"inicio": inicio, "fim": fim, "texto": fala[inicio:fim]})
            inicio = fim
    if inicio < len(fala):
        partes.append({"inicio": inicio, "fim": len(fala), "texto": fala[inicio:]})
    assert "".join(parte["texto"] for parte in partes) == fala
    return partes


def auditar_anotacoes(
    fala: str,
    anotacoes: Mapping[int, Mapping[str, str]],
    fontes: Mapping[str, str],
) -> dict[str, Any]:
    """Valida cobertura e proveniência literal de julgamentos *humanos*.

    Um trecho localizado não prova que a fonte implica a fala. Por isso o
    resultado jamais contém aprovação de conteúdo ou ``publicavel=True``.
    """
    partes = segmentar_fala(fala)
    indices = set(range(len(partes)))
    pendentes = sorted(indices - set(anotacoes))
    invalidas: list[int] = []
    classes: dict[str, int] = {classe: 0 for classe in sorted(_CLASSES)}
    for indice, anotacao in anotacoes.items():
        if indice not in indices or not isinstance(anotacao, Mapping):
            invalidas.append(indice)
            continue
        classe = anotacao.get("classe")
        if classe not in _CLASSES:
            invalidas.append(indice)
            continue
        if classe == "amparada":
            fonte_id = anotacao.get("fonte_id", "")
            citacao = anotacao.get("citacao", "")
            if not citacao or citacao not in fontes.get(fonte_id, ""):
                invalidas.append(indice)
                continue
        elif classe in {"sem_prova", "contradita", "mista"}:
            if not anotacao.get("motivo", "").strip():
                invalidas.append(indice)
                continue
        classes[classe] += 1
    return {
        "total_partes": len(partes),
        "cobertura_integral": not pendentes and not invalidas,
        "indices_pendentes": pendentes,
        "indices_invalidos": sorted(invalidas),
        "classes_humanas": classes,
        "revisao_semantica_automatizada": False,
        "aprovado_para_producao": False,
    }
