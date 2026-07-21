"""Roteador de comandos de conteúdo da Laylay.

Separa comandos ligados a navegador, mídia e playlists do arquivo principal.
"""

from __future__ import annotations

import ctypes
import re
from typing import Any, Mapping

VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1


def _get(ctx: Mapping[str, Any], key: str):
    valor = ctx.get(key)
    return valor


def executar_comando_conteudo(c_nome: str, c_args: str, comando: str, c_upper: str, ctx: Mapping[str, Any]) -> bool:
    c = str(c_nome or "").upper()
    a = "" if c_args is None else str(c_args).strip()

    enviar_comando_chrome = _get(ctx, "enviar_comando_chrome")
    validar_e_enviar_comando = _get(ctx, "validar_e_enviar_comando")
    ajustar_volume_sistema = _get(ctx, "ajustar_volume_sistema")
    falar = _get(ctx, "falar_com_lipsync")
    play_playlist = _get(ctx, "play_playlist")
    playlist_shuffle = _get(ctx, "_playlist_shuffle_start")
    solicitar_aba_ativa = _get(ctx, "solicitar_aba_ativa")
    fechar_programa = _get(ctx, "fechar_programa")
    APPS_MAP = _get(ctx, "APPS_MAP")
    add_to_playlist = _get(ctx, "ADD_TO_PLAYLIST")
    set_ultima_playlist = _get(ctx, "set_ultima_playlist")
    ativar_tela_cheia_robusta = _get(ctx, "ativar_tela_cheia_robusta")
    is_valid_url = _get(ctx, "is_valid_url")
    formatar_url_ou_busca = _get(ctx, "formatar_url_ou_busca")
    listar_playlists = _get(ctx, "_listar_playlists_salvas")
    autorizar_acao_pratica = _get(ctx, "_autorizar_acao_pratica")
    texto_base = str(_get(ctx, "texto") or comando or a).strip()

    if c == "YOUTUBE":
        if callable(autorizar_acao_pratica):
            decisao = autorizar_acao_pratica("MUSIC_SEARCH", texto_base, origem="conteudo")
            if not bool(decisao.get("permitido")):
                print(f"🎵 [AUTONOMIA] YOUTUBE bloqueado: {decisao.get('motivo')}.")
                return False
        if a and callable(validar_e_enviar_comando):
            validar_e_enviar_comando("youtube_search", {"query": a})
            return True
        return False

    if c in {"YT_VOLUME", "SET_VOLUME"}:
        if not callable(ajustar_volume_sistema):
            return False
        try:
            m_vol = re.search(r"\d+", a)
            nivel = int(m_vol.group()) if m_vol else 50
            ajustar_volume_sistema(nivel)
            print(f"🔊 Volume do sistema ajustado para {nivel}%")
            return True
        except Exception as e:
            print(f"❌ Erro ao ajustar volume do sistema: {e}")
            return False

    if c == "OPEN_SITE":
        if not a or not callable(enviar_comando_chrome):
            return False
        url = a
        if callable(is_valid_url) and callable(formatar_url_ou_busca) and not is_valid_url(url):
            url = formatar_url_ou_busca(url, prefer_com_br=False)
        enviar_comando_chrome("open_url", {"url": url})
        return True

    if c == "CLOSE_TAB":
        if isinstance(APPS_MAP, dict) and a:
            alvo_norm = a.lower().strip()
            for app in sorted(APPS_MAP.keys(), key=len, reverse=True):
                if alvo_norm == app or app in alvo_norm:
                    if callable(fechar_programa):
                        fechar_programa(APPS_MAP.get(app, a))
                        return True
                    break
        if not callable(enviar_comando_chrome):
            return False
        target = str(_get(ctx, "arg") or "").strip()
        if target and len(target) > 2:
            enviar_comando_chrome("close_tab", {"title": target})
        else:
            enviar_comando_chrome("close_current_tab", {})
        return True

    if c in {"YT_PLAY", "YT_PAUSE"}:
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
        print("⏸️ [MÍDIA] Comando Play/Pause enviado nativamente (ctypes)!")
        return True

    if c == "YT_NEXT":
        ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 2, 0)
        print("⏭️ [MÍDIA] Comando Próxima Música enviado nativamente!")
        return True

    if c == "YT_REPLAY":
        ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
        print("⏮️ [MÍDIA] Comando Música Anterior enviado nativamente!")
        return True

    if c == "LISTAR_PLAYLISTS" and callable(falar) and callable(listar_playlists):
        falar(listar_playlists(), "calma", 1)
        return True

    if c == "TOCAR_PLAYLIST" and callable(play_playlist) and callable(falar):
        nome_playlist = a.strip("\"'")
        if not nome_playlist:
            falar("Qual playlist você quer que eu toque, Pedro?", "debochada", 2)
            return True
        if callable(autorizar_acao_pratica):
            decisao = autorizar_acao_pratica("TOCAR_PLAYLIST", texto_base, origem="conteudo")
            if not bool(decisao.get("permitido")):
                print(f"🎵 [AUTONOMIA] TOCAR_PLAYLIST bloqueado: {decisao.get('motivo')}.")
                return False
        ok = play_playlist(nome_playlist)
        if ok:
            falar(f"Abrindo sua playlist {nome_playlist}. Prepare os ouvidos!", "calma", 1)
        else:
            falar(f"Não encontrei a playlist {nome_playlist}. Tem certeza que ela existe?", "debochada", 2)
        return True

    if c == "TOCAR_PLAYLIST_SHUFFLE" and callable(playlist_shuffle) and callable(validar_e_enviar_comando) and callable(falar):
        nome_playlist = a.strip("\"'")
        if not nome_playlist:
            falar("Qual playlist você quer que eu toque em modo aleatório, Pedro?", "debochada", 2)
            return True
        if callable(autorizar_acao_pratica):
            decisao = autorizar_acao_pratica("TOCAR_PLAYLIST_SHUFFLE", texto_base, origem="conteudo")
            if not bool(decisao.get("permitido")):
                print(f"🎵 [AUTONOMIA] TOCAR_PLAYLIST_SHUFFLE bloqueado: {decisao.get('motivo')}.")
                return False
        info = playlist_shuffle(nome_playlist)
        if info and info.get("url"):
            url = str(info.get("url") or "")
            validar_e_enviar_comando("youtube_play", {"url": url})
            falar(f"Misturando sua playlist {nome_playlist}. Surpresa a cada música!", "calma", 1)
        else:
            falar(f"Não encontrei a playlist {nome_playlist} ou ela está vazia. Que tal adicionar umas músicas?", "debochada", 2)
        return True

    if c == "ADICIONAR_A_PLAYLIST" and callable(solicitar_aba_ativa) and callable(add_to_playlist) and callable(falar):
        match = re.search(r"ADICIONAR_A_PLAYLIST\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]\)", comando, re.IGNORECASE)
        if not match:
            print(f"⚠️ [ADICIONAR_A_PLAYLIST] Formato inválido: {comando}")
            return True
        playlist_nome = match.group(1).strip()
        titulo_musica = match.group(2).strip()
        info = solicitar_aba_ativa(timeout_s=3.0)
        url_atual = str((info or {}).get("url") or "").strip()
        titulo_real = str((info or {}).get("title") or titulo_musica).strip()
        canal = str((info or {}).get("canal") or "").strip()
        if not url_atual or "youtube.com" not in url_atual:
            falar("Pedro, não tem vídeo do YouTube aberto. Abre a música primeiro.", "irritada", 2)
            return True
        sucesso = add_to_playlist(playlist_nome, url_atual, titulo_real, canal)
        if sucesso:
            falar(f"Beleza, guardei '{titulo_real}' na playlist {playlist_nome}.", "debochada", 2)
            if callable(set_ultima_playlist):
                set_ultima_playlist(playlist_nome)
        else:
            falar("Ih, deu erro ao salvar. Verifica se tá no YouTube.", "calma", 1)
        return True

    if c == "CLICK" and callable(enviar_comando_chrome):
        selector = a
        if (selector.startswith("'") and selector.endswith("'")) or (selector.startswith('"') and selector.endswith('"')):
            selector = selector[1:-1]
        if selector.lower().startswith("js:"):
            print("🛑 [SISTEMA] CLICK com JavaScript recusado por segurança.")
            if callable(falar):
                falar("Não executo JavaScript arbitrário na página. Posso clicar em um elemento identificado.", "calma", 1)
        else:
            enviar_comando_chrome("click", {"selector": selector})
        return True

    if c == "TYPE" and callable(enviar_comando_chrome):
        pattern = r"'(.*?)'|\"(.*?)\""
        matches = re.findall(pattern, a, re.DOTALL)
        args = [m[0] if m[0] else m[1] for m in matches]
        if len(args) >= 2:
            enviar_comando_chrome("type", {"selector": args[0], "text": args[1]})
        else:
            parts = a.split(",", 1)
            if len(parts) == 2:
                enviar_comando_chrome("type", {"selector": parts[0].strip(), "text": parts[1].strip()})
        return True

    if c == "PRESS" and callable(enviar_comando_chrome):
        key = a.strip("\'\"").lower()
        print(f"⌨️ [SISTEMA] Enviando tecla: {key}")
        enviar_comando_chrome("press", {"key": key})
        return True

    if c == "CLOSE_SPECIFIC_TAB" and callable(enviar_comando_chrome):
        termo = a.strip("'\"")
        print(f"❌ [SISTEMA] Fechando aba específica: {termo}")
        enviar_comando_chrome("close_tab", {"title": termo})
        return True

    if "TELA_CHEIA" in c_upper or "FULLSCREEN" in c_upper:
        app_alvo = a.strip(' "\'') if a else "opera"
        if callable(ativar_tela_cheia_robusta):
            sucesso = ativar_tela_cheia_robusta(app_alvo)
            if callable(falar):
                if sucesso:
                    falar(f"{app_alvo.title()} em tela cheia agora, Pedro.", "debochada", 2)
                else:
                    falar(f"Não consegui colocar o {app_alvo} em tela cheia.", "irritada", 2)
            return True

    return False
