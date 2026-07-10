"""Runtime das playlists proprias da Laylay.

Mantem persistencia e curadoria em um modulo separado, recebendo os dados da
mente musical compartilhada por callbacks para nao criar um estado paralelo.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Callable, Dict

from mente_laylay.memoria_mental.curadoria_musical import (
    encontrar_faixa_playlist,
    sincronizar_playlists_da_laylay,
)
from mente_laylay.memoria_mental.playlist_mental import (
    fala_playlist_conteudo_estilosa,
    limpar_nome_playlist,
    playlists_load,
    playlists_save,
    yt_clean_title,
    yt_clean_url,
)


class PlaylistLaylayRuntime:
    def __init__(
        self,
        *,
        state_file: str,
        cache: Dict[str, Any],
        playlists_usuario_getter: Callable[[], Dict[str, Any]],
        historico_musical_getter: Callable[[], Dict[str, Any]],
        adicionar_playlist_usuario: Callable[[str, str, str, str], Any],
    ) -> None:
        self.state_file = state_file
        self.cache = cache
        self.playlists_usuario_getter = playlists_usuario_getter
        self.historico_musical_getter = historico_musical_getter
        self.adicionar_playlist_usuario = adicionar_playlist_usuario

    def _sync_cache(self, data: Dict[str, Any] | None) -> Dict[str, Any]:
        data = data if isinstance(data, dict) else {}
        self.cache.clear()
        self.cache.update(data)
        return self.cache

    def load(self) -> Dict[str, Any]:
        pasta = os.path.dirname(self.state_file)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        data = playlists_load(self.state_file, self.state_file)
        return self._sync_cache(data)

    def save(self, data: Dict[str, Any]) -> bool:
        pasta = os.path.dirname(self.state_file)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        ok = playlists_save(self.state_file, data or {})
        if ok:
            self._sync_cache(data or {})
        return bool(ok)

    def sincronizar(self) -> Dict[str, Any]:
        atuais = self.load()
        try:
            playlists_usuario = self.playlists_usuario_getter() or {}
        except Exception:
            playlists_usuario = {}
        try:
            historico = self.historico_musical_getter() or {}
        except Exception:
            historico = {}
        sincronizadas = sincronizar_playlists_da_laylay(
            playlists_usuario if isinstance(playlists_usuario, dict) else {},
            historico if isinstance(historico, dict) else {},
            atuais,
        )
        self.save(sincronizadas)
        return sincronizadas

    def listar(self, nome: str = "") -> str:
        data = self.sincronizar()
        nome_limpo = limpar_nome_playlist(nome or "")
        if nome_limpo:
            itens = data.get(nome_limpo)
            itens = itens if isinstance(itens, list) else []
            return fala_playlist_conteudo_estilosa(
                {
                    "name": nome_limpo,
                    "total": len(itens),
                    "last_titles": [
                        yt_clean_title(str(item.get("titulo") or ""))
                        for item in itens[:3]
                        if isinstance(item, dict)
                    ],
                },
                nome_limpo,
            )

        nomes = []
        for chave, itens in sorted(data.items(), key=lambda kv: str(kv[0]).lower()):
            total = len(itens) if isinstance(itens, list) else 0
            nomes.append(f"{chave} ({total})")
        if not nomes:
            return "Eu ainda não montei playlists minhas por aqui."
        return f"As minhas playlists são: {', '.join(nomes)}."

    def adicionar_descoberta(self, item: dict) -> None:
        if not isinstance(item, dict):
            return
        data = self.load()
        lista = data.setdefault("descobertas_da_laylay", [])
        if not isinstance(lista, list):
            lista = []
            data["descobertas_da_laylay"] = lista
        url = yt_clean_url(str(item.get("url") or "").strip())
        for existente in lista:
            if (
                isinstance(existente, dict)
                and yt_clean_url(str(existente.get("url") or "").strip()) == url
            ):
                self.save(data)
                return
        lista.append(
            {
                "url": url,
                "titulo": str(item.get("titulo") or "").strip(),
                "canal": str(item.get("canal") or "").strip(),
                "data": str(item.get("data") or datetime.now().date().isoformat()),
                "motivo": str(item.get("motivo") or "descoberta_da_laylay").strip(),
            }
        )
        self.save(data)

    def copiar_faixa(
        self,
        nome_playlist_laylay: str,
        musica: str,
        destino_usuario: str,
    ) -> dict:
        data = self.sincronizar()
        faixa = encontrar_faixa_playlist(data, nome_playlist_laylay, musica)
        if not faixa:
            return {"ok": False, "erro": "nao_encontrada"}
        resultado = self.adicionar_playlist_usuario(
            destino_usuario,
            str(faixa.get("url") or ""),
            str(faixa.get("titulo") or ""),
            str(faixa.get("canal") or ""),
        )
        return {
            "ok": bool(isinstance(resultado, dict) and resultado.get("ok")),
            "faixa": faixa,
            "destino": destino_usuario,
        }


def criar_playlist_laylay_runtime(**kwargs: Any) -> PlaylistLaylayRuntime:
    return PlaylistLaylayRuntime(**kwargs)
