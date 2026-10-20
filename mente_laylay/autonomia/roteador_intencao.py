"""Roteador principal de intencoes da Laylay."""

from __future__ import annotations

from typing import Any, Dict
from mente_laylay.personalidade.falas_variadas import escolher as _escolher_fala_variada
from mente_laylay.personalidade.politica_resistencia import (
    avaliar_resistencia_contextual,
    mesma_identidade_pedido_resistencia,
    projetar_pedido_resistencia,
)
from mente_laylay.autonomia.executor_janelas import (
    DependenciasExecutorJanelas,
    executar_intencao_janelas as _executar_intencao_janelas,
)
from mente_laylay.autonomia.executor_navegador import (
    DependenciasExecutorNavegador,
    executar_intencao_navegador as _executar_intencao_navegador,
)
from mente_laylay.autonomia.executor_audio import (
    DependenciasExecutorAudio,
    executar_intencao_audio as _executar_intencao_audio,
)
from mente_laylay.autonomia.executor_corpo import (
    DependenciasExecutorCorpo, executar_intencao_corpo,
)
from mente_laylay.autonomia.executor_agenda import (
    DependenciasExecutorAgenda,
    executar_intencao_agenda as _executar_intencao_agenda,
)
from mente_laylay.autonomia.executor_informacoes import (
    DependenciasExecutorInformacoes,
    executar_intencao_informacoes as _executar_intencao_informacoes,
)
from mente_laylay.autonomia.executor_sistema import (
    DependenciasExecutorSistema,
    executar_intencao_sistema as _executar_intencao_sistema,
)
from mente_laylay.autonomia.executor_musical import (
    DependenciasExecutorMusical,
    executar_intencao_musical as _executar_intencao_musical,
)
from mente_laylay.autonomia.executor_playlists import (
    DependenciasExecutorPlaylists,
    executar_intencao_playlists as _executar_intencao_playlists,
)
from mente_laylay.autonomia.executor_cancelamentos import (
    DependenciasExecutorCancelamentos,
    executar_intencao_cancelamentos as _executar_intencao_cancelamentos,
)
from mente_laylay.autonomia.executor_integracoes import (
    DependenciasExecutorIntegracoes,
    executar_intencao_integracoes as _executar_intencao_integracoes,
)
from mente_laylay.autonomia.validacao_ambiente import ValidadorAmbiente
from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.autonomia.rota_musical import RotaMusical
from mente_laylay.autonomia.classificacao_habilidade import (
    classificar_habilidade_intent,
    extrair_alvo_mental,
)
from mente_laylay.percepcao.modo_jogo import pedido_foco_explicito
from mente_laylay.cognicao.modalidade_turno import autoriza_execucao_efetiva
from mente_laylay.memoria_mental.resultado_acao import (
    CHAVE_RESULTADO_OPERACIONAL_PUBLICADO,
    ResultadoAcao,
    interpretar_tratamento_operacional,
    marcar_tratamento_operacional,
)


def _get(ctx: Dict[str, Any], nome: str, default=None):
    return ctx.get(nome, default)


def bloquear_por_emocao(intent: str, texto_original: str, ctx: Dict[str, Any]) -> bool:
    # Estado expressivo não é uma autorização para vetar uma ação. Uma recusa
    # por redundância exige recibo atual do alvo e decisão do owner da ação;
    # emoção categórica e histórico anterior não provam esse estado agora.
    return False


def executar_intencao(resultado: dict, texto_original: str, ctx: Dict[str, Any]) -> bool:
    if not isinstance(resultado, dict):
        return False

    # Recursão começa outro adaptador. O canal comum não pode permanecer
    # vinculado à publicação do pai quando o filho ainda não publicou nada.
    canal = _get(ctx, "falar_com_lipsync")
    if (getattr(canal, "__func__", None) is AdaptadorResultadoOperacional.falar_texto_da_invocacao
        and type(getattr(canal, "__self__", None)) is AdaptadorResultadoOperacional):
        ctx = dict(ctx, falar_com_lipsync=canal.__self__.ctx.get("falar_com_lipsync"))

    destino = _get(ctx, "_target_from_params", lambda p, t="": "pc_a")
    registrar_mente_curta = _get(ctx, "_registrar_mente_curta")
    falar = _get(ctx, "falar_com_lipsync")

    def _reg(*args, **kwargs):
        if callable(registrar_mente_curta):
            return registrar_mente_curta(*args, **kwargs)
        return None

    intent = str(resultado.get("intent") or "").upper().strip()
    raw_params = resultado.get("params")
    params = dict(raw_params) if isinstance(raw_params, dict) else {}
    execucao_silenciosa = params.pop("_execucao_silenciosa", None) is True
    if execucao_silenciosa:
        # Controles tipados do painel já têm feedback de recebido/executando/
        # confirmado. Eles continuam no executor e no contrato de resultado,
        # mas não entram na LLM nem geram uma fala artificial no chat.
        ctx = dict(ctx)
        ctx["falar_com_lipsync"] = None
        ctx["enviar_mensagem"] = None
        ctx["_registrar_mente_curta"] = None
        falar = None
        registrar_mente_curta = None
    if intent not in {"CORPO_MOVER", "CORPO_PARAR", "CORPO_COMPANHIA"} and pedido_foco_explicito(texto_original):
        params["permitir_foco"] = True
    destino_val = destino(params, texto_original) if callable(destino) else "pc_a"
    validacao_ambiente = ValidadorAmbiente(ctx, destino_val, texto_original)
    rota_musical = RotaMusical(ctx, destino_val, texto_original)
    adaptador_resultado = AdaptadorResultadoOperacional(
        resultado, params, texto_original, destino_val, ctx
    )
    # Escopo só desta invocação; registro global e contexto do chamador
    # permanecem intactos. Métodos por status já usam o mesmo owner de fala.
    ctx = dict(ctx, falar_com_lipsync=(adaptador_resultado.falar_texto_da_invocacao
                                     if callable(ctx.get("falar_com_lipsync")) else None))

    def _finalizar_despacho_moderno(despacho) -> bool:
        """Impede que executor moderno sem receipt seja rebaixado a bool legado."""
        tratamento = interpretar_tratamento_operacional(
            resultado,
            despacho.retorno,
        )
        if tratamento.legado:
            marcar_tratamento_operacional(
                resultado,
                tratado=True,
                executou=None,
                confirmado=None,
                status="tratado_sem_receipt",
                resultado_publicado=False,
                retorno_legado=bool(despacho.retorno),
            )
        return bool(despacho.retorno)

    alvo_mental = extrair_alvo_mental(params)
    habilidade = classificar_habilidade_intent(intent)
    _reg(texto_original, "", intent, alvo_mental, destino_val, habilidade)

    pendencias = ctx.get("_pendencia_acao_runtime")
    pedido_resistido = projetar_pedido_resistencia(
        intent=intent, params=params, destino_resolvido=destino_val,
    )
    if (
        intent == "MEDIA_CONTROL"
        and params.get("acao") == "repeat_toggle"
        and autoriza_execucao_efetiva(ctx.get("turno_atual"))
    ):
        try:
            anterior = pendencias.obter() if callable(getattr(pendencias, "obter", None)) else None
        except Exception:
            anterior = None
        metadados_anteriores = anterior.get("metadados") if isinstance(anterior, dict) else None
        pedido_anterior = metadados_anteriores.get("pedido") if isinstance(metadados_anteriores, dict) else None
        if (
            isinstance(anterior, dict)
            and anterior.get("origem") == "resistencia_personalidade"
            and mesma_identidade_pedido_resistencia(pedido_anterior, pedido_resistido)
        ):
            encerrada = False
            if anterior.get("status") == "ativa":
                try:
                    encerrada = pendencias.concluir(
                        str(anterior.get("id") or ""),
                        "substituida_por_novo_pedido",
                        status_esperado="ativa",
                    )
                except Exception:
                    encerrada = False
            if anterior.get("status") == "em_processamento" or not encerrada:
                if callable(falar):
                    falar("Já estou tratando esse controle de repetição.", "calma", 1)
                    marcar_tratamento_operacional(
                        resultado,
                        tratado=True,
                        executou=False,
                        confirmado=False,
                        status="pendencia_em_processamento",
                        resultado_publicado=False,
                        retorno_legado=True,
                    )
                    return True
                return False

    decisao_resistencia = avaliar_resistencia_contextual(
        intent=intent,
        params=params,
        texto_usuario=texto_original,
        estado_emocional={
            "current_emotion": ctx.get("current_emotion"),
            "emotion_level": ctx.get("emotion_level"),
            "episodio_emocional": ctx.get("episodio_emocional"),
        },
        turno=ctx.get("turno_atual"),
        ultima_referencia_resistida=str(ctx.get("resistencia_p17_ref") or ""),
        referencias_resistidas=ctx.get("resistencias_p17_refs") or (),
    )
    if decisao_resistencia.resistir:
        registrar_resistencia = ctx.get("registrar_resistencia_p17")
        try:
            sem_pendencia = callable(getattr(pendencias, "obter", None)) and not pendencias.obter()
        except Exception:
            sem_pendencia = False
        if (
            callable(falar)
            and callable(getattr(pendencias, "registrar", None))
            and callable(registrar_resistencia)
            and sem_pendencia
            and pedido_resistido is not None
        ):
            pergunta = (
                "Vou segurar essa mudança opcional por um instante. "
                "Quer que eu altere a repetição mesmo assim?"
            )
            try:
                pendencia = pendencias.registrar(
                    origem="resistencia_personalidade",
                    acao="retomar_controle_midia",
                    pergunta=pergunta,
                    referencia=decisao_resistencia.evidencia_ref,
                    dominio=decisao_resistencia.dominio,
                    metadados={
                        "intent": intent,
                        "acao": decisao_resistencia.acao,
                        "id_solicitacao": adaptador_resultado.id_solicitacao,
                        "pedido": pedido_resistido,
                        "evento_ref": decisao_resistencia.evidencia_ref,
                        "sobrevive_comando_independente": True,
                    },
                    motivo=decisao_resistencia.motivo,
                    ttl_s=90.0,
                )
            except Exception:
                pendencia = None
            if pendencia:
                adiamento_publicado = False
                try:
                    if registrar_resistencia(decisao_resistencia.evidencia_ref) is not True:
                        raise RuntimeError("registro_resistencia_recusado")
                    registrar_resultado = ctx.get("_registrar_resultado_execucao")
                    if callable(registrar_resultado):
                        # A política confirma somente a criação da pendência.
                        # Não existe receipt de mídia nem evento emocional de
                        # efeito nesta transição; o aceite usará o executor.
                        contrato_adiamento = ResultadoAcao(
                            intent=intent,
                            status="aguardando_confirmacao",
                            params=dict(pedido_resistido["params"]),
                            executou=False,
                            confirmado=False,
                            origem="politica",
                            texto_usuario=texto_original,
                            id_solicitacao=adaptador_resultado.id_solicitacao,
                            detalhe=decisao_resistencia.motivo,
                            contexto={
                                "pendencia_id": str(pendencia.get("id") or ""),
                                "evento_ref": decisao_resistencia.evidencia_ref,
                            },
                            evidencia_confirmacao=(
                                "Pendência canônica registrada: "
                                f"{pendencia.get('id')}; causa={decisao_resistencia.evidencia_ref}"
                            ),
                        )
                        if registrar_resultado(
                            contrato_adiamento,
                            texto_original,
                            False,
                            origem="politica",
                            status="aguardando_confirmacao",
                        ) is False:
                            raise RuntimeError("publicacao_adiamento_recusada")
                        adiamento_publicado = True
                    falar(pergunta, "brava", 3)
                except Exception:
                    try:
                        pendencias.concluir(str(pendencia.get("id") or ""), "resistencia_indisponivel")
                    except Exception:
                        pass
                else:
                    if adiamento_publicado:
                        resultado[CHAVE_RESULTADO_OPERACIONAL_PUBLICADO] = adaptador_resultado.id_solicitacao
                    marcar_tratamento_operacional(
                        resultado,
                        tratado=True,
                        executou=False,
                        confirmado=False,
                        status="aguardando_confirmacao" if adiamento_publicado else "aguardando_insistencia",
                        resultado_publicado=adiamento_publicado,
                        retorno_legado=True,
                    )
                    return True

    despacho_corpo = executar_intencao_corpo(
        intent, params, texto_original, ctx,
        DependenciasExecutorCorpo(marcar_resultado=adaptador_resultado.marcar_resultado,
                                 falar_por_status=adaptador_resultado.falar_por_status,
                                 id_solicitacao=adaptador_resultado.id_solicitacao),
    )
    if despacho_corpo.tratado:
        return _finalizar_despacho_moderno(despacho_corpo)

    despacho_janelas = _executar_intencao_janelas(
        intent,
        params,
        destino_val,
        ctx,
        DependenciasExecutorJanelas(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
            falar_resultado_janela=adaptador_resultado.falar_resultado_janela,
            alvo_preciso_para_aba=validacao_ambiente.alvo_preciso_para_aba,
            esperar_aba_fechar=validacao_ambiente.esperar_aba_fechar,
            esperar_programa_fechar=validacao_ambiente.esperar_programa_fechar,
            executar_recursivo=executar_intencao,
        ),
        texto_original=texto_original,
    )
    if despacho_janelas.tratado:
        return _finalizar_despacho_moderno(despacho_janelas)

    despacho_navegador = _executar_intencao_navegador(
        intent,
        params,
        texto_original,
        destino_val,
        ctx,
        DependenciasExecutorNavegador(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
            abrir_url_com_validacao=validacao_ambiente.abrir_url_com_validacao,
            alvo_preciso_para_aba=validacao_ambiente.alvo_preciso_para_aba,
            esperar_aba_fechar=validacao_ambiente.esperar_aba_fechar,
            esperar_programa_fechar=validacao_ambiente.esperar_programa_fechar,
            executar_recursivo=executar_intencao,
        ),
    )
    if despacho_navegador.tratado:
        return _finalizar_despacho_moderno(despacho_navegador)

    despacho_audio = _executar_intencao_audio(
        intent,
        params,
        destino_val,
        ctx,
        DependenciasExecutorAudio(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
        ),
    )
    if despacho_audio.tratado:
        return _finalizar_despacho_moderno(despacho_audio)

    despacho_agenda = _executar_intencao_agenda(
        intent,
        params,
        texto_original,
        ctx,
        DependenciasExecutorAgenda(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
        ),
    )
    if despacho_agenda.tratado:
        return _finalizar_despacho_moderno(despacho_agenda)

    despacho_informacoes = _executar_intencao_informacoes(
        intent,
        params,
        texto_original,
        ctx,
        DependenciasExecutorInformacoes(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
            registrar_mente=_reg,
        ),
    )
    if despacho_informacoes.tratado:
        return _finalizar_despacho_moderno(despacho_informacoes)

    despacho_sistema = _executar_intencao_sistema(
        intent,
        params,
        destino_val,
        ctx,
        DependenciasExecutorSistema(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
        ),
    )
    if despacho_sistema.tratado:
        return _finalizar_despacho_moderno(despacho_sistema)

    despacho_musical = _executar_intencao_musical(
        intent,
        params,
        texto_original,
        ctx,
        DependenciasExecutorMusical(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            abrir_url_musical=rota_musical.abrir_detalhado,
            registrar_mente=_reg,
            falar_por_status=adaptador_resultado.falar_por_status,
            musica_leitura=ctx.get("_registro_musica_leitura_runtime"),
            musica_operacoes=ctx.get("_registro_musica_operacoes_runtime"),
        ),
    )
    if despacho_musical.tratado:
        return despacho_musical.retorno

    despacho_playlists = _executar_intencao_playlists(
        intent,
        params,
        texto_original,
        destino_val,
        ctx,
        DependenciasExecutorPlaylists(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
            abrir_url_musical=rota_musical.abrir,
            contexto_fala=adaptador_resultado.contexto_fala,
            musica_leitura=ctx.get("_registro_musica_leitura_runtime"),
            musica_operacoes=ctx.get("_registro_musica_operacoes_runtime"),
        ),
    )
    if despacho_playlists.tratado:
        return despacho_playlists.retorno

    despacho_cancelamentos = _executar_intencao_cancelamentos(
        intent,
        ctx,
        DependenciasExecutorCancelamentos(
            marcar_resultado=adaptador_resultado.marcar_resultado
        ),
    )
    if despacho_cancelamentos.tratado:
        return _finalizar_despacho_moderno(despacho_cancelamentos)

    despacho_integracoes = _executar_intencao_integracoes(
        intent,
        resultado,
        params,
        texto_original,
        destino_val,
        ctx,
        DependenciasExecutorIntegracoes(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
            contexto_fala=adaptador_resultado.contexto_fala,
            iot=ctx.get("_registro_iot_runtime"),
            arquivos_leitura=ctx.get("_registro_arquivos_leitura_runtime"),
            arquivos_mutacao=ctx.get("_registro_arquivos_mutacao_runtime"),
        ),
    )
    if despacho_integracoes.tratado:
        if intent in {"MEDIA_CONTROL", "MUSIC_STATUS"}:
            return despacho_integracoes.retorno
        return _finalizar_despacho_moderno(despacho_integracoes)

    if intent == "RESUMIR_PAGINA":
        # O resumo assíncrono é iniciado pelo fluxo prioritário, que possui o
        # loop do WebSocket e registra o resultado real ao concluir. Se este
        # intent chegar ao roteador sem aquele executor, a ação não ocorreu.
        adaptador_resultado.marcar_resultado(
            "executor_indisponivel",
            executou=False,
            confirmado=False,
        )
        if callable(falar):
            falar(
                "Não consegui iniciar a leitura da página por este caminho.",
                "calma",
                1,
            )
        return False

    if callable(falar):
        falar(_escolher_fala_variada([
            "Eu não fechei tua intenção direito agora. Tenta falar de outro jeito pra mim.",
            "Me perdi um pouco aqui. Tenta falar de outro jeito.",
            "Não entendi direito. Repete pra mim com outras palavras.",
            "Quase peguei o fio, mas ele escapou. Me fala de novo sem pressa.",
        ]), "calma", 1)
    marcar_tratamento_operacional(
        resultado,
        tratado=True,
        executou=False,
        confirmado=False,
        status="intent_nao_reconhecida",
        resultado_publicado=False,
        retorno_legado=True,
    )
    return True
