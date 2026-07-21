"""Navegacao por abas usando o transporte compartilhado do Chrome."""

from __future__ import annotations

import urllib.parse
from typing import Any, Callable, Iterable
from urllib.parse import urlparse


def _url_normalizada_para_comparacao(url: str) -> tuple[str, str, str]:
    try:
        parsed = urlparse(str(url or "").strip())
    except Exception:
        return "", "", ""
    host = str(parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = (parsed.path or "/").rstrip("/") or "/"
    query = str(parsed.query or "").strip()
    return host, path, query


def achar_aba_equivalente(abas: Iterable[Any], url_alvo: str) -> int | None:
    """Encontra a mesma página; páginas iniciais também equivalem pelo site."""
    host_alvo, path_alvo, query_alvo = _url_normalizada_para_comparacao(url_alvo)
    if not host_alvo:
        return None
    pagina_inicial = path_alvo in {"/", "/."} and not query_alvo
    for aba in abas if isinstance(abas, list) else []:
        if not isinstance(aba, dict) or not isinstance(aba.get("id"), int):
            continue
        host, path, query = _url_normalizada_para_comparacao(str(aba.get("url") or ""))
        if host != host_alvo:
            continue
        if pagina_inicial or (path == path_alvo and query == query_alvo):
            return int(aba["id"])
    return None


def is_valid_url(url: str) -> bool:
    """Valida URLs http/https bem formadas para comandos do navegador."""
    if not isinstance(url, str) or not url.strip():
        return False
    parsed = urlparse(url)
    return bool(parsed.scheme in ["http", "https"] and parsed.netloc)


def formatar_url_ou_busca(
    termo: str,
    *,
    sites_directos: dict[str, str] | None = None,
    prefer_com_br: bool = False,
) -> str:
    """Transforma um alvo em URL direta ou busca Google."""
    termo = str(termo or "").strip()
    termo_lower = termo.lower()
    sites = dict(sites_directos or {})

    if "google.com/search" in termo_lower or termo.startswith("http"):
        return termo if termo.startswith("http") else f"https://{termo}"

    for site, url_base in sites.items():
        if site == termo_lower:
            return url_base

    if "." in termo and " " not in termo:
        url_tentativa = f"https://{termo}" if not termo.startswith("http") else termo
        if is_valid_url(url_tentativa):
            return url_tentativa

    query = urllib.parse.quote(termo)
    if prefer_com_br:
        return f"https://www.google.com.br/search?q={query}"
    return f"https://www.google.com/search?q={query}"


def classificar_contexto_por_url(url: str) -> dict[str, str | None]:
    """Classifica uma URL para atualizar o contexto web da Laylay."""
    parsed_url = urlparse(str(url or ""))
    host = parsed_url.netloc
    if "youtube.com" in host:
        return {"site": "youtube"}
    if "netflix.com" in host:
        return {"site": "netflix"}
    if "google.com" in host:
        if "search?q=" in str(url):
            query = urllib.parse.unquote_plus(parsed_url.query.split("q=")[1].split("&")[0])
            return {"site": "google_search", "termo_busca": query}
        return {"site": "google"}
    return {"site": "outro", "termo_busca": None}


def fechar_aba_ativa_nativa(
    alvo: str = "",
    *,
    get_active_window: Callable[[], Any],
    hotkey: Callable[..., Any],
    sleep: Callable[[float], Any],
) -> bool:
    """Fecha a aba ativa sem extensão, somente quando o foco está num navegador."""
    try:
        janela = get_active_window() if callable(get_active_window) else None
        titulo = str(getattr(janela, "title", "") or "").strip().lower()
        navegadores = ("opera", "google chrome", "chrome", "microsoft edge", "edge", "brave", "firefox")
        if not janela or not titulo or not any(nome in titulo for nome in navegadores):
            return False
        alvo_norm = str(alvo or "").strip().lower()
        if alvo_norm and alvo_norm not in {"aba", "essa aba", "aba atual", "isso", "ela", "ele"}:
            tokens_genericos = {"www", "com", "org", "net", "br", "http", "https"}
            alvo_tokens = [
                token
                for token in alvo_norm.replace(":", " ").replace("/", " ").replace(".", " ").split()
                if len(token) >= 3 and token not in tokens_genericos
            ]
            if alvo_tokens and not any(token in titulo for token in alvo_tokens):
                return False
        try:
            janela.activate()
        except Exception:
            pass
        hotkey("ctrl", "w")
        sleep(0.15)
        return True
    except Exception:
        return False


def abrir_url_reutilizando_aba(
    url_alvo: str,
    *,
    conectado: Callable[[], bool],
    solicitar_lista_abas: Callable[..., list[Any]],
    enviar_comando: Callable[[str, dict[str, Any]], Any],
    abrir_fallback: Callable[[str], Any],
    auto_click: bool = False,
    corrigir_url_busca: bool = False,
    preservar_foco: bool = False,
) -> bool:
    """Reutiliza uma aba; no modo protegido, trabalha sem trocar a tela."""
    url = str(url_alvo or "").strip()
    if not url:
        return False
    if corrigir_url_busca:
        url = url.replace("searchq=", "search?q=")

    if conectado():
        abas = solicitar_lista_abas()
        tab_id = achar_aba_equivalente(abas, url)
        if tab_id is not None:
            if preservar_foco:
                return True
            enviar_comando(
                "focus_tab",
                {"tabId": tab_id, "url": url},
            )
            return True
        payload = {"url": url, "auto_click": bool(auto_click)}
        if preservar_foco:
            payload["background"] = True
        enviar_comando("open_url", payload)
        return True

    try:
        return abrir_fallback(url) is not False
    except Exception:
        return False


def identificar_abas_vazias(abas: Any, *, log: Callable[[str], Any] = print) -> list[int]:
    """Identifica abas sem conteudo sem atingir paginas de midia protegidas."""
    lista = abas if isinstance(abas, list) else []
    log(f"[ABAS VAZIAS] Total de abas recebidas: {len(lista)}")
    ids: list[int] = []
    for aba in lista:
        if not isinstance(aba, dict):
            continue
        tab_id = aba.get("id")
        url = str(aba.get("url") or "").strip().lower()
        titulo = str(aba.get("title") or "").strip()
        if not isinstance(tab_id, int):
            continue

        log(f"[ABAS VAZIAS] Aba {tab_id} | titulo='{titulo}' | url='{url}'")
        vazia = url.startswith("chrome://newtab") or url == "about:blank" or not url
        if titulo in {"", "Nova guia", "Nova aba", "New Tab", "Nova guia - Google Chrome"}:
            vazia = True
        titulo_lower = titulo.lower()
        if len(titulo) <= 12 and not any(
            nome in titulo_lower for nome in ["youtube", "netflix", "google", "spotify", "whatsapp"]
        ):
            vazia = True
        if "netflix.com" in url or "youtube.com" in url:
            vazia = False
        if vazia:
            ids.append(tab_id)
            log(f"[ABAS VAZIAS] Marcada para fechar: {tab_id}")
    return ids


def fechar_abas_vazias(
    *,
    solicitar_abas: Callable[[], Any],
    enviar_comando: Callable[[str, dict[str, Any]], Any],
    log: Callable[[str], Any] = print,
) -> list[int]:
    """Consulta e fecha as abas classificadas como vazias em um unico lote."""
    try:
        abas = solicitar_abas()
    except Exception as erro:
        log(f"[ABAS VAZIAS] Falha ao consultar abas: {erro}")
        return []
    ids = identificar_abas_vazias(abas, log=log)
    if not ids:
        log("[ABAS VAZIAS] Nenhuma aba vazia detectada")
        return []
    log(f"[ABAS VAZIAS] Fechando {len(ids)} aba(s) em lote")
    enviar_comando("close_tabs", {"ids": ids})
    return ids
