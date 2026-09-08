"""Provedor textual leve para conversar sem disputar a GPU com o jogo."""

from __future__ import annotations

import re
import threading
import time
from typing import Any, Callable, Mapping


def _mensagens_minimas(payload: Mapping[str, Any]) -> list[dict[str, str]]:
    """Preserva personalidade e fio recente sem enviar o retrato mental inteiro."""
    originais = [item for item in list(payload.get("messages") or []) if isinstance(item, dict)]
    sistemas = [item for item in originais if str(item.get("role") or "").casefold() == "system"]
    conversa = [item for item in originais if str(item.get("role") or "").casefold() != "system"]
    possui_evento_cognitivo = any(
        "EVENTO COGNITIVO ESTRUTURADO" in str(item.get("content") or "")
        for item in sistemas
    )
    resultado: list[dict[str, str]] = []
    if sistemas:
        partes_sistema = [str(sistemas[0].get("content") or "").strip()[:6000]]
        partes_sistema.extend(
            str(item.get("content") or "").strip()[:3000]
            for item in sistemas[1:][-2:]
            if str(item.get("content") or "").strip()
        )
        conteudo_sistema = "\n\n".join(parte for parte in partes_sistema if parte)
        if conteudo_sistema:
            resultado.append({"role": "system", "content": conteudo_sistema})
    for item in conversa[-6:]:
        papel = str(item.get("role") or "user").casefold()
        if papel not in {"user", "assistant"}:
            papel = "user"
        conteudo = re.sub(r"\s+", " ", str(item.get("content") or "")).strip()[:1400]
        if conteudo:
            resultado.append({"role": papel, "content": conteudo})
    if possui_evento_cognitivo:
        # A API da Groq exige uma consulta conversacional mesmo quando a origem
        # canônica é um evento de sistema. Esta ponte existe apenas no payload
        # efêmero do provedor: não entra no histórico e não concede autoridade.
        resultado.append({
            "role": "user",
            "content": (
                "SOLICITAÇÃO TÉCNICA INTERNA DO ORQUESTRADOR: gere a resposta "
                "ao EVENTO COGNITIVO ESTRUTURADO acima. Isto não é fala, pedido, "
                "confirmação ou autorização de Pedro; não execute ações. "
                "Responda somente no formato solicitado pelo sistema."
            ),
        })
    return resultado


class ConversaJogoRemotaRuntime:
    """Usa a credencial Groq já autorizada, com circuito de falha isolado."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        requests_post: Callable[..., Any],
        timeout_s: float = 8.0,
        cooldown_s: float = 45.0,
        clock: Callable[[], float] = time.monotonic,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.api_key = str(api_key or "").strip()
        self.model = str(model or "").strip()
        self.requests_post = requests_post
        self.timeout_s = max(3.0, float(timeout_s))
        self.cooldown_s = max(5.0, float(cooldown_s))
        self.clock = clock
        self.log = log
        self._lock = threading.Lock()
        self._indisponivel_ate = 0.0

    @property
    def disponivel(self) -> bool:
        return bool(self.api_key and self.model and self.clock() >= self._indisponivel_ate)

    def enviar(self, payload: Mapping[str, Any]) -> str:
        if not self.disponivel:
            return ""
        # Visão e conversa usam a mesma conta. Uma segunda conversa concorrente
        # cai imediatamente para o caminho local em vez de criar outra fila.
        if not self._lock.acquire(blocking=False):
            return ""
        inicio = time.perf_counter()
        try:
            mensagens = _mensagens_minimas(payload)
            if not mensagens:
                return ""
            try:
                limite = min(220, max(48, int(payload.get("max_tokens") or 160)))
            except (TypeError, ValueError):
                limite = 160
            resposta = self.requests_post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": mensagens,
                    "temperature": 0.65,
                    "top_p": 0.9,
                    "reasoning_effort": "none",
                    "max_completion_tokens": limite,
                },
                timeout=self.timeout_s,
            )
            status = int(getattr(resposta, "status_code", 200) or 200)
            if status >= 400:
                self._indisponivel_ate = self.clock() + (
                    300.0 if status in {401, 403} else self.cooldown_s
                )
                self.log(f"⚠️ [CONVERSA:JOGO] Groq HTTP {status}; usando rota local temporariamente.")
                return ""
            dados = resposta.json()
            texto = str(
                (((dados.get("choices") or [{}])[0].get("message") or {}).get("content"))
                or ""
            ).strip()
            texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.I | re.S).strip()
            if texto:
                self.log(
                    f"⚡ [CONVERSA:JOGO] resposta remota em "
                    f"{(time.perf_counter() - inicio) * 1000:.0f}ms"
                )
            return texto
        except Exception as erro:
            self._indisponivel_ate = self.clock() + self.cooldown_s
            self.log(
                f"⚠️ [CONVERSA:JOGO] {type(erro).__name__}; "
                "usando rota local temporariamente."
            )
            return ""
        finally:
            self._lock.release()


def criar_conversa_jogo_remota_runtime(**kwargs: Any) -> ConversaJogoRemotaRuntime:
    return ConversaJogoRemotaRuntime(**kwargs)
