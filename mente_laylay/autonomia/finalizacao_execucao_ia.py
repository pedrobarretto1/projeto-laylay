"""Finalização da execução da resposta da IA da Laylay."""

from __future__ import annotations

from typing import Any, Dict, List

from mente_laylay.integracao.registro_conversa_llm import PedidoModelo


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def _ultima_fala_usuario(messages: Any) -> str:
    if not isinstance(messages, list):
        return ""
    for mensagem in reversed(messages):
        if not isinstance(mensagem, dict):
            continue
        if str(mensagem.get("role") or "").strip().lower() != "user":
            continue
        texto = str(mensagem.get("content") or "").strip()
        if texto:
            return texto
    return ""


def _registrar_interacao_diaria(ctx: Dict[str, Any], usuario: str, fala: str) -> None:
    memoria = _get(ctx, "memoria_inteligente")
    registrar = getattr(memoria, "adicionar_interacao", None)
    if not callable(registrar) or not str(usuario or "").strip() or not str(fala or "").strip():
        return
    try:
        registrar(usuario, fala)
    except Exception as erro:
        # A memória diária nunca pode derrubar a resposta que já foi entregue.
        print(
            "⚠️ [MEMÓRIA] conversa entregue, mas o registro diário falhou: "
            f"{type(erro).__name__}: {erro}"
        )


def _chamar_modelo_finalizacao(ctx: Dict[str, Any], messages: Any) -> str:
    """Usa a porta tipada; aceita o callback antigo só fora da composição nova."""
    modelo = _get(ctx, "modelo_llm")
    executar = getattr(modelo, "executar", None)
    if callable(executar):
        resultado = executar(PedidoModelo.criar(
            messages,
            com_tools=False,
            tipo_chamada="autoria_operacional",
            classe_timeout="rapida",
        ))
        return str(getattr(resultado, "texto", "") or "")
    enviar_legado = _get(ctx, "enviar_mensagem")
    if callable(enviar_legado):
        return str(enviar_legado(
            messages,
            _com_tools=False,
            _tipo_chamada="autoria_operacional",
            _classe_timeout="rapida",
        ) or "")
    return ""


def finalizar_execucao_resposta_ia(
    ctx: Dict[str, Any],
    comandos: List[Dict[str, Any]],
    erros_execucao: List[str],
    fala_limpa_original: str,
    fala_ja_emitida: bool,
    fala_emitida_por_acao: bool,
    fala_salva_no_inicio: bool,
) -> Dict[str, Any]:
    resultado_final = {
        "fala": "",
        "registrar_no_historico": False,
        "tipo": "sem_fala",
    }
    messages = _get(ctx, "messages")
    current_emotion = _get(ctx, "current_emotion", "calma")
    emotion_level = _get(ctx, "emotion_level", 1)
    modelo_llm = _get(ctx, "modelo_llm")
    enviar_mensagem = _get(ctx, "enviar_mensagem")
    limpar_resposta_da_ia = _get(ctx, "limpar_resposta_da_ia")
    falar_com_lipsync = _get(ctx, "falar_com_lipsync")
    verificar_fala_turno = _get(ctx, "verificar_fala_turno")
    salvar_memoria = _get(ctx, "salvar_memoria")
    registrar_autoaprimoramento = _get(ctx, "_registrar_autoaprimoramento")
    registrar_autocorrecao_virtual = _get(ctx, "_registrar_autocorrecao_virtual")
    falhas_consecutivas = _get(ctx, "_falhas_consecutivas")
    max_tentativas = int(_get(ctx, "MAX_TENTATIVAS_AUTOCORRECAO", 3))

    modelo_disponivel = callable(getattr(modelo_llm, "executar", None))
    if (
        not modelo_disponivel
        and not callable(enviar_mensagem)
    ) or not callable(limpar_resposta_da_ia):
        return resultado_final

    if erros_execucao:
        erros_txt = " | ".join(erros_execucao)

        for erro_item in erros_execucao:
            try:
                if callable(registrar_autoaprimoramento):
                    registrar_autoaprimoramento(
                        {},
                        texto=erro_item,
                        sucesso=False,
                        erro=erro_item,
                        contexto=erros_txt,
                        origem="execucao",
                    )
            except Exception as ap_err:
                print(f"⚠️ [AUTOAPRENDIZADO] falha ao registrar erro: {ap_err}")

        chave_erro = erros_txt[:120]
        if isinstance(falhas_consecutivas, dict):
            falhas_consecutivas[chave_erro] = falhas_consecutivas.get(chave_erro, 0) + 1
            tentativas = falhas_consecutivas[chave_erro]
        else:
            tentativas = 1

        print(f"🔄 [AUTOCORREÇÃO] Tentativa {tentativas}/{max_tentativas} | Erros: {erros_txt[:120]}")

        if tentativas >= max_tentativas:
            if isinstance(falhas_consecutivas, dict) and chave_erro in falhas_consecutivas:
                del falhas_consecutivas[chave_erro]
            msg_desistencia = (
                f"System: VOCÊ JÁ TENTOU CORRIGIR ISSO {tentativas} VEZES E CONTINUA FALHANDO. "
                f"O erro é: {erros_txt}. "
                f"Isso já é um problema persistente do Windows (permissão, arquivo em uso, etc). "
                f"Diga ao usuário de forma direta, sem novas tentativas, que você esgotou as opções "
                f"e que é um problema do sistema. Diga explicitamente que o pedido não foi realizado. "
                f"Seja curta, direta e com o seu jeito debochado. "
                f"NÃO gere mais comandos. Não tente de novo. Só avise."
            )
            msg_desistencia += "\n\n[RESPOSTA OBRIGATÓRIA EM JSON: {\"fala\": \"...\", \"comandos\": []}]"
            if isinstance(messages, list):
                messages.append({"role": "user", "content": msg_desistencia})
            print("🛑 [AUTOCORREÇÃO] Limite atingido. Laylay desistindo...")
            try:
                bot_desist_raw = _chamar_modelo_finalizacao(ctx, messages)
                fala_desist, _ = limpar_resposta_da_ia(bot_desist_raw)
                if fala_desist:
                    print(f"Laylay [desistência]: {fala_desist}")
                    if isinstance(messages, list):
                        messages.append({"role": "assistant", "content": fala_desist})
                    if callable(falar_com_lipsync):
                        falar_com_lipsync(fala_desist, "irritada", 3)
                    if callable(salvar_memoria):
                        salvar_memoria()
                    return {
                        "fala": fala_desist,
                        "registrar_no_historico": True,
                        "tipo": "desistencia",
                    }
            except Exception as desist_err:
                print(f"❌ [DESISTÊNCIA] Falha até no aviso: {desist_err}")
        else:
            msg_feedback = (
                f"System: FALHA NA EXECUÇÃO (tentativa {tentativas}/{max_tentativas}). "
                f"As seguintes ações falharam: {erros_txt}. "
                f"O usuário está aguardando. Diga explicitamente que o pedido não foi realizado e avise sobre a falha de forma natural e "
                f"com o seu jeito debochado. Não repita o que já disse antes. "
                f"Peça desculpas curtas e diga o que aconteceu ou pergunte o que ele quer fazer agora."
            )
            msg_feedback += "\n\n[RESPOSTA OBRIGATÓRIA EM JSON: {\"fala\": \"...\", \"comandos\": [...]}]"
            if isinstance(messages, list):
                messages.append({"role": "user", "content": msg_feedback})
            print(f"🔄 [AUTOCORREÇÃO] {len(erros_execucao)} erro(s). Chamando IA para se corrigir...")
            try:
                bot_corr_raw = _chamar_modelo_finalizacao(ctx, messages)
                fala_corr, _cmds_corr = limpar_resposta_da_ia(bot_corr_raw)
                if fala_corr:
                    if bool(_get(ctx, "log_verbose", False)):
                        print(f"Laylay [autocorreção]: {fala_corr}")
                    try:
                        if callable(registrar_autocorrecao_virtual):
                            registrar_autocorrecao_virtual(
                                "execucao",
                                erros_txt,
                                fala_corr,
                                f"{len(erros_execucao)} erro(s) corrigido(s) no loop de execução",
                            )
                    except Exception as reg_err:
                        print(f"⚠️ [AUTOCORREÇÃO] falha ao registrar recompensa: {reg_err}")
                    if isinstance(messages, list):
                        messages.append({"role": "assistant", "content": fala_corr})
                    if callable(falar_com_lipsync):
                        falar_com_lipsync(fala_corr, current_emotion or "calma", emotion_level or 1)
                    if callable(salvar_memoria):
                        salvar_memoria()
                    return {
                        "fala": fala_corr,
                        "registrar_no_historico": True,
                        "tipo": "autocorrecao",
                    }
            except Exception as feedback_err:
                print(f"❌ [AUTOCORREÇÃO] Falha no loop de feedback: {feedback_err}")
    else:
        for cmd_ok in (comandos or []):
            if isinstance(cmd_ok, dict) and isinstance(falhas_consecutivas, dict):
                k = f"{cmd_ok.get('acao','')}|{cmd_ok.get('alvo','')}"[:120]
                falhas_consecutivas.pop(k, None)

        if fala_limpa_original and not comandos and not fala_ja_emitida and not fala_salva_no_inicio and not fala_emitida_por_acao:
            texto_usuario = _ultima_fala_usuario(messages)
            if callable(verificar_fala_turno):
                verificacao = verificar_fala_turno(fala_limpa_original, origem="ia_final")
                if isinstance(verificacao, dict):
                    if not verificacao.get("aceita", True):
                        contingencia = str(
                            verificacao.get("fala_contingencia") or ""
                        ).strip()
                        if not contingencia:
                            return resultado_final
                        fala_limpa_original = contingencia
                    else:
                        fala_limpa_original = str(
                            verificacao.get("fala") or fala_limpa_original
                        ).strip()
            # A mesma fala será emitida pela fronteira oficial abaixo, que já
            # formata o balão e publica no Terminal 2.x. Este print cru fazia
            # cada resposta conversacional aparecer duas vezes no modo limpo;
            # fica disponível somente no log técnico explícito.
            if bool(_get(ctx, "log_verbose", False)):
                print(f"Laylay: {fala_limpa_original}")
            if isinstance(messages, list):
                messages.append({"role": "assistant", "content": fala_limpa_original})
            fala_entregue = True
            if callable(falar_com_lipsync):
                fala_entregue = falar_com_lipsync(
                    fala_limpa_original,
                    current_emotion or "calma",
                    emotion_level or 1,
                ) is not False
            if fala_entregue:
                _registrar_interacao_diaria(ctx, texto_usuario, fala_limpa_original)
            return {
                "fala": fala_limpa_original,
                "registrar_no_historico": True,
                "tipo": "conversa",
                "audio_entregue": bool(fala_entregue),
            }
    return resultado_final
