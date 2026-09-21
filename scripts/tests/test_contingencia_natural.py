from mente_laylay.personalidade.contingencia_natural import fala_contingencia_natural


def test_fallback_reage_ao_progresso_sem_mencionar_falha_tecnica() -> None:
    fala = fala_contingencia_natural("to terminando minha casa")

    assert fala == "Ahh, então era isso. Vai terminando sua casa no seu ritmo — quero ver como fica."
    assert "resposta" not in fala.casefold()
    assert "modelo" not in fala.casefold()


def test_fallback_nao_finge_responder_pergunta_incompleta() -> None:
    fala = fala_contingencia_natural("essa bota é boa?")

    assert any(
        trecho in fala.casefold()
        for trecho in ("sem chutar", "faltou uma peça", "seria no chute")
    )


def test_opiniao_visual_reutiliza_detalhes_da_ultima_observacao() -> None:
    fala = fala_contingencia_natural(
        "minha casinha ta legal ne lay",
        contexto={
            "contexto_jogo_atual": {
                "ultima_observacao": (
                    "Que aconchego! Adorei a decoração com as camas amarelas "
                    "e a vista para a água."
                ),
            },
        },
    )

    assert "camas amarelas" in fala
    assert "vista para a água" in fala
    assert "acompanhando daqui" not in fala


def test_resposta_de_bem_estar_nao_cai_no_fallback_generico() -> None:
    fala = fala_contingencia_natural("to bem sim lay")

    assert any(
        trecho in fala.casefold()
        for trecho in ("bom saber", "que bom", "ótimo")
    )
    assert "acompanhando daqui" not in fala


def test_bem_estar_negativo_recebe_acolhimento() -> None:
    fala = fala_contingencia_natural("não tô muito bem lay")

    assert any(
        trecho in fala.casefold()
        for trecho in ("quer me contar", "não está bem", "parece pesado")
    )
    assert "acompanhando daqui" not in fala


def test_agradecimento_curto_tem_resposta_social() -> None:
    fala = fala_contingencia_natural("obrigado lay")

    assert any(
        trecho in fala.casefold()
        for trecho in ("de nada", "que nada", "por nada")
    )
    assert "acompanhando daqui" not in fala.casefold()
