from __future__ import annotations

from types import SimpleNamespace

import pytest

from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
from mente_laylay.integracao.desktop_bridge import sanitizar_dashboard_estado
from mente_laylay.percepcao.telemetria_gpu import TelemetriaGpuRuntime


class _Percentual:
    percent = 42.0


class _Psutil:
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
        "psutil_mod": _Psutil,
        "clock": lambda: 1_000.0,
        "monotonic": lambda: 1_000.0,
    }
    parametros.update(extras)
    return DashboardTerminalRuntime(**parametros)


def test_nvidia_smi_publica_uso_e_vram_percentual_com_cache() -> None:
    chamadas: list[list[str]] = []

    def executar(comando, **_kwargs):
        chamadas.append(list(comando))
        return SimpleNamespace(
            returncode=0,
            stdout="25, 4514, 6144\n7, 1024, 4096\n",
        )

    runtime = TelemetriaGpuRuntime(
        run=executar,
        which=lambda _nome: r"C:\\driver\\nvidia-smi.exe",
        monotonic=lambda: 10.0,
    )

    primeiro = runtime.snapshot()
    segundo = runtime.snapshot()

    assert primeiro == {
        "gpu_percent": 25.0,
        "vram_percent": 73.5,
        "source": "nvidia-smi",
    }
    assert segundo == primeiro
    assert len(chamadas) == 1
    assert "--query-gpu=utilization.gpu,memory.used,memory.total" in chamadas[0]


def test_fallback_windows_agrega_processos_da_mesma_engine_sem_inventar_vram() -> None:
    motores = [
        SimpleNamespace(
            Name="pid_10_luid_0x0_0x1_phys_0_eng_0_engtype_3D",
            UtilizationPercentage=18,
        ),
        SimpleNamespace(
            Name="pid_20_luid_0x0_0x1_phys_0_eng_0_engtype_3D",
            UtilizationPercentage=24,
        ),
        SimpleNamespace(
            Name="pid_20_luid_0x0_0x1_phys_0_eng_1_engtype_Copy",
            UtilizationPercentage=99,
        ),
    ]

    class Servico:
        @staticmethod
        def Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine():
            return motores

    runtime = TelemetriaGpuRuntime(
        which=lambda _nome: None,
        os_name="nt",
        wmi_factory=lambda **_kwargs: Servico(),
    )

    assert runtime.snapshot() == {
        "gpu_percent": 42.0,
        "vram_percent": None,
        "source": "windows-performance-counters",
    }


def test_dashboard_e_ponte_preservam_apenas_metricas_gpu_validas() -> None:
    runtime = _dashboard(gpu_getter=lambda: {
        "gpu_percent": 37.0,
        "vram_percent": 68.5,
        "source": r"C:\\segredo\\driver.exe",
        "token": "sk-segredo",
    })
    sistema = runtime._sistema(1_000.0, {})

    assert sistema["gpu_percent"]["value"] == 37.0
    assert sistema["vram_percent"]["value"] == 68.5
    publico = sanitizar_dashboard_estado({
        "generated_at": 1_000.0,
        "system": sistema,
    })
    assert publico["system"]["gpu_percent"]["value"] == 37.0
    assert publico["system"]["vram_percent"]["value"] == 68.5
    assert "source" not in publico["system"]
    assert "token" not in publico["system"]


def test_interface_reutiliza_o_mesmo_estilo_para_gpu_e_vram(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.dashboard import PainelLateralDashboard, PaginaSistema
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    app = QApplication.instance() or QApplication([])
    dashboard = {
        "system": {
            "gpu_percent": {
                "value": 37.0, "unit": "%", "freshness": "fresh",
                "observed_at": 1_000.0,
            },
            "vram_percent": {
                "value": 68.5, "unit": "%", "freshness": "fresh",
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

    assert lateral.metricas["gpu"].text() == "37%"
    assert lateral.metricas["vram"].text() == "68,5%"
    assert lateral.barras_metricas["gpu"].objectName() == "railSystemProgress"
    assert lateral.barras_metricas["vram"].objectName() == "railSystemProgress"
    assert pagina_sistema.valores["gpu"].text() == "37%"
    assert pagina_sistema.valores["vram"].text() == "68%"
    assert pagina_musica.sistema_valores["gpu_percent"].text() == "37%"
    assert pagina_musica.sistema_valores["vram_percent"].text() == "68,5%"
    assert pagina_musica.sistema_barras["gpu_percent"].objectName() == "musicSystemBar"
    assert pagina_musica.sistema_barras["vram_percent"].objectName() == "musicSystemBar"

    lateral.deleteLater()
    pagina_sistema.deleteLater()
    pagina_musica.deleteLater()
    app.processEvents()


def test_gpu_ausente_permanece_traco_sem_barra_falsa(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.dashboard import PainelLateralDashboard

    app = QApplication.instance() or QApplication([])
    painel = PainelLateralDashboard()
    painel.aplicar_dashboard({"system": {}, "music": {}, "routines": {}})
    app.processEvents()

    assert painel.metricas["gpu"].text() == "—"
    assert painel.metricas["vram"].text() == "—"
    assert painel.barras_metricas["gpu"].value() == 0
    assert painel.barras_metricas["vram"].value() == 0
    assert painel.barras_metricas["gpu"].property("available") is False
    assert painel.barras_metricas["vram"].property("available") is False

    painel.deleteLater()
    app.processEvents()
