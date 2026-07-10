"""Runtime de playlists da Laylay.

Este modulo concentra operacoes de arquivo/cache de playlist, mas recebe os
callbacks do cerebro principal para continuar conectado a mesma mente.
"""

from __future__ import annotations

import random
from typing import Any, Callable, Dict

from mente_laylay.memoria_mental.playlist_mental import (
    add_to_playlist_url as add_to_playlist_url_mental,
    detectar_playlist_nome_direto,
    ensure_playlists_file,
    limpar_nome_playlist,
    list_playlist_urls,
    listar_playlists_salvas,
    playlist_item_at,
    playlist_item_label,
    playlist_item_match,
    playlist_len,
    playlist_primeira_url,
    playlists_load,
    playlists_save,
    resolver_nome_playlist_contextual,
    yt_clean_title,
    yt_clean_url,
)


class PlaylistRuntime:
    def __init__(
        self,
        *,
        state_file: str,
        legacy_file: str,
        cache: Dict[str, Any],
        ultima_playlist_getter: Callable[[], str],
        ultima_playlist_setter: Callable[[str], None] | None = None,
        playlist_state: Dict[str, Any] | None = None,
        indice_setter: Callable[[int], None] | None = None,
        youtube_play: Callable[[str], Any] | None = None,
        solicitar_aba_ativa: Callable[..., dict] | None = None,
        log: Callable[[str], None] | None = None,
    ) -> None:
        self.state_file = state_file
        self.legacy_file = legacy_file
        self.cache = cache
        self.ultima_playlist_getter = ultima_playlist_getter
        self.ultima_playlist_setter = ultima_playlist_setter
        self.playlist_state = playlist_state if isinstance(playlist_state, dict) else {}
        self.indice_setter = indice_setter
        self.youtube_play = youtube_play
        self.solicitar_aba_ativa = solicitar_aba_ativa
        self.log = log or print

    def _ultima_playlist(self) -> str:
        try:
            return str(self.ultima_playlist_getter() or "").strip()
        except Exception:
            return ""

    def _set_ultima_playlist(self, valor: str) -> None:
        if callable(self.ultima_playlist_setter):
            try:
                self.ultima_playlist_setter(valor)
            except Exception:
                pass

    def _set_indice(self, valor: int) -> None:
        if callable(self.indice_setter):
            try:
                self.indice_setter(int(valor or 0))
            except Exception:
                pass

    def _item_info(self, item: Any) -> dict:
        if isinstance(item, dict):
            url = str(item.get("url") or "")
            titulo = yt_clean_title(str(item.get("titulo") or "")) or url
            canal = str(item.get("canal") or "")
        else:
            url = str(item or "")
            titulo = url
            canal = ""
        return {"url": url, "titulo": titulo, "canal": canal}

    def _abrir_youtube_item(self, item: Any, *, prefixo_log: str = "Abrindo") -> bool:
        info = self._item_info(item)
        url = str(info.get("url") or "").strip()
        if not url:
            return False
        self.log(f"[PLAYLIST] {prefixo_log} (Strong Reuse): {info.get('titulo') or url} | Canal: {info.get('canal') or ''}")
        if callable(self.youtube_play):
            try:
                retorno = self.youtube_play(url)
            except Exception as exc:
                self.log(f"⚠️ [PLAYLIST:EXECUCAO] falha ao enviar faixa: {type(exc).__name__}: {exc}")
                return False
            if retorno is False:
                self.log("⚠️ [PLAYLIST:EXECUCAO] navegador recusou o comando youtube_play")
                return False
        self.playlist_state["last_url"] = url
        self.log(f"✅ [PLAYLIST:EXECUCAO] faixa enviada | playlist={self.playlist_state.get('name') or '-'}")
        return True

    def _limpar_estado_reproducao(self) -> None:
        self.playlist_state["name"] = ""
        self.playlist_state["index"] = 0
        self._set_indice(0)
        self.playlist_state.pop("shuffle", None)
        self.playlist_state.pop("shuffle_queue", None)
        self.playlist_state.pop("shuffle_index", None)

    def _sync_cache(self, data: Dict[str, Any] | None) -> Dict[str, Any]:
        data = data if isinstance(data, dict) else {}
        try:
            self.cache.clear()
            self.cache.update(data)
        except Exception:
            pass
        return self.cache

    def load(self) -> Dict[str, Any]:
        data = playlists_load(self.state_file, self.legacy_file)
        return self._sync_cache(data)

    def save(self, data: Dict[str, Any]) -> bool:
        ok = playlists_save(self.state_file, data or {})
        if ok:
            self._sync_cache(data or {})
        return bool(ok)

    def ensure_file(self) -> bool:
        return bool(ensure_playlists_file(self.state_file, self.legacy_file))

    def resolver_nome(self, nome: str) -> str:
        data = self.cache if isinstance(self.cache, dict) and self.cache else self.load()
        return resolver_nome_playlist_contextual(nome, data, self._ultima_playlist())

    def detectar_nome_direto(
        self,
        texto: str,
        *,
        normalizar_texto_cb: Callable[[str], str] | None = None,
    ) -> str:
        data = self.cache if isinstance(self.cache, dict) and self.cache else self.load()
        return detectar_playlist_nome_direto(
            texto,
            data,
            normalizar_texto_cb=normalizar_texto_cb,
        )

    def list_content(self, nome_playlist: str) -> dict:
        nm = self.resolver_nome(nome_playlist or "")
        if not nm:
            return {"ok": False, "error": "missing_name", "name": "", "total": 0, "last_titles": []}
        data = self.load()
        lst = data.get(nm)
        if not isinstance(lst, list):
            lst = []
        titulos = []
        for item in lst:
            if isinstance(item, dict):
                titulo = str(item.get("titulo") or "").strip()
                if titulo:
                    titulos.append(yt_clean_title(titulo) or titulo)
        return {"ok": True, "name": nm, "total": len(lst), "last_titles": [t for t in titulos[-3:] if t]}

    def list_urls(self, name: str) -> list:
        return list_playlist_urls(name, self.load())

    def listar_salvas(self) -> str:
        return listar_playlists_salvas(self.load())

    def primeira_url(self, nome: str) -> str | None:
        return playlist_primeira_url(nome, self.load())

    def item_at(self, nome: str, idx: int) -> dict | None:
        return playlist_item_at(nome, idx, self.load())

    def len(self, nome: str) -> int:
        return playlist_len(nome, self.load())

    def formatar_para_prompt(self) -> str:
        data = self.cache if isinstance(self.cache, dict) and self.cache else self.load()
        if not data:
            return "Nenhuma playlist salva ainda."
        nomes = sorted(str(nome) for nome in data.keys() if str(nome or "").strip())
        if not nomes:
            return "Nenhuma playlist salva ainda."
        return "Playlists salvas: " + ", ".join([f"'{n}'" for n in nomes]) + "."

    def add_url(self, playlist_name: str, url: str, title: str = "", canal: str = "") -> dict:
        data = self.load()
        res = add_to_playlist_url_mental(
            playlist_name,
            url,
            title,
            canal,
            state_file=self.state_file,
            legacy_file=self.legacy_file,
            data=data,
            ultima_playlist=self._ultima_playlist(),
        )
        try:
            name = self.resolver_nome(playlist_name or "")
            link = yt_clean_url(str(url or ""))
            if isinstance(res, dict) and res.get("ok"):
                self.log(f"[PLAYLIST] Adicionando URL {link} na chave {name}")
                self.log(f"[PLAYLIST] Sucesso: {yt_clean_title(title) or link} salvo em {name}")
                self._sync_cache(data)
        except Exception:
            pass
        return res if isinstance(res, dict) else {"ok": bool(res)}

    def add_from_active_tab(self, playlist_name: str) -> bool:
        name = str(playlist_name or "").strip().lower()
        if not name or not callable(self.solicitar_aba_ativa):
            return False
        info = self.solicitar_aba_ativa(timeout_s=2.0)
        url = str(info.get("url") or "")
        title = str(info.get("title") or "")
        canal = str(info.get("canal") or "")
        res = self.add_url(name, url, title, canal)
        return bool(isinstance(res, dict) and res.get("ok"))

    def add_and_verify(self, nome_playlist: str, url: str, titulo: str, canal: str = "") -> bool:
        name = self.resolver_nome(nome_playlist)
        if not name:
            return False
        link = str(url or "").strip()
        if not link:
            return False
        musica = yt_clean_title(str(titulo or "")) or link
        self.log(f"[DISK] Escrevendo {musica} em {self.state_file}...")
        res = self.add_url(name, link, str(titulo or ""), str(canal or ""))
        if not (isinstance(res, dict) and res.get("ok")):
            return False
        data = self.load()
        lst = data.get(name)
        if not isinstance(lst, list):
            return False
        target = yt_clean_url(link)
        for item in reversed(lst[-10:]):
            if isinstance(item, dict):
                item_url = str(item.get("url") or "").strip()
            else:
                item_url = str(item or "").strip()
            if item_url and yt_clean_url(item_url) == target:
                return True
        return False

    def delete(self, nome: str) -> bool:
        pl = self.resolver_nome(nome)
        if not pl:
            return False
        data = self.load()
        if pl not in data:
            return False
        try:
            data.pop(pl, None)
        except Exception:
            return False
        return self.save(data)

    def mover_item(
        self,
        origem: str,
        destino: str,
        musica: str = "",
        *,
        normalizar_texto_cb: Callable[[str], str] | None = None,
    ) -> dict:
        data = self.load()
        origem_nm = limpar_nome_playlist(origem)
        destino_nm = limpar_nome_playlist(destino)
        musica_txt = str(musica or "").strip()
        if not origem_nm or not destino_nm:
            return {"ok": False, "error": "missing_playlist", "titulo": ""}

        origem_lst = data.get(origem_nm)
        if not isinstance(origem_lst, list) or not origem_lst:
            return {
                "ok": False,
                "error": "source_empty",
                "titulo": "",
                "origem": origem_nm,
                "destino": destino_nm,
            }

        normalizar = normalizar_texto_cb if callable(normalizar_texto_cb) else str
        referencia_generica = normalizar(musica_txt) in {
            "ela",
            "essa",
            "isso",
            "musica",
            "música",
        }
        idx = -1
        if musica_txt and not referencia_generica:
            for i, item in enumerate(origem_lst):
                if playlist_item_match(
                    item,
                    musica_txt,
                    normalizar_texto_cb=normalizar_texto_cb,
                ):
                    idx = i
                    break
        if idx < 0:
            idx = len(origem_lst) - 1

        item = origem_lst.pop(idx)
        destino_lst = data.setdefault(destino_nm, [])
        if not isinstance(destino_lst, list):
            destino_lst = []
            data[destino_nm] = destino_lst

        if isinstance(item, dict):
            item_url = yt_clean_url(str(item.get("url") or ""))
        else:
            item_url = yt_clean_url(str(item or ""))
        ja_existe = False
        if item_url:
            for existente in destino_lst:
                if isinstance(existente, dict):
                    existente_url = yt_clean_url(str(existente.get("url") or ""))
                else:
                    existente_url = yt_clean_url(str(existente or ""))
                if existente_url == item_url:
                    ja_existe = True
                    break
        if not ja_existe:
            destino_lst.append(item)
        if not origem_lst:
            data[origem_nm] = []
        self.save(data)
        return {
            "ok": True,
            "duplicated": ja_existe,
            "titulo": playlist_item_label(item),
            "origem": origem_nm,
            "destino": destino_nm,
        }

    def shuffle_start(self, nome: str) -> dict | None:
        pl = self.resolver_nome(nome)
        if not pl:
            return None
        data = self.load()
        lst = data.get(pl)
        if not isinstance(lst, list) or not lst:
            return None
        queue = list(lst)
        random.shuffle(queue)
        self._set_ultima_playlist(pl)
        self.playlist_state["name"] = pl
        self.playlist_state["user_intervened"] = False
        self.playlist_state["shuffle"] = True
        self.playlist_state["shuffle_queue"] = queue
        self.playlist_state["shuffle_index"] = 0
        self._set_indice(0)
        first = queue[0]
        info = self._item_info(first)
        info["len"] = len(queue)
        return info

    def avancar_proxima(self) -> bool:
        nm = str(self.playlist_state.get("name") or "")
        if not nm:
            return False
        if self.playlist_state.get("shuffle") and isinstance(self.playlist_state.get("shuffle_queue"), list):
            queue = self.playlist_state.get("shuffle_queue") or []
            idx = int(self.playlist_state.get("shuffle_index") or 0) + 1
            if idx >= len(queue):
                self.log(f"🎵 Playlist '{nm}' terminou")
                self._limpar_estado_reproducao()
                return False
            self.playlist_state["shuffle_index"] = idx
            self._set_indice(idx)
            return self._abrir_youtube_item(queue[idx], prefixo_log="Abrindo")

        data = self.load()
        lst = data.get(nm)
        if not isinstance(lst, list) or not lst:
            return False
        idx = int(self.playlist_state.get("index") or 0) + 1
        if idx >= len(lst):
            self.log(f"🎵 Playlist '{nm}' terminou")
            self.playlist_state["name"] = ""
            self.playlist_state["index"] = 0
            self._set_indice(0)
            return False
        self.playlist_state["index"] = idx
        self._set_indice(idx)
        return self._abrir_youtube_item(lst[idx], prefixo_log="Abrindo")

    def voltar_anterior(self) -> bool:
        nm = str(self.playlist_state.get("name") or "")
        if not nm:
            return False
        if self.playlist_state.get("shuffle") and isinstance(self.playlist_state.get("shuffle_queue"), list):
            queue = self.playlist_state.get("shuffle_queue") or []
            idx_atual = int(self.playlist_state.get("shuffle_index") or 0)
            if idx_atual <= 0 or idx_atual >= len(queue):
                return False
            idx = idx_atual - 1
            self.playlist_state["shuffle_index"] = idx
            self._set_indice(idx)
            return self._abrir_youtube_item(queue[idx], prefixo_log="Voltando")

        data = self.load()
        lst = data.get(nm)
        if not isinstance(lst, list) or not lst:
            return False
        idx_atual = int(self.playlist_state.get("index") or 0)
        if idx_atual <= 0 or idx_atual >= len(lst):
            return False
        idx = idx_atual - 1
        self.playlist_state["index"] = idx
        self._set_indice(idx)
        return self._abrir_youtube_item(lst[idx], prefixo_log="Voltando")

    def play(self, name: str) -> bool:
        nm = self.resolver_nome(name)
        self.log(f"🎵 [PLAYLIST:PLAY] pedido={name!r} resolvida={nm!r}")
        if not nm:
            self.log("⚠️ [PLAYLIST:PLAY] nome não corresponde a uma playlist salva")
            return False
        data = self.load()
        lst = data.get(nm)
        if not isinstance(lst, list) or not lst:
            self.log(f"⚠️ Playlist vazia ou inexistente: {nm}")
            return False
        self.log(f"🎵 [PLAYLIST:PLAY] {nm} possui {len(lst)} faixa(s); abrindo a primeira")
        self._set_ultima_playlist(nm)
        self.playlist_state["name"] = nm
        self.playlist_state["index"] = 0
        self._set_indice(0)
        self.playlist_state["user_intervened"] = False
        self.playlist_state["last_url"] = ""
        self.playlist_state.pop("shuffle", None)
        self.playlist_state.pop("shuffle_queue", None)
        self.playlist_state.pop("shuffle_index", None)
        return self._abrir_youtube_item(lst[0], prefixo_log="Abrindo")


def criar_playlist_runtime(**kwargs: Any) -> PlaylistRuntime:
    return PlaylistRuntime(**kwargs)
