"""Inventário e troca confirmada da saída padrão de áudio do Windows."""

from __future__ import annotations

import hashlib
import os
import threading
import time
from typing import Any, Callable


# Valores oficiais da API MMDevice usados pelo Pycaw:
# eRender seleciona saídas e DEVICE_STATE_ACTIVE exclui registros ausentes.
_DATA_FLOW_RENDER = 0
_DEVICE_STATE_ACTIVE = 0x00000001


def _referencia_dispositivo(endpoint_id: str) -> str:
    """Cria uma referência pública sem expor o identificador do hardware."""
    return hashlib.sha256(str(endpoint_id).encode("utf-8")).hexdigest()[:16]


class GerenciadorSaidasAudioWindows:
    """Mantém a enumeração fora da UI e confirma a troca relendo o Windows."""

    def __init__(
        self,
        *,
        audio_utilities: Any = None,
        clock: Callable[[], float] = time.monotonic,
        cache_s: float = 1.0,
        log: Callable[[str], Any] = print,
    ) -> None:
        self._audio_utilities = audio_utilities
        self._clock = clock
        self._cache_s = max(0.0, float(cache_s))
        self._log = log
        self._lock = threading.RLock()
        self._cache: dict[str, Any] = {}
        self._cache_em = 0.0
        self._ids_por_ref: dict[str, tuple[str, str]] = {}

    def _porta(self) -> Any:
        if self._audio_utilities is not None:
            return self._audio_utilities
        from pycaw.pycaw import AudioUtilities

        return AudioUtilities

    @staticmethod
    def _com(iniciar: bool) -> None:
        try:
            import comtypes

            (comtypes.CoInitialize if iniciar else comtypes.CoUninitialize)()
        except Exception:
            pass

    def _coletar(self) -> dict[str, Any]:
        self._com(True)
        try:
            porta = self._porta()
            padrao = porta.GetSpeakers()
            padrao_id = str(getattr(padrao, "id", "") or "")
            dispositivos: list[dict[str, Any]] = []
            ids: dict[str, tuple[str, str]] = {}
            for item in list(porta.GetAllDevices(
                data_flow=_DATA_FLOW_RENDER,
                device_state=_DEVICE_STATE_ACTIVE,
            ) or ()):
                endpoint_id = str(getattr(item, "id", "") or "").strip()
                # MMDevice usa 0 para renderização e 1 para captura.
                if not endpoint_id.casefold().startswith("{0.0.0."):
                    continue
                estado = getattr(getattr(item, "state", None), "value", None)
                if estado is None:
                    estado = getattr(item, "state", None)
                if estado != 1:
                    continue
                nome = " ".join(
                    str(getattr(item, "FriendlyName", "") or "").split()
                )[:100]
                if not nome:
                    continue
                referencia = _referencia_dispositivo(endpoint_id)
                selecionado = endpoint_id.casefold() == padrao_id.casefold()
                dispositivos.append({
                    "ref": referencia,
                    "name": nome,
                    "selected": selecionado,
                })
                ids[referencia] = (endpoint_id, nome)
            dispositivos.sort(key=lambda item: (not item["selected"], item["name"].casefold()))
            atual = next((item for item in dispositivos if item["selected"]), None)
            with self._lock:
                self._ids_por_ref = ids
            return {
                "name": str((atual or {}).get("name") or ""),
                "source": "padrão do sistema",
                "available": bool(atual),
                "selected_ref": str((atual or {}).get("ref") or ""),
                "switch_available": bool(dispositivos),
                "devices": dispositivos,
                "observed_at": time.time(),
            }
        finally:
            self._com(False)

    def snapshot(self, *, forcar: bool = False) -> dict[str, Any]:
        agora = self._clock()
        with self._lock:
            if (
                not forcar and self._cache
                and agora - self._cache_em <= self._cache_s
            ):
                return {
                    **self._cache,
                    "devices": [dict(item) for item in self._cache.get("devices", ())],
                }
        try:
            retrato = self._coletar()
        except Exception as erro:
            self._log(
                "⚠️ [ÁUDIO:SAÍDA] inventário indisponível "
                f"| tipo={type(erro).__name__}"
            )
            retrato = {
                "name": "", "source": "", "available": False,
                "selected_ref": "", "switch_available": False,
                "devices": [], "observed_at": time.time(),
            }
        with self._lock:
            self._cache = dict(retrato)
            self._cache_em = agora
        return {**retrato, "devices": [dict(item) for item in retrato["devices"]]}

    def selecionar(self, referencia: str) -> dict[str, Any]:
        referencia = str(referencia or "").strip().casefold()
        if len(referencia) != 16 or any(ch not in "0123456789abcdef" for ch in referencia):
            return {"executou": False, "confirmado": False, "resumo": "Dispositivo inválido"}
        # Atualiza o mapa antes de aceitar a referência recebida do painel.
        atual = self.snapshot(forcar=True)
        with self._lock:
            escolha = self._ids_por_ref.get(referencia)
        if escolha is None:
            return {
                "executou": False,
                "confirmado": False,
                "resumo": "Essa saída de áudio não está mais disponível",
            }
        endpoint_id, nome = escolha
        if atual.get("selected_ref") == referencia:
            return {
                "executou": False,
                "confirmado": True,
                "resumo": f"{nome} já é a saída padrão",
            }

        self._com(True)
        try:
            porta = self._porta()
            try:
                from pycaw.constants import ERole

                papeis = [ERole.eConsole, ERole.eMultimedia, ERole.eCommunications]
                porta.SetDefaultDevice(endpoint_id, roles=papeis)
            except (ImportError, TypeError):
                porta.SetDefaultDevice(endpoint_id)
        except Exception as erro:
            self._log(
                "⚠️ [ÁUDIO:SAÍDA] troca não confirmada "
                f"| tipo={type(erro).__name__}"
            )
            return {
                "executou": False,
                "confirmado": False,
                "resumo": "O Windows não aceitou a troca de saída",
            }
        finally:
            self._com(False)

        with self._lock:
            self._cache = {}
            self._cache_em = 0.0
        confirmado = self.snapshot(forcar=True).get("selected_ref") == referencia
        if confirmado:
            # A voz da Laylay consulta esta preferência antes de cada fala.
            os.environ["LAYLAY_SAIDA_AUDIO"] = nome
        return {
            "executou": True,
            "confirmado": bool(confirmado),
            "resumo": (
                f"Saída alterada para {nome}"
                if confirmado else "A troca foi enviada, mas o Windows não confirmou"
            ),
        }
