"""A LLM apenas propõe; a cobertura e as fontes são verificadas fora dela."""

from mente_laylay.cognicao.auditoria_alegacoes_didaticas import (
    auditar_fala_didatica_sombra,
)
from scripts.analises.sonda_propostas_alegacoes_fala import (
    conferir_classificacao_qualitativa,
    conferir_proposta,
)


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


def test_derivacao_qualitativa_proposta_chega_ao_verificador_externo():
    fala = "Isso é bastante seco."
    resultado = conferir_proposta(fala, _fonte("O sensor leu 15% de umidade."), {
        "alegacoes": [{
            "indice": 0, "papel": "conclusao_derivada",
            "evidencias": [{"fonte_id": "u", "citacao": "15% de umidade"}],
            "derivacao": {"tipo": "qualificacao_qualitativa",
                          "referente_id": "solo", "atributo": "umidade",
                          "valor": "15", "unidade": "%", "rotulo": "seco",
                          "medida_fonte_id": "u", "criterio_fonte_id": ""},
        }],
    })
    assert resultado["alegacoes"][0]["estado"] == "qualificacao_sem_criterio"
    assert resultado["aprovado_para_producao"] is False


def test_triagem_qualitativa_localiza_rotulo_sem_validar_o_sentido():
    fala = "A leitura foi 15%. Isso é bastante seco."
    segmentos = auditar_fala_didatica_sombra(
        fala, fontes={}, plano_id="teste",
    )["segmentos"]
    propostas = [{"indice": indice, "tipo": "outro", "rotulo": ""}
                 for indice in range(len(segmentos))]
    propostas[-1].update(tipo="qualificacao_qualitativa", rotulo="seco")
    resultado = conferir_classificacao_qualitativa(
        fala, {"segmentos": propostas},
    )
    assert resultado["estado"] == "candidatos_qualitativos_revisao_pendente"
    assert [item["rotulo"] for item in resultado["candidatos"]] == ["seco"]
    assert resultado["classificacao_verificada"] is False
    assert resultado["aprovado_para_producao"] is False


def test_triagem_qualitativa_rejeita_rotulo_ou_indice_forjado():
    fala = "A função retorna True quando x > 0."
    bruto = {"segmentos": [{"indice": 0, "tipo": "outro", "rotulo": ""}]}
    assert conferir_classificacao_qualitativa(fala, bruto)["candidatos"] == []
    bruto["segmentos"][0].update(tipo="qualificacao_qualitativa",
                                 rotulo="seco")
    assert conferir_classificacao_qualitativa(fala, bruto)["estado"] \
        == "classificacao_invalida"


def test_triagem_qualitativa_tipo_malformado_falha_fechada_sem_excecao():
    fala = "A bateria está fraca."
    segmentos = auditar_fala_didatica_sombra(
        fala, fontes={}, plano_id="teste",
    )["segmentos"]
    bruto = {"segmentos": [
        {"indice": indice, "tipo": ["qualificacao_qualitativa"],
         "rotulo": "fraca"}
        for indice, _ in enumerate(segmentos)
    ]}
    resultado = conferir_classificacao_qualitativa(fala, bruto)
    assert resultado["estado"] == "classificacao_invalida"
    assert resultado["aprovado_para_producao"] is False
    bruto["segmentos"][0].update(indice=1)
    assert conferir_classificacao_qualitativa(fala, bruto)["estado"] \
        == "classificacao_invalida"
