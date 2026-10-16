"""Escolha contextual, persistência e carga comandada; percepção não é inventada."""
from mente_laylay.cognicao.decisao_corporal import decidir_intencao_corporal
from scripts.tests.test_companhia_corporal import montar, motores
import pytest


def ritmo(**campos):
    return {"origem": "ritmo_corporal_observado", "motor_ms_60s": 0,
            "gestos_120s": 0, "exploracoes_180s": 0,
            "tempo_sem_gesto_s": 20, "primeira_iniciativa": False, **campos}


def test_observar_descansar_e_explorar_competem_pelo_contexto():
    def decidir(r):
        return decidir_intencao_corporal({}, {}, permitir_passeio=True, ritmo_corporal=r, agora=100)
    assert decidir(ritmo()).nome == "atenta"
    assert decidir(ritmo(motor_ms_60s=23000)).nome == "descansar"
    assert decidir(ritmo(tempo_sem_gesto_s=150)).nome == "explorar"
    repetida = decidir(ritmo(tempo_sem_gesto_s=150, exploracoes_180s=3))
    assert repetida.nome == "atenta"
    assert dict(repetida.pontuacoes)["explorar"] < dict(repetida.pontuacoes)["atenta"]


def test_momento_quieto_tem_inercia_mas_tarefa_no_pc_tem_prioridade():
    r = ritmo(tempo_sem_gesto_s=150, momento_nome="atenta", momento_ate=120)
    d = decidir_intencao_corporal({}, {}, permitir_passeio=True, ritmo_corporal=r, agora=110)
    assert d.nome == "atenta" and not d.permite_movimento
    assert decidir_intencao_corporal({}, {}, permitir_passeio=True, ritmo_corporal=r, agora=121).nome == "explorar"
    d = decidir_intencao_corporal({}, {"origem": "atividade_operacional_observada", "ativos": 1},
        permitir_passeio=True, ritmo_corporal=r, agora=110)
    assert d.motivo == "atividade_pc_em_andamento" and not d.permite_movimento


def test_orcamento_modera_iniciativa_da_mente_sem_conceder_ou_confirmar_efeito():
    d = decidir_intencao_corporal({}, {}, permitir_passeio=True,
        ritmo_corporal=ritmo(motor_ms_60s=23000), agora=100,
        proposta_corporal={"nome": "explorar", "id": "p1"})
    assert d.nome == "descansar" and not d.permite_movimento and not d.proposta_id
    assert d.motivo == "orcamento_de_movimento_recente"
    assert not decidir_intencao_corporal({}, {}, permitir_passeio=False,
        ritmo_corporal=ritmo(tempo_sem_gesto_s=300), agora=100).permite_movimento


def test_ritmo_le_historico_canonico_sem_promover_restauracao_ou_outro_dispositivo():
    estado, _, rosto, corpo, _, _ = montar()
    sessao = rosto.diagnostico()["sessao"]
    fonte = {"id": "e1", "origem": "executor_corpo", "confirmado": True, "sessao": sessao,
        "perfil": "bancada", "ts": 990, "familia": "explorar:0",
        "movimentos": [[100, 100, 1200]], "resultado": "pwm_e_parada_confirmados"}
    estado.atualizar_campos("mental", historico_corporal=[fonte,
        {**fonte, "recuperada_da_memoria": True}, {**fonte, "sessao": "outro"},
        {**fonte, "confirmado": False}, {**fonte, "ts": 1100}])
    antes = estado.obter_copia("mental", "historico_corporal", [])
    r = corpo.experiencias.ritmo_recente(sessao=sessao, perfil="bancada", agora=1000)
    assert r["motor_ms_60s"] == 1200 and r["exploracoes_180s"] == 1 and r["gestos_120s"] == 1
    assert r["autoriza_execucao"] is False and r["prova_deslocamento"] is False
    assert estado.obter_copia("mental", "historico_corporal", []) == antes
    assert corpo.experiencias.ritmo_recente(sessao=sessao, perfil="bancada", agora=1300)["motor_ms_60s"] == 0


def test_escolha_quieta_vai_a_mente_e_mantem_identidade_entre_leituras():
    estado, esp, rosto, corpo, _, clock = montar(automatico=True, passeio=True)
    assert corpo.companhia.processar()["ok"]
    clock[0] += 9
    corpo.companhia._concessao["gestos"] = 1
    corpo.companhia._concessao["ultimo_fim_gesto"] = clock[0] - 20
    for _ in range(4):
        assert corpo.companhia.processar().get("em_observacao")
    i = dict(estado.mental["intencao_corporal"])
    assert i["nome"] == "atenta" and i["fase"] == "observando"
    assert i["pontuacoes"] and i["momento_ate_monotonic"] > clock[0]
    clock[0] += 10
    assert corpo.companhia.processar().get("em_observacao")
    assert estado.mental["intencao_corporal"]["id"] == i["id"]
    assert not motores(esp)


@pytest.mark.parametrize("campo,valor", [("motor_ms_60s", "muito"),
    ("tempo_sem_gesto_s", float("nan")), ("momento_ate", float("inf")), ("origem", "texto_llm")])
def test_ritmo_invalido_nao_vira_candidato_motor(campo, valor):
    d = decidir_intencao_corporal({}, {}, permitir_passeio=True, ritmo_corporal=ritmo(**{campo: valor}),
        proposta_corporal={"nome": "explorar", "id": "p1"}, agora=100)
    assert d.nome == "atenta" and not d.permite_movimento and not d.proposta_id


def test_tempo_comandado_parcial_confirmado_conta_no_orcamento_sem_confirmar_gesto():
    _, _, rosto, corpo, _, _ = montar()
    corpo.experiencias.clock = lambda: 1000
    e = corpo.experiencias.iniciar(nome="explorar", origem_intencao="mente_causal", perfil="bancada")
    corpo.experiencias.registrar(e, {"ok": False}, [
        {"ok": False, "aplicacao_pwm_confirmada": True, "parada_confirmada": True, "duracao_ms": 1000}])
    r = corpo.experiencias.ritmo_recente(sessao=rosto.diagnostico()["sessao"], perfil="bancada")
    assert r["motor_ms_60s"] == 1000 and r["gestos_120s"] == 0


def test_pontuacoes_e_motivo_alcancam_autoria_pela_composicao_real(tmp_path):
    import subprocess, sys
    codigo = f'''
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir({str(tmp_path / 'instancia')!r})
import laylay
from mente_laylay.cognicao.modelo_corporal import formatar_realidade_corporal, formatar_modelo_corporal
corpo, estado = laylay._corpo_motor_runtime, laylay._estado_compartilhado_runtime
estado.substituir("conversacional", {{}})
estado.atualizar_campos("mental", atividade_operacional={{}}, plano_turno_atual={{}})
corpo.companhia.prioridade_interacao_getter = lambda: False
corpo.transporte.diagnostico = lambda: {{"sessao": "hardware-simulado", "transporte": "serial",
    "aplicacao_confirmada": True, "confirmado": [0, 1, 0],
    "motor": {{"disponivel": True, "duracao_maxima_ms": 5000}}}}
def proibir(*a, **k): raise AssertionError("observação não deve enviar MOTOR")
corpo.transporte.mover_corpo = proibir
assert corpo.companhia._ativar_sessao(passeio=True)["ok"]
agora = corpo.companhia.monotonic()
# Cena diagnóstica controlada no owner; não é observação de movimento físico.
corpo.companhia._concessao.update(proximo_passeio=agora-1, gestos=1, ultimo_fim_gesto=agora-20)
assert corpo.companhia.processar()["em_observacao"]
modelo = corpo.modelo_para_mente()
assert modelo["intencao_em_curso"]["pontuacoes"]["atenta"] > modelo["intencao_em_curso"]["pontuacoes"]["explorar"]
texto = formatar_realidade_corporal(modelo)
assert "equilibrio_observar" in texto and "pontuacoes" in texto
assert len(formatar_modelo_corporal(modelo)) <= 3800
assert modelo["autoriza_execucao"] is False
assert laylay._dev_console_runtime.snapshot()["body"]["fase"] == "observando"
'''
    r = subprocess.run([sys.executable, "-"], input=codigo, text=True, capture_output=True, timeout=40)
    assert r.returncode == 0, r.stdout + r.stderr
