"""Proteção contra repetição recente de comandos."""

from __future__ import annotations

import re
import time
from typing import Dict, List


def normalizar_chave_comando(acao: str, alvo: str) -> str:
    alvo_norm = re.sub(r"\s+", " ", str(alvo or "").strip().lower())
    return f"{str(acao or '').strip().lower()}|{alvo_norm}"


def comando_repetido_recentemente(historico: List[Dict[str, float]], acao: str, alvo: str, janela_s: float = 18.0) -> bool:
    acao_norm = str(acao or "").strip().lower()
    if acao_norm not in {"open_url", "youtube_play", "tocar_playlist", "youtube_search"}:
        return False
    chave = normalizar_chave_comando(acao_norm, alvo)
    agora = time.time()
    recentes = [
        item for item in historico
        if agora - float(item.get("ts", 0.0)) <= janela_s
    ]
    historico[:] = recentes
    return any(item.get("chave") == chave for item in recentes)


def registrar_comando_executado(historico: List[Dict[str, float]], acao: str, alvo: str) -> None:
    chave = normalizar_chave_comando(acao, alvo)
    historico.append({"chave": chave, "ts": time.time()})
    if len(historico) > 30:
        del historico[:-30]
