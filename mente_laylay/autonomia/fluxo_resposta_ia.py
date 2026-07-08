"""Fluxo principal de resposta da IA da Laylay."""

from __future__ import annotations

import re
from typing import Any, Dict


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def _emitir_conversa_curta(
    ctx: Dict[str, Any],
    texto_usuario: str,
    fala: str,
    *,
    emocao: str,
    nivel: int,
) -> bool:
    fala = str(fala or "").strip()
    if not fala:
        return False

    emitir_resposta_curta = _get(ctx, "_emitir_resposta_curta")
    if callable(emitir_resposta_curta):
        emitir_resposta_curta(
            texto_usuario,
            fala,
            emocao=emocao or "calma",
            nivel=nivel or 1,
            habilidade="conversa",
        )
        return True

    mensagens_append = _get(ctx, "mensagens_append")
    falar_com_lipsync = _get(ctx, "falar_com_lipsync")
    registrar_mente_curta = _get(ctx, "_registrar_mente_curta")
    salvar_memoria = _get(ctx, "salvar_memoria")

    if callable(mensagens_append):
        mensagens_append({"role": "user", "content": str(texto_usuario or "")})
        mensagens_append({"role": "assistant", "content": fala})
    if callable(falar_com_lipsync):
        falar_com_lipsync(fala, emocao or "calma", nivel or 1)
    if callable(registrar_mente_curta):
        registrar_mente_curta(str(texto_usuario or ""), fala, habilidade="conversa")
    if callable(salvar_memoria):
        salvar_memoria()
    return True


def _executar_intencao_contextual(
    ctx: Dict[str, Any],
    resultado: Dict[str, Any] | None,
    texto_usuario: str,
    *,
    log_prefixo: str,
    log_rota: str,
    origem_resultado: str,
    contexto_autoaprimoramento: str,
) -> bool:
    if not isinstance(resultado, dict) or not str(resultado.get("intent") or "").strip():
        return False

    executar_intencao = _get(ctx, "executar_intencao")
    registrar_resultado_execucao = _get(ctx, "_registrar_resultado_execucao")
    registrar_autoaprimoramento = _get(ctx, "_registrar_autoaprimoramento")

    print(f"⚡ [{log_rota}] {resultado}")
    executou = bool(executar_intencao(resultado, texto_usuario)) if callable(executar_intencao) else False
    if callable(registrar_resultado_execucao):
        registrar_resultado_execucao(resultado, texto_usuario, executou, origem=origem_resultado)
    if executou and callable(registrar_autoaprimoramento):
        registrar_autoaprimoramento(
            resultado,
            texto_usuario,
            True,
            contexto=contexto_autoaprimoramento,
            origem=log_prefixo,
        )
    return True


def processar_inicio_fluxo_resposta_ia(ctx: Dict[str, Any], texto: str) -> bool:
    messages = _get(ctx, "messages")
    current_emotion = _get(ctx, "current_emotion", "calma")
    emotion_level = _get(ctx, "emotion_level", 1)
    t = str(texto or "").strip()
    if not t:
        return True

    refinar_contexto_mental = _get(ctx, "_refinar_contexto_mental")
    if callable(refinar_contexto_mental):
        refinar_contexto_mental(t)

    texto_social_curto = _get(ctx, "_texto_social_curto")
    texto_conversa_casual_sem_acao = _get(ctx, "_texto_conversa_casual_sem_acao")
    texto_tem_comando_explicito = _get(ctx, "_texto_tem_comando_explicito")
    resposta_conversa_rapida_local = _get(ctx, "_resposta_conversa_rapida_local")
    texto_pede_direcao_musical_generica = _get(ctx, "_texto_pede_direcao_musical_generica")
    responder_pedido_direcao_musical_generica = _get(ctx, "_responder_pedido_direcao_musical_generica")
    processar_confirmacao_sugestao_musical = _get(ctx, "_processar_confirmacao_sugestao_musical")
    handle_feedback_pendente_misto = _get(ctx, "_handle_feedback_pendente_misto")
    handle_feedback_pendente = _get(ctx, "_handle_feedback_pendente")
    texto_bloqueia_playlist_agora = _get(ctx, "_texto_bloqueia_playlist_agora")
    bloquear_playlist_temporariamente = _get(ctx, "_bloquear_playlist_temporariamente")
    parece_elogio_ou_agradecimento_curto = _get(ctx, "_parece_elogio_ou_agradecimento_curto")
    responder_agradecimento_ou_elogio = _get(ctx, "_responder_agradecimento_ou_elogio")
    resolver_pergunta_curta_contextual_intencao = _get(ctx, "_resolver_pergunta_curta_contextual_intencao")
    texto_responde_pergunta_aberta = _get(ctx, "_texto_responde_pergunta_aberta")
    responder_pergunta_aberta = _get(ctx, "_responder_pergunta_aberta")
    resolver_comando_contextual_forcado = _get(ctx, "_resolver_comando_contextual_forcado")
    responder_contexto_janela_indisponivel = _get(ctx, "_responder_contexto_janela_indisponivel")
    executar_intencao_curta_contextual = _get(ctx, "_executar_intencao_curta_contextual")
    executar_intencao = _get(ctx, "executar_intencao")

    def _log(etapa: str, detalhe: str = "") -> None:
        extra = f" | {detalhe}" if detalhe else ""
        print(f"🧭 [PRE-FLUXO] {etapa}{extra}")

    if callable(parece_elogio_ou_agradecimento_curto) and parece_elogio_ou_agradecimento_curto(t):
        _log("elogio_ou_agradecimento")
        fala = responder_agradecimento_ou_elogio(t) if callable(responder_agradecimento_ou_elogio) else ""
        return _emitir_conversa_curta(ctx, t, fala, emocao=current_emotion or "calma", nivel=emotion_level or 1)

    if callable(texto_bloqueia_playlist_agora) and texto_bloqueia_playlist_agora(t):
        _log("bloqueio_playlist")
        if callable(bloquear_playlist_temporariamente):
            try:
                bloquear_playlist_temporariamente()
            except Exception:
                pass
        fala = "Fechado, sem playlist agora. Guardei a caixinha de som."
        return _emitir_conversa_curta(ctx, t, fala, emocao="calma", nivel=1)

    if callable(handle_feedback_pendente_misto) and handle_feedback_pendente_misto(t):
        _log("feedback_pendente_misto")
        return True
    if callable(handle_feedback_pendente) and handle_feedback_pendente(t):
        _log("feedback_pendente")
        return True

    if callable(processar_confirmacao_sugestao_musical) and processar_confirmacao_sugestao_musical(t):
        _log("confirmacao_sugestao_musical")
        return True

    if callable(texto_pede_direcao_musical_generica) and texto_pede_direcao_musical_generica(t):
        _log("direcao_musical_generica")
        if callable(responder_pedido_direcao_musical_generica):
            return bool(responder_pedido_direcao_musical_generica(t))
        return True

    if callable(resolver_pergunta_curta_contextual_intencao):
        intencao_curta = resolver_pergunta_curta_contextual_intencao(t)
        if isinstance(intencao_curta, dict) and str(intencao_curta.get("intent") or "").strip():
            try:
                if callable(executar_intencao_curta_contextual):
                    if bool(executar_intencao_curta_contextual(intencao_curta, t, origem="pre-ia", contexto_autoaprimoramento="pergunta curta dependente do topico")):
                        _log("pergunta_curta_contextual", str(intencao_curta.get("intent") or ""))
                        return True
                else:
                    executar_intencao = _get(ctx, "executar_intencao")
                    if bool(executar_intencao(intencao_curta, t)) if callable(executar_intencao) else False:
                        _log("pergunta_curta_contextual_fallback", str(intencao_curta.get("intent") or ""))
                        return True
            except Exception as e:
                print(f"⚠️ [PERGUNTA-CURTA] falha no fluxo pre-ia: {e}")

    if callable(texto_responde_pergunta_aberta) and texto_responde_pergunta_aberta(t):
        _log("pergunta_aberta")
        fala = responder_pergunta_aberta(t) if callable(responder_pergunta_aberta) else ""
        return _emitir_conversa_curta(ctx, t, fala, emocao=current_emotion or "calma", nivel=emotion_level or 1)

    if callable(resolver_comando_contextual_forcado):
        try:
            comando_contextual = resolver_comando_contextual_forcado(t)
            if comando_contextual:
                rota = str(comando_contextual.get("_rota_contextual") or "GERAL").upper()
                intent_limpo = dict(comando_contextual)
                intent_limpo.pop("_rota_contextual", None)
                _log(f"continuidade_{rota.lower()}", str(intent_limpo.get("intent") or ""))
                return _executar_intencao_contextual(
                    ctx,
                    intent_limpo,
                    t,
                    log_prefixo="pre-ia",
                    log_rota=f"ROTEADOR CONTEXTO-{rota} [pre-ia]",
                    origem_resultado=f"contexto_{rota.lower()}_pre_ia",
                    contexto_autoaprimoramento=f"continuidade contextual de {rota.lower()}",
                )
        except Exception as e:
            print(f"⚠️ [CONTEXTO-UNIFICADO] falha no fluxo pre-ia: {e}")

    if callable(responder_contexto_janela_indisponivel) and responder_contexto_janela_indisponivel(t):
        _log("janela_indisponivel")
        return True

    if callable(texto_social_curto) and texto_social_curto(t) and not (callable(texto_tem_comando_explicito) and texto_tem_comando_explicito(t)):
        _log("conversa_social_curta")
        fala = resposta_conversa_rapida_local(t) if callable(resposta_conversa_rapida_local) else ""
        return _emitir_conversa_curta(ctx, t, fala, emocao=current_emotion or "calma", nivel=emotion_level or 1)

    if callable(texto_conversa_casual_sem_acao) and texto_conversa_casual_sem_acao(t) and not (callable(texto_tem_comando_explicito) and texto_tem_comando_explicito(t)):
        _log("conversa_casual_sem_acao")
        fala = resposta_conversa_rapida_local(t) if callable(resposta_conversa_rapida_local) else ""
        return _emitir_conversa_curta(ctx, t, fala, emocao=current_emotion or "calma", nivel=emotion_level or 1)

    processar_aprendizado_apelido_imediato = _get(ctx, "_processar_aprendizado_apelido_imediato")
    if callable(processar_aprendizado_apelido_imediato) and processar_aprendizado_apelido_imediato(t):
        _log("aprendizado_apelido")
        return True

    processar_comando_deterministico = _get(ctx, "processar_comando_deterministico")
    if callable(processar_comando_deterministico) and processar_comando_deterministico(t, "pre-ia"):
        _log("comando_deterministico_pre_ia")
        return True

    usar_modo_rapido_conversa = _get(ctx, "_usar_modo_rapido_conversa")
    modo_rapido = bool(usar_modo_rapido_conversa(t)) if callable(usar_modo_rapido_conversa) else False

    interpretar_comando_local_rapido = _get(ctx, "interpretar_comando_local_rapido")
    comando_local = interpretar_comando_local_rapido(t) if callable(interpretar_comando_local_rapido) else None
    if comando_local:
        try:
            executou = bool(executar_intencao(comando_local, t)) if callable(executar_intencao) else False
        except Exception as e:
            print(f"⚠️ [FOCO LOCAL] falha ao executar comando local: {e}")
            executou = False
        if executou:
            _log("comando_local_rapido", str(comando_local.get("intent") or ""))
            try:
                if callable(registrar_autoaprimoramento):
                    registrar_autoaprimoramento(comando_local, t, True, contexto="ia local rapido", origem="ia")
            except Exception as e_auto:
                print(f"⚠️ [AUTOAPRENDIZADO] falha ao registrar sucesso local: {e_auto}")
            return True

    _log("sem_vencedor_precoce", "segue para ia principal")
    print(f"🧠 [IA] Gerando resposta para: '{texto}'")
    return False
