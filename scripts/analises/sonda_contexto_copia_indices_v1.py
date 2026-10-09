"""Seleção offline de contexto sem alvo fornecido; cópia versus índices."""

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

from scripts.analises import sonda_copia_indices_literal_v1 as representacao


schema = representacao.literal.schema
etapas = schema.etapas
BASE = etapas.BASE
MODOS = ("indices", "copia")
HASH_REPRESENTACAO = "fb9d6085e296e1d70c6f70ccf14c3ac97d3bb81616ec7f44b9eae6633897f2de"
SISTEMA_COPIA = etapas.SISTEMA_SELECAO.replace(
    "ate dois intervalos de CONTEXTO EXTERNO", "ate dois trechos literais de CONTEXTO EXTERNO"
).replace(
    "Use inicio inclusivo e fim exclusivo dos IDs de tokens, preservando ordem dos intervalos.",
    "Copie exatamente cada trecho, preservando sua ordem na fonte. Nao retorne indices."
).replace("Retorne somente JSON com evidencias.",
          "Retorne somente JSON com evidencias como lista de strings literais.")


def carregar_painel() -> tuple[list[dict], dict, list[str]]:
    if hashlib.sha256(Path(representacao.__file__).read_bytes()).hexdigest() != HASH_REPRESENTACAO:
        raise ValueError("guarda de representacao congelada alterada")
    # Autentica também as dependências transitivas da materialização de cópia.
    representacao.carregar_painel()
    return schema.carregar_painel()


def preparar_requisicao(caso: dict, modo: str) -> dict:
    if modo not in MODOS:
        raise ValueError("modo de representacao invalido")
    requisicao = schema.preparar_requisicao(caso, "schema_restritivo")
    if modo == "copia":
        requisicao["messages"][0]["content"] = SISTEMA_COPIA
        requisicao["format"] = deepcopy(representacao.FORMATO_COPIA)
    return requisicao


def medir_caso(caso: dict, *, modo: str, post: Callable = requests.post) -> dict:
    requisicao = preparar_requisicao(caso, modo)
    registro = {**BASE, "id": caso["id"], "modo": modo,
                "requisicao": deepcopy(requisicao), "entrada_host": etapas.vinculo.preparar_entrada(caso)}
    inicio = perf_counter()
    try:
        registro.update(schema.capturar_http(deepcopy(requisicao), post))
    except Exception as erro:
        registro["erro_consulta"] = type(erro).__name__
    registro["duracao_consulta_s"] = perf_counter() - inicio
    return registro


def aferir_caso(caso: dict, registro: dict, ouro: dict) -> dict:
    if (not isinstance(registro, dict) or registro.get("id") != caso["id"]
            or registro.get("modo") not in MODOS):
        raise ValueError("registro invalido")
    if not etapas.iguais_tipados(registro.get("requisicao"), preparar_requisicao(caso, registro["modo"])):
        raise ValueError("requisicao adulterada")
    host = etapas.vinculo.preparar_entrada(caso)
    if (not etapas.iguais_tipados(registro.get("entrada_host"), host)
            or any(registro.get(k) is not False for k in BASE)):
        raise ValueError("host ou flags adulterados")
    etapas.conferir_registro_consulta({"proposta": None,
                                      "duracao_consulta_s": registro.get("duracao_consulta_s")})
    if "erro_consulta" in registro:
        if (not isinstance(registro["erro_consulta"], str)
                or "http_bruto" in registro or "http_status" in registro):
            raise ValueError("consulta contraditoria")
        dec = {"estado_transporte": "erro_consulta", "finalizacao": "nao_confirmada"}
    else:
        dec = schema.decodificar_http(registro.get("http_status"), registro.get("http_bruto"))
    guarda = etapas.conferir_selecao_externa if registro["modo"] == "indices" else representacao.conferir_copia
    conf = guarda(caso, host, dec.get("proposta"))
    literal = conf["evidencia_literal_externa"]
    concluida = dec["finalizacao"] == "concluida"
    proposta = dec.get("proposta")
    emitiu = (isinstance(proposta, dict) and isinstance(proposta.get("evidencias"), list)
              and bool(proposta["evidencias"]))
    # Métrica lexical a posteriori, nunca fornecida ao modelo ou à guarda.
    cobertura = bool(literal and any(all(any(ancora.casefold() in e["texto"].casefold()
        for e in conf["evidencias"]) for ancora in alternativa) for alternativa in ouro["ancoras"]))
    return {**BASE, "interpretacao": dec, "estado_selecao": conf["estado"],
            "selecao_literal_valida": literal, "selecao_literal_concluida": literal and concluida,
            "selecao_vazia": conf["estado"] == "selecao_vazia_revisao_pendente",
            "selecao_invalida": conf["estado"] not in {
                "selecao_literal_revisao_pendente", "selecao_vazia_revisao_pendente"},
            "emitiu_trechos": emitiu, "cobertura_lexical": cobertura,
            "cobertura_lexical_concluida": cobertura and concluida, "evidencias": conf["evidencias"]}


def resumir(casos: list[dict], resultados: list[dict], ouro: dict) -> dict:
    invalido = {**BASE, "tipo": "resumo_invalido"}
    canonicos, ouro_canonico, pares = carregar_painel()
    if (not etapas.iguais_tipados({"casos": casos}, {"casos": canonicos})
            or not etapas.iguais_tipados(ouro, ouro_canonico)):
        return invalido
    if any(not isinstance(r, dict) or not isinstance(r.get("id"), str)
           or r.get("modo") not in MODOS for r in resultados):
        return invalido
    chaves = [(r["id"], r["modo"]) for r in resultados]
    if len(set(chaves)) != len(chaves) or set(chaves) != {(c["id"], m) for c in casos for m in MODOS}:
        return invalido
    por_id = {c["id"]: c for c in casos}
    try:
        aferidos = {(r["id"], r["modo"]): aferir_caso(por_id[r["id"]], r, ouro[r["id"]]) for r in resultados}
        duracoes = {m: math.fsum(r["duracao_consulta_s"] for r in resultados if r["modo"] == m) for m in MODOS}
    except (KeyError, ValueError, TypeError, OverflowError):
        return invalido
    resumo = {**BASE, "tipo": "resumo_contexto_representacao", "holdout_novo": False,
              "segunda_etapa_executada": False, "bracos": {}}
    campos = ("selecao_literal_valida", "selecao_literal_concluida", "selecao_vazia",
              "selecao_invalida", "emitiu_trechos", "cobertura_lexical", "cobertura_lexical_concluida")
    for modo in MODOS:
        rs = [aferidos[c["id"], modo] for c in casos]
        resumo["bracos"][modo] = {**{k: sum(a[k] for a in rs) for k in campos},
            "casos": len(rs), "consultas": len(rs), "duracao_consultas_s": duracoes[modo],
            "pares": len(pares), "pares_cobertura_lexical_concluida": sum(
                all(aferidos[p + lado, modo]["cobertura_lexical_concluida"] for lado in ("A", "B")) for p in pares),
            "estados_transporte": dict(Counter(a["interpretacao"]["estado_transporte"] for a in rs)),
            "finalizacoes": dict(Counter(a["interpretacao"]["finalizacao"] for a in rs)),
            "estados_selecao": dict(Counter(a["estado_selecao"] for a in rs))}
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    casos, ouro, pares = carregar_painel()
    digest = etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        metadata = {**BASE, "tipo": "metadata", "data_contexto": "2026-10-06",
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "hash_representacao": HASH_REPRESENTACAO, "hashes_painel": etapas.vinculo.HASHES,
            "digest_modelo_inicio": digest, "ordem_10_ab_10_ba": True,
            "runtime_laylay": False, "holdout_novo": False, "segunda_etapa_executada": False,
            "alvo_e_ancoras_fornecidos": False, "schema_nos_dois_bracos": True,
            "instrucoes_de_representacao_diferentes": True,
            "http_textual_bruto_preservado": True, "http_bytes_preservados": False,
            "referencias_host_pre_consulta": ouro, "pares_pre_consulta": pares}
        arquivo.write(json.dumps(metadata, ensure_ascii=False, allow_nan=False) + "\n")
        arquivo.flush()
        resultados = []
        for i, caso in enumerate(casos):
            for modo in MODOS if i % 2 == 0 else tuple(reversed(MODOS)):
                r = medir_caso(caso, modo=modo)
                a = aferir_caso(caso, r, ouro[caso["id"]])
                resultados.append(r)
                arquivo.write(json.dumps({**r, "tipo": "consulta", "afericao": a}, ensure_ascii=False, allow_nan=False) + "\n")
                arquivo.flush()
                print(json.dumps({"id": caso["id"], "modo": modo, "estado": a["estado_selecao"],
                                  "cobertura_lexical_concluida": a["cobertura_lexical_concluida"]}), flush=True)
        resumo = resumir(casos, resultados, ouro)
        try:
            resumo["digest_modelo_final"] = etapas.coordenadas.digest_modelo()
            resumo["modelo_inalterado_entre_leituras"] = resumo["digest_modelo_final"] == digest
        except Exception as erro:
            resumo["erro_digest_final"] = type(erro).__name__
            resumo["modelo_inalterado_entre_leituras"] = False
        arquivo.write(json.dumps(resumo, ensure_ascii=False, allow_nan=False) + "\n")
        print(json.dumps(resumo, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
