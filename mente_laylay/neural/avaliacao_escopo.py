"""Mede relações ação/alvo; não interpreta linguagem nem autoriza efeitos."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable, Mapping

from .anotacao_escopo import _chaves, _mencoes, _mencoes_vinculadas, validar_anotacao_escopo

PAPEIS = ("alvos_solicitados", "alvos_excluidos", "alvos_mencionados")


def _indexar(segmentos: Any, textos: dict[int, str], variantes: set, *, versao: int = 1) -> dict:
    if not isinstance(segmentos, list):
        raise ValueError("previsão precisa listar segmentos")
    resultado, vistos = {}, set()
    for segmento in segmentos:
        _chaves(segmento, {"indice", "acoes"})
        indice = segmento["indice"]
        if type(indice) is not int or indice not in textos or indice in vistos:
            raise ValueError("segmento previsto inválido")
        vistos.add(indice)
        if not isinstance(segmento["acoes"], list):
            raise ValueError("ações previstas inválidas")
        for acao in segmento["acoes"]:
            _chaves(acao, {"intent", "action", "ato", "resolucao_alvo", *PAPEIS})
            chave = (indice, acao["intent"], acao["action"])
            if chave in resultado or chave[1:] not in variantes:
                raise ValueError("variante prevista inválida ou repetida")
            if acao["ato"] not in {"pedido", "recusa", "relato", "preservacao", "indeterminado"}:
                raise ValueError("ato previsto inválido")
            if acao["resolucao_alvo"] not in {"explicito", "contextual", "alternativa", "ausente", "nao_aplicavel"}:
                raise ValueError("resolução prevista inválida")
            relacao = {k: acao[k] for k in ("ato", "resolucao_alvo")}
            spans = set()
            for papel in PAPEIS:
                mencoes = (_mencoes(acao[papel], textos[indice]) if versao == 1 else
                           _mencoes_vinculadas(acao[papel], textos))
                relacao[papel] = {(m.get("segmento", indice), m["inicio"], m["fim"], m["texto"]) for m in mencoes}
                for origem, a, b, _ in relacao[papel]:
                    if any(origem == s and a < d and c < b for s, c, d in spans):
                        raise ValueError("papéis previstos sobrepostos")
                    spans.add((origem, a, b))
            # Erros semânticos coerentes na forma devem ser MEDIDOS, não
            # reparados pelo rótulo esperado (ex.: relato virou pedido).
            resultado[chave] = relacao
    return resultado


def avaliar_escopo(
    casos: Iterable[Mapping[str, Any]], *,
    prever: Callable[[dict[str, Any]], Any],
    variantes_permitidas: Iterable[tuple[str, str]],
) -> dict[str, Any]:
    """Recebe sidecars validados e entrega ao preditor só texto/segmentos.

    Falha de inferência é erro no denominador, nunca recusa correta. Nenhuma
    cabeça antiga ganha capacidade de prever alvos por adaptação artificial.
    """
    variantes = set(variantes_permitidas)
    preparados, ids = [], set()
    for caso in casos:
        ident = caso.get("id")
        if not isinstance(ident, str) or not ident or ident in ids:
            raise ValueError("id de avaliação inválido ou repetido")
        ids.add(ident)
        if (caso.get("treino_permitido") is not False
                or caso.get("autoriza_execucao") is not False
                or caso.get("autoriza_promocao") is not False):
            raise ValueError("avaliação deve proibir treino, execução e promoção")
        ref = caso["referencia"]
        validado = validar_anotacao_escopo(
            caso["anotacao"], turno=ref["leitura_observada"], variantes_permitidas=variantes,
        )
        if ref["sha256"] != validado["referencia"]["sha256"]:
            raise ValueError("referência da avaliação divergiu")
        texto = caso["texto_entrada"]
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError("entrada de avaliação vazia")
        segmentos = [{"indice": s["indice"], "texto": s["texto"]}
                     for s in ref["leitura_observada"]["segmentos"]]
        textos = {s["indice"]: s["texto"] for s in segmentos}
        versao = validado["versao"]
        esperado = _indexar([{k: s[k] for k in ("indice", "acoes")}
                             for s in validado["anotacao"]["segmentos"]], textos, variantes, versao=versao)
        preparados.append((ident, {"texto_entrada": texto, "segmentos": segmentos}, textos, esperado, versao))
    if not preparados:
        raise ValueError("avaliação vazia")
    totais = {k: 0 for k in (
        "casos", "casos_exatos", "falhas_inferencia", "acoes_esperadas",
        "acoes_ausentes", "acoes_extras", "atos_corretos", "resolucoes_corretas",
        "excluidos_solicitados", "mencoes_solicitadas", "pedidos_perdidos", "pedidos_inventados",
    )}
    papeis = {p: {k: 0 for k in ("corretos", "ausentes", "extras")} for p in PAPEIS}
    linhas = []
    for ident, entrada, textos, esperado, versao in preparados:
        totais["casos"] += 1
        totais["acoes_esperadas"] += len(esperado)
        erro = None
        try:
            previsto = _indexar(prever(deepcopy(entrada)), textos, variantes, versao=versao)
        except Exception as exc:
            # Detalhes privados da exceção não são publicados.
            erro, previsto = type(exc).__name__, {}
            totais["falhas_inferencia"] += 1
        exato = erro is None and previsto == esperado
        totais["casos_exatos"] += exato
        totais["acoes_ausentes"] += len(esperado.keys() - previsto.keys())
        totais["acoes_extras"] += len(previsto.keys() - esperado.keys())
        for chave in esperado.keys() | previsto.keys():
            e, p = esperado.get(chave, {}), previsto.get(chave, {})
            totais["atos_corretos"] += bool(e and p and e["ato"] == p["ato"])
            totais["resolucoes_corretas"] += bool(e and p and e["resolucao_alvo"] == p["resolucao_alvo"])
            totais["pedidos_perdidos"] += e.get("ato") == "pedido" and p.get("ato") != "pedido"
            totais["pedidos_inventados"] += p.get("ato") == "pedido" and e.get("ato") != "pedido"
            for papel in PAPEIS:
                a, b = e.get(papel, set()), p.get(papel, set())
                papeis[papel]["corretos"] += len(a & b)
                papeis[papel]["ausentes"] += len(a - b)
                papeis[papel]["extras"] += len(b - a)
            totais["excluidos_solicitados"] += len(e.get("alvos_excluidos", set()) & p.get("alvos_solicitados", set()))
            totais["mencoes_solicitadas"] += len(e.get("alvos_mencionados", set()) & p.get("alvos_solicitados", set()))
        linhas.append({"id": ident, "exato": exato, "erro": erro})
    return {"totais": totais, "papeis": papeis, "casos": linhas,
            "taxa_casos_exatos": totais["casos_exatos"] / totais["casos"],
            "treino_permitido": False, "autoriza_execucao": False, "autoriza_promocao": False}
