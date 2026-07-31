"""Handlers pequenos do WebSocket da extensao Chrome.

Eles resolvem respostas pendentes por `requestId`.
Nao executam acoes praticas nem alteram o fluxo conversacional.
"""

from __future__ import annotations

import asyncio
import re
import threading
import time
from typing import Any, Callable, Dict

from mente_laylay.cognicao.erros_navegador import (
    resumir_erro_navegador,
    sanitizar_texto_navegador,
    url_sem_dados_sensiveis,
)


def _set_event(entry: Any) -> None:
    if not isinstance(entry, dict):
        return
    ev = entry.get("event")
    if ev:
        try:
            ev.set()
        except Exception:
            pass


def handle_tabs_list(data: Dict[str, Any], pending_tabs_requests: Dict[str, Any]) -> None:
    rid = str(data.get("requestId") or "")
    tabs = data.get("tabs")
    if rid and rid in pending_tabs_requests:
        entry = pending_tabs_requests.get(rid) or {}
        entry["tabs"] = tabs if isinstance(tabs, list) else []
        _set_event(entry)


def handle_active_tab_url(data: Dict[str, Any], pending_active_url_requests: Dict[str, Any]) -> None:
    rid = str(data.get("requestId") or "")
    url = str(data.get("url") or "")
    title = str(data.get("title") or "")
    if rid and rid in pending_active_url_requests:
        entry = pending_active_url_requests.get(rid)
        if isinstance(entry, asyncio.Future):
            if not entry.done():
                entry.set_result({"url": url, "title": title})
        elif isinstance(entry, dict):
            entry["url"] = url
            entry["title"] = title
            _set_event(entry)


def handle_youtube_data(data: Dict[str, Any], pending_active_url_requests: Dict[str, Any]) -> None:
    rid = str(data.get("requestId") or "")
    url = str(data.get("url") or "")
    title = str(data.get("title") or "")
    canal = str(data.get("canal") or data.get("channel") or "")
    tab_id = data.get("tabId")
    if rid and rid in pending_active_url_requests:
        entry = pending_active_url_requests.get(rid)
        if isinstance(entry, asyncio.Future):
            if not entry.done():
                entry.set_result({"url": url, "title": title, "canal": canal, "tabId": tab_id})
        elif isinstance(entry, dict):
            entry["url"] = url
            entry["title"] = title
            entry["canal"] = canal
            entry["tabId"] = tab_id
            _set_event(entry)


def handle_check_tabs_result(data: Dict[str, Any], pending_check_tabs_requests: Dict[str, Any]) -> None:
    try:
        rid = str(data.get("requestId") or "")
        tab_id = data.get("tabId", None)
        if rid and rid in pending_check_tabs_requests:
            entry = pending_check_tabs_requests.get(rid) or {}
            entry["tabId"] = int(tab_id) if isinstance(tab_id, int) else None
            _set_event(entry)
    except Exception:
        pass


def handle_page_content(data: Dict[str, Any], pending_page_content_requests: Dict[str, Any]) -> None:
    request_id = data.get("requestId")
    if request_id and request_id in pending_page_content_requests:
        future = pending_page_content_requests.pop(request_id)
        future.set_result(data)


def handle_command_result(data: Dict[str, Any], pending_command_requests: Dict[str, Any]) -> None:
    request_id = str(data.get("requestId") or "")
    if not request_id:
        return
    entry = pending_command_requests.get(request_id)
    if not isinstance(entry, dict):
        return
    entry["result"] = dict(data)
    event = entry.get("event")
    if event is not None:
        event.set()


def handle_player_event(
    data: Dict[str, Any],
    *,
    playlist_state: Dict[str, Any],
    yt_clean_url: Callable[[str], str] | None,
    playlist_avancar_proxima: Callable[[], bool] | None,
    falar_com_lipsync: Callable[..., Any] | None,
) -> None:
    event = str(data.get("event") or "").strip().lower()
    url = str(data.get("url") or "")
    is_ad = bool(data.get("isAd"))
    duration = int(data.get("duration") or 0)
    tab_id = data.get("tabId")

    if event == "user_click_detected":
        playlist_state["user_intervened"] = True
        print("🎧 USER_CLICK_DETECTED → playlists automáticas pausadas até o fim do vídeo atual")
        return

    if event != "video_ended":
        return
    # A duração não é um identificador confiável de anúncio: músicas curtas são
    # válidas e o YouTube às vezes entrega 0 quando substitui o elemento de vídeo.
    if is_ad:
        return
    if not playlist_state.get("name"):
        return

    now = time.time()
    event_id = str(data.get("eventId") or "").strip()
    clean_url = yt_clean_url(url) if callable(yt_clean_url) else str(url or "")
    dedup_key = event_id or f"ended:{tab_id}:{clean_url}:{duration}"
    vistos = playlist_state.setdefault("ended_event_ids", [])
    if not isinstance(vistos, list):
        vistos = []
        playlist_state["ended_event_ids"] = vistos
    if dedup_key in vistos:
        print(f"🎧 [AUTO-NEXT] evento duplicado ignorado: {dedup_key}")
        return
    vistos.append(dedup_key)
    del vistos[:-32]
    playlist_state["last_ended_event"] = dedup_key
    playlist_state["last_ended_ts"] = now
    if isinstance(tab_id, int):
        playlist_state["tab_id"] = tab_id

    pl_nm = str(playlist_state.get("name") or "")

    def _falar_fim_playlist() -> None:
        if callable(falar_com_lipsync):
            falar_com_lipsync(f"Acabou o show. Essa foi a última da playlist {pl_nm}.", "debochada", 2)

    if playlist_state.get("user_intervened"):
        playlist_state["user_intervened"] = False
        print("🎧 Vídeo manual terminou — retomando playlist")
        print("[AUTO-NEXT] Música anterior finalizada. Carregando próxima...")
        ok_next = bool(playlist_avancar_proxima()) if callable(playlist_avancar_proxima) else False
        if not ok_next and playlist_state.get("last_advance_status") == "fim":
            _falar_fim_playlist()
        return

    if str(playlist_state.get("last_url") or "") and str(playlist_state.get("last_url") or "") != clean_url:
        return

    print("[AUTO-NEXT] Música anterior finalizada. Carregando próxima...")
    ok_next = bool(playlist_avancar_proxima()) if callable(playlist_avancar_proxima) else False
    if not ok_next and playlist_state.get("last_advance_status") == "fim":
        _falar_fim_playlist()
    elif not ok_next:
        print("⚠️ [AUTO-NEXT] não consegui abrir a próxima faixa; a playlist continua ativa")


def montar_linha_user_context(data: Dict[str, Any]) -> tuple[str, str, Any, str, str]:
    kind = str(data.get("kind") or "").strip()
    detail = data.get("detail")
    url = str(data.get("url") or "").strip()
    title = str(data.get("title") or "").strip()
    if not kind and (detail is None or detail == "" or detail == {}):
        return "", kind, detail, url, title

    linha = ""
    if kind == "nav":
        linha = f"Navegação: {sanitizar_texto_navegador(title)} | {url_sem_dados_sensiveis(url)}".strip()
    elif kind == "click":
        if isinstance(detail, dict):
            label = str(detail.get("label") or "").strip()
            href = str(detail.get("href") or "").strip()
            linha = f"Clique: {sanitizar_texto_navegador(label)}" + (
                f" | {url_sem_dados_sensiveis(href)}" if href else ""
            )
        else:
            linha = f"Clique: {str(detail)}"
    elif kind == "console":
        if isinstance(detail, dict):
            level = str(detail.get("level") or "log").strip()
            msg = str(detail.get("message") or "").strip()
            linha = f"Console {level}: {sanitizar_texto_navegador(msg)}"
        else:
            linha = f"Console: {str(detail)}"
    else:
        linha = f"{kind}: {str(detail)}".strip()
    return linha, kind, detail, url, title


def handle_user_context(data: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Processa contexto vindo da extensao e devolve updates para o orquestrador."""
    updates: Dict[str, Any] = {}

    contexto_navegador_relevante = ctx.get("_contexto_navegador_relevante")
    registrar_log_navegador = ctx.get("_registrar_log_navegador")
    continuidades_get = ctx.get("_continuidades_get")
    continuidades_update = ctx.get("_continuidades_update")
    falar_com_lipsync = ctx.get("falar_com_lipsync")

    linha, kind, detail, url, title = montar_linha_user_context(data)
    if not linha and not kind:
        return updates

    estado_percepcao = ctx.get("estado_percepcao")
    if linha and callable(contexto_navegador_relevante) and contexto_navegador_relevante(linha):
        if callable(registrar_log_navegador):
            estado_percepcao = registrar_log_navegador(estado_percepcao, linha, limite=5)
            updates["estado_percepcao"] = estado_percepcao
        print(f"🧠 [CTX] {linha}")

    now = time.time()

    if kind == "nav":
        if "spinning.fish" in url:
            updates["fish_mode_active"] = True
            updates["fish_mode_started_ts"] = now
        elif bool(ctx.get("fish_mode_active")):
            updates["fish_mode_active"] = False
            updates["fish_mode_started_ts"] = 0.0

    is_speaking = bool(ctx.get("is_speaking"))
    ultimo_proativo_ts = float(ctx.get("_ultimo_proativo_ts") or 0.0)
    ultimo_sugerido_ts = float(ctx.get("_ultimo_sugerido_ts") or 0.0)
    sugestao_bloqueada_ate = ctx.get("sugestao_bloqueada_ate") or {}

    if kind == "nav":
        u = url.lower()
        sites_3d = ["thingiverse.com", "printables.com", "cults3d.com", "myminifactory.com", "makerworld.com"]
        if any(x in u for x in sites_3d):
            try:
                contexto_sistema = ctx.get("contexto_sistema") or {}
                exe = str(contexto_sistema.get("exe") or "").lower()
                assunto = str(contexto_sistema.get("assunto") or "")
            except Exception:
                exe = ""
                assunto = ""
            estado_sugestao = continuidades_get("comando_sugerido_estado", "NONE") if callable(continuidades_get) else "NONE"
            if ("cura" in exe) or ("prusa" in exe) or (assunto == "Impressão 3D"):
                if not is_speaking and estado_sugestao == "NONE" and now - ultimo_proativo_ts >= 1200:
                    updates["_ultimo_proativo_ts"] = now
                    if callable(falar_com_lipsync):
                        falar_com_lipsync("Preparando algo pra impressora 3D do seu irmão?", "calma", 1)

    estado_sugestao = continuidades_get("comando_sugerido_estado", "NONE") if callable(continuidades_get) else "NONE"
    if estado_sugestao == "NONE" and now - ultimo_sugerido_ts > 15:
        def _bloqueado(chave: str) -> bool:
            try:
                return now < float(sugestao_bloqueada_ate.get(chave, 0.0))
            except Exception:
                return False

        erro_detectado = False
        erro_txt = ""
        if kind == "nav" and ("404" in (title.lower() + " " + url.lower())):
            erro_detectado = True
            erro_txt = f"{title} | {url}"
        if kind == "console" and isinstance(detail, dict):
            lvl = str(detail.get("level") or "").lower()
            msg = str(detail.get("message") or "")
            if "error" in lvl or "uncaught" in msg.lower() or "404" in msg:
                erro_detectado = True
                erro_txt = f"{linha} | {title} | {url}"

        comando_sugerido = continuidades_get("comando_sugerido") if callable(continuidades_get) else None
        if erro_detectado and comando_sugerido is None:
            try:
                ultimo_open_site = ctx.get("ultimo_open_site") or {}
                last_ts = float(ultimo_open_site.get("ts") or 0.0)
                last_topic = str(ultimo_open_site.get("topic") or "").lower()
                last_url = str(ultimo_open_site.get("url") or "").lower()
            except Exception:
                last_ts = 0.0
                last_topic = ""
                last_url = ""

            if now - last_ts < 25 and ("pet" in last_topic or "petz" in last_url) and not _bloqueado("OPEN_SITE_ALT"):
                if callable(continuidades_update):
                    continuidades_update(
                        comando_sugerido="OPEN_SITE_ALT",
                        comando_sugerido_payload={"topic": "pet", "erro": erro_txt, "url": url, "title": title},
                        comando_sugerido_estado="PENDING_CONFIRM",
                        comando_sugerido_ts=now,
                    )
                updates["_ultimo_sugerido_ts"] = now
                if not is_speaking and callable(falar_com_lipsync):
                    falar_com_lipsync("Ih, esse site de pet tá dando erro. Quer que eu tente outro?", "calma", 1)
                return updates

            lower_erro = (erro_txt or "").lower()
            if ("play" in lower_erro) or ("autoplay" in lower_erro) or ("failed" in lower_erro) or ("falhou" in lower_erro):
                if not _bloqueado("RELOAD_PAGE") and callable(continuidades_update):
                    continuidades_update(
                        comando_sugerido="RELOAD_PAGE",
                        comando_sugerido_payload={"url": url, "title": title, "erro": erro_txt},
                    )
                    if not is_speaking and callable(falar_com_lipsync):
                        falar_com_lipsync("Vi que o play falhou no Chrome. Quer que eu tente recarregar a página?", "calma", 1)
            else:
                if not _bloqueado("EXPLAIN_ERROR") and callable(continuidades_update):
                    continuidades_update(
                        comando_sugerido="EXPLAIN_ERROR",
                        comando_sugerido_payload={"erro": erro_txt, "url": url, "title": title, "linha": linha},
                    )

        comando_sugerido = continuidades_get("comando_sugerido") if callable(continuidades_get) else None
        if comando_sugerido:
            if callable(continuidades_update):
                continuidades_update(comando_sugerido_estado="PENDING_CONFIRM", comando_sugerido_ts=now)
            updates["_ultimo_sugerido_ts"] = now
            if comando_sugerido == "EXPLAIN_ERROR" and not is_speaking and callable(falar_com_lipsync):
                payload_atual = continuidades_get("comando_sugerido_payload") if callable(continuidades_get) else {}
                falar_com_lipsync(
                    resumir_erro_navegador(payload_atual),
                    "curiosa",
                    1,
                )

    return updates


def dispatch_event(data: Dict[str, Any], handlers: Dict[str, Callable[[Dict[str, Any]], Any]]) -> Any:
    """Encaminha cada mensagem WebSocket para um unico handler conhecido."""
    if not isinstance(data, dict):
        return None
    tipo = str(data.get("type") or "").strip()
    if tipo == "ping":
        return None

    por_tipo = {
        "TABS_LIST": "tabs_list",
        "CHECK_TABS_RESULT": "check_tabs_result",
        "ACTIVE_TAB_URL": "active_tab_url",
        "YOUTUBE_DATA": "youtube_data",
        "PLAYER_EVENT": "player_event",
        "USER_CONTEXT": "user_context",
        "PAGE_CONTENT": "page_content",
        "COMMAND_RESULT": "command_result",
    }
    nome_handler = por_tipo.get(tipo, "action")
    handler = handlers.get(nome_handler)
    # PAGE_SNAPSHOT é percepção contínua e pode conter URLs, textos e campos
    # inteiros da página. Ele continua sendo processado, mas não deve inundar
    # o terminal nem expor o payload bruto a cada atualização.
    if nome_handler == "action" and tipo not in {"ping", "PAGE_SNAPSHOT"}:
        print(f"📥 [DEBUG Chrome] {data}")
    return handler(data) if callable(handler) else None


class ChromeWsEventosRuntime:
    """Coordena handlers da extensão sem possuir o estado global da Laylay."""

    def __init__(
        self,
        *,
        solicitacoes: Any,
        playlist_state: Dict[str, Any],
        yt_clean_url: Callable[[str], str],
        playlist_avancar_proxima: Callable[[], bool],
        falar_com_lipsync: Callable[..., Any],
        user_context_getter: Callable[[], Dict[str, Any]],
        aplicar_user_updates: Callable[[Dict[str, Any]], Any],
        action_context_getter: Callable[[], Dict[str, Any]],
        aplicar_action_updates: Callable[[Dict[str, Any]], Any],
    ) -> None:
        self.solicitacoes = solicitacoes
        self.playlist_state = playlist_state
        self.yt_clean_url = yt_clean_url
        self.playlist_avancar_proxima = playlist_avancar_proxima
        self.falar_com_lipsync = falar_com_lipsync
        self.user_context_getter = user_context_getter
        self.aplicar_user_updates = aplicar_user_updates
        self.action_context_getter = action_context_getter
        self.aplicar_action_updates = aplicar_action_updates

    def _user_context(self, data: Dict[str, Any]) -> None:
        updates = handle_user_context(data, self.user_context_getter() or {})
        if isinstance(updates, dict):
            self.aplicar_user_updates(updates)

    def _action(self, data: Dict[str, Any]) -> bool:
        updates = handle_action(data, self.action_context_getter() or {})
        if not isinstance(updates, dict):
            return False
        self.aplicar_action_updates(updates)
        return bool(updates.get("handled"))

    def _command_result(self, data: Dict[str, Any]) -> bool:
        with self.solicitacoes.pendencias_lock:
            handle_command_result(data, self.solicitacoes.pendencias_comandos)
        return self._action(data)

    def dispatch(self, data: Dict[str, Any]) -> Any:
        def protegido(func: Callable[[Dict[str, Any]], Any]) -> Callable[[Dict[str, Any]], Any]:
            def executar(item: Dict[str, Any]) -> Any:
                with self.solicitacoes.pendencias_lock:
                    return func(item)
            return executar

        handlers = {
            "tabs_list": protegido(lambda item: handle_tabs_list(item, self.solicitacoes.pendencias_abas)),
            "check_tabs_result": protegido(lambda item: handle_check_tabs_result(item, self.solicitacoes.pendencias_checagem_abas)),
            "active_tab_url": protegido(lambda item: handle_active_tab_url(item, self.solicitacoes.pendencias_aba_ativa)),
            "youtube_data": protegido(lambda item: handle_youtube_data(item, self.solicitacoes.pendencias_aba_ativa)),
            "player_event": lambda item: handle_player_event(
                item,
                playlist_state=self.playlist_state,
                yt_clean_url=self.yt_clean_url,
                playlist_avancar_proxima=self.playlist_avancar_proxima,
                falar_com_lipsync=self.falar_com_lipsync,
            ),
            "user_context": self._user_context,
            "page_content": protegido(lambda item: handle_page_content(item, self.solicitacoes.pendencias_conteudo_pagina)),
            "command_result": self._command_result,
            "action": self._action,
        }
        return dispatch_event(data, handlers)


def criar_chrome_ws_eventos_runtime(**kwargs: Any) -> ChromeWsEventosRuntime:
    return ChromeWsEventosRuntime(**kwargs)


def handle_action(data: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Processa mensagens de action da extensao Chrome e devolve updates."""
    updates: Dict[str, Any] = {"handled": False}
    action = str(data.get("action") or "").strip()

    aba_titulo_atual = str(ctx.get("aba_titulo_atual") or "")
    aba_url_atual = str(ctx.get("aba_url_atual") or "")
    aba_anterior_id = ctx.get("aba_anterior_id")
    aba_historico = list(ctx.get("aba_historico") or [])
    tab_last_seen = dict(ctx.get("_tab_last_seen") or {})
    musica_busca_query = ctx.get("_musica_busca_query")
    musica_ultima_verificada = ctx.get("_musica_ultima_verificada")

    percepcao_set = ctx.get("_percepcao_set")
    atualizar_contexto_por_url = ctx.get("atualizar_contexto_por_url")
    musica_registrar_historico = ctx.get("_musica_registrar_historico")
    verificar_musica_autonoma = ctx.get("_verificar_musica_autonoma")
    falar_com_lipsync = ctx.get("falar_com_lipsync")
    registrar_musica_atual = ctx.get("_registrar_musica_atual")

    message_type = str(data.get("type") or "").strip().upper()
    if message_type == "PAGE_SNAPSHOT":
        snapshot = data.get("payload")
        if isinstance(snapshot, dict) and callable(percepcao_set):
            percepcao_set("pagina_ativa", dict(snapshot))
            url = str(snapshot.get("url") or "")
            title = str(snapshot.get("title") or "")
            if url:
                updates["aba_url_atual"] = url
            if title:
                updates["aba_titulo_atual"] = title
        updates["handled"] = True
        return updates

    if message_type == "COMMAND_RESULT":
        if callable(percepcao_set):
            percepcao_set("ultimo_resultado_chrome", {
                "requestId": data.get("requestId"),
                "action": str(data.get("action") or ""),
                "ok": data.get("ok") is True,
                "status": str(data.get("status") or ""),
                "message": str(data.get("message") or ""),
                "evidence": data.get("evidence"),
                "tab": data.get("tab"),
                "ts": data.get("ts"),
            })
        updates["handled"] = True
        return updates

    if message_type == "EXTENSION_HELLO":
        if callable(percepcao_set):
            percepcao_set("extensao_chrome", {
                "protocolVersion": data.get("protocolVersion"),
                "capabilities": list(data.get("capabilities") or []),
                "conectada": True,
                "ts": time.time(),
            })
        updates["handled"] = True
        return updates

    if action == "title_update":
        novo_titulo = str(data.get("title") or "").strip()
        if novo_titulo and novo_titulo != aba_titulo_atual:
            aba_titulo_atual = novo_titulo
            updates["aba_titulo_atual"] = aba_titulo_atual
            if callable(percepcao_set):
                percepcao_set("aba_ativa", {"titulo": aba_titulo_atual, "url": aba_url_atual})
            print(f"📥 [Chrome] Título atualizado → {aba_titulo_atual}")
        updates["handled"] = True
        return updates

    if action in ("url_update", "active_tab_changed") or (not action and "url" in data):
        nova_url = str(data.get("url") or "").strip()
        novo_titulo = str(data.get("title") or "").strip()

        mudou = False
        if nova_url and nova_url != aba_url_atual:
            aba_url_atual = nova_url
            updates["aba_url_atual"] = aba_url_atual
            mudou = True

        if novo_titulo and novo_titulo != aba_titulo_atual:
            aba_titulo_atual = novo_titulo
            updates["aba_titulo_atual"] = aba_titulo_atual
            mudou = True

        if mudou:
            if callable(percepcao_set):
                percepcao_set("aba_ativa", {"titulo": aba_titulo_atual, "url": aba_url_atual})
            print(f"🧠 [CTX] Aba Ativa -> [{aba_titulo_atual}] {aba_url_atual}")

            if action == "active_tab_changed":
                if callable(atualizar_contexto_por_url):
                    atualizar_contexto_por_url(aba_url_atual)

                if aba_url_atual and not aba_url_atual.startswith("chrome://"):
                    tab_last_seen[aba_url_atual] = {"title": aba_titulo_atual, "ts": time.time()}
                    updates["_tab_last_seen"] = tab_last_seen

                if (
                    "youtube.com/watch" in aba_url_atual
                    and aba_titulo_atual
                    and aba_titulo_atual != "YouTube"
                    and not aba_titulo_atual.endswith(") YouTube")
                ):
                    clean_title = re.sub(r"^\(\d+\)\s*", "", aba_titulo_atual).replace(" - YouTube", "").strip()
                    if callable(registrar_musica_atual):
                        registrar_musica_atual(clean_title, "tocando", aba_url_atual)
                    if callable(musica_registrar_historico):
                        threading.Thread(target=musica_registrar_historico, args=(clean_title,), daemon=True).start()

                    if musica_busca_query and musica_ultima_verificada != aba_url_atual:
                        updates["_musica_ultima_verificada"] = aba_url_atual
                        if callable(verificar_musica_autonoma):
                            threading.Thread(target=verificar_musica_autonoma, args=(clean_title,), daemon=True).start()

        updates["handled"] = True
        return updates

    if action == "manual_tab_change":
        frm = data.get("from")
        to = data.get("to")
        ft = data.get("fromTitle", "")
        tt = data.get("toTitle", "")
        if frm and to and frm != to:
            if aba_anterior_id and aba_anterior_id != to:
                aba_historico.append(aba_anterior_id)
                updates["aba_historico"] = aba_historico
            updates["aba_anterior_id"] = to
            print(f"🔄 [Chrome] Troca de aba manual: {ft} ({frm}) → {tt} ({to})")
        updates["handled"] = True
        return updates

    if action == "tab_closed":
        closed_id = data.get("id")
        print(f"🗑️ [Chrome] Aba {closed_id} fechada.")
        aba_historico = [aid for aid in aba_historico if aid != closed_id]
        updates["aba_historico"] = aba_historico
        if aba_anterior_id == closed_id:
            updates["aba_anterior_id"] = None
        updates["handled"] = True
        return updates

    if action == "youtube_video_started":
        video_title = data.get("title", "")
        if callable(registrar_musica_atual):
            registrar_musica_atual(video_title, "tocando", str(data.get("url") or aba_url_atual))
        if callable(musica_registrar_historico):
            threading.Thread(target=musica_registrar_historico, args=(video_title,), daemon=True).start()
        if musica_busca_query and callable(verificar_musica_autonoma):
            threading.Thread(target=verificar_musica_autonoma, args=(video_title,), daemon=True).start()
        print(f"▶️ [YouTube] Vídeo iniciado: {video_title}")
        updates["handled"] = True
        return updates

    if action == "youtube_video_paused":
        video_title = data.get("title", "")
        if callable(registrar_musica_atual):
            registrar_musica_atual(video_title, "pausada", str(data.get("url") or aba_url_atual))
        print(f"⏸️ [YouTube] Vídeo pausado: {video_title}")
        updates["handled"] = True
        return updates

    if action == "youtube_video_resumed":
        video_title = data.get("title", "")
        if callable(registrar_musica_atual):
            registrar_musica_atual(video_title, "tocando", str(data.get("url") or aba_url_atual))
        print(f"▶️ [YouTube] Vídeo retomado: {video_title}")
        updates["handled"] = True
        return updates

    if action == "youtube_video_ended":
        video_title = data.get("title", "")
        if callable(registrar_musica_atual):
            registrar_musica_atual(video_title, "finalizada", str(data.get("url") or aba_url_atual))
        print(f"⏹️ [YouTube] Vídeo finalizado: {video_title}")
        updates["handled"] = True
        return updates

    if action == "youtube_search_result_clicked":
        query = data.get("query", "")
        title = data.get("title", "")
        print(f"✅ [YouTube] Resultado de busca clicado para '{query}': {title}")
        updates["handled"] = True
        return updates

    if action == "auto_click_status":
        status = str(data.get("status") or "").strip()
        motivo = str(data.get("motivo") or "").strip()
        if status == "erro_clique":
            print(f"❌ [AUTO-CLICK] Falhou: {motivo}")
            if callable(falar_com_lipsync):
                falar_com_lipsync("Não achei um link orgânico pra clicar.", "calma", 1)
        updates["handled"] = True
        return updates

    if action == "close_tab_status":
        status = str(data.get("status") or "").strip()
        if status == "blocked_form" and callable(falar_com_lipsync):
            falar_com_lipsync("Você está digitando em um formulário. Eu não vou fechar e apagar teu trabalho.", "calma", 1)
        updates["handled"] = True
        return updates

    if action == "error":
        error_msg = data.get("message", "Erro desconhecido na extensão.")
        print(f"❌ [Chrome ERRO] {error_msg}")
        if callable(falar_com_lipsync):
            falar_com_lipsync(
                resumir_erro_navegador({"erro": error_msg}), "irritada", 2
            )
        updates["handled"] = True
        return updates

    if action == "ping":
        updates["handled"] = True
        return updates

    if action:
        print(f"🤔 [Chrome] Mensagem desconhecida da extensão: {data}")
        updates["handled"] = True
        return updates

    return updates
