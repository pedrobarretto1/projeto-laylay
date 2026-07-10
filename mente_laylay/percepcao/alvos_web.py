"""Decisão contextual para diferenciar sites/abas de aplicativos."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


DOMINIOS_WEB_PADRAO = [
    "instagram.com",
    "youtube.com",
    "netflix.com",
    "twitch.tv",
    "spotify.com",
    "web.whatsapp.com",
]

GATILHOS_CONTEXTO_WEB = [
    "instagram", "insta", "direct", "dm", "conversa do insta", "conversa do instagram",
    "youtube", "netflix", "twitch", "spotify", "whatsapp web", "web.whatsapp",
    "gmail", "google", "drive", "facebook", "twitter", "x.com",
]

BLOQUEIOS_CONTEXTO_NAVEGADOR = [
    "localhost:1455",
    "sign into codex",
    "id_token=",
    "needs_setup=",
    "platform_url=",
    "auth.openai.com",
    "localhost",
    "127.0.0.1",
    "chrome-extension://",
    "moz-extension://",
    "edge-extension://",
    "about:blank",
]


def contexto_navegador_relevante(linha: str, *, normalizar_texto: Callable[[str], str]) -> bool:
    t = normalizar_texto(linha)
    if not t:
        return False
    if any(b in t for b in BLOQUEIOS_CONTEXTO_NAVEGADOR):
        return False
    return True


def eh_alvo_site_web(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str],
    sites_web_alias: set[str] | list[str] | tuple[str, ...],
    sites_directos: dict[str, str],
) -> bool:
    t = normalizar_texto(texto or "")
    if not t:
        return False
    aliases = set(sites_web_alias or [])
    sites = dict(sites_directos or {})
    if t in aliases:
        return True
    if t in sites:
        return True
    if any(alias in t for alias in aliases):
        return True
    return any(dom in t for dom in DOMINIOS_WEB_PADRAO)


def contexto_aponta_site_web(
    texto: str = "",
    *,
    normalizar_texto: Callable[[str], str],
    mente_integrada_estado: dict[str, Any] | None,
    contexto_perceptivo: dict[str, Any] | None,
) -> bool:
    """Usa a mente curta e o contexto vivo para decidir se algo deve ser tratado como site/aba."""
    amostra = []
    texto_norm = normalizar_texto(texto or "")
    if texto_norm:
        amostra.append(texto_norm)

    try:
        mente = dict(mente_integrada_estado or {})
    except Exception:
        mente = {}
    try:
        ctx = dict(contexto_perceptivo or {})
    except Exception:
        ctx = {}

    for item in [
        mente.get("ultima_entrada"),
        mente.get("ultima_resposta"),
        mente.get("ultima_intencao"),
        mente.get("ultimo_alvo"),
        mente.get("ultima_habilidade"),
        ctx.get("exe"),
        ctx.get("title"),
        ctx.get("assunto"),
        ctx.get("topico_ativo"),
        " ".join(ctx.get("logs_recentes") or []),
        " ".join(ctx.get("topicos_recentes") or []),
    ]:
        if item:
            amostra.append(normalizar_texto(str(item)))

    txt = " | ".join([x for x in amostra if x]).strip()
    if not txt:
        return False

    return any(g in txt for g in GATILHOS_CONTEXTO_WEB)


def normalizar_alvo_web_ou_app(
    alvo: str,
    *,
    normalizar_texto: Callable[[str], str],
    sites_web_alias: set[str] | list[str] | tuple[str, ...],
    sites_directos: dict[str, str],
    mente_integrada_estado: dict[str, Any] | None,
    contexto_perceptivo: dict[str, Any] | None,
) -> str:
    """Quando o contexto aponta site, devolve o alvo normalizado; caso contrário, mantém normalizado."""
    alvo_limpo = normalizar_texto(alvo or "")
    if not alvo_limpo:
        return ""
    if eh_alvo_site_web(
        alvo_limpo,
        normalizar_texto=normalizar_texto,
        sites_web_alias=sites_web_alias,
        sites_directos=sites_directos,
    ) or contexto_aponta_site_web(
        alvo_limpo,
        normalizar_texto=normalizar_texto,
        mente_integrada_estado=mente_integrada_estado,
        contexto_perceptivo=contexto_perceptivo,
    ):
        return alvo_limpo
    return alvo_limpo
