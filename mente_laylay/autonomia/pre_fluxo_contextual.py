"""Helpers compartilhados para o pre-fluxo conversacional da Laylay."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Tuple


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def texto_eh_conversa_social_sem_comando(ctx: Dict[str, Any], texto: str) -> bool:
    texto_social_curto = _get(ctx, "_texto_social_curto")
    texto_conversa_casual_sem_acao = _get(ctx, "_texto_conversa_casual_sem_acao")
    texto_tem_comando_explicito = _get(ctx, "_texto_tem_comando_explicito")
    t = str(texto or "").strip()
    if not t:
        return False
    eh_social = (
        (callable(texto_social_curto) and texto_social_curto(t))
        or (callable(texto_conversa_casual_sem_acao) and texto_conversa_casual_sem_acao(t))
    )
    if not eh_social:
        return False
    if callable(texto_tem_comando_explicito) and texto_tem_comando_explicito(t):
        return False
    return True


def texto_deve_evitar_llm_de_comando(ctx: Dict[str, Any], texto: str) -> bool:
    """Evita mandar conversa casual para o analisador de comando."""
    texto_tem_comando_explicito = _get(ctx, "_texto_tem_comando_explicito")
    texto_conversa_contextual_sem_comando = _get(ctx, "_texto_conversa_contextual_sem_comando")
    t = str(texto or "").strip()
    if not t:
        return True
    if callable(texto_tem_comando_explicito) and texto_tem_comando_explicito(t):
        return False
    if texto_eh_conversa_social_sem_comando(ctx, t):
        return True
    if callable(texto_conversa_contextual_sem_comando) and texto_conversa_contextual_sem_comando(t):
        return True
    return False


def analisar_intencao_com_porteiro(
    ctx: Dict[str, Any],
    texto: str,
) -> Tuple[str, Dict[str, Any] | None]:
    """Chama o analisador IA-first somente quando o porteiro permitir."""
    t = str(texto or "").strip()
    if not t:
        return "vazio", None
    if texto_deve_evitar_llm_de_comando(ctx, t):
        return "evitar", None

    analisar_intencao = _get(ctx, "analisar_intencao")
    if not callable(analisar_intencao):
        return "sem_analisador", None

    try:
        resultado = analisar_intencao(t)
    except Exception:
        return "falha", None

    if not isinstance(resultado, dict):
        return "falha", None

    intent = str(resultado.get("intent") or "").upper().strip()
    if intent in {"", "NONE", "NENHUM"}:
        return "sem_intencao", None

    return "ok", resultado


def emitir_conversa_curta(
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


def responder_conversa_social_curta(
    ctx: Dict[str, Any],
    texto_usuario: str,
    *,
    emocao: str,
    nivel: int,
) -> Tuple[bool, str]:
    t = str(texto_usuario or "").strip()
    if not texto_eh_conversa_social_sem_comando(ctx, t):
        return False, ""

    texto_social_curto = _get(ctx, "_texto_social_curto")
    texto_conversa_casual_sem_acao = _get(ctx, "_texto_conversa_casual_sem_acao")
    resposta_conversa_rapida_local = _get(ctx, "_resposta_conversa_rapida_local")
    if not callable(resposta_conversa_rapida_local):
        return False, ""

    fala = resposta_conversa_rapida_local(t)
    if callable(texto_social_curto) and texto_social_curto(t):
        return emitir_conversa_curta(ctx, t, fala, emocao=emocao, nivel=nivel), "conversa_social_curta"
    if callable(texto_conversa_casual_sem_acao) and texto_conversa_casual_sem_acao(t):
        return emitir_conversa_curta(ctx, t, fala, emocao=emocao, nivel=nivel), "conversa_casual_sem_acao"
    return False, ""


def processar_pergunta_curta_contextual(
    ctx: Dict[str, Any],
    texto_usuario: str,
) -> Tuple[bool, str]:
    resolver_pergunta_curta_contextual_intencao = _get(ctx, "_resolver_pergunta_curta_contextual_intencao")
    executar_intencao_curta_contextual = _get(ctx, "_executar_intencao_curta_contextual")
    executar_intencao = _get(ctx, "executar_intencao")

    t = str(texto_usuario or "").strip()
    if not callable(resolver_pergunta_curta_contextual_intencao):
        return False, ""

    intencao_curta = resolver_pergunta_curta_contextual_intencao(t)
    if not isinstance(intencao_curta, dict) or not str(intencao_curta.get("intent") or "").strip():
        return False, ""

    if callable(executar_intencao_curta_contextual):
        ok = bool(executar_intencao_curta_contextual(
            intencao_curta,
            t,
            origem="pre-ia",
            contexto_autoaprimoramento="pergunta curta dependente do topico",
        ))
        return ok, "pergunta_curta_contextual" if ok else ""

    ok = bool(executar_intencao(intencao_curta, t)) if callable(executar_intencao) else False
    return ok, "pergunta_curta_contextual_fallback" if ok else ""


def processar_pergunta_aberta(
    ctx: Dict[str, Any],
    texto_usuario: str,
    *,
    emocao: str,
    nivel: int,
) -> Tuple[bool, str]:
    texto_responde_pergunta_aberta = _get(ctx, "_texto_responde_pergunta_aberta")
    responder_pergunta_aberta = _get(ctx, "_responder_pergunta_aberta")

    t = str(texto_usuario or "").strip()
    if not callable(texto_responde_pergunta_aberta) or not texto_responde_pergunta_aberta(t):
        return False, ""
    fala = responder_pergunta_aberta(t) if callable(responder_pergunta_aberta) else ""
    return emitir_conversa_curta(ctx, t, fala, emocao=emocao, nivel=nivel), "pergunta_aberta"


def processar_elogio_ou_agradecimento(
    ctx: Dict[str, Any],
    texto_usuario: str,
    *,
    emocao: str,
    nivel: int,
) -> Tuple[bool, str]:
    parece_elogio_ou_agradecimento_curto = _get(ctx, "_parece_elogio_ou_agradecimento_curto")
    responder_agradecimento_ou_elogio = _get(ctx, "_responder_agradecimento_ou_elogio")
    t = str(texto_usuario or "").strip()
    if not callable(parece_elogio_ou_agradecimento_curto) or not parece_elogio_ou_agradecimento_curto(t):
        return False, ""
    fala = responder_agradecimento_ou_elogio(t) if callable(responder_agradecimento_ou_elogio) else ""
    return emitir_conversa_curta(ctx, t, fala, emocao=emocao, nivel=nivel), "elogio_ou_agradecimento"


def processar_bloqueio_playlist_temporario(
    ctx: Dict[str, Any],
    texto_usuario: str,
) -> Tuple[bool, str]:
    texto_bloqueia_playlist_agora = _get(ctx, "_texto_bloqueia_playlist_agora")
    bloquear_playlist_temporariamente = _get(ctx, "_bloquear_playlist_temporariamente")
    t = str(texto_usuario or "").strip()
    if not callable(texto_bloqueia_playlist_agora) or not texto_bloqueia_playlist_agora(t):
        return False, ""
    if callable(bloquear_playlist_temporariamente):
        try:
            bloquear_playlist_temporariamente()
        except Exception:
            pass
    ok = emitir_conversa_curta(
        ctx,
        t,
        "Fechado, sem playlist agora. Guardei a caixinha de som.",
        emocao="calma",
        nivel=1,
    )
    return ok, "bloqueio_playlist" if ok else ""


def processar_feedback_pendente(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    handle_feedback_pendente_misto = _get(ctx, "_handle_feedback_pendente_misto")
    handle_feedback_pendente = _get(ctx, "_handle_feedback_pendente")
    t = str(texto_usuario or "").strip()
    if callable(handle_feedback_pendente_misto) and handle_feedback_pendente_misto(t):
        return True, "feedback_pendente_misto"
    if callable(handle_feedback_pendente) and handle_feedback_pendente(t):
        return True, "feedback_pendente"
    return False, ""


def processar_fluxo_musical_generico(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    texto_pede_direcao_musical_generica = _get(ctx, "_texto_pede_direcao_musical_generica")
    responder_pedido_direcao_musical_generica = _get(ctx, "_responder_pedido_direcao_musical_generica")
    processar_confirmacao_sugestao_musical = _get(ctx, "_processar_confirmacao_sugestao_musical")
    t = str(texto_usuario or "").strip()

    if callable(processar_confirmacao_sugestao_musical) and processar_confirmacao_sugestao_musical(t):
        return True, "confirmacao_sugestao_musical"

    if callable(texto_pede_direcao_musical_generica) and texto_pede_direcao_musical_generica(t):
        if callable(responder_pedido_direcao_musical_generica):
            ok = bool(responder_pedido_direcao_musical_generica(t))
            return ok, "direcao_musical_generica" if ok else ""
        return True, "direcao_musical_generica"

    return False, ""


def resolver_contexto_unificado(ctx: Dict[str, Any], texto: str) -> Tuple[Dict[str, Any] | None, str]:
    resolver_comando_contextual_forcado = _get(ctx, "_resolver_comando_contextual_forcado")
    if not callable(resolver_comando_contextual_forcado):
        return None, ""
    try:
        comando_contextual = resolver_comando_contextual_forcado(str(texto or "").strip())
    except Exception:
        return None, ""
    if not isinstance(comando_contextual, dict):
        return None, ""
    rota = str(comando_contextual.get("_rota_contextual") or "GERAL").upper()
    intent_limpo = dict(comando_contextual)
    intent_limpo.pop("_rota_contextual", None)
    if not str(intent_limpo.get("intent") or "").strip():
        return None, ""
    return intent_limpo, rota


def processar_contexto_unificado_precoce(
    ctx: Dict[str, Any],
    texto_usuario: str,
    *,
    origem: str = "pre-ia",
) -> Tuple[bool, str]:
    try:
        comando_contextual, rota = resolver_contexto_unificado(ctx, texto_usuario)
        if comando_contextual:
            ok = executar_resultado_contextual(
                ctx,
                comando_contextual,
                texto_usuario,
                log_rota=f"ROTEADOR CONTEXTO-{rota} [{origem}]",
                origem_resultado=f"contexto_{rota.lower()}_{str(origem).replace('-', '_')}",
                contexto_autoaprimoramento=f"continuidade contextual de {rota.lower()}",
            )
            return ok, f"continuidade_{rota.lower()}" if ok else ""
    except Exception as e:
        print(f"⚠️ [CONTEXTO-UNIFICADO] falha no fluxo {origem}: {e}")
    return False, ""


def processar_janela_indisponivel(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    responder_contexto_janela_indisponivel = _get(ctx, "_responder_contexto_janela_indisponivel")
    t = str(texto_usuario or "").strip()
    if callable(responder_contexto_janela_indisponivel) and responder_contexto_janela_indisponivel(t):
        return True, "janela_indisponivel"
    return False, ""


def processar_aprendizado_apelido(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    processar_aprendizado_apelido_imediato = _get(ctx, "_processar_aprendizado_apelido_imediato")
    t = str(texto_usuario or "").strip()
    if callable(processar_aprendizado_apelido_imediato) and processar_aprendizado_apelido_imediato(t):
        return True, "aprendizado_apelido"
    return False, ""


def processar_comando_deterministico_precoce(
    ctx: Dict[str, Any],
    texto_usuario: str,
    *,
    origem: str = "pre-ia",
) -> Tuple[bool, str]:
    processar_comando_deterministico = _get(ctx, "processar_comando_deterministico")
    t = str(texto_usuario or "").strip()
    if callable(processar_comando_deterministico) and processar_comando_deterministico(t, origem):
        return True, f"comando_deterministico_{str(origem).replace('-', '_')}"
    return False, ""


def executar_resultado_contextual(
    ctx: Dict[str, Any],
    resultado: Dict[str, Any] | None,
    texto_usuario: str,
    *,
    origem_resultado: str,
    contexto_autoaprimoramento: str,
    log_rota: str,
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
            origem=origem_resultado,
        )
    return True


def executar_comando_local_rapido(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, Dict[str, Any] | None]:
    interpretar_comando_local_rapido = _get(ctx, "interpretar_comando_local_rapido")
    executar_intencao = _get(ctx, "executar_intencao")
    registrar_resultado_execucao = _get(ctx, "_registrar_resultado_execucao")
    registrar_autoaprimoramento = _get(ctx, "_registrar_autoaprimoramento")

    comando_local = interpretar_comando_local_rapido(str(texto_usuario or "").strip()) if callable(interpretar_comando_local_rapido) else None
    if not isinstance(comando_local, dict) or not str(comando_local.get("intent") or "").strip():
        return False, None

    executou = bool(executar_intencao(comando_local, texto_usuario)) if callable(executar_intencao) else False
    if callable(registrar_resultado_execucao):
        registrar_resultado_execucao(comando_local, texto_usuario, executou, origem="comando_local_rapido")
    if executou and callable(registrar_autoaprimoramento):
        registrar_autoaprimoramento(
            comando_local,
            texto_usuario,
            True,
            contexto="comando local rapido",
            origem="comando_local_rapido",
        )
    return True, comando_local


def processar_comando_local_rapido_precoce(ctx: Dict[str, Any], texto_usuario: str) -> Tuple[bool, str]:
    try:
        houve_comando_local, comando_local = executar_comando_local_rapido(ctx, texto_usuario)
    except Exception as e:
        print(f"⚠️ [FOCO LOCAL] falha ao executar comando local: {e}")
        return False, ""
    if houve_comando_local and isinstance(comando_local, dict):
        return True, "comando_local_rapido"
    return False, ""


def processar_execucao_pratica_precoce(
    ctx: Dict[str, Any],
    texto_usuario: str,
    *,
    origem: str = "pre-ia",
) -> Tuple[bool, str]:
    """Agrupa rotas praticas para diminuir competicao entre roteadores."""
    etapas = [
        lambda: processar_contexto_unificado_precoce(ctx, texto_usuario, origem=origem),
        lambda: processar_janela_indisponivel(ctx, texto_usuario),
        lambda: processar_comando_deterministico_precoce(ctx, texto_usuario, origem=origem),
        lambda: processar_comando_local_rapido_precoce(ctx, texto_usuario),
    ]
    for etapa in etapas:
        ok, nome = etapa()
        if ok:
            return True, nome or "execucao_pratica"
    return False, ""


def executar_pipeline_pre_fluxo(
    ctx: Dict[str, Any],
    texto_usuario: str,
    etapas: Iterable[Callable[[], Tuple[bool, str]]],
    *,
    log_cb: Callable[[str, str], None] | None = None,
) -> bool:
    for etapa in etapas:
        try:
            ok, nome = etapa()
        except Exception as e:
            print(f"⚠️ [PRE-FLUXO] falha em etapa compartilhada: {e}")
            continue
        if ok:
            if callable(log_cb):
                log_cb(nome or "etapa_sem_nome", "")
            return True
    return False
