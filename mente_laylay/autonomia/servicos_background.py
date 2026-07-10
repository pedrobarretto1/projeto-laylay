"""Ciclo de vida dos servicos em background da mente da Laylay."""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, Mapping, Optional


def _thread_factory_padrao(*, target: Callable[[], Any], name: str):
    return threading.Thread(target=target, daemon=True, name=name)


class GerenciadorServicosBackground:
    """Inicia cada servico uma unica vez e isola falhas entre threads."""

    def __init__(
        self,
        *,
        thread_factory: Optional[Callable[..., Any]] = None,
        log: Callable[[str], None] = print,
    ) -> None:
        self.thread_factory = thread_factory or _thread_factory_padrao
        self.log = log
        self._lock = threading.RLock()
        self._iniciados: set[str] = set()

    def _executar_protegido(self, nome: str, target: Callable[[], Any]) -> None:
        try:
            target()
        except Exception as erro:
            self.log(f"[SERVICOS] {nome} encerrou com erro: {erro}")
        finally:
            with self._lock:
                self._iniciados.discard(nome)

    def iniciar(self, nome: str, target: Callable[[], Any]) -> bool:
        nome_limpo = str(nome or "").strip()
        if not nome_limpo or not callable(target):
            return False

        with self._lock:
            if nome_limpo in self._iniciados:
                self.log(f"[SERVICOS] {nome_limpo} ja estava iniciado.")
                return False
            self._iniciados.add(nome_limpo)

        try:
            thread = self.thread_factory(
                target=lambda: self._executar_protegido(nome_limpo, target),
                name=nome_limpo,
            )
            thread.start()
        except Exception:
            with self._lock:
                self._iniciados.discard(nome_limpo)
            raise

        self.log(f"[SERVICOS] {nome_limpo} conectado a mente.")
        return True

    def iniciar_varios(
        self,
        servicos: Mapping[str, Callable[[], Any]],
    ) -> Dict[str, bool]:
        resultados: Dict[str, bool] = {}
        for nome, target in dict(servicos or {}).items():
            nome_limpo = str(nome)
            try:
                resultados[nome_limpo] = self.iniciar(nome_limpo, target)
            except Exception as erro:
                resultados[nome_limpo] = False
                self.log(f"[SERVICOS] falha ao iniciar {nome_limpo}: {erro}")
        return resultados

    def ativos(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._iniciados))


def criar_gerenciador_servicos_background(**kwargs: Any) -> GerenciadorServicosBackground:
    return GerenciadorServicosBackground(**kwargs)
