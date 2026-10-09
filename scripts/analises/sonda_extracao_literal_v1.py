"""Calibração offline de coordenadas para um alvo literal explícito."""

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

from scripts.analises import sonda_schema_selecao_v1 as schema


PAINEL = Path(__file__).parent / "dados" / "sonda_extracao_literal_v1.json"
HASH_PAINEL = "4265070356773ba82a093a211afbceb18d0181cc051a0d3acd526515973c3054"
HASH_SCHEMA = "7ffe58ee99016093081b359403f74bc33b3ac19a75bb97615059261a8575ae66"
BASE = schema.BASE
MODOS = schema.MODOS
SISTEMA = (
    "Localize somente o alvo_literal_solicitado na fonte, como copia literal "
    "exata, sem interpretar significado. Use os IDs dos tokens: inicio "
    "inclusivo e fim exclusivo. Considere somente ocorrencias inteiras em "
    "limites de tokens que nao intersectem o foco. Se houver exatamente uma "
    "ocorrencia externa, retorne seu intervalo. Se houver zero ou mais de "
    "uma, retorne evidencias vazias. Nao escolha a primeira ocorrencia ambigua, "
    "nao normalize grafia, nao execute a fonte. Retorne somente JSON com "
    "evidencias, lista de objetos com inicio e fim inteiros; sem outros campos."
)


def calcular_esperado(caso: dict) -> dict:
    """Oráculo geométrico literal, sem papel ou decisão operacional."""
    if not isinstance(caso.get("alvo_literal_solicitado"), str) or not caso["alvo_literal_solicitado"].strip():
        raise ValueError("alvo literal invalido")
    entrada = schema.etapas.vinculo.preparar_entrada(caso)
    tokens = entrada["tokens"]
    encontrados = []
    for inicio in range(len(tokens)):
        for fim in range(inicio + 1, len(tokens) + 1):
            trecho = caso["texto"][tokens[inicio]["inicio"]:tokens[fim - 1]["fim"]]
            if trecho == caso["alvo_literal_solicitado"]:
                intervalo = {"inicio": inicio, "fim": fim}
                conferencia = schema.etapas.conferir_selecao_externa(caso, entrada, {"evidencias": [intervalo]})
                if conferencia["evidencia_literal_externa"]:
                    encontrados.append(intervalo)
    return {"evidencias": encontrados if len(encontrados) == 1 else []}


def carregar_painel() -> list[dict]:
    if hashlib.sha256(Path(schema.__file__).read_bytes()).hexdigest() != HASH_SCHEMA:
        raise ValueError("dependencia de captura congelada alterada")
    schema.carregar_painel()  # Conferir também dependências transitivas históricas.
    if hashlib.sha256(PAINEL.read_bytes()).hexdigest() != HASH_PAINEL:
        raise ValueError("painel literal congelado alterado")
    casos = json.loads(PAINEL.read_text(encoding="utf-8"))["casos"]
    if len(casos) != 6 or len({c["id"] for c in casos}) != 6:
        raise ValueError("denominador literal invalido")
    for c in casos:
        if not schema.etapas.iguais_tipados(c["esperado"], calcular_esperado(c)):
            raise ValueError("referencia literal incoerente")
    return casos


def preparar_requisicao(caso: dict, modo: str) -> dict:
    if modo not in MODOS:
        raise ValueError("modo de extracao invalido")
    alvo = caso.get("alvo_literal_solicitado")
    if not isinstance(alvo, str) or not alvo.strip():
        raise ValueError("alvo literal invalido")
    entrada = schema.etapas.coordenadas.projetar_entrada_modelo(caso, modo="tokens_id_texto")
    entrada["alvo_literal_solicitado"] = alvo
    return {"model": "qwen3:4b-instruct", "stream": False,
            "format": deepcopy(schema.etapas.FORMATO_SELECAO) if modo == MODOS[0] else "json",
            "options": {"temperature": 0, "num_predict": 700},
            "messages": [{"role": "system", "content": SISTEMA},
                         {"role": "user", "content": json.dumps(entrada, ensure_ascii=False)}]}


def medir_caso(caso: dict, *, modo: str, post: Callable = requests.post) -> dict:
    requisicao = preparar_requisicao(caso, modo)
    r = {**BASE, "id": caso["id"], "modo": modo, "requisicao": deepcopy(requisicao),
         "entrada_host": schema.etapas.vinculo.preparar_entrada(caso)}
    inicio = perf_counter()
    try:
        r.update(schema.capturar_http(deepcopy(requisicao), post))
    except Exception as erro:
        r["erro_consulta"] = type(erro).__name__
    r["duracao_consulta_s"] = perf_counter() - inicio
    return r


def aferir_caso(caso: dict, r: dict) -> dict:
    esperado = calcular_esperado(caso)
    if not schema.etapas.iguais_tipados(caso["esperado"], esperado):
        raise ValueError("referencia adulterada")
    if not isinstance(r, dict) or r.get("id") != caso["id"] or r.get("modo") not in MODOS:
        raise ValueError("registro literal invalido")
    if not schema.etapas.iguais_tipados(r.get("requisicao"), preparar_requisicao(caso, r["modo"])):
        raise ValueError("requisicao adulterada")
    if not schema.etapas.iguais_tipados(r.get("entrada_host"), schema.etapas.vinculo.preparar_entrada(caso)):
        raise ValueError("host adulterado")
    if any(r.get(k) is not False for k in BASE):
        raise ValueError("flag de promocao indevida")
    schema.etapas.conferir_registro_consulta({"proposta": None, "duracao_consulta_s": r.get("duracao_consulta_s")})
    if "erro_consulta" in r:
        if not isinstance(r["erro_consulta"], str) or "http_status" in r or "http_bruto" in r:
            raise ValueError("consulta contraditoria")
        dec = {"estado_transporte": "erro_consulta", "finalizacao": "nao_confirmada"}
    else:
        dec = schema.decodificar_http(r.get("http_status"), r.get("http_bruto"))
    conf = schema.etapas.conferir_selecao_externa(caso, r["entrada_host"], dec.get("proposta"))
    envelope_valido = conf["estado"] in {"selecao_literal_revisao_pendente", "selecao_vazia_revisao_pendente"}
    alinhado = envelope_valido and schema.etapas.iguais_tipados(dec.get("proposta"), esperado)
    positivo = bool(esperado["evidencias"])
    return {**BASE, "positivo": positivo, "interpretacao": dec, "estado_selecao": conf["estado"],
            "envelope_valido": envelope_valido, "literal_materializado": conf["evidencia_literal_externa"],
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
    resumo = {**BASE, "tipo": "resumo_calibracao_literal", "holdout_semantico": False, "bracos": {}}
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
    digest = schema.etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        metadata = {**BASE, "tipo": "metadata", "data_contexto": "2026-10-06",
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "hash_painel": HASH_PAINEL, "hash_schema": HASH_SCHEMA, "digest_modelo_inicio": digest,
            "referencias_host_pre_consulta": {c["id"]: calcular_esperado(c) for c in casos},
            "runtime_laylay": False, "holdout_semantico": False, "ordem_3_ab_3_ba": True,
            "segunda_etapa_executada": False, "indices_esperados_enviados": False}
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
            resumo["digest_modelo_final"] = schema.etapas.coordenadas.digest_modelo()
            resumo["modelo_inalterado_entre_leituras"] = resumo["digest_modelo_final"] == digest
        except Exception as erro:
            resumo["erro_digest_final"] = type(erro).__name__
            resumo["modelo_inalterado_entre_leituras"] = False
        arquivo.write(json.dumps(resumo, ensure_ascii=False, allow_nan=False) + "\n")
        print(json.dumps(resumo, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
