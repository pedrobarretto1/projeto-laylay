from __future__ import annotations

from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia
from mente_laylay.autonomia.pre_fluxo_contextual import responder_conversa_social_curta
from mente_laylay.cognicao.fundamentacao_factual import extrair_tema_fundamentacao
from mente_laylay.cognicao.identidade_conversacional import ajustar_autorreferencia_assistente
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.personalidade.conversa_natural import (
    resolver_equacao_linear_local,
    responder_conversa_curta_por_tipo,
    resposta_pergunta_curta_dependente_topico,
)


def test_equacao_linear_e_resolvida_localmente_com_resposta_curta_completa() -> None:
    fala = resolver_equacao_linear_local(
        "resolva passo a passo: 3(2x-5)-4(x+1)=2(3x-7)+9"
    )

    assert "lado esquerdo vira 2x - 19" in fala
    assert "direito vira 6x - 5" in fala
    assert "-4x igual a 14" in fala
    assert fala.endswith("x é igual a -3,5.")
    assert len(fala) < 400


def test_pre_fluxo_nao_substitui_llm_por_fala_matematica_local() -> None:
    texto = "resolva passo a passo: 3(2x-5)-4(x+1)=2(3x-7)+9"
    falas: list[str] = []
    contexto = {
        "mente_integrada_estado": {"pendencia_atual": {}},
        "_contexto_horario_atual": lambda: "tarde",
        "_refinar_contexto_mental": lambda _texto: {},
        "_resposta_conversa_rapida_local": lambda entrada: resolver_equacao_linear_local(entrada),
        "_texto_social_curto": lambda _texto: False,
        "_texto_conversa_casual_sem_acao": lambda _texto: False,
        "_emitir_resposta_curta": lambda _entrada, fala, **_kwargs: falas.append(fala),
    }
    contexto["_recarregar_contexto_inicio"] = lambda: dict(contexto)

    assert processar_inicio_fluxo_resposta_ia(contexto, texto) is False
    assert falas == []


def _turno(texto: str) -> dict:
    return classificar_modalidade_turno(
        texto,
        normalizar_texto=lambda valor: str(valor).casefold(),
        texto_tem_comando_explicito=lambda _texto: False,
    )


def test_bem_estar_seguido_de_pergunta_e_turno_composto() -> None:
    for texto in (
        "ta tudo bem sim lay, voce gosta do slipknot?",
        "eu to bem, voce gosta de slipknot?",
        "estou bem também. Você gosta de Slipknot?",
        "estou bem também! Você prefere rock ou metal?",
    ):
        turno = _turno(texto)
        assert turno["modalidade_geral"] == "misto"
        assert turno["atos"] == ["conversa", "pergunta"]
        plano = planejar_turno(texto, turno=turno)
        assert "sem ignorar nenhum dos atos" in plano["resposta_esperada"]


def test_resposta_social_com_pergunta_reciproca_eliptica_e_turno_composto() -> None:
    for texto in (
        "foi tudo bem, e o seu?",
        "tô bem; mas e você?",
        "meu dia foi tranquilo e o seu?",
        "por aqui está tudo certo, e por aí?",
    ):
        turno = _turno(texto)
        assert turno["modalidade_geral"] == "misto"
        assert turno["atos"] == ["conversa", "pergunta"]


def test_atalho_social_nao_engole_pergunta_temática() -> None:
    texto = "ta tudo bem sim lay, voce gosta do slipknot?"
    falas: list[str] = []
    tratado, etapa = responder_conversa_social_curta({
        "mente_integrada_estado": {"turno_atual": _turno(texto)},
        "_texto_social_curto": lambda _texto: False,
        "_texto_conversa_casual_sem_acao": lambda _texto: True,
        "_texto_tem_comando_explicito": lambda _texto: False,
        "_resposta_conversa_rapida_local": lambda _texto: "Resposta social incompleta.",
        "_emitir_resposta_curta": lambda *_args, **_kwargs: falas.append("falou"),
    }, texto, emocao="calma", nivel=1)

    assert tratado is False
    assert etapa == ""
    assert falas == []


def test_pre_fluxo_completo_nao_trata_apenas_bem_estar_com_retrato_atrasado() -> None:
    texto = "eu estou bem lay, voce gosta de slipknot?"
    falas: list[str] = []
    contexto = {
        "mente_integrada_estado": {
            # Simula o retrato transitório anterior que causava o erro real.
            "pergunta_aberta_texto": "E você, como tá?",
            "pendencia_atual": {},
        },
        "_contexto_horario_atual": lambda: "tarde",
        "_registrar_interacao_temporal": lambda _texto: None,
        "_refinar_contexto_mental": lambda _texto: None,
        "_texto_tem_comando_explicito": lambda _texto: False,
        "_texto_social_curto": lambda _texto: False,
        "_texto_conversa_casual_sem_acao": lambda _texto: True,
        "_texto_responde_pergunta_aberta": lambda _texto: True,
        "_responder_pergunta_aberta": lambda _texto: "Bom. Ai meu sistema ate respira mais bonito.",
        "_resposta_conversa_rapida_local": lambda _texto: "Bom. Ai meu sistema ate respira mais bonito.",
        "_emitir_resposta_curta": lambda *_args, **_kwargs: falas.append("falou"),
    }
    contexto["_recarregar_contexto_inicio"] = lambda: dict(contexto)

    tratado = processar_inicio_fluxo_resposta_ia(contexto, texto)

    assert tratado is False
    assert falas == []


def test_pre_fluxo_nao_engole_pergunta_apos_ponto_com_retrato_atrasado() -> None:
    texto = "estou bem também. Você gosta de Slipknot?"
    falas: list[str] = []
    contexto = {
        "mente_integrada_estado": {
            "pergunta_aberta_texto": "E você, como tá?",
            "pendencia_atual": {},
        },
        "_contexto_horario_atual": lambda: "tarde",
        "_registrar_interacao_temporal": lambda _texto: None,
        "_refinar_contexto_mental": lambda _texto: None,
        "_texto_tem_comando_explicito": lambda _texto: False,
        "_texto_social_curto": lambda _texto: False,
        "_texto_conversa_casual_sem_acao": lambda _texto: True,
        "_texto_responde_pergunta_aberta": lambda _texto: True,
        "_responder_pergunta_aberta": lambda _texto: "Que bom. Fico mais tranquila.",
        "_resposta_conversa_rapida_local": lambda _texto: "Que bom. Fico mais tranquila.",
        "_emitir_resposta_curta": lambda *_args, **_kwargs: falas.append("falou"),
    }
    contexto["_recarregar_contexto_inicio"] = lambda: dict(contexto)

    tratado = processar_inicio_fluxo_resposta_ia(contexto, texto)

    assert tratado is False
    assert falas == []


def test_pre_fluxo_nao_engole_pergunta_reciproca_com_retrato_atrasado() -> None:
    texto = "foi tudo bem, e o seu?"
    falas: list[str] = []
    contexto = {
        "mente_integrada_estado": {
            "pergunta_aberta_texto": "Como foi seu começo de dia?",
            "pendencia_atual": {},
        },
        "_contexto_horario_atual": lambda: "manhã",
        "_registrar_interacao_temporal": lambda _texto: None,
        "_refinar_contexto_mental": lambda _texto: None,
        "_texto_tem_comando_explicito": lambda _texto: False,
        "_texto_social_curto": lambda _texto: False,
        "_texto_conversa_casual_sem_acao": lambda _texto: True,
        "_texto_responde_pergunta_aberta": lambda _texto: True,
        "_responder_pergunta_aberta": lambda _texto: "Resposta só da primeira parte.",
        "_resposta_conversa_rapida_local": lambda _texto: "Resposta só da primeira parte.",
        "_emitir_resposta_curta": lambda *_args, **_kwargs: falas.append("falou"),
    }
    contexto["_recarregar_contexto_inicio"] = lambda: dict(contexto)

    tratado = processar_inicio_fluxo_resposta_ia(contexto, texto)

    assert tratado is False
    assert falas == []


def test_preferencia_pessoal_depois_da_resposta_social_nao_vira_pesquisa() -> None:
    assert extrair_tema_fundamentacao(
        "ta tudo bem sim lay, voce gosta do slipknot?"
    ) == ""


def test_pedido_com_assunto_novo_nao_explica_a_fala_anterior() -> None:
    import time

    contexto = {
        "mente_integrada_estado": {
            "ultima_resposta": "O metal é mais focado em intensidade.",
            "ultima_opiniao": "O metal é mais focado em intensidade.",
            "continuidade_fala_ts": time.time(),
        },
        "_normalizar_texto_curto": lambda texto: str(texto).casefold(),
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "ultimo_topico_conversa": "metal",
        "foco_vivo": {},
    }

    assert resposta_pergunta_curta_dependente_topico(
        contexto, "me explica o que é inteligência artificial"
    ) == ""
    assert resposta_pergunta_curta_dependente_topico(
        contexto, "explica isso melhor"
    )


def test_opiniao_sem_fonte_nao_inventa_repertorio_nem_chama_usuario_de_laylay() -> None:
    chamadas_llm: list[object] = []
    ctx = {
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "_normalizar_texto_curto": lambda texto: str(texto).casefold(),
        "_ajustar_fala_por_horario": lambda fala, *_args: fala,
        "_pesquisar_contexto_tema": lambda _tema: {},
        "enviar_mensagem": lambda *args, **kwargs: chamadas_llm.append((args, kwargs)),
        "mente_integrada_estado": {},
        "foco_vivo": {},
    }

    fala = responder_conversa_curta_por_tipo(ctx, "OPINION", "voce gosta do slipknot?")

    assert chamadas_llm == []
    assert "não conheço slipknot o bastante" in fala.casefold()
    assert "laylay" not in fala.casefold()
    assert "vocês" not in fala.casefold()


def test_vocativo_invertido_da_assistente_e_removido() -> None:
    fala = ajustar_autorreferencia_assistente("É complicado, Laylay. Eu ainda estou formando uma opinião.")

    assert fala == "É complicado. Eu ainda estou formando uma opinião."
