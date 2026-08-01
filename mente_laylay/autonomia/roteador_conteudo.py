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

    navegador_operacoes = _get(ctx, "_registro_navegador_operacoes_runtime")
    ajustar_volume_sistema = _get(ctx, "ajustar_volume_sistema")
    falar = _get(ctx, "falar_com_lipsync")
    musica_operacoes = _get(ctx, "_registro_musica_operacoes_runtime")
    fechar_programa = _get(ctx, "fechar_programa")
    APPS_MAP = _get(ctx, "APPS_MAP")
    ativar_tela_cheia_robusta = _get(ctx, "ativar_tela_cheia_robusta")
    is_valid_url = _get(ctx, "is_valid_url")
    formatar_url_ou_busca = _get(ctx, "formatar_url_ou_busca")
    musica_leitura = _get(ctx, "_registro_musica_leitura_runtime")
    autorizar_acao_pratica = _get(ctx, "_autorizar_acao_pratica")
    texto_base = str(_get(ctx, "texto") or comando or a).strip()

    if c == "YOUTUBE":
        if callable(autorizar_acao_pratica):
            decisao = autorizar_acao_pratica("MUSIC_SEARCH", texto_base, origem="conteudo")
            if not bool(decisao.get("permitido")):
                print(f"🎵 [AUTONOMIA] YOUTUBE bloqueado: {decisao.get('motivo')}.")
                return False
        if a and navegador_operacoes is not None:
            navegador_operacoes.pesquisar_youtube(a)
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
        if not a or navegador_operacoes is None:
            return False
        url = a
        if callable(is_valid_url) and callable(formatar_url_ou_busca) and not is_valid_url(url):
            url = formatar_url_ou_busca(url, prefer_com_br=False)
        navegador_operacoes.abrir_url(url)
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
        if navegador_operacoes is None:
            return False
        target = str(_get(ctx, "arg") or "").strip()
        if target and len(target) > 2:
            navegador_operacoes.fechar_aba(target)
        else:
            navegador_operacoes.fechar_aba_atual()
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

    if c == "LISTAR_PLAYLISTS" and callable(falar) and musica_leitura is not None:
        falar(musica_leitura.listar_usuario(), "calma", 1)
        return True

    if c == "TOCAR_PLAYLIST" and musica_operacoes is not None and callable(falar):
        nome_playlist = a.strip("\"'")
        if not nome_playlist:
            falar("Qual playlist você quer que eu toque?", "debochada", 2)
            return True
        if callable(autorizar_acao_pratica):
            decisao = autorizar_acao_pratica("TOCAR_PLAYLIST", texto_base, origem="conteudo")
            if not bool(decisao.get("permitido")):
                print(f"🎵 [AUTONOMIA] TOCAR_PLAYLIST bloqueado: {decisao.get('motivo')}.")
                return False
        ok = musica_operacoes.tocar_playlist(nome_playlist)
        if ok:
            falar(f"Abrindo sua playlist {nome_playlist}. Prepare os ouvidos!", "calma", 1)
        else:
            falar(f"Não encontrei a playlist {nome_playlist}. Tem certeza que ela existe?", "debochada", 2)
        return True

    if c == "TOCAR_PLAYLIST_SHUFFLE" and musica_operacoes is not None and navegador_operacoes is not None and callable(falar):
        nome_playlist = a.strip("\"'")
        if not nome_playlist:
            falar("Qual playlist você quer que eu toque em modo aleatório?", "debochada", 2)
            return True
        if callable(autorizar_acao_pratica):
            decisao = autorizar_acao_pratica("TOCAR_PLAYLIST_SHUFFLE", texto_base, origem="conteudo")
            if not bool(decisao.get("permitido")):
                print(f"🎵 [AUTONOMIA] TOCAR_PLAYLIST_SHUFFLE bloqueado: {decisao.get('motivo')}.")
                return False
        info = musica_operacoes.preparar_shuffle(nome_playlist)
        if info and info.get("url"):
            url = str(info.get("url") or "")
            navegador_operacoes.tocar_youtube(url)
            musica_operacoes.definir_ultima_url(url)
            falar(f"Misturando sua playlist {nome_playlist}. Surpresa a cada música!", "calma", 1)
        else:
            falar(f"Não encontrei a playlist {nome_playlist} ou ela está vazia. Que tal adicionar umas músicas?", "debochada", 2)
        return True

    if c == "ADICIONAR_A_PLAYLIST" and musica_operacoes is not None and callable(falar):
        match = re.search(r"ADICIONAR_A_PLAYLIST\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]\)", comando, re.IGNORECASE)
        if not match:
            print(f"⚠️ [ADICIONAR_A_PLAYLIST] Formato inválido: {comando}")
            return True
        playlist_nome = match.group(1).strip()
        titulo_musica = match.group(2).strip()
        info = musica_operacoes.faixa_atual()
        url_atual = str((info or {}).get("url") or "").strip()
        titulo_real = str((info or {}).get("title") or titulo_musica).strip()
        canal = str((info or {}).get("canal") or "").strip()
        if not url_atual or "youtube.com" not in url_atual:
            falar("Não tem vídeo do YouTube aberto. Abre a música primeiro.", "irritada", 2)
            return True
        sucesso = musica_operacoes.adicionar_faixa(
            playlist_nome, url_atual, titulo_real, canal
        )
        if sucesso:
            falar(f"Beleza, guardei '{titulo_real}' na playlist {playlist_nome}.", "debochada", 2)
            musica_operacoes.definir_ultima_playlist(playlist_nome)
        else:
            falar("Ih, deu erro ao salvar. Verifica se tá no YouTube.", "calma", 1)
        return True

    if c == "CLICK" and navegador_operacoes is not None:
        selector = a
        if (selector.startswith("'") and selector.endswith("'")) or (selector.startswith('"') and selector.endswith('"')):
            selector = selector[1:-1]
        if selector.lower().startswith("js:"):
            print("🛑 [SISTEMA] CLICK com JavaScript recusado por segurança.")
            if callable(falar):
                falar("Não executo JavaScript arbitrário na página. Posso clicar em um elemento identificado.", "calma", 1)
        else:
            navegador_operacoes.clicar(selector)
        return True

    if c == "TYPE" and navegador_operacoes is not None:
        pattern = r"'(.*?)'|\"(.*?)\""
        matches = re.findall(pattern, a, re.DOTALL)
        args = [m[0] if m[0] else m[1] for m in matches]
        if len(args) >= 2:
            navegador_operacoes.digitar(args[0], args[1])
        else:
            parts = a.split(",", 1)
            if len(parts) == 2:
                navegador_operacoes.digitar(parts[0].strip(), parts[1].strip())
        return True

    if c == "PRESS" and navegador_operacoes is not None:
        key = a.strip("\'\"").lower()
        print(f"⌨️ [SISTEMA] Enviando tecla: {key}")
        navegador_operacoes.pressionar(key)
        return True

    if c == "CLOSE_SPECIFIC_TAB" and navegador_operacoes is not None:
        termo = a.strip("'\"")
        print(f"❌ [SISTEMA] Fechando aba específica: {termo}")
        navegador_operacoes.fechar_aba(termo)
        return True

    if "TELA_CHEIA" in c_upper or "FULLSCREEN" in c_upper:
        app_alvo = a.strip(' "\'') if a else "opera"
        if callable(ativar_tela_cheia_robusta):
            sucesso = ativar_tela_cheia_robusta(app_alvo)
            if callable(falar):
                if sucesso:
                    falar(f"{app_alvo.title()} em tela cheia agora.", "debochada", 2)
                else:
                    falar(f"Não consegui colocar o {app_alvo} em tela cheia.", "irritada", 2)
            return True

    return False
