from __future__ import annotations

import pytest

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_audio import (
    DependenciasExecutorAudio,
    executar_intencao_audio,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao


def _dependencias(eventos: list[tuple]) -> DependenciasExecutorAudio:
    return DependenciasExecutorAudio(
        marcar_resultado=lambda status, **kwargs: eventos.append(("resultado", status, kwargs)),
        falar_por_status=lambda status, fallback, **kwargs: eventos.append(
            ("fala_status", status, fallback, kwargs)
        ),
    )


def test_executor_audio_nao_interfere_em_outro_dominio() -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_audio(
        "APP_OPEN", {}, "pc_a", {}, _dependencias(eventos)
    )

    assert despacho == ResultadoDespacho.nao_tratado()
    assert eventos == []


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [(40, 40), ("75", 75), (0.5, 50)],
)
def test_volume_absoluto_local_preserva_conversao(entrada, esperado: int) -> None:
    eventos: list[tuple] = []
    niveis: list[int] = []

    despacho = executar_intencao_audio(
        "VOLUME",
        {"acao": "set", "nivel_volume": entrada},
        "pc_a",
        {"ajustar_volume_sistema": lambda nivel: niveis.append(nivel)},
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert niveis == [esperado]
    assert eventos[0] == ("resultado", "volume_ajustado", {"executou": True})
    assert str(esperado) in eventos[1][2]


@pytest.mark.parametrize(
    ("acao", "delta", "status"),
    [("aumentar", 10, "volume_aumentado"), ("baixar", -10, "volume_baixado")],
)
def test_volume_relativo_local_preserva_delta(acao: str, delta: int, status: str) -> None:
    eventos: list[tuple] = []
    deltas: list[int] = []

    despacho = executar_intencao_audio(
        "VOLUME",
        {"acao": acao},
        "pc_a",
        {"ajustar_volume_sistema_relativo": deltas.append},
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert deltas == [delta]
    assert eventos[0] == ("resultado", status, {"executou": True})


def test_mudo_local_respeita_confirmacao_real_do_backend() -> None:
    eventos: list[tuple] = []
    chamadas: list[bool] = []

    despacho = executar_intencao_audio(
        "VOLUME",
        {"acao": "mudo"},
        "pc_a",
        {"definir_mudo_sistema": lambda ativar: chamadas.append(ativar) or False},
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert chamadas == [True]
    assert eventos[0] == ("resultado", "falha_execucao", {"executou": False})


@pytest.mark.parametrize(
    ("params", "payload", "status"),
    [
        ({"acao": "up"}, {"action": "volume_up", "delta": 10}, "volume_aumentado"),
        ({"acao": "mute"}, {"action": "set_volume", "nivel": 0}, "volume_mudo"),
        ({"acao": "unmute"}, {"action": "volume_unmute"}, "volume_desmutado"),
        ({"nivel_volume": 35}, {"action": "set_volume", "nivel": 35}, "volume_ajustado"),
    ],
)
def test_volume_no_pc_b_preserva_protocolos(params: dict, payload: dict, status: str) -> None:
    eventos: list[tuple] = []
    remotos: list[dict] = []

    despacho = executar_intencao_audio(
        "VOLUME",
        params,
        "pc_b",
        {"_enviar_pc_b": remotos.append},
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert remotos == [payload]
    assert eventos[0] == ("resultado", status, {"executou": True})


def test_roteador_principal_delega_volume_ao_executor_audio() -> None:
    niveis: list[int] = []
    resultados = []

    retorno = executar_intencao(
        {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": 42}},
        "coloca o volume em 42",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "ajustar_volume_sistema": niveis.append,
            "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: resultados.append(
                contrato
            ),
            "falar_com_lipsync": lambda *_args: None,
        },
    )

    assert retorno is True
    assert niveis == [42]
    assert resultados and resultados[0].status == "volume_ajustado"
