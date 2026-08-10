"""Focos conversacionais e operacionais da continuidade contextual."""

from __future__ import annotations

import re
import time
from typing import Any, Dict

from mente_laylay.memoria_mental.continuidade_geral import (
    registrar_evento_continuidade,
    selecionar_continuidade,
    selecionar_continuidade_por_classe,
)


def extrair_refino_contexto_mental(texto: str, resultado: Dict[str, Any] | None = None) -> Dict[str, str]:
    """Extrai campos curtos para refinar a memória mental compartilhada."""
    txt = str(texto or "").strip()
    dados = {
        "texto": txt,
        "intencao": "",
        "alvo": "",
        "escopo": "",
        "habilidade": "",
    }
    if not txt:
        return dados
    if isinstance(resultado, dict):
        dados["intencao"] = str(resultado.get("intent") or resultado.get("acao") or "").strip()
        params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
        dados["alvo"] = str(
            params.get("nome_playlist")
            or params.get("nome_app")
            or params.get("query")
            or params.get("url")
            or params.get("alvo")
            or ""
        ).strip()
        dados["escopo"] = str(params.get("target") or params.get("modo") or params.get("platform") or "").strip()
        dados["habilidade"] = str(resultado.get("habilidade") or resultado.get("skill") or "").strip()
    return dados


def inferir_tipo_foco_vivo(
    intencao: str = "",
    habilidade: str = "",
    alvo: str = "",
    texto: str = "",
    resposta: str = "",
    *,
    normalizar_texto_cb=None,
) -> str:
    normalizar = normalizar_texto_cb if callable(normalizar_texto_cb) else lambda v: str(v or "").lower().strip()
    base = normalizar(" ".join([
        str(intencao or ""),
        str(habilidade or ""),
        str(alvo or ""),
        str(texto or ""),
        str(resposta or ""),
    ]))
    intent = str(intencao or "").upper().strip()
    hab = str(habilidade or "").lower().strip()
    if intent in {"CREATE_FOLDER", "DELETE_ITEM", "MOVE_ITEM", "CREATE_FILE"} or hab in {"arquivo", "arquivos"} or any(p in base for p in ["arquivo", "pasta", ".txt"]):
        return "arquivo"
    if intent in {"APP_OPEN", "CLOSE_APP", "MAXIMIZE_WINDOW"} or hab in {"janela", "app"}:
        return "janela"
    if intent in {"OPEN_URL", "CLOSE_TAB", "SITE_ENTER"} or hab in {"site", "navegador"}:
        return "site"
    if intent in {"SEARCH"} or hab in {"pesquisa", "search"}:
        return "pesquisa"
    if intent in {"WEATHER"} or hab in {"clima", "tempo"}:
        return "clima"
    if intent in {"EMAIL_READ", "EMAIL_SYNC", "NOTIFICATIONS"} or "email" in base:
        return "email"
    if intent in {"LAYLAY_PLAYLIST_LIST", "LAYLAY_PLAYLIST_PLAY", "LAYLAY_PLAYLIST_COPY"} or hab in {"playlist_laylay", "curadoria_laylay"}:
        return "playlist_laylay"
    if intent in {"PLAYLIST_CREATE", "PLAYLIST_PLAY", "PLAYLIST_ADD", "PLAYLIST_LIST", "PLAYLIST_MOVE", "MUSIC_SEARCH", "MEDIA_CONTROL"} or hab in {"musica", "música", "playlist", "midia"}:
        return "musica"
    if intent in {"AGENDAR_LEMBRETE", "AGENDAR_ACAO", "LISTAR_AGENDAMENTOS", "CANCELAR_AGENDAMENTO"} or hab == "agenda":
        return "agenda"
    if hab == "conversa" or not intent:
        if any(p in base for p in ["opini", "acha", "presidente", "lula", "política", "politica"]):
            return "opiniao"
        return "conversa"
    return hab or "conversa"


def extrair_topico_foco_vivo(
    texto: str = "",
    resposta: str = "",
    alvo: str = "",
    habilidade: str = "",
    intencao: str = "",
    *,
    normalizar_texto_cb=None,
) -> str:
    alvo_limpo = str(alvo or "").strip()
    if alvo_limpo:
        return alvo_limpo[:120]
    normalizar = normalizar_texto_cb if callable(normalizar_texto_cb) else lambda v: str(v or "").lower().strip()
    t = normalizar(texto)
    for padrao in [
        r"(?:o que voce acha|o que você acha|voce acha|você acha|qual sua opiniao|qual sua opinião)\s+(?:do|da|de|sobre)?\s*(?P<tema>.+)$",
        r"(?:quem\s+e|quem\s+é|o\s+que\s+e|o\s+que\s+é|como\s+funciona|como\s+que\s+funciona|me\s+explica|explica|me\s+fala\s+sobre|fala\s+sobre|me\s+fala\s+de|fala\s+de)\s+(?P<tema>.+)$",
        r"(?:como assim|por que|porque|pq)\s+(?P<tema>.+)$",
    ]:
        m = re.search(padrao, t, flags=re.IGNORECASE)
        if m:
            tema = str(m.group("tema") or "").strip(" ?!.:,;")
            if tema:
                return tema[:120]
    if "lula" in t:
        return "presidente Lula"
    if "presidente" in t:
        return "presidente"
    hab = str(habilidade or "").strip()
    intent = str(intencao or "").strip()
    if hab:
        return hab[:120]
    if intent:
        return intent[:120]
    resp = str(resposta or "").strip()
    return resp[:120]


def atualizar_foco_vivo(
    estado: Dict[str, Any] | None,
    *,
    texto: str = "",
    resposta: str = "",
    intencao: str = "",
    alvo: str = "",
    habilidade: str = "",
    escopo: str = "",
    normalizar_texto_cb=None,
) -> Dict[str, Any]:
    estado = dict(estado or {})
    tipo = inferir_tipo_foco_vivo(
        intencao,
        habilidade,
        alvo,
        texto,
        resposta,
        normalizar_texto_cb=normalizar_texto_cb,
    )
    topico = extrair_topico_foco_vivo(
        texto,
        resposta,
        alvo,
        habilidade,
        intencao,
        normalizar_texto_cb=normalizar_texto_cb,
    )
    agora = time.time()
    tipos_conversacionais = {"conversa", "opiniao", "opinião"}
    dominio = "conversacional" if tipo in tipos_conversacionais else "operacional"
    prefixo = f"foco_{dominio}"
    topico_limpo = str(topico or "").strip()
    alvo_limpo = str(alvo or "").strip()
    topicos_genericos = {"", "conversa", "chat", "opinion", "opiniao", "opinião"}

    # Uma resposta conversacional genérica atualiza a fala, mas preserva o
    # assunto explícito que foi identificado na entrada imediatamente anterior.
    if dominio == "conversacional" and topico_limpo.lower() in topicos_genericos:
        topico_limpo = str(estado.get(f"{prefixo}_topico") or "").strip()
        if not alvo_limpo:
            alvo_limpo = str(estado.get(f"{prefixo}_alvo") or "").strip()

    possui_conteudo = bool(topico_limpo or alvo_limpo or resposta or intencao or habilidade)
    if dominio == "conversacional" and not possui_conteudo:
        return estado

    campos = {
        "tipo": tipo,
        "alvo": str(alvo_limpo or topico_limpo or "").strip()[:160],
        "topico": topico_limpo[:160],
        "habilidade": str(habilidade or tipo or "").strip()[:80],
        "intencao": str(intencao or "").strip()[:80],
        "texto": str(texto or "").strip()[:180],
        "resposta": str(resposta or "").strip()[:180],
        "escopo": str(escopo or "").strip()[:80],
    }
    for chave, valor in campos.items():
        estado[f"{prefixo}_{chave}"] = valor
        # Fachada de compatibilidade: continua representando o foco atualizado
        # mais recentemente para consumidores ainda não migrados.
        estado[f"foco_vivo_{chave}"] = valor
    estado[f"{prefixo}_ts"] = agora
    estado["foco_vivo_ts"] = agora
    estado["ts"] = agora

    dominio_especifico = {
        "janela": "app",
        "app": "app",
        "site": "site",
        "navegador": "site",
        "musica": "musica",
        "música": "musica",
        "playlist": "musica",
        "midia": "musica",
        "arquivo": "arquivo",
        "arquivos": "arquivo",
        "iot": "iot",
    }.get(str(tipo or "").strip().lower())
    if dominio_especifico:
        focos = dict(estado.get("focos_por_dominio") or {})
        focos[dominio_especifico] = {**campos, "ts": agora}
        estado["focos_por_dominio"] = focos

    entrada_norm = str(texto or "").strip().lower()
    referencia_generica = entrada_norm in {
        "como assim", "como assim?", "isso", "essa", "esse", "ela", "ele",
        "pode explicar", "explica melhor", "continua", "pode continuar",
    }
    if (alvo_limpo or (topico_limpo and topico_limpo.lower() not in topicos_genericos)) and not referencia_generica:
        estado["topico_explicito_atual"] = str(alvo_limpo or topico_limpo)[:160]
        estado["topico_explicito_origem"] = dominio
        estado["topico_explicito_ts"] = agora
    estado = registrar_evento_continuidade(
        estado,
        evento="foco",
        tipo=tipo,
        intent=intencao,
        habilidade=habilidade,
        alvo=alvo_limpo,
        topico=topico_limpo,
        texto=texto,
        resposta=resposta,
        origem=dominio,
        ttl_s=900.0 if dominio != "conversacional" else 480.0,
    )
    return estado


def foco_por_dominio(
    estado_atual: Dict[str, Any] | None,
    dominio: str,
    *,
    ttl_s: float = 900.0,
) -> Dict[str, Any]:
    """Retorna o último foco de uma habilidade sem competir com outros domínios."""
    try:
        estado = dict(estado_atual or {})
        chave = str(dominio or "").strip().lower()
        oficial = selecionar_continuidade(
            estado,
            dominio=chave,
            ttl_s=ttl_s,
        )
        if oficial:
            return {
                "tipo": str(oficial.get("tipo") or "").strip(),
                "alvo": str(oficial.get("alvo") or "").strip(),
                "topico": str(oficial.get("topico") or "").strip(),
                "habilidade": str(oficial.get("habilidade") or "").strip(),
                "intencao": str(oficial.get("intent") or "").strip(),
                "texto": str(oficial.get("texto") or "").strip(),
                "resposta": str(oficial.get("resposta") or "").strip(),
                "escopo": str((oficial.get("params") or {}).get("modo") or "").strip(),
                "dominio": str(oficial.get("dominio") or chave),
                "idade_s": float(oficial.get("idade_s") or 0.0),
                "origem_continuidade": "geral_oficial",
            }
        foco = dict((estado.get("focos_por_dominio") or {}).get(chave) or {})
        ts = float(foco.get("ts") or 0.0)
        if not ts or time.time() - ts > ttl_s:
            return {}
        foco["dominio"] = chave
        foco["idade_s"] = max(0.0, time.time() - ts)
        return foco
    except Exception:
        return {}


def foco_vivo_atual(
    estado_atual: Dict[str, Any] | None,
    *,
    ttl_s: float = 480.0,
    dominio: str = "auto",
) -> Dict[str, Any]:
    try:
        estado = dict(estado_atual or {})
        dominio_norm = str(dominio or "auto").strip().lower()
        oficial = selecionar_continuidade_por_classe(
            estado,
            classe=dominio_norm,
            ttl_s=ttl_s,
        )
        if oficial:
            dominio_oficial = str(oficial.get("dominio") or "")
            return {
                "tipo": str(oficial.get("tipo") or "").strip(),
                "alvo": str(oficial.get("alvo") or "").strip(),
                "topico": str(oficial.get("topico") or "").strip(),
                "habilidade": str(oficial.get("habilidade") or "").strip(),
                "intencao": str(oficial.get("intent") or "").strip(),
                "texto": str(oficial.get("texto") or "").strip(),
                "resposta": str(oficial.get("resposta") or "").strip(),
                "escopo": str((oficial.get("params") or {}).get("modo") or "").strip(),
                "dominio": "conversacional" if dominio_oficial == "conversa" else "operacional",
                "dominio_especifico": dominio_oficial,
                "idade_s": float(oficial.get("idade_s") or 0.0),
                "origem_continuidade": "geral_oficial",
            }
        if dominio_norm in {"conversa", "conversacional"}:
            prefixo = "foco_conversacional"
        elif dominio_norm in {"operacao", "operação", "operacional"}:
            prefixo = "foco_operacional"
        else:
            ts_conversa = float(estado.get("foco_conversacional_ts") or 0.0)
            ts_operacao = float(estado.get("foco_operacional_ts") or 0.0)
            prefixo = "foco_conversacional" if ts_conversa >= ts_operacao else "foco_operacional"

        ts = float(estado.get(f"{prefixo}_ts") or 0.0)
        if not ts:
            # Compatibilidade com memórias gravadas antes da separação C2.
            tipo_legado = str(estado.get("foco_vivo_tipo") or "").strip().lower()
            legado_conversa = tipo_legado in {"conversa", "opiniao", "opinião"}
            if dominio_norm in {"conversa", "conversacional"} and not legado_conversa:
                return {}
            if dominio_norm in {"operacao", "operação", "operacional"} and legado_conversa:
                return {}
            prefixo = "foco_vivo"
            ts = float(estado.get("foco_vivo_ts") or 0.0)
        if not ts or time.time() - ts > ttl_s:
            return {}
        return {
            "tipo": str(estado.get(f"{prefixo}_tipo") or "").strip(),
            "alvo": str(estado.get(f"{prefixo}_alvo") or "").strip(),
            "topico": str(estado.get(f"{prefixo}_topico") or "").strip(),
            "habilidade": str(estado.get(f"{prefixo}_habilidade") or "").strip(),
            "intencao": str(estado.get(f"{prefixo}_intencao") or "").strip(),
            "texto": str(estado.get(f"{prefixo}_texto") or "").strip(),
            "resposta": str(estado.get(f"{prefixo}_resposta") or "").strip(),
            "escopo": str(estado.get(f"{prefixo}_escopo") or "").strip(),
            "dominio": "conversacional" if "conversacional" in prefixo else "operacional" if "operacional" in prefixo else "legado",
            "idade_s": max(0.0, time.time() - ts),
        }
    except Exception:
        return {}
