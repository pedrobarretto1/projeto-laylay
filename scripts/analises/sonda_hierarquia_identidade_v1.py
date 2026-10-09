"""Fatorial offline: caminho sintático explícito e rótulo de transporte do foco."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter
from typing import Callable

import requests

from scripts.analises import sonda_ensino_contrastivo_v1 as anterior


BASE = anterior.BASE
HASH_ANTERIOR = "45cdb3e8fe8802d65fed5c6d38b1e69608ca74eaf4930663643706d5dc326244"
IDS = ("E04A", "E04B", "U04", "N03", "E03A", "E03B", "U02", "N06", "E05A", "E05B")
MODOS = ("base", "id_uniforme", "hierarquia", "hierarquia_id_uniforme")


def carregar_painel() -> list[dict]:
    if hashlib.sha256(Path(anterior.__file__).read_bytes()).hexdigest() != HASH_ANTERIOR:
        raise ValueError("dependencia congelada alterada")
    indice = {c["id"]: c for c in anterior.carregar_painel()["avaliacao"]}
    return [indice[i] for i in IDS]


def projetar_entrada(caso: dict, entrada: dict, modo: str) -> dict:
    """Autentica antes de projetar. Não modifica identidade canônica ou fonte."""
    if modo not in MODOS:
        raise ValueError("modo invalido")
    canonica = anterior.papel.preparar_entrada(anterior.caso_host(caso))
    if not anterior.etapas.iguais_tipados(canonica, entrada):
        raise ValueError("entrada adulterada")
    e = deepcopy(entrada)
    if modo.endswith("id_uniforme"):
        # Apenas etiqueta de transporte; a ocorrência continua nos offsets do host.
        e["foco"]["id"] = "c1"
    if modo.startswith("hierarquia"):
        regioes = {r["id"]: r for r in e["aspas_sintaticas"]["regioes_entre_aspas"]}
        caminho, vistos = [], set()
        cursor = e["foco"]["regiao_aspas_id"]
        while cursor:
            if cursor in vistos or cursor not in regioes:
                raise ValueError("hierarquia inconsistente")
            vistos.add(cursor)
            r = regioes[cursor]
            if not r["inicio"] <= e["foco"]["inicio"] < e["foco"]["fim"] <= r["fim"]:
                raise ValueError("regiao nao contem foco")
            caminho.append(deepcopy(r))
            cursor = r["pai_id"]
        e["hierarquia_sintatica_do_foco"] = {
            "fonte_id": e["fonte"]["identificador"],
            "regioes_externa_para_interna": list(reversed(caminho)),
            "ocorrencia": deepcopy(e["foco"])}
    return e


def preparar_requisicao(caso: dict, modo: str) -> dict:
    r = anterior.preparar_requisicao(caso, "com_exemplos")
    if modo not in MODOS:
        raise ValueError("modo invalido")
    if modo == "base":
        return r
    casos = anterior.carregar_painel()["demonstracoes"] + [caso]
    for c, mensagem in zip(casos, r["messages"][1::2], strict=True):
        e = projetar_entrada(c, json.loads(mensagem["content"]), modo)
        mensagem["content"] = json.dumps(e, ensure_ascii=False)
    return r


def sequencia(casos: list[dict]) -> list[tuple[dict, str, int]]:
    # Mesmo caso recebe todas as variantes; segunda passagem inverte blocos e ordem.
    primeira = [(c, m) for i, c in enumerate(casos) for m in MODOS[i % 4:] + MODOS[:i % 4]]
    return [(c, m, rep) for rep in (1, 2)
            for c, m in (primeira if rep == 1 else list(reversed(primeira)))]


def medir_caso(caso: dict, *, modo: str, repeticao: int, post: Callable = requests.post) -> dict:
    r = {**BASE, "id": caso["id"], "modo": modo, "repeticao": repeticao,
         "entrada_host": anterior.papel.preparar_entrada(caso), "requisicao": preparar_requisicao(caso, modo)}
    inicio = perf_counter()
    try:
        r.update(anterior.schema.capturar_http(deepcopy(r["requisicao"]), post))
    except Exception as erro:
        r["erro_consulta"] = type(erro).__name__
    r["duracao_consulta_s"] = perf_counter() - inicio
    return r


def aferir_caso(caso: dict, r: dict) -> dict:
    if (not isinstance(r, dict) or r.get("modo") not in MODOS
            or not anterior.etapas.iguais_tipados(r.get("requisicao"), preparar_requisicao(caso, r["modo"]))):
        raise ValueError("projecao ou requisicao adulterada")
    # A requisição efetiva foi autenticada acima. Delegar a mesma saída bruta
    # ao aferidor congelado em seu envelope conhecido, sem adaptar texto/offsets.
    # Este envelope transitório não substitui a requisição efetiva no artefato.
    ponte = {**r, "modo": "com_exemplos", "requisicao": anterior.preparar_requisicao(caso, "com_exemplos")}
    return anterior.aferir_caso(caso, ponte)


def resumir(rs: list[dict]) -> dict:
    invalido = {**BASE, "tipo": "resumo_invalido"}
    casos = carregar_painel()
    if (not isinstance(rs, list) or any(not isinstance(r, dict) for r in rs)
            or [(r.get("id"), r.get("modo"), r.get("repeticao")) for r in rs]
            != [(c["id"], m, rep) for c, m, rep in sequencia(casos)]):
        return invalido
    ix = {c["id"]: c for c in casos}
    try:
        aferidos = {(r["id"], r["modo"], r["repeticao"]): aferir_caso(ix[r["id"]], r) for r in rs}
    except (ValueError, KeyError, TypeError, OverflowError):
        return invalido
    bracos, por_caso = {}, {}
    for m in MODOS:
        bracos[m] = {str(rep): {k: sum(aferidos[c["id"], m, rep][k] for c in casos)
                                for k in anterior.METRICAS} for rep in (1, 2)}
    for c in casos:
        por_caso[c["id"]] = {m: [
            {k: aferidos[c["id"], m, rep][k] for k in (*anterior.METRICAS, "papel_proposto")}
            for rep in (1, 2)] for m in MODOS}
    return {**BASE, "tipo": "resumo_hierarquia_identidade", "consultas": len(rs), "casos": len(casos),
            "bracos": bracos, "por_caso": por_caso, "runtime_laylay": False, "holdout_novo": False,
            "revisao_humana_independente": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    casos = carregar_painel()
    digest = anterior.etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arq:
        def escrever(item: dict) -> None:
            arq.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n")
            arq.flush()
        escrever({**BASE, "tipo": "metadata", "casos_pre_consulta": casos,
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "hash_anterior": HASH_ANTERIOR, "hash_dados": anterior.HASH_DADOS, "digest_inicio": digest,
            "ordem": [(c["id"], m, rep) for c, m, rep in sequencia(casos)],
            "runtime_laylay": False, "holdout_novo": False})
        rs = []
        for c, m, rep in sequencia(casos):
            r = medir_caso(c, modo=m, repeticao=rep)
            a = aferir_caso(c, r)
            rs.append(r)
            escrever({**r, "tipo": "consulta", "afericao": a})
            print(json.dumps({"id": c["id"], "modo": m, "rep": rep,
                              "papel": a["papel_proposto"], "conjunto": a["conjunto"]}), flush=True)
        resumo = resumir(rs)
        try:
            resumo["digest_final"] = anterior.etapas.coordenadas.digest_modelo()
            resumo["modelo_igual_entre_leituras"] = resumo["digest_final"] == digest
        except Exception as erro:
            resumo["erro_digest_final"] = type(erro).__name__
            resumo["modelo_igual_entre_leituras"] = False
        escrever(resumo)
        print(json.dumps(resumo["bracos"]), flush=True)


if __name__ == "__main__":
    main()
