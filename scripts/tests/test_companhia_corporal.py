"""Companhia corporal: uma concessão temporária não é percepção nem receipt."""
import pytest

from mente_laylay.cognicao.gramatica_corpo import detectar_intencao_corpo
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.especialistas.capacidades import consultar_capacidade


@pytest.mark.parametrize("texto,acao", [
    ("ative modo companhia na bancada", "ativar"),
    ("pode ativar o modo companhia na área delimitada?", "ativar"),
    ("desative o modo companhia", "desativar"),
])
def test_modo_corporal_deriva_concessao_da_fala_atual(texto, acao):
    pedido = detectar_intencao_corpo(texto)
    assert pedido and pedido["intent"] == "CORPO_COMPANHIA", "falta operação canônica de concessão corporal"
    assert pedido["params"]["acao"] == acao
    assert classificar_modalidade_turno(texto)["autoriza_execucao"] is True


def test_catalogo_descreve_concessao_limitada_sem_promover_emocao_a_permissao():
    capacidade = consultar_capacidade("CORPO_COMPANHIA")
    assert capacidade and capacidade["dominio"] == "corpo_motor", "catálogo desconhece companhia corporal"
    assert "USB" in capacidade["limites"]


@pytest.mark.parametrize("texto", [
    "não ative modo companhia na bancada", "talvez ative modo companhia na bancada",
    "você consegue ativar modo companhia?", "ative modo companhia", 
    "ative modo companhia na mesa", "traduza 'ative modo companhia na bancada'",
])
def test_mencao_ou_area_sem_limites_nao_concede_iniciativa_corporal(texto):
    assert detectar_intencao_corpo(texto) is None


from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
from mente_laylay.autonomia.orquestracao_cooperativa import OrquestradorCooperativoRuntime
from mente_laylay.autonomia.quadro_cooperacao import QuadroCooperacaoRuntime
from scripts.tests.test_corpo_transporte_oled import EspCorpo
from scripts.tests.test_rosto_oled import estado_emocional


def montar(*, esp=None, automatico=False, passeio=False):
    estado = criar_estado_compartilhado_runtime()
    esp = esp or EspCorpo()
    rosto = RostoOledRuntime(estado_getter=lambda: estado.retrato_dominio("conversacional"),
                            porta="TESTE", abrir_serial=lambda _: esp)
    agora = [100.0]
    corpo = CorpoMotorRuntime(transporte=rosto, estado=estado, monotonic=lambda: agora[0],
        **({"companhia_bancada_ao_iniciar": True} if automatico else {}),
        **({"passeio_bancada_ao_iniciar": True} if passeio else {}))
    quadro = QuadroCooperacaoRuntime(modo="ativo", log=lambda _: None)
    cooperacao = OrquestradorCooperativoRuntime(quadro=quadro,
        clipboard_snapshot=lambda: {}, clipboard_getter=lambda: "", executar_intencao=lambda *_: False,
        resolver_caminho=lambda s: s, falar=lambda *_: None, log=lambda _: None)
    corpo.companhia.coordenador = cooperacao
    cooperacao.governanca.registrar_autorizador_escopo("corpo_companhia", corpo.companhia.autorizar_escopo)
    assert rosto.sincronizar()
    return estado, esp, rosto, corpo, quadro, agora


def ativar(corpo):
    texto = "ative modo companhia na bancada"
    return corpo.executar("CORPO_COMPANHIA", detectar_intencao_corpo(texto)["params"],
                         autorizacao=classificar_modalidade_turno(texto))


def emocao(estado, rosto, valor):
    estado.substituir("conversacional", estado_emocional(valor))
    assert rosto.sincronizar()


def motores(esp):
    return [p for p in esp.enviados if p.startswith("MOTOR ")]


def test_emocao_ou_diagnostico_restaurado_nao_arma_corpo():
    estado, esp, rosto, corpo, _, _ = montar()
    emocao(estado, rosto, "alegre")
    estado.atualizar_campos("mental", companhia_corporal={"ativa": True})
    assert not corpo.companhia.processar()["ok"]
    assert not motores(esp) and not corpo.diagnostico()["autonomia_ativada"]
    assert not corpo.executar("CORPO_COMPANHIA", {"acao": "ativar"})["ok"]


def test_modo_explicito_gesto_cooperativo_cooldown_sem_replay_da_emocao_antiga():
    estado, esp, rosto, corpo, quadro, agora = montar()
    emocao(estado, rosto, "alegre")
    assert ativar(corpo)["ok"] and not motores(esp)
    assert not corpo.companhia.processar()["ok"]
    emocao(estado, rosto, "triste")
    assert corpo.companhia.processar()["ok"]
    p = motores(esp)[0].split()
    assert p[-3:-1] == ["-100", "-100"] and 50 <= int(p[-1]) <= 500
    assert quadro.snapshot()["planos_recentes"][-1]["estado"] == "confirmado"
    assert not estado.mental["corpo_motor"]["prova_rotacao"]
    emocao(estado, rosto, "brava")
    assert not corpo.companhia.processar()["ok"]
    agora[0] += 21
    assert not corpo.companhia.processar()["ok"], "gesto descartado não aguarda no cooldown"
    emocao(estado, rosto, "alegre")
    # Tristeza usa um movimento; alegria agora tem resposta e acomodação.
    assert corpo.companhia.processar()["ok"] and len(motores(esp)) == 3
    assert corpo.companhia.diagnostico()["gestos_emitidos"] == 2


@pytest.mark.parametrize("invalidar", ["sessao", "ack", "stop", "manual"])
def test_concessao_vigente_precisa_sobreviver_ate_executor_sem_rearme(invalidar):
    estado, esp, rosto, corpo, _, agora = montar()
    assert ativar(corpo)["ok"]
    if invalidar == "sessao":
        rosto.encerrar()
        assert rosto.sincronizar()
    elif invalidar == "ack":
        rosto._ultimo_ack = float("-inf")
    elif invalidar == "stop":
        assert corpo.executar("CORPO_PARAR", {})["ok"]
    else:
        assert corpo.executar("CORPO_MOVER", {"direcao": "frente"})["ok"]
    corpo.companhia.processar()  # Consome a perda antes de qualquer reconexão.
    assert not corpo.diagnostico()["autonomia_ativada"]
    assert rosto.sincronizar()
    numero = len(motores(esp))
    emocao(estado, rosto, "alegre")
    assert not corpo.companhia.processar()["ok"] and len(motores(esp)) == numero


def test_face_confirmada_nao_empresta_sucesso_ao_motor_sem_mack():
    estado, esp, rosto, corpo, quadro, _ = montar(esp=EspCorpo(mack=False))
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "alegre")
    assert not corpo.companhia.processar()["ok"]
    final = quadro.snapshot()["planos_recentes"][-1]
    assert final["estado"] == "falhou" and final["etapas"][0]["estado"] == "confirmado"
    assert not corpo.diagnostico()["autonomia_ativada"]
    assert len(motores(esp)) == 1
    assert not corpo.companhia.processar()["ok"] and len(motores(esp)) == 1


def test_revogacao_entre_etapas_e_dentro_do_transporte_impede_motor():
    estado, esp, rosto, corpo, _, _ = montar()
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "alegre")
    original = rosto.mover_corpo
    def antes_do_motor(*args, **kwargs):
        corpo.companhia.revogar("parada_concorrente")
        return original(*args, **kwargs)
    rosto.mover_corpo = antes_do_motor
    assert not corpo.companhia.processar()["ok"]
    assert not motores(esp)


def test_concessao_de_um_escopo_nao_autoriza_outro_intent():
    _, _, _, corpo, _, agora = montar()
    assert ativar(corpo)["ok"]
    plano = {"autorizacao": "autonomia_previamente_concedida", "metadados": {
        "escopo_autorizacao": "corpo_companhia", "fluxo": "companhia_corporal",
        "concessao_id": corpo.companhia._concessao["id"], "proposto_em": agora[0]}}
    governanca = corpo.companhia.coordenador.governanca
    assert not governanca.avaliar_autorizacao(plano, {"intent": "DELETE_ITEM"})["permitido"]
    plano["metadados"]["escopo_autorizacao"] = "inventado"
    assert not governanca.avaliar_autorizacao(plano, {"intent": "CORPO_GESTO"})["permitido"]


def test_sessao_tcp_nao_aceita_concessao_usb():
    _, esp, rosto, corpo, _, _ = montar()
    original = rosto.diagnostico
    rosto.diagnostico = lambda: {**original(), "transporte": "tcp"}
    assert not ativar(corpo)["ok"] and not motores(esp)


def test_erro_motor_alimenta_observador_visual_real_sem_transformar_stop_em_falha():
    from mente_laylay.memoria_mental.atividade_operacional_runtime import criar_atividade_operacional_runtime
    estado, _, rosto, corpo, _, _ = montar(esp=EspCorpo(stopped=False))
    atividade = criar_atividade_operacional_runtime(estado=estado)
    corpo.observar_resultado_cb = lambda r: atividade.observar_resultado(r, retorno_executor=True)
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "alegre")
    assert not corpo.companhia.processar()["ok"]
    assert estado.obter_copia("mental", "atividade_operacional", {})["falha_id"] == 1


def test_fala_gesticula_uma_vez_e_silencio_nao_concede_modo():
    estado, esp, rosto, corpo, _, agora = montar()
    estado.atualizar_campos("conversacional", is_speaking=True)
    assert rosto.sincronizar()
    assert not corpo.companhia.processar()["ok"] and not motores(esp)
    estado.atualizar_campos("conversacional", is_speaking=False)
    assert rosto.sincronizar()
    assert ativar(corpo)["ok"]
    estado.atualizar_campos("conversacional", is_speaking=True)
    assert rosto.sincronizar()
    assert corpo.companhia.processar()["ok"] and len(motores(esp)) == 1
    for _ in range(3):
        agora[0] += 21
        assert not corpo.companhia.processar()["ok"]
    agora[0] += 1801
    corpo.companhia.processar()
    assert corpo.diagnostico()["autonomia_ativada"] and len(motores(esp)) == 1


def test_composicao_instalada_ativa_por_fala_aprende_receipt_e_conhece_modo(monkeypatch, tmp_path):
    from scripts.tests.test_corpo_motor import _root_instalado
    from mente_laylay.autonomia.roteador_intencao import executar_intencao
    root, _, falas = _root_instalado(monkeypatch, tmp_path)
    estado = root._estado_compartilhado_runtime
    esp = EspCorpo()
    rosto = RostoOledRuntime(estado_getter=lambda: estado.retrato_dominio("conversacional"),
                            porta="TESTE", abrir_serial=lambda _: esp)
    assert rosto.sincronizar()
    corpo = root._corpo_motor_runtime
    monkeypatch.setattr(corpo, "transporte", rosto)
    corpo.companhia.revogar("inicio_teste")
    assert corpo.companhia.coordenador is root._orquestrador_cooperativo_runtime
    target = root._composicao_servicos_runtime.catalogo_threads()["Laylay-Companhia-Corporal"]
    assert target.func.__self__ is corpo.companhia
    ciclo = root._composicao_ciclo_comandos_runtime.ciclo
    texto = "ative modo companhia na bancada"
    estado.atualizar_campos("mental", turno_atual=classificar_modalidade_turno(texto))
    pedido, rota = ciclo.resolver_comando_natural(texto, "teste_companhia")
    assert pedido and pedido["intent"] == "CORPO_COMPANHIA", rota
    assert not corpo.diagnostico()["autonomia_ativada"]
    assert ciclo.executar_intencao(pedido, texto)
    assert corpo.diagnostico()["autonomia_ativada"] and not motores(esp)
    receipt = estado.obter_copia("mental", "ultima_acao_contrato", {})
    assert receipt["intent"] == "CORPO_COMPANHIA" and receipt["confirmado"] is True
    memoria = root._motor_aprendizado_runtime.memoria
    hipotese = memoria.obter_hipotese_aprendizado("confiabilidade:CORPO_COMPANHIA:ativar:corpo")
    assert hipotese and hipotese["evidencias_positivas"] == 1
    assert "autoriza_execucao" not in hipotese["valor"]
    pergunta = "você consegue usar modo companhia?"
    turno = classificar_modalidade_turno(pergunta)
    assert "sessão USB" in root._mapa_habilidades_runtime.responder_pergunta_capacidade(pergunta, turno=turno)
    emocao(estado, rosto, "alegre")
    assert corpo.companhia.processar()["ok"]
    assert len(motores(esp)) == 2
    assert not memoria.obter_hipotese_aprendizado("cooperacao:rosto_oled:corpo_motor"), "receipt automático não é preferência humana"
    # A concessão não pode ser repetida implicitamente pelo canal de última ação.
    assert not root._composicao_ciclo_comandos_runtime.contexto.montar()["_resolver_repeticao_ultima_acao"]("de novo")
    texto = "pare os motores"
    estado.atualizar_campos("mental", turno_atual=classificar_modalidade_turno(texto))
    pedido, _ = ciclo.resolver_comando_natural(texto, "teste_companhia")
    assert ciclo.executar_intencao(pedido, texto)
    assert not corpo.diagnostico()["autonomia_ativada"]
    assert len(falas) >= 2


def test_tick_da_mente_antes_do_heartbeat_oled_aguarda_mesmo_retrato_sem_falha():
    estado, esp, rosto, corpo, _, _ = montar()
    assert ativar(corpo)["ok"]
    estado.substituir("conversacional", estado_emocional("alegre"))
    assert corpo.companhia.processar()["motivo"] == "aguardando_retrato_no_oled"
    assert corpo.diagnostico()["autonomia_ativada"] and not motores(esp)
    assert rosto.sincronizar()
    assert corpo.companhia.processar()["ok"] and len(motores(esp)) == 2


def test_documentacao_preserva_disponibilidade_por_capacidade_sem_suprimir_domino():
    import json
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    from mente_laylay.memoria_mental.disponibilidade_operacional import DisponibilidadeOperacionalRuntime
    _, _, rosto, corpo, _, _ = montar()
    original = rosto.diagnostico
    rosto.diagnostico = lambda: {**original(), "transporte": "tcp"}
    disp = DisponibilidadeOperacionalRuntime(rosto_oled_getter=rosto.diagnostico, corpo_motor_getter=corpo.diagnostico)
    mapa = MapaHabilidadesRuntime(operacional_getter=disp.snapshot)
    texto = "como eu poderia andar?"
    doc = json.loads(mapa.evidencia_conversacional(texto, turno=classificar_modalidade_turno(texto))["documentacao_capacidades"])[0]
    assert doc["estado"] == "disponivel" and "ande para frente" in doc["exemplos"]
    assert "ative modo companhia na bancada" not in doc["exemplos"]
    assert next(c for c in doc["estados_por_capacidade"] if c["intent"] == "CORPO_COMPANHIA")["estado"] == "indisponivel"


def test_plano_fisico_declara_nao_idempotencia_e_disputa_execucao_uma_vez():
    from threading import Thread, Event
    from mente_laylay.autonomia.executor_cooperacao import ExecutorPlanoCooperativoRuntime
    from mente_laylay.autonomia.governanca_cooperacao import GovernancaPlanoCooperativoRuntime
    quadro = QuadroCooperacaoRuntime(modo="ativo", log=lambda _: None)
    plano = quadro.criar_plano(objetivo="efeito não idempotente", evento_ids=(), confianca=1,
        risco="medio", autorizacao="explicita_no_pedido", etapas=[{
            "id": "efeito", "acao": "teste", "idempotente": False, "reexecutavel": False}])
    assert plano["etapas"][0]["idempotente"] is False
    executor = ExecutorPlanoCooperativoRuntime(quadro=quadro, governanca=GovernancaPlanoCooperativoRuntime(
        quadro=quadro, autorizar_acao=lambda *_a, **_k: {"permitido": True}), log=lambda _: None)
    entrou, liberar = Event(), Event()
    efeitos = []
    def efeito(*_):
        efeitos.append(1)
        entrou.set()
        assert liberar.wait(3)
        return {"ok": True, "confirmado": True}
    worker = Thread(target=lambda: executor.executar(plano["id"], {"efeito": efeito}))
    worker.start()
    assert entrou.wait(3)
    try:
        assert not executor.executar(plano["id"], {"efeito": efeito})["ok"]
    finally:
        liberar.set()
        worker.join(3)
    assert efeitos == [1]


def test_alegria_tem_resposta_e_acomodacao_com_receipt_independente():
    estado, esp, rosto, corpo, quadro, _ = montar()
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "alegre")
    assert corpo.companhia.processar()["ok"]
    comandos = [p.split()[-3:] for p in motores(esp)]
    assert len(comandos) == 2, "gesto continua reduzido a um movimento sem acomodação"
    assert comandos[0][:2] == ["100", "100"]
    assert comandos[1][:2] == ["-100", "-100"]
    assert 180 < sum(int(p[2]) for p in comandos) <= 1500
    assert quadro.snapshot()["planos_recentes"][-1]["estado"] == "confirmado"


def test_falha_da_acomodacao_nao_herda_receipt_do_primeiro_movimento():
    class EspSemSegundoAck(EspCorpo):
        def write(self, dados):
            if dados.startswith(b"MOTOR ") and len(motores(self)) == 1:
                self.mack = False
            return super().write(dados)
    estado, esp, rosto, corpo, quadro, _ = montar(esp=EspSemSegundoAck())
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "alegre")
    assert not corpo.companhia.processar()["ok"], "primeiro MACK não confirma a sequência inteira"
    assert len(motores(esp)) == 2
    assert quadro.snapshot()["planos_recentes"][-1]["estado"] == "falhou"
    assert not corpo.diagnostico()["autonomia_ativada"]


@pytest.mark.parametrize("mudanca", ["stop", "emocao", "sessao"])
def test_sequencia_revalida_causa_e_concessao_antes_de_cada_movimento(mudanca):
    estado, esp, rosto, corpo, _, _ = montar()
    falhas = []
    corpo.observar_resultado_cb = falhas.append
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "alegre")
    original = rosto.mover_corpo
    def primeiro_movimento(*args, **kwargs):
        retorno = original(*args, **kwargs)
        if mudanca == "stop":
            assert corpo.executar("CORPO_PARAR", {})["ok"]
        elif mudanca == "emocao":
            emocao(estado, rosto, "triste")
        else:
            rosto.encerrar()
            assert rosto.sincronizar()
        return retorno
    rosto.mover_corpo = primeiro_movimento
    assert not corpo.companhia.processar()["ok"], "gesto obsoleto não pode se declarar concluído"
    assert len(motores(esp)) == 1, "segunda etapa não pode usar a causa/concessão anterior"
    if mudanca in {"stop", "emocao"}:
        assert not falhas, "interrupção intencional ou nova causa não é erro para glitch"


@pytest.mark.parametrize("emocao_id", range(1, 8))
@pytest.mark.parametrize("nivel", [1, 2, 3])
def test_partitura_preserva_piso_pwm_e_orcamento_motor(emocao_id, nivel):
    from mente_laylay.autonomia.companhia_corporal import selecionar_gesto
    gesto = selecionar_gesto(emocao_id, nivel)
    assert 1 <= len(gesto.movimentos) <= 4
    assert 100 <= sum(ms for _, _, ms in gesto.movimentos) <= 1500
    assert all(abs(e) == abs(d) == 100 and 50 <= ms <= 500 for e, d, ms in gesto.movimentos)
    assert gesto.antecipacao_ms + gesto.pausa_ms * (len(gesto.movimentos) - 1) + sum(
        ms for _, _, ms in gesto.movimentos) <= 2400


def test_intensidade_modula_tempo_e_vergonha_nao_repete_surpresa():
    from mente_laylay.autonomia.companhia_corporal import selecionar_gesto
    assert selecionar_gesto(1, 1).movimentos != selecionar_gesto(1, 3).movimentos
    assert selecionar_gesto(6, 2).antecipacao_ms > selecionar_gesto(5, 2).antecipacao_ms
    assert selecionar_gesto(6, 2).movimentos != selecionar_gesto(5, 2).movimentos
    assert selecionar_gesto(0, 2) is None and selecionar_gesto(8, 2) is None


def test_stop_acorda_antecipacao_sem_esperar_ou_acionar_motor():
    import time
    from threading import Thread, Event
    estado, esp, rosto, corpo, _, _ = montar()
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "envergonhada")
    esperando = Event()
    original = corpo.companhia._aguardar_gesto
    def aguardar(ms, validar):
        esperando.set()
        return original(ms, validar)
    corpo.companhia._aguardar_gesto = aguardar
    worker = Thread(target=corpo.companhia.processar)
    worker.start()
    assert esperando.wait(2)
    inicio = time.monotonic()
    try:
        assert corpo.executar("CORPO_PARAR", {})["ok"]
        worker.join(.2)
        assert not worker.is_alive() and time.monotonic() - inicio < .2
        assert not motores(esp)
    finally:
        corpo.companhia.revogar("fim_teste")
        worker.join(2)


def test_concessao_dura_sessao_sem_expirar_por_tempo_ou_trinta_gestos():
    estado, esp, rosto, corpo, _, agora = montar()
    assert ativar(corpo)["ok"]
    agora[0] += 3601
    corpo.companhia._concessao["gestos"] = 31
    emocao(estado, rosto, "alegre")
    assert corpo.companhia.processar()["ok"]
    assert corpo.diagnostico()["autonomia_ativada"]
    assert corpo.companhia.diagnostico()["gestos_emitidos"] == 32
    assert len(motores(esp)) == 2


def test_preferencia_explicita_ativa_companhia_usb_sem_motor_ou_passeio():
    _, esp, _, corpo, _, _ = montar(automatico=True)
    assert not corpo.companhia.diagnostico()["ativa"]
    corpo.companhia.processar()
    diag = corpo.companhia.diagnostico()
    assert diag["ativa"] and diag["ativacao_automatica_ao_iniciar"]
    assert diag["origem"] == "configuracao_explicita_de_bancada"
    assert not diag["passeio_ativado"] and not motores(esp)
    corpo.companhia.processar()
    assert not motores(esp)


def test_preferencia_de_passeio_autorizado_inicia_usb_e_anda_apos_pausa():
    _, esp, _, corpo, _, agora = montar(automatico=True, passeio=True)
    retorno = corpo.companhia.processar()
    assert retorno["modo_ativado"] and retorno["passeio_ativado"]
    assert corpo.companhia.diagnostico()["passeio_automatico_ao_iniciar"]
    assert not motores(esp)
    agora[0] += 8.1
    assert corpo.companhia.processar()["ok"]
    assert len(motores(esp)) == 2
    assert corpo.executar("CORPO_PARAR", {})["ok"]
    agora[0] += 20
    corpo.companhia.processar()
    assert not corpo.companhia.diagnostico()["ativa"] and len(motores(esp)) == 2


def test_flag_de_passeio_sem_preferencia_de_companhia_nao_arma_motor():
    _, esp, _, corpo, _, agora = montar(passeio=True)
    agora[0] += 20
    corpo.companhia.processar()
    assert not corpo.companhia.diagnostico()["ativa"] and not motores(esp)


@pytest.mark.parametrize("antes", [True, False])
@pytest.mark.parametrize("passeio", [True, False])
def test_stop_prevalece_sobre_ativacao_automatica_sem_rearme_na_sessao(antes, passeio):
    _, esp, _, corpo, _, _ = montar(automatico=True, passeio=passeio)
    if not antes:
        corpo.companhia.processar()
    assert corpo.executar("CORPO_PARAR", {})["ok"]
    corpo.companhia.processar()
    assert not corpo.companhia.diagnostico()["ativa"] and not motores(esp)


def test_preferencia_aguarda_usb_pronta_sem_conceder_escopo_tcp():
    _, esp, rosto, corpo, _, _ = montar(automatico=True)
    original = rosto.diagnostico
    rosto.diagnostico = lambda: {**original(), "transporte": "tcp"}
    corpo.companhia.processar()
    assert not corpo.companhia.diagnostico()["ativa"] and not motores(esp)
    rosto.diagnostico = original
    corpo.companhia.processar()
    assert corpo.companhia.diagnostico()["ativa"] and not motores(esp)


def test_stop_durante_consulta_da_usb_impede_concessao_automatica():
    _, esp, rosto, corpo, _, _ = montar(automatico=True)
    original = rosto.diagnostico
    def consulta_interrompida():
        corpo.companhia.revogar("parada_solicitada")
        return original()
    rosto.diagnostico = consulta_interrompida
    corpo.companhia.processar()
    assert not corpo.companhia.diagnostico()["ativa"] and not motores(esp)


def test_reconexao_nao_renova_preferencia_consumida_na_mesma_execucao():
    _, esp, rosto, corpo, _, _ = montar(automatico=True)
    corpo.companhia.processar()
    original = rosto.diagnostico
    rosto.diagnostico = lambda: {**original(), "sessao": "nova_sessao"}
    corpo.companhia.processar()
    rosto.diagnostico = original
    corpo.companhia.processar()
    assert not corpo.companhia.diagnostico()["ativa"] and not motores(esp)


@pytest.mark.parametrize("passeio", [False, True])
def test_composicao_instalada_le_preferencia_e_owner_reage_por_cooperacao(tmp_path, passeio):
    import subprocess
    import sys
    programa = r'''
import os
import sys
from pathlib import Path
from pytest import MonkeyPatch
os.environ["LAYLAY_ROSTO_PORTA"] = "OFF"
from mente_laylay.integracao.configuracao_aplicacao import ConfiguracaoAplicacaoRuntime
# Substitui somente a leitura externa da preferência; composição e owners reais.
ConfiguracaoAplicacaoRuntime.companhia_bancada_ao_iniciar = lambda self: True
ConfiguracaoAplicacaoRuntime.passeio_bancada_ao_iniciar = lambda self: sys.argv[2] == "1"
from scripts.tests.test_corpo_motor import _root_instalado
from scripts.tests.test_companhia_corporal import EspCorpo, RostoOledRuntime, emocao, motores
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
with MonkeyPatch.context() as mp:
    root, _, _ = _root_instalado(mp, Path(sys.argv[1]))
    corpo, estado = root._corpo_motor_runtime, root._estado_compartilhado_runtime
    assert corpo.companhia.diagnostico()["ativacao_automatica_ao_iniciar"]
    assert root._composicao_servicos_runtime.catalogo_threads()["Laylay-Companhia-Corporal"].func.__self__ is corpo.companhia
    esp = EspCorpo()
    rosto = RostoOledRuntime(estado_getter=lambda: estado.retrato_dominio("conversacional"),
                            porta="TESTE", abrir_serial=lambda _: esp)
    mp.setattr(corpo, "transporte", rosto)
    assert rosto.sincronizar()
    pergunta = "você consegue usar modo companhia?"
    resposta = root._mapa_habilidades_runtime.responder_pergunta_capacidade(
        pergunta, turno=classificar_modalidade_turno(pergunta))
    assert "preferência salva" in resposta and not motores(esp)
    assert ("passeio também inicia automaticamente" in resposta) is (sys.argv[2] == "1")
    assert not corpo.companhia.diagnostico()["ativa"]
    assert corpo.companhia.processar()["modo_ativado"]
    assert corpo.companhia.diagnostico()["passeio_ativado"] is (sys.argv[2] == "1") and not motores(esp)
    emocao(estado, rosto, "surpresa")
    assert corpo.companhia.processar()["ok"] and len(motores(esp)) == 1
    assert corpo.executar("CORPO_PARAR", {})["ok"]
    corpo.companhia.processar()
    assert not corpo.companhia.diagnostico()["ativa"]
    rosto.encerrar()
'''
    retorno = subprocess.run([sys.executable, "-c", programa, str(tmp_path), "1" if passeio else "0"],
                             capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert retorno.returncode == 0, retorno.stdout[-4000:] + retorno.stderr[-4000:]


def test_falha_motor_automatico_bloqueia_gestos_ate_nova_ativacao():
    estado, esp, rosto, corpo, _, _ = montar(esp=EspCorpo(mack=False), automatico=True)
    corpo.companhia.processar()
    emocao(estado, rosto, "surpresa")
    assert not corpo.companhia.processar()["ok"]
    quantidade = len(motores(esp))
    assert quantidade == 1 and not corpo.companhia.diagnostico()["ativa"]
    esp.mack = True
    corpo.companhia.processar()
    assert not corpo.companhia.diagnostico()["ativa"] and len(motores(esp)) == quantidade


def test_emocao_nova_pode_reagir_depois_de_dois_segundos():
    estado, esp, rosto, corpo, _, agora = montar()
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "triste")
    assert corpo.companhia.processar()["ok"]
    agora[0] += 2.1
    emocao(estado, rosto, "surpresa")
    assert corpo.companhia.processar()["ok"]
    assert len(motores(esp)) == 2


@pytest.mark.parametrize("nome,quantidade", [
    ("alegre", 2), ("triste", 1), ("brava", 4), ("irritada", 2),
    ("surpresa", 1), ("envergonhada", 2), ("debochada", 2),
])
def test_cada_emocao_percorre_rosto_cooperacao_e_todos_os_receipts(nome, quantidade):
    estado, esp, rosto, corpo, quadro, _ = montar()
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, nome)
    assert corpo.companhia.processar()["ok"]
    assert len(motores(esp)) == quantidade
    assert quadro.snapshot()["planos_recentes"][-1]["estado"] == "confirmado"
    assert corpo.companhia.diagnostico()["gestos_emitidos"] == 1
    assert corpo.diagnostico()["autonomia_ativada"]


def test_falha_real_nao_e_silenciada_por_mudanca_simultanea_de_emocao():
    estado, _, rosto, corpo, _, _ = montar(esp=EspCorpo(mack=False))
    falhas = []
    corpo.observar_resultado_cb = falhas.append
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "alegre")
    original = rosto.mover_corpo
    def falhou_e_mudou(*args, **kwargs):
        retorno = original(*args, **kwargs)
        emocao(estado, rosto, "triste")
        return retorno
    rosto.mover_corpo = falhou_e_mudou
    assert not corpo.companhia.processar()["ok"]
    assert len(falhas) == 1 and not corpo.diagnostico()["autonomia_ativada"]


def test_sessao_sem_ttl_nao_permite_proposta_antiga_ou_direcao_fora_do_escopo():
    _, _, _, corpo, _, agora = montar()
    assert ativar(corpo)["ok"]
    meta = {"concessao_id": corpo.companhia._concessao["id"], "proposto_em": agora[0] - 6}
    assert not corpo.companhia._vigente(meta)
    assert corpo.diagnostico()["autonomia_ativada"]
