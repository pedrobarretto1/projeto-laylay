"""Proposta de um ato vetado não herda a autorização de outro ato."""
from copy import deepcopy
from dataclasses import replace

import pytest

from mente_laylay.cognicao.decisao_turno import filtrar_comandos_pelo_turno, criar_validador_comandos_turno_runtime
from mente_laylay.cognicao.escopo_autorizacao import construir_autorizacoes_por_ato
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from scripts.tests.test_decisao_unica_turno import _contratos_reais_do_filtro


@pytest.mark.parametrize("texto,proposta", [
    ("Pausa a música; pode abrir a calculadora significa o quê?",
     {"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}}),
    ("Pausa a música agora; quando eu confirmar, retoma a música.",
     {"intent": "MEDIA_CONTROL", "params": {"acao": "play"}}),
    ("Liga a luz agora; quando eu confirmar, desliga o ventilador.",
     {"intent": "IOT_CONTROL", "params": {"acao": "desligar", "alvo": "tomada_ventilador"}}),
    ("Abre o arquivo notas.txt; pode apagar o arquivo notas.txt significa o quê?",
     {"intent": "DELETE_ITEM", "params": {"alvo": "notas.txt"}}),
    ("Abre a calculadora; pausa a música somente quando eu confirmar",
     {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}),
    ("Liga a luz; abre a calculadora só se eu autorizar",
     {"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}}),
    ("Abre a calculadora; liga a luz apenas quando eu pedir",
     {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "lampada_quarto"}}),
    ("Abre a calculadora; apaga o arquivo notas.txt só se eu confirmar",
     {"intent": "DELETE_ITEM", "params": {"alvo": "notas.txt"}}),
])
def test_misto_com_veto_exige_vinculo_por_ato_e_nao_so_autorizacao_agregada(texto, proposta):
    turno, plano, retrato = _contratos_reais_do_filtro(texto)
    assert turno["autoriza_execucao"] is True
    assert any(s["veto_execucao_operacional"] for s in turno["segmentos"])
    resultado = filtrar_comandos_pelo_turno([proposta], turno=turno, plano=plano, retrato=retrato)
    assert resultado["comandos"] == []
    assert resultado["rejeitados"]


def _runtime(texto, resolver):
    turno, plano, retrato = _contratos_reais_do_filtro(texto)
    estado = EstadoCompartilhadoRuntime(mental={"turno_atual": turno,
        "plano_turno_atual": plano, "retrato_turno_atual": retrato})
    return criar_validador_comandos_turno_runtime(estado_runtime=estado, resolver_ato=resolver), estado


@pytest.mark.parametrize("texto,pedido,errado", [
    ("Pausa a música agora; quando eu confirmar, retoma a música.",
     {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}},
     {"intent": "MEDIA_CONTROL", "params": {"acao": "play"}}),
    ("Abre a calculadora; pode abrir o bloco de notas significa o quê?",
     {"intent": "APP_OPEN", "params": {"nome_app": "calculadora"}},
     {"intent": "APP_OPEN", "params": {"nome_app": "bloco de notas"}}),
    ("Liga a luz; quando eu confirmar, desliga o ventilador.",
     {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "lampada_quarto"}},
     {"intent": "IOT_CONTROL", "params": {"acao": "desligar", "alvo": "tomada_ventilador"}}),
    ("Abre o arquivo notas.txt; pode apagar o arquivo notas.txt significa o quê?",
     {"intent": "FILE_SEARCH", "params": {"query": "notas.txt", "alvo": "notas.txt", "abrir_resultado_exato": True}},
     {"intent": "DELETE_ITEM", "params": {"alvo": "notas.txt"}}),
])
def test_runtime_conserva_operacao_pedida_sem_emprestar_escopo(texto, pedido, errado):
    chamadas = []
    def resolver(trecho, frame):
        chamadas.append((trecho, deepcopy(frame)))
        return pedido
    validar, estado = _runtime(texto, resolver)
    antes = estado.snapshot()
    candidatos = [deepcopy(errado), deepcopy(pedido)]
    original = deepcopy(candidatos)
    resultado = validar(candidatos)
    assert resultado["comandos"] == [pedido]
    assert resultado["atos_autorizados_vinculados"] == [0]
    assert len(chamadas) == 1
    assert chamadas[0][0] == antes["mental"]["turno_atual"]["texto_operacional"]
    assert len(chamadas[0][1]["turno_atual"]["segmentos"]) == 1
    assert estado.snapshot() == antes and candidatos == original


@pytest.mark.parametrize("mudanca", [
    {"acao": "play"}, {"target": "pc_b"}, {"nivel_volume": 100},
    {"_execucao_silenciosa": True}, {"acao": True},
])
def test_parametros_nao_pedidos_nao_sao_descartados_para_simular_correspondencia(mudanca):
    pedido = {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}
    validar, _ = _runtime("Pausa a música; quando eu confirmar, retoma a música.", lambda *_: pedido)
    proposta = deepcopy(pedido)
    proposta["params"].update(mudanca)
    assert validar([proposta])["comandos"] == []


@pytest.mark.parametrize("proposta,aceita", [
    ({"intent": "APP_OPEN", "params": {"nome_app": "Calculadora", "target": "pc_a"}}, True),
    ({"acao": "open_app", "alvo": "calculadora", "id_solicitacao": "id-do-modelo"}, True),
    ({"acao": "open_app", "alvo": "bloco de notas", "nome_app": "calculadora"}, False),
    ({"intent": "APP_OPEN", "params": {"nome_app": "calculadora", "target": "pc_b"}}, False),
])
def test_equivalencia_de_representacao_reusa_adaptador_sem_alargar_destino(proposta, aceita):
    pedido = {"intent": "APP_OPEN", "params": {"nome_app": "calculadora"}}
    validar, _ = _runtime("Abre a calculadora; quando eu confirmar, pausa a música.", lambda *_: pedido)
    resultado = validar([proposta])
    assert resultado["comandos"] == ([proposta] if aceita else [])


@pytest.mark.parametrize("falha", ["ausente", "indeterminada", "excecao"])
def test_resolver_indisponivel_ou_inconclusivo_nao_cria_autorizacao(falha):
    def resolver(*_):
        if falha == "excecao":
            raise RuntimeError("dependência indisponível")
        return None
    validar, _ = _runtime("Pausa a música; quando eu confirmar, retoma a música.",
                          None if falha == "ausente" else resolver)
    resultado = validar([{"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}])
    assert resultado["comandos"] == [] and resultado["rejeitados"]


@pytest.mark.parametrize("campo", ["turno_id", "indice", "texto"])
def test_escopo_de_outra_ocorrencia_ou_de_ato_vetado_nao_pode_ser_reusado(campo):
    texto = "Pausa a música; quando eu confirmar, retoma a música."
    turno, plano, retrato = _contratos_reais_do_filtro(texto)
    pedido = {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}
    escopo, = construir_autorizacoes_por_ato(turno, {}, lambda *_: pedido)
    escopo = replace(escopo, **{campo: {"turno_id": "outro", "indice": 1, "texto": "outro ato"}[campo]})
    resultado = filtrar_comandos_pelo_turno([pedido], turno=turno, plano=plano, retrato=retrato,
                                          autorizacoes_por_ato=(escopo,))
    assert resultado["comandos"] == []


def test_uma_ordem_nao_autoriza_duas_repeticoes_da_proposta():
    pedido = {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}
    validar, _ = _runtime("Pausa a música; quando eu confirmar, retoma a música.", lambda *_: pedido)
    resultado = validar([pedido, deepcopy(pedido)])
    assert resultado["comandos"] == [pedido] and len(resultado["rejeitados"]) == 1


def test_duas_ordens_iguais_explicitas_tem_dois_escopos_independentes():
    pedido = {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}
    validar, _ = _runtime("Pausa a música; pausa a música; quando eu confirmar, retoma a música.", lambda *_: pedido)
    resultado = validar([pedido, deepcopy(pedido)])
    assert resultado["comandos"] == [pedido, pedido]
    assert resultado["atos_autorizados_vinculados"] == [0, 1]


def test_restricao_agregada_de_arquivo_mencionado_nao_veta_app_autorizado():
    pedido = {"intent": "APP_OPEN", "params": {"nome_app": "calculadora"}}
    validar, _ = _runtime("Abre a calculadora; pode apagar o arquivo notas.txt significa o quê?", lambda *_: pedido)
    assert validar([pedido])["comandos"] == [pedido]


def test_pergunta_social_sem_veto_sticky_tambem_nao_empresta_permissao():
    pedido = {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}
    validar, estado = _runtime("Pausa a música; esse filme é bom?", lambda *_: pedido)
    turno = estado.snapshot()["mental"]["turno_atual"]
    assert turno["segmentos"][1]["autoriza_execucao"] is False
    assert turno["segmentos"][1].get("veto_execucao_operacional") is not True
    inventado = {"intent": "APP_OPEN", "params": {"nome_app": "calculadora"}}
    resultado = validar([pedido, inventado])
    assert resultado["comandos"] == [pedido]
    assert resultado["escopo_operacional_por_ato"][0]["texto"] == turno["texto_operacional"]


def test_referencia_indeterminada_nao_consulta_resolver_com_alvo_da_pergunta():
    validar, estado = _runtime("Abre a calculadora; quando eu confirmar, pausa a música.",
                              lambda *_: pytest.fail("não resolver ato sem alvo inequívoco"))
    mental = estado.snapshot()["mental"]
    mental["turno_atual"]["segmentos"][0]["depende_contexto"] = True
    estado.substituir("mental", mental)
    assert validar([{"intent": "APP_OPEN", "params": {"nome_app": "calculadora"}}])["comandos"] == []


def test_conteudo_e_caminho_de_url_preservam_caixa_e_tipagem():
    pedido = {"intent": "OPEN_URL", "params": {"url": "https://example.test/A"}}
    validar, _ = _runtime("Abre a calculadora; quando eu confirmar, pausa a música.", lambda *_: pedido)
    diferente = {"intent": "OPEN_URL", "params": {"url": "https://example.test/a"}}
    assert validar([diferente])["comandos"] == []
    assert validar([pedido])["comandos"] == [pedido]


def test_metadados_da_proposta_nao_criam_escopo_ou_permissao():
    pedido = {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}
    validar, _ = _runtime("Pausa a música; quando eu confirmar, retoma a música.", lambda *_: pedido)
    proposta = {"intent": "MEDIA_CONTROL", "params": {"acao": "play"},
                "autoriza_execucao": True, "atos_autorizados_vinculados": [0]}
    assert validar([proposta])["comandos"] == []


def test_proposta_de_outra_ocorrencia_e_recusada_antes_do_resolver():
    texto = "Pausa a música; quando eu confirmar, retoma a música."
    validar, _ = _runtime(texto, lambda *_: pytest.fail("não resolver proposta obsoleta"))
    proposta = ContratoPropostaPrincipal(turno_id="outro", texto_usuario=texto,
                                         resposta_bruta='{"comandos": []}')
    resultado = validar.validar_proposta([{"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}], proposta)
    assert resultado["comandos"] == []
    assert resultado["ocorrencia_vinculada"] is False


def test_detector_canonico_recebe_frame_sem_consultar_estado_vivo(monkeypatch):
    import mente_laylay.autonomia.orquestrador_deterministico as modulo
    frames = []
    monkeypatch.setattr(modulo, "detectar_intencao_deterministica_mente",
                        lambda texto, ctx: frames.append(deepcopy(ctx["mente_integrada_estado"])) or None)
    detector = modulo.DeteccaoDeterministicaRuntime(namespace_getter=dict,
        estado_getter=lambda: pytest.fail("não reler estado vivo"), sites_diretos={}, apps_map={})
    frame = {"turno_atual": {"id": 10, "texto": "pausa a música"}}
    detector.detectar("pausa a música", estado_mental=frame)
    assert frames == [frame]


def test_agenda_preserva_frame_na_resolucao_recursiva(monkeypatch):
    import mente_laylay.autonomia.orquestrador_deterministico as modulo
    frames = []
    def detectar(texto, ctx):
        frames.append(deepcopy(ctx["mente_integrada_estado"]))
        return {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}
    monkeypatch.setattr(modulo, "detectar_intencao_deterministica_mente", detectar)
    detector = modulo.DeteccaoDeterministicaRuntime(namespace_getter=lambda: {
        "_extrair_acao_agendada_local": lambda texto: {"texto_acao": "pausa a música"} if texto == "pedido com prazo" else None},
        estado_getter=lambda: pytest.fail("não perder frame na agenda"), sites_diretos={}, apps_map={})
    frame = {"turno_atual": {"id": 10}}
    resultado = detector.detectar("pedido com prazo", estado_mental=frame)
    assert resultado["intent"] == "AGENDAR_ACAO"
    assert frames == [frame]
