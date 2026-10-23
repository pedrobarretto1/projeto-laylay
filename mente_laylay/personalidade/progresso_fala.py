"""Acompanhamento efêmero de áudio; nunca autoriza nem confirma uma ação."""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import Event
from typing import Callable


@dataclass(slots=True)
class ProgressoFala:
    id: str
    vigente: Callable[[], bool]
    pronto: Event = field(default_factory=Event, init=False)
    audio_iniciado: Event = field(default_factory=Event, init=False)
    encerrado: Event = field(default_factory=Event, init=False)

    def pode_emitir(self) -> bool:
        try:
            return not self.encerrado.is_set() and self.vigente() is True
        except Exception:
            return False

    def iniciar_audio(self) -> None:
        self.audio_iniciado.set()
        self.pronto.set()

    def concluir(self) -> None:
        self.encerrado.set()
        self.pronto.set()

    def aguardar_inicio(self, timeout_s: float) -> bool:
        """Espera somente o início; voz indisponível não impede o trabalho."""
        if not self.pronto.wait(timeout=max(0.0, min(timeout_s, 15.0))):
            self.concluir()  # anúncio atrasado não deve tocar após a conclusão
        return self.audio_iniciado.is_set()
