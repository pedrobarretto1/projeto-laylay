"""USB/composição/modelo reais; referências entre turnos, sem enviar MOTOR."""
from pathlib import Path
import json
import sys
import threading
import time

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
DESTINO = RAIZ / "artifacts/rosto_oled/objetivos_entre_turnos"
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir(DESTINO / "instancia_sonda")
import laylay
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.decisao_corporal import IntencaoCorporal
from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal

estado, rosto, corpo = laylay._estado_compartilhado_runtime, laylay._rosto_oled_runtime, laylay._corpo_motor_runtime
abrir = rosto.abrir_serial
trilha, consultas, etapas = [], [], []
fim = threading.Event()


class SerialSemMotor:
    def __init__(self, porta):
        self.serial = abrir(porta)
    def write(self, dados):
        texto = dados.decode().strip()
        assert not texto.startswith("MOTOR "), "sonda não permite movimento"
        trilha.append({"tx": texto})
        return self.serial.write(dados)
    def read(self, tamanho):
        return self.serial.read(tamanho)
    def close(self):
        self.serial.close()


def turno(identidade: str, texto: str) -> None:
    estado.atualizar_campos("mental", turno_atual={"id": identidade, "retrato_id": identidade, "texto": texto},
        retrato_turno_atual={"id": identidade, "texto": texto},
        plano_turno_atual={"id": identidade, "retrato_id": identidade, "texto_usuario": texto,
            "decisao_turno": {"turno_id": identidade}, "fase": "executado", "ts": time.time()})


def consultar(identidade: str, texto: str) -> dict:
    turno(identidade, texto)
    corpo.companhia._registrar_intencao(IntencaoCorporal("atenta", "atividade_pc_em_andamento", 100, 0, 1))
    modelo = corpo.modelo_para_mente(identidade)
    instrucao = formatar_modelo_corporal(modelo)
    resposta = laylay._registro_modelo_llm_runtime.enviar([
        {"role": "system", "content": instrucao},
        {"role": "user", "content": texto}], max_tokens=400, timeout=35,
        modo_rapido=True, _permitir_durante_interacao=True, _contexto_fechado=True, _com_tools=False)
    json.loads(resposta)
    proposta = ContratoPropostaPrincipal(identidade, texto, resposta)
    plano = laylay._composicao_turno_runtime.atualizar_proposta("resposta_planejada", proposta)
    dados = {"turno": identidade, "texto": texto, "resposta": resposta,
             "instrucao_chars": len(instrucao),
             "referencia_observada": modelo["objetivo_para_continuar"],
             "proposta_vinculada": plano.get("intencao_corporal"), "executou_proposta": False}
    consultas.append(dados)
    return plano


rosto.abrir_serial = SerialSemMotor
supervisor = threading.Thread(target=lambda: rosto.executar(deve_parar=fim.is_set, aguardar_fn=fim.wait), daemon=True)
falha = ""
try:
    supervisor.start()
    prazo = time.monotonic() + 10
    while time.monotonic() < prazo and not rosto.diagnostico()["aplicacao_confirmada"]:
        time.sleep(.05)
    assert rosto.diagnostico()["aplicacao_confirmada"], rosto.diagnostico()
    # Só a ativação pela preferência já autorizada; nenhuma execução de gesto.
    assert corpo.companhia.processar()["ok"]
    turno("objetivo-a", "Gosto de conversar com você, Laylay.")
    corpo.companhia._registrar_intencao(IntencaoCorporal("interagir", "conversa_em_andamento", 90, 0, 1, True))
    objetivo = corpo.companhia.diagnostico()["intencao"]["objetivo_id"]
    plano = consultar("objetivo-b", "E eu fico feliz quando você me acompanha nessa conversa. Como você fica?")
    p = plano.get("intencao_corporal") or {}
    assert p.get("objetivo_id") == objetivo, "autoria real não vinculou continuidade do propósito"
    corpo.companhia._registrar_intencao(IntencaoCorporal(p["nome"], "intencao_da_mente", 95, 0, 1,
                                                       proposta_id=p["id"]))
    i = corpo.companhia.diagnostico()["intencao"]
    assert i["objetivo_id"] == objetivo and i["turnos_objetivo"] == 2
    etapas.append({"etapa": "continuidade_autorada", "intencao": i})
    # Assunto independente: nenhum resultado ou continuidade forçada.
    plano = consultar("objetivo-c", "Mudando de assunto: quanto é 17 mais 28?")
    p = plano.get("intencao_corporal") or {}
    assert not p.get("objetivo_id"), "mudança de assunto não deve herdar objetivo"
    etapas.append({"etapa": "mudanca_assunto", "proposta": p})
    assert not any(e["tx"].startswith("MOTOR ") for e in trilha)
except Exception as erro:
    falha = type(erro).__name__ + ": " + str(erro)
finally:
    corpo.companhia.revogar("fim_sonda_sem_motor")
    fim.set()
    supervisor.join(5)
    rosto.encerrar()
    rosto.abrir_serial = abrir
    destino = DESTINO / "receipt_sem_motor.json"
    destino.write_text(json.dumps({"falha": falha, "etapas": etapas, "consultas": consultas,
        "trilha": trilha, "motor_enviado": False, "prova_deslocamento": False,
        "interface_aberta": False, "origem": "USB e autoria principal configurada, diagnostico sem execucao"},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"receipt": str(destino), "falha": falha}, ensure_ascii=False), flush=True)
if falha: raise SystemExit(1)
