"""Controle pareado: remove apenas o bloco lexical/posição do head contextual."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import warnings

import numpy as np
import sklearn
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction import DictVectorizer
from sklearn.neural_network import MLPClassifier
from threadpoolctl import threadpool_limits

from .comparar_ocorrencias_v4 import (
    BASE, PASTA_ENCODER, SHA_ENCODER, SHA_LOTE, PARAMETROS_COMPARACAO, ROTULOS,
    EncoderSemanticoONNX, Tokenizer, conferir_comprimentos, carregar_perfil,
    codificar_contexto, representar_tokens, rotular_ocorrencias, medir, estado_ajuste,
)

ANTERIOR = BASE / "memoria/neural/experimentos/comparacao_ocorrencias_v4_20260908_r1"
MODOS = ("janela_contextual", "contexto_sem_lexico")


def montar_matriz(lexico, contexto: np.ndarray, modo: str) -> csr_matrix:
    """Sem léxico nem posição explícita no segundo modo; sem remover tokens."""
    if modo not in MODOS:
        raise ValueError("condição fora do protocolo")
    if (contexto.ndim != 2 or contexto.shape[1] != 384 or not len(contexto)
            or not np.isfinite(contexto).all() or np.any(np.linalg.norm(contexto, axis=1) < 1e-9)):
        raise ValueError("contexto inválido; sem fallback")
    ctx = csr_matrix(contexto)
    if modo == "contexto_sem_lexico":
        return ctx
    if lexico is None or lexico.shape[0] != contexto.shape[0]:
        raise ValueError("controle sem alinhamento lexical")
    return hstack((lexico, ctx), format="csr")


def controle_igual(atual: dict, anterior: dict) -> bool:
    # Compara erros individuais, não apenas uma média coincidentemente igual.
    return all(atual[k] == anterior[k] for k in ("grupo", "dobra", "treino", "teste"))


def resumir(medicoes: list[dict]) -> dict:
    if len(medicoes) != 4 or {m["dobra"] for m in medicoes} != set(range(4)):
        raise ValueError("condição incompleta")
    ms = [m["teste"] for m in medicoes]
    r = {k: sum(m[k] for m in ms) for k in ("casos", "casos_exatos_acao_sem_alvos", "acoes_esperadas",
        "acoes_ausentes", "acoes_extras", "pedidos_inventados")}
    if r["casos"] != 1176 or r["acoes_esperadas"] != 1848:
        raise ValueError("denominador do perfil mudou")
    r["taxa_exata"] = r["casos_exatos_acao_sem_alvos"] / r["casos"]
    r["media_por_grupo"] = sum(m["casos_exatos_acao_sem_alvos"] / m["casos"] for m in ms) / 4
    r["apto_proxima_fronteira"] = r["taxa_exata"] >= .95 and r["pedidos_inventados"] == r["acoes_extras"] == 0
    return r


def executar(destino: Path) -> dict:
    if destino.exists():
        raise FileExistsError("preservar ablação anterior")
    casos, dobras = carregar_perfil()
    protocolo_antigo = json.loads((ANTERIOR / "protocolo.json").read_text(encoding="utf-8"))
    for nome, sha in protocolo_antigo["codigo_sha256"].items():
        if hashlib.sha256((BASE / nome).read_bytes()).hexdigest() != sha:
            raise ValueError("código de referência divergiu")
    if (protocolo_antigo["dobras"] != dobras or protocolo_antigo["fonte_sha256"] != SHA_LOTE
            or protocolo_antigo["parametros"] != json.loads(json.dumps(PARAMETROS_COMPARACAO))):
        raise ValueError("dados, partições ou parâmetros divergiram")
    encoder = EncoderSemanticoONNX(PASTA_ENCODER, sha256_modelo=SHA_ENCODER, batch_size=16)
    encoder.validar_artefatos()
    if hashlib.sha256(encoder.caminho_tokenizer.read_bytes()).hexdigest() != protocolo_antigo["tokenizer_sha256"]:
        raise ValueError("tokenizer divergiu")
    textos = [c["alinhado"]["entrada"]["texto_entrada"] for c in casos]
    tamanhos = conferir_comprimentos(textos, Tokenizer.from_file(str(encoder.caminho_tokenizer)))
    fontes = [ANTERIOR / "protocolo.json", ANTERIOR / "resultado.json",
              *[ANTERIOR / f"janela_contextual_dobra_{i}.json" for i in range(4)]]
    protocolo = {**protocolo_antigo, "perfil": "ablacao_lexical_ocorrencias_v4", "modos": MODOS,
        "codigo_ablacao_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "fontes_controle_sha256": {str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in fontes},
        "max_tokens": max(tamanhos), "sklearn": sklearn.__version__,
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE, text=True).strip(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=BASE, text=True).splitlines(),
        "hipotese": "o bloco lexical/posição favorece atalhos prejudiciais fora da família de treino",
        "candidato": "apenas os mesmos 384 estados contextuais; sem janela, sufixos ou posição explícita",
        "limites": "remove bloco completo, não palavras isoladas; dimensão/inicialização da MLP mudam; encoder continua codificando ordem e léxico",
        "politica_controle": "reproduzir treino/teste das quatro dobras antes de ajustar condição nova"}
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    inicio = time.perf_counter()
    ctx = codificar_contexto(textos, encoder)
    xs = [representar_tokens(c["alinhado"]["entrada"])[1] for c in casos]
    ys = [rotular_ocorrencias(c) for c in casos]
    por_id = {c["id"]: i for i, c in enumerate(casos)}
    resultados, controle_ok = [], True
    with threadpool_limits(limits=1):
        for modo in MODOS:
            if not controle_ok:
                break
            for numero, dobra in enumerate(dobras):
                tr, te = ([por_id[k] for k in dobra[chave]] for chave in ("treino", "teste"))
                xtr = xte = None
                if modo == "janela_contextual":
                    vectorizer = DictVectorizer(dtype=np.float32)
                    xtr = vectorizer.fit_transform([x for i in tr for x in xs[i]])
                    xte = vectorizer.transform([x for i in te for x in xs[i]])
                xtr = montar_matriz(xtr, np.vstack([ctx[i] for i in tr]), modo)
                xte = montar_matriz(xte, np.vstack([ctx[i] for i in te]), modo)
                ytr = [y for i in tr for y in ys[i]]
                if set(ytr) != ROTULOS:
                    raise ValueError("treino sem classes completas")
                modelo = MLPClassifier(**PARAMETROS_COMPARACAO)
                with warnings.catch_warnings(record=True) as avisos:
                    warnings.simplefilter("always")
                    modelo.fit(xtr, ytr)

                def avaliar(ids, matriz):
                    pred, partes, cursor = modelo.predict(matriz).tolist(), [], 0
                    for i in ids:
                        fim = cursor + len(ys[i])
                        partes.append(pred[cursor:fim])
                        cursor = fim
                    return medir([casos[i] for i in ids], partes)

                m = {"modo": modo, "dobra": numero, "grupo": dobra["grupo_teste"],
                     "treino": avaliar(tr, xtr), "teste": avaliar(te, xte), **estado_ajuste(modelo),
                     "avisos": [str(a.message) for a in avisos]}
                if modo == "janela_contextual":
                    antigo = json.loads((ANTERIOR / f"janela_contextual_dobra_{numero}.json").read_text(encoding="utf-8"))
                    m["controle_reproduzido"] = controle_igual(m, antigo)
                    controle_ok = controle_ok and m["controle_reproduzido"]
                resultados.append(m)
                with (destino / f"{modo}_dobra_{numero}.json").open("x", encoding="utf-8") as f:
                    json.dump(m, f, ensure_ascii=False, indent=2)
                print(json.dumps({"modo": modo, "dobra": numero,
                    "exatos": m["teste"]["casos_exatos_acao_sem_alvos"],
                    "inventados": m["teste"]["pedidos_inventados"], "controle_ok": controle_ok}), flush=True)
    resumo = {modo: resumir([m for m in resultados if m["modo"] == modo]) for modo in MODOS
              if len([m for m in resultados if m["modo"] == modo]) == 4}
    r = {"resumo": resumo, "controle_reproduzido": controle_ok, "comparacao_conclusiva": controle_ok and len(resumo) == 2,
         "segundos": time.perf_counter() - inicio, "modelo_completo_avaliado": False,
         "autoriza_promocao": False, "autoriza_execucao": False, "reservas_usadas": False}
    with (destino / "resultado.json").open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    print(json.dumps(executar(parser.parse_args().destino), ensure_ascii=False))
