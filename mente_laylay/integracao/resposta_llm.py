"""Interpretacao da resposta bem-sucedida do modelo da Laylay."""

from __future__ import annotations

import json
from typing import Any, Callable


def interpretar_payload_llm(payload: dict, *, log: Callable[[str], Any] = print) -> str:
    escolha = payload["choices"][0]
    mensagem = escolha["message"]
    tool_calls = mensagem.get("tool_calls") or []
    if tool_calls:
        chamada = tool_calls[0]
        funcao = chamada.get("function", {})
        nome_funcao = funcao.get("name", "")
        argumentos_brutos = funcao.get("arguments", "{}")
        try:
            argumentos = json.loads(argumentos_brutos)
        except Exception:
            argumentos = {}
        fala = str(argumentos.get("fala") or "").strip()
        comandos = argumentos.get("comandos") or []
        log(f"[TOOLS] Function Call recebida: '{nome_funcao}' | fala={fala[:60]} | cmds={len(comandos)}")
        return json.dumps({"fala": fala, "comandos": comandos}, ensure_ascii=False)
    return mensagem.get("content") or ""
