"""Ajuste local e silencioso do volume mestre do Windows.

O acesso ao ``pycaw`` fica deliberadamente lazy: importar a página Música em
testes ou em outra plataforma nunca consulta dispositivos reais. O endpoint é
mantido somente durante um gesto do slider e descartado ao final ou em falha.
"""

from __future__ import annotations

from collections.abc import Callable
import os
import warnings


class DefinidorVolumeMestreWindows:
    """Callable pequeno que aplica e confirma o volume mestre via ``pycaw``."""

    def __init__(self, endpoint_factory: Callable[[], object] | None = None) -> None:
        self._endpoint_factory = endpoint_factory
        self._endpoint: object | None = None
        self._falhou_no_gesto = False

    def iniciar_gesto(self) -> None:
        self._endpoint = None
        self._falhou_no_gesto = False

    def finalizar_gesto(self) -> None:
        self._endpoint = None

    def __call__(self, percentual: int) -> bool:
        if self._falhou_no_gesto:
            return False
        try:
            endpoint = self._endpoint or self._obter_endpoint()
            if endpoint is None:
                raise RuntimeError("endpoint de volume indisponível")
            self._endpoint = endpoint
            nivel = max(0, min(100, int(percentual)))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                endpoint.SetMasterVolumeLevelScalar(nivel / 100.0, None)
                observado = int(
                    round(float(endpoint.GetMasterVolumeLevelScalar()) * 100)
                )
            if abs(observado - nivel) > 2:
                raise RuntimeError("volume local não confirmado")
            return True
        except Exception:
            # COM pode desaparecer durante uma troca de dispositivo. Evitamos
            # ruído e novas tentativas no mesmo gesto; o próximo gesto reabre.
            self._endpoint = None
            self._falhou_no_gesto = True
            return False

    def _obter_endpoint(self) -> object | None:
        if self._endpoint_factory is not None:
            return self._endpoint_factory()
        if os.name != "nt":
            return None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            from pycaw.pycaw import AudioUtilities

            dispositivo = AudioUtilities.GetSpeakers()
            return getattr(dispositivo, "EndpointVolume", None)
