"""Contraste offline de cópia exata versus índices de um alvo explícito."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import subprocess
from time import perf_counter
from typing import Callable

import requests

from scripts.analises import sonda_extracao_literal_v1 as literal


BASE = literal.BASE
MODOS = ("indices", "copia")
HASH_LITERAL = "2d7a8f1562967848a85e02b1afe21101c983b33ed4eee799ea7eb7fbf64e7d95"
FORMATO_COPIA = {"type": "object", "additionalProperties": False, "required": ["evidencias"],
    "properties": {"evidencias": {"type": "array", "maxItems": 2, "items": {"type": "string"}}}}
SISTEMA_COPIA = literal.SISTEMA.replace(
    "Use os IDs dos tokens: inicio inclusivo e fim exclusivo.",
    "Copie o texto literal, nao os IDs ou indices dos tokens."
).replace("retorne seu intervalo", "retorne seu texto literal").replace(
    "lista de objetos com inicio e fim inteiros", "lista de strings literais")


def carregar_painel() -> list[dict]:
    if hashlib.sha256(Path(literal.__file__).read_bytes()).hexdigest() != HASH_LITERAL:
        raise ValueError("dependencia literal congelada alterada")
    return literal.carregar_painel()


def conferir_copia(caso: dict, entrada_host: dict, proposta: object) -> dict:
    guarda = literal.schema.etapas.conferir_selecao_externa
    base = guarda(caso, entrada_host, None)
    if base["estado"] in {"entrada_adulterada", "fonte_ou_foco_invalido"}:
        return base
    if (not isinstance(proposta, dict) or set(proposta) != {"evidencias"}
            or not isinstance(proposta["evidencias"], list) or len(proposta["evidencias"]) > 2
            or any(not isinstance(t, str) or not t.strip() for t in proposta["evidencias"])):
        return base
    intervalos = []
    for texto in proposta["evidencias"]:
        ocorrencia = literal.calcular_esperado({**caso, "alvo_literal_solicitado": texto})["evidencias"]
        if not ocorrencia:
            return {**base, "estado": "copia_sem_ocorrencia_externa_unica"}
        intervalos.extend(ocorrencia)
    return guarda(caso, entrada_host, {"evidencias": intervalos})


def preparar_requisicao(caso: dict, modo: str) -> dict:
    if modo not in MODOS:
        raise ValueError("modo de representacao invalido")
    r = literal.preparar_requisicao(caso, "schema_restritivo")
    if modo == "copia":
        r["messages"][0]["content"] = SISTEMA_COPIA
        r["format"] = deepcopy(FORMATO_COPIA)
    return r


def medir_caso(caso: dict, *, modo: str, post: Callable = requests.post) -> dict:
    requisicao = preparar_requisicao(caso, modo)
    r = {**BASE, "id": caso["id"], "modo": modo, "requisicao": deepcopy(requisicao),
         "entrada_host": literal.schema.etapas.vinculo.preparar_entrada(caso)}
    inicio = perf_counter()
    try:
        r.update(literal.schema.capturar_http(deepcopy(requisicao), post))
    except Exception as erro:
        r["erro_consulta"] = type(erro).__name__
    r["duracao_consulta_s"] = perf_counter() - inicio
    return r


def aferir_caso(caso: dict, r: dict) -> dict:
    esperado = literal.calcular_esperado(caso)
    iguais = literal.schema.etapas.iguais_tipados
    if not iguais(caso["esperado"], esperado):
        raise ValueError("referencia literal adulterada")
    if not isinstance(r, dict) or r.get("id") != caso["id"] or r.get("modo") not in MODOS:
        raise ValueError("registro invalido")
    if not iguais(r.get("requisicao"), preparar_requisicao(caso, r["modo"])):
        raise ValueError("requisicao adulterada")
    host = literal.schema.etapas.vinculo.preparar_entrada(caso)
    if not iguais(r.get("entrada_host"), host) or any(r.get(k) is not False for k in BASE):
        raise ValueError("host ou flags adulterados")
    literal.schema.etapas.conferir_registro_consulta({"proposta": None,
        "duracao_consulta_s": r.get("duracao_consulta_s")})
    if "erro_consulta" in r:
        if not isinstance(r["erro_consulta"], str) or "http_bruto" in r or "http_status" in r:
            raise ValueError("consulta contraditoria")
        dec = {"estado_transporte": "erro_consulta", "finalizacao": "nao_confirmada"}
    else:
        dec = literal.schema.decodificar_http(r.get("http_status"), r.get("http_bruto"))
    guarda = literal.schema.etapas.conferir_selecao_externa if r["modo"] == "indices" else conferir_copia
    conf = guarda(caso, host, dec.get("proposta"))
    referencia = literal.schema.etapas.conferir_selecao_externa(caso, host, esperado)
    valido = conf["estado"] in {"selecao_literal_revisao_pendente", "selecao_vazia_revisao_pendente"}
    alinhado = valido and iguais({"evidencias": conf["evidencias"]}, {"evidencias": referencia["evidencias"]})
    return {**BASE, "positivo": bool(esperado["evidencias"]), "interpretacao": dec,
            "estado_selecao": conf["estado"], "literal_materializado": conf["evidencia_literal_externa"],
            "evidencias": conf["evidencias"], "alinhado_literal": alinhado,
            "alinhado_literal_concluido": alinhado and dec["finalizacao"] == "concluida"}


def resumir(casos: list[dict], resultados: list[dict]) -> dict:
    invalido = {**BASE, "tipo": "resumo_invalido"}
    if casos != carregar_painel():
        return invalido
    if any(not isinstance(r, dict) or not isinstance(r.get("id"), str) or r.get("modo") not in MODOS
           for r in resultados):
        return invalido
    chaves = [(r["id"], r["modo"]) for r in resultados]
    if len(set(chaves)) != len(chaves) or set(chaves) != {(c["id"], m) for c in casos for m in MODOS}:
        return invalido
    por_id = {c["id"]: c for c in casos}
    try:
        aferidos = [(r, aferir_caso(por_id[r["id"]], r)) for r in resultados]
        duracoes = {m: math.fsum(r["duracao_consulta_s"] for r in resultados if r["modo"] == m) for m in MODOS}
    except (KeyError, TypeError, ValueError, OverflowError):
        return invalido
    resumo = {**BASE, "tipo": "resumo_representacao_literal", "holdout_semantico": False, "bracos": {}}
    for m in MODOS:
        rs = [a for r, a in aferidos if r["modo"] == m]
        resumo["bracos"][m] = {"casos": len(rs), "consultas": len(rs), "duracao_consultas_s": duracoes[m],
            "positivos": sum(a["positivo"] for a in rs), "negativos": sum(not a["positivo"] for a in rs),
            "positivos_alinhados_concluidos": sum(a["positivo"] and a["alinhado_literal_concluido"] for a in rs),
            "negativos_alinhados_concluidos": sum(not a["positivo"] and a["alinhado_literal_concluido"] for a in rs),
            "literais_materializados": sum(a["literal_materializado"] for a in rs),
            "estados_selecao": dict(Counter(a["estado_selecao"] for a in rs)),
            "estados_transporte": dict(Counter(a["interpretacao"]["estado_transporte"] for a in rs)),
            "finalizacoes": dict(Counter(a["interpretacao"]["finalizacao"] for a in rs))}
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    casos = carregar_painel()
    digest = literal.schema.etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        metadata = {**BASE, "tipo": "metadata", "data_contexto": "2026-10-06",
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "hash_literal": HASH_LITERAL, "hash_painel": literal.HASH_PAINEL,
            "digest_modelo_inicio": digest, "ordem_3_ab_3_ba": True,
            "runtime_laylay": False, "holdout_semantico": False, "alvo_explicito_pode_ser_ecoado": True,
            "schema_nos_dois_bracos": True, "instrucoes_de_representacao_diferentes": True,
            "referencias_host_pre_consulta": {c["id"]: literal.calcular_esperado(c) for c in casos}}
        arquivo.write(json.dumps(metadata, ensure_ascii=False, allow_nan=False) + "\n")
        arquivo.flush()
        resultados = []
        for i, c in enumerate(casos):
            for modo in MODOS if i % 2 == 0 else tuple(reversed(MODOS)):
                r = medir_caso(c, modo=modo)
                a = aferir_caso(c, r)
                resultados.append(r)
                arquivo.write(json.dumps({**r, "tipo": "consulta", "afericao": a}, ensure_ascii=False, allow_nan=False) + "\n")
                arquivo.flush()
                print(json.dumps({"id": c["id"], "modo": modo, "estado": a["estado_selecao"],
                                  "alinhado_concluido": a["alinhado_literal_concluido"]}), flush=True)
        resumo = resumir(casos, resultados)
        try:
            resumo["digest_modelo_final"] = literal.schema.etapas.coordenadas.digest_modelo()
            resumo["modelo_inalterado_entre_leituras"] = resumo["digest_modelo_final"] == digest
        except Exception as erro:
            resumo["erro_digest_final"] = type(erro).__name__
            resumo["modelo_inalterado_entre_leituras"] = False
        arquivo.write(json.dumps(resumo, ensure_ascii=False, allow_nan=False) + "\n")
        print(json.dumps(resumo, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
