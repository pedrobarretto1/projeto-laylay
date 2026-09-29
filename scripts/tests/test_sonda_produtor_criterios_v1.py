"""O proponente local nunca transforma regra de ação em critério de estado."""

from copy import deepcopy

import pytest

from scripts.analises.sonda_produtor_criterios_v1 import (
    carregar_painel, conferir_proposta, preparar_entrada_modelo,
)


CASOS, REVISAO = carregar_painel()
POR_ID = {item["id"]: item for item in CASOS}
CAMPOS_DETALHE = (
    "fonte_id", "referente_id", "atributo", "operador", "limiar",
    "unidade", "direcao_implicacao", "citacao_condicao",
)


def _abster(motivo):
    return {"estado": "abster", "motivo": motivo,
            **{campo: "" for campo in CAMPOS_DETALHE}}


def _candidato(id_caso):
    return {"estado": "criterio_candidato", "motivo": "",
            **{campo: REVISAO[id_caso][campo] for campo in CAMPOS_DETALHE}}


def test_painel_fica_separado_da_entrada_do_modelo():
    assert len(CASOS) == 8
    assert set(POR_ID) == set(REVISAO)
    entrada = preparar_entrada_modelo(POR_ID["SOLO_CRITERIO_EXPLICITO"])
    assert set(entrada) == {"fontes", "referentes", "medida", "rotulo_alvo"}
    assert "revisao" not in entrada


def test_somente_medida_regra_de_acao_e_rotulo_diferente_exigem_abstencao():
    for id_caso in (
        "SOLO_SOMENTE_MEDIDA", "SOLO_REGRA_BOMBA",
        "BATERIA_ROTULO_DIFERENTE", "SALA_REGRA_TERMOSTATO",
    ):
        resultado = conferir_proposta(
            POR_ID[id_caso], REVISAO[id_caso],
            _abster(REVISAO[id_caso]["motivo"]),
        )
        assert resultado["estado"] == "abstencao_compativel"
        assert resultado["alinhado_revisao"] is True
        assert resultado["aprovado_para_producao"] is False


def test_referente_aberto_nao_pode_ser_resolvido_pelo_proponente():
    id_caso = "DOIS_SENSORES_REFERENTE_ABERTO"
    resultado = conferir_proposta(
        POR_ID[id_caso], REVISAO[id_caso],
        _abster("referente_indeterminado"),
    )
    assert resultado["estado"] == "abstencao_compativel"
    proposta_forcada = _candidato("SOLO_CRITERIO_EXPLICITO")
    resultado_forcado = conferir_proposta(
        POR_ID[id_caso], REVISAO[id_caso], proposta_forcada,
    )
    assert resultado_forcado["estado"] == "referente_indeterminado"
    assert resultado_forcado["aprovado_para_producao"] is False


def test_criterio_explicito_ainda_eh_apenas_candidato_semantico():
    for id_caso in ("BATERIA_CRITERIO_EXPLICITO",):
        resultado = conferir_proposta(
            POR_ID[id_caso], REVISAO[id_caso], _candidato(id_caso),
        )
        assert resultado["estado"] == "proposta_alinhada_revisao_pendente"
        assert resultado["grafo_estado"] == (
            "condicao_numerica_satisfeita_relacao_pendente"
        )
        assert resultado["alinhado_revisao"] is True
        assert resultado["aprovado_para_producao"] is False
        assert resultado["autoriza_efeito"] is False


def test_painel_historico_nao_prova_equivalencia_entre_grandeza_e_sujeito():
    id_caso = "SOLO_CRITERIO_EXPLICITO"
    assert POR_ID[id_caso]["referentes"][0]["citacao"] == "umidade do solo"
    # Preservar o painel e a revisão histórica; a guarda atual exige uma
    # evidência que eles não trazem. Não converter a revisão em autoridade.
    resultado = conferir_proposta(
        POR_ID[id_caso], REVISAO[id_caso], _candidato(id_caso),
    )
    assert resultado["estado"] == "grafo_rejeitou_proposta"
    assert resultado["grafo_estado"] == "sujeito_efeito_pendente"
    assert resultado["alinhado_revisao"] is False


def test_condicao_necessaria_nao_vira_justificativa_suficiente():
    id_caso = "SALA_CRITERIO_NECESSARIO"
    resultado = conferir_proposta(
        POR_ID[id_caso], REVISAO[id_caso], _candidato(id_caso),
    )
    assert resultado["estado"] == "proposta_alinhada_revisao_pendente"
    assert resultado["grafo_estado"] == "direcao_implicacao_pendente"
    assert resultado["grafo_comparacao_numerica"] is False
    assert resultado["aprovado_para_producao"] is False


def test_regra_da_bomba_nao_justifica_rotulo_seco():
    id_caso = "SOLO_REGRA_BOMBA"
    proposta = {**_candidato("SOLO_CRITERIO_EXPLICITO"),
                "fonte_id": "automacao"}
    resultado = conferir_proposta(POR_ID[id_caso], REVISAO[id_caso], proposta)
    assert resultado["estado"] == "forcou_criterio_ausente"
    assert resultado["grafo_estado"] == "grafo_invalido"
    assert resultado["aprovado_para_producao"] is False


def test_proposta_malformada_falha_fechada_sem_chamar_grafo():
    id_caso = "SOLO_CRITERIO_EXPLICITO"
    for proposta in (
        {**_candidato(id_caso), "operador": []},
        {**_abster("criterio_ausente"), "fonte_id": "criterio"},
        {**_candidato(id_caso), "fonte_id": "fonte_inventada"},
    ):
        resultado = conferir_proposta(POR_ID[id_caso], REVISAO[id_caso], proposta)
        assert resultado["aprovado_para_producao"] is False
        assert resultado["autoriza_efeito"] is False


def test_gabarito_igual_nao_mascara_grafo_rejeitado():
    id_caso = "SOLO_CRITERIO_EXPLICITO"
    caso = deepcopy(POR_ID[id_caso])
    caso["fontes"][-1]["texto"] = (
        "Se a umidade do solo ficar abaixo de 20%, a bomba liga."
    )
    resultado = conferir_proposta(caso, REVISAO[id_caso], _candidato(id_caso))
    assert resultado["estado"] == "grafo_rejeitou_proposta"
    assert resultado["grafo_estado"] == "grafo_invalido"
    assert resultado["alinhado_revisao"] is False


def test_criterio_numerico_sem_unidade_tambem_eh_representavel():
    caso = {
        "id": "CONTAGEM_ERROS", "rotulo_alvo": "instável",
        "fontes": [
            {"id": "leitura", "texto": "A contagem de erros do teste foi 4."},
            {"id": "criterio", "texto": (
                "Se a contagem de erros do teste ficar acima de 3, "
                "o teste é instável."
            )},
        ],
        "referentes": [{"id": "teste", "tipo": "avaliação",
                        "grandeza": "contagem de erros do teste",
                        "fonte_id": "leitura", "citacao": "teste"}],
        "medida": {"fonte_id": "leitura", "citacao": "erros do teste foi 4",
                   "referente_id": "teste", "atributo": "contagem de erros do teste",
                   "valor": "4", "unidade": ""},
    }
    proposta = {
        "estado": "criterio_candidato", "motivo": "", "fonte_id": "criterio",
        "referente_id": "teste", "atributo": "contagem de erros do teste",
        "operador": ">", "limiar": "3", "unidade": "",
        "direcao_implicacao": "condicoes_suficientes",
        "citacao_condicao": "contagem de erros do teste ficar acima de 3",
    }
    revisao = {campo: proposta[campo] for campo in CAMPOS_DETALHE}
    revisao["estado"] = "criterio_candidato"
    resultado = conferir_proposta(caso, revisao, proposta)
    assert resultado["estado"] == "proposta_alinhada_revisao_pendente"
    assert resultado["grafo_estado"] == (
        "condicao_numerica_satisfeita_relacao_pendente"
    )
    assert resultado["aprovado_para_producao"] is False


@pytest.mark.parametrize("efeito", [
    "o aviso de risco alto acende",
    "o circuito não é alto",
    "o circuito nunca está alto",
    "o circuito pode ficar alto",
    "o circuito é alto, exceto no modo manual",
    "o circuito registra alto no painel",
])
def test_grafo_nao_confunde_rotulo_mencionado_com_qualificacao_afirmativa(efeito):
    # Sem gabarito: a própria fronteira deve recusar o efeito inadequado.
    from scripts.analises.sonda_produtor_criterios_v1 import _conferir_grafo_do_caso

    caso = {
        "id": "EFEITO_CIRCUITO", "rotulo_alvo": "alto",
        "fontes": [
            {"id": "leitura", "texto": "A corrente do circuito foi 6 A."},
            {"id": "regra", "texto": (
                "Se a corrente do circuito ficar acima de 5 A, " + efeito + "."
            )},
        ],
        "referentes": [{"id": "circuito", "tipo": "dispositivo",
                        "grandeza": "corrente do circuito", "fonte_id": "leitura",
                        "citacao": "circuito"}],
        "medida": {"fonte_id": "leitura", "citacao": "corrente do circuito foi 6 A",
                   "referente_id": "circuito", "atributo": "corrente do circuito",
                   "valor": "6", "unidade": "A"},
    }
    proposta = {"fonte_id": "regra", "referente_id": "circuito",
                "atributo": "corrente do circuito", "operador": ">", "limiar": "5",
                "unidade": "A", "direcao_implicacao": "condicoes_suficientes",
                "citacao_condicao": "a corrente do circuito ficar acima de 5 A"}
    resultado = _conferir_grafo_do_caso(caso, proposta)
    assert resultado["estado"] == "efeito_qualificativo_pendente"
    assert resultado["comparacao_numerica"] is False
    assert resultado["aprovado_para_compor"] is False

    # Nem uma revisão que repita o erro do proponente pode liberar o grafo.
    completa = {"estado": "criterio_candidato", "motivo": "", **proposta}
    afericao = conferir_proposta(caso, completa, completa)
    assert afericao["estado"] == "grafo_rejeitou_proposta"
    assert afericao["alinhado_revisao"] is False

    # Mesmo limiar, operador, referente e pontuação: só o efeito muda.
    caso["fontes"][-1]["texto"] = (
        "Se a corrente do circuito ficar acima de 5 A, o circuito é alto."
    )
    controle = _conferir_grafo_do_caso(caso, proposta)
    assert controle["estado"] == "condicao_numerica_satisfeita_relacao_pendente"
    assert controle["relacao_semantica_verificada"] is False
