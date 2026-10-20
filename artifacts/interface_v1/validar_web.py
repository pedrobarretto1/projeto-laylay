"""Prova visual do renderer oficial com WebEngine e transporte autenticado.

Somente telemetria local de leitura. Sem mente, microfone, música, IoT,
credenciais ou preferências pessoais. Não é launcher da assistente.
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
    parser.add_argument("--movimento", action="store_true", help="Valida animação contínua e identidade DOM com telemetria real")
    argumentos = parser.parse_args()
    os.environ["QT_QPA_PLATFORM"] = "windows"
    if argumentos.movimento:
        os.environ.pop("LAYLAY_REDUZIR_MOVIMENTO", None)
    else:
        os.environ["LAYLAY_REDUZIR_MOVIMENTO"] = "1"
    import psutil
    from PySide6.QtCore import QSettings, QThread
    from PySide6.QtGui import QFont
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    import cliente.terminal_laylay_2 as terminal
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1
    from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
    from mente_laylay.integracao.desktop_bridge import DesktopBridgeRuntime

    saida = Path(__file__).parent
    preferencias = tempfile.TemporaryDirectory(prefix="laylay-web-v1-")
    original_settings = terminal.QSettings
    terminal.QSettings = lambda *_: QSettings(str(Path(preferencias.name) / "ui.ini"), QSettings.IniFormat)
    app = QApplication([])
    app.setFont(QFont(terminal.carregar_fontes_interface(), 10))
    estado = {"activity": "idle", "activity_label": "Validação da interface", "interaction_mode": "chat", "voice_available": False}
    entradas, mensagens = [], []
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
        conversas_getter=lambda: [{"id": "11111111111111111111111111111111", "titulo": "Verificação da interface", "status": "ativa"}],
        conversa_ativa_getter=lambda: "11111111111111111111111111111111",
        configuracao_getter=lambda: {},
        dashboard_interval_s=0.3, log=lambda _: None,
    )
    ponte.iniciar()
    worker = terminal.PonteWorker(*ponte.endereco, ponte.token, session_id=ponte.session_id)
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.executar)
    worker.terminou.connect(thread.quit)
    worker.mensagem.connect(mensagens.append)
    janela = JanelaInterfaceWebV1(worker, RAIZ, session_id=ponte.session_id)
    capturas = []

    def aguardar(condicao, segundos=10):
        limite = time.monotonic() + segundos
        while not condicao() and time.monotonic() < limite:
            QTest.qWait(30)
        assert condicao(), "A composição WebEngine/ponte não atingiu o estado esperado"

    def js(codigo):
        retorno = []
        janela.web.page().runJavaScript(codigo, retorno.append)
        aguardar(lambda: bool(retorno), 5)
        return retorno[0]

    def pronto():
        return js("!!(window.LaylayInterface && document.querySelector('.nav'))") is True

    def foto(nome):
        # JS pronto não significa que o compositor Chromium já entregou o
        # frame à superfície nativa. Aguardar duas pinturas antes do grab.
        js("window.__capturaPronta=false;requestAnimationFrame(()=>requestAnimationFrame(()=>{window.__capturaPronta=true}));")
        aguardar(lambda: js("window.__capturaPronta===true"))
        QTest.qWait(650)
        arquivo = saida / (nome + ".png")
        assert janela.grab().save(str(arquivo))
        capturas.append({"arquivo": arquivo.name, "largura": janela.width(), "altura": janela.height()})

    try:
        janela.resize(1440, 1000)
        janela.show()
        thread.start()
        aguardar(pronto)
        aguardar(lambda: janela.controlador._conectado and janela.controlador._dashboard_recebido)
        aguardar(lambda: js("!!LaylayInterface.state.connected"))
        aguardar(lambda: js("LaylayInterface.state.conversations.active_id==='11111111111111111111111111111111'"))
        aguardar(lambda: js("!!LaylayInterface.state.dashboard.system?.cpu_percent?.observed_at"), 30)
        foto("web-inicio")
        if argumentos.movimento:
            js("window.__continuidade={avatar:document.querySelector('.presence .avatar'),play:document.querySelector('.music-play')};__continuidade.animation=__continuidade.avatar.getAnimations()[0];__continuidade.tempo=__continuidade.animation?.currentTime;")
            for indice in range(4):
                QTest.qWait(500)
                foto(f"web-inicio-movimento-{indice}")
            assert js("__continuidade.avatar===document.querySelector('.presence .avatar')&&__continuidade.play===document.querySelector('.music-play')"), "Uma atualização recriou mascote ou play do Início"
            assert js("__continuidade.animation===__continuidade.avatar.getAnimations()[0]&&__continuidade.animation.currentTime>__continuidade.tempo"), "Animação reiniciada em uma atualização periódica"
        for pagina in ("music", "system", "settings", "memory", "lamp", "dev", "streaming"):
            js("LaylayInterface.goPage(" + json.dumps(pagina) + ")")
            aguardar(lambda: js("LaylayInterface.state.page===" + json.dumps(pagina)))
            foto("web-" + pagina)
        js("LaylayInterface.goPage('chat')")
        texto = "Verificação local do renderer oficial."
        js("LaylayInterface.request('texto', {text:" + json.dumps(texto) + "});")
        aguardar(lambda: entradas == [texto])
        aguardar(lambda: any(m.get("type") == "input_ack" and m.get("accepted") for m in mensagens))
        js("LaylayInterface.goMode('island')")
        aguardar(lambda: janela.height() < 200)
        assert ponte.publicar_fala_final("Mensagem entregue pela ponte real. A mente não está conectada nesta verificação.")
        aguardar(lambda: not janela.controlador._envios)
        aguardar(lambda: js("LaylayInterface.state.messages.some(m=>m.role==='assistant'&&m.conversation_id===LaylayInterface.state.conversations.active_id)"))
        foto("web-ilha")
        js("LaylayInterface.goMode('quick')")
        aguardar(lambda: 200 < janela.height() <= 800)
        foto("web-painel")
        js("LaylayInterface.goMode('full')")
        aguardar(lambda: janela.width() > 800)
        foto("web-conversa")
        for largura, altura in ((768, 800), (390, 844)):
            janela.resize(largura, altura)
            foto(f"web-conversa-{largura}")
        assert entradas == [texto]
        resultado = {
            "plataforma": app.platformName(), "renderer": "QtWebEngine",
            "frontend_local": janela.web.url().isLocalFile(),
            "ponte_autenticada": janela.controlador._conectado,
            "dashboard_real_psutil": True, "mente_iniciada": False,
            "efeitos_externos": False, "mensagens_texto_recebidas": len(entradas),
            "continuidade_dom_e_animacao": argumentos.movimento,
            "capturas": capturas,
        }
        (saida / "resultado_web.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(resultado, ensure_ascii=False))
    finally:
        janela.close()
        worker.parar()
        ponte.parar()
        dashboard.parar()
        thread.quit()
        assert thread.wait(3000)
        app.processEvents()
        terminal.QSettings = original_settings
        preferencias.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
