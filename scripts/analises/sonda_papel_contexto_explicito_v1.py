"""Papel do foco: fonte integral versus mesma fonte com contexto externo explícito."""

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

from scripts.analises import sonda_contextos_enumerados_v1 as enumerados


etapas, schema, BASE = enumerados.etapas, enumerados.schema, enumerados.BASE
papel = etapas.vinculo.papel
MODOS = ("fonte_integral", "contexto_explicito")
HASH_ENUMERADOS = "9e012ce7e08a176f63c6c87d754678de5bf22bd9a8bcd20c7b37b7b4b34e384f"
HASH_PAPEL = "cfa1043d142a01dedaac2e1fb03f8c38e4bdc4686923b5bbdf94a91ae3146bf0"


def carregar_painel() -> tuple[list[dict], dict, list[str]]:
    for modulo, esperado in ((enumerados, HASH_ENUMERADOS), (papel, HASH_PAPEL)):
        if hashlib.sha256(Path(modulo.__file__).read_bytes()).hexdigest() != esperado:
            raise ValueError("dependencia congelada alterada")
    return enumerados.carregar_painel()


def preparar_requisicao(caso: dict, modo: str) -> dict:
    if modo not in MODOS:
        raise ValueError("modo de contexto invalido")
    entrada = papel.preparar_entrada(caso)
    if modo == "contexto_explicito":
        host = etapas.vinculo.preparar_entrada(caso)
        entrada["contextos_externos"] = [{"id": item["id"], "texto": item["texto"]}
                                       for item in enumerados.enumerar_externos(caso, host)]
    return {"model": "qwen3:4b-instruct", "stream": False, "format": deepcopy(papel.FORMATO),
            "options": {"temperature": 0, "num_predict": 700},
            "messages": [{"role": "system", "content": papel.SISTEMA},
                         {"role": "user", "content": json.dumps(entrada, ensure_ascii=False)}]}


def medir_caso(caso: dict, *, modo: str, post: Callable = requests.post) -> dict:
    requisicao = preparar_requisicao(caso, modo)
    host = etapas.vinculo.preparar_entrada(caso)
    r = {**BASE, "id": caso["id"], "modo": modo, "requisicao": deepcopy(requisicao),
         "entrada_host": host, "inventario_host": enumerados.enumerar_externos(caso, host)}
    inicio = perf_counter()
    try:
        r.update(schema.capturar_http(deepcopy(requisicao), post))
    except Exception as erro:
        r["erro_consulta"] = type(erro).__name__
    r["duracao_consulta_s"] = perf_counter() - inicio
    return r


def aferir_caso(caso: dict, r: dict, ouro: dict) -> dict:
    if not isinstance(r, dict) or r.get("id") != caso["id"] or r.get("modo") not in MODOS:
        raise ValueError("registro invalido")
    host = etapas.vinculo.preparar_entrada(caso)
    inventario = enumerados.enumerar_externos(caso, host)
    if (not etapas.iguais_tipados(r.get("entrada_host"), host)
            or not etapas.iguais_tipados({"itens": r.get("inventario_host")}, {"itens": inventario})
            or not etapas.iguais_tipados(r.get("requisicao"), preparar_requisicao(caso, r["modo"]))
            or any(r.get(k) is not False for k in BASE)):
        raise ValueError("requisicao, host, inventario ou flags adulterados")
    etapas.conferir_registro_consulta({"proposta": None, "duracao_consulta_s": r.get("duracao_consulta_s")})
    if "erro_consulta" in r:
        if not isinstance(r["erro_consulta"], str) or "http_bruto" in r or "http_status" in r:
            raise ValueError("consulta contraditoria")
        dec = {"estado_transporte": "erro_consulta", "finalizacao": "nao_confirmada"}
    else:
        dec = schema.decodificar_http(r.get("http_status"), r.get("http_bruto"))
    conf = papel.conferir_papel(caso, papel.preparar_entrada(caso), dec.get("proposta"))
    valido = conf["estado"] == "papel_proposto_revisao_pendente"
    concluida = dec["finalizacao"] == "concluida"
    alinhado = valido and conf["papel_proposto"] == ouro["papel"]
    return {**BASE, "interpretacao": dec, "estado_papel": conf["estado"],
            "papel_proposto": conf["papel_proposto"], "saida_valida": valido,
            "saida_valida_concluida": valido and concluida,
            "papel_alinhado_local": bool(alinhado), "papel_alinhado_concluido": bool(alinhado and concluida),
            "numero_contextos_host": len(inventario), "avaliacao": "papel_local_nao_suporte_ou_autoridade"}


def resumir(casos: list[dict], resultados: list[dict], ouro: dict) -> dict:
    invalido = {**BASE, "tipo": "resumo_invalido"}
    canonicos, ouro_canonico, pares = carregar_painel()
    if (not etapas.iguais_tipados({"casos": casos}, {"casos": canonicos})
            or not etapas.iguais_tipados(ouro, ouro_canonico)):
        return invalido
    if any(not isinstance(r, dict) or not isinstance(r.get("id"), str) or r.get("modo") not in MODOS for r in resultados):
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
    resumo = {**BASE, "tipo": "resumo_papel_contexto_explicito", "holdout_novo": False,
              "avalia_runtime_laylay": False, "seletor_modelo_executado": False, "bracos": {}}
    for modo in MODOS:
        rs = [aferidos[c["id"], modo] for c in casos]
        por_papel = {}
        confusao = {}
        for esperado in papel.PAPEIS:
            ids = [c["id"] for c in casos if ouro[c["id"]]["papel"] == esperado]
            por_papel[esperado] = {"total": len(ids), "alinhados_concluidos": sum(
                aferidos[i, modo]["papel_alinhado_concluido"] for i in ids)}
            confusao[esperado] = dict(Counter(aferidos[i, modo]["papel_proposto"]
                if aferidos[i, modo]["saida_valida_concluida"] else "saida_invalida_ou_inconclusa" for i in ids))
        resumo["bracos"][modo] = {
            **{k: sum(a[k] for a in rs) for k in ("saida_valida", "saida_valida_concluida",
                                                  "papel_alinhado_local", "papel_alinhado_concluido")},
            "casos": len(rs), "consultas": len(rs), "duracao_consultas_s": duracoes[modo],
            "pares_contextuais": len(pares), "pares_contextuais_alinhados_concluidos": sum(
                all(aferidos[p + lado, modo]["papel_alinhado_concluido"] for lado in ("A", "B")) for p in pares),
            "por_papel": por_papel, "confusao": confusao,
            "estados_transporte": dict(Counter(a["interpretacao"]["estado_transporte"] for a in rs)),
            "finalizacoes": dict(Counter(a["interpretacao"]["finalizacao"] for a in rs)),
            "estados_papel": dict(Counter(a["estado_papel"] for a in rs))}
    comparacoes = Counter()
    mudancas = []
    for c in casos:
        a, b = [aferidos[c["id"], m] for m in MODOS]
        ca, cb = a["papel_alinhado_concluido"], b["papel_alinhado_concluido"]
        comparacoes["ganhos" if cb and not ca else "perdas" if ca and not cb
                    else "ambos_alinhados" if ca else "nenhum_alinhado"] += 1
        if (a["papel_proposto"], a["saida_valida_concluida"]) != (b["papel_proposto"], b["saida_valida_concluida"]):
            mudancas.append({"id": c["id"], "esperado_local": ouro[c["id"]]["papel"],
                            "fonte_integral": a["papel_proposto"], "contexto_explicito": b["papel_proposto"],
                            "alinhado_concluido_fonte": ca, "alinhado_concluido_contexto": cb})
    resumo["comparacao_pareada"] = {k: comparacoes[k] for k in (
        "ganhos", "perdas", "ambos_alinhados", "nenhum_alinhado")}
    resumo["mudancas"] = mudancas
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
            "hash_enumerados": HASH_ENUMERADOS, "hash_papel": HASH_PAPEL,
            "hashes_painel": etapas.vinculo.HASHES, "digest_modelo_inicio": digest,
            "ordem_10_ab_10_ba": True, "runtime_laylay": False, "holdout_novo": False,
            "seletor_modelo_executado": False, "diferenca_somente_campo_contextos_externos": True,
            "prompt_schema_papel_iguais": True, "tokens_nao_fornecidos_em_ambos": True,
            "alvo_e_ancoras_fornecidos": False, "referencias_host_pre_consulta": ouro, "pares_pre_consulta": pares}
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
                print(json.dumps({"id": caso["id"], "modo": modo, "papel": a["papel_proposto"],
                                  "alinhado_concluido": a["papel_alinhado_concluido"]}), flush=True)
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
