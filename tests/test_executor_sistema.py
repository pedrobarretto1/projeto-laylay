from __future__ import annotations

from types import SimpleNamespace

import pytest

import mente_laylay.autonomia.executor_sistema as modulo_sistema
from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_sistema import (
    DependenciasExecutorSistema,
    executar_intencao_sistema,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao


def _dependencias(eventos: list[tuple]) -> DependenciasExecutorSistema:
    return DependenciasExecutorSistema(
        marcar_resultado=lambda status, **kwargs: eventos.append(("resultado", status, kwargs)),
        falar_por_status=lambda status, fallback, **kwargs: eventos.append(
            ("fala_status", status, fallback, kwargs)
        ),
    )


def test_executor_sistema_nao_interfere_em_outro_dominio() -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_sistema(
        "WEATHER", {}, "pc_a", {}, _dependencias(eventos)
    )

    assert despacho == ResultadoDespacho.nao_tratado()
    assert eventos == []


@pytest.mark.parametrize(
    ("intent", "status"),
    [
        ("SCREEN_CAPTURE", "captura_solicitada"),
        ("GAME_VISION", "analise_visual_solicitada"),
    ],
)
def test_percepcao_preserva_retorno_booleano(intent: str, status: str) -> None:
    eventos: list[tuple] = []
    recebidos: list[object] = []
    argumento = "pc_b" if intent == "SCREEN_CAPTURE" else {"tipo": "item"}

    contexto = (
        {"_executar_captura_tela_intent": lambda valor: recebidos.append(valor) or True}
        if intent == "SCREEN_CAPTURE"
        else {"_registro_visao_jogo_analise_runtime": SimpleNamespace(
            executar=lambda valor: recebidos.append(valor) or True,
        )}
    )
    despacho = executar_intencao_sistema(
        intent,
        argumento if isinstance(argumento, dict) else {},
        argumento if isinstance(argumento, str) else "pc_a",
        contexto,
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert recebidos == [argumento]
    assert eventos == [("resultado", status, {"executou": True})]


def test_falha_visual_continua_retornando_falso_ao_roteador() -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_sistema(
        "GAME_VISION",
        {"tipo": "item"},
        "pc_a",
        {"_registro_visao_jogo_analise_runtime": SimpleNamespace(
            executar=lambda _params: False,
        )},
        _dependencias(eventos),
    )

    assert despacho.tratado is True
    assert despacho.retorno is False
    assert eventos == [("resultado", "falha_execucao", {"executou": False})]


def test_silenciar_remetente_preserva_integracao_gmail() -> None:
    eventos: list[tuple] = []
    silenciados: list[str] = []

    despacho = executar_intencao_sistema(
        "NOTIFICATIONS",
        {"acao": "silenciar_remetente", "remetente": "loja@example.com"},
        "pc_a",
        {
            "_gmail_silenciar_remetente": silenciados.append,
            "falar_com_lipsync": lambda *_args: None,
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert silenciados == ["loja@example.com"]
    assert eventos[0] == ("resultado", "remetente_silenciado", {})


def test_notificacoes_do_windows_continuam_declarando_falta_de_suporte() -> None:
    eventos: list[tuple] = []

    executar_intencao_sistema(
        "NOTIFICATIONS",
        {"acao": "silenciar"},
        "pc_a",
        {"falar_com_lipsync": lambda *_args: None},
        _dependencias(eventos),
    )

    assert eventos[0] == ("resultado", "notificacoes_sem_suporte", {})
    assert eventos[1][0:2] == ("fala_status", "notificacoes_sem_suporte")


def test_notificacoes_usam_central_quando_disponivel() -> None:
    eventos: list[tuple] = []
    recebidos = []

    despacho = executar_intencao_sistema(
        "NOTIFICATIONS",
        {"acao": "ler"},
        "pc_a",
        {
            "falar_com_lipsync": lambda *_args: None,
            "_central_notificacoes_executar": lambda params: (
                recebidos.append(params) or {
                    "ok": True,
                    "status": "notificacoes_lidas",
                    "fala": "Tenho dois avisos importantes.",
                }
            ),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert recebidos == [{"acao": "ler"}]
    assert eventos[0] == (
        "resultado", "notificacoes_lidas", {"executou": True, "confirmado": True},
    )
    assert eventos[1][2] == "Tenho dois avisos importantes."


def test_bloqueio_no_pc_b_preserva_fala_sem_confirmacao_final() -> None:
    eventos: list[tuple] = []
    remotos: list[dict] = []
    falas: list[str] = []

    despacho = executar_intencao_sistema(
        "LOCK_PC",
        {},
        "pc_b",
        {
            "_enviar_pc_b": remotos.append,
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert remotos == [{"action": "lock_pc"}]
    assert "não confirmou" in falas[0]
    assert eventos[0] == ("resultado", "bloqueio_solicitado", {"executou": True})


def test_bloqueio_local_registra_apenas_solicitacao(monkeypatch) -> None:
    eventos: list[tuple] = []
    chamadas: list[bool] = []
    falso_ctypes = SimpleNamespace(
        windll=SimpleNamespace(
            user32=SimpleNamespace(LockWorkStation=lambda: chamadas.append(True))
        )
    )
    monkeypatch.setattr(modulo_sistema, "ctypes", falso_ctypes)

    despacho = executar_intencao_sistema(
        "LOCK_PC", {}, "pc_a", {}, _dependencias(eventos)
    )

    assert despacho == ResultadoDespacho.concluido()
    assert chamadas == [True]
    assert eventos[0] == ("resultado", "bloqueio_solicitado", {"executou": True})


def test_roteador_principal_delega_captura_ao_executor_sistema() -> None:
    resultados = []

    retorno = executar_intencao(
        {"intent": "SCREEN_CAPTURE", "params": {}},
        "tira um print",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_executar_captura_tela_intent": lambda destino: destino == "pc_a",
            "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: resultados.append(
                contrato
            ),
        },
    )

    assert retorno is True
    assert resultados and resultados[0].status == "captura_solicitada"
