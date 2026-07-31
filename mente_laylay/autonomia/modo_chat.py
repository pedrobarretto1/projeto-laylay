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
        iniciar_sessao: Callable[[str, bool], Any] | None = None,
        encerrar_sessao: Callable[[str, bool], Any] | None = None,
        deve_emitir_fala: Callable[[bool], bool] | None = None,
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
        self.iniciar_sessao = iniciar_sessao
        self.encerrar_sessao = encerrar_sessao
        self.deve_emitir_fala = deve_emitir_fala
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
                fala_dinamica = str(self.gerar_abertura() or "").strip()
            except Exception:
                fala_dinamica = ""
            if fala_dinamica:
                return fala_dinamica
            fallback = "Pode falar comigo. Tô aqui."
            return str(self.fala_confirmacao("chat_on", fallback=fallback) or fallback).strip()
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
            if desejado and not estado_atual and callable(self.iniciar_sessao):
                self.iniciar_sessao("ativacao_chat", True)
            self.estado_setter(desejado)
            fala = self._criar_fala(desejado)
            emitir_fala = True
            if callable(self.deve_emitir_fala):
                try:
                    emitir_fala = bool(self.deve_emitir_fala(desejado))
                except Exception:
                    emitir_fala = True
            texto = str(texto_usuario or "").strip()
            try:
                messages = self.messages_getter()
            except Exception:
                messages = None
            if texto and isinstance(messages, list) and emitir_fala:
                messages.append({"role": "user", "content": texto})
                messages.append({"role": "assistant", "content": fala})
            if emitir_fala:
                self.log(f"🗨️ [CHAT] {fala} | origem={origem}")
                self.falar(fala, "calma", 1)
            else:
                self.log(f"🗨️ [CHAT] conversa aberta sem repetir a saudação recente | origem={origem}")
            if not desejado and estado_atual and callable(self.encerrar_sessao):
                self.encerrar_sessao("desativacao_chat", False)
            self.salvar_memoria()
            return {
                "tratado": True,
                "alterado": desejado != estado_atual,
                "emitido": emitir_fala,
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


class InteracaoChatRuntime:
    """Conecta estado, hotkeys e terminal ao runtime único do modo chat."""

    def __init__(
        self,
        *,
        estado_runtime_getter: Callable[[], Any],
        modo_chat_runtime_getter: Callable[[], Any],
        abertura_runtime_getter: Callable[[], Any],
        processar_texto: Callable[[str], Any],
        escutar_terminal: Callable[..., Any],
        keyboard_mod: Any,
        hotkey_liga: str,
        hotkey_desliga: str,
        stdin_getter: Callable[[], Any],
        raw_print: Callable[..., Any],
        print_lock: Any,
        log: Callable[..., Any] = print,
    ) -> None:
        self._estado_runtime_getter = estado_runtime_getter
        self._modo_chat_runtime_getter = modo_chat_runtime_getter
        self._abertura_runtime_getter = abertura_runtime_getter
        self._processar_texto = processar_texto
        self._escutar_terminal = escutar_terminal
        self._keyboard = keyboard_mod
        self._hotkey_liga = hotkey_liga
        self._hotkey_desliga = hotkey_desliga
        self._stdin_getter = stdin_getter
        self._raw_print = raw_print
        self._print_lock = print_lock
        self._log = log

    def atualizar_estado(self, ativo: bool) -> None:
        self._estado_runtime_getter().atualizar_campos(
            "conversacional",
            modo_chat=bool(ativo),
            conversa_ativa=bool(ativo),
        )

    def definir(self, ativo: bool, origem: str = "desconhecida") -> str:
        runtime = self._modo_chat_runtime_getter()
        if runtime is None:
            return "Modo chat ainda não foi inicializado."
        resultado = runtime.definir(ativo, origem=origem)
        return str(resultado.get("fala") or "")

    def gerar_abertura(self) -> str:
        runtime = self._abertura_runtime_getter()
        if runtime is None:
            return "Modo chat ativado. Agora eu fico no papo e largo os comandos por um instante."
        # Abrir o campo de conversa não pode acordar ou disputar a LLM com a
        # primeira mensagem digitada. O runtime já possui variedade local e
        # consciência do horário para esta saudação curta.
        gerar_local = getattr(runtime, "gerar_local", None)
        if callable(gerar_local):
            return str(gerar_local("chat"))
        return str(runtime.gerar())

    def alternar_por_hotkey(self, ativo: bool) -> None:
        try:
            self.definir(ativo, origem="hotkey")
        except Exception as exc:
            self._log(f"⚠️ [CHAT] Falha ao alternar modo chat pela hotkey: {exc}")

    def _iniciar_alternancia(self, ativo: bool) -> threading.Thread:
        thread = threading.Thread(target=self.alternar_por_hotkey, args=(ativo,), daemon=True)
        thread.start()
        return thread

    def registrar_hotkeys(self) -> bool:
        try:
            self._keyboard.add_hotkey(self._hotkey_liga, lambda: self._iniciar_alternancia(True))
            self._keyboard.add_hotkey(self._hotkey_desliga, lambda: self._iniciar_alternancia(False))
            self._log(
                f"⌨️ [CHAT] Hotkeys registradas: {self._hotkey_liga} (liga) | "
                f"{self._hotkey_desliga} (desliga)"
            )
            return True
        except Exception as exc:
            self._log(f"⚠️ [CHAT] Não consegui registrar hotkeys do modo chat: {exc}")
            return False

    def escutar_terminal(self) -> None:
        estado = self._estado_runtime_getter()
        return self._escutar_terminal(
            estado_ativo=lambda: bool(
                estado.obter("conversacional", "modo_chat", False)
                or estado.obter("conversacional", "conversa_ativa", False)
            ),
            processar_texto=self._processar_texto,
            stdin=self._stdin_getter(),
            raw_print=self._raw_print,
            print_lock=self._print_lock,
            log=self._log,
            entrada_permitida=lambda: not bool(
                estado.obter("conversacional", "is_speaking", False)
            ),
        )

    def definir_messages(self, novas_messages: Any) -> None:
        mensagens = novas_messages if isinstance(novas_messages, list) else []
        self._estado_runtime_getter().atualizar_campos(
            "memoria_conversa",
            messages=mensagens,
        )


def criar_interacao_chat_runtime(**kwargs: Any) -> InteracaoChatRuntime:
    return InteracaoChatRuntime(**kwargs)
