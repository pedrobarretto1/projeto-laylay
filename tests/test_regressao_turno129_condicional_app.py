from __future__ import annotations

import pytest

from mente_laylay.autonomia.executor_janelas import (
    DependenciasExecutorJanelas,
    executar_intencao_janelas,
)
from mente_laylay.autonomia.roteador_deterministico import (
    _detectar_abrir_app_ou_site_base_c1d,
    extrair_intencao_abrir_app,
)
from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto


FALA = (
    "Se a microsoft store não estiver aberta, abre; "
    "se já estiver, só me avisa."
)


def _detectar_como_producao(texto: str) -> dict | None:
    return _detectar_abrir_app_ou_site_base_c1d(
        texto,
        params_cb=lambda **kwargs: kwargs,
        extrair_intencao_abrir_app=lambda valor: extrair_intencao_abrir_app(
            valor,
            normalizar_texto=normalizar_texto,
            limpar_destino=lambda alvo: alvo,
            apps_map={"microsoft store": "ms-windows-store:"},
            sites_diretos={},
        ),
    )


def test_red_turno129_condicional_preserva_alvo_e_politica() -> None:
    comando = extrair_intencao_abrir_app(
        FALA,
        # O normalizador operacional real remove vírgulas e ponto-e-vírgula.
        # Uma cópia que preserva pontuação mascara exatamente a falha vista no
        # caos e, por isso, não é prova suficiente desta rota.
        normalizar_texto=normalizar_texto,
        limpar_destino=lambda valor: valor,
        apps_map={"microsoft store": "ms-windows-store:"},
        sites_diretos={},
    )

    assert comando == {
        "intent": "APP_OPEN",
        "params": {
            "nome_app": "microsoft store",
            "somente_se_fechado": True,
            "avisar_se_aberto": True,
        },
    }


def test_red_turno129_modalidade_preserva_condicional_como_um_contrato() -> None:
    turno = classificar_modalidade_turno(
        FALA,
        normalizar_texto=normalizar_texto,
    )

    assert turno["modalidade_geral"] == "comando"
    assert turno["autoriza_execucao"] is True
    assert turno["texto_operacional"] == FALA.casefold()


@pytest.mark.parametrize(
    "fala_sem_autoridade",
    [
        (
            "Se a microsoft store não estiver aberta, não abre; "
            "se já estiver, só me avisa."
        ),
        (
            "Se a microsoft store não estiver aberta, abre; "
            "se já estiver, você só me avisa?"
        ),
        "Se eu disser abre a microsoft store, só estou dando um exemplo.",
    ],
)
def test_guard_condicional_nao_generaliza_autorizacao(
    fala_sem_autoridade: str,
) -> None:
    turno = classificar_modalidade_turno(
        fala_sem_autoridade,
        normalizar_texto=normalizar_texto,
    )

    assert turno["autoriza_execucao"] is False


def test_red_turno129_caminho_producao_preserva_politica_condicional() -> None:
    turno = classificar_modalidade_turno(
        FALA,
        normalizar_texto=normalizar_texto,
    )
    comando, rota = resolver_intencao(
        FALA,
        "caos-128",
        {
            "normalizar_texto": normalizar_texto,
            "refinar_contexto_mental": lambda _texto: None,
            "turno_atual": turno,
            "retrato_turno_atual": {},
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: False,
            "detectar_intencao_deterministica": _detectar_como_producao,
            "resolver_comando_contextual_forcado": lambda _texto: None,
            "resolver_comando_acao_geral_contextual_forcado": lambda _texto: None,
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "registrar_arbitragem_turno": lambda *_args: None,
            "tentar_intencao_ai_primeiro": lambda _texto: None,
            "texto_parece_consulta_operacional": lambda _texto: True,
            "continuidade_geral": {},
        },
    )

    assert comando == {
        "intent": "APP_OPEN",
        "params": {
            "nome_app": "microsoft store",
            "somente_se_fechado": True,
            "avisar_se_aberto": True,
        },
    }
    assert rota == "deterministico-explicito"


def test_red_turno129_app_aberto_e_observado_sem_receber_foco(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    eventos: list[tuple] = []

    def nao_pode_executar(*_args, **_kwargs):
        raise AssertionError("app já aberto não pode receber foco nem nova abertura")

    monkeypatch.setattr(
        "mente_laylay.autonomia.executor_janelas.executar_habilidade_janelas",
        nao_pode_executar,
    )
    deps = DependenciasExecutorJanelas(
        marcar_resultado=lambda status, **kwargs: eventos.append(
            ("resultado", status, kwargs)
        ),
        falar_por_status=lambda status, fala, **kwargs: eventos.append(
            ("fala", status, fala, kwargs)
        ),
        falar_resultado_janela=lambda *_args: None,
    )

    retorno = executar_intencao_janelas(
        "APP_OPEN",
        {
            "nome_app": "microsoft store",
            "somente_se_fechado": True,
            "avisar_se_aberto": True,
        },
        "pc_a",
        {
            "_resolver_alvo_ambiente": lambda _nome: {
                "programa_aberto": True,
                "programa_em_foco": False,
            },
        },
        deps,
    )

    assert retorno.tratado is True
    assert ("resultado", "app_ja_aberto_observado", {
        "executou": False,
        "confirmado": True,
    }) in eventos
    assert any(
        item[0:2] == ("fala", "app_ja_aberto_observado")
        and "já está aberto" in item[2]
        for item in eventos
    )
