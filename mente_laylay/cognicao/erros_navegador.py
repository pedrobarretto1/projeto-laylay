"""Resumo seguro e oral de falhas percebidas no navegador."""

from __future__ import annotations

import re
from typing import Any, Mapping
from urllib.parse import urlsplit


def url_sem_dados_sensiveis(url: str) -> str:
    """Remove query/fragmentos que podem conter tokens, IDs e callbacks."""
    bruto = str(url or "").strip()
    if not bruto:
        return ""
    try:
        partes = urlsplit(bruto)
        if partes.scheme and partes.netloc:
            caminho = partes.path.rstrip("/")
            return f"{partes.scheme}://{partes.netloc}{caminho}"[:300]
    except Exception:
        pass
    return re.split(r"[?#]", bruto, maxsplit=1)[0][:300]


def sanitizar_texto_navegador(texto: str) -> str:
    """Retira URLs completas e parâmetros de autenticação de texto técnico."""
    limpo = re.sub(
        r"https?://[^\s|]+",
        lambda achado: url_sem_dados_sensiveis(achado.group(0)),
        str(texto or ""),
        flags=re.IGNORECASE,
    )
    limpo = re.sub(
        r"\b(access_token|refresh_token|id_token|client_id|code|state|nonce)\b"
        r"\s*[:=]?\s*[^\s|,;]+",
        r"\1 [oculto]",
        limpo,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", limpo).strip()


def _contexto(payload: Mapping[str, Any] | None) -> tuple[str, str, str]:
    dados = dict(payload or {})
    titulo = sanitizar_texto_navegador(str(dados.get("title") or "")).strip(" -|:")
    url = str(dados.get("url") or "").strip()
    tecnico = sanitizar_texto_navegador(
        str(dados.get("linha") or dados.get("erro") or "")
    )
    return titulo, url, tecnico


def resumir_erro_navegador(
    payload: Mapping[str, Any] | None,
    *,
    detalhado: bool = False,
) -> str:
    """Explica o evento sem recitar URL, stack trace ou credenciais."""
    titulo, url, tecnico = _contexto(payload)
    identidade = f"{titulo} {url} {tecnico}".casefold()
    oauth_hytale_discord = (
        "discord" in identidade
        and "hytale" in identidade
        and ("oauth" in identidade or "authorize" in identidade or "callback" in identidade)
    )
    if oauth_hytale_discord:
        if detalhado:
            return (
                "A autorização que conecta o Discord à conta do Hytale não terminou direito. "
                "A aba mostrou a falha de autenticação, mas não informou se foi sessão expirada, "
                "login recusado ou problema no redirecionamento."
            )
        return "Ih, a conexão do Hytale com o Discord deu um tropeço. Quer que eu explique sem o tecnês?"

    site = titulo if titulo and len(titulo) <= 60 else "navegador"
    if "404" in identidade:
        if detalhado:
            return f"A página na aba {site} não foi encontrada; o navegador indicou erro 404."
        return f"A aba {site} esbarrou numa página não encontrada. Quer que eu explique?"
    if detalhado:
        return (
            f"A aba {site} registrou uma falha de navegação. O navegador não deu evidência "
            "suficiente para eu afirmar a causa exata sem inventar."
        )
    return f"Ih, houve um erro na aba {site}. Quer que eu explique sem despejar o código todo?"
