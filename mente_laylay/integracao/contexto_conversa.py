"""Integradores de contexto conversacional da Laylay.

Este modulo nao executa acoes.
Ele apenas organiza o retrato curto usado pelos fluxos de conversa.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from mente_laylay.cognicao.coerencia_temporal import responder_correcao_temporal


def montar_contexto_conversa_natural(
    *,
    current_emotion: str,
    mente_integrada_estado: Dict[str, Any] | None,
    ultimo_topico_conversa: str,
    foco_vivo: Dict[str, Any] | None,
    obter_conteudo_atual: Callable[..., Any] | None,
    pesquisar_contexto_tema: Callable[..., Any] | None,
    normalizar_texto_curto: Callable[..., Any] | None,
    normalizar_texto_com_apelidos: Callable[..., Any] | None,
    resumo_mente_integrada_para_prompt: Callable[..., Any] | None,
    enviar_mensagem: Callable[..., Any] | None,
    extrair_json_da_ia: Callable[..., Any] | None,
    ajustar_fala_por_horario: Callable[..., Any] | None,
    fala_de_confirmacao_variada: Callable[..., Any] | None,
    texto_parece_navegacao_ou_janela_ia: Callable[..., Any] | None,
    fala_e_fallback_neutro: Callable[..., Any] | None,
    ajustar_tom_por_emocao: Callable[..., Any] | None,
    contexto_perceptivo: Dict[str, Any] | None = None,
    registrar_leitura_emocional_usuario: Callable[..., Any] | None = None,
    acalmar_emocao: Callable[..., Any] | None = None,
    definir_emocao: Callable[..., Any] | None = None,
) -> Dict[str, Any]:
    return {
        "current_emotion": current_emotion,
        "mente_integrada_estado": dict(mente_integrada_estado or {}),
        "ultimo_topico_conversa": str(ultimo_topico_conversa or "").strip(),
        "foco_vivo": dict(foco_vivo or {}),
        "_obter_conteudo_atual": obter_conteudo_atual,
        "_pesquisar_contexto_tema": pesquisar_contexto_tema,
        "_normalizar_texto_curto": normalizar_texto_curto,
        "_normalizar_texto_com_apelidos": normalizar_texto_com_apelidos,
        "_resumo_mente_integrada_para_prompt": resumo_mente_integrada_para_prompt,
        "enviar_mensagem": enviar_mensagem,
        "_extrair_json_da_ia": extrair_json_da_ia,
        "_ajustar_fala_por_horario": ajustar_fala_por_horario,
        "_fala_de_confirmacao_variada": fala_de_confirmacao_variada,
        "_texto_parece_navegacao_ou_janela_ia": texto_parece_navegacao_ou_janela_ia,
        "_fala_e_fallback_neutro": fala_e_fallback_neutro,
        "_ajustar_tom_por_emocao": ajustar_tom_por_emocao,
        "contexto_perceptivo": dict(contexto_perceptivo or {}),
        "_registrar_leitura_emocional_usuario": registrar_leitura_emocional_usuario,
        "_acalmar_emocao": acalmar_emocao,
        "_definir_emocao": definir_emocao,
    }


def montar_contexto_gate_conversa(
    *,
    mente_integrada_estado: Dict[str, Any] | None,
    foco_vivo: Dict[str, Any] | None,
    obter_conteudo_atual: Callable[..., Any] | None,
    ultimo_topico_conversa: str,
) -> Dict[str, Any]:
    return {
        "mente": dict(mente_integrada_estado or {}),
        "foco_vivo": dict(foco_vivo or {}),
        "_obter_conteudo_atual": obter_conteudo_atual,
        "ultimo_topico": str(ultimo_topico_conversa or "").strip(),
    }


def montar_contexto_inicio_chat_por_grupos(
    *,
    base: Dict[str, Any] | None = None,
    memoria: Dict[str, Any] | None = None,
    conversa: Dict[str, Any] | None = None,
    musica_feedback: Dict[str, Any] | None = None,
    comandos: Dict[str, Any] | None = None,
    execucao: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    base = dict(base or {})
    memoria = dict(memoria or {})
    conversa = dict(conversa or {})
    musica_feedback = dict(musica_feedback or {})
    comandos = dict(comandos or {})
    execucao = dict(execucao or {})

    messages = base.get("messages")
    contexto = {
        "messages": messages,
        "current_emotion": base.get("current_emotion", "calma"),
        "emotion_level": base.get("emotion_level", 1),
        "_semantica_na_resposta_principal": bool(base.get("semantica_na_resposta_principal")),
        "_processar_aprendizado_apelido_imediato": memoria.get("processar_aprendizado_apelido_imediato"),
        "_refinar_contexto_mental": memoria.get("refinar_contexto_mental"),
        "_registrar_autoaprimoramento": memoria.get("registrar_autoaprimoramento"),
        "_registrar_mente_curta": memoria.get("registrar_mente_curta"),
        "_registrar_interacao_temporal": memoria.get("registrar_interacao_temporal"),
        "_registrar_resultado_execucao": memoria.get("registrar_resultado_execucao"),
        "_recuperar_aprendizados": memoria.get("recuperar_aprendizados"),
        "_texto_social_curto": conversa.get("texto_social_curto"),
        "_texto_conversa_casual_sem_acao": conversa.get("texto_conversa_casual_sem_acao"),
        "_texto_tem_comando_explicito": conversa.get("texto_tem_comando_explicito"),
        "_resposta_conversa_rapida_local": conversa.get("resposta_conversa_rapida_local"),
        "_parece_elogio_ou_agradecimento_curto": conversa.get("parece_elogio_ou_agradecimento_curto"),
        "_responder_agradecimento_ou_elogio": conversa.get("responder_agradecimento_ou_elogio"),
        "_resolver_pergunta_curta_contextual_intencao": conversa.get("resolver_pergunta_curta_contextual_intencao"),
        "_texto_responde_pergunta_aberta": conversa.get("texto_responde_pergunta_aberta"),
        "_responder_pergunta_aberta": conversa.get("responder_pergunta_aberta"),
        "_texto_bloqueia_playlist_agora": musica_feedback.get("texto_bloqueia_playlist_agora"),
        "_texto_pede_direcao_musical_generica": musica_feedback.get("texto_pede_direcao_musical_generica"),
        "_responder_pedido_direcao_musical_generica": musica_feedback.get("responder_pedido_direcao_musical_generica"),
        "_processar_confirmacao_sugestao_musical": musica_feedback.get("processar_confirmacao_sugestao_musical"),
        "_texto_pede_opiniao_musica_atual": musica_feedback.get("texto_pede_opiniao_musica_atual"),
        "_responder_opiniao_musica_atual": musica_feedback.get("responder_opiniao_musica_atual"),
        "_handle_feedback_pendente_misto": musica_feedback.get("handle_feedback_pendente_misto"),
        "_handle_feedback_pendente": musica_feedback.get("handle_feedback_pendente"),
        "_detectar_mover_playlist_texto": musica_feedback.get("detectar_mover_playlist_texto"),
        "_mover_item_playlist": musica_feedback.get("mover_item_playlist"),
        "_bloquear_playlist_temporariamente": musica_feedback.get("bloquear_playlist_temporariamente"),
        "processar_comando_deterministico": comandos.get("processar_comando_deterministico"),
        "_usar_modo_rapido_conversa": comandos.get("usar_modo_rapido_conversa"),
        "interpretar_comando_local_rapido": comandos.get("interpretar_comando_local_rapido"),
        "_resolver_comando_contextual_forcado": comandos.get("resolver_comando_contextual_forcado"),
        "_resolver_reparacao_conversacional": comandos.get("resolver_reparacao_conversacional"),
        "_responder_contexto_janela_indisponivel": comandos.get("responder_contexto_janela_indisponivel"),
        "_detectar_sugestao_indireta": comandos.get("detectar_sugestao_indireta"),
        "_registrar_sugestao_indireta": comandos.get("registrar_sugestao_indireta"),
        "mente_integrada_estado": comandos.get("mente_integrada_estado", {}),
        "executar_intencao": execucao.get("executar_intencao"),
        "_emitir_resposta_curta": execucao.get("emitir_resposta_curta"),
        "_executar_intencao_curta_contextual": execucao.get("executar_intencao_curta_contextual"),
        "falar_com_lipsync": execucao.get("falar_com_lipsync"),
        "salvar_memoria": execucao.get("salvar_memoria"),
        "mensagens_append": messages.append if hasattr(messages, "append") else None,
    }
    return contexto


class ContextoInicioChatRuntime:
    def __init__(
        self,
        *,
        namespace_getter: Callable[[], Dict[str, Any]],
        estado_getter: Callable[[], Dict[str, Any]],
        memoria_sqlite: Any,
    ) -> None:
        self.namespace_getter = namespace_getter
        self.estado_getter = estado_getter
        self.memoria_sqlite = memoria_sqlite

    def montar(self) -> Dict[str, Any]:
        ns = self.namespace_getter() or {}
        estado = self.estado_getter() or {}
        contexto = montar_contexto_inicio_chat_por_grupos(
            base={
                "messages": estado.get("messages", []),
                "current_emotion": estado.get("current_emotion", "calma"),
                "emotion_level": estado.get("emotion_level", 1),
                "semantica_na_resposta_principal": str(
                    getattr(ns.get("_interpretador_semantico_runtime"), "modo", "") or ""
                ).lower() == "main",
            },
            memoria={
                "processar_aprendizado_apelido_imediato": ns.get("_processar_aprendizado_apelido_imediato"),
                "refinar_contexto_mental": ns.get("_refinar_contexto_mental"),
                "registrar_autoaprimoramento": ns.get("_registrar_autoaprimoramento"),
                "registrar_mente_curta": ns.get("_registrar_mente_curta"),
                "registrar_interacao_temporal": ns.get("_registrar_interacao_temporal"),
                "registrar_resultado_execucao": ns.get("_registrar_resultado_execucao"),
                "recuperar_aprendizados": getattr(self.memoria_sqlite, "recuperar_aprendizados", None),
            },
            conversa={
                "texto_social_curto": ns.get("_texto_social_curto"),
                "texto_conversa_casual_sem_acao": ns.get("_texto_conversa_casual_sem_acao"),
                "texto_tem_comando_explicito": ns.get("_texto_tem_comando_explicito"),
                "resposta_conversa_rapida_local": ns.get("_resposta_conversa_rapida_local"),
                "parece_elogio_ou_agradecimento_curto": ns.get("_parece_elogio_ou_agradecimento_curto"),
                "responder_agradecimento_ou_elogio": ns.get("_responder_agradecimento_ou_elogio"),
                "resolver_pergunta_curta_contextual_intencao": ns.get("_resolver_pergunta_curta_contextual_intencao"),
                "texto_responde_pergunta_aberta": ns.get("_texto_responde_pergunta_aberta"),
                "responder_pergunta_aberta": ns.get("_responder_pergunta_aberta"),
            },
            musica_feedback={
                "texto_bloqueia_playlist_agora": ns.get("_texto_bloqueia_playlist_agora"),
                "texto_pede_direcao_musical_generica": ns.get("_texto_pede_direcao_musical_generica"),
                "responder_pedido_direcao_musical_generica": ns.get("_responder_pedido_direcao_musical_generica"),
                "processar_confirmacao_sugestao_musical": ns.get("_processar_confirmacao_sugestao_musical"),
                "texto_pede_opiniao_musica_atual": ns.get("_texto_pede_opiniao_musica_atual"),
                "responder_opiniao_musica_atual": ns.get("_responder_opiniao_musica_atual"),
                "handle_feedback_pendente_misto": ns.get("_handle_feedback_pendente_misto"),
                "handle_feedback_pendente": ns.get("_handle_feedback_pendente"),
                "bloquear_playlist_temporariamente": ns.get("_bloquear_playlist_temporariamente"),
                "detectar_mover_playlist_texto": ns.get("detectar_mover_playlist_texto"),
                "mover_item_playlist": ns.get("mover_item_playlist"),
            },
            comandos={
                "processar_comando_deterministico": ns.get("processar_comando_deterministico"),
                "usar_modo_rapido_conversa": ns.get("_usar_modo_rapido_conversa"),
                "interpretar_comando_local_rapido": ns.get("interpretar_comando_local_rapido"),
                "resolver_comando_contextual_forcado": ns.get("_resolver_comando_contextual_forcado"),
                "resolver_reparacao_conversacional": ns.get("_resolver_reparacao_conversacional"),
                "responder_contexto_janela_indisponivel": ns.get("_responder_contexto_janela_indisponivel"),
                "detectar_sugestao_indireta": ns.get("_detectar_sugestao_indireta"),
                "registrar_sugestao_indireta": ns.get("_registrar_sugestao_indireta"),
                "mente_integrada_estado": getattr(ns.get("_estado_compartilhado_runtime"), "mental", {}),
            },
            execucao={
                "executar_intencao": ns.get("executar_intencao"),
                "emitir_resposta_curta": ns.get("_emitir_resposta_curta"),
                "executar_intencao_curta_contextual": ns.get("_executar_intencao_curta_contextual"),
                "falar_com_lipsync": ns.get("falar_com_lipsync"),
                "salvar_memoria": ns.get("salvar_memoria"),
            },
        )
        # O refinamento substitui o dicionario mental por um novo retrato.
        # Permite ao pre-fluxo reconstruir o contexto no mesmo turno, evitando
        # que respondedores locais continuem olhando para o objeto anterior.
        contexto["_recarregar_contexto_inicio"] = self.montar
        contexto["_responder_correcao_temporal"] = lambda texto: responder_correcao_temporal(
            texto,
            ns["_contexto_horario_atual"]() if callable(ns.get("_contexto_horario_atual")) else "",
        )
        contexto["_contexto_horario_atual"] = ns.get("_contexto_horario_atual")
        contexto["_renovar_sessao_conversa"] = ns.get("_renovar_sessao_conversa")
        return contexto


def criar_contexto_inicio_chat_runtime(**kwargs: Any) -> ContextoInicioChatRuntime:
    return ContextoInicioChatRuntime(**kwargs)
