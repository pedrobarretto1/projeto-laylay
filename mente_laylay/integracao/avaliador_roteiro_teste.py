# -*- coding: utf-8 -*-
"""Avaliador determinístico do roteiro conversacional da Laylay."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re
import unicodedata
from typing import Any, Mapping, Sequence

VERSAO_AVALIADOR = 16
LIMITE_ALERTA_LATENCIA_S = 15.0

DOMINIOS_EXTERNOS = frozenset({"browser", "musica", "iot", "visao", "clima"})

PADROES_FALLBACK_CONVERSACIONAL = (
    re.compile(
        r"\besse assunto sobre .{1,100} parece interessante, mas eu ainda "
        r"nao tenho informacao verificada\b",
    ),
    re.compile(
        r"\bainda nao tenho dados suficientes para responder com confianca "
        r"sem inventar informacoes\b",
    ),
)

INTENTS_MUTACAO = frozenset({
    "CREATE_FILE", "CREATE_FOLDER", "DELETE_ITEM", "CONFIRM_DELETE_ITEM",
    "RESTORE_DELETED_ITEM", "MOVE_ITEM", "FILE_TRANSACTION", "CLOSE_APP",
    "APP_OPEN", "MAXIMIZE_WINDOW", "ORGANIZAR_DESKTOP", "OPEN_URL",
    "CLOSE_TAB", "SWITCH_PREVIOUS_TAB", "MEDIA_CONTROL", "PLAYLIST_ADD",
    "PLAYLIST_DELETE", "PLAYLIST_MOVE", "PLAYLIST_CREATE", "PLAYLIST_PLAY",
    "IOT_CONTROL", "AGENDAR_LEMBRETE", "CANCELAR_AGENDAMENTO",
})

DOMINIO_POR_INTENT = {
    "CREATE_FILE": "arquivos", "CREATE_FOLDER": "arquivos",
    "DELETE_ITEM": "arquivos", "CONFIRM_DELETE_ITEM": "arquivos",
    "CANCEL_DELETE_ITEM": "arquivos", "RESTORE_DELETED_ITEM": "arquivos",
    "MOVE_ITEM": "arquivos", "FILE_TRANSACTION": "arquivos",
    "FILE_READ": "arquivos", "FILE_SEARCH": "arquivos",
    "FILE_OPEN_RESULT": "arquivos",
    "APP_OPEN": "apps", "CLOSE_APP": "apps", "MAXIMIZE_WINDOW": "apps",
    "ORGANIZAR_DESKTOP": "apps", "LIST_WINDOWS": "apps",
    "OPEN_URL": "browser", "CLOSE_TAB": "browser", "LIST_TABS": "browser",
    "SWITCH_PREVIOUS_TAB": "browser", "SEARCH": "browser",
    "RESUMIR_PAGINA": "browser", "PAGE_FIND": "browser",
    "MEDIA_CONTROL": "musica", "MUSIC_STATUS": "musica",
    "PLAYLIST_ADD": "musica", "PLAYLIST_DELETE": "musica",
    "PLAYLIST_MOVE": "musica", "PLAYLIST_CREATE": "musica",
    "PLAYLIST_PLAY": "musica", "PLAYLIST_LIST": "musica",
    "IOT_CONTROL": "iot", "IOT_STATUS": "iot",
    "WEATHER": "clima", "BRIEFING_REPEAT": "clima",
    "SCREEN_CAPTURE": "visao", "VISION_QUERY": "visao",
    "AGENDAR_LEMBRETE": "agenda", "LISTAR_AGENDAMENTOS": "agenda",
    "CANCELAR_AGENDAMENTO": "agenda",
}

EXPECTATIVAS_CRITICAS = {
    "o opera continua aberto?": {
        "intents_any": ("LIST_WINDOWS",),
        "intents_forbidden": ("APP_OPEN",),
        "statuses_any": ("estado_app_consultado",),
        "confirmado": True,
        "fala_any": ("aberto", "fechado"),
        "dominio": "apps",
        "nome": "consulta_app_read_only",
    },
    "essa tambem.": {
        "intents_any": ("PLAYLIST_ADD",),
        "statuses_any": ("playlist_musica_adicionada", "playlist_musica_ja_existia"),
        "confirmado": True,
        "dominio": "musica",
        "nome": "continuidade_playlist_aditiva",
    },
    "tenta de novo.": {
        "intents_any": ("PLAYLIST_ADD",),
        "statuses_any": ("playlist_musica_adicionada", "playlist_musica_ja_existia"),
        "confirmado": True,
        "dominio": "musica",
        "nome": "retry_playlist_aditiva",
    },
    "guarda essa ideia e me lembra dela amanha as 15 e 20.": {
        "intents_any": ("AGENDAR_LEMBRETE",),
        "statuses_any": ("lembrete_agendado", "lembrete_ja_agendado"),
        "confirmado": True,
        "dominio": "agenda",
        "nome": "lembrete_ideia_idempotente",
    },
}

# Alguns textos do roteiro dependem da posição para ter um contrato inequívoco:
# ``continua`` muda com o contexto musical, os resumos curtos dependem da página
# já aberta e a próxima faixa composta preserva duas etapas. O índice é
# zero-based, como no checkpoint do roteiro.
EXPECTATIVAS_CRITICAS_POR_TURNO = {
    (21, "continua"): {
        "sem_comando": True,
        "dominio": "seguranca",
        "nome": "continua_ambigua_sem_contexto",
    },
    (
        99,
        "pausa a musica... esquece, continua tocando.",
    ): {
        "intents_any": ("MEDIA_CONTROL",),
        "statuses_any": ("midia_play",),
        "aceita_confirmacao_indeterminada": True,
        "intents_confirmacao_indeterminada": ("MEDIA_CONTROL",),
        "statuses_confirmacao_indeterminada": ("midia_play",),
        "dominio": "musica",
        "nome": "autocorrecao_midia_envio_honesto",
    },
    (
        95,
        "fecha a microsoft store... quer dizer, maximiza ela.",
    ): {
        "intents_any": ("MAXIMIZE_WINDOW",),
        "statuses_any": ("janela_maximizada",),
        "confirmado": True,
        "dominio": "apps",
        "nome": "autocorrecao_maximiza_microsoft_store",
    },
    (111, "maximiza ele."): {
        "intents_any": ("MAXIMIZE_WINDOW",),
        "statuses_any": ("janela_maximizada",),
        "confirmado": True,
        "dominio": "apps",
        "nome": "maximiza_store_contextual_confirmada",
    },
    (116, "qual aba ficou aberta?"): {
        "intents_any": ("LIST_TABS",),
        "statuses_any": ("aba_sobrevivente_consultada",),
        "confirmado": True,
        "fala_any": ("prime video",),
        "dominio": "browser",
        "nome": "aba_sobrevivente_apos_fechamento_ordinal",
    },
    (122, "resume isso."): {
        "intents_any": ("RESUMIR_PAGINA",),
        "statuses_any": ("resumo_concluido",),
        "confirmado": True,
        "dominio": "browser",
        "nome": "resumo_contextual_da_pagina_aberta",
    },
    (125, "resume agora."): {
        "intents_any": ("RESUMIR_PAGINA",),
        "statuses_any": ("resumo_concluido",),
        "confirmado": True,
        "dominio": "browser",
        "nome": "resumo_da_pagina_atual_apos_navegacao",
    },
    (
        128,
        "se a microsoft store nao estiver aberta, abre; se ja estiver, "
        "so me avisa.",
    ): {
        "intents_any": ("APP_OPEN",),
        "statuses_any": (
            "app_ja_aberto_observado", "app_iniciado_focado",
        ),
        "confirmado": True,
        "fala_any": ("abert",),
        "dominio": "apps",
        "nome": "abertura_condicional_store_observavel",
    },
    (
        147,
        "adiciona essa musica na playlist caos sonora e depois me mostra "
        "o que tem nela.",
    ): {
        "intents_all": ("PLAYLIST_ADD", "PLAYLIST_LIST"),
        "statuses_all": (
            "playlist_musica_adicionada", "playlists_listadas",
        ),
        "confirmado": True,
        "dominio": "musica",
        "nome": "adicionar_e_listar_playlist_na_mesma_cadeia",
    },
    (
        148,
        "vai para a proxima faixa e adiciona essa tambem na caos sonora.",
    ): {
        "intents_all": ("MEDIA_CONTROL", "PLAYLIST_ADD"),
        "intents_forbidden": ("CREATE_FILE",),
        "aceita_confirmacao_indeterminada": True,
        "intents_confirmacao_indeterminada": ("MEDIA_CONTROL",),
        "statuses_confirmacao_indeterminada": (
            "midia_next", "midia_next_playlist",
        ),
        "dominio": "musica",
        "nome": "proxima_faixa_e_adicao_playlist",
    },
    (170, "continua"): {
        "intents_any": ("MEDIA_CONTROL",),
        "statuses_any": ("midia_play",),
        "aceita_confirmacao_indeterminada": True,
        "dominio": "musica",
        "nome": "continua_em_contexto_musical",
    },
    (
        226,
        "eu quero que voce abra a microsoft store, coloque ela na direita, "
        "confira se ficou aberta e so entao me diga o resultado",
    ): {
        "intents_all": ("APP_OPEN", "ORGANIZAR_DESKTOP", "LIST_WINDOWS"),
        "statuses_all": ("layout_confirmado", "estado_app_consultado"),
        "confirmado": True,
        "fala_any": ("abert",),
        "dominio": "apps",
        "nome": "abrir_posicionar_e_confirmar_microsoft_store",
    },
}


def _sem_acentos(texto: Any) -> str:
    bruto = str(texto or "").casefold()
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", bruto)
        if not unicodedata.combining(ch)
    )


def _norm(texto: Any) -> str:
    return re.sub(r"\s+", " ", _sem_acentos(texto)).strip()


def _comandos(plano: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    retrato = dict(plano or {})
    return [
        dict(item) for item in retrato.get("comandos") or []
        if isinstance(item, Mapping)
    ]


_CAMPO_AUSENTE = object()


def _campo_por_caminho(
    retrato: Mapping[str, Any],
    caminho: str,
) -> Any:
    atual: Any = retrato
    for parte in str(caminho or "").split("."):
        if not parte or not isinstance(atual, Mapping) or parte not in atual:
            return _CAMPO_AUSENTE
        atual = atual[parte]
    return atual


def _campo_presente(valor: Any) -> bool:
    return bool(
        valor is not _CAMPO_AUSENTE
        and valor is not None
        and (not isinstance(valor, str) or bool(valor.strip()))
    )


def _expectativa_automatica(
    comando: str,
    *,
    indice: int | None = None,
) -> dict[str, Any]:
    t = _norm(comando)
    expectativa_turno = EXPECTATIVAS_CRITICAS_POR_TURNO.get((indice, t))
    if expectativa_turno:
        return dict(expectativa_turno)
    if t in EXPECTATIVAS_CRITICAS:
        return dict(EXPECTATIVAS_CRITICAS[t])

    if (
        re.match(r"^(?:como eu|talvez eu|eu talvez)\b", t)
        or re.match(
            r"^nao\s+(?:crie|cria|apague|apaga|abra|abre|feche|fecha|"
            r"ligue|liga|desligue|desliga|toque|toca)\b",
            t,
        )
        or re.match(r"^voce consegue\b", t)
    ):
        return {"sem_comando": True, "nome": "nao_autoriza_execucao", "dominio": "seguranca"}

    regras = [
        (r"\bcria (?:um )?arquivo\b", ("CREATE_FILE",), "arquivos"),
        (
            r"^(?:leia|le)\b(?:.*\b(?:conteudo|arquivo|dele|desse)\b|"
            r".*\.[a-z0-9][a-z0-9_-]{0,15}[.!?]*$)",
            ("FILE_READ",),
            "arquivos",
        ),
        (r"^acrescente\b", ("CREATE_FILE",), "arquivos"),
        (r"^onde\b.*\barquivo\b", ("FILE_SEARCH",), "arquivos"),
        (r"^abre\b.*\barquivo\b|^abre o auditoria\b", ("FILE_OPEN_RESULT",), "arquivos"),
        (r"^fecha (?:esse|o) arquivo\b", ("CLOSE_APP",), "arquivos"),
        (r"\bcria (?:uma )?pasta\b", ("CREATE_FOLDER",), "arquivos"),
        (r"^coloca o arquivo\b.*\bdentro\b", ("FILE_TRANSACTION",), "arquivos"),
        (r"^apaga\b.*\b(?:arquivo|pasta)\b", ("DELETE_ITEM",), "arquivos"),
        (r"^quero ele de volta[.!?]*$", ("RESTORE_DELETED_ITEM",), "arquivos"),
        (r"^maximiza\b", ("MAXIMIZE_WINDOW",), "apps"),
        (r"^coloca\b.*\b(?:esquerda|direita)\b", ("ORGANIZAR_DESKTOP",), "apps"),
        (r"^fecha (?:a )?(?:calculadora|opera)\b|^fecha (?:um )?programa\b", ("CLOSE_APP",), "apps"),
        (r"^abre (?:a )?(?:wikipedia|prime video)\b", ("OPEN_URL",), "browser"),
        (r"^quais abas\b", ("LIST_TABS",), "browser"),
        (r"^resume a pagina\b", ("RESUMIR_PAGINA",), "browser"),
        (r"^fecha essa aba\b", ("CLOSE_TAB",), "browser"),
        (r"^pesquisa por\b", ("SEARCH",), "browser"),
        (r"^volta para a aba anterior\b", ("SWITCH_PREVIOUS_TAB",), "browser"),
        (r"^encontra o arquivo\b", ("FILE_SEARCH",), "arquivos"),
        (r"^pausa a musica\b", ("MEDIA_CONTROL",), "musica"),
        (r"^vai para a proxima faixa\b|^volta para a faixa anterior\b", ("MEDIA_CONTROL",), "musica"),
        (r"^coloca essa musica na playlist\b", ("PLAYLIST_ADD",), "musica"),
        (r"^apaga a playlist\b", ("PLAYLIST_DELETE",), "musica"),
        (r"^liga\b.*\blampada\b|^deixa ela azul\b|^desliga ela\b", ("IOT_CONTROL",), "iot"),
        (r"^como ela esta\??$", ("IOT_STATUS",), "iot"),
        (r"\btempo amanha\b|\btemperatura maxima\b", ("WEATHER",), "clima"),
        (r"^olha minha tela\b", ("SCREEN_CAPTURE",), "visao"),
        (r"^o que tem na minha tela\b", ("SCREEN_CAPTURE", "VISION_QUERY"), "visao"),
        (r"^continua daquele ponto\b", ("VISION_QUERY",), "visao"),
        (r"^me lembra\b", ("AGENDAR_LEMBRETE",), "agenda"),
        (r"^quais lembretes\b", ("LISTAR_AGENDAMENTOS",), "agenda"),
        (r"^cancela o lembrete\b", ("CANCELAR_AGENDAMENTO",), "agenda"),
    ]
    for padrao, intents, dominio in regras:
        if re.search(padrao, t):
            return {"intents_any": intents, "nome": "expectativa_por_padrao", "dominio": dominio}
    return {}


def _dominio(comandos: Sequence[Mapping[str, Any]], expectativa: Mapping[str, Any]) -> str:
    if expectativa.get("dominio"):
        return str(expectativa["dominio"])
    dominios = [
        DOMINIO_POR_INTENT.get(str(item.get("intent") or "").upper(), "")
        for item in comandos
    ]
    dominios = [x for x in dominios if x]
    return Counter(dominios).most_common(1)[0][0] if dominios else "conversa"


def _contradicoes_fala(resposta: str, comandos: Sequence[Mapping[str, Any]]) -> list[str]:
    t = _norm(resposta)
    if not t:
        return ["fala_vazia"]
    problemas = []
    confirmou = any(x.get("confirmado") is True for x in comandos)
    noop = any(x.get("executou") is False and x.get("confirmado") is True for x in comandos)
    if confirmou and any(x in t for x in (
        "nao consegui confirmar", "nao foi possivel confirmar",
        "sem conseguir confirmar", "nao tenho como confirmar",
    )):
        problemas.append("fala_diz_incerteza_com_resultado_confirmado")
    if noop and re.search(r"\b(?:falhei|deu errado|nao funcionou)\b", t):
        problemas.append("fala_trata_noop_confirmado_como_falha")
    statuses = {str(x.get("status") or "").casefold() for x in comandos}
    if "lembrete_ja_agendado" in statuses and not ("ja" in t and ("agend" in t or "marcad" in t)):
        problemas.append("fala_nao_explica_lembrete_ja_agendado")
    if "playlist_musica_ja_existia" in statuses and "ja" not in t:
        problemas.append("fala_nao_explica_faixa_ja_existente")
    if "estado_app_consultado" in statuses and not ("abert" in t or "fechad" in t):
        problemas.append("fala_nao_expressa_estado_do_app")
    return problemas


def _fala_e_fallback_conversacional(resposta: str) -> bool:
    texto = _norm(resposta)
    return any(padrao.search(texto) for padrao in PADROES_FALLBACK_CONVERSACIONAL)


def avaliar_turno_roteiro(
    *,
    indice: int,
    comando: str,
    resposta: str,
    plano: Mapping[str, Any] | None,
    respondeu: bool,
    motivo_resultado: str = "",
    enviado_em: float | None = None,
    finalizado_em: float | None = None,
    avaliacao_mecanica: Mapping[str, Any] | None = None,
    expectativa_local: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    base = dict(avaliacao_mecanica or {})
    retrato = dict(plano or {})
    comandos = _comandos(retrato)
    intents = [str(x.get("intent") or "").upper() for x in comandos]
    statuses = [str(x.get("status") or "") for x in comandos]
    origem_expectativa = (
        "roteiro_dedicado"
        if expectativa_local is not None
        else "avaliador_global"
    )
    expectativa = (
        dict(expectativa_local)
        if expectativa_local is not None
        else _expectativa_automatica(comando, indice=indice)
    )
    if not expectativa:
        origem_expectativa = "nenhuma"
    erros, alertas, checagens = [], [], []

    if not respondeu or not str(resposta or "").strip():
        erros.append("sem_resposta")
    if not retrato:
        alertas.append("plano_ausente")
    if retrato.get("erros"):
        erros.append("plano_publicou_erros")
    sem_execucao_esperada = bool(
        expectativa.get("sem_comando")
        and not comandos
    )
    if (
        motivo_resultado
        in {"execucao_nao_publicada", "contrato_operacional_incompleto"}
        and not (
            motivo_resultado == "execucao_nao_publicada"
            and sem_execucao_esperada
        )
    ):
        erros.append(motivo_resultado)

    semantica_avaliada = bool(expectativa)
    if _fala_e_fallback_conversacional(resposta):
        # Fallback repetitivo é um resultado semântico observável por si só;
        # não pode desaparecer na categoria "não avaliado" só porque o turno
        # não possuía expectativa operacional.
        semantica_avaliada = True
        erros.append("fallback_conversacional_generico")
        checagens.append("fallback_conversacional")
    if expectativa.get("sem_comando"):
        checagens.append("sem_comando_operacional")
        if comandos:
            erros.append("comando_inesperado_em_fala_nao_autorizadora")

    esperadas = {str(x).upper() for x in expectativa.get("intents_any") or ()}
    if esperadas:
        checagens.append("intent_esperada")
        if not esperadas.intersection(intents):
            erros.append("intent_incorreta:esperado=" + "|".join(sorted(esperadas))
                          + ";observado=" + "|".join(intents or ["SEM_INTENT"]))

    obrigatorias = {
        str(x).upper() for x in expectativa.get("intents_all") or ()
    }
    if obrigatorias:
        checagens.append("intents_obrigatorias")
        for ausente in sorted(obrigatorias.difference(intents)):
            erros.append(f"intent_ausente:{ausente}")

    proibidas = {str(x).upper() for x in expectativa.get("intents_forbidden") or ()}
    violacoes = [x for x in intents if x in proibidas]
    if violacoes:
        erros.append("intent_proibida:" + "|".join(violacoes))

    status_esperados = {str(x).casefold() for x in expectativa.get("statuses_any") or ()}
    if status_esperados:
        checagens.append("status_esperado")
        if not status_esperados.intersection(str(x).casefold() for x in statuses):
            erros.append("status_incorreto:esperado=" + "|".join(sorted(status_esperados))
                          + ";observado=" + "|".join(statuses or ["SEM_STATUS"]))

    status_obrigatorios = {
        str(x).casefold() for x in expectativa.get("statuses_all") or ()
    }
    if status_obrigatorios:
        checagens.append("statuses_obrigatorios")
        observados = {str(x).casefold() for x in statuses}
        for ausente in sorted(status_obrigatorios.difference(observados)):
            erros.append(f"status_ausente:{ausente}")

    if "confirmado" in expectativa and comandos:
        checagens.append("confirmacao_esperada")
        esperado = expectativa.get("confirmado")
        if not any(x.get("confirmado") is esperado for x in comandos):
            erros.append(f"confirmacao_incorreta:esperado={esperado!r}")

    fala_any = tuple(_norm(x) for x in expectativa.get("fala_any") or ())
    if fala_any:
        checagens.append("fala_minima")
        t_resp = _norm(resposta)
        if not any(x in t_resp for x in fala_any):
            erros.append("fala_nao_contem_evidencia_esperada")

    campos_plano = expectativa.get("campos_plano") or {}
    campos_presentes = tuple(
        str(x) for x in expectativa.get("campos_plano_presentes") or ()
    )
    campos_ausentes = tuple(
        str(x) for x in expectativa.get("campos_plano_ausentes") or ()
    )
    if campos_plano or campos_presentes or campos_ausentes:
        checagens.append("campos_plano")
    if isinstance(campos_plano, Mapping):
        for caminho, esperado in campos_plano.items():
            caminho_textual = str(caminho or "").strip()
            observado = _campo_por_caminho(retrato, caminho_textual)
            if observado is _CAMPO_AUSENTE or observado != esperado:
                observado_texto = (
                    "AUSENTE"
                    if observado is _CAMPO_AUSENTE
                    else repr(observado)[:160]
                )
                erros.append(
                    f"campo_plano_incorreto:{caminho_textual}:"
                    f"esperado={esperado!r};observado={observado_texto}"
                )
    else:
        erros.append("campos_plano_invalido")
    for caminho in campos_presentes:
        if not _campo_presente(_campo_por_caminho(retrato, caminho)):
            erros.append(f"campo_plano_ausente:{caminho}")
    for caminho in campos_ausentes:
        if _campo_presente(_campo_por_caminho(retrato, caminho)):
            erros.append(f"campo_plano_inesperado:{caminho}")

    contradicoes = _contradicoes_fala(resposta, comandos)
    if contradicoes:
        erros.extend(contradicoes)
        checagens.append("coerencia_fala_contrato")

    mutacoes = [x for x in intents if x in INTENTS_MUTACAO]
    t = _norm(comando)
    if (
        re.match(r"^(?:como eu|talvez eu|eu talvez|voce consegue)\b", t)
        or re.match(r"^nao\s+\w+", t)
    ) and mutacoes:
        semantica_avaliada = True
        erros.append("efeito_colateral_em_fala_nao_autorizadora:" + "|".join(mutacoes))

    dominio = _dominio(comandos, expectativa)
    comandos_indeterminados = [
        x for x in comandos if x.get("confirmado") is None
    ]
    confirm_none = len(comandos_indeterminados)
    intents_indeterminadas = {
        str(x).upper()
        for x in expectativa.get("intents_confirmacao_indeterminada")
        or esperadas
    }
    statuses_indeterminados = {
        str(x).casefold()
        for x in expectativa.get("statuses_confirmacao_indeterminada")
        or status_esperados
    }
    indeterminacao_midia_com_evidencia = bool(
        comandos_indeterminados
        and all(
            item.get("executou") is True
            and str(item.get("intent") or "").upper() == "MEDIA_CONTROL"
            and str(
                item.get("confirmacao_oferecida") or ""
            ).casefold() == "variavel"
            and bool(str(item.get("evidencia_confirmacao") or "").strip())
            for item in comandos_indeterminados
        )
    )
    indeterminacao_aceita_por_expectativa = bool(
        expectativa.get("aceita_confirmacao_indeterminada")
        and comandos_indeterminados
        and intents_indeterminadas
        and statuses_indeterminados
        and all(
            item.get("executou") is True
            and str(item.get("intent") or "").upper()
            in intents_indeterminadas
            and str(item.get("status") or "").casefold()
            in statuses_indeterminados
            and str(
                item.get("confirmacao_oferecida") or ""
            ).casefold() == "variavel"
            and bool(str(item.get("evidencia_confirmacao") or "").strip())
            for item in comandos_indeterminados
        )
    )
    indeterminacao_aceita = (
        indeterminacao_midia_com_evidencia
        or indeterminacao_aceita_por_expectativa
    )
    if indeterminacao_aceita:
        checagens.append("envio_sem_observacao_externa_esperado")
    elif confirm_none:
        alertas.append(f"etapas_sem_confirmacao_externa:{confirm_none}")

    duracao = None
    if isinstance(enviado_em, (int, float)) and isinstance(finalizado_em, (int, float)):
        duracao = max(0.0, float(finalizado_em) - float(enviado_em))
        if duracao >= LIMITE_ALERTA_LATENCIA_S:
            alertas.append(f"latencia_alta:{duracao:.2f}s")

    if dominio in DOMINIOS_EXTERNOS and comandos:
        if any(x.get("executou") is False and x.get("confirmado") is False for x in comandos):
            if not status_esperados and "confirmado" not in expectativa:
                alertas.append("dependencia_externa_nao_confirmada")

    if erros:
        resultado = "falhou"
    elif semantica_avaliada:
        resultado = "alerta" if alertas else "passou"
    else:
        resultado = "nao_avaliado"

    intencao_correta = (
        "nao" if any(x.startswith(("intent_", "comando_inesperado", "efeito_colateral")) for x in erros)
        else ("sim" if semantica_avaliada else "nao_avaliado")
    )
    fala_coerente = (
        "nao" if any(x.startswith("fala_") for x in erros)
        else ("sim" if respondeu and comandos else "nao_avaliado")
    )

    base.update({
        "versao_avaliador": VERSAO_AVALIADOR,
        "resultado_semantico": resultado,
        "semantica_avaliada": semantica_avaliada,
        "expectativa": str(expectativa.get("nome") or ""),
        "origem_expectativa": origem_expectativa,
        "dominio": dominio,
        "intents_observadas": intents,
        "statuses_observados": statuses,
        "intencao_correta": intencao_correta,
        "fala_coerente": fala_coerente,
        "criterio_fala": "contrato_operacional_deterministico",
        "erros_semanticos": erros,
        "alertas_semanticos": alertas,
        "checagens_semanticas": checagens,
        "confirmacoes_indeterminadas": confirm_none,
        "duracao_s": round(duracao, 3) if duracao is not None else None,
    })
    return base


def _percentil(valores: Sequence[float], q: float) -> float | None:
    dados = sorted(float(x) for x in valores)
    if not dados:
        return None
    if len(dados) == 1:
        return dados[0]
    pos = (len(dados) - 1) * q
    baixo, alto = math.floor(pos), math.ceil(pos)
    if baixo == alto:
        return dados[baixo]
    peso = pos - baixo
    return dados[baixo] * (1 - peso) + dados[alto] * peso


def resumir_estado_roteiro(estado: Mapping[str, Any]) -> dict[str, Any]:
    itens = [dict(x) for x in estado.get("itens") or [] if isinstance(x, Mapping)]
    resultados = Counter()
    dominios = defaultdict(Counter)
    duracoes = []
    confirm_none = 0
    comandos_total = 0
    fallbacks_conversacionais = 0
    erros_turnos, alertas_turnos = [], []
    frequencia_falas = Counter(
        _norm(item.get("resposta"))
        for item in itens
        if _norm(item.get("resposta"))
    )

    for item in itens:
        av = dict(item.get("avaliacao") or {})
        resultado = str(av.get("resultado_semantico") or "nao_avaliado")
        resultados[resultado] += 1
        dominio = str(av.get("dominio") or "nao_classificado")
        dominios[dominio][resultado] += 1
        if isinstance(av.get("duracao_s"), (int, float)):
            duracoes.append(float(av["duracao_s"]))
        confirm_none += int(av.get("confirmacoes_indeterminadas") or 0)
        comandos_total += int(av.get("quantidade_comandos") or 0)
        if av.get("erros_semanticos"):
            erros_turnos.append(int(item.get("indice") or 0) + 1)
            if "fallback_conversacional_generico" in av.get("erros_semanticos"):
                fallbacks_conversacionais += 1
        if av.get("alertas_semanticos"):
            alertas_turnos.append(int(item.get("indice") or 0) + 1)

    avaliados = resultados["passou"] + resultados["falhou"] + resultados["alerta"]
    taxa = (resultados["passou"] / avaliados * 100) if avaliados else None
    return {
        "versao_avaliador": VERSAO_AVALIADOR,
        "total_turnos": len(itens),
        "respondidos": sum(1 for x in itens if x.get("status") == "respondido"),
        "concluido_transporte": bool(estado.get("concluido")),
        "avaliados_semanticamente": avaliados,
        "passaram": resultados["passou"],
        "falharam": resultados["falhou"],
        "alertas": resultados["alerta"],
        "nao_avaliados": resultados["nao_avaliado"],
        "taxa_semantica_percentual": round(taxa, 2) if taxa is not None else None,
        "comandos_observados": comandos_total,
        "confirmacoes_indeterminadas": confirm_none,
        "fallbacks_conversacionais": fallbacks_conversacionais,
        "falas_repetidas": sum(
            quantidade for quantidade in frequencia_falas.values()
            if quantidade > 1
        ),
        "maior_repeticao_da_mesma_fala": max(
            frequencia_falas.values(), default=0,
        ),
        "latencia_s": {
            "p50": round(_percentil(duracoes, .50), 3) if duracoes else None,
            "p95": round(_percentil(duracoes, .95), 3) if duracoes else None,
            "max": round(max(duracoes), 3) if duracoes else None,
            "media": round(sum(duracoes) / len(duracoes), 3) if duracoes else None,
        },
        "por_dominio": {k: dict(v) for k, v in sorted(dominios.items())},
        "turnos_com_erros": erros_turnos,
        "turnos_com_alertas": alertas_turnos,
    }


def renderizar_relatorio_markdown(estado: Mapping[str, Any]) -> str:
    resumo = resumir_estado_roteiro(estado)
    itens = [dict(x) for x in estado.get("itens") or [] if isinstance(x, Mapping)]
    linhas = [
        "# Relatório semântico do roteiro da Laylay", "",
        f"Avaliador determinístico v{VERSAO_AVALIADOR}. Não usa LLM para dar nota ao texto livre.", "",
        "## Placar", "",
        f"- Transporte: **{resumo['respondidos']}/{resumo['total_turnos']}** respostas.",
        f"- Avaliados semanticamente: **{resumo['avaliados_semanticamente']}**.",
        f"- Passaram: **{resumo['passaram']}**.",
        f"- Falharam: **{resumo['falharam']}**.",
        f"- Alertas: **{resumo['alertas']}**.",
        f"- Não avaliados semanticamente: **{resumo['nao_avaliados']}**.",
        f"- Fallbacks conversacionais genéricos: **{resumo['fallbacks_conversacionais']}**.",
        f"- Falas envolvidas em repetição: **{resumo['falas_repetidas']}**.",
        f"- Taxa semântica: **{resumo['taxa_semantica_percentual']}%**."
        if resumo["taxa_semantica_percentual"] is not None else "- Taxa semântica: sem amostra.", "",
        "## Latência", "",
        f"- p50: {resumo['latencia_s']['p50']} s",
        f"- p95: {resumo['latencia_s']['p95']} s",
        f"- máxima: {resumo['latencia_s']['max']} s",
        f"- média: {resumo['latencia_s']['media']} s",
        f"- Etapas com `confirmado=None`: **{resumo['confirmacoes_indeterminadas']}**.", "",
        "## Por domínio", "",
        "| Domínio | Passou | Falhou | Alerta | Não avaliado |",
        "|---|---:|---:|---:|---:|",
    ]
    for dominio, c in resumo["por_dominio"].items():
        linhas.append(
            f"| {dominio} | {c.get('passou', 0)} | {c.get('falhou', 0)} | "
            f"{c.get('alerta', 0)} | {c.get('nao_avaliado', 0)} |"
        )

    problemas = [
        x for x in itens
        if (x.get("avaliacao") or {}).get("erros_semanticos")
        or (x.get("avaliacao") or {}).get("alertas_semanticos")
    ]
    linhas += ["", "## Falhas e alertas", ""]
    if not problemas:
        linhas.append("Nenhuma falha ou alerta semântico registrado.")
    for item in problemas:
        av = dict(item.get("avaliacao") or {})
        n = int(item.get("indice") or 0) + 1
        linhas += [f"### Turno {n:03d} — {av.get('resultado_semantico', 'nao_avaliado')}", "",
                   f"**Comando:** {item.get('comando', '')}", "",
                   f"**Intents:** {', '.join(av.get('intents_observadas') or []) or 'nenhuma'}", ""]
        if av.get("erros_semanticos"):
            linhas += ["**Erros:** " + "; ".join(av["erros_semanticos"]), ""]
        if av.get("alertas_semanticos"):
            linhas += ["**Alertas:** " + "; ".join(av["alertas_semanticos"]), ""]

    linhas += ["## Matriz de turnos", "",
               "| # | Resultado | Domínio | Tempo | Intents | Comando |",
               "|---:|---|---|---:|---|---|"]
    for item in itens:
        av = dict(item.get("avaliacao") or {})
        n = int(item.get("indice") or 0) + 1
        dur = av.get("duracao_s")
        tempo = f"{dur:.2f}s" if isinstance(dur, (int, float)) else "-"
        intents = ", ".join(av.get("intents_observadas") or []) or "sem intent"
        comando = str(item.get("comando") or "").replace("|", "\\|").replace("\n", " ")
        linhas.append(
            f"| {n:03d} | {av.get('resultado_semantico', 'nao_avaliado')} | "
            f"{av.get('dominio', '-')} | {tempo} | {intents} | {comando[:90]} |"
        )
    linhas.append("")
    return "\n".join(linhas)


def gravar_relatorios_roteiro(estado: Mapping[str, Any], diretorio: str | Path) -> dict[str, Any]:
    pasta = Path(diretorio)
    pasta.mkdir(parents=True, exist_ok=True)
    resumo = resumir_estado_roteiro(estado)

    tmp = pasta / "resumo.json.tmp"
    tmp.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(pasta / "resumo.json")

    tmp_md = pasta / "relatorio_semantico.md.tmp"
    tmp_md.write_text(renderizar_relatorio_markdown(estado), encoding="utf-8")
    tmp_md.replace(pasta / "relatorio_semantico.md")
    return resumo
