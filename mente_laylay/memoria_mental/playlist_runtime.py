"""Runtime de playlists da Laylay.

Este modulo concentra operacoes de arquivo/cache de playlist, mas recebe os
callbacks do cerebro principal para continuar conectado a mesma mente.
"""

from __future__ import annotations

import random
import re
import threading
import unicodedata
from copy import deepcopy
from typing import Any, Callable, Dict

from mente_laylay.memoria_mental.playlist_mental import (
    add_to_playlist_url as add_to_playlist_url_mental,
    detectar_playlist_nome_direto,
    extrair_nome_playlist,
    limpar_nome_playlist,
    listar_playlists_salvas,
    playlist_item_at,
    playlist_item_label,
    playlist_item_match,
    playlist_len,
    playlist_primeira_url,
    playlists_load,
    playlists_save,
    pedido_lista_geral_playlist,
    playlist_nome_explicito_na_frase,
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
        youtube_play: Callable[[str], Any] | None = None,
        solicitar_aba_ativa: Callable[..., dict] | None = None,
        normalizar_texto: Callable[[str], str] | None = None,
        normalizar_texto_com_apelidos: Callable[[str], str] | None = None,
        sincronizar_playlists_laylay: Callable[[], Any] | None = None,
        log: Callable[[str], None] | None = None,
    ) -> None:
        self.state_file = state_file
        self.legacy_file = legacy_file
        self.cache = cache
        self.ultima_playlist_getter = ultima_playlist_getter
        self.ultima_playlist_setter = ultima_playlist_setter
        self.playlist_state = playlist_state if isinstance(playlist_state, dict) else {}
        self.youtube_play = youtube_play
        self.solicitar_aba_ativa = solicitar_aba_ativa
        self.normalizar_texto = normalizar_texto
        self.normalizar_texto_com_apelidos = normalizar_texto_com_apelidos
        self.sincronizar_playlists_laylay = sincronizar_playlists_laylay
        self.log = log or print
        self._state_lock = threading.RLock()

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
        confirmado = None
        status_entrega = ""
        if callable(self.youtube_play):
            try:
                tab_id = self.playlist_state.get("tab_id")
                try:
                    retorno = self.youtube_play(url, target_tab_id=tab_id if isinstance(tab_id, int) else None)
                except TypeError:
                    retorno = self.youtube_play(url)
            except Exception as exc:
                self.log(f"⚠️ [PLAYLIST:EXECUCAO] falha ao enviar faixa: {type(exc).__name__}: {exc}")
                return False
            if isinstance(retorno, dict):
                status_entrega = str(retorno.get("status") or "").strip()
                confirmado = retorno.get("confirmado")
                tab = retorno.get("tab")
                if isinstance(tab, dict) and isinstance(tab.get("id"), int):
                    self.playlist_state["tab_id"] = tab["id"]
                # ``autoplay_blocked`` só é devolvido pela extensão depois de
                # a navegação terminar e o controle ``play`` ser tentado na
                # página. Portanto a faixa foi entregue à aba, embora o áudio
                # não tenha sido confirmado. Isso é evidência suficiente para
                # manter a fila ativa, mas não para afirmar que está tocando.
                entregue = bool(retorno.get("ok")) or status_entrega == "autoplay_blocked"
            else:
                entregue = retorno is not False
                confirmado = True if entregue else False
            if not entregue:
                self.log("⚠️ [PLAYLIST:EXECUCAO] navegador recusou o comando youtube_play")
                self.playlist_state["last_delivery_status"] = status_entrega or "falha_execucao"
                self.playlist_state["last_play_confirmed"] = False
                return False
        self.playlist_state["last_url"] = url
        self.playlist_state["last_delivery_status"] = status_entrega or "enviado"
        self.playlist_state["last_play_confirmed"] = confirmado is True
        if confirmado is False:
            self.log(
                "⚠️ [PLAYLIST:EXECUCAO] faixa aberta; reprodução não confirmada "
                f"| playlist={self.playlist_state.get('name') or '-'}"
            )
        else:
            self.log(f"✅ [PLAYLIST:EXECUCAO] faixa enviada | playlist={self.playlist_state.get('name') or '-'}")
        return True

    def _limpar_estado_reproducao(self) -> None:
        self.playlist_state["name"] = ""
        self.playlist_state["index"] = 0
        self.playlist_state.pop("shuffle", None)
        self.playlist_state.pop("shuffle_queue", None)
        self.playlist_state.pop("shuffle_index", None)
        self.playlist_state.pop("tab_id", None)
        self.playlist_state.pop("last_ended_event", None)
        self.playlist_state.pop("last_ended_ts", None)

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
        if not data and isinstance(self.cache, dict) and self.cache:
            self.log("⚠️ [PLAYLISTS] leitura vazia; mantendo o último cache válido")
            return self.cache
        return self._sync_cache(data)

    def catalogo_publico(self) -> list[dict[str, Any]]:
        """Retrato O(1) do catálogo já carregado, sem reler disco na UI."""
        with self._state_lock:
            dados = deepcopy(self.cache) if isinstance(self.cache, dict) else {}
        catalogo: list[dict[str, Any]] = []
        for nome in sorted(dados, key=lambda item: str(item).casefold()):
            nome_limpo = re.sub(r"\s+", " ", str(nome or "")).strip()[:80]
            itens = dados.get(nome)
            if not nome_limpo or not isinstance(itens, list):
                continue
            video_id = ""
            for item in itens:
                url = str(item.get("url") or "") if isinstance(item, dict) else str(item or "")
                encontrado = re.search(
                    r"(?:[?&]v=|youtu\.be/|/(?:shorts|embed|live)/)"
                    r"([A-Za-z0-9_-]{11})(?:[^A-Za-z0-9_-]|$)",
                    url,
                )
                if encontrado:
                    video_id = encontrado.group(1)
                    break
            catalogo.append({
                "name": nome_limpo,
                "count": len(itens),
                "artwork_video_id": video_id,
            })
        return catalogo

    def fila_publica(self) -> list[dict[str, Any]]:
        """Expõe as próximas faixas da playlist ativa, sem URLs privadas.

        A extensão observa a fila do YouTube quando ela existe. Playlists
        locais da Laylay, porém, avançam por este runtime e não precisam estar
        materializadas no painel lateral do site. Este retrato é a fonte
        canônica dessa segunda fila.
        """
        with self._state_lock:
            nome = str(self.playlist_state.get("name") or "").strip()
            if not nome:
                return []
            if (
                self.playlist_state.get("shuffle") is True
                and isinstance(self.playlist_state.get("shuffle_queue"), list)
            ):
                itens = deepcopy(self.playlist_state.get("shuffle_queue") or [])
                indice = int(self.playlist_state.get("shuffle_index") or 0)
            else:
                itens_brutos = self.cache.get(nome) if isinstance(self.cache, dict) else []
                itens = deepcopy(itens_brutos) if isinstance(itens_brutos, list) else []
                indice = int(self.playlist_state.get("index") or 0)

        fila: list[dict[str, Any]] = []
        for item in itens[max(0, indice + 1):]:
            info = self._item_info(item)
            titulo = re.sub(r"\s+", " ", str(info.get("titulo") or "")).strip()[:160]
            if not titulo:
                continue
            url = str(info.get("url") or "")
            encontrado = re.search(
                r"(?:[?&]v=|youtu\.be/|/(?:shorts|embed|live)/)"
                r"([A-Za-z0-9_-]{11})(?:[^A-Za-z0-9_-]|$)",
                url,
            )
            fila.append({
                "title": titulo,
                "channel": re.sub(
                    r"\s+", " ", str(info.get("canal") or "")
                ).strip()[:100],
                "artwork_video_id": encontrado.group(1) if encontrado else "",
            })
        return fila

    def save(self, data: Dict[str, Any]) -> bool:
        ok = playlists_save(self.state_file, data or {})
        if ok:
            self._sync_cache(data or {})
        return bool(ok)

    def resolver_nome(self, nome: str) -> str:
        data = self.load()
        return resolver_nome_playlist_contextual(nome, data, self._ultima_playlist())

    def detectar_nome_direto(
        self,
        texto: str,
        *,
        normalizar_texto_cb: Callable[[str], str] | None = None,
    ) -> str:
        data = self.load()
        return detectar_playlist_nome_direto(
            texto,
            data,
            normalizar_texto_cb=normalizar_texto_cb,
        )

    def nome_explicito_na_frase(self, texto: str) -> bool:
        return playlist_nome_explicito_na_frase(
            texto,
            normalizar_texto_cb=self.normalizar_texto_com_apelidos,
        )

    def extrair_nome(self, texto: str) -> str:
        nome = extrair_nome_playlist(
            texto,
            normalizar_texto_cb=self.normalizar_texto_com_apelidos,
        )
        self.log(f"[DEBUG] Nome extraído da playlist: {nome}")
        return nome

    def pedido_lista_geral(self, texto_original: str, params: dict) -> bool:
        return pedido_lista_geral_playlist(
            texto_original,
            params,
            normalizar_texto_cb=self.normalizar_texto_com_apelidos,
        )

    def detectar_nome_direto_contextual(self, texto: str) -> str:
        return self.detectar_nome_direto(
            texto,
            normalizar_texto_cb=self.normalizar_texto_com_apelidos,
        )

    def mover_item_contextual(
        self,
        origem: str,
        destino: str,
        musica: str = "",
    ) -> dict:
        return self.mover_item(
            origem,
            destino,
            musica,
            normalizar_texto_cb=self.normalizar_texto,
        )

    def carregar_para_memoria(self) -> Dict[str, Any]:
        playlists = self.load()
        if callable(self.sincronizar_playlists_laylay):
            self.sincronizar_playlists_laylay()
        self.log(f"🎵 [PLAYLISTS] Playlists carregadas: {list(playlists.keys())}")
        return playlists

    def list_content(self, nome_playlist: str) -> dict:
        nm = self.resolver_nome(nome_playlist or "")
        if not nm:
            return {"ok": False, "error": "missing_name", "name": "", "total": 0, "last_titles": []}
        data = self.load()
        if nm not in data:
            return {
                "ok": False,
                "error": "playlist_not_found",
                "name": nm,
                "total": 0,
                "last_titles": [],
            }
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
        return "Playlists salvas: " + ", ".join(
            f"'{nome}' ({len(data.get(nome) or [])})" for nome in nomes
        ) + "."

    def retrato_para_mente(self, texto: str = "") -> dict[str, Any]:
        """Entrega dados musicais úteis sem expor URLs ou o JSON bruto."""
        data = self.load()
        playlists = [
            {"nome": str(nome), "total": len(itens) if isinstance(itens, list) else 0}
            for nome, itens in sorted(data.items(), key=lambda item: str(item[0]).casefold())
            if str(nome or "").strip()
        ]
        normalizado = unicodedata.normalize("NFKD", str(texto or "").casefold())
        normalizado = "".join(ch for ch in normalizado if not unicodedata.combining(ch))
        normalizado = re.sub(r"\s+", " ", normalizado).strip()
        detalhe: dict[str, Any] = {}
        for nome, itens in data.items():
            nome_norm = unicodedata.normalize("NFKD", str(nome).casefold())
            nome_norm = "".join(ch for ch in nome_norm if not unicodedata.combining(ch))
            if not nome_norm or not re.search(rf"\b{re.escape(nome_norm)}\b", normalizado):
                continue
            titulos = []
            for item in itens if isinstance(itens, list) else []:
                titulo = (
                    str(item.get("titulo") or "").strip()
                    if isinstance(item, dict) else ""
                )
                titulo = yt_clean_title(titulo)
                if titulo:
                    titulos.append(titulo)
            detalhe = {"nome": str(nome), "titulos": titulos[:8]}
            break
        return {"playlists": playlists[:30], "detalhe": detalhe}

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

    def create(self, nome_playlist: str) -> dict:
        """Cria uma playlist vazia e confirma a persistência local."""
        nome = limpar_nome_playlist(str(nome_playlist or ""))
        if not nome:
            return {"ok": False, "criada": False, "status": "alvo_ausente", "nome": ""}
        with self._state_lock:
            data = self.load()
            if nome in data:
                return {
                    "ok": isinstance(data.get(nome), list),
                    "criada": False,
                    "status": "playlist_ja_existia",
                    "nome": nome,
                }
            data[nome] = []
            if not self.save(data):
                return {
                    "ok": False,
                    "criada": False,
                    "status": "falha_persistencia",
                    "nome": nome,
                }
            confirmado = self.load()
            ok = nome in confirmado and isinstance(confirmado.get(nome), list)
            if ok:
                self._set_ultima_playlist(nome)
            return {
                "ok": ok,
                "criada": ok,
                "status": "playlist_criada" if ok else "falha_confirmacao",
                "nome": nome,
            }

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
        # A mudança só entra no cache depois que o arquivo confirma a gravação.
        # Assim uma falha de disco não cria um estado em memória diferente do
        # que será lido na próxima inicialização.
        data = deepcopy(self.load())
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
        if not self.save(data):
            return {
                "ok": False,
                "error": "save_failed",
                "titulo": playlist_item_label(item),
                "origem": origem_nm,
                "destino": destino_nm,
            }
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
        first = queue[0]
        info = self._item_info(first)
        info["len"] = len(queue)
        return info

    def avancar_proxima(self) -> bool:
        with self._state_lock:
            return self._avancar_proxima_sem_lock()

    def _avancar_proxima_sem_lock(self) -> bool:
        nm = str(self.playlist_state.get("name") or "")
        if not nm:
            self.playlist_state["last_advance_status"] = "inativa"
            return False
        if self.playlist_state.get("shuffle") and isinstance(self.playlist_state.get("shuffle_queue"), list):
            queue = self.playlist_state.get("shuffle_queue") or []
            idx = int(self.playlist_state.get("shuffle_index") or 0) + 1
            if idx >= len(queue):
                self.log(f"🎵 Playlist '{nm}' terminou")
                self._limpar_estado_reproducao()
                self.playlist_state["last_advance_status"] = "fim"
                return False
            idx_anterior = int(self.playlist_state.get("shuffle_index") or 0)
            self.playlist_state["shuffle_index"] = idx
            ok = self._abrir_youtube_item(queue[idx], prefixo_log="Abrindo")
            if not ok:
                self.playlist_state["shuffle_index"] = idx_anterior
                self.playlist_state["last_advance_status"] = "falha_execucao"
                return False
            self.playlist_state["last_advance_status"] = (
                "ok" if self.playlist_state.get("last_play_confirmed") is not False
                else "enviado_sem_confirmacao"
            )
            return True

        data = self.load()
        lst = data.get(nm)
        if not isinstance(lst, list) or not lst:
            self.playlist_state["last_advance_status"] = "playlist_invalida"
            return False
        idx_anterior = int(self.playlist_state.get("index") or 0)
        idx = idx_anterior + 1
        if idx >= len(lst):
            self.log(f"🎵 Playlist '{nm}' terminou")
            self.playlist_state["name"] = ""
            self.playlist_state["index"] = 0
            self.playlist_state["last_advance_status"] = "fim"
            return False
        self.playlist_state["index"] = idx
        ok = self._abrir_youtube_item(lst[idx], prefixo_log="Abrindo")
        if not ok:
            self.playlist_state["index"] = idx_anterior
            self.playlist_state["last_advance_status"] = "falha_execucao"
            return False
        self.playlist_state["last_advance_status"] = (
            "ok" if self.playlist_state.get("last_play_confirmed") is not False
            else "enviado_sem_confirmacao"
        )
        return True

    def voltar_anterior(self) -> bool:
        with self._state_lock:
            return self._voltar_anterior_sem_lock()

    def _voltar_anterior_sem_lock(self) -> bool:
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
            ok = self._abrir_youtube_item(queue[idx], prefixo_log="Voltando")
            if not ok:
                self.playlist_state["shuffle_index"] = idx_atual
            return ok

        data = self.load()
        lst = data.get(nm)
        if not isinstance(lst, list) or not lst:
            return False
        idx_atual = int(self.playlist_state.get("index") or 0)
        if idx_atual <= 0 or idx_atual >= len(lst):
            return False
        idx = idx_atual - 1
        self.playlist_state["index"] = idx
        ok = self._abrir_youtube_item(lst[idx], prefixo_log="Voltando")
        if not ok:
            self.playlist_state["index"] = idx_atual
        return ok

    def play(self, name: str) -> bool:
        with self._state_lock:
            return self._play_sem_lock(name)

    def _play_sem_lock(self, name: str) -> bool:
        data = self.load()
        nm = resolver_nome_playlist_contextual(name, data, self._ultima_playlist())
        self.log(f"🎵 [PLAYLIST:PLAY] pedido={name!r} resolvida={nm!r}")
        if not nm:
            self.log("⚠️ [PLAYLIST:PLAY] nome não corresponde a uma playlist salva")
            return False
        lst = data.get(nm)
        if not isinstance(lst, list) or not lst:
            self.log(f"⚠️ Playlist vazia ou inexistente: {nm}")
            return False
        self.log(f"🎵 [PLAYLIST:PLAY] {nm} possui {len(lst)} faixa(s); abrindo a primeira")
        estado_anterior = dict(self.playlist_state)
        self.playlist_state["name"] = nm
        self.playlist_state["index"] = 0
        self.playlist_state["user_intervened"] = False
        self.playlist_state["last_url"] = ""
        self.playlist_state.pop("shuffle", None)
        self.playlist_state.pop("shuffle_queue", None)
        self.playlist_state.pop("shuffle_index", None)
        ok = self._abrir_youtube_item(lst[0], prefixo_log="Abrindo")
        if not ok:
            self.playlist_state.clear()
            self.playlist_state.update(estado_anterior)
            return False
        self._set_ultima_playlist(nm)
        self.playlist_state["last_advance_status"] = (
            "ok" if self.playlist_state.get("last_play_confirmed") is not False
            else "enviado_sem_confirmacao"
        )
        return True


def criar_playlist_runtime(**kwargs: Any) -> PlaylistRuntime:
    return PlaylistRuntime(**kwargs)
