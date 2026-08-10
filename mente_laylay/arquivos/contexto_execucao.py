"""Resolução de caminhos e referências contextuais para ações de arquivos."""

from __future__ import annotations

import os
from typing import Any, Dict

from mente_laylay.integracao.registro_mutacoes_arquivos import PortaArquivosMutacao


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def registrar_arquivo(ctx: Dict[str, Any], alvo: str, tipo: str = "arquivos") -> None:
    registrar = _get(ctx, "registrar_contexto_arquivo")
    if callable(registrar):
        try:
            registrar(alvo, tipo)
        except Exception:
            pass


def resolver_caminho_local(
    ctx: Dict[str, Any], valor: str,
    arquivos_mutacao: PortaArquivosMutacao | None = None,
) -> str:
    bruto = str(valor or "").strip()
    if not bruto:
        return ""
    resolver = getattr(arquivos_mutacao, "resolver_caminho", None)
    if not callable(resolver):
        resolver = _get(ctx, "resolver_caminho")
    if callable(resolver):
        try:
            return str(resolver(bruto) or "").strip()
        except Exception:
            return bruto
    return bruto


def item_local_existe(
    ctx: Dict[str, Any], valor: str, tipo: str = "",
    arquivos_mutacao: PortaArquivosMutacao | None = None,
) -> bool:
    caminho = resolver_caminho_local(ctx, valor, arquivos_mutacao)
    if not caminho:
        return False
    try:
        if "arquivo" in str(tipo or "").lower():
            return os.path.isfile(caminho)
        if "pasta" in str(tipo or "").lower():
            return os.path.isdir(caminho)
        return os.path.exists(caminho)
    except Exception:
        return False


def resolver_referencia_arquivo_contextual(
    ctx: Dict[str, Any], alvo_ref: str, tipo_ref: str = ""
) -> str:
    ref = str(alvo_ref or "").strip()
    ref_norm = ref.lower()
    tipo_norm = str(tipo_ref or "").strip().lower()
    referencias = {
        "ela", "ele", "isso", "essa", "esse", "essa pasta", "esse arquivo",
    }
    if ref_norm not in referencias:
        return ref

    obter_pasta = _get(ctx, "ultima_pasta_contextual")
    obter_arquivo = _get(ctx, "ultimo_arquivo_contextual")
    obter_estrutura = _get(ctx, "estrutura_arquivo_recente")
    ultima_pasta = (
        str(obter_pasta() or "").strip() if callable(obter_pasta) else ""
    )
    ultimo_arquivo = (
        str(obter_arquivo() or "").strip() if callable(obter_arquivo) else ""
    )
    estrutura: Any = {}
    if callable(obter_estrutura):
        try:
            estrutura = obter_estrutura() or {}
        except Exception:
            estrutura = {}
    if not isinstance(estrutura, dict):
        estrutura = {}
    estrutura_caminho = str(estrutura.get("caminho") or "").strip()
    estrutura_tipo = str(estrutura.get("tipo") or "").strip().casefold()
    estrutura_pasta = str(
        estrutura.get("nome")
        or estrutura.get("pasta")
        or estrutura.get("alvo")
        or ""
    ).strip()
    estrutura_arquivo = str(
        estrutura.get("arquivo_nome")
        or estrutura.get("nome_arquivo")
        or estrutura.get("arquivo")
        or ""
    ).strip()
    if (
        estrutura_arquivo
        and "." not in estrutura_arquivo
        and str(estrutura.get("tipo_arquivo") or "").strip().casefold()
        in {"texto", "txt", "arquivo de texto"}
    ):
        estrutura_arquivo = f"{estrutura_arquivo}.txt"

    ultimo_alvo = str(_get(ctx, "ultimo_alvo", "") or "").strip()
    alvo_mental_existe = bool(
        ultimo_alvo and item_local_existe(ctx, ultimo_alvo)
    )
    estrutura_existe = bool(
        estrutura_caminho
        and item_local_existe(ctx, estrutura_caminho, estrutura_tipo)
    )
    if "pasta" in tipo_norm or ref_norm in {"ela", "essa", "essa pasta", "isso"}:
        return (
            (estrutura_caminho if estrutura_tipo == "pasta" and estrutura_existe else "")
            or ultima_pasta
            or estrutura_pasta
            or (ultimo_alvo if alvo_mental_existe else "")
            or ultimo_arquivo
            or estrutura_arquivo
            or ref
        )
    if "arquivo" in tipo_norm or ref_norm in {"ele", "esse", "esse arquivo"}:
        return (
            (estrutura_caminho if estrutura_tipo == "arquivo" and estrutura_existe else "")
            or ultimo_arquivo
            or estrutura_arquivo
            or (ultimo_alvo if alvo_mental_existe else "")
            or ultima_pasta
            or estrutura_pasta
            or ref
        )
    if ultimo_alvo and item_local_existe(ctx, ultimo_alvo):
        return ultimo_alvo
    if estrutura_caminho and item_local_existe(ctx, estrutura_caminho, estrutura_tipo):
        return estrutura_caminho
    foco_vivo = _get(ctx, "foco_vivo", {}) or {}
    alvo_foco = str((foco_vivo or {}).get("alvo") or "").strip()
    if alvo_foco and item_local_existe(ctx, alvo_foco):
        return alvo_foco
    if ultimo_arquivo and item_local_existe(ctx, ultimo_arquivo, "arquivo"):
        return ultimo_arquivo
    if ultima_pasta and item_local_existe(ctx, ultima_pasta, "pasta"):
        return ultima_pasta
    return ultima_pasta or estrutura_pasta or ultimo_arquivo or estrutura_arquivo or ref
