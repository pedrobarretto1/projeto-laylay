import os,sys,json
from pathlib import Path
SAIDA=Path(__file__).resolve().parent
sys.path.insert(0,str(SAIDA.parents[2]));os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from cliente.terminal_laylay_2 import carregar_fontes_interface
from cliente.terminal_2.desenvolvedor import PaginaDesenvolvedor
from mente_laylay.integracao.dev_console_runtime import DevConsoleRuntime
from scripts.tests.test_dev_corpo import dados_corpo
dados=dados_corpo();dados['transporte']['saude']={'suportado':True,'recente':True,
    'motivo_boot':'usb','reinicios_observados':1,'perdas_sessao':2,'motivo_perda_sessao':'NACK_OLED'}
dados['corpo']['companhia'].update(ativa=False,recuperacao_pendente=True,motivo='aguardando_recuperacao_usb')
app=QApplication([]);app.setFont(QFont(carregar_fontes_interface(),10))
p=PaginaDesenvolvedor();p.definir_conectada(True)
dev=DevConsoleRuntime();dev.configurar_corpo_getter(lambda:dados)
p.aplicar_corpo(dev.snapshot()['body']);p.botoes_categoria['CORPO'].click()
p.resize(1600,900);p.show();app.processEvents()
assert 'NACK_OLED' in p.corpo_detalhes.text() and 'aguardando_recuperacao_usb' in p.corpo_detalhes.text()
assert p.grab().save(str(SAIDA/'dev.png'));p.close()
