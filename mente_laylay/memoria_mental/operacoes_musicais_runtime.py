"""Operações musicais mutáveis reunidas atrás de uma única fronteira.

O runtime compõe os serviços de playlists já existentes. Ele não decide se uma
ação está autorizada; essa decisão continua pertencendo aos executores e ao
porteiro da mente única.
"""

from __future__ import annotations

import time
import json
from typing import Any, Callable, Mapping
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


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
        if parsed.netloc.casefold() in {"youtu.be", "www.youtu.be"} and partes:
            return f"youtube:{partes[0]}"
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
        youtube_metadata_resolver: Callable[[str], Mapping[str, Any]] | None = None,
    ) -> None:
        self.playlists_usuario = playlists_usuario
        self.playlists_laylay = playlists_laylay
        self.musica_estado_getter = musica_estado_getter
        self.musica_estado_setter = musica_estado_setter
        self.solicitar_aba_ativa = solicitar_aba_ativa
        self.playlist_state = playlist_state
        self.log = log
        self.youtube_metadata_resolver = (
            youtube_metadata_resolver or self._resolver_metadados_youtube
        )

    @staticmethod
    def _resolver_metadados_youtube(url: str) -> dict[str, Any]:
        identidade = _identidade_youtube(url)
        video_id = identidade.removeprefix("youtube:") if identidade.startswith("youtube:") else ""
        if len(video_id) != 11:
            return {}
        pagina = f"https://www.youtube.com/watch?v={video_id}"
        try:
            with urlopen(Request(
                pagina,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Laylay/1",
                    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
                },
            ), timeout=6) as resposta:
                html = resposta.read(2_000_000).decode("utf-8", errors="replace")
            marcador = '"videoDetails":'
            inicio = html.find(marcador)
            if inicio >= 0:
                detalhes, _fim = json.JSONDecoder().raw_decode(
                    html[inicio + len(marcador):].lstrip(),
                )
                detalhes = detalhes if isinstance(detalhes, dict) else {}
                duracao = int(detalhes.get("lengthSeconds") or 0)
                if (
                    str(detalhes.get("videoId") or "") == video_id
                    and str(detalhes.get("title") or "").strip()
                ):
                    return {
                        "video_id": video_id,
                        "title": str(detalhes.get("title") or "").strip(),
                        "channel": str(detalhes.get("author") or "").strip(),
                        "duration_seconds": duracao if 0 < duracao <= 86_400 else None,
                    }
        except Exception:
            pass
        endpoint = (
            "https://www.youtube.com/oembed?format=json&url="
            + pagina
        )
        try:
            with urlopen(Request(endpoint, headers={"User-Agent": "Laylay/1"}), timeout=6) as resposta:
                bruto = json.loads(resposta.read(128_000).decode("utf-8"))
            return {
                "video_id": video_id,
                "title": str(bruto.get("title") or "").strip(),
                "channel": str(bruto.get("author_name") or "").strip(),
            }
        except Exception:
            return {}

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

    def detalhar_playlist(self, nome: str, **paginacao: Any) -> dict[str, Any]:
        return dict(self.playlists_usuario.detalhar(nome, **paginacao) or {})

    def tocar_faixa_exata(self, nome: str, video_id: str, revisao: str) -> dict[str, Any]:
        return dict(self.playlists_usuario.tocar_faixa_exata(nome, video_id, revisao) or {})

    def adicionar_url_playlist(self, nome: str, url: str) -> dict[str, Any]:
        try:
            metadados = dict(self.youtube_metadata_resolver(str(url or "")) or {})
        except Exception:
            metadados = {}
        return dict(self.playlists_usuario.adicionar_url_resolvida(nome, url, metadados) or {})

    def copiar_faixa_exata(
        self, origem: str, destino: str, video_id: str, revisao: str,
    ) -> dict[str, Any]:
        return dict(self.playlists_usuario.copiar_faixa_exata(origem, destino, video_id, revisao) or {})

    def mover_faixa_exata(
        self, origem: str, destino: str, video_id: str, revisao: str,
    ) -> dict[str, Any]:
        return dict(self.playlists_usuario.mover_faixa_exata(origem, destino, video_id, revisao) or {})

    def remover_faixa_exata(self, nome: str, video_id: str, revisao: str) -> dict[str, Any]:
        return dict(self.playlists_usuario.remover_faixa_exata(nome, video_id, revisao) or {})

    def definir_capa_playlist(self, nome: str, caminho: str, revisao: str) -> dict[str, Any]:
        return dict(self.playlists_usuario.definir_capa(nome, caminho, revisao) or {})

    def restaurar_capa_playlist(self, nome: str, revisao: str) -> dict[str, Any]:
        return dict(self.playlists_usuario.restaurar_capa(nome, revisao) or {})

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
