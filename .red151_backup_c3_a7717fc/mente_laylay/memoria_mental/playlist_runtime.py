"""Runtime de playlists da Laylay.

Este modulo concentra operacoes de arquivo/cache de playlist, mas recebe os
callbacks do cerebro principal para continuar conectado a mesma mente.
"""

from __future__ import annotations

import random
import re
import threading
import unicodedata
import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
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
        artwork_dir: str | None = None,
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
        self.artwork_dir = Path(
            artwork_dir or (Path.home() / ".laylay" / "playlist_artwork")
        )
        self._playlist_metadata_file = f"{self.state_file}.metadata.json"
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
        metadados = self._carregar_metadados_playlist()
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
            capa = self._capa_publica(
                nome_limpo, itens, metadados=metadados,
            )
            retrato = {
                "name": nome_limpo,
                "count": len(itens),
                "artwork_video_id": video_id,
            }
            # A capa automática já é derivada do ID pela fronteira pública.
            # Só acrescentamos o novo campo quando existe uma capa controlada,
            # preservando o contrato exato dos consumidores antigos.
            if capa.startswith("laylay-playlist-artwork://"):
                retrato["artwork_url"] = capa
            catalogo.append(retrato)
        return catalogo

    @staticmethod
    def _video_id_item(item: Any) -> str:
        url = str(item.get("url") or "") if isinstance(item, dict) else str(item or "")
        encontrado = re.search(
            r"(?:[?&]v=|youtu\.be/|/(?:shorts|embed|live)/)"
            r"([A-Za-z0-9_-]{11})(?:[^A-Za-z0-9_-]|$)",
            url,
        )
        return encontrado.group(1) if encontrado else ""

    def _carregar_metadados_playlist(self) -> dict[str, Any]:
        try:
            with open(self._playlist_metadata_file, "r", encoding="utf-8") as arquivo:
                bruto = json.load(arquivo)
            return bruto if isinstance(bruto, dict) else {}
        except (OSError, ValueError, TypeError):
            return {}

    def _salvar_metadados_playlist(self, dados: dict[str, Any]) -> bool:
        return bool(playlists_save(self._playlist_metadata_file, dados))

    def _remover_capa_se_orfa(
        self,
        identificador: str,
        metadados_atuais: dict[str, Any],
    ) -> None:
        identificador = str(identificador or "").strip()
        if not re.fullmatch(r"[a-f0-9]{24}\.png", identificador):
            return
        ainda_referenciada = any(
            isinstance(valor, dict)
            and str(valor.get("artwork_id") or "") == identificador
            for valor in metadados_atuais.values()
        )
        if ainda_referenciada:
            return
        try:
            (self.artwork_dir / identificador).unlink(missing_ok=True)
        except OSError:
            self.log(
                "⚠️ [PLAYLISTS:CAPA] arquivo órfão não pôde ser removido "
                f"| id={identificador}"
            )

    def _capa_publica(
        self,
        nome: str,
        itens: list[Any],
        *,
        metadados: dict[str, Any] | None = None,
    ) -> str:
        meta = (metadados or self._carregar_metadados_playlist()).get(nome)
        meta = meta if isinstance(meta, dict) else {}
        identificador = str(meta.get("artwork_id") or "").strip()
        if re.fullmatch(r"[a-f0-9]{24}\.png", identificador):
            arquivo = self.artwork_dir / identificador
            if arquivo.is_file():
                return f"laylay-playlist-artwork://{identificador}"
        video_id = next((self._video_id_item(item) for item in itens if self._video_id_item(item)), "")
        return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else ""

    def _revisao_playlist(
        self,
        nome: str,
        itens: list[Any],
        *,
        metadados: dict[str, Any] | None = None,
    ) -> str:
        meta = (metadados or self._carregar_metadados_playlist()).get(nome)
        meta = meta if isinstance(meta, dict) else {}
        serializavel = {
            "nome": nome,
            "itens": itens,
            "artwork_id": str(meta.get("artwork_id") or ""),
        }
        bruto = json.dumps(
            serializavel, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(bruto).hexdigest()[:24]

    def detalhar(
        self,
        nome: str,
        *,
        consulta: str = "",
        deslocamento: int = 0,
        limite: int = 50,
    ) -> dict[str, Any]:
        """Publica uma página sanitizada; URLs brutas nunca atravessam a leitura."""
        with self._state_lock:
            dados = deepcopy(self.load())
            resolvido = resolver_nome_playlist_contextual(
                nome, dados, self._ultima_playlist(),
            )
            itens = dados.get(resolvido) if resolvido else None
            if not isinstance(itens, list):
                return {"ok": False, "status": "playlist_not_found", "items": []}
            metadados = self._carregar_metadados_playlist()
            revisao = self._revisao_playlist(resolvido, itens, metadados=metadados)

        consulta_norm = unicodedata.normalize("NFKD", str(consulta or "").casefold())
        consulta_norm = "".join(ch for ch in consulta_norm if not unicodedata.combining(ch))
        consulta_norm = re.sub(r"\s+", " ", consulta_norm).strip()[:120]
        filtrados: list[dict[str, Any]] = []
        duracao_total = 0
        duracao_completa = True
        for item in itens:
            info = item if isinstance(item, dict) else {"url": str(item or "")}
            video_id = self._video_id_item(info)
            if not video_id:
                continue
            titulo = re.sub(r"\s+", " ", yt_clean_title(str(info.get("titulo") or ""))).strip()[:180]
            canal = re.sub(r"\s+", " ", str(info.get("canal") or "")).strip()[:120]
            busca = unicodedata.normalize("NFKD", f"{titulo} {canal}".casefold())
            busca = "".join(ch for ch in busca if not unicodedata.combining(ch))
            if consulta_norm and consulta_norm not in busca:
                continue
            duracao_bruta = info.get("duracao_segundos")
            duracao: int | None = None
            if isinstance(duracao_bruta, (int, float)) and not isinstance(duracao_bruta, bool):
                candidato = int(duracao_bruta)
                if 0 < candidato <= 86_400:
                    duracao = candidato
            if duracao is None:
                duracao_completa = False
            else:
                duracao_total += duracao
            filtrados.append({
                "video_id": video_id,
                "title": titulo or "Faixa sem título",
                "channel": canal,
                "added_at": str(info.get("data") or "").strip()[:10],
                "duration_seconds": duracao,
                "artwork_url": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
            })
        inicio = max(0, int(deslocamento or 0))
        tamanho = max(1, min(100, int(limite or 50)))
        pagina = filtrados[inicio:inicio + tamanho]
        return {
            "ok": True,
            "name": resolvido,
            "total": len(filtrados),
            "offset": inicio,
            "limit": tamanho,
            "has_more": inicio + len(pagina) < len(filtrados),
            "revision": revisao,
            "artwork_url": self._capa_publica(
                resolvido, itens, metadados=metadados,
            ),
            "duration_seconds": duracao_total if duracao_completa and itens else None,
            "items": pagina,
        }

    def _localizar_exata(
        self,
        dados: dict[str, Any],
        nome: str,
        video_id: str,
        revisao: str,
    ) -> tuple[str, list[Any], int] | tuple[None, None, None]:
        resolvido = resolver_nome_playlist_contextual(nome, dados, self._ultima_playlist())
        itens = dados.get(resolvido) if resolvido else None
        if not isinstance(itens, list):
            return None, None, None
        if self._revisao_playlist(resolvido, itens) != str(revisao or ""):
            return None, None, -2
        identidade = str(video_id or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", identidade):
            return None, None, None
        indices = [i for i, item in enumerate(itens) if self._video_id_item(item) == identidade]
        if len(indices) != 1:
            return None, None, None
        return resolvido, itens, indices[0]

    def tocar_faixa_exata(self, nome: str, video_id: str, revisao: str) -> dict[str, Any]:
        with self._state_lock:
            dados = self.load()
            resolvido, itens, indice = self._localizar_exata(dados, nome, video_id, revisao)
            if indice == -2:
                return {"ok": False, "status": "revision_conflict"}
            if resolvido is None or itens is None or indice is None:
                return {"ok": False, "status": "track_not_found"}
            estado_anterior = dict(self.playlist_state)
            self.playlist_state.update(name=resolvido, index=indice, user_intervened=False)
            self.playlist_state.pop("shuffle", None)
            self.playlist_state.pop("shuffle_queue", None)
            self.playlist_state.pop("shuffle_index", None)
            if not self._abrir_youtube_item(itens[indice], prefixo_log="Abrindo faixa exata"):
                self.playlist_state.clear()
                self.playlist_state.update(estado_anterior)
                return {"ok": False, "status": "play_failed"}
            self._set_ultima_playlist(resolvido)
            return {"ok": True, "status": "track_started", "video_id": video_id}

    def copiar_faixa_exata(
        self, origem: str, destino: str, video_id: str, revisao: str,
    ) -> dict[str, Any]:
        with self._state_lock:
            dados = deepcopy(self.load())
            origem_nm, itens, indice = self._localizar_exata(
                dados, origem, video_id, revisao,
            )
            if indice == -2:
                return {"ok": False, "status": "revision_conflict"}
            destino_nm = limpar_nome_playlist(destino)
            if origem_nm is None or itens is None or indice is None or not destino_nm:
                return {"ok": False, "status": "track_not_found"}
            destino_itens = dados.setdefault(destino_nm, [])
            if not isinstance(destino_itens, list):
                return {"ok": False, "status": "destination_invalid"}
            if any(self._video_id_item(item) == video_id for item in destino_itens):
                return {"ok": True, "status": "already_present", "copied": False}
            destino_itens.append(deepcopy(itens[indice]))
            if not self.save(dados):
                return {"ok": False, "status": "save_failed"}
            return {"ok": True, "status": "copied", "copied": True}

    def distribuir_faixa_exata(
        self,
        origem: str,
        destinos: list[str],
        video_id: str,
        revisao: str,
        *,
        remover_origem: bool = False,
    ) -> dict[str, Any]:
        """Copia para vários destinos com uma única persistência atômica."""
        with self._state_lock:
            dados = deepcopy(self.load())
            origem_nm, itens, indice = self._localizar_exata(
                dados, origem, video_id, revisao,
            )
            if indice == -2:
                return {"ok": False, "status": "revision_conflict"}
            if origem_nm is None or itens is None or indice is None:
                return {"ok": False, "status": "track_not_found"}
            if not isinstance(destinos, list) or not 1 <= len(destinos) <= 1_000:
                return {"ok": False, "status": "destinations_invalid"}

            destinos_resolvidos: list[str] = []
            vistos: set[str] = set()
            for bruto in destinos:
                limpo = limpar_nome_playlist(str(bruto or ""))
                resolvido = (
                    resolver_nome_playlist_contextual(limpo, dados, "")
                    if limpo else ""
                )
                destino_nm = resolvido or limpo
                chave = destino_nm.casefold()
                if (
                    not destino_nm or chave == origem_nm.casefold()
                    or chave in vistos
                ):
                    continue
                destino_itens = dados.get(destino_nm)
                if not isinstance(destino_itens, list):
                    return {"ok": False, "status": "destination_invalid"}
                vistos.add(chave)
                destinos_resolvidos.append(destino_nm)
            if not destinos_resolvidos:
                return {"ok": False, "status": "destinations_invalid"}

            item = deepcopy(itens[indice])
            copiados = 0
            ja_presentes = 0
            for destino_nm in destinos_resolvidos:
                destino_itens = dados[destino_nm]
                if any(
                    self._video_id_item(atual) == video_id
                    for atual in destino_itens
                ):
                    ja_presentes += 1
                    continue
                destino_itens.append(deepcopy(item))
                copiados += 1

            if remover_origem:
                del itens[indice]
            elif copiados == 0:
                return {
                    "ok": True,
                    "status": "already_present_all",
                    "destination_count": len(destinos_resolvidos),
                    "copied_count": 0,
                    "already_present_count": ja_presentes,
                }
            if not self.save(dados):
                return {"ok": False, "status": "save_failed"}
            return {
                "ok": True,
                "status": "moved_many" if remover_origem else "copied_many",
                "destination_count": len(destinos_resolvidos),
                "copied_count": copiados,
                "already_present_count": ja_presentes,
                "source_removed": bool(remover_origem),
            }

    def copiar_faixa_multiplas(
        self, origem: str, destinos: list[str], video_id: str, revisao: str,
    ) -> dict[str, Any]:
        return self.distribuir_faixa_exata(
            origem, destinos, video_id, revisao,
        )

    def mover_faixa_multiplas(
        self, origem: str, destinos: list[str], video_id: str, revisao: str,
    ) -> dict[str, Any]:
        return self.distribuir_faixa_exata(
            origem, destinos, video_id, revisao, remover_origem=True,
        )

    def mover_faixa_exata(
        self, origem: str, destino: str, video_id: str, revisao: str,
    ) -> dict[str, Any]:
        with self._state_lock:
            dados = deepcopy(self.load())
            origem_nm, itens, indice = self._localizar_exata(
                dados, origem, video_id, revisao,
            )
            if indice == -2:
                return {"ok": False, "status": "revision_conflict"}
            destino_nm = limpar_nome_playlist(destino)
            if origem_nm is None or itens is None or indice is None or not destino_nm:
                return {"ok": False, "status": "track_not_found"}
            if destino_nm == origem_nm:
                return {"ok": True, "status": "same_playlist"}
            destino_itens = dados.setdefault(destino_nm, [])
            if not isinstance(destino_itens, list):
                return {"ok": False, "status": "destination_invalid"}
            item = itens[indice]
            if not any(self._video_id_item(atual) == video_id for atual in destino_itens):
                destino_itens.append(deepcopy(item))
            del itens[indice]
            if not self.save(dados):
                return {"ok": False, "status": "save_failed"}
            return {"ok": True, "status": "moved"}

    def remover_faixa_exata(
        self, nome: str, video_id: str, revisao: str,
    ) -> dict[str, Any]:
        with self._state_lock:
            dados = deepcopy(self.load())
            resolvido, itens, indice = self._localizar_exata(
                dados, nome, video_id, revisao,
            )
            if indice == -2:
                return {"ok": False, "status": "revision_conflict"}
            if resolvido is None or itens is None or indice is None:
                return {"ok": False, "status": "track_not_found"}
            del itens[indice]
            if not self.save(dados):
                return {"ok": False, "status": "save_failed"}
            return {"ok": True, "status": "removed"}

    def adicionar_url_resolvida(
        self,
        nome: str,
        url: str,
        metadados: dict[str, Any],
    ) -> dict[str, Any]:
        """Adiciona somente quando o resolvedor confirma o mesmo vídeo pedido."""
        video_id = self._video_id_item({"url": url})
        resolvido_id = str(dict(metadados or {}).get("video_id") or "").strip()
        titulo = str(dict(metadados or {}).get("title") or "").strip()
        if not video_id or resolvido_id != video_id or not titulo:
            return {"ok": False, "status": "metadata_mismatch"}
        resultado = self.add_and_verify_result(
            nome, f"https://www.youtube.com/watch?v={video_id}", titulo,
            str(metadados.get("channel") or ""),
        )
        duracao = metadados.get("duration_seconds")
        if (
            resultado.get("ok") and resultado.get("added")
            and isinstance(duracao, (int, float)) and not isinstance(duracao, bool)
            and 0 < int(duracao) <= 86_400
        ):
            with self._state_lock:
                dados = deepcopy(self.load())
                nome_resolvido = resolver_nome_playlist_contextual(
                    nome, dados, self._ultima_playlist(),
                )
                itens = dados.get(nome_resolvido)
                if isinstance(itens, list):
                    for item in reversed(itens):
                        if isinstance(item, dict) and self._video_id_item(item) == video_id:
                            item["duracao_segundos"] = int(duracao)
                            self.save(dados)
                            break
        return resultado

    def definir_capa(
        self, nome: str, caminho_origem: str, revisao: str,
    ) -> dict[str, Any]:
        with self._state_lock:
            dados = self.load()
            resolvido = resolver_nome_playlist_contextual(nome, dados, self._ultima_playlist())
            itens = dados.get(resolvido) if resolvido else None
            if not isinstance(itens, list):
                return {"ok": False, "status": "playlist_not_found"}
            if self._revisao_playlist(resolvido, itens) != str(revisao or ""):
                return {"ok": False, "status": "revision_conflict"}
            origem = Path(str(caminho_origem or "")).expanduser()
            if not origem.is_file() or origem.stat().st_size > 12 * 1024 * 1024:
                return {"ok": False, "status": "invalid_artwork"}
            try:
                from PIL import Image
                with Image.open(origem) as imagem:
                    imagem.verify()
                with Image.open(origem) as imagem:
                    imagem = imagem.convert("RGB")
                    imagem.thumbnail((1200, 1200))
                    self.artwork_dir.mkdir(parents=True, exist_ok=True)
                    digest = hashlib.sha256(origem.read_bytes()).hexdigest()[:24]
                    identificador = f"{digest}.png"
                    temporario = self.artwork_dir / f".{digest}.tmp"
                    imagem.save(temporario, format="PNG", optimize=True)
                    os.replace(temporario, self.artwork_dir / identificador)
            except Exception:
                return {"ok": False, "status": "invalid_artwork"}
            metadados = self._carregar_metadados_playlist()
            anterior = dict(metadados.get(resolvido) or {})
            identificador_anterior = str(anterior.get("artwork_id") or "")
            metadados[resolvido] = {**anterior, "artwork_id": identificador}
            if not self._salvar_metadados_playlist(metadados):
                if identificador != identificador_anterior:
                    self._remover_capa_se_orfa(
                        identificador, self._carregar_metadados_playlist(),
                    )
                return {"ok": False, "status": "save_failed"}
            if identificador_anterior != identificador:
                self._remover_capa_se_orfa(identificador_anterior, metadados)
            nova_revisao = self._revisao_playlist(resolvido, itens, metadados=metadados)
            return {
                "ok": True,
                "status": "artwork_updated",
                "revision": nova_revisao,
                "artwork_url": f"laylay-playlist-artwork://{identificador}",
            }

    def restaurar_capa(self, nome: str, revisao: str) -> dict[str, Any]:
        with self._state_lock:
            dados = self.load()
            resolvido = resolver_nome_playlist_contextual(nome, dados, self._ultima_playlist())
            itens = dados.get(resolvido) if resolvido else None
            if not isinstance(itens, list):
                return {"ok": False, "status": "playlist_not_found"}
            metadados = self._carregar_metadados_playlist()
            if self._revisao_playlist(resolvido, itens, metadados=metadados) != str(revisao or ""):
                return {"ok": False, "status": "revision_conflict"}
            anterior = dict(metadados.get(resolvido) or {})
            identificador_anterior = str(anterior.get("artwork_id") or "")
            metadados.pop(resolvido, None)
            if not self._salvar_metadados_playlist(metadados):
                return {"ok": False, "status": "save_failed"}
            self._remover_capa_se_orfa(identificador_anterior, metadados)
            return {
                "ok": True,
                "status": "artwork_restored",
                "revision": self._revisao_playlist(resolvido, itens, metadados=metadados),
                "artwork_url": self._capa_publica(resolvido, itens, metadados=metadados),
            }

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

    def selecionar_faixa_fila(
        self, video_id: str, deslocamento: int,
    ) -> dict[str, Any]:
        """Salta para uma próxima faixa confirmando o retrato que foi clicado."""
        identidade = str(video_id or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", identidade):
            return {"ok": False, "status": "queue_item_invalid"}
        if isinstance(deslocamento, bool):
            return {"ok": False, "status": "queue_position_invalid"}
        try:
            deslocamento = int(deslocamento)
        except (TypeError, ValueError):
            return {"ok": False, "status": "queue_position_invalid"}
        if not 0 <= deslocamento <= 999:
            return {"ok": False, "status": "queue_position_invalid"}

        with self._state_lock:
            nome = str(self.playlist_state.get("name") or "").strip()
            if not nome:
                return {"ok": False, "status": "playlist_inactive"}
            aleatoria = bool(
                self.playlist_state.get("shuffle") is True
                and isinstance(self.playlist_state.get("shuffle_queue"), list)
            )
            if aleatoria:
                itens = self.playlist_state.get("shuffle_queue") or []
                chave_indice = "shuffle_index"
            else:
                itens = self.cache.get(nome) if isinstance(self.cache, dict) else []
                chave_indice = "index"
            if not isinstance(itens, list):
                return {"ok": False, "status": "playlist_invalid"}
            indice_atual = max(0, int(self.playlist_state.get(chave_indice) or 0))
            indice_alvo = indice_atual + 1 + deslocamento
            if not 0 <= indice_alvo < len(itens):
                return {"ok": False, "status": "queue_stale"}
            if self._video_id_item(itens[indice_alvo]) != identidade:
                return {"ok": False, "status": "queue_stale"}

            self.playlist_state[chave_indice] = indice_alvo
            self.playlist_state["user_intervened"] = False
            if not self._abrir_youtube_item(
                itens[indice_alvo], prefixo_log="Abrindo faixa escolhida na fila",
            ):
                self.playlist_state[chave_indice] = indice_atual
                self.playlist_state["last_advance_status"] = "falha_execucao"
                return {"ok": False, "status": "play_failed"}
            self.playlist_state["last_advance_status"] = "ok"
            self._set_ultima_playlist(nome)
            return {
                "ok": True,
                "status": "queue_track_started",
                "video_id": identidade,
                "confirmed": self.playlist_state.get("last_play_confirmed") is True,
            }

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

    def add_and_verify_result(
        self, nome_playlist: str, url: str, titulo: str, canal: str = "",
    ) -> dict[str, Any]:
        """Persiste uma faixa e distingue inclusão nova de repetição idempotente."""
        name = self.resolver_nome(nome_playlist)
        if not name:
            return {"ok": False, "added": False, "status": "alvo_ausente"}
        link = str(url or "").strip()
        if not link:
            return {"ok": False, "added": False, "status": "fonte_ausente"}
        musica = yt_clean_title(str(titulo or "")) or link
        self.log(f"[DISK] Escrevendo {musica} em {self.state_file}...")
        res = self.add_url(name, link, str(titulo or ""), str(canal or ""))
        if not (isinstance(res, dict) and res.get("ok")):
            return {
                "ok": False,
                "added": False,
                "status": "falha_persistencia",
            }
        data = self.load()
        lst = data.get(name)
        if not isinstance(lst, list):
            return {
                "ok": False,
                "added": False,
                "status": "falha_confirmacao",
            }
        target = yt_clean_url(link)
        confirmado = False
        for item in reversed(lst[-10:]):
            if isinstance(item, dict):
                item_url = str(item.get("url") or "").strip()
            else:
                item_url = str(item or "").strip()
            if item_url and yt_clean_url(item_url) == target:
                confirmado = True
                break
        duplicada = bool(res.get("duplicated") or res.get("duplicated_meta"))
        # Duplicação por metadado pode apontar para outra URL já existente;
        # nesse caso a própria resposta do gravador é a confirmação de que a
        # biblioteca rejeitou a cópia de forma idempotente.
        confirmado = confirmado or bool(res.get("duplicated_meta"))
        return {
            "ok": confirmado,
            "added": bool(confirmado and not duplicada),
            "duplicated": duplicada,
            "duplicate_other_channel": bool(res.get("duplicate_other_channel")),
            "status": (
                "playlist_musica_ja_existia"
                if confirmado and duplicada
                else "playlist_musica_adicionada"
                if confirmado
                else "falha_confirmacao"
            ),
        }

    def add_and_verify(
        self, nome_playlist: str, url: str, titulo: str, canal: str = "",
    ) -> bool:
        """Compatibilidade booleana para integrações anteriores."""
        return bool(
            self.add_and_verify_result(nome_playlist, url, titulo, canal).get("ok")
        )

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
