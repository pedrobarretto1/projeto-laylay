from __future__ import annotations

import pytest

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_informacoes import (
    DependenciasExecutorInformacoes,
    executar_intencao_informacoes,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_consulta_aprendizados,
)


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


def test_consulta_natural_de_aprendizados_vira_intent_sem_lista_rigida() -> None:
    assert detectar_consulta_aprendizados(
        "me conta quais coisas você guardou sobre mim",
        params_cb=lambda **kwargs: kwargs,
    ) == {"intent": "LEARNING_QUERY", "params": {"limit": 3}}
    assert detectar_consulta_aprendizados(
        "como uma inteligência artificial aprende?",
        params_cb=lambda **kwargs: kwargs,
    ) is None


@pytest.mark.parametrize(
    "texto",
    ("qual é meu nome?", "como eu me chamo?", "você lembra do meu nome?"),
)
def test_consulta_do_proprio_nome_usa_memoria_confirmada(texto: str) -> None:
    assert detectar_consulta_aprendizados(
        texto,
        params_cb=lambda **kwargs: kwargs,
    ) == {
        "intent": "LEARNING_QUERY",
        "params": {
            "limit": 1,
            "query": "nome do usuario",
            "modo": "identidade",
        },
    }


def test_consulta_do_nome_responde_do_estado_sem_chamar_llm_ou_inventar() -> None:
    eventos: list[tuple] = []
    falas: list[str] = []
    despacho = executar_intencao_informacoes(
        "LEARNING_QUERY",
        {"limit": 1, "query": "nome do usuario", "modo": "identidade"},
        "qual é meu nome?",
        {
            "mente_integrada_estado": {"nome_usuario": "Pedro"},
            "_recuperar_aprendizados": lambda **_kwargs: pytest.fail(
                "o estado confirmado deve responder sem uma segunda busca"
            ),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert falas == ["Seu nome é Pedro."]
    assert eventos == [(
        "resultado",
        "aprendizados_consultados",
        {"executou": True, "confirmado": True},
    )]


def test_consulta_do_nome_sem_registro_admite_a_lacuna() -> None:
    falas: list[str] = []
    despacho = executar_intencao_informacoes(
        "LEARNING_QUERY",
        {"limit": 1, "query": "nome do usuario", "modo": "identidade"},
        "qual é meu nome?",
        {
            "mente_integrada_estado": {"nome_usuario": ""},
            "_recuperar_aprendizados": lambda **_kwargs: [],
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias([]),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert "Ainda não tenho seu nome confirmado" in falas[0]
    assert "Seu nome é você" not in falas[0]


def test_consulta_natural_de_preferencias_usa_a_mesma_memoria() -> None:
    for texto in ("do que eu gosto?", "quais são minhas preferências?"):
        assert detectar_consulta_aprendizados(
            texto,
            params_cb=lambda **kwargs: kwargs,
        ) == {
            "intent": "LEARNING_QUERY",
            "params": {
                "limit": 5,
                "query": "preferencia",
                "modo": "listar",
            },
        }


@pytest.mark.parametrize(
    ("texto", "query"),
    (
        ("onde eu moro?", "mora local"),
        ("qual é minha profissão?", "trabalho profissao"),
        ("o que eu estudo?", "estudo"),
    ),
)
def test_consultas_de_fatos_pessoais_usam_memoria_geral(
    texto: str,
    query: str,
) -> None:
    assert detectar_consulta_aprendizados(
        texto,
        params_cb=lambda **kwargs: kwargs,
    ) == {
        "intent": "LEARNING_QUERY",
        "params": {"limit": 3, "query": query, "modo": "listar"},
    }


def test_consulta_de_aprendizados_le_memoria_persistente_e_confirma() -> None:
    eventos: list[tuple] = []
    falas: list[str] = []

    despacho = executar_intencao_informacoes(
        "LEARNING_QUERY",
        {"limit": 3},
        "o que você aprendeu comigo?",
        {
            "_recuperar_aprendizados": lambda **_kwargs: [
                "você prefere luz roxa à noite",
                "sua namorada se chama Nanda",
            ],
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert falas and "luz roxa" in falas[0] and "Nanda" in falas[0]
    assert eventos == [(
        "resultado",
        "aprendizados_consultados",
        {"executou": True, "confirmado": True},
    )]


def test_consulta_humaniza_registro_antigo_de_afinidade() -> None:
    eventos: list[tuple] = []
    falas: list[str] = []
    despacho = executar_intencao_informacoes(
        "LEARNING_QUERY", {"limit": 3}, "o que você aprendeu comigo?",
        {
            "_recuperar_aprendizados": lambda **_kwargs: [{
                "texto": "o usuário gosto de nirvana",
                "regra": "o usuário gosto de nirvana",
                "valor": "Nirvana",
                "chave": "preferencia:afinidade:nirvana",
                "natureza": "confirmado",
                "confirmado_usuario": True,
            }],
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert falas == ["Do que lembro com segurança, você gosta de Nirvana."]


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
    assert eventos == [(
        "resultado",
        "emails_lidos",
        {
            "executou": True,
            "confirmado": True,
        },
    )]


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

    assert despacho == ResultadoDespacho.concluido(True)
    assert eventos[0] == (
        "mente",
        "repete o briefing",
        "Hoje está ensolarado.",
        "BRIEFING_REPEAT",
        "briefing do clima",
        "conversa",
        "briefing",
    )
    assert eventos[1] == (
        "resultado",
        "briefing_repetido",
        {"executou": True, "confirmado": True},
    )


@pytest.mark.parametrize("modo", ["ausente", "falso", "vazio", "erro"])
def test_briefing_repeat_sem_conteudo_nao_inventa_sucesso(modo: str) -> None:
    eventos: list[tuple] = []
    falas: list[str] = []
    ctx = {"falar_com_lipsync": lambda fala, *_args: falas.append(fala)}
    if modo == "falso":
        ctx["repetir_briefing"] = lambda: False
    elif modo == "vazio":
        ctx["repetir_briefing"] = lambda: "  "
    elif modo == "erro":
        def falhar() -> None:
            raise RuntimeError("falha interna")

        ctx["repetir_briefing"] = falhar

    despacho = executar_intencao_informacoes(
        "BRIEFING_REPEAT",
        {},
        "me passa o briefing de hoje",
        ctx,
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido(False)
    assert falas == [
        "Ainda não tenho um briefing pronto para repetir. Posso montar um novo quando você quiser."
    ]
    assert eventos == [(
        "resultado",
        "briefing_indisponivel",
        {"executou": False, "confirmado": False},
    )]


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
    assert eventos == [(
        "resultado", "clima_consultado",
        {"executou": True, "confirmado": True},
    )]


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
    assert eventos == [(
        "resultado", "clima_indisponivel",
        {"executou": False, "confirmado": False},
    )]


def test_weather_responde_diretamente_se_vai_chover() -> None:
    eventos: list[tuple] = []
    falas: list[str] = []

    executar_intencao_informacoes(
        "WEATHER",
        {},
        "vai chover hoje?",
        {
            "cidade_padrao_clima": "Boituva",
            "obter_clima_localidade": lambda _local: {
                "ok": True,
                "localidade": "Boituva",
                "temperatura_c": 21,
                "sensacao_c": 19,
                "descricao": "Smoky haze",
                "umidade": 51,
                "chance_chuva_pct": 18,
                "previsao_chuva_disponivel": True,
            },
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias(eventos),
    )

    assert falas
    assert "não indica chuva significativa" in falas[0].casefold()
    assert "18%" in falas[0]
    assert "21 graus" in falas[0]


def test_weather_responde_a_temperatura_maxima_em_vez_da_atual() -> None:
    eventos: list[tuple] = []
    falas: list[str] = []

    executar_intencao_informacoes(
        "WEATHER",
        {},
        "Qual será a temperatura máxima hoje?",
        {
            "cidade_padrao_clima": "Boituva",
            "obter_clima_localidade": lambda _local: {
                "ok": True,
                "localidade": "Boituva",
                "temperatura_c": 21,
                "temperatura_max_c": 28,
                "temperatura_min_c": 17,
            },
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias(eventos),
    )

    assert falas == [
        "A temperatura máxima prevista hoje em Boituva é de 28 graus."
    ]


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
