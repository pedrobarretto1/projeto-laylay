"""Cliente HTTP compatível para LLM remoto/local usado pela Laylay."""

from __future__ import annotations

import time
import threading
from typing import Any, Callable

import requests

from mente_laylay.cognicao.conversa_sobre_capacidades import resposta_conversa_sobre_capacidade


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
    ultima_usuario = ""
    for mensagem in reversed(list(mensagens or [])):
        if isinstance(mensagem, dict) and str(mensagem.get("role") or "").lower() == "user":
            ultima_usuario = str(mensagem.get("content") or "").strip()
            break
    resposta_capacidade = resposta_conversa_sobre_capacidade(ultima_usuario)
    if resposta_capacidade:
        return resposta_capacidade
    usuario_baixo = ultima_usuario.lower()
    if any(p in usuario_baixo for p in ("música", "musica", "playlist", "som", "faixa")):
        return "Peguei que o assunto é música, mas meu modelo travou nessa resposta. Me dá o estilo ou artista e eu continuo exatamente desse ponto."
    return "Me perdi um pouco nessa resposta, Pedro. Segura um segundo e me fala de outro jeito."


def conteudo_fallback_modo_jogo(data: dict) -> str:
    """Mantém contratos JSON válidos sem acordar o modelo durante uma partida."""
    mensagens = data.get("messages") if isinstance(data, dict) else []
    texto = " ".join(str((m or {}).get("content") or "")[:500] for m in mensagens if isinstance(m, dict))
    baixo = texto.casefold()
    if "intent" in baixo and "json" in baixo:
        return '{"intent":"NONE","params":{}}'
    if "responda apenas json" in baixo or "json válido" in baixo or "json valido" in baixo:
        return "{}"
    try:
        if int((data or {}).get("max_tokens") or 0) <= 5:
            return "NAO"
    except (TypeError, ValueError):
        pass
    return "Tô poupando a placa enquanto você joga. Os comandos rápidos continuam comigo."


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
        espera_lock = min(5.0, max(0.1, float(timeout or 5.0)))
        print_fn(f"[IA] Modelo local ocupado; aguardando no máximo {espera_lock:.1f}s...")
        pegou_lock = lock.acquire(timeout=espera_lock)
        if not pegou_lock:
            print_fn("⚠️ [IA] Modelo local continuou ocupado; chamada liberada sem bloquear o fluxo.")
            return RespostaLLMFallback(
                "Meu modelo local está ocupado com outra tarefa agora. Tenta novamente em alguns segundos."
            ), float(bad_request_until or 0.0)
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
        if resp.status_code >= 500:
            print_fn(f"⚠️ [IA] {resp.status_code} temporário do modelo local; usando resposta contextual.")
            novo_bad_request_until = time.time() + 10.0
            return RespostaLLMFallback(conteudo_fallback_llm_local(data)), novo_bad_request_until
        return resp, float(bad_request_until or 0.0)
    finally:
        if pegou_lock:
            lock.release()


class LLMHttpRuntime:
    """Mantém configuração e estado transitório do transporte HTTP da LLM."""

    def __init__(
        self,
        *,
        base_url: str,
        local_timeout: int,
        remote_timeout: int,
        requests_post: Callable[..., Any],
        print_fn: Callable[..., Any] = print,
        ao_finalizar_conversa_modo_jogo: Callable[[], Any] | None = None,
    ) -> None:
        self.base_url = str(base_url or "").rstrip("/")
        self.local_timeout = int(local_timeout)
        self.remote_timeout = int(remote_timeout)
        self.requests_post = requests_post
        self.print_fn = print_fn
        self.ao_finalizar_conversa_modo_jogo = ao_finalizar_conversa_modo_jogo
        self._lock = threading.RLock()
        self._bad_request_until = 0.0
        self._modo_jogo_ativo = False

    @property
    def bad_request_until(self) -> float:
        return self._bad_request_until

    def endpoint_eh_local(self) -> bool:
        return endpoint_eh_local(self.base_url)

    @property
    def modo_jogo_ativo(self) -> bool:
        with self._lock:
            return self._modo_jogo_ativo

    def definir_modo_jogo(self, ativo: bool) -> None:
        with self._lock:
            self._modo_jogo_ativo = bool(ativo)

    def post(self, headers: dict, data: dict, timeout: int | None = None):
        dados_envio = dict(data or {})
        permitir_conversa_jogo = bool(dados_envio.pop("_laylay_conversa_modo_jogo", False))
        local_em_jogo = self.endpoint_eh_local() and self.modo_jogo_ativo
        if local_em_jogo and not permitir_conversa_jogo:
            return RespostaLLMFallback(conteudo_fallback_modo_jogo(dados_envio))

        if local_em_jogo:
            # A resposta principal pode acordar o modelo uma única vez, usando
            # menos contexto e menos tokens para reduzir o impacto na partida.
            dados_envio = compactar_payload_llm_local(dados_envio)
            try:
                dados_envio["max_tokens"] = min(int(dados_envio.get("max_tokens") or 256), 256)
            except (TypeError, ValueError):
                dados_envio["max_tokens"] = 256
            self.print_fn("🎮 [MODO JOGO] conversa solicitada; IA local acordada só para esta resposta.")

        try:
            resposta, novo_limite = post_chat_llm(
                headers,
                dados_envio,
                base_url=self.base_url,
                local_timeout=self.local_timeout,
                remote_timeout=self.remote_timeout,
                bad_request_until=self._bad_request_until,
                lock=self._lock,
                requests_post=self.requests_post,
                print_fn=self.print_fn,
                timeout=timeout,
            )
            self._bad_request_until = novo_limite
            return resposta
        finally:
            if local_em_jogo and callable(self.ao_finalizar_conversa_modo_jogo):
                try:
                    self.ao_finalizar_conversa_modo_jogo()
                except Exception as erro:
                    self.print_fn(f"⚠️ [MODO JOGO] não consegui descarregar a IA local: {erro}")


def criar_llm_http_runtime(**kwargs: Any) -> LLMHttpRuntime:
    return LLMHttpRuntime(**kwargs)


def executar_chat_llm(
    data: dict,
    *,
    post_chat: Callable[[dict, dict], Any],
    interpretar_payload: Callable[[dict], str],
    api_key: str,
    http_referer: str,
    app_title: str,
    endpoint_local: bool,
    timeout: int | None = None,
    log: Callable[[str], Any] = print,
) -> str:
    """Executa uma chamada preparada e converte rede/payload em fala."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": http_referer,
        "X-Title": app_title,
    }
    try:
        response = post_chat(headers, data, timeout=timeout) if timeout is not None else post_chat(headers, data)
        if response.status_code == 401:
            log("Erro 401 (Unauthorized) no OpenRouter.")
            return "Pedro, cheque sua chave do OpenRouter."
        response.raise_for_status()
        payload = response.json()
        return interpretar_payload(payload)
    except requests.exceptions.ReadTimeout as erro:
        log(f"Timeout na LLM local/API: {erro}")
        if endpoint_local:
            return "Meu modelo local demorou demais pra responder agora. O Ollama pode estar carregando ou ocupado; tenta de novo em alguns segundos."
        return "A inteligência artificial demorou demais pra responder agora. Tenta de novo em alguns segundos."
    except requests.exceptions.RequestException as erro:
        log(f"Erro na API: {erro}")
        return "Minha conexão com a parte da IA falhou agora. Tenta de novo em instantes."
