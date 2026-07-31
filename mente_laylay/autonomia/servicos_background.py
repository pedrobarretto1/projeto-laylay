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
        monotonic: Callable[[], float] = time.monotonic,
        registrar_falha: Callable[..., Any] | None = None,
        registrar_evento: Callable[..., Any] | None = None,
    ) -> None:
        self.thread_factory = thread_factory or _thread_factory_padrao
        self.log = log
        self.reiniciar_apos_falha = bool(reiniciar_apos_falha)
        self.atraso_reinicio_s = max(0.1, float(atraso_reinicio_s))
        self.sleep = sleep
        self.monotonic = monotonic
        self.registrar_falha = registrar_falha
        self.registrar_evento = registrar_evento
        self._lock = threading.RLock()
        self._iniciados: set[str] = set()
        self._threads: Dict[str, Any] = {}
        self._parar = threading.Event()
        self._encerrando = False

    def _relatar_falha(
        self, nome: str, codigo: str, erro: BaseException, *, fallback: str,
    ) -> None:
        if callable(self.registrar_falha):
            try:
                self.registrar_falha(
                    f"servico_{nome}", codigo, erro=erro,
                    classe="degradacao", impacto="servico", fallback=fallback,
                )
            except Exception as erro_diagnostico:
                self.log(
                    "[SERVICOS] observabilidade indisponível: "
                    f"{type(erro_diagnostico).__name__}"
                )

    def _registrar_evento(
        self,
        nome: str,
        estado: str,
        *,
        tentativa: int = 0,
        atraso_s: float = 0.0,
        fallback: str = "",
    ) -> None:
        if not callable(self.registrar_evento):
            return
        try:
            self.registrar_evento(
                nome,
                estado,
                tentativa=tentativa,
                atraso_s=atraso_s,
                fallback=fallback,
            )
        except Exception as erro_diagnostico:
            self.log(
                "[SERVICOS] ciclo de vida indisponível: "
                f"{type(erro_diagnostico).__name__}"
            )

    def _aguardar_reinicio(self, timeout_s: float) -> bool:
        """Mantém injeção de espera nos testes e é interrompível em produção."""
        if self.sleep is time.sleep:
            return self._parar.wait(max(0.0, float(timeout_s)))
        self.sleep(max(0.0, float(timeout_s)))
        return self._parar.is_set()

    @property
    def evento_parada(self) -> threading.Event:
        """Sinal compartilhado para os serviços cooperarem com o encerramento."""
        return self._parar

    def deve_parar(self) -> bool:
        return self._parar.is_set()

    def aguardar(self, timeout_s: float) -> bool:
        """Espera interrompível; retorna True quando o encerramento foi pedido."""
        return self._parar.wait(max(0.0, float(timeout_s)))

    def solicitar_encerramento(self) -> None:
        self._parar.set()

    def _executar_protegido(self, nome: str, target: Callable[[], Any]) -> None:
        falhas_consecutivas = 0
        tentativa = 1
        try:
            while not self._parar.is_set():
                self._registrar_evento(
                    nome,
                    "ativo" if tentativa == 1 else "reiniciando",
                    tentativa=tentativa,
                )
                try:
                    target()
                    self._registrar_evento(
                        nome,
                        "encerrado" if self._parar.is_set() else "finalizado",
                        tentativa=tentativa,
                    )
                    return
                except Exception as erro:
                    falhas_consecutivas += 1
                    havera_reinicio = self.reiniciar_apos_falha and not self._parar.is_set()
                    fallback = "reinicio_agendado" if havera_reinicio else "servico_indisponivel"
                    self.log(
                        f"[SERVICOS] {nome} encerrou com erro: {type(erro).__name__}"
                    )
                    self._registrar_evento(
                        nome, "queda", tentativa=tentativa, fallback=fallback,
                    )
                    self._relatar_falha(
                        nome, "queda_background", erro, fallback=fallback,
                    )
                    if not self.reiniciar_apos_falha or self._parar.is_set():
                        return
                    atraso = min(60.0, self.atraso_reinicio_s * (2 ** min(falhas_consecutivas - 1, 4)))
                    self._registrar_evento(
                        nome,
                        "reinicio_agendado",
                        tentativa=tentativa + 1,
                        atraso_s=atraso,
                        fallback="reinicio_automatico",
                    )
                    self.log(
                        f"[SERVICOS] reiniciando {nome} em {atraso:g}s."
                    )
                    if self._aguardar_reinicio(atraso):
                        return
                    tentativa += 1
        finally:
            with self._lock:
                self._iniciados.discard(nome)
                self._threads.pop(nome, None)

    def iniciar(self, nome: str, target: Callable[[], Any]) -> bool:
        nome_limpo = str(nome or "").strip()
        if not nome_limpo or not callable(target):
            return False

        with self._lock:
            if self._parar.is_set() or self._encerrando:
                self.log(f"[SERVICOS] {nome_limpo} ignorado durante o encerramento.")
                return False
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
        except Exception as erro:
            with self._lock:
                self._iniciados.discard(nome_limpo)
                self._threads.pop(nome_limpo, None)
            self._registrar_evento(
                nome_limpo,
                "falha_inicializacao",
                fallback="servico_indisponivel",
            )
            self._relatar_falha(
                nome_limpo,
                "falha_inicializacao",
                erro,
                fallback="servico_indisponivel",
            )
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
                self.log(
                    f"[SERVICOS] falha ao iniciar {nome_limpo}: "
                    f"{type(erro).__name__}"
                )
        return resultados

    def ativos(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._iniciados))

    def encerrar(self, timeout_s: float = 1.5) -> None:
        """Sinaliza encerramento e usa um único prazo para todas as threads.

        Um segundo Ctrl+C durante a espera apenas acelera a saída. Ele não deve
        escapar como traceback, pois o processo já está deliberadamente sendo
        encerrado.
        """
        self.solicitar_encerramento()
        with self._lock:
            if self._encerrando:
                return
            self._encerrando = True
            threads = list(self._threads.items())

        try:
            prazo = self.monotonic() + max(0.0, float(timeout_s))
            for _nome, thread in threads:
                join = getattr(thread, "join", None)
                if not callable(join) or thread is threading.current_thread():
                    continue
                restante = max(0.0, prazo - self.monotonic())
                if restante <= 0.0:
                    break
                try:
                    join(timeout=restante)
                except (RuntimeError, TypeError):
                    continue
            for nome, thread in threads:
                esta_viva = getattr(thread, "is_alive", None)
                if not callable(esta_viva):
                    continue
                try:
                    orfao = bool(esta_viva())
                except Exception:
                    orfao = False
                if not orfao:
                    continue
                self._registrar_evento(
                    nome,
                    "orfao",
                    fallback="encerramento_do_processo",
                )
                self._relatar_falha(
                    nome,
                    "servico_orfao",
                    TimeoutError("serviço excedeu o prazo de encerramento"),
                    fallback="encerramento_do_processo",
                )
        except KeyboardInterrupt:
            self.log("\n🛑 Encerramento acelerado por novo Ctrl+C.")


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
        # Os controles humanos entram antes dos serviços pesados. Assim Pedro
        # pode abrir o chat ou pausar a escuta durante o restante da partida.
        if callable(hotkeys):
            try:
                hotkeys()
            except Exception as erro:
                self.log(f"⚠️ [MAIN] Falha ao registrar hotkeys do modo chat: {erro}")
        resultados_threads = self.servicos.iniciar_varios(threads)
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
                except KeyboardInterrupt:
                    self.log("🛑 Encerramento acelerado por novo Ctrl+C.")
                except Exception as erro:
                    self.log(f"⚠️ [MAIN] Falha ao salvar memória no encerramento: {erro}")
        finally:
            try:
                self.servicos.encerrar()
            except KeyboardInterrupt:
                # Proteção final para um sinal que chegue antes de o próprio
                # gerenciador entrar no trecho protegido de espera.
                self.log("🛑 Encerramento acelerado por novo Ctrl+C.")


def criar_orquestrador_inicializacao(**kwargs: Any) -> OrquestradorInicializacao:
    return OrquestradorInicializacao(**kwargs)
