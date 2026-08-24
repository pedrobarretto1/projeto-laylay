from __future__ import annotations

from mente_laylay.memoria_mental.continuidade_semantica import (
    resolver_continuidade_semantica,
)


def _estado_app_com_preferencia_antiga() -> dict:
    """Reproduz o estado mínimo observado antes da segunda etapa da cadeia."""
    return {
        "ultima_acao_intent": "APP_OPEN",
        "ultima_acao_params": {"nome_app": "microsoft store"},
        "ultimo_app_janela": "microsoft store",
        "aprendizado_continuidade": {
            "preferencias_conflito": {},
            "preferencias_operacao": {"app:ABRIR>FECHAR": 3},
            "correcoes": [],
        },
    }


def test_guard_verbo_fechar_explicito_continua_fechando_o_app_referido() -> None:
    decisao = resolver_continuidade_semantica(
        "fecha ela",
        mente=_estado_app_com_preferencia_antiga(),
    )

    assert decisao.intent == "CLOSE_APP"
    assert decisao.params["nome_app"] == "microsoft store"


def test_guard_coloca_espacial_nao_herda_fechar_da_preferencia_antiga() -> None:
    decisao = resolver_continuidade_semantica(
        "coloca ela na direita",
        mente=_estado_app_com_preferencia_antiga(),
    )

    assert decisao.intent != "CLOSE_APP"


def test_acao_espacial_explicita_materializa_layout_em_vez_de_herdar_fechar() -> None:
    for fala in ("coloque ela na direita", "coloca ela na direita"):
        decisao = resolver_continuidade_semantica(
            fala,
            mente=_estado_app_com_preferencia_antiga(),
        )

        assert decisao.intent == "ORGANIZAR_DESKTOP", fala
        assert decisao.params == {
            "right": "microsoft store",
            "modo": "posicionar",
            "referencia_contextual": True,
        }
        assert decisao.acao == "POSICIONAR"

    ambigua = resolver_continuidade_semantica(
        "coloque ela",
        mente=_estado_app_com_preferencia_antiga(),
    )
    assert ambigua.intent not in {"CLOSE_APP", "ORGANIZAR_DESKTOP"}
