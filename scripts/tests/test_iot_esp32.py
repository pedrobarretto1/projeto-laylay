from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
import requests

from memoria_sqlite import MemoriaSQLite
from mente_laylay.especialistas.capacidades import consultar_capacidade
from mente_laylay.integracao.acoes_painel_runtime import executar_acao_painel_tipado
from mente_laylay.integracao.desktop_bridge import ErroProtocoloDesktop, validar_mensagem_cliente
from mente_laylay.iot.composicao import criar_composicao_iot_laylay_runtime
from mente_laylay.iot.protocolos.esp32 import ProtocoloESP32
from mente_laylay.iot.registro import criar_dispositivo_esp32


@pytest.fixture
def iot(monkeypatch, tmp_path):
    monkeypatch.setenv("LAYLAY_IOT_ESP32", "SIM")
    monkeypatch.setenv("IOT_CONTROLE_FISICO_AUTORIZADO", "SIM")
    monkeypatch.setenv("LAYLAY_IOT_ESP32_KEY", "0123456789abcdef")
    monkeypatch.setenv("LAYLAY_IOT_ESP32_BLE_NAME", "Laylay Home")
    memoria = MemoriaSQLite(str(tmp_path / "iot.db"))
    estado = {}

    def criar():
        return criar_composicao_iot_laylay_runtime(
            memoria_sqlite=memoria, falar=lambda *_: None,
            estado_mental_getter=lambda: estado, definir_emocao=None,
            enviar_mensagem=lambda *_: None, modo="simulado", log=lambda *_: None,
        )

    return criar


def test_composicao_iot_executa_rele_e_rele_estado_separadamente(iot, monkeypatch):
    def post(_sessao, url, *, headers, data, **opcoes):
        assert url == "http://laylay-home.local/api/rele"
        assert headers["X-Laylay-Key"] == "0123456789abcdef"
        assert opcoes["allow_redirects"] is False
        chamadas.append(data)
        return SimpleNamespace(status_code=200, text=next(respostas))

    chamadas = []
    respostas = iter(["0", "1", "1", "1", "0", "1"])
    monkeypatch.setattr(requests.Session, "post", post)
    app = iot()
    texto = "Laylay, liga o relé ESP32"
    ligado = app.executar(app.detectar(texto), texto)
    assert (ligado["status"], ligado["confirmado"], ligado["modo"]) == ("ligado", True, "esp32")
    texto = "desliga o relé"
    falha = app.executar(app.detectar(texto), texto)
    assert (falha["status"], falha["confirmado"]) == ("falha_validacao", False)
    assert chamadas == ["S", "1", "S", "S", "0", "S"]


def test_transporte_faz_fallback_ble_quando_wifi_falha(iot, monkeypatch):
    def post(*_args, **_kwargs):
        raise requests.ConnectionError

    async def ble(_protocolo, nome, chave, comando):
        assert (nome, chave, comando) == ("Laylay Home", "0123456789abcdef", "1")
        return "1"

    monkeypatch.setattr(requests.Session, "post", post)
    monkeypatch.setattr(ProtocoloESP32, "_operar_ble_limitado", ble)
    resposta = ProtocoloESP32().definir_estado(criar_dispositivo_esp32(), True)
    assert resposta.ok and resposta.estado is True
    assert resposta.detalhes == {"transporte": "bluetooth"}


def test_painel_persiste_configuracao_e_informa_capacidade(iot):
    payload = {
        "device": "rele_esp32", "display_name": "Relé da bancada", "room": "Escritório",
        "transport": "bluetooth", "ble_name": "Laylay Home",
    }
    mensagem = {
        "type": "input_submit", "kind": "panel_action", "action": "iot_esp32_config",
        "text": "salvar configuração ESP32", "payload": payload,
    }
    validado = validar_mensagem_cliente(mensagem, token="teste", autenticado=True)
    app = iot()
    resultado = executar_acao_painel_tipado(
        mensagem["action"], validado["payload"], executar_intencao=app.executar,
        configurar_esp32=app.runtime.configurar_esp32,
    )
    assert resultado["confirmado"] is True
    app = iot()
    assert app.detectar("liga o relé da bancada")["params"]["alvo"] == "rele_esp32"
    retrato = app.runtime.retrato_para_mente()
    dispositivo = next(d for d in retrato["dispositivos"] if d["nome"] == "rele_esp32")
    assert dispositivo["ambiente"] == "Escritório"
    assert dispositivo["transporte_esp32"] == "bluetooth"
    assert "0123456789abcdef" not in json.dumps(retrato)
    assert "Bluetooth LE" in consultar_capacidade("IOT_CONTROL")["limites"]
    with pytest.raises(ErroProtocoloDesktop):
        validar_mensagem_cliente(
            {**mensagem, "payload": {**payload, "key": "x"}}, token="teste", autenticado=True,
        )
    assert not app.runtime.configurar_esp32("rele_esp32", "lâmpada", "Quarto", "auto", "Laylay Home")


def test_esp32_exige_autorizacao_fisica_e_bloqueia_acao_autonoma(iot, monkeypatch):
    def sem_rede(*_args, **_kwargs):
        pytest.fail("consulta física sem autorização")

    monkeypatch.setattr(requests.Session, "post", sem_rede)
    app = iot()
    resultado = app.executar({
        "intent": "IOT_CONTROL",
        "params": {"acao": "ligar", "alvo": "rele_esp32", "origem": "autonomia"},
    })
    assert resultado["status"] == "confirmacao_necessaria"
    monkeypatch.setenv("IOT_CONTROLE_FISICO_AUTORIZADO", "NAO")
    app = iot()
    assert app.runtime.registro.resolver("rele_esp32") is None


@pytest.mark.parametrize("nome", ["rele_esp32", "lampada_quarto", "tomada_ventilador"])
def test_esquecer_dispositivo_pelo_painel_persiste_sem_enviar_comando(iot, nome, monkeypatch):
    def sem_rede(*_args, **_kwargs):
        pytest.fail("Esquecer não deve enviar comando físico")

    monkeypatch.setattr(requests.Session, "post", sem_rede)
    app = iot()
    mensagem = {
        "type": "input_submit", "kind": "panel_action", "action": "iot_forget",
        "text": "esquecer dispositivo IoT", "payload": {"device": nome},
    }
    assert app.runtime.registro.resolver(nome)
    with pytest.raises(ErroProtocoloDesktop):
        validar_mensagem_cliente(mensagem, token="teste", autenticado=True)
    assert executar_acao_painel_tipado(
        "iot_forget", mensagem["payload"], executar_intencao=app.executar,
        esquecer_dispositivo=app.runtime.esquecer_dispositivo,
    ) is False

    mensagem["payload"]["confirmed"] = True
    validado = validar_mensagem_cliente(mensagem, token="teste", autenticado=True)
    resultado = executar_acao_painel_tipado(
        "iot_forget", validado["payload"], executar_intencao=app.executar,
        esquecer_dispositivo=app.runtime.esquecer_dispositivo,
    )
    assert resultado["confirmado"] is True
    for sessao in (app, iot()):
        assert nome not in {item["nome"] for item in sessao.runtime.retrato_para_mente()["dispositivos"]}
        assert sessao.executar({
            "intent": "IOT_CONTROL", "params": {"alvo": nome, "acao": "desligar"},
        })["status"] == "nao_encontrado"
