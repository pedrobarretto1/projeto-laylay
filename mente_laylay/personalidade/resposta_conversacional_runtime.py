"""Entrega conversacional ligada ao resultado real e à memória compartilhada."""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Dict

from mente_laylay.memoria_mental.continuidade_conversa import (
    atualizar_memoria_topicos,
    topico_memoria_valido,
)
from mente_laylay.personalidade.falas_variadas import emitir_falha_contextual
from mente_laylay.personalidade.higiene_fala import remover_residuos_operacionais
from mente_laylay.emocoes.estado_emocional import (
    aplicar_estado_emocional,
    decair_estado_emocional,
)


class RespostaConversacionalRuntime:
    def __init__(
        self,
        *,
        namespace_getter: Callable[[], Dict[str, Any]],
        estado_runtime_getter: Callable[[], Any],
        fallback_fala: str,
        log: Callable[..., Any] = print,
    ) -> None:
        self.namespace_getter = namespace_getter
        self.estado_runtime_getter = estado_runtime_getter
        self.fallback_fala = fallback_fala
        self.log = log

    def _ns(self) -> Dict[str, Any]:
        return self.namespace_getter() or {}

    def limpar_texto_fala_ia(self, texto: str) -> str:
        fala = str(texto or "").strip()
        if not fala:
            return self.fallback_fala
        fala = re.sub(
            r"(?is)\bcomandos?\s*:\s*(?:\[\s*\]|\[.*?\]|\{.*?\}|none|null|nada|nenhum(?:a)?)",
            " ",
            fala,
        )
        fala = re.sub(r"(?is)\bcomandos?\s*:\s*", " ", fala)
        fala = re.sub(r"(?is)\bcomando\s*:\s*", " ", fala)
        fala = re.sub(r"(?is)\[EXEC:?[^]]*\]", " ", fala)
        fala = remover_residuos_operacionais(fala)
        return fala or self.fallback_fala

    def atualizar_memoria_topicos(self, texto_usuario: str, resposta_ia: str = "") -> None:
        ns = self._ns()
        estado = self.estado_runtime_getter()
        conversa = estado.conversacional
        normalizar = ns["_normalizar_texto_curto"]
        ultimo_salvo = str(conversa.get("ultimo_topico_conversa") or "").strip()
        # Também cura dados ruins já persistidos por versões anteriores.
        if ultimo_salvo and not topico_memoria_valido(ultimo_salvo, normalizar):
            conversa = dict(conversa)
            conversa["ultimo_topico_conversa"] = ""
            conversa["ultimo_topico_ts"] = 0.0
            conversa["topicos_conversa_recente"] = [
                topico for topico in conversa.get("topicos_conversa_recente", [])
                if topico_memoria_valido(str(topico), normalizar)
            ]
            estado.substituir("conversacional", conversa)
        recentes, topico, ts = atualizar_memoria_topicos(
            texto_usuario=texto_usuario,
            topicos_recentes=conversa.get("topicos_conversa_recente", []),
            ultimo_topico=conversa.get("ultimo_topico_conversa", ""),
            normalizar_texto_curto=normalizar,
        )
        if topico and ts:
            estado.atualizar_campos(
                "conversacional",
                topicos_conversa_recente=recentes,
                ultimo_topico_conversa=topico,
                ultimo_topico_ts=ts,
            )

    def acalmar_emocao(self, motivo: str = "") -> None:
        try:
            estado = self.estado_runtime_getter()
            conversa = estado.conversacional
            emocao = str(conversa.get("current_emotion") or "calma")
            if emocao.strip().lower() in {"brava", "irritada", "nervosa", "raivosa"}:
                conversa = aplicar_estado_emocional(
                    conversa,
                    "acalmando-se",
                    1,
                    causa=motivo or "pedido para se acalmar",
                    duracao_s=60,
                    interacoes=2,
                )
            humor = max(0, int(conversa.get("humor_level") or 0))
            conversa["humor_level"] = humor
            estado.substituir("conversacional", conversa)
            if motivo:
                self.log(f"🧘 [HUMOR] acalmando por conversa: {motivo}")
        except Exception as erro:
            self.log(f"⚠️ [CONVERSA] falha ao acalmar emoção: {type(erro).__name__}: {erro}")

    def definir_emocao(self, emocao: str, nivel: int = 1, motivo: str = "") -> None:
        """Atualiza a emoção conversacional na mesma fonte de estado da voz."""
        try:
            emocao_limpa = str(emocao or "calma").strip().lower() or "calma"
            nivel_limpo = max(1, min(3, int(nivel or 1)))
            estado = self.estado_runtime_getter()
            novo = aplicar_estado_emocional(
                estado.conversacional,
                emocao_limpa,
                nivel_limpo,
                causa=motivo or "reação da fala",
            )
            estado.substituir("conversacional", novo)
            if motivo:
                self.log(f"🎭 [EMOÇÃO] {emocao_limpa} nível {nivel_limpo} | {motivo}")
        except Exception as erro:
            self.log(f"⚠️ [EMOÇÃO] falha ao atualizar estado: {type(erro).__name__}: {erro}")

    def avancar_emocao(
        self,
        *,
        consumir_interacao: bool = True,
        interaction_key: str = "",
    ) -> None:
        try:
            estado = self.estado_runtime_getter()
            anterior = dict(estado.conversacional)
            chave = re.sub(r"\s+", " ", str(interaction_key or "")).strip().casefold()
            agora = time.time()
            if consumir_interacao and chave:
                chave_anterior = str(anterior.get("emotion_last_input_key") or "")
                ts_anterior = float(anterior.get("emotion_last_input_at") or 0.0)
                if chave == chave_anterior and agora - ts_anterior <= 2.0:
                    return
            novo, alterou = decair_estado_emocional(
                anterior,
                agora=agora,
                consumir_interacao=consumir_interacao,
            )
            if consumir_interacao and chave:
                novo["emotion_last_input_key"] = chave[:180]
                novo["emotion_last_input_at"] = agora
                alterou = True
            if alterou:
                estado.substituir("conversacional", novo)
                antes = f"{anterior.get('current_emotion', 'calma')}({anterior.get('emotion_level', 1)})"
                depois = f"{novo.get('current_emotion', 'calma')}({novo.get('emotion_level', 1)})"
                self.log(f"🎭 [EMOÇÃO] decaimento {antes} -> {depois}")
        except Exception as erro:
            self.log(f"⚠️ [EMOÇÃO] falha no decaimento: {type(erro).__name__}: {erro}")

    def emitir_resposta_curta(
        self,
        texto_usuario: str,
        fala: str,
        *,
        emocao: str = "",
        nivel: int = 1,
        habilidade: str = "conversa",
    ) -> bool:
        fala = str(fala or "").strip()
        if not fala:
            return False
        ns = self._ns()
        estado = self.estado_runtime_getter()
        verificar_fala = ns.get("_verificar_fala_do_turno")
        if callable(verificar_fala):
            verificacao = verificar_fala(fala, origem=habilidade or "conversa")
            if isinstance(verificacao, dict):
                if not verificacao.get("aceita", True):
                    return False
                fala = str(verificacao.get("fala") or fala).strip()
        conversa = estado.conversacional
        fala_aceita = ns["falar_com_lipsync"](
            fala,
            emocao or conversa.get("current_emotion") or "calma",
            nivel or conversa.get("emotion_level") or 1,
        )
        if fala_aceita is False:
            self.log("🧠 [MEMÓRIA:TURNO] fala descartada não foi registrada")
            return False
        mensagens = list(estado.memoria_conversa.get("messages", []) or [])
        mensagens.extend([
            {"role": "user", "content": str(texto_usuario or "")},
            {"role": "assistant", "content": fala},
        ])
        estado.atualizar_campos("memoria_conversa", messages=mensagens)
        ns["_registrar_mente_curta"](str(texto_usuario or ""), fala, habilidade=habilidade)
        ns["memoria_inteligente"].adicionar_interacao(str(texto_usuario or ""), fala)
        ns["salvar_memoria"]()
        return True

    def falar_falha_contextual(self, categoria: str, texto_usuario: str = "", *, detalhe: str = "") -> None:
        ns = self._ns()
        emitir_falha_contextual(
            categoria,
            texto_usuario,
            detalhe=detalhe,
            normalizar_texto=ns["_normalizar_texto_com_apelidos"],
            texto_parece_navegacao=ns["_texto_parece_navegacao_ou_janela_ia"],
            resposta_conversa_local=ns["_resposta_conversa_local"],
            fala_e_fallback_neutro=ns["_fala_e_fallback_neutro"],
            falar=ns["falar_com_lipsync"],
            log=self.log,
        )

    def executar_intencao_curta(
        self,
        resultado: Dict[str, Any] | None,
        texto_usuario: str,
        *,
        origem: str,
        contexto_autoaprimoramento: str = "",
    ) -> bool:
        if not isinstance(resultado, dict) or not str(resultado.get("intent") or "").strip():
            return False
        ns = self._ns()
        self.log(f"⚡ [ROTEADOR PERGUNTA-CURTA [{origem}]] {resultado}")
        executou = bool(ns["executar_intencao"](resultado, texto_usuario))
        ns["_registrar_resultado_execucao"](
            resultado, texto_usuario, executou, origem="pergunta_curta_contextual"
        )
        if executou:
            ns["_registrar_autoaprimoramento"](
                resultado,
                texto_usuario,
                True,
                contexto=contexto_autoaprimoramento or "pergunta curta dependente do topico",
                origem=origem,
            )
        return executou


def criar_resposta_conversacional_runtime(**kwargs: Any) -> RespostaConversacionalRuntime:
    return RespostaConversacionalRuntime(**kwargs)
