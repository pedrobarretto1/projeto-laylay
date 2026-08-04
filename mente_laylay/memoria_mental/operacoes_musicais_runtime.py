"""Operações musicais mutáveis reunidas atrás de uma única fronteira.

O runtime compõe os serviços de playlists já existentes. Ele não decide se uma
ação está autorizada; essa decisão continua pertencendo aos executores e ao
porteiro da mente única.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping


class OperacoesMusicaisRuntime:
    def __init__(
        self,
        *,
        playlists_usuario: Any,
        playlists_laylay: Any,
        musica_estado_getter: Callable[[str, Any], Any],
        musica_estado_setter: Callable[[str, Any], Any],
        solicitar_aba_ativa: Callable[..., Mapping[str, Any]],
        playlist_state: dict[str, Any],
        log: Callable[..., Any] = print,
    ) -> None:
        self.playlists_usuario = playlists_usuario
        self.playlists_laylay = playlists_laylay
        self.musica_estado_getter = musica_estado_getter
        self.musica_estado_setter = musica_estado_setter
        self.solicitar_aba_ativa = solicitar_aba_ativa
        self.playlist_state = playlist_state
        self.log = log

    def apagar_playlist(self, nome: str) -> bool:
        return bool(self.playlists_usuario.delete(nome))

    def adicionar_faixa(
        self, nome: str, url: str, titulo: str, canal: str = "",
    ) -> bool:
        return bool(self.playlists_usuario.add_and_verify(nome, url, titulo, canal))

    def mover_faixa(self, origem: str, destino: str, musica: str = "") -> dict[str, Any]:
        return dict(
            self.playlists_usuario.mover_item_contextual(origem, destino, musica) or {}
        )

    def tocar_playlist(self, nome: str) -> bool:
        return bool(self.playlists_usuario.play(nome))

    def preparar_shuffle(self, nome: str) -> dict[str, Any]:
        return dict(self.playlists_usuario.shuffle_start(nome) or {})

    def primeira_url(self, nome: str) -> str:
        return str(self.playlists_usuario.primeira_url(nome) or "").strip()

    def avancar_proxima(self) -> bool:
        return bool(self.playlists_usuario.avancar_proxima())

    def voltar_anterior(self) -> bool:
        return bool(self.playlists_usuario.voltar_anterior())

    def definir_ultima_playlist(self, nome: str) -> None:
        self.musica_estado_setter("ultima_playlist", str(nome or "").strip())

    def definir_ultima_url(self, url: str) -> None:
        self.playlist_state["last_url"] = str(url or "").strip()

    def faixa_atual(self) -> dict[str, Any]:
        """Resolve a faixa viva antes de consultar a aba ativa do navegador."""
        try:
            instante = float(self.musica_estado_getter("musica_atual_ts", 0.0) or 0.0)
            status = str(
                self.musica_estado_getter("musica_atual_status", "") or ""
            ).strip().casefold()
            url = str(
                self.musica_estado_getter("musica_atual_url", "") or ""
            ).strip()
            titulo = str(
                self.musica_estado_getter("musica_atual_titulo", "") or ""
            ).strip()
            if (
                instante
                and time.time() - instante <= 7200.0
                and status not in {"finalizada", "encerrada", "parada"}
                and "youtube.com" in url.casefold()
            ):
                return {
                    "url": url,
                    "title": titulo,
                    "canal": "",
                    "origem": "player_atual",
                }
        except Exception as erro:
            self.log(
                "⚠️ [PLAYLIST:CONTEXTO] estado da música atual indisponível: "
                f"{type(erro).__name__}: {erro}"
            )
        try:
            return dict(self.solicitar_aba_ativa() or {})
        except Exception as erro:
            self.log(
                "⚠️ [PLAYLIST:CONTEXTO] aba ativa indisponível: "
                f"{type(erro).__name__}: {erro}"
            )
            return {}

    def copiar_curadoria(
        self, origem: str, musica: str, destino: str,
    ) -> dict[str, Any]:
        return dict(self.playlists_laylay.copiar_faixa(origem, musica, destino) or {})

    def estado(self) -> dict[str, Any]:
        return {
            "playlist_ativa": str(self.playlist_state.get("name") or "").strip(),
            "indice": max(0, int(self.playlist_state.get("index") or 0)),
            "modo_aleatorio": bool(self.playlist_state.get("shuffle", False)),
            "status_avanco": str(
                self.playlist_state.get("last_advance_status") or ""
            ).strip(),
            "tab_id": (
                self.playlist_state.get("tab_id")
                if isinstance(self.playlist_state.get("tab_id"), int)
                else None
            ),
        }

    def diagnostico(self) -> dict[str, Any]:
        estado = self.estado()
        return {
            "mutacao_disponivel": True,
            "reproducao_disponivel": True,
            "auto_next_disponivel": True,
            "curadoria_disponivel": callable(
                getattr(self.playlists_laylay, "copiar_faixa", None)
            ),
            "playlist_ativa": bool(estado.get("playlist_ativa")),
        }


def criar_operacoes_musicais_runtime(**kwargs: Any) -> OperacoesMusicaisRuntime:
    return OperacoesMusicaisRuntime(**kwargs)
