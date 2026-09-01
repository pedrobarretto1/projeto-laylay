from __future__ import annotations

from PySide6.QtWidgets import QApplication

from cliente.terminal_2.dashboard import PaginaAutomacao
from mente_laylay.integracao.acoes_painel_runtime import (
    comando_tipado_acao_painel,
)
from mente_laylay.integracao.desktop_bridge import sanitizar_dashboard_estado


def _iot_operacional() -> dict:
    return {
        "configured": True,
        "read_only": False,
        "controls_available": True,
        "mode": "simulado",
        "provider_available": True,
        "devices": [
            {
                "name": "lampada_quarto",
                "display_name": "Lâmpada do quarto",
                "type": "lampada_rgb",
                "room": "quarto",
                "capabilities": [
                    "ligar", "desligar", "status", "ajustar_brilho",
                    "ajustar_cor", "ajustar_branco",
                ],
                "state": "off",
                "state_confirmed": True,
                "state_observed_at": 995.0,
                "brightness_percent": 40,
            },
            {
                "name": "tomada_ventilador",
                "display_name": "Ventilador",
                "type": "tomada",
                "room": "quarto",
                "capabilities": ["ligar", "desligar", "alternar", "status"],
                "state": "on",
                "state_confirmed": True,
                "state_observed_at": 995.0,
            },
        ],
        "freshness": "fresh",
        "observed_at": 1_000.0,
    }


def test_red_p1_painel_iot_traduz_somente_payload_fechado() -> None:
    status = comando_tipado_acao_painel(
        "iot_status", {"device": "lampada_quarto"},
    )
    ligar = comando_tipado_acao_painel(
        "iot_power", {"device": "lampada_quarto", "state": "on"},
    )
    brilho = comando_tipado_acao_painel(
        "iot_brightness", {"device": "lampada_quarto", "value": 65},
    )

    assert status == (
        {
            "intent": "IOT_STATUS",
            "params": {
                "alvo": "lampada_quarto",
                "_execucao_silenciosa": True,
                "origem": "terminal_panel",
            },
        },
        "consulta manual IoT: lampada_quarto",
    )
    assert ligar == (
        {
            "intent": "IOT_CONTROL",
            "params": {
                "acao": "ligar",
                "alvo": "lampada_quarto",
                "_execucao_silenciosa": True,
                "origem": "terminal_panel",
            },
        },
        "controle manual IoT: ligar lampada_quarto",
    )
    assert brilho == (
        {
            "intent": "IOT_CONTROL",
            "params": {
                "acao": "ajustar_brilho",
                "alvo": "lampada_quarto",
                "valor": 65,
                "_execucao_silenciosa": True,
                "origem": "terminal_panel",
            },
        },
        "controle manual IoT: brilho lampada_quarto em 65 por cento",
    )
    assert comando_tipado_acao_painel(
        "iot_power", {"device": "lampada_quarto; apaga tudo", "state": "on"},
    ) is None
    assert comando_tipado_acao_painel(
        "iot_power", {"device": "lampada_quarto", "state": "toggle"},
    ) is None
    assert comando_tipado_acao_painel(
        "iot_brightness", {"device": "lampada_quarto", "value": 101},
    ) is None
    assert comando_tipado_acao_painel(
        "iot_brightness", {"device": "lampada_quarto", "value": True},
    ) is None


def test_p1_ponte_preserva_estado_confirmado_e_bloqueia_estado_inventado() -> None:
    seguro = sanitizar_dashboard_estado({"iot": _iot_operacional()})

    assert seguro["iot"]["mode"] == "simulado"
    assert seguro["iot"]["controls_available"] is True
    assert seguro["iot"]["read_only"] is False
    assert seguro["iot"]["devices"][0]["state"] == "off"
    assert seguro["iot"]["devices"][0]["state_confirmed"] is True
    assert seguro["iot"]["devices"][0]["brightness_percent"] == 40
    assert seguro["iot"]["devices"][1]["brightness_percent"] is None

    hostil = _iot_operacional()
    hostil["devices"][0].update(state="executando_shell", state_confirmed=True)
    hostil["devices"][1]["brightness_percent"] = 80
    filtrado = sanitizar_dashboard_estado({"iot": hostil})
    assert filtrado["iot"]["devices"][0]["state"] == "unknown"
    assert filtrado["iot"]["devices"][0]["state_confirmed"] is False
    assert filtrado["iot"]["devices"][1]["brightness_percent"] is None


def test_p1_card_iot_emite_controle_tipado_sem_mudar_estado_otimista() -> None:
    app = QApplication.instance() or QApplication([])
    pagina = PaginaAutomacao()
    eventos: list[tuple[str, str, dict]] = []
    pagina.acao_dados_solicitada.connect(
        lambda acao, texto, payload: eventos.append((acao, texto, payload)),
    )
    pagina.definir_conectada(True)
    pagina.aplicar_dashboard(sanitizar_dashboard_estado({"iot": _iot_operacional()}))
    app.processEvents()

    card = pagina.iot_dispositivos[0]
    assert card.estado_chave == "off"
    assert card.estado.text() == "DESLIGADA"
    assert card.botao_energia.text() == "Ligar"
    assert card.botao_energia.isEnabled()
    card.botao_energia.click()
    app.processEvents()

    assert eventos == [(
        "iot_power",
        "ligar Lâmpada do quarto",
        {"device": "lampada_quarto", "state": "on"},
    )]
    assert card.estado_chave == "off"
    assert card.estado.text() == "DESLIGADA"
    pagina.close()


def test_p2_lampada_tem_brilho_confirmado_e_ventilador_nao_tem_velocidade() -> None:
    app = QApplication.instance() or QApplication([])
    pagina = PaginaAutomacao()
    eventos: list[tuple[str, str, dict]] = []
    pagina.acao_dados_solicitada.connect(
        lambda acao, texto, payload: eventos.append((acao, texto, payload)),
    )
    pagina.definir_conectada(True)
    pagina.aplicar_dashboard(sanitizar_dashboard_estado({"iot": _iot_operacional()}))
    app.processEvents()

    lampada, ventilador = pagina.iot_dispositivos[:2]
    assert not lampada.controle_brilho.isHidden()
    assert lampada.brilho_confirmado == 40
    assert lampada.valor_brilho.text() == "40%"
    assert ventilador.controle_brilho.isHidden()
    assert not hasattr(ventilador, "controle_velocidade")

    lampada.slider_brilho.setValue(65)
    lampada._solicitar_brilho()
    app.processEvents()

    assert eventos == [(
        "iot_brightness",
        "ajustar o brilho de Lâmpada do quarto para 65 por cento",
        {"device": "lampada_quarto", "value": 65},
    )]
    assert lampada.brilho_confirmado == 40
    assert lampada.slider_brilho.value() == 40
    assert lampada.valor_brilho.text() == "40%"
    pagina.close()
