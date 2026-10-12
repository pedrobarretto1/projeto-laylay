"""Contrato do corpo no plano original da IA, sem promover contexto a autoridade."""
import json
import pytest

from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal


def instalar_turno(estado, nome="expressar", turno_id="t1"):
    import time
    texto = "gosto de você"
    estado.atualizar_campos("mental",
        turno_atual={"id": turno_id, "retrato_id": turno_id, "texto": texto},
        retrato_turno_atual={"id": turno_id, "texto": texto},
        plano_turno_atual={"id": turno_id, "retrato_id": turno_id, "texto_usuario": texto,
            "decisao_turno": {"turno_id": turno_id}, "fase": "executado", "ts": time.time()})
    return ContratoPropostaPrincipal(turno_id, texto, json.dumps({"fala": "Obrigada!", "intencao_corporal": {"nome": nome}}))


def publicar(estado, proposta):
    from mente_laylay.cognicao.composicao_turno import ComposicaoTurnoRuntime
    from mente_laylay.cognicao.plano_turno import atualizar_plano_turno
    return ComposicaoTurnoRuntime(servicos={"_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": atualizar_plano_turno,
        "_registrar_etapa_turno_mente": lambda trilha, *args, **kw: trilha,
        "print": lambda *args: None}).atualizar_proposta("resposta_planejada", proposta)


def test_writer_canonico_retem_intencao_da_emissao_original():
    from scripts.tests.test_companhia_corporal import montar
    estado, _, rosto, _, _, _ = montar()
    p = instalar_turno(estado)
    plano = estado.obter_copia("mental", "plano_turno_atual", {})
    plano["retrato_corporal"] = {"turno_id": "t1", "sessao": rosto.diagnostico()["sessao"], "concessao_id": "c1"}
    estado.atualizar_campos("mental", plano_turno_atual=plano)
    publicado = publicar(estado, p)
    assert publicado["fase"] == "resposta_planejada", "teste deve alcançar publicação real do plano"
    assert publicado.get("intencao_corporal", {}).get("nome") == "expressar", "primeira fronteira: plano descarta decisão corporal original"


def test_proposta_original_materializa_intencao_finita_vinculada_ao_plano():
    from mente_laylay.cognicao.modelo_corporal import vincular_intencao_corporal
    plano = {"id": "t1", "retrato_corporal": {"turno_id": "t1", "sessao": "s1", "concessao_id": "c1"}}
    p = ContratoPropostaPrincipal("t1", "gosto de você", json.dumps({"fala": "Obrigada!", "intencao_corporal": {"nome": "expressar"}}))
    candidato = vincular_intencao_corporal(plano, p, agora=100)
    assert candidato["nome"] == "expressar" and candidato["turno_id"] == "t1"
    assert candidato["concessao_id"] == "c1" and candidato["autoriza_execucao"] is False
    assert candidato["ate_monotonic"] == 130


@pytest.mark.parametrize("bruto", [
    '{"intencao_corporal":{"nome":"expressar","pwm":255}}',
    '{"intencao_corporal":{"nome":"expressar","autoriza_execucao":true}}',
    '{"intencao_corporal":{"nome":"expressar","nome":"explorar"}}',
    '{"intencao_corporal":{"nome":"andar_360"}}',
    '{"intenção_corporal":{"nome":"expressar"}}',
    'resposta: {"intencao_corporal":{"nome":"expressar"}}',
])
def test_payload_tecnico_ou_reparado_nao_materializa_proposta(bruto):
    from mente_laylay.cognicao.modelo_corporal import vincular_intencao_corporal
    plano = {"id": "t1", "retrato_corporal": {"turno_id": "t1", "sessao": "s1", "concessao_id": "c1"}}
    assert not vincular_intencao_corporal(plano, ContratoPropostaPrincipal("t1", "oi", bruto), agora=100)


def test_plano_sem_retrato_corporal_do_turno_nao_recebe_decisao():
    from mente_laylay.cognicao.modelo_corporal import vincular_intencao_corporal
    p = ContratoPropostaPrincipal("t1", "oi", '{"intencao_corporal":{"nome":"explorar"}}')
    assert not vincular_intencao_corporal({"id": "t2"}, p, agora=100)


def test_retrato_corporal_negocia_json_no_preparador_e_preserva_campo_fora_da_fala():
    from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal
    from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
    from mente_laylay.integracao.llm_http import compactar_payload_llm_local
    instrucao = formatar_modelo_corporal({"origem": "owner_corpo_usb", "conectada": True, "companhia_ativa": True})
    payload = preparar_payload_llm([
        {"role": "system", "content": instrucao},
        {"role": "user", "content": "gosto muito de você"},
    ], model="qwen3-vl:4b", max_tokens=256, endpoint_local=True, contexto_fechado=True)
    assert payload.get("response_format") == {"type": "json_object"}, "intenção precisa nascer no JSON original, sem reparar prosa"
    compacto = compactar_payload_llm_local(payload)
    # O transporte legado retira json_object por compatibilidade; a instrução
    # do ato deve sobreviver inteira. json_schema tem outro contrato próprio.
    assert instrucao in compacto["messages"][-2]["content"]
    assert "fora de fala" in instrucao


@pytest.mark.parametrize("origem,conectada", [("owner_corpo_usb", True), ("owner_corpo_usb", False), ("llm", True)])
def test_reparo_factual_consulta_corpo_real_sem_inventar_sensacoes_ou_intencao(origem, conectada):
    from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
    chamadas = []
    def enviar(mensagens, **kwargs):
        chamadas.append(mensagens)
        return '{"fala":"Gostei do seu carinho, obrigada!","comandos":[]}'
    resultado = preparar_resposta_para_execucao("gosto muito de você",
        '{"fala":"Hoje estou comendo um bolo que o Pedro me deu.","comandos":[]}',
        enviar_mensagem_cb=enviar, limpar_texto_fala_cb=lambda fala: fala,
        fallback_fala="fallback", memoria_sqlite=None, log=lambda _: None,
        contexto_comunicacao={"modelo_corporal": {"origem": origem, "conectada": conectada}})
    assert len(chamadas) == 1, "deve alcançar a reescrita da realidade"
    instrucao = chamadas[0][0]["content"]
    assert "Laylay não tem corpo físico" not in instrucao, "ausência de biologia não prova ausência de hardware"
    assert ("corpo robótico conectado" in instrucao) == (origem == "owner_corpo_usb" and conectada)
    assert "sensações físicas exigem observação" in instrucao
    assert "intencao_corporal" not in instrucao, "reparo não é segunda autora da intenção"
    assert resultado["fala"] == "Gostei do seu carinho, obrigada!"


def preparar_mente(monkeypatch, nome="expressar", passeio=False):
    from types import SimpleNamespace
    from scripts.tests.test_companhia_corporal import montar, ativar, emocao
    from mente_laylay.cognicao import modelo_corporal
    estado, esp, rosto, corpo, quadro, clock = montar()
    assert ativar(corpo)["ok"]
    if passeio:
        with corpo.companhia._lock:
            corpo.companhia._concessao["passeio"] = True
    emocao(estado, rosto, "alegre")
    p = instalar_turno(estado, nome)
    monkeypatch.setattr(modelo_corporal, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    corpo.modelo_para_mente("t1")
    assert publicar(estado, p)["intencao_corporal"]["nome"] == nome
    plano = estado.obter_copia("mental", "plano_turno_atual", {})
    estado.atualizar_campos("mental", plano_turno_atual={**plano, "fase": "executado"})
    monkeypatch.setattr(corpo.companhia, "_aguardar_gesto", lambda ms, validar: validar())
    return estado, esp, rosto, corpo, quadro, clock


def test_proposta_mente_executa_uma_vez_e_devolve_receipt_sem_prova_de_movimento(monkeypatch):
    from scripts.tests.test_companhia_corporal import motores
    estado, esp, rosto, corpo, quadro, clock = preparar_mente(monkeypatch)
    assert corpo.companhia.processar()["ok"]
    p = estado.mental["plano_turno_atual"]["intencao_corporal"]
    assert p["estado"] == "concluida" and p["resultado"]["confirmado"] is True
    assert p["resultado"]["prova_deslocamento"] is False
    assert quadro.snapshot()["planos_recentes"][-1]["metadados"]["turno_id"] == "t1"
    quantidade = len(motores(esp))
    clock[0] += 3
    corpo.companhia.processar()
    assert len(motores(esp)) == quantidade, "uma resposta não permite replay corporal"
    assert corpo.modelo_para_mente("t1")["ultima_experiencia"]["intencao_id"] == p["id"]


@pytest.mark.parametrize("causa", ["troca_turno", "expiracao", "revogacao", "reconexao", "atividade_pc"])
def test_contexto_ou_permissao_substituidos_nao_executam_proposta(monkeypatch, causa):
    from scripts.tests.test_companhia_corporal import motores
    estado, esp, rosto, corpo, _, clock = preparar_mente(monkeypatch)
    corpo.companhia._observado = corpo.companhia._retrato()
    if causa == "troca_turno": instalar_turno(estado, turno_id="t2")
    if causa == "expiracao": clock[0] += 31
    if causa == "revogacao": corpo.companhia.revogar("usuario_parou")
    if causa == "reconexao":
        with corpo.companhia._lock: corpo.companhia._concessao["sessao"] = "outra_sessao"
    if causa == "atividade_pc": estado.atualizar_campos("mental", atividade_operacional={"origem": "atividade_operacional_observada", "ativos": 1})
    antes = len(motores(esp))
    corpo.companhia.processar()
    assert len(motores(esp)) == antes


def test_descansar_escolhido_pela_ia_suspende_passeio_ja_concedido(monkeypatch):
    from scripts.tests.test_companhia_corporal import motores
    _, esp, _, corpo, _, clock = preparar_mente(monkeypatch, "descansar", passeio=True)
    clock[0] += 10
    assert not corpo.companhia.processar()["ok"]
    assert not motores(esp)
    assert corpo.companhia.diagnostico()["intencao"]["nome"] == "descansar"


def test_sucesso_parcial_nao_libera_comemoracao_da_ia(monkeypatch):
    from scripts.tests.test_companhia_corporal import motores
    estado, esp, _, corpo, _, _ = preparar_mente(monkeypatch, "comemorar")
    plano = estado.obter_copia("mental", "plano_turno_atual", {})
    c = {"id_solicitacao": "a", "origem": "executor", "executou": True, "confirmado": True, "evidencia_confirmacao": "estado_lido"}
    estado.atualizar_campos("mental", plano_turno_atual={**plano, "comandos": [c, {**c, "id_solicitacao": "b", "confirmado": False}]})
    assert not corpo.companhia.processar()["ok"] and not motores(esp)
    estado.atualizar_campos("mental", plano_turno_atual={**plano, "comandos": [c]})
    assert corpo.companhia.processar()["ok"]


def test_falha_no_rosto_nao_confirma_motor_e_volta_a_mente(monkeypatch):
    from scripts.tests.test_presenca_corporal_v2 import EspPresenca
    from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
    from scripts.tests.test_companhia_corporal import montar, motores, emocao
    from types import SimpleNamespace
    from mente_laylay.cognicao import modelo_corporal
    estado, esp, rosto, antigo, quadro, clock = montar(esp=EspPresenca())
    corpo = CorpoMotorRuntime(transporte=rosto, estado=estado, perfil_corporal="rodas_suspensas", companhia_bancada_ao_iniciar=True, monotonic=lambda: clock[0])
    corpo.companhia.coordenador = antigo.companhia.coordenador
    corpo.companhia.coordenador.governanca.registrar_autorizador_escopo("corpo_companhia", corpo.companhia.autorizar_escopo)
    assert corpo.companhia.processar()["ok"]
    emocao(estado, rosto, "alegre")
    p = instalar_turno(estado)
    monkeypatch.setattr(modelo_corporal, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    corpo.modelo_para_mente("t1")
    publicar(estado, p)
    plano = estado.obter_copia("mental", "plano_turno_atual", {})
    estado.atualizar_campos("mental", plano_turno_atual={**plano, "fase": "executado"})
    esp.eack = False
    assert not corpo.companhia.processar()["ok"] and not motores(esp)
    assert estado.mental["experiencia_corporal"]["confirmado"] is False
    assert estado.mental["plano_turno_atual"]["intencao_corporal"]["estado"] == "interrompida"
    assert quadro.snapshot()["planos_recentes"][-1]["estado"] != "confirmado"


def test_resultado_tardio_nao_conclui_plano_novo(monkeypatch):
    estado, _, _, corpo, _, _ = preparar_mente(monkeypatch)
    proposta = estado.obter_copia("mental", "plano_turno_atual", {})["intencao_corporal"]
    instalar_turno(estado, turno_id="t2")
    corpo.companhia._devolver_experiencia(proposta, {"ok": True}, [{"ok": True, "aplicacao_pwm_confirmada": True, "parada_confirmada": True}])
    assert "intencao_corporal" not in estado.mental["plano_turno_atual"]
    assert estado.mental["experiencia_corporal"]["turno_id"] == "t1"
    assert estado.mental["experiencia_corporal"]["pertence_ao_turno_atual"] is False


def test_composicao_real_injeta_retrato_no_prompt_e_vincula_na_mesma_transacao(tmp_path):
    import subprocess, sys, os
    codigo = f'''
from mente_laylay.integracao import instancia_unica
adquirir=instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica=lambda _:adquirir({str(tmp_path/'instancia')!r})
import laylay
from scripts.tests.test_corpo_na_mente import instalar_turno
from scripts.tests.test_presenca_corporal_v2 import EspPresenca
from scripts.tests.test_rosto_oled import estado_emocional
from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
estado=laylay._estado_compartilhado_runtime
corpo=laylay._corpo_motor_runtime
esp=EspPresenca()
rosto=RostoOledRuntime(estado_getter=lambda:estado.retrato_dominio("conversacional"),porta="TESTE",abrir_serial=lambda _:esp)
corpo.transporte=rosto
assert rosto.sincronizar()
assert corpo.companhia.processar()["ok"]
estado.substituir("conversacional",estado_emocional("alegre"))
assert rosto.sincronizar()
p=instalar_turno(estado)
pacote=laylay._contexto_prompt_runtime.preparar_pacote(p.texto_usuario)
assert "MEU CORPO AGORA" in pacote.prompt_sistema
assert "intencao_corporal" in pacote.prompt_sistema
assert "MEU CORPO AGORA" in laylay._contexto_prompt_runtime.preparar_instrucao_rapida(p.texto_usuario)
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
from mente_laylay.integracao.llm_http import compactar_payload_llm_local
mensagens=list(pacote.mensagens)+[{{"role":"user","content":p.texto_usuario}}]
payload=preparar_payload_llm(mensagens,model="qwen3-vl:4b",max_tokens=256,endpoint_local=True)
assert payload["response_format"]=={{"type":"json_object"}}
compacto=compactar_payload_llm_local(payload)
assert "MEU CORPO AGORA" in compacto["messages"][-2]["content"]
assert "fora de fala" in compacto["messages"][-2]["content"]
plano=laylay._composicao_turno_runtime.atualizar_proposta("resposta_planejada",p)
assert plano["intencao_corporal"]["sessao"]==rosto.diagnostico()["sessao"]
assert plano["retrato_corporal"]["companhia_ativa"] is True
assert corpo.companhia.coordenador is laylay._orquestrador_cooperativo_runtime
assert corpo.companhia.coordenador.governanca.registrar_aprendizado is not None
assert "intenção corporal" in laylay._mapa_habilidades_runtime.contexto_para_prompt("como controla seu corpo e seus motores?")
corpo.companhia.revogar("fim_teste")
rosto.encerrar()
'''
    env = dict(os.environ, LAYLAY_CORPO_PERFIL="rodas_suspensas", LAYLAY_CORPO_COMPANHIA_AO_INICIAR="1", LAYLAY_CORPO_WIFI_CONFIG=str(tmp_path/"sem_wifi.json"))
    r = subprocess.run([sys.executable, "-"], input=codigo, text=True, capture_output=True, env=env, timeout=40)
    assert r.returncode == 0, r.stdout+r.stderr
