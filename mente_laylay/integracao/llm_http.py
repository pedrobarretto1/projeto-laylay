"""Cliente HTTP compatível para LLM remoto/local usado pela Laylay."""

from __future__ import annotations

import time
from typing import Any, Callable


class RespostaLLMFallback:
    def __init__(self, content: str, status_code: int = 200):
        self.status_code = status_code
        self._content = str(content or "")
        self.text = self._content

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": self._content,
                    }
                }
            ]
        }


def endpoint_eh_local(base_url: str) -> bool:
    base = str(base_url or "").lower()
    return "localhost" in base or "127.0.0.1" in base or "0.0.0.0" in base


def timeout_padrao(base_url: str, local_timeout: int, remote_timeout: int) -> int:
    return int(local_timeout if endpoint_eh_local(base_url) else remote_timeout)


def conteudo_fallback_llm_local(data: dict) -> str:
    mensagens = data.get("messages") if isinstance(data, dict) else []
    texto = " ".join(str((m or {}).get("content") or "")[:500] for m in mensagens if isinstance(m, dict))
    baixo = texto.lower()
    if "intent" in baixo and "json" in baixo:
        return '{"intent":"NONE","params":{}}'
    if "responda apenas json" in baixo or "json válido" in baixo or "json valido" in baixo:
        return "{}"
    if int((data or {}).get("max_tokens") or 0) <= 5:
        return "NAO"
    return "Me perdi um pouco nessa resposta, Pedro. Segura um segundo e me fala de outro jeito."


def compactar_payload_llm_local(data: dict) -> dict:
    novo = dict(data or {})
    novo.pop("response_format", None)
    novo.pop("tools", None)
    novo.pop("tool_choice", None)
    novo["stream"] = False
    mensagens = []
    for msg in list(novo.get("messages") or []):
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role") or "user").strip().lower()
        if role not in {"system", "user", "assistant"}:
            role = "user"
        content = str(msg.get("content") or "")
        if not content.strip():
            continue
        limite = 2500 if role == "system" else 1200
        mensagens.append({"role": role, "content": content[:limite]})
    if not mensagens:
        mensagens = [{"role": "user", "content": "Responda em português, curto e natural."}]
    if len(mensagens) > 6:
        sistemas = [m for m in mensagens if m["role"] == "system"][:1]
        mensagens = sistemas + [m for m in mensagens if m["role"] != "system"][-5:]
    novo["messages"] = mensagens
    try:
        novo["max_tokens"] = min(int(novo.get("max_tokens") or 512), 384)
    except Exception:
        novo["max_tokens"] = 384
    return novo


def payload_precisa_compactar_llm_local(data: dict) -> bool:
    mensagens = data.get("messages") if isinstance(data, dict) else []
    if not isinstance(mensagens, list):
        return False
    total_chars = 0
    for msg in mensagens:
        if isinstance(msg, dict):
            total_chars += len(str(msg.get("content") or ""))
    try:
        max_tokens = int((data or {}).get("max_tokens") or 0)
    except Exception:
        max_tokens = 0
    # Qwen 7B local costuma estar em 4096 tokens; compactar antes evita 400.
    return total_chars > 9500 or max_tokens > 640


def post_chat_llm(
    headers: dict,
    data: dict,
    *,
    base_url: str,
    local_timeout: int,
    remote_timeout: int,
    bad_request_until: float,
    lock: Any,
    requests_post: Callable[..., Any],
    print_fn: Callable[..., Any],
    timeout: int | None = None,
) -> tuple[Any, float]:
    """Serializa chamadas locais e recupera 400 com payload compacto."""
    url = f"{base_url}/chat/completions"
    timeout = timeout or timeout_padrao(base_url, local_timeout, remote_timeout)
    local = endpoint_eh_local(base_url)

    if local and time.time() < float(bad_request_until or 0.0):
        return RespostaLLMFallback(conteudo_fallback_llm_local(data)), float(bad_request_until or 0.0)

    def _post(payload: dict):
        return requests_post(url, headers=headers, json=payload, timeout=timeout)

    if not local:
        return _post(data), float(bad_request_until or 0.0)

    pegou_lock = lock.acquire(blocking=False)
    if not pegou_lock:
        print_fn("[IA] Modelo local ocupado; aguardando a chamada anterior terminar...")
        lock.acquire()
    try:
        payload_envio = compactar_payload_llm_local(data) if payload_precisa_compactar_llm_local(data) else data
        resp = _post(payload_envio)
        if resp.status_code == 400:
            print_fn(f"⚠️ [IA] 400 do modelo local. Corpo: {str(resp.text or '')[:500]}")
            retry_data = compactar_payload_llm_local(payload_envio)
            resp_retry = _post(retry_data)
            if resp_retry.status_code != 400:
                print_fn("✓ [IA] Requisição local recuperada com payload compacto.")
                return resp_retry, float(bad_request_until or 0.0)
            print_fn(f"⚠️ [IA] 400 persistiu no retry compacto. Corpo: {str(resp_retry.text or '')[:500]}")
            novo_bad_request_until = time.time() + 20.0
            return RespostaLLMFallback(conteudo_fallback_llm_local(data)), novo_bad_request_until
        return resp, float(bad_request_until or 0.0)
    finally:
        lock.release()
