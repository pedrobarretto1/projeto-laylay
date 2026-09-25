"""Sonda P01: tentar falsificar implicação antes de aprovar uma alegação.

Somente avaliação offline. O mesmo Qwen continua sendo um juiz correlacionado
com a geração; nem rótulo correto nem citação localizada certificam a fala.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any, Callable

import requests

from scripts.analises.sonda_implicacao_inedita import (
    CASOS, FONTES, avaliar_com_prova, prova_localizada,
)


INSTRUCAO = (
    "Julgue somente o que a frase-fonte afirma, sem conhecimento externo. "
    "Antes de aprovar, tente imaginar a fonte verdadeira e a alegação falsa: "
    "se isso for possível, a fonte não sustenta a alegação inteira, mesmo que "
    "sustente o começo. Antes de dizer contradita, tente imaginar ambas "
    "verdadeiras: se isso for possível, não é contradição. "
    "sustentada: não existe contraexemplo para a alegação completa; "
    "contradita: fonte e alegação não podem ser verdadeiras na mesma situação; "
    "sem_prova: a fonte não resolve a alegação inteira. "
    "Trate definições, exemplos e detalhes adicionais da mesma maneira. "
    "Retorne SOMENTE JSON com classe e trecho_literal. "
    "Se sustentada ou contradita, copie trecho literal da fonte; "
    "se sem_prova, trecho_literal deve ser vazio."
)


def validar_saida(bruto: Any, fonte: str) -> dict[str, Any]:
    """Confere formato/proveniência; não transforma a opinião em prova semântica."""
    if not isinstance(bruto, dict):
        return {"classe": "invalida", "prova_localizada": False, "rotulo_bruto": "", "trecho_bruto": ""}
    classe = str(bruto.get("classe") or "").strip()
    trecho = str(bruto.get("trecho_literal") or "").strip()
    if not prova_localizada(classe, trecho, fonte):
        return {"classe": "invalida", "prova_localizada": False, "rotulo_bruto": classe, "trecho_bruto": trecho}
    return {"classe": classe, "prova_localizada": True, "rotulo_bruto": classe, "trecho_bruto": trecho}


def avaliar(alegacao: str, fonte: str, *, post=requests.post) -> dict[str, Any]:
    mensagens = [
        {"role": "system", "content": INSTRUCAO},
        {"role": "user", "content": f"Fonte literal: {fonte}\nAlegação: {alegacao}"},
    ]
    inicio = time.monotonic()
    try:
        resposta = post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": "qwen3:4b-instruct", "messages": mensagens,
                  "stream": False, "format": "json",
                  "options": {"temperature": 0, "num_predict": 160}},
            timeout=80,
        )
        resposta.raise_for_status()
        bruto = json.loads(resposta.json()["message"]["content"])
        validado = validar_saida(bruto, fonte)
        erro = ""
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        validado = {"classe": "invalida", "prova_localizada": False, "rotulo_bruto": "", "trecho_bruto": ""}
        erro = type(exc).__name__
    return {**validado, "latencia_s": round(time.monotonic() - inicio, 3), "erro": erro}


def aprovar_seletivamente(resultado: dict[str, Any]) -> bool:
    """Rejeita ou se abstém; jamais converte contradição em fato aprovado."""
    return bool(resultado.get("classe") == "sustentada" and resultado.get("prova_localizada") is True)


def medir_portao_seletivo(
    casos: tuple,
    fontes: dict,
    *,
    julgador: Callable[[str, str], dict[str, Any]],
) -> dict[str, Any]:
    grupos = {papel: {"aceitos_corretos": 0, "sustentados": 0} for papel in ("definicao", "exemplo")}
    falsos_suportes = []
    latencias = []
    for id_caso, id_fonte, papel, alegacao, esperado in casos:
        observado = julgador(alegacao, fontes[id_fonte]["texto"])
        aceito = aprovar_seletivamente(observado)
        grupos[papel]["sustentados"] += int(esperado == "sustentada")
        grupos[papel]["aceitos_corretos"] += int(aceito and esperado == "sustentada")
        if aceito and esperado != "sustentada":
            falsos_suportes.append(id_caso)
        latencias.append(float(observado.get("latencia_s") or 0.0))
    return {
        "grupos": grupos,
        "falsos_suportes": falsos_suportes,
        "latencia_total_s": round(sum(latencias), 2),
        "aprovado_para_producao": False,
    }


def _avaliar_anterior(alegacao: str, fonte: str) -> dict[str, Any]:
    resultado = avaliar_com_prova(alegacao, fonte)
    return {
        "classe": resultado["classe"],
        "prova_localizada": resultado["prova_localizada"],
        "latencia_s": resultado["latencia_s"],
    }


def medir(casos: tuple, fontes: dict) -> dict[str, Any]:
    grupos = {papel: {"acertos": 0, "total": 0} for papel in ("definicao", "exemplo")}
    falsos_suportes = []
    erros = []
    latencias = []
    for id_caso, id_fonte, papel, alegacao, esperado in casos:
        observado = avaliar(alegacao, fontes[id_fonte]["texto"])
        grupos[papel]["total"] += 1
        grupos[papel]["acertos"] += int(observado["classe"] == esperado)
        if esperado != "sustentada" and observado["classe"] == "sustentada":
            falsos_suportes.append(id_caso)
        if observado["classe"] != esperado:
            erros.append({
                "id": id_caso, "esperado": esperado, "observado": observado["classe"],
                "rotulo_bruto": observado["rotulo_bruto"],
                "trecho_bruto": observado["trecho_bruto"],
            })
        latencias.append(observado["latencia_s"])
    return {
        "grupos": grupos, "falsos_suportes": falsos_suportes, "erros": erros,
        "latencia_total_s": round(sum(latencias), 2),
        "aprovado_para_producao": False,
    }


def main() -> int:
    if "--holdout" in sys.argv[1:]:
        from scripts.analises.holdout_implicacao_ensino_v2 import CASOS as casos, FONTES as fontes
        relatorio = {
            "referencia": medir_portao_seletivo(casos, fontes, julgador=_avaliar_anterior),
            "contramundo": medir_portao_seletivo(casos, fontes, julgador=avaliar),
            "gabarito": "holdout_v2_congelado_antes_da_primeira_medicao",
            "aprovado_para_producao": False,
        }
    else:
        relatorio = medir(CASOS, FONTES)
    print(json.dumps(relatorio, ensure_ascii=False))
    return 0 if "referencia" in relatorio or not relatorio["erros"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
