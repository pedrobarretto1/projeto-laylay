from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import pytest

from mente_laylay.integracao.desktop_bridge import sanitizar_estado
from mente_laylay.percepcao.ouvido_whisper import OuvidoWhisperRuntime


def _criar_janela(monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_laylay_2 import JanelaLaylay

    class Worker(QObject):
        mensagem = Signal(dict)
        conectado = Signal(bool)
        falha = Signal(str)

        def __init__(self) -> None:
            super().__init__()
            self.enviadas: list[dict] = []

        def enfileirar(self, mensagem: dict) -> bool:
            self.enviadas.append(dict(mensagem))
            return True

        def parar(self) -> None:
            return None

    app = QApplication.instance() or QApplication([])
    worker = Worker()
    janela = JanelaLaylay(worker, Path(__file__).parents[1])
    janela.show()
    worker.conectado.emit(True)
    for _ in range(4):
        app.processEvents()
    return app, worker, janela


def test_nivel_microfone_e_efemero_limitado_e_sem_audio() -> None:
    ouvido = OuvidoWhisperRuntime(
        processar_texto=lambda _texto: None,
        esta_falando=lambda: False,
    )
    ouvido._nivel_microfone = 1.8
    assert ouvido.nivel_microfone() == 1.0
    ouvido._nivel_microfone = -2
    assert ouvido.nivel_microfone() == 0.0

    estado = sanitizar_estado({"microphone_level": 0.62})
    assert estado["microphone_level"] == pytest.approx(0.62)
    assert "audio" not in estado and "samples" not in estado
    assert sanitizar_estado({"microphone_level": float("nan")})[
        "microphone_level"
    ] == 0.0


def test_p5_shell_tem_cabecalho_icones_svg_e_waveform_real(monkeypatch) -> None:
    app, worker, janela = _criar_janela(monkeypatch)
    assert "Como posso te ajudar hoje?" == janela.chat_subtitulo.text()
    assert not janela._nav["inicio"].icon().isNull()
    assert not janela._nav["musica"].icon().isNull()
    assert not janela.composer.botao.icon().isNull()

    worker.mensagem.emit({
        "type": "state",
        "activity": "listening",
        "activity_label": "Ouvindo",
        "emotion": "calma",
        "voice_available": True,
        "interaction_mode": "voice",
        "microphone_level": 0.73,
    })
    for _ in range(3):
        app.processEvents()
    assert janela.waveform._ativo is True
    assert janela.waveform._alvo == pytest.approx(0.73)
    janela.close()


def test_trocar_paginas_nao_promove_controles_do_topo_a_janelas(monkeypatch) -> None:
    app, _worker, janela = _criar_janela(monkeypatch)
    from PySide6.QtWidgets import QApplication

    for nome in (
        "inicio", "conversa", "automacao", "musica", "memoria", "sistema",
        "configuracoes", "inicio",
    ):
        janela.selecionar_pagina(nome)
        janela.resize(740 if nome == "conversa" else 1680, 900)
        for _ in range(2):
            app.processEvents()

    assert janela.voltar.parentWidget() is not None
    assert janela.avancar.parentWidget() is not None
    assert janela.titulo_header.parentWidget() is not None
    assert not janela.voltar.isWindow()
    assert not janela.avancar.isWindow()
    assert not janela.titulo_header.isWindow()
    toplevels = set(QApplication.topLevelWidgets())
    assert janela.voltar not in toplevels
    assert janela.avancar not in toplevels
    assert janela.titulo_header not in toplevels
    janela.close()


def test_botao_microfone_e_player_continuam_na_ponte_canonica(monkeypatch) -> None:
    app, worker, janela = _criar_janela(monkeypatch)
    worker.mensagem.emit({
        "type": "state", "activity": "idle", "activity_label": "Pronta",
        "emotion": "calma", "voice_available": True,
        "interaction_mode": "chat", "microphone_level": 0,
    })
    janela.composer.microfone.click()
    for _ in range(2):
        app.processEvents()
    assert any(
        item.get("type") == "mode_set" and item.get("mode") == "voice"
        for item in worker.enviadas
    )

    janela._atualizar_dashboard({
        "schema_version": 1,
        "status": "ok",
        "health": {},
        "context": {},
        "memory_recent": [],
        "system": {},
        "routines": {},
        "music": {
            "title": "Faixa observada", "channel": "Canal",
            "state": "playing", "position_seconds": 15,
            "duration_seconds": 120, "controls_available": True,
            "freshness": "fresh", "observed_at": 1,
        },
    })
    botao = janela.painel_lateral.musica_botoes["media_toggle"]
    assert botao.isEnabled()
    botao.click()
    for _ in range(2):
        app.processEvents()
    enviados = [
        item for item in worker.enviadas
        if item.get("type") == "input_submit"
    ]
    assert enviados[-1]["kind"] == "panel_action"
    assert enviados[-1]["action"] == "media_toggle"
    assert enviados[-1]["text"] == "pausa a música"
    janela.close()


def test_cartao_compacto_usa_a_mesma_thumbnail_observada_da_pagina_musica(
    monkeypatch,
) -> None:
    app, _worker, janela = _criar_janela(monkeypatch)
    thumbnail = "https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg"
    janela._atualizar_dashboard({
        "schema_version": 1,
        "status": "ok",
        "health": {},
        "context": {},
        "memory_recent": [],
        "system": {},
        "routines": {},
        "music": {
            "title": "Faixa observada", "channel": "Canal",
            "artwork_url": thumbnail,
            "state": "playing", "position_seconds": 15,
            "duration_seconds": 120, "controls_available": True,
            "freshness": "fresh", "observed_at": 1,
        },
    })
    for _ in range(2):
        app.processEvents()

    assert janela.painel_lateral.musica_capa._artwork_url == thumbnail
    assert janela.pagina_musica._artwork_url == thumbnail

    janela.painel_lateral.invalidar_dashboard()
    assert janela.painel_lateral.musica_capa._artwork_url == ""
    janela.close()


def test_historico_longo_preserva_feed_e_posicao_de_leitura(monkeypatch) -> None:
    app, _worker, janela = _criar_janela(monkeypatch)
    for indice in range(90):
        janela.adicionar_mensagem(
            "assistant" if indice % 2 else "user",
            f"Mensagem longa de regressão número {indice}. " * 2,
            animar=False,
            rolar_ao_final=False,
        )
    for _ in range(8):
        app.processEvents()
    barra = janela.scroll.verticalScrollBar()
    assert barra.maximum() > 0
    barra.setValue(barra.maximum() // 3)
    posicao = barra.value()
    janela.adicionar_mensagem(
        "assistant", "Nova resposta sem roubar a leitura antiga.",
        animar=False, rolar_ao_final=False,
    )
    for _ in range(4):
        app.processEvents()
    assert janela.scroll.horizontalScrollBar().maximum() == 0
    assert barra.value() == posicao
    janela.close()


def test_atalhos_foco_acessivel_e_movimento_reduzido(monkeypatch) -> None:
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "1")
    app, _worker, janela = _criar_janela(monkeypatch)
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    assert janela.composer.editor.accessibleName() == "Mensagem para a Laylay"
    assert janela.composer.botao.accessibleName() == "Enviar mensagem"
    assert janela._nav["musica"].accessibleName() == "Música"

    QTest.keyClick(janela, Qt.Key_4, Qt.ControlModifier)
    app.processEvents()
    assert janela.paginas.currentIndex() == 5
    QTest.keyClick(janela, Qt.Key_1, Qt.ControlModifier)
    app.processEvents()
    assert janela.paginas.currentIndex() == 0

    mensagem = janela.adicionar_mensagem(
        "assistant", "Resposta sem animação obrigatória.", animar=True,
    )
    assert mensagem is not None
    assert mensagem.graphicsEffect() is None
    janela.waveform.definir_nivel(0.8, ativo=True)
    janela.waveform._avancar()
    assert janela.waveform._fase == 0
    assert janela.waveform._nivel == pytest.approx(0.8)
    janela.close()


@pytest.mark.parametrize("escala", ["1", "1.25", "1.5"])
def test_ciclo_qt_real_abre_navega_redimensiona_e_fecha_em_dpi(
    escala: str,
) -> None:
    raiz = Path(__file__).parents[1]
    codigo = r'''
from pathlib import Path
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from cliente.terminal_laylay_2 import JanelaLaylay
class Worker(QObject):
    mensagem = Signal(dict)
    conectado = Signal(bool)
    falha = Signal(str)
    def enfileirar(self, _mensagem): return True
    def parar(self): return None
app = QApplication([])
worker = Worker()
janela = JanelaLaylay(worker, Path.cwd())
janela.show()
worker.conectado.emit(True)
for ciclo in range(4):
    for pagina in ("inicio", "conversa", "automacao", "musica", "memoria", "sistema", "configuracoes"):
        janela.selecionar_pagina(pagina)
        janela.resize(1680 if ciclo % 2 == 0 else 760, 940 if ciclo % 2 == 0 else 680)
        app.processEvents()
    janela._modo = "voice" if ciclo % 2 == 0 else "chat"
    janela._voz_disponivel = True
    janela._aplicar_modo()
    app.processEvents()
janela.close()
app.processEvents()
print("P5_DPI_OK")
'''
    ambiente = dict(os.environ)
    ambiente.update({
        "QT_QPA_PLATFORM": "offscreen",
        "QT_SCALE_FACTOR": escala,
        "LAYLAY_REDUZIR_MOVIMENTO": "1",
    })
    resultado = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=raiz,
        env=ambiente,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    saida = resultado.stdout + resultado.stderr
    assert resultado.returncode == 0, saida
    assert "P5_DPI_OK" in saida
    assert "Tcl_AsyncDelete" not in saida
    assert "Segmentation fault" not in saida
