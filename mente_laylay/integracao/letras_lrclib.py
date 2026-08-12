"""Consulta responsável e não bloqueante de letras públicas na LRCLIB.

O runtime recebe somente o retrato público da faixa observada, mantém uma fila
de uma música (a mais recente) e nunca faz rede na thread do dashboard/Qt.
Letras são cacheadas apenas em memória e não entram na memória da Laylay.
"""

from __future__ import annotations

from collections import OrderedDict
from difflib import SequenceMatcher
import math
import re
import threading
import time
import unicodedata
from typing import Any, Callable, Mapping

import requests


LRCLIB_API = "https://lrclib.net/api"
LRCLIB_USER_AGENT = (
    "Laylay/3.0 (https://github.com/pedrobarretto1/projeto-laylay)"
)
_STATUS_VALIDOS = {
    "idle", "loading", "available", "instrumental", "not_found",
    "error", "rate_limited",
}
_MARCADOR_TEMPO = re.compile(
    r"\[(?P<min>\d{1,3}):(?P<seg>\d{2})(?:[.:](?P<frac>\d{1,3}))?\]"
)
_METADADO_LRC = re.compile(r"^\[(?:ar|al|ti|au|by|re|ve|length):", re.I)
_ROTULO_VIDEO = re.compile(
    r"(?ix)[\[(](?:official\s+)?(?:music\s+)?(?:video|audio|lyric(?:s)?(?:\s+video)?|"
    r"legendado|tradu[çc][aã]o|visualizer|clipe\s+oficial|letra)[^\])]*[\])]"
)
_PREFIXO_INDICE = re.compile(r"^\s*\(\s*\d{1,6}\s*\)\s*")


def _texto(valor: Any, limite: int) -> str:
    return re.sub(r"\s+", " ", str(valor or "").replace("\x00", " ")).strip()[:limite]


def _normalizar(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", _texto(valor, 300)).casefold()
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def _numero(valor: Any, *, minimo: float = 0.0, maximo: float = 86_400.0) -> float:
    if isinstance(valor, bool):
        return 0.0
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return 0.0
    return numero if math.isfinite(numero) and minimo <= numero <= maximo else 0.0


def identificar_faixa(
    titulo: Any,
    artista: Any,
) -> tuple[str, str]:
    """Reduz títulos do YouTube sem apagar partes musicais relevantes."""
    bruto = _PREFIXO_INDICE.sub("", _texto(titulo, 300))
    bruto = _ROTULO_VIDEO.sub(" ", bruto)
    partes_barra = [parte.strip() for parte in bruto.split("|") if parte.strip()]
    nome_faixa = partes_barra[0] if partes_barra else bruto
    artista_limpo = _texto(artista, 140)
    artista_limpo = re.sub(r"(?i)\s*[-–—]?\s*(?:topic|vevo)\s*$", "", artista_limpo)
    artista_limpo = artista_limpo.replace("_", " ").strip()

    # O padrão mais comum é "Artista - Faixa". Só o aplicamos quando o lado
    # esquerdo parece um nome curto, evitando quebrar títulos com hífen.
    hifen = re.split(r"\s+[-–—]\s+", nome_faixa, maxsplit=1)
    if len(hifen) == 2 and 0 < len(hifen[0].split()) <= 6:
        candidato_artista, candidato_faixa = hifen
        if candidato_faixa.strip():
            artista_limpo = candidato_artista.strip() or artista_limpo
            nome_faixa = candidato_faixa.strip()

    # Em vídeos no formato "Faixa | Anime | Artista", o último segmento com
    # autoria explícita é uma evidência melhor que o nome técnico do canal.
    for parte in reversed(partes_barra[1:]):
        if re.search(r"(?i)\b(?:ft\.?|feat\.?)\b|@", parte):
            candidato = re.split(r"(?i)\b(?:ft\.?|feat\.?)\b", parte, maxsplit=1)[0]
            candidato = candidato.replace("@", " ").strip()
            if candidato:
                artista_limpo = candidato
                break
    nome_faixa = _texto(nome_faixa, 180)
    return nome_faixa, _texto(artista_limpo, 120)


def analisar_lrc(texto: Any) -> list[dict[str, Any]]:
    """Converte LRC em linhas ordenadas, incluindo timestamps múltiplos."""
    bruto = str(texto or "").replace("\r\n", "\n").replace("\r", "\n")
    deslocamento_ms = 0
    encontrado_offset = re.search(r"(?im)^\[offset:([+-]?\d+)\]", bruto)
    if encontrado_offset:
        try:
            deslocamento_ms = int(encontrado_offset.group(1))
        except ValueError:
            deslocamento_ms = 0
    linhas: list[dict[str, Any]] = []
    for linha in bruto.split("\n"):
        if _METADADO_LRC.match(linha.strip()) or linha.lower().startswith("[offset:"):
            continue
        marcadores = list(_MARCADOR_TEMPO.finditer(linha))
        if not marcadores:
            continue
        conteudo = _MARCADOR_TEMPO.sub("", linha).strip()
        if not conteudo:
            continue
        for marcador in marcadores:
            frac = marcador.group("frac") or "0"
            fracao = int(frac) / (10 ** len(frac))
            segundos = (
                int(marcador.group("min")) * 60
                + int(marcador.group("seg"))
                + fracao
                + deslocamento_ms / 1000.0
            )
            linhas.append({
                "time_seconds": round(max(0.0, segundos), 3),
                "text": _texto(conteudo, 240),
            })
    linhas.sort(key=lambda item: item["time_seconds"])
    return linhas[:400]


def _pontuar_registro(
    registro: Mapping[str, Any],
    *,
    faixa: str,
    artista: str,
    duracao: float,
) -> tuple[float, float]:
    nome_registro = _normalizar(registro.get("trackName"))
    nome_faixa = _normalizar(faixa)
    if not nome_registro or not nome_faixa:
        return 0.0, 0.0
    semelhanca_titulo = SequenceMatcher(None, nome_faixa, nome_registro).ratio()
    semelhanca_artista = SequenceMatcher(
        None, _normalizar(artista), _normalizar(registro.get("artistName")),
    ).ratio() if artista else 0.5
    duracao_registro = _numero(registro.get("duration"))
    if duracao > 0 and duracao_registro > 0:
        diferenca = abs(duracao - duracao_registro)
        nota_duracao = max(0.0, 1.0 - diferenca / 30.0)
    else:
        nota_duracao = 0.5
    return (
        semelhanca_titulo * 0.68
        + semelhanca_artista * 0.17
        + nota_duracao * 0.15,
        semelhanca_titulo,
    )


def _resultado_vazio(status: str = "idle") -> dict[str, Any]:
    return {
        "status": status if status in _STATUS_VALIDOS else "error",
        "source": "lrclib" if status not in {"idle", "loading"} else "",
        "synced": False,
        "track_name": "",
        "artist_name": "",
        "plain_text": "",
        "lines": [],
        "observed_at": 0.0,
    }


class LetrasLRCLibRuntime:
    """Worker sequencial com cache em memória e estado público O(1)."""

    def __init__(
        self,
        *,
        requests_get: Callable[..., Any] = requests.get,
        clock: Callable[[], float] = time.time,
        monotonic: Callable[[], float] = time.monotonic,
        timeout_s: float = 6.0,
        cache_max: int = 32,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.requests_get = requests_get
        self.clock = clock
        self.monotonic = monotonic
        self.timeout_s = max(1.0, min(15.0, float(timeout_s)))
        self.cache_max = max(4, min(128, int(cache_max)))
        self.log = log
        self._cond = threading.Condition(threading.RLock())
        self._stop = False
        self._pendente: tuple[str, dict[str, Any]] | None = None
        self._chave_atual = ""
        self._estado = _resultado_vazio()
        self._cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._repetir_depois: dict[str, float] = {}
        self._bloqueado_ate = 0.0
        self._ultimo_request = float("-inf")
        self._thread: threading.Thread | None = None

    def _garantir_thread(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._executar,
            name="Laylay-Letras-LRCLIB",
            daemon=True,
        )
        self._thread.start()

    @staticmethod
    def _chave(player: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        faixa, artista = identificar_faixa(
            player.get("title"), player.get("channel"),
        )
        duracao = _numero(player.get("duration_seconds"))
        video_id = _texto(player.get("video_id"), 32)
        chave = "|".join((video_id, _normalizar(faixa), _normalizar(artista), str(round(duracao))))
        return chave if faixa else "", {
            "track_name": faixa,
            "artist_name": artista,
            "duration": duracao,
        }

    def snapshot(self, player: Mapping[str, Any] | None) -> dict[str, Any]:
        player = dict(player or {})
        estado_player = _texto(player.get("state"), 24).casefold()
        chave, consulta = self._chave(player)
        with self._cond:
            if not chave or estado_player not in {"playing", "paused", "ended"}:
                self._chave_atual = ""
                self._estado = _resultado_vazio()
                self._pendente = None
                return dict(self._estado)
            if chave != self._chave_atual:
                self._chave_atual = chave
                if chave in self._cache:
                    self._cache.move_to_end(chave)
                    self._estado = dict(self._cache[chave])
                elif self.monotonic() < self._bloqueado_ate:
                    self._estado = _resultado_vazio("rate_limited")
                    self._estado["observed_at"] = float(self.clock())
                else:
                    self._estado = _resultado_vazio("loading")
                    self._pendente = (chave, consulta)
                    self._garantir_thread()
                    self._cond.notify()
            elif (
                str(self._estado.get("status") or "") in {"error", "rate_limited"}
                and self.monotonic() >= self._repetir_depois.get(chave, float("inf"))
                and self._pendente is None
            ):
                self._estado = _resultado_vazio("loading")
                self._pendente = (chave, consulta)
                self._garantir_thread()
                self._cond.notify()
            return {
                **self._estado,
                "lines": [dict(item) for item in self._estado.get("lines") or ()],
            }

    def _executar(self) -> None:
        while True:
            with self._cond:
                while not self._stop and self._pendente is None:
                    self._cond.wait(timeout=1.0)
                if self._stop:
                    return
                chave, consulta = self._pendente
                self._pendente = None
            espera = 0.25 - (self.monotonic() - self._ultimo_request)
            if espera > 0:
                time.sleep(espera)
            resultado = self._buscar(consulta)
            with self._cond:
                status = str(resultado.get("status") or "error")
                if status not in {"error", "rate_limited"}:
                    self._cache[chave] = dict(resultado)
                    self._cache.move_to_end(chave)
                    self._repetir_depois.pop(chave, None)
                    while len(self._cache) > self.cache_max:
                        removida, _valor = self._cache.popitem(last=False)
                        self._repetir_depois.pop(removida, None)
                else:
                    self._repetir_depois[chave] = (
                        self._bloqueado_ate if status == "rate_limited"
                        else self.monotonic() + 30.0
                    )
                if chave == self._chave_atual:
                    self._estado = dict(resultado)

    def _buscar(self, consulta: Mapping[str, Any]) -> dict[str, Any]:
        faixa = _texto(consulta.get("track_name"), 180)
        artista = _texto(consulta.get("artist_name"), 120)
        duracao = _numero(consulta.get("duration"))
        try:
            self._ultimo_request = self.monotonic()
            resposta = self.requests_get(
                f"{LRCLIB_API}/search",
                params={"q": " ".join(parte for parte in (faixa, artista) if parte)},
                headers={"User-Agent": LRCLIB_USER_AGENT},
                timeout=self.timeout_s,
            )
            if int(getattr(resposta, "status_code", 0) or 0) == 429:
                try:
                    espera = float((getattr(resposta, "headers", {}) or {}).get("Retry-After", 60))
                except (TypeError, ValueError):
                    espera = 60.0
                self._bloqueado_ate = self.monotonic() + max(1.0, min(3_600.0, espera))
                resultado = _resultado_vazio("rate_limited")
                resultado["observed_at"] = float(self.clock())
                return resultado
            resposta.raise_for_status()
            bruto = resposta.json()
            candidatos = [item for item in bruto if isinstance(item, Mapping)] if isinstance(bruto, list) else []
            pontuados = [
                (*_pontuar_registro(item, faixa=faixa, artista=artista, duracao=duracao), item)
                for item in candidatos
            ]
            pontuados.sort(key=lambda item: item[0], reverse=True)
            if not pontuados or pontuados[0][0] < 0.52 or pontuados[0][1] < 0.48:
                resultado = _resultado_vazio("not_found")
                resultado["observed_at"] = float(self.clock())
                return resultado
            registro = pontuados[0][2]
            instrumental = registro.get("instrumental") is True
            sincronizada = str(registro.get("syncedLyrics") or "")
            simples = str(registro.get("plainLyrics") or "")
            linhas = analisar_lrc(sincronizada)
            status = "instrumental" if instrumental else "available" if linhas or simples.strip() else "not_found"
            return {
                "status": status,
                "source": "lrclib",
                "synced": bool(linhas),
                "track_name": _texto(registro.get("trackName") or faixa, 180),
                "artist_name": _texto(registro.get("artistName") or artista, 120),
                "plain_text": simples.replace("\x00", "").strip()[:24_000] if not linhas else "",
                "lines": linhas,
                "observed_at": float(self.clock()),
            }
        except Exception as erro:
            self.log(
                "⚠️ [LETRAS:LRCLIB] consulta indisponível "
                f"| tipo={type(erro).__name__}"
            )
            resultado = _resultado_vazio("error")
            resultado["observed_at"] = float(self.clock())
            return resultado

    def diagnostico(self) -> dict[str, Any]:
        with self._cond:
            return {
                "disponivel": not self._stop,
                "worker_ativo": bool(self._thread and self._thread.is_alive()),
                "status": str(self._estado.get("status") or "idle"),
                "cache_itens": len(self._cache),
                "consulta_pendente": self._pendente is not None,
                "bloqueado_por_limite": self.monotonic() < self._bloqueado_ate,
            }

    def parar(self, timeout_s: float = 1.0) -> None:
        with self._cond:
            self._stop = True
            self._pendente = None
            self._cond.notify_all()
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=max(0.0, float(timeout_s)))


def criar_letras_lrclib_runtime(**kwargs: Any) -> LetrasLRCLibRuntime:
    return LetrasLRCLibRuntime(**kwargs)
