"""Prova técnica isolada de forward/backward; não treina linguagem nem salva pesos.

Executar diretamente com o Python do ambiente de treino, não com laylay.py.
Rótulos artificiais servem apenas para exercitar o grafo e o otimizador.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

BASE = Path(__file__).resolve().parents[2]
REPOSITORIO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
REVISAO = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
SHA_PESOS = "eaa086f0ffee582aeb45b36e34cdd1fe2d6de2bef61f8a559a1bbc9bd955917b"
SHA_TOKENIZER = "2c3387be76557bd40970cec13153b3bbf80407865484b209e655e5e4729076b8"
PASTA_MODELO = BASE / "memoria/neural/modelos/minilm-treinavel-e8f8c211"
ARQUIVOS = ("config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json",
            "special_tokens_map.json", "sentence_bert_config.json")
TEXTO_SINTETICO = "Abre o navegador de testes, mas não abre outro aplicativo."


def sha_arquivo(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def conferir_modelo(pasta: Path) -> dict[str, str]:
    hashes = {nome: sha_arquivo(pasta / nome) for nome in ARQUIVOS}
    if hashes["model.safetensors"] != SHA_PESOS or hashes["tokenizer.json"] != SHA_TOKENIZER:
        raise ValueError("pesos/tokenizer divergem da revisão fixada")
    cfg = json.loads((pasta / "config.json").read_text(encoding="utf-8"))
    if cfg.get("model_type") != "bert" or cfg.get("hidden_size") != 384:
        raise ValueError("arquitetura fora do perfil técnico")
    return hashes


def conferir_resultados(resultados: list[dict]) -> None:
    if len(resultados) != 2 or any(type(r["treinar_encoder"]) is not bool for r in resultados) or [r["treinar_encoder"] for r in resultados] != [False, True]:
        raise ValueError("duas condições completas são obrigatórias")
    a, b = resultados
    for chave in ("encoder_inicial_sha256", "cabeca_inicial_sha256", "logits_iniciais_sha256"):
        if a[chave] != b[chave]:
            raise ValueError(f"condições não começaram iguais: {chave}")
    for r in resultados:
        if r["gradientes_finitos"] is not True or r["cabeca_mudou"] is not True:
            raise ValueError("passo do otimizador não comprovado")
        if r["encoder_mudou"] is not r["treinar_encoder"]:
            raise ValueError("efeito no encoder incompatível com congelamento")
        if r["encoder_com_gradiente"] is not r["treinar_encoder"]:
            raise ValueError("gradiente incompatível com congelamento")


def _sha_estado(modelo) -> str:
    digest = hashlib.sha256()
    for nome, valor in modelo.state_dict().items():
        digest.update(nome.encode())
        digest.update(str(tuple(valor.shape)).encode())
        digest.update(valor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def _medir_condicao(pasta: Path, *, treinar_encoder: bool) -> dict:
    import torch
    from transformers import AutoModel, AutoTokenizer

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    inicio = time.perf_counter()
    modelo = AutoModel.from_pretrained(str(pasta), local_files_only=True,
        trust_remote_code=False, use_safetensors=True, dtype=torch.float32, attn_implementation="eager")
    tokenizer = AutoTokenizer.from_pretrained(str(pasta), local_files_only=True, trust_remote_code=False)
    torch.manual_seed(27)
    cabeca = torch.nn.Linear(384, 10)
    antes_encoder, antes_cabeca = _sha_estado(modelo), _sha_estado(cabeca)
    parametros = sum(p.numel() for p in modelo.parameters())
    modelo.requires_grad_(treinar_encoder)
    modelo.to("cuda")
    cabeca.to("cuda")
    # Dropout desligado para verificar igualdade exata das condições iniciais.
    # eval() não desliga autograd; o braço ajustado continua diferenciável.
    modelo.eval()
    entradas = tokenizer(TEXTO_SINTETICO, return_tensors="pt", padding="max_length",
                         max_length=128, truncation=False)
    if entradas["input_ids"].shape != (1, 128):
        raise ValueError("dimensão/truncamento fora do smoke")
    entradas = {k: v.to("cuda") for k, v in entradas.items()}
    alvos = torch.arange(128, device="cuda").remainder(10).unsqueeze(0)
    alvos[entradas["attention_mask"] == 0] = -100
    otimizador = torch.optim.AdamW(
        [p for p in [*modelo.parameters(), *cabeca.parameters()] if p.requires_grad],
        lr=2e-5, foreach=False,
    )
    torch.cuda.synchronize()
    inicio_passo = time.perf_counter()
    ocultos = modelo(**entradas).last_hidden_state
    logits = cabeca(ocultos)
    inicial_logits = hashlib.sha256(logits.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
    perda = torch.nn.functional.cross_entropy(logits.reshape(-1, 10), alvos.reshape(-1))
    if not torch.isfinite(perda).item():
        raise ValueError("perda não finita")
    perda.backward()
    # O pooler existe no checkpoint, mas não participa da saída token-level.
    # Seu gradiente pode ser None; os parâmetros usados são conferidos abaixo.
    usados = [p for nome, p in modelo.named_parameters() if not nome.startswith("pooler.")]
    finitos = all(p.grad is not None and torch.isfinite(p.grad).all().item()
                  for p in usados if p.requires_grad) and all(
                      p.grad is not None and torch.isfinite(p.grad).all().item() for p in cabeca.parameters())
    if not finitos:
        raise ValueError("gradiente ausente/não finito em parâmetro usado")
    encoder_com_gradiente = any(p.grad is not None for p in modelo.parameters())
    otimizador.step()
    torch.cuda.synchronize()
    segundos_passo = time.perf_counter() - inicio_passo
    pico = torch.cuda.max_memory_allocated()
    depois_encoder, depois_cabeca = _sha_estado(modelo), _sha_estado(cabeca)
    return {"treinar_encoder": treinar_encoder, "encoder_parametros": parametros,
            "encoder_inicial_sha256": antes_encoder, "cabeca_inicial_sha256": antes_cabeca,
            "logits_iniciais_sha256": inicial_logits, "encoder_final_sha256": depois_encoder,
            "encoder_mudou": antes_encoder != depois_encoder, "cabeca_mudou": antes_cabeca != depois_cabeca,
            "encoder_com_gradiente": encoder_com_gradiente, "gradientes_finitos": finitos,
            "perda_artificial": float(perda.detach().cpu()), "pico_alocado_mib": round(pico / 2**20, 2),
            "segundos_passo": round(segundos_passo, 3), "segundos_total": round(time.perf_counter() - inicio, 3)}


def executar(destino: Path, *, baixar: bool = False) -> dict:
    if destino.exists():
        raise FileExistsError("preservar resultado anterior")
    # Configuração apenas deste processo, antes de carregar CUDA/Hugging Face.
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    import torch
    from huggingface_hub import snapshot_download

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA indisponível; não trocar silenciosamente para CPU")
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if baixar:
        snapshot_download(repo_id=REPOSITORIO, revision=REVISAO, local_dir=str(PASTA_MODELO),
                          allow_patterns=list(ARQUIVOS), token=False, max_workers=2)
    hashes = conferir_modelo(PASTA_MODELO)
    protocolo = {"tipo": "smoke_tecnico_encoder", "repo": REPOSITORIO, "revisao": REVISAO,
                 "arquivos_sha256": hashes, "codigo_sha256": sha_arquivo(Path(__file__)),
                 "python": sys.version, "executavel": sys.executable,
                 "dependencias": dict(sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions())),
                 "gpu": torch.cuda.get_device_name(), "cuda": torch.version.cuda,
                 "capacidade_cuda": torch.cuda.get_device_capability(), "semente": 27,
                 "batch_fisico": 1, "comprimento": 128, "precisao": "float32", "modo": "eval_com_autograd",
                 "rotulos": "artificiais_arange_mod10_sem_corpus", "passos_por_condicao": 1,
                 "treino_linguistico": False, "pesos_salvos": False, "autoriza_execucao": False,
                 "autoriza_promocao": False}
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    resultados = []
    try:
        for treinar in (False, True):
            r = _medir_condicao(PASTA_MODELO, treinar_encoder=treinar)
            resultados.append(r)
            print(json.dumps(r), flush=True)
            gc.collect()
        conferir_resultados(resultados)
        r = {"ok": True, "condicoes": resultados, "viavel_apenas_batch1_len128_eval_fp32": True,
             "qualidade_linguistica_avaliada": False, "pesos_salvos": False,
             "autoriza_execucao": False, "autoriza_promocao": False}
    except Exception as erro:
        r = {"ok": False, "condicoes": resultados, "erro": type(erro).__name__,
             "detalhe": str(erro), "pesos_salvos": False, "autoriza_promocao": False}
        raise
    finally:
        with (destino / "resultado.json").open("x", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    parser.add_argument("--baixar", action="store_true")
    args = parser.parse_args()
    print(json.dumps(executar(args.destino, baixar=args.baixar), ensure_ascii=False))
