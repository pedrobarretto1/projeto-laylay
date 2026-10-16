"""Não movimentar é uma decisão corporal observável, sem receipt inventado."""
import pytest
from mente_laylay.cognicao.decisao_corporal import decidir_intencao_corporal
from scripts.tests.test_companhia_corporal import montar, motores, emocao


def test_reposo_espontaneo_e_intencao_sem_movimento():
    d = decidir_intencao_corporal({}, {}, permitir_passeio=True,
        passeio_em_repouso=True, agora=110)
    assert d.nome == "descansar" and not d.permite_movimento
    assert d.motivo == "repouso_espontaneo"


@pytest.mark.parametrize("perfil", ["bancada", "rodas_suspensas"])
def test_passeio_concedido_pode_descansar_sem_perder_concessao(monkeypatch, perfil):
    estado, esp, rosto, corpo, _, clock = montar(automatico=True, passeio=True)
    # Perfil longo negociado pelo firmware é necessário apenas para esse perfil.
    if perfil == "rodas_suspensas":
        corpo.companhia.perfil_corporal = perfil
        rosto._limite_motor_ms = 5000
    assert corpo.companhia.processar()["ok"]
    clock[0] += 8.1
    monkeypatch.setattr(corpo.companhia, "_aguardar_gesto", lambda ms, validar: validar())
    if perfil == "rodas_suspensas":
        from mente_laylay.autonomia.companhia_corporal import GestoCorporal
        monkeypatch.setattr(corpo.companhia, "_gesto_suspenso",
            lambda *a, **k: GestoCorporal("exploracao_teste", 0, ((100, 100, 50),)))
    assert corpo.companhia.processar()["ok"]
    antes = len(motores(esp))
    clock[0] += 20
    for _ in range(12):
        assert corpo.companhia.processar().get("em_repouso") is True
    assert len(motores(esp)) == antes
    i = estado.mental["intencao_corporal"]
    assert i["nome"] == "descansar" and i["fase"] == "repousando"
    assert i["autoriza_execucao"] is False
    assert corpo.companhia.diagnostico()["passeio_ativado"]
    clock[0] += 91
    assert corpo.companhia.processar()["ok"]
    assert len(motores(esp)) > antes


def test_repouso_nao_apaga_mudanca_emocional_ou_pedido_direto(monkeypatch):
    estado, esp, rosto, corpo, _, clock = montar(automatico=True, passeio=True)
    assert corpo.companhia.processar()["ok"]
    corpo.companhia._concessao["proximo_passeio"] = clock[0] + 90
    monkeypatch.setattr(corpo.companhia, "_aguardar_gesto", lambda ms, validar: validar())
    assert corpo.companhia.processar().get("em_repouso")
    emocao(estado, rosto, "envergonhada")
    assert corpo.companhia.processar()["ok"]
    assert motores(esp)
    # Movimento manual segue o executor e receipt canônicos; repouso não é bloqueio.
    assert corpo.executar("CORPO_MOVER", {"direcao": "frente", "pwm": 100, "duracao_ms": 50})["ok"]


def test_repouso_sem_concessao_nao_arma_motor():
    _, esp, _, corpo, _, _ = montar()
    for _ in range(5):
        assert corpo.companhia.processar()["motivo"] == "companhia_inativa"
    assert not motores(esp)


def test_repouso_chega_a_mente_e_dev_na_composicao_instalada(tmp_path):
    import subprocess, sys
    codigo = f'''
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir({str(tmp_path / 'instancia')!r})
import laylay
corpo = laylay._corpo_motor_runtime
estado = laylay._estado_compartilhado_runtime
estado.substituir("conversacional", {{}})
estado.atualizar_campos("mental", atividade_operacional={{}}, plano_turno_atual={{}})
corpo.companhia.prioridade_interacao_getter = lambda: False
# Apenas a fronteira de hardware é simulada; owners/composição são instalados.
corpo.transporte.diagnostico = lambda: {{"sessao": "diagnostico-simulado", "transporte": "serial",
    "aplicacao_confirmada": True, "confirmado": [0, 1, 0],
    "motor": {{"disponivel": True, "duracao_maxima_ms": 5000}}}}
def movimento_proibido(*a, **k): raise AssertionError("Repouso enviou MOTOR")
corpo.transporte.mover_corpo = movimento_proibido
assert corpo.companhia._ativar_sessao(passeio=True)["ok"]
assert corpo.companhia.processar()["em_repouso"]
modelo = corpo.modelo_para_mente()
assert modelo["intencao_em_curso"]["nome"] == "descansar"
assert modelo["intencao_em_curso"]["fase"] == "repousando"
assert modelo["autoriza_execucao"] is False
body = laylay._dev_console_runtime.snapshot()["body"]
assert body["intencao"] == "descansar" and body["fase"] == "repousando"
assert body["deslocamento"] == "nao_medido"
'''
    r = subprocess.run([sys.executable, "-"], input=codigo, text=True, capture_output=True, timeout=40)
    assert r.returncode == 0, r.stdout + r.stderr
