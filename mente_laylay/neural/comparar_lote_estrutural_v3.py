"""Comparação pareada do head de ação em desenvolvimento, nunca liberação."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
import warnings

import sklearn
from sklearn.feature_extraction import DictVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from threadpoolctl import threadpool_limits

from .candidato_relacional import PARAMETROS
from .diagnosticar_head_relacional import montar_linhas, medir_acoes
from .treinar_relacional_isolado import BASE, VARIANTES, exportar_supervisao, particoes_por_grupo

FONTES_V3 = {
    "memoria/neural/experimentos/lote_relacional_estrutural_v3_20260907/lote_fonte.json":
        "ce61ca42177f98d7e243d925be56d90735a5546bb5104b8a621d91d7b9e3333e",
    "memoria/neural/experimentos/lote_relacional_estrutural_v3_alinhado_20260907/alinhamento.json":
        "845667adc7131ebb8dd2ab50c01fc605d04178167c5fa9cd037cd27842f28ba3",
}
PARAMETROS_COMPARACAO = {**PARAMETROS, "max_iter": 1200}


def carregar_lote(base: Path = BASE) -> tuple[list[dict], list[dict]]:
    conteudos = []
    for nome, sha in FONTES_V3.items():
        bruto = (base / nome).read_bytes()
        if hashlib.sha256(bruto).hexdigest() != sha:
            raise ValueError("fonte divergiu do perfil autorizado")
        d = json.loads(bruto)
        if any(d.get(k) is not False for k in ("treino_permitido", "autoriza_execucao", "autoriza_promocao")):
            raise ValueError("fonte sem isolamento")
        conteudos.append(d["casos"])
    exemplos = exportar_supervisao(*conteudos)
    if len(exemplos) != 144:
        raise ValueError("perfil exige os 144 casos completos")
    por_id = {c["id"]: c for c in conteudos[1]}
    for e in exemplos:
        # Preserva a interface comum de supervisão; o perfil v3 e suas fontes
        # são autorizados explicitamente neste runner, não por mutar sidecars.
        e["grupo_construcao"] = por_id[e["id"]]["grupo_validacao"]
    return exemplos, conteudos[1]


def preparar_dobras(exemplos: list[dict]) -> list[tuple[list[int], list[int]]]:
    dobras = particoes_por_grupo(exemplos, "grupo_construcao")
    if len(dobras) != 12:
        raise ValueError("grupos divergiram; revisar protocolo, não redistribuir por score")
    for tr, te in dobras:
        if len(tr) != 132 or len(te) != 12:
            raise ValueError("dobra incompleta")
        acoes = [a for i in tr for s in exemplos[i]["segmentos_anotados"] for a in s["acoes"]]
        if {(a["intent"], a["action"]) for a in acoes} != VARIANTES:
            raise ValueError("variante ausente no treino")
        if {a["ato"] for a in acoes} != {"pedido", "recusa", "relato"}:
            raise ValueError("ato ausente no treino")
        if not any(s["indice"] == 1 and s["acoes"] for i in tr for s in exemplos[i]["segmentos_anotados"]):
            raise ValueError("treino sem ação no segundo segmento")
    return dobras


def resumir(medicoes: list[dict]) -> dict:
    campos = ("casos", "casos_exatos_acao_sem_alvos", "acoes_esperadas", "acoes_ausentes",
              "acoes_extras", "pedidos_inventados")
    r = {k: sum(m["teste"][k] for m in medicoes) for k in campos}
    r["taxa_exata_acao"] = r["casos_exatos_acao_sem_alvos"] / r["casos"] if r["casos"] else 0.0
    r["apto_para_avaliar_alvos"] = (r["casos"] == 144 and r["taxa_exata_acao"] >= 0.95
                                    and r["pedidos_inventados"] == 0 and r["acoes_extras"] == 0)
    r["autoriza_promocao"] = False
    return r


def executar(destino: Path) -> dict:
    exemplos, _ = carregar_lote()
    dobras = preparar_dobras(exemplos)
    destino.mkdir(parents=True, exist_ok=False)
    protocolo = {"perfil": "desenvolvimento_estrutural_v3", "fontes": FONTES_V3,
        "parametros": PARAMETROS_COMPARACAO, "condicoes": ["original", "cruzada"],
        "python": platform.python_version(), "sklearn": sklearn.__version__,
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE, text=True).strip(),
        "git_branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=BASE, text=True).strip(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=BASE, text=True).splitlines(),
        "codigo_sha256": {nome: hashlib.sha256((Path(__file__).parent / nome).read_bytes()).hexdigest()
                          for nome in ("comparar_lote_estrutural_v3.py", "diagnosticar_head_relacional.py",
                                       "treinar_relacional_isolado.py", "candidato_relacional.py")},
        "dobras": [{"treino": [exemplos[i]["id"] for i in tr], "teste": [exemplos[i]["id"] for i in te]}
                   for tr, te in dobras],
        "gate_apenas_para_proxima_avaliacao": {"minimo_exato_acao": 0.95,
                                               "max_pedidos_inventados": 0, "max_acoes_extras": 0},
        "reserva_usada": False, "autoriza_promocao": False, "autoriza_execucao": False,
        "limites": "um seed; dados sintéticos conhecidos; não compara com runtime ou legado Python"}
    with (destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    inicio, resultados = time.perf_counter(), []
    with threadpool_limits(limits=1):
        for modo in protocolo["condicoes"]:
            for numero, (tr, te) in enumerate(dobras):
                x, y, c = montar_linhas([exemplos[i] for i in tr], sorted(VARIANTES), modo)
                xt, yt, ct = montar_linhas([exemplos[i] for i in te], sorted(VARIANTES), modo)
                modelo = make_pipeline(DictVectorizer(), MLPClassifier(**PARAMETROS_COMPARACAO))
                with warnings.catch_warnings(record=True) as avisos:
                    warnings.simplefilter("always")
                    modelo.fit(x, y)
                resultados.append({"modo": modo, "dobra": numero,
                    "grupo_teste": exemplos[te[0]]["grupo_construcao"],
                    "treino": medir_acoes(c, y, modelo.predict(x).tolist()),
                    "teste": medir_acoes(ct, yt, modelo.predict(xt).tolist()),
                    "iteracoes": modelo[-1].n_iter_, "loss": modelo[-1].loss_,
                    "avisos": [{"tipo": a.category.__name__, "mensagem": str(a.message)} for a in avisos]})
    resumo = {modo: resumir([m for m in resultados if m["modo"] == modo]) for modo in protocolo["condicoes"]}
    r = {"medicoes": resultados, "resumo": resumo, "segundos": time.perf_counter() - inicio,
         "reserva_usada": False, "modelo_completo_avaliado": False,
         "autoriza_promocao": False, "autoriza_execucao": False}
    with (destino / "resultado.json").open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    r = executar(parser.parse_args().destino)
    print(json.dumps(r["resumo"], ensure_ascii=False))
