from __future__ import annotations

from mente_laylay.personalidade.diretor_fala import dirigir_fala
from mente_laylay.personalidade.memoria_sutil import sutilizar_referencia_memoria
from mente_laylay.personalidade.oralidade import naturalizar_texto_para_fala


def _mente_social(funcao: str, *, permite_pergunta: bool = True, operacional: bool = False) -> dict:
    return {
        "especialistas_turno_atual": {
            "social": {
                "ativo": True,
                "funcao": funcao,
                "permite_pergunta": permite_pergunta,
                "politica_resposta": (
                    "reconhecer_sem_pergunta" if not permite_pergunta else "reconhecer_e_continuar"
                ),
            },
            "operacional": {"ativo": operacional},
        }
    }


def test_agradecimento_nao_termina_com_pergunta_automatica() -> None:
    direcao = dirigir_fala(
        "Que nada, Pedro. Fico feliz que tenha ajudado. Quer conversar sobre outra coisa?",
        estado_mental=_mente_social("agradecimento", permite_pergunta=False),
    )
    assert direcao["fala"] == "Que nada, Pedro. Fico feliz que tenha ajudado."
    assert direcao["tom"] == "calorosa"


def test_agradecimento_mecanico_e_substituido_pelo_contexto_real() -> None:
    mente = _mente_social("agradecimento", permite_pergunta=False)
    mente["ultima_acao_alvo"] = "a receita da coxinha"
    direcao = dirigir_fala(
        "Tá. Isso foi fofo. Vou guardar aqui.",
        estado_mental=mente,
    )
    assert direcao["fala"] == (
        "Que nada. Fico feliz que tenha ajudado com a receita da coxinha."
    )


def test_pergunta_necessaria_de_confirmacao_e_preservada() -> None:
    direcao = dirigir_fala(
        "A pasta não está vazia. Confirma que posso prosseguir?",
        estado_mental=_mente_social("informacao", permite_pergunta=False, operacional=True),
    )
    assert "Confirma" in direcao["fala"]
    assert direcao["fala"].endswith("?")


def test_resultado_operacional_nao_recebe_raiva_fabricada() -> None:
    texto = "Não consegui desligar a lâmpada porque ela não respondeu."
    direcao = dirigir_fala(
        texto,
        estado_mental=_mente_social("informacao", operacional=True),
        emocao="irritada",
        nivel=3,
    )
    assert direcao["fala"] == texto
    assert direcao["emocao"] == "calma"
    assert direcao["preservar_resultado_operacional"] is True


def test_abertura_envergonhada_mecanica_nao_se_repete() -> None:
    mente = _mente_social("elogio", permite_pergunta=False)
    mente["ultima_resposta"] = "A-ah... obrigada."
    direcao = dirigir_fala(
        "A-ah... isso foi bonito da sua parte.",
        estado_mental=mente,
        emocao="envergonhada",
    )
    assert direcao["fala"] == "Isso foi bonito da sua parte."
    assert direcao["emocao"] == "envergonhada"


def test_conquista_recebe_alegria_proporcional() -> None:
    direcao = dirigir_fala(
        "Parabéns, essa nota foi merecida.",
        estado_mental=_mente_social("conquista"),
        emocao="calma",
        nivel=1,
    )
    assert direcao["emocao"] == "alegre"
    assert direcao["nivel"] == 2


def test_emocao_positiva_deixa_rastro_leve_no_turno_seguinte() -> None:
    mente = _mente_social("informacao")
    mente["direcao_fala_atual"] = {"emocao": "alegre", "ts": 100.0}
    direcao = dirigir_fala(
        "Gostei dessa ideia.", estado_mental=mente, emocao="calma", agora=150.0,
    )
    assert direcao["emocao"] == "alegre"
    assert direcao["nivel"] == 1


def test_oralidade_e_memoria_sutil_continuam_no_fluxo() -> None:
    texto = "### Ingredientes\n- Farinha: 300g\n- Ovos: 3"
    fala = naturalizar_texto_para_fala(texto)
    assert "300 gramas de farinha" in fala
    assert "Segundo minha memória" not in sutilizar_referencia_memoria(
        "Segundo minha memória, você gosta dessa playlist."
    )


def test_resposta_social_generica_ganha_presenca_sem_pergunta_artificial() -> None:
    direcao = dirigir_fala(
        "Entendi.",
        estado_mental=_mente_social("desabafo", permite_pergunta=False),
    )
    assert direcao["fala"] == "Eu ouvi. Não vou te apressar nem transformar isso em tarefa."
    assert "?" not in direcao["fala"]


def test_carisma_social_nao_enfeita_resultado_operacional() -> None:
    texto = "Certo."
    direcao = dirigir_fala(
        texto,
        estado_mental=_mente_social("brincadeira", operacional=True),
    )
    assert direcao["fala"] == texto


def test_voz_unica_preserva_texto_mesmo_quando_diretor_trocaria_resposta() -> None:
    texto = "Entendi. Quer conversar sobre outra coisa?"
    direcao = dirigir_fala(
        texto,
        estado_mental=_mente_social("desabafo", permite_pergunta=False),
        preservar_texto=True,
    )

    assert direcao["fala"] == texto
