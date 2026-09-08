"""Anotações manuais de escopo, offline: não interpreta, treina ou autoriza.

Offsets referem-se ao texto do segmento canônico, que pode diferir da fala
original. A anotação é evidência esperada independente, nunca decisão real.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Iterable, Mapping

from mente_laylay.cognicao.contratos_turno import LeituraTurnoDict


def referencia_canonica(turno: LeituraTurnoDict) -> dict[str, Any]:
    """Captura a fronteira recebida sem resegmentar nem inferir autoridade."""
    segmentos = turno.get("segmentos")
    if not isinstance(segmentos, list) or not segmentos:
        raise ValueError("turno sem segmentos canônicos")
    vistos = set()
    copia = []
    for s in segmentos:
        if not isinstance(s, Mapping):
            raise ValueError("segmento inválido")
        indice, texto = s.get("indice"), s.get("texto")
        if type(indice) is not int or indice < 0 or indice in vistos:
            raise ValueError("índice canônico inválido ou duplicado")
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError("segmento sem texto")
        vistos.add(indice)
        copia.append({k: deepcopy(s.get(k)) for k in (
            "indice", "texto", "modalidade", "autoriza_execucao",
            "veto_execucao_operacional", "depende_contexto", "requer_esclarecimento",
        )})
    # Não inclui timestamp: duas leituras equivalentes devem ser comparáveis.
    dados = {"segmentos": copia, **{k: deepcopy(turno.get(k)) for k in (
        "natureza_entrada", "autoriza_execucao", "veto_execucao_operacional",
    )}}
    serializado = json.dumps(dados, sort_keys=True, ensure_ascii=False, allow_nan=False)
    return {"sha256": hashlib.sha256(serializado.encode("utf-8")).hexdigest(),
            "leitura_observada": dados}


def _chaves(dados: Any, esperadas: set[str]) -> None:
    if not isinstance(dados, Mapping) or set(dados) != esperadas:
        raise ValueError("campos ausentes ou desconhecidos na anotação")


def _mencoes(dados: Any, texto: str) -> list[dict[str, Any]]:
    if not isinstance(dados, list):
        raise ValueError("menções devem ser lista")
    resultado = []
    intervalos = set()
    for m in dados:
        _chaves(m, {"inicio", "fim", "texto"})
        a, b = m["inicio"], m["fim"]
        if (type(a) is not int or type(b) is not int
                or not 0 <= a < b <= len(texto)
                or not isinstance(m["texto"], str) or not m["texto"].strip()
                or texto[a:b] != m["texto"]):
            raise ValueError("span não corresponde ao texto canônico")
        if (a, b) in intervalos:
            raise ValueError("menção duplicada")
        intervalos.add((a, b))
        resultado.append(dict(m))
    return resultado


def _mencoes_vinculadas(dados: Any, textos: Mapping[int, str]) -> list[dict[str, Any]]:
    """Uma referência v2 possui origem explícita; não procura outro segmento."""
    if not isinstance(dados, list):
        raise ValueError("menções devem ser lista")
    resultado, vistas = [], set()
    for mencao in dados:
        _chaves(mencao, {"segmento", "inicio", "fim", "texto"})
        indice = mencao["segmento"]
        if type(indice) is not int or indice not in textos:
            raise ValueError("segmento de origem da menção inválido")
        local = {k: mencao[k] for k in ("inicio", "fim", "texto")}
        _mencoes([local], textos[indice])
        chave = (indice, local["inicio"], local["fim"])
        if chave in vistas:
            raise ValueError("menção vinculada duplicada")
        vistas.add(chave)
        resultado.append({"segmento": indice, **local})
    return resultado


def validar_anotacao_escopo(
    anotacao: Mapping[str, Any], *, turno: LeituraTurnoDict,
    variantes_permitidas: Iterable[tuple[str, str]],
) -> dict[str, Any]:
    """Valida um sidecar manual; não converte rótulos para o head booleano.

    O catálogo é injetado pelo chamador a partir do manifesto já existente.
    Validação estrutural não prova que a interpretação manual está correta.
    """
    _chaves(anotacao, {"versao", "origem", "referencia_sha256", "segmentos"})
    if type(anotacao["versao"]) is not int or anotacao["versao"] not in (1, 2):
        raise ValueError("versão de anotação inválida")
    versao = anotacao["versao"]
    if anotacao["origem"] != "anotacao_manual":
        raise ValueError("rótulo deve ser independente da previsão")
    referencia = referencia_canonica(turno)
    if anotacao["referencia_sha256"] != referencia["sha256"]:
        raise ValueError("referência canônica mudou; revisar anotação")
    catalogo = set(variantes_permitidas)
    por_indice = {s["indice"]: s for s in referencia["leitura_observada"]["segmentos"]}
    textos = {i: s["texto"] for i, s in por_indice.items()}
    segmentos = anotacao["segmentos"]
    if not isinstance(segmentos, list) or not segmentos:
        raise ValueError("anotação sem segmentos")
    vistos = set()
    for segmento in segmentos:
        _chaves(segmento, {"indice", "texto", "acoes"})
        indice = segmento["indice"]
        if type(indice) is not int or indice not in por_indice or indice in vistos:
            raise ValueError("segmento anotado inválido ou duplicado")
        vistos.add(indice)
        texto = por_indice[indice]["texto"]
        if segmento["texto"] != texto:
            raise ValueError("texto anotado divergiu do segmento canônico")
        acoes = segmento["acoes"]
        if not isinstance(acoes, list) or (versao == 1 and not acoes):
            raise ValueError("segmento sem anotação de ação")
        variantes_vistas = set()
        for acao in acoes:
            _chaves(acao, {"intent", "action", "ato", "resolucao_alvo",
                           "alvos_solicitados", "alvos_excluidos", "alvos_mencionados"})
            if (acao["intent"], acao["action"]) not in catalogo:
                raise ValueError("ação fora do catálogo injetado")
            variante = (acao["intent"], acao["action"])
            if variante in variantes_vistas:
                raise ValueError("consolidar escopo da mesma ação no segmento")
            variantes_vistas.add(variante)
            ato, resolucao = acao["ato"], acao["resolucao_alvo"]
            if ato not in {"pedido", "recusa", "relato", "preservacao", "indeterminado"}:
                raise ValueError("ato inválido")
            if resolucao not in {"explicito", "contextual", "alternativa", "ausente", "nao_aplicavel"}:
                raise ValueError("resolução inválida")
            papeis = {k: (_mencoes(acao[k], texto) if versao == 1 else
                           _mencoes_vinculadas(acao[k], textos)) for k in (
                "alvos_solicitados", "alvos_excluidos", "alvos_mencionados",
            )}
            spans = [(m.get("segmento", indice), m["inicio"], m["fim"]) for ms in papeis.values() for m in ms]
            if any(s == t and a < d and c < b for i, (s, a, b) in enumerate(spans)
                   for t, c, d in spans[i + 1:]):
                raise ValueError("papéis sobrepostos na mesma ação")
            pedidos, excluidos, mencionados = papeis.values()
            if {m["texto"].casefold() for m in pedidos} & {m["texto"].casefold() for m in excluidos}:
                raise ValueError("alvo simultaneamente solicitado e excluído")
            if ato != "pedido" and pedidos:
                raise ValueError("somente pedido possui alvo solicitado")
            if ato in {"relato", "indeterminado"} and excluidos:
                raise ValueError("menção não cria restrição operacional")
            if ato != "pedido" and resolucao != "nao_aplicavel":
                raise ValueError("resolução de pedido aplicada a outro ato")
            if ato == "pedido":
                if resolucao == "nao_aplicavel" or (resolucao == "explicito" and not pedidos):
                    raise ValueError("pedido precisa explicitar resolução do alvo")
                if resolucao in {"alternativa", "ausente"} and pedidos:
                    raise ValueError("alvo ainda ausente não pode constar como solicitado")
                if resolucao == "contextual" and not mencionados:
                    raise ValueError("referência contextual precisa de menção")
    if vistos != set(por_indice):
        raise ValueError("segmentos canônicos sem cobertura")
    return {"versao": versao, "tipo": "anotacao_escopo_offline",
            "somente_observacao": True, "autoriza_execucao": False,
            "treino_permitido": False, "autoriza_promocao": False,
            "referencia": referencia, "anotacao": deepcopy(dict(anotacao))}
