"""Orquestracao do ciclo principal de resposta da Laylay."""

from __future__ import annotations

import threading
import time
import traceback
from typing import Any, Callable, Dict

from mente_laylay.autonomia.pre_fluxo_contextual import responder_conversa_social_curta
from mente_laylay.integracao.registro_conversa_llm import PedidoModelo
from mente_laylay.personalidade.proporcao_resposta import limite_tokens_resposta


LIMITE_TOKENS_ESTIMADOS_PRAZO_RAPIDO = 1200


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    return ctx.get(key, default) if isinstance(ctx, dict) else default


def _classe_timeout_resposta(
    mensagens: list[dict[str, Any]],
    *,
    modo_rapido: bool,
    limite_saida_tokens: int,
) -> str:
    """Separa compactação do prompt do prazo concedido ao transporte.

    Um prompt pode usar o contrato compacto e ainda carregar evidência ou
    histórico suficientes para exceder oito segundos num modelo local frio.
    O custo aproximado governa somente o timeout; formato e conteúdo continuam
    sob responsabilidade do preparador canônico.
    """
    if not modo_rapido:
        return "normal"
    caracteres = sum(
        len(str(item.get("content") or ""))
        for item in mensagens
        if isinstance(item, dict)
    )
    tokens_estimados = (caracteres + 3) // 4 + max(0, int(limite_saida_tokens))
    return (
        "contextual"
        if tokens_estimados > LIMITE_TOKENS_ESTIMADOS_PRAZO_RAPIDO
        else "rapida"
    )


def _registrar_metrica(
    ctx: Dict[str, Any],
    componente: str,
    duracao_ms: float,
    sucesso: bool,
    **metadados: Any,
) -> None:
    registrar = _get(ctx, "registrar_metrica_diagnostico")
    if not callable(registrar):
        return
    try:
        registrar(componente, duracao_ms, sucesso, **metadados)
    except TypeError:
        # Adaptadores antigos e dublês de teste aceitam somente os três
        # argumentos históricos. Telemetria enriquecida nunca quebra o turno.
        registrar(componente, duracao_ms, sucesso)


def _atualizar_trace(ctx: Dict[str, Any], turno_id: str, **campos: Any) -> None:
    atualizar = _get(ctx, "atualizar_trace_diagnostico")
    if callable(atualizar):
        try:
            atualizar(turno_id, **campos)
        except Exception:
            pass


class RespostaIARuntime:
    """Coordena conversa, comandos e finalizacao usando o contexto da mente."""

    def __init__(self, *, contexto_getter: Callable[[], Dict[str, Any]], log: Callable[..., Any] = print) -> None:
        self._contexto_getter = contexto_getter
        self._log = log
        self._process_lock = threading.RLock()
        self._sequencia_turnos = 0

    def _contexto(self) -> Dict[str, Any]:
        try:
            contexto = self._contexto_getter()
            return contexto if isinstance(contexto, dict) else {}
        except Exception:
            return {}

    def processar(
        self,
        texto: str,
        ainda_atual_cb: Callable[[], bool] | None = None,
        origem: str = "desconhecida",
    ) -> None:
        # Entradas podem chegar por voz, terminal e hotkey ao mesmo tempo. Uma
        # mente única precisa concluir uma frase antes de interpretar a próxima.
        with self._process_lock:
            ctx = self._contexto()
            inicio_total = time.perf_counter()
            sucesso = False
            self._sequencia_turnos += 1
            trace_id = f"turno-{self._sequencia_turnos:06d}"
            iniciar_trace = _get(ctx, "iniciar_trace_diagnostico")
            if callable(iniciar_trace):
                try:
                    iniciar_trace(trace_id, origem=origem, rota="roteamento")
                except Exception:
                    pass
            iniciar_orcamento_llm = _get(ctx, "iniciar_orcamento_llm_turno")
            if callable(iniciar_orcamento_llm):
                try:
                    iniciar_orcamento_llm(
                        trace_id,
                        classe="normal",
                        ainda_atual_cb=ainda_atual_cb,
                    )
                except Exception:
                    pass
            iniciar_turno_voz = _get(ctx, "iniciar_turno_voz")
            finalizar_turno_voz = _get(ctx, "finalizar_turno_voz")
            if callable(iniciar_turno_voz):
                iniciar_turno_voz()
            try:
                resultado_turno = self._processar_serializado(
                    texto,
                    ainda_atual_cb=ainda_atual_cb,
                    origem=origem,
                    trace_id=trace_id,
                )
                sucesso = resultado_turno is not False
            finally:
                _registrar_metrica(
                    ctx,
                    "turno_total",
                    (time.perf_counter() - inicio_total) * 1000.0,
                    sucesso,
                    turno_id=trace_id,
                )
                finalizar_trace = _get(ctx, "finalizar_trace_diagnostico")
                if callable(finalizar_trace):
                    try:
                        finalizar_trace(trace_id, sucesso=sucesso)
                    except Exception:
                        pass
                finalizar_orcamento_llm = _get(ctx, "finalizar_orcamento_llm_turno")
                if callable(finalizar_orcamento_llm):
                    try:
                        finalizar_orcamento_llm(trace_id, sucesso=sucesso)
                    except Exception:
                        pass
                if callable(finalizar_turno_voz):
                    finalizar_turno_voz()

    def _processar_serializado(
        self,
        texto: str,
        *,
        ainda_atual_cb: Callable[[], bool] | None = None,
        origem: str = "desconhecida",
        trace_id: str = "",
    ) -> None:
        ctx = self._contexto()
        inicio_serializado = time.perf_counter()
        t = str(texto or "").strip()
        if not t:
            return

        observar_feedback_presenca = _get(ctx, "observar_feedback_presenca")
        if callable(observar_feedback_presenca):
            try:
                observar_feedback_presenca(t)
            except Exception as erro:
                # Aprendizado de presença nunca pode impedir o turno principal,
                # mas também não deve desaparecer sem diagnóstico.
                self._log(
                    "⚠️ [PRESENÇA:FEEDBACK] observação ignorada: "
                    f"{type(erro).__name__}: {erro}"
                )
                registrar_falha = _get(ctx, "registrar_falha_diagnostico")
                if callable(registrar_falha):
                    registrar_falha(
                        "presenca_feedback", "falha_observacao", erro=erro,
                    )

        if callable(ainda_atual_cb):
            try:
                if not ainda_atual_cb():
                    self._log("🧠 [TURNO] entrada antiga descartada antes do processamento.")
                    return True
            except Exception:
                pass

        marcar_inicio_turno = _get(ctx, "marcar_inicio_turno")
        if callable(marcar_inicio_turno):
            if origem != "desconhecida":
                marcar_inicio_turno(t, origem=origem)
            else:
                marcar_inicio_turno(t)
        sincronizar_turno_voz = _get(ctx, "sincronizar_turno_voz")
        if callable(sincronizar_turno_voz):
            sincronizar_turno_voz()
        obter_turno = _get(ctx, "obter_turno_atual")
        turno = obter_turno() if callable(obter_turno) else {}
        turno_conversa_id = str(
            (turno.get("id") if isinstance(turno, dict) else "") or ""
        ).strip() or trace_id or f"resposta-ia-{self._sequencia_turnos}"
        estado_conversa_turno = None
        turno_conversa_iniciado = False
        if isinstance(turno, dict):
            self._log(
                "🧠 [TURNO] "
                f"modalidade={turno.get('modalidade') or '-'} | "
                f"geral={turno.get('modalidade_geral') or '-'} | "
                f"atos={turno.get('atos') or []} | "
                f"operacional={turno.get('texto_operacional') or '-'} | "
                f"autoriza={bool(turno.get('autoriza_execucao'))} | "
                f"esclarecer={bool(turno.get('requer_esclarecimento'))} | "
                f"motivo={turno.get('motivo_decisao') or turno.get('motivo') or '-'}"
            )
        atualizar_plano = _get(ctx, "atualizar_plano_turno")

        def marcar_fase(fase: str) -> None:
            if callable(atualizar_plano):
                atualizar_plano(fase)
            rotas_fase = {
                "tratado_modo_chat": "modo_chat",
                "tratado_prioritario": "comando_prioritario",
                "tratado_pre_fluxo": "pre_fluxo",
                "resposta_tecnica_suprimida": "resposta_tecnica",
            }
            dados_trace = {"fase": fase}
            if fase in rotas_fase:
                dados_trace["rota"] = rotas_fase[fase]
            elif fase.startswith("tratado_social"):
                dados_trace["rota"] = "social_local"
            _atualizar_trace(ctx, trace_id, **dados_trace)

        def resposta_ainda_atual() -> bool:
            if not callable(ainda_atual_cb):
                return True
            try:
                return bool(ainda_atual_cb())
            except Exception:
                return True

        def descartar_se_obsoleta() -> bool:
            if resposta_ainda_atual():
                return False
            self._log("🧠 [TURNO] resposta antiga descartada porque uma nova mensagem já chegou.")
            return True

        try:
            modo_chat_runtime = _get(ctx, "modo_chat_runtime")
            if modo_chat_runtime is not None and modo_chat_runtime.processar_texto(t):
                marcar_fase("tratado_modo_chat")
                return

            comandos_prioritarios = _get(ctx, "processar_comandos_prioritarios")
            if callable(comandos_prioritarios) and comandos_prioritarios(t):
                marcar_fase("tratado_prioritario")
                return

            contexto_inicio_cb = _get(ctx, "contexto_inicio")
            contexto_inicio = contexto_inicio_cb() if callable(contexto_inicio_cb) else {}
            inicio_fluxo = _get(ctx, "processar_inicio_fluxo")
            if callable(inicio_fluxo) and inicio_fluxo(contexto_inicio, t):
                marcar_fase("tratado_pre_fluxo")
                return

            if _get(ctx, "modo_chat", False) or _get(ctx, "conversa_ativa", False):
                self._log("🗨️ [CHAT] Modo chat ativo, mas seguindo o mesmo cérebro para comandos e conversa.")

            modo_rapido_cb = _get(ctx, "usar_modo_rapido")
            modo_rapido = bool(modo_rapido_cb(t)) if callable(modo_rapido_cb) else False
            instrucao_rapida = ""
            depende_contexto_cb = _get(ctx, "texto_depende_de_contexto")
            try:
                depende_contexto = bool(depende_contexto_cb(t)) if callable(depende_contexto_cb) else False
            except Exception:
                depende_contexto = False

            # Durante uma partida, cumprimentos e respostas sociais muito
            # curtas não justificam acordar um modelo de 6+ GB. O mesmo
            # cérebro local já sabe responder a esses atos e preserva o fio
            # da conversa. Comandos continuam vencendo acima deste ponto e
            # perguntas compostas continuam reservadas para a LLM.
            modo_jogo_ativo = _get(ctx, "modo_jogo_ativo", False)
            try:
                em_jogo = bool(
                    modo_jogo_ativo()
                    if callable(modo_jogo_ativo)
                    else modo_jogo_ativo
                )
            except Exception:
                em_jogo = False
            if em_jogo and modo_rapido:
                contexto_social = dict(contexto_inicio or {})
                contexto_social.update(ctx)
                try:
                    tratado_social, rota_social = responder_conversa_social_curta(
                        contexto_social,
                        t,
                        emocao=str(
                            contexto_inicio.get("current_emotion") or "calma"
                        ),
                        nivel=int(contexto_inicio.get("emotion_level") or 1),
                    )
                except Exception as erro:
                    tratado_social, rota_social = False, ""
                    self._log(
                        "⚠️ [CONVERSA:JOGO] atalho social local ignorado: "
                        f"{type(erro).__name__}: {erro}"
                    )
                if tratado_social:
                    marcar_fase(f"tratado_{rota_social or 'social_jogo'}")
                    self._log("⚡ [CONVERSA:JOGO] resposta social local imediata.")
                    return

            _registrar_metrica(
                ctx,
                "roteamento_pre_llm",
                (time.perf_counter() - inicio_serializado) * 1000.0,
                True,
                turno_id=trace_id,
                rota="llm_rapida" if modo_rapido else "llm_normal",
            )

            prompt_runtime = (
                _get(ctx, "preparacao_conversa")
                or _get(ctx, "contexto_prompt_runtime")
            )
            if not modo_rapido:
                if prompt_runtime is None:
                    raise RuntimeError("Contexto do prompt ainda não foi inicializado.")
                inicio_prompt = time.perf_counter()
                if callable(getattr(prompt_runtime, "preparar_pacote", None)):
                    pacote_prompt = prompt_runtime.preparar_pacote(t)
                    mensagens_novas = [dict(item) for item in pacote_prompt.mensagens]
                else:
                    mensagens_novas, _prompt_com_humor = prompt_runtime.preparar(t)
                _registrar_metrica(
                    ctx,
                    "preparacao_prompt",
                    (time.perf_counter() - inicio_prompt) * 1000.0,
                    True,
                    turno_id=trace_id,
                    rota="llm_normal",
                )
                estado_conversa = _get(ctx, "estado_conversa")
                if callable(getattr(estado_conversa, "substituir", None)):
                    estado_conversa.substituir(mensagens_novas)
                else:
                    set_messages = _get(ctx, "set_messages")
                    if callable(set_messages):
                        set_messages(mensagens_novas)
            elif callable(getattr(prompt_runtime, "preparar_instrucao_rapida", None)):
                inicio_prompt_rapido = time.perf_counter()
                try:
                    instrucao_rapida = str(
                        prompt_runtime.preparar_instrucao_rapida(t) or ""
                    ).strip()
                    _registrar_metrica(
                        ctx,
                        "preparacao_prompt_rapido",
                        (time.perf_counter() - inicio_prompt_rapido) * 1000.0,
                        True,
                        turno_id=trace_id,
                        rota="llm_rapida",
                    )
                except Exception as erro:
                    instrucao_rapida = ""
                    self._log(
                        "⚠️ [PROMPT:RÁPIDO] contrato de fala indisponível: "
                        f"{type(erro).__name__}"
                    )
                    registrar_falha = _get(ctx, "registrar_falha_diagnostico")
                    if callable(registrar_falha):
                        registrar_falha(
                            "prompt_rapido", "falha_contrato_fala", erro=erro,
                        )

            estado_conversa = _get(ctx, "estado_conversa")
            estado_conversa_turno = estado_conversa
            iniciar_turno = getattr(estado_conversa, "iniciar_turno", None)
            if callable(iniciar_turno):
                mensagens = iniciar_turno(turno_conversa_id, t)
                turno_conversa_iniciado = True
            elif callable(getattr(estado_conversa, "mensagens", None)):
                mensagens = estado_conversa.mensagens()
                mensagens.append({"role": "user", "content": t})
                substituir = getattr(estado_conversa, "substituir", None)
                if callable(substituir):
                    substituir(mensagens)
                turno_conversa_iniciado = True
            else:
                get_messages = _get(ctx, "get_messages")
                mensagens = get_messages() if callable(get_messages) else []
            if not isinstance(mensagens, list):
                mensagens = []
            if not turno_conversa_iniciado:
                mensagens.append({"role": "user", "content": t})

            # A instrução rápida participa apenas deste pedido. Ela não entra
            # no histórico e por isso não reaparece como memória ou como fala
            # do usuário em turnos futuros.
            mensagens_modelo = [dict(item) for item in mensagens if isinstance(item, dict)]
            if instrucao_rapida:
                indice_usuario = len(mensagens_modelo)
                for indice in range(len(mensagens_modelo) - 1, -1, -1):
                    if str(mensagens_modelo[indice].get("role") or "").casefold() == "user":
                        indice_usuario = indice
                        break
                mensagens_modelo.insert(indice_usuario, {
                    "role": "system",
                    "content": instrucao_rapida,
                })

            inicio_llm = time.perf_counter()
            sucesso_llm = False
            limite_tokens = limite_tokens_resposta(
                t,
                modo_rapido=modo_rapido,
                depende_contexto=depende_contexto,
            )
            classe_timeout = _classe_timeout_resposta(
                mensagens_modelo,
                modo_rapido=modo_rapido,
                limite_saida_tokens=limite_tokens,
            )
            rota_llm = "llm_rapida" if modo_rapido else "llm_normal"
            configurar_orcamento_llm = _get(ctx, "configurar_orcamento_llm_turno")
            if callable(configurar_orcamento_llm):
                try:
                    configurar_orcamento_llm(
                        classe=classe_timeout,
                    )
                except Exception:
                    pass
            _atualizar_trace(
                ctx,
                trace_id,
                rota=rota_llm,
                tipo_chamada="principal",
            )
            modelo_llm = _get(ctx, "modelo_llm")
            try:
                if callable(getattr(modelo_llm, "executar", None)):
                    pedido_modelo = PedidoModelo.criar(
                        mensagens_modelo,
                        com_tools=False,
                        max_tokens=limite_tokens,
                        modo_rapido=modo_rapido,
                        permitir_conversa_modo_jogo=bool(
                            _get(ctx, "modo_chat", False) or _get(ctx, "conversa_ativa", False)
                        ),
                        prioridade_interativa=True,
                        tipo_chamada="principal",
                        classe_timeout=classe_timeout,
                    )
                    resultado_modelo = modelo_llm.executar(pedido_modelo)
                    bot_raw = resultado_modelo.texto
                    sucesso_llm = bool(getattr(resultado_modelo, "sucesso", True))
                else:
                    enviar_mensagem = _get(ctx, "enviar_mensagem")
                    if not callable(enviar_mensagem):
                        raise RuntimeError("modelo LLM ainda não foi inicializado.")
                    bot_raw = enviar_mensagem(
                        mensagens_modelo,
                        _com_tools=False,
                        max_tokens=limite_tokens,
                        modo_rapido=modo_rapido,
                        _permitir_conversa_modo_jogo=bool(
                            _get(ctx, "modo_chat", False)
                            or _get(ctx, "conversa_ativa", False)
                        ),
                        _prioridade_interativa=True,
                        _tipo_chamada="principal",
                        _classe_timeout=classe_timeout,
                    )
                    sucesso_llm = True
            finally:
                _registrar_metrica(
                    ctx,
                    "llm_resposta_principal",
                    (time.perf_counter() - inicio_llm) * 1000.0,
                    sucesso_llm,
                    turno_id=trace_id,
                    rota=rota_llm,
                    tipo_chamada="principal",
                )
            self._log(f"🤖 [IA] Resposta bruta recebida (tamanho {len(str(bot_raw))} chars)")
            if descartar_se_obsoleta():
                abortar = getattr(estado_conversa_turno, "abortar_turno", None)
                if callable(abortar) and turno_conversa_iniciado:
                    abortar(turno_conversa_id)
                return True

            preparar_resposta = _get(ctx, "preparar_resposta")
            if not callable(preparar_resposta):
                raise RuntimeError("Preparador de resposta ainda não foi inicializado.")
            inicio_preparacao = time.perf_counter()
            sucesso_preparacao = False
            try:
                resposta = preparar_resposta(t, bot_raw)
                sucesso_preparacao = True
            finally:
                _registrar_metrica(
                    ctx,
                    "pos_processamento_resposta",
                    (time.perf_counter() - inicio_preparacao) * 1000.0,
                    sucesso_preparacao,
                    turno_id=trace_id,
                    rota=rota_llm,
                )
            if descartar_se_obsoleta():
                abortar = getattr(estado_conversa_turno, "abortar_turno", None)
                if callable(abortar) and turno_conversa_iniciado:
                    abortar(turno_conversa_id)
                return True
            bot_raw = resposta.get("resposta_bruta", bot_raw)
            suprimir_fala = bool(resposta.get("suprimir_fala"))
            fala_limpa_original = (
                "" if suprimir_fala
                else str(resposta.get("fala") or _get(ctx, "fallback_fala", "Tô por aqui."))
            )
            comandos = list(resposta.get("comandos") or [])
            # A decisão capturada no começo deste turno é a autoridade. Uma
            # resposta da LLM (ou um fallback contaminado por outro assunto)
            # nunca pode anexar comandos a uma pergunta/conversa que não
            # autorizou execução. A validação canônica abaixo continua sendo
            # aplicada aos turnos operacionais autorizados.
            if (
                comandos
                and isinstance(turno, dict)
                and "autoriza_execucao" in turno
                and not bool(turno.get("autoriza_execucao"))
            ):
                intents_bloqueados = [
                    str(item.get("intent") or item.get("acao") or "").strip().upper()
                    for item in comandos
                    if isinstance(item, dict)
                ]
                self._log(
                    "🛡️ [DONO DO TURNO] comandos descartados antes do plano | "
                    f"motivo=turno_sem_autorizacao intents={intents_bloqueados}"
                )
                comandos = []
            tipo_interacao = str(resposta.get("tipo_interacao") or "")
            emocao_resposta = str(resposta.get("emocao") or "").strip().lower()
            try:
                nivel_emocao_resposta = max(1, min(3, int(resposta.get("nivel_emocao") or 1)))
            except (TypeError, ValueError):
                nivel_emocao_resposta = 1
            leitura_semantica = dict(resposta.get("leitura_semantica") or {})
            registrar_leitura_semantica = _get(ctx, "registrar_leitura_semantica_principal")
            if leitura_semantica and callable(registrar_leitura_semantica):
                try:
                    registrar_leitura_semantica(t, leitura_semantica)
                except Exception as erro:
                    self._log(f"⚠️ [SEMÂNTICA:PRINCIPAL] falha ao registrar leitura: {erro}")
            validar_comandos = _get(ctx, "validar_comandos_planejados")
            if comandos and callable(validar_comandos):
                validacao_comandos = validar_comandos(comandos)
                if isinstance(validacao_comandos, dict):
                    comandos = list(validacao_comandos.get("comandos") or [])
                    rejeitados = list(validacao_comandos.get("rejeitados") or [])
                    if rejeitados:
                        self._log(
                            "🛡️ [DONO DO TURNO] comandos da resposta bloqueados | "
                            f"proprietario={validacao_comandos.get('proprietario') or '-'} | "
                            f"rejeitados={rejeitados}"
                        )
                        registrar_decisao = _get(ctx, "registrar_decisao_diagnostico")
                        if callable(registrar_decisao):
                            registrar_decisao(
                                "execucao", "bloqueada", ("dono do turno recusou comandos",),
                                categoria="comandos_planejados",
                            )
            if callable(atualizar_plano):
                atualizar_plano(
                    "resposta_planejada",
                    comandos=comandos,
                    fala=fala_limpa_original,
                )

            if suprimir_fala and not comandos:
                marcar_fase("resposta_tecnica_suprimida")
                self._log("⚠️ [IA] Turno técnico encerrado sem contaminar a conversa.")
                abortar = getattr(estado_conversa_turno, "abortar_turno", None)
                if callable(abortar) and turno_conversa_iniciado:
                    abortar(turno_conversa_id)
                return True

            if descartar_se_obsoleta():
                abortar = getattr(estado_conversa_turno, "abortar_turno", None)
                if callable(abortar) and turno_conversa_iniciado:
                    abortar(turno_conversa_id)
                return True

            dispatcher_runtime = _get(ctx, "contexto_dispatch_runtime")
            if dispatcher_runtime is None:
                raise RuntimeError("Contexto do dispatcher ainda não foi inicializado.")
            resultado_dispatch = _get(ctx, "executar_comandos_json")
            if not callable(resultado_dispatch):
                raise RuntimeError("Dispatcher de comandos ainda não foi inicializado.")
            inicio_execucao = time.perf_counter()
            sucesso_dispatch = False
            try:
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
                sucesso_dispatch = True
            finally:
                _registrar_metrica(
                    ctx,
                    "dispatcher",
                    (time.perf_counter() - inicio_execucao) * 1000.0,
                    sucesso_dispatch,
                    turno_id=trace_id,
                    rota=rota_llm,
                )
            erros_execucao = list(dispatch.get("erros", []) or [])
            fala_ja_emitida = bool(dispatch.get("fala_ja_emitida", False))
            fala_emitida_por_acao = bool(dispatch.get("fala_emitida_por_acao", False))
            fala_salva_no_inicio = bool(dispatch.get("fala_salva_no_inicio", False))
            if callable(atualizar_plano):
                atualizar_plano(
                    "executado" if not erros_execucao else "falha_execucao",
                    comandos=comandos,
                    erros=erros_execucao,
                    fala=fala_limpa_original,
                )

            # A emoção escolhida pela LLM só entra depois da execução. Assim,
            # ela colore a fala e os próximos turnos, mas nunca muda a
            # autorização ou o resultado operacional deste pedido.
            definir_emocao_resposta = _get(ctx, "definir_emocao_resposta")
            if emocao_resposta and callable(definir_emocao_resposta):
                try:
                    definir_emocao_resposta(
                        emocao_resposta,
                        nivel_emocao_resposta,
                        f"escolha da LLM no turno: {t[:80]}",
                    )
                    self._log(
                        f"🎭 [IA:EMOÇÃO] {emocao_resposta} nível {nivel_emocao_resposta}"
                    )
                except Exception as erro:
                    self._log(
                        f"⚠️ [IA:EMOÇÃO] decisão ignorada: {type(erro).__name__}: {erro}"
                    )

            finalizacao_runtime = _get(ctx, "contexto_finalizacao_runtime")
            finalizar = _get(ctx, "finalizar_execucao")
            if finalizacao_runtime is None or not callable(finalizar):
                raise RuntimeError("Contexto de finalizacao ainda não foi inicializado.")
            resultado_finalizacao = finalizar(
                finalizacao_runtime.montar(),
                comandos,
                erros_execucao,
                fala_limpa_original,
                fala_ja_emitida,
                fala_emitida_por_acao,
                fala_salva_no_inicio,
            )
            resultado_finalizacao = (
                resultado_finalizacao
                if isinstance(resultado_finalizacao, dict)
                else {}
            )
            fala_final = str(resultado_finalizacao.get("fala") or "").strip()
            registrar_historico = bool(
                resultado_finalizacao.get("registrar_no_historico")
            )
            concluir = getattr(estado_conversa_turno, "concluir_turno", None)
            registrado = False
            if (
                registrar_historico
                and fala_final
                and callable(concluir)
                and turno_conversa_iniciado
            ):
                registrado = bool(concluir(turno_conversa_id, fala_final))
            if registrado:
                atualizar_topicos = _get(ctx, "atualizar_memoria_topicos")
                if (
                    not comandos
                    and tipo_interacao in {"conversa", "", "confirmacao"}
                    and callable(atualizar_topicos)
                ):
                    atualizar_topicos(t, fala_final)
                registrar_mente_curta = _get(ctx, "registrar_mente_curta")
                if callable(registrar_mente_curta):
                    registrar_mente_curta(
                        t,
                        fala_final,
                        habilidade="conversa",
                    )
                salvar_memoria = _get(ctx, "salvar_memoria")
                if callable(salvar_memoria):
                    salvar_memoria()
            elif turno_conversa_iniciado:
                abortar = getattr(estado_conversa_turno, "abortar_turno", None)
                if callable(abortar):
                    abortar(turno_conversa_id)
        except Exception as erro:
            abortar = getattr(estado_conversa_turno, "abortar_turno", None)
            if callable(abortar) and turno_conversa_iniciado:
                abortar(turno_conversa_id)
            self._log(f"❌ Erro grave na geração da resposta IA: {erro}")
            registrar_falha = _get(ctx, "registrar_falha_diagnostico")
            if callable(registrar_falha):
                registrar_falha(
                    "turno", "erro_resposta_ia", erro=erro,
                    classe="defeito", impacto="turno", fallback="nenhum",
                )
            traceback.print_exc()
            return False
        return True


def criar_resposta_ia_runtime(
    *, contexto_getter: Callable[[], Dict[str, Any]], log: Callable[..., Any] = print
) -> RespostaIARuntime:
    return RespostaIARuntime(contexto_getter=contexto_getter, log=log)
