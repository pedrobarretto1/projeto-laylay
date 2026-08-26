"""Adaptadores legados para consultas do contexto compartilhado.
As funções permanecem puras e não gravam estado. O módulo original as
reexporta enquanto os consumidores antigos migram para contratos tipados.
"""

from __future__ import annotations

import re
from typing import Any, Dict

from mente_laylay.memoria_mental.continuidade_geral import (
    selecionar_continuidade_reexecutavel,
    selecionar_operacao_reexecutavel_compativel,
)
from mente_laylay.memoria_mental.politica_reexecucao import (
    intents_compativeis_repeticao,
)


_PADRAO_REPETICAO_CURTA = re.compile(
    r"(?:(?P<verbo>tenta|tente|faz|fa[cç]a|vai|leia|l[eê]|ler)\s+)?"
    r"(?:de\s+novo|novamente|outra\s+vez|mais\s+uma\s+vez)|"
    r"tenta\s+outra\s+vez"
)


def classificar_repeticao_curta(texto: str, normalizar_texto_cb) -> Dict[str, str]:
    """Preserva a restrição lexical antes de selecionar a operação."""
    t = str(normalizar_texto_cb(str(texto or "")) or "").strip(" .,!?:;")
    if not t or len(t.split()) > 8:
        return {}
    achado = _PADRAO_REPETICAO_CURTA.fullmatch(t)
    if not achado:
        return {}

    verbo = str(achado.groupdict().get("verbo") or "").strip().casefold()
    if verbo in {"leia", "le", "lê", "ler"}:
        return {"tipo": "tipada", "acao_semantica": "LER", "verbo": verbo}
    return {"tipo": "generica", "acao_semantica": "", "verbo": verbo}


def texto_pede_repeticao_curta(texto: str, normalizar_texto_cb) -> bool:
    return bool(classificar_repeticao_curta(texto, normalizar_texto_cb))


def resolver_repeticao_ultima_acao(
    texto: str,
    estado_atual: Dict[str, Any] | None,
    normalizar_texto_cb,
):
    repeticao = classificar_repeticao_curta(texto, normalizar_texto_cb)
    if not repeticao:
        return None
    estado = dict(estado_atual or {})

    # ROOT R1: repetição tipada nunca cai no fluxo genérico.
    if repeticao.get("tipo") == "tipada":
        permitidos = intents_compativeis_repeticao(
            repeticao.get("acao_semantica", "")
        )
        if not permitidos:
            return None
        oficial_tipado = selecionar_operacao_reexecutavel_compativel(
            estado,
            intents_permitidos=permitidos,
            ttl_s=900.0,
        )
        if oficial_tipado:
            intent_tipado = str(oficial_tipado.get("intent") or "").strip().upper()
            params_tipados = oficial_tipado.get("params")
            if intent_tipado and isinstance(params_tipados, dict):
                return {"intent": intent_tipado, "params": dict(params_tipados)}

        # Compatibilidade V1: só a última ação atômica ainda disponível.
        intent_legado = str(estado.get("ultima_acao_intent") or "").strip().upper()
        params_legados = estado.get("ultima_acao_params")
        if (
            intent_legado in permitidos
            and bool(estado.get("ultima_acao_reexecutavel"))
            and isinstance(params_legados, dict)
        ):
            return {"intent": intent_legado, "params": dict(params_legados)}
        return None

    # Somente repetição genérica entra nos atalhos de mutação falha.
    intent_recente = str(estado.get("ultima_acao_intent") or "").strip().upper()
    status_recente = str(estado.get("ultima_acao_status") or "").strip().casefold()
    params_recentes = estado.get("ultima_acao_params")

    falhas_retentaveis_exclusao = {
        "falha_execucao", "nao_encontrado", "alvo_ambiguo",
        "referencia_nao_resolvida", "falhou",
    }
    if (
        intent_recente == "DELETE_ITEM"
        and status_recente in falhas_retentaveis_exclusao
        and estado.get("ultima_acao_ok") is not True
        and estado.get("ultima_acao_confirmada") is not True
        and isinstance(params_recentes, dict)
        and str(params_recentes.get("alvo") or "").strip()
    ):
        return {"intent": "DELETE_ITEM", "params": dict(params_recentes)}

    falhas_retentaveis_transacao = {
        "falha_execucao", "origem_nao_encontrada", "destino_nao_encontrado",
        "destino_bloqueado", "validacao_falhou", "falhou",
    }
    if (
        intent_recente == "FILE_TRANSACTION"
        and status_recente in falhas_retentaveis_transacao
        and estado.get("ultima_acao_ok") is not True
        and estado.get("ultima_acao_confirmada") is not True
        and isinstance(params_recentes, dict)
        and str(params_recentes.get("operacao") or "").strip().casefold()
        in {"mover", "renomear"}
        and str(params_recentes.get("origem") or "").strip()
        and str(params_recentes.get("destino") or "").strip()
    ):
        return {"intent": "FILE_TRANSACTION", "params": dict(params_recentes)}

    oficial = selecionar_continuidade_reexecutavel(
        estado,
        classe="operacional",
        ttl_s=900.0,
    )
    if oficial:
        if not bool(oficial.get("reexecutavel")):
            return None
        intent = str(oficial.get("intent") or "").strip().upper()
        params = oficial.get("params")
    else:
        if not bool(estado.get("ultima_acao_reexecutavel")):
            return None
        intent = str(estado.get("ultima_acao_intent") or "").strip().upper()
        params = estado.get("ultima_acao_params")
    if not intent or not isinstance(params, dict):
        return None
    return {"intent": intent, "params": dict(params)}


def contexto_musical_ativo(ultima_playlist: Any, playlist_state: Dict[str, Any]) -> bool:
    try:
        if str(ultima_playlist or "").strip():
            return True
        if str(playlist_state.get("name") or "").strip():
            return True
        if str(playlist_state.get("last_url") or "").strip():
            return True
    except Exception:
        pass
    return False


def contexto_mental_ativo(mente_integrada_estado: Dict[str, Any], ultima_playlist: Any, playlist_state: Dict[str, Any]) -> bool:
    try:
        estado = dict(mente_integrada_estado or {})
        if str(estado.get("ultima_entrada") or "").strip():
            return True
        if str(estado.get("ultima_intencao") or "").strip():
            return True
        if str(estado.get("ultimo_alvo") or "").strip():
            return True
        if str(estado.get("ultima_habilidade") or "").strip():
            return True
    except Exception:
        pass
    return contexto_musical_ativo(ultima_playlist, playlist_state)


def texto_depende_de_contexto(texto: str, normalizar_texto_cb) -> bool:
    from mente_laylay.cognicao.referencias_linguagem import texto_tem_referencia_contextual

    t = normalizar_texto_cb(texto)
    if not t:
        return False
    return texto_tem_referencia_contextual(t)


def fluxo_prioritario_da_ia(texto: str, normalizar_texto_cb, texto_depende_de_contexto_cb) -> bool:
    t = normalizar_texto_cb(texto)
    if not t:
        return False
    if any(p in t for p in ["playlist", "música", "musica", "site", "web", "aba", "janela", "foco", "tela cheia", "fullscreen", "opera", "chrome", "edge", "vscode"]):
        if texto_depende_de_contexto_cb(t):
            return True
        if any(p in t for p in ["coloca", "toca", "abre", "abra", "entra", "vai", "mostra", "lista", "quais"]):
            return True
    return False
