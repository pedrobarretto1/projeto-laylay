"""Parsing e execucao legada de respostas da IA na Laylay.

Este modulo continua existindo como fallback de compatibilidade enquanto
o roteador modular de conteudo assume o caminho principal.
"""

from __future__ import annotations

import ast
import asyncio
import json
import re
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple


_COMANDOS_OWNED_PELO_ROTEADOR_MODULAR = {
    "YOUTUBE", "YT_VOLUME", "SET_VOLUME", "OPEN_SITE", "CLOSE_TAB",
    "YT_PLAY", "YT_PAUSE", "YT_NEXT", "YT_REPLAY", "LISTAR_PLAYLISTS",
    "TOCAR_PLAYLIST", "TOCAR_PLAYLIST_SHUFFLE", "ADICIONAR_A_PLAYLIST",
    "CLICK", "TYPE", "PRESS", "CLOSE_SPECIFIC_TAB", "TELA_CHEIA", "FULLSCREEN",
}


def remover_prefixo_exec(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    limpo = re.sub(r"^\s*\[EXEC:[^\]]+\]\s*", "", texto.strip(), flags=re.IGNORECASE).strip()
    # Modelos locais ocasionalmente devolvem a chave do contrato como texto.
    # Removemos apenas no inicio para preservar frases naturais como "ele fala: ...".
    for _ in range(3):
        novo = re.sub(
            r'^\s*["\']?(?:fala|mensagem)["\']?\s*:\s*["\']?',
            "",
            limpo,
            count=1,
            flags=re.IGNORECASE,
        ).strip()
        if novo == limpo:
            break
        limpo = novo
    if limpo.endswith(('"', "'")) and limpo[:1] not in {'"', "'"}:
        limpo = limpo[:-1].rstrip()
    return limpo


def executar_exec(
    cmd: str,
    arg: Any,
    contexto: Dict[str, Any],
) -> bool:
    """Compatibilidade mínima para comandos ainda não migrados ao roteador modular."""
    c = str(cmd or "").strip().upper()
    a = "" if arg is None else str(arg).strip()

    abrir_programa = contexto.get("abrir_programa")
    fechar_programa = contexto.get("fechar_programa")
    _eh_alvo_site_web = contexto.get("_eh_alvo_site_web")
    _contexto_aponta_site_web = contexto.get("_contexto_aponta_site_web")

    if c == "OPEN_APP":
        if not a or len(a) < 2 or not callable(abrir_programa):
            return False
        return bool(abrir_programa(a))

    if c == "FECHAR_PROGRAMA":
        if not a:
            return False
        if callable(_eh_alvo_site_web) and callable(_contexto_aponta_site_web) and (_eh_alvo_site_web(a) or _contexto_aponta_site_web(a)):
            # Fechamento de abas pertence ao roteador modular. Retornar falso
            # impede que este fallback contorne suas validações.
            return False
        if callable(fechar_programa):
            fechar_programa(a)
            return True
        return False

    return False


class ContextoExecRuntime:
    """Coordena o caminho modular e o fallback EXEC com contexto atualizado."""

    def __init__(
        self,
        *,
        contexto_getter: Callable[[], Dict[str, Any]],
        executar_conteudo_cb: Callable[..., bool],
        executar_legado_cb: Callable[[str, Any, Dict[str, Any]], bool] = executar_exec,
        log: Callable[[str], None] = print,
    ) -> None:
        self.contexto_getter = contexto_getter
        self.executar_conteudo_cb = executar_conteudo_cb
        self.executar_legado_cb = executar_legado_cb
        self.log = log

    def montar_contexto(self, arg: Any) -> Dict[str, Any]:
        contexto = dict(self.contexto_getter() or {})
        contexto["arg"] = arg
        return contexto

    def executar(self, cmd: str, arg: Any) -> bool:
        comando = str(cmd or "").strip()
        c_args = "" if arg is None else str(arg).strip()
        contexto = self.montar_contexto(arg)

        executou_modular = bool(self.executar_conteudo_cb(
            comando,
            c_args,
            comando,
            comando.upper(),
            contexto,
        ))
        if executou_modular:
            self.log(f"🧠 [EXEC] caminho modular de conteudo assumiu: {comando}")
            return True

        if comando.upper() in _COMANDOS_OWNED_PELO_ROTEADOR_MODULAR:
            self.log(
                f"🛡️ [EXEC] comando modular recusado ou indisponível; fallback legado bloqueado: {comando}"
            )
            return False

        ok_legado = bool(self.executar_legado_cb(cmd, arg, contexto))
        if ok_legado:
            self.log(f"🧩 [EXEC] fallback legado assumiu: {comando}")
        return ok_legado


def criar_contexto_exec_runtime(**kwargs: Any) -> ContextoExecRuntime:
    return ContextoExecRuntime(**kwargs)


class CoordenadorExecRuntime:
    """Liga execução EXEC e processamento de resposta sem antecipar o bootstrap."""

    def __init__(
        self,
        *,
        contexto_exec_getter: Callable[[], Any],
        resposta_ia_getter: Callable[[], Any],
        loop_getter: Callable[[], Any],
        log: Callable[..., Any] = print,
    ) -> None:
        self._contexto_exec_getter = contexto_exec_getter
        self._resposta_ia_getter = resposta_ia_getter
        self._loop_getter = loop_getter
        self._log = log
        self._agendamento_lock = threading.Lock()
        self._ultima_entrada_assinatura = ""
        self._ultima_entrada_ts = 0.0

    def executar(self, cmd: str, arg: Any) -> bool:
        runtime = self._contexto_exec_getter()
        if runtime is None:
            raise RuntimeError("Contexto de execução EXEC ainda não foi inicializado.")
        return bool(runtime.executar(cmd, arg))

    def processar_sync(self, texto: str) -> Any:
        runtime = self._resposta_ia_getter()
        if runtime is None:
            self._log("⚠️ [IA] Runtime de resposta ainda não foi inicializado.")
            return None
        return runtime.processar(texto)

    def _iniciar_thread(self, texto: str) -> threading.Thread:
        thread = threading.Thread(target=self.processar_sync, args=(texto,), daemon=True)
        thread.start()
        return thread

    def agendar(self, texto: str) -> Any:
        assinatura = re.sub(r"\s+", " ", str(texto or "").casefold()).strip()
        agora = time.monotonic()
        with self._agendamento_lock:
            if (
                assinatura
                and assinatura == self._ultima_entrada_assinatura
                and agora - self._ultima_entrada_ts <= 1.0
            ):
                self._log(f"🧠 [ENTRADA] duplicata imediata ignorada: {texto!r}")
                return None
            self._ultima_entrada_assinatura = assinatura
            self._ultima_entrada_ts = agora
        loop = self._loop_getter()
        if loop:
            try:
                return asyncio.run_coroutine_threadsafe(
                    asyncio.to_thread(self.processar_sync, texto),
                    loop,
                )
            except Exception as exc:
                self._log(f"Erro ao jogar IA pro background: {exc}")
        return self._iniciar_thread(texto)


def criar_coordenador_exec_runtime(**kwargs: Any) -> CoordenadorExecRuntime:
    return CoordenadorExecRuntime(**kwargs)


def filtrar_apenas_fala(
    texto_bruto: str,
    executar_comando_autonomo_cb: Optional[Callable[[str], Any]] = None,
    fallback_fala: str = "Tô por aqui, Pedro. Me dá só mais um pedaço disso.",
) -> str:
    if not texto_bruto:
        return fallback_fala

    match_cmd = re.search(r"\[COMANDO\]:\s*(.*?)(?:\n|Laylay:|$)", texto_bruto, re.IGNORECASE | re.DOTALL)
    if match_cmd:
        cmd_str = match_cmd.group(1).strip()
        cmd_final = ""
        try:
            lista = ast.literal_eval(cmd_str)
            if isinstance(lista, list):
                cmd_final = " | ".join([str(x).strip() for x in lista])
        except Exception:
            cmd_final = re.sub(r'[\[\]\'"]', '', cmd_str).strip()
        if cmd_final and "NENHUM" not in cmd_final.upper() and callable(executar_comando_autonomo_cb):
            executar_comando_autonomo_cb(cmd_final)

    match_fala = re.search(r"Laylay:\s*(.*)", texto_bruto, re.IGNORECASE | re.DOTALL)
    if match_fala:
        fala = match_fala.group(1).strip()
        return fala or fallback_fala

    fala_limpa = re.sub(r"\[.*?\]:?.*?\n", "", texto_bruto, flags=re.IGNORECASE | re.DOTALL)
    fala_limpa = re.sub(r"\[.*?\]", "", fala_limpa, flags=re.IGNORECASE | re.DOTALL)
    return fala_limpa.strip() or fallback_fala


def parsear_resposta_json(resposta_bruta: str, fallback_fala: str) -> Tuple[str, str]:
    if not resposta_bruta or not isinstance(resposta_bruta, str):
        return fallback_fala, ""
    texto = re.sub(r"```(?:python|json)?", "", resposta_bruta.strip(), flags=re.IGNORECASE).strip()

    fala = ""
    comandos_str = ""

    try:
        dados = ast.literal_eval(texto)
        if isinstance(dados, tuple) and len(dados) >= 2:
            fala = str(dados[0]).strip()
            comandos_raw = dados[1] if isinstance(dados[1], list) else []
            for cmd in comandos_raw:
                if isinstance(cmd, dict):
                    acao = str(cmd.get("acao", "")).strip().upper()
                    alvo = str(cmd.get("alvo", "")).strip()
                    if acao and acao != "NENHUM":
                        comandos_str += f"{acao}('{alvo}')" if alvo else f"{acao}()"
                        comandos_str += " | "
            comandos_str = comandos_str.strip(" | ")
    except Exception:
        pass

    if not fala:
        try:
            data = json.loads(texto)
            fala = str(data.get("fala", fallback_fala)).strip()
            cmds = data.get("comandos", [])
            if isinstance(cmds, list):
                for cmd in cmds:
                    acao = str(cmd.get("acao", "")).strip().upper()
                    alvo = str(cmd.get("alvo", "")).strip()
                    if acao and acao != "NENHUM":
                        comandos_str += f"{acao}('{alvo}')" if alvo else f"{acao}()"
                        comandos_str += " | "
                comandos_str = comandos_str.strip(" | ")
        except Exception:
            pass

    if not fala:
        fala = re.sub(r"\[.*?\]", "", texto, flags=re.DOTALL).strip() or fallback_fala

    return fala, comandos_str
