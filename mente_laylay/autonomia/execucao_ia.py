"""Coordenação de respostas da IA e da ponte modular de conteúdo."""

from __future__ import annotations

import ast
import asyncio
import json
import re
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple


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


class ContextoExecRuntime:
    """Entrega comandos de conteúdo exclusivamente ao roteador modular."""

    def __init__(
        self,
        *,
        contexto_getter: Callable[[], Dict[str, Any]],
        executar_conteudo_cb: Callable[..., bool],
        log: Callable[[str], None] = print,
    ) -> None:
        self.contexto_getter = contexto_getter
        self.executar_conteudo_cb = executar_conteudo_cb
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
            self.log(f"🧠 [CONTEÚDO] roteador modular assumiu: {comando}")
        return executou_modular


def criar_contexto_exec_runtime(**kwargs: Any) -> ContextoExecRuntime:
    return ContextoExecRuntime(**kwargs)


class CoordenadorExecRuntime:
    """Liga conteúdo modular e processamento de resposta sem antecipar o bootstrap."""

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
        self._assinaturas_em_processamento: set[str] = set()
        self._geracao_entrada = 0

    def executar(self, cmd: str, arg: Any) -> bool:
        runtime = self._contexto_exec_getter()
        if runtime is None:
            raise RuntimeError("Contexto modular de conteúdo ainda não foi inicializado.")
        return bool(runtime.executar(cmd, arg))

    def processar_sync(
        self,
        texto: str,
        geracao: int | None = None,
        origem: str = "desconhecida",
    ) -> Any:
        runtime = self._resposta_ia_getter()
        if runtime is None:
            self._log("⚠️ [IA] Runtime de resposta ainda não foi inicializado.")
            return None
        ainda_atual = None
        if geracao is not None:
            ainda_atual = lambda: self._geracao_atual() == geracao
            if origem != "desconhecida":
                return runtime.processar(
                    texto,
                    ainda_atual_cb=ainda_atual,
                    origem=origem,
                )
            return runtime.processar(texto, ainda_atual_cb=ainda_atual)
        if origem != "desconhecida":
            return runtime.processar(texto, origem=origem)
        return runtime.processar(texto)

    def processar_entrada(
        self,
        texto: str,
        geracao: int | None = None,
        origem: str = "desconhecida",
    ) -> Any:
        """Entrega toda entrada à resposta canônica, que cria o turno primeiro."""
        return self.processar_sync(texto, geracao, origem)

    def _geracao_atual(self) -> int:
        with self._agendamento_lock:
            return self._geracao_entrada

    def _iniciar_thread(
        self,
        texto: str,
        geracao: int,
        origem: str = "desconhecida",
    ) -> threading.Thread:
        thread = threading.Thread(
            target=self._processar_agendado,
            args=(texto, geracao, origem),
            daemon=True,
        )
        thread.start()
        return thread

    @staticmethod
    def _assinatura_entrada(texto: str) -> str:
        return re.sub(r"\s+", " ", str(texto or "").casefold()).strip()

    def _processar_agendado(
        self,
        texto: str,
        geracao: int,
        origem: str = "desconhecida",
    ) -> Any:
        assinatura = self._assinatura_entrada(texto)
        try:
            return self.processar_entrada(texto, geracao, origem)
        finally:
            with self._agendamento_lock:
                self._assinaturas_em_processamento.discard(assinatura)

    def agendar(self, texto: str, origem: str = "desconhecida") -> Any:
        assinatura = self._assinatura_entrada(texto)
        agora = time.monotonic()
        with self._agendamento_lock:
            if (
                assinatura
                and assinatura in self._assinaturas_em_processamento
            ):
                self._log(
                    "🧠 [ENTRADA] duplicata imediata ignorada "
                    f"(ainda em processamento): {texto!r}"
                )
                return None
            self._ultima_entrada_assinatura = assinatura
            self._ultima_entrada_ts = agora
            if assinatura:
                self._assinaturas_em_processamento.add(assinatura)
            self._geracao_entrada += 1
            geracao = self._geracao_entrada
        # O Terminal 2 possui transporte e ciclo de vida próprios. Vincular a
        # sua entrada ao loop da extensão Chrome fazia uma mensagem ficar
        # órfã quando esse loop ainda estava subindo, era reiniciado ou estava
        # ocupado. O worker dedicado preserva a mesma mente serializada pelo
        # ``RespostaIARuntime`` sem criar dependência entre os dois canais.
        if origem == "desktop":
            try:
                return self._iniciar_thread(texto, geracao, origem)
            except Exception:
                with self._agendamento_lock:
                    self._assinaturas_em_processamento.discard(assinatura)
                raise
        loop = self._loop_getter()
        loop_ativo = False
        if loop is not None:
            try:
                loop_ativo = bool(loop.is_running()) and not bool(loop.is_closed())
            except (AttributeError, RuntimeError):
                loop_ativo = False
        if loop_ativo:
            try:
                futuro = asyncio.run_coroutine_threadsafe(
                    asyncio.to_thread(self._processar_agendado, texto, geracao, origem),
                    loop,
                )
                futuro.add_done_callback(self._observar_agendamento_assincrono)
                return futuro
            except Exception as exc:
                self._log(f"Erro ao jogar IA pro background: {exc}")
        elif loop is not None:
            self._log(
                "🧠 [ENTRADA] loop compartilhado ainda não está ativo; "
                "usando worker dedicado"
            )
        try:
            return self._iniciar_thread(texto, geracao, origem)
        except TypeError:
            # Compatibilidade com adaptadores antigos que substituíam o
            # iniciador e ainda recebem somente o texto.
            try:
                return self._iniciar_thread(texto, geracao)
            except TypeError:
                try:
                    return self._iniciar_thread(texto)  # type: ignore[call-arg]
                except Exception:
                    with self._agendamento_lock:
                        self._assinaturas_em_processamento.discard(assinatura)
                    raise
        except Exception:
            with self._agendamento_lock:
                self._assinaturas_em_processamento.discard(assinatura)
            raise

    def _observar_agendamento_assincrono(self, futuro: Any) -> None:
        """Torna falhas do loop visíveis sem repetir uma entrada incerta."""
        try:
            futuro.result()
        except asyncio.CancelledError:
            self._log("⚠️ [ENTRADA] processamento assíncrono cancelado")
        except Exception as erro:
            self._log(
                "⚠️ [ENTRADA] worker assíncrono encerrou com erro: "
                f"{type(erro).__name__}: {erro}"
            )


def criar_coordenador_exec_runtime(**kwargs: Any) -> CoordenadorExecRuntime:
    return CoordenadorExecRuntime(**kwargs)


def filtrar_apenas_fala(
    texto_bruto: str,
    executar_comando_autonomo_cb: Optional[Callable[[str], Any]] = None,
    fallback_fala: str = "Tô por aqui. Me dá só mais um pedaço disso.",
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
