from __future__ import annotations

import importlib

import pytest


def _criar_runtime():
    """Carrega o contrato futuro sem transformar ausência em erro de coleta."""

    try:
        modulo = importlib.import_module(
            "mente_laylay.integracao.prioridade_interacao_usuario"
        )
    except ModuleNotFoundError:
        pytest.fail(
            "P1-HC1 RED esperado: owner canônico da interação "
            "do usuário ainda não existe."
        )

    fabrica = getattr(
        modulo,
        "criar_prioridade_interacao_usuario_runtime",
        None,
    )

    assert callable(fabrica), (
        "o módulo existe, mas não publica a fábrica canônica "
        "criar_prioridade_interacao_usuario_runtime"
    )

    return fabrica()


def test_red_p1hc1_claims_sobrepostos_nao_liberam_prioridade_cedo() -> None:
    prioridade = _criar_runtime()

    assert prioridade.ativa() is False

    # ---------------------------------------------------------
    # FASE 1 — captura/VAD possui a interação
    # ---------------------------------------------------------

    claim_vad = prioridade.adquirir("vad")

    assert claim_vad
    assert prioridade.ativa() is True

    # ---------------------------------------------------------
    # HANDOFF VAD -> STT
    #
    # O próximo estágio adquire ANTES de o anterior liberar.
    # ---------------------------------------------------------

    claim_stt = prioridade.adquirir("stt")

    assert claim_stt
    assert claim_stt != claim_vad
    assert prioridade.ativa() is True

    snapshot = prioridade.snapshot()

    assert snapshot["ativa"] is True
    assert snapshot["total_claims"] == 2
    assert set(snapshot["fontes_ativas"]) == {
        "vad",
        "stt",
    }

    # VAD acabou.
    #
    # Isso NÃO significa que a interação acabou:
    # STT ainda possui um claim.
    assert prioridade.liberar(claim_vad) is True
    assert prioridade.ativa() is True

    snapshot = prioridade.snapshot()

    assert snapshot["total_claims"] == 1
    assert set(snapshot["fontes_ativas"]) == {"stt"}

    # ---------------------------------------------------------
    # HANDOFF STT -> entrada agendada
    # ---------------------------------------------------------

    claim_entrada = prioridade.adquirir("entrada_agendada")

    assert prioridade.ativa() is True

    # STT pode terminar sem abrir um buraco.
    assert prioridade.liberar(claim_stt) is True
    assert prioridade.ativa() is True

    snapshot = prioridade.snapshot()

    assert snapshot["total_claims"] == 1
    assert set(snapshot["fontes_ativas"]) == {
        "entrada_agendada",
    }

    # ---------------------------------------------------------
    # HANDOFF entrada -> turno
    # ---------------------------------------------------------

    claim_turno = prioridade.adquirir("turno")

    assert prioridade.ativa() is True

    assert prioridade.liberar(claim_entrada) is True

    # O turno ainda possui a interação.
    assert prioridade.ativa() is True

    snapshot = prioridade.snapshot()

    assert snapshot["total_claims"] == 1
    assert set(snapshot["fontes_ativas"]) == {"turno"}

    # ---------------------------------------------------------
    # ÚNICO ponto onde a interação realmente termina
    # ---------------------------------------------------------

    assert prioridade.liberar(claim_turno) is True

    assert prioridade.ativa() is False

    snapshot = prioridade.snapshot()

    assert snapshot["total_claims"] == 0
    assert snapshot["fontes_ativas"] == []


def test_guard_p1hc1_release_repetido_nao_libera_claim_alheio() -> None:
    prioridade = _criar_runtime()

    claim_vad = prioridade.adquirir("vad")
    claim_stt = prioridade.adquirir("stt")

    assert prioridade.ativa() is True

    assert prioridade.liberar(claim_vad) is True

    # Release duplicado/stale deve ser inofensivo.
    assert prioridade.liberar(claim_vad) is False

    # STT continua mantendo ownership.
    assert prioridade.ativa() is True

    snapshot = prioridade.snapshot()

    assert snapshot["total_claims"] == 1
    assert set(snapshot["fontes_ativas"]) == {"stt"}

    assert prioridade.liberar(claim_stt) is True
    assert prioridade.ativa() is False


def test_guard_p1hc1_mesma_fonte_pode_ter_claims_independentes() -> None:
    prioridade = _criar_runtime()

    # Não podemos assumir que haverá sempre apenas uma operação por fonte.
    #
    # Um simples dict:
    #
    #     {"stt": True}
    #
    # seria insuficiente para representar duas posses independentes.
    claim_a = prioridade.adquirir("stt")
    claim_b = prioridade.adquirir("stt")

    assert claim_a != claim_b

    snapshot = prioridade.snapshot()

    assert snapshot["total_claims"] == 2
    assert set(snapshot["fontes_ativas"]) == {"stt"}

    # Encerrar uma operação STT não encerra a outra.
    assert prioridade.liberar(claim_a) is True
    assert prioridade.ativa() is True

    snapshot = prioridade.snapshot()

    assert snapshot["total_claims"] == 1

    assert prioridade.liberar(claim_b) is True
    assert prioridade.ativa() is False