"""Envio de comandos para a extensao Chrome da Laylay."""

from __future__ import annotations

import asyncio
import json
import re
import urllib.parse
import webbrowser
from typing import Any, Callable, Dict


_ACOES_FIXADAS_NA_ABA = {"click", "type", "press", "scroll", "search_in_page"}
_MARCADORES_PAGINA_SENSIVEL = (
    "login", "signin", "sign-in", "password", "senha", "checkout", "pagamento",
    "payment", "bank", "banco", "internetbanking", "carteira", "wallet",
)


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def validar_e_enviar_comando(ctx: Dict[str, Any], action: str | None = None, payload: dict | None = None) -> bool:
    """Valida e envia comandos para a extensao Chrome, com fallback nativo."""
    print(f"🌐 [CHROME:ENTRADA] action={action} payload={payload}")

    action = str(action or "").strip()
    payload = payload if isinstance(payload, dict) else {}
    msg: Dict[str, Any] = {}

    allowed_actions = set(_get(ctx, "ALLOWED_ACTIONS", set()) or set())
    connected_extensions = _get(ctx, "connected_extensions", set())
    ws_loop = _get(ctx, "ws_loop")
    broadcast_command = _get(ctx, "broadcast_command")
    formatar_url_ou_busca = _get(ctx, "formatar_url_ou_busca")
    is_valid_url = _get(ctx, "is_valid_url")
    atualizar_contexto_por_url = _get(ctx, "atualizar_contexto_por_url")
    atualizar_contexto = _get(ctx, "atualizar_contexto")
    buscar_primeiro_video_youtube = _get(ctx, "_buscar_primeiro_video_youtube")
    enviar_confirmado = _get(ctx, "enviar_chrome_confirmado")
    executar_confirmado = _get(ctx, "executar_chrome_confirmado")
    solicitar_aba_ativa = _get(ctx, "solicitar_aba_ativa")
    ultimo_resultado_getter = _get(ctx, "ultimo_resultado_chrome")
    modo_jogo_ativo = _get(ctx, "modo_jogo_ativo")
    jogo_ativo = bool(modo_jogo_ativo()) if callable(modo_jogo_ativo) else False
    permitir_foco = bool(payload.get("permitir_foco"))
    if jogo_ativo and not permitir_foco and action in {"open_tab", "open_url", "youtube_search", "youtube_play"}:
        payload = {**payload, "background": True}
        print(f"🎮 [MODO JOGO] {action} será executado em segundo plano, sem roubar o foco.")

    def _enviar_extensao(msg: Dict[str, Any]) -> bool:
        acao_msg = str(msg.get("action") or "")
        if acao_msg in _ACOES_FIXADAS_NA_ABA and callable(executar_confirmado):
            info = solicitar_aba_ativa(timeout_s=2.5) if callable(solicitar_aba_ativa) else {}
            url = str((info or {}).get("url") or "")
            tab_id = (info or {}).get("tabId")
            if not url or tab_id is None:
                print("❌ [Chrome] Não consegui fixar o comando à aba percebida.")
                return False
            if acao_msg == "type" and any(marcador in url.casefold() for marcador in _MARCADORES_PAGINA_SENSIVEL):
                print(f"🛑 [Chrome] Digitação automática bloqueada em página sensível: {url}")
                return False
            msg = {**msg, "expectedUrl": url, "expectedTabId": tab_id}
            sucesso = bool(executar_confirmado(msg, timeout_s=3.0))
            if not sucesso and callable(ultimo_resultado_getter):
                ultimo = ultimo_resultado_getter() or {}
                if str(ultimo.get("status") or "") == "stale_context":
                    print("⚠️ [Chrome] A aba mudou antes da ação; o comando foi cancelado.")
            return sucesso
        if callable(enviar_confirmado):
            return bool(enviar_confirmado(msg, timeout_s=1.5))
        if ws_loop and connected_extensions and callable(broadcast_command):
            try:
                futuro = asyncio.run_coroutine_threadsafe(
                    broadcast_command(json.dumps(msg)),
                    ws_loop,
                )
                return bool(futuro.result(timeout=1.5))
            except Exception:
                return False
        return False

    prefer_com_br = False
    if action == "entrar_no_site":
        action = "open_url"
        prefer_com_br = True

    if action == "execute_js":
        print("🛑 [Chrome] Execução arbitrária de JavaScript foi removida por segurança.")
        return False
    if action not in allowed_actions and action not in ["click", "type", "press"]:
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
        if ws_loop and connected_extensions and callable(broadcast_command):
            msg = {"action": "open_url", "url": url}
            if payload.get("background"):
                msg["background"] = True
            if not _enviar_extensao(msg):
                print("⚠️ [Chrome] Entrega ficou ambígua; não vou abrir uma segunda aba por fallback.")
                return False
            print(f"📤 [Chrome] Entrega WebSocket confirmada para abrir/atualizar: {url}")
        else:
            print("⚠️ [Fallback] Extensão não conectada, abrindo aba nativa.")
            try:
                return webbrowser.open(url) is not False
            except Exception:
                return False
        return True

    if action == "close_specific_tab":
        target = str(payload.get("target") or "").strip()
        if not target:
            print("❌ [Chrome] close_specific_tab sem target")
            return False
        print(f"📤 [Chrome] Enviando fechamento específico → '{target}'")
        msg = {"action": "close_specific_tab", "target": target}
        if ws_loop and connected_extensions and callable(broadcast_command):
            # Fechamento não pode ser confirmado apenas porque o socket
            # recebeu bytes. Quando a extensão suporta requestId, aguardamos o
            # resultado real da ação; instalações antigas continuam na
            # validação observável feita logo depois pelo executor.
            confirmou_efeito = False
            if callable(executar_confirmado):
                confirmou_efeito = bool(executar_confirmado(msg, timeout_s=3.0))
            else:
                confirmou_efeito = _enviar_extensao(msg)
            if not confirmou_efeito:
                print("❌ [Chrome] extensão não confirmou o fechamento específico")
                return False
            print(f"📤 [Chrome] ✅ Comando ENVIADO → close_specific_tab | target={target}")
            return True
        print("❌ [Chrome] ws_loop ou extensão não conectada")
        return False

    if action == "close_tabs":
        ids = [
            valor for valor in (payload.get("ids") or [])
            if isinstance(valor, int) and not isinstance(valor, bool)
        ]
        if not ids or not (ws_loop and connected_extensions):
            return False
        msg = {"action": "close_tabs", "ids": ids}
        return bool(
            callable(executar_confirmado)
            and executar_confirmado(msg, timeout_s=4.0)
        )

    if action == "click_first_result":
        if not (ws_loop and connected_extensions):
            return False
        msg = {
            "action": "click_first_result",
            "query": str(payload.get("query") or "").strip(),
        }
        return bool(
            callable(executar_confirmado)
            and executar_confirmado(msg, timeout_s=6.0)
        )

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
            msg = {
                "action": "youtube_play",
                "url": url_musica,
                **({"background": True} if payload.get("background") else {}),
                **({"target_tab_id": payload.get("target_tab_id")} if payload.get("target_tab_id") is not None else {}),
            }
            # Música exige confirmação do efeito na página. O simples aceite
            # do WebSocket ou a navegação da aba não provam que há áudio.
            if callable(executar_confirmado):
                confirmou = bool(executar_confirmado(msg, timeout_s=20.0))
            else:
                confirmou = False
            if confirmou:
                print(f"📤 [Chrome] Reprodução do YouTube confirmada: {url_musica}")
                return True
            getter_resultado = _get(ctx, "ultimo_resultado_chrome")
            bruto_resultado = (
                getter_resultado() if callable(getter_resultado) else {}
            )
            resultado_extensao = (
                dict(bruto_resultado) if isinstance(bruto_resultado, dict) else {}
            )
            mesma_acao = (
                str(resultado_extensao.get("action") or "").strip()
                == "youtube_play"
            )
            status_extensao = str(
                resultado_extensao.get("status") or ""
            ).strip()
            mensagem_extensao = str(
                resultado_extensao.get("message") or ""
            ).strip()
            if mesma_acao and status_extensao == "autoplay_blocked":
                print(
                    "⚠️ [Chrome] vídeo aberto; a extensão confirmou a navegação, "
                    "mas não confirmou o áudio"
                )
            elif mesma_acao:
                detalhe = f": {mensagem_extensao}" if mensagem_extensao else ""
                print(
                    "⚠️ [Chrome] youtube_play respondeu "
                    f"status={status_extensao or 'sem_status'}{detalhe}"
                )
            else:
                print(
                    "⚠️ [Chrome] a extensão não devolveu confirmação do "
                    "youtube_play dentro do prazo"
                )
            return False
        try:
            abriu = webbrowser.open(url_musica)
            print(f"🌐 [Chrome] youtube_play sem extensão; fallback nativo: {url_musica}")
            return abriu is not False
        except Exception as exc:
            print(f"❌ [Chrome] fallback de youtube_play falhou: {type(exc).__name__}: {exc}")
            return False

    if action == "youtube_control":
        command = str(payload.get("command") or "").strip().lower()
        if not command:
            print("❌ [Chrome] youtube_control sem comando")
            return False
        if not (ws_loop and connected_extensions):
            print("❌ [Chrome] extensão desconectada; controle do YouTube não foi executado")
            return False
        msg = {
            "action": "youtube_control",
            "command": command,
            **(
                {"target_tab_id": payload.get("target_tab_id")}
                if payload.get("target_tab_id") is not None else {}
            ),
        }
        if command == "queue_select":
            item_id = str(payload.get("queue_item_id") or "").strip()
            indice = payload.get("queue_index")
            if (
                not re.fullmatch(r"[A-Za-z0-9_-]{11}", item_id)
                or isinstance(indice, bool)
            ):
                print("❌ [Chrome] item da fila inválido")
                return False
            try:
                indice = int(indice)
            except (TypeError, ValueError):
                return False
            if not 0 <= indice <= 7:
                return False
            msg.update(queue_item_id=item_id, queue_index=indice)
        if callable(executar_confirmado):
            # O play pode exigir uma segunda tentativa observável depois do
            # bloqueio de autoplay. A pausa tem um caminho curto próprio na
            # extensão. Os prazos cobrem essa verificação, não um sucesso
            # presumido pelo simples envio no socket.
            timeout_controle = (
                12.0
                if command in {"play", "pause_play"}
                else (5.0 if command in {"pause", "queue_select"} else 3.0)
            )
            sucesso = bool(executar_confirmado(msg, timeout_s=timeout_controle))
        else:
            sucesso = _enviar_extensao(msg)
        if not sucesso:
            print(f"⚠️ [Chrome] O YouTube não confirmou o comando {command}")
        return sucesso

    if ws_loop and connected_extensions and callable(broadcast_command):
        if action == "youtube_search":
            query = str(payload.get("query") or "").strip()
            if not query:
                print("❌ [Chrome] youtube_search sem query.")
                return False
            url_escolhida = buscar_primeiro_video_youtube(query) if callable(buscar_primeiro_video_youtube) else ""
            if url_escolhida:
                payload = {
                    "url": url_escolhida,
                    **({"background": True} if payload.get("background") else {}),
                }
                action = "open_url"
                print(f"🎯 [Chrome] youtube_search virou open_url com melhor match: {url_escolhida}")
            else:
                msg = {
                    "action": "youtube_search",
                    "query": query,
                    **({"background": True} if payload.get("background") else {}),
                }
        else:
            msg = {"action": action, **payload}
        if action != "youtube_search":
            msg = {"action": action, **payload}
        if not _enviar_extensao(msg):
            print(f"❌ [Chrome] A extensão não confirmou a execução de {action}.")
            return False
    else:
        print("[WebSocket] Extensão não conectada; comando não foi enviado.")
        return False

    return True


class ChromeComandosRuntime:
    def __init__(self, *, contexto_getter: Callable[[], Dict[str, Any]]) -> None:
        self.contexto_getter = contexto_getter

    def enviar(self, action: str | None = None, payload: dict | None = None) -> bool:
        return validar_e_enviar_comando(self.contexto_getter() or {}, action, payload)

    def enviar_detalhado(
        self, action: str | None = None, payload: dict | None = None,
    ) -> dict[str, Any]:
        """Envia o comando sem descartar a evidência devolvida pela extensão."""
        acao = str(action or "").strip()
        ctx = self.contexto_getter() or {}
        ok = validar_e_enviar_comando(ctx, acao, payload)
        getter = _get(ctx, "ultimo_resultado_chrome")
        bruto = getter() if callable(getter) else {}
        resultado = dict(bruto) if isinstance(bruto, dict) else {}
        mesma_acao = str(resultado.get("action") or "").strip() == acao
        if mesma_acao:
            confirmado = bool(resultado.get("ok") is True)
            return {
                "ok": bool(ok and confirmado),
                "confirmado": confirmado,
                "status": str(resultado.get("status") or "").strip(),
                "message": str(resultado.get("message") or "").strip(),
                "evidence": resultado.get("evidence"),
                "tab": resultado.get("tab"),
                "request_id": str(resultado.get("requestId") or "").strip(),
            }
        return {
            "ok": bool(ok),
            "confirmado": None if ok else False,
            "status": "enviado_sem_evidencia" if ok else "sem_confirmacao",
            "message": "",
            "evidence": None,
            "tab": None,
        }

    def enviar_payload_bruto(self, payload: dict) -> bool:
        ctx = self.contexto_getter() or {}
        loop = _get(ctx, "ws_loop")
        broadcast = _get(ctx, "broadcast_command")
        if not loop or not callable(broadcast):
            return False
        asyncio.run_coroutine_threadsafe(broadcast(json.dumps(dict(payload or {}))), loop)
        return True


def criar_chrome_comandos_runtime(**kwargs: Any) -> ChromeComandosRuntime:
    return ChromeComandosRuntime(**kwargs)
