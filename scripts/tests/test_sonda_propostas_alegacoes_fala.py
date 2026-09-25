"""A LLM apenas propõe; a cobertura e as fontes são verificadas fora dela."""

from scripts.analises.sonda_propostas_alegacoes_fala import conferir_proposta


def _fonte(texto):
    return {"u": {"origem": "usuario", "texto": texto}}


def _proposta(indice, papel="premissa_usuario", citacao=""):
    return {"indice": indice, "papel": papel, "evidencias": (
        [{"fonte_id": "u", "citacao": citacao}] if citacao else []
    )}


def test_omissao_e_duplicacao_de_segmento_rejeitadas_antes_da_semantica():
    fala = "A leitura foi 15%. Isso garante flores."
    for itens in ([ _proposta(0) ], [ _proposta(0), _proposta(0) ]):
        resultado = conferir_proposta(
            fala, _fonte("A leitura foi 15%."), {"alegacoes": itens},
        )
        assert resultado["estado"] == "indices_invalidos"
        assert resultado["aprovado_para_producao"] is False


def test_cauda_sem_fonte_aparece_separada_da_premissa_literal():
    fala = "A leitura foi 15%. Isso garante flores."
    resultado = conferir_proposta(fala, _fonte("A leitura foi 15%."), {
        "alegacoes": [
            _proposta(0, citacao="A leitura foi 15%"),
            _proposta(1, "conclusao_derivada"),
        ],
    })
    assert resultado["cobertura_textual"] is True
    assert resultado["alegacoes"][0]["estado"] == "revisao_semantica_pendente"
    assert resultado["alegacoes"][1]["estado"] == "sem_fonte"
    assert resultado["aprovado_para_producao"] is False


def test_citacao_parcial_de_condicao_nao_aprova_conclusao():
    fala = "A bomba liga."
    resultado = conferir_proposta(fala, _fonte(
        "Se a umidade ficar abaixo de 20%, a bomba liga."
    ), {"alegacoes": [_proposta(0, "conclusao_derivada", "a bomba liga")]})
    assert resultado["alegacoes"][0]["estado"] == "revisao_semantica_pendente"
    assert resultado["condicoes_verificadas"] is False
    assert resultado["aprovado_para_producao"] is False


def test_modelo_nao_pode_criar_nova_fonte_nem_citacao():
    fala = "A muda floresce amanhã."
    resultado = conferir_proposta(fala, _fonte("A muda recebeu luz."), {
        "alegacoes": [_proposta(0, "fato_externo", "floresce amanhã")],
    })
    assert resultado["alegacoes"][0]["estado"] == "citacao_invalida"


def test_conta_correta_tem_recibo_independente_sem_aprovar_frase_vizinha():
    fala = "12 dividido por 3 = 4. Cada pessoa recebe 4 objetos."
    resultado = conferir_proposta(fala, _fonte(
        "Divida igualmente 12 objetos entre 3 pessoas."
    ), {"alegacoes": [
        _proposta(0, "comparacao_numerica"),
        _proposta(1, "conclusao_derivada"),
    ]})
    assert resultado["recibos_calculo"][0]["estado"] == "calculo_conferido"
    assert resultado["alegacoes"][1]["estado"] == "sem_fonte"
    assert resultado["aprovado_para_producao"] is False


def test_conta_incorreta_nunca_recebe_recibo_de_sucesso():
    fala = "12 dividido por 3 = 5."
    resultado = conferir_proposta(fala, _fonte(
        "Divida igualmente 12 objetos entre 3 pessoas."
    ), {"alegacoes": [_proposta(0, "comparacao_numerica")]})
    assert resultado["recibos_calculo"][0]["estado"] == "calculo_incorreto"
    assert resultado["aprovado_para_producao"] is False
