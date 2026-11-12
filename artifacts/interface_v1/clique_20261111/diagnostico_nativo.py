"""Janela oficial isolada para verificar clique nativo, sem conexão à mente."""
from pathlib import Path
import json
import sys
import tempfile

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication
from cliente import terminal_laylay_2 as terminal
from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1

app = QApplication([])
perfil = tempfile.TemporaryDirectory(prefix='laylay-clique-')
preferencias = QSettings(str(Path(perfil.name) / 'ui.ini'), QSettings.IniFormat)
terminal.QSettings = lambda *_: preferencias
worker = terminal.PonteWorker('127.0.0.1', 1, 'isolado')
entradas = []
worker.enfileirar = lambda msg: entradas.append(msg) or True
janela = JanelaInterfaceWebV1(worker, RAIZ)
janela.apresentar('desktop')
janela.iniciar_apresentacao()
anterior = None
falhas = []

def observar():
    global anterior
    estado = {
        'estado': janela.estado_desktop, 'fase': janela._desktop_fase,
        'recolhida': janela._desktop_recolhida,
        'geometria': janela.geometry().getRect(), 'entradas': entradas,
        'pronta': janela.ponte_web._pronta,
        'entrada_pendente': janela._entrada_pendente,
        'opacidade': janela.windowOpacity(),
    }
    if estado != anterior:
        print(json.dumps(estado), flush=True)
        anterior = estado

timer = QTimer()
timer.timeout.connect(observar)
timer.start(100)
def clicar():
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    if janela._entrada_pendente or janela.windowOpacity() != 1:
        falhas.append('Entrada oficial não confirmou visibilidade antes do clique')
    QTest.mouseClick(janela.web.focusProxy(), Qt.LeftButton, pos=janela.web.rect().center())

def verificar_expansao():
    if janela.estado_desktop != 'expanded' or janela._desktop_fase != 'idle' or janela.height() <= 36:
        falhas.append('Clique não concluiu expansão nativa')
    if entradas:
        falhas.append('Gesto local emitiu entradas')
    janela.grab().save(str(Path(__file__).with_name('expandida.png')))
    print(json.dumps({'resultado': 'RED' if falhas else 'GREEN', 'falhas': falhas}), flush=True)
    janela.close()

if '--automatico' in sys.argv:
    QTimer.singleShot(1800, clicar)
    QTimer.singleShot(3400, verificar_expansao)
QTimer.singleShot(180_000, janela.close)
janela.encerrada.connect(app.quit)
app.exec()
perfil.cleanup()
sys.exit(bool(falhas))
