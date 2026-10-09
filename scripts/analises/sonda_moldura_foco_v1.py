"""Ablação diagnóstica de fontes, sem alterar o proponente contrastivo.

Variantes são novas fontes sintéticas, não reescrita de entrada em produção.
O papel de referência permanece no host; não há promoção de interpretação.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

from scripts.analises import sonda_ensino_contrastivo_v1 as anterior


BASE = anterior.BASE
HASH_ANTERIOR = "45cdb3e8fe8802d65fed5c6d38b1e69608ca74eaf4930663643706d5dc326244"
ANINHADOS = ("E04A", "E04B", "U04", "N03")
CONTROLES = ("E03B", "U02", "N06")
medir_caso = anterior.medir_caso
aferir_caso = anterior.aferir_caso


def carregar_painel() -> list[dict]:
    if hashlib.sha256(Path(anterior.__file__).read_bytes()).hexdigest() != HASH_ANTERIOR:
        raise ValueError("proponente congelado alterado")
    antigos = {c["id"]: c for c in anterior.carregar_painel()["avaliacao"]}
    familias = {}
    for origem in ANINHADOS:
        c = antigos[origem]
        e = anterior.papel.preparar_entrada(c)
        regioes = e["aspas_sintaticas"]["regioes_entre_aspas"]
        externa = next(r for r in regioes if not r["pai_id"])
        inicio, fim = externa["inicio"], externa["fim"]
        texto = c["texto"]
        # Fonte contrafactual local: os offsets serão recalculados pelo host.
        familias[origem] = [
            {**c, "variante": "original"},
            {**c, "variante": "citacao_plana", "foco_id": "c1",
             "texto": texto[:inicio].rstrip() + ": " + texto[inicio + 1:fim - 1] + texto[fim:]},
            {**c, "variante": "sem_moldura", "foco_id": "c1",
             "texto": texto[inicio + 1:fim - 1] + "."}]
    c = antigos["E03A"]
    inicio, ressalva = c["texto"].split(", embora ")
    familias["E03A"] = [
        {**c, "variante": "original"},
        {**c, "variante": "sem_ressalva", "texto": inicio + "."},
        {**c, "variante": "ressalva_primeiro",
         "texto": "Embora " + ressalva.removesuffix(".") + ", " + inicio[0].lower() + inicio[1:] + "."}]
    for origem in CONTROLES:
        familias[origem] = [{**antigos[origem], "variante": "original"}]
    # Intercala variantes/famílias; segunda passagem inverte esta ordem.
    casos = []
    for pos in range(3):
        for origem, variantes in familias.items():
            if pos >= len(variantes):
                continue
            v = deepcopy(variantes[pos])
            v.update(id=origem + ":" + v["variante"], origem=origem)
            e = anterior.papel.preparar_entrada(v)
            foco_original = anterior.papel.preparar_entrada(antigos[origem])["foco"]["texto"]
            if e["foco"]["texto"] != foco_original or not e["aspas_sintaticas"]["aspas_coerentes"]:
                raise ValueError("foco alterado na ablacao")
            conf = anterior.anterior.materializar_vinculo(v, e, {"predicado": v["pista"], "papel": v["papel"]})
            if not conf["vinculo_estrutural_valido"]:
                raise ValueError("pista de referencia ausente")
            casos.append(v)
    if len(casos) != 18 or len({c["id"] for c in casos}) != 18:
        raise ValueError("cobertura divergente")
    return casos


def sequencia(casos: list[dict]) -> list[tuple[dict, int]]:
    return [(c, rep) for rep in (1, 2) for c in (casos if rep == 1 else list(reversed(casos)))]


def resumir(registros: list[dict]) -> dict:
    invalido = {**BASE, "tipo": "resumo_invalido"}
    casos = carregar_painel()
    if (not isinstance(registros, list) or any(not isinstance(r, dict) for r in registros)
            or [(r.get("id"), r.get("repeticao"), r.get("modo")) for r in registros]
            != [(c["id"], rep, "com_exemplos") for c, rep in sequencia(casos)]):
        return invalido
    ix = {c["id"]: c for c in casos}
    try:
        aferidos = {(r["id"], r["repeticao"]): aferir_caso(ix[r["id"]], r) for r in registros}
    except (KeyError, TypeError, ValueError, OverflowError):
        return invalido
    familias = {}
    for c in casos:
        itens = [aferidos[c["id"], rep] for rep in (1, 2)]
        familias.setdefault(c["origem"], {})[c["variante"]] = {
            "referencia_local": c["papel"],
            "papeis": [a["papel_proposto"] for a in itens],
            "estados": [a["conferencia"]["estado"] for a in itens],
            "finalizacoes": [a["interpretacao"]["finalizacao"] for a in itens],
            **{k: [a[k] for a in itens] for k in anterior.METRICAS}}
    return {**BASE, "tipo": "resumo_moldura_foco", "familias": familias,
            "consultas": len(registros), "fontes_variantes": len(casos),
            "runtime_laylay": False, "holdout_novo": False, "revisao_humana_independente": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    casos = carregar_painel()
    digest = anterior.etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        def escrever(item: dict) -> None:
            arquivo.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n")
            arquivo.flush()
        escrever({**BASE, "tipo": "metadata", "casos_pre_consulta": casos,
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "hash_anterior": HASH_ANTERIOR, "hash_dados_anteriores": anterior.HASH_DADOS,
            "digest_inicio": digest, "ordem": [(c["id"], rep) for c, rep in sequencia(casos)],
            "runtime_laylay": False, "holdout_novo": False, "proponente_inalterado": True})
        rs = []
        for c, rep in sequencia(casos):
            r = medir_caso(c, modo="com_exemplos", repeticao=rep)
            a = aferir_caso(c, r)
            rs.append(r)
            escrever({**r, "tipo": "consulta", "afericao": a})
            print(json.dumps({"id": c["id"], "rep": rep, "papel": a["papel_proposto"],
                              "alinhado": a["papel_alinhado"], "vinculo": a["vinculo"]}), flush=True)
        resumo = resumir(rs)
        try:
            resumo["digest_final"] = anterior.etapas.coordenadas.digest_modelo()
            resumo["modelo_igual_entre_leituras"] = resumo["digest_final"] == digest
        except Exception as erro:
            resumo["erro_digest_final"] = type(erro).__name__
            resumo["modelo_igual_entre_leituras"] = False
        escrever(resumo)
        print(json.dumps(resumo, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
