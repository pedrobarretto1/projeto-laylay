"""Contraste offline: índices livres versus IDs de contextos delimitados pelo host."""

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

from scripts.analises import sonda_contexto_copia_indices_v1 as controle


etapas, schema, BASE = controle.etapas, controle.schema, controle.BASE
MODOS = ("indices", "ids_contextos")
HASH_CONTROLE = "688390e78582949caeeff5fb2ba2c72b3735273c5afa391f311c1f3aec1afa9b"
SISTEMA_IDS = etapas.SISTEMA_SELECAO.replace(
    "ate dois intervalos de CONTEXTO EXTERNO", "ate dois itens de CONTEXTO EXTERNO"
).replace(
    "Use inicio inclusivo e fim exclusivo dos IDs de tokens, preservando ordem dos intervalos.",
    "O host delimitou todos os contextos externos em contextos_externos, sem indicar "
    "quais apoiam o foco. Escolha seus IDs, preservando a ordem dos itens. "
    "Nao copie texto nem retorne indices."
).replace("Retorne somente JSON com evidencias.",
          "Retorne somente JSON com evidencias como lista de IDs de contextos_externos.")


def carregar_painel() -> tuple[list[dict], dict, list[str]]:
    if hashlib.sha256(Path(controle.__file__).read_bytes()).hexdigest() != HASH_CONTROLE:
        raise ValueError("controle congelado alterado")
    return controle.carregar_painel()


def enumerar_externos(caso: dict, entrada_host: dict) -> list[dict]:
    """Enumera blocos maximais de tokens disjuntos do foco, sem consulta ao gold."""
    base = etapas.conferir_selecao_externa(caso, entrada_host, {"evidencias": []})
    if base["estado"] != "selecao_vazia_revisao_pendente":
        raise ValueError("fonte ou entrada host invalida")
    foco, tokens = entrada_host["foco"], entrada_host["tokens"]
    intervalos, inicio = [], None
    for i, token in enumerate(tokens):
        externo = token["fim"] <= foco["inicio"] or token["inicio"] >= foco["fim"]
        if externo and inicio is None:
            inicio = i
        if not externo and inicio is not None:
            intervalos.append({"inicio": inicio, "fim": i})
            inicio = None
    if inicio is not None:
        intervalos.append({"inicio": inicio, "fim": len(tokens)})
    conf = etapas.conferir_selecao_externa(caso, entrada_host, {"evidencias": intervalos})
    if conf["estado"] not in {"selecao_literal_revisao_pendente", "selecao_vazia_revisao_pendente"}:
        raise ValueError("enumeracao nao materializada")
    return [{"id": f"e{i}", "inicio_token": intervalo["inicio"], "fim_token": intervalo["fim"],
             **evidencia} for i, (intervalo, evidencia) in enumerate(zip(intervalos, conf["evidencias"]))]


def conferir_ids(caso: dict, host: dict, inventario: list[dict], proposta: object) -> dict:
    base = etapas.conferir_selecao_externa(caso, host, None)
    if base["estado"] in {"entrada_adulterada", "fonte_ou_foco_invalido"}:
        return base
    autentico = enumerar_externos(caso, host)
    if not etapas.iguais_tipados({"itens": inventario}, {"itens": autentico}):
        return {**base, "estado": "inventario_adulterado"}
    if (not isinstance(proposta, dict) or set(proposta) != {"evidencias"}
            or not isinstance(proposta["evidencias"], list) or len(proposta["evidencias"]) > 2):
        return base
    por_id = {item["id"]: item for item in autentico}
    if any(not isinstance(i, str) or i not in por_id for i in proposta["evidencias"]):
        return {**base, "estado": "id_contexto_invalido"}
    # Não ordenar, deduplicar, recortar nem reparar a proposta do modelo.
    intervalos = [{"inicio": por_id[i]["inicio_token"], "fim": por_id[i]["fim_token"]}
                  for i in proposta["evidencias"]]
    return etapas.conferir_selecao_externa(caso, host, {"evidencias": intervalos})


def preparar_requisicao(caso: dict, modo: str) -> dict:
    if modo not in MODOS:
        raise ValueError("modo de selecao invalido")
    r = controle.preparar_requisicao(caso, "indices")
    if modo == "ids_contextos":
        host = etapas.vinculo.preparar_entrada(caso)
        entrada = etapas.coordenadas.projetar_entrada_modelo(caso, modo="tokens_id_texto")
        entrada["contextos_externos"] = [{"id": item["id"], "texto": item["texto"]}
                                       for item in enumerar_externos(caso, host)]
        r["messages"][0]["content"] = SISTEMA_IDS
        r["messages"][1]["content"] = json.dumps(entrada, ensure_ascii=False)
        r["format"] = deepcopy(controle.representacao.FORMATO_COPIA)
    return r


def medir_caso(caso: dict, *, modo: str, post: Callable = requests.post) -> dict:
    requisicao = preparar_requisicao(caso, modo)
    host = etapas.vinculo.preparar_entrada(caso)
    r = {**BASE, "id": caso["id"], "modo": modo, "requisicao": deepcopy(requisicao),
         "entrada_host": host, "inventario_host": enumerar_externos(caso, host)}
    inicio = perf_counter()
    try:
        r.update(schema.capturar_http(deepcopy(requisicao), post))
    except Exception as erro:
        r["erro_consulta"] = type(erro).__name__
    r["duracao_consulta_s"] = perf_counter() - inicio
    return r


def cobertura_lexical(evidencias: list[dict], ouro: dict) -> bool:
    return bool(evidencias and any(all(any(ancora.casefold() in e["texto"].casefold()
        for e in evidencias) for ancora in alternativa) for alternativa in ouro["ancoras"]))


def aferir_caso(caso: dict, r: dict, ouro: dict) -> dict:
    if not isinstance(r, dict) or r.get("id") != caso["id"] or r.get("modo") not in MODOS:
        raise ValueError("registro invalido")
    host = etapas.vinculo.preparar_entrada(caso)
    inventario = enumerar_externos(caso, host)
    if (not etapas.iguais_tipados(r.get("entrada_host"), host)
            or not etapas.iguais_tipados({"itens": r.get("inventario_host")}, {"itens": inventario})
            or not etapas.iguais_tipados(r.get("requisicao"), preparar_requisicao(caso, r["modo"]))
            or any(r.get(k) is not False for k in BASE)):
        raise ValueError("requisicao, host, inventario ou flags adulterados")
    if r["modo"] == "indices":
        a = controle.aferir_caso(caso, r, ouro)
    else:
        etapas.conferir_registro_consulta({"proposta": None, "duracao_consulta_s": r.get("duracao_consulta_s")})
        if "erro_consulta" in r:
            if not isinstance(r["erro_consulta"], str) or "http_bruto" in r or "http_status" in r:
                raise ValueError("consulta contraditoria")
            dec = {"estado_transporte": "erro_consulta", "finalizacao": "nao_confirmada"}
        else:
            dec = schema.decodificar_http(r.get("http_status"), r.get("http_bruto"))
        conf = conferir_ids(caso, host, inventario, dec.get("proposta"))
        literal, concluida = conf["evidencia_literal_externa"], dec["finalizacao"] == "concluida"
        proposta = dec.get("proposta")
        cobertura = literal and cobertura_lexical(conf["evidencias"], ouro)
        a = {**BASE, "interpretacao": dec, "estado_selecao": conf["estado"],
             "selecao_literal_valida": literal, "selecao_literal_concluida": literal and concluida,
             "selecao_vazia": conf["estado"] == "selecao_vazia_revisao_pendente",
             "selecao_invalida": conf["estado"] not in {
                 "selecao_literal_revisao_pendente", "selecao_vazia_revisao_pendente"},
             "emitiu_trechos": isinstance(proposta, dict) and isinstance(proposta.get("evidencias"), list)
                 and bool(proposta["evidencias"]), "cobertura_lexical": bool(cobertura),
             "cobertura_lexical_concluida": bool(cobertura and concluida), "evidencias": conf["evidencias"]}
    a["numero_contextos"] = len(inventario)
    a["numero_evidencias"] = len(a["evidencias"])
    a["selecionou_todos_contextos"] = (a["selecao_literal_valida"] and bool(inventario)
        and etapas.iguais_tipados({"evidencias": a["evidencias"]}, {"evidencias": [
            {k: item[k] for k in ("fonte_id", "inicio", "fim", "texto")} for item in inventario]}))
    return a


def medir_controle_todos(casos: list[dict], ouro: dict) -> dict:
    """Controle sem LLM: literalidade/cobertura não demonstram escolha útil."""
    aferidos = []
    for caso in casos:
        host = etapas.vinculo.preparar_entrada(caso)
        inventario = enumerar_externos(caso, host)
        conf = conferir_ids(caso, host, inventario, {"evidencias": [i["id"] for i in inventario]})
        aferidos.append({"id": caso["id"], "numero_contextos": len(inventario),
                        "literal_valido": conf["evidencia_literal_externa"],
                        "cobertura_lexical": cobertura_lexical(conf["evidencias"], ouro[caso["id"]])})
    return {**BASE, "sem_modelo": True, "casos": len(casos),
            "literais_validos": sum(a["literal_valido"] for a in aferidos),
            "cobertura_lexical": sum(a["cobertura_lexical"] for a in aferidos), "aferidos": aferidos}


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
    resumo = {**BASE, "tipo": "resumo_contextos_enumerados", "holdout_novo": False,
              "segunda_etapa_executada": False, "controle_todos_sem_modelo": medir_controle_todos(casos, ouro), "bracos": {}}
    campos = ("selecao_literal_valida", "selecao_literal_concluida", "selecao_vazia", "selecao_invalida",
              "emitiu_trechos", "cobertura_lexical", "cobertura_lexical_concluida", "selecionou_todos_contextos")
    for modo in MODOS:
        rs = [aferidos[c["id"], modo] for c in casos]
        resumo["bracos"][modo] = {**{k: sum(a[k] for a in rs) for k in campos},
            "casos": len(rs), "consultas": len(rs), "duracao_consultas_s": duracoes[modo],
            "evidencias_materializadas": sum(a["numero_evidencias"] for a in rs),
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
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "hash_controle": HASH_CONTROLE,
            "hashes_painel": etapas.vinculo.HASHES, "digest_modelo_inicio": digest, "ordem_10_ab_10_ba": True,
            "runtime_laylay": False, "holdout_novo": False, "segunda_etapa_executada": False,
            "alvo_e_ancoras_fornecidos": False, "schema_nos_dois_bracos": True,
            "contraste_pacotes_geometria_instrucao_schema": True,
            "referencias_host_pre_consulta": ouro, "pares_pre_consulta": pares,
            "controle_todos_pre_consulta": medir_controle_todos(casos, ouro)}
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
                    "cobertura_lexical_concluida": a["cobertura_lexical_concluida"],
                    "selecionou_todos": a["selecionou_todos_contextos"]}), flush=True)
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
