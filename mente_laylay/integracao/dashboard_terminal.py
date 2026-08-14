"""Projeção pública e não bloqueante do painel desktop da Laylay.

O cliente gráfico nunca consulta SQLite, sensores ou estado interno diretamente.
Este runtime coleta as fontes em uma thread própria, reduz tudo a um contrato
pequeno e mantém ``snapshot()`` como uma leitura O(1) do último retrato.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import math
import os
import platform
import re
import threading
import time
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import parse_qs, urlparse

from mente_laylay.especialistas.capacidades import INTENTS_SOMENTE_LEITURA
from mente_laylay.integracao.acoes_terminal import ACOES_RAPIDAS_TERMINAL


_PROVEDORES = {
    "ollama": "Local",
    "portatil": "Portátil",
    "openrouter": "OpenRouter",
}
_ESTADOS_LLM_DEGRADADOS = {
    "degradado", "degraded", "falha", "failed", "indisponivel",
    "indisponível", "offline", "timeout",
}
_PADRAO_SENSIVEL = re.compile(
    r"(?ix)(?:"
    r"\b(?:senha|password|token|api[ _-]?key|chave[ _-]?api|cpf|cnpj|cvv|pin|pix)\b"
    r"|\bsk-(?:or-v1-)?[a-z0-9_-]{8,}\b"
    r"|\bgh[pousr]_[a-z0-9]{16,}\b"
    r"|\beyj[a-z0-9_-]{6,}\.[a-z0-9_-]{6,}\.[a-z0-9_-]{6,}\b"
    r"|https?://|(?:[a-z]:\\)|(?:\\\\[\w.-]+\\)"
    r"|\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b"
    r"|\b(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?\d{4,5}[- ]?\d{4}\b"
    r")"
)
_PADRAO_TEMA_SENSIVEL = re.compile(
    r"(?ix)\b(?:"
    r"sa[uú]de|doen[çc]a|diagn[oó]stico|m[eé]dic[oa]|medica[çc][aã]o|"
    r"rem[eé]dio|terapia|sexual|[ií]ntim[oa]|religi[aã]o|religioso|"
    r"pol[ií]tica|partido|voto|sal[aá]rio|d[ií]vida|conta banc[aá]ria|"
    r"cart[aã]o|endere[çc]o"
    r")\b"
)
_PADRAO_COMANDO_EM_NOME_PLAYLIST = re.compile(
    r"(?i)(?:[;&|<>]|\b(?:apaga|delete|deleta|remove|exclui|desliga|liga|"
    r"abre|fecha|envia|manda|executa|roda|formata|reinicia)\b)"
)


def _texto(valor: Any, limite: int) -> str:
    return re.sub(r"\s+", " ", str(valor or "").replace("\x00", " ")).strip()[:limite]


def _numero(valor: Any, *, minimo: float, maximo: float) -> float | None:
    if isinstance(valor, bool):
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numero) or numero < minimo or numero > maximo:
        return None
    return round(numero, 1)


def _metrica_indisponivel(unidade: str, max_age_s: float) -> dict[str, Any]:
    return {
        "value": None,
        "unit": unidade,
        "freshness": "unavailable",
        "observed_at": 0.0,
        "max_age_s": float(max_age_s),
    }


def _saude_indisponivel(rotulo: str) -> dict[str, Any]:
    return {
        "state": "unavailable",
        "label": rotulo,
        "freshness": "unavailable",
        "observed_at": 0.0,
    }


def _retrato_inicial() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "unavailable",
        "generated_at": 0.0,
        "sequence": 0,
        "health": {
            "llm": _saude_indisponivel("Aguardando estado"),
            "microphone": _saude_indisponivel("Aguardando estado"),
            "memory": _saude_indisponivel("Aguardando estado"),
        },
        "context": {
            "project": "Laylay",
            "mode": "—",
            "interaction_mode": "chat",
            "city": "—",
            "game_active": False,
            "game_name": "",
            "freshness": "unavailable",
            "observed_at": 0.0,
        },
        "memory_recent": [],
        "quick_actions": [],
        "music": {
            "title": "",
            "channel": "",
            "artwork_url": "",
            "state": "unavailable",
            "position_seconds": 0.0,
            "duration_seconds": 0.0,
            "playlist": "",
            "controls_available": False,
            "volume_percent": None,
            "player_volume_percent": None,
            "muted": False,
            "replay_available": False,
            "repeat_enabled": False,
            "repeat_available": False,
            "shuffle_available": False,
            "audio_output": {"name": "", "source": "", "available": False},
            "lights": {"configured": False, "sync_available": False},
            "freshness": "unavailable",
            "observed_at": 0.0,
            "queue": [],
            "queue_freshness": "unavailable",
            "queue_observed_at": 0.0,
            "catalog": [],
            "catalog_available": False,
            "catalog_play_available": False,
            "catalog_observed_at": 0.0,
            "context_music": {
                "summary": "",
                "recommendation": "",
                "basis": [],
                "freshness": "unavailable",
                "observed_at": 0.0,
            },
            "lyrics": {
                "status": "idle",
                "source": "",
                "synced": False,
                "track_name": "",
                "artist_name": "",
                "plain_text": "",
                "lines": [],
                "observed_at": 0.0,
            },
        },
        "routines": {
            "items": [],
            "freshness": "unavailable",
            "observed_at": 0.0,
        },
        "system": {
            "cpu_percent": _metrica_indisponivel("%", 5.0),
            "gpu_percent": _metrica_indisponivel("%", 5.0),
            "ram_percent": _metrica_indisponivel("%", 5.0),
            "vram_percent": _metrica_indisponivel("%", 5.0),
            "network_percent": _metrica_indisponivel("%", 5.0),
            "download_mbps": _metrica_indisponivel("Mbps", 5.0),
            "upload_mbps": _metrica_indisponivel("Mbps", 5.0),
            "disk_percent": _metrica_indisponivel("%", 20.0),
            "temperature_c": _metrica_indisponivel("°C", 120.0),
            "uptime_seconds": _metrica_indisponivel("s", 20.0),
        },
    }


def _publicar_texto_memoria(texto: Any, *, fallback: str) -> str:
    limpo = _texto(texto, 160)
    if (
        not limpo
        or _PADRAO_SENSIVEL.search(limpo)
        or _PADRAO_TEMA_SENSIVEL.search(limpo)
    ):
        return fallback
    return limpo


def _nome_playlist_publico(valor: Any) -> str:
    nome = _texto(valor, 80)
    if (
        not nome
        or _PADRAO_SENSIVEL.search(nome)
        or _PADRAO_COMANDO_EM_NOME_PLAYLIST.search(nome)
    ):
        return ""
    return nome


def _instante_iso(valor: Any) -> float:
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return max(0.0, float(valor))
    texto = _texto(valor, 64)
    if not texto:
        return 0.0
    try:
        return max(0.0, datetime.fromisoformat(texto).timestamp())
    except (TypeError, ValueError, OSError):
        return 0.0


def _video_id_youtube(valor: Any) -> str:
    bruto = _texto(valor, 500)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", bruto):
        return bruto
    try:
        url = urlparse(bruto)
        host = url.netloc.casefold().removeprefix("www.")
        partes = [parte for parte in url.path.split("/") if parte]
        candidato = (
            partes[0] if host == "youtu.be" and partes else
            (parse_qs(url.query).get("v") or [""])[0]
        )
        if not candidato and len(partes) >= 2 and partes[0] in {
            "shorts", "embed", "live",
        }:
            candidato = partes[1]
        return candidato if re.fullmatch(r"[A-Za-z0-9_-]{11}", candidato) else ""
    except (TypeError, ValueError):
        return ""


class DashboardTerminalRuntime:
    """Coleta isolada e cacheada das fontes usadas pelo Terminal 3."""

    def __init__(
        self,
        *,
        configuracao_getter: Callable[[], Mapping[str, Any]],
        llm_getter: Callable[[], Mapping[str, Any]],
        interacao_getter: Callable[[], Mapping[str, Any]],
        memoria_saude_getter: Callable[[], Mapping[str, Any]],
        agenda_getter: Callable[[], Sequence[Mapping[str, Any]]],
        aprendizados_getter: Callable[..., Sequence[Mapping[str, Any]]],
        estado_mental_getter: Callable[[], Mapping[str, Any]],
        contexto_jogo_getter: Callable[[], Mapping[str, Any]],
        psutil_mod: Any,
        capacidade_getter: Callable[[str], Mapping[str, Any]] | None = None,
        temperatura_getter: Callable[[], Any] | None = None,
        gpu_getter: Callable[[], Mapping[str, Any]] | None = None,
        network_getter: Callable[[], Mapping[str, Any]] | None = None,
        musica_getter: Callable[[], Mapping[str, Any]] | None = None,
        playlists_getter: Callable[[], Sequence[Mapping[str, Any]]] | None = None,
        playlist_queue_getter: Callable[[], Sequence[Mapping[str, Any]]] | None = None,
        audio_output_getter: Callable[[], Mapping[str, Any]] | None = None,
        volume_getter: Callable[[], Any] | None = None,
        iot_getter: Callable[[], Mapping[str, Any]] | None = None,
        letras_getter: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        projeto: str = "Laylay",
        cidade: str = "",
        intervalo_s: float = 1.5,
        intervalo_memoria_s: float = 15.0,
        intervalo_temperatura_s: float = 60.0,
        clock: Callable[[], float] = time.time,
        monotonic: Callable[[], float] = time.monotonic,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.configuracao_getter = configuracao_getter
        self.llm_getter = llm_getter
        self.interacao_getter = interacao_getter
        self.memoria_saude_getter = memoria_saude_getter
        self.agenda_getter = agenda_getter
        self.aprendizados_getter = aprendizados_getter
        self.estado_mental_getter = estado_mental_getter
        self.contexto_jogo_getter = contexto_jogo_getter
        self.capacidade_getter = capacidade_getter
        self.psutil = psutil_mod
        self.temperatura_getter = temperatura_getter
        self.gpu_getter = gpu_getter
        self.network_getter = network_getter
        self.musica_getter = musica_getter
        self.playlists_getter = playlists_getter
        self.playlist_queue_getter = playlist_queue_getter
        self.audio_output_getter = audio_output_getter
        self.volume_getter = volume_getter
        self.iot_getter = iot_getter
        self.letras_getter = letras_getter
        self.projeto = _texto(projeto, 80) or "Laylay"
        self.cidade = _texto(cidade, 80)
        self.intervalo_s = max(0.25, float(intervalo_s))
        self.intervalo_memoria_s = max(5.0, float(intervalo_memoria_s))
        self.intervalo_temperatura_s = max(10.0, float(intervalo_temperatura_s))
        self.clock = clock
        self.monotonic = monotonic
        self.log = log
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._cache = _retrato_inicial()
        self._coleta_em_andamento = False
        self._ultima_solicitacao = float("-inf")
        self._thread: threading.Thread | None = None
        self._memoria_thread: threading.Thread | None = None
        self._temperatura_thread: threading.Thread | None = None
        self._temperatura_ultima_solicitacao = float("-inf")
        self._memoria_ultima_coleta = float("-inf")
        self._falhas = 0
        # P10.5 — especificações reais do sistema.
        # Inventário estático coletado uma vez.
        self._system_info_cache: dict[str, Any] = {}
        self._fontes_pendentes: dict[
            str, tuple[threading.Thread, dict[str, Any]]
        ] = {}
        try:
            self.psutil.cpu_percent(interval=None)
        except Exception:
            pass

    def _acoes_rapidas(self) -> list[dict[str, Any]]:
        """Projeta o catálogo vivo sem criar uma segunda lista de capacidades."""
        resultado: list[dict[str, Any]] = []
        for definicao in ACOES_RAPIDAS_TERMINAL:
            acao_id = str(definicao["id"])
            intent = str(definicao.get("intent") or "")
            pedido = str(definicao.get("request") or "")
            if not intent:
                estado = "unavailable"
                motivo = "capacidade_ainda_nao_registrada"
            elif not pedido:
                estado = "requires_input"
                motivo = "precisa_de_um_alvo_antes_de_enviar"
            elif not callable(self.capacidade_getter):
                estado = "unavailable"
                motivo = "catalogo_vivo_indisponivel"
            else:
                capacidade = dict(self.capacidade_getter(intent) or {})
                estado_vivo = str(capacidade.get("estado") or "").casefold()
                disponivel = capacidade.get("disponivel") is True
                if not disponivel or estado_vivo == "indisponivel":
                    estado = "unavailable"
                elif estado_vivo == "degradado":
                    estado = "degraded"
                else:
                    estado = "available"
                motivo = str(capacidade.get("motivo") or "")
            resultado.append({
                "id": acao_id,
                "intent": intent,
                "state": estado,
                "reason": motivo,
            })
        return resultado

    def snapshot(self) -> dict[str, Any]:
        """Devolve o cache imediatamente e agenda atualização quando necessário."""
        agora = float(self.monotonic())
        with self._lock:
            deve_coletar = bool(
                not self._stop.is_set()
                and not self._coleta_em_andamento
                and agora - self._ultima_solicitacao >= self.intervalo_s
            )
            if deve_coletar:
                self._coleta_em_andamento = True
                self._ultima_solicitacao = agora
                self._thread = threading.Thread(
                    target=self._coletar,
                    name="Laylay-Dashboard-State",
                    daemon=True,
                )
                self._thread.start()
            retrato = deepcopy(self._cache)
        self._marcar_frescor_por_idade(retrato, float(self.clock()))
        return retrato

    @staticmethod
    def _marcar_frescor_por_idade(retrato: dict[str, Any], agora: float) -> None:
        limites_saude = {"llm": 5.0, "microphone": 5.0, "memory": 60.0}
        saude = retrato.get("health") if isinstance(retrato.get("health"), dict) else {}
        for chave, limite in limites_saude.items():
            item = saude.get(chave)
            if not isinstance(item, dict) or item.get("state") == "unavailable":
                continue
            observado = float(item.get("observed_at") or 0.0)
            if observado <= 0 or agora - observado > limite:
                item["freshness"] = "stale"
        contexto = retrato.get("context")
        if isinstance(contexto, dict):
            observado = float(contexto.get("observed_at") or 0.0)
            if observado <= 0 or agora - observado > 5.0:
                contexto["freshness"] = "stale" if observado else "unavailable"
        sistema = retrato.get("system") if isinstance(retrato.get("system"), dict) else {}
        for metrica in sistema.values():
            if not isinstance(metrica, dict) or metrica.get("value") is None:
                continue
            observado = float(metrica.get("observed_at") or 0.0)
            limite = float(metrica.get("max_age_s") or 0.0)
            if observado <= 0 or (limite > 0 and agora - observado > limite):
                metrica["freshness"] = "stale"
        musica = retrato.get("music")
        if isinstance(musica, dict) and musica.get("freshness") != "unavailable":
            observado = float(musica.get("observed_at") or 0.0)
            idade_musica = agora - observado if observado > 0 else float("inf")
            if idade_musica > 30.0:
                musica.update({
                    "title": "",
                    "channel": "",
                    "artwork_url": "",
                    "state": "unavailable",
                    "position_seconds": 0.0,
                    "duration_seconds": 0.0,
                    "controls_available": False,
                    "freshness": "unavailable",
                    "observed_at": 0.0,
                    "queue": [],
                    "queue_freshness": "unavailable",
                    "queue_observed_at": 0.0,
                })
            elif observado <= 0 or idade_musica > 12.0:
                musica["freshness"] = "stale" if observado else "unavailable"
                musica["controls_available"] = False
        rotinas = retrato.get("routines")
        if isinstance(rotinas, dict) and rotinas.get("freshness") != "unavailable":
            observado = float(rotinas.get("observed_at") or 0.0)
            if observado <= 0 or agora - observado > 60.0:
                rotinas["freshness"] = "stale" if observado else "unavailable"
        if any(
            isinstance(item, dict) and item.get("freshness") == "stale"
            for item in (
                *saude.values(),
                contexto,
                *sistema.values(),
                musica,
                rotinas,
            )
        ):
            retrato["status"] = "partial"

    def _musica(self, agora: float) -> dict[str, Any]:
        if not callable(self.musica_getter):
            return deepcopy(_retrato_inicial()["music"])
        bruto = dict(self.musica_getter() or {})
        player = dict(bruto.get("player") or {}) if isinstance(
            bruto.get("player"), Mapping,
        ) else bruto
        estado = _texto(
            player.get("state") or player.get("musica_atual_status"), 24,
        ).casefold()
        aliases = {
            "tocando": "playing", "reproduzindo": "playing",
            "pausada": "paused", "pausado": "paused",
            "finalizada": "ended", "finalizado": "ended",
        }
        estado = aliases.get(estado, estado)
        if estado not in {"playing", "paused", "ended"}:
            estado = "unknown" if player else "unavailable"
        observado = _instante_iso(
            player.get("observed_at") or bruto.get("musica_atual_ts")
        )
        titulo = _texto(
            player.get("title") or bruto.get("musica_atual_titulo"), 180,
        )
        if not titulo and estado == "unavailable":
            observado = 0.0
        idade = agora - observado if observado > 0 else float("inf")
        controles = bool(
            player.get("controls_available") is True
            and observado > 0
            and idade <= 12.0
        )
        video_id = (
            _video_id_youtube(player.get("video_id"))
            or _video_id_youtube(player.get("url"))
            or _video_id_youtube(bruto.get("musica_atual_url"))
        )
        artwork_url = (
            f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id) else ""
        )
        catalogo: list[dict[str, Any]] = []
        catalogo_disponivel = False
        if callable(self.playlists_getter):
            try:
                for item in list(self.playlists_getter() or ()):
                    if not isinstance(item, Mapping):
                        continue
                    nome = _nome_playlist_publico(item.get("name"))
                    if not nome:
                        continue
                    try:
                        quantidade = max(0, min(10_000, int(item.get("count") or 0)))
                    except (TypeError, ValueError):
                        quantidade = 0
                    capa_id = _video_id_youtube(item.get("artwork_video_id"))
                    catalogo.append({
                        "name": nome,
                        "count": quantidade,
                        "artwork_url": (
                            f"https://i.ytimg.com/vi/{capa_id}/hqdefault.jpg"
                            if capa_id else ""
                        ),
                    })
                catalogo_disponivel = True
            except Exception:
                catalogo = []
        try:
            capacidade_playlist = (
                dict(self.capacidade_getter("PLAYLIST_PLAY") or {})
                if callable(self.capacidade_getter) else {}
            )
        except Exception:
            capacidade_playlist = {}
        tocar_playlist_disponivel = bool(
            capacidade_playlist.get("disponivel") is True
            and str(capacidade_playlist.get("estado") or "").casefold()
            != "indisponivel"
        )
        def capacidade_disponivel(intent: str) -> bool:
            if not callable(self.capacidade_getter):
                return False
            try:
                capacidade = dict(self.capacidade_getter(intent) or {})
            except Exception:
                return False
            return bool(
                capacidade.get("disponivel") is True
                and str(capacidade.get("estado") or "").casefold()
                != "indisponivel"
            )

        saida_audio = {
            "name": "", "source": "", "available": False,
            "selected_ref": "", "switch_available": False,
            "devices": [], "observed_at": 0.0,
        }
        if callable(self.audio_output_getter):
            try:
                audio_bruto = dict(self.audio_output_getter() or {})
                nome_saida = _texto(audio_bruto.get("name"), 100)
                dispositivos_audio: list[dict[str, Any]] = []
                for item in list(audio_bruto.get("devices") or ()):
                    if not isinstance(item, Mapping):
                        continue
                    referencia = str(item.get("ref") or "").strip().casefold()
                    nome = _texto(item.get("name"), 100)
                    if (
                        nome and len(referencia) == 16
                        and all(ch in "0123456789abcdef" for ch in referencia)
                    ):
                        dispositivos_audio.append({
                            "ref": referencia,
                            "name": nome,
                            "selected": item.get("selected") is True,
                        })
                if nome_saida:
                    saida_audio = {
                        "name": nome_saida,
                        "source": _texto(audio_bruto.get("source"), 40),
                        "available": True,
                        "selected_ref": _texto(
                            audio_bruto.get("selected_ref"), 16,
                        ).casefold(),
                        "switch_available": bool(
                            audio_bruto.get("switch_available") is True
                            and dispositivos_audio
                        ),
                        "devices": dispositivos_audio,
                        "observed_at": _numero(
                            audio_bruto.get("observed_at"),
                            minimo=0, maximo=9_999_999_999,
                        ) or 0.0,
                    }
            except Exception:
                pass

        volume_sistema = None
        if callable(self.volume_getter):
            try:
                volume_sistema = _numero(
                    self.volume_getter(), minimo=0, maximo=100,
                )
            except Exception:
                pass

        luz_configurada = False
        if callable(self.iot_getter):
            try:
                dispositivos = list(
                    dict(self.iot_getter() or {}).get("dispositivos") or ()
                )
                luz_configurada = any(
                    isinstance(item, Mapping)
                    and str(item.get("tipo") or "").startswith("lampada")
                    and "ajustar_cor" in set(item.get("capacidades") or ())
                    for item in dispositivos
                )
            except Exception:
                pass
        fila: list[dict[str, Any]] = []
        fila_fonte = "youtube"
        for item in list(player.get("queue") or ()):
            if not isinstance(item, Mapping):
                continue
            titulo_fila = _texto(item.get("title"), 160)
            if not titulo_fila:
                continue
            fila_video_id = _video_id_youtube(item.get("video_id"))
            fila.append({
                "title": titulo_fila,
                "channel": _texto(item.get("channel"), 100),
                "item_id": fila_video_id,
                "duration_seconds": _numero(
                    item.get("duration_seconds"), minimo=0, maximo=86_400,
                ) or 0.0,
                "artwork_url": (
                    f"https://i.ytimg.com/vi/{fila_video_id}/hqdefault.jpg"
                    if fila_video_id else ""
                ),
            })
        fila_observada = _instante_iso(player.get("queue_observed_at"))
        if not fila and callable(self.playlist_queue_getter):
            try:
                fila_interna = list(self.playlist_queue_getter() or ())
            except Exception:
                fila_interna = []
            for item in fila_interna:
                if not isinstance(item, Mapping):
                    continue
                titulo_fila = _texto(item.get("title"), 160)
                if not titulo_fila:
                    continue
                fila_video_id = _video_id_youtube(item.get("artwork_video_id"))
                fila.append({
                    "title": titulo_fila,
                    "channel": _texto(item.get("channel"), 100),
                    "item_id": fila_video_id,
                    "duration_seconds": 0.0,
                    "artwork_url": (
                        f"https://i.ytimg.com/vi/{fila_video_id}/hqdefault.jpg"
                        if fila_video_id else ""
                    ),
                })
            if fila:
                fila_observada = agora
                fila_fonte = "laylay_playlist"
        idade_fila = agora - fila_observada if fila_observada > 0 else float("inf")
        expirado = idade > 30.0
        nome_playlist = _texto(
            bruto.get("playlist") or bruto.get("name")
            or bruto.get("playlist_ativa"), 100,
        )
        hora = datetime.fromtimestamp(agora).hour
        periodo = (
            "madrugada" if hora < 6 else "manhã" if hora < 12
            else "tarde" if hora < 18 else "noite"
        )
        contexto_musical = {
            "summary": (
                f"É {periodo} e a playlist {nome_playlist} está ativa."
                if nome_playlist else
                f"É {periodo}; nenhuma playlist da Laylay está ativa agora."
            ),
            "recommendation": "",
            "basis": ["horario_local"] + (["playlist_ativa"] if nome_playlist else []),
            "freshness": "fresh",
            "observed_at": agora,
        }
        if nome_playlist:
            contexto_musical["recommendation"] = (
                f"Posso manter a sequência de {nome_playlist}; foi a playlist que você escolheu."
            )

        letras = deepcopy(_retrato_inicial()["music"]["lyrics"])
        if callable(self.letras_getter) and not expirado and titulo:
            try:
                letras = dict(self.letras_getter({
                    "title": titulo,
                    "channel": _texto(player.get("channel"), 120),
                    "duration_seconds": _numero(
                        player.get("duration_seconds"), minimo=0, maximo=86_400,
                    ) or 0.0,
                    "video_id": video_id,
                    "state": estado,
                }) or letras)
            except Exception:
                letras = deepcopy(_retrato_inicial()["music"]["lyrics"])
                letras["status"] = "error"
                letras["source"] = "lrclib"
                letras["observed_at"] = agora
        return {
            "title": "" if expirado else titulo,
            "channel": "" if expirado else _texto(player.get("channel"), 120),
            "artwork_url": "" if expirado else artwork_url,
            "state": "unavailable" if expirado else estado,
            "position_seconds": 0.0 if expirado else (_numero(
                player.get("position_seconds"), minimo=0, maximo=86_400,
            ) or 0.0),
            "duration_seconds": 0.0 if expirado else (_numero(
                player.get("duration_seconds"), minimo=0, maximo=86_400,
            ) or 0.0),
            "playlist": nome_playlist,
            "controls_available": controles,
            "volume_percent": volume_sistema,
            "player_volume_percent": None if expirado else _numero(
                player.get("volume_percent"), minimo=0, maximo=100,
            ),
            "muted": bool(not expirado and player.get("muted") is True),
            "replay_available": bool(
                not expirado and controles
                and capacidade_disponivel("MEDIA_CONTROL")
            ),
            "repeat_enabled": bool(
                not expirado and player.get("repeat_enabled") is True
            ),
            "repeat_available": bool(
                not expirado and controles
                and capacidade_disponivel("MEDIA_CONTROL")
            ),
            "shuffle_available": bool(
                not expirado and tocar_playlist_disponivel
                and capacidade_disponivel("TOCAR_PLAYLIST_SHUFFLE")
                and bool(
                    bruto.get("playlist") or bruto.get("name")
                    or bruto.get("playlist_ativa")
                )
            ),
            "audio_output": saida_audio,
            "lights": {
                "configured": luz_configurada,
                # A lâmpada e a música possuem executores independentes. Ainda
                # não existe um coordenador que confirme sincronização contínua.
                "sync_available": False,
            },
            "freshness": (
                "fresh" if observado > 0 and idade <= 12.0
                else "stale" if observado > 0 and idade <= 30.0
                else "unavailable"
            ),
            "observed_at": observado if idade <= 30.0 else 0.0,
            "catalog": catalogo,
            "catalog_available": catalogo_disponivel,
            "catalog_play_available": tocar_playlist_disponivel,
            "catalog_observed_at": agora if catalogo_disponivel else 0.0,
            "queue": fila if idade_fila <= 30.0 else [],
            "queue_source": fila_fonte if fila and idade_fila <= 30.0 else "",
            "queue_freshness": (
                "fresh" if fila_observada > 0 and idade_fila <= 12.0
                else "stale" if fila_observada > 0 and idade_fila <= 30.0
                else "unavailable"
            ),
            "queue_observed_at": fila_observada if idade_fila <= 30.0 else 0.0,
            "context_music": contexto_musical,
            "lyrics": letras,
        }

    def _rotinas_publicas(self, agora: float) -> dict[str, Any]:
        candidatos: list[tuple[tuple[int, float], dict[str, Any]]] = []
        dias_validos = {"seg", "ter", "qua", "qui", "sex", "sab", "dom"}
        for item in self.agenda_getter() or ():
            if not isinstance(item, Mapping) or not bool(item.get("ativo", True)):
                continue
            tipo = _texto(item.get("tipo"), 20).casefold()
            if tipo not in {"once", "daily", "weekly"}:
                continue
            if _texto(item.get("origem"), 40).casefold() != "pedido_usuario":
                continue
            if _texto(item.get("evidencia"), 40).casefold() != "persistencia_local":
                continue
            nome = _publicar_texto_memoria(
                item.get("nome") or item.get("descricao"),
                fallback=("Agendamento pessoal" if tipo == "once" else "Rotina pessoal"),
            )
            data = ""
            if tipo == "once":
                try:
                    execucao_ts = float(item.get("ts_execucao") or 0.0)
                except (TypeError, ValueError):
                    execucao_ts = 0.0
                if not math.isfinite(execucao_ts) or execucao_ts <= 0:
                    continue
                instante = datetime.fromtimestamp(execucao_ts)
                hora = instante.strftime("%H:%M")
                data = instante.strftime("%Y-%m-%d")
                dias: list[str] = []
                ordem = (0, execucao_ts)
            else:
                hora = _texto(item.get("hora"), 8)
                if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", hora):
                    hora = "—"
                dias_brutos = (
                    item.get("dias") if isinstance(item.get("dias"), list) else []
                )
                dias = [
                    _texto(dia, 3).casefold() for dia in dias_brutos
                    if _texto(dia, 3).casefold() in dias_validos
                ]
                if tipo == "daily" and not dias:
                    dias = ["todos"]
                minutos = (
                    int(hora[:2]) * 60 + int(hora[3:])
                    if re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", hora)
                    else 1_440
                )
                ordem = (1, float(minutos))
            publico = {
                "name": nome,
                "time": hora,
                "days": dias[:7],
                "active": True,
                "can_disable": True,
            }
            if data:
                publico["date"] = data
            candidatos.append((ordem, publico))
        candidatos.sort(key=lambda candidato: candidato[0])
        return {
            "items": [item for _ordem, item in candidatos[:6]],
            "freshness": "fresh",
            "observed_at": agora,
        }

    @staticmethod
    def _calcular_status(
        saude: Mapping[str, Any],
        contexto: Mapping[str, Any],
        sistema: Mapping[str, Any],
        *,
        falhas: int = 0,
    ) -> str:
        itens_saude = tuple(
            item for item in saude.values() if isinstance(item, Mapping)
        )
        metricas_principais = tuple(
            sistema.get(chave) for chave in (
                "cpu_percent", "ram_percent", "disk_percent",
                "uptime_seconds",
            )
        )
        tem_sistema = any(
            isinstance(item, Mapping) and item.get("value") is not None
            for item in metricas_principais
        )
        indisponiveis = sum(
            item.get("state") == "unavailable" for item in itens_saude
        )
        if itens_saude and indisponiveis == len(itens_saude) and not tem_sistema:
            return "unavailable"
        saude_parcial = any(
            item.get("state") in {"degraded", "unavailable"}
            or item.get("freshness") in {"stale", "unavailable"}
            for item in itens_saude
        )
        sistema_parcial = any(
            not isinstance(item, Mapping)
            or item.get("value") is None
            or item.get("freshness") != "fresh"
            for item in metricas_principais
        )
        contexto_parcial = contexto.get("freshness") != "fresh"
        return (
            "partial"
            if falhas or saude_parcial or sistema_parcial or contexto_parcial
            else "ok"
        )

    def _chamar_limitado(
        self,
        chave: str,
        funcao: Callable[[], Any],
        *,
        timeout_s: float = 0.5,
    ) -> Any:
        """Evita que uma integração prenda o único ciclo do dashboard."""
        if self._stop.is_set():
            raise RuntimeError("dashboard encerrado")
        with self._lock:
            if self._stop.is_set():
                raise RuntimeError("dashboard encerrado")
            pendente = self._fontes_pendentes.get(chave)
            if pendente is None:
                caixa: dict[str, Any] = {}

                def executar() -> None:
                    try:
                        caixa["valor"] = funcao()
                    except Exception as erro:  # transportado, nunca logado bruto
                        caixa["erro"] = erro

                thread = threading.Thread(
                    target=executar,
                    name=f"Laylay-Dashboard-Fonte-{chave}",
                    daemon=True,
                )
                self._fontes_pendentes[chave] = (thread, caixa)
                thread.start()
            else:
                thread, caixa = pendente
        thread.join(timeout=max(0.01, float(timeout_s)))
        if thread.is_alive():
            raise TimeoutError(f"coletor {chave} excedeu o orçamento")
        with self._lock:
            self._fontes_pendentes.pop(chave, None)
        if "erro" in caixa:
            raise caixa["erro"]
        return caixa.get("valor")

    def _saude_llm(self, agora: float) -> tuple[dict[str, Any], str]:
        configuracao = dict(self.configuracao_getter() or {})
        diagnostico = dict(self.llm_getter() or {})
        provedor = _texto(configuracao.get("provider"), 32).casefold() or "ollama"
        modelo = _texto(configuracao.get("model"), 120)
        disponivel = bool(
            diagnostico.get("modelo_disponivel", diagnostico.get("disponivel", False))
            and diagnostico.get("prompt_disponivel", True)
            and diagnostico.get("estado_disponivel", True)
        )
        falhas_consecutivas = int(diagnostico.get("falhas_consecutivas") or 0)
        estado_bruto = _texto(diagnostico.get("estado"), 40).casefold()
        sucessos = max(0, int(diagnostico.get("sucessos") or 0))
        if not disponivel:
            estado, rotulo = "unavailable", "Indisponível"
        elif falhas_consecutivas or estado_bruto in _ESTADOS_LLM_DEGRADADOS:
            estado, rotulo = "degraded", "Degradado"
        elif sucessos > 0:
            estado, rotulo = "online", "Online"
        else:
            estado, rotulo = "ready", "Pronto"
        return ({
            "state": estado,
            "label": rotulo,
            "provider": provedor,
            "provider_label": _PROVEDORES.get(provedor, provedor.title()),
            "model": modelo,
            "freshness": "fresh",
            "observed_at": agora,
        }, provedor)

    def _saude_microfone(self, agora: float) -> tuple[dict[str, Any], str]:
        estado = dict(self.interacao_getter() or {})
        modo = _texto(estado.get("interaction_mode"), 16).casefold()
        if modo not in {"chat", "voice"}:
            modo = "chat"
        disponivel = bool(estado.get("voice_available"))
        if not disponivel:
            valor, rotulo = "unavailable", "Indisponível"
        elif modo == "voice":
            valor, rotulo = "online", "Ativo"
        else:
            valor, rotulo = "paused", "Pausado no chat"
        return ({
            "state": valor,
            "label": rotulo,
            "freshness": "fresh",
            "observed_at": agora,
        }, modo)

    def _saude_memoria(self, agora: float) -> dict[str, Any]:
        diagnostico = dict(self.memoria_saude_getter() or {})
        disponivel = bool(diagnostico.get("disponivel"))
        persistencia = bool(diagnostico.get("persistencia_local", disponivel))
        if disponivel and persistencia:
            estado, rotulo = "online", "Ativa"
        elif disponivel:
            estado, rotulo = "degraded", "Degradada"
        else:
            estado, rotulo = "unavailable", "Indisponível"
        return {
            "state": estado,
            "label": rotulo,
            "freshness": "fresh",
            "observed_at": agora,
        }

    def _contexto(self, agora: float, provedor: str, modo: str) -> dict[str, Any]:
        jogo = dict(self.contexto_jogo_getter() or {})
        ativo = bool(jogo.get("ativo"))
        processo = os.path.basename(_texto(jogo.get("processo"), 120))
        titulo = _texto(jogo.get("titulo"), 100)
        nome_jogo = titulo or processo if ativo else ""
        return {
            "project": self.projeto,
            "mode": _PROVEDORES.get(provedor, provedor.title()),
            "interaction_mode": modo,
            "city": self.cidade,
            "game_active": ativo,
            "game_name": nome_jogo,
            "freshness": "fresh",
            "observed_at": agora,
        }

    def _lembrete_publico(self, agora: float) -> dict[str, Any] | None:
        candidatos: list[tuple[float, Mapping[str, Any]]] = []
        for item in self.agenda_getter() or ():
            if not isinstance(item, Mapping) or not bool(item.get("ativo", True)):
                continue
            if _texto(item.get("tipo"), 20).casefold() not in {"", "once"}:
                continue
            if _texto(item.get("origem"), 40).casefold() != "pedido_usuario":
                continue
            if _texto(item.get("evidencia"), 40).casefold() != "persistencia_local":
                continue
            if item.get("intencao_no_disparo") or item.get("comandos_no_disparo"):
                continue
            instante = _instante_iso(item.get("ts_execucao"))
            if instante <= 0:
                continue
            candidatos.append((instante, item))
        if not candidatos:
            return None
        instante, item = min(candidatos, key=lambda par: par[0])
        texto = _publicar_texto_memoria(
            item.get("nome") or item.get("descricao"),
            fallback="Você tem um lembrete",
        )
        quando = datetime.fromtimestamp(instante).strftime("%d/%m às %H:%M")
        if instante < agora:
            quando = f"Atrasado · {quando}"
        return {
            "kind": "reminder",
            "summary": texto,
            "detail": quando,
            "source": "agenda_confirmed",
            "timestamp": instante,
        }

    def _preferencia_publica(self) -> dict[str, Any] | None:
        for item in self.aprendizados_getter(consulta="", limit=20) or ():
            if not isinstance(item, Mapping):
                continue
            if (
                _texto(item.get("fonte"), 40).casefold() != "aprendizado_semantico"
                or _texto(item.get("natureza"), 40).casefold() != "confirmado"
                or _texto(item.get("tipo"), 40).casefold() != "preferencia"
                or item.get("confirmado_usuario") is not True
            ):
                continue
            texto = _publicar_texto_memoria(
                item.get("texto"), fallback="Preferência confirmada por você",
            )
            return {
                "kind": "preference",
                "summary": texto,
                "detail": "Confirmado por você",
                "source": "user_confirmed",
                "timestamp": _instante_iso(item.get("atualizado_em")),
            }
        return None

    def _tarefa_publica(self, agora: float) -> dict[str, Any] | None:
        estado = dict(self.estado_mental_getter() or {})
        if isinstance(estado.get("mental"), Mapping):
            estado = dict(estado["mental"])
        contrato = dict(estado.get("ultima_acao_contrato") or {})
        intent = _texto(contrato.get("intent"), 80).upper()
        if (
            not intent
            or intent in INTENTS_SOMENTE_LEITURA
            or contrato.get("executou") is not True
            or contrato.get("confirmado") is not True
        ):
            return None
        instante = _instante_iso(estado.get("ultima_acao_ts"))
        if instante <= 0 or instante > agora + 30.0 or agora - instante > 3_600.0:
            return None
        resumo_por_intent = {
            "APP_OPEN": "Aplicativo aberto",
            "CLOSE_APP": "Aplicativo fechado",
            "MAXIMIZE_APP": "Janela maximizada",
            "CREATE_FILE": "Arquivo criado",
            "CREATE_FOLDER": "Pasta criada",
            "DELETE_ITEM": "Item enviado para a lixeira",
            "IOT_CONTROL": "Dispositivo ajustado",
            "PLAYLIST_ADD": "Música adicionada à playlist",
            "PLAYLIST_PLAY": "Playlist enviada ao player",
            "MUSIC_SEARCH": "Música enviada ao player",
            "MEDIA_CONTROL": "Controle de mídia aplicado",
            "INBOX_ADD": "Ideia guardada",
        }
        texto = resumo_por_intent.get(intent, "Ação concluída")
        return {
            "kind": "task",
            "summary": texto,
            "detail": "Resultado confirmado",
            "source": "executor_confirmed",
            "timestamp": instante,
        }

    def _memoria_recente(self, agora: float) -> tuple[list[dict[str, Any]], int]:
        itens: list[dict[str, Any]] = []
        falhas = 0
        for chave, getter in (
            ("reminder", lambda: self._lembrete_publico(agora)),
            ("preference", self._preferencia_publica),
            ("task", lambda: self._tarefa_publica(agora)),
        ):
            try:
                item = self._chamar_limitado(
                    f"memory_{chave}", getter, timeout_s=0.35,
                )
            except Exception:
                falhas += 1
                item = None
            if item:
                itens.append(item)
        return itens[:3], falhas

    def _metrica(
        self,
        getter: Callable[[], Any],
        *,
        unidade: str,
        minimo: float,
        maximo: float,
        max_age_s: float,
        anterior: Mapping[str, Any] | None,
        agora: float,
    ) -> dict[str, Any]:
        try:
            valor = _numero(getter(), minimo=minimo, maximo=maximo)
        except Exception:
            valor = None
        if valor is not None:
            return {
                "value": valor,
                "unit": unidade,
                "freshness": "fresh",
                "observed_at": agora,
                "max_age_s": float(max_age_s),
            }
        anterior = dict(anterior or {})
        if anterior.get("value") is not None:
            anterior["freshness"] = "stale"
            anterior["max_age_s"] = float(max_age_s)
            return anterior
        return _metrica_indisponivel(unidade, max_age_s)


    @staticmethod
    def _capacidade_bytes(
        valor: Any,
    ) -> str:
        try:
            total = max(
                0.0,
                float(valor),
            )
        except (
            TypeError,
            ValueError,
        ):
            return "—"

        if total <= 0:
            return "—"

        gib = total / (1024 ** 3)

        if gib >= 1024:
            texto = (
                f"{gib / 1024:.1f} TB"
            )
            return texto.replace(
                ".0 TB",
                " TB",
            )

        return f"{gib:.0f} GB"

    def _info_sistema(
        self,
        gpu: Mapping[str, Any],
        raiz: str,
    ) -> dict[str, Any]:
        if not self._system_info_cache:
            sistema = str(
                platform.system() or ""
            ).strip()
            arquitetura = str(
                platform.machine() or ""
            ).strip()

            arquitetura_rotulo = (
                "64-bit"
                if "64" in arquitetura
                else arquitetura or "—"
            )

            if sistema.casefold() == "windows":
                versao_bruta = str(
                    platform.version() or ""
                )
                try:
                    build = int(
                        versao_bruta.split(
                            "."
                        )[-1]
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    build = 0

                versao = (
                    "11"
                    if build >= 22000
                    else str(
                        platform.release()
                        or ""
                    ).strip()
                )

                edicao = ""
                try:
                    edicao = str(
                        platform.win32_edition()
                        or ""
                    ).strip()
                except Exception:
                    edicao = ""

                if edicao.casefold().startswith(
                    "professional"
                ):
                    edicao = "Pro"

                partes_so = [
                    f"Windows {versao}".strip(),
                    edicao,
                    arquitetura_rotulo,
                ]
                sistema_operacional = " ".join(
                    parte
                    for parte in partes_so
                    if parte
                    and parte != "—"
                )
            else:
                sistema_operacional = " ".join(
                    parte
                    for parte in (
                        sistema,
                        str(
                            platform.release()
                            or ""
                        ).strip(),
                        arquitetura_rotulo,
                    )
                    if parte
                    and parte != "—"
                )

            cpu_nome = str(
                platform.processor()
                or ""
            ).strip()

            if os.name == "nt":
                try:
                    import winreg

                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                    ) as chave:
                        (
                            cpu_registro,
                            _,
                        ) = winreg.QueryValueEx(
                            chave,
                            "ProcessorNameString",
                        )

                    if str(
                        cpu_registro
                        or ""
                    ).strip():
                        cpu_nome = str(
                            cpu_registro
                        ).strip()
                except Exception:
                    pass

            if not cpu_nome:
                cpu_nome = str(
                    os.environ.get(
                        "PROCESSOR_IDENTIFIER",
                        "",
                    )
                ).strip()

            try:
                fisicos = self.psutil.cpu_count(
                    logical=False
                )
            except Exception:
                fisicos = None

            try:
                logicos = self.psutil.cpu_count(
                    logical=True
                )
            except Exception:
                logicos = None

            detalhes_cpu = []
            if fisicos:
                detalhes_cpu.append(
                    f"{int(fisicos)} núcleos"
                )
            if logicos:
                detalhes_cpu.append(
                    f"{int(logicos)} threads"
                )

            try:
                ram_total = (
                    self.psutil
                    .virtual_memory()
                    .total
                )
            except Exception:
                ram_total = 0

            try:
                disco_total = (
                    self.psutil
                    .disk_usage(raiz)
                    .total
                )
            except Exception:
                disco_total = 0

            self._system_info_cache = {
                "os": {
                    "value": _texto(
                        sistema_operacional,
                        160,
                    )
                    or "—",
                    "detail": "",
                },
                "cpu": {
                    "value": _texto(
                        cpu_nome,
                        180,
                    )
                    or "—",
                    "detail": " / ".join(
                        detalhes_cpu
                    ),
                },
                "gpu": {
                    "value": "—",
                    "detail": "",
                },
                "ram": {
                    "value": self._capacidade_bytes(
                        ram_total
                    ),
                    "detail": "Memória física",
                },
                "vram": {
                    "value": "—",
                    "detail": "",
                },
                "disk": {
                    "value": self._capacidade_bytes(
                        disco_total
                    ),
                    "detail": "Unidade do sistema",
                },
            }

        info = deepcopy(
            self._system_info_cache
        )

        gpu_nome = _texto(
            gpu.get("gpu_name"),
            180,
        )
        driver = _texto(
            gpu.get("driver_version"),
            80,
        )

        if gpu_nome:
            info["gpu"] = {
                "value": gpu_nome,
                "detail": (
                    f"Driver {driver}"
                    if driver
                    else ""
                ),
            }

        try:
            vram_mb = float(
                gpu.get("vram_total_mb")
            )
        except (
            TypeError,
            ValueError,
        ):
            vram_mb = 0.0

        if vram_mb > 0:
            gib = vram_mb / 1024.0
            valor_vram = (
                f"{gib:.1f} GB"
            ).replace(
                ".0 GB",
                " GB",
            )
            info["vram"] = {
                "value": valor_vram,
                "detail": "Memória dedicada",
            }

        return info

    def _sistema(self, agora: float, anterior: Mapping[str, Any]) -> dict[str, Any]:
        anterior = dict(anterior or {})
        raiz = os.path.abspath(os.sep)
        temperatura = dict(
            anterior.get("temperature_c")
            or _metrica_indisponivel("°C", 120)
        )
        observado_temperatura = float(temperatura.get("observed_at") or 0.0)
        if (
            temperatura.get("value") is not None
            and observado_temperatura > 0
            and agora - observado_temperatura > 120.0
        ):
            temperatura["freshness"] = "stale"

        def limitada(
            chave: str,
            getter: Callable[[], Any],
            *,
            timeout_s: float = 0.2,
        ) -> Any:
            return self._chamar_limitado(
                f"system_{chave}", getter, timeout_s=timeout_s,
            )

        gpu: Mapping[str, Any] = {}
        if callable(self.gpu_getter):
            try:
                resposta_gpu = limitada(
                    "gpu", self.gpu_getter, timeout_s=0.45,
                )
                gpu = resposta_gpu if isinstance(resposta_gpu, Mapping) else {}
            except Exception:
                gpu = {}

        rede: Mapping[str, Any] = {}
        if callable(self.network_getter):
            try:
                resposta_rede = limitada(
                    "network", self.network_getter, timeout_s=0.35,
                )
                rede = resposta_rede if isinstance(resposta_rede, Mapping) else {}
            except Exception:
                rede = {}

        return {
            "info": self._info_sistema(
                gpu,
                raiz,
            ),
            "cpu_percent": self._metrica(
                lambda: limitada(
                    "cpu", lambda: self.psutil.cpu_percent(interval=0.1),
                    timeout_s=0.35,
                ), unidade="%",
                minimo=0, maximo=100, max_age_s=5,
                anterior=anterior.get("cpu_percent"), agora=agora,
            ),
            "gpu_percent": self._metrica(
                lambda: gpu.get("gpu_percent"), unidade="%",
                minimo=0, maximo=100, max_age_s=5,
                anterior=anterior.get("gpu_percent"), agora=agora,
            ),
            "ram_percent": self._metrica(
                lambda: limitada(
                    "ram", lambda: self.psutil.virtual_memory().percent,
                ), unidade="%",
                minimo=0, maximo=100, max_age_s=5,
                anterior=anterior.get("ram_percent"), agora=agora,
            ),
            "vram_percent": self._metrica(
                lambda: gpu.get("vram_percent"), unidade="%",
                minimo=0, maximo=100, max_age_s=5,
                anterior=anterior.get("vram_percent"), agora=agora,
            ),
            "network_percent": self._metrica(
                lambda: rede.get("network_percent"), unidade="%",
                minimo=0, maximo=100, max_age_s=5,
                anterior=anterior.get("network_percent"), agora=agora,
            ),
            "download_mbps": self._metrica(
                lambda: rede.get("download_mbps"), unidade="Mbps",
                minimo=0, maximo=1_000_000, max_age_s=5,
                anterior=anterior.get("download_mbps"), agora=agora,
            ),
            "upload_mbps": self._metrica(
                lambda: rede.get("upload_mbps"), unidade="Mbps",
                minimo=0, maximo=1_000_000, max_age_s=5,
                anterior=anterior.get("upload_mbps"), agora=agora,
            ),
            "disk_percent": self._metrica(
                lambda: limitada(
                    "disk", lambda: self.psutil.disk_usage(raiz).percent,
                ), unidade="%",
                minimo=0, maximo=100, max_age_s=20,
                anterior=anterior.get("disk_percent"), agora=agora,
            ),
            "temperature_c": temperatura,
            "uptime_seconds": self._metrica(
                lambda: limitada(
                    "uptime",
                    lambda: max(0.0, agora - float(self.psutil.boot_time())),
                ), unidade="s",
                minimo=0, maximo=20 * 365 * 24 * 3600, max_age_s=20,
                anterior=anterior.get("uptime_seconds"), agora=agora,
            ),
        }

    def _coletar(self) -> None:
        try:
            self._coletar_impl()
        except Exception as erro:
            with self._lock:
                self._coleta_em_andamento = False
                encerrando = self._stop.is_set()
                self._falhas += 1
            if encerrando:
                return
            self.log(
                "⚠️ [TERMINAL 3:DASHBOARD] coleta isolada falhou "
                f"| tipo={type(erro).__name__}"
            )

    def _coletar_impl(self) -> None:
        agora = float(self.clock())
        with self._lock:
            anterior = deepcopy(self._cache)
        falhas_secoes = 0
        saude_anterior = dict(anterior.get("health") or {})

        def saude_stale(chave: str) -> dict[str, Any]:
            item = dict(
                saude_anterior.get(chave)
                or _saude_indisponivel("Indisponível")
            )
            if item.get("observed_at") and item.get("state") != "unavailable":
                item["freshness"] = "stale"
            return item

        try:
            llm, provedor = self._chamar_limitado(
                "llm", lambda: self._saude_llm(agora),
            )
        except Exception:
            falhas_secoes += 1
            llm = saude_stale("llm")
            provedor = str(llm.get("provider") or "")
        try:
            microfone, modo = self._chamar_limitado(
                "microphone", lambda: self._saude_microfone(agora),
            )
        except Exception:
            falhas_secoes += 1
            microfone = saude_stale("microphone")
            modo = str(
                (anterior.get("context") or {}).get("interaction_mode") or "chat"
            )
        try:
            contexto = self._chamar_limitado(
                "context", lambda: self._contexto(agora, provedor, modo),
            )
        except Exception:
            falhas_secoes += 1
            contexto = dict(anterior.get("context") or _retrato_inicial()["context"])
            contexto["freshness"] = (
                "stale" if contexto.get("observed_at") else "unavailable"
            )
        try:
            sistema = self._sistema(agora, anterior.get("system") or {})
        except Exception:
            falhas_secoes += 1
            sistema = deepcopy(
                anterior.get("system") or _retrato_inicial()["system"]
            )
            for metrica in sistema.values():
                if isinstance(metrica, dict) and metrica.get("value") is not None:
                    metrica["freshness"] = "stale"
        try:
            acoes_rapidas = self._chamar_limitado(
                "quick_actions", self._acoes_rapidas, timeout_s=0.25,
            )
        except Exception:
            falhas_secoes += 1
            acoes_rapidas = list(anterior.get("quick_actions") or [])
        try:
            musica = self._chamar_limitado(
                "music", lambda: self._musica(agora), timeout_s=0.25,
            )
        except Exception:
            falhas_secoes += 1
            musica = dict(anterior.get("music") or _retrato_inicial()["music"])
            if musica.get("observed_at"):
                musica["freshness"] = "stale"
            musica["controls_available"] = False
        # A primeira projeção precisa nascer coerente. A coleta continua fora
        # da thread da UI, mas não publicamos sequence=1 com memória ainda no
        # placeholder para logo em seguida substituí-la por outro snapshot.
        memoria_inicial: dict[str, Any] | None = None
        memoria_recente_inicial: list[dict[str, Any]] | None = None
        rotinas_iniciais: dict[str, Any] | None = None
        if (
            (saude_anterior.get("memory") or {}).get("state")
            == "unavailable"
        ):
            try:
                memoria_inicial = self._chamar_limitado(
                    "memory_health", lambda: self._saude_memoria(agora),
                    timeout_s=1.0,
                )
                memoria_recente_inicial, falhas_memoria = self._memoria_recente(agora)
                rotinas_iniciais = self._chamar_limitado(
                    "memory_routines", lambda: self._rotinas_publicas(agora),
                    timeout_s=0.5,
                )
                falhas_secoes += int(falhas_memoria)
                if falhas_memoria and memoria_inicial.get("state") == "online":
                    memoria_inicial.update(state="degraded", label="Degradada")
            except Exception:
                falhas_secoes += 1
                if memoria_inicial is not None:
                    memoria_inicial.update(
                        state="degraded", label="Degradada",
                    )
                if memoria_recente_inicial is None:
                    memoria_recente_inicial = []
                if rotinas_iniciais is None:
                    rotinas_iniciais = deepcopy(_retrato_inicial()["routines"])
        metricas_principais = (
            sistema.get("cpu_percent", {}),
            sistema.get("ram_percent", {}),
            sistema.get("disk_percent", {}),
            sistema.get("uptime_seconds", {}),
        )
        falhas_sistema = sum(
            not isinstance(item, Mapping) or item.get("value") is None
            for item in metricas_principais
        )
        if falhas_sistema:
            falhas_secoes += falhas_sistema
        with self._lock:
            if self._stop.is_set():
                self._coleta_em_andamento = False
                return
            cache_atual = self._cache
            saude_atual = cache_atual.get("health") or {}
            memoria = dict(
                memoria_inicial
                or saude_atual.get("memory")
                or _saude_indisponivel("Aguardando estado")
            )
            memoria_recente = list(
                memoria_recente_inicial
                if memoria_recente_inicial is not None
                else cache_atual.get("memory_recent") or []
            )
            rotinas = dict(
                rotinas_iniciais
                or cache_atual.get("routines")
                or _retrato_inicial()["routines"]
            )
            temperatura_atual = dict(
                (cache_atual.get("system") or {}).get("temperature_c")
                or _metrica_indisponivel("°C", 120)
            )
            sistema["temperature_c"] = temperatura_atual
            saude = {
                "llm": llm,
                "microphone": microfone,
                "memory": memoria,
            }
            status = self._calcular_status(
                saude, contexto, sistema, falhas=falhas_secoes,
            )
            sequencia = int(self._cache.get("sequence") or 0) + 1
            self._cache = {
                "schema_version": 1,
                "status": status,
                "generated_at": agora,
                "sequence": sequencia,
                "health": saude,
                "context": contexto,
                "memory_recent": memoria_recente,
                "quick_actions": list(acoes_rapidas or []),
                "music": musica,
                "routines": rotinas,
                "system": sistema,
            }
            if memoria_inicial is not None:
                self._memoria_ultima_coleta = float(self.monotonic())
            self._coleta_em_andamento = False
            self._falhas += falhas_secoes
        self._agendar_memoria()
        self._agendar_temperatura()

    def _agendar_memoria(self) -> None:
        if self._stop.is_set():
            return
        agora = float(self.monotonic())
        with self._lock:
            if self._stop.is_set():
                return
            if (
                self._memoria_thread
                and self._memoria_thread.is_alive()
            ) or agora - self._memoria_ultima_coleta < self.intervalo_memoria_s:
                return
            self._memoria_ultima_coleta = agora
            self._memoria_thread = threading.Thread(
                target=self._coletar_memoria,
                name="Laylay-Dashboard-Memoria",
                daemon=True,
            )
            self._memoria_thread.start()

    def _coletar_memoria(self) -> None:
        agora = float(self.clock())
        falhas = 0
        try:
            memoria = self._chamar_limitado(
                "memory_health", lambda: self._saude_memoria(agora),
                timeout_s=1.0,
            )
        except Exception:
            falhas += 1
            with self._lock:
                memoria = dict(
                    (self._cache.get("health") or {}).get("memory")
                    or _saude_indisponivel("Indisponível")
                )
            if memoria.get("observed_at"):
                memoria.update(
                    state="degraded", label="Degradada", freshness="stale",
                )
        memoria_recente, falhas_recentes = self._memoria_recente(agora)
        falhas += int(falhas_recentes)
        try:
            rotinas = self._chamar_limitado(
                "memory_routines", lambda: self._rotinas_publicas(agora),
                timeout_s=0.5,
            )
        except Exception:
            falhas += 1
            with self._lock:
                rotinas = dict(
                    self._cache.get("routines")
                    or _retrato_inicial()["routines"]
                )
            if rotinas.get("observed_at"):
                rotinas["freshness"] = "stale"
        if falhas and memoria.get("state") == "online":
            memoria.update(state="degraded", label="Degradada")
        with self._lock:
            if self._stop.is_set():
                return
            self._cache["health"]["memory"] = memoria
            self._cache["memory_recent"] = list(memoria_recente)[:3]
            self._cache["routines"] = rotinas
            self._cache["generated_at"] = agora
            self._cache["sequence"] = int(self._cache.get("sequence") or 0) + 1
            self._falhas += falhas
            sistema = self._cache.get("system") or {}
            contexto = self._cache.get("context") or {}
            self._cache["status"] = self._calcular_status(
                self._cache.get("health") or {},
                contexto,
                sistema,
                falhas=falhas,
            )

    def _agendar_temperatura(self) -> None:
        sensor_psutil = getattr(self.psutil, "sensors_temperatures", None)
        if (
            not callable(self.temperatura_getter)
            and not callable(sensor_psutil)
        ) or self._stop.is_set():
            return
        agora = float(self.monotonic())
        with self._lock:
            if self._stop.is_set():
                return
            if (
                self._temperatura_thread
                and self._temperatura_thread.is_alive()
            ) or agora - self._temperatura_ultima_solicitacao < self.intervalo_temperatura_s:
                return
            self._temperatura_ultima_solicitacao = agora
            self._temperatura_thread = threading.Thread(
                target=self._coletar_temperatura,
                name="Laylay-Dashboard-Temperatura",
                daemon=True,
            )
            self._temperatura_thread.start()

    def _ler_temperatura(self) -> Any:
        if callable(self.temperatura_getter):
            return self.temperatura_getter()
        getter = getattr(self.psutil, "sensors_temperatures", None)
        if not callable(getter):
            return None
        sensores = getter() or {}
        if not isinstance(sensores, Mapping):
            return None
        for grupo in sensores.values():
            for sensor in grupo or ():
                atual = getattr(sensor, "current", None)
                valor = _numero(atual, minimo=0, maximo=125)
                if valor is not None:
                    return valor
        return None

    def _coletar_temperatura(self) -> None:
        agora = float(self.clock())
        try:
            valor = _numero(self._ler_temperatura(), minimo=0, maximo=125)
        except Exception:
            valor = None
        with self._lock:
            if self._stop.is_set():
                return
            anterior = dict(
                (self._cache.get("system") or {}).get("temperature_c")
                or _metrica_indisponivel("°C", 120)
            )
            if valor is not None:
                metrica = {
                    "value": valor,
                    "unit": "°C",
                    "freshness": "fresh",
                    "observed_at": agora,
                    "max_age_s": 120.0,
                }
            elif anterior.get("value") is not None:
                metrica = {**anterior, "freshness": "stale"}
            else:
                metrica = _metrica_indisponivel("°C", 120)
            self._cache["system"]["temperature_c"] = metrica
            self._cache["generated_at"] = agora
            self._cache["sequence"] = int(self._cache.get("sequence") or 0) + 1

    def parar(self, timeout_s: float = 1.0) -> None:
        self._stop.set()
        for thread in (
            self._thread, self._memoria_thread, self._temperatura_thread,
        ):
            if thread and thread.is_alive() and thread is not threading.current_thread():
                thread.join(timeout=max(0.0, float(timeout_s)))

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            letras = dict(
                (self._cache.get("music") or {}).get("lyrics") or {}
            )
            return {
                "disponivel": not self._stop.is_set(),
                "schema_version": 1,
                "sequence": int(self._cache.get("sequence") or 0),
                "status": str(self._cache.get("status") or "unavailable"),
                "coleta_em_andamento": self._coleta_em_andamento,
                "falhas": int(self._falhas),
                "fontes_pendentes": sum(
                    thread.is_alive()
                    for thread, _caixa in self._fontes_pendentes.values()
                ),
                "consulta_bloqueante_no_snapshot": False,
                "conteudo_bruto_exposto": False,
                "autoriza_execucao": False,
                "letras": {
                    "fonte": (
                        "lrclib" if letras.get("source") == "lrclib" else ""
                    ),
                    "status": str(letras.get("status") or "idle"),
                    "sincronizada": letras.get("synced") is True,
                    "conteudo_exposto_no_diagnostico": False,
                },
            }


def criar_dashboard_terminal_runtime(**kwargs: Any) -> DashboardTerminalRuntime:
    return DashboardTerminalRuntime(**kwargs)
