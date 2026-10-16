"""Prova da composição instalada → USB → ponte → DEV, sem movimento."""
import json
import os
from pathlib import Path
import socket
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["LAYLAY_TERMINAL_2_PORTA"] = "0"
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from mente_laylay.integracao import instancia_unica

adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir(str(Path(__file__).parent / "instancia_diagnostico"))
import laylay
from mente_laylay.cognicao.decisao_corporal import IntencaoCorporal
from scripts.tests.test_dev_console_runtime import _linha, _ate_tipo
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from cliente.terminal_laylay_2 import carregar_fontes_interface
from cliente.terminal_2.desenvolvedor import PaginaDesenvolvedor

rosto = laylay._rosto_oled_runtime
ponte = laylay._desktop_bridge_runtime
tipos = []
escrever = rosto._escrever

def escrever_observado(texto):
    tipo = texto.split()[0]
    if tipo == "MOTOR":
        raise AssertionError("Diagnóstico DEV não autoriza movimento")
    tipos.append(tipo)
    return escrever(texto)

rosto._escrever = escrever_observado
prova = {}
try:
    assert rosto.sincronizar(), rosto.diagnostico()["motivo"]
    ponte.iniciar()
    with socket.create_connection(ponte.endereco, timeout=2) as cliente:
        cliente.sendall((json.dumps({"type": "hello", "token": ponte.token}) + "\n").encode())
        inicial = _linha(cliente)
        body = inicial["dev_console"]["body"]
        assert body["conexao"] == "conectada" and body["porta"] == "COM4", body
        # Registro diagnóstico no owner, sem processar concessões ou gestos.
        laylay._corpo_motor_runtime.companhia._registrar_intencao(
            IntencaoCorporal("atenta", "diagnostico_DEV_sem_movimento", 100, 0, 1))
        while True:
            lote = _ate_tipo(cliente, "dev_events")
            if lote["body"]["intencao"] == "atenta":
                break
        cliente.sendall((json.dumps({"type": "dev_query", "id": "prova-corpo", "command": "inspect corpo"}) + "\n").encode())
        consulta = _ate_tipo(cliente, "dev_query_result")
        assert consulta["result"]["ok"]
        app = QApplication([])
        app.setFont(QFont(carregar_fontes_interface(), 10))
        pagina = PaginaDesenvolvedor()
        pagina.definir_conectada(True)
        pagina.aplicar_corpo(lote["body"])
        pagina.botoes_categoria["CORPO"].click()
        for evento in lote["events"]:
            pagina.registrar_evento("Corpo", evento["message"], categoria=evento["category"])
        pagina.resize(1280, 850)
        pagina.show()
        app.processEvents()
        assert "COM4" in pagina.corpo_resumo.text() and "atenta" in pagina.corpo_resumo.text()
        pagina.grab().save(str(Path(__file__).parent / "dev_corpo_runtime_usb.png"))
        pagina.close()
        prova = {"composicao": "laylay.py", "usb_frame_confirmado": True,
                 "body_pela_ponte_autenticada": lote["body"], "consulta_readonly": consulta["result"]["ok"],
                 "intencao": "diagnostico_no_owner_sem_executar", "janela_normal_aberta": False}
finally:
    ponte.parar()
    rosto.encerrar()
    prova.update(comandos_firmware=tipos, movimento_enviado="MOTOR" in tipos,
                 encerrada=True)
    (Path(__file__).parent / "runtime_usb.json").write_text(json.dumps(prova, ensure_ascii=False, indent=2), encoding="utf-8")
print("USB + composição + ponte autenticada + página DEV: confirmados; nenhum MOTOR enviado; encerrada.")
