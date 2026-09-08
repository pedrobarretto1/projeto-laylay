"""Controles fatoriais de desenvolvimento: primeira fronteira, não promoção.

Congela quatro condições antes dos fits. Não altera o candidato anterior nem
consulta reservas. Resultados são do head de ação, sem preencher alvos gold.
"""
from __future__ import annotations

import argparse
from collections import Counter
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

from .candidato_relacional import PARAMETROS, atributos_acao, validar_entrada
from .treinar_relacional_isolado import (
    BASE, FONTES, carregar_desenvolvimento, particoes_por_grupo,
)

CONDICOES = (
    ("original_180", "original", 180),
    ("original_1200", "original", 1200),
    ("cruzada_180", "cruzada", 180),
    ("cruzada_1200", "cruzada", 1200),
)


def representar(entrada: dict, posicao: int, variante: tuple[str, str], modo: str) -> dict:
    validar_entrada(entrada)
    if modo not in {"original", "cruzada"}:
        raise ValueError("representação fora do protocolo")
    base = atributos_acao(entrada, posicao, variante)
    if modo == "original":
        return base
    # Mesma informação, com interação explícita e genérica. Não escolhe qual
    # variante é correta; aplica-se a TODAS as candidatas, inclusive negativas.
    cruzada = {"cruzamento:" + "/".join(variante) + ":" + k: v
               for k, v in base.items() if k.startswith(("entrada:", "dono:"))}
    return {**base, **cruzada}


def montar_linhas(exemplos: list[dict], variantes: list[tuple[str, str]], modo: str) -> tuple:
    if not variantes or len(set(variantes)) != len(variantes):
        raise ValueError("variantes vazias ou duplicadas")
    atributos, rotulos, chaves = [], [], []
    for e in exemplos:
        if (e.get("perfil_treino") != "desenvolvimento_relacional_v1"
                or e.get("papel_dataset") != "desenvolvimento"):
            raise ValueError("diagnóstico restrito à exportação de desenvolvimento")
        acoes = {(s["indice"], a["intent"], a["action"]): a
                 for s in e["segmentos_anotados"] for a in s["acoes"]}
        if any(chave[1:] not in variantes for chave in acoes):
            raise ValueError("ação esperada fora das variantes; não excluir do denominador")
        for pos, s in enumerate(e["entrada"]["segmentos"]):
            for variante in variantes:
                atributos.append(representar(e["entrada"], pos, variante, modo))
                a = acoes.get((s["indice"], *variante))
                rotulos.append(a["ato"] + "/" + a["resolucao_alvo"] if a else "ausente")
                # Identificadores só para medição. Nunca entram no vectorizer.
                chaves.append((e["id"], s["indice"], *variante))
    return atributos, rotulos, chaves


def medir_acoes(chaves: list, esperado: list[str], previsto: list[str]) -> dict:
    if not chaves or not len(chaves) == len(esperado) == len(previsto) or len(set(chaves)) != len(chaves):
        raise ValueError("medição incompleta ou duplicada")
    ids = {c[0] for c in chaves}
    erros = {c[0] for c, e, p in zip(chaves, esperado, previsto) if e != p}
    confusao = Counter(zip(esperado, previsto))
    return {
        "casos": len(ids), "casos_exatos_acao_sem_alvos": len(ids - erros),
        "linhas": len(chaves), "rotulos_corretos": sum(e == p for e, p in zip(esperado, previsto)),
        "acoes_esperadas": sum(e != "ausente" for e in esperado),
        "acoes_ausentes": sum(e != "ausente" and p == "ausente" for e, p in zip(esperado, previsto)),
        "acoes_extras": sum(e == "ausente" and p != "ausente" for e, p in zip(esperado, previsto)),
        "pedidos_inventados": sum(p.startswith("pedido/") and not e.startswith("pedido/")
                                   for e, p in zip(esperado, previsto)),
        "distribuicao_esperada": dict(Counter(esperado)),
        "distribuicao_prevista": dict(Counter(previsto)),
        "confusao": [{"esperado": e, "previsto": p, "total": n}
                     for (e, p), n in sorted(confusao.items())],
        "erros": [{"chave": list(c), "esperado": e, "previsto": p}
                  for c, e, p in zip(chaves, esperado, previsto) if e != p],
    }


def auditar_vocabulario(vectorizer: DictVectorizer, atributos: list[dict]) -> dict:
    """Diagnóstico posterior; não adiciona vocabulário da avaliação ao modelo."""
    vistos, ausentes = set(), set()
    for linha in atributos:
        for k, v in linha.items():
            nome = k + vectorizer.separator + v if isinstance(v, str) else k
            vistos.add(nome)
            if nome not in vectorizer.vocabulary_:
                ausentes.add(nome)
    return {"features_distintas_teste": len(vistos), "features_fora_vocabulario": len(ausentes)}


def executar(saida: Path) -> dict:
    exemplos, _ = carregar_desenvolvimento()
    partes = {eixo: particoes_por_grupo(exemplos, eixo)
              for eixo in ("grupo_construcao", "grupo_entidades")}
    anterior = BASE / "memoria/neural/experimentos/candidato_relacional_mlp_v1_20260907"
    protocolo_anterior = json.loads((anterior / "protocolo.json").read_text(encoding="utf-8"))
    for nome, sha in protocolo_anterior["codigo_sha256"].items():
        if hashlib.sha256((Path(__file__).parent / nome).read_bytes()).hexdigest() != sha:
            raise ValueError("código baseline divergiu; diagnosticar a base antes de repetir")
    saida.mkdir(parents=True, exist_ok=False)
    protocolo = {
        "hipoteses": {
            "ajuste": "180 iterações insuficientes: comparar 1200 mantendo a representação",
            "representacao": "interação variante/texto difícil: cruzar features mantendo iterações",
            "cobertura": "vocabulário e construções pouco variados: auditar OOV e classes por dobra",
        },
        "limites": "um seed; diagnóstico em desenvolvimento, não estimativa independente ou liberação",
        "condicoes": CONDICOES, "parametros_comuns": PARAMETROS,
        "fontes": FONTES, "python": platform.python_version(), "sklearn": sklearn.__version__,
        "codigo_sha256": {n: hashlib.sha256((Path(__file__).parent / n).read_bytes()).hexdigest()
                          for n in ("diagnosticar_head_relacional.py", "candidato_relacional.py",
                                    "treinar_relacional_isolado.py")},
        "baseline_resultado_sha256": hashlib.sha256((anterior / "resultado.json").read_bytes()).hexdigest(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE, text=True).strip(),
        "git_branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=BASE, text=True).strip(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=BASE, text=True).splitlines(),
        "dobras": {eixo: [{"treino": [exemplos[i]["id"] for i in tr],
                           "teste": [exemplos[i]["id"] for i in te]} for tr, te in dobras]
                   for eixo, dobras in partes.items()},
        "reservas_usadas": False, "autoriza_execucao": False, "autoriza_promocao": False,
    }
    with (saida / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    inicio = time.perf_counter()
    resultados = []
    with threadpool_limits(limits=1):
        for nome, modo, iteracoes in CONDICOES:
            for eixo, dobras in partes.items():
                for dobra, (tr, te) in enumerate(dobras):
                    treino, teste = [exemplos[i] for i in tr], [exemplos[i] for i in te]
                    variantes = sorted({(a["intent"], a["action"]) for e in treino
                                        for s in e["segmentos_anotados"] for a in s["acoes"]})
                    x, y, chaves = montar_linhas(treino, variantes, modo)
                    xt, yt, ct = montar_linhas(teste, variantes, modo)
                    params = {**PARAMETROS, "max_iter": iteracoes}
                    modelo = make_pipeline(DictVectorizer(), MLPClassifier(**params))
                    with warnings.catch_warnings(record=True) as avisos:
                        warnings.simplefilter("always")
                        modelo.fit(x, y)
                    resultados.append({
                        "condicao": nome, "eixo": eixo, "dobra": dobra,
                        "treino": medir_acoes(chaves, y, modelo.predict(x).tolist()),
                        "teste": medir_acoes(ct, yt, modelo.predict(xt).tolist()),
                        "vocabulario": auditar_vocabulario(modelo[0], xt),
                        "iteracoes_reais": modelo[-1].n_iter_, "loss": modelo[-1].loss_,
                        "avisos": [{"tipo": a.category.__name__, "mensagem": str(a.message)} for a in avisos],
                    })
    resultado = {"medicoes": resultados, "segundos": time.perf_counter() - inicio,
                 "reserva_avaliada": False, "modelo_completo_avaliado": False,
                 "autoriza_execucao": False, "autoriza_promocao": False}
    with (saida / "resultado.json").open("x", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    r = executar(parser.parse_args().saida)
    print(json.dumps({"segundos": r["segundos"], "medicoes": [
        {"condicao": m["condicao"], "eixo": m["eixo"], "dobra": m["dobra"],
         "treino_exato": m["treino"]["casos_exatos_acao_sem_alvos"],
         "teste_exato": m["teste"]["casos_exatos_acao_sem_alvos"],
         "ausentes": m["teste"]["acoes_ausentes"], "extras": m["teste"]["acoes_extras"],
         "iteracoes": m["iteracoes_reais"]} for m in r["medicoes"]]}, ensure_ascii=False))
