"""Todo caminho corporal devolve experiência factual à mesma mente."""
from copy import deepcopy
import pytest


def test_pedido_manual_devolve_experiencia_apos_pwm_e_parada():
    from scripts.tests.test_companhia_corporal import montar
    estado, _, _, corpo, _, _ = montar()
    estado.atualizar_campos("mental", turno_atual={"id": "manual-1"})
    receipt = corpo.executar("CORPO_MOVER", {"direcao": "frente"})
    assert receipt["ok"] and receipt["aplicacao_pwm_confirmada"] and receipt["parada_confirmada"]
    experiencia = estado.obter_copia("mental", "experiencia_corporal", {})
    assert experiencia.get("origem") == "executor_corpo", "primeira fronteira: movimento manual não devolve experiência"
    assert experiencia["turno_id"] == "manual-1" and experiencia["confirmado"]
    assert experiencia["origem_intencao"] == "pedido_usuario"
    assert experiencia["prova_deslocamento"] is False and experiencia["autoriza_execucao"] is False
    assert estado.mental["historico_corporal"][-1]["id"] == experiencia["id"]


def test_gesto_espontaneo_devolve_experiencia_sem_proposta_da_llm(monkeypatch):
    from scripts.tests.test_companhia_corporal import montar, ativar, emocao
    estado, _, rosto, corpo, quadro, _ = montar()
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "alegre")
    monkeypatch.setattr(corpo.companhia, "_aguardar_gesto", lambda ms, validar: validar())
    receipt = corpo.companhia.processar()
    assert receipt["ok"]
    experiencia = estado.obter_copia("mental", "experiencia_corporal", {})
    assert experiencia.get("origem") == "executor_corpo", "primeira fronteira: gesto causal ficou fora da experiência"
    assert experiencia["origem_intencao"] == "mente_causal"
    assert experiencia["confirmado"] and experiencia["nome"]
    assert quadro.snapshot()["planos_recentes"][-1]["estado"] == "confirmado"
    assert corpo.modelo_para_mente()["ultima_experiencia"]["id"] == experiencia["id"]


def conectar_aprendizado(corpo, tmp_path):
    from memoria_sqlite import MemoriaSQLite
    from mente_laylay.memoria_mental.motor_aprendizado import MotorAprendizadoRuntime
    motor = MotorAprendizadoRuntime(memoria_sqlite=MemoriaSQLite(str(tmp_path / "corpo.sqlite")),
        contexto_getter=lambda: {}, log=lambda _: None)
    corpo.experiencias.conectar_aprendizado(motor)
    return motor


def test_confirmacao_eletrica_aprende_uma_vez_e_recuperacao_nao_restaura_concessao(tmp_path):
    from scripts.tests.test_companhia_corporal import montar
    from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
    estado, esp, rosto, corpo, _, _ = montar()
    motor = conectar_aprendizado(corpo, tmp_path)
    r = corpo.executar("CORPO_MOVER", {"direcao": "frente"})
    e = estado.obter_copia("mental", "experiencia_corporal", {})
    corpo.experiencias.registrar(e, r, [r])
    chave = "corpo_execucao:bancada:mover_frente:0"
    eventos = motor.memoria.listar_eventos_aprendizado(chave)
    assert len(eventos) == 1 and eventos[0]["origem"] == "executor_corpo"
    assert eventos[0]["contexto"]["experiencia"]["prova_deslocamento"] is False
    novo_estado = criar_estado_compartilhado_runtime()
    novo = CorpoMotorRuntime(transporte=rosto, estado=novo_estado)
    novo.experiencias.conectar_aprendizado(motor)
    assert novo_estado.mental["experiencia_corporal"]["recuperada_da_memoria"]
    assert not novo.companhia.diagnostico()["ativa"]
    antes = list(esp.enviados)
    novo.modelo_para_mente("nova_sessao")
    assert esp.enviados == antes, "consultar experiência não aciona corpo"


@pytest.mark.parametrize("texto,tipo", [
    ("gostei desse movimento", "aceitacao"), ("adorei essa dancinha", "aceitacao"),
    ("não gostei desse gesto", "recusa"),
    ("esse movimento ficou muito forte", "correcao"), ("repete esse gesto", "repeticao"),
    ("gostei", ""), ("não gostei da música", ""), ("sim", ""),
    ("ele disse que gostei desse movimento", ""), ("gostei desse movimento?", ""),
    ("traduza 'gostei desse movimento'", ""),
])
def test_feedback_no_interpretador_compartilhado_exige_referencia_corporal(texto, tipo):
    from mente_laylay.cognicao.interpretador_continuidade import qualificar_feedback_corporal
    assert qualificar_feedback_corporal(texto).get("tipo", "") == tipo


def test_feedback_liga_ocorrencia_sem_preferencia_duravel_imediata(tmp_path):
    from scripts.tests.test_companhia_corporal import montar
    estado, _, _, corpo, _, _ = montar()
    motor = conectar_aprendizado(corpo, tmp_path)
    corpo.executar("CORPO_MOVER", {"direcao": "frente"})
    e = estado.mental["experiencia_corporal"]
    assert corpo.experiencias.observar_feedback("gostei desse movimento", turno_id="feedback-1", referencia_id=e["id"])
    corpo.experiencias.observar_feedback("gostei desse movimento", turno_id="feedback-1", referencia_id=e["id"])
    chave = "corpo_preferencia:bancada:mover_frente:0"
    eventos = motor.memoria.listar_eventos_aprendizado(chave)
    assert len(eventos) == 1 and not eventos[0]["confirmado_usuario"]
    assert eventos[0]["contexto"]["experiencia_id"] == e["id"]
    assert not motor.avaliar_hipotese(chave)["aplicavel"]
    assert corpo.experiencias.selecionar_variante("mover_frente", "bancada", 2) == 2
    assert not corpo.experiencias.observar_feedback("gostei", turno_id="feedback-2", referencia_id=e["id"])


@pytest.mark.parametrize("causa", ["expiracao", "sessao", "restaurada", "sem_alvo"])
def test_feedback_antigo_ou_sem_vinculo_nao_ensina(tmp_path, monkeypatch, causa):
    from scripts.tests.test_companhia_corporal import montar
    estado, _, rosto, corpo, _, _ = montar()
    motor = conectar_aprendizado(corpo, tmp_path)
    corpo.executar("CORPO_MOVER", {"direcao": "frente"})
    e = estado.obter_copia("mental", "experiencia_corporal", {})
    if causa == "expiracao": monkeypatch.setattr(corpo.experiencias, "clock", lambda: e["ts"] + 61)
    if causa == "sessao": e["sessao"] = "outra"
    if causa == "restaurada": e["recuperada_da_memoria"] = True
    estado.atualizar_campos("mental", historico_corporal=[e])
    assert not corpo.experiencias.observar_feedback("gostei desse movimento", turno_id="f", referencia_id="" if causa == "sem_alvo" else e["id"])
    assert not motor.memoria.obter_hipotese_aprendizado("corpo_preferencia:bancada:mover_frente:0")


def test_condicao_atual_no_prompt_nao_empresta_acesso_do_historico():
    from scripts.tests.test_companhia_corporal import montar
    from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal
    estado, _, rosto, corpo, _, _ = montar()
    corpo.executar("CORPO_MOVER", {"direcao": "frente"})
    modelo = corpo.modelo_para_mente()
    assert modelo["condicao"]["estado"] == "pronta"
    assert "historico_recente" in formatar_modelo_corporal(modelo)
    rosto.encerrar()
    modelo = corpo.modelo_para_mente()
    assert modelo["condicao"]["estado"] == "desconectada"
    prompt = formatar_modelo_corporal(modelo)
    assert "não alegue acesso atual" in prompt and "observações de sessões anteriores" in prompt
    assert not modelo["autoriza_execucao"] and not corpo.companhia.diagnostico()["ativa"]


def test_experiencia_reprojetada_preserva_turno_original_e_movimento_desconhecido():
    from scripts.tests.test_companhia_corporal import montar
    from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal
    estado, _, _, corpo, _, _ = montar()
    estado.atualizar_campos("mental", turno_atual={"id": "origem"})
    corpo.executar("CORPO_MOVER", {"direcao": "frente"})
    estado.atualizar_campos("mental", turno_atual={"id": "novo"})
    modelo = corpo.modelo_para_mente("novo")
    assert modelo["turno_id"] == "novo" and modelo["ultima_experiencia"]["turno_id"] == "origem"
    assert not modelo["ultima_experiencia"]["pertence_ao_turno_atual"]
    assert modelo["percepcao_fisica"]["deslocamento"] == "nao_medido"
    assert "nunca ausência de movimento" in formatar_modelo_corporal(modelo)


def test_excecao_do_transporte_devolve_experiencia_sem_confirmacao(monkeypatch, tmp_path):
    from scripts.tests.test_companhia_corporal import montar
    estado, _, rosto, corpo, _, _ = montar()
    motor = conectar_aprendizado(corpo, tmp_path)
    def falhar(*args, **kwargs):
        raise OSError("porta perdida")
    monkeypatch.setattr(rosto, "mover_corpo", falhar)
    with pytest.raises(OSError):
        corpo.executar("CORPO_MOVER", {"direcao": "frente"})
    e = estado.mental["experiencia_corporal"]
    assert not e["confirmado"] and not e["prova_deslocamento"]
    assert motor.memoria.obter_hipotese_aprendizado("corpo_execucao:bancada:mover_frente:0")["evidencias_negativas"] == 1


def test_composicao_real_liga_receipt_aprendizado_feedback_e_catalogo(monkeypatch, tmp_path):
    from scripts.tests.test_corpo_motor import _root_instalado
    from scripts.tests.test_corpo_na_mente import instalar_turno
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    root, _, _ = _root_instalado(monkeypatch, tmp_path)
    estado, corpo = root._estado_compartilhado_runtime, root._corpo_motor_runtime
    from scripts.tests.test_presenca_corporal_v2 import EspPresenca
    from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
    esp = EspPresenca()
    rosto = RostoOledRuntime(estado_getter=lambda: estado.retrato_dominio("conversacional"),
        porta="TESTE", abrir_serial=lambda _: esp)
    monkeypatch.setattr(corpo, "transporte", rosto)
    assert rosto.sincronizar()
    assert corpo.experiencias.aprendizado is root._motor_aprendizado_runtime
    corpo.executar("CORPO_MOVER", {"direcao": "frente"})
    e = estado.obter_copia("mental", "experiencia_corporal", {})
    assert root._motor_aprendizado_runtime.memoria.obter_hipotese_aprendizado("corpo_execucao:bancada:mover_frente:0")
    instalar_turno(estado, turno_id="feedback-corporal-1")
    mental = estado.retrato_dominio("mental")
    literal = "gostei desse movimento"
    estado.atualizar_campos("mental", turno_atual={**mental["turno_atual"], "texto": literal},
        retrato_turno_atual={**mental["retrato_turno_atual"], "texto": literal},
        plano_turno_atual={**mental["plano_turno_atual"], "texto_usuario": literal})
    corpo.modelo_para_mente("feedback-corporal-1")
    assert root._adaptadores_aplicacao_runtime._ns().get("_corpo_motor_runtime") is corpo, "composição deve injetar o owner"
    assert estado.mental["plano_turno_atual"]["retrato_corporal"]["ultima_experiencia"]["id"] == e["id"]
    root._adaptadores_aplicacao_runtime.registrar_mente_curta("gostei desse movimento", "obrigada")
    assert estado.mental["feedback_corporal"]["experiencia_id"] == e["id"]
    pergunta = "você consegue aprender com os gestos corporais?"
    resposta = root._mapa_habilidades_runtime.responder_pergunta_capacidade(pergunta, turno=classificar_modalidade_turno(pergunta))
    assert resposta and "mesma experiência corporal" in resposta and "aprender" in resposta
    rosto.encerrar()


def test_preferencia_madura_escolhe_variante_sem_criar_permissao(tmp_path):
    from scripts.tests.test_companhia_corporal import montar
    from datetime import datetime, timedelta
    import sqlite3
    estado, esp, _, corpo, _, _ = montar()
    motor = conectar_aprendizado(corpo, tmp_path)
    chave = "corpo_preferencia:rodas_suspensas:expressar:1:2"
    for i in range(10):
        motor.registrar_evidencia(chave=chave, tipo="preferencia_corporal", escopo="corpo_motor",
            valor={"nome": "alegria", "perfil": "rodas_suspensas", "variante": 2},
            sinal=.45, origem="feedback_usuario", evidencia="gostei desse gesto",
            contexto={"perfil": "rodas_suspensas"}, id_evento=f"qualificado-{i}")
    # Dias distintos na memória isolada: testa maturidade real, sem baixar regra.
    with sqlite3.connect(str(tmp_path / "corpo.sqlite")) as con:
        con.execute("UPDATE aprendizado_eventos SET criado_em=? WHERE id_evento=?", ((datetime.now()-timedelta(days=1)).isoformat(), "qualificado-0"))
    assert motor.avaliar_hipotese(chave)["aplicavel"]
    antes = list(esp.enviados)
    assert corpo.experiencias.selecionar_variante("expressar:1", "rodas_suspensas", 0) == 2
    assert corpo.experiencias.selecionar_variante("expressar:1", "bancada", 0) == 0
    assert esp.enviados == antes and not corpo.companhia.diagnostico()["ativa"]
    corpo.executar("CORPO_MOVER", {"direcao": "frente"})
    e = estado.obter_copia("mental", "experiencia_corporal", {})
    assert corpo.experiencias.observar_feedback("não gostei desse gesto", turno_id="recusa-1", referencia_id=e["id"])
    rejeicao = motor.memoria.obter_hipotese_aprendizado("corpo_evitacao:bancada:mover_frente:0")
    assert rejeicao["valor"]["direcao"] == "evitar" and not motor.avaliar_hipotese(rejeicao["chave"])["aplicavel"]


def test_evitar_variantes_exige_maturidade_e_nao_bloqueia_pedido_manual(tmp_path):
    from scripts.tests.test_companhia_corporal import montar
    from datetime import datetime, timedelta
    import sqlite3
    _, esp, _, corpo, _, _ = montar()
    motor = conectar_aprendizado(corpo, tmp_path)
    for variante in range(3):
        for i in range(10):
            motor.registrar_evidencia(chave=f"corpo_evitacao:rodas_suspensas:expressar:1:{variante}", tipo="preferencia_corporal", escopo="corpo_motor",
                valor={"direcao": "evitar", "variante": variante}, sinal=.45, origem="feedback_usuario", evidencia="não gostei desse gesto",
                contexto={"perfil": "rodas_suspensas"}, id_evento=f"recusa-{variante}-{i}")
        with sqlite3.connect(str(tmp_path / "corpo.sqlite")) as con:
            con.execute("UPDATE aprendizado_eventos SET criado_em=? WHERE id_evento=?", ((datetime.now()-timedelta(days=1)).isoformat(), f"recusa-{variante}-0"))
    antes = list(esp.enviados)
    assert corpo.experiencias.selecionar_variante("expressar:1", "rodas_suspensas", 0) is None
    assert esp.enviados == antes
    assert corpo.executar("CORPO_MOVER", {"direcao": "frente"})["ok"]


def test_falha_de_aprendizado_nao_altera_receipt_do_motor(tmp_path, monkeypatch):
    from scripts.tests.test_companhia_corporal import montar
    estado, _, _, corpo, _, _ = montar()
    motor = conectar_aprendizado(corpo, tmp_path)
    def falhar(**kwargs):
        raise OSError("memória indisponível")
    monkeypatch.setattr(motor.memoria, "registrar_evidencia_aprendizado", falhar)
    receipt = corpo.executar("CORPO_MOVER", {"direcao": "frente"})
    assert receipt["ok"] and estado.mental["experiencia_corporal"]["confirmado"]
    assert corpo.experiencias.retrato()["ultimo_erro"] == "falha_persistencia_experiencia"


def test_olhos_falham_na_cooperacao_sem_motor_nem_sucesso_aprendido(tmp_path, monkeypatch):
    from scripts.tests.test_corpo_na_mente import preparar_mente
    estado, esp, rosto, corpo, quadro, _ = preparar_mente(monkeypatch)
    motor = conectar_aprendizado(corpo, tmp_path)
    monkeypatch.setattr(corpo.companhia, "_olhos_confirmados", lambda _: False)
    assert not corpo.companhia.processar()["ok"]
    assert not estado.obter_copia("mental", "historico_corporal", [])
    assert not motor.memoria.listar_hipoteses_aprendizado()


def test_falha_de_parada_na_cooperacao_nao_vira_cancelamento_ou_sucesso(tmp_path, monkeypatch):
    from scripts.tests.test_companhia_corporal import montar, ativar, emocao
    from scripts.tests.test_corpo_transporte_oled import EspCorpo
    estado, esp, rosto, corpo, _, _ = montar(esp=EspCorpo(stopped=False))
    motor = conectar_aprendizado(corpo, tmp_path)
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "alegre")
    monkeypatch.setattr(corpo.companhia, "_aguardar_gesto", lambda ms, validar: validar())
    assert not corpo.companhia.processar()["ok"]
    e = estado.obter_copia("mental", "experiencia_corporal", {})
    assert not e["confirmado"] and e["resultado"] == "gesto_nao_confirmado"
    chave = f"corpo_execucao:{e['perfil']}:{e['nome']}:{e['variante']}"
    assert motor.memoria.obter_hipotese_aprendizado(chave)["evidencias_negativas"] == 1
