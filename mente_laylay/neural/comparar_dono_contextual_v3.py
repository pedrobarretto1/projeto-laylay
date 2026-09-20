"""Ablação do contexto global e marcação do trecho, sem mudar decisões reais."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import warnings

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from threadpoolctl import threadpool_limits
from tokenizers import Tokenizer

from .candidato_relacional import validar_entrada
from .comparar_contexto_semantico_v3 import (
    PASTA_ENCODER, SHA_ENCODER, representar_contexto, conferir_comprimentos,
)
from .comparar_lote_estrutural_v3 import carregar_lote, preparar_dobras, resumir, PARAMETROS_COMPARACAO
from .diagnosticar_head_relacional import montar_linhas, medir_acoes
from .encoder_semantico import EncoderSemanticoONNX
from .treinar_relacional_isolado import BASE, VARIANTES

MODOS = ("global_local", "local", "marcado")


def contexto_marcado(entrada: dict, posicao: int) -> str:
    validar_entrada(entrada)
    if type(posicao) is not int or not 0 <= posicao < len(entrada["segmentos"]):
        raise ValueError("posição do trecho inválida")
    linhas = ["Frase original: " + entrada["texto_entrada"], "Trechos em ordem:"]
    for i, s in enumerate(entrada["segmentos"]):
        marca = " [trecho em análise]" if i == posicao else ""
        linhas.append(f"{i + 1}{marca}: {s['texto']}")
    return "\n".join(linhas)


def representar_dono(entrada: dict, posicao: int, variante: tuple[str, str], vetores: dict, modo: str) -> dict:
    validar_entrada(entrada)
    if modo not in MODOS or type(posicao) is not int or not 0 <= posicao < len(entrada["segmentos"]):
        raise ValueError("modo fora do protocolo")
    if modo == "marcado":
        virtual = {**entrada, "texto_entrada": contexto_marcado(entrada, posicao)}
        return representar_contexto(virtual, posicao, variante, vetores, "semantico")
    if modo == "local":
        # A chamada reutilizada recebe somente o texto local como global:
        # depois REMOVE esse bloco. Nem consulta vetor global do turno.
        virtual = {**entrada, "texto_entrada": entrada["segmentos"][posicao]["texto"]}
        r = representar_contexto(virtual, posicao, variante, vetores, "semantico")
        return {k: v for k, v in r.items() if not (k.startswith("semantica:") and ":global:" in k)}
    return representar_contexto(entrada, posicao, variante, vetores, "semantico")


def executar(destino: Path) -> dict:
    exemplos, _ = carregar_lote()
    dobras = preparar_dobras(exemplos)
    anterior = BASE / "memoria/neural/experimentos/sonda_contexto_semantico_v3_20260908"
    p = json.loads((anterior / "protocolo.json").read_text(encoding="utf-8"))
    fonte_sonda = Path(__file__).with_name("comparar_contexto_semantico_v3.py")
    if hashlib.sha256(fonte_sonda.read_bytes()).hexdigest() != p["codigo_sonda_sha256"]:
        raise ValueError("controle semântico anterior mudou")
    for nome, sha in p["codigo_sha256"].items():
        if hashlib.sha256(Path(__file__).with_name(nome).read_bytes()).hexdigest() != sha:
            raise ValueError("dependência do controle anterior mudou")
    textos = sorted({texto for e in exemplos for texto in [e["entrada"]["texto_entrada"],
        *[s["texto"] for s in e["entrada"]["segmentos"]],
        *[contexto_marcado(e["entrada"], pos) for pos in range(len(e["entrada"]["segmentos"]))]]})
    encoder = EncoderSemanticoONNX(PASTA_ENCODER, sha256_modelo=SHA_ENCODER, batch_size=16)
    encoder.validar_artefatos()
    if hashlib.sha256(encoder.caminho_tokenizer.read_bytes()).hexdigest() != p["tokenizer_sha256"]:
        raise ValueError("tokenizer do controle mudou")
    textos_base = p["textos_encoder"]
    textos_novos = sorted(set(textos) - set(textos_base))
    tamanhos = conferir_comprimentos(textos, Tokenizer.from_file(str(encoder.caminho_tokenizer)))
    destino.mkdir(parents=True, exist_ok=False)
    protocolo = {**p, "perfil": "ablacao_dono_contextual_v3", "condicoes": MODOS,
        "codigo_ablacao_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=BASE, text=True).splitlines(),
        "textos_encoder": textos, "max_tokens_observado": max(tamanhos),
        "lotes_encoder": {"controle_mesma_ordem": textos_base, "novos": textos_novos},
        "pooling": "global/local versus somente local versus global marcado/local; média L2 congelada",
        "hipotese": "separar influência do contexto global de erro de ato local, sem usar gabarito",
        "limites": "marcadores não treinados como tokens especiais; um seed; sem comparação com runtime"}
    with (destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    inicio = time.perf_counter()
    # Reproduzir exatamente o lote/ordem original, sem misturar os textos novos.
    matriz_base = encoder.codificar(textos_base)
    matriz_nova = encoder.codificar(textos_novos)
    segundos_encoder = time.perf_counter() - inicio
    if (matriz_base.shape != (len(textos_base), 384) or matriz_nova.shape != (len(textos_novos), 384)
            or not np.isfinite(matriz_base).all() or not np.isfinite(matriz_nova).all()):
        raise ValueError("encoder retornou matriz inválida")
    vetores = {**dict(zip(textos_base, matriz_base)), **dict(zip(textos_novos, matriz_nova))}
    print(json.dumps({"textos_codificados": len(textos), "segundos": segundos_encoder}), flush=True)
    _, y, chaves = montar_linhas(exemplos, sorted(VARIANTES), "cruzada")
    entradas = {e["id"]: e["entrada"] for e in exemplos}
    posicoes = {(e["id"], s["indice"]): pos for e in exemplos for pos, s in enumerate(e["entrada"]["segmentos"])}
    resultados = []
    with threadpool_limits(limits=1):
        for modo in MODOS:
            x = [representar_dono(entradas[c[0]], posicoes[c[0], c[1]], (c[2], c[3]), vetores, modo) for c in chaves]
            for numero, (tr, te) in enumerate(dobras):
                ids_tr, ids_te = {exemplos[i]["id"] for i in tr}, {exemplos[i]["id"] for i in te}
                itr = [i for i, c in enumerate(chaves) if c[0] in ids_tr]
                ite = [i for i, c in enumerate(chaves) if c[0] in ids_te]
                modelo = make_pipeline(DictVectorizer(), MLPClassifier(**PARAMETROS_COMPARACAO))
                with warnings.catch_warnings(record=True) as avisos:
                    warnings.simplefilter("always")
                    modelo.fit([x[i] for i in itr], [y[i] for i in itr])
                medir = lambda ids: medir_acoes([chaves[i] for i in ids], [y[i] for i in ids],
                                               modelo.predict([x[i] for i in ids]).tolist())
                resultados.append({"modo": modo, "dobra": numero, "treino": medir(itr), "teste": medir(ite),
                    "iteracoes": modelo[-1].n_iter_, "loss": modelo[-1].loss_,
                    "avisos": [a.category.__name__ for a in avisos]})
            print(json.dumps({"modo": modo, **resumir([m for m in resultados if m["modo"] == modo])}), flush=True)
    resumos = {modo: resumir([m for m in resultados if m["modo"] == modo]) for modo in MODOS}
    controle = json.loads((anterior / "resultado.json").read_text(encoding="utf-8"))["resumo"]["semantico"]
    # Controle divergente torna a comparação inconclusiva, sem substituir baseline.
    controle_ok = resumos["global_local"] == controle
    r = {"resumo": resumos, "medicoes": resultados, "controle_reproduzido": controle_ok,
         "encoder_segundos": segundos_encoder, "total_segundos": time.perf_counter() - inicio,
         "reserva_usada": False, "autoriza_promocao": False, "autoriza_execucao": False,
         "comparacao_conclusiva": controle_ok, "modelo_completo_avaliado": False}
    with (destino / "resultado.json").open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    executar(parser.parse_args().destino)
