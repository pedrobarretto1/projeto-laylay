"""Agregação diferenciável e perda por token literal do piloto offline.

Não contém otimizador, leitura de corpus, autorização de fit ou persistência.
O mapa vem da preparação canônica; gold só entra depois dos logits.
"""
from __future__ import annotations

import math
import torch
from torch import Tensor


def agregar_tokens(ocultos: Tensor, mapa: list[dict]) -> Tensor:
    """Média por interseção e L2, preservando o grafo de autograd."""
    if ocultos.ndim != 2 or ocultos.shape[1] != 384 or not ocultos.is_floating_point():
        raise ValueError("estados devem ter dimensão subtokens x 384")
    if not torch.isfinite(ocultos).all().item() or not mapa:
        raise ValueError("estados não finitos ou mapa vazio")
    saida = []
    for token in mapa:
        indices, pesos = token["indices"], token["pesos"]
        if (not indices or len(indices) != len(pesos) or len(set(indices)) != len(indices)
                or any(type(i) is not int or not 0 <= i < len(ocultos) for i in indices)
                or any(type(p) not in (int, float) or not math.isfinite(p) or p <= 0 for p in pesos)
                or not math.isclose(sum(pesos), 1.0, rel_tol=1e-6, abs_tol=1e-7)):
            raise ValueError("mapa de agregação inválido")
        ponderados = ocultos[indices] * ocultos.new_tensor(pesos).unsqueeze(1)
        media = ponderados.sum(dim=0)
        norma = torch.linalg.vector_norm(media)
        if not torch.isfinite(norma).item() or norma.item() < 1e-9:
            raise ValueError("vetor agregado sem norma válida")
        saida.append(media / norma)
    return torch.stack(saida)


def logits_por_tokens(encoder: torch.nn.Module, cabeca: torch.nn.Module, entrada: dict) -> Tensor:
    """Inferência recebe apenas representação do texto, nunca supervisão."""
    campos = {"texto", "encoder", "offsets", "especiais", "mapa_tokens", "agregacao"}
    if set(entrada) != campos or set(entrada["encoder"]) != {"input_ids", "attention_mask", "token_type_ids"}:
        raise ValueError("entrada contém campos desconhecidos")
    dispositivo = next(encoder.parameters()).device
    tensores = {k: torch.tensor([v], dtype=torch.long, device=dispositivo)
                for k, v in entrada["encoder"].items()}
    ocultos = encoder(**tensores).last_hidden_state[0]
    return cabeca(agregar_tokens(ocultos, entrada["mapa_tokens"]))


def calcular_perda(logits: Tensor, ids_rotulos: list[int], *, numero_classes: int = 10) -> Tensor:
    """CE média por token literal, incluindo ausente; sem peso/limiar ajustado."""
    if (logits.ndim != 2 or logits.shape != (len(ids_rotulos), numero_classes)
            or not ids_rotulos or not logits.is_floating_point()
            or not torch.isfinite(logits).all().item()
            or any(type(r) is not int or not 0 <= r < numero_classes for r in ids_rotulos)):
        raise ValueError("logits ou rótulos incompatíveis")
    rotulos = torch.tensor(ids_rotulos, dtype=torch.long, device=logits.device)
    perda = torch.nn.functional.cross_entropy(logits, rotulos)
    if not torch.isfinite(perda).item():
        raise ValueError("perda não finita")
    return perda
