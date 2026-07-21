"""Coordenador unico do fluxo de intencao da Laylay."""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Dict, Tuple

from mente_laylay.autonomia.analise_comandos import (
    executar_comando_em_texto,
    processar_comandos_em_cadeia,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.autonomia.agendamento_mental import texto_pede_lembrete_explicito
from mente_laylay.cognicao.arbitro_turno import CandidatoDecisao, arbitrar_turno
from mente_laylay.especialistas.capacidades import intents_registradas

INTENTS_EXECUTAVEIS = set(intents_registradas())

DEPENDENCIAS_CICLO_COMANDOS = (
    "_interpretacao_intencao_runtime",
    "_normalizar_texto_com_apelidos",
    "_texto_depende_de_contexto",
    "_refinar_contexto_mental",
    "_texto_cancela_acao_agora",
    "_resolver_comando_midia_contextual_forcado",
    "_resolver_comando_contextual_forcado",
    "_resolver_comando_acao_geral_contextual_forcado",
    "_resolver_repeticao_ultima_acao",
    "detectar_intencao_deterministica",
    "_extrair_agendamento_local",
    "_extrair_acao_agendada_local",
    "_registrar_resultado_execucao",
    "_registrar_autoaprimoramento",
    "_detectar_repetir_briefing",
    "repetir_briefing",
    "interpretar_comando_local_rapido",
)


def _call(ctx: Dict[str, Any], nome: str, *args: Any, default: Any = None, **kwargs: Any) -> Any:
    fn = ctx.get(nome) if isinstance(ctx, dict) else None
    if callable(fn):
        return fn(*args, **kwargs)
    return default


def _normalizar_intent(resultado: Any) -> str:
    if not isinstance(resultado, dict):
        return ""
    return str(resultado.get("intent") or resultado.get("acao") or "").upper().strip()


def _intencao_deterministica_tem_alvo_explicito(resultado: Any, texto: str) -> bool:
    if not isinstance(resultado, dict):
        return False
    intent = _normalizar_intent(resultado)
    params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
    alvo = str(
        params.get("alvo") or params.get("nome_app") or params.get("url")
        or params.get("site") or params.get("nome") or params.get("pasta") or ""
    ).strip().casefold()
    pronomes = {"", "ele", "ela", "isso", "esse", "essa", "aqui", "ali"}
    fala = str(texto or "").strip().casefold()
    if intent in {"CREATE_FOLDER", "CREATE_FILE", "DELETE_ITEM", "CONFIRM_DELETE_ITEM", "CANCEL_DELETE_ITEM", "RESTORE_DELETED_ITEM", "MOVE_ITEM", "FILE_TRANSACTION"}:
        return alvo not in pronomes or any(nome in fala for nome in ("pasta", "arquivo", "documento"))
    if intent in {"APP_OPEN", "CLOSE_APP", "MAXIMIZE_WINDOW", "OPEN_URL", "CLOSE_TAB"}:
        return alvo not in pronomes
    if intent in {"IOT_CONTROL", "IOT_STATUS"}:
        return alvo not in pronomes and any(
            nome in fala for nome in ("ventilador", "tomada", "luz", "lampada", "lâmpada", "dispositivo")
        )
    return False


def resolver_referencias_da_intencao(
    resultado: Dict[str, Any] | None,
    retrato: Dict[str, Any] | None,
) -> Dict[str, Any] | None:
    """Resolve referências antes da execução e bloqueia pronomes crus."""
    if not isinstance(resultado, dict):
        return None
    saida = dict(resultado)
    params = dict(saida.get("params") or {})
    intent = _normalizar_intent(saida)
    snapshot = dict(retrato or {})
    referencia = dict(snapshot.get("referencia_resolvida") or {})
    tipo = str(referencia.get("tipo") or "").casefold()
    nome = str(referencia.get("nome") or "").strip()
    pronome_exato = re.compile(
        r"^(?:(?:o|a|os|as)\s+)?(?:ele|ela|eles|elas|isso|esse|essa|desse|dessa|dele|dela|aqui|ali)$",
        re.IGNORECASE,
    )

    def resolver_campo(chaves: tuple[str, ...], tipos_aceitos: set[str]) -> bool:
        for chave in chaves:
            valor = str(params.get(chave) or "").strip()
            if not valor or not pronome_exato.fullmatch(valor):
                continue
            if not nome or tipo not in tipos_aceitos:
                return False
            params[f"{chave}_original"] = valor[:160]
            params[chave] = nome
            params["referencia_contextual"] = True
        return True

    if intent == "MUSIC_SEARCH":
        query = str(params.get("query") or "").strip()
        query_norm = query.casefold()
        referencia_crua = bool(re.search(
            r"\b(?:ele|ela|dele|dela|desse|dessa)\b", query_norm
        ))
        tipos_musicais = {"artista", "cantor", "cantora", "banda", "referencia_nomeada"}
        if referencia_crua and nome and tipo in tipos_musicais:
            params["query_original"] = query[:160]
            params["query"] = nome
            params["referencia_contextual"] = True
        elif referencia_crua:
            return None
        saida["params"] = params
    elif intent in {"APP_OPEN", "CLOSE_APP", "MAXIMIZE_WINDOW"}:
        if not resolver_campo(("nome_app", "app", "alvo"), {"app", "janela"}):
            return None
    elif intent in {"OPEN_URL", "CLOSE_TAB", "SITE_ENTER"}:
        if not resolver_campo(("alvo", "site", "url"), {"site", "janela"}):
            return None
    elif intent in {"IOT_CONTROL", "IOT_STATUS"}:
        if not resolver_campo(("alvo", "dispositivo"), {"iot", "dispositivo"}):
            return None
    elif intent in {"PLAYLIST_PLAY", "PLAYLIST_ADD"}:
        if not resolver_campo(("nome_playlist", "playlist"), {"playlist"}):
            return None
    elif intent in {"DELETE_ITEM", "MOVE_ITEM", "FILE_TRANSACTION"}:
        if not resolver_campo(("alvo", "origem"), {"arquivo", "pasta"}):
            return None
    saida["params"] = params
    return saida


def resolver_intencao(texto: str, origem: str, ctx: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, str]:
    texto_norm = _call(ctx, "normalizar_texto", texto, default=str(texto or ""))
    _call(ctx, "refinar_contexto_mental", texto_norm)
    retrato_atual = dict(ctx.get("retrato_turno_atual") or {})

    # Lembretes completos são comandos locais. Eles precisam ser resolvidos
    # antes da IA-first para que uma frase como "me lembra ... daqui 5 minutos"
    # nunca seja respondida como conversa ou promessa sem agendamento real.
    lembrete = _call(ctx, "extrair_agendamento", texto_norm)
    if isinstance(lembrete, dict) and _normalizar_intent(lembrete) in {
        "AGENDAR_LEMBRETE", "LISTAR_AGENDAMENTOS", "CANCELAR_AGENDAMENTO"
    }:
        return lembrete, "agenda"

    agendamento = _call(ctx, "extrair_acao_agendada", texto_norm)
    if isinstance(agendamento, dict) and agendamento.get("texto_acao"):
        ctx_base = dict(ctx)
        ctx_base["extrair_acao_agendada"] = lambda _texto: None
        intencao_base, rota_base = resolver_intencao(
            str(agendamento.get("texto_acao") or ""),
            origem,
            ctx_base,
        )
        intent_base = _normalizar_intent(intencao_base)
        bloqueados = {"AGENDAR_ACAO", "AGENDAR_LEMBRETE", "LISTAR_AGENDAMENTOS", "CANCELAR_AGENDAMENTO", "SUGGEST_ACTION", "CANCELAR_ACAO"}
        if isinstance(intencao_base, dict) and intent_base in INTENTS_EXECUTAVEIS and intent_base not in bloqueados:
            params_agenda = dict(agendamento)
            params_agenda["acao_agendada"] = intencao_base
            params_agenda["rota_original"] = rota_base
            return {"intent": "AGENDAR_ACAO", "params": params_agenda}, "agendamento"

    if _call(ctx, "texto_cancela_acao_agora", texto_norm, default=False):
        # Uma desistência pode ser uma reversão quando o efeito anterior já foi
        # confirmado (ligou, abriu, pausou etc.). O resolvedor contextual é
        # quem possui estado suficiente para decidir isso com segurança.
        reversao = _call(ctx, "resolver_comando_contextual_forcado", texto_norm)
        semantica = reversao.get("_semantica", {}) if isinstance(reversao, dict) else {}
        if str(semantica.get("operacao") or "").upper() == "REVERTER":
            return reversao, "contexto-reversao"
        return {"intent": "CANCELAR_ACAO", "params": {}}, "imediato"

    depende_contexto = bool(_call(ctx, "texto_depende_de_contexto", texto_norm, default=False))

    intent_deterministica = resolver_referencias_da_intencao(
        _call(ctx, "detectar_intencao_deterministica", texto_norm),
        retrato_atual,
    )

    candidatos: list[CandidatoDecisao] = []
    det_explicito = _intencao_deterministica_tem_alvo_explicito(intent_deterministica, texto_norm)
    if isinstance(intent_deterministica, dict) and (not depende_contexto or det_explicito):
        candidatos.append(CandidatoDecisao(
            tipo="comando_explicito",
            valor=intent_deterministica,
            origem="deterministico-explicito" if det_explicito else "deterministico",
            confianca=0.98 if det_explicito else 0.90,
            evidencia=("verbo operacional detectado", "alvo explicito" if det_explicito else "frase independente"),
        ))

    # Continuidade contextual unificada vem antes da repeticao generica para
    # pronomes e respostas curtas. Ex.: "fecha ela", "coloca ele em foco".
    intent_contextual = resolver_referencias_da_intencao(
        _call(ctx, "resolver_comando_contextual_forcado", texto_norm),
        retrato_atual,
    )
    if isinstance(intent_contextual, dict):
        rota = str(intent_contextual.get("_rota_contextual") or "contexto").lower()
        intent_limpo = dict(intent_contextual)
        intent_limpo.pop("_rota_contextual", None)
        candidatos.append(CandidatoDecisao(
            tipo="comando_contextual",
            valor=intent_limpo,
            origem=f"contexto-{rota}",
            confianca=float((intent_contextual.get("_semantica") or {}).get("confianca") or 0.72),
            evidencia=("continuidade semantica",),
        ))

    intent_repeticao = resolver_referencias_da_intencao(
        _call(ctx, "resolver_repeticao_ultima_acao", texto_norm),
        retrato_atual,
    )
    if isinstance(intent_repeticao, dict):
        candidatos.append(CandidatoDecisao(
            tipo="repeticao",
            valor=intent_repeticao,
            origem="repeticao",
            confianca=0.66,
            evidencia=("referencia a ultima acao",),
        ))

    if depende_contexto:
        if isinstance(intent_deterministica, dict) and not det_explicito:
            candidatos.append(CandidatoDecisao(
                tipo="comando_contextual",
                valor=intent_deterministica,
                origem="deterministico-contextual",
                confianca=0.62,
                evidencia=("deteccao deterministica dependente de contexto",),
            ))

    arbitragem = arbitrar_turno(
        texto_norm,
        candidatos,
        turno=dict(ctx.get("turno_atual") or {}),
        retrato=dict(ctx.get("retrato_turno_atual") or {}),
    )
    _call(ctx, "registrar_arbitragem_turno", texto_norm, arbitragem)
    if candidatos:
        print(
            "🧭 [ARBITRO:TURNO] "
            f"modalidade={arbitragem.get('modalidade')} | "
            f"vencedor={arbitragem.get('tipo') or '-'}:{arbitragem.get('origem') or '-'} | "
            f"rejeitados={arbitragem.get('rejeitados') or []}"
        )
    if isinstance(arbitragem.get("decisao"), dict):
        return arbitragem["decisao"], str(arbitragem.get("origem") or "arbitro")

    intent = _call(ctx, "tentar_intencao_ai_primeiro", texto)
    if isinstance(intent, dict):
        if _normalizar_intent(intent) == "AGENDAR_LEMBRETE":
            pendente = bool(ctx.get("lembrete_pendente"))
            if not texto_pede_lembrete_explicito(texto_norm) and not pendente:
                # A IA pode perceber uma data futura em um relato casual, mas
                # isso não autoriza criar uma ação. Ex.: "sexta eu participo
                # de um campeonato" deve continuar sendo conversa.
                return None, ""
        intent_resolvida = resolver_referencias_da_intencao(
            intent,
            retrato_atual,
        )
        if intent_resolvida is None:
            print("⚠️ [CONTEXTO:REFERÊNCIA] intenção bloqueada por conter referência não resolvida")
            return None, ""
        # A IA é mais um especialista, não uma segunda autoridade. Sua
        # intenção precisa respeitar a modalidade e a autorização congeladas
        # no começo do turno, como qualquer detector determinístico.
        turno_atual = dict(ctx.get("turno_atual") or {})
        modalidade = str(
            turno_atual.get("modalidade_geral")
            or turno_atual.get("modalidade")
            or "conversa"
        ).strip().lower()
        if modalidade == "confirmacao" and turno_atual.get("confirmacao_contextual_valida"):
            tipo_candidato = "resposta_pendencia"
        elif turno_atual.get("autoriza_execucao") and modalidade in {"comando", "misto"}:
            tipo_candidato = "comando_explicito"
        else:
            tipo_candidato = "comando_contextual"
        arbitragem_ia = arbitrar_turno(
            texto_norm,
            [CandidatoDecisao(
                tipo=tipo_candidato,
                valor=intent_resolvida,
                origem="ia-first",
                confianca=float(intent_resolvida.get("confianca") or 0.84),
                evidencia=("intenção proposta pela IA",),
            )],
            turno=turno_atual,
            retrato=retrato_atual,
        )
        _call(ctx, "registrar_arbitragem_turno", texto_norm, arbitragem_ia)
        print(
            "🧭 [ARBITRO:IA] "
            f"modalidade={arbitragem_ia.get('modalidade')} | "
            f"vencedor={arbitragem_ia.get('tipo') or '-'} | "
            f"rejeitados={arbitragem_ia.get('rejeitados') or []}"
        )
        if isinstance(arbitragem_ia.get("decisao"), dict):
            return arbitragem_ia["decisao"], "ia-first-arbitrada"
        return None, ""

    return None, ""


def executar_fluxo_intencao(
    texto: str,
    origem: str,
    ctx: Dict[str, Any],
    *,
    texto_original: str = "",
) -> bool:
    intent, rota = resolver_intencao(texto, origem, ctx)
    if not isinstance(intent, dict):
        return False

    tag = f" [{origem}]" if origem else ""
    if rota == "imediato":
        tag = f"[{origem}]" if origem else ""
    print(f"⚡ [ROTEADOR {rota.upper()}{tag}] {intent}")

    try:
        texto_execucao = str(texto_original or texto)
        executou = bool(_call(ctx, "executar_intencao", intent, texto_execucao, default=False))
        _call(ctx, "registrar_resultado_execucao", intent, texto_execucao, executou, origem=f"{rota}:{origem}")
        if executou:
            _call(ctx, "registrar_autoaprimoramento", intent, texto_execucao, True, contexto=f"{rota}:{origem}", origem=origem)
        return executou
    except Exception as e:
        print(f"⚠️ [ROTEADOR {rota.upper()}] falha ao executar: {e}")
        return False


class CicloComandosRuntime:
    """Fachada única sobre interpretação, cadeia e execução prática."""

    def __init__(
        self,
        *,
        namespace_getter: Callable[[], Dict[str, Any]],
        contexto_intencao_runtime: Any,
        log: Callable[..., Any] = print,
        dependencias_tardias: tuple[str, ...] = (),
        monitor_saude: Any = None,
        registrar_metrica_cb: Callable[[str, float, bool], Any] | None = None,
        registrar_falha_cb: Callable[..., Any] | None = None,
        registrar_decisao_cb: Callable[..., Any] | None = None,
    ) -> None:
        self.namespace_getter = namespace_getter
        self.contexto_intencao_runtime = contexto_intencao_runtime
        self.log = log
        self.monitor_saude = monitor_saude
        self.dependencias_tardias = frozenset(dependencias_tardias or ())
        self.registrar_metrica_cb = registrar_metrica_cb
        self.registrar_falha_cb = registrar_falha_cb
        self.registrar_decisao_cb = registrar_decisao_cb
        namespace = self.namespace_getter() or {}
        self._servicos_estaticos = {
            nome: namespace[nome]
            for nome in DEPENDENCIAS_CICLO_COMANDOS
            if nome not in self.dependencias_tardias and nome in namespace
        }

    def _ns(self) -> Dict[str, Any]:
        servicos = dict(self._servicos_estaticos)
        if self.dependencias_tardias:
            namespace = self.namespace_getter() or {}
            for nome in self.dependencias_tardias:
                if nome in namespace:
                    servicos[nome] = namespace[nome]
        return servicos

    def validar_conexoes(self) -> Dict[str, Any]:
        servicos = self._ns()
        if self.monitor_saude is not None:
            return self.monitor_saude.validar_dependencias(
                "ciclo_comandos",
                servicos,
                DEPENDENCIAS_CICLO_COMANDOS,
            )
        ausentes = [nome for nome in DEPENDENCIAS_CICLO_COMANDOS if nome not in servicos]
        return {"status": "saudavel" if not ausentes else "degradado", "ausentes": ausentes}

    def executar_intencao(self, resultado: Dict[str, Any], texto_original: str) -> bool:
        inicio = time.perf_counter()
        intent = str((resultado or {}).get("intent") or "desconhecida")
        sucesso = False
        try:
            sucesso = bool(executar_intencao(
                resultado,
                texto_original,
                self.contexto_intencao_runtime.montar(),
            ))
            if not sucesso and callable(self.registrar_decisao_cb):
                self.registrar_decisao_cb(
                    "execucao", "nao_confirmada", ("executor retornou falso",), categoria=intent,
                )
            return sucesso
        except Exception as erro:
            if callable(self.registrar_falha_cb):
                self.registrar_falha_cb("execucao", "excecao_intencao", erro=erro)
            raise
        finally:
            if callable(self.registrar_metrica_cb):
                self.registrar_metrica_cb(
                    "execucao", (time.perf_counter() - inicio) * 1000.0, sucesso,
                )

    def tentar_intencao_ai_primeiro(self, texto: str):
        runtime = self._ns().get("_interpretacao_intencao_runtime")
        return runtime.tentar_ai_primeiro(texto) if runtime is not None else None

    def processar_deterministico(self, texto: str, origem: str = "", texto_original: str = "") -> bool:
        ns = self._ns()
        contexto_execucao = self.contexto_intencao_runtime.montar()
        contexto = {
            "normalizar_texto": ns.get("_normalizar_texto_com_apelidos"),
            "texto_depende_de_contexto": ns.get("_texto_depende_de_contexto"),
            "refinar_contexto_mental": ns.get("_refinar_contexto_mental"),
            "texto_cancela_acao_agora": ns.get("_texto_cancela_acao_agora"),
            "resolver_comando_midia_contextual_forcado": ns.get("_resolver_comando_midia_contextual_forcado"),
            "resolver_comando_contextual_forcado": ns.get("_resolver_comando_contextual_forcado"),
            "resolver_comando_acao_geral_contextual_forcado": ns.get("_resolver_comando_acao_geral_contextual_forcado"),
            "resolver_repeticao_ultima_acao": ns.get("_resolver_repeticao_ultima_acao"),
            "tentar_intencao_ai_primeiro": self.tentar_intencao_ai_primeiro,
            "detectar_intencao_deterministica": ns.get("detectar_intencao_deterministica"),
            "extrair_agendamento": ns.get("_extrair_agendamento_local"),
            "extrair_acao_agendada": ns.get("_extrair_acao_agendada_local"),
            "executar_intencao": self.executar_intencao,
            "registrar_resultado_execucao": ns.get("_registrar_resultado_execucao"),
            "registrar_autoaprimoramento": ns.get("_registrar_autoaprimoramento"),
            "turno_atual": dict(contexto_execucao.get("turno_atual") or {}),
            "retrato_turno_atual": dict(contexto_execucao.get("retrato_turno_atual") or {}),
            "registrar_arbitragem_turno": contexto_execucao.get("registrar_arbitragem_turno"),
            "lembrete_pendente": (
                str(contexto_execucao.get("ultima_intencao") or "").upper() == "AGENDAR_LEMBRETE"
                and str(contexto_execucao.get("ultima_habilidade") or "").casefold() == "agenda"
                and bool(str(contexto_execucao.get("ultimo_alvo") or "").strip())
            ),
        }
        return executar_fluxo_intencao(texto, origem, contexto, texto_original=texto_original)

    def executar_texto(self, texto: str, origem: str = "") -> bool:
        ns = self._ns()
        return executar_comando_em_texto(
            texto,
            origem,
            detectar_repetir_briefing=ns.get("_detectar_repetir_briefing"),
            repetir_briefing=ns.get("repetir_briefing"),
            processar_comando_deterministico=self.processar_deterministico,
            interpretar_comando_local_rapido=ns.get("interpretar_comando_local_rapido"),
            executar_intencao=self.executar_intencao,
            log=self.log,
        )

    def processar_cadeia(self, texto: str, origem: str = "") -> bool:
        normalizar = self._ns().get("_normalizar_texto_com_apelidos")
        return processar_comandos_em_cadeia(
            texto,
            origem,
            normalizar_texto=normalizar,
            executar_trecho=self.executar_texto,
        )


def criar_ciclo_comandos_runtime(**kwargs: Any) -> CicloComandosRuntime:
    return CicloComandosRuntime(**kwargs)
