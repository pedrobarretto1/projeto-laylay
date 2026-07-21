"""Protocolo em memória para validar a integração sem acionar eletricidade."""

from __future__ import annotations

from typing import Any, Dict

from mente_laylay.iot.contratos import DispositivoIoT, ResultadoProtocolo
from mente_laylay.iot.protocolos.base import ProtocoloIoT


class ProtocoloSimulado(ProtocoloIoT):
    nome = "simulado"

    def __init__(self) -> None:
        self._estados: Dict[str, bool | None] = {}
        self._disponibilidade: Dict[str, bool] = {}
        self._parametros: Dict[str, Dict[str, Any]] = {}

    def configurar(
        self,
        dispositivo: str,
        *,
        estado: bool | None = False,
        disponivel: bool = True,
        parametros: Dict[str, Any] | None = None,
    ) -> None:
        self._estados[str(dispositivo)] = estado
        self._disponibilidade[str(dispositivo)] = bool(disponivel)
        self._parametros[str(dispositivo)] = dict(parametros or {})

    def consultar_estado(self, dispositivo: DispositivoIoT) -> ResultadoProtocolo:
        nome = dispositivo.nome
        if not self._disponibilidade.get(nome, True):
            return ResultadoProtocolo(False, None, False, "dispositivo indisponível")
        return ResultadoProtocolo(True, self._estados.get(nome), True)

    def definir_estado(self, dispositivo: DispositivoIoT, ligado: bool) -> ResultadoProtocolo:
        nome = dispositivo.nome
        if not self._disponibilidade.get(nome, True):
            return ResultadoProtocolo(False, None, False, "dispositivo indisponível")
        self._estados[nome] = bool(ligado)
        return ResultadoProtocolo(True, bool(ligado), True)

    def definir_parametros(
        self,
        dispositivo: DispositivoIoT,
        acao: str,
        parametros: Dict[str, Any],
    ) -> ResultadoProtocolo:
        nome = dispositivo.nome
        if not self._disponibilidade.get(nome, True):
            return ResultadoProtocolo(False, None, False, "dispositivo indisponível")

        propriedades = self._parametros.setdefault(nome, {})
        try:
            if acao == "ajustar_brilho":
                valor = int(parametros.get("valor"))
                if not 1 <= valor <= 100:
                    raise ValueError
                propriedades["brilho"] = valor
                detalhes = {"brilho": valor}
            elif acao == "ajustar_cor":
                rgb = tuple(int(item) for item in parametros.get("rgb", ()))
                if len(rgb) != 3 or any(item < 0 or item > 255 for item in rgb):
                    raise ValueError
                propriedades["cor_rgb"] = rgb
                detalhes = {
                    "rgb": rgb,
                    "cor": str(parametros.get("cor") or "").strip(),
                    "brilho": max(1, round(max(rgb) * 100 / 255)),
                }
            elif acao == "ajustar_branco":
                brilho = int(parametros.get("brilho", 70))
                temperatura = int(parametros.get("temperatura", 50))
                if not 1 <= brilho <= 100 or not 0 <= temperatura <= 100:
                    raise ValueError
                propriedades.update({"brilho": brilho, "temperatura": temperatura})
                detalhes = {
                    "brilho": brilho,
                    "temperatura": temperatura,
                    "cor": str(parametros.get("cor") or "branco").strip(),
                }
            else:
                return ResultadoProtocolo(False, self._estados.get(nome), True, "parâmetro não suportado")
        except (TypeError, ValueError):
            return ResultadoProtocolo(False, self._estados.get(nome), True, "parâmetros inválidos")

        self._estados[nome] = True
        return ResultadoProtocolo(True, True, True, detalhes=detalhes)
