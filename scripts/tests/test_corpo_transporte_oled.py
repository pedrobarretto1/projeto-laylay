"""A porta física é dublê; sessão, sincronização e executor serial são reais."""
from threading import Event, Thread
import time

import pytest

from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime


class EspCorpo:
    def __init__(self, *, motor=True, glitch=True, mack=True, stopped=True, gack=True):
        self.motor, self.glitch = motor, glitch
        self.mack, self.stopped, self.gack = mack, stopped, gack
        self.enviados = []
        self.rx = bytearray()
        self.fechado = False
        self.aplicou_motor = Event()

    def write(self, dados):
        linha = dados.decode().strip()
        self.enviados.append(linha)
        p = linha.split()
        resposta = ""
        if p[0] == "HELLO":
            resposta = f"READY 1 {p[2]} SSD1306 128 64"
        elif p[0] == "FACE":
            resposta = "ACK " + " ".join(p[1:-1])
        elif p[0] == "CAPS":
            resposta = f"CAPS 1 {p[2]} HACK1"
        elif p[0] == "GCAPS":
            resposta = f"GCAPS 1 {p[2]} GLITCH1" if self.glitch else "ERROR 1 PACOTE_INVALIDO"
        elif p[0] == "MCAPS":
            resposta = f"MCAPS 1 {p[2]} MOTOR{int(self.motor)}"
        elif p[0] == "SCAPS":
            resposta = "ERROR 1 PACOTE_INVALIDO"
        elif p[0] in {"LCAPS", "ECAPS", "RCAPS"}:
            resposta = "ERROR 1 PACOTE_INVALIDO"
        elif p[0] == "ACTIVITY":
            resposta = "AACK " + " ".join(p[1:-1])
        elif p[0] == "GLITCH" and self.gack:
            resposta = "GACK " + " ".join(p[1:])
        elif p[0] == "MOTOR":
            self.aplicou_motor.set()
            if self.mack:
                resposta = "MACK " + " ".join(p[1:])
        elif p[0] == "STOP" and self.stopped:
            resposta = "SACK " + " ".join(p[1:]) if len(p) == 4 else "STOPPED 1"
        if resposta:
            self.rx.extend((resposta + "\n").encode())
        return len(dados)

    def read(self, tamanho):
        dados = bytes(self.rx[:tamanho])
        del self.rx[:tamanho]
        if not dados:
            time.sleep(.001)
        return dados

    def close(self):
        self.fechado = True


def criar(esp=None, **kwargs):
    esp = esp or EspCorpo()
    return RostoOledRuntime(estado_getter=lambda: {}, porta="TESTE", abrir_serial=lambda _: esp, **kwargs), esp


def test_negociacao_motor_nao_aciona_e_receipt_face_nao_afirma_rotacao():
    runtime, esp = criar()
    assert runtime.sincronizar()
    assert runtime.diagnostico()["motor"]["disponivel"], "primeira fronteira: suporte motor não negociado"
    assert not any(p.startswith("MOTOR ") for p in esp.enviados)
    assert not runtime.diagnostico()["motor"]["prova_rotacao"]


def test_pulso_exige_mack_e_stopped_do_mesmo_owner_sem_repetir_motor():
    runtime, esp = criar()
    receipt = runtime.mover_corpo(255, 255, 50)
    assert receipt["ok"] and receipt["aplicacao_pwm_confirmada"] and receipt["parada_confirmada"]
    assert len([p for p in esp.enviados if p.startswith("MOTOR ")]) == 1
    assert esp.enviados[-1].startswith("STOP 1 ")
    assert not receipt["prova_rotacao"] and not receipt["prova_parada_fisica"]


@pytest.mark.parametrize("esp, motivo", [
    (EspCorpo(motor=False), "firmware_sem_motor"),
    (EspCorpo(mack=False), "sem_confirmacao_pwm"),
    (EspCorpo(stopped=False), "sem_confirmacao_parada"),
])
def test_falha_parcial_nao_confirma_operacao_e_motor_nunca_e_retentado(esp, motivo):
    runtime, _ = criar(esp)
    receipt = runtime.mover_corpo(255, 0, 50)
    assert not receipt["ok"] and receipt["motivo"] == motivo
    motores = [p for p in esp.enviados if p.startswith("MOTOR ")]
    assert len(motores) == (0 if not esp.motor else 1)
    if esp.motor:
        assert any(p.startswith("STOP 1 ") for p in esp.enviados)


@pytest.mark.parametrize("parametros", [
    (True, 0, 100), (256, 0, 100), (-256, 0, 100), (0, 0, 100),
    (1, 1, 501), (1, 1, 49), (1, 1, 100.0), ("255", 0, 100),
])
def test_parametros_invalidos_falham_antes_de_abrir_usb(parametros):
    runtime, esp = criar()
    assert not runtime.mover_corpo(*parametros)["ok"]
    assert not esp.enviados


def test_stop_interrompe_espera_e_novo_movimento_concorrente_nao_entra_em_fila():
    runtime, esp = criar()
    retornos = []
    worker = Thread(target=lambda: retornos.append(runtime.mover_corpo(255, 255, 500)))
    worker.start()
    assert esp.aplicou_motor.wait(2)
    assert not runtime.mover_corpo(255, 255, 50)["ok"]
    assert runtime.parar_corpo()["parada_confirmada"]
    worker.join(2)
    assert not worker.is_alive()
    assert len([p for p in esp.enviados if p.startswith("MOTOR ")]) == 1
    assert retornos[0]["parada_confirmada"]
    assert not retornos[0]["ok"] and retornos[0]["cancelado"]


def test_glitch_usa_falha_recente_uma_vez_e_nao_transmite_texto():
    estado = {"origem": "atividade_operacional_observada", "falha_id": 1,
              "falha_monotonic": time.monotonic(), "ativos": 0}
    runtime, esp = criar(atividade_getter=lambda: estado)
    assert runtime.sincronizar()
    assert any(p.startswith("GLITCH ") for p in esp.enviados), "primeira fronteira: falha não chega ao OLED"
    assert runtime.diagnostico()["glitch"]["aplicacao_confirmada"]
    assert runtime.sincronizar()
    assert len([p for p in esp.enviados if p.startswith("GLITCH ")]) == 1
    assert not any(p.startswith("MOTOR ") for p in esp.enviados)


@pytest.mark.parametrize("estado", [
    {"falha_id": 1, "falha_monotonic": time.monotonic()},
    {"origem": "atividade_operacional_observada", "falha_id": 1, "falha_monotonic": time.monotonic() - 5},
    {"origem": "plano_turno", "falha_id": 1, "falha_monotonic": time.monotonic()},
])
def test_plano_falha_antiga_ou_sem_owner_nao_disparam_glitch(estado):
    runtime, esp = criar(atividade_getter=lambda: estado)
    assert runtime.sincronizar()
    assert not any(p.startswith("GLITCH ") for p in esp.enviados)


def test_glitch_sem_gack_preserva_face_e_nao_reenvia_evento_na_reconexao():
    estado = {"origem": "atividade_operacional_observada", "falha_id": 5,
              "falha_monotonic": time.monotonic(), "ativos": 0}
    esp = EspCorpo(gack=False)
    runtime, _ = criar(esp, atividade_getter=lambda: estado)
    assert runtime.sincronizar()
    assert not runtime.diagnostico()["glitch"]["aplicacao_confirmada"]
    assert runtime.diagnostico()["aplicacao_confirmada"]
    runtime.encerrar()
    assert runtime.sincronizar()
    assert len([p for p in esp.enviados if p.startswith("GLITCH ")]) == 1


@pytest.mark.parametrize("prefixo", ["MACK", "SACK"])
def test_receipt_de_outra_sequencia_nao_confirma_acionamento_ou_parada(prefixo):
    class EspReceiptAntigo(EspCorpo):
        def write(self, dados):
            retorno = super().write(dados)
            if self.rx.startswith(prefixo.encode()):
                campos = self.rx.decode().split()
                campos[3] = "999"
                self.rx = bytearray((" ".join(campos) + "\n").encode())
            return retorno
    runtime, esp = criar(EspReceiptAntigo())
    resultado = runtime.mover_corpo(255, 0, 50)
    assert not resultado["ok"]
    assert len([p for p in esp.enviados if p.startswith("MOTOR ")]) == 1


def test_publicacao_diagnostica_nao_apaga_receipt_da_parada_real():
    runtime, esp = criar()
    assert runtime.sincronizar()
    def quebrada(_):
        raise ValueError("painel indisponível")
    runtime.publicar_diagnostico = quebrada
    assert runtime.parar_corpo()["ok"]
    assert not esp.fechado


def test_stop_nao_aguarda_timeout_de_mack_ausente():
    runtime, esp = criar(EspCorpo(mack=False))
    resultados = []
    worker = Thread(target=lambda: resultados.append(runtime.mover_corpo(255, 0, 500)))
    worker.start()
    assert esp.aplicou_motor.wait(2)
    inicio = time.monotonic()
    assert runtime.parar_corpo()["ok"]
    assert time.monotonic() - inicio < .3, "STOP ficou preso na espera de MACK"
    worker.join(2)
    assert not worker.is_alive()
    assert resultados[0]["cancelado"] and not resultados[0]["ok"]


def test_renovar_sessao_no_meio_do_pulso_nao_junta_mack_antigo_e_sack_novo():
    runtime, esp = criar()
    resultados = []
    worker = Thread(target=lambda: resultados.append(runtime.mover_corpo(255, 0, 500)))
    worker.start()
    assert esp.aplicou_motor.wait(2)
    with runtime._lock:
        runtime._ultimo_ack = float("-inf")
    assert runtime.sincronizar()
    worker.join(2)
    assert not worker.is_alive()
    assert not resultados[0]["ok"] and resultados[0]["motivo"] == "sessao_alterada"
    assert len([p for p in esp.enviados if p.startswith("MOTOR ")]) == 1


def test_painel_diagnostico_quebrado_nao_muda_efeito_e_receipt_motor():
    runtime, esp = criar()
    assert runtime.sincronizar()
    def quebrada(_):
        raise ValueError("painel indisponível")
    runtime.publicar_diagnostico = quebrada
    assert runtime.mover_corpo(255, 0, 50)["ok"]
    assert not esp.fechado
