from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.roteador_deterministico import detectar_consulta_abas
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.integracao.avaliador_roteiro_teste import avaliar_turno_roteiro
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.continuidade_geral import (
    resolver_fechamento_ordinal_aberturas_recentes,
)
from mente_laylay.memoria_mental.continuidade_conversa import (
    detectar_comentario_resultado_operacional,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from tests.fakes_navegador import NavegadorLeituraFake


def _params(**kwargs):
    return kwargs


@pytest.mark.parametrize(
    "texto",
    (
        "Qual aba ficou aberta?",
        "Me diz qual aba ficou aberta.",
        "Que aba ficou aberta?",
    ),
)
def test_red_turno117_consulta_aba_sobrevivente_pela_percepcao_atual(
    texto: str,
) -> None:
    assert detectar_consulta_abas(texto, params_cb=_params) == {
        "intent": "LIST_TABS",
        "params": {"somente_ativa": True},
    }


def test_red_turno117_pergunta_factual_nao_vira_comentario_da_aba_fechada() -> None:
    estado = {
        "ultima_acao_intent": "CLOSE_TAB",
        "ultima_acao_alvo": "Wikipédia, a enciclopédia livre",
        "ultima_acao_status": "aba_fechada",
        "ultima_acao_ok": True,
        "ultima_acao_confirmada": True,
        "ultima_acao_params": {"alvo": "wikipedia", "tab_id": 11},
        "ultima_acao_ts": time.time(),
    }

    assert detectar_comentario_resultado_operacional(
        "Qual aba ficou aberta?",
        estado,
    ) is None


def test_red_turno117_leitura_atravessa_prioridade_sem_autoridade_de_mutacao() -> None:
    executados: list[dict] = []
    registros: list[tuple] = []
    estado = SimpleNamespace(mental={
        "turno_atual": {
            "id": "turno-117",
            "texto": "Qual aba ficou aberta?",
            "modalidade": "pergunta",
            "modalidade_geral": "pergunta",
            "autoriza_execucao": False,
            "requer_esclarecimento": False,
        }
    })
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "detectar_intencao_deterministica": lambda texto: (
                detectar_intencao_deterministica_mente(
                    texto,
                    {
                        "normalizar_texto": lambda valor: str(valor).casefold(),
                        "mente_integrada_estado": estado.mental,
                    },
                )
            ),
            "executar_intencao": lambda comando, _texto: (
                executados.append(dict(comando)) or True
            ),
            "_registrar_resultado_execucao": (
                lambda *args, **kwargs: registros.append((args, kwargs))
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("Qual aba ficou aberta?") is True
    assert executados == [{
        "intent": "LIST_TABS",
        "params": {"somente_ativa": True},
    }]
    assert registros
    assert registros[0][1]["origem"] == "prioritario_deterministico_contextual"


def test_red_turno117_executor_rele_prime_video_em_vez_do_recibo_fechado() -> None:
    falas: list[str] = []
    resultados: list[ResultadoAcao] = []
    leitura = NavegadorLeituraFake(
        aba={
            "id": 22,
            "title": "Prime Video",
            "url": "https://www.primevideo.com/",
            "active": True,
        },
    )
    comando = {
        "intent": "LIST_TABS",
        "params": {"somente_ativa": True},
    }

    assert executar_intencao(
        comando,
        "Qual aba ficou aberta?",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_registro_navegador_leitura_runtime": leitura,
            "_registrar_resultado_execucao": (
                lambda resultado, *_args, **_kwargs: resultados.append(resultado)
            ),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
    ) is True

    assert falas == ["A aba ativa agora é Prime Video — primevideo.com."]
    assert resultados and resultados[0].intent == "LIST_TABS"
    assert resultados[0].status == "aba_ativa_consultada"
    assert resultados[0].alvo == "Prime Video — primevideo.com"
    assert resultados[0].confirmado is True
    assert resultados[0].params["tab_id"] == 22


def _estado_apos_fechamento_ordinal_confirmado() -> dict:
    estado = estado_mental_inicial()
    for alvo, fala in (
        ("wikipedia", "Abre a Wikipédia."),
        ("prime video", "Abre o Prime Video."),
    ):
        estado = registrar_resultado_execucao(
            estado,
            ResultadoAcao(
                intent="OPEN_URL",
                status="url_aberta",
                alvo=alvo,
                params={"alvo": alvo},
                executou=True,
                confirmado=True,
                origem="executor",
            ),
            fala,
        )
    fechamento = resolver_fechamento_ordinal_aberturas_recentes(
        estado,
        texto="Fecha a primeira.",
    )
    assert fechamento["params"]["aba_sobrevivente_contextual"] == "prime video"
    return registrar_resultado_execucao(
        estado,
        ResultadoAcao(
            intent="CLOSE_TAB",
            status="aba_fechada",
            alvo="Wikipédia",
            params=dict(fechamento["params"]),
            executou=True,
            confirmado=True,
            origem="executor",
        ),
        "Fecha a primeira.",
    )


def test_red_turno117_detector_preserva_sobrevivente_do_conjunto_causal() -> None:
    estado = _estado_apos_fechamento_ordinal_confirmado()

    comando = detectar_intencao_deterministica_mente(
        "Qual aba ficou aberta?",
        {
            "normalizar_texto": lambda texto: str(texto).casefold(),
            "mente_integrada_estado": estado,
        },
    )

    assert comando == {
        "intent": "LIST_TABS",
        "params": {
            "somente_sobrevivente": True,
            "alvo_contextual": "prime video",
            "origem_contextual": "fechamento_ordinal",
        },
    }


def test_red_turno117_ativa_global_nao_sombreia_sobrevivente_contextual() -> None:
    falas: list[str] = []
    resultados: list[ResultadoAcao] = []
    leitura = NavegadorLeituraFake(
        aba={
            "id": 77,
            "title": "ChatGPT",
            "url": "https://chatgpt.com/",
            "active": True,
        },
        abas=[
            {
                "id": 77,
                "title": "ChatGPT",
                "url": "https://chatgpt.com/",
                "active": True,
            },
            {
                "id": 22,
                "title": "Prime Video",
                "url": "https://www.primevideo.com/",
                "active": False,
            },
        ],
    )

    assert executar_intencao(
        {
            "intent": "LIST_TABS",
            "params": {
                "somente_sobrevivente": True,
                "alvo_contextual": "prime video",
                "origem_contextual": "fechamento_ordinal",
            },
        },
        "Qual aba ficou aberta?",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_registro_navegador_leitura_runtime": leitura,
            "_registrar_resultado_execucao": (
                lambda resultado, *_args, **_kwargs: resultados.append(resultado)
            ),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
    ) is True

    assert falas == [
        "A aba que ficou aberta desse conjunto é Prime Video — primevideo.com."
    ]
    assert resultados and resultados[0].status == "aba_sobrevivente_consultada"
    assert resultados[0].alvo == "Prime Video — primevideo.com"
    assert resultados[0].confirmado is True


def test_guard_turno117_comentario_real_com_ficou_continua_reconhecido() -> None:
    estado = {
        "ultima_acao_intent": "IOT_CONTROL",
        "ultima_acao_alvo": "lâmpada do quarto",
        "ultima_acao_params": {"acao": "ajustar_cor", "cor": "azul"},
        "ultima_acao_ts": time.time(),
    }

    comentario = detectar_comentario_resultado_operacional(
        "Ficou mais roxa do que azul.",
        estado,
    )

    assert comentario and comentario["tipo"] == "aparencia_cor"


def test_red_turno117_caos_reprova_resposta_da_aba_fechada_e_aprova_prime() -> None:
    comando_observado = {
        "intent": "LIST_TABS",
        "status": "aba_sobrevivente_consultada",
        "alvo": "Prime Video — primevideo.com",
        "executou": True,
        "confirmado": True,
    }
    plano = {
        "fase": "tratado_prioritario",
        "comandos": [comando_observado],
        "erros": [],
    }

    ruim = avaliar_turno_roteiro(
        indice=116,
        comando="Qual aba ficou aberta?",
        resposta="Entendi o que você percebeu em Wikipédia.",
        plano=plano,
        respondeu=True,
        motivo_resultado="execucao_confirmada",
    )
    bom = avaliar_turno_roteiro(
        indice=116,
        comando="Qual aba ficou aberta?",
        resposta="A aba ativa agora é Prime Video.",
        plano=plano,
        respondeu=True,
        motivo_resultado="execucao_confirmada",
    )

    assert ruim["resultado_semantico"] == "falhou"
    assert bom["resultado_semantico"] == "passou"
    assert bom["expectativa"] == "aba_sobrevivente_apos_fechamento_ordinal"
