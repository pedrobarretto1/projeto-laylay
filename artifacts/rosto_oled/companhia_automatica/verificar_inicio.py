"""Consulta a composição e a USB reais sem abrir interface nem mover motores."""
import json
import os
import sys
import threading
import time
from pathlib import Path

raiz = Path(__file__).resolve().parents[3]
os.chdir(raiz)
sys.path.insert(0, str(raiz))
import laylay as root

rosto, corpo = root._rosto_oled_runtime, root._corpo_motor_runtime
comandos = []
original = rosto._escrever

def escrever(linha):
    comandos.append(linha.split()[0])
    return original(linha)

rosto._escrever = escrever
resultado = {"interface_aberta": False, "observacao_fisica_humana": False}
passear = "--passeio" in sys.argv
parar = threading.Event()
supervisor = None
try:
    assert root._configuracao_aplicacao_runtime.companhia_bancada_ao_iniciar()
    assert corpo.companhia.diagnostico()["ativacao_automatica_ao_iniciar"]
    assert rosto.diagnostico()["transporte"] == "serial"
    assert root._composicao_servicos_runtime.catalogo_threads()["Laylay-Companhia-Corporal"].func.__self__ is corpo.companhia
    assert rosto.sincronizar(), rosto.diagnostico()["motivo"]
    if passear:
        assert root._configuracao_aplicacao_runtime.passeio_bancada_ao_iniciar()
        supervisor = threading.Thread(target=lambda: rosto.executar(
            deve_parar=parar.is_set, aguardar_fn=parar.wait), daemon=True)
        supervisor.start()
    resultado["ativacao"] = corpo.companhia.processar()
    assert resultado["ativacao"].get("modo_ativado") is True
    resultado["companhia"] = corpo.companhia.diagnostico()
    assert resultado["companhia"]["ativa"]
    assert resultado["companhia"]["passeio_ativado"] is root._configuracao_aplicacao_runtime.passeio_bancada_ao_iniciar()
    corpo.companhia.processar()
    assert "MOTOR" not in comandos
    if passear:
        inicio = time.monotonic()
        while time.monotonic() - inicio < 15:
            retorno = corpo.companhia.processar()
            if corpo.companhia.diagnostico()["passeios_emitidos"]:
                resultado["passeio"] = retorno
                resultado["espera_inicial_s"] = time.monotonic() - inicio
                break
            time.sleep(.2)
        assert resultado.get("passeio", {}).get("ok") is True, resultado
        assert comandos.count("MOTOR") == 2
    resultado["parada"] = corpo.executar("CORPO_PARAR", {})
    assert resultado["parada"]["ok"]
    corpo.companhia.processar()
    resultado["sem_rearme_apos_parada"] = not corpo.companhia.diagnostico()["ativa"]
    assert resultado["sem_rearme_apos_parada"]
    assert comandos.count("MOTOR") == (2 if passear else 0)
    resultado["ok"] = True
finally:
    corpo.companhia.revogar("fim_da_verificacao_de_inicio")
    if "parada" not in resultado:
        resultado["parada_final"] = rosto.parar_corpo()
    parar.set()
    if supervisor is not None:
        supervisor.join(3)
    rosto.encerrar()
    resultado["comandos"] = comandos
    Path(__file__).with_name("receipt_passeio.json" if passear else "receipt_inicio.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"inicio_usb_confirmado": resultado.get("ok", False),
                  "motores_acionados": "MOTOR" in comandos, "interface_aberta": False}))
