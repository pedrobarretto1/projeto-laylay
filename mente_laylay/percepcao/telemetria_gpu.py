"""Telemetria local e conservadora de GPU para o dashboard da Laylay.

O módulo não mantém um processo externo vivo. A leitura principal usa o
``nvidia-smi`` já fornecido pelo driver e conserva o último retrato por poucos
segundos. Em outras GPUs no Windows, tenta obter somente o uso observado pelos
contadores do sistema; VRAM permanece indisponível quando o total não pode ser
comprovado.
"""

from __future__ import annotations

from copy import deepcopy
import math
import os
import re
import shutil
import subprocess
import threading
import time
from typing import Any, Callable


def _percentual(valor: Any) -> float | None:
    if isinstance(valor, bool):
        return None
    try:
        numero = float(str(valor).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numero) or not 0 <= numero <= 100:
        return None
    return round(numero, 1)


def _numero_positivo(valor: Any) -> float | None:
    if isinstance(valor, bool):
        return None
    try:
        numero = float(str(valor).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numero) or numero < 0:
        return None
    return numero


class TelemetriaGpuRuntime:
    """Lê GPU/VRAM sem bloquear a UI e sem publicar valores inventados."""

    def __init__(
        self,
        *,
        run: Callable[..., Any] = subprocess.run,
        which: Callable[[str], str | None] = shutil.which,
        monotonic: Callable[[], float] = time.monotonic,
        ttl_s: float = 2.5,
        os_name: str = os.name,
        wmi_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.run = run
        self.which = which
        self.monotonic = monotonic
        self.ttl_s = max(1.0, float(ttl_s))
        self.os_name = str(os_name)
        self.wmi_factory = wmi_factory
        self._lock = threading.RLock()
        self._coletando = False
        self._observado_monotonic = float("-inf")
        self._cache: dict[str, Any] = {
            "gpu_percent": None,
            "vram_percent": None,
            "gpu_name": "",
            "driver_version": "",
            "vram_total_mb": None,
            "source": "",
        }
        # P10.5 — metadados estáticos de GPU.
        # Coletados uma vez e reaproveitados.
        self._metadata_cache: dict[str, Any] = {
            "gpu_name": "",
            "driver_version": "",
            "vram_total_mb": None,
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
            retrato = self._coletar_nvidia()
            if retrato.get("gpu_percent") is None and self.os_name == "nt":
                fallback = self._coletar_windows()
                if fallback.get("gpu_percent") is not None:
                    retrato["gpu_percent"] = fallback["gpu_percent"]
                    if not retrato.get("source"):
                        retrato["source"] = fallback.get("source", "")
                if (
                    retrato.get("vram_percent") is None
                    and fallback.get("vram_percent") is not None
                ):
                    retrato["vram_percent"] = fallback["vram_percent"]
        except Exception:
            retrato = {
                "gpu_percent": None,
                "vram_percent": None,
                "source": "",
            }
        with self._lock:
            self._cache = dict(retrato)
            self._observado_monotonic = agora
            self._coletando = False
            return deepcopy(self._cache)

    def _coletar_nvidia(self) -> dict[str, Any]:
        executavel = self.which("nvidia-smi")
        if not executavel:
            return {
                "gpu_percent": None,
                "vram_percent": None,
                "source": "",
            }
        resultado = self.run(
            [
                executavel,
                "--query-gpu=utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=1.2,
            check=False,
        )
        if int(getattr(resultado, "returncode", 1)) != 0:
            return {
                "gpu_percent": None,
                "vram_percent": None,
                "source": "",
            }
        candidatos: list[dict[str, float | None]] = []
        for linha in str(getattr(resultado, "stdout", "") or "").splitlines():
            partes = [parte.strip() for parte in linha.split(",")]
            if len(partes) != 3:
                continue
            uso = _percentual(partes[0])
            usada = _numero_positivo(partes[1])
            total = _numero_positivo(partes[2])
            vram = (
                _percentual((usada / total) * 100)
                if usada is not None and total not in {None, 0.0}
                else None
            )
            if uso is not None or vram is not None:
                candidatos.append({"gpu_percent": uso, "vram_percent": vram})
        if not candidatos:
            return {
                "gpu_percent": None,
                "vram_percent": None,
                "source": "",
            }
        escolhido = max(
            candidatos,
            key=lambda item: (
                float(item.get("gpu_percent") or 0.0),
                float(item.get("vram_percent") or 0.0),
            ),
        )
        metadata = self._coletar_nvidia_metadata(
            executavel
        )
        return {
            **escolhido,
            **metadata,
            "source": "nvidia-smi",
        }

    def _coletar_nvidia_metadata(
        self,
        executavel: str,
    ) -> dict[str, Any]:
        if self._metadata_cache.get("gpu_name"):
            return deepcopy(
                self._metadata_cache
            )

        try:
            resultado = self.run(
                [
                    executavel,
                    "--query-gpu=name,driver_version,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=1.2,
                check=False,
            )
        except Exception:
            return deepcopy(
                self._metadata_cache
            )

        if int(
            getattr(
                resultado,
                "returncode",
                1,
            )
        ) != 0:
            return deepcopy(
                self._metadata_cache
            )

        candidatos: list[
            dict[str, Any]
        ] = []

        for linha in str(
            getattr(
                resultado,
                "stdout",
                "",
            )
            or ""
        ).splitlines():
            partes = [
                parte.strip()
                for parte in linha.split(",")
            ]
            if len(partes) != 3:
                continue

            nome = str(
                partes[0] or ""
            ).strip()[:160]
            driver = str(
                partes[1] or ""
            ).strip()[:80]
            total = _numero_positivo(
                partes[2]
            )

            if nome:
                candidatos.append(
                    {
                        "gpu_name": nome,
                        "driver_version": driver,
                        "vram_total_mb": total,
                    }
                )

        if candidatos:
            escolhido = max(
                candidatos,
                key=lambda item: float(
                    item.get(
                        "vram_total_mb"
                    )
                    or 0.0
                ),
            )
            self._metadata_cache = dict(
                escolhido
            )

        return deepcopy(
            self._metadata_cache
        )

    def _coletar_windows(self) -> dict[str, Any]:
        inicializou_com = False
        try:
            if self.wmi_factory is None:
                import pythoncom
                import wmi

                pythoncom.CoInitialize()
                inicializou_com = True
                fabrica = wmi.WMI
            else:
                fabrica = self.wmi_factory
            servico = fabrica(namespace=r"root\cimv2")
            motores = servico.Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine()
            valores_por_motor: dict[str, float] = {}
            for motor in motores:
                nome = str(getattr(motor, "Name", "") or "").casefold()
                if "engtype_3d" not in nome and "engtype_compute" not in nome:
                    continue
                uso = _percentual(getattr(motor, "UtilizationPercentage", None))
                if uso is not None:
                    # O contador do Windows expõe uma linha por processo. A
                    # mesma engine física precisa ser somada antes de escolher
                    # a mais ocupada, como faz o Gerenciador de Tarefas.
                    chave_motor = re.sub(r"^pid_\d+_", "", nome)
                    valores_por_motor[chave_motor] = min(
                        100.0,
                        valores_por_motor.get(chave_motor, 0.0) + uso,
                    )
            valores = list(valores_por_motor.values())
            return {
                "gpu_percent": max(valores) if valores else None,
                "vram_percent": None,
                "source": "windows-performance-counters" if valores else "",
            }
        except Exception:
            return {
                "gpu_percent": None,
                "vram_percent": None,
                "source": "",
            }
        finally:
            if inicializou_com:
                try:
                    import pythoncom

                    pythoncom.CoUninitialize()
                except Exception:
                    pass


def criar_telemetria_gpu_runtime(**kwargs: Any) -> TelemetriaGpuRuntime:
    return TelemetriaGpuRuntime(**kwargs)
