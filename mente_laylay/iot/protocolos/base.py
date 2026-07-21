"""Interface que todos os protocolos físicos ou simulados devem respeitar."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from mente_laylay.iot.contratos import DispositivoIoT, ResultadoProtocolo


class ProtocoloIoT(ABC):
    nome = "base"

    @abstractmethod
    def consultar_estado(self, dispositivo: DispositivoIoT) -> ResultadoProtocolo:
        raise NotImplementedError

    @abstractmethod
    def definir_estado(self, dispositivo: DispositivoIoT, ligado: bool) -> ResultadoProtocolo:
        raise NotImplementedError

    def definir_parametros(
        self,
        dispositivo: DispositivoIoT,
        acao: str,
        parametros: Dict[str, Any],
    ) -> ResultadoProtocolo:
        return ResultadoProtocolo(False, None, True, "parâmetro não suportado pelo protocolo")
