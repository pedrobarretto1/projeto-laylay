"""Orquestracao do ciclo principal de resposta da Laylay."""

from __future__ import annotations

import threading
import time
import traceback
from typing import Any, Callable, Dict

from mente_laylay.autonomia.pre_fluxo_contextual import responder_conversa_social_curta
from mente_laylay.personalidade.proporcao_resposta import limite_tokens_resposta


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    return ctx.get(key, default) if isinstance(ctx, dict) else default


class RespostaIARuntime:
    """Coordena conversa, comandos e finalizacao usando o contexto da mente."""

    def __init__(self, *, contexto_getter: Callable[[], Dict[str, Any]], log: Callable[..., Any] = print) -> None:
        self._contexto_getter = contexto_getter
        self._log = log
        self._process_lock = threading.RLock()

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
            iniciar_turno_voz = _get(ctx, "iniciar_turno_voz")
            finalizar_turno_voz = _get(ctx, "finalizar_turno_voz")
            if callable(iniciar_turno_voz):
                iniciar_turno_voz()
            try:
                resultado_turno = self._processar_serializado(
                    texto,
                    ainda_atual_cb=ainda_atual_cb,
                    origem=origem,
                )
                sucesso = resultado_turno is not False
            finally:
                registrar_metrica = _get(ctx, "registrar_metrica_diagnostico")
                if callable(registrar_metrica):
                    registrar_metrica(
                        "turno_total", (time.perf_counter() - inicio_total) * 1000.0, sucesso,
                    )
                if callable(finalizar_turno_voz):
                    finalizar_turno_voz()

    def _processar_serializado(
        self,
        texto: str,
        *,
        ainda_atual_cb: Callable[[], bool] | None = None,
        origem: str = "desconhecida",
    ) -> None:
        ctx = self._contexto()
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
            depende_contexto_cb = _get(ctx, "texto_depende_de_contexto")
            try:
                depende_contexto = bool(depende_contexto_cb(t)) if callable(depende_contexto_cb) else False
            except Exception:
                depende_contexto = False

            comandos_imediatos = _get(ctx, "processar_comandos_imediatos")
            if callable(comandos_imediatos):
                try:
                    if comandos_imediatos(t, contexto_mental_ja_refinado=True):
                        marcar_fase("tratado_imediato")
                        return
                except Exception as erro:
                    self._log(f"⚠️ [IA] falha ao processar comandos imediatos: {erro}")

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

            if not modo_rapido:
                pre_fluxos = _get(ctx, "processar_pre_fluxos")
                if callable(pre_fluxos) and pre_fluxos(contexto_inicio, t):
                    marcar_fase("tratado_pre_ia")
                    return

                prompt_runtime = _get(ctx, "contexto_prompt_runtime")
                if prompt_runtime is None:
                    raise RuntimeError("Contexto do prompt ainda não foi inicializado.")
                inicio_prompt = time.perf_counter()
                mensagens_novas, _prompt_com_humor = prompt_runtime.preparar(t)
                registrar_metrica = _get(ctx, "registrar_metrica_diagnostico")
                if callable(registrar_metrica):
                    registrar_metrica(
                        "preparacao_prompt",
                        (time.perf_counter() - inicio_prompt) * 1000.0,
                        True,
                    )
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
            inicio_llm = time.perf_counter()
            bot_raw = enviar_mensagem(
                mensagens,
                _com_tools=False,
                max_tokens=limite_tokens_resposta(
                    t,
                    modo_rapido=modo_rapido,
                    depende_contexto=depende_contexto,
                ),
                modo_rapido=modo_rapido,
                _permitir_conversa_modo_jogo=bool(
                    _get(ctx, "modo_chat", False) or _get(ctx, "conversa_ativa", False)
                ),
                _prioridade_interativa=True,
            )
            registrar_metrica = _get(ctx, "registrar_metrica_diagnostico")
            if callable(registrar_metrica):
                registrar_metrica(
                    "llm_resposta_principal",
                    (time.perf_counter() - inicio_llm) * 1000.0,
                    True,
                )
            self._log(f"🤖 [IA] Resposta bruta recebida (tamanho {len(str(bot_raw))} chars)")
            if descartar_se_obsoleta():
                return True

            preparar_resposta = _get(ctx, "preparar_resposta")
            if not callable(preparar_resposta):
                raise RuntimeError("Preparador de resposta ainda não foi inicializado.")
            inicio_preparacao = time.perf_counter()
            resposta = preparar_resposta(t, bot_raw)
            if callable(registrar_metrica):
                registrar_metrica(
                    "pos_processamento_resposta",
                    (time.perf_counter() - inicio_preparacao) * 1000.0,
                    True,
                )
            if descartar_se_obsoleta():
                return True
            bot_raw = resposta.get("resposta_bruta", bot_raw)
            suprimir_fala = bool(resposta.get("suprimir_fala"))
            fala_limpa_original = (
                "" if suprimir_fala
                else str(resposta.get("fala") or _get(ctx, "fallback_fala", "Tô por aqui."))
            )
            comandos = list(resposta.get("comandos") or [])
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
                return True

            if descartar_se_obsoleta():
                return True

            atualizar_topicos = _get(ctx, "atualizar_memoria_topicos")
            if not comandos and tipo_interacao in {"conversa", "", "confirmacao"} and callable(atualizar_topicos):
                atualizar_topicos(t, fala_limpa_original)

            executar_deterministico = _get(ctx, "processar_comando_deterministico")
            if not comandos and callable(executar_deterministico) and executar_deterministico(t, "pos-ia-0-comandos"):
                marcar_fase("tratado_deterministico_pos_ia")
                return

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
                registrar_metrica = _get(ctx, "registrar_metrica_diagnostico")
                if callable(registrar_metrica):
                    registrar_metrica(
                        "dispatcher", (time.perf_counter() - inicio_execucao) * 1000.0,
                        sucesso_dispatch,
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
