from __future__ import annotations

import asyncio
from concurrent.futures import Future
from functools import partial
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.comandos_imediatos import (
    ComandosImediatosRuntime,
    texto_pede_resumo_pagina,
)
from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
from mente_laylay.autonomia.orquestrador_deterministico import (
    DeteccaoDeterministicaRuntime,
)
from mente_laylay.autonomia.porteiro_acoes import (
    texto_bloqueia_playlist_agora,
    texto_conversa_casual_sem_acao,
    texto_social_curto,
    texto_tem_comando_explicito,
)
from mente_laylay.autonomia.roteador_deterministico import (
    texto_expresso_melhor_no_deterministico,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno


def _normalizar(texto: str) -> str:
    return str(texto or "").casefold().strip()


def _criar_detector(
    estado: SimpleNamespace,
) -> tuple[DeteccaoDeterministicaRuntime, dict]:
    servicos = {
        "_normalizar_texto_com_apelidos": _normalizar,
        "_texto_conversa_casual_sem_acao": texto_conversa_casual_sem_acao,
        "_texto_bloqueia_playlist_agora": texto_bloqueia_playlist_agora,
        "_texto_social_curto": texto_social_curto,
        "_ignorar_token_solto": lambda _texto: False,
        "_fluxo_prioritario_da_ia": lambda _texto: False,
        "_texto_expresso_melhor_no_deterministico": partial(
            texto_expresso_melhor_no_deterministico,
            normalizar_texto=_normalizar,
        ),
        "_texto_depende_de_contexto": lambda _texto: False,
        "_limpar_destino_pc_b": lambda texto: texto,
        "_target_from_params": lambda _params, _texto: "pc_a",
        "_limpar_nome_playlist": lambda texto: str(texto).strip(),
        "_musica_estado_get": lambda *_args: "",
        "_contexto_musical_ativo": lambda: False,
        "_estado_compartilhado_runtime": estado,
    }
    detector = DeteccaoDeterministicaRuntime(
        namespace_getter=lambda: servicos,
        estado_getter=lambda: estado.mental,
        sites_diretos={},
        apps_map={},
    )
    return detector, servicos


@pytest.mark.parametrize(
    ("texto", "intent"),
    (
        ("olha minha tela", "SCREEN_CAPTURE"),
        ("o que tem na minha tela?", "SCREEN_CAPTURE"),
        ("me resume essa pagina", "RESUMIR_PAGINA"),
        ("me passa o briefing de hoje", "BRIEFING_REPEAT"),
        ("qual o briefing de hoje?", "BRIEFING_REPEAT"),
    ),
)
def test_modalidade_reconhece_leituras_exatas_como_comando(
    texto: str,
    intent: str,
) -> None:
    turno = classificar_modalidade_turno(
        texto,
        normalizar_texto=_normalizar,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )

    assert turno["modalidade_geral"] == "comando", intent
    assert turno["autoriza_execucao"] is True
    assert turno["natureza_acao"] == "consulta"


@pytest.mark.parametrize(
    "texto",
    (
        "não olha minha tela",
        "talvez você possa ver minha tela",
        "você consegue ver minha tela?",
        "não me resume essa página",
        "talvez você possa resumir essa página",
        "você consegue resumir essa página?",
        "não me passa o briefing de hoje",
        "talvez você me passe o briefing de hoje",
        "você consegue me passar o briefing de hoje?",
    ),
)
def test_negacao_hipotese_e_capacidade_nao_executam_leitura(texto: str) -> None:
    estado = SimpleNamespace(mental={})
    detector, _servicos = _criar_detector(estado)
    turno = classificar_modalidade_turno(
        texto,
        normalizar_texto=_normalizar,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )

    assert turno["autoriza_execucao"] is False
    assert detector.detectar(texto) is None
    assert texto_pede_resumo_pagina(texto) is False


def test_composicao_real_entrega_tela_e_briefing_aos_executores_sem_llm() -> None:
    estado = SimpleNamespace(mental={})
    detector, servicos = _criar_detector(estado)
    intencoes: list[str] = []
    evidencias: list[tuple[str, str]] = []
    contratos: list[tuple] = []

    def resolver_natural(texto: str, origem: str):
        turno = classificar_modalidade_turno(
            texto,
            normalizar_texto=_normalizar,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )
        return resolver_intencao(
            texto,
            origem,
            {
                "normalizar_texto": _normalizar,
                "refinar_contexto_mental": lambda _texto: None,
                "extrair_agendamento": lambda _texto: None,
                "extrair_acao_agendada": lambda _texto: None,
                "texto_cancela_acao_agora": lambda _texto: False,
                "texto_depende_de_contexto": lambda _texto: False,
                "detectar_intencao_deterministica": detector.detectar,
                "resolver_comando_contextual_forcado": lambda _texto: None,
                "resolver_repeticao_ultima_acao": lambda _texto: None,
                "tentar_intencao_ai_primeiro": lambda _texto: (_ for _ in ()).throw(
                    AssertionError("uma leitura explícita não pode chegar à LLM")
                ),
                "registrar_arbitragem_turno": lambda *_args: None,
                "turno_atual": turno,
                "retrato_turno_atual": {},
            },
        )

    contexto_executor = {
        "_target_from_params": lambda *_args: "pc_a",
        "_executar_captura_tela_intent": lambda destino: (
            evidencias.append(("tela", destino)) or True
        ),
        "repetir_briefing": lambda: (
            evidencias.append(("briefing", "observado"))
            or "Briefing recuperado de dados observados."
        ),
        "_registrar_resultado_execucao": (
            lambda *args, **kwargs: contratos.append((args, kwargs))
        ),
    }

    def executar(resultado: dict, texto: str) -> bool:
        intencoes.append(str(resultado.get("intent") or ""))
        return executar_intencao(resultado, texto, contexto_executor)

    servicos.update({
        "resolver_comando_natural": resolver_natural,
        "executar_intencao": executar,
        "_registrar_resultado_execucao": (
            lambda *args, **kwargs: contratos.append((args, kwargs))
        ),
    })
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: servicos,
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("olha minha tela") is True
    assert runtime.processar_prioritarios("o que tem na minha tela?") is True
    assert runtime.processar_prioritarios("me passa o briefing de hoje") is True
    assert runtime.processar_prioritarios("qual o briefing de hoje?") is True

    assert intencoes == [
        "SCREEN_CAPTURE", "SCREEN_CAPTURE", "BRIEFING_REPEAT", "BRIEFING_REPEAT",
    ]
    assert evidencias == [
        ("tela", "pc_a"),
        ("tela", "pc_a"),
        ("briefing", "observado"),
        ("briefing", "observado"),
    ]
    assert contratos


def test_composicao_real_entrega_me_resume_ao_executor_observavel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    estado = SimpleNamespace(mental={})
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
                lambda resultado, texto, executou, **kwargs: registros.append(
                    (resultado, texto, executou, kwargs)
                )
            ),
        },
        loop_getter=lambda: loop,
    )

    assert runtime.processar_prioritarios("me resume essa pagina") is True
    assert registros == [(
        {"intent": "RESUMIR_PAGINA", "params": {}},
        "me resume essa pagina",
        True,
        {
            "origem": "prioritario_resumo_pagina",
            "status": "resumo_concluido",
        },
    )]
