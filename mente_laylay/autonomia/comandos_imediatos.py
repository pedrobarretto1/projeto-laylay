"""Fase operacional prioritária do turno canônico da Laylay.

Esta camada recebe o turno já criado, resolve uma única vez habilidades e
linguagem natural e só então libera a conversa livre para a IA.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Callable, Dict
from mente_laylay.integracao.registro_memoria_pessoas import PortaMemoriaPessoas
from mente_laylay.integracao.registro_iot import PortaIoT
from mente_laylay.autonomia.pre_fluxo_contextual import (
    processar_aprendizado_apelido,
    processar_consulta_sistema_local,
    processar_pedido_direcao_musical,
    processar_identidade_usuario,
    processar_sugestao_indireta,
)
from mente_laylay.especialistas.capacidades import (
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
from mente_laylay.memoria_mental.continuidade_geral import (
    resolver_continuacao_aditiva,
    texto_e_continuacao_aditiva,
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

    def processar_prioritarios(self, texto: str) -> bool:
        """Resolve habilidades pelo turno canônico antes da conversa livre."""
        ns = self.namespace_getter() or {}
        estado_runtime = ns.get("_estado_compartilhado_runtime")
        contexto_prioritario = dict(ns)
        contexto_prioritario["mente_integrada_estado"] = getattr(
            estado_runtime, "mental", {},
        )

        # Comandos internos iniciados por barra nunca são respostas naturais
        # a uma oferta pendente. O diagnóstico precisa vencer clipboard,
        # cooperação e conversa para que "/diagnostico mente" não seja lido
        # como "sim, resuma o texto copiado".
        detectar_diagnostico = ns.get("_detectar_pedido_diagnostico_mente")
        if callable(detectar_diagnostico) and detectar_diagnostico(texto):
            print("⚡ [PRIORIDADE:DIAGNÓSTICO] retrato da mente única")
            mostrar_diagnostico = ns.get("_mostrar_diagnostico_mente")
            if callable(mostrar_diagnostico):
                mostrar_diagnostico()
            return True

        # Continuação operacional curta é resolvida diretamente pela fonte
        # canônica antes de clipboard, cooperação ou LLM. O coordenador geral
        # continua sendo a rota para todo o restante; esta barreira cobre
        # apenas políticas aditivas explicitamente seguras, como manter a
        # playlist e usar a nova faixa atual em ``essa também``.
        if texto_e_continuacao_aditiva(texto):
            continuidade_aditiva = resolver_continuacao_aditiva(
                getattr(estado_runtime, "mental", {}),
                texto=texto,
            )
            if continuidade_aditiva:
                executar = ns.get("executar_intencao")
                if callable(executar):
                    try:
                        executou = bool(executar(continuidade_aditiva, texto))
                    except Exception as erro:
                        print(
                            "⚠️ [PRIORIDADE:CONTINUIDADE] falha isolada: "
                            f"{type(erro).__name__}: {erro}"
                        )
                        return True
                    registrar = ns.get("_registrar_resultado_execucao")
                    if callable(registrar):
                        registrar(
                            continuidade_aditiva,
                            texto,
                            executou,
                            origem="prioritario_continuidade_aditiva",
                        )
                    print(
                        "⚡ [PRIORIDADE:CONTINUIDADE] "
                        f"intent={continuidade_aditiva.get('intent')}"
                    )
                    return True

        # Uma entrada de barra é um comando interno ou uma tentativa dele;
        # nunca representa "sim" para uma pergunta aberta. Isso evita que um
        # typo ou a saída concorrente do terminal entregue o clipboard para
        # resumo por engano.
        if str(texto or "").lstrip().startswith("/"):
            print("⚠️ [COMANDO INTERNO] comando de barra não reconhecido")
            return True

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
        # Estas habilidades eram atalhos do pré-fluxo. Agora pertencem à fase
        # operacional única, depois da criação do turno e antes da conversa.
        habilidades_prioritarias = (
            processar_identidade_usuario,
            processar_consulta_sistema_local,
            processar_pedido_direcao_musical,
            processar_sugestao_indireta,
            processar_aprendizado_apelido,
        )
        for habilidade in habilidades_prioritarias:
            try:
                tratada, rota = habilidade(contexto_prioritario, texto)
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:HABILIDADE] falha isolada em "
                    f"{habilidade.__name__}: {type(erro).__name__}: {erro}"
                )
                continue
            if tratada:
                print(
                    "⚡ [PRIORIDADE:HABILIDADE] "
                    f"rota={rota or habilidade.__name__}"
                )
                return True
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
        detectar_saude = ns.get("detectar_comando_saude")
        if callable(detectar_saude) and detectar_saude(texto):
            print("⚡ [PRIORIDADE:SAÚDE] consulta objetiva do computador")
            falar_saude = ns.get("_falar_status_saude")
            if callable(falar_saude):
                falar_saude()
            return True
        if texto_pede_resumo_pagina(texto):
            print("⚡ [PRIORIDADE:RESUMO] leitura da página atual")
            executar = ns.get("executar_intencao")
            if not callable(executar):
                return False
            intencao_resumo = {"intent": "RESUMIR_PAGINA", "params": {}}
            executou = bool(executar(intencao_resumo, texto))
            registrar = ns.get("_registrar_resultado_execucao")
            if callable(registrar):
                registrar(
                    intencao_resumo,
                    texto,
                    executou,
                    origem="prioritario_resumo_pagina",
                )
            return True

        # Última barreira antes da conversa: usa o coordenador canônico inteiro,
        # não só o detector de frases literais. Esse único caminho combina
        # linguagem natural, catálogo de habilidades, contexto, referências e
        # o árbitro de segurança. Ele também evita chamar o roteador uma vez
        # aqui e outra no fluxo principal.
        resolver_natural = ns.get("resolver_comando_natural")
        try:
            resolucao = (
                resolver_natural(texto, "prioritario-linguagem-natural")
                if callable(resolver_natural)
                else (None, "")
            )
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
            registrar = ns.get("_registrar_resultado_execucao")
            if callable(registrar):
                registrar(
                    detectada,
                    texto,
                    executou,
                    origem=f"prioritario_linguagem_natural:{rota or 'coordenador'}",
                )
            autoaprimorar = ns.get("_registrar_autoaprimoramento")
            if executou and callable(autoaprimorar):
                autoaprimorar(
                    detectada,
                    texto,
                    True,
                    contexto=f"linguagem natural:{rota or 'coordenador'}",
                    origem="prioritario_linguagem_natural",
                )
            # Resultado indisponível também é um turno tratado. O executor do
            # domínio é quem relata a falha real, sem fallback conversacional.
            return True
        return False


def criar_comandos_imediatos_runtime(**kwargs: Any) -> ComandosImediatosRuntime:
    return ComandosImediatosRuntime(**kwargs)
