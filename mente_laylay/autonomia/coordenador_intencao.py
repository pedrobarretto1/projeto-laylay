"""Coordenador unico do fluxo de intencao da Laylay."""

from __future__ import annotations

import re
import time
import json
from copy import deepcopy
from threading import Event, RLock, get_ident
from typing import Any, Callable, Dict, Tuple
from uuid import uuid4

from mente_laylay.autonomia.analise_comandos import (
    executar_comando_em_texto,
    processar_comandos_em_cadeia,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_playlist_contextual_musica_atual,
)
from mente_laylay.autonomia.agendamento_mental import (
    extrair_complemento_temporal_lembrete,
    texto_pede_lembrete_explicito,
)
from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    classificar_confirmacao_local,
)
from mente_laylay.cognicao.arbitro_turno import CandidatoDecisao, arbitrar_turno
from mente_laylay.cognicao.referencias_linguagem import (
    separar_alvo_e_complemento_foco,
    valor_e_referencia_contextual,
)
from mente_laylay.especialistas.capacidades import INTENTS_SOMENTE_LEITURA, intents_registradas
from mente_laylay.autonomia.classificacao_habilidade import classificar_habilidade_intent
from mente_laylay.cognicao.evidencia_operacional import (
    bloqueia_controle_iot_por_modalidade,
)
from mente_laylay.memoria_mental.continuidade_geral import (
    normalizar_dominio_continuidade,
    resolver_continuacao_aditiva,
)
from mente_laylay.memoria_mental.pendencia_acao import dominio_pendencia
from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos

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
    "_limpar_nome_playlist",
    "_extrair_agendamento_local",
    "_extrair_acao_agendada_local",
    "_registrar_resultado_execucao",
    "_registrar_autoaprimoramento",
    "_detectar_repetir_briefing",
    "repetir_briefing",
    "interpretar_comando_local_rapido",
    "_texto_parece_consulta_operacional",
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
        or params.get("site") or params.get("nome") or params.get("pasta")
        or params.get("nome_playlist") or params.get("playlist") or ""
    ).strip().casefold()
    fala = str(texto or "").strip().casefold()
    if intent in {"CREATE_FOLDER", "CREATE_FILE", "DELETE_ITEM", "CONFIRM_DELETE_ITEM", "CANCEL_DELETE_ITEM", "RESTORE_DELETED_ITEM", "MOVE_ITEM", "FILE_TRANSACTION", "FILE_READ", "FILE_OPEN_RESULT"}:
        return not valor_e_referencia_contextual(alvo)
    if intent in {"APP_OPEN", "CLOSE_APP", "MAXIMIZE_WINDOW", "OPEN_URL", "CLOSE_TAB"}:
        # "essa aba" nomeia inequivocamente a aba ativa; não precisa herdar
        # um nome, ao contrário de "esse app" ou "esse site".
        if intent == "CLOSE_TAB" and not alvo and re.search(r"\b(?:fecha|fechar|encerra|encerrar)\b.*\baba\b", fala):
            return True
        return not valor_e_referencia_contextual(alvo)
    if intent == "ORGANIZAR_DESKTOP":
        if _eh_elipse_espacial_c1c_contextual(resultado):
            return False
        if str(params.get("modo") or "").casefold() == "automatico":
            return True
        lados = [
            str(params.get(chave) or "").strip()
            for chave in ("left", "right", "esquerda", "direita")
            if str(params.get(chave) or "").strip()
        ]
        return bool(lados) and all(not valor_e_referencia_contextual(valor) for valor in lados)
    if intent in {"IOT_CONTROL", "IOT_STATUS"}:
        return not valor_e_referencia_contextual(alvo) and any(
            nome in fala for nome in ("ventilador", "tomada", "luz", "lampada", "lâmpada", "dispositivo")
        )
    if intent == "PLAYLIST_MOVE":
        origem = str(params.get("origem") or params.get("playlist_origem") or "").strip()
        destino = str(params.get("destino") or params.get("playlist_destino") or "").strip()
        musica = str(params.get("musica") or params.get("faixa") or "").strip()
        return bool(origem and destino and musica) and not any(
            valor_e_referencia_contextual(valor)
            for valor in (origem, destino, musica)
        )
    if intent in {"PLAYLIST_CREATE", "PLAYLIST_ADD", "PLAYLIST_PLAY", "PLAYLIST_LIST", "PLAYLIST_DELETE"}:
        # Em PLAYLIST_ADD, "essa música" resolve a fonte pelo player atual,
        # mas o destino dito depois de "playlist" já é um alvo explícito.
        return not valor_e_referencia_contextual(alvo) and "playlist" in fala
    if intent in {"LAYLAY_PLAYLIST_PLAY", "LAYLAY_PLAYLIST_COPY"}:
        # O detector da curadoria resolve o ordinal para ``#N`` ou para um
        # nome catalogado. A posse "sua" é contexto de domínio, não um alvo
        # incompleto que precise voltar à conversa livre.
        return bool(alvo) and (
            alvo.startswith("#") or not valor_e_referencia_contextual(alvo)
        )
    if intent == "MUSIC_SEARCH":
        consulta = str(
            params.get("query") or params.get("musica") or params.get("nome") or ""
        ).strip().casefold()
        return bool(consulta) and not valor_e_referencia_contextual(consulta) and bool(
            re.search(r"\b(?:coloca|colocar|bota|botar|toca|tocar|poe|põe|quero\s+ouvir)\b", fala)
        )
    if intent in {"MEDIA_CONTROL", "VOLUME"}:
        acao = str(params.get("acao") or "").strip()
        return bool(acao)
    if intent in INTENTS_SOMENTE_LEITURA:
        # Consultas operacionais são seguras e completas mesmo quando o retrato
        # do jogo faz a frase parecer contextual. O detector já forneceu a
        # habilidade; não há motivo para fazê-la esperar pela LLM local.
        return True
    return False


def _eh_elipse_espacial_c1c_contextual(resultado: Any) -> bool:
    if not isinstance(resultado, dict):
        return False
    if _normalizar_intent(resultado) != "ORGANIZAR_DESKTOP":
        return False
    params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
    if set(params) == {"left", "modo", "referencia_contextual", "referencia_contextual_fonte", "direcao_original"}:
        lado, direcao = "left", "esquerda"
    elif set(params) == {"right", "modo", "referencia_contextual", "referencia_contextual_fonte", "direcao_original"}:
        lado, direcao = "right", "direita"
    else:
        return False
    return bool(
        str(params.get("modo") or "").casefold() == "posicionar"
        and params.get("referencia_contextual") is True
        and str(params.get("referencia_contextual_fonte") or "") == "turno_atual.referencia_resolvida"
        and str(params.get("direcao_original") or "").casefold() == direcao
        and str(params.get(lado) or "").strip()
    )


def _intencao_deterministica_depende_contexto_operacional(resultado: Any) -> bool:
    return _eh_elipse_espacial_c1c_contextual(resultado)


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
    dados_referencia = dict(referencia.get("dados") or {})
    def resolver_campo(chaves: tuple[str, ...], tipos_aceitos: set[str]) -> bool:
        for chave in chaves:
            valor = str(params.get(chave) or "").strip()
            if not valor:
                continue
            if not valor_e_referencia_contextual(valor):
                continue
            if not nome or tipo not in tipos_aceitos:
                return False
            params[f"{chave}_original"] = valor[:160]
            valor_resolvido = nome
            if tipo in {"arquivo", "pasta"}:
                valor_resolvido = str(dados_referencia.get("caminho") or nome).strip()
            params[chave] = valor_resolvido
            params["referencia_contextual"] = True
        return True

    if intent == "MUSIC_SEARCH":
        query = str(params.get("query") or "").strip()
        query_norm = query.casefold()
        referencia_crua = valor_e_referencia_contextual(query) or bool(re.search(
            r"\b(?:ele|ela|dele|dela|desse|dessa)\b", query_norm
        ))
        tipos_musicais = {
            "artista", "cantor", "cantora", "banda", "referencia_nomeada",
            "musica", "playlist",
        }
        if referencia_crua and nome and tipo in tipos_musicais:
            params["query_original"] = query[:160]
            params["query"] = nome
            params["referencia_contextual"] = True
        elif referencia_crua:
            return None
        saida["params"] = params
    elif intent == "SEARCH":
        query = str(params.get("query") or "").strip()
        if valor_e_referencia_contextual(query):
            tipos_pesquisaveis = {
                "referencia_nomeada", "jogo", "filme", "serie", "livro",
                "artista", "cantor", "cantora", "banda", "musica",
            }
            if not nome or tipo not in tipos_pesquisaveis:
                return None
            params["query_original"] = query[:160]
            params["query"] = nome
            params["referencia_contextual"] = True
        saida["params"] = params
    elif intent in {"APP_OPEN", "CLOSE_APP", "MAXIMIZE_WINDOW"}:
        # Defesa comum para qualquer origem da intenção (determinístico, IA,
        # continuidade ou botão). Um complemento operacional nunca pode virar
        # parte do nome passado ao executor. Depois da separação, pronomes
        # continuam obrigados a resolver pelo retrato do turno.
        for chave in ("nome_app", "app", "alvo"):
            valor = str(params.get(chave) or "").strip()
            if not valor:
                continue
            alvo_limpo, pediu_foco = separar_alvo_e_complemento_foco(valor)
            if pediu_foco:
                params[chave] = alvo_limpo
                if intent == "APP_OPEN":
                    params["modo"] = "focus"
        if not resolver_campo(("nome_app", "app", "alvo"), {"app", "janela"}):
            return None
    elif intent == "ORGANIZAR_DESKTOP":
        if not resolver_campo(("left", "right", "esquerda", "direita"), {"app", "janela"}):
            return None
    elif intent in {"OPEN_URL", "CLOSE_TAB", "SITE_ENTER"}:
        if not resolver_campo(("alvo", "site", "url"), {"site", "janela"}):
            return None
    elif intent in {"IOT_CONTROL", "IOT_STATUS"}:
        if not resolver_campo(("alvo", "dispositivo"), {"iot", "dispositivo"}):
            return None
    elif intent in {"PLAYLIST_CREATE", "PLAYLIST_PLAY", "PLAYLIST_ADD", "PLAYLIST_LIST", "PLAYLIST_DELETE"}:
        if not resolver_campo(("nome_playlist", "playlist"), {"playlist"}):
            return None
    elif intent == "PLAYLIST_MOVE":
        if not resolver_campo(("origem", "playlist_origem"), {"playlist"}):
            return None
        if not resolver_campo(("destino", "playlist_destino"), {"playlist"}):
            return None
    elif intent in {"DELETE_ITEM", "MOVE_ITEM", "FILE_TRANSACTION", "FILE_OPEN_RESULT"}:
        if not resolver_campo(("alvo", "origem"), {"arquivo", "pasta"}):
            return None
    saida["params"] = params
    return saida


def resolver_intencao(texto: str, origem: str, ctx: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, str]:
    texto_norm = _call(ctx, "normalizar_texto", texto, default=str(texto or ""))
    _call(ctx, "refinar_contexto_mental", texto_norm)
    retrato_atual = dict(ctx.get("retrato_turno_atual") or {})
    turno_congelado = dict(ctx.get("turno_atual") or {})
    # P0_REVISAO_INTRA_TURNO_V1_1_20260816
    revisao_turno = (
        dict(turno_congelado.get("revisao_intra_turno") or {})
        if isinstance(turno_congelado.get("revisao_intra_turno"), dict)
        else {}
    )
    revisao_resolvida = bool(
        revisao_turno.get("detectada")
        and revisao_turno.get("resolvida")
        and not revisao_turno.get("cancelada")
    )
    trecho_operacional = str(
        turno_congelado.get("texto_operacional_efetivo")
        or turno_congelado.get("texto_operacional")
        or ""
    ).strip()
    moldura_nao_autoriza_recorte = bool(
        re.match(r"^(?:nao|não)\b", str(texto_norm or "").strip())
        or "?" in str(texto or "")
        or re.match(
            r"^(?:como\s+(?:eu\s+)?faria|voc[eê]\s+consegue|"
            r"se\s+eu\s+pedir)\b",
            str(texto_norm or "").strip(),
        )
    )
    texto_deteccao = (
        _call(ctx, "normalizar_texto", trecho_operacional, default=trecho_operacional)
        if trecho_operacional
        and (
            revisao_resolvida
            or str(turno_congelado.get("modalidade_geral") or "") == "misto"
        )
        and bool(turno_congelado.get("autoriza_execucao"))
        and not moldura_nao_autoriza_recorte
        else texto_norm
    )

    # Lembretes completos são comandos locais. Eles precisam ser resolvidos
    # antes da IA-first para que uma frase como "me lembra ... daqui 5 minutos"
    # nunca seja respondida como conversa ou promessa sem agendamento real.
    lembrete = _call(ctx, "extrair_agendamento", texto)
    if isinstance(lembrete, dict) and _normalizar_intent(lembrete) in {
        "AGENDAR_LEMBRETE", "LISTAR_AGENDAMENTOS", "CANCELAR_AGENDAMENTO"
    }:
        return lembrete, "agenda"

    pendencia_agenda = dict(ctx.get("pendencia_agenda") or {})
    if pendencia_agenda:
        decisao = classificar_confirmacao_local(texto)
        if decisao is False:
            return {
                "intent": "AGENDAR_LEMBRETE",
                "params": {"cancelar_pendente": True},
            }, "agenda-continuacao"
        metadados = dict(pendencia_agenda.get("metadados") or {})
        complemento = extrair_complemento_temporal_lembrete(
            texto,
            referencia_data=str(metadados.get("referencia_data") or ""),
        )
        if isinstance(complemento, dict):
            complemento.setdefault("descricao", str(metadados.get("descricao") or "lembrete"))
            complemento.setdefault("data_hora", str(metadados.get("referencia_data") or ""))
            complemento["pendencia_id"] = str(pendencia_agenda.get("id") or "")
            return {
                "intent": "AGENDAR_LEMBRETE",
                "params": complemento,
            }, "agenda-continuacao"

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

    # Elipses aditivas pertencem à continuidade oficial, não a um detector de
    # domínio específico. O coordenador consulta essa fonte diretamente para
    # que "essa também" preserve a operação e o destino anteriores mesmo se
    # um especialista determinístico estiver degradado ou não produzir um
    # candidato neste turno. A arbitragem abaixo continua sendo a autoridade
    # que permite ou bloqueia a execução.
    continuidade_aditiva = resolver_continuacao_aditiva(
        {"continuidade_geral": dict(ctx.get("continuidade_geral") or {})},
        texto=texto_norm,
    )

    # O detector de domínio recebe a fala original sempre que o turno inteiro
    # é operacional. A forma normalizada remove pontuação útil de argumentos
    # (por exemplo, transforma ``resultado.md`` em ``resultado md``). O
    # orquestrador determinístico já cria sua própria cópia normalizada para
    # comparar verbos, portanto manter o original aqui não reduz tolerância a
    # português e preserva nomes, URLs, aspas e extensões.
    preservar_argumentos_arquivo = bool(
        str(turno_congelado.get("modalidade_geral") or "") != "misto"
        and re.search(
            r"\b(?:arquivo|pasta|documento|escreve|escreva|grava|grave)\b",
            str(texto or ""),
            flags=re.IGNORECASE,
        )
        and (
            bool(re.search(r"\.[a-z0-9]{1,8}\b", str(texto or ""), re.IGNORECASE))
            or '"' in str(texto or "")
            or "'" in str(texto or "")
            or bool(re.search(r"\b(?:nele|nela|dentro\s+dele|dentro\s+dela)\b", str(texto or ""), re.IGNORECASE))
        )
    )
    texto_detector_deterministico = (
        str(texto or "") if preservar_argumentos_arquivo else texto_deteccao
    )
    intent_deterministica = resolver_referencias_da_intencao(
        _call(ctx, "detectar_intencao_deterministica", texto_detector_deterministico),
        retrato_atual,
    )
    # Salvaguarda de leitura do próprio projeto. O detector composto pode
    # estar degradado ou ausente em uma instalação parcial; uma busca explícita
    # de arquivo/código continua sendo segura e não deve cair na conversa livre.
    # Aceitamos somente FILE_SEARCH aqui: mutações permanecem exclusivamente
    # no caminho determinístico principal e em suas políticas de confirmação.
    busca_codigo_explicita = (
        ("codigo" in texto_deteccao or "código" in texto_deteccao)
        and any(
            verbo in texto_deteccao
            for verbo in ("encontra", "encontre", "ache", "localiza", "localize")
        )
    )
    if _normalizar_intent(intent_deterministica) in {"", "NONE"} and busca_codigo_explicita:
        consulta_arquivo = detectar_intencao_arquivos(
            texto_deteccao,
            params_cb=lambda **kwargs: kwargs,
            estado_mental={},
            normalizar_texto=ctx.get("normalizar_texto"),
        )
        if (
            isinstance(consulta_arquivo, dict)
            and _normalizar_intent(consulta_arquivo) == "FILE_SEARCH"
        ):
            intent_deterministica = consulta_arquivo
    # Salvaguarda local do coordenador para uma operação explícita e de baixo
    # risco. A composição real pode manter o detector de domínio indisponível
    # ou devolver ``None`` sem lançar erro; nesse caso o pedido não pode cair
    # na conversa livre. Esta rota só roda quando o detector principal não
    # produziu candidato, portanto não duplica classificação nem execução.
    if _normalizar_intent(intent_deterministica) in {"", "NONE"}:
        limpar_playlist = ctx.get("limpar_nome_playlist")
        if not callable(limpar_playlist):
            limpar_playlist = lambda valor: str(valor or "").strip(" \t\r\n.,;:!?\"'")
        intent_deterministica = resolver_referencias_da_intencao(
            detectar_playlist_contextual_musica_atual(
                texto_deteccao,
                params_cb=lambda **kwargs: kwargs,
                limpar_nome_playlist=limpar_playlist,
                ultima_playlist=_call(
                    ctx, "musica_estado_get", "ultima_playlist", default="",
                ),
            ),
            retrato_atual,
        )

    candidatos: list[CandidatoDecisao] = []
    det_explicito = _intencao_deterministica_tem_alvo_explicito(intent_deterministica, texto_deteccao)
    det_contexto_operacional = _intencao_deterministica_depende_contexto_operacional(
        intent_deterministica
    )
    depende_contexto_deterministico = bool(
        depende_contexto or det_contexto_operacional
    )
    if isinstance(continuidade_aditiva, dict) and continuidade_aditiva:
        candidatos.append(CandidatoDecisao(
            tipo="comando_contextual",
            valor=continuidade_aditiva,
            origem="continuidade-aditiva",
            confianca=0.97,
            evidencia=("continuidade oficial compatível", "operação aditiva segura"),
        ))
    elif isinstance(intent_deterministica, dict) and (
        not depende_contexto_deterministico or det_explicito
    ):
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

    if depende_contexto_deterministico and not continuidade_aditiva:
        if isinstance(intent_deterministica, dict) and not det_explicito:
            candidatos.append(CandidatoDecisao(
                tipo="comando_contextual",
                valor=intent_deterministica,
                origem="deterministico-contextual",
                confianca=0.62,
                evidencia=(
                    "deteccao deterministica dependente de contexto operacional"
                    if det_contexto_operacional
                    else "deteccao deterministica dependente de contexto",
                ),
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

    # P0_REVISAO_INTRA_TURNO_B1_3_20260816
    # Se a revisão intra-turno já definiu a proposta operacional final,
    # o fallback de IA recebe essa mesma visão. A fala original continua sendo
    # identidade/auditoria, mas não pode reintroduzir a proposta descartada.
    texto_ia = (
        trecho_operacional
        if revisao_resolvida and trecho_operacional
        else texto
    )
    intent = _call(ctx, "tentar_intencao_ai_primeiro", texto_ia)
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
        consulta_operacional = bool(_call(
            ctx, "texto_parece_consulta_operacional", texto_norm, default=False
        ))
        intent_ia = _normalizar_intent(intent_resolvida)
        if modalidade == "confirmacao" and turno_atual.get("confirmacao_contextual_valida"):
            tipo_candidato = "resposta_pendencia"
        elif consulta_operacional and intent_ia in INTENTS_SOMENTE_LEITURA:
            tipo_candidato = "comando_explicito"
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


# P0_CONTRATO_EXECUCAO_NONE_V1_20260815
def _preparar_intent_execucao(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Cria a identidade da ocorrência antes do despacho, sem mutar o pedido original."""
    identificado = dict(intent or {})
    id_existente = str(
        identificado.get("id_solicitacao")
        or identificado.get("request_id")
        or ""
    ).strip()
    identificado["id_solicitacao"] = id_existente or uuid4().hex
    return identificado


def executar_fluxo_intencao(
    texto: str,
    origem: str,
    ctx: Dict[str, Any],
    *,
    texto_original: str = "",
    resolver_cb: Callable[
        [str, str, Dict[str, Any]], Tuple[Dict[str, Any] | None, str]
    ] | None = None,
) -> bool:
    # O pré-fluxo pode entregar em ``texto`` somente o segmento operacional
    # (por exemplo, "desligar a luz"), enquanto ``texto_original`` ainda é
    # "como eu faria..." ou "não desliga...". Não classifique o segmento
    # amputado: além de gerar um candidato falso, ele seria classificado outra
    # vez no pós-IA.
    original = str(texto_original or texto)
    menciona_iot = bool(re.search(
        r"\b(?:luz|luzes|lampada|lâmpada|ventilador|tomada|dispositivo|aparelho|iot)\b",
        original,
        flags=re.IGNORECASE,
    ))
    if menciona_iot and bloqueia_controle_iot_por_modalidade(original):
        return False
    resolvedor = resolver_cb if callable(resolver_cb) else resolver_intencao
    intent, rota = resolvedor(texto, origem, ctx)
    if not isinstance(intent, dict):
        return False

    tag = f" [{origem}]" if origem else ""
    if rota == "imediato":
        tag = f"[{origem}]" if origem else ""
    print(f"⚡ [ROTEADOR {rota.upper()}{tag}] {intent}")

    try:
        texto_execucao = str(texto_original or texto)
        intent_execucao = _preparar_intent_execucao(intent)
        executou = bool(_call(ctx, "executar_intencao", intent_execucao, texto_execucao, default=False))
        _call(
            ctx,
            "registrar_resultado_execucao",
            intent_execucao,
            texto_execucao,
            executou,
            origem=f"{rota}:{origem}",
        )
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
        self._lock_linguagem_natural = RLock()
        self._metricas_linguagem_natural: Dict[str, Any] = {
            "tentativas": 0,
            "resolvidas": 0,
            "sem_intencao": 0,
            "reutilizadas_no_turno": 0,
            "rotas": {},
            "ultima_rota": "",
            "ultima_intent": "",
            "por_habilidade": {},
            "por_moldura": {},
            "comandos_nao_reconhecidos": 0,
            "conversas_legitimas": 0,
            "ultima_classificacao": "",
            "ultima_nao_resolvida": {},
        }
        self._cache_decisao_turno: Dict[
            tuple[str, str], Tuple[Dict[str, Any] | None, str]
        ] = {}
        self._cache_turno_id = ""
        self._lock_execucao_turno = RLock()
        self._execucoes_turno: Dict[tuple[str, str], Dict[str, Any]] = {}
        self._metricas_execucao_turno: Dict[str, int] = {
            "iniciadas": 0,
            "reutilizadas": 0,
            "aguardadas": 0,
            "timeouts": 0,
            "falhas": 0,
        }
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

    @staticmethod
    def _normalizar_valor_acao(valor: Any) -> Any:
        if isinstance(valor, dict):
            metadados = {
                "confidence", "confianca", "referencia_contextual",
                "_semantica", "_rota_contextual",
            }
            return {
                str(chave): CicloComandosRuntime._normalizar_valor_acao(item)
                for chave, item in sorted(valor.items(), key=lambda par: str(par[0]))
                if str(chave) not in metadados
                and not str(chave).endswith("_original")
            }
        if isinstance(valor, (list, tuple, set, frozenset)):
            itens = [CicloComandosRuntime._normalizar_valor_acao(item) for item in valor]
            if isinstance(valor, (set, frozenset)):
                return sorted(itens, key=lambda item: repr(item))
            return itens
        if valor is None or isinstance(valor, (str, int, float, bool)):
            return valor
        return str(valor)

    def _chave_execucao_turno(
        self, resultado: Dict[str, Any], contexto: Dict[str, Any],
    ) -> tuple[str, str] | None:
        turno = dict(contexto.get("turno_atual") or {})
        turno_id = str(turno.get("id") or "").strip()
        intent = _normalizar_intent(resultado)
        if not turno_id or not intent:
            return None
        plano = contexto.get("plano_turno_atual")
        if isinstance(plano, dict) and plano:
            plano_id = str(plano.get("id") or "").strip()
            fase = str(plano.get("fase") or "").strip().casefold()
            if plano_id != turno_id or fase not in {"planejado", "resposta_planejada"}:
                # Ações autônomas e serviços em background não podem herdar o
                # cache de uma conversa que já terminou.
                return None
        params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
        assinatura = json.dumps(
            {
                "intent": intent,
                "params": self._normalizar_valor_acao(params),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return turno_id, assinatura

    def _podar_execucoes_turno(self) -> None:
        if len(self._execucoes_turno) <= 256:
            return
        concluidas = sorted(
            (
                (chave, registro)
                for chave, registro in self._execucoes_turno.items()
                if str(registro.get("status") or "") != "em_andamento"
            ),
            key=lambda item: float(item[1].get("ts") or 0.0),
        )
        for chave, _registro in concluidas[: max(0, len(self._execucoes_turno) - 192)]:
            self._execucoes_turno.pop(chave, None)

    def executar_intencao(self, resultado: Dict[str, Any], texto_original: str) -> bool:
        inicio = time.perf_counter()
        intent = str((resultado or {}).get("intent") or "desconhecida")
        sucesso = False
        try:
            contexto_execucao = self.contexto_intencao_runtime.montar()
        except Exception as erro:
            with self._lock_execucao_turno:
                self._metricas_execucao_turno["falhas"] += 1
            if callable(self.registrar_falha_cb):
                self.registrar_falha_cb("execucao", "falha_contexto_intencao", erro=erro)
            if callable(self.registrar_metrica_cb):
                self.registrar_metrica_cb(
                    "execucao", (time.perf_counter() - inicio) * 1000.0, False,
                )
            raise
        chave_execucao = self._chave_execucao_turno(resultado, contexto_execucao)
        evento_existente: Event | None = None
        if chave_execucao is not None:
            with self._lock_execucao_turno:
                registro = self._execucoes_turno.get(chave_execucao)
                if registro is not None:
                    self._metricas_execucao_turno["reutilizadas"] += 1
                    if str(registro.get("status") or "") == "em_andamento":
                        if int(registro.get("thread_id") or 0) == get_ident():
                            # Evita autoespera caso uma integração devolva a
                            # mesma ação ao coordenador durante sua execução.
                            return False
                        evento_existente = registro.get("evento")
                        self._metricas_execucao_turno["aguardadas"] += 1
                    else:
                        return bool(registro.get("resultado"))
                else:
                    self._execucoes_turno[chave_execucao] = {
                        "status": "em_andamento",
                        "resultado": False,
                        "evento": Event(),
                        "thread_id": get_ident(),
                        "ts": time.monotonic(),
                    }
                    self._metricas_execucao_turno["iniciadas"] += 1
                    self._podar_execucoes_turno()

        if evento_existente is not None:
            if not evento_existente.wait(timeout=30.0):
                with self._lock_execucao_turno:
                    self._metricas_execucao_turno["timeouts"] += 1
                return False
            with self._lock_execucao_turno:
                concluida = self._execucoes_turno.get(chave_execucao, {})
                return bool(concluida.get("resultado"))

        try:
            sucesso = bool(executar_intencao(
                resultado,
                texto_original,
                contexto_execucao,
            ))
            if not sucesso and callable(self.registrar_decisao_cb):
                self.registrar_decisao_cb(
                    "execucao", "nao_confirmada", ("executor retornou falso",), categoria=intent,
                )
            return sucesso
        except Exception as erro:
            with self._lock_execucao_turno:
                self._metricas_execucao_turno["falhas"] += 1
            if callable(self.registrar_falha_cb):
                self.registrar_falha_cb("execucao", "excecao_intencao", erro=erro)
            raise
        finally:
            if chave_execucao is not None:
                with self._lock_execucao_turno:
                    registro = self._execucoes_turno.get(chave_execucao)
                    if registro is not None:
                        registro["status"] = "concluida" if sucesso else "falhou"
                        registro["resultado"] = bool(sucesso)
                        registro["ts"] = time.monotonic()
                        evento = registro.get("evento")
                        if isinstance(evento, Event):
                            evento.set()
            if callable(self.registrar_metrica_cb):
                self.registrar_metrica_cb(
                    "execucao", (time.perf_counter() - inicio) * 1000.0, sucesso,
                )

    def tentar_intencao_ai_primeiro(self, texto: str):
        runtime = self._ns().get("_interpretacao_intencao_runtime")
        return runtime.tentar_ai_primeiro(texto) if runtime is not None else None

    def _montar_contexto_resolucao(self) -> Dict[str, Any]:
        """Monta uma única visão da mente para qualquer forma de comando.

        O nome histórico ``processar_deterministico`` ficou estreito demais:
        esse contexto já reúne detector literal, continuidade, referências e
        interpretação natural pela IA. Mantê-lo em um só lugar evita que a
        barreira prioritária e o fluxo normal decidam com estados diferentes.
        """
        ns = self._ns()
        contexto_execucao = self.contexto_intencao_runtime.montar()
        pendencia_runtime = contexto_execucao.get("_pendencia_acao_runtime")
        try:
            pendencia_atual = dict(pendencia_runtime.obter() or {}) if pendencia_runtime is not None else {}
        except Exception:
            pendencia_atual = {}
        pendencia_agenda = (
            pendencia_atual if str(pendencia_atual.get("origem") or "") == "agenda" else {}
        )
        return {
            "normalizar_texto": ns.get("_normalizar_texto_com_apelidos"),
            "texto_depende_de_contexto": ns.get("_texto_depende_de_contexto"),
            "texto_parece_consulta_operacional": ns.get("_texto_parece_consulta_operacional"),
            "refinar_contexto_mental": ns.get("_refinar_contexto_mental"),
            "texto_cancela_acao_agora": ns.get("_texto_cancela_acao_agora"),
            "resolver_comando_midia_contextual_forcado": ns.get("_resolver_comando_midia_contextual_forcado"),
            "resolver_comando_contextual_forcado": ns.get("_resolver_comando_contextual_forcado"),
            "resolver_comando_acao_geral_contextual_forcado": ns.get("_resolver_comando_acao_geral_contextual_forcado"),
            "resolver_repeticao_ultima_acao": ns.get("_resolver_repeticao_ultima_acao"),
            "tentar_intencao_ai_primeiro": self.tentar_intencao_ai_primeiro,
            "detectar_intencao_deterministica": ns.get("detectar_intencao_deterministica"),
            "limpar_nome_playlist": ns.get("_limpar_nome_playlist"),
            "musica_estado_get": contexto_execucao.get("_musica_estado_get"),
            "extrair_agendamento": ns.get("_extrair_agendamento_local"),
            "extrair_acao_agendada": ns.get("_extrair_acao_agendada_local"),
            "executar_intencao": self.executar_intencao,
            "registrar_resultado_execucao": ns.get("_registrar_resultado_execucao"),
            "registrar_autoaprimoramento": ns.get("_registrar_autoaprimoramento"),
            "turno_atual": dict(contexto_execucao.get("turno_atual") or {}),
            "retrato_turno_atual": dict(contexto_execucao.get("retrato_turno_atual") or {}),
            "continuidade_geral": dict(
                contexto_execucao.get("continuidade_geral") or {}
            ),
            "registrar_arbitragem_turno": contexto_execucao.get("registrar_arbitragem_turno"),
            "pendencia_agenda": pendencia_agenda,
            "pendencia_acao": pendencia_atual,
            "pendencia_acao_runtime": pendencia_runtime,
            "lembrete_pendente": (
                str(contexto_execucao.get("ultima_intencao") or "").upper() == "AGENDAR_LEMBRETE"
                and str(contexto_execucao.get("ultima_habilidade") or "").casefold() == "agenda"
                and bool(str(contexto_execucao.get("ultimo_alvo") or "").strip())
            ) or bool(pendencia_agenda),
        }

    @staticmethod
    def _copiar_resolucao(
        resolucao: Tuple[Dict[str, Any] | None, str],
    ) -> Tuple[Dict[str, Any] | None, str]:
        resultado, rota = resolucao
        return (deepcopy(resultado) if isinstance(resultado, dict) else None, str(rota or ""))

    @staticmethod
    def _moldura_linguagem_natural(texto: str) -> str:
        t = re.sub(r"\s+", " ", str(texto or "").casefold()).strip()
        if re.fullmatch(
            r"(?:sim|nao|não|pode|isso|essa|esse|ela|ele|essa tambem|essa também|"
            r"tenta de novo|de novo)",
            t,
        ):
            return "continuacao"
        if "?" in str(texto or "") or re.match(
            r"^(?:o que|qual|quais|quantos|quantas|como|tem|ha|há|me fala|me fale)\b",
            t,
        ):
            return "pergunta"
        if re.match(
            r"^(?:abre|fecha|coloca|toca|pausa|passa|liga|desliga|cria|apaga|"
            r"remove|pesquisa|busca|procura|organiza|salva|guarda|lista|mostra|"
            r"escreve|grava|lembra|cancela)\b",
            t,
        ):
            return "pedido_direto"
        return "fala_natural"

    def _chave_decisao_turno(
        self, texto: str, contexto: Dict[str, Any],
    ) -> tuple[str, str] | None:
        turno = dict(contexto.get("turno_atual") or {})
        turno_id = str(turno.get("id") or "").strip()
        if not turno_id:
            # Sem uma identidade de turno não existe limite seguro para o
            # cache. Clientes antigos continuam reavaliando como antes.
            return None
        normalizar = contexto.get("normalizar_texto")
        try:
            texto_normalizado = (
                normalizar(texto) if callable(normalizar) else str(texto or "").casefold()
            )
        except Exception:
            texto_normalizado = str(texto or "").casefold()
        texto_normalizado = re.sub(r"\s+", " ", str(texto_normalizado or "")).strip()
        return turno_id, texto_normalizado

    def _resolver_decisao_canonica(
        self,
        texto: str,
        origem: str,
        contexto: Dict[str, Any] | None = None,
    ) -> Tuple[Dict[str, Any] | None, str]:
        contexto_resolucao = contexto or self._montar_contexto_resolucao()
        chave = self._chave_decisao_turno(texto, contexto_resolucao)
        with self._lock_linguagem_natural:
            if chave is not None:
                turno_id = chave[0]
                if turno_id != self._cache_turno_id:
                    self._cache_decisao_turno.clear()
                    self._cache_turno_id = turno_id
                if chave in self._cache_decisao_turno:
                    self._metricas_linguagem_natural["reutilizadas_no_turno"] = (
                        int(self._metricas_linguagem_natural.get("reutilizadas_no_turno") or 0)
                        + 1
                    )
                    return self._copiar_resolucao(self._cache_decisao_turno[chave])

            resolucao = resolver_intencao(texto, origem, contexto_resolucao)
            resultado, rota = resolucao
            intent = _normalizar_intent(resultado)
            metricas = self._metricas_linguagem_natural
            metricas["tentativas"] = int(metricas.get("tentativas") or 0) + 1
            chave_rota = str(rota or "sem_intencao")
            rotas = dict(metricas.get("rotas") or {})
            rotas[chave_rota] = int(rotas.get(chave_rota) or 0) + 1
            metricas["rotas"] = rotas
            moldura = self._moldura_linguagem_natural(texto)
            por_moldura = dict(metricas.get("por_moldura") or {})
            por_moldura[moldura] = int(por_moldura.get(moldura) or 0) + 1
            metricas["por_moldura"] = por_moldura
            if intent:
                metricas["resolvidas"] = int(metricas.get("resolvidas") or 0) + 1
                metricas["ultima_rota"] = str(rota or "coordenador")
                metricas["ultima_intent"] = intent
                habilidade = classificar_habilidade_intent(intent) or "outros"
                pendencia_acao = dict(
                    contexto_resolucao.get("pendencia_acao")
                    or contexto_resolucao.get("pendencia_agenda")
                    or {}
                )
                pendencia_runtime = contexto_resolucao.get("pendencia_acao_runtime")
                dominio_atual = dominio_pendencia(pendencia_acao)
                dominio_novo = normalizar_dominio_continuidade(intent=intent)
                if (
                    pendencia_acao
                    and dominio_atual
                    and dominio_novo != dominio_atual
                    and pendencia_runtime is not None
                ):
                    try:
                        pendencia_runtime.concluir(
                            str(pendencia_acao.get("id") or ""),
                            "substituida_por_troca_dominio",
                        )
                    except Exception:
                        pass
                por_habilidade = dict(metricas.get("por_habilidade") or {})
                por_habilidade[habilidade] = int(por_habilidade.get(habilidade) or 0) + 1
                metricas["por_habilidade"] = por_habilidade
                metricas["ultima_classificacao"] = f"resolvida:{habilidade}:{moldura}"
            else:
                metricas["sem_intencao"] = int(metricas.get("sem_intencao") or 0) + 1
                parece_operacional = bool(_call(
                    contexto_resolucao,
                    "texto_parece_consulta_operacional",
                    texto,
                    default=False,
                ))
                chave_classificacao = (
                    "comandos_nao_reconhecidos" if parece_operacional
                    else "conversas_legitimas"
                )
                metricas[chave_classificacao] = int(metricas.get(chave_classificacao) or 0) + 1
                metricas["ultima_classificacao"] = (
                    "comando_nao_reconhecido" if parece_operacional
                    else "conversa_legitima"
                ) + f":{moldura}"
                motivo = (
                    "nenhuma_habilidade_atingiu_confianca"
                    if parece_operacional else "fala_classificada_como_conversa"
                )
                metricas["ultima_nao_resolvida"] = {
                    "motivo": motivo,
                    "moldura": moldura,
                    "rota": chave_rota,
                    "parecia_operacional": parece_operacional,
                }
                if callable(self.registrar_decisao_cb):
                    try:
                        self.registrar_decisao_cb(
                            "linguagem_natural",
                            "nao_resolvida",
                            (motivo, f"moldura_{moldura}", f"rota_{chave_rota}"),
                            categoria="operacional" if parece_operacional else "conversa",
                        )
                    except Exception:
                        pass
            if chave is not None:
                self._cache_decisao_turno[chave] = self._copiar_resolucao(resolucao)
            return self._copiar_resolucao(resolucao)

    def decisao_ja_avaliada(self, texto: str) -> bool:
        """Informa se o coordenador já classificou este texto no turno atual."""
        contexto = self._montar_contexto_resolucao()
        chave = self._chave_decisao_turno(texto, contexto)
        if chave is None:
            return False
        with self._lock_linguagem_natural:
            if chave[0] != self._cache_turno_id:
                return False
            return chave in self._cache_decisao_turno

    def resolver_comando_natural(
        self, texto: str, origem: str = "",
    ) -> Tuple[Dict[str, Any] | None, str]:
        """Resolve linguagem natural sem executar nem produzir fala.

        A decisão passa pelo mesmo árbitro usado pelo fluxo operacional. Assim,
        perguntas sobre capacidade, hipóteses e negações continuam bloqueadas,
        enquanto pedidos naturais podem escolher qualquer intent registrado.
        """
        return self._resolver_decisao_canonica(texto, origem)

    def diagnostico_linguagem_natural(self) -> Dict[str, Any]:
        with self._lock_linguagem_natural:
            metricas = dict(self._metricas_linguagem_natural)
            metricas["rotas"] = dict(metricas.get("rotas") or {})
            metricas["por_habilidade"] = dict(metricas.get("por_habilidade") or {})
            metricas["por_moldura"] = dict(metricas.get("por_moldura") or {})
        metricas.update(
            modo="coordenador_canonico",
            usa_contexto=True,
            usa_memoria=True,
            usa_catalogo_habilidades=True,
            autoriza_execucao=False,
        )
        with self._lock_execucao_turno:
            metricas["execucao_turno"] = {
                **dict(self._metricas_execucao_turno),
                "ativas": sum(
                    1 for registro in self._execucoes_turno.values()
                    if str(registro.get("status") or "") == "em_andamento"
                ),
            }
        return metricas

    def processar_deterministico(self, texto: str, origem: str = "", texto_original: str = "") -> bool:
        contexto = self._montar_contexto_resolucao()
        return executar_fluxo_intencao(
            texto,
            origem,
            contexto,
            texto_original=texto_original,
            resolver_cb=self._resolver_decisao_canonica,
        )

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
        ns = self._ns()
        normalizar = ns.get("_normalizar_texto_com_apelidos")

        def executar_trecho_isolado(trecho: str, origem_trecho: str) -> bool:
            """Resolve cada etapa contra seu texto, preservando o estado vivo.

            O turno compartilhado descreve a frase composta inteira. Reutilizar
            seu ``texto_operacional`` ao resolver uma etapa isolada pode fazer
            a primeira ordem herdar a segunda (por exemplo, a busca herdar
            ``abre o primeiro resultado``). O contexto continua sendo o mesmo,
            mas a moldura operacional passa a representar somente a etapa.
            """
            contexto = self._montar_contexto_resolucao()
            self.log(
                "🧩 [COOPERAÇÃO:CADEIA] resolvendo etapa isolada | "
                f"origem={origem_trecho} trecho={str(trecho or '')[:120]}"
            )
            # P0_CADEIA_CONTEXTO_VIVO_V2_20260815
            # Cada etapa precisa de uma moldura de decisão própria. O texto
            # composto já foi validado pelo segmentador, mas especialistas e
            # referências do retrato pertencem à frase inteira e podem ficar
            # obsoletos depois que uma etapa anterior muda o estado.
            turno = dict(contexto.get("turno_atual") or {})
            autoridade_pai = bool(turno.get("autoriza_execucao"))
            turno["especialistas"] = {}
            turno.update({
                "texto": str(trecho or "").strip(),
                "texto_operacional": str(trecho or "").strip(),
                "texto_conversacional": "",
                "modalidade": "comando",
                "modalidade_geral": "comando",
                "ato_principal": "comando",
                "acao_explicita": True,
                "autoriza_execucao": autoridade_pai,
                "requer_esclarecimento": False,
            })
            contexto["turno_atual"] = turno

            # O resolvedor determinístico/contextual continua consultando a
            # mente viva. Removemos somente as restrições referenciais
            # congeladas no início do turno composto.
            retrato = dict(contexto.get("retrato_turno_atual") or {})
            retrato["referencia_resolvida"] = {}
            retrato["referencia_tipo"] = ""
            retrato["intents_permitidos"] = []
            retrato["operacao_explicita"] = ""
            retrato["entidade_explicita"] = {}
            contexto["retrato_turno_atual"] = retrato

            return executar_fluxo_intencao(
                trecho,
                origem_trecho,
                contexto,
                resolver_cb=self._resolver_decisao_canonica,
            )

        def relatar_falha(trecho: str, indice: int, concluidas: int) -> None:
            self.log(
                "⚠️ [COOPERAÇÃO:CADEIA] etapa não executada | "
                f"indice={indice} concluidas={concluidas} trecho={trecho[:120]}"
            )
            # A fala pertence ao contexto de execução tipado, não à
            # allowlist enxuta do resolvedor. Consultá-la daqui evita que uma
            # falha consumida deixe o turno sem resposta.
            try:
                contexto_fala = self.contexto_intencao_runtime.montar()
            except Exception:
                contexto_fala = {}
            falar = (
                contexto_fala.get("falar_com_lipsync")
                if isinstance(contexto_fala, dict)
                else None
            )
            if not callable(falar):
                return
            if concluidas:
                fala = (
                    f"Concluí {concluidas} etapa(s), mas não consegui executar "
                    f"a etapa {indice}. Parei ali para não fingir que o pedido "
                    "inteiro deu certo."
                )
            else:
                fala = (
                    f"Não consegui executar a etapa {indice}, então não avancei "
                    "para as próximas sem a dependência certa."
                )
            falar(fala, "calma", 1)

        return processar_comandos_em_cadeia(
            texto,
            origem,
            normalizar_texto=normalizar,
            executar_trecho=executar_trecho_isolado,
            relatar_falha=relatar_falha,
        )


def criar_ciclo_comandos_runtime(**kwargs: Any) -> CicloComandosRuntime:
    return CicloComandosRuntime(**kwargs)
