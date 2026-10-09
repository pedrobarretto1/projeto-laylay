"""Contraste offline de oito demonstrações fixas; sem treino ou autoridade."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter
from typing import Callable

import requests

from scripts.analises import sonda_predicado_host_v1 as anterior


BASE, etapas, schema, papel = anterior.BASE, anterior.etapas, anterior.schema, anterior.papel
DADOS = Path(__file__).parent / "dados" / "sonda_ensino_contrastivo_v1.json"
HASH_DADOS = "becead72f0fde7b20cc46e50741aeaa6b65c4da8c320b562e3db08e5670d01d5"
HASH_ANTERIOR = "cabbfe97fa3c2f2e1711dda5cdce3f0c2343ba08475c953bde6e2f20257aa01c"
MODOS = ("sem_exemplos", "com_exemplos")
REPETICOES = (1, 2)
METRICAS = ("shape", "papel_alinhado", "vinculo", "pista", "conjunto", "falso_indeterminado")


def caso_host(item: dict) -> dict:
    """Remove referências de avaliação antes de qualquer preparação de entrada."""
    return {k: item[k] for k in ("id", "foco_id", "texto")}


def carregar_painel() -> dict:
    for arquivo, esperado in ((DADOS, HASH_DADOS), (Path(anterior.__file__), HASH_ANTERIOR)):
        if hashlib.sha256(arquivo.read_bytes()).hexdigest() != esperado:
            raise ValueError("dependencia congelada alterada")
    antigos, _, _ = anterior.carregar_painel()
    d = json.loads(DADOS.read_bytes())
    demos, avaliacao = d["demonstracoes"], d["avaliacao"]
    if d["versao"] != 1 or len(demos) != 8 or len(avaliacao) != 24:
        raise ValueError("cobertura divergente")
    ids = [c["id"] for c in demos + avaliacao]
    if len(set(ids)) != 32:
        raise ValueError("identidade duplicada")
    focos = {}
    for c in demos + avaliacao:
        e = papel.preparar_entrada(caso_host(c))
        if not e["aspas_sintaticas"]["aspas_coerentes"] or c["papel"] not in papel.PAPEIS:
            raise ValueError("fonte ou papel invalido")
        focos[c["id"]] = e["foco"]["texto"].casefold()
        pista = c.get("predicado", c.get("pista"))
        v = anterior.materializar_vinculo(caso_host(c), e, {"predicado": pista, "papel": c["papel"]})
        if not v["vinculo_estrutural_valido"]:
            raise ValueError("referencia literal invalida: " + c["id"])
    proibidos = {papel.preparar_entrada(c)["foco"]["texto"].casefold() for c in antigos}
    demos_focos = {focos[c["id"]] for c in demos}
    if (any(focos[c["id"]] in proibidos for c in demos + avaliacao)
            or any(focos[c["id"]] in demos_focos for c in avaliacao)):
        raise ValueError("foco reutilizado entre particoes")
    for itens, n in ((demos, 2), (avaliacao, 6)):
        if Counter(c["papel"] for c in itens) != dict.fromkeys(papel.PAPEIS, n):
            raise ValueError("classes desbalanceadas")
    ix = {c["id"]: c for c in avaliacao}
    for i in range(1, 7):
        a, b = (f"E{i:02}{lado}" for lado in ("A", "B"))
        if (focos[a] != focos[b] or ix[a]["papel"] != "nome_designacao"
                or ix[b]["papel"] != "operacao_mencionada"):
            raise ValueError("par contextual divergente")
    return d


def preparar_requisicao(caso: dict, modo: str) -> dict:
    if modo not in MODOS:
        raise ValueError("modo invalido")
    r = anterior.preparar_requisicao(caso_host(caso), "predicado_host")
    if modo == "com_exemplos":
        mensagens = []
        for c in carregar_painel()["demonstracoes"]:
            mensagens.append(anterior.preparar_requisicao(caso_host(c), "predicado_host")["messages"][1])
            mensagens.append({"role": "assistant", "content": json.dumps(
                {"predicado": c["predicado"], "papel": c["papel"]}, ensure_ascii=False)})
        r["messages"][1:1] = mensagens
    return r


def sequencia(casos: list[dict]) -> list[tuple[dict, str, int]]:
    indices = list(enumerate(casos))
    return [(c, m, rep) for rep in REPETICOES
            for i, c in (indices if rep == 1 else list(reversed(indices)))
            for m in (MODOS if (i + rep) % 2 else tuple(reversed(MODOS)))]


def medir_caso(caso: dict, *, modo: str, repeticao: int, post: Callable = requests.post) -> dict:
    r = {**BASE, "id": caso["id"], "modo": modo, "repeticao": repeticao,
         "requisicao": preparar_requisicao(caso, modo), "entrada_host": papel.preparar_entrada(caso_host(caso))}
    inicio = perf_counter()
    try:
        r.update(schema.capturar_http(deepcopy(r["requisicao"]), post))
    except Exception as erro:
        r["erro_consulta"] = type(erro).__name__
    r["duracao_consulta_s"] = perf_counter() - inicio
    return r


def aferir_caso(caso: dict, r: dict) -> dict:
    if (r.get("id") != caso["id"] or r.get("modo") not in MODOS
            or type(r.get("repeticao")) is not int or r["repeticao"] not in REPETICOES):
        raise ValueError("identidade invalida")
    e = papel.preparar_entrada(caso_host(caso))
    if (not etapas.iguais_tipados(e, r.get("entrada_host"))
            or not etapas.iguais_tipados(preparar_requisicao(caso, r["modo"]), r.get("requisicao"))
            or any(r.get(k) is not False for k in BASE)):
        raise ValueError("host, requisicao ou flags adulterados")
    etapas.conferir_registro_consulta({"proposta": None, "duracao_consulta_s": r.get("duracao_consulta_s")})
    if "erro_consulta" in r:
        if not isinstance(r["erro_consulta"], str) or "http_status" in r or "http_bruto" in r:
            raise ValueError("consulta contraditoria")
        dec = {"estado_transporte": "erro_consulta", "finalizacao": "nao_confirmada"}
    else:
        dec = schema.decodificar_http(r.get("http_status"), r.get("http_bruto"))
    p = dec.get("proposta")
    rotulo = papel.conferir_papel(caso_host(caso), e, {"papel": p.get("papel")} if isinstance(p, dict) else None)
    v = anterior.materializar_vinculo(caso_host(caso), e, p)
    fim = dec["finalizacao"] == "concluida"
    valido = rotulo["estado"] == "papel_proposto_revisao_pendente"
    shape = bool(fim and valido and isinstance(p, dict) and set(p) == {"predicado", "papel"}
                 and all(isinstance(x, str) for x in p.values()))
    alinhado = bool(fim and valido and rotulo["papel_proposto"] == caso["papel"])
    vinculo = bool(fim and v["vinculo_estrutural_valido"])
    pista = bool(vinculo and caso["pista"].casefold() in v["intervalo_ligacao"]["predicado"]["texto"].casefold())
    return {**BASE, "interpretacao": dec, "conferencia": v, "papel_proposto": rotulo["papel_proposto"],
            "shape": shape, "papel_alinhado": alinhado, "vinculo": vinculo, "pista": pista,
            "conjunto": alinhado and pista,
            "falso_indeterminado": bool(fim and valido and rotulo["papel_proposto"] == "indeterminado"
                                       and caso["papel"] != "indeterminado")}


def resumir(resultados: list[dict]) -> dict:
    invalido = {**BASE, "tipo": "resumo_invalido"}
    casos = carregar_painel()["avaliacao"]
    esperados = [(c["id"], m, rep) for c, m, rep in sequencia(casos)]
    if (not isinstance(resultados, list) or any(not isinstance(r, dict) for r in resultados)
            or [(r.get("id"), r.get("modo"), r.get("repeticao")) for r in resultados] != esperados):
        return invalido
    ix = {c["id"]: c for c in casos}
    try:
        aferidos = {(r["id"], r["modo"], r["repeticao"]): aferir_caso(ix[r["id"]], r) for r in resultados}
    except (KeyError, ValueError, TypeError, OverflowError):
        return invalido
    resumo = {**BASE, "tipo": "resumo_ensino_contrastivo", "runtime_laylay": False,
              "revisao_humana_independente": False, "bracos": {}, "comparacoes": {}}
    for modo in MODOS:
        reps = {}
        for rep in REPETICOES:
            dados = [aferidos[c["id"], modo, rep] for c in casos]
            reps[str(rep)] = {"casos": len(dados), **{k: sum(a[k] for a in dados) for k in METRICAS},
                "por_papel": {p: sum(aferidos[c["id"], modo, rep]["papel_alinhado"]
                                     for c in casos if c["papel"] == p) for p in papel.PAPEIS},
                "pares_papel": sum(all(aferidos[f"E{i:02}{lado}", modo, rep]["papel_alinhado"]
                                       for lado in ("A", "B")) for i in range(1, 7)),
                "finalizacoes": dict(Counter(a["interpretacao"]["finalizacao"] for a in dados))}
        resumo["bracos"][modo] = {"repeticoes": reps,
            "papeis_validos_iguais_nas_duas": sum(all(aferidos[c["id"], modo, r]["shape"] for r in REPETICOES)
                and aferidos[c["id"], modo, 1]["papel_proposto"] == aferidos[c["id"], modo, 2]["papel_proposto"] for c in casos),
            "conjunto_nas_duas": sum(all(aferidos[c["id"], modo, r]["conjunto"] for r in REPETICOES) for c in casos)}
    for rep in REPETICOES:
        grupos = {}
        for metrica in ("papel_alinhado", "conjunto"):
            grupos[metrica] = {"ganhos": [], "perdas": []}
            for c in casos:
                a, b = [aferidos[c["id"], m, rep][metrica] for m in MODOS]
                if a != b:
                    grupos[metrica]["ganhos" if b else "perdas"].append(c["id"])
        resumo["comparacoes"][str(rep)] = grupos
    # Critério descritivo de continuar a investigação, nunca aprovação operacional.
    resumo["criterio_predefinido_atendido"] = all(
        b["shape"] == 24 and b["conjunto"] > a["conjunto"] and b["papel_alinhado"] >= a["papel_alinhado"]
        and b["por_papel"]["indeterminado"] > a["por_papel"]["indeterminado"]
        and all(b["por_papel"][p] >= a["por_papel"][p] for p in papel.PAPEIS)
        and b["falso_indeterminado"] <= a["falso_indeterminado"]
        for rep in REPETICOES
        for a, b in [[resumo["bracos"][m]["repeticoes"][str(rep)] for m in MODOS]])
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    dados = carregar_painel()
    digest = etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        def escrever(r: dict) -> None:
            arquivo.write(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n")
            arquivo.flush()
        escrever({**BASE, "tipo": "metadata", "dados_pre_consulta": dados,
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "hash_dados": HASH_DADOS, "hash_anterior": HASH_ANTERIOR, "digest_inicio": digest,
            "runtime_laylay": False, "treino_pesos": False, "avaliacao_fornecida_com_respostas": False,
            "ordem": [(c["id"], m, rep) for c, m, rep in sequencia(dados["avaliacao"])]})
        rs = []
        for c, modo, rep in sequencia(dados["avaliacao"]):
            r = medir_caso(c, modo=modo, repeticao=rep)
            a = aferir_caso(c, r)
            rs.append(r)
            escrever({**r, "tipo": "consulta", "afericao": a})
            print(json.dumps({"id": c["id"], "modo": modo, "rep": rep,
                              "papel": a["papel_proposto"], "conjunto": a["conjunto"]}), flush=True)
        resumo = resumir(rs)
        try:
            resumo["digest_final"] = etapas.coordenadas.digest_modelo()
            resumo["modelo_igual_entre_leituras"] = resumo["digest_final"] == digest
        except Exception as erro:
            resumo["erro_digest_final"] = type(erro).__name__
            resumo["modelo_igual_entre_leituras"] = False
        escrever(resumo)
        print(json.dumps(resumo, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
