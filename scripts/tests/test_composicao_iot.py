from __future__ import annotations

from mente_laylay.iot.composicao import ComposicaoIoTLaylayRuntime
from mente_laylay.integracao.registro_iot import registrar_iot
import pytest


class _IoTFake:
    def __init__(self):
        self.deteccoes = []
        self.execucoes = []

    def detectar(self, texto, estado=None):
        self.deteccoes.append((texto, estado))
        return {"intent": "IOT_STATUS"}

    def executar(self, resultado, texto_original=""):
        self.execucoes.append((resultado, texto_original))
        return {"handled": True, "ok": True}

    def retrato_para_mente(self, _texto=""):
        return {
            "dispositivos": [{
                "nome": "lampada_quarto",
                "ambiente": "quarto",
                "local_key": "não pode sair",
                "configuracao": {"device_id": "segredo"},
            }],
        }


def _dependencias():
    return {
        "memoria_sqlite": object(),
        "falar": lambda *_: None,
        "estado_mental_getter": lambda: {"ultimo_dispositivo_iot": "lampada_quarto"},
        "definir_emocao": lambda *_: None,
        "enviar_mensagem": lambda *_args, **_kwargs: '{"rgb":[128,0,255]}',
        "log": lambda *_: None,
    }


def test_composicao_iot_monta_runtime_e_preserva_api() -> None:
    capturado = {}
    iot = _IoTFake()

    runtime = ComposicaoIoTLaylayRuntime(
        **_dependencias(),
        runtime_factory=lambda **kwargs: capturado.update(kwargs) or iot,
    )

    assert runtime.runtime is iot
    assert capturado["emitir_fala"] is False
    assert "modo" not in capturado
    assert capturado["resolver_cor"] == runtime.resolver_cor
    assert runtime.detectar("como está a luz?", {}) == {"intent": "IOT_STATUS"}
    assert runtime.executar({"intent": "IOT_STATUS"}, "consulta") == {
        "handled": True,
        "ok": True,
    }


def test_composicao_iot_resolve_cor_pela_mesma_fronteira_da_ia() -> None:
    chamadas = []
    dependencias = _dependencias()
    enviar = dependencias["enviar_mensagem"]

    def resolver(nome, *, enviar_mensagem, log):
        chamadas.append((nome, enviar_mensagem, log))
        return {"nome": nome, "rgb": (128, 0, 255)}

    runtime = ComposicaoIoTLaylayRuntime(
        **dependencias,
        runtime_factory=lambda **_kwargs: _IoTFake(),
        resolver_cor_fn=resolver,
        modo="tuya",
    )

    assert runtime.resolver_cor("roxo") == {"nome": "roxo", "rgb": (128, 0, 255)}
    assert chamadas[0][0] == "roxo"
    assert chamadas[0][1] is enviar


def test_registro_iot_preserva_api_e_remove_configuracao_sensivel() -> None:
    iot = _IoTFake()
    registro = registrar_iot(iot)

    assert registro.servico is iot
    assert registro.detectar("como está a luz?", {}) == {"intent": "IOT_STATUS"}
    assert registro.executar({"intent": "IOT_STATUS"}, "consulta")["ok"] is True
    retrato = registro.retrato_para_mente("quais dispositivos?")
    dispositivo = retrato["dispositivos"][0]
    assert dispositivo == {"nome": "lampada_quarto", "ambiente": "quarto"}
    assert "segredo" not in repr(registro).casefold()
    # A sanitização da fronteira não altera o objeto mantido pelo runtime.
    assert "local_key" in iot.retrato_para_mente()["dispositivos"][0]


def test_registro_iot_rejeita_servico_incompleto_na_composicao() -> None:
    with pytest.raises(RuntimeError, match="operações ausentes"):
        registrar_iot(object())
