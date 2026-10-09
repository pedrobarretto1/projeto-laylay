"""Receipts aceitos alimentam a emoção antes e independentemente da fala."""

from __future__ import annotations

import time

import pytest

from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.emocoes.avaliador_eventos import AvaliadorEventosEmocionaisRuntime
from mente_laylay.memoria_mental.resultado_acao import CHAVE_RESULTADO_OPERACIONAL_PUBLICADO


def _adaptador(intent, ctx, *, identidade="pedido", alvo="alvo"):
    return AdaptadorResultadoOperacional(
        {"intent": intent, "id_solicitacao": identidade},
        {"alvo": alvo}, f"execute a ação em {alvo}", "pc_a", ctx,
    )


@pytest.mark.parametrize("intent, sucesso", [
    ("CREATE_FILE", "conteudo_atualizado"), ("APP_OPEN", "app_iniciado_focado"),
])
def test_receipts_sem_chamar_fala_alimentam_falha_repetida_e_recuperacao(intent, sucesso):
    avaliador = AvaliadorEventosEmocionaisRuntime(log=lambda *_: None)
    publicados = []
    observados = []

    def observar(receipt):
        observados.append(receipt)
        assert publicados[-1].id_solicitacao == receipt.id_solicitacao
        return avaliador.avaliar(receipt)

    ctx = {"_registrar_resultado_execucao": lambda receipt, *_a, **_k: publicados.append(receipt),
           "_avaliar_evento_emocional_operacional": observar}
    for numero in (1, 2):
        adaptador = _adaptador(intent, ctx, identidade=f"falha-{numero}")
        adaptador.marcar_resultado("falha_execucao", False, confirmado=False)
        assert len(observados) == numero
    assert avaliador.diagnostico()["ultima"]["arco"] == "irritacao_compartilhada"
    recuperacao = _adaptador(intent, ctx, identidade="recuperacao")
    recuperacao.marcar_resultado(sucesso, True, confirmado=True)
    assert avaliador.diagnostico()["ultima"]["arco"] == "alivio"
    assert observados[-1].origem == "executor"
    assert observados[-1].confirmado is True


@pytest.mark.parametrize("publicacao", ["ausente", "recusada", "erro"])
def test_publicacao_sem_aceitacao_nao_alimenta_avaliador_nem_fala(publicacao):
    observados = []
    ctx = {"_avaliar_evento_emocional_operacional": lambda receipt: observados.append(receipt),
           "falar_com_lipsync": lambda *_: None, "modo_jogo_ativo": True}
    if publicacao == "recusada":
        ctx["_registrar_resultado_execucao"] = lambda *_a, **_k: False
    elif publicacao == "erro":
        def registrar(*_a, **_k):
            raise RuntimeError("publicação indisponível")
        ctx["_registrar_resultado_execucao"] = registrar
    adaptador = _adaptador("APP_OPEN", ctx)
    adaptador.marcar_resultado("falha_execucao", False, confirmado=False)
    assert observados == []
    adaptador.falar_por_status("falha_execucao", "Não consegui abrir.", alvo="alvo")
    assert observados == []
    assert CHAVE_RESULTADO_OPERACIONAL_PUBLICADO not in adaptador.resultado


def test_fala_correlacionada_consume_avaliacao_sem_reavaliar_ou_renovar_ttl():
    avaliador = AvaliadorEventosEmocionaisRuntime(log=lambda *_: None)
    observados = []
    entregas = []

    def observar(receipt):
        observados.append(receipt)
        return avaliador.avaliar(receipt)

    ctx = {"_registrar_resultado_execucao": lambda *_a, **_k: None,
           "_avaliar_evento_emocional_operacional": observar,
           "falar_com_lipsync": lambda *_: None, "modo_jogo_ativo": True,
           "_falar_resultado_operacional": lambda *args: entregas.append(args)}
    adaptador = _adaptador("APP_OPEN", ctx)
    adaptador.marcar_resultado("falha_execucao", False, confirmado=False)
    assert len(observados) == 1
    for _ in range(2):
        adaptador.falar_por_status("falha_execucao", "Não consegui abrir.", alvo="alvo")
    assert len(observados) == 1
    assert avaliador.diagnostico()["historico_efemero"] == 1
    eventos = [entrega[0].contexto["avaliacao_evento"] for entrega in entregas]
    assert eventos[0] == eventos[1]
    assert eventos[0]["validade"]["expira_ts"] == eventos[1]["validade"]["expira_ts"]


@pytest.mark.parametrize("divergencia", ["alvo", "status", "identidade"])
def test_fala_estrangeira_nao_observa_nem_herda_avaliacao_publicada(divergencia):
    entregas = []
    avaliador = AvaliadorEventosEmocionaisRuntime(log=lambda *_: None)
    ctx = {"_registrar_resultado_execucao": lambda *_a, **_k: None,
           "_avaliar_evento_emocional_operacional": avaliador.avaliar,
           "falar_com_lipsync": lambda *_: None, "modo_jogo_ativo": True,
           "_falar_resultado_operacional": lambda *args: entregas.append(args)}
    adaptador = _adaptador("APP_OPEN", ctx)
    adaptador.marcar_resultado("falha_execucao", False, confirmado=False)
    if divergencia == "identidade":
        adaptador.resultado["id_solicitacao"] = "pedido-estrangeiro"
    adaptador.falar_por_status(
        "app_aberto" if divergencia == "status" else "falha_execucao",
        "Resultado observado.", alvo="outro" if divergencia == "alvo" else "alvo",
    )
    assert avaliador.diagnostico()["avaliados"] == 1
    assert not entregas[0][0].contexto.get("avaliacao_evento")


def test_avaliacao_injetada_no_contexto_nao_vira_prova_do_observador():
    entregas = []
    ctx = {"_registrar_resultado_execucao": lambda *_a, **_k: None,
           "falar_com_lipsync": lambda *_: None, "modo_jogo_ativo": True,
           "_falar_resultado_operacional": lambda *args: entregas.append(args)}
    adaptador = _adaptador("APP_OPEN", ctx)
    adaptador.marcar_resultado(
        "falha_execucao", False, confirmado=False,
        contexto_resultado={"avaliacao_evento": {"permite_expressao": True,
                                               "emocao": "brava", "ts": time.time()}},
    )
    adaptador.falar_por_status("falha_execucao", "Não consegui abrir.", alvo="alvo")
    assert not entregas[0][0].contexto.get("avaliacao_evento")


def test_falha_do_observador_nao_muda_receipt_aceito_nem_inventa_evento():
    publicados = []
    entregas = []

    def observar(receipt):
        receipt.alvo = "outro"
        receipt.confirmado = True
        raise RuntimeError("observador indisponível")

    ctx = {"_registrar_resultado_execucao": lambda receipt, *_a, **_k: publicados.append(receipt),
           "_avaliar_evento_emocional_operacional": observar,
           "falar_com_lipsync": lambda *_: None, "modo_jogo_ativo": True,
           "_falar_resultado_operacional": lambda *args: entregas.append(args)}
    adaptador = _adaptador("APP_OPEN", ctx)
    adaptador.marcar_resultado("falha_execucao", False, confirmado=False)
    assert publicados[0].alvo == "alvo" and publicados[0].confirmado is False
    assert adaptador.resultado[CHAVE_RESULTADO_OPERACIONAL_PUBLICADO] == adaptador.id_solicitacao
    adaptador.falar_por_status("falha_execucao", "Não consegui abrir.", alvo="alvo")
    fala = entregas[0][0]
    assert fala.origem == "executor" and fala.alvo == "alvo" and fala.confirmado is False
    assert "avaliacao_evento" not in fala.contexto


def test_mutacao_tardia_da_avaliacao_nao_substitui_copia_da_publicacao():
    avaliacao = {"diagnostico": {"origem": "observador"}}
    entregas = []
    ctx = {"_registrar_resultado_execucao": lambda *_a, **_k: None,
           "_avaliar_evento_emocional_operacional": lambda _: avaliacao,
           "falar_com_lipsync": lambda *_: None, "modo_jogo_ativo": True,
           "_falar_resultado_operacional": lambda *args: entregas.append(args)}
    adaptador = _adaptador("APP_OPEN", ctx)
    adaptador.marcar_resultado("falha_execucao", False, confirmado=False)
    avaliacao["diagnostico"]["origem"] = "alterada"
    adaptador.falar_por_status("falha_execucao", "Não consegui abrir.", alvo="alvo")
    assert entregas[0][0].contexto["avaliacao_evento"]["diagnostico"]["origem"] == "observador"
