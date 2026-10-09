"""Identidade do pedido protege a evidência na republicação do plano."""

from __future__ import annotations

from copy import deepcopy
import json
import time
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.autonomia.dispatcher_comandos_json import executar_comandos_json
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.orquestrador_turno_runtime import atualizar_planejamento_turno
from mente_laylay.cognicao.plano_turno import atualizar_plano_turno, planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo
from mente_laylay.integracao.adaptadores_aplicacao_runtime import AdaptadoresAplicacaoRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.trilha_turno import registrar_etapa_turno


INTENTS = ("PLAYLIST_CREATE", "IOT_CONTROL", "APP_OPEN")


def _estado(comandos: list[dict]) -> EstadoCompartilhadoRuntime:
    texto = "abre a Calculadora e o Bloco de Notas"
    turno = classificar_modalidade_turno(texto)
    retrato, _ = construir_retrato_turno(texto, turno=turno, mente={}, contexto_perceptivo={})
    turno["retrato_id"] = retrato["id"]
    plano = atualizar_plano_turno(planejar_turno(texto, turno=turno, mente={}), fase="executado", comandos=comandos)
    return EstadoCompartilhadoRuntime(mental={
        "turno_atual": turno, "retrato_turno_atual": retrato, "plano_turno_atual": plano,
    })


def _publicar(estado: EstadoCompartilhadoRuntime, comandos: list[dict]) -> dict:
    return atualizar_planejamento_turno(lambda: {
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": atualizar_plano_turno,
        "_registrar_etapa_turno_mente": registrar_etapa_turno,
        "time": time, "print": lambda *_args: None,
    }, "executado", comandos=comandos)


def _receipt(intent: str, identidade: str, alvo: str, *, confirmado: bool = True) -> dict:
    return {
        "id_solicitacao": identidade, "intent": intent, "alvo": alvo,
        "params": {"alvo": alvo}, "origem": "executor",
        "status": "sucesso" if confirmado else "falha_execucao",
        "executou": confirmado, "confirmado": confirmado,
        "evidencia_confirmacao": "receipt de " + alvo if confirmado else "",
    }


@pytest.mark.parametrize("intent", INTENTS)
def test_republicacao_preserva_receipts_distintos_da_mesma_intencao(intent: str) -> None:
    estado = _estado([_receipt(intent, "req-a", "primeiro"), _receipt(intent, "req-b", "segundo", confirmado=False)])
    antes = estado.obter_copia("mental", "plano_turno_atual")["comandos"]
    publicado = _publicar(estado, [{"id_solicitacao": "req-b", "intent": intent, "params": {"alvo": "segundo"}}])
    assert [item["id_solicitacao"] for item in publicado["comandos"]] == ["req-a", "req-b"], "a primeira fronteira não pode colapsar ocorrências pela intent"
    assert publicado["comandos"] == antes


@pytest.mark.parametrize("intent", INTENTS)
@pytest.mark.parametrize("identidade", ["req-nova", ""])
def test_outro_pedido_nao_herda_confirmacao_e_evidencia_por_intencao(intent: str, identidade: str) -> None:
    estado = _estado([_receipt(intent, "req-confirmada", "primeiro")])
    anterior = estado.obter_copia("mental", "plano_turno_atual")["comandos"][0]
    publicado = _publicar(estado, [{"id_solicitacao": identidade, "intent": intent, "alvo": "segundo"}])
    assert len(publicado["comandos"]) == 2, "receipt anterior e pedido novo têm identidades independentes"
    assert publicado["comandos"][0] == anterior
    novo = publicado["comandos"][1]
    assert not novo["status"] and novo["executou"] is None and novo["confirmado"] is None
    assert not novo["evidencia_confirmacao"]


@pytest.mark.parametrize("intent", INTENTS)
def test_mesma_ocorrencia_preserva_evidencia_omitida_sem_mover_receipt(intent: str) -> None:
    estado = _estado([_receipt(intent, "req-a", "primeiro"), _receipt("NOTIFICATIONS", "req-b", "avisos")])
    antes = estado.obter_copia("mental", "plano_turno_atual")["comandos"]
    publicado = _publicar(estado, [{"request_id": "req-a", "intent": intent}])
    assert publicado["comandos"] == antes


@pytest.mark.parametrize("intent", INTENTS)
def test_pedidos_legados_de_alvos_distintos_nao_compartilham_receipt(intent: str) -> None:
    estado = _estado([_receipt(intent, "", "primeiro")])
    publicado = _publicar(estado, [{"intent": intent, "alvo": "segundo"}])
    assert len(publicado["comandos"]) == 2
    assert publicado["comandos"][0]["confirmado"] is True
    assert publicado["comandos"][1]["confirmado"] is None


@pytest.mark.parametrize("comando", [
    {"acao": "open_app", "alvo": "Calculadora"},
    {"acao": "ligar", "alvo": "lampada_quarto"},
    {"acao": "open_url", "alvo": "https://example.test"},
    {"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}},
])
def test_dispatcher_transporta_identidade_top_level_ate_receipt(comando: dict) -> None:
    comando = dict(comando, id_solicitacao="pedido-validado")
    receipts = []
    pedidos = []

    def executar(pedido: dict, texto: str) -> bool:
        pedidos.append(deepcopy(pedido))
        adaptador = AdaptadorResultadoOperacional(pedido, pedido["params"], texto, "pc_a", {
            "_registrar_resultado_execucao": lambda receipt, *_args, **_kwargs: receipts.append(receipt),
        })
        adaptador.marcar_resultado("sucesso", executou=True, confirmado=True)
        return True

    executar_comandos_json({"executar_intencao": executar}, "executa o pedido", [comando], "", "comando", False, False, False)
    assert pedidos and receipts, "a sonda precisa chegar ao executor e à publicação real"
    assert pedidos[0].get("id_solicitacao") == "pedido-validado"
    assert "id_solicitacao" not in pedidos[0]["params"] and "request_id" not in pedidos[0]["params"]
    assert receipts[0].id_solicitacao == "pedido-validado"


def test_dispatcher_recusa_aliases_divergentes_sem_executar_fallback() -> None:
    chamados = []
    resultado = executar_comandos_json({
        "executar_intencao": lambda *_args: chamados.append("canonico"),
        "_executar_comando_conteudo": lambda *_args: chamados.append("legado"),
    }, "abre a Calculadora", [{
        "acao": "open_app", "alvo": "Calculadora",
        "id_solicitacao": "pedido-a", "request_id": "pedido-b",
    }], "", "comando", False, False, False)
    assert resultado["erros"] and chamados == []


def _publicador_resultado(estado: EstadoCompartilhadoRuntime, publicados: list) -> AdaptadoresAplicacaoRuntime:
    return AdaptadoresAplicacaoRuntime(lambda: {
        "_estado_compartilhado_runtime": estado,
        "_registrar_resultado_execucao_base": lambda *_args, **_kwargs: publicados.append("base"),
        "_atualizar_plano_turno_mente": atualizar_plano_turno,
        "_concluir_correcao_interpretacao_mente": lambda *_args, **_kwargs: {},
        "print": lambda *_args: None,
    })


def test_publicador_receipt_recusa_mesmo_id_com_intencao_divergente() -> None:
    estado = _estado([_receipt("APP_OPEN", "req-a", "Calculadora")])
    antes = estado.snapshot()
    publicados = []
    retorno = _publicador_resultado(estado, publicados).registrar_resultado_execucao(
        _receipt("IOT_CONTROL", "req-a", "lampada_quarto"),
        "abre a Calculadora e o Bloco de Notas",
    )
    assert estado.snapshot() == antes, "ID igual não torna intenções diferentes a mesma ocorrência"
    assert publicados == [], "recusar vínculo antes de alimentar consumidores de receipt"
    assert retorno is False, "a recusa deve alcançar o chamador"


def test_adaptador_nao_certifica_receipt_recusado_pelo_publicador_real() -> None:
    estado = _estado([_receipt("APP_OPEN", "req-a", "Calculadora")])
    antes = estado.snapshot()
    publicador = _publicador_resultado(estado, [])
    pedido = {"intent": "IOT_CONTROL", "id_solicitacao": "req-a",
              "params": {"alvo": "lampada_quarto"}}
    adaptador = AdaptadorResultadoOperacional(pedido, pedido["params"],
        "abre a Calculadora e o Bloco de Notas", "pc_a", {
            "_registrar_resultado_execucao": publicador.registrar_resultado_execucao,
        })
    adaptador.marcar_resultado("ligado", True, confirmado=True)
    assert estado.snapshot() == antes
    assert adaptador._receipt_publicado is None
    assert not pedido.get("_laylay_resultado_operacional_publicado")


def test_publicador_receipt_sem_id_preserva_ocorrencias_legadas_independentes() -> None:
    estado = _estado([_receipt("APP_OPEN", "", "Calculadora")])
    _publicador_resultado(estado, []).registrar_resultado_execucao(
        _receipt("APP_OPEN", "", "Bloco de Notas", confirmado=False),
        "abre a Calculadora e o Bloco de Notas",
    )
    comandos = estado.obter_copia("mental", "plano_turno_atual")["comandos"]
    assert len(comandos) == 2
    assert [item["confirmado"] for item in comandos] == [True, False]


def test_publicador_nova_falha_na_mesma_ocorrencia_nao_herda_evidencia_de_sucesso() -> None:
    estado = _estado([_receipt("APP_OPEN", "req-a", "Calculadora")])
    _publicador_resultado(estado, []).registrar_resultado_execucao(
        _receipt("APP_OPEN", "req-a", "Calculadora", confirmado=False),
        "abre a Calculadora e o Bloco de Notas",
    )
    comandos = estado.obter_copia("mental", "plano_turno_atual")["comandos"]
    assert len(comandos) == 1 and comandos[0]["confirmado"] is False
    assert comandos[0]["evidencia_confirmacao"] != "receipt de Calculadora"


def test_publicador_novo_resultado_incerto_nao_herda_confirmacao_anterior() -> None:
    estado = _estado([_receipt("APP_OPEN", "req-a", "Calculadora")])
    resultado = dict(_receipt("APP_OPEN", "req-a", "Calculadora"),
                     status="comando_enviado", executou=True, confirmado=None,
                     evidencia_confirmacao="aguardando observação")
    _publicador_resultado(estado, []).registrar_resultado_execucao(
        resultado, "abre a Calculadora e o Bloco de Notas",
    )
    comandos = estado.obter_copia("mental", "plano_turno_atual")["comandos"]
    assert len(comandos) == 1 and comandos[0]["confirmado"] is None
    assert comandos[0]["status"] == "comando_enviado"


def test_runtime_identifica_copias_apos_validacao_sem_reutilizar_id_do_modelo() -> None:
    fonte = [{"acao": "open_app", "alvo": alvo, "id_solicitacao": "id-do-modelo", "request_id": "id-do-modelo"}
             for alvo in ("Calculadora", "Bloco de Notas")]
    original = deepcopy(fonte)
    observados = {}

    def validar(comandos: list[dict]) -> dict:
        observados["validados"] = deepcopy(comandos)
        return {"comandos": fonte}

    def publicar(fase: str, **campos) -> dict:
        observados[fase] = deepcopy(campos.get("comandos"))
        return {"fase": fase}

    def dispatch(_ctx, _texto, comandos, *_args) -> dict:
        observados["dispatch"] = deepcopy(comandos)
        return {"erros": []}

    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "usar_modo_rapido": lambda _texto: False,
        "preparacao_conversa": SimpleNamespace(preparar_pacote=lambda _texto: PacotePrompt(())),
        "modelo_llm": SimpleNamespace(executar=lambda _pedido: ResultadoModelo(json.dumps({"fala": "Vou verificar.", "comandos": fonte}), True)),
        "preparar_resposta": lambda _texto, bruto: json.loads(bruto),
        "validar_comandos_planejados": validar,
        "atualizar_plano_turno": publicar,
        "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {}),
        "executar_comandos_json": dispatch,
        "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {}),
        "finalizar_execucao": lambda *_args: {},
    }, log=lambda *_args: None)
    runtime.processar("abre a Calculadora e o Bloco de Notas")
    assert observados["validados"] == original, "identidade host só nasce após validação"
    assert fonte == original, "não mutar a proposta nem a lista devolvida pelo validador"
    ids = [item.get("id_solicitacao") for item in observados["resposta_planejada"]]
    assert len(set(ids)) == 2 and all(ids) and "id-do-modelo" not in ids
    assert all("request_id" not in item for item in observados["dispatch"])
    assert observados["resposta_planejada"] == observados["dispatch"] == observados["executado"]
