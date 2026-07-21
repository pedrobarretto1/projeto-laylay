"""Resolução segura de nomes livres de cores para o subsistema IoT."""

from __future__ import annotations

import json
import re
from typing import Any, Callable


def _rgb_validado(valor: Any) -> tuple[int, int, int] | None:
    if isinstance(valor, str):
        hexadecimal = re.fullmatch(r"\s*#?([0-9a-fA-F]{6})\s*", valor)
        if hexadecimal:
            codigo = hexadecimal.group(1)
            return tuple(int(codigo[indice:indice + 2], 16) for indice in (0, 2, 4))
        return None
    if not isinstance(valor, (list, tuple)) or len(valor) != 3:
        return None
    try:
        rgb = tuple(int(canal) for canal in valor)
    except (TypeError, ValueError):
        return None
    return rgb if all(0 <= canal <= 255 for canal in rgb) else None


def extrair_rgb_resolvido(resposta: Any) -> tuple[int, int, int] | None:
    """Aceita apenas JSON/RGB/HEX bem formado; texto livre nunca vira comando."""
    if isinstance(resposta, dict):
        return _rgb_validado(resposta.get("rgb")) or _rgb_validado(resposta.get("hex"))
    rgb_direto = _rgb_validado(resposta)
    if rgb_direto:
        return rgb_direto
    texto = str(resposta or "").strip()
    bloco = re.search(r"\{[^{}]*\}", texto, re.DOTALL)
    if bloco:
        try:
            dados = json.loads(bloco.group(0))
        except (json.JSONDecodeError, TypeError):
            dados = None
        if isinstance(dados, dict):
            rgb = _rgb_validado(dados.get("rgb")) or _rgb_validado(dados.get("hex"))
            if rgb:
                return rgb
    hexadecimal = re.search(r"(?<![0-9a-fA-F])#([0-9a-fA-F]{6})(?![0-9a-fA-F])", texto)
    return _rgb_validado(hexadecimal.group(1)) if hexadecimal else None


def resolver_cor_por_ia(
    nome: str,
    *,
    enviar_mensagem: Callable[..., str],
    log: Callable[..., Any] = print,
) -> dict[str, Any] | None:
    """Consulta o modelo somente para converter um nome de cor em RGB."""
    nome_limpo = re.sub(r"\s+", " ", str(nome or "").strip())[:80]
    if not nome_limpo:
        return None
    log(f"🎨 [IOT:COR] pesquisando código RGB de '{nome_limpo}'")
    mensagens = [
        {
            "role": "system",
            "content": (
                "Converta nomes de cores em português para uma representação RGB convencional. "
                "Responda somente JSON no formato {\"rgb\":[0,0,0]}. "
                "Cada canal deve ser um inteiro de 0 a 255. Não execute ações e não explique."
            ),
        },
        {"role": "user", "content": f"Cor: {nome_limpo}"},
    ]
    try:
        resposta = enviar_mensagem(
            mensagens,
            _com_tools=False,
            max_tokens=60,
            modo_rapido=True,
            timeout=12,
        )
    except Exception as exc:
        log(f"⚠️ [IOT:COR] pesquisa falhou: {exc}")
        return None
    rgb = extrair_rgb_resolvido(resposta)
    if rgb is None:
        log(f"⚠️ [IOT:COR] resposta sem RGB válido para '{nome_limpo}'")
        return None
    log(f"🎨 [IOT:COR] '{nome_limpo}' resolvida como RGB {rgb}")
    return {"nome": nome_limpo, "rgb": rgb, "fonte": "pesquisa_ia"}
