"""Controle offline do formato da primeira seleção; não promove significado."""

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
from typing import Callable, Mapping

import requests

from scripts.analises import sonda_vinculo_duas_etapas_v1 as etapas


BASE = etapas.BASE
MODOS = ("schema_restritivo", "json_generico")
HASH_ETAPAS = "656c8d2174469a054d23c826a146085792471849f0e5213ada8eac5b230b68b0"


def carregar_painel() -> tuple[list[dict], dict, list[str]]:
    if hashlib.sha256(Path(etapas.__file__).read_bytes()).hexdigest() != HASH_ETAPAS:
        raise ValueError("sonda de etapas congelada alterada")
    return etapas.carregar_painel()


def preparar_requisicao(caso: Mapping[str, object], modo: str) -> dict:
    if modo not in MODOS:
        raise ValueError("modo de schema invalido")
    entrada = etapas.coordenadas.projetar_entrada_modelo(caso, modo="tokens_id_texto")
    return {"model": "qwen3:4b-instruct", "stream": False,
            "format": deepcopy(etapas.FORMATO_SELECAO) if modo == MODOS[0] else "json",
            "options": {"temperature": 0, "num_predict": 700},
            "messages": [{"role": "system", "content": etapas.SISTEMA_SELECAO},
                         {"role": "user", "content": json.dumps(entrada, ensure_ascii=False)}]}


def capturar_http(requisicao: dict, post: Callable = requests.post) -> dict:
    resposta = post("http://127.0.0.1:11434/api/chat", json=requisicao, timeout=90)
    # A captura precede HTTP/JSON/shape: falhas de interpretação não apagam a fonte.
    return {"http_status": resposta.status_code, "http_bruto": resposta.text}


def _recusar_constante(valor: str) -> None:
    raise ValueError("constante JSON nao finita: " + valor)


def decodificar_http(status: int, bruto: str) -> dict:
    if type(status) is not int or not 100 <= status <= 599 or not isinstance(bruto, str):
        raise ValueError("captura HTTP invalida")
    r = {"estado_transporte": "erro_http", "finalizacao": "nao_confirmada"}
    if status != 200:
        return r
    try:
        envelope = json.loads(bruto, parse_constant=_recusar_constante)
    except (ValueError, TypeError):
        return {**r, "estado_transporte": "http_json_invalido"}
    if not isinstance(envelope, dict):
        return {**r, "estado_transporte": "envelope_invalido"}
    r["resposta_json"] = envelope
    if envelope.get("done") is True:
        if envelope.get("done_reason") == "stop":
            r["finalizacao"] = "concluida"
        elif envelope.get("done_reason") == "length":
            r["finalizacao"] = "limite_tokens"
    mensagem = envelope.get("message")
    if not isinstance(mensagem, dict) or not isinstance(mensagem.get("content"), str):
        return {**r, "estado_transporte": "conteudo_ausente"}
    r["conteudo_bruto"] = mensagem["content"]
    try:
        r["proposta"] = json.loads(mensagem["content"], parse_constant=_recusar_constante)
    except (ValueError, TypeError):
        return {**r, "estado_transporte": "conteudo_json_invalido"}
    return {**r, "estado_transporte": "json_parseado"}


def medir_caso(caso: Mapping[str, object], *, modo: str,
               post: Callable = requests.post) -> dict:
    requisicao = preparar_requisicao(caso, modo)
    entrada = etapas.vinculo.preparar_entrada(caso)
    r = {**BASE, "id": caso["id"], "modo": modo, "requisicao": deepcopy(requisicao),
         "entrada_host": entrada}
    inicio = perf_counter()
    try:
        r.update(capturar_http(deepcopy(requisicao), post))
    except Exception as erro:
        r["erro_consulta"] = type(erro).__name__
    r["duracao_consulta_s"] = perf_counter() - inicio
    return r


def aferir_caso(caso: Mapping[str, object], r: dict, ouro: dict) -> dict:
    if not isinstance(r, dict) or r.get("id") != caso["id"] or r.get("modo") not in MODOS:
        raise ValueError("registro de caso invalido")
    if not etapas.iguais_tipados(r.get("requisicao"), preparar_requisicao(caso, r["modo"])):
        raise ValueError("requisicao adulterada")
    if not etapas.iguais_tipados(r.get("entrada_host"), etapas.vinculo.preparar_entrada(caso)):
        raise ValueError("entrada host adulterada")
    if any(r.get(k) is not False for k in BASE):
        raise ValueError("flag indevida de promocao")
    etapas.conferir_registro_consulta({"proposta": None, "duracao_consulta_s": r.get("duracao_consulta_s")})
    if "erro_consulta" in r:
        if (not isinstance(r["erro_consulta"], str) or "http_bruto" in r or "http_status" in r):
            raise ValueError("consulta contraditoria")
        dec = {"estado_transporte": "erro_consulta", "finalizacao": "nao_confirmada"}
    else:
        dec = decodificar_http(r.get("http_status"), r.get("http_bruto"))
    conferencia = etapas.conferir_selecao_externa(caso, r["entrada_host"], dec.get("proposta"))
    literal = conferencia["evidencia_literal_externa"]
    concluida = dec["finalizacao"] == "concluida"
    proposta = dec.get("proposta")
    emitiu = (isinstance(proposta, dict) and isinstance(proposta.get("evidencias"), list)
              and bool(proposta["evidencias"]))
    cobertura = bool(literal and any(all(any(a.casefold() in e["texto"].casefold()
        for e in conferencia["evidencias"]) for a in alternativa) for alternativa in ouro["ancoras"]))
    return {**BASE, "estado_transporte": dec["estado_transporte"], "finalizacao": dec["finalizacao"],
            "estado_selecao": conferencia["estado"], "interpretacao": dec,
            "selecao_literal_valida": literal, "selecao_literal_concluida": literal and concluida,
            "selecao_vazia": conferencia["estado"] == "selecao_vazia_revisao_pendente",
            "selecao_invalida": conferencia["estado"] not in {
                "selecao_literal_revisao_pendente", "selecao_vazia_revisao_pendente"},
            "emitiu_intervalos": emitiu, "cobertura_local": cobertura,
            "cobertura_local_concluida": cobertura and concluida,
            "evidencias": conferencia["evidencias"]}


def resumir(casos: list[dict], resultados: list[dict], ouro: dict) -> dict:
    invalido = {**BASE, "tipo": "resumo_invalido"}
    ids = [c["id"] for c in casos]
    if len(ids) != 20 or len(set(ids)) != 20 or set(ids) != set(ouro):
        return invalido
    if any(not isinstance(r, dict) or not isinstance(r.get("id"), str)
           or r.get("modo") not in MODOS for r in resultados):
        return invalido
    chaves = [(r["id"], r["modo"]) for r in resultados]
    if len(chaves) != len(set(chaves)) or set(chaves) != {(i, m) for i in ids for m in MODOS}:
        return invalido
    por_id = {c["id"]: c for c in casos}
    try:
        aferidos = [(r, aferir_caso(por_id[r["id"]], r, ouro[r["id"]])) for r in resultados]
        duracoes = {m: math.fsum(r["duracao_consulta_s"] for r in resultados if r["modo"] == m)
                   for m in MODOS}
    except (KeyError, ValueError, TypeError, OverflowError):
        return invalido
    resumo = {**BASE, "tipo": "resumo_diagnostico_schema", "holdout_novo": False, "bracos": {}}
    for modo in MODOS:
        rs = [a for r, a in aferidos if r["modo"] == modo]
        campos = ("selecao_literal_valida", "selecao_literal_concluida", "selecao_vazia",
                  "selecao_invalida", "emitiu_intervalos", "cobertura_local", "cobertura_local_concluida")
        resumo["bracos"][modo] = {**{k: sum(a[k] for a in rs) for k in campos}, "casos": len(rs),
            "consultas": len(rs), "duracao_consultas_s": duracoes[modo],
            "estados_transporte": dict(Counter(a["estado_transporte"] for a in rs)),
            "finalizacoes": dict(Counter(a["finalizacao"] for a in rs)),
            "estados_selecao": dict(Counter(a["estado_selecao"] for a in rs))}
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    casos, ouro, _ = carregar_painel()
    digest = etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        metadata = {**BASE, "tipo": "metadata", "data_contexto": "2026-10-06",
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "hash_etapas": HASH_ETAPAS, "hashes_dependencias": etapas.HASHES_DEPENDENCIAS,
            "hashes_painel": etapas.vinculo.HASHES, "digest_modelo_inicio": digest,
            "diferenca_somente_campo_format": True, "ordem_10_ab_10_ba": True,
            "runtime_laylay": False, "holdout_novo": False,
            "http_textual_bruto_preservado": True, "http_bytes_preservados": False,
            "segunda_etapa_executada": False, "modelo": "qwen3:4b-instruct"}
        arquivo.write(json.dumps(metadata, ensure_ascii=False, allow_nan=False) + "\n")
        arquivo.flush()
        resultados = []
        for i, c in enumerate(casos):
            for modo in MODOS if i % 2 == 0 else tuple(reversed(MODOS)):
                r = medir_caso(c, modo=modo)
                afericao = aferir_caso(c, r, ouro[c["id"]])
                resultados.append(r)
                arquivo.write(json.dumps({**r, "tipo": "consulta", "afericao": afericao},
                                         ensure_ascii=False, allow_nan=False) + "\n")
                arquivo.flush()
                print(json.dumps({"id": r["id"], "modo": modo,
                    "transporte": afericao["estado_transporte"], "finalizacao": afericao["finalizacao"],
                    "selecao": afericao["estado_selecao"]}, ensure_ascii=False), flush=True)
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
