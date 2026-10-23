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


def validar_desktop(janela, js, aguardar, foto, *, janela_unica=False) -> dict:
    """Prova Windows da apresentação local, sem mente nem executor externo."""
    import ctypes
    from ctypes import wintypes
    from PySide6.QtCore import QPoint, QRect, Qt
    from PySide6.QtGui import QCursor
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QLineEdit, QVBoxLayout, QWidget

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.WindowFromPoint.argtypes = [wintypes.POINT]
    user32.WindowFromPoint.restype = wintypes.HWND
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND
    bancada = QWidget()
    bancada.setWindowTitle("Prova local da Laylay — foco e transparência")
    bancada.setStyleSheet("background:#263241;color:#e8e4f4;font-size:18px")
    layout = QVBoxLayout(bancada)
    campo = QLineEdit("Este campo conserva o foco ao aproximar o mouse da Laylay.")
    layout.addWidget(campo)
    disponivel = janela.screen().availableGeometry()
    QCursor.setPos(disponivel.left() + 25, disponivel.bottom() - 40)
    bancada.setGeometry(QRect(disponivel.center().x() - 430, disponivel.top() + 20, 860, 400))
    identidade = (janela.web, janela.pagina_web, janela.canal, janela.controlador, janela.worker)
    trajetoria = []
    try:
        janela.apresentar("desktop")
        aguardar(lambda: js("LaylayInterface.state.mode==='desktop'"))
        bancada.show()
        bancada.raise_()
        bancada.activateWindow()
        campo.setFocus()
        QTest.qWait(100)
        foco_antes = int(user32.GetForegroundWindow() or 0)
        # O Windows pode conservar o app que o usuário está usando, mesmo
        # após activateWindow. O contrato do hover é preservar esse foco real.
        assert foco_antes != int(janela.winId()), "A bancada precisa começar com a ilha passiva"
        janela.raise_()
        janela.recolher_desktop()
        QTest.qWait(320)
        foto("desktop-compacto")
        js("window.desktopProva={raiz:document.querySelector('.desktop-island'),avatar:document.querySelector('.desktop-island .avatar')}")
        QCursor.setPos(janela.mapToGlobal(QPoint(janela.width() // 2, janela.height() // 2)))
        QTest.qWait(450)
        assert janela.estado_desktop == "compact", "Hover abriu a ilha sem clique"
        assert int(user32.GetForegroundWindow() or 0) == foco_antes, "Hover retirou o foco do aplicativo em uso"
        assert js("!document.hasFocus()"), "O renderer passivo ganhou foco sem clique"
        receptor = janela.web.focusProxy() or janela.web
        QTest.mouseClick(receptor, Qt.LeftButton, Qt.NoModifier, QPoint(janela.width() // 2, janela.height() // 2))
        aguardar(lambda: janela.estado_desktop == "expanded")
        for _ in range(24):
            trajetoria.append([janela.x(), janela.y(), janela.width(), janela.height()])
            QTest.qWait(16)
        assert len({tuple(p) for p in trajetoria}) >= 3, "A expansão não apresentou estados intermediários"
        assert js("desktopProva.raiz===document.querySelector('.desktop-island')&&desktopProva.avatar===document.querySelector('.desktop-island .avatar')")
        foto("desktop-expandido-clique")
        canto = QPoint(1, janela.height() - 2)
        assert not janela.mask().contains(canto)
        ponto = janela.mapToGlobal(canto)
        alvo = user32.WindowFromPoint(wintypes.POINT(ponto.x(), ponto.y()))
        raiz_alvo = int(user32.GetAncestor(alvo, 2) or 0)
        assert raiz_alvo != int(janela.winId()), "Canto transparente intercepta a janela por trás"
        aguardar(lambda: js("document.querySelector('.desktop-portrait .avatar').getAnimations({subtree:true}).some(a=>a.playState==='running')"))
        janela.expandir_desktop(fixar=True)
        retangulo = json.loads(js("JSON.stringify((()=>{const r=document.getElementById('composer-input').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})())"))
        receptor = janela.web.focusProxy() or janela.web
        QTest.mouseClick(receptor, Qt.LeftButton, Qt.NoModifier, QPoint(int(retangulo['x']), int(retangulo['y'])))
        aguardar(lambda: int(user32.GetForegroundWindow() or 0) == int(janela.winId()))
        aguardar(lambda: js("document.activeElement?.id==='composer-input'"))
        QTest.keyClicks(receptor, "Rascunho de prova, sem envio")
        aguardar(lambda: js("LaylayInterface.state.draft==='Rascunho de prova, sem envio'"))
        foto("desktop-expandido-fixado")
        janela.recolher_desktop()
        aguardar(lambda: janela.estado_desktop == "compact")
        QTest.qWait(400)
        janela.expandir_desktop(fixar=True)
        aguardar(lambda: js("document.getElementById('composer-input').value==='Rascunho de prova, sem envio'"))
        assert identidade == (janela.web, janela.pagina_web, janela.canal, janela.controlador, janela.worker)
        js("document.getElementById('composer-input').value='';document.getElementById('composer-input').dispatchEvent(new Event('input',{bubbles:true}))")
        janela.definir_preferencia("reduzir_movimento", True)
        janela.recolher_desktop()
        janela.expandir_desktop(fixar=True)
        assert janela._animacao_desktop.state() == janela._animacao_desktop.State.Stopped
        foto("desktop-movimento-reduzido")
        janela.definir_preferencia("reduzir_movimento", False)
        navegacao = []
        if janela_unica:
            hwnd_inicial = int(janela.winId())
            flags_iniciais = janela.windowFlags()
            topo = janela.y()
            centro = janela.geometry().center().x()
            for pagina in ("home", "chat", "lamp", "music", "streaming", "memory", "system", "dev", "settings"):
                seletor = json.dumps('.desktop-island [data-page="' + pagina + '"]')
                js("document.querySelector(" + seletor + ").scrollIntoView({block:'nearest',inline:'nearest'})")
                posicao = json.loads(js("JSON.stringify((()=>{const r=document.querySelector(" + seletor + ").getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})())"))
                anterior = QRect(janela.geometry())
                QTest.mouseClick(receptor, Qt.LeftButton, Qt.NoModifier, QPoint(int(posicao['x']), int(posicao['y'])))
                aguardar(lambda: js("LaylayInterface.state.page===" + json.dumps(pagina)))
                aguardar(lambda: janela.desktop_pagina == pagina)
                geometria_aba = []
                for _ in range(22):
                    atual = janela.geometry()
                    assert int(janela.winId()) == hwnd_inicial
                    assert janela.windowFlags() == flags_iniciais
                    assert atual.top() == topo and abs(atual.center().x() - centro) <= 1
                    geometria_aba.append([atual.x(), atual.y(), atual.width(), atual.height()])
                    QTest.qWait(16)
                assert janela.modo_apresentacao == "desktop"
                assert js("desktopProva.raiz===document.querySelector('.desktop-island')")
                if anterior.size() != janela.size():
                    assert len({tuple(g) for g in geometria_aba}) >= 2, "A aba mudou de tamanho sem animação"
                assert js("!!document.querySelector('.desktop-island #page-content')")
                foto("desktop-aba-" + pagina)
                navegacao.append({"pagina": pagina, "mesmo_hwnd": True, "mesmas_flags": True,
                                   "topo_e_centro_preservados": True, "geometrias": geometria_aba})
            janela.recolher_desktop()
            QTest.qWait(320)
            assert int(janela.winId()) == hwnd_inicial
            janela.expandir_desktop(fixar=True)
            aguardar(lambda: js("LaylayInterface.state.page==='settings'&&!!document.querySelector('.desktop-island #page-content')"))
            janela.ponte_web.gesto_desktop("resumo")
            aguardar(lambda: janela.desktop_pagina is None)
            QTest.qWait(320)
            foto("desktop-volta-resumo")
        janela.apresentar("full")
        return {"hover_preserva_foco": True, "hover_nao_expande": True, "expansao_por_clique": True, "canto_transparente_nao_intercepta": True,
                "janela_alvo_canto_distinta": raiz_alvo != int(janela.winId()),
                "identidade_superficie_preservada": True, "rascunho_preservado": True,
                "clique_explicito_permite_foco_e_teclado": True,
                "abas_na_mesma_janela": navegacao,
                "animacao_geometrias": trajetoria, "mente_iniciada": False}
    finally:
        bancada.close()
        if janela.modo_apresentacao == "full":
            janela.raise_()
            janela.activateWindow()
            janela.web.setFocus()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--movimento", action="store_true", help="Valida animação contínua e identidade DOM com telemetria real")
    parser.add_argument("--mascote", action="store_true", help="Inspeciona expressões de demonstração transportadas e olhar com mouse nativo")
    parser.add_argument("--desktop", action="store_true", help="Valida ilha expansível com foco e região de input reais do Windows")
    parser.add_argument("--janela-unica", action="store_true", help="Clica nas nove abas dentro da ilha e verifica HWND, âncora e animação")
    parser.add_argument("--ilha-suave", action="store_true", help="Prova player integrado com captura real de janela própria e inatividade real de20s")
    parser.add_argument("--clique-windows", action="store_true", help="Aguarda clique Computer Use e marcador retomar-clique-windows antes das provas de foco")
    parser.add_argument("--demonstracao", action="store_true", help="Abre somente a ilha local por15min, sem rodar a sequência de provas nem iniciar a mente")
    parser.add_argument("--saida", type=Path, help="Diretório separado para preservar evidências históricas")
    parser.add_argument("--inspecionar", action="store_true", help="Mantém esta composição isolada aberta para inspeção; criar arquivo encerrar no diretório de saída para concluir")
    argumentos = parser.parse_args()
    os.environ["QT_QPA_PLATFORM"] = "windows"
    if argumentos.movimento:
        os.environ.pop("LAYLAY_REDUZIR_MOVIMENTO", None)
    else:
        os.environ["LAYLAY_REDUZIR_MOVIMENTO"] = "1"
    import psutil
    from PySide6.QtCore import QPoint, QSettings, QThread
    from PySide6.QtGui import QFont
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    import cliente.terminal_laylay_2 as terminal
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1
    from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
    from mente_laylay.integracao.desktop_bridge import DesktopBridgeRuntime

    saida = argumentos.saida or Path(__file__).parent
    saida.mkdir(parents=True, exist_ok=True)
    preferencias = tempfile.TemporaryDirectory(prefix="laylay-web-v1-")
    original_settings = terminal.QSettings
    terminal.QSettings = lambda *_: QSettings(str(Path(preferencias.name) / "ui.ini"), QSettings.IniFormat)
    app = QApplication([])
    app.setFont(QFont(terminal.carregar_fontes_interface(), 10))
    estado = {"activity": "idle", "activity_label": "Validação da interface", "interaction_mode": "chat", "voice_available": False}
    entradas, mensagens, olhares = [], [], []
    prova_desktop = None
    prova_ilha_suave = None
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
        if argumentos.demonstracao:
            janela.setWindowTitle('Laylay — demonstração desktop local, sem mente')
            janela.apresentar('desktop')
            janela.iniciar_apresentacao()
            thread.start()
            aguardar(lambda: janela.ponte_web._pronta and janela.controlador._conectado)
            aguardar(lambda: janela._entrada_exibida)
            print('DEMONSTRACAO_DESKTOP_PRONTA_SEM_MENTE', flush=True)
            limite = time.monotonic()+900
            while not janela._fechada and not (saida/'encerrar').exists() and time.monotonic()<limite:
                QTest.qWait(100)
            return 0
        janela.resize(1440, 1000)
        janela.show()
        thread.start()
        aguardar(pronto)
        aguardar(lambda: janela.controlador._conectado and janela.controlador._dashboard_recebido)
        aguardar(lambda: js("!!LaylayInterface.state.connected"))
        aguardar(lambda: js("LaylayInterface.state.conversations.active_id==='11111111111111111111111111111111'"))
        aguardar(lambda: js("!!LaylayInterface.state.dashboard.system?.cpu_percent?.observed_at"), 30)
        if argumentos.clique_windows:
            janela.setWindowTitle('Laylay — validação integrada local (sem mente)')
            marcador_clique = saida / 'retomar-clique-windows'
            print('AGUARDANDO_CLIQUE_WINDOWS', flush=True)
            aguardar(marcador_clique.exists, 90)
            marcador_clique.unlink()
        foto("web-inicio")
        if argumentos.desktop:
            assert argumentos.movimento, "A prova desktop exige --movimento"
            prova_desktop = validar_desktop(janela, js, aguardar, foto, janela_unica=argumentos.janela_unica)
            js("LaylayInterface.goPage('home')")
            aguardar(lambda: js("!!document.querySelector('.presence .avatar')"))
        if argumentos.movimento:
            js("window.__continuidade={avatar:document.querySelector('.presence .avatar'),play:document.querySelector('.music-play')};__continuidade.animation=__continuidade.avatar.getAnimations()[0];__continuidade.tempo=__continuidade.animation?.currentTime;")
            for indice in range(4):
                QTest.qWait(500)
                foto(f"web-inicio-movimento-{indice}")
            assert js("__continuidade.avatar===document.querySelector('.presence .avatar')&&__continuidade.play===document.querySelector('.music-play')"), "Uma atualização recriou mascote ou play do Início"
            assert js("__continuidade.animation===__continuidade.avatar.getAnimations()[0]&&__continuidade.animation.currentTime>__continuidade.tempo"), "Animação reiniciada em uma atualização periódica"
        if argumentos.mascote:
            assert argumentos.movimento, "A prova do olhar exige --movimento"
            janela.activateWindow()
            janela.web.setFocus()
            aguardar(lambda: js("document.hasFocus()"))
            receptor = janela.web.focusProxy() or janela.web
            for nome, x, y, eixo, sinal in (
                ("esquerda", 5, 5, "x", -1),
                ("direita", receptor.width() - 5, 5, "x", 1),
                ("cima", receptor.width() // 2, 5, "y", -1),
                ("baixo", receptor.width() // 2, receptor.height() - 5, "y", 1),
            ):
                QTest.mouseMove(receptor, QPoint(x, y))
                aguardar(lambda: js(f"parseFloat(document.querySelector('.presence .avatar').style.getPropertyValue('--look-{eixo}'))*{sinal}>0.2"))
                foto("web-olhar-" + nome)
                olhares.append({"direcao": nome, "face_translate": js("getComputedStyle(document.querySelector('.presence .face')).translate")})
            for emocao, expressao in (("alegre", "feliz"), ("triste", "triste"), ("irritada", "brava"), ("surpresa", "surpresa")):
                estado.update(emotion=emocao, emotion_level=3)
                aguardar(lambda: js("document.querySelector('.presence .avatar').dataset.expression===" + json.dumps(expressao)))
                foto("web-expressao-" + expressao)
            estado.update(emotion="calma", emotion_level=1)
            aguardar(lambda: js("document.querySelector('.presence .avatar').dataset.expression==='neutra'"))
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
        if argumentos.ilha_suave:
            from validar_ilha_suave import validar_ilha_suave
            prova_ilha_suave = validar_ilha_suave(janela, js, aguardar, foto, evidencias=saida)
        assert entradas == [texto]
        resultado = {
            "plataforma": app.platformName(), "renderer": "QtWebEngine",
            "frontend_local": janela.web.url().isLocalFile(),
            "ponte_autenticada": janela.controlador._conectado,
            "dashboard_real_psutil": True, "mente_iniciada": False,
            "efeitos_externos": False, "mensagens_texto_recebidas": len(entradas),
            "continuidade_dom_e_animacao": argumentos.movimento,
            "mouse_nativo": olhares,
            "expressoes_de_demonstracao_transportadas": argumentos.mascote,
            "desktop_integrado": prova_desktop,
            "ilha_suave": prova_ilha_suave,
            "capturas": capturas,
        }
        (saida / "resultado_web.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(resultado, ensure_ascii=False))
        if argumentos.inspecionar:
            # Somente esta composição de validação: não inicia mente nem
            # conecta executores externos. Encerramento explícito e limitado.
            if argumentos.desktop:
                janela.setWindowTitle("Laylay — demonstração desktop local, sem mente")
                janela.apresentar("desktop")
                if argumentos.janela_unica:
                    js("(()=>{const c=document.getElementById('composer-input');if(c){c.value='';c.dispatchEvent(new Event('input',{bubbles:true}))}})()")
                    janela.recolher_desktop()
                else:
                    janela.expandir_desktop(fixar=True)
            limite_inspecao = time.monotonic() + 900
            while not janela._fechada and not (saida / "encerrar").exists() and time.monotonic() < limite_inspecao:
                QTest.qWait(100)
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
