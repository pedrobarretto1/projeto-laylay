from __future__ import annotations

import hashlib
import json

import pytest

from mente_laylay.neural.propostas_anotacao_operacional import (
    preparar_propostas_anotacao,
)


def _span(texto, literal):
    inicio = texto.index(literal)
    return {"inicio": inicio, "fim": inicio + len(literal), "texto": literal}


def _anotacao(texto, *, intent, action, ancora, alvo):
    return {
        "versao": 1,
        "perfil": "operacional_literal_v1",
        "escopo": "literal_imediato",
        "origem_rotulo": "curadoria_ia",
        "referencia_rotulo": "fixture/proposta",
        "fonte_v4": {
            "versao": 4,
            "texto_entrada": texto,
            "nos": [{
                "id": "n0",
                "intent": intent,
                "action": action,
                "ato": "pedido",
                "trecho": {"inicio": 0, "fim": len(texto), "texto": texto},
                "ancora": _span(texto, ancora),
                "alvos": [_span(texto, alvo)],
            }],
            "relacoes": [],
            "treino_permitido": False,
            "autoriza_execucao": False,
            "autoriza_promocao": False,
        },
        "parametros": [],
        "treino_permitido": False,
        "autoriza_execucao": False,
        "autoriza_promocao": False,
    }


def _fonte(tmp_path):
    itens = [
        {
            "indice_fila": 10,
            "texto": "liga a luz",
            "grupo_texto": "g_liga",
            "status": "candidato_literal",
            "intent_proposta": "IOT_CONTROL",
            "action_proposta": "on",
        },
        {
            "indice_fila": 11,
            "texto": "liga a luz",
            "grupo_texto": "g_liga",
            "status": "candidato_literal",
            "intent_proposta": "IOT_CONTROL",
            "action_proposta": "on",
        },
        {
            "indice_fila": 12,
            "texto": "desliga a luz",
            "grupo_texto": "g_desliga",
            "status": "candidato_literal",
            "intent_proposta": "IOT_CONTROL",
            "action_proposta": "off",
        },
        {
            "indice_fila": 13,
            "texto": "oi lay",
            "grupo_texto": "g_social",
            "status": "fora_perfil",
        },
    ]
    fila = tmp_path / "fila_revisao.jsonl"
    fila.write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in itens),
        encoding="utf-8",
    )
    resumo = tmp_path / "resumo.json"
    resumo.write_text(json.dumps({
        "contrato": {
            "uso": "fila_revisao_operacional",
            "revisao_humana": False,
            "dados_prontos_para_treino": False,
            "treino_permitido": False,
            "autoriza_execucao": False,
            "autoriza_promocao": False,
        }
    }), encoding="utf-8")
    return fila, resumo


def _manifesto(fila):
    return {
        "versao": 1,
        "fonte_triagem_sha256": hashlib.sha256(fila.read_bytes()).hexdigest(),
        "origem_rotulo": "curadoria_ia",
        "revisao_humana": False,
        "treino_permitido": False,
        "autoriza_execucao": False,
        "autoriza_promocao": False,
        "propostas": [
            {
                "grupo_texto": "g_liga",
                "validation_entity_group": "iot_luz",
                "anotacao": _anotacao(
                    "liga a luz",
                    intent="IOT_CONTROL",
                    action="on",
                    ancora="liga",
                    alvo="luz",
                ),
            },
            {
                "grupo_texto": "g_desliga",
                "validation_entity_group": "iot_luz",
                "anotacao": _anotacao(
                    "desliga a luz",
                    intent="IOT_CONTROL",
                    action="off",
                    ancora="desliga",
                    alvo="luz",
                ),
            },
        ],
    }


def test_propostas_sao_por_texto_distinto_e_preservam_eventos(tmp_path):
    fila, resumo = _fonte(tmp_path)
    resultado = preparar_propostas_anotacao(
        fila, resumo, _manifesto(fila)
    )

    assert resultado["resumo"]["eventos_candidatos"] == 3
    assert resultado["resumo"]["textos_distintos_candidatos"] == 2
    assert len(resultado["exemplos"]) == 2
    liga = next(x for x in resultado["exemplos"] if x["text"] == "liga a luz")
    assert liga["indices_fila"] == [10, 11]
    assert liga["validation_group"] == "g_liga"
    assert liga["validation_entity_group"] == "iot_luz"
    assert liga["intent"] == "IOT_CONTROL"
    assert liga["action"] == "on"


def test_saida_continua_sem_autoridade_ou_revisao_humana(tmp_path):
    fila, resumo = _fonte(tmp_path)
    resultado = preparar_propostas_anotacao(
        fila, resumo, _manifesto(fila)
    )

    assert resultado["contrato"] == {
        "uso": "propostas_anotacao_operacional",
        "origem_rotulo": "curadoria_ia",
        "revisao_humana": False,
        "dados_prontos_para_treino": False,
        "treino_permitido": False,
        "autoriza_execucao": False,
        "autoriza_promocao": False,
    }
    assert all(
        exemplo["contrato"]["treino_permitido"] is False
        for exemplo in resultado["exemplos"]
    )


@pytest.mark.parametrize("modo", ["faltando", "duplicado", "extra"])
def test_manifesto_cobre_grupos_candidatos_exatamente_uma_vez(tmp_path, modo):
    fila, resumo = _fonte(tmp_path)
    manifesto = _manifesto(fila)
    if modo == "faltando":
        manifesto["propostas"].pop()
    elif modo == "duplicado":
        manifesto["propostas"].append(dict(manifesto["propostas"][0]))
    else:
        manifesto["propostas"].append({
            "grupo_texto": "g_social",
            "validation_entity_group": "social",
            "anotacao": _anotacao(
                "oi lay",
                intent="IOT_CONTROL",
                action="on",
                ancora="oi",
                alvo="lay",
            ),
        })
    with pytest.raises(ValueError, match="cobrir"):
        preparar_propostas_anotacao(fila, resumo, manifesto)


def test_proposta_precisa_bater_com_intent_action_da_triagem(tmp_path):
    fila, resumo = _fonte(tmp_path)
    manifesto = _manifesto(fila)
    manifesto["propostas"][0]["anotacao"]["fonte_v4"]["nos"][0]["action"] = "off"

    with pytest.raises(ValueError, match="triagem"):
        preparar_propostas_anotacao(fila, resumo, manifesto)


def test_span_invalido_e_rejeitado_pelo_contrato_operacional(tmp_path):
    fila, resumo = _fonte(tmp_path)
    manifesto = _manifesto(fila)
    manifesto["propostas"][0]["anotacao"]["fonte_v4"]["nos"][0]["ancora"]["inicio"] = 1

    with pytest.raises(ValueError):
        preparar_propostas_anotacao(fila, resumo, manifesto)


def test_manifesto_fica_vinculado_ao_sha_da_triagem(tmp_path):
    fila, resumo = _fonte(tmp_path)
    manifesto = _manifesto(fila)
    manifesto["fonte_triagem_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="SHA"):
        preparar_propostas_anotacao(fila, resumo, manifesto)
