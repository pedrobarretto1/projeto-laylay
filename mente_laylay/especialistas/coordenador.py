"""Coordena conversa e operação mantendo uma memória, executor e voz."""

from __future__ import annotations

from typing import Any, Dict, Iterable

from mente_laylay.especialistas.conversa import construir_parecer_conversa
from mente_laylay.especialistas.operacional import (
    anexar_resultados_operacionais,
    construir_parecer_operacional,
)


def construir_parecer_especialistas(
    texto: str,
    *,
    turno: Dict[str, Any] | None,
    funcao_comunicativa: Dict[str, Any] | None,
    retrato: Dict[str, Any] | None,
    saude: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    leitura = dict(turno or {})
    funcao = dict(funcao_comunicativa or {})
    snapshot = dict(retrato or {})
    operacional = construir_parecer_operacional(texto, turno=leitura, retrato=snapshot)
    operacional["saude_componentes"] = dict(saude or {})
    social = construir_parecer_conversa(
        texto,
        turno=leitura,
        funcao_comunicativa=funcao,
        operacional_ativo=bool(operacional.get("ativo")),
    )

    if social.get("ativo") and operacional.get("ativo"):
        modo = "integrado"
        ordem = ["reconhecer_parte_humana", "executar_parte_operacional", "unificar_resultado"]
        consultas = [
            "operacional_consulta_limites_sociais_antes_de_agir",
            "social_consulta_resultado_operacional_antes_de_falar",
        ]
    elif operacional.get("ativo"):
        modo = "operacional"
        ordem = ["executar_parte_operacional", "informar_resultado_real"]
        consultas = []
    else:
        modo = "social"
        ordem = ["responder_parte_humana"]
        consultas = []

    return {
        "social": social,
        "operacional": operacional,
        "coordenacao": {
            "modo": modo,
            "ordem": ordem,
            "consultas": consultas,
            "memoria_compartilhada": True,
            "voz_unica": True,
            "executor_unico": True,
            "consulta_concluida": False,
        },
    }


def registrar_resultado_operacional(
    especialistas: Dict[str, Any] | None,
    comandos: Iterable[Dict[str, Any]] = (),
) -> Dict[str, Any]:
    painel = dict(especialistas or {})
    social = dict(painel.get("social") or {})
    coordenacao = dict(painel.get("coordenacao") or {})
    operacional, possui_resultado = anexar_resultados_operacionais(
        dict(painel.get("operacional") or {}),
        comandos,
    )
    if possui_resultado:
        social["resultado_operacional_consultado"] = bool(social.get("ativo"))
        coordenacao["consulta_concluida"] = True
    painel.update(social=social, operacional=operacional, coordenacao=coordenacao)
    return painel
