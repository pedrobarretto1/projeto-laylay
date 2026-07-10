"""Controle unificado do modo chat da Laylay."""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict


class ModoChatRuntime:
    def __init__(
        self,
        *,
        estado_getter: Callable[[], Dict[str, Any]],
        estado_setter: Callable[[bool], None],
        messages_getter: Callable[[], Any],
        fala_confirmacao: Callable[..., str],
        gerar_abertura: Callable[[], str],
        falar: Callable[[str, str, int], Any],
        salvar_memoria: Callable[[], Any],
        log: Callable[[str], None] | None = None,
        time_fn: Callable[[], float] | None = None,
        debounce_s: float = 0.8,
    ) -> None:
        self.estado_getter = estado_getter
        self.estado_setter = estado_setter
        self.messages_getter = messages_getter
        self.fala_confirmacao = fala_confirmacao
        self.gerar_abertura = gerar_abertura
        self.falar = falar
        self.salvar_memoria = salvar_memoria
        self.log = log or print
        self.time_fn = time_fn or time.time
        self.debounce_s = float(debounce_s)
        self._ultimo_toggle_ts = 0.0
        self._lock = threading.RLock()

    def _estado_ativo(self) -> bool:
        try:
            estado = self.estado_getter() or {}
        except Exception:
            estado = {}
        if not isinstance(estado, dict):
            return False
        return bool(estado.get("modo_chat") or estado.get("conversa_ativa"))

    def _criar_fala(self, ativo: bool) -> str:
        if ativo:
            try:
                fallback = self.gerar_abertura()
            except Exception:
                fallback = "Modo chat ativado. Pode falar comigo sem eu sair distribuindo comando."
            return str(
                self.fala_confirmacao("chat_on", fallback=fallback) or fallback
            ).strip()
        fallback = "Modo chat desativado. Voltei pro modo ação."
        return str(
            self.fala_confirmacao("chat_off", fallback=fallback) or fallback
        ).strip()

    def definir(
        self,
        ativo: bool,
        *,
        origem: str = "desconhecida",
        texto_usuario: str = "",
    ) -> Dict[str, Any]:
        desejado = bool(ativo)
        with self._lock:
            agora = float(self.time_fn())
            estado_atual = self._estado_ativo()
            if (
                agora - self._ultimo_toggle_ts < self.debounce_s
                and desejado == estado_atual
            ):
                return {
                    "tratado": True,
                    "alterado": False,
                    "emitido": False,
                    "fala": "Modo chat já está no estado pedido.",
                }

            self._ultimo_toggle_ts = agora
            self.estado_setter(desejado)
            fala = self._criar_fala(desejado)
            texto = str(texto_usuario or "").strip()
            try:
                messages = self.messages_getter()
            except Exception:
                messages = None
            if texto and isinstance(messages, list):
                messages.append({"role": "user", "content": texto})
                messages.append({"role": "assistant", "content": fala})
            self.log(f"🗨️ [CHAT] {fala} | origem={origem}")
            self.falar(fala, "calma", 1)
            self.salvar_memoria()
            return {
                "tratado": True,
                "alterado": desejado != estado_atual,
                "emitido": True,
                "fala": fala,
            }

    def processar_texto(self, texto: str, *, origem: str = "texto") -> bool:
        entrada = str(texto or "").strip()
        normalizada = entrada.lower()
        ativar = {"modo chat", "ativar modo chat", "entrar no chat"}
        desativar = {"sair do chat", "desativar modo chat", "modo comandos"}
        if normalizada in ativar:
            self.definir(True, origem=origem, texto_usuario=entrada)
            return True
        if normalizada in desativar:
            self.definir(False, origem=origem, texto_usuario=entrada)
            return True
        return False


def criar_modo_chat_runtime(**kwargs: Any) -> ModoChatRuntime:
    return ModoChatRuntime(**kwargs)
