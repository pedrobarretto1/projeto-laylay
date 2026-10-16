"""Continuidade proposta pela autoria atual; nunca replay da execução antiga."""
import json
import pytest
from types import SimpleNamespace

from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.decisao_corporal import IntencaoCorporal
from scripts.tests.test_corpo_na_mente import instalar_turno, publicar
from scripts.tests.test_companhia_corporal import montar, ativar


def preparar_objetivo(monkeypatch):
    from mente_laylay.cognicao import modelo_corporal
    estado, esp, rosto, corpo, quadro, clock = montar()
    assert ativar(corpo)["ok"]
    monkeypatch.setattr(modelo_corporal, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    instalar_turno(estado, turno_id="a")
    corpo.companhia._registrar_intencao(IntencaoCorporal("interagir", "conversa_em_andamento", 90, 0, 1, True))
    objetivo = estado.mental["intencao_corporal"]["objetivo_id"]
    return estado, esp, rosto, corpo, quadro, clock, objetivo


def continuar(estado, corpo, objetivo, *, turno_id="b", texto="e como você ficou com isso?", aguardando_mente=False, recapturar=False):
    instalar_turno(estado, turno_id=turno_id)
    # O texto e a proposta pertencem à mesma ocorrência no contrato principal.
    mental = estado.retrato_dominio("mental")
    mental["turno_atual"]["texto"] = texto
    mental["retrato_turno_atual"]["texto"] = texto
    mental["plano_turno_atual"]["texto_usuario"] = texto
    estado.substituir("mental", mental)
    modelo = corpo.modelo_para_mente(turno_id)
    if aguardando_mente:
        corpo.companhia._registrar_intencao(IntencaoCorporal("atenta", "atividade_pc_em_andamento", 100, 0, 1))
        if recapturar:
            modelo = corpo.modelo_para_mente(turno_id)
    proposta = ContratoPropostaPrincipal(turno_id, texto, json.dumps({
        "fala": "Continuo acompanhando nossa conversa.",
        "intencao_corporal": {"nome": "interagir", "objetivo_id": objetivo}}))
    plano = publicar(estado, proposta)
    return modelo, plano


def test_autoria_principal_vincula_objetivo_anterior_sem_herdar_comando(monkeypatch):
    estado, _, _, corpo, _, _, objetivo = preparar_objetivo(monkeypatch)
    _, plano = continuar(estado, corpo, objetivo)
    p = plano.get("intencao_corporal") or {}
    assert p.get("objetivo_id") == objetivo, "primeira fronteira: codec descarta referência ao objetivo vivo"
    assert p["turno_id"] == "b" and p["autoriza_execucao"] is False
    assert p["estado"] == "proposta"
    assert not p.get("resultado"), "continuidade não herda receipt anterior"


def test_owner_preserva_objetivo_mas_cria_intencao_do_novo_turno(monkeypatch):
    estado, _, _, corpo, _, _, objetivo = preparar_objetivo(monkeypatch)
    antiga = estado.mental["intencao_corporal"]["id"]
    _, plano = continuar(estado, corpo, objetivo)
    p = plano.get("intencao_corporal") or {}
    assert p.get("id"), "a proposta deve chegar ao owner"
    corpo.companhia._registrar_intencao(IntencaoCorporal("interagir", "intencao_da_mente", 95, 0, 1, True, p["id"]))
    atual = estado.mental["intencao_corporal"]
    assert atual["objetivo_id"] == objetivo
    assert atual["id"] != antiga and atual["turno_id"] == "b"
    assert atual["objetivo_turno_origem"] == "a"
    assert atual["turnos_objetivo"] == 2


def test_planejamento_evitar_repeticao_usa_historico_factual_no_owner_existente():
    estado, _, _, corpo, _, _ = montar()
    # Registro de execução elétrica via owner real; não afirma movimento físico.
    e = corpo.experiencias.iniciar(nome="expressar_frase_v1", origem_intencao="mente_causal",
        perfil="rodas_suspensas", familia="expressar:1", variante=0)
    corpo.experiencias.registrar(e, {"ok": True}, [
        {"ok": True, "aplicacao_pwm_confirmada": True, "parada_confirmada": True}])
    assert corpo.experiencias.selecionar_variante("expressar:1", "rodas_suspensas", 0) != 0
    assert estado.mental["experiencia_corporal"]["prova_deslocamento"] is False


def test_espera_da_llm_nao_perde_referencia_capturada_no_retrato(monkeypatch):
    estado, _, _, corpo, _, _, objetivo = preparar_objetivo(monkeypatch)
    _, plano = continuar(estado, corpo, objetivo, aguardando_mente=True)
    p = plano.get("intencao_corporal") or {}
    assert p.get("objetivo_id") == objetivo
    corpo.companhia._registrar_intencao(IntencaoCorporal("interagir", "intencao_da_mente", 95, 0, 1, True, p["id"]))
    assert estado.mental["intencao_corporal"]["objetivo_id"] == objetivo, "a espera não é mudança de assunto"


def test_retrato_capturado_depois_da_espera_conserva_candidato_sem_autorizar(monkeypatch):
    estado, esp, _, corpo, _, _, objetivo = preparar_objetivo(monkeypatch)
    modelo, plano = continuar(estado, corpo, objetivo, aguardando_mente=True, recapturar=True)
    assert modelo["intencao_em_curso"]["objetivo_id"] != objetivo
    assert modelo["objetivo_para_continuar"]["objetivo_id"] == objetivo
    assert not modelo["objetivo_para_continuar"]["autoriza_execucao"]
    assert plano["intencao_corporal"]["objetivo_id"] == objetivo
    from scripts.tests.test_companhia_corporal import motores
    assert not motores(esp)


@pytest.mark.parametrize("invalidar", ["prazo", "revogacao", "sessao", "identificador", "assunto"])
def test_referencia_fora_do_contexto_nao_cria_proposta_ou_movimento(monkeypatch, invalidar):
    estado, esp, _, corpo, _, clock, objetivo = preparar_objetivo(monkeypatch)
    if invalidar == "prazo": clock[0] += 121
    elif invalidar == "revogacao": corpo.companhia.revogar("pedido_usuario")
    elif invalidar == "sessao": corpo.companhia._concessao["sessao"] = "ffff0123"
    elif invalidar == "identificador": objetivo = "000000000000"
    elif invalidar == "assunto":
        instalar_turno(estado, turno_id="outra-conversa")
        corpo.companhia._registrar_intencao(IntencaoCorporal("expressar", "mudanca_emocional_causal", 70, 1, 2, True))
    _, plano = continuar(estado, corpo, objetivo)
    assert not plano.get("intencao_corporal")
    from scripts.tests.test_companhia_corporal import motores
    assert not motores(esp)


def test_continuar_nao_renova_prazo_e_limite_de_turnos(monkeypatch):
    estado, _, _, corpo, _, clock, objetivo = preparar_objetivo(monkeypatch)
    prazo = estado.mental["intencao_corporal"]["objetivo_ate_monotonic"]
    for numero in range(2, 9):
        clock[0] += 1
        _, plano = continuar(estado, corpo, objetivo, turno_id=str(numero))
        p = plano["intencao_corporal"]
        corpo.companhia._registrar_intencao(IntencaoCorporal("interagir", "intencao_da_mente", 95, 0, 1, True, p["id"]))
        assert estado.mental["intencao_corporal"]["turnos_objetivo"] == numero
        assert estado.mental["intencao_corporal"]["objetivo_ate_monotonic"] == prazo
    _, plano = continuar(estado, corpo, objetivo, turno_id="9")
    assert not plano.get("intencao_corporal")


def test_omitir_referencia_inicia_novo_objetivo(monkeypatch):
    estado, _, _, corpo, _, _, objetivo = preparar_objetivo(monkeypatch)
    proposta = instalar_turno(estado, nome="expressar", turno_id="novo-assunto")
    corpo.modelo_para_mente("novo-assunto")
    plano = publicar(estado, proposta)
    corpo.companhia._registrar_intencao(IntencaoCorporal("expressar", "intencao_da_mente", 95, 1, 2, True, plano["intencao_corporal"]["id"]))
    assert estado.mental["intencao_corporal"]["objetivo_id"] != objetivo


def test_descansar_encerra_objetivo_sem_reativar_por_retrato_idle(monkeypatch):
    estado, _, _, corpo, _, _, objetivo = preparar_objetivo(monkeypatch)
    continuar(estado, corpo, objetivo)
    # Re-publica pelo mesmo canal original a intenção de descansar neste turno.
    plano = estado.mental["plano_turno_atual"]
    estado.atualizar_campos("mental", plano_turno_atual={k: v for k, v in plano.items() if k != "intencao_corporal"})
    p = ContratoPropostaPrincipal("b", "e como você ficou com isso?", json.dumps({
        "fala": "Vou me acomodar.", "intencao_corporal": {"nome": "descansar", "objetivo_id": objetivo}}))
    publicado = publicar(estado, p)
    corpo.companhia._registrar_intencao(IntencaoCorporal("descansar", "intencao_da_mente", 95, 0, 1,
                                                      proposta_id=publicado["intencao_corporal"]["id"]))
    assert not corpo.modelo_para_mente()["objetivo_para_continuar"]["continuidade_disponivel"]
    corpo.companhia._registrar_intencao(IntencaoCorporal("descansar", "sem_intencao_de_movimento", 10, 0, 1))
    assert not corpo.modelo_para_mente()["objetivo_para_continuar"]["continuidade_disponivel"]


def test_selecao_ignora_experiencia_de_outra_sessao_ou_recuperada():
    estado, _, _, corpo, _, _ = montar()
    estado.atualizar_campos("mental", historico_corporal=[{
        "familia": "expressar:1", "perfil": "rodas_suspensas", "sessao": "outra", "variante": 0, "confirmado": True}])
    assert corpo.experiencias.selecionar_variante("expressar:1", "rodas_suspensas", 0) == 0
    e = estado.mental["historico_corporal"][0]
    estado.atualizar_campos("mental", historico_corporal=[{**e, "sessao": corpo.transporte.diagnostico()["sessao"], "recuperada_da_memoria": True}])
    assert corpo.experiencias.selecionar_variante("expressar:1", "rodas_suspensas", 0) == 0


def test_retrato_povoado_cabe_inteiro_no_transporte_local_sem_perder_contrato(monkeypatch):
    from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal
    from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
    from mente_laylay.integracao.llm_http import compactar_payload_llm_local
    estado, _, _, corpo, _, _, objetivo = preparar_objetivo(monkeypatch)
    for n in range(3):
        e = corpo.experiencias.iniciar(nome="expressar_frase_v1", origem_intencao="mente_causal",
            perfil="rodas_suspensas", familia="expressar:1", variante=n,
            movimentos=((100, -100, 500), (-100, 100, 500)))
        corpo.experiencias.registrar(e, {"ok": True}, [
            {"ok": True, "aplicacao_pwm_confirmada": True, "parada_confirmada": True}])
    modelo, _ = continuar(estado, corpo, objetivo, aguardando_mente=True, recapturar=True)
    instrucao = formatar_modelo_corporal(modelo)
    payload = preparar_payload_llm([{"role": "system", "content": instrucao},
        {"role": "user", "content": "e como você ficou com isso?"}], model="qwen3-vl:4b",
        max_tokens=256, endpoint_local=True, contexto_fechado=True)
    compacto = compactar_payload_llm_local(payload)
    assert instrucao in compacto["messages"][-2]["content"], "a projeção deve caber sem perder o fim do contrato"
    assert objetivo in instrucao and "historico_recente" in instrucao
    assert "nunca ausência de movimento" in instrucao


def test_catalogo_vivo_conhece_objetivos_entre_turnos_sem_armar_corpo():
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    _, esp, rosto, corpo, _, _ = montar()
    disp = DisponibilidadeOperacionalRuntime(rosto_oled_getter=rosto.diagnostico, corpo_motor_getter=corpo.diagnostico)
    mapa = MapaHabilidadesRuntime(operacional_getter=disp.snapshot)
    pergunta = "você consegue manter um objetivo corporal entre turnos?"
    fala = mapa.responder_pergunta_capacidade(pergunta, turno=classificar_modalidade_turno(pergunta))
    assert "oito turnos" in fala and "histórico recente" in fala
    from scripts.tests.test_companhia_corporal import motores
    assert not motores(esp)


def test_continuacao_executa_nova_partitura_uma_vez_pelo_coordenador(monkeypatch):
    from scripts.tests.test_companhia_corporal import motores
    estado, esp, rosto, corpo, quadro, clock, objetivo = preparar_objetivo(monkeypatch)
    _, plano = continuar(estado, corpo, objetivo)
    estado.atualizar_campos("mental", plano_turno_atual={**plano, "fase": "executado"})
    estado.atualizar_campos("conversacional", audio_playing=True, is_speaking=True)
    assert rosto.sincronizar()
    monkeypatch.setattr(corpo.companhia, "_aguardar_gesto", lambda ms, validar: validar())
    assert corpo.companhia.processar()["ok"]
    experiencia = estado.mental["experiencia_corporal"]
    assert experiencia["turno_id"] == "b" and experiencia["objetivo_id"] == objetivo
    assert experiencia["confirmado"] and not experiencia["prova_deslocamento"]
    assert quadro.snapshot()["planos_recentes"][-1]["metadados"]["turno_id"] == "b"
    quantidade = len(motores(esp))
    clock[0] += 3
    corpo.companhia.processar()
    assert len(motores(esp)) == quantidade, "continuidade não permite repetir a mesma proposta"


def test_tarefa_pc_interrompe_continuacao_e_receipt_nao_passam_a_outro_turno(monkeypatch):
    from scripts.tests.test_companhia_corporal import motores
    estado, esp, rosto, corpo, quadro, _, objetivo = preparar_objetivo(monkeypatch)
    _, plano = continuar(estado, corpo, objetivo)
    estado.atualizar_campos("mental", plano_turno_atual={**plano, "fase": "executado"})
    estado.atualizar_campos("conversacional", audio_playing=True, is_speaking=True)
    assert rosto.sincronizar()
    monkeypatch.setattr(corpo.companhia, "_aguardar_gesto", lambda ms, validar: validar())
    mover = rosto.mover_corpo
    def iniciar_tarefa(e, d, ms, **kw):
        estado.atualizar_campos("mental", atividade_operacional={"origem": "atividade_operacional_observada", "ativos": 1})
        return mover(e, d, ms, **kw)
    monkeypatch.setattr(rosto, "mover_corpo", iniciar_tarefa)
    assert not corpo.companhia.processar()["ok"]
    assert not motores(esp)
    assert quadro.snapshot()["planos_recentes"][-1]["estado"] != "confirmado"
    assert estado.mental["experiencia_corporal"]["turno_id"] == "b"
    assert not estado.mental["experiencia_corporal"]["confirmado"]


def test_composicao_instalada_publica_referencia_apos_espera_sem_motor(tmp_path):
    import subprocess, sys
    codigo = f'''
import json
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir({str(tmp_path/'instancia')!r})
import laylay
from scripts.tests.test_presenca_corporal_v2 import EspPresenca
from scripts.tests.test_corpo_na_mente import instalar_turno
from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
from mente_laylay.cognicao.decisao_corporal import IntencaoCorporal
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
estado, corpo = laylay._estado_compartilhado_runtime, laylay._corpo_motor_runtime
esp = EspPresenca()
rosto = RostoOledRuntime(estado_getter=lambda: estado.retrato_dominio("conversacional"), porta="TESTE", abrir_serial=lambda _: esp)
corpo.transporte = rosto
assert rosto.sincronizar()
assert corpo.companhia.processar()["ok"]
instalar_turno(estado, turno_id="a")
corpo.companhia._registrar_intencao(IntencaoCorporal("interagir", "conversa_em_andamento", 90, 0, 1, True))
objetivo = estado.mental["intencao_corporal"]["objetivo_id"]
instalar_turno(estado, turno_id="b")
corpo.companhia._registrar_intencao(IntencaoCorporal("atenta", "atividade_pc_em_andamento", 100, 0, 1))
pacote = laylay._contexto_prompt_runtime.preparar_pacote("gosto de você")
assert "objetivo_para_continuar" in pacote.prompt_sistema and objetivo in pacote.prompt_sistema
p = ContratoPropostaPrincipal("b", "gosto de você", json.dumps({{"fala":"Obrigada!","intencao_corporal":{{"nome":"interagir","objetivo_id":objetivo}}}}))
plano = laylay._composicao_turno_runtime.atualizar_proposta("resposta_planejada", p)
assert plano["intencao_corporal"]["objetivo_id"] == objetivo
assert plano["intencao_corporal"]["turno_id"] == "b" and not plano["intencao_corporal"]["autoriza_execucao"]
assert not any(c.startswith("MOTOR ") for c in esp.enviados)
rosto.encerrar()
'''
    r = subprocess.run([sys.executable, "-"], input=codigo, text=True, capture_output=True, timeout=40)
    assert r.returncode == 0, r.stdout + r.stderr
