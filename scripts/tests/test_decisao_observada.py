"""A fonte da decisão não é resultado, autorização ou causa reconstruída."""
from dataclasses import FrozenInstanceError

import pytest

from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
from mente_laylay.memoria_mental.decisao_observada import DecisaoObservada


def fonte(**alteracoes):
    campos = dict(id="decisao-1", owner="owner_companhia_corporal", nome="expressar",
        motivo="mudanca_emocional_causal", turno_id="turno-1", sessao="sessao-1",
        intencao_id="proposta-1", objetivo_id="objetivo-1", registrada_em=100.0,
        evidencias=SnapshotComandoIA({"referencia_causal": ["evento-1", 99.0, "rosto:1"]}),
        criterios=(("descansar", 10), ("expressar", 30)))
    return DecisaoObservada(**(campos | alteracoes))


@pytest.mark.parametrize("owner,nome,motivo", [
    ("owner_companhia_corporal", "expressar", "mudanca_emocional_causal"),
    ("owner_iniciativa", "observar", "permissao_apenas_observar"),
])
def test_fonte_reutilizavel_preserva_decisao_sem_conceder_efeito(owner, nome, motivo):
    decisao = fonte(owner=owner, nome=nome, motivo=motivo)
    retrato = decisao.como_dict()
    assert (retrato["owner"], retrato["nome"], retrato["motivo"]) == (owner, nome, motivo)
    assert retrato["autoriza_execucao"] is False
    assert retrato["confirma_efeito"] is False
    assert retrato["criterios"] == {"descansar": 10, "expressar": 30}
    retrato["evidencias"]["referencia_causal"][0] = "outro-evento"
    assert decisao.como_dict()["evidencias"]["referencia_causal"][0] == "evento-1"
    with pytest.raises(FrozenInstanceError):
        decisao.motivo = "causa_posterior"


@pytest.mark.parametrize("alteracoes", [
    {"id": ""}, {"owner": ""}, {"motivo": ""}, {"nome": ""},
    {"registrada_em": float("nan")}, {"registrada_em": True},
    {"evidencias": {"referencia_causal": "nao_tipado"}},
    {"criterios": (("a", True),)}, {"criterios": (("a", 1), ("a", 2))},
])
def test_rejeita_fonte_sem_identidade_ou_dados_invalidos(alteracoes):
    with pytest.raises((ValueError, TypeError)):
        fonte(**alteracoes)


def experiencia():
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
    from mente_laylay.memoria_mental.experiencia_corporal_runtime import ExperienciaCorporalRuntime
    estado = criar_estado_compartilhado_runtime()
    estado.atualizar_campos("mental", turno_atual={"id": "turno-1"})
    runtime = ExperienciaCorporalRuntime(estado=estado,
        diagnostico_getter=lambda: {"sessao": "sessao-1"}, clock=lambda: 101.0)
    return estado, runtime


@pytest.mark.parametrize("alteracoes", [
    {"turno_id": "outro"}, {"sessao": "outra"}, {"intencao_id": "outra"},
    {"registrada_em": 102.0},
])
def test_fonte_estrangeira_ou_posterior_nao_entra_na_ocorrencia(alteracoes):
    _, runtime = experiencia()
    with pytest.raises(ValueError):
        runtime.iniciar(nome="gesto", origem_intencao="mente_causal", perfil="bancada",
            intencao_id="proposta-1", decisao_origem=fonte(**alteracoes))


def test_projecao_nao_pode_reentrar_como_captura_tipada():
    _, runtime = experiencia()
    with pytest.raises(ValueError):
        runtime.iniciar(nome="gesto", origem_intencao="mente_causal", perfil="bancada",
            intencao_id="proposta-1", decisao_origem=fonte().como_dict())


@pytest.mark.parametrize("ok,status", [(True, "plano_confirmado"), (False, "sem_confirmacao_pwm"),
                                          (False, "cancelado")])
def test_resultado_tardio_nao_reescreve_decisao_nem_vira_autorizacao(ok, status):
    estado, runtime = experiencia()
    inicio = runtime.iniciar(nome="gesto", origem_intencao="llm_principal", perfil="bancada",
        intencao_id="proposta-1", decisao_origem=fonte())
    estado.atualizar_campos("mental", turno_atual={"id": "turno-2"},
        intencao_corporal={"id": "outra", "motivo": "atividade_pc_em_andamento"})
    receipt = {"ok": ok, "aplicacao_pwm_confirmada": ok, "parada_confirmada": ok}
    resultado = runtime.registrar(inicio, {"ok": ok, "status": status}, [receipt])
    assert resultado["decisao_origem"] == fonte().como_dict()
    assert resultado["motivo"] == status
    assert resultado["confirmado"] is ok
    assert resultado["turno_id"] == "turno-1" and not resultado["pertence_ao_turno_atual"]
    assert resultado["autoriza_execucao"] is False and resultado["prova_deslocamento"] is False
    inicio["decisao_origem"]["motivo"] = "alteracao_apos_entrega"
    assert resultado["decisao_origem"]["motivo"] == "mudanca_emocional_causal"
    assert runtime.retrato()["historico_recente"][0]["decisao_origem"] == fonte().como_dict()


def test_registro_sem_fonte_nao_empresta_motivo_do_estado_vivo():
    estado, runtime = experiencia()
    estado.atualizar_campos("mental", intencao_corporal={"motivo": "mudanca_emocional_causal"})
    inicio = runtime.iniciar(nome="manual", origem_intencao="pedido_usuario", perfil="bancada")
    resultado = runtime.registrar(inicio, {"ok": False}, [])
    assert "decisao_origem" not in inicio and "decisao_origem" not in resultado


def test_proposta_llm_preserva_fonte_sem_inventar_rationale(monkeypatch):
    from scripts.tests.test_corpo_na_mente import preparar_mente
    estado, _, rosto, corpo, _, _ = preparar_mente(monkeypatch)
    try:
        proposta = estado.obter_copia("mental", "plano_turno_atual", {})["intencao_corporal"]
        assert corpo.companhia.processar()["ok"]
        e = estado.obter_copia("mental", "experiencia_corporal", {})
        assert e["decisao_origem"]["motivo"] == "intencao_da_mente"
        assert e["decisao_origem"]["intencao_id"] == proposta["id"]
        assert e["decisao_origem"]["id"] != proposta["id"]
        assert e["decisao_origem"]["autoriza_execucao"] is False
    finally:
        rosto.encerrar()


def test_fonte_sobrevive_na_memoria_sem_restaurar_concessao(tmp_path, monkeypatch):
    from scripts.tests.test_companhia_corporal import montar, ativar, emocao
    from scripts.tests.test_experiencia_corporal_continua import conectar_aprendizado
    from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
    estado, esp, rosto, corpo, _, _ = montar()
    try:
        motor = conectar_aprendizado(corpo, tmp_path)
        assert ativar(corpo)["ok"]
        emocao(estado, rosto, "alegre")
        monkeypatch.setattr(corpo.companhia, "_aguardar_gesto", lambda ms, validar: validar())
        assert corpo.companhia.processar()["ok"]
        e = estado.obter_copia("mental", "experiencia_corporal", {})
        novo_estado = criar_estado_compartilhado_runtime()
        novo = CorpoMotorRuntime(transporte=rosto, estado=novo_estado)
        antes = list(esp.enviados)
        novo.experiencias.conectar_aprendizado(motor)
        modelo = novo.modelo_para_mente("nova-sessao")
        assert modelo["ultima_experiencia"]["decisao_origem"] == e["decisao_origem"]
        assert modelo["ultima_experiencia"]["recuperada_da_memoria"] is True
        assert not novo.companhia.diagnostico()["ativa"] and esp.enviados == antes
    finally:
        rosto.encerrar()
