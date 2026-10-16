"""Renderiza a página real em tamanhos diferentes, com dados diagnósticos."""
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["LAYLAY_REDUZIR_MOVIMENTO"] = "1"
from pathlib import Path
import sys
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from cliente.terminal_laylay_2 import carregar_fontes_interface
from cliente.terminal_2.desenvolvedor import PaginaDesenvolvedor
from mente_laylay.integracao.dev_console_runtime import DevConsoleRuntime
from scripts.tests.test_dev_corpo import dados_corpo

app = QApplication([])
app.setFont(QFont(carregar_fontes_interface(), 10))
pagina = PaginaDesenvolvedor()
dados = dados_corpo("antecipando")
dev = DevConsoleRuntime()
dev.configurar_corpo_getter(lambda: dados)
pagina.definir_conectada(True)
for fase in ("aguardando", "antecipando", "gesticulando", "acomodando"):
    dados["corpo"]["companhia"]["intencao"]["fase"] = fase
    snapshot = dev.snapshot()
    pagina.registrar_evento("Corpo", snapshot["events"][-1]["message"], categoria="AUTONOMY")
pagina.aplicar_corpo(snapshot["body"])
pagina.registrar_evento("Ponte DEV", "Diagnóstico disponível", categoria="SYSTEM")
pagina.show()
for largura in (1600, 900):
    pagina.resize(largura, 850)
    app.processEvents()
    assert pagina.corpo_compacto.isHidden() and pagina.card_corpo.isHidden()
    assert "AUTONOMIA:CORPO" not in pagina.console.toPlainText()
    pagina.grab().save(str(Path(__file__).parent / f"dev_geral_{largura}.png"))
pagina.botoes_categoria["CORPO"].click()
for largura in (1600, 1280, 900):
    pagina.resize(largura, 850)
    app.processEvents()
    pagina.grab().save(str(Path(__file__).parent / f"dev_corpo_{largura}.png"))
pagina.definir_conectada(False)
app.processEvents()
pagina.grab().save(str(Path(__file__).parent / "dev_corpo_desconectado.png"))
pagina.close()
print("Frames geral/CORPO renderizados; nenhum runtime motor iniciado.")
