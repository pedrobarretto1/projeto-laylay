"""Contratos do adaptador offline do perfil operacional v1."""
from copy import deepcopy

import pytest

from mente_laylay.neural.adaptador_validacao_operacional import (
    preparar_exemplo_validacao_operacional,
)
from mente_laylay.neural.supervisao_operacional_v1 import PERFIL
from mente_laylay.neural.supervisao_relacoes_v4 import FLAGS
from tests.test_neural_protocolo_ajuste_supervisionado import caso
from tests.test_neural_supervisao_operacional_v1 import exemplo


def _preparar(anotacao, *, grupo="g1", entidade="entidade_1"):
    return preparar_exemplo_validacao_operacional(
        anotacao,
        validation_group=grupo,
        validation_entity_group=entidade,
    )


@pytest.mark.parametrize("ato,prefixo", [
    ("pedido", ""),
    ("recusa", "nao "),
    ("relato", "ontem eu disse: "),
])
def test_ato_fica_diagnostico_e_nao_muda_intent_action(ato, prefixo):
    texto = prefixo + "liga luz"
    anotacao = exemplo(
        texto,
        intent="IOT_CONTROL",
        action="on",
        ancora="liga",
        alvo="luz",
        ato=ato,
    )
    antes = deepcopy(anotacao)

    item = _preparar(anotacao)

    assert anotacao == antes
    assert item["text"] == texto
    assert item["intent"] == "IOT_CONTROL"
    assert item["action"] == "on"
    assert item["extension_scope"] == PERFIL
    assert item["diagnostico_operacional"]["atos"] == [ato]
    assert "extension_factors" not in item
    assert item["contrato"] == {
        "uso": "validacao_offline",
        "treino_permitido": False,
        "autoriza_promocao": False,
        "autoriza_execucao": False,
    }


def test_actions_da_mesma_intent_permanecem_distintas():
    ligado = _preparar(exemplo(
        "liga luz",
        intent="IOT_CONTROL",
        action="on",
        ancora="liga",
        alvo="luz",
    ))
    desligado = _preparar(exemplo(
        "desliga luz",
        intent="IOT_CONTROL",
        action="off",
        ancora="desliga",
        alvo="luz",
    ))

    assert (ligado["intent"], ligado["action"]) == ("IOT_CONTROL", "on")
    assert (desligado["intent"], desligado["action"]) == ("IOT_CONTROL", "off")


def test_parametro_volume_e_preservado_so_como_diagnostico():
    item = _preparar(exemplo(
        "coloca o volume em 37",
        valor=37,
    ))

    assert item["diagnostico_operacional"]["parametros"][0]["valor"] == 37
    assert item["diagnostico_operacional"]["parametros"][0]["nome"] == "nivel_volume"
    assert "params" not in item
    assert "extension_factors" not in item


@pytest.mark.parametrize("campo", ["validation_group", "validation_entity_group"])
def test_grupos_precisam_ser_explicitos(campo):
    kwargs = {
        "validation_group": "g1",
        "validation_entity_group": "e1",
    }
    kwargs[campo] = ""
    with pytest.raises(ValueError, match=campo):
        preparar_exemplo_validacao_operacional(
            exemplo("liga luz", intent="IOT_CONTROL", action="on", ancora="liga", alvo="luz"),
            **kwargs,
        )


def _span(texto, literal):
    inicio = texto.index(literal)
    return {
        "inicio": inicio,
        "fim": inicio + len(literal),
        "texto": literal,
    }


def test_multivariante_nao_e_achatada_para_uma_label():
    texto = "liga luz e pausa musica"
    anotacao = exemplo(
        texto,
        intent="IOT_CONTROL",
        action="on",
        ancora="liga",
        alvo="luz",
    )
    inicio_segundo = texto.index("pausa")
    anotacao["fonte_v4"]["nos"][0]["trecho"] = {
        "inicio": 0,
        "fim": inicio_segundo,
        "texto": texto[:inicio_segundo],
    }
    anotacao["fonte_v4"]["nos"].append({
        "id": "n1",
        "intent": "MEDIA_CONTROL",
        "action": "pause",
        "ato": "pedido",
        "trecho": {
            "inicio": inicio_segundo,
            "fim": len(texto),
            "texto": texto[inicio_segundo:],
        },
        "ancora": _span(texto, "pausa"),
        "alvos": [_span(texto, "musica")],
    })

    with pytest.raises(ValueError, match="mais de uma variante"):
        _preparar(anotacao)


def test_proveniencia_e_flags_sao_preservados_sem_autoridade():
    anotacao = exemplo(
        "pausa musica",
        intent="MEDIA_CONTROL",
        action="pause",
        ancora="pausa",
        alvo="musica",
    )
    anotacao["origem_rotulo"] = "revisao_humana"
    anotacao["referencia_rotulo"] = "revisao/teste/1"

    item = _preparar(anotacao)

    diag = item["diagnostico_operacional"]
    assert diag["origem_rotulo"] == "revisao_humana"
    assert diag["referencia_rotulo"] == "revisao/teste/1"
    assert all(diag["flags"][chave] is False for chave in FLAGS)
