"""Sonda isolada da composição emocional de P16, sem executar habilidades.

Os ResultadoAcao abaixo são receipts sintéticos para exercitar o caminho
publicador -> setter -> estado -> projeções. Não comprovam efeito externo.
Executar com ``python -m scripts.roteiros.sonda_personalidade_viva_p16_composicao``.
"""

from __future__ import annotations

import json
import sys

import laylay

from mente_laylay.emocoes.estado_emocional import retrato_emocional_expressavel
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


def _retrato() -> dict:
    conversa = dict(laylay._estado_compartilhado_runtime.conversacional)
    visual = laylay._estado_visual_laylay()
    return {
        "estado": [conversa.get("current_emotion"), conversa.get("emotion_level")],
        "voz": list(retrato_emocional_expressavel(conversa)),
        "avatar": [visual.get("emotion"), visual.get("level")],
        "episodio_ativo": bool(conversa.get("episodio_emocional")),
        "humor_level": conversa.get("humor_level"),
    }


def main() -> None:
    estado = laylay._estado_compartilhado_runtime
    # O processo termina após a sonda; esta troca é apenas de estado em memória.
    estado.substituir("conversacional", {"current_emotion": "calma", "humor_level": 0})
    avaliacoes = []
    for indice in range(4):
        resultado = ResultadoAcao(
            intent="APP_OPEN", status="ja_aberto_focado", alvo="Opera",
            executou=False, confirmado=True, texto_usuario="abre o Opera",
            origem="executor",
            id_solicitacao=f"sonda:p16:opera:{indice}",
        )
        avaliacoes.append(laylay._avaliar_evento_emocional_operacional(resultado))
    forte = _retrato()

    laylay._refinar_contexto_mental("Como está o tempo?")
    ordinario = _retrato()
    laylay._refinar_contexto_mental("Mudando de assunto: como está o tempo?")
    mudou = _retrato()

    for indice in range(4):
        avaliacao = laylay._avaliar_evento_emocional_operacional(ResultadoAcao(
            intent="IOT_CONTROL", status="ja_estava_ligado", alvo="lâmpada",
            executou=False, confirmado=True, texto_usuario="liga a lâmpada",
            origem="executor",
            id_solicitacao=f"sonda:p16:lampada:{indice}",
        ))
        assert avaliacao["permite_expressao"] is True
    antes_erro = _retrato()
    incerto = laylay._avaliar_evento_emocional_operacional(ResultadoAcao(
        intent="IOT_CONTROL", status="alvo_ausente", alvo="lâmpada",
        executou=False, confirmado=False, texto_usuario="você entendeu o alvo errado",
        origem="executor",
        id_solicitacao="sonda:p16:erro:incerto",
        contexto={"responsabilidade": "laylay", "confianca_responsabilidade": 0.70},
    ))
    depois_incerto = _retrato()
    erro = laylay._avaliar_evento_emocional_operacional(ResultadoAcao(
        intent="IOT_CONTROL", status="alvo_ausente", alvo="lâmpada",
        executou=False, confirmado=False, texto_usuario="você entendeu o alvo errado",
        origem="executor",
        id_solicitacao="sonda:p16:erro:confirmado",
        contexto={"responsabilidade": "laylay", "confianca_responsabilidade": 0.98},
    ))
    depois_erro = _retrato()

    for indice in range(4):
        avaliacao = laylay._avaliar_evento_emocional_operacional(ResultadoAcao(
            intent="APP_OPEN", status="ja_aberto_focado", alvo="Calculadora",
            executou=False, confirmado=True, texto_usuario="abre a Calculadora",
            origem="executor",
            id_solicitacao=f"sonda:p16:calculadora:{indice}",
        ))
        assert avaliacao["permite_expressao"] is True
    antes_conquista = _retrato()
    laylay._refinar_contexto_mental("Não consegui terminar o projeto.")
    conquista_negada = _retrato()
    laylay._refinar_contexto_mental("Estou muito feliz porque terminei um projeto.")
    conquista = _retrato()

    resultado = {
        "repeticoes": [item.get("repeticoes") for item in avaliacoes],
        "expressoes": [item.get("permite_expressao") for item in avaliacoes],
        "forte": forte,
        "ordinario": ordinario,
        "mudou": mudou,
        "antes_erro": antes_erro,
        "incerto_expressavel": incerto.get("permite_expressao"),
        "depois_incerto": depois_incerto,
        "erro_expressavel": erro.get("permite_expressao"),
        "depois_erro": depois_erro,
        "antes_conquista": antes_conquista,
        "conquista_negada": conquista_negada,
        "conquista": conquista,
    }
    # laylay.py pode espelhar stdout; o canal original deixa o recibo visível.
    sys.__stdout__.write("P16_COMPOSICAO " + json.dumps(resultado, ensure_ascii=False) + "\n")
    assert resultado["repeticoes"] == [1, 2, 3, 4]
    assert resultado["expressoes"] == [True] * 4
    assert forte["estado"] == ordinario["estado"] == ["brava", 3]
    assert mudou["estado"] == ["calma", 1]
    assert forte["voz"] == forte["avatar"] == ["brava", 3]
    assert mudou["voz"] == mudou["avatar"] == ["calma", 1]
    assert forte["episodio_ativo"] and not mudou["episodio_ativo"]
    assert mudou["humor_level"] == ordinario["humor_level"]
    assert antes_erro["estado"] == depois_incerto["estado"] == ["brava", 3]
    assert incerto["permite_expressao"] is False
    assert erro["arco"] == "autorreparo" and erro["permite_expressao"] is True
    assert depois_erro["estado"] == depois_erro["voz"] == depois_erro["avatar"] == ["envergonhada", 1]
    assert antes_conquista["estado"] == conquista_negada["estado"] == ["brava", 3]
    assert conquista["estado"] == conquista["voz"] == conquista["avatar"] == ["calma", 1]
    assert not conquista["episodio_ativo"]
    assert conquista["humor_level"] == conquista_negada["humor_level"]


if __name__ == "__main__":
    main()
