from __future__ import annotations

from mente_laylay.autonomia.orquestrador_deterministico import (
    DeteccaoDeterministicaRuntime,
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.roteador_deterministico import detectar_fechar_alvo
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.memoria_mental.continuidade_geral import (
    resolver_fechamento_ordinal_aberturas_recentes,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from tests.fakes_navegador import NavegadorLeituraFake, NavegadorOperacoesFake


def _params(**kwargs):
    return kwargs


def _estado_duas_aberturas() -> dict:
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        ResultadoAcao(
            intent="OPEN_URL",
            status="url_aberta",
            alvo="wikipedia",
            params={"alvo": "wikipedia"},
            executou=True,
            confirmado=True,
            origem="executor",
        ),
        "Abre a Wikipédia.",
    )
    return registrar_resultado_execucao(
        estado,
        ResultadoAcao(
            intent="OPEN_URL",
            status="url_aberta",
            alvo="prime video",
            params={"alvo": "prime video"},
            executou=True,
            confirmado=True,
            origem="executor",
        ),
        "Abre o Prime Video.",
    )


def _contexto(estado: dict) -> dict:
    return {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "texto_conversa_casual_sem_acao": lambda _texto: False,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: False,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: False,
        "texto_expresso_melhor_no_deterministico": lambda _texto: True,
        "texto_depende_de_contexto": lambda _texto: True,
        "limpar_destino_pc_b": lambda texto: texto,
        "limpar_nome_playlist": lambda texto: str(texto).strip(),
        "extrair_nome_playlist": lambda _texto: "",
        "detectar_playlist_nome_direto": lambda _texto: "",
        "normalizar_query_musical": lambda texto: str(texto).strip(),
        "extrair_intencao_abrir_app": lambda _texto: None,
        "sites_diretos": {},
        "apps_map": {},
        "mente_integrada_estado": estado,
    }


def test_red_turno116_fecha_primeira_abertura_confirmada() -> None:
    comando = detectar_intencao_deterministica_mente(
        "Fecha a primeira.",
        _contexto(_estado_duas_aberturas()),
    )

    assert comando == {
        "intent": "CLOSE_TAB",
        "params": {
            "alvo": "wikipedia",
            "referencia_contextual": True,
            "indice_ordinal": 1,
            "aba_sobrevivente_contextual": "prime video",
        },
    }


def test_red_turno116_fecha_segunda_sem_inverter_ordem_causal() -> None:
    comando = detectar_intencao_deterministica_mente(
        "Fecha a segunda.",
        _contexto(_estado_duas_aberturas()),
    )

    assert comando and comando["intent"] == "CLOSE_TAB"
    assert comando["params"]["alvo"] == "prime video"
    assert comando["params"]["indice_ordinal"] == 2


def test_red_turno116_roteador_real_fecha_wikipedia_por_id_e_preserva_prime() -> None:
    comando = detectar_intencao_deterministica_mente(
        "Fecha a primeira.",
        _contexto(_estado_duas_aberturas()),
    )
    assert comando and comando["intent"] == "CLOSE_TAB"

    navegador = NavegadorOperacoesFake()
    leitura = NavegadorLeituraFake(
        aba={
            "id": 22,
            "title": "Prime Video",
            "url": "https://www.primevideo.com/",
            "active": True,
        },
        abas=[
            {
                "id": 11,
                "title": "Wikipédia",
                "url": "https://pt.wikipedia.org/",
                "active": False,
            },
            {
                "id": 22,
                "title": "Prime Video",
                "url": "https://www.primevideo.com/",
                "active": True,
            },
        ],
    )
    resultados: list[ResultadoAcao] = []

    assert executar_intencao(
        comando,
        "Fecha a primeira.",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_registro_navegador_leitura_runtime": leitura,
            "_registro_navegador_operacoes_runtime": navegador,
            "_registrar_resultado_execucao": (
                lambda resultado, *_args, **_kwargs: resultados.append(resultado)
            ),
            "falar_com_lipsync": lambda *_args: None,
        },
    ) is True

    assert navegador.chamadas == [("close_tabs", {"ids": [11]})]
    assert resultados and resultados[0].status == "aba_fechada"
    assert resultados[0].alvo == "Wikipédia"
    assert resultados[0].confirmado is True


def test_red_turno116_wiring_do_detector_runtime_preserva_historico() -> None:
    estado = _estado_duas_aberturas()
    detector = DeteccaoDeterministicaRuntime(
        namespace_getter=lambda: {
            "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        },
        estado_getter=lambda: estado,
        sites_diretos={},
        apps_map={},
    )
    assert detector.detectar("Fecha a primeira.") == {
        "intent": "CLOSE_TAB",
        "params": {
            "alvo": "wikipedia",
            "referencia_contextual": True,
            "indice_ordinal": 1,
            "aba_sobrevivente_contextual": "prime video",
        },
    }


def test_guard_turno116_ordinal_sem_historico_nao_vira_nome_de_app() -> None:
    assert detectar_fechar_alvo(
        "fecha a primeira",
        params_cb=_params,
        sites_diretos={},
        apps_map={},
    ) is None
    assert detectar_intencao_deterministica_mente(
        "Fecha a primeira.",
        _contexto({}),
    ) is None


def test_guard_turno116_primeira_janela_nao_e_promovida_a_aba() -> None:
    comando = detectar_intencao_deterministica_mente(
        "Fecha a primeira janela.",
        _contexto(_estado_duas_aberturas()),
    )
    assert not comando or comando["intent"] != "CLOSE_TAB"


def test_guard_turno116_uma_unica_abertura_nao_forma_conjunto_ordinal() -> None:
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        ResultadoAcao(
            intent="OPEN_URL",
            status="url_aberta",
            alvo="wikipedia",
            params={"alvo": "wikipedia"},
            executou=True,
            confirmado=True,
            origem="executor",
        ),
        "Abre a Wikipédia.",
    )
    assert resolver_fechamento_ordinal_aberturas_recentes(
        estado,
        texto="Fecha a primeira.",
    ) == {}
