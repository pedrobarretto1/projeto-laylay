from __future__ import annotations

import pytest

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_informacoes import (
    DependenciasExecutorInformacoes,
    executar_intencao_informacoes,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao


def _dependencias(eventos: list[tuple]) -> DependenciasExecutorInformacoes:
    return DependenciasExecutorInformacoes(
        marcar_resultado=lambda status, **kwargs: eventos.append(("resultado", status, kwargs)),
        falar_por_status=lambda status, fallback, **kwargs: eventos.append(
            ("fala_status", status, fallback, kwargs)
        ),
        registrar_mente=lambda *args: eventos.append(("mente", *args)),
    )


def test_executor_informacoes_nao_interfere_em_outro_dominio() -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_informacoes(
        "VOLUME", {}, "volume em 20", {}, _dependencias(eventos)
    )

    assert despacho == ResultadoDespacho.nao_tratado()
    assert eventos == []


def test_email_read_filtra_prioridade_e_remetente_sem_emitir_proatividade() -> None:
    eventos: list[tuple] = []
    recebidos: list[tuple] = []
    falas: list[str] = []
    emails = [
        {"remetente": "ana@example.com", "prioritario": True},
        {"remetente": "loja@example.com", "prioritario": False},
    ]

    despacho = executar_intencao_informacoes(
        "EMAIL_READ",
        {"prioritarios": True, "remetente": "ana"},
        "leia emails prioritários da Ana",
        {
            "_gmail_nao_lidos_cache": emails,
            "_gmail_falar_resumo_estiloso": lambda itens, **kwargs: recebidos.append(
                (itens, kwargs)
            ) or "Um email importante da Ana.",
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert recebidos == [(
        [{"remetente": "ana@example.com", "prioritario": True}],
        {"somente_prioritarios": True, "emitir_proativa": False},
    )]
    assert falas == ["Um email importante da Ana."]
    assert eventos == [("resultado", "emails_lidos", {})]


@pytest.mark.parametrize("retorno, status", [([], "emails_sincronizados"), (None, "falha_execucao")])
def test_email_sync_valida_tipo_retornado(retorno, status: str) -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_informacoes(
        "EMAIL_SYNC",
        {},
        "sincroniza meus emails",
        {"_gmail_buscar_nao_lidos": lambda: retorno},
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert eventos[0] == ("resultado", status, {"executou": status != "falha_execucao"})


def test_briefing_repeat_registra_fala_retornada_na_memoria() -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_informacoes(
        "BRIEFING_REPEAT",
        {},
        "repete o briefing",
        {"repetir_briefing": lambda: "Hoje está ensolarado."},
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert eventos[0] == (
        "mente",
        "repete o briefing",
        "Hoje está ensolarado.",
        "BRIEFING_REPEAT",
        "briefing do clima",
        "conversa",
        "briefing",
    )
    assert eventos[1] == ("resultado", "briefing_repetido", {})


def test_weather_formata_dados_confirmados_e_registra_consulta() -> None:
    eventos: list[tuple] = []
    falas: list[str] = []

    despacho = executar_intencao_informacoes(
        "WEATHER",
        {"local": "boituva"},
        "como está o tempo em Boituva",
        {
            "obter_clima_localidade": lambda _local: {
                "ok": True,
                "localidade": "boituva",
                "temperatura_c": 21,
                "sensacao_c": 20,
                "descricao": "Ensolarado",
                "umidade": 52,
            },
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert "Boituva" in falas[0]
    assert "21 graus" in falas[0]
    assert eventos == [("resultado", "clima_consultado", {})]


def test_weather_indisponivel_preserva_fala_sem_registrar_sucesso() -> None:
    eventos: list[tuple] = []
    falas: list[str] = []

    despacho = executar_intencao_informacoes(
        "WEATHER",
        {},
        "como está o tempo",
        {
            "cidade_padrao_clima": "Boituva",
            "obter_clima_localidade": lambda _local: {"ok": False},
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert falas and "Boituva" in falas[0]
    assert eventos == []


def test_roteador_principal_delega_weather_ao_executor_informacoes() -> None:
    resultados = []

    retorno = executar_intencao(
        {"intent": "WEATHER", "params": {"local": "Boituva"}},
        "tempo em Boituva",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "obter_clima_localidade": lambda local: {
                "ok": True,
                "localidade": local,
                "temperatura_c": 22,
            },
            "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: resultados.append(
                contrato
            ),
            "falar_com_lipsync": lambda *_args: None,
        },
    )

    assert retorno is True
    assert resultados and resultados[0].status == "clima_consultado"
