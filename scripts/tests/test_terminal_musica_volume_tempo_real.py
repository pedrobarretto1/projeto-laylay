from __future__ import annotations

import pytest


class _DefinidorFalso:
    def __init__(self, resultados: list[bool] | None = None) -> None:
        self.valores: list[int] = []
        self.inicios = 0
        self.finais = 0
        self._resultados = list(resultados or [])

    def iniciar_gesto(self) -> None:
        self.inicios += 1

    def finalizar_gesto(self) -> None:
        self.finais += 1

    def __call__(self, nivel: int) -> bool:
        self.valores.append(nivel)
        return self._resultados.pop(0) if self._resultados else True


def _pagina(monkeypatch, definidor=None):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    app = QApplication.instance() or QApplication([])
    pagina = PaginaMusicaM1(definidor_volume_local=definidor)
    pagina.definir_conectada(True)
    pagina.aplicar_dashboard({
        "music": {"volume_percent": 30},
        "system": {},
        "routines": {},
    })
    return app, pagina


def _fechar(app, pagina) -> None:
    pagina.close()
    app.processEvents()


def test_volume_local_coalesce_arraste_e_aplica_final_sem_acao_textual(
    monkeypatch,
) -> None:
    definidor = _DefinidorFalso()
    app, pagina = _pagina(monkeypatch, definidor)
    pedidos: list[tuple[str, str]] = []
    pagina.acao_solicitada.connect(lambda acao, texto: pedidos.append((acao, texto)))

    pagina.volume_slider.sliderPressed.emit()
    pagina.volume_slider.setValue(41)
    pagina.volume_slider.setValue(52)
    pagina.volume_slider.setValue(63)

    assert pagina._timer_volume_local.isActive()
    assert definidor.valores == []
    pagina._aplicar_volume_local_pendente()
    assert definidor.valores == [63]

    pagina.volume_slider.setValue(67)
    pagina.volume_slider.sliderReleased.emit()

    assert definidor.valores == [63, 67]
    assert definidor.inicios == 1
    assert definidor.finais == 1
    assert pedidos == []
    assert pagina.volume.text() == "VOLUME\n67%"
    assert pagina.acoes_sessao["Volume —"].text() == "◖  Volume 67%"
    assert pagina.audicao_volume_valor.text() == "67%"
    _fechar(app, pagina)


def test_volume_sem_setter_local_usa_um_unico_fallback_e_nao_toca_windows(
    monkeypatch,
) -> None:
    app, pagina = _pagina(monkeypatch)
    pedidos: list[tuple[str, str]] = []
    pagina.acao_solicitada.connect(lambda acao, texto: pedidos.append((acao, texto)))

    assert pagina._definidor_volume_local is None
    pagina.volume_slider.sliderPressed.emit()
    pagina.volume_slider.setValue(48)
    pagina.volume_slider.sliderReleased.emit()

    assert pedidos == [("volume_set", "deixa o volume em 48 por cento")]
    _fechar(app, pagina)


def test_volume_setter_falho_nao_repete_erro_e_preserva_fallback(
    monkeypatch,
) -> None:
    definidor = _DefinidorFalso([False])
    app, pagina = _pagina(monkeypatch, definidor)
    pedidos: list[tuple[str, str]] = []
    pagina.acao_solicitada.connect(lambda acao, texto: pedidos.append((acao, texto)))

    pagina.volume_slider.sliderPressed.emit()
    pagina.volume_slider.setValue(54)
    pagina._aplicar_volume_local_pendente()
    pagina.volume_slider.setValue(59)
    pagina.volume_slider.sliderReleased.emit()

    assert definidor.valores == [54]
    assert pedidos == [("volume_set", "deixa o volume em 59 por cento")]
    _fechar(app, pagina)


def test_dashboard_nao_sobrescreve_volume_enquanto_usuario_arrasta(
    monkeypatch,
) -> None:
    app, pagina = _pagina(monkeypatch, _DefinidorFalso())

    pagina.volume_slider.sliderPressed.emit()
    pagina.volume_slider.setValue(72)
    pagina.aplicar_dashboard({
        "music": {"volume_percent": 12},
        "system": {},
        "routines": {},
    })

    assert pagina.volume_slider.value() == 72
    assert pagina.volume.text() == "VOLUME\n72%"
    assert pagina.acoes_sessao["Volume —"].text() == "◖  Volume 72%"
    assert pagina.audicao_volume_valor.text() == "72%"
    pagina.volume_slider.sliderReleased.emit()
    _fechar(app, pagina)


def test_definidor_windows_cacheia_endpoint_no_gesto_e_reabre_apos_falha() -> None:
    from cliente.terminal_2.volume_mestre_windows import (
        DefinidorVolumeMestreWindows,
    )

    class _Endpoint:
        def __init__(self) -> None:
            self.nivel = 0.0

        def SetMasterVolumeLevelScalar(self, nivel, _contexto) -> None:
            self.nivel = nivel

        def GetMasterVolumeLevelScalar(self) -> float:
            return self.nivel

    criados: list[_Endpoint] = []

    def fabrica() -> _Endpoint:
        endpoint = _Endpoint()
        criados.append(endpoint)
        return endpoint

    definidor = DefinidorVolumeMestreWindows(fabrica)
    definidor.iniciar_gesto()
    assert definidor(25)
    assert definidor(60)
    assert len(criados) == 1
    definidor.finalizar_gesto()
    definidor.iniciar_gesto()
    assert definidor(70)
    assert len(criados) == 2


def test_definidor_windows_silencia_falha_ate_o_proximo_gesto() -> None:
    from cliente.terminal_2.volume_mestre_windows import (
        DefinidorVolumeMestreWindows,
    )

    chamadas = 0

    def fabrica() -> object:
        nonlocal chamadas
        chamadas += 1
        if chamadas == 1:
            raise OSError("COM indisponível")
        return type("Endpoint", (), {
            "SetMasterVolumeLevelScalar": lambda self, nivel, contexto: setattr(
                self, "nivel", nivel,
            ),
            "GetMasterVolumeLevelScalar": lambda self: self.nivel,
        })()

    definidor = DefinidorVolumeMestreWindows(fabrica)
    definidor.iniciar_gesto()
    assert not definidor(40)
    assert not definidor(45)
    assert chamadas == 1
    definidor.iniciar_gesto()
    assert definidor(50)
    assert chamadas == 2
