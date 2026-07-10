"""Falas da Laylay para eventos de playlist."""

from __future__ import annotations

from mente_laylay.memoria_mental.playlist_mental import limpar_nome_playlist, yt_clean_title


def fala_playlist_sucesso(title: str, playlist_nome: str, created: bool) -> str:
    pl = limpar_nome_playlist(playlist_nome)
    tit = yt_clean_title(title) or "esse som"
    if created:
        return f"Beleza, Pedro. Criei a playlist {pl} e já guardei o link."
    return f"Pronto, {tit} tá lá na playlist {pl}. Só não me pede pra arrumar a bagunça desse arquivo."


def fala_playlist_duplicado(title: str, playlist_nome: str) -> str:
    pl = limpar_nome_playlist(playlist_nome)
    tit = yt_clean_title(title) or "esse som"
    return f"Essa já tá lá, Pedro. Quer ouvir {tit} o dia inteiro ou tá com saudade do repeat?"


def fala_playlist_duplicado_meta(title: str, playlist_nome: str, other_channel: bool) -> str:
    pl = limpar_nome_playlist(playlist_nome)
    tit = yt_clean_title(title) or "essa música"
    if other_channel:
        return f"Pedro, você já tem {tit} na playlist {pl}, só que de outro canal. Não vou salvar de novo pra não virar bagunça."
    return f"Essa música já tá guardada na playlist {pl}, só que o link é outro. Vou manter o que já tava lá pra poupar espaço."
