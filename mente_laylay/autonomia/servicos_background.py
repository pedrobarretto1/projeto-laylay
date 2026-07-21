"""Ciclo de vida dos servicos em background da mente da Laylay."""

from __future__ import annotations

import threading
import time
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
        reiniciar_apos_falha: bool = False,
        atraso_reinicio_s: float = 5.0,
        sleep: Callable[[float], Any] = time.sleep,
    ) -> None:
        self.thread_factory = thread_factory or _thread_factory_padrao
        self.log = log
        self.reiniciar_apos_falha = bool(reiniciar_apos_falha)
        self.atraso_reinicio_s = max(0.1, float(atraso_reinicio_s))
        self.sleep = sleep
        self._lock = threading.RLock()
        self._iniciados: set[str] = set()
        self._threads: Dict[str, Any] = {}
        self._parar = threading.Event()

    def _executar_protegido(self, nome: str, target: Callable[[], Any]) -> None:
        falhas_consecutivas = 0
        try:
            while not self._parar.is_set():
                try:
                    target()
                    return
                except Exception as erro:
                    falhas_consecutivas += 1
                    self.log(f"[SERVICOS] {nome} encerrou com erro: {erro}")
                    if not self.reiniciar_apos_falha or self._parar.is_set():
                        return
                    atraso = min(60.0, self.atraso_reinicio_s * (2 ** min(falhas_consecutivas - 1, 4)))
                    self.log(
                        f"[SERVICOS] reiniciando {nome} em {atraso:g}s."
                    )
                    self.sleep(atraso)
        finally:
            with self._lock:
                self._iniciados.discard(nome)
                self._threads.pop(nome, None)

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
            with self._lock:
                self._threads[nome_limpo] = thread
            thread.start()
        except Exception:
            with self._lock:
                self._iniciados.discard(nome_limpo)
                self._threads.pop(nome_limpo, None)
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

    def encerrar(self, timeout_s: float = 1.5) -> None:
        """Sinaliza encerramento e espera brevemente pelos serviços cooperativos."""
        self._parar.set()
        with self._lock:
            threads = list(self._threads.values())
        for thread in threads:
            join = getattr(thread, "join", None)
            if callable(join) and thread is not threading.current_thread():
                try:
                    join(timeout=max(0.0, float(timeout_s)))
                except (RuntimeError, TypeError):
                    continue


def criar_gerenciador_servicos_background(**kwargs: Any) -> GerenciadorServicosBackground:
    return GerenciadorServicosBackground(**kwargs)


class OrquestradorInicializacao:
    """Executa a inicialização da mente em ordem e mantém falhas isoladas."""

    def __init__(
        self,
        *,
        servicos: GerenciadorServicosBackground,
        log: Callable[[str], None] = print,
        sleep: Callable[[float], Any] = time.sleep,
    ) -> None:
        self.servicos = servicos
        self.log = log
        self.sleep = sleep

    def executar_etapas(self, etapas: Mapping[str, Callable[[], Any]]) -> Dict[str, bool]:
        resultados: Dict[str, bool] = {}
        for descricao, target in dict(etapas or {}).items():
            try:
                target()
                resultados[descricao] = True
            except Exception as erro:
                resultados[descricao] = False
                self.log(f"⚠️ [MAIN] Falha ao {descricao}: {erro}")
        return resultados

    def iniciar(
        self,
        *,
        etapas: Mapping[str, Callable[[], Any]],
        threads: Mapping[str, Callable[[], Any]],
        hotkeys: Callable[[], Any] | None = None,
    ) -> Dict[str, Dict[str, bool]]:
        resultados_etapas = self.executar_etapas(etapas)
        resultados_threads = self.servicos.iniciar_varios(threads)
        if callable(hotkeys):
            try:
                hotkeys()
            except Exception as erro:
                self.log(f"⚠️ [MAIN] Falha ao registrar hotkeys do modo chat: {erro}")
        return {"etapas": resultados_etapas, "threads": resultados_threads}

    def manter_ativo(
        self,
        *,
        fala_pronta: str,
        ao_encerrar: Callable[[], Any] | None = None,
    ) -> None:
        if str(fala_pronta or "").strip():
            self.log(fala_pronta)
        try:
            while True:
                self.sleep(1)
        except KeyboardInterrupt:
            self.log("\n🛑 Encerrando Laylay por Ctrl+C...")
            if callable(ao_encerrar):
                try:
                    ao_encerrar()
                except Exception as erro:
                    self.log(f"⚠️ [MAIN] Falha ao salvar memória no encerramento: {erro}")
        finally:
            self.servicos.encerrar()


def criar_orquestrador_inicializacao(**kwargs: Any) -> OrquestradorInicializacao:
    return OrquestradorInicializacao(**kwargs)
