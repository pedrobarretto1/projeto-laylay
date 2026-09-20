"""Forward/backward real com supervisão preparada; nenhum passo de otimizador.

Executar diretamente no Python isolado de treino. Verifica o sinal de erro,
não aprendizado ou qualidade linguística. Não escreve pesos.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
from pathlib import Path
import sys

if __package__:
    from .perda_encoder import calcular_perda, logits_por_tokens
    from .sonda_ambiente_encoder import PASTA_MODELO, conferir_modelo, sha_arquivo, _sha_estado
else:
    from perda_encoder import calcular_perda, logits_por_tokens
    from sonda_ambiente_encoder import PASTA_MODELO, conferir_modelo, sha_arquivo, _sha_estado


def executar(preparacao: Path, sha_esperado: str, destino: Path) -> dict:
    if destino.exists():
        raise FileExistsError("preservar sonda anterior")
    if sha_arquivo(preparacao) != sha_esperado:
        raise ValueError("preparação diverge do snapshot aprovado")
    dados = json.loads(preparacao.read_text(encoding="utf-8"))
    if (dados["particao"] != "desenvolvimento" or dados["uso"] != "diagnostico"
            or not dados["exemplos"] or len(dados["rotulos_catalogo"]) != 10
            or any(dados[k] is not False for k in ("treino_permitido", "autoriza_execucao", "autoriza_promocao"))):
        raise ValueError("sonda exige preparação de diagnóstico isolada")
    fontes = dict(dados["fontes_sha256"])
    fontes[str(preparacao.resolve())] = sha_esperado
    for nome in ("perda_encoder.py", "sonda_perda_encoder.py", "sonda_ambiente_encoder.py"):
        p = Path(__file__).with_name(nome)
        fontes[str(p.resolve())] = sha_arquivo(p)
    def conferir_fontes():
        if any(sha_arquivo(Path(p)) != digest for p, digest in fontes.items()):
            raise ValueError("fonte mudou desde a preparação")
    conferir_fontes()
    hashes_modelo = conferir_modelo(PASTA_MODELO)
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    import torch
    from transformers import AutoModel

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA indisponível para a sonda fixada")
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    resultados = []
    for liberar_encoder in (False, True):
        encoder = AutoModel.from_pretrained(str(PASTA_MODELO), local_files_only=True,
            trust_remote_code=False, use_safetensors=True, dtype=torch.float32, attn_implementation="eager")
        encoder.requires_grad_(liberar_encoder)
        encoder.eval().to("cuda")
        torch.manual_seed(27)
        cabeca = torch.nn.Linear(384, 10).to("cuda")
        antes = {"encoder": _sha_estado(encoder), "cabeca": _sha_estado(cabeca)}
        torch.cuda.reset_peak_memory_stats()
        casos = []
        for e in dados["exemplos"]:
            encoder.zero_grad(set_to_none=True)
            cabeca.zero_grad(set_to_none=True)
            # Supervisão não atravessa a chamada de inferência.
            logits = logits_por_tokens(encoder, cabeca, e["entrada"])
            perda = calcular_perda(logits, e["supervisao"]["ids_rotulos"])
            perda.backward()
            grad_encoder = [p.grad for p in encoder.parameters() if p.grad is not None]
            grad_cabeca = [p.grad for p in cabeca.parameters()]
            if (bool(grad_encoder) != liberar_encoder
                    or any(g is None or not torch.isfinite(g).all().item() for g in grad_cabeca)
                    or any(not torch.isfinite(g).all().item() for g in grad_encoder)
                    or not any(torch.count_nonzero(g).item() for g in grad_cabeca)
                    or (liberar_encoder and not any(torch.count_nonzero(g).item() for g in grad_encoder))):
                raise ValueError("gradientes ausentes, não finitos ou congelamento incorreto")
            casos.append({"id": e["id"], "perda": perda.item(),
                          "gradiente_encoder": bool(grad_encoder), "gradiente_cabeca": True})
            del logits, perda, grad_encoder, grad_cabeca
        depois = {"encoder": _sha_estado(encoder), "cabeca": _sha_estado(cabeca)}
        if antes != depois:
            raise ValueError("backward alterou pesos sem otimizador")
        resultados.append({"encoder_liberado": liberar_encoder, "casos": casos,
                           "hashes_iniciais": antes, "hashes_finais": depois,
                           "pico_alocado_mib": torch.cuda.max_memory_allocated() / 2**20})
        print(json.dumps({"encoder_liberado": liberar_encoder, "casos": len(casos), "pesos_intactos": True}), flush=True)
        del encoder, cabeca
        gc.collect()
        torch.cuda.empty_cache()
    if (resultados[0]["hashes_iniciais"] != resultados[1]["hashes_iniciais"]
            or [c["perda"] for c in resultados[0]["casos"]] != [c["perda"] for c in resultados[1]["casos"]]):
        raise ValueError("condições iniciais não são pareadas")
    conferir_fontes()
    if conferir_modelo(PASTA_MODELO) != hashes_modelo:
        raise ValueError("checkpoint mudou durante sonda")
    r = {"ok": True, "condicoes": resultados, "fontes_sha256": fontes,
         "checkpoint_sha256": hashes_modelo, "python": sys.version,
         "torch": torch.__version__, "gpu": torch.cuda.get_device_name(),
         "passos_otimizador": 0, "pesos_salvos": False, "aprendizado_medido": False,
         "treino_permitido": False, "autoriza_execucao": False, "autoriza_promocao": False}
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "resultado.json").open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparacao", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--destino", type=Path, required=True)
    args = parser.parse_args()
    executar(args.preparacao, args.sha256, args.destino)
