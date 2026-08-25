"""Operações musicais mutáveis reunidas atrás de uma única fronteira.

O runtime compõe os serviços de playlists já existentes. Ele não decide se uma
ação está autorizada; essa decisão continua pertencendo aos executores e ao
porteiro da mente única.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping
from urllib.parse import parse_qs, urlparse


def _identidade_youtube(url: str) -> str:
    valor = str(url or "").strip()
    if not valor:
        return ""
    try:
        parsed = urlparse(valor)
        video_id = str((parse_qs(parsed.query).get("v") or [""])[0]).strip()
        if video_id:
            return f"youtube:{video_id}"
        partes = [parte for parte in parsed.path.split("/") if parte]
        if partes and partes[0].casefold() in {"shorts", "embed", "live"}:
            return f"youtube:{partes[-1]}"
    except Exception:
        pass
    return valor.casefold().split("#", 1)[0]


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

    def criar_playlist(self, nome: str) -> dict[str, Any]:
        return dict(self.playlists_usuario.create(nome) or {})

    def adicionar_faixa(
        self, nome: str, url: str, titulo: str, canal: str = "",
    ) -> bool:
        return bool(self.playlists_usuario.add_and_verify(nome, url, titulo, canal))

    def adicionar_faixa_resultado(
        self, nome: str, url: str, titulo: str, canal: str = "",
    ) -> dict[str, Any]:
        detalhado = getattr(self.playlists_usuario, "add_and_verify_result", None)
        if callable(detalhado):
            return dict(detalhado(nome, url, titulo, canal) or {})
        ok = bool(self.playlists_usuario.add_and_verify(nome, url, titulo, canal))
        return {
            "ok": ok,
            "added": ok,
            "status": "playlist_musica_adicionada" if ok else "falha_execucao",
        }

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
        """Prefere a reprodução observada; memória recente é só fallback."""
        aba_observada: dict[str, Any] = {}
        instante = 0.0
        status_memoria = ""
        url_memoria = ""
        titulo_memoria = ""
        origem_troca_url = ""
        try:
            instante = float(
                self.musica_estado_getter("musica_atual_ts", 0.0) or 0.0
            )
            status_memoria = str(
                self.musica_estado_getter("musica_atual_status", "") or ""
            ).strip().casefold()
            url_memoria = str(
                self.musica_estado_getter("musica_atual_url", "") or ""
            ).strip()
            titulo_memoria = str(
                self.musica_estado_getter("musica_atual_titulo", "") or ""
            ).strip()
            origem_troca_url = str(
                self.musica_estado_getter("musica_troca_origem_url", "") or ""
            ).strip()
        except Exception as erro:
            self.log(
                "⚠️ [PLAYLIST:CONTEXTO] estado da música atual indisponível: "
                f"{type(erro).__name__}: {erro}"
            )
        try:
            aba_observada = dict(self.solicitar_aba_ativa() or {})
        except Exception as erro:
            self.log(
                "⚠️ [PLAYLIST:CONTEXTO] reprodução do navegador indisponível: "
                f"{type(erro).__name__}: {erro}"
            )
        url_observada = str(aba_observada.get("url") or "").strip()
        reproducao_confirmada = bool(
            aba_observada.get("audibleConfirmed") is True
            or aba_observada.get("playingConfirmed") is True
        )
        player_observado = (
            dict(self.playlist_state.get("player") or {})
            if isinstance(self.playlist_state.get("player"), dict)
            else {}
        )
        url_player = str(player_observado.get("url") or "").strip()
        try:
            idade_player = time.time() - float(
                player_observado.get("observed_at") or 0.0
            )
        except (TypeError, ValueError):
            idade_player = float("inf")
        player_recente = bool(
            0.0 <= idade_player <= 12.0
            and "youtube.com" in url_player.casefold()
            and str(player_observado.get("state") or "").casefold()
            not in {"ended", "finalizada", "encerrada", "parada"}
        )
        troca_pendente = status_memoria == "troca_nao_confirmada"
        identidade_origem = _identidade_youtube(origem_troca_url)

        def identidade_mudou(url_candidata: str) -> bool:
            identidade_candidata = _identidade_youtube(url_candidata)
            return bool(
                identidade_origem
                and identidade_candidata
                and identidade_candidata != identidade_origem
            )

        # O player observado é independente da aba ativa. Durante uma cadeia,
        # o navegador pode estar exibindo Wikipédia enquanto o YouTube toca em
        # outra aba; consultar só ``aba_ativa`` perde justamente a faixa que o
        # Chrome publicou. A observação precisa ser recente e, após next/prev,
        # ter identidade diferente da origem para não confirmar a faixa velha.
        if (
            player_recente
            and (not troca_pendente or identidade_mudou(url_player))
        ):
            return {
                "url": url_player,
                "title": str(player_observado.get("title") or "").strip(),
                "canal": str(
                    player_observado.get("channel")
                    or player_observado.get("canal")
                    or ""
                ).strip(),
                "origem": str(
                    player_observado.get("source")
                    or "player_navegador_observado"
                ).strip(),
            }

        if (
            "youtube.com" in url_observada.casefold()
            and reproducao_confirmada
            and (not troca_pendente or identidade_mudou(url_observada))
        ):
            return {
                **aba_observada,
                "origem": str(
                    aba_observada.get("source") or "player_navegador_observado"
                ),
            }
        try:
            if (
                instante
                and time.time() - instante <= 7200.0
                and status_memoria not in {
                    "finalizada", "encerrada", "parada",
                }
                and (
                    not troca_pendente
                    or identidade_mudou(url_memoria)
                )
                and "youtube.com" in url_memoria.casefold()
            ):
                return {
                    "url": url_memoria,
                    "title": titulo_memoria,
                    "canal": "",
                    "origem": "player_atual",
                }
        except Exception as erro:
            self.log(
                "⚠️ [PLAYLIST:CONTEXTO] estado da música atual indisponível: "
                f"{type(erro).__name__}: {erro}"
            )
        # Compatibilidade com uma extensão antiga ou uma aba pausada: ela só
        # entra quando não há faixa recente confirmada na mente.
        if (
            "youtube.com" in url_observada.casefold()
            and not troca_pendente
        ):
            return aba_observada
        return {}

    def copiar_curadoria(
        self, origem: str, musica: str, destino: str,
    ) -> dict[str, Any]:
        return dict(self.playlists_laylay.copiar_faixa(origem, musica, destino) or {})

    def selecionar_curadoria(
        self, nome: str = "", indice_faixa: int = 0,
    ) -> dict[str, Any]:
        selecionar = getattr(self.playlists_laylay, "selecionar", None)
        if not callable(selecionar):
            return {"ok": False, "erro": "curadoria_indisponivel"}
        return dict(selecionar(nome, indice_faixa) or {})

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
