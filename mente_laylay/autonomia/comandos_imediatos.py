"""Camada de comandos imediatos da Laylay.

Esta camada roda depois do pre-fluxo de conversa e antes da conversa livre da
IA. Ela tenta resolver comandos praticos sem competir com o fluxo social.
"""

from __future__ import annotations

import asyncio
import re
import unicodedata
from typing import Any, Callable, Dict
from mente_laylay.integracao.registro_memoria_pessoas import PortaMemoriaPessoas
from mente_laylay.integracao.registro_iot import PortaIoT
from mente_laylay.autonomia.pre_fluxo_contextual import (
    analisar_intencao_com_porteiro,
    processar_execucao_pratica_precoce,
    texto_eh_conversa_social_sem_comando,
)
from mente_laylay.autonomia.coordenador_intencao import (
    resolver_referencias_da_intencao,
)
from mente_laylay.especialistas.capacidades import (
    INTENTS_SOMENTE_LEITURA,
    intents_registradas,
)
from mente_laylay.cognicao.evidencia_operacional import (
    bloqueia_controle_iot_por_modalidade,
    detectar_consulta_lista_iot,
)
from mente_laylay.percepcao.ritmo_circadiano import (
    agora_no_fuso,
    detectar_consulta_horario,
    responder_consulta_horario,
)


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def texto_pede_resumo_pagina(texto: str) -> bool:
    t = str(texto or "").strip().lower()
    t = "".join(ch for ch in unicodedata.normalize("NFD", t) if unicodedata.category(ch) != "Mn")
    alvos = ("pagina", "site", "video", "aba")
    pedidos = ("resume", "resuma", "resumir", "explica", "explique", "o que essa", "o que esta")
    return any(alvo in t for alvo in alvos) and any(pedido in t for pedido in pedidos)


def processar_comandos_imediatos(ctx: Dict[str, Any], texto: str) -> bool:
    normalizar = _get(ctx, "_normalizar_texto_com_apelidos")
    refinar_contexto_mental = _get(ctx, "_refinar_contexto_mental")
    contexto_mental_ja_refinado = bool(_get(ctx, "_contexto_mental_ja_refinado", False))
    processar_comandos_em_cadeia = _get(ctx, "processar_comandos_em_cadeia")
    executar_intencao = _get(ctx, "executar_intencao")
    registrar_resultado_execucao = _get(ctx, "_registrar_resultado_execucao")
    falar_falha_contextual = _get(ctx, "_falar_falha_contextual")
    ws_loop = _get(ctx, "ws_loop")
    resumir_pagina_ou_video = _get(ctx, "resumir_pagina_ou_video")
    falar_com_lipsync = _get(ctx, "falar_com_lipsync")
    extrair_acao_agendada = _get(ctx, "_extrair_acao_agendada_local")

    t = normalizar((texto or "").strip()) if callable(normalizar) else str(texto or "").strip()
    if not t:
        return False

    def _log(etapa: str, detalhe: str = "") -> None:
        extra = f" | {detalhe}" if detalhe else ""
        print(f"🧭 [IMEDIATO] {etapa}{extra}")

    decisao_ja_avaliada = _get(ctx, "decisao_comando_ja_avaliada")
    if callable(decisao_ja_avaliada):
        try:
            if decisao_ja_avaliada(t):
                _log(
                    "decisao_canonica_reutilizada",
                    "segue para conversa sem rerotear",
                )
                return False
        except Exception as erro:
            _log("falha_guarda_decisao", type(erro).__name__)

    # Perguntas sobre dados reais ("o que tem em trap?", "quais dispositivos
    # estão disponíveis?") são classificadas corretamente como perguntas pelo
    # árbitro conversacional. Ainda assim, elas precisam chegar aos leitores de
    # habilidades. Fazemos isso antes da trava de modalidade, mas somente para
    # intents explicitamente sem efeito colateral. Assim uma pergunta como
    # "como apaga a pasta?" nunca ganha autorização de execução por esta rota.
    resolver_consulta = _get(ctx, "_resolver_consulta_recurso_local")
    executar_consulta_recurso = _get(ctx, "_executar_consulta_recurso_local")
    parece_consulta = _get(ctx, "_texto_parece_consulta_operacional")
    detectar_deterministico = _get(ctx, "detectar_intencao_deterministica")
    try:
        candidato_consulta = resolver_consulta(t) if callable(resolver_consulta) else None
    except Exception as erro:
        _log("falha_consulta_recurso", type(erro).__name__)
        candidato_consulta = None
    if not isinstance(candidato_consulta, dict) and callable(parece_consulta):
        try:
            eh_consulta_operacional = bool(parece_consulta(t))
        except Exception:
            eh_consulta_operacional = False
        if eh_consulta_operacional and callable(detectar_deterministico):
            candidato_consulta = detectar_deterministico(t)
    if isinstance(candidato_consulta, dict):
        intent_consulta = str(candidato_consulta.get("intent") or "").upper().strip()
        if intent_consulta in INTENTS_SOMENTE_LEITURA:
            _log("consulta_operacional", intent_consulta)
            try:
                executou = (
                    bool(executar_consulta_recurso(candidato_consulta, t))
                    if callable(executar_consulta_recurso)
                    else False
                )
                if not executou:
                    executou = bool(executar_intencao(candidato_consulta, t)) if callable(executar_intencao) else False
            except Exception as erro:
                _log("falha_execucao_consulta", type(erro).__name__)
                if callable(falar_falha_contextual):
                    falar_falha_contextual("execucao", t)
                return True
            if callable(registrar_resultado_execucao):
                registrar_resultado_execucao(
                    candidato_consulta, t, executou, origem="consulta_operacional",
                )
            # Mesmo uma consulta indisponível é um turno operacional concluído:
            # o executor responsável explica a indisponibilidade sem deixar a
            # LLM inventar uma resposta genérica.
            return True

    mente = _get(ctx, "mente_integrada_estado", {})
    turno = mente.get("turno_atual") if isinstance(mente, dict) else {}
    modalidade = str((turno or {}).get("modalidade_geral") or (turno or {}).get("modalidade") or "").lower()
    if isinstance(turno, dict) and turno and (
        turno.get("requer_esclarecimento")
        or (
            modalidade in {"conversa", "pergunta", "deliberacao", "correcao", "reacao"}
            and not turno.get("autoriza_execucao")
        )
    ):
        _log(
            "bloqueado_pelo_arbitro",
            str(turno.get("motivo_decisao") or turno.get("motivo") or modalidade),
        )
        return False

    if texto_pede_resumo_pagina(t):
        _log("resumir_pagina_direto")
        if ws_loop and callable(resumir_pagina_ou_video):
            asyncio.run_coroutine_threadsafe(resumir_pagina_ou_video(), ws_loop)
        elif callable(falar_com_lipsync):
            falar_com_lipsync("O navegador não está conectado agora, então não consigo ler essa página.", "irritada", 2)
        return True

    if texto_eh_conversa_social_sem_comando(ctx, t):
        _log("ignorado_por_conversa")
        return False

    if callable(extrair_acao_agendada):
        agendamento = extrair_acao_agendada(t)
        if isinstance(agendamento, dict) and agendamento.get("texto_acao"):
            resolver_contexto = _get(ctx, "_resolver_comando_contextual_forcado")
            acao_base = resolver_contexto(str(agendamento.get("texto_acao") or "")) if callable(resolver_contexto) else None
            if isinstance(acao_base, dict) and str(acao_base.get("intent") or "").strip():
                acao_base = dict(acao_base)
                acao_base.pop("_rota_contextual", None)
                resultado_agenda = {
                    "intent": "AGENDAR_ACAO",
                    "params": {**agendamento, "acao_agendada": acao_base, "rota_original": "contextual"},
                }
                _log("agendamento_local", str(acao_base.get("intent") or ""))
                executou = bool(executar_intencao(resultado_agenda, t)) if callable(executar_intencao) else False
                if callable(registrar_resultado_execucao):
                    registrar_resultado_execucao(resultado_agenda, t, executou, origem="agendamento_local")
                return True

    if callable(refinar_contexto_mental) and not contexto_mental_ja_refinado:
        refinar_contexto_mental(t)

    if callable(processar_comandos_em_cadeia) and processar_comandos_em_cadeia(t, "imediato"):
        _log("comando_em_cadeia")
        return True

    try:
        ok_pratico, nome_pratico = processar_execucao_pratica_precoce(ctx, t, origem="imediato")
    except Exception as e:
        print(f"⚠️ [IMEDIATO] falha na execução prática compartilhada: {e}")
        return False
    if ok_pratico:
        _log(nome_pratico or "execucao_pratica")
        return True

    status_analise, resultado = analisar_intencao_com_porteiro(ctx, t)
    if status_analise == "evitar":
        _log("sem_sinal_pratico", "seguindo como conversa")
        return False
    if status_analise in {"vazio", "sem_analisador"}:
        _log(status_analise)
        return False
    if status_analise == "falha":
        _log("falha_entendimento_llm")
        texto_tem_comando_explicito = _get(ctx, "_texto_tem_comando_explicito")
        if not callable(texto_tem_comando_explicito) or not texto_tem_comando_explicito(t):
            _log("falha_ignorada_sem_comando", "segue para conversa")
            return False
        if callable(falar_falha_contextual):
            falar_falha_contextual("entendimento", t)
        return True
    if status_analise == "sem_intencao":
        _log("sem_intencao_llm")
        return False
    if not isinstance(resultado, dict):
        return False

    if resultado.get("intent") == "RESUMIR_PAGINA":
        _log("llm_resumir_pagina")
        if ws_loop and callable(resumir_pagina_ou_video):
            asyncio.run_coroutine_threadsafe(resumir_pagina_ou_video(), ws_loop)
        elif callable(falar_com_lipsync):
            falar_com_lipsync("O servidor WebSocket não está ativo. Não consigo resumir a página.", "irritada", 2)
        return True

    try:
        _log("llm_intencao", str(resultado.get("intent") or ""))
        executou = bool(executar_intencao(resultado, t)) if callable(executar_intencao) else False
        if callable(registrar_resultado_execucao):
            registrar_resultado_execucao(resultado, t, executou, origem="imediato_llm")
        if str(resultado.get("intent") or "").upper().strip() == "SUGGEST_ACTION" and not executou:
            _log("sugestao_invalida", "seguindo como conversa")
            return False
        return True
    except Exception:
        alvo_falha = str(
            (resultado.get("params") or {}).get("nome_app")
            or (resultado.get("params") or {}).get("nome_playlist")
            or (resultado.get("params") or {}).get("query")
            or (resultado.get("params") or {}).get("url")
            or (resultado.get("params") or {}).get("alvo")
            or ""
        ).strip()
        if callable(falar_falha_contextual):
            falar_falha_contextual("execucao", t, detalhe=alvo_falha)
        return True


class ComandosImediatosRuntime:
    def __init__(
        self,
        *,
        namespace_getter: Callable[[], Dict[str, Any]],
        loop_getter: Callable[[], Any],
        memoria_pessoas: PortaMemoriaPessoas | None = None,
        iot: PortaIoT | None = None,
    ) -> None:
        self.namespace_getter = namespace_getter
        self.loop_getter = loop_getter
        self.memoria_pessoas = memoria_pessoas
        self.iot = iot

    def processar(self, texto: str, *, contexto_mental_ja_refinado: bool = False) -> bool:
        ns = self.namespace_getter() or {}
        nomes = (
            "_normalizar_texto_com_apelidos", "_texto_social_curto",
            "_texto_conversa_casual_sem_acao", "_refinar_contexto_mental",
            "_texto_tem_comando_explicito", "_texto_conversa_contextual_sem_comando",
            "_resolver_comando_janela_contextual_forcado", "_resolver_comando_midia_contextual_forcado",
            "_resolver_comando_arquivo_contextual_forcado", "_resolver_comando_acao_geral_contextual_forcado",
            "_resolver_comando_contextual_forcado", "_responder_contexto_janela_indisponivel",
            "_resolver_repeticao_ultima_acao",
            "_resolver_consulta_recurso_local", "_executar_consulta_recurso_local",
            "_texto_parece_consulta_operacional",
            "_extrair_acao_agendada_local",
            "processar_comandos_em_cadeia", "processar_comando_deterministico",
            "interpretar_comando_local_rapido", "analisar_intencao", "executar_intencao",
            "decisao_comando_ja_avaliada",
            "_registrar_resultado_execucao", "_registrar_autoaprimoramento",
            "_falar_falha_contextual", "resumir_pagina_ou_video", "falar_com_lipsync",
        )
        contexto = {nome: ns.get(nome) for nome in nomes}
        estado_runtime = ns.get("_estado_compartilhado_runtime")
        contexto["mente_integrada_estado"] = getattr(estado_runtime, "mental", {})
        contexto["_contexto_mental_ja_refinado"] = bool(contexto_mental_ja_refinado)
        contexto["ws_loop"] = self.loop_getter()
        return processar_comandos_imediatos(contexto, texto)

    def processar_prioritarios(self, texto: str) -> bool:
        """Protege percepções objetivas antes dos fallbacks conversacionais."""
        ns = self.namespace_getter() or {}
        orquestrador_cooperativo = ns.get("_orquestrador_cooperativo_runtime")
        if callable(getattr(orquestrador_cooperativo, "processar", None)):
            try:
                if orquestrador_cooperativo.processar(texto):
                    print("⚡ [PRIORIDADE:COOPERAÇÃO] plano entre habilidades tratado")
                    return True
            except Exception as erro:
                print(
                    "⚠️ [COOPERAÇÃO] falha isolada: "
                    f"{type(erro).__name__}: {erro}"
                )
        processar_oferta_clipboard = ns.get("_processar_oferta_area_transferencia_pendente")
        if callable(processar_oferta_clipboard):
            try:
                if processar_oferta_clipboard(texto):
                    print("⚡ [PRIORIDADE:ÁREA DE TRANSFERÊNCIA] resposta natural à oferta tratada")
                    return True
            except Exception as erro:
                print(
                    "⚠️ [ÁREA DE TRANSFERÊNCIA] resposta à oferta isolada: "
                    f"{type(erro).__name__}: {erro}"
                )
        memoria_pessoas = self.memoria_pessoas
        if callable(getattr(memoria_pessoas, "processar", None)):
            try:
                if memoria_pessoas.processar(texto):
                    print("⚡ [PRIORIDADE:MEMÓRIA DE PESSOAS] pedido tratado")
                    return True
            except Exception as erro:
                print(
                    "⚠️ [MEMÓRIA:PESSOAS] falha isolada: "
                    f"{type(erro).__name__}: {erro}"
                )
        central_notificacoes = ns.get("_central_notificacoes_runtime")
        detectar_notificacao = getattr(central_notificacoes, "detectar", None)
        if callable(detectar_notificacao):
            try:
                comando_notificacao = detectar_notificacao(texto)
            except Exception as erro:
                print(
                    "⚠️ [CENTRAL DE NOTIFICAÇÕES] falha isolada: "
                    f"{type(erro).__name__}: {erro}"
                )
                comando_notificacao = None
            if isinstance(comando_notificacao, dict):
                executar = ns.get("executar_intencao")
                if callable(executar):
                    executou = bool(executar(comando_notificacao, texto))
                    registrar = ns.get("_registrar_resultado_execucao")
                    if callable(registrar):
                        registrar(
                            comando_notificacao,
                            texto,
                            executou,
                            origem="prioritario_central_notificacoes",
                        )
                    print("⚡ [PRIORIDADE:NOTIFICAÇÕES] pedido tratado pela central")
                    return True
        area_transferencia = ns.get("_area_transferencia_runtime")
        if callable(getattr(area_transferencia, "processar", None)):
            try:
                if area_transferencia.processar(texto):
                    print("⚡ [PRIORIDADE:ÁREA DE TRANSFERÊNCIA] pedido temporário tratado")
                    return True
            except Exception as erro:
                print(
                    "⚠️ [ÁREA DE TRANSFERÊNCIA] falha isolada: "
                    f"{type(erro).__name__}: {erro}"
                )
        caixa_entrada = ns.get("_caixa_entrada_pessoal_runtime")
        if callable(getattr(caixa_entrada, "processar", None)):
            try:
                if caixa_entrada.processar(texto):
                    print("⚡ [PRIORIDADE:CAIXA DE ENTRADA] pedido pessoal tratado")
                    return True
            except Exception as erro:
                print(
                    "⚠️ [CAIXA DE ENTRADA] falha isolada: "
                    f"{type(erro).__name__}: {erro}"
                )
        resolver_repeticao = ns.get("_resolver_repeticao_ultima_acao")
        if callable(resolver_repeticao) and callable(getattr(caixa_entrada, "reexecutar", None)):
            try:
                repeticao = resolver_repeticao(texto)
            except Exception:
                repeticao = None
            if (
                isinstance(repeticao, dict)
                and str(repeticao.get("intent") or "").upper() == "INBOX_LIST"
                and caixa_entrada.reexecutar(repeticao, texto)
            ):
                print("⚡ [PRIORIDADE:CAIXA DE ENTRADA] consulta repetida pela continuidade oficial")
                return True
        texto_iot = str(texto or "")
        menciona_iot = bool(re.search(
            r"\b(?:luz|luzes|lampada|lâmpada|ventilador|tomada|dispositivo|aparelho|iot)\b",
            texto_iot,
            flags=re.IGNORECASE,
        ))
        if menciona_iot and bloqueia_controle_iot_por_modalidade(texto_iot):
            # É instrução, dúvida ou recusa sobre uma ação, não uma ação. Uma
            # resposta local curta evita LLM e impede que os roteadores sejam
            # chamados novamente no pós-processamento.
            pergunta_como = bool(re.search(
                r"^(?:como\s+(?:eu\s+)?(?:faria|faço|faco|posso|poderia)|"
                r"o\s+que\s+(?:eu\s+)?(?:faria|faço|faco))\b",
                texto_iot.strip(),
                flags=re.IGNORECASE,
            ))
            if pergunta_como:
                fala = (
                    "É só me pedir diretamente para desligar a luz. "
                    "Como você perguntou apenas como fazer, não alterei nada agora."
                )
            else:
                fala = "Pode deixar. Não vou alterar a luz."
            print("🛡️ [PRIORIDADE:IOT] menção sem autorização; nenhum comando foi criado")
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar(fala, "calma", 1)
            return True
        # Consultas de estado são somente leitura. Elas precisam chegar ao
        # runtime IoT antes que "como ele está?" seja confundido com conversa.
        detectar_iot = getattr(self.iot, "detectar", None)
        estado_runtime = ns.get("_estado_compartilhado_runtime")
        mente_iot = getattr(estado_runtime, "mental", {})
        turno_prioritario = dict(mente_iot.get("turno_atual") or {}) if isinstance(mente_iot, dict) else {}
        candidato_iot = (
            detectar_iot(texto, mente_iot)
            if callable(detectar_iot)
            else None
        )
        if isinstance(candidato_iot, dict) and str(candidato_iot.get("intent") or "").upper() == "IOT_STATUS":
            print("⚡ [PRIORIDADE:IOT] consulta contextual de estado")
            executar = ns.get("executar_intencao")
            if callable(executar):
                executou = bool(executar(candidato_iot, texto))
                registrar = ns.get("_registrar_resultado_execucao")
                if callable(registrar):
                    registrar(candidato_iot, texto, executou, origem="prioritario_iot_status")
                return True

        consulta_iot = detectar_consulta_lista_iot(texto)
        if consulta_iot:
            print("⚡ [PRIORIDADE:IOT] listagem objetiva de dispositivos")
            executar = ns.get("executar_intencao")
            if not callable(executar):
                return False
            try:
                executou = bool(executar(consulta_iot, texto))
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:IOT] falha ao listar: "
                    f"{type(erro).__name__}: {erro}"
                )
                return False
            registrar = ns.get("_registrar_resultado_execucao")
            if callable(registrar):
                registrar(
                    consulta_iot, texto, executou, origem="prioritario_iot_lista",
                )
            return True

        responder_capacidade = ns.get("_responder_pergunta_capacidade_local")
        fala_capacidade = responder_capacidade(texto) if callable(responder_capacidade) else ""
        if fala_capacidade:
            print("⚡ [PRIORIDADE:HABILIDADE] consulta sobre capacidade real")
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar(fala_capacidade, "calma", 1)
            return True
        if detectar_consulta_horario(texto):
            agora_cb = ns.get("_agora_temporal_cb")
            agora = agora_cb() if callable(agora_cb) else agora_no_fuso()
            fala = responder_consulta_horario(agora)
            print("⚡ [PRIORIDADE:RELÓGIO] consulta local objetiva")
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar(fala, "calma", 1)
            return True
        detectar_governanca = ns.get("_detectar_comando_governanca_iniciativa")
        pedido_governanca = (
            detectar_governanca(texto) if callable(detectar_governanca) else None
        )
        if pedido_governanca:
            print("⚡ [PRIORIDADE:AUTONOMIA] configuração explícita")
            processar_governanca = ns.get("_processar_governanca_iniciativa")
            if callable(processar_governanca):
                processar_governanca(pedido_governanca)
            return True
        detectar_diagnostico = ns.get("_detectar_pedido_diagnostico_mente")
        if callable(detectar_diagnostico) and detectar_diagnostico(texto):
            print("⚡ [PRIORIDADE:DIAGNÓSTICO] retrato da mente única")
            mostrar_diagnostico = ns.get("_mostrar_diagnostico_mente")
            if callable(mostrar_diagnostico):
                mostrar_diagnostico()
            return True
        detectar_saude = ns.get("detectar_comando_saude")
        if callable(detectar_saude) and detectar_saude(texto):
            print("⚡ [PRIORIDADE:SAÚDE] consulta objetiva do computador")
            falar_saude = ns.get("_falar_status_saude")
            if callable(falar_saude):
                falar_saude()
            return True
        # O retrato congelado completa pronomes e elipses na resolução central.
        # Não há mais uma rota particular para playlist aqui: música, arquivos,
        # IoT, agenda e habilidades futuras passam pelo mesmo coordenador.
        estado_runtime = ns.get("_estado_compartilhado_runtime")
        mente = getattr(estado_runtime, "mental", {})
        retrato = dict(mente.get("retrato_turno_atual") or {}) if isinstance(mente, dict) else {}
        if texto_pede_resumo_pagina(texto):
            print("⚡ [PRIORIDADE:RESUMO] leitura da página atual")
            return self.processar(texto, contexto_mental_ja_refinado=False)

        # Última barreira antes da conversa: usa o coordenador canônico inteiro,
        # não só o detector de frases literais. Esse único caminho combina
        # linguagem natural, catálogo de habilidades, contexto, referências e
        # o árbitro de segurança. Ele também evita chamar o roteador uma vez
        # aqui e outra no fluxo principal.
        resolver_natural = ns.get("resolver_comando_natural")
        try:
            if callable(resolver_natural):
                resolucao = resolver_natural(
                    texto, "prioritario-linguagem-natural",
                )
            else:
                # Compatibilidade para composições mínimas e clientes antigos.
                # Na aplicação real o coordenador acima sempre existe, portanto
                # esta rota não duplica a classificação de um turno normal.
                if not bool(turno_prioritario.get("autoriza_execucao")):
                    resolucao = (None, "")
                    detectar_legado = None
                else:
                    detectar_legado = ns.get("detectar_intencao_deterministica")
                legado = (
                    detectar_legado(texto)
                    if callable(detectar_legado)
                    else None
                )
                intent_legado = str(
                    (legado or {}).get("intent")
                    if isinstance(legado, dict) else ""
                ).upper().strip()
                if intent_legado in {
                    "DELETE_ITEM", "MOVE_ITEM", "FILE_TRANSACTION",
                    "FILE_OPEN_RESULT",
                }:
                    resolver_arquivo = ns.get(
                        "_resolver_comando_arquivo_contextual_forcado"
                    )
                    contextual = (
                        resolver_arquivo(texto)
                        if callable(resolver_arquivo)
                        else None
                    )
                    if (
                        isinstance(contextual, dict)
                        and str(contextual.get("intent") or "").upper().strip()
                        == intent_legado
                    ):
                        legado = contextual
                legado = resolver_referencias_da_intencao(legado, retrato)
                resolucao = (legado, "deterministico-compatibilidade")
        except Exception as erro:
            print(
                "⚠️ [PRIORIDADE:LINGUAGEM NATURAL] resolução falhou: "
                f"{type(erro).__name__}: {erro}"
            )
            resolucao = (None, "")
        detectada, rota = (
            resolucao
            if isinstance(resolucao, tuple) and len(resolucao) == 2
            else (None, "")
        )
        intent_detectada = str(
            (detectada or {}).get("intent") if isinstance(detectada, dict) else ""
        ).upper().strip()
        if (
            isinstance(detectada, dict)
            and intent_detectada in set(intents_registradas())
            and intent_detectada != "SUGGEST_ACTION"
        ):
            print(
                "⚡ [PRIORIDADE:LINGUAGEM NATURAL] "
                f"intent={intent_detectada} | rota={rota or 'coordenador'}"
            )
            executar = ns.get("executar_intencao")
            if not callable(executar):
                return False
            try:
                executou = bool(executar(detectada, texto))
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:LINGUAGEM NATURAL] falha ao executar: "
                    f"{type(erro).__name__}: {erro}"
                )
                falar_falha = ns.get("_falar_falha_contextual")
                if callable(falar_falha):
                    falar_falha("execucao", texto)
                # A frase já foi compreendida; não a devolva à conversa para
                # inventar incapacidade, sucesso ou um pedido de repetição.
                return True
            compat_playlist = (
                rota == "deterministico-compatibilidade"
                and str(
                    retrato.get("operacao_explicita")
                    or turno_prioritario.get("operacao_explicita")
                    or ""
                ).strip().casefold() == "playlist_adicionar"
                and intent_detectada == "PLAYLIST_ADD"
            )
            registrar = ns.get("_registrar_resultado_execucao")
            if callable(registrar):
                origem_resultado = (
                    "prioritario_playlist"
                    if compat_playlist
                    else "prioritario_comando_explicito"
                    if rota == "deterministico-compatibilidade"
                    else f"prioritario_linguagem_natural:{rota or 'coordenador'}"
                )
                registrar(
                    detectada,
                    texto,
                    executou,
                    origem=origem_resultado,
                )
            autoaprimorar = ns.get("_registrar_autoaprimoramento")
            if executou and callable(autoaprimorar):
                contexto_aprendizado = (
                    "playlist explícita prioritária"
                    if compat_playlist
                    else "comando explícito prioritário"
                    if rota == "deterministico-compatibilidade"
                    else f"linguagem natural:{rota or 'coordenador'}"
                )
                origem_aprendizado = (
                    "prioritario_playlist"
                    if compat_playlist
                    else "prioritario_comando_explicito"
                    if rota == "deterministico-compatibilidade"
                    else "prioritario_linguagem_natural"
                )
                autoaprimorar(
                    detectada,
                    texto,
                    True,
                    contexto=contexto_aprendizado,
                    origem=origem_aprendizado,
                )
            # Resultado indisponível também é um turno tratado. O executor do
            # domínio é quem relata a falha real, sem fallback conversacional.
            return True
        return False


def criar_comandos_imediatos_runtime(**kwargs: Any) -> ComandosImediatosRuntime:
    return ComandosImediatosRuntime(**kwargs)
