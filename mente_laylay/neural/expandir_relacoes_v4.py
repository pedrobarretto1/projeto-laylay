"""Expansão aditiva de desenvolvimento, com auditoria antes de qualquer fit."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
from itertools import combinations
import json
from pathlib import Path
import subprocess

from .preparar_lote_relacional_v3 import VARIANTES, preencher
from .preparar_relacoes_v4 import agrupar_projecoes
from .qualidade import auditar_leakage_dataset
from .supervisao_relacoes_v4 import alinhar_relacoes, validar_fonte_relacional

BASE = Path(__file__).resolve().parents[2]
FONTE = BASE / "memoria/neural/experimentos/supervisao_relacoes_v4_20260908"
SHA_FONTE = "f0b93360db17042b7c5af3794e44448a39611dfee62c96f135815d6bc074d09b"
FORMAS = {
    "sequencia_solicitada": {
        "pedido": "comece por {dono}{infinitivo} {a}, conforme estou solicitando agora",
        "recusa": "essa operação está vetada: {dono}{infinitivo} {a} não deve acontecer",
        "relato": "foi durante a conversa de ontem que ela disse ter conseguido {dono}{infinitivo} {a}"},
    "instrucao_destacada": {
        "pedido": "faça o seguinte agora: {dono}{infinitivo} {a}",
        "recusa": "minha instrução é deixar de lado a possibilidade de {dono}{infinitivo} {a}",
        "relato": "lembrei de quando eu costumava {dono}{infinitivo} {a}"},
    "alvo_topicalizado": {
        "pedido": "{a}: estou solicitando que você {dono}{verbo} esse item",
        "recusa": "{a}: estou proibindo você de {dono}{infinitivo} esse item",
        "relato": "{a}: ontem ela contou que tentou {dono}{infinitivo} esse item"},
}
LEXICO = {("APP_OPEN", "open"): ("abra", "abrir", "o aplicativo"),
          ("MUSIC_SEARCH", "search"): ("toque", "tocar", "a faixa"),
          ("FILE_READ", "read"): ("leia", "ler", "o arquivo")}


def carregar_base() -> list[dict]:
    bruto = (FONTE / "lote.json").read_bytes()
    if hashlib.sha256(bruto).hexdigest() != SHA_FONTE:
        raise ValueError("lote anterior mudou; não atualizar baseline automaticamente")
    protocolo = json.loads((FONTE / "protocolo.json").read_text(encoding="utf-8"))
    for nome, sha in protocolo["codigo_sha256"].items():
        if hashlib.sha256((BASE / nome).read_bytes()).hexdigest() != sha:
            raise ValueError("dependência da supervisão anterior mudou")
    casos = json.loads(bruto)["casos"]
    if len(casos) != 672 or any(c["particao"] != "desenvolvimento" for c in casos):
        raise ValueError("perfil anterior incompleto")
    return casos


def expandir(base: list[dict]) -> list[dict]:
    """Troca moldes, preservando pares/atos explicitamente anotados, não previsões."""
    controles = [c for c in base if c["grupo_construcao"] == "direto"]
    novos = []
    for familia, formas in FORMAS.items():
        for controle in controles:
            c = deepcopy(controle)
            c["id"] = c["id"].replace("rel_v4_direto_", f"rel_v4_{familia}_", 1)
            c["grupo_construcao"] = familia
            c["grupo_contraste"] = c["grupo_contraste"].replace("direto_", familia + "_", 1)
            c.pop("grupo_validacao", None)
            c.pop("alinhado", None)
            texto = ""
            for no in c["fonte"]["nos"]:
                verbo, infinitivo, objeto = LEXICO[no["intent"], no["action"]]
                alvo = no["alvos"][0]["texto"]
                molde = formas[no["ato"]]
                valor = objeto + " " + (f'"{alvo}"' if "_q1_" in c["id"] else alvo)
                clausula, mencoes, ancora = preencher(molde,
                    {"a": valor, "verbo": verbo, "infinitivo": infinitivo}, {"a": alvo})
                if texto:
                    texto += "; "
                inicio = len(texto)
                texto += clausula
                v = verbo if "{verbo}" in molde else infinitivo
                no["trecho"] = {"inicio": inicio, "fim": len(texto), "texto": clausula}
                no["ancora"] = {"inicio": inicio + ancora, "fim": inicio + ancora + len(v), "texto": v}
                no["alvos"] = [{**mencoes["a"], "inicio": inicio + mencoes["a"]["inicio"],
                                "fim": inicio + mencoes["a"]["fim"]}]
            c["fonte"]["texto_entrada"] = texto
            validar_fonte_relacional(c["fonte"], variantes_permitidas=VARIANTES)
            c["alinhado"] = alinhar_relacoes(c["fonte"], variantes_permitidas=VARIANTES)
            novos.append(c)
    return novos


def auditar_grupos(casos: list[dict], grupos: dict[str, str]) -> tuple[dict, list[dict]]:
    """Audita só blocos diferentes: irmãos já agrupados nunca serão separados."""
    pais = {g: g for g in grupos.values()}
    blocos = defaultdict(list)
    for c in casos:
        blocos[grupos[c["id"]]].append(c)

    def raiz(g):
        while pais[g] != g:
            g = pais[g]
        return g

    evidencias = []
    for ga, gb in combinations(sorted(blocos), 2):
        a, b = blocos[ga], blocos[gb]
        itens = lambda xs: [{"text": c["fonte"]["texto_entrada"], "family": grupos[c["id"]]} for c in xs]
        r = auditar_leakage_dataset(itens(a), itens(b), limiar_similaridade=0.9)
        pares = r["duplicados_exatos"] + r["quase_duplicados"]
        for p in pares:
            evidencias.append({"id_a": a[p["linha_dev"] - 1]["id"],
                               "id_b": b[p["linha_frozen"] - 1]["id"], "similaridade": p["similaridade"]})
        if pares:
            x, y = sorted((raiz(ga), raiz(gb)))
            pais[y] = x
        print(json.dumps({"bloco_a": ga, "bloco_b": gb, "pares": len(pares)}), flush=True)
    return {i: raiz(g) for i, g in grupos.items()}, evidencias


def preparar_dobras(casos: list[dict], grupos: dict[str, str]) -> list[dict]:
    """Gate de cobertura, nunca aprovação de modelo ou autorização de treino."""
    if len({c["id"] for c in casos}) != len(casos) or set(grupos) != {c["id"] for c in casos}:
        raise ValueError("partição incompleta ou identificadores repetidos")
    if len(set(grupos.values())) < 3:
        raise ValueError("menos de três grupos de construção independentes")
    for campo in ("grupo_construcao", "grupo_contraste"):
        donos = defaultdict(set)
        for c in casos:
            donos[c[campo]].add(grupos[c["id"]])
        if any(len(v) != 1 for v in donos.values()):
            raise ValueError("irmãos separados entre grupos")
    projetados, _ = agrupar_projecoes(casos, grupos)
    if len(set(projetados.values())) != len(set(grupos.values())):
        raise ValueError("entrada local idêntica atravessa grupos")
    dobras = []
    for g in sorted(set(grupos.values())):
        tr = [c for c in casos if grupos[c["id"]] != g]
        te = [c for c in casos if grupos[c["id"]] == g]
        for fatia in (tr, te):
            combinacoes = {(n["intent"], n["action"], n["ato"])
                           for c in fatia for n in c["alinhado"]["supervisao"]["nos"]}
            if combinacoes != {(i, a, ato) for i, a in VARIANTES for ato in ("pedido", "recusa", "relato")}:
                raise ValueError("ato/variante sem cobertura na partição")
            ordens = {tuple(n["ato"] for n in c["fonte"]["nos"]) for c in fatia}
            if not {("pedido", "recusa"), ("recusa", "pedido"), ("pedido", "relato"), ("relato", "pedido")} <= ordens:
                raise ValueError("composição sem cobertura nas duas ordens")
        dobras.append({"grupo_teste": g, "treino": [c["id"] for c in tr], "teste": [c["id"] for c in te]})
    return dobras


def executar(destino: Path) -> dict:
    if destino.exists():
        raise FileExistsError("preservar execução anterior")
    base = carregar_base()
    novos = expandir(base)
    casos = base + novos
    grupos = {c["id"]: c.get("grupo_validacao", c["grupo_construcao"]) for c in casos}
    protocolo = {"perfil": "expansao_relacoes_v4", "fonte_sha256": SHA_FONTE, "moldes": FORMAS,
        "casos_base": len(base), "casos_novos": len(novos), "limiar": 0.9,
        "minimo_grupos": 3, "modelo_consultado": False, "reservas_usadas": False,
        "autoriza_execucao": False, "autoriza_promocao": False, "treino_permitido": False,
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE, text=True).strip(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=BASE, text=True).splitlines(),
        "codigo_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "revisao": "moldes assistidos por IA; não revisados por avaliador independente",
        "limites": "divisões de desenvolvimento; não são reservas independentes nem prova de generalização"}
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    grupos, pares = auditar_grupos(casos, grupos)
    grupos, repeticoes = agrupar_projecoes(casos, grupos)
    try:
        dobras, motivo = preparar_dobras(casos, grupos), ""
    except ValueError as exc:
        dobras, motivo = [], str(exc)
    lote = {"casos": [{**c, "grupo_validacao": grupos[c["id"]]} for c in casos],
            "treino_permitido": False, "autoriza_execucao": False, "autoriza_promocao": False}
    bruto = json.dumps(lote, ensure_ascii=False, indent=2).encode("utf-8")
    with (destino / "lote.json").open("xb") as f:
        f.write(bruto)
    resultado = {"casos": len(casos), "grupos": dict(Counter(grupos.values())), "pares": pares,
        "repeticoes_locais": repeticoes, "dobras": dobras, "divisao_viavel": bool(dobras),
        "motivo_bloqueio": motivo, "lote_sha256": hashlib.sha256(bruto).hexdigest(),
        "treino_permitido": False, "autoriza_execucao": False, "autoriza_promocao": False}
    with (destino / "resultado.json").open("x", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    r = executar(parser.parse_args().destino)
    print(json.dumps({k: r[k] for k in ("casos", "grupos", "divisao_viavel", "motivo_bloqueio")}, ensure_ascii=False))
