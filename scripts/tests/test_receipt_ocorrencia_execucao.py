"""Receipt pertence ao turno capturado antes do efeito, não à frase vigente."""

from copy import deepcopy

import pytest

from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.cognicao.contratos_turno import ContratoOcorrenciaTurno
from mente_laylay.cognicao.plano_turno import atualizar_plano_turno
from mente_laylay.integracao.adaptadores_aplicacao_runtime import AdaptadoresAplicacaoRuntime
from mente_laylay.integracao.contexto_execucao_ia import ContextoIntencaoRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.resultado_acao import CHAVE_RESULTADO_OPERACIONAL_PUBLICADO
from scripts.tests.test_publicacao_ocorrencia_turno import _frame, _nova_ocorrencia


DOMINIOS = (
    ("abre a Calculadora", "APP_OPEN", {"nome_app": "Calculadora"}, "app_iniciado_focado"),
    ("liga a lâmpada", "IOT_CONTROL", {"alvo": "lampada_quarto", "acao": "ligar"}, "ligado"),
    ("cria a playlist foco", "PLAYLIST_CREATE", {"nome_playlist": "foco"}, "playlist_criada"),
)


def _montar(texto, *, base_callback=None):
    original = _frame(texto)
    estado = EstadoCompartilhadoRuntime(mental=original)
    consumos = []
    ns = {
        "_estado_compartilhado_runtime": estado,
        "_registrar_resultado_execucao_base": base_callback or (lambda *_a, **_k: consumos.append("base")),
        "_atualizar_plano_turno_mente": atualizar_plano_turno,
        "_concluir_correcao_interpretacao_mente": lambda *_a, **_k: {},
        "_limpar_pergunta_aberta": lambda: consumos.append("limpar"),
        "_suspender_topico_conversacional": lambda *_: consumos.append("suspender"),
        "print": lambda *_: None,
    }
    publicador = AdaptadoresAplicacaoRuntime(lambda: ns)
    servicos = {"_registrar_resultado_execucao": publicador.registrar_resultado_execucao}
    vincular = getattr(publicador, "vincular_registro_resultado_execucao", None)
    if callable(vincular): servicos["_vincular_registro_resultado_execucao"] = vincular
    contexto = ContextoIntencaoRuntime(namespace_getter=lambda: servicos,
        estado_getter=lambda: estado.snapshot()["mental"])
    return estado, publicador, contexto, consumos, original


@pytest.mark.parametrize("texto,intent,params,status", DOMINIOS)
@pytest.mark.parametrize("troca", ("controle", "mesma_frase", "outra_frase", "vazio"))
def test_resultado_da_execucao_antiga_nao_alimenta_plano_e_contexto_do_novo_turno(texto, intent, params, status, troca):
    estado, publicador, contexto, consumos, original = _montar(texto)
    ctx = contexto.montar()
    pedido = {"intent": intent, "params": params, "id_solicitacao": "pedido-capturado"}
    adaptador = AdaptadorResultadoOperacional(pedido, params, texto, "pc_a", ctx)
    if troca != "controle":
        novo = {} if troca == "vazio" else _nova_ocorrencia(original) if troca == "mesma_frase" else _frame("como você está?")
        estado.substituir("mental", novo)
    antes = estado.snapshot()
    adaptador.marcar_resultado(status, True, confirmado=True, evidencia_confirmacao="efeito observado do pedido original")
    mental = estado.snapshot()["mental"]
    if troca == "controle":
        assert consumos == ["base", "limpar", "suspender"]
        assert mental["plano_turno_atual"]["comandos"][0]["id_solicitacao"] == "pedido-capturado"
        assert pedido[CHAVE_RESULTADO_OPERACIONAL_PUBLICADO] == "pedido-capturado"
        assert not mental.get("resultados_execucao_tardios")
    else:
        assert consumos == [], "primeira fronteira: receipt estrangeiro não chega a base/aprendizado/limpadores"
        tardios = mental.pop("resultados_execucao_tardios", [])
        assert mental == antes["mental"], "plano, última ação e pendências vigentes permanecem intactos"
        assert CHAVE_RESULTADO_OPERACIONAL_PUBLICADO not in pedido
        assert adaptador._receipt_publicado is None
        assert len(tardios) == 1, "efeito real tardio deve ficar disponível para reconciliação"
        assert tardios[0]["turno_id"] == str(original["turno_atual"]["id"])
        receipt = tardios[0]["resultado"]
        assert receipt["id_solicitacao"] == "pedido-capturado"
        assert receipt["intent"] == intent and receipt["status"] == status and receipt["confirmado"] is True


@pytest.mark.parametrize("texto,intent,params,status", DOMINIOS)
def test_troca_durante_consumidor_nao_restaura_plano_antigo_no_commit(texto, intent, params, status):
    estado, publicador, contexto, consumos, original = _montar(texto)
    novos = []
    def mudar(*_a, **_k):
        estado.substituir("mental", _nova_ocorrencia(original))
        novos.append(estado.snapshot())
    publicador._ns()["_registrar_resultado_execucao_base"] = mudar
    pedido = {"intent": intent, "id_solicitacao": "pedido-capturado"}
    adaptador = AdaptadorResultadoOperacional(pedido, params, texto, "pc_a", contexto.montar())
    adaptador.marcar_resultado(status, True, confirmado=True)
    atual = estado.snapshot()["mental"]
    assert novos, "a publicação começou legitimamente e alcançou a intercalação"
    atual.pop("resultados_execucao_tardios", None)
    assert atual == novos[-1]["mental"], "commit não pode restaurar plano capturado antes do callback"
    assert consumos == [] and CHAVE_RESULTADO_OPERACIONAL_PUBLICADO not in pedido


def test_origem_do_callback_nao_pode_ser_substituida_por_contexto_do_receipt():
    texto, intent, params, status = DOMINIOS[0]
    estado, _, contexto, consumos, original = _montar(texto)
    ctx = contexto.montar()
    novo = _nova_ocorrencia(original)
    estado.substituir("mental", novo)
    adaptador = AdaptadorResultadoOperacional({"intent": intent}, params, texto, "pc_a", ctx)
    adaptador.marcar_resultado(status, True, confirmado=True,
        contexto_resultado={"turno_id": novo["turno_atual"]["id"], "ocorrencia_turno": {"turno_id": novo["turno_atual"]["id"]}})
    assert consumos == []
    assert estado.obter_copia("mental", "resultados_execucao_tardios")[0]["turno_id"] == str(original["turno_atual"]["id"])


def test_contexto_legado_sem_factory_conserva_callback_original():
    registrar = lambda *_a, **_k: True
    contexto = ContextoIntencaoRuntime(namespace_getter=lambda: {"_registrar_resultado_execucao": registrar}, estado_getter=lambda: {})
    assert contexto.montar()["_registrar_resultado_execucao"] is registrar
