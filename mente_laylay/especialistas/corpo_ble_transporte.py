"""Canal GATT do corpo, com o mesmo fluxo de bytes usado por USB e TCP."""
from __future__ import annotations

import asyncio
import hmac
import re
import secrets
from concurrent.futures import Future
from threading import Condition, Thread
from typing import Any

SERVICO_BLE = "e0086801-e5a7-44bb-ac7d-a21706aa9301"
ENTRADA_BLE = "e0086801-e5a7-44bb-ac7d-a21706aa9302"
SAIDA_BLE = "e0086801-e5a7-44bb-ac7d-a21706aa9303"


class FluxoCorpoBle:
    def __init__(self, token: str, *, scanner: Any, cliente_factory: Any) -> None:
        self._condicao = Condition()
        self._rx = bytearray()
        self._fechado = False
        self._loop = asyncio.new_event_loop()
        self._pronto: Future[None] = Future()
        self._thread = Thread(target=self._executar, args=(token, scanner, cliente_factory), daemon=True)
        self._thread.start()
        try:
            self._pronto.result(timeout=17)
        except BaseException:
            self.close()
            raise

    def _executar(self, token: str, scanner: Any, cliente_factory: Any) -> None:
        try:
            self._loop.run_until_complete(self._sessao(token, scanner, cliente_factory))
        except Exception as erro:
            if not self._pronto.done():
                self._pronto.set_exception(erro)
        finally:
            self._fechar_fluxo()
            self._loop.close()

    async def _sessao(self, token: str, scanner: Any, cliente_factory: Any) -> None:
        self._fim = asyncio.Event()
        self._notificacao = asyncio.Event()
        with self._condicao:
            if self._fechado:
                return
        alvos = await scanner.discover(timeout=3.0, service_uuids=[SERVICO_BLE])
        if len(alvos) != 1:
            raise ConnectionError("corpo_ble_ausente_ou_ambiguo")
        if self._fim.is_set():
            return
        async with cliente_factory(alvos[0], timeout=5.0, disconnected_callback=self._desconectou) as cliente:
            self._cliente = cliente
            await cliente.start_notify(SAIDA_BLE, self._receber)
            await asyncio.wait_for(self._autenticar(token), timeout=5)
            self._pronto.set_result(None)
            await self._fim.wait()

    def _receber(self, _caracteristica: Any, dados: bytearray) -> None:
        with self._condicao:
            if self._fechado:
                return
            if len(self._rx) + len(dados) > 2048:
                self._desconectou(None)
                return
            self._rx.extend(dados)
            self._condicao.notify_all()
        self._notificacao.set()

    def _desconectou(self, _cliente: Any) -> None:
        self._fechar_fluxo()
        self._fim.set()
        self._notificacao.set()

    def _fechar_fluxo(self) -> None:
        with self._condicao:
            self._fechado = True
            self._rx.clear()
            self._condicao.notify_all()

    async def _ler_linha_auth(self) -> bytes:
        while True:
            self._notificacao.clear()
            with self._condicao:
                if self._fechado:
                    raise ConnectionError("ble_desconectado")
                fim = self._rx.find(b"\n")
                if fim >= 0:
                    linha = bytes(self._rx[:fim])
                    del self._rx[:fim + 1]
                    return linha
            await self._notificacao.wait()

    async def _autenticar(self, token: str) -> None:
        nonce_cliente = secrets.token_hex(16)
        await self._escrever(f"BLE_HELLO 1 {nonce_cliente}\n".encode("ascii"))
        resposta = await self._ler_linha_auth()
        desafio = re.fullmatch(rb"BLE_CHALLENGE 1 ([0-9a-f]{32}) ([0-9a-f]{64})", resposta)
        if not desafio:
            raise ConnectionError("desafio_ble_invalido")
        nonces = f":{nonce_cliente}:{desafio[1].decode('ascii')}".encode("ascii")
        chave = token.encode("ascii")
        servidor = hmac.digest(chave, b"S" + nonces, "sha256").hex().encode("ascii")
        if not hmac.compare_digest(servidor, desafio[2]):
            raise ConnectionError("identidade_ble_divergente")
        cliente = hmac.digest(chave, b"C" + nonces, "sha256").hex().encode("ascii")
        await self._escrever(b"BLE_AUTH 1 " + cliente + b"\n")
        if await self._ler_linha_auth() != b"BLE_READY 1":
            raise ConnectionError("autenticacao_ble_recusada")

    async def _escrever(self, dados: bytes) -> None:
        for inicio in range(0, len(dados), 20):
            with self._condicao:
                if self._fechado:
                    raise ConnectionError("ble_desconectado")
            await self._cliente.write_gatt_char(ENTRADA_BLE, dados[inicio:inicio+20], response=True)

    def write(self, dados: bytes) -> int:
        with self._condicao:
            if self._fechado:
                raise ConnectionError("ble_desconectado")
            tarefa = asyncio.run_coroutine_threadsafe(self._escrever(dados), self._loop)
        try:
            tarefa.result(timeout=0.9)
        except Exception:
            tarefa.cancel()
            self.close()
            raise
        return len(dados)

    def read(self, tamanho: int) -> bytes:
        with self._condicao:
            self._condicao.wait_for(lambda: self._rx or self._fechado, timeout=0.08)
            if self._fechado:
                raise ConnectionError("ble_desconectado")
            dados = bytes(self._rx[:tamanho])
            del self._rx[:tamanho]
            return dados

    def close(self) -> None:
        self._fechar_fluxo()
        try:
            self._loop.call_soon_threadsafe(lambda: getattr(self, "_fim", None) and self._fim.set())
        except RuntimeError:
            pass  # O worker já fechou o loop.
        self._thread.join(timeout=1)


def abrir_corpo_ble(token: str) -> FluxoCorpoBle:
    from bleak import BleakClient, BleakScanner

    return FluxoCorpoBle(token, scanner=BleakScanner, cliente_factory=BleakClient)
