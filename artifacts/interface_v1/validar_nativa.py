"""Captura o cliente real com ponte autenticada e telemetria somente leitura.

Não inicia a mente, microfone, player, automações ou serviços externos. Usa
preferências temporárias; não carrega credenciais ou histórico pessoal.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offscreen", action="store_true")
    args = parser.parse_args()
    os.environ["QT_QPA_PLATFORM"] = "offscreen" if args.offscreen else "windows"
    os.environ["LAYLAY_REDUZIR_MOVIMENTO"] = "1"
    import psutil
    from PySide6.QtCore import QSettings, QThread
    from PySide6.QtGui import QFont
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    import cliente.terminal_laylay_2 as terminal
    from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
    from mente_laylay.integracao.desktop_bridge import DesktopBridgeRuntime

    saida = Path(__file__).parent
    erros: list[str] = []
    original_hook = sys.excepthook
    def capturar_erro(tipo, erro, tb):
        erros.append(f"{tipo.__name__}: {erro}")
        original_hook(tipo, erro, tb)
    sys.excepthook = capturar_erro
    preferencias = tempfile.TemporaryDirectory(prefix="laylay-interface-v1-")
    settings_original = terminal.QSettings
    terminal.QSettings = lambda *_: QSettings(
        str(Path(preferencias.name) / "interface.ini"), QSettings.IniFormat,
    )
    app = QApplication([])
    app.setApplicationName("Laylay Interface 1.0 — validação nativa")
    app.setFont(QFont(terminal.carregar_fontes_interface(), 10))
    entradas: list[str] = []
    mensagens: list[dict] = []
    pedidos_ui: list[dict] = []
    estado = {
        "activity": "idle", "activity_label": "Verificação da interface",
        "emotion": "calma", "voice_available": False, "interaction_mode": "chat",
    }
    dashboard = DashboardTerminalRuntime(
        configuracao_getter=lambda: {}, llm_getter=lambda: {},
        interacao_getter=lambda: dict(estado), memoria_saude_getter=lambda: {},
        agenda_getter=lambda: [], aprendizados_getter=lambda **_: [],
        estado_mental_getter=lambda: {}, contexto_jogo_getter=lambda: {},
        psutil_mod=psutil, projeto="Laylay", intervalo_s=0.3, log=lambda _: None,
    )
    ponte = DesktopBridgeRuntime(
        enviar_entrada=entradas.append, historico_getter=lambda: [],
        estado_getter=lambda: dict(estado), dashboard_getter=dashboard.snapshot,
        dashboard_interval_s=0.3, log=lambda _: None,
    )
    ponte.iniciar()
    worker = terminal.PonteWorker(*ponte.endereco, ponte.token, session_id=ponte.session_id)
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.executar)
    worker.terminou.connect(thread.quit)
    worker.mensagem.connect(mensagens.append)
    janela = terminal.JanelaLaylay(worker, RAIZ, session_id=ponte.session_id)
    janela.enviar_json.connect(pedidos_ui.append)
    capturas: list[dict] = []

    def aguardar(condicao, segundos=6):
        limite = time.monotonic() + segundos
        while not condicao() and time.monotonic() < limite:
            QTest.qWait(25)
        if not condicao():
            raise AssertionError("Estado não entregue pela composição Qt/ponte")

    def foto(nome: str):
        QTest.qWait(150)
        caminho = saida / f"{nome}.png"
        assert janela.grab().save(str(caminho))
        capturas.append({"arquivo": caminho.name, "largura": janela.width(), "altura": janela.height()})

    try:
        janela.resize(1440, 900)
        janela.show()
        thread.start()
        aguardar(lambda: janela._conectado and janela._dashboard_recebido)
        aguardar(lambda: bool(janela._dashboard_mais_recente.get("system", {}).get("cpu_percent", {}).get("observed_at")))
        foto("inicio-nativo")
        for pagina in ("musica", "sistema", "configuracoes", "memoria", "automacao"):
            janela.selecionar_pagina(pagina)
            QTest.qWait(140)
            foto(f"{pagina}-nativo")
        janela.selecionar_pagina("conversa")
        janela.enviar_texto("Verificação local do recebimento pela ponte.")
        aguardar(lambda: len(entradas) == 1)
        aguardar(lambda: any(m.get("type") == "input_ack" and m.get("accepted") for m in mensagens))
        janela.apresentacao.definir_modo("ilha")
        assert ponte.publicar_fala_final("A ponte autenticada recebeu a mensagem. A mente não está conectada nesta validação.")
        aguardar(lambda: not janela._envios)
        foto("ilha-nativa")
        janela.apresentacao.definir_modo("painel")
        foto("painel-nativo")
        janela.apresentacao.definir_modo("completa")
        foto("conversa-nativa")
        for largura, altura in ((768, 800), (375, 667)):
            janela.resize(largura, altura)
            foto(f"conversa-{largura}")
        janela.resize(1440, 900)
        janela.selecionar_pagina("sistema")
        janela.apresentacao.definir_modo("painel")
        janela.apresentacao.definir_modo("completa")
        assert janela._pagina_visual_ativa == "sistema"
        assert entradas == ["Verificação local do recebimento pela ponte."]
        assert not erros
        resultado = {
            "plataforma": app.platformName(), "capturas": capturas,
            "ponte_autenticada": janela._conectado,
            "dashboard_real_psutil": True, "mente_iniciada": False,
            "microfone_iniciado": False, "efeitos_externos": False,
            "envios_texto": len(entradas), "erros_qt": erros,
            "preferencias_pessoais_alteradas": False,
        }
        (saida / "resultado_nativo.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(resultado, ensure_ascii=False))
    finally:
        janela.close()
        worker.parar()
        ponte.parar()
        dashboard.parar()
        thread.quit()
        if not thread.wait(3000):
            raise RuntimeError("Transporte não encerrou")
        app.processEvents()
        terminal.QSettings = settings_original
        sys.excepthook = original_hook
        preferencias.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
