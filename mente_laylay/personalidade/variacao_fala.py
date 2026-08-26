"""Variação de falas locais com memória curta de sessão.

Esta camada não escreve a personalidade da Laylay no lugar da LLM. Ela existe
somente para contingências e falas locais inevitáveis, impedindo que uma
recuperação técnica vire um bordão repetido.
"""

from __future__ import annotations

import random
import re
import threading
import unicodedata
from collections import OrderedDict, deque
from collections.abc import Iterable, Sequence
from typing import Any, TypeVar


T = TypeVar("T")
_MAXIMO_CONJUNTOS = 256
_TRAVA = threading.RLock()
_USADAS: "OrderedDict[tuple[str, ...], deque[str]]" = OrderedDict()


def _normalizar(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or "").casefold())
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip()


def _lista_evitar(evitar: Iterable[Any] | Any) -> set[str]:
    if isinstance(evitar, (str, bytes)) or evitar is None:
        itens = [evitar]
    else:
        try:
            itens = list(evitar)
        except TypeError:
            itens = [evitar]
    return {_normalizar(item) for item in itens if _normalizar(item)}


def escolher_variacao(
    opcoes: Sequence[T],
    *,
    evitar: Iterable[Any] | Any = (),
) -> T:
    """Escolhe sem repetir até esgotar o conjunto.

    A assinatura usa o conteúdo do conjunto, então chamadas espalhadas pelo
    código compartilham a lembrança somente quando representam o mesmo grupo
    de falas. A função mantém a assinatura de ``random.choice`` para poder ser
    usada como dependência nos módulos antigos.
    """
    candidatos = list(opcoes)
    if not candidatos:
        raise IndexError("não é possível escolher de uma sequência vazia")
    if len(candidatos) == 1:
        return candidatos[0]

    assinatura = tuple(_normalizar(item) for item in candidatos)
    bloqueadas = _lista_evitar(evitar)
    with _TRAVA:
        historico = _USADAS.get(assinatura)
        if historico is None:
            historico = deque(maxlen=max(1, len(candidatos) - 1))
            _USADAS[assinatura] = historico
        else:
            _USADAS.move_to_end(assinatura)

        disponiveis = [
            item for item in candidatos
            if _normalizar(item) not in bloqueadas
            and _normalizar(item) not in historico
        ]
        if not disponiveis:
            ultimo = historico[-1] if historico else ""
            historico.clear()
            disponiveis = [
                item for item in candidatos
                if _normalizar(item) not in bloqueadas
                and _normalizar(item) != ultimo
            ]
        if not disponiveis:
            disponiveis = [
                item for item in candidatos if _normalizar(item) not in bloqueadas
            ] or candidatos

        escolhida = random.SystemRandom().choice(disponiveis)
        historico.append(_normalizar(escolhida))
        while len(_USADAS) > _MAXIMO_CONJUNTOS:
            _USADAS.popitem(last=False)
        return escolhida


def resetar_variacoes_para_testes() -> None:
    with _TRAVA:
        _USADAS.clear()
