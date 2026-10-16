"""Um objetivo acompanha contexto, etapas e receipts sem renovar autoridade."""
from mente_laylay.cognicao.decisao_corporal import IntencaoCorporal
from scripts.tests.test_companhia_corporal import montar, ativar, emocao, motores


def test_espera_do_mesmo_objetivo_nao_renasce_por_timeout_de_apresentacao():
    estado, _, _, corpo, _, clock = montar()
    assert ativar(corpo)["ok"]
    estado.atualizar_campos("mental", atividade_operacional={
        "origem": "atividade_operacional_observada", "ativos": 1})
    corpo.companhia.processar()
    antes = dict(estado.mental["intencao_corporal"])
    clock[0] += 13
    corpo.companhia.processar()
    depois = estado.mental["intencao_corporal"]
    assert depois["id"] == antes["id"], "timeout visual não cria outro acontecimento"
    assert depois["autoriza_execucao"] is False


def test_contextos_distintos_com_mesma_emocao_nao_compartilham_objetivo():
    estado, _, _, corpo, _, _ = montar()
    assert ativar(corpo)["ok"]
    d = IntencaoCorporal("atenta", "atividade_pc_em_andamento", 100, 0, 1)
    estado.atualizar_campos("mental", turno_atual={"id": "a"}, plano_turno_atual={"id": "a"})
    corpo.companhia._registrar_intencao(d)
    antes = dict(estado.mental["intencao_corporal"])
    estado.atualizar_campos("mental", turno_atual={"id": "b"}, plano_turno_atual={"id": "b"})
    corpo.companhia._registrar_intencao(d)
    depois = estado.mental["intencao_corporal"]
    assert depois["id"] != antes["id"], "um novo turno não herda a intenção anterior"


def test_objetivo_persiste_entre_espera_e_reacao_mas_resultados_tem_identidade():
    estado, _, _, corpo, _, _ = montar()
    assert ativar(corpo)["ok"]
    estado.atualizar_campos("mental", turno_atual={"id": "t"}, plano_turno_atual={"id": "t"})
    corpo.companhia._registrar_intencao(IntencaoCorporal("atenta", "atividade_pc_em_andamento", 100, 1, 2))
    aguardando = dict(estado.mental["intencao_corporal"])
    estado.atualizar_campos("mental", atividade_operacional={
        "origem": "atividade_operacional_observada", "ativos": 0,
        "sucesso_id": 1, "sucesso_monotonic": 100})
    d = IntencaoCorporal("comemorar", "sucesso_operacional_confirmado", 80, 1, 2, True)
    corpo.companhia._registrar_intencao(d)
    primeiro = dict(estado.mental["intencao_corporal"])
    assert primeiro["objetivo_id"] == aguardando["objetivo_id"]
    assert primeiro["id"] != aguardando["id"]
    estado.atualizar_campos("mental", atividade_operacional={
        "origem": "atividade_operacional_observada", "ativos": 0,
        "sucesso_id": 2, "sucesso_monotonic": 100})
    corpo.companhia._registrar_intencao(d)
    assert estado.mental["intencao_corporal"]["id"] != primeiro["id"]


def test_emocao_vigente_aguarda_intervalo_sem_ser_consumida(monkeypatch):
    estado, esp, rosto, corpo, _, clock = montar()
    assert ativar(corpo)["ok"]
    monkeypatch.setattr(corpo.companhia, "_aguardar_gesto", lambda ms, validar: validar())
    emocao(estado, rosto, "alegre")
    assert corpo.companhia.processar()["ok"]
    emocao(estado, rosto, "envergonhada")
    assert not corpo.companhia.processar()["ok"]
    pendente = dict(estado.mental["intencao_corporal"])
    quantidade = len(motores(esp))
    clock[0] += 3
    assert corpo.companhia.processar()["ok"], "intervalo não descarta emoção ainda vigente"
    assert len(motores(esp)) > quantidade
    atual = estado.mental["intencao_corporal"]
    assert atual["id"] == pendente["id"]
    assert atual["estado"] == "concluida" and atual["fase"] == "acomodando"
    assert atual["resultado"]["experiencia_id"] == estado.mental["experiencia_corporal"]["id"]
    assert atual["resultado"]["prova_deslocamento"] is False


def test_turno_novo_interrompe_gesto_sem_emprestar_resultado_a_nova_conversa(monkeypatch):
    estado, esp, rosto, corpo, quadro, _ = montar()
    assert ativar(corpo)["ok"]
    estado.atualizar_campos("mental", turno_atual={"id": "a"}, plano_turno_atual={"id": "a"})
    emocao(estado, rosto, "alegre")
    mover = rosto.mover_corpo
    def trocar_turno(e, d, ms, **kw):
        estado.atualizar_campos("mental", turno_atual={"id": "b"}, plano_turno_atual={"id": "b"})
        return mover(e, d, ms, **kw)
    monkeypatch.setattr(rosto, "mover_corpo", trocar_turno)
    monkeypatch.setattr(corpo.companhia, "_aguardar_gesto", lambda ms, validar: validar())
    assert not corpo.companhia.processar()["ok"]
    assert not motores(esp)
    assert quadro.snapshot()["planos_recentes"][-1]["estado"] != "confirmado"
    e = estado.mental["experiencia_corporal"]
    assert e["turno_id"] == "a" and not e["confirmado"]
    m = corpo.modelo_para_mente("b")
    assert not m["intencao_em_curso"]["pertence_ao_turno_atual"]
    assert m["intencao_em_curso"]["fase"] == "interrompida"


def test_resultado_atrasado_nao_conclui_intencao_substituida():
    estado, _, _, corpo, _, _ = montar()
    assert ativar(corpo)["ok"]
    d = IntencaoCorporal("atenta", "atividade_pc_em_andamento", 100, 0, 1)
    corpo.companhia._registrar_intencao(d)
    antiga = estado.mental["intencao_corporal"]["id"]
    estado.atualizar_campos("mental", turno_atual={"id": "novo"})
    corpo.companhia._registrar_intencao(d)
    atual = dict(estado.mental["intencao_corporal"])
    corpo.companhia._fase_intencao(antiga, "acomodando", estado="concluida", resultado={"ok": True})
    assert estado.mental["intencao_corporal"] == atual


def test_intencao_restaurada_e_contexto_nao_ativam_companhia():
    estado, esp, _, corpo, _, _ = montar()
    estado.atualizar_campos("mental", intencao_corporal={"estado": "executando", "objetivo_id": "salvo"})
    assert not corpo.companhia.processar()["ok"]
    m = corpo.modelo_para_mente()
    assert m["intencao_em_curso"]["autoriza_execucao"] is False
    assert not m["intencao_em_curso"]["sessao_vigente"]
    assert not motores(esp)


def test_emocao_expirada_no_intervalo_nao_e_reproduzida(monkeypatch):
    estado, esp, rosto, corpo, _, clock = montar()
    assert ativar(corpo)["ok"]
    monkeypatch.setattr(corpo.companhia, "_aguardar_gesto", lambda ms, validar: validar())
    emocao(estado, rosto, "alegre")
    assert corpo.companhia.processar()["ok"]
    emocao(estado, rosto, "brava")
    assert not corpo.companhia.processar()["ok"]
    quantidade = len(motores(esp))
    estado.atualizar_campos("conversacional", emotion_interactions_left=0)
    assert rosto.sincronizar()
    clock[0] += 3
    assert not corpo.companhia.processar()["ok"]
    assert len(motores(esp)) == quantidade


def test_catalogo_vivo_explica_continuidade_sem_conceder_movimento():
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    _, esp, rosto, corpo, _, _ = montar()
    disp = DisponibilidadeOperacionalRuntime(rosto_oled_getter=rosto.diagnostico,
                                            corpo_motor_getter=corpo.diagnostico)
    mapa = MapaHabilidadesRuntime(operacional_getter=disp.snapshot)
    pergunta = "você consegue andar e controlar os motores?"
    resposta = mapa.responder_pergunta_capacidade(pergunta, turno=classificar_modalidade_turno(pergunta))
    assert "objetivo corporal" in resposta and "sem renovar permissão" in resposta
    assert not motores(esp)


def test_composicao_instalada_envia_intencao_continua_ao_contexto_da_mente(tmp_path):
    import subprocess, sys
    codigo = f'''
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir({str(tmp_path/'instancia')!r})
import laylay
from mente_laylay.cognicao.decisao_corporal import IntencaoCorporal
from mente_laylay.cognicao.modelo_corporal import formatar_realidade_corporal
corpo = laylay._corpo_motor_runtime
corpo.companhia._registrar_intencao(IntencaoCorporal("atenta", "atividade_pc_em_andamento", 100, 0, 1))
modelo = corpo.modelo_para_mente()
assert modelo["intencao_em_curso"]["fase"] == "aguardando"
assert not modelo["intencao_em_curso"]["autoriza_execucao"]
instrucao = formatar_realidade_corporal(modelo)
assert '"intencao_em_curso"' in instrucao and '"fase":"aguardando"' in instrucao
assert "não significa ação executada" in instrucao
assert laylay._estado_compartilhado_runtime.obter_copia("mental", "modelo_corporal", {{}})["intencao_em_curso"] == modelo["intencao_em_curso"]
'''
    r = subprocess.run([sys.executable, "-"], input=codigo, text=True, capture_output=True, timeout=40)
    assert r.returncode == 0, r.stdout + r.stderr
