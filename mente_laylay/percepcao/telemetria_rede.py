"""Telemetria local de rede para o dashboard da Laylay.

A leitura usa apenas contadores do sistema operacional. Nenhum pacote, ping ou
requisição externa é criado para medir a conexão. A porcentagem representa o
tráfego observado em relação à velocidade informada pela interface ativa.
"""

from __future__ import annotations

from copy import deepcopy
import math
import threading
import time
from typing import Any, Callable


_NOMES_LOOPBACK = ("loopback", "pseudo-interface", "isatap", "teredo")


def _numero_nao_negativo(valor: Any) -> float | None:
    if isinstance(valor, bool):
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numero) or numero < 0:
        return None
    return numero


def _interface_util(nome: str, estado: Any) -> bool:
    nome_normalizado = str(nome or "").casefold().strip()
    if nome_normalizado == "lo" or any(
        marcador in nome_normalizado for marcador in _NOMES_LOOPBACK
    ):
        return False
    if not bool(getattr(estado, "isup", False)):
        return False
    flags = str(getattr(estado, "flags", "") or "").casefold()
    return "loopback" not in flags


class TelemetriaRedeRuntime:
    """Calcula uso, download e upload da interface local ativa."""

    def __init__(
        self,
        *,
        psutil_mod: Any,
        monotonic: Callable[[], float] = time.monotonic,
        ttl_s: float = 0.75,
    ) -> None:
        self.psutil = psutil_mod
        self.monotonic = monotonic
        self.ttl_s = max(0.25, float(ttl_s))
        self._lock = threading.RLock()
        self._coletando = False
        self._observado_monotonic = float("-inf")
        self._amostra_ts: float | None = None
        self._amostras: dict[str, tuple[float, float]] = {}
        self._cache = self._indisponivel()

    @staticmethod
    def _indisponivel() -> dict[str, Any]:
        return {
            "network_percent": None,
            "download_mbps": None,
            "upload_mbps": None,
            "source": "",
        }

    def snapshot(self) -> dict[str, Any]:
        agora = float(self.monotonic())
        with self._lock:
            if agora - self._observado_monotonic < self.ttl_s:
                return deepcopy(self._cache)
            if self._coletando:
                return deepcopy(self._cache)
            self._coletando = True
        try:
            retrato = self._coletar(agora)
        except Exception:
            retrato = self._indisponivel()
        with self._lock:
            self._cache = dict(retrato)
            self._observado_monotonic = agora
            self._coletando = False
            return deepcopy(self._cache)

    def _coletar(self, agora: float) -> dict[str, Any]:
        estados = dict(self.psutil.net_if_stats() or {})
        contadores = dict(self.psutil.net_io_counters(pernic=True) or {})
        atuais: dict[str, tuple[float, float]] = {}
        candidatos: list[dict[str, float | str | None]] = []
        intervalo = (
            max(0.0, agora - self._amostra_ts)
            if self._amostra_ts is not None
            else 0.0
        )

        for nome, estado in estados.items():
            contador = contadores.get(nome)
            if contador is None or not _interface_util(nome, estado):
                continue
            recebidos = _numero_nao_negativo(getattr(contador, "bytes_recv", None))
            enviados = _numero_nao_negativo(getattr(contador, "bytes_sent", None))
            if recebidos is None or enviados is None:
                continue
            atuais[str(nome)] = (recebidos, enviados)
            anterior = self._amostras.get(str(nome))
            if anterior is None or intervalo <= 0:
                continue
            download = max(0.0, recebidos - anterior[0]) * 8 / intervalo / 1_000_000
            upload = max(0.0, enviados - anterior[1]) * 8 / intervalo / 1_000_000
            velocidade = _numero_nao_negativo(getattr(estado, "speed", None))
            candidatos.append({
                "name": str(nome),
                "download_mbps": download,
                "upload_mbps": upload,
                "link_mbps": velocidade,
            })

        self._amostras = atuais
        self._amostra_ts = agora
        if not candidatos:
            return self._indisponivel()

        escolhido = max(
            candidatos,
            key=lambda item: (
                float(item["download_mbps"] or 0.0)
                + float(item["upload_mbps"] or 0.0),
                float(item["link_mbps"] or 0.0),
            ),
        )
        download = float(escolhido["download_mbps"] or 0.0)
        upload = float(escolhido["upload_mbps"] or 0.0)
        velocidade = float(escolhido["link_mbps"] or 0.0)
        percentual = (
            min(100.0, ((download + upload) / velocidade) * 100.0)
            if velocidade > 0
            else None
        )
        return {
            "network_percent": round(percentual, 1) if percentual is not None else None,
            "download_mbps": round(download, 3),
            "upload_mbps": round(upload, 3),
            "source": "system-network-counters",
        }


def criar_telemetria_rede_runtime(**kwargs: Any) -> TelemetriaRedeRuntime:
    return TelemetriaRedeRuntime(**kwargs)
