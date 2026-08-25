from __future__ import annotations

from mente_laylay.autonomia import executor_janelas
from mente_laylay.autonomia.executor_janelas import (
    DependenciasExecutorJanelas,
    executar_intencao_janelas,
)
from mente_laylay.autonomia.habilidade_janelas import executar_habilidade_janelas


def _contexto_store(resolver, aberturas: list[str]) -> dict:
    return {
        "APPS_MAP": {"microsoft store": "ms-windows-store:"},
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "_resolver_alvo_ambiente": resolver,
        "abrir_programa": lambda alvo: aberturas.append(alvo) or True,
    }


def test_red_store_aberta_por_uri_e_relida_antes_da_confirmacao(monkeypatch) -> None:
    estados = iter((
        {"programa_aberto": False, "programa_em_foco": False},
        {"programa_aberto": False, "programa_em_foco": False},
        {"programa_aberto": True, "programa_em_foco": True},
    ))
    ultimo = {"programa_aberto": True, "programa_em_foco": True}
    aberturas: list[str] = []

    def resolver(_nome: str) -> dict:
        return dict(next(estados, ultimo))

    monkeypatch.setattr(
        "mente_laylay.autonomia.habilidade_janelas.time.sleep",
        lambda _segundos: None,
    )
    resultado = executar_habilidade_janelas(
        "APP_OPEN",
        {"nome_app": "microsoft store"},
        _contexto_store(resolver, aberturas),
    )

    assert aberturas == ["ms-windows-store:"]
    assert resultado["status"] == "app_iniciado_focado"
    assert resultado["ok"] is True
    assert resultado["confirmado"] is True


def test_guard_uri_aceita_sem_janela_observada_nao_vira_sucesso_confirmado(
    monkeypatch,
) -> None:
    aberturas: list[str] = []
    monkeypatch.setattr(
        "mente_laylay.autonomia.habilidade_janelas.time.sleep",
        lambda _segundos: None,
    )

    resultado = executar_habilidade_janelas(
        "APP_OPEN",
        {"nome_app": "microsoft store"},
        _contexto_store(
            lambda _nome: {
                "programa_aberto": False,
                "programa_em_foco": False,
            },
            aberturas,
        ),
    )

    assert aberturas == ["ms-windows-store:"]
    assert resultado["status"] == "abertura_solicitada"
    assert resultado["ok"] is True
    assert resultado["confirmado"] is False


def test_executor_publica_confirmacao_observada_da_habilidade(monkeypatch) -> None:
    eventos: list[tuple] = []
    monkeypatch.setattr(
        executor_janelas,
        "executar_habilidade_janelas",
        lambda *_args, **_kwargs: {
            "handled": True,
            "nome_app": "microsoft store",
            "status": "app_iniciado_focado",
            "ok": True,
            "confirmado": True,
        },
    )
    deps = DependenciasExecutorJanelas(
        marcar_resultado=lambda status, **kwargs: eventos.append(
            ("resultado", status, kwargs)
        ),
        falar_por_status=lambda *_args, **_kwargs: None,
        falar_resultado_janela=lambda *_args, **_kwargs: None,
        alvo_preciso_para_aba=lambda alvo: alvo,
        esperar_aba_fechar=lambda *_args: True,
        esperar_programa_fechar=lambda *_args: True,
        executar_recursivo=lambda *_args: True,
    )

    executar_intencao_janelas(
        "APP_OPEN",
        {"nome_app": "microsoft store"},
        "pc_a",
        {},
        deps,
    )

    assert eventos == [(
        "resultado",
        "app_iniciado_focado",
        {"executou": True, "confirmado": True},
    )]


def test_red_store_ja_aberta_e_maximizada_pelo_nome_da_janela() -> None:
    alvos_maximizacao: list[str] = []
    aberturas: list[str] = []
    resultado = executar_habilidade_janelas(
        "MAXIMIZE_WINDOW",
        {"nome_app": "microsoft store"},
        {
            **_contexto_store(
                lambda _nome: {
                    "programa_aberto": True,
                    "programa_em_foco": True,
                },
                aberturas,
            ),
            "ativar_tela_cheia_robusta": (
                lambda alvo: alvos_maximizacao.append(alvo)
                or alvo == "microsoft store"
            ),
        },
    )

    assert alvos_maximizacao == ["microsoft store"]
    assert aberturas == []
    assert resultado["status"] == "janela_maximizada"
    assert resultado["ok"] is True
