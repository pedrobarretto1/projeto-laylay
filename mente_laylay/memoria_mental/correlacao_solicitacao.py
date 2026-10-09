"""Mescla evidência somente dentro da mesma ocorrência operacional.

Identidade organiza pedidos; nunca representa autorização ou prova de efeito.
O executor continua sendo o owner da resolução e do receipt.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import Any

from mente_laylay.memoria_mental.resultado_acao import obter_id_solicitacao


_CAMPOS_RESULTADO = (
    "status", "executou", "confirmado", "ok", "estado_final", "estado_confirmacao",
    "origem", "detalhe", "contexto", "confirmacao_oferecida", "evidencia_confirmacao",
)


def _tem_resultado(solicitacao: Mapping[str, Any]) -> bool:
    return bool(
        str(solicitacao.get("status") or "").strip()
        or any(solicitacao.get(campo) is not None for campo in ("executou", "confirmado", "ok"))
    )


def _intent_canonica(solicitacao: Mapping[str, Any]) -> str:
    # Importação tardia evita o ciclo entre contratos e composição do dispatcher.
    # A projeção resolve apenas o nome; alvo/params não são reinterpretados.
    from mente_laylay.autonomia.dispatcher_comandos_json import (
        normalizar_candidato_json_para_intencao,
    )

    nomes = []
    for campo in ("intent", "acao"):
        nome = solicitacao.get(campo)
        if nome in (None, ""):
            continue
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("Intenção de solicitação deve ser textual.")
        canonico = normalizar_candidato_json_para_intencao({"intent": nome, "params": {}})
        if canonico is None:
            canonico = normalizar_candidato_json_para_intencao({
                "acao": nome, "alvo": solicitacao.get("alvo"),
            })
        if canonico is None:
            raise ValueError("Intenção sem projeção canônica não permite correlação.")
        nomes.append(str(canonico["intent"]))
    if not nomes or len(set(nomes)) != 1:
        raise ValueError("Intenções concorrentes não identificam a mesma solicitação.")
    return nomes[0]


def _copiar_solicitacao(solicitacao: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(solicitacao, Mapping):
        raise ValueError("Solicitação exige um mapping.")
    identidade = obter_id_solicitacao(solicitacao)
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime

    copia = EstadoCompartilhadoRuntime._copiar_valor(dict(solicitacao))
    copia.pop("request_id", None)
    copia["id_solicitacao"] = identidade
    return copia


def _mesclar_mesma_solicitacao(anterior: dict[str, Any], nova: dict[str, Any]) -> dict[str, Any]:
    intent = _intent_canonica(anterior)
    if intent != _intent_canonica(nova):
        raise ValueError("A mesma solicitação não pode mudar de intenção.")
    if _tem_resultado(anterior) and not _tem_resultado(nova):
        # Republicação da proposta não desfaz a resolução observada do executor.
        return deepcopy(anterior)
    mesclada = deepcopy(anterior)
    if _tem_resultado(nova):
        # Um receipt novo substitui o conjunto operacional. Campos ausentes
        # deixam de carregar confirmação e evidência do resultado anterior.
        for campo in _CAMPOS_RESULTADO:
            mesclada.pop(campo, None)
    mesclada.update(deepcopy(nova))
    mesclada.pop("acao", None)
    mesclada["intent"] = intent
    return mesclada


def mesclar_solicitacoes(
    anteriores: Iterable[Mapping[str, Any]], novas: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Mantém ordem e isola ocorrências sem transferir receipt por semelhança.

    Sem ID não há mescla, mesmo quando texto, alvo e intenção são iguais.
    IDs/aliases ou intenções conflitantes levantam ``ValueError`` antes de
    publicar qualquer estado; o chamador decide como registrar a recusa.
    """
    resultado: list[dict[str, Any]] = []
    indices: dict[str, int] = {}
    for grupo in (anteriores, novas):
        for solicitacao in grupo:
            nova = _copiar_solicitacao(solicitacao)
            identidade = nova["id_solicitacao"]
            if identidade and identidade in indices:
                indice = indices[identidade]
                resultado[indice] = _mesclar_mesma_solicitacao(resultado[indice], nova)
            else:
                if identidade:
                    indices[identidade] = len(resultado)
                resultado.append(nova)
    return resultado
