"""Interpretacao binaria de confirmacoes contextuais pela IA."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, Dict, Optional


def interpretar_confirmacao_llm(
    fala_usuario: str,
    sugestao: str,
    *,
    post_chat: Callable[[dict, dict], Any],
    api_key: str,
    model: str,
    http_referer: str,
    app_title: str,
) -> Optional[bool]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": http_referer,
        "X-Title": app_title,
    }
    fala = str(fala_usuario or "").strip()
    contexto = str(sugestao or "").strip()
    prompt = (
        f'O usuário disse: "{fala}". Com base no contexto de que eu sugeri "{contexto}", '
        'o usuário confirmou a ação? Responda apenas "SIM" ou "NAO".'
    )
    data = {
        "model": model,
        "messages": [{"role": "system", "content": prompt}],
        "max_tokens": 4,
        "temperature": 0.0,
    }
    try:
        response = post_chat(headers, data)
        response.raise_for_status()
        payload = response.json()
        resposta = str(payload["choices"][0]["message"]["content"] or "").strip().upper()
        if resposta.startswith("SIM"):
            return True
        if resposta.startswith("NAO") or resposta.startswith("NÃO"):
            return False
    except Exception:
        pass
    return None


def mesclar_intencao_confirmada(
    original_payload: dict,
    fala_usuario: str,
    *,
    post_chat: Callable[[dict, dict], Any],
    api_key: str,
    model: str,
    http_referer: str,
    app_title: str,
) -> dict:
    """Atualiza detalhes de uma sugestão já aceita sem perder o payload original."""
    original = original_payload if isinstance(original_payload, dict) else {}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": http_referer,
        "X-Title": app_title,
    }
    prompt = (
        f"Sugestão original: {json.dumps(original, ensure_ascii=False)}. "
        f'Fala do usuário: "{fala_usuario}". '
        "O usuário aceitou a estrutura, mas mudou algum detalhe? "
        'Corrija erros de fala/fonética (ex: "Tin Maia" -> "Tim Maia"). '
        "Retorne APENAS o novo JSON do comando mantendo o que ele aceitou e trocando o que ele pediu para mudar. "
        "Campos permitidos: action, clean_tabs, music_query, image_topic, image_action."
    )
    data = {
        "model": model,
        "messages": [{"role": "system", "content": prompt}],
        "max_tokens": 120,
        "temperature": 0.0,
    }
    try:
        response = post_chat(headers, data)
        response.raise_for_status()
        payload = response.json()
        raw = str(payload["choices"][0]["message"]["content"] or "").strip()
        encontrado = re.search(r"\{[\s\S]*\}", raw)
        if encontrado:
            raw = encontrado.group(0)
        merged = json.loads(raw)
        return merged if isinstance(merged, dict) else original
    except Exception:
        return original


class ConfirmacaoLLMRuntime:
    """Liga confirmação e correção de intenção à configuração LLM viva."""

    def __init__(self, *, namespace_getter: Callable[[], Dict[str, Any]]) -> None:
        self.namespace_getter = namespace_getter

    def _deps(self) -> Dict[str, Any]:
        ns = self.namespace_getter() or {}
        return {
            "post_chat": ns["post_chat"],
            "api_key": os.environ.get("OPENROUTER_API_KEY") or ns.get("api_key", ""),
            "model": ns["model"],
            "http_referer": ns.get("http_referer", ""),
            "app_title": ns.get("app_title", ""),
        }

    def interpretar(self, fala_usuario: str, sugestao: str) -> Optional[bool]:
        return interpretar_confirmacao_llm(fala_usuario, sugestao, **self._deps())

    def mesclar(self, original_payload: dict, fala_usuario: str) -> dict:
        return mesclar_intencao_confirmada(
            original_payload,
            fala_usuario,
            **self._deps(),
        )


def criar_confirmacao_llm_runtime(**kwargs: Any) -> ConfirmacaoLLMRuntime:
    return ConfirmacaoLLMRuntime(**kwargs)
