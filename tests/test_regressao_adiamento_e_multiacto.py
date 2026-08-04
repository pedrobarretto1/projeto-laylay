from __future__ import annotations

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao,
    contingencia_comunicacao,
    montar_mensagens_reparo_comunicacao,
)


def _plano_multiacto() -> dict:
    return {
        "id": 91,
        "ato_principal": "conversa",
        "atos": [
            {"ordem": 0, "tipo": "conversa", "objetivo": "acolher a resposta social"},
            {"ordem": 1, "tipo": "pergunta", "objetivo": "responder à preferência"},
        ],
        "resposta_esperada": "reconhecer o estado e responder à pergunta",
        "referencia_resolvida": {},
        "requer_execucao": False,
        "permite_pergunta": True,
    }


def test_adiamento_natural_nao_vira_comando() -> None:
    for texto in (
        "deixa para depois",
        "deixa pra depois",
        "melhor deixar para depois",
        "isso fica para depois",
        "a gente ve isso depois",
        "fazemos isso depois",
    ):
        turno = classificar_modalidade_turno(texto)
        plano = planejar_turno(texto, turno=turno, mente={})

        assert turno["modalidade"] == "recusa", texto
        assert turno["natureza_acao"] == "adiamento", texto
        assert turno["autoriza_execucao"] is False, texto
        assert plano["requer_execucao"] is False, texto


def test_deixa_com_alvo_operacional_continua_sendo_comando() -> None:
    turno = classificar_modalidade_turno("deixa a luz ligada")

    assert turno["modalidade"] == "comando"
    assert turno["autoriza_execucao"] is True


def test_reparo_multiacto_explicita_todos_os_atos_obrigatorios() -> None:
    texto = "Tá tudo bem, você prefere rock ou metal?"
    contrato = construir_contrato_semantico_fala(
        texto,
        plano=_plano_multiacto(),
        funcao_comunicativa={"funcao": "informacao"},
    )
    plano = {**_plano_multiacto(), "contrato_fala": contrato}
    avaliacao = avaliar_qualidade_comunicacao(
        texto,
        "Tô bem por aqui. E você, como tá?",
        plano=plano,
    )
    reparo = avaliacao["contrato_reparo"]
    mensagens = montar_mensagens_reparo_comunicacao(
        texto,
        "Tô bem por aqui. E você, como tá?",
        avaliacao,
    )

    assert avaliacao["aceita"] is False
    assert "ato_opiniao_nao_respondido" in avaliacao["problemas"]
    assert "estado_pessoal" in reparo["atos_obrigatorios"]
    assert "opiniao" in reparo["atos_obrigatorios"]
    assert reparo["referente"] == "rock ou metal"
    assert "cada item de atos_obrigatorios" in mensagens[0]["content"]


def test_contingencia_multiacto_nao_abandona_a_pergunta_final() -> None:
    fala = contingencia_comunicacao(
        "Tá tudo bem, você prefere rock ou metal?",
        contrato_reparo={
            "estrategia": "resposta_multiacto",
            "atos_obrigatorios": ["conversa", "estado_pessoal", "pergunta", "opiniao"],
            "referente": "rock ou metal",
        },
    )

    assert fala.startswith("Que bom saber.")
    assert "prefiro rock" in fala
    assert "porque" in fala
    assert fala != "Tô bem por aqui. E você, como tá?"


def test_preferencia_degradada_e_estavel_quando_opcoes_invertem() -> None:
    contrato = {
        "estrategia": "resposta_multiacto",
        "atos_obrigatorios": ["estado_pessoal", "opiniao"],
    }
    direta = contingencia_comunicacao(
        "Tá tudo bem, você prefere rock ou metal?",
        contrato_reparo={**contrato, "referente": "rock ou metal"},
    )
    invertida = contingencia_comunicacao(
        "Tá tudo bem, você prefere metal ou rock?",
        contrato_reparo={**contrato, "referente": "metal ou rock"},
    )

    assert "prefiro rock" in direta
    assert "prefiro rock" in invertida
