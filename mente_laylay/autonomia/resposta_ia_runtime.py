"""Orquestracao do ciclo principal de resposta da Laylay."""

from __future__ import annotations

import traceback
from typing import Any, Callable, Dict


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    return ctx.get(key, default) if isinstance(ctx, dict) else default


class RespostaIARuntime:
    """Coordena conversa, comandos e finalizacao usando o contexto da mente."""

    def __init__(self, *, contexto_getter: Callable[[], Dict[str, Any]], log: Callable[..., Any] = print) -> None:
        self._contexto_getter = contexto_getter
        self._log = log

    def _contexto(self) -> Dict[str, Any]:
        try:
            contexto = self._contexto_getter()
            return contexto if isinstance(contexto, dict) else {}
        except Exception:
            return {}

    def processar(self, texto: str) -> None:
        ctx = self._contexto()
        t = str(texto or "").strip()
        if not t:
            return

        try:
            modo_chat_runtime = _get(ctx, "modo_chat_runtime")
            if modo_chat_runtime is not None and modo_chat_runtime.processar_texto(t):
                return

            contexto_inicio_cb = _get(ctx, "contexto_inicio")
            contexto_inicio = contexto_inicio_cb() if callable(contexto_inicio_cb) else {}
            inicio_fluxo = _get(ctx, "processar_inicio_fluxo")
            if callable(inicio_fluxo) and inicio_fluxo(contexto_inicio, t):
                return

            if _get(ctx, "modo_chat", False) or _get(ctx, "conversa_ativa", False):
                self._log("🗨️ [CHAT] Modo chat ativo, mas seguindo o mesmo cérebro para comandos e conversa.")

            modo_rapido_cb = _get(ctx, "usar_modo_rapido")
            modo_rapido = bool(modo_rapido_cb(t)) if callable(modo_rapido_cb) else False

            comandos_imediatos = _get(ctx, "processar_comandos_imediatos")
            if callable(comandos_imediatos):
                try:
                    if comandos_imediatos(t, contexto_mental_ja_refinado=True):
                        return
                except Exception as erro:
                    self._log(f"⚠️ [IA] falha ao processar comandos imediatos: {erro}")

            if not modo_rapido:
                pre_fluxos = _get(ctx, "processar_pre_fluxos")
                if callable(pre_fluxos) and pre_fluxos(contexto_inicio, t):
                    return

                prompt_runtime = _get(ctx, "contexto_prompt_runtime")
                if prompt_runtime is None:
                    raise RuntimeError("Contexto do prompt ainda não foi inicializado.")
                mensagens_novas, _prompt_com_humor = prompt_runtime.preparar(t)
                set_messages = _get(ctx, "set_messages")
                if callable(set_messages):
                    set_messages(mensagens_novas)

            get_messages = _get(ctx, "get_messages")
            mensagens = get_messages() if callable(get_messages) else []
            if not isinstance(mensagens, list):
                mensagens = []
            mensagens.append({"role": "user", "content": texto})

            enviar_mensagem = _get(ctx, "enviar_mensagem")
            if not callable(enviar_mensagem):
                raise RuntimeError("enviar_mensagem ainda não foi inicializado.")
            bot_raw = enviar_mensagem(
                mensagens,
                _com_tools=False,
                max_tokens=384 if modo_rapido else 640,
                modo_rapido=modo_rapido,
            )
            self._log(f"🤖 [IA] Resposta bruta recebida (tamanho {len(str(bot_raw))} chars)")

            preparar_resposta = _get(ctx, "preparar_resposta")
            if not callable(preparar_resposta):
                raise RuntimeError("Preparador de resposta ainda não foi inicializado.")
            resposta = preparar_resposta(t, bot_raw)
            bot_raw = resposta.get("resposta_bruta", bot_raw)
            fala_limpa_original = str(resposta.get("fala") or _get(ctx, "fallback_fala", "Tô por aqui."))
            comandos = list(resposta.get("comandos") or [])
            tipo_interacao = str(resposta.get("tipo_interacao") or "")

            atualizar_topicos = _get(ctx, "atualizar_memoria_topicos")
            if not comandos and tipo_interacao in {"conversa", "", "confirmacao"} and callable(atualizar_topicos):
                atualizar_topicos(t, fala_limpa_original)

            executar_deterministico = _get(ctx, "processar_comando_deterministico")
            if not comandos and callable(executar_deterministico) and executar_deterministico(t, "pos-ia-0-comandos"):
                return

            dispatcher_runtime = _get(ctx, "contexto_dispatch_runtime")
            if dispatcher_runtime is None:
                raise RuntimeError("Contexto do dispatcher ainda não foi inicializado.")
            resultado_dispatch = _get(ctx, "executar_comandos_json")
            if not callable(resultado_dispatch):
                raise RuntimeError("Dispatcher de comandos ainda não foi inicializado.")
            dispatch = resultado_dispatch(
                dispatcher_runtime.montar(),
                texto,
                comandos,
                fala_limpa_original,
                tipo_interacao,
                False,
                False,
                False,
            )
            erros_execucao = list(dispatch.get("erros", []) or [])
            fala_ja_emitida = bool(dispatch.get("fala_ja_emitida", False))
            fala_emitida_por_acao = bool(dispatch.get("fala_emitida_por_acao", False))
            fala_salva_no_inicio = bool(dispatch.get("fala_salva_no_inicio", False))

            finalizacao_runtime = _get(ctx, "contexto_finalizacao_runtime")
            finalizar = _get(ctx, "finalizar_execucao")
            if finalizacao_runtime is None or not callable(finalizar):
                raise RuntimeError("Contexto de finalizacao ainda não foi inicializado.")
            finalizar(
                finalizacao_runtime.montar(),
                comandos,
                erros_execucao,
                fala_limpa_original,
                fala_ja_emitida,
                fala_emitida_por_acao,
                fala_salva_no_inicio,
            )
        except Exception as erro:
            self._log(f"❌ Erro grave na geração da resposta IA: {erro}")
            traceback.print_exc()


def criar_resposta_ia_runtime(
    *, contexto_getter: Callable[[], Dict[str, Any]], log: Callable[..., Any] = print
) -> RespostaIARuntime:
    return RespostaIARuntime(contexto_getter=contexto_getter, log=log)
