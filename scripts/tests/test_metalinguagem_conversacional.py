"""Contratos de conversa para exemplos e perguntas sobre formulação."""

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.interpretacao_social import analisar_ato_social
from mente_laylay.cognicao.normalizacao_linguagem import texto_e_metalinguistico
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.cognicao.validacao_contrato_fala import (
    validar_aderencia_contrato_fala,
)
from mente_laylay.cognicao.qualidade_comunicacao import contingencia_comunicacao


def _contrato(texto: str) -> dict:
    return construir_contrato_semantico_fala(
        texto,
        plano={
            "resposta_esperada": "responder ao conteudo atual",
            "permite_pergunta": True,
        },
        mente={},
    )


def test_pergunta_sobre_evidencia_textual_preserva_objeto_no_contrato():
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    for texto in (
        "Esse relato informa se a lâmpada está ligada neste momento?",
        "Esse pedido prova que o arquivo foi lido?",
        "Esse relato confirma que meus e-mails foram lidos?",
    ):
        turno = classificar_modalidade_turno(texto)
        assert turno["veto_execucao_operacional"]
        contrato = construir_contrato_semantico_fala(texto, turno=turno)
        assert contrato["roteiro_concreto"]["estrategia"] == "analise_evidencia_textual"
        assert "pedir" in contrato["roteiro_concreto"]["nucleo_resposta"]
        assert not contrato["autoriza_execucao"]


def test_consulta_real_e_relato_simples_nao_viram_metalinguagem():
    for texto in ("A lâmpada está ligada?", "Leia meus e-mails.", "Esse relato é interessante."):
        assert not texto_e_metalinguistico(texto)


def test_como_eu_perguntaria_nao_vira_pergunta_de_bem_estar() -> None:
    texto = "Como eu perguntaria se o Opera está aberto?"

    assert analisar_ato_social(texto).get("tipo") != "WELLBEING"
    assert _contrato(texto)["roteiro_concreto"]["estrategia"] != (
        "reciprocidade_social"
    )


def test_pergunta_de_bem_estar_explicitamente_dirigida_continua_social() -> None:
    for texto in ("Como você está?", "Como a Laylay está?"):
        assert analisar_ato_social(texto)["tipo"] == "WELLBEING"
        assert _contrato(texto)["roteiro_concreto"]["estrategia"] == (
            "reciprocidade_social"
        )


def test_pergunta_sobre_formulacao_recebe_contrato_metalinguistico() -> None:
    contrato = _contrato("Como eu perguntaria se o Opera está aberto?")

    assert "metalinguagem" in contrato["atos"]
    assert contrato["roteiro_concreto"]["estrategia"] == (
        "resposta_metalinguistica"
    )
    assert contrato["autoriza_execucao"] is False


def test_pergunta_sobre_formulacao_precisa_entregar_a_formulacao_diretamente() -> None:
    texto = "Como eu perguntaria se o Opera está aberto?"
    contrato = _contrato(texto)

    indireta = validar_aderencia_contrato_fala(
        texto,
        (
            'A frase "o Opera está aberto?" é apenas um exemplo de estrutura. '
            "Se quiser, posso mostrar outra forma."
        ),
        contrato_fala=contrato,
    )
    direta = validar_aderencia_contrato_fala(
        texto,
        'Você pode perguntar assim: "O Opera está aberto?"',
        contrato_fala=contrato,
    )

    assert "metalinguagem_nao_entregou_formulacao_direta" in indireta["problemas"]
    assert indireta["aceita"] is False
    assert direta["aceita"] is True


def test_citacao_e_exemplo_nao_viram_consulta_factual_na_fala() -> None:
    casos = (
        '"O Opera está aberto?"',
        'A frase "o Opera está aberto?" é apenas um exemplo.',
        'Se eu disser "o Opera está aberto?", isso é uma consulta.',
    )

    for texto in casos:
        contrato = _contrato(texto)
        assert contrato["roteiro_concreto"]["estrategia"] == (
            "resposta_metalinguistica"
        )


def test_hipotese_sobre_capacidade_nao_e_confundida_com_citacao() -> None:
    assert texto_e_metalinguistico(
        "Se eu falar para você criar um arquivo, você vai criar?"
    ) is False


def test_validador_rejeita_responder_conteudo_embutido_como_fato_atual() -> None:
    texto = "Como eu perguntaria se o Opera está aberto?"
    contrato = _contrato(texto)

    ruim = validar_aderencia_contrato_fala(
        texto,
        "O Opera está aberto pra mim, ou é só o que eu acho que está?",
        contrato_fala=contrato,
    )
    boa = validar_aderencia_contrato_fala(
        texto,
        'Você pode perguntar exatamente assim: "O Opera está aberto?"',
        contrato_fala=contrato,
    )

    assert "metalinguagem_tratada_como_conteudo" in ruim["problemas"]
    assert ruim["aceita"] is False
    assert boa["aceita"] is True


def test_metalinguagem_nao_inventa_leitura_alternativa_nao_solicitada() -> None:
    texto = '"O Opera está aberto?"'
    contrato = _contrato(texto)

    resultado = validar_aderencia_contrato_fala(
        texto,
        (
            'A frase "O Opera está aberto?" é uma pergunta para confirmar se o '
            "programa está ativo, mas também pode ser interpretada como uma "
            "forma de verificar foco ou atenção."
        ),
        contrato_fala=contrato,
    )
    direta = validar_aderencia_contrato_fala(
        texto,
        "Essa frase é uma pergunta direta para saber se o Opera está aberto.",
        contrato_fala=contrato,
    )

    assert "metalinguagem_inventou_leitura_alternativa" in resultado["problemas"]
    assert resultado["aceita"] is False
    assert direta["aceita"] is True


def test_guardiao_factual_nao_confunde_exemplo_com_obra_ou_fato_externo() -> None:
    texto = "Como eu perguntaria se o Opera está aberto?"
    contrato = _contrato(texto)
    plano = {
        "texto_usuario": texto,
        "dominio": "conversa",
        "contrato_fala": contrato,
    }

    resultado = verificar_fala_turno(
        'Você pode perguntar exatamente assim: "O Opera está aberto?"',
        plano=plano,
    )

    assert "obra_sem_evidencia" not in resultado["problemas"]
    assert "alegacao_especifica_sem_fonte" not in resultado["problemas"]
    assert resultado["aceita"] is True


def test_metalinguagem_nao_desliga_protecao_para_data_externa_inventada() -> None:
    texto = 'A frase "o Opera está aberto?" é apenas um exemplo.'
    contrato = _contrato(texto)

    resultado = verificar_fala_turno(
        'A frase "o Opera está aberto?" foi criada em 1999 como exemplo.',
        plano={
            "texto_usuario": texto,
            "dominio": "conversa",
            "contrato_fala": contrato,
        },
    )

    assert "data_sem_evidencia" in resultado["problemas"]


def test_contingencia_metalinguistica_responde_ao_sentido_sem_pedir_detalhe() -> None:
    texto = 'Se eu disser "o Opera está aberto?", isso é uma consulta.'
    contrato = _contrato(texto)

    fala = contingencia_comunicacao(
        texto,
        contrato_reparo=contrato["roteiro_concreto"],
    )

    assert "consulta" in fala.casefold()
    assert any(termo in fala.casefold() for termo in ("citada", "exemplo", "frase"))
    assert "detalhe" not in fala.casefold()
    assert "não" in fala.casefold() and "executei" in fala.casefold()


def test_metalinguagem_nao_pode_contradizer_classificacao_explicita() -> None:
    texto = 'Se eu disser "o Opera está aberto?", isso é uma consulta.'
    contrato = _contrato(texto)

    resultado = validar_aderencia_contrato_fala(
        texto,
        "Não é uma consulta; é só uma metáfora de presença.",
        contrato_fala=contrato,
    )

    assert "metalinguagem_contradisse_classificacao" in resultado["problemas"]
    assert resultado["aceita"] is False


def test_metalinguagem_nao_puxa_citacao_ausente_do_turno_atual() -> None:
    texto = "A palavra aberto aparece aqui, mas não consulte nada."
    contrato = _contrato(texto)

    resultado = validar_aderencia_contrato_fala(
        texto,
        'Entendi. A frase "o Opera está aberto?" não é uma consulta.',
        contrato_fala=contrato,
    )
    ancorada = validar_aderencia_contrato_fala(
        texto,
        'Entendi: você está falando da palavra "aberto"; não fiz uma consulta.',
        contrato_fala=contrato,
    )
    entidade_sem_aspas = validar_aderencia_contrato_fala(
        texto,
        'Entendi. A palavra "aberto" é só um estado. O Opera está lá.',
        contrato_fala=contrato,
    )
    negacao_permanente = validar_aderencia_contrato_fala(
        texto,
        'Entendi. A palavra "aberto" é só um estado. Não faço consultas.',
        contrato_fala=contrato,
    )

    assert "metalinguagem_citou_conteudo_ausente" in resultado["problemas"]
    assert resultado["aceita"] is False
    assert "metalinguagem_introduziu_entidade_ausente" in (
        entidade_sem_aspas["problemas"]
    )
    assert entidade_sem_aspas["aceita"] is False
    assert "metalinguagem_negou_capacidade" in negacao_permanente["problemas"]
    assert negacao_permanente["aceita"] is False
    assert ancorada["aceita"] is True
