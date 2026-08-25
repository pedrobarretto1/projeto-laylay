from __future__ import annotations

import asyncio
import time
from concurrent.futures import Future
from types import SimpleNamespace

import pytest

from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.comandos_imediatos import (
    ComandosImediatosRuntime,
    texto_pede_resumo_pagina,
)
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.roteador_deterministico import detectar_fechar_alvo
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.memoria_mental.contexto_compartilhado import (
    registrar_resultado_execucao,
)


def _params(**kwargs):
    return kwargs


def _contexto_deterministico() -> dict:
    return {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "texto_conversa_casual_sem_acao": lambda _texto: False,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: False,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "limpar_nome_playlist": lambda texto: str(texto).strip(),
        "extrair_nome_playlist": lambda _texto: "",
        "detectar_playlist_nome_direto": lambda _texto: "",
        "normalizar_query_musical": lambda texto: str(texto).strip(),
        "extrair_intencao_abrir_app": lambda _texto: None,
        "sites_diretos": {},
        "apps_map": {},
    }


def test_pesquisa_documentacao_sem_marcador_local_vai_para_web() -> None:
    texto = "pesquisa por documentação do Python"

    assert detectar_intencao_arquivos(texto, params_cb=_params) is None
    resultado = detectar_intencao_deterministica_mente(
        texto,
        _contexto_deterministico(),
    )

    assert resultado == {
        "intent": "SEARCH",
        "params": {"query": "documentação do python", "engine": "google"},
    }


def test_pesquisa_com_marcador_de_arquivo_continua_local() -> None:
    resultado = detectar_intencao_deterministica_mente(
        "pesquisa o arquivo controlador.py",
        _contexto_deterministico(),
    )

    assert resultado is not None
    assert resultado["intent"] == "FILE_SEARCH"
    assert resultado["params"]["query"] == "controlador.py"


@pytest.mark.parametrize(
    ("texto", "esperado"),
    (
        ("fecha as abas paradas", {"intent": "CLOSE_IDLE_TABS", "params": {}}),
        ("fecha abas paradas", {"intent": "CLOSE_IDLE_TABS", "params": {}}),
        ("fecha essa aba", {"intent": "CLOSE_TAB", "params": {}}),
        (
            "fecha a aba do ifood",
            {"intent": "CLOSE_TAB", "params": {"alvo": "ifood"}},
        ),
    ),
)
def test_roteador_navegador_preserva_plural_e_aba_atual(
    texto: str,
    esperado: dict,
) -> None:
    resultado = detectar_fechar_alvo(
        texto,
        params_cb=_params,
        sites_diretos={"ifood"},
        apps_map={},
    )

    assert resultado == esperado


@pytest.mark.parametrize("resultado_real", (True, False))
def test_resumo_registra_apenas_resultado_real_concluido(
    monkeypatch: pytest.MonkeyPatch,
    resultado_real: bool,
) -> None:
    registros: list[tuple] = []
    chamadas_roteador: list[dict] = []
    loop = object()

    async def resumir() -> bool:
        return resultado_real

    def executar_corrotina(corrotina, loop_recebido):
        assert loop_recebido is loop
        futuro: Future[bool] = Future()
        futuro.set_result(asyncio.run(corrotina))
        return futuro

    monkeypatch.setattr(
        "mente_laylay.autonomia.comandos_imediatos.asyncio.run_coroutine_threadsafe",
        executar_corrotina,
    )
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": SimpleNamespace(mental={}),
            "resumir_pagina_ou_video": resumir,
            "executar_intencao": lambda intencao, _texto: (
                chamadas_roteador.append(intencao) or True
            ),
            "_registrar_resultado_execucao": (
                lambda resultado, texto, executou, **kwargs: registros.append(
                    (resultado, texto, executou, kwargs)
                )
            ),
        },
        loop_getter=lambda: loop,
    )

    assert runtime.processar_prioritarios("resume a página atual") is True
    assert chamadas_roteador == []
    assert registros == [(
        {"intent": "RESUMIR_PAGINA", "params": {}},
        "resume a página atual",
        resultado_real,
        {
            "origem": "prioritario_resumo_pagina",
            "status": "resumo_concluido" if resultado_real else "falha_execucao",
        },
    )]


def test_resumo_sem_executor_e_registrado_como_indisponivel() -> None:
    registros: list[tuple] = []
    falas: list[str] = []
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": SimpleNamespace(mental={}),
            "_registrar_resultado_execucao": (
                lambda resultado, texto, executou, **kwargs: registros.append(
                    (resultado, texto, executou, kwargs)
                )
            ),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("resume a página atual") is True
    assert registros[0][2] is False
    assert registros[0][3]["status"] == "executor_indisponivel"
    assert falas and "não consigo ler" in falas[0].casefold()


@pytest.mark.parametrize("texto", ("Resume isso.", "Resume agora."))
def test_red_resumo_eliptico_usa_pagina_atual_tipificada(
    monkeypatch: pytest.MonkeyPatch,
    texto: str,
) -> None:
    estado = SimpleNamespace(mental={
        "conteudo_atual": {
            "tipo": "pagina",
            "titulo": "Documentação oficial do Python",
            "url": "https://docs.python.org/3/",
            "status": "visivel",
            "fonte": "extensao_chrome",
            "ts": time.time(),
        },
    })
    registros: list[tuple] = []
    loop = object()

    async def resumir() -> bool:
        return True

    def agendar(corrotina, loop_recebido):
        assert loop_recebido is loop
        futuro: Future[bool] = Future()
        futuro.set_result(asyncio.run(corrotina))
        return futuro

    monkeypatch.setattr(
        "mente_laylay.autonomia.comandos_imediatos.asyncio.run_coroutine_threadsafe",
        agendar,
    )
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "resumir_pagina_ou_video": resumir,
            "_registrar_resultado_execucao": (
                lambda resultado, fala, executou, **kwargs: registros.append(
                    (resultado, fala, executou, kwargs)
                )
            ),
        },
        loop_getter=lambda: loop,
    )

    assert runtime.processar_prioritarios(texto) is True
    assert registros == [(
        {"intent": "RESUMIR_PAGINA", "params": {}},
        texto,
        True,
        {
            "origem": "prioritario_resumo_pagina",
            "status": "resumo_concluido",
        },
    )]


def _estado_apos_resultado_web_confirmado() -> dict:
    return registrar_resultado_execucao(
        {},
        {
            "intent": "SEARCH",
            "params": {
                "query": "documentacao do python",
                "abrir_resultado": 1,
            },
            "alvo": "documentacao do python",
            "status": "resultado_web_aberto",
            "executou": True,
            "confirmado": True,
            "origem": "executor",
        },
        "Abre o primeiro resultado.",
        True,
        origem="executor",
        status="resultado_web_aberto",
    )


@pytest.mark.parametrize("texto", ("Resume isso.", "Resume agora."))
def test_red_turnos_123_126_usam_recibo_real_da_pagina_aberta(
    monkeypatch: pytest.MonkeyPatch,
    texto: str,
) -> None:
    """O caos não recebe PAGE_DATA espontâneo; o resumo captura sob demanda."""
    estado = SimpleNamespace(mental=_estado_apos_resultado_web_confirmado())
    assert "conteudo_atual" not in estado.mental
    registros: list[tuple] = []
    loop = object()

    async def resumir() -> bool:
        return True

    def agendar(corrotina, loop_recebido):
        assert loop_recebido is loop
        futuro: Future[bool] = Future()
        futuro.set_result(asyncio.run(corrotina))
        return futuro

    monkeypatch.setattr(
        "mente_laylay.autonomia.comandos_imediatos.asyncio.run_coroutine_threadsafe",
        agendar,
    )
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "resumir_pagina_ou_video": resumir,
            "_registrar_resultado_execucao": (
                lambda resultado, fala, executou, **kwargs: registros.append(
                    (resultado, fala, executou, kwargs)
                )
            ),
        },
        loop_getter=lambda: loop,
    )

    assert runtime.processar_prioritarios(texto) is True
    assert registros == [(
        {"intent": "RESUMIR_PAGINA", "params": {}},
        texto,
        True,
        {
            "origem": "prioritario_resumo_pagina",
            "status": "resumo_concluido",
        },
    )]


@pytest.mark.parametrize(
    "contrato",
    (
        {
            "intent": "SEARCH",
            "status": "falha_execucao",
            "executou": False,
            "confirmado": False,
        },
        {
            "intent": "SEARCH",
            "status": "resultado_web_aberto",
            "executou": True,
            "confirmado": None,
        },
        {
            "intent": "APP_OPEN",
            "status": "app_aberto",
            "executou": True,
            "confirmado": True,
        },
    ),
)
def test_guard_recibo_inseguro_nao_autoriza_resumo_eliptico(
    contrato: dict,
) -> None:
    estado = {
        "ultima_acao_contrato": contrato,
        "ultima_acao_ts": time.time(),
    }
    assert texto_pede_resumo_pagina(
        "Resume isso.",
        estado_mental=estado,
    ) is False


def test_guard_recibo_de_navegacao_expirado_nao_autoriza_resumo() -> None:
    estado = _estado_apos_resultado_web_confirmado()
    estado["ultima_acao_ts"] = time.time() - 301.0

    assert texto_pede_resumo_pagina(
        "Resume agora.",
        estado_mental=estado,
    ) is False


def test_red_turno_126_sobrevive_ao_recibo_do_resumo_123_concluido() -> None:
    estado = _estado_apos_resultado_web_confirmado()
    estado = registrar_resultado_execucao(
        estado,
        {"intent": "RESUMIR_PAGINA", "params": {}},
        "Resume isso.",
        True,
        origem="prioritario_resumo_pagina",
        status="resumo_concluido",
    )

    assert estado["ultima_acao_contrato"]["intent"] == "RESUMIR_PAGINA"
    assert texto_pede_resumo_pagina(
        "Resume agora.",
        estado_mental=estado,
    ) is True


def test_guard_resumo_anterior_falho_nao_autoriza_nova_leitura() -> None:
    estado = registrar_resultado_execucao(
        {},
        {"intent": "RESUMIR_PAGINA", "params": {}},
        "Resume isso.",
        False,
        origem="prioritario_resumo_pagina",
        status="falha_execucao",
    )

    assert texto_pede_resumo_pagina(
        "Resume agora.",
        estado_mental=estado,
    ) is False


@pytest.mark.parametrize(
    "estado_mental",
    (
        {},
        {"conteudo_atual": "pagina sem contrato tipado"},
        {
            "conteudo_atual": {
                "tipo": "arquivo",
                "titulo": "anotacoes.txt",
                "status": "recente",
                "fonte": "memoria_arquivos",
                "ts": time.time(),
            },
        },
        {
            "conteudo_atual": {
                "tipo": "pagina",
                "titulo": "Página antiga",
                "url": "https://example.test/antiga",
                "status": "visivel",
                "fonte": "extensao_chrome",
                "ts": time.time() - 301.0,
            },
        },
    ),
)
def test_guard_resumo_eliptico_exige_pagina_tipificada_recente(
    estado_mental: dict,
) -> None:
    assert texto_pede_resumo_pagina(
        "Resume isso.",
        estado_mental=estado_mental,
    ) is False


@pytest.mark.parametrize(
    "texto",
    (
        "Não resume isso.",
        "Você consegue resumir isso?",
        "Como eu resumo isso?",
    ),
)
def test_guard_pagina_atual_nao_libera_fala_sem_autorizacao(texto: str) -> None:
    estado = {
        "conteudo_atual": {
            "tipo": "pagina",
            "titulo": "Documentação oficial do Python",
            "url": "https://docs.python.org/3/",
            "status": "visivel",
            "fonte": "extensao_chrome",
            "ts": time.time(),
        },
    }

    assert texto_pede_resumo_pagina(
        texto,
        estado_mental=estado,
    ) is False


def test_roteador_nao_confirma_resumo_sem_executor_assincrono() -> None:
    contratos = []
    falas: list[str] = []

    retorno = executar_intencao(
        {"intent": "RESUMIR_PAGINA", "params": {}},
        "resume a página atual",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_registrar_resultado_execucao": (
                lambda contrato, *_args, **_kwargs: contratos.append(contrato)
            ),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
    )

    assert retorno is False
    assert contratos
    assert contratos[0].intent == "RESUMIR_PAGINA"
    assert contratos[0].status == "executor_indisponivel"
    assert contratos[0].executou is False
    assert contratos[0].confirmado is False
    assert falas and "não consegui iniciar" in falas[0].casefold()
