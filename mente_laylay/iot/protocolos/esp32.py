"""Controle local do relé com o firmware Laylay Home."""

from __future__ import annotations

import asyncio
from time import monotonic

import requests

from mente_laylay.iot.configuracao import ler_variavel_ambiente
from mente_laylay.iot.contratos import DispositivoIoT, ResultadoProtocolo
from mente_laylay.iot.protocolos.base import ProtocoloIoT


UUID_SERVICO = "a0c5d100-18c8-4fb2-98b7-0af81d123456"
UUID_CONTROLE = "a0c5d101-18c8-4fb2-98b7-0af81d123456"
HOST_PADRAO = "laylay-home.local"
CHAVE_ESP32 = "LAYLAY_IOT_ESP32_KEY"
TRANSPORTES = {"auto", "wifi", "bluetooth"}


class ProtocoloESP32(ProtocoloIoT):
    nome = "esp32"

    def __init__(self) -> None:
        self._wifi_indisponivel_ate = 0.0

    def consultar_estado(self, dispositivo: DispositivoIoT) -> ResultadoProtocolo:
        return self._operar(dispositivo, "S")

    def definir_estado(self, dispositivo: DispositivoIoT, ligado: bool) -> ResultadoProtocolo:
        return self._operar(dispositivo, "1" if ligado else "0")

    def _operar(self, dispositivo: DispositivoIoT, comando: str) -> ResultadoProtocolo:
        chave = ler_variavel_ambiente(CHAVE_ESP32).strip()
        if not 16 <= len(chave) <= 18 or any(not 33 <= ord(c) <= 126 or c == "|" for c in chave):
            return ResultadoProtocolo(False, disponivel=False, erro="ESP32 ainda não pareado")

        config = dispositivo.configuracao
        transporte = config.get("transporte", "auto")
        if transporte != "bluetooth" and (
            transporte == "wifi" or monotonic() >= self._wifi_indisponivel_ate
        ):
            try:
                with requests.Session() as sessao:
                    sessao.trust_env = False
                    resposta = sessao.post(
                        f"http://{HOST_PADRAO}/api/rele",
                        headers={"X-Laylay-Key": chave},
                        data=comando,
                        timeout=(1.0, 1.0),
                        allow_redirects=False,
                    )
                if resposta.status_code == 200:
                    return self._confirmar(resposta.text.strip(), comando, "wifi")
                return ResultadoProtocolo(False, erro="ESP32 recusou a operação pela rede")
            except requests.RequestException:
                self._wifi_indisponivel_ate = monotonic() + 10
        if transporte == "wifi":
            return ResultadoProtocolo(False, disponivel=False, erro="ESP32 não respondeu na rede")

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            try:
                resposta_ble = asyncio.run(self._operar_ble_limitado(
                    config.get("nome_ble", "Laylay Home"), chave, comando,
                ))
            except Exception:
                # Exceções do backend BLE podem conter identificadores da placa.
                return ResultadoProtocolo(False, disponivel=False, erro="ESP32 não respondeu por Bluetooth")
            return self._confirmar(resposta_ble, comando, "bluetooth")
        return ResultadoProtocolo(False, disponivel=False, erro="Bluetooth precisa de execução síncrona")

    async def _operar_ble_limitado(self, nome: str, chave: str, comando: str) -> str:
        return await asyncio.wait_for(self._operar_ble(nome, chave, comando), timeout=10)

    @staticmethod
    async def _operar_ble(nome: str, chave: str, comando: str) -> str:
        from bleak import BleakClient, BleakScanner

        encontrados = await BleakScanner.discover(timeout=2.0, return_adv=True)
        alvos = [
            dispositivo for dispositivo, anuncio in encontrados.values()
            if (anuncio.local_name or dispositivo.name) == nome
            and UUID_SERVICO in anuncio.service_uuids
        ]
        if len(alvos) != 1:
            raise LookupError("ESP32 Bluetooth ausente ou ambíguo")
        async with BleakClient(alvos[0], timeout=4.0) as cliente:
            if comando != "S":
                await cliente.write_gatt_char(
                    UUID_CONTROLE, f"{chave}|{comando}".encode("ascii"), response=True,
                )
            return bytes(await cliente.read_gatt_char(UUID_CONTROLE)).decode("ascii").strip()

    @staticmethod
    def _confirmar(valor: str, comando: str, transporte: str) -> ResultadoProtocolo:
        detalhes = {"transporte": transporte}
        if valor not in {"0", "1"} or (comando != "S" and valor != comando):
            return ResultadoProtocolo(False, erro="ESP32 não confirmou o estado", detalhes=detalhes)
        return ResultadoProtocolo(True, valor == "1", detalhes=detalhes)
