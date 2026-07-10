"""Estado compartilhado da percepcao de abas do navegador."""

from __future__ import annotations

import threading
from typing import Any, Dict


class ChromeEstadoRuntime:
    """Mantem uma unica fonte de verdade para o estado observado das abas."""

    def __init__(self, *, titulo_inicial: str = "", url_inicial: str = "") -> None:
        self._lock = threading.RLock()
        self._aba_titulo_atual = str(titulo_inicial or "")
        self._aba_url_atual = str(url_inicial or "")
        self._aba_anterior_id: Any = None
        self._aba_historico: list[Any] = []
        self._tab_last_seen: Dict[str, Dict[str, Any]] = {}

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "aba_titulo_atual": self._aba_titulo_atual,
                "aba_url_atual": self._aba_url_atual,
                "aba_anterior_id": self._aba_anterior_id,
                "aba_historico": list(self._aba_historico),
                "_tab_last_seen": {
                    url: dict(dados) if isinstance(dados, dict) else {}
                    for url, dados in self._tab_last_seen.items()
                },
            }

    def contexto_handler(self, extras: Dict[str, Any] | None = None) -> Dict[str, Any]:
        contexto = self.snapshot()
        if isinstance(extras, dict):
            contexto.update(extras)
        return contexto

    def aplicar_updates(self, updates: Dict[str, Any] | None) -> None:
        if not isinstance(updates, dict):
            return
        with self._lock:
            if "aba_titulo_atual" in updates:
                self._aba_titulo_atual = str(updates.get("aba_titulo_atual") or "")
            if "aba_url_atual" in updates:
                self._aba_url_atual = str(updates.get("aba_url_atual") or "")
            if "aba_anterior_id" in updates:
                self._aba_anterior_id = updates.get("aba_anterior_id")
            if "aba_historico" in updates:
                self._aba_historico = list(updates.get("aba_historico") or [])
            if "_tab_last_seen" in updates:
                recebido = updates.get("_tab_last_seen") or {}
                if isinstance(recebido, dict):
                    self._tab_last_seen = {
                        str(url): dict(dados) if isinstance(dados, dict) else {}
                        for url, dados in recebido.items()
                    }

    @property
    def aba_titulo_atual(self) -> str:
        with self._lock:
            return self._aba_titulo_atual

    @property
    def aba_url_atual(self) -> str:
        with self._lock:
            return self._aba_url_atual
