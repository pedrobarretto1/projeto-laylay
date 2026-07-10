"""Envio de comandos para a extensao Chrome da Laylay."""

from __future__ import annotations

import asyncio
import json
import urllib.parse
import webbrowser
from typing import Any, Dict
from urllib.parse import urlparse


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def validar_e_enviar_comando(ctx: Dict[str, Any], action: str | None = None, payload: dict | None = None) -> bool:
    """Valida e envia comandos para a extensao Chrome, com fallback nativo."""
    print(f"DEBUG: Entrou em validar_e_enviar_comando → action={action} | payload={payload}")

    action = str(action or "").strip()
    payload = payload if isinstance(payload, dict) else {}

    allowed_actions = set(_get(ctx, "ALLOWED_ACTIONS", set()) or set())
    connected_extensions = _get(ctx, "connected_extensions", set())
    ws_loop = _get(ctx, "ws_loop")
    broadcast_command = _get(ctx, "broadcast_command")
    formatar_url_ou_busca = _get(ctx, "formatar_url_ou_busca")
    is_valid_url = _get(ctx, "is_valid_url")
    atualizar_contexto_por_url = _get(ctx, "atualizar_contexto_por_url")
    atualizar_contexto = _get(ctx, "atualizar_contexto")
    buscar_primeiro_video_youtube = _get(ctx, "_buscar_primeiro_video_youtube")
    solicitar_tab_reciclagem = _get(ctx, "solicitar_tab_reciclagem")

    prefer_com_br = False
    if action == "entrar_no_site":
        action = "open_url"
        prefer_com_br = True

    if action not in allowed_actions and action not in ["click", "type", "press", "execute_js"]:
        print(f"❌ [Chrome] Ação não autorizada: {action}")
        return False

    if action in ["open_tab", "open_url"]:
        raw = payload.get("url") or payload.get("query") or ""
        url = str(formatar_url_ou_busca(str(raw), prefer_com_br=prefer_com_br)).strip().strip("`").strip()
        url = url.replace("searchq=", "search?q=")
        while url.endswith((".", ",", ")", "]")):
            url = url[:-1]
        payload["url"] = url
        if "query" in payload:
            payload.pop("query", None)
        if not is_valid_url(url):
            fallback = f"https://www.google.com/search?q={urllib.parse.quote(str(raw))}"
            print(f"[Navegação] 🔍 Termo '{raw}' não é URL. Convertendo para busca Google...")
            payload["url"] = fallback
            url = fallback
        atualizar_contexto_por_url(url)

        if ws_loop and connected_extensions and callable(broadcast_command):
            msg = {"action": "open_url", "url": url}
            asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg)), ws_loop)
            print(f"📤 [Chrome] Enviando para extensão abrir/atualizar: {url}")
        else:
            print("⚠️ [Fallback] Extensão não conectada, abrindo aba nativa.")
            webbrowser.open(url)
        return True

    if action == "close_specific_tab":
        target = str(payload.get("target") or "").strip()
        if not target:
            print("❌ [Chrome] close_specific_tab sem target")
            return False
        print(f"📤 [Chrome] Enviando fechamento específico → '{target}'")
        msg = {"action": "close_specific_tab", "target": target}
        if ws_loop and connected_extensions and callable(broadcast_command):
            asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg)), ws_loop)
            print(f"📤 [Chrome] ✅ Comando ENVIADO → close_specific_tab | target={target}")
            return True
        print("❌ [Chrome] ws_loop ou extensão não conectada")
        return False

    if action == "youtube_search" and payload.get("query"):
        atualizar_contexto(site="youtube", termo_busca=str(payload.get("query")), aba_id=None)

    if action == "reload_url":
        url = str(payload.get("url") or "").strip()
        if not is_valid_url(url):
            print(f"❌ [Chrome] reload_url inválida: {url}")
            return False
        payload = {"url": url}
        atualizar_contexto_por_url(url)

    if action == "youtube_play":
        url_musica = str(payload.get("url") or "").strip()
        if not url_musica or not is_valid_url(url_musica):
            print("❌ [Chrome] youtube_play sem URL válida")
            return False
        if ws_loop and connected_extensions and callable(broadcast_command):
            msg = {"action": "youtube_play", "url": url_musica}
            asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg)), ws_loop)
            print(f"📤 [Chrome] youtube_play enviado para a extensão: {url_musica}")
            return True
        try:
            abriu = webbrowser.open(url_musica)
            print(f"🌐 [Chrome] youtube_play sem extensão; fallback nativo: {url_musica}")
            return abriu is not False
        except Exception as exc:
            print(f"❌ [Chrome] fallback de youtube_play falhou: {type(exc).__name__}: {exc}")
            return False

    if ws_loop and connected_extensions and callable(broadcast_command):
        if action == "youtube_search":
            query = str(payload.get("query") or "").strip()
            if not query:
                print("❌ [Chrome] youtube_search sem query.")
                return False
            url_escolhida = buscar_primeiro_video_youtube(query) if callable(buscar_primeiro_video_youtube) else ""
            if url_escolhida:
                payload = {"url": url_escolhida}
                action = "open_url"
                print(f"🎯 [Chrome] youtube_search virou open_url com melhor match: {url_escolhida}")
            else:
                msg = {"action": "youtube_search", "query": query}
        else:
            if action == "open_url":
                try:
                    purl = str(payload.get("url") or "").strip()
                    dom = urlparse(purl).netloc or ""
                    tab_id = solicitar_tab_reciclagem(dom, timeout_s=3.0) if callable(solicitar_tab_reciclagem) else None
                    if tab_id is not None:
                        msg = {"action": "update_tab", "tabId": tab_id, "url": purl}
                        if payload.get("auto_click") is True:
                            msg["auto_click"] = True
                        asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg)), ws_loop)
                        return True
                    try:
                        webbrowser.open(purl)
                    except Exception:
                        pass
                    return True
                except Exception:
                    pass
            msg = {"action": action, **payload}
        if action == "youtube_search":
            asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg)), ws_loop)
        else:
            msg = {"action": action, **payload}
            asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg)), ws_loop)
    else:
        print("[WebSocket] Extensão não conectada; comando não foi enviado.")
        return False

    return True
