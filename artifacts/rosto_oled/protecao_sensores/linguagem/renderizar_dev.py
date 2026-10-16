import os,sys
from pathlib import Path
SAIDA=Path(__file__).resolve().parent
sys.path.insert(0,str(SAIDA.parents[3]))
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from cliente.terminal_laylay_2 import carregar_fontes_interface
from cliente.terminal_2.desenvolvedor import PaginaDesenvolvedor
from scripts.tests.test_dev_corpo import dados_corpo
from mente_laylay.integracao.dev_console_runtime import DevConsoleRuntime
app=QApplication([]); app.setFont(QFont(carregar_fontes_interface(),10))
p=PaginaDesenvolvedor(); p.definir_conectada(True)
d=dados_corpo(); d['transporte']['sensores']={'recente':True,
    'leituras':{'frente':{'estado':'VALIDA','mm':80},'borda':{'estado':'VALIDA','mm':100}},
    'protecao':{'risco':'OBSTACULO','fase':'ESPERA_BUSCA','reacao_expressiva':'irritada',
                'tentativa_busca':4,'vigia_ativa':True}}
dev=DevConsoleRuntime(); dev.configurar_corpo_getter(lambda:d)
p.aplicar_corpo(dev.snapshot()['body']); p.botoes_categoria['CORPO'].click()
p.resize(1600,900); p.show(); app.processEvents()
assert 'autorizados na placa' in p.corpo_detalhes.text()
assert p.grab().save(str(SAIDA/'dev.png')); p.close()
