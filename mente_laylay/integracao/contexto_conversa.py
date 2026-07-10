"""Integradores de contexto conversacional da Laylay.

Este modulo nao executa acoes.
Ele apenas organiza o retrato curto usado pelos fluxos de conversa.
"""

from __future__ import annotations

from typing import Any, Callable, Dict


def montar_contexto_conversa_natural(
    *,
    current_emotion: str,
    mente_integrada_estado: Dict[str, Any] | None,
    ultimo_topico_conversa: str,
    foco_vivo: Dict[str, Any] | None,
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
    acalmar_emocao: Callable[..., Any] | None = None,
) -> Dict[str, Any]:
    return {
        "current_emotion": current_emotion,
        "mente_integrada_estado": dict(mente_integrada_estado or {}),
        "ultimo_topico_conversa": str(ultimo_topico_conversa or "").strip(),
        "foco_vivo": dict(foco_vivo or {}),
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
        "_acalmar_emocao": acalmar_emocao,
    }


def montar_contexto_fala_curta(
    *,
    current_emotion: str,
    mente_integrada_estado: Dict[str, Any] | None,
) -> Dict[str, Any]:
    mente = dict(mente_integrada_estado or {})
    return {
        "current_emotion": current_emotion,
        "ultima_habilidade": str(mente.get("ultima_habilidade", "") or "").strip(),
        "ultimo_alvo": str(mente.get("ultimo_alvo", "") or "").strip(),
    }


def montar_contexto_gate_conversa(
    *,
    mente_integrada_estado: Dict[str, Any] | None,
    foco_vivo: Dict[str, Any] | None,
    ultimo_topico_conversa: str,
) -> Dict[str, Any]:
    return {
        "mente": dict(mente_integrada_estado or {}),
        "foco_vivo": dict(foco_vivo or {}),
        "ultimo_topico": str(ultimo_topico_conversa or "").strip(),
    }


def montar_contexto_inicio_chat(
    *,
    messages: Any,
    current_emotion: str,
    emotion_level: int,
    processar_aprendizado_apelido_imediato: Callable[..., Any] | None,
    refinar_contexto_mental: Callable[..., Any] | None,
    processar_comando_deterministico: Callable[..., Any] | None,
    usar_modo_rapido_conversa: Callable[..., Any] | None,
    interpretar_comando_local_rapido: Callable[..., Any] | None,
    executar_intencao: Callable[..., Any] | None,
    registrar_autoaprimoramento: Callable[..., Any] | None,
    texto_social_curto: Callable[..., Any] | None,
    texto_conversa_casual_sem_acao: Callable[..., Any] | None,
    texto_tem_comando_explicito: Callable[..., Any] | None,
    texto_bloqueia_playlist_agora: Callable[..., Any] | None,
    resposta_conversa_rapida_local: Callable[..., Any] | None,
    parece_elogio_ou_agradecimento_curto: Callable[..., Any] | None,
    responder_agradecimento_ou_elogio: Callable[..., Any] | None,
    resolver_pergunta_curta_contextual_intencao: Callable[..., Any] | None,
    texto_responde_pergunta_aberta: Callable[..., Any] | None,
    responder_pergunta_aberta: Callable[..., Any] | None,
    texto_pede_direcao_musical_generica: Callable[..., Any] | None,
    responder_pedido_direcao_musical_generica: Callable[..., Any] | None,
    processar_confirmacao_sugestao_musical: Callable[..., Any] | None,
    handle_feedback_pendente_misto: Callable[..., Any] | None,
    handle_feedback_pendente: Callable[..., Any] | None,
    bloquear_playlist_temporariamente: Callable[..., Any] | None,
    resolver_comando_janela_contextual_forcado: Callable[..., Any] | None,
    resolver_comando_midia_contextual_forcado: Callable[..., Any] | None,
    resolver_comando_arquivo_contextual_forcado: Callable[..., Any] | None,
    resolver_comando_acao_geral_contextual_forcado: Callable[..., Any] | None,
    resolver_comando_contextual_forcado: Callable[..., Any] | None,
    responder_contexto_janela_indisponivel: Callable[..., Any] | None,
    emitir_resposta_curta: Callable[..., Any] | None,
    executar_intencao_curta_contextual: Callable[..., Any] | None,
    registrar_mente_curta: Callable[..., Any] | None,
    registrar_resultado_execucao: Callable[..., Any] | None,
    falar_com_lipsync: Callable[..., Any] | None,
    salvar_memoria: Callable[..., Any] | None,
) -> Dict[str, Any]:
    return {
        "messages": messages,
        "current_emotion": current_emotion,
        "emotion_level": emotion_level,
        "_processar_aprendizado_apelido_imediato": processar_aprendizado_apelido_imediato,
        "_refinar_contexto_mental": refinar_contexto_mental,
        "processar_comando_deterministico": processar_comando_deterministico,
        "_usar_modo_rapido_conversa": usar_modo_rapido_conversa,
        "interpretar_comando_local_rapido": interpretar_comando_local_rapido,
        "executar_intencao": executar_intencao,
        "_registrar_autoaprimoramento": registrar_autoaprimoramento,
        "_texto_social_curto": texto_social_curto,
        "_texto_conversa_casual_sem_acao": texto_conversa_casual_sem_acao,
        "_texto_tem_comando_explicito": texto_tem_comando_explicito,
        "_texto_bloqueia_playlist_agora": texto_bloqueia_playlist_agora,
        "_resposta_conversa_rapida_local": resposta_conversa_rapida_local,
        "_parece_elogio_ou_agradecimento_curto": parece_elogio_ou_agradecimento_curto,
        "_responder_agradecimento_ou_elogio": responder_agradecimento_ou_elogio,
        "_resolver_pergunta_curta_contextual_intencao": resolver_pergunta_curta_contextual_intencao,
        "_texto_responde_pergunta_aberta": texto_responde_pergunta_aberta,
        "_responder_pergunta_aberta": responder_pergunta_aberta,
        "_texto_pede_direcao_musical_generica": texto_pede_direcao_musical_generica,
        "_responder_pedido_direcao_musical_generica": responder_pedido_direcao_musical_generica,
        "_processar_confirmacao_sugestao_musical": processar_confirmacao_sugestao_musical,
        "_handle_feedback_pendente_misto": handle_feedback_pendente_misto,
        "_handle_feedback_pendente": handle_feedback_pendente,
        "_bloquear_playlist_temporariamente": bloquear_playlist_temporariamente,
        "_resolver_comando_janela_contextual_forcado": resolver_comando_janela_contextual_forcado,
        "_resolver_comando_midia_contextual_forcado": resolver_comando_midia_contextual_forcado,
        "_resolver_comando_arquivo_contextual_forcado": resolver_comando_arquivo_contextual_forcado,
        "_resolver_comando_acao_geral_contextual_forcado": resolver_comando_acao_geral_contextual_forcado,
        "_resolver_comando_contextual_forcado": resolver_comando_contextual_forcado,
        "_responder_contexto_janela_indisponivel": responder_contexto_janela_indisponivel,
        "_emitir_resposta_curta": emitir_resposta_curta,
        "_executar_intencao_curta_contextual": executar_intencao_curta_contextual,
        "_registrar_mente_curta": registrar_mente_curta,
        "_registrar_resultado_execucao": registrar_resultado_execucao,
        "falar_com_lipsync": falar_com_lipsync,
        "salvar_memoria": salvar_memoria,
        "mensagens_append": messages.append if hasattr(messages, "append") else None,
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
        "_processar_aprendizado_apelido_imediato": memoria.get("processar_aprendizado_apelido_imediato"),
        "_refinar_contexto_mental": memoria.get("refinar_contexto_mental"),
        "_registrar_autoaprimoramento": memoria.get("registrar_autoaprimoramento"),
        "_registrar_mente_curta": memoria.get("registrar_mente_curta"),
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
        "_handle_feedback_pendente_misto": musica_feedback.get("handle_feedback_pendente_misto"),
        "_handle_feedback_pendente": musica_feedback.get("handle_feedback_pendente"),
        "_detectar_mover_playlist_texto": musica_feedback.get("detectar_mover_playlist_texto"),
        "_mover_item_playlist": musica_feedback.get("mover_item_playlist"),
        "_bloquear_playlist_temporariamente": musica_feedback.get("bloquear_playlist_temporariamente"),
        "processar_comando_deterministico": comandos.get("processar_comando_deterministico"),
        "_usar_modo_rapido_conversa": comandos.get("usar_modo_rapido_conversa"),
        "interpretar_comando_local_rapido": comandos.get("interpretar_comando_local_rapido"),
        "_resolver_comando_janela_contextual_forcado": comandos.get("resolver_comando_janela_contextual_forcado"),
        "_resolver_comando_midia_contextual_forcado": comandos.get("resolver_comando_midia_contextual_forcado"),
        "_resolver_comando_arquivo_contextual_forcado": comandos.get("resolver_comando_arquivo_contextual_forcado"),
        "_resolver_comando_acao_geral_contextual_forcado": comandos.get("resolver_comando_acao_geral_contextual_forcado"),
        "_resolver_comando_contextual_forcado": comandos.get("resolver_comando_contextual_forcado"),
        "_responder_contexto_janela_indisponivel": comandos.get("responder_contexto_janela_indisponivel"),
        "executar_intencao": execucao.get("executar_intencao"),
        "_emitir_resposta_curta": execucao.get("emitir_resposta_curta"),
        "_executar_intencao_curta_contextual": execucao.get("executar_intencao_curta_contextual"),
        "falar_com_lipsync": execucao.get("falar_com_lipsync"),
        "salvar_memoria": execucao.get("salvar_memoria"),
        "mensagens_append": messages.append if hasattr(messages, "append") else None,
    }
    return contexto
