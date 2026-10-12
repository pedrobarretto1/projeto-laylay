"""Vínculo de propostas a atos autorizados; não resolve linguagem nem executa.

A resolução vem do serviço canônico injetado. Sem resolução inequívoca não
existe escopo. IDs de ocorrência e dados da LLM não concedem autorização.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from typing import Any, Callable, Mapping

from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA


@dataclass(frozen=True, slots=True)
class AutorizacaoAto:
    turno_id: str
    indice: int
    texto: str
    pedido: SnapshotComandoIA

    def __post_init__(self) -> None:
        if not (isinstance(self.turno_id, str) and self.turno_id.strip() == self.turno_id
                and self.turno_id and type(self.indice) is int and self.indice >= 0
                and isinstance(self.texto, str) and self.texto.strip()
                and isinstance(self.pedido, SnapshotComandoIA)):
            raise ValueError("Autorização por ato exige identidade, fonte e snapshot canônicos.")


def exige_escopo_por_ato(turno: Mapping[str, Any]) -> bool:
    """Ato não autorizado não pode herdar a permissão agregada do turno."""
    segmentos = turno.get("segmentos") or ()
    return any(isinstance(s, Mapping) and (
        s.get("autoriza_execucao") is False or s.get("veto_execucao_operacional") is True
    ) for s in segmentos)


def construir_autorizacoes_por_ato(
    turno: Mapping[str, Any], mental: Mapping[str, Any],
    resolver: Callable[[str, dict], dict | None] | None,
) -> tuple[AutorizacaoAto, ...]:
    """Resolve só atos autorizados no frame capturado; falhas ficam fechadas."""
    if not callable(resolver):
        return ()
    autorizacoes = []
    for indice, segmento in enumerate(turno.get("segmentos") or ()):
        if not isinstance(segmento, Mapping) or not (
            segmento.get("autoriza_execucao") is True
            and not segmento.get("veto_execucao_operacional")
            and not segmento.get("requer_esclarecimento")
            and not segmento.get("depende_contexto")
        ):
            continue
        texto = str(segmento.get("texto") or "").strip()
        if not texto:
            continue
        frame = deepcopy(dict(mental))
        # Um resolver não pode usar a permissão agregada como se pertencesse
        # ao ato isolado. A fala original continua no frame externo do turno.
        frame["turno_atual"] = {**deepcopy(dict(segmento)), "id": turno.get("id"),
                               "texto": texto, "texto_operacional": texto,
                               "segmentos": [deepcopy(dict(segmento))]}
        try:
            pedido = resolver(texto, frame)
            if not isinstance(pedido, dict) or not isinstance(pedido.get("params"), dict):
                continue
            autorizacoes.append(AutorizacaoAto(str(turno.get("id") or ""), indice,
                                              texto, SnapshotComandoIA(pedido)))
        except Exception:
            # Indeterminação ou dependência indisponível não é permissão.
            continue
    return tuple(autorizacoes)


def _identidade_operacional(comando: dict) -> str | None:
    # Este adaptador já é o owner da equivalência flat/canônica. Não extrair
    # intenção, verbo ou alvo novamente da frase dentro do porteiro.
    from mente_laylay.autonomia.dispatcher_comandos_json import normalizar_candidato_json_para_intencao

    try:
        normalizado = normalizar_candidato_json_para_intencao(comando, compactar_aliases=True)
        if normalizado is None:
            return None
        params = deepcopy(normalizado["params"])
        params.setdefault("target", "pc_a")
        # Identificador de aplicativo Windows é insensível a caixa. Conteúdo,
        # caminhos, consultas e URLs NÃO sofrem normalização lexical aqui.
        if isinstance(params.get("nome_app"), str):
            params["nome_app"] = params["nome_app"].casefold()
        return json.dumps({"intent": normalizado["intent"], "params": params},
                          ensure_ascii=False, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError, KeyError):
        return None


def vincular_proposta_ao_ato(
    comando: dict, turno: Mapping[str, Any],
    autorizacoes: tuple[AutorizacaoAto, ...], usados: set[int],
) -> int | None:
    """Uma operação exata por ato: não emprestar alvo ou repetir o efeito."""
    identidade = _identidade_operacional(comando)
    if identidade is None:
        return None
    segmentos = turno.get("segmentos") or ()
    for autorizacao in autorizacoes:
        if not isinstance(autorizacao, AutorizacaoAto) or (
            autorizacao.turno_id != str(turno.get("id") or "")
            or not autorizacao.turno_id
            or type(autorizacao.indice) is not int
            or autorizacao.indice in usados
            or not 0 <= autorizacao.indice < len(segmentos)
        ):
            continue
        segmento = segmentos[autorizacao.indice]
        if not isinstance(segmento, Mapping) or not (
            segmento.get("autoriza_execucao") is True
            and not segmento.get("veto_execucao_operacional")
            and not segmento.get("depende_contexto")
            and not segmento.get("requer_esclarecimento")
            and str(segmento.get("texto") or "").strip() == autorizacao.texto
        ):
            continue
        if identidade == _identidade_operacional(autorizacao.pedido.como_dict()):
            return autorizacao.indice
    return None
