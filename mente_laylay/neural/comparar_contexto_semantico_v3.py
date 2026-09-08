"""Sonda offline de representação congelada; não é fine-tuning de Transformer.

Compara lexical, semântica global/local e híbrida no mesmo head e dobras.
O encoder existente não aprende com DEV nem reserva. Nenhum alvo gold entra
na representação. A média dos tokens não oferece saída de spans/receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
import warnings

import numpy as np
import sklearn
import onnxruntime
import tokenizers
from sklearn.feature_extraction import DictVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from threadpoolctl import threadpool_limits
from tokenizers import Tokenizer

from .candidato_relacional import validar_entrada
from .comparar_lote_estrutural_v3 import carregar_lote, preparar_dobras, resumir, PARAMETROS_COMPARACAO
from .diagnosticar_head_relacional import montar_linhas, representar, medir_acoes
from .encoder_semantico import EncoderSemanticoONNX
from .treinar_relacional_isolado import BASE, VARIANTES

PASTA_ENCODER = BASE / "memoria/neural/modelos/paraphrase-multilingual-MiniLM-L12-v2-onnx-qint8-avx2"
SHA_ENCODER = "98a01d88b7de996cdea58c32ca71208c09968d143798814b2ea09d3439dc334f"
MODOS = ("lexical", "semantico", "hibrido")


def representar_contexto(entrada: dict, posicao: int, variante: tuple[str, str],
                        vetores: dict[str, np.ndarray], modo: str) -> dict:
    validar_entrada(entrada)
    if modo not in MODOS:
        raise ValueError("representação fora do protocolo")
    if modo == "lexical":
        return representar(entrada, posicao, variante, "cruzada")
    chave = "/".join(variante)
    base = (representar(entrada, posicao, variante, "cruzada") if modo == "hibrido" else
            {"variante": chave, "posicao_dono": float(posicao),
             "total_segmentos": float(len(entrada["segmentos"]))})
    for escopo, texto in (("global", entrada["texto_entrada"]),
                           ("local", entrada["segmentos"][posicao]["texto"])):
        vetor = np.asarray(vetores[texto])  # Sem fallback lexical em vetor ausente.
        if vetor.shape != (384,) or not np.isfinite(vetor).all() or np.linalg.norm(vetor) < 1e-9:
            raise ValueError("vetor semântico inválido")
        for i, valor in enumerate(vetor):
            base[f"semantica:{escopo}:{i}"] = float(valor)
            base[f"semantica:{chave}:{escopo}:{i}"] = float(valor)
    return base


def conferir_comprimentos(textos: list[str], tokenizer: Tokenizer, limite: int = 128) -> list[int]:
    # Objeto separado: não altera tokenizer/sessão do encoder de produção.
    tokenizer.no_truncation()
    tokenizer.no_padding()
    tamanhos = [len(tokenizer.encode(t).ids) for t in textos]
    if not textos or any(n > limite for n in tamanhos):
        raise ValueError("texto excede contexto; não permitir truncamento silencioso")
    return tamanhos


def executar(destino: Path) -> dict:
    exemplos, _ = carregar_lote()
    dobras = preparar_dobras(exemplos)
    anterior = BASE / "memoria/neural/experimentos/comparacao_estrutural_v3_20260907"
    protocolo_anterior = json.loads((anterior / "protocolo.json").read_text(encoding="utf-8"))
    for nome, sha in protocolo_anterior["codigo_sha256"].items():
        if hashlib.sha256((Path(__file__).parent / nome).read_bytes()).hexdigest() != sha:
            raise ValueError("controle anterior mudou")
    encoder = EncoderSemanticoONNX(PASTA_ENCODER, sha256_modelo=SHA_ENCODER, batch_size=16)
    encoder.validar_artefatos()
    textos = sorted({texto for e in exemplos for texto in
                     [e["entrada"]["texto_entrada"], *[s["texto"] for s in e["entrada"]["segmentos"]]]})
    tamanhos = conferir_comprimentos(textos, Tokenizer.from_file(str(encoder.caminho_tokenizer)))
    destino.mkdir(parents=True, exist_ok=False)
    protocolo = {**protocolo_anterior, "perfil": "sonda_contexto_semantico_v3",
        "python": platform.python_version(), "sklearn": sklearn.__version__,
        "onnxruntime": onnxruntime.__version__, "tokenizers": tokenizers.__version__,
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=BASE, text=True).splitlines(),
        "condicoes": MODOS, "encoder_congelado": True, "encoder_sha256": SHA_ENCODER,
        "tokenizer_sha256": hashlib.sha256(encoder.caminho_tokenizer.read_bytes()).hexdigest(),
        "pooling": "média mascarada L2; vetor global e local separados; sem spans",
        "max_length": 128, "batch_size": 16, "max_tokens_observado": max(tamanhos),
        "textos_encoder": textos, "codigo_sonda_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "codigo_encoder_sha256": hashlib.sha256((Path(__file__).parent / "encoder_semantico.py").read_bytes()).hexdigest(),
        "fontes_tecnicas": [
            "https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "https://arxiv.org/abs/1902.10909", "https://sbert.net/examples/cross_encoder/applications/README.html"],
        "limites": "um seed; encoder congelado, não joint token-level nem CrossEncoder ajustado; sem comparação com runtime"}
    with (destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    inicio = time.perf_counter()
    matriz = encoder.codificar(textos)
    tempo_encoder = time.perf_counter() - inicio
    if matriz.shape != (len(textos), 384) or not np.isfinite(matriz).all():
        raise ValueError("lote do encoder inválido")
    vetores = dict(zip(textos, matriz))
    np.save(destino / "vetores_congelados.npy", matriz, allow_pickle=False)
    print(json.dumps({"encoder_concluido": len(textos), "segundos": tempo_encoder}), flush=True)
    _, y, chaves = montar_linhas(exemplos, sorted(VARIANTES), "cruzada")
    entradas = {e["id"]: e["entrada"] for e in exemplos}
    posicoes = {(e["id"], s["indice"]): p for e in exemplos for p, s in enumerate(e["entrada"]["segmentos"])}
    resultados = []
    with threadpool_limits(limits=1):
        for modo in MODOS:
            x = [representar_contexto(entradas[ident], posicoes[ident, indice], (intent, action), vetores, modo)
                 for ident, indice, intent, action in chaves]
            for numero, (tr, te) in enumerate(dobras):
                ids_tr, ids_te = {exemplos[i]["id"] for i in tr}, {exemplos[i]["id"] for i in te}
                itr = [i for i, c in enumerate(chaves) if c[0] in ids_tr]
                ite = [i for i, c in enumerate(chaves) if c[0] in ids_te]
                modelo = make_pipeline(DictVectorizer(), MLPClassifier(**PARAMETROS_COMPARACAO))
                with warnings.catch_warnings(record=True) as avisos:
                    warnings.simplefilter("always")
                    modelo.fit([x[i] for i in itr], [y[i] for i in itr])
                medir = lambda indices: medir_acoes([chaves[i] for i in indices], [y[i] for i in indices],
                            modelo.predict([x[i] for i in indices]).tolist())
                resultados.append({"modo": modo, "dobra": numero, "treino": medir(itr), "teste": medir(ite),
                                   "iteracoes": modelo[-1].n_iter_, "loss": modelo[-1].loss_,
                                   "avisos": [a.category.__name__ for a in avisos]})
            print(json.dumps({"modo": modo, **resumir([m for m in resultados if m["modo"] == modo])}), flush=True)
    resumos = {modo: resumir([m for m in resultados if m["modo"] == modo]) for modo in MODOS}
    controle = json.loads((anterior / "resultado.json").read_text(encoding="utf-8"))["resumo"]["cruzada"]
    if resumos["lexical"] != controle:
        raise ValueError("controle não reproduziu baseline; não comparar candidatos")
    r = {"resumo": resumos, "medicoes": resultados, "encoder_segundos": tempo_encoder,
         "total_segundos": time.perf_counter() - inicio, "controle_reproduzido": True,
         "reserva_usada": False, "autoriza_promocao": False, "autoriza_execucao": False,
         "modelo_completo_avaliado": False}
    with (destino / "resultado.json").open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    executar(parser.parse_args().destino)
