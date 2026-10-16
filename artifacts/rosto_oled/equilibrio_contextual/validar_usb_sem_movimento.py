"""Diagnóstico com composição/USB reais; sem ativar concessão ou executar gesto."""
import os
import json
from pathlib import Path
import sys
import socket

os.environ["LAYLAY_TERMINAL_2_PORTA"] = "0"
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir(str(Path(__file__).parent / "diagnostico_instancia"))
import laylay
from mente_laylay.cognicao.decisao_corporal import decidir_intencao_corporal
from mente_laylay.cognicao.modelo_corporal import formatar_realidade_corporal
from scripts.tests.test_dev_console_runtime import _linha

corpo, rosto = laylay._corpo_motor_runtime, laylay._rosto_oled_runtime
ponte = laylay._desktop_bridge_runtime
enviados = []
escrever = rosto._escrever
def sem_movimento(texto):
    tipo = texto.split()[0]
    if tipo == "MOTOR":
        raise AssertionError("diagnóstico não pode mover")
    enviados.append(tipo)
    return escrever(texto)
rosto._escrever = sem_movimento
prova = {}
try:
    assert rosto.sincronizar(), rosto.diagnostico()["motivo"]
    diag = rosto.diagnostico()
    ritmo = corpo.experiencias.ritmo_recente(sessao=diag["sessao"], perfil=corpo.companhia.perfil_corporal)
    # Consulta diagnóstica ao decisor com fatos da nova sessão, sem concessão.
    d = decidir_intencao_corporal(corpo.companhia._conversa(), corpo.companhia._atividade(),
        permitir_passeio=True, ritmo_corporal=ritmo, agora=corpo.companhia.monotonic())
    assert d.nome == "atenta" and d.pontuacoes and not d.permite_movimento
    corpo.companhia._registrar_intencao(d)
    corpo.companhia._fase_intencao(corpo.companhia._intencao["id"], "observando", estado="em_observacao")
    modelo = corpo.modelo_para_mente()
    assert "pontuacoes" in formatar_realidade_corporal(modelo)
    assert modelo["autoriza_execucao"] is False
    ponte.iniciar()
    with socket.create_connection(ponte.endereco, timeout=2) as cliente:
        cliente.sendall((json.dumps({"type": "hello", "token": ponte.token}) + "\n").encode())
        retrato = _linha(cliente)["dev_console"]["body"]
        assert retrato["conexao"] == "conectada" and retrato["motivo"] == "equilibrio_observar"
        assert retrato["autoriza_execucao"] is False
    prova = {"composicao": "laylay.py", "usb_frame_confirmado": True,
        "cena": "consulta_diagnostica_sem_concessao_ou_gesto", "decisao": d.nome,
        "pontuacoes": dict(d.pontuacoes), "ritmo_factual": ritmo,
        "motivo_na_mente": modelo["intencao_em_curso"]["motivo"], "body_ponte_real": retrato}
finally:
    ponte.parar()
    rosto.encerrar()
    prova.update(comandos_firmware=enviados, motor_enviado="MOTOR" in enviados, encerrada=True)
    (Path(__file__).parent / "runtime_usb.json").write_text(json.dumps(prova, ensure_ascii=False, indent=2), encoding="utf-8")
