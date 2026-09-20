"""Auditoria dos resultados congelados: sem novos fits e sem previsão gold-fed."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

from .comparar_ocorrencias_v4 import (
    BASE, MODOS, carregar_perfil, medir, representar_tokens, rotular_ocorrencias,
)
from .preparar_lote_relacional_v3 import VARIANTES

FONTE = BASE / "memoria/neural/experimentos/comparacao_ocorrencias_v4_20260908_r1"


def reconstruir_previsoes(casos: list[dict], metrica: dict) -> list[list[str]]:
    """Reconstrói a previsão implícita no relatório COMPLETO, verificando-o.

Não é inferência do candidato: uma linha sem erro deve ser igual ao esperado
por definição do relatório. Recalcular toda a métrica detecta omissões e
inconsistências; sem o relatório íntegro a reconstrução é rejeitada.
"""
    estados = {}
    for c in casos:
        ts, _ = representar_tokens(c["alinhado"]["entrada"])
        for (_, inicio, _), y in zip(ts, rotular_ocorrencias(c)):
            for intent, action in sorted(VARIANTES):
                ato = y.split("|")[-1]
                valor = (ato + ("/explicito" if ato == "pedido" else "/nao_aplicavel")) if y.startswith(f"{intent}|{action}|") else "ausente"
                estados[c["id"], inicio, intent, action] = valor
    vistos = set()
    permitidos = {"ausente", "pedido/explicito", "recusa/nao_aplicavel", "relato/nao_aplicavel"}
    for erro in metrica["erros"]:
        chave = tuple(erro["chave"])
        if (chave not in estados or chave in vistos or estados[chave] != erro["esperado"]
                or erro["previsto"] not in permitidos or erro["previsto"] == erro["esperado"]):
            raise ValueError("erro incompatível com o relatório congelado")
        estados[chave] = erro["previsto"]
        vistos.add(chave)
    saida = []
    for c in casos:
        ys = []
        for _, inicio, _ in representar_tokens(c["alinhado"]["entrada"])[0]:
            presentes = [f"{i}|{a}|{estados[c['id'], inicio, i, a].split('/')[0]}" for i, a in sorted(VARIANTES)
                         if estados[c["id"], inicio, i, a] != "ausente"]
            if len(presentes) > 1:
                raise ValueError("relatório contradiz a saída única por token")
            ys.append(presentes[0] if presentes else "ausente")
        saida.append(ys)
    if medir(casos, saida) != metrica:
        raise ValueError("relatório incompleto: métricas não foram reproduzidas")
    return saida


def medir_colisoes(casos: list[dict]) -> dict:
    """Limite inferior por tokens com features exatamente iguais, não por casos."""
    assinaturas = defaultdict(list)
    for c in casos:
        ts, xs = representar_tokens(c["alinhado"]["entrada"])
        for t, x, y in zip(ts, xs, rotular_ocorrencias(c)):
            assinaturas[tuple(sorted(x.items()))].append({"id": c["id"], "inicio": t[1], "rotulo": y})
    conflitos = []
    for assinatura, linhas in assinaturas.items():
        contagem = Counter(l["rotulo"] for l in linhas)
        if len(contagem) > 1:
            conflitos.append({"atributos": dict(assinatura), "rotulos": dict(contagem), "linhas": linhas,
                              "erros_minimos_tokens": sum(contagem.values()) - max(contagem.values())})
    return {"assinaturas_conflitantes": len(conflitos), "conflitos": conflitos,
            "erros_minimos_tokens": sum(c["erros_minimos_tokens"] for c in conflitos)}


def comparar_pares(casos: list[dict], previsoes: dict[str, list[str]], grupos: dict[str, str]) -> dict:
    """Pares já existentes na MESMA dobra, não teste cego ou prova de causa única."""
    if set(previsoes) != {c["id"] for c in casos} or set(grupos) != set(previsoes):
        raise ValueError("pares sem cobertura completa")
    solos = {}
    for c in casos:
        if len(c["fonte"]["nos"]) == 1:
            texto = c["fonte"]["texto_entrada"]
            if texto in solos:
                raise ValueError("contraparte isolada ambígua")
            solos[texto] = c

    def previsao(c, n):
        ts, _ = representar_tokens(c["alinhado"]["entrada"])
        if len(previsoes[c["id"]]) != len(ts):
            raise ValueError("previsão incompleta")
        indices = [i for i, (t, a, b) in enumerate(ts) if (t, a, b) ==
                   (n["ancora"]["texto"], n["ancora"]["inicio"], n["ancora"]["fim"])]
        if len(indices) != 1:
            raise ValueError("âncora da análise não corresponde a token único")
        return previsoes[c["id"]][indices[0]]

    fatias, transicoes, pares = Counter(), Counter(), []
    for c in casos:
        for n in c["fonte"]["nos"]:
            p = previsao(c, n)
            tipo = "isolado" if len(c["fonte"]["nos"]) == 1 else "composto"
            fatias[n["ato"], tipo, p] += 1
            if tipo == "isolado":
                continue
            s = solos.get(n["trecho"]["texto"])
            if s is None or grupos[s["id"]] != grupos[c["id"]]:
                raise ValueError("contraparte ausente ou em outra dobra")
            ns = s["fonte"]["nos"][0]
            if any(ns[k] != n[k] for k in ("intent", "action", "ato")):
                raise ValueError("contraparte sem equivalência de supervisão")
            ps = previsao(s, ns)
            transicoes[n["ato"], ps, p] += 1
            pares.append({"isolado": s["id"], "composto": c["id"], "ocorrencia": n["id"],
                          "esperado": n["ato"], "previsao_isolada": ps, "previsao_composta": p})
    return {"fatias": [{"ato": a, "tipo": t, "previsto": p, "total": n} for (a, t, p), n in sorted(fatias.items())],
        "transicoes": [{"ato": a, "isolado": s, "composto": c, "total": n} for (a, s, c), n in sorted(transicoes.items())],
        "pares": pares, "limites": "mesma ocorrência participa de mais de um par; posição/janela/contexto variam juntos"}


def executar(destino: Path) -> dict:
    if destino.exists():
        raise FileExistsError("preservar auditoria anterior")
    casos, dobras = carregar_perfil()
    protocolo = json.loads((FONTE / "protocolo.json").read_text(encoding="utf-8"))
    for nome, sha in protocolo["codigo_sha256"].items():
        if hashlib.sha256((BASE / nome).read_bytes()).hexdigest() != sha:
            raise ValueError("dependência do comparativo mudou")
    if protocolo["dobras"] != dobras:
        raise ValueError("dobras do comparativo divergiram")
    por_id = {c["id"]: c for c in casos}
    arquivos = [FONTE / "protocolo.json", FONTE / "resultado.json", Path(__file__)]
    resultados = {}
    for modo in MODOS:
        previstas = {}
        for i, dobra in enumerate(dobras):
            arq = FONTE / f"{modo}_dobra_{i}.json"
            arquivos.append(arq)
            r = json.loads(arq.read_text(encoding="utf-8"))
            if r["modo"] != modo or r["dobra"] != i or r["grupo"] != dobra["grupo_teste"]:
                raise ValueError("relatório de outra condição/dobra")
            cs = [por_id[k] for k in dobra["teste"]]
            ps = reconstruir_previsoes(cs, r["teste"])
            previstas.update({c["id"]: p for c, p in zip(cs, ps)})
        resultados[modo] = comparar_pares(casos, previstas, {c["id"]: c["grupo_validacao"] for c in casos})
    r = {"pareamento": resultados,
         "colisoes_lexicais_treino": [{"grupo_teste": d["grupo_teste"], **medir_colisoes([por_id[i] for i in d["treino"]])} for d in dobras],
         "fontes_sha256": {str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in arquivos},
         "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE, text=True).strip(),
         "novos_fits": 0, "nova_inferencia": False, "reservas_usadas": False,
         "autoriza_execucao": False, "autoriza_promocao": False,
         "natureza": "auditoria posterior de desenvolvimento, não seleção de parâmetros nem nova avaliação"}
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "auditoria.json").open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    r = executar(parser.parse_args().destino)
    print(json.dumps({"condicoes": list(r["pareamento"]), "novos_fits": r["novos_fits"]}))
