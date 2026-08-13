from __future__ import annotations

from types import SimpleNamespace

import pytest

from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
from mente_laylay.integracao.desktop_bridge import sanitizar_dashboard_estado
from mente_laylay.percepcao.telemetria_rede import TelemetriaRedeRuntime


class _Percentual:
    percent = 42.0


class _PsutilDashboard:
    @staticmethod
    def cpu_percent(*, interval=None):
        return 18.0

    @staticmethod
    def virtual_memory():
        return _Percentual()

    @staticmethod
    def disk_usage(_raiz):
        return _Percentual()

    @staticmethod
    def boot_time():
        return 100.0


def _dashboard(**extras) -> DashboardTerminalRuntime:
    parametros = {
        "configuracao_getter": lambda: {},
        "llm_getter": lambda: {},
        "interacao_getter": lambda: {},
        "memoria_saude_getter": lambda: {},
        "agenda_getter": lambda: [],
        "aprendizados_getter": lambda **_kwargs: [],
        "estado_mental_getter": lambda: {},
        "contexto_jogo_getter": lambda: {},
        "psutil_mod": _PsutilDashboard,
        "clock": lambda: 1_000.0,
        "monotonic": lambda: 1_000.0,
    }
    parametros.update(extras)
    return DashboardTerminalRuntime(**parametros)


def test_rede_calcula_download_upload_e_percentual_sem_gerar_trafego() -> None:
    relogio = {"agora": 10.0}
    bytes_rede = {"recebidos": 1_000_000.0, "enviados": 500_000.0}
    chamadas = {"contadores": 0}

    class PsutilRede:
        @staticmethod
        def net_if_stats():
            return {
                "Ethernet": SimpleNamespace(isup=True, speed=100, flags=""),
                "Loopback": SimpleNamespace(isup=True, speed=10_000, flags="loopback"),
            }

        @staticmethod
        def net_io_counters(*, pernic):
            assert pernic is True
            chamadas["contadores"] += 1
            return {
                "Ethernet": SimpleNamespace(
                    bytes_recv=bytes_rede["recebidos"],
                    bytes_sent=bytes_rede["enviados"],
                ),
                "Loopback": SimpleNamespace(bytes_recv=999_999_999, bytes_sent=999_999_999),
            }

    runtime = TelemetriaRedeRuntime(
        psutil_mod=PsutilRede,
        monotonic=lambda: relogio["agora"],
    )
    assert runtime.snapshot()["network_percent"] is None

    relogio["agora"] = 11.0
    bytes_rede["recebidos"] += 10_000_000
    bytes_rede["enviados"] += 1_250_000
    retrato = runtime.snapshot()

    assert retrato == {
        "network_percent": 90.0,
        "download_mbps": 80.0,
        "upload_mbps": 10.0,
        "source": "system-network-counters",
    }
    relogio["agora"] = 11.1
    assert runtime.snapshot() == retrato
    assert chamadas["contadores"] == 2


def test_rede_sem_velocidade_ainda_expoe_taxas_sem_inventar_percentual() -> None:
    relogio = {"agora": 1.0}
    contador = {"recebidos": 0, "enviados": 0}

    class PsutilRede:
        @staticmethod
        def net_if_stats():
            return {"VPN": SimpleNamespace(isup=True, speed=0, flags="")}

        @staticmethod
        def net_io_counters(*, pernic):
            return {"VPN": SimpleNamespace(
                bytes_recv=contador["recebidos"], bytes_sent=contador["enviados"],
            )}

    runtime = TelemetriaRedeRuntime(
        psutil_mod=PsutilRede,
        monotonic=lambda: relogio["agora"],
    )
    runtime.snapshot()
    contador.update(recebidos=125_000, enviados=62_500)
    relogio["agora"] = 2.0

    retrato = runtime.snapshot()
    assert retrato["network_percent"] is None
    assert retrato["download_mbps"] == 1.0
    assert retrato["upload_mbps"] == 0.5


def test_dashboard_e_ponte_publicam_somente_metricas_de_rede() -> None:
    runtime = _dashboard(network_getter=lambda: {
        "network_percent": 32.0,
        "download_mbps": 78.4,
        "upload_mbps": 9.2,
        "adapter": r"C:\segredo\Ethernet",
        "token": "sk-segredo",
    })
    sistema = runtime._sistema(1_000.0, {})

    assert sistema["network_percent"]["value"] == 32.0
    assert sistema["download_mbps"]["value"] == 78.4
    assert sistema["upload_mbps"]["value"] == 9.2

    publico = sanitizar_dashboard_estado({
        "generated_at": 1_000.0,
        "system": sistema,
    })
    assert publico["system"]["network_percent"]["value"] == 32.0
    assert publico["system"]["download_mbps"]["value"] == 78.4
    assert publico["system"]["upload_mbps"]["value"] == 9.2
    assert "adapter" not in publico["system"]
    assert "token" not in publico["system"]


def test_rede_reutiliza_os_componentes_visuais_do_sistema(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.dashboard import PainelLateralDashboard, PaginaSistema
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    app = QApplication.instance() or QApplication([])
    dashboard = {
        "system": {
            "network_percent": {
                "value": 32.0, "unit": "%", "freshness": "fresh",
                "observed_at": 1_000.0,
            },
            "download_mbps": {
                "value": 78.4, "unit": "Mbps", "freshness": "fresh",
                "observed_at": 1_000.0,
            },
            "upload_mbps": {
                "value": 9.2, "unit": "Mbps", "freshness": "fresh",
                "observed_at": 1_000.0,
            },
        },
        "music": {}, "routines": {},
    }

    lateral = PainelLateralDashboard()
    pagina_sistema = PaginaSistema()
    pagina_musica = PaginaMusicaM1()
    lateral.aplicar_dashboard(dashboard)
    pagina_sistema.aplicar_dashboard(dashboard)
    pagina_musica._aplicar_lateral(dashboard)
    app.processEvents()

    assert lateral.metricas["rede"].text() == "32%"
    assert lateral.barras_metricas["rede"].objectName() == "railSystemProgress"
    assert pagina_sistema.valores["network"].text() == "32%"
    assert pagina_sistema.rede_taxas.text() == "↓ 78,4Mbps  ·  ↑ 9,2Mbps"
    assert pagina_musica.sistema_valores["network_percent"].text() == "32%"
    assert pagina_musica.sistema_barras["network_percent"].objectName() == "musicSystemBar"

    lateral.deleteLater()
    pagina_sistema.deleteLater()
    pagina_musica.deleteLater()
    app.processEvents()


def test_rede_ausente_permanece_traco_sem_barra_falsa(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.dashboard import PainelLateralDashboard, PaginaSistema

    app = QApplication.instance() or QApplication([])
    lateral = PainelLateralDashboard()
    pagina = PaginaSistema()
    lateral.aplicar_dashboard({"system": {}})
    pagina.aplicar_dashboard({"system": {}})
    app.processEvents()

    assert lateral.metricas["rede"].text() == "—"
    assert lateral.barras_metricas["rede"].value() == 0
    assert lateral.barras_metricas["rede"].property("available") is False
    assert pagina.valores["network"].text() == "—"
    assert pagina.rede_taxas.text() == "↓ —  ·  ↑ —"

    lateral.deleteLater()
    pagina.deleteLater()
    app.processEvents()
