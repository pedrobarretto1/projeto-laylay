"""Sonda local independente de NLI para alegações didáticas.

Usa somente um modelo ONNX já presente no cache Hugging Face. Nenhum dado do
usuário vai para a rede durante a inferência. Não integra o runtime Laylay.
"""

from __future__ import annotations

import argparse
import json
import time

from huggingface_hub import hf_hub_download
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from scripts.analises.sonda_implicacao_inedita import CASOS, FONTES


REPOSITORIO = "onnx-community/multilingual-MiniLMv2-L6-mnli-xnli-ONNX"
REVISAO = "ca5daf3d11b6c4b3143b1f4602a2edfb64c3ad7e"
ROTULO_LOCAL = {
    "entailment": "sustentada",
    "neutral": "sem_prova",
    "contradiction": "contradita",
}


def carregar_artefatos(
    nome_modelo: str = "onnx/model_uint8.onnx",
) -> tuple[Tokenizer, ort.InferenceSession, dict[str, str]]:
    if nome_modelo not in {"onnx/model_uint8.onnx", "onnx/model.onnx"}:
        raise ValueError("variante ONNX não permitida na sonda")
    def caminho(nome: str) -> str:
        return hf_hub_download(
            repo_id=REPOSITORIO, revision=REVISAO,
            filename=nome, local_files_only=True,
        )

    with open(caminho("config.json"), encoding="utf-8") as arquivo:
        config = json.load(arquivo)
    rotulos = {str(k): str(v) for k, v in config["id2label"].items()}
    if set(rotulos.values()) != set(ROTULO_LOCAL):
        raise ValueError(f"ordem de classes inesperada: {rotulos}")
    tokenizer = Tokenizer.from_file(caminho("tokenizer.json"))
    tokenizer.enable_truncation(max_length=256)
    sessao = ort.InferenceSession(
        caminho(nome_modelo), providers=["CPUExecutionProvider"],
    )
    return tokenizer, sessao, rotulos


def inferir(
    tokenizer: Tokenizer, sessao: ort.InferenceSession,
    rotulos: dict[str, str], fonte: str, alegacao: str,
) -> dict:
    inicio = time.monotonic()
    codificado = tokenizer.encode(fonte, alegacao)
    entrada = {
        "input_ids": np.asarray([codificado.ids], dtype=np.int64),
        "attention_mask": np.asarray([codificado.attention_mask], dtype=np.int64),
    }
    logits = sessao.run(None, entrada)[0][0]
    probabilidades = np.exp(logits - np.max(logits))
    probabilidades = probabilidades / probabilidades.sum()
    scores = {
        ROTULO_LOCAL[rotulos[str(i)]]: round(float(probabilidade), 4)
        for i, probabilidade in enumerate(probabilidades)
    }
    return {
        "classe": max(scores, key=scores.get), "scores": scores,
        "latencia_s": round(time.monotonic() - inicio, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=len(CASOS))
    args = parser.parse_args()
    inicio = time.monotonic()
    tokenizer, sessao, rotulos = carregar_artefatos()
    carregamento = round(time.monotonic() - inicio, 3)
    totais = {campo: {"acertos": 0, "n": 0} for campo in ("definicao", "exemplo")}
    falsos_positivos = 0
    for id_caso, id_fonte, campo, alegacao, esperado in CASOS[:args.limit]:
        resultado = inferir(tokenizer, sessao, rotulos, FONTES[id_fonte]["texto"], alegacao)
        totais[campo]["acertos"] += int(resultado["classe"] == esperado)
        totais[campo]["n"] += 1
        falsos_positivos += int(esperado != "sustentada" and resultado["classe"] == "sustentada")
        print(json.dumps({"id": id_caso, "tipo": campo, "esperado": esperado,
                          "observado": resultado}, ensure_ascii=False), flush=True)
    print(json.dumps({"totais": totais, "falsos_positivos_sustentada": falsos_positivos,
                      "carregamento_s": carregamento,
                      "aprovado_para_producao": False}, ensure_ascii=False), flush=True)
    return 0 if all(v["acertos"] == v["n"] for v in totais.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
