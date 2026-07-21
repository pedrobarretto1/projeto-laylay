"""Contratos estáveis entre a mente, o controlador e os protocolos IoT."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Tuple


ACOES_IOT = frozenset({
    "ligar", "desligar", "alternar", "status",
    "ajustar_brilho", "ajustar_cor", "ajustar_branco",
})
RISCOS_IOT = frozenset({"baixo", "moderado", "alto"})


@dataclass(frozen=True)
class DispositivoIoT:
    nome: str
    nome_amigavel: str
    tipo: str
    ambiente: str
    protocolo: str
    aliases: Tuple[str, ...] = ()
    capacidades: FrozenSet[str] = field(default_factory=lambda: ACOES_IOT)
    risco: str = "moderado"
    configuracao: Dict[str, Any] = field(default_factory=dict)
    ativo: bool = True

    def __post_init__(self) -> None:
        if not str(self.nome or "").strip():
            raise ValueError("Dispositivo IoT precisa de nome canônico.")
        if str(self.risco or "").lower() not in RISCOS_IOT:
            raise ValueError(f"Nível de risco IoT inválido: {self.risco}")
        capacidades = frozenset(str(item).lower().strip() for item in self.capacidades)
        invalidas = capacidades - ACOES_IOT
        if invalidas:
            raise ValueError(f"Capacidades IoT inválidas: {sorted(invalidas)}")
        object.__setattr__(self, "capacidades", capacidades)


@dataclass(frozen=True)
class ResultadoProtocolo:
    ok: bool
    estado: bool | None = None
    disponivel: bool = True
    erro: str = ""
    detalhes: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisaoSeguranca:
    permitido: bool
    confirmacao_necessaria: bool = False
    motivo: str = ""


@dataclass
class ResultadoIoT:
    ok: bool
    status: str
    acao: str
    dispositivo: str = ""
    ambiente: str = ""
    estado_anterior: bool | None = None
    estado_atual: bool | None = None
    confirmado: bool = False
    protocolo: str = ""
    erro: str = ""
    detalhes: Dict[str, Any] = field(default_factory=dict)
