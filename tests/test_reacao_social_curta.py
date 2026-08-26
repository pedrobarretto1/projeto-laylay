from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.qualidade_comunicacao import contingencia_comunicacao
from mente_laylay.cognicao.reacao_social_curta import classificar_provocacao_curta
from mente_laylay.personalidade.perfil_amizade import selecionar_postura_amizade


def test_provocacao_isolada_e_reacao_social_sem_autoridade_operacional() -> None:
    leitura = classificar_provocacao_curta("boiola")

    assert leitura["tipo"] == "provocacao_curta"
    assert leitura["tom"] == "limite_firme"
    assert leitura["autoriza_execucao"] is False
    assert leitura["memorizar_como_fato"] is False


def test_tema_curto_comum_nao_e_inventado_como_provocacao() -> None:
    assert classificar_provocacao_curta("rock") == {}
    assert classificar_provocacao_curta("Minecraft") == {}


def test_contrato_orienta_reacao_social_em_vez_de_resposta_informativa() -> None:
    contrato = construir_contrato_semantico_fala("boiola")

    assert "provocacao_curta" in contrato["atos"]
    assert contrato["roteiro_concreto"]["estrategia"] == "reacao_social_curta"
    assert contrato["autoriza_execucao"] is False


def test_postura_curta_ofensiva_e_firme_sem_escalar() -> None:
    postura = selecionar_postura_amizade("sua idiota")

    assert postura.nome == "firme_debochada"
    assert postura.max_tirada == 1
    assert postura.max_frases == 2


def test_contingencia_de_provocacao_nao_expoe_falha_tecnica() -> None:
    fala = contingencia_comunicacao("boiola")

    assert any(item in fala.casefold() for item in ("provoca", "baixar", "criatividade"))
    assert "resposta saiu torta" not in fala
    assert "erro" not in fala


def test_contingencia_social_nao_repete_a_fala_recente() -> None:
    primeira = contingencia_comunicacao("boiola")
    segunda = contingencia_comunicacao("boiola", falas_evitar=[primeira])

    assert segunda != primeira


def test_fragmento_curto_desconhecido_pede_contexto_sem_fallback_tecnico() -> None:
    fala = contingencia_comunicacao("abacaxi")

    assert any(item in fala.casefold() for item in ("contexto", "completa", "legenda"))
    assert "resposta saiu torta" not in fala


def test_brincadeira_declarada_recupera_continuidade_sem_expor_verificador() -> None:
    leitura = classificar_provocacao_curta("tava tirando uma onda só")
    fala = contingencia_comunicacao("tava tirando uma onda só")

    assert leitura["tipo"] == "brincadeira_declarada"
    assert leitura["autoriza_execucao"] is False
    assert any(
        item in fala.casefold()
        for item in ("eu saquei", "era zoeira", "tá explicado")
    )
    assert "li isso" not in fala.casefold()
    assert "resposta saiu torta" not in fala.casefold()
