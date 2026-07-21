from __future__ import annotations

from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia
from mente_laylay.autonomia.pre_fluxo_contextual import responder_conversa_social_curta
from mente_laylay.cognicao.fundamentacao_factual import extrair_tema_fundamentacao
from mente_laylay.cognicao.identidade_conversacional import ajustar_autorreferencia_assistente
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.personalidade.conversa_natural import responder_conversa_curta_por_tipo


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
    ):
        turno = _turno(texto)
        assert turno["modalidade_geral"] == "misto"
        assert turno["atos"] == ["conversa", "pergunta"]
        plano = planejar_turno(texto, turno=turno)
        assert "sem ignorar nenhum dos atos" in plano["resposta_esperada"]


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


def test_tema_factual_e_extraido_depois_da_resposta_social() -> None:
    assert extrair_tema_fundamentacao(
        "ta tudo bem sim lay, voce gosta do slipknot?"
    ).casefold() == "slipknot"


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
