"""Ajuste de limiar em três partições por grupos; nunca promove modelos."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from sklearn.model_selection import GroupKFold

from mente_laylay.especialistas.capacidades import intents_registradas
from .avaliacao import head_aplicavel
from .dataset import carregar_jsonl
from .diagnostico_fold_negacao import selecionar_fold
from .experimento_escopo_negacao import ajustar_cabeca, criar_prototipo_negacao, grupos_sem_duplicatas, medir_negacao
from .modelo import carregar_modelo
from .treino import _hash_dados


def escolher_limiar(scores: list[float], rotulos: list[bool], fatias: list[str]) -> dict:
    """Recebe apenas calibração; exige Pareto por fatia e prefere zero no empate."""
    if not scores or len(scores) != len(rotulos) or len(scores) != len(fatias):
        raise ValueError("calibração vazia ou desalinhada")
    if any(type(y) is not bool for y in rotulos) or any(not isinstance(f, str) or not f for f in fatias):
        raise ValueError("rótulos booleanos e fatias explícitas são obrigatórios")
    s = np.asarray(scores, dtype=float)
    if s.ndim != 1 or not np.isfinite(s).all():
        raise ValueError("scores precisam ser finitos e unidimensionais")
    y, f = np.asarray(rotulos), np.asarray(fatias)
    nomes = sorted(set(fatias))

    def medir(t: float) -> dict:
        p = s > t
        return {nome: {"negacoes_perdidas": int(np.sum((f == nome) & y & ~p)),
                       "negacoes_falsas": int(np.sum((f == nome) & ~y & p))}
                for nome in nomes}

    original = medir(0.0)
    if set(nomes) != {"historica", "nova"} or any(set(y[f == nome].tolist()) != {False, True} for nome in nomes):
        return {"limiar": 0.0, "motivo": "suporte_insuficiente_por_fatia", "zero": original, "ajustado": original}
    valores = np.unique(s)
    # Metades somadas evitam overflow de (a+b). Não usamos scores do teste.
    candidatos = {0.0, float(valores[-1]), float(np.nextafter(valores[0], -np.inf))}
    candidatos.update(float(a / 2 + b / 2) for a, b in zip(valores[:-1], valores[1:]))
    elegiveis = []
    for t in sorted(candidatos):
        if not np.isfinite(t):
            continue
        m = medir(t)
        if all(m[n][k] <= original[n][k] for n in nomes for k in original[n]):
            elegiveis.append((sum(m[n]["negacoes_perdidas"] for n in nomes),
                               sum(m[n]["negacoes_falsas"] for n in nomes), abs(t), t, m))
    _, _, _, t, m = min(elegiveis, key=lambda v: v[:4])
    return {"limiar": t, "motivo": "ganho_pareto" if t != 0 else "zero_preservado", "zero": original, "ajustado": m}


def criar_particoes(itens: list[dict], cv: dict) -> list[dict]:
    grupos = grupos_sem_duplicatas(itens)
    particoes = []
    for n, ref in enumerate(cv["folds"]):
        pool, teste = selecionar_fold(itens, cv, ref["grupos_teste"][0])
        grupos_pool = [grupos[i] for i in pool]
        internos = list(GroupKFold(n_splits=3).split(pool, groups=grupos_pool))
        tr, ca = internos[n % 3]
        p = {"fold": n, "treino": [pool[int(i)] for i in tr],
             "calibracao": [pool[int(i)] for i in ca], "teste": teste}
        conjuntos = [{grupos[i] for i in p[k]} for k in ("treino", "calibracao", "teste")]
        if any(conjuntos[a] & conjuntos[b] for a, b in ((0, 1), (0, 2), (1, 2))):
            raise ValueError("família atravessou treino/calibração/teste")
        if sorted(p["treino"] + p["calibracao"] + p["teste"]) != list(range(len(itens))):
            raise ValueError("partição incompleta ou duplicada")
        p["grupos"] = {k: sorted({grupos[i] for i in p[k]}) for k in ("treino", "calibracao", "teste")}
        particoes.append(p)
    if sorted(i for p in particoes for i in p["teste"]) != list(range(len(itens))):
        raise ValueError("cada exemplo deve ser avaliado uma vez")
    return particoes


def executar(*, referencia: Path, historico: Path, destino: Path) -> dict:
    if destino.exists():
        raise FileExistsError("destino existente; não sobrescrever")
    raiz = Path(__file__).resolve().parents[2]
    ler = lambda p: json.loads(p.read_text(encoding="utf-8"))
    r = ler(referencia / "relatorio.json")
    prov = r["proveniencia"]
    for nome, digest in prov["sha256_componentes"].items():
        if hashlib.sha256((raiz / nome).read_bytes()).hexdigest() != digest:
            raise ValueError(f"componente de referência mudou: {nome}")
    modelo_path = raiz / prov["modelo"]
    modelo_hash = hashlib.sha256(modelo_path.read_bytes()).hexdigest()
    if modelo_hash != prov["sha256_modelo"]:
        raise ValueError("modelo de referência mudou")
    catalogo = intents_registradas()
    datasets = raiz / "mente_laylay/neural/datasets"
    hist = carregar_jsonl(datasets / "dev_v0.jsonl", intents_permitidas=catalogo)
    for nome in ler(historico / "validacao_cruzada_heads.json")["dataset"]["lotes_candidatos"]:
        hist.extend(carregar_jsonl(datasets / "candidatos" / nome, intents_permitidas=catalogo))
    novos = carregar_jsonl(referencia / "lote_negacao.jsonl", intents_permitidas=catalogo)
    if _hash_dados(hist) != prov["sha256_historicos"] or _hash_dados(novos) != prov["sha256_novos"]:
        raise ValueError("dataset de referência mudou")
    hist = [i for i in hist if head_aplicavel(i, "negation")]
    novos = [i for i in novos if head_aplicavel(i, "negation")]
    itens = hist + novos
    particoes = criar_particoes(itens, r["cv"])
    protocolo = {"autoriza_promocao": False, "autoriza_execucao": False,
                 "metodo": "holdout_interno_3_partes_por_grupos_sem_refit", "eixo": "construcao",
                 "representacoes": ["base", "sinais_atomicos"], "peso_novos": 1,
                 "selecao": "Pareto por fatia; minimizar perdidas, falsas, distancia a zero, limiar",
                 "limites": ["teste externo conhecido de pesquisa, não reserva inédita", "não é calibração de probabilidades",
                             "modelo treina em menos dados que CV anterior; comparação válida é zero vs ajustado desta rodada"],
                 "sha256_modelo": modelo_hash, "sha256_itens": _hash_dados(itens), "particoes": particoes,
                 "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=raiz, text=True).strip(),
                 "worktree": subprocess.check_output(["git", "status", "--short"], cwd=raiz, text=True, encoding="utf-8"),
                 "sha256_componentes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                    (Path(__file__), raiz / "mente_laylay/neural/diagnostico_fold_negacao.py", referencia / "relatorio.json")}}
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    base = carregar_modelo(modelo_path).cabeca_negacao
    resultados = {}
    for representacao in protocolo["representacoes"]:
        registros, folds = [], []
        for p in particoes:
            cabeca = ajustar_cabeca(criar_prototipo_negacao(base, representacao), [itens[i] for i in p["treino"]])
            # Mesmos pesos e extrator para calibração e teste; nunca refazer fit.
            calibracao = p["calibracao"]
            scores = [float(s) for s in cabeca.decision_function([itens[i]["text"] for i in calibracao])]
            escolha = escolher_limiar(scores, [itens[i]["negated"] for i in calibracao],
                                     ["historica" if i < len(hist) else "nova" for i in calibracao])
            t = escolha["limiar"]
            teste = p["teste"]
            ss = cabeca.decision_function([itens[i]["text"] for i in teste])
            if not np.isfinite(ss).all():
                raise ValueError("score de teste não finito")
            if list(ss > 0) != list(cabeca.predict([itens[i]["text"] for i in teste])):
                raise ValueError("limiar zero não reproduz predict")
            registros.extend({"id": i, "fold": p["fold"], "score": float(s), "limiar": t,
                              "esperado": itens[i]["negated"], "zero": bool(s > 0), "ajustado": bool(s > t)}
                             for i, s in zip(teste, ss, strict=True))
            folds.append({"fold": p["fold"], "calibracao": escolha})
            print(f"{representacao}: fold {p['fold']} concluído; limiar={t:.6f}", flush=True)
        registros.sort(key=lambda x: x["id"])
        medidas = {}
        for nome, indices in (("historica", range(len(hist))), ("nova", range(len(hist), len(itens)))):
            ii = list(indices)
            medidas[nome] = {ch: medir_negacao([itens[i] for i in ii], [registros[i][ch] for i in ii]) for ch in ("zero", "ajustado")}
            medidas[nome]["ganhos"] = sum(registros[i]["zero"] != registros[i]["esperado"] == registros[i]["ajustado"] for i in ii)
            medidas[nome]["regressoes"] = sum(registros[i]["zero"] == registros[i]["esperado"] != registros[i]["ajustado"] for i in ii)
        resultados[representacao] = {"medidas": medidas, "folds": folds, "previsoes": registros}
    if hashlib.sha256(modelo_path.read_bytes()).hexdigest() != modelo_hash:
        raise ValueError("modelo mudou durante experimento")
    relatorio = {"autoriza_promocao": False, "autoriza_execucao": False, "modelos_salvos": False,
                 "protocolo_sha256": hashlib.sha256((destino / "protocolo.json").read_bytes()).hexdigest(), "resultados": resultados}
    with (destino / "relatorio.json").open("x", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
    return relatorio


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for nome in ("referencia", "historico", "destino"):
        p.add_argument("--" + nome, type=Path, required=True)
    r = executar(**vars(p.parse_args()))
    print(json.dumps({k: v["medidas"] for k, v in r["resultados"].items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
