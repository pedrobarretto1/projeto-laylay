from __future__ import annotations

import pytest

from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.especialistas.capacidades import consultar_capacidade, intents_registradas
from mente_laylay.especialistas.operacional import anexar_resultados_operacionais
from mente_laylay.memoria_mental.resultado_acao import normalizar_resultado_acao
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao


def test_todo_intent_documenta_como_confirma_resultado() -> None:
    assert intents_registradas()
    for intent in intents_registradas():
        capacidade = consultar_capacidade(intent)
        assert capacidade["confirmacao_oferecida"] in {
            "estado_observado", "persistencia_local", "retorno_dados",
            "estado_local", "variavel", "indisponivel",
        }
        assert capacidade["evidencia_confirmacao"]
        assert capacidade["estado_sem_confirmacao"] == "nao_confirmado"


@pytest.mark.parametrize(
    ("intent", "status"),
    [
        ("APP_OPEN", "app_aberto_pc_b"),
        ("OPEN_URL", "protocolo_aberto"),
        ("MEDIA_CONTROL", "midia_next"),
        ("CREATE_FOLDER", "pasta_criada_pc_b"),
        ("IOT_CONTROL", "ligado"),
    ],
)
def test_execucao_sem_evidencia_fica_nao_confirmada_por_dominio(intent: str, status: str) -> None:
    resultado = normalizar_resultado_acao({
        "intent": intent,
        "status": status,
        "executou": True,
    })

    assert resultado.confirmado is None
    assert resultado.como_dict()["estado_confirmacao"] == "nao_confirmado"
    assert planejar_resposta_acao(resultado, "Pronto, concluí.").classe == "incerto"
    assert "não consegui confirmar" in planejar_resposta_acao(resultado, "Pronto, concluí.").fala


@pytest.mark.parametrize(
    ("intent", "status"),
    [
        ("CLOSE_APP", "app_fechado"),
        ("OPEN_URL", "url_aberta"),
        ("CREATE_FILE", "arquivo_criado"),
    ],
)
def test_estado_local_realmente_observado_pode_ser_confirmado(intent: str, status: str) -> None:
    resultado = normalizar_resultado_acao({
        "intent": intent,
        "status": status,
        "executou": True,
    })

    assert resultado.confirmado is True
    assert resultado.como_dict()["estado_confirmacao"] == "confirmado"


def test_iot_exige_confirmacao_explicita_da_releitura() -> None:
    sem_releitura = normalizar_resultado_acao({
        "intent": "IOT_CONTROL", "status": "desligado", "executou": True,
    })
    com_releitura = normalizar_resultado_acao({
        "intent": "IOT_CONTROL", "status": "desligado", "executou": True,
        "confirmado": True,
    })

    assert sem_releitura.confirmado is None
    assert com_releitura.confirmado is True


def test_intent_sem_confirmacao_possivel_nao_aceita_sucesso_forcado() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "LOCK_PC", "status": "bloqueio_solicitado",
        "executou": True, "confirmado": True,
    })

    assert resultado.confirmacao_oferecida == "indisponivel"
    assert resultado.confirmado is None
    assert resultado.como_dict()["estado_confirmacao"] == "nao_confirmado"


def test_guardiao_nao_confunde_envio_com_conclusao() -> None:
    validacao = validar_alegacoes_da_fala(
        "Pronto, desliguei a lâmpada.",
        plano={"comandos": [{
            "intent": "IOT_CONTROL", "status": "desligado",
            "executou": True, "confirmado": None,
        }]},
        origem="resposta_ia",
    )

    assert "execucao_alegada_sem_resultado" in validacao["problemas"]
    assert "comando foi enviado" in validacao["fala"]
    assert "não consegui confirmar" in validacao["fala"]


def test_parecer_operacional_so_libera_conclusao_quando_todos_confirmam() -> None:
    parcial, _ = anexar_resultados_operacionais({}, [
        {"intent": "OPEN_URL", "status": "url_aberta", "executou": True},
        {"intent": "MEDIA_CONTROL", "status": "midia_next", "executou": True},
    ])
    completo, _ = anexar_resultados_operacionais({}, [
        {"intent": "OPEN_URL", "status": "url_aberta", "executou": True},
        {"intent": "MEDIA_CONTROL", "status": "midia_next", "executou": True, "confirmado": True},
    ])

    assert parcial["pode_afirmar_conclusao"] is False
    assert parcial["sem_confirmacao"]
    assert completo["pode_afirmar_conclusao"] is True
