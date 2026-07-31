"""Runtime para feedback pendente e continuacao de comando.

Este modulo coordena pendencias sem guardar uma mente paralela: ele recebe
callbacks do `laylay.py` a cada chamada e devolve o estado atualizado pelo
mesmo dicionario de continuidades.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    classificar_confirmacao_contextual as _classificar_confirmacao_contextual,
    classificar_confirmacao_local as _classificar_confirmacao_local,
    normalizar_confirmacao_texto as _normalizar_confirmacao_texto,
)


def _get(ctx: Dict[str, Any], chave: str, default: Any = None) -> Any:
    return ctx.get(chave, default) if isinstance(ctx, dict) else default


class FeedbackPendenteRuntime:
    def __init__(
        self,
        *,
        contexto_getter: Callable[[], Dict[str, Any]],
        log: Callable[..., Any] = print,
    ) -> None:
        self._contexto_getter = contexto_getter
        self._log = log

    def _ctx(self) -> Dict[str, Any]:
        try:
            ctx = self._contexto_getter() if callable(self._contexto_getter) else {}
            return ctx if isinstance(ctx, dict) else {}
        except Exception:
            return {}

    def normalizar_confirmacao_texto(self, texto: str) -> str:
        return _normalizar_confirmacao_texto(texto)

    def classificar_confirmacao_local(self, texto: str):
        return _classificar_confirmacao_local(texto)

    def classificar_confirmacao_contextual(self, texto: str, sugestao: str):
        local = self.classificar_confirmacao_local(texto)
        if local is not None:
            return local
        interpretar = _get(self._ctx(), "interpretar_confirmacao_llm")
        return _classificar_confirmacao_contextual(
            texto,
            sugestao,
            interpretar_confirmacao_llm=interpretar,
        )

    def interpretar_resposta_pendente(self, texto: str, pendencia: dict) -> dict:
        ctx = self._ctx()
        resumo_cb = _get(ctx, "resumo_mente_integrada_para_prompt")
        enviar_mensagem = _get(ctx, "enviar_mensagem")
        mente = _get(ctx, "mente_integrada_estado", {})

        contexto_recente = ""
        try:
            if callable(resumo_cb):
                contexto_recente = str(resumo_cb(mente) or "")
        except Exception:
            contexto_recente = ""

        def _llm(prompt: str) -> str:
            if not callable(enviar_mensagem):
                return ""
            return enviar_mensagem(
                [{"role": "system", "content": prompt}],
                _com_tools=False,
                max_tokens=120,
                modo_rapido=True,
            )

        interpretador = _get(ctx, "interpretar_resposta_pendente")
        if callable(interpretador):
            return interpretador(
                texto_usuario=texto,
                pendencia=pendencia,
                contexto=contexto_recente,
                interpretar_llm=_llm,
            )
        return {}

    def handle_feedback_pendente(self, texto: str) -> bool:
        ctx = self._ctx()
        handle_feedback = _get(ctx, "handle_feedback_pendente")
        continuidades_get = _get(ctx, "continuidades_get")
        continuidades_update = _get(ctx, "continuidades_update")

        contexto = {
            "_rotina_sugestao_pendente": continuidades_get("rotina_sugestao_pendente") if callable(continuidades_get) else None,
            "_playlist_sugestao_pendente": continuidades_get("playlist_sugestao_pendente") if callable(continuidades_get) else None,
            "_email_sugestao_pendente": continuidades_get("email_sugestao_pendente") if callable(continuidades_get) else None,
            "_classificar_confirmacao_contextual": self.classificar_confirmacao_contextual,
            "_classificar_confirmacao_local": self.classificar_confirmacao_local,
            "_handle_sugestao_confirmacao": _get(ctx, "handle_sugestao_confirmacao"),
            "solicitar_aba_ativa": _get(ctx, "solicitar_aba_ativa"),
            "add_to_playlist_url": _get(ctx, "add_to_playlist_url"),
            "extrair_nome_playlist": _get(ctx, "extrair_nome_playlist"),
            "_yt_clean_title": _get(ctx, "yt_clean_title"),
            "falar_com_lipsync": _get(ctx, "falar_com_lipsync"),
            "_set_ultima_playlist": _get(ctx, "set_ultima_playlist"),
            "_rotina_registrar_feedback": _get(ctx, "rotina_registrar_feedback"),
            "_interpretar_resposta_pendente": self.interpretar_resposta_pendente,
            "_gmail_buscar_nao_lidos": _get(ctx, "gmail_buscar_nao_lidos"),
            "_gmail_falar_resumo_estiloso": _get(ctx, "gmail_falar_resumo_estiloso"),
            "_registrar_feedback_proatividade": _get(ctx, "registrar_feedback_proatividade"),
        }

        resultado = bool(handle_feedback(contexto, texto)) if callable(handle_feedback) else False
        if callable(continuidades_update):
            continuidades_update(
                rotina_sugestao_pendente=contexto.get("_rotina_sugestao_pendente"),
                playlist_sugestao_pendente=contexto.get("_playlist_sugestao_pendente"),
                email_sugestao_pendente=contexto.get("_email_sugestao_pendente"),
            )
        return resultado

    def separar_feedback_e_continuacao(self, texto: str):
        bruto = str(texto or "").strip()
        if not bruto:
            return None
        normalizar = _get(self._ctx(), "normalizar_texto_com_apelidos")
        t = normalizar(bruto) if callable(normalizar) else bruto.lower().strip()
        if not t:
            return None

        separadores = [
            " mas ",
            " mas, ",
            " e depois ",
            " depois ",
            " e ai ",
            " e aí ",
            " e ",
        ]
        for sep in separadores:
            if sep not in t:
                continue
            esquerda, direita = t.split(sep, 1)
            esquerda = esquerda.strip(" ,.!?;:")
            direita = direita.strip(" ,.!?;:")
            if not esquerda or not direita:
                continue
            if len(esquerda.split()) > 8:
                continue
            confirmado = self.classificar_confirmacao_local(esquerda)
            if confirmado is None:
                continue
            return esquerda, direita, confirmado
        return None

    def handle_feedback_pendente_misto(self, texto: str) -> bool:
        partes = self.separar_feedback_e_continuacao(texto)
        if not partes:
            return False

        prefixo, resto, confirmado = partes
        if not self.handle_feedback_pendente(prefixo):
            return False

        if resto:
            processar_comandos = _get(self._ctx(), "processar_comandos_imediatos")
            try:
                if callable(processar_comandos) and processar_comandos(resto):
                    return True
            except Exception as e:
                self._log(f"⚠️ [FEEDBACK MISTO] falha ao executar continuacao: {e}")

        return bool(confirmado)


def criar_feedback_pendente_runtime(
    *,
    contexto_getter: Callable[[], Dict[str, Any]],
    log: Callable[..., Any] = print,
) -> FeedbackPendenteRuntime:
    return FeedbackPendenteRuntime(contexto_getter=contexto_getter, log=log)
