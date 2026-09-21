from __future__ import annotations

import json

from PySide6.QtWidgets import QApplication, QPushButton

from cliente.terminal_2.dashboard import PaginaAutomacao
from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
from mente_laylay.integracao.desktop_bridge import sanitizar_dashboard_estado


class _Percentual:
    percent = 20.0


class _Psutil:
    @staticmethod
    def cpu_percent(*, interval=None):
        return 10.0

    @staticmethod
    def virtual_memory():
        return _Percentual()

    @staticmethod
    def disk_usage(_raiz):
        return _Percentual()

    @staticmethod
    def boot_time():
        return 500.0


def _runtime(**trocas) -> DashboardTerminalRuntime:
    base = {
        "configuracao_getter": lambda: {},
        "llm_getter": lambda: {},
        "interacao_getter": lambda: {},
        "memoria_saude_getter": lambda: {
            "disponivel": True,
            "persistencia_local": True,
        },
        "agenda_getter": lambda: [],
        "aprendizados_getter": lambda **_kwargs: [],
        "estado_mental_getter": lambda: {},
        "contexto_jogo_getter": lambda: {},
        "psutil_mod": _Psutil,
        "clock": lambda: 1_000.0,
        "log": lambda _texto: None,
    }
    base.update(trocas)
    return DashboardTerminalRuntime(**base)


def _catalogo_iot_hostil() -> dict:
    return {
        "dispositivos": [
            {
                "nome": "lampada_quarto",
                "nome_amigavel": "Lâmpada do quarto",
                "tipo": "lampada_rgb",
                "ambiente": "quarto",
                "capacidades": [
                    "ligar",
                    "desligar",
                    "status",
                    "ajustar_brilho",
                    "ajustar_cor",
                    "ajustar_branco",
                    "executar_shell",
                ],
                "device_id": "id-super-secreto",
                "local_key": "chave-super-secreta",
                "configuracao": {"snapshot_path": "credencia_tuya/snapshot.json"},
            },
            {
                "nome": "tomada_ventilador",
                "nome_amigavel": "Ventilador",
                "tipo": "tomada",
                "ambiente": "quarto",
                "capacidades": ["ligar", "desligar", "alternar", "status"],
            },
        ],
        "credenciais": "nunca pode atravessar",
    }


def test_red_p0_dashboard_projeta_catalogo_iot_fechado_sem_autorizar_controle() -> None:
    runtime = _runtime(iot_getter=_catalogo_iot_hostil)

    retrato = runtime._iot(1_000.0)

    assert retrato == {
        "configured": True,
        "read_only": True,
        "controls_available": False,
        "mode": "unknown",
        "provider_available": False,
        "devices": [
            {
                "name": "lampada_quarto",
                "display_name": "Lâmpada do quarto",
                "type": "lampada_rgb",
                "room": "quarto",
                "capabilities": [
                    "ajustar_branco",
                    "ajustar_brilho",
                    "ajustar_cor",
                    "desligar",
                    "ligar",
                    "status",
                ],
                "state": "unknown",
                "state_confirmed": False,
                "state_observed_at": 0.0,
                "brightness_percent": None,
            },
            {
                "name": "tomada_ventilador",
                "display_name": "Ventilador",
                "type": "tomada",
                "room": "quarto",
                "capabilities": ["alternar", "desligar", "ligar", "status"],
                "state": "unknown",
                "state_confirmed": False,
                "state_observed_at": 0.0,
                "brightness_percent": None,
            },
        ],
        "freshness": "fresh",
        "observed_at": 1_000.0,
    }
    serializado = json.dumps(retrato, ensure_ascii=False)
    assert "local_key" not in serializado
    assert "device_id" not in serializado
    assert "credencia_tuya" not in serializado
    assert "executar_shell" not in serializado


def test_p0_ponte_reaplica_allowlist_iot_mesmo_com_dashboard_hostil() -> None:
    seguro = sanitizar_dashboard_estado({
        "schema_version": 1,
        "status": "ok",
        "generated_at": 1_000,
        "sequence": 1,
        "iot": {
            **_runtime(iot_getter=_catalogo_iot_hostil)._iot(1_000.0),
            "autoriza_execucao": True,
            "local_key": "segredo",
        },
    })

    assert seguro["iot"]["read_only"] is True
    assert seguro["iot"]["controls_available"] is False
    assert seguro["iot"]["devices"][0]["name"] == "lampada_quarto"
    assert "autoriza_execucao" not in seguro["iot"]
    assert "local_key" not in json.dumps(seguro, ensure_ascii=False)


def test_p0_coleta_real_publica_iot_no_snapshot_sem_criar_acao() -> None:
    runtime = _runtime(iot_getter=_catalogo_iot_hostil)
    runtime._coletar_impl()

    seguro = sanitizar_dashboard_estado(runtime._cache)

    assert seguro["iot"]["freshness"] == "fresh"
    assert len(seguro["iot"]["devices"]) == 2
    assert seguro["iot"]["controls_available"] is False
    assert "action" not in json.dumps(seguro["iot"], ensure_ascii=False)


def test_p0_automacao_exibe_casa_agora_sem_controle_fisico() -> None:
    app = QApplication.instance() or QApplication([])
    pagina = PaginaAutomacao()
    pagina.aplicar_dashboard(sanitizar_dashboard_estado({
        "schema_version": 1,
        "status": "ok",
        "generated_at": 1_000,
        "sequence": 1,
        "iot": _runtime(iot_getter=_catalogo_iot_hostil)._iot(1_000.0),
    }))
    app.processEvents()

    assert pagina.iot_estado.text() == (
        "2 dispositivos no catálogo seguro · estado físico ainda não consultado"
    )
    assert pagina.iot_dispositivos[0].nome.text() == "Lâmpada do quarto"
    assert pagina.iot_dispositivos[0].ambiente.text() == "QUARTO"
    assert pagina.iot_dispositivos[0]._suporta_brilho is True
    assert not pagina.iot_dispositivos[0].slider_brilho.isEnabled()
    controles = [
        botao
        for cartao in pagina.iot_dispositivos[:2]
        for botao in cartao.findChildren(QPushButton)
    ]
    assert controles
    assert all(not botao.isEnabled() for botao in controles)
    pagina.close()
