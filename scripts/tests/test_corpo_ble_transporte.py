import hmac
import json
from types import SimpleNamespace

import pytest

from mente_laylay.especialistas.corpo_ble_transporte import (
    ENTRADA_BLE, SAIDA_BLE, SERVICO_BLE, FluxoCorpoBle,
)
from mente_laylay.especialistas.capacidades import consultar_capacidade
from mente_laylay.integracao.composicao_rosto_oled import criar_composicao_rosto_oled_runtime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
from scripts.tests.test_corpo_transporte_oled import EspCorpo

TOKEN = "c7" * 32


class GattSimulado:
    """Dublê da borda de rádio. Fragmenta notificações como o ESP."""
    def __init__(self, *, token=TOKEN, alvos=1):
        self.token = token
        self.alvos = alvos
        self.esp = EspCorpo()
        self.fragmentos = []
        self._rx = bytearray()
        self.autenticada = False
        self.fechada = False

    async def discover(self, *, timeout, service_uuids):
        assert service_uuids == [SERVICO_BLE]
        return [object() for _ in range(self.alvos)]

    def cliente(self, _alvo, *, timeout, disconnected_callback):
        self.desconectou = disconnected_callback
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        self.fechada = True

    async def start_notify(self, caracteristica, callback):
        assert caracteristica == SAIDA_BLE
        self.callback = callback

    async def write_gatt_char(self, caracteristica, dados, *, response):
        assert caracteristica == ENTRADA_BLE and response and len(dados) <= 20
        self.fragmentos.append(bytes(dados))
        self._rx.extend(dados)
        if b"\n" not in self._rx:
            return
        linha = bytes(self._rx)
        self._rx.clear()
        if linha.startswith(b"BLE_HELLO "):
            nonce = b"a" * 32
            self.nonces = b":" + linha[12:-1] + b":" + nonce
            resposta = b"BLE_CHALLENGE 1 " + nonce + b" " + self.prova(b"S") + b"\n"
        elif linha.startswith(b"BLE_AUTH "):
            assert linha == b"BLE_AUTH 1 " + self.prova(b"C") + b"\n"
            self.autenticada = True
            resposta = b"BLE_READY 1\n"
        else:
            assert self.autenticada
            self.esp.write(linha)
            resposta = self.esp.read(512)
        for inicio in range(0, len(resposta), 20):
            self.callback(None, resposta[inicio:inicio+20])

    def prova(self, papel):
        return hmac.digest(self.token.encode(), papel + self.nonces, "sha256").hex().encode()

    def abrir(self, token):
        return FluxoCorpoBle(token, scanner=self, cliente_factory=self.cliente)


@pytest.mark.parametrize("radio,motivo", [
    (GattSimulado(token="ab"*32), "identidade_ble_divergente"),
    (GattSimulado(alvos=2), "corpo_ble_ausente_ou_ambiguo"),
])
def test_ble_recusa_identidade_errada_e_descoberta_ambigua(radio, motivo):
    with pytest.raises(ConnectionError, match=motivo):
        radio.abrir(TOKEN)
    assert not radio.autenticada and not radio.esp.enviados


def test_composicao_ble_reutiliza_sessao_corporal_e_para_sem_replay(tmp_path):
    radio = GattSimulado()
    cfg = tmp_path / "pareamento.json"
    cfg.write_text(json.dumps(dict(version=1, ativo=True, host="127.0.0.1", porta=8765,
                                   hostname="laylay-corpo.local", token=TOKEN)))
    mente = criar_estado_compartilhado_runtime()
    r = criar_composicao_rosto_oled_runtime(
        estado=mente, observabilidade=SimpleNamespace(relatar_falha=lambda *a, **k: None),
        porta="BLE", config_wifi_path=cfg, abrir_ble=radio.abrir,
        listar_portas=lambda: pytest.fail("BLE explícito não procura USB"),
    )
    try:
        assert r.sincronizar(), r.diagnostico()
        assert (r.diagnostico()["transporte"], r.diagnostico()["canal_autenticado"]) == ("ble", True)
        assert not any(x.startswith("MOTOR ") for x in radio.esp.enviados)
        resultado = r.mover_corpo(170, 170, 50)
        assert resultado["ok"] and resultado["parada_confirmada"] and not resultado["prova_rotacao"]
        assert sum(x.startswith("MOTOR ") for x in radio.esp.enviados) == 1
        assert TOKEN.encode() not in b"".join(radio.fragmentos)
    finally:
        r.encerrar()
    assert radio.fechada


def test_ble_desconexao_descarta_buffer_e_desbloqueia_leitura():
    radio = GattSimulado()
    fluxo = radio.abrir(TOKEN)
    try:
        fluxo._loop.call_soon_threadsafe(radio.desconectou, radio)
        with pytest.raises(ConnectionError, match="ble_desconectado"):
            fluxo.read(1)
        with pytest.raises(ConnectionError, match="ble_desconectado"):
            fluxo.write(b"MOTOR\n")
    finally:
        fluxo.close()
    assert not radio.esp.enviados


def test_catalogo_corporal_descreve_ble_com_adaptador_e_pareamento():
    capacidade = consultar_capacidade("CORPO_COMPANHIA")
    texto = capacidade["bluetooth_condicional"]
    assert "adaptador" in texto and "pareamento" in texto and "AUTO" in texto
