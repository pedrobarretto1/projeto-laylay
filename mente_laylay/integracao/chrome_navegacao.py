"""Navegacao por abas usando o transporte compartilhado do Chrome."""

from __future__ import annotations

import urllib.parse
from typing import Any, Callable, Iterable
from urllib.parse import urlparse


def achar_aba_por_dominio(abas: Iterable[Any], dominio: str) -> int | None:
    dominio_normalizado = str(dominio or "").strip().lower()
    if not dominio_normalizado:
        return None
    for aba in abas if isinstance(abas, list) else []:
        if not isinstance(aba, dict):
            continue
        tab_id = aba.get("id")
        url = str(aba.get("url") or "").lower()
        if isinstance(tab_id, int) and dominio_normalizado in url:
            return tab_id
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


def trazer_chrome_para_frente(
    *,
    get_all_windows: Callable[[], Any],
    sleep: Callable[[float], Any],
) -> bool:
    """Tenta trazer uma janela do Chrome para frente sem acoplar o módulo ao pygetwindow."""
    try:
        wins = []
        try:
            wins = list(get_all_windows() or []) if callable(get_all_windows) else []
        except Exception:
            wins = []

        candidatos = []
        for janela in wins:
            try:
                titulo = str(getattr(janela, "title", "") or "")
            except Exception:
                titulo = ""
            if not titulo:
                continue
            titulo_norm = titulo.lower()
            if "google chrome" in titulo_norm or "chrome" in titulo_norm:
                candidatos.append(janela)

        if not candidatos:
            return False

        janela = candidatos[0]
        try:
            janela.activate()
        except Exception:
            pass
        try:
            janela.maximize()
        except Exception:
            pass
        sleep(0.5)
        return True
    except Exception:
        return False


def fechar_aba_ativa_nativa(
    *,
    get_active_window: Callable[[], Any],
    hotkey: Callable[..., Any],
    sleep: Callable[[float], Any],
    alvo: str = "",
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
) -> bool:
    """Atualiza uma aba do mesmo dominio ou abre uma nova quando necessario."""
    url = str(url_alvo or "").strip()
    if not url:
        return False
    if corrigir_url_busca:
        url = url.replace("searchq=", "search?q=")

    if conectado():
        try:
            dominio = urlparse(url).netloc.lower()
        except Exception:
            dominio = ""
        abas = solicitar_lista_abas()
        tab_id = achar_aba_por_dominio(abas, dominio) if dominio else None
        if tab_id is not None:
            enviar_comando(
                "update_tab",
                {"tabId": tab_id, "url": url, "auto_click": bool(auto_click)},
            )
            return True
        enviar_comando("open_url", {"url": url, "auto_click": bool(auto_click)})
        return True

    try:
        abrir_fallback(url)
        return True
    except Exception:
        return False
