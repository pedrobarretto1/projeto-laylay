"""Schema de trechos externos versus cópia livre; literalidade não é apoio."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter

import requests

from scripts.analises import sonda_hierarquia_transferencia_v1 as painel
from scripts.analises import sonda_contextos_enumerados_v1 as externos
from scripts.analises.sonda_produtor_condicoes_v2 import _ancorar_trecho

anterior = painel.anterior.anterior
BASE = anterior.BASE
MODOS = ("livre", "catalogado")
IDS = ("T01", "T02", "T03", "T08", "T09", "T12", "T14", "T15")
PREFIXO = "Há uma caixa vermelha na mesa. "
SUFIXO = " O catálogo possui nove páginas."
HASH_PAINEL = "3c4f4631ac6113a23a9749c9d65f163d260c2f6b909b8647a834ac82ba663636"


def carregar_painel() -> list[dict]:
    if hashlib.sha256(Path(painel.__file__).read_bytes()).hexdigest() != HASH_PAINEL:
        raise ValueError("painel congelado alterado")
    ix = {c["id"]: c for c in painel.carregar_painel()}
    return [{**ix[i], "texto": PREFIXO + ix[i]["texto"] + SUFIXO} for i in IDS]


def catalogar(caso: dict) -> list[dict]:
    """Todos os spans de tokens externos, únicos; nenhuma seleção por gold/verbo."""
    host = externos.etapas.vinculo.preparar_entrada(anterior.caso_host(caso))
    if len(host["tokens"]) > 64:
        raise ValueError("fonte excede limite offline de tokens")
    tokens, texto = host["tokens"], host["fonte"]["texto"]
    itens = []
    for bloco in externos.enumerar_externos(caso, host):
        for i in range(bloco["inicio_token"], bloco["fim_token"]):
            for j in range(i + 1, bloco["fim_token"] + 1):
                inicio, fim = tokens[i]["inicio"], tokens[j-1]["fim"]
                trecho = texto[inicio:fim]
                if _ancorar_trecho(texto, trecho) is not None:
                    itens.append({"inicio": inicio, "fim": fim, "texto": trecho})
    return itens


def preparar_requisicao(caso: dict, modo: str) -> dict:
    if modo not in MODOS:
        raise ValueError("modo invalido")
    r = anterior.preparar_requisicao(caso, "com_exemplos")
    if modo == "catalogado":
        r["format"]["properties"]["predicado"]["enum"] = [""] + [i["texto"] for i in catalogar(caso)]
    return r


def medir_caso(caso: dict, modo: str, repeticao: int, post=requests.post) -> dict:
    r = {**BASE, "id": caso["id"], "modo": modo, "repeticao": repeticao,
         "entrada_host": anterior.papel.preparar_entrada(anterior.caso_host(caso)),
         "catalogo_host": catalogar(caso), "requisicao": preparar_requisicao(caso, modo)}
    inicio = perf_counter()
    try:
        r.update(anterior.schema.capturar_http(deepcopy(r["requisicao"]), post))
    except Exception as erro:
        r["erro_consulta"] = type(erro).__name__
    r["duracao_consulta_s"] = perf_counter() - inicio
    return r


def aferir_caso(caso: dict, r: dict) -> dict:
    eq = anterior.etapas.iguais_tipados
    if not isinstance(r, dict) or r.get("modo") not in MODOS:
        raise ValueError("registro invalido")
    itens = catalogar(caso)
    if not eq(r.get("requisicao"), preparar_requisicao(caso, r["modo"])) or not eq(
            {"itens": r.get("catalogo_host")}, {"itens": itens}):
        raise ValueError("requisicao ou catalogo adulterado")
    ponte = {**r, "modo": "com_exemplos", "requisicao": anterior.preparar_requisicao(caso, "com_exemplos")}
    a = anterior.aferir_caso(caso, ponte)
    p = a["interpretacao"].get("proposta")
    predicado = p.get("predicado") if isinstance(p, dict) else None
    aceito = isinstance(predicado, str) and predicado in [""] + [i["texto"] for i in itens]
    a["respeita_catalogo"] = aceito
    if r["modo"] == "catalogado" and not aceito:
        # Violação de enum não pode ser aceita se o backend ignorar o schema.
        for k in ("vinculo", "pista", "conjunto"):
            a[k] = False
    v = a["conferencia"].get("intervalo_ligacao")
    span = v["predicado"] if a["vinculo"] and v else None
    # Sentenças irrelevantes conhecidas só pela avaliação; não orientam catálogo.
    fora = bool(span and (span["inicio"] < len(PREFIXO) or span["fim"] > len(caso["texto"]) - len(SUFIXO)))
    a["inclui_distrator"] = fora
    a["selecao_discriminativa_local"] = a["pista"] and not fora
    a["conjunto_discriminativo_local"] = a["conjunto"] and not fora
    return a


def controle_todos(caso: dict) -> dict:
    host = externos.etapas.vinculo.preparar_entrada(caso)
    blocos = externos.enumerar_externos(caso, host)
    pista = any(caso["pista"].casefold() in b["texto"].casefold() for b in blocos)
    distrator = any(b["inicio"] < len(PREFIXO) or b["fim"] > len(caso["texto"]) - len(SUFIXO) for b in blocos)
    return {**BASE, "pista": pista, "inclui_distrator": distrator,
            "selecao_discriminativa_local": pista and not distrator}


def sequencia(casos: list[dict]) -> list[tuple[dict, str, int]]:
    ordem = [(c, m) for i, c in enumerate(casos) for m in (MODOS if i % 2 == 0 else MODOS[::-1])]
    return [(c, m, rep) for rep in (1, 2) for c, m in (ordem if rep == 1 else ordem[::-1])]


def resumir(rs: list[dict]) -> dict:
    cs = carregar_painel()
    invalido = {**BASE, "tipo": "resumo_invalido"}
    if not isinstance(rs, list) or any(not isinstance(r, dict) for r in rs):
        return invalido
    if [(r.get("id"), r.get("modo"), r.get("repeticao")) for r in rs] != [(c["id"], m, rep) for c, m, rep in sequencia(cs)]:
        return invalido
    ix = {c["id"]: c for c in cs}
    try:
        a = {(r["id"], r["modo"], r["repeticao"]): aferir_caso(ix[r["id"]], r) for r in rs}
    except (ValueError, TypeError, KeyError, OverflowError):
        return invalido
    metricas = (*anterior.METRICAS, "respeita_catalogo", "inclui_distrator", "selecao_discriminativa_local", "conjunto_discriminativo_local")
    return {**BASE, "tipo": "resumo_predicado_catalogado", "consultas": len(rs),
            "bracos": {m: {str(rep): {k: sum(a[c["id"], m, rep][k] for c in cs) for k in metricas} for rep in (1, 2)} for m in MODOS},
            "controle_todos": {c["id"]: controle_todos(c) for c in cs},
            "runtime_laylay": False, "holdout_novo": False, "revisao_humana_independente": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    cs = carregar_painel()
    digest = anterior.etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arq:
        def escrever(r: dict) -> None:
            arq.write(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n")
            arq.flush()
        escrever({**BASE, "tipo": "metadata", "casos_pre_consulta": cs,
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "hash_painel": HASH_PAINEL, "digest_inicio": digest,
            "hashes_servicos": {m.__name__: hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()
                                for m in (externos, externos.etapas, externos.etapas.vinculo, anterior)},
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
            "ordem": [(c["id"], m, rep) for c, m, rep in sequencia(cs)], "runtime_laylay": False})
        rs = []
        for c, m, rep in sequencia(cs):
            r = medir_caso(c, m, rep)
            a = aferir_caso(c, r)
            rs.append(r)
            escrever({**r, "tipo": "consulta", "afericao": a})
            print(json.dumps({"id": c["id"], "modo": m, "rep": rep, "papel": a["papel_proposto"], "discriminativo": a["conjunto_discriminativo_local"]}), flush=True)
        resumo = resumir(rs)
        try:
            resumo["digest_final"] = anterior.etapas.coordenadas.digest_modelo()
            resumo["modelo_igual_entre_leituras"] = resumo["digest_final"] == digest
        except Exception as erro:
            resumo.update(erro_digest_final=type(erro).__name__, modelo_igual_entre_leituras=False)
        escrever(resumo)
        print(json.dumps(resumo["bracos"]), flush=True)


if __name__ == "__main__":
    main()
