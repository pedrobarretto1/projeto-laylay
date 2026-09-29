"""Marcador explícito restringe direção; não é gabarito semântico global."""

from scripts.analises.sinal_relacao_condicional import (
    analisar_efeito_qualificativo, analisar_marcador_condicional,
    confrontar_direcao_marcador,
)

import pytest


def test_apenas_se_e_somente_quando_indicam_condicoes_necessarias():
    for fonte in (
        "O arquivo sai apenas se a revisão terminar.",
        "A luz acende somente quando o sensor detectar movimento.",
        "A rega inicia só se o solo estiver seco.",
    ):
        sinal = analisar_marcador_condicional(fonte)
        assert sinal["estado"] == "marcador_explicito"
        assert sinal["direcao"] == "condicoes_necessarias"
        assert sinal["autoriza_efeito"] is False


def test_se_e_somente_se_e_se_simples_nao_se_confundem():
    assert analisar_marcador_condicional(
        "O painel fica verde se e somente se o autoteste passar."
    )["direcao"] == "equivalencia"
    assert analisar_marcador_condicional(
        "Se a porta abrir, o alerta toca."
    )["direcao"] == "condicoes_suficientes"


def test_quando_simples_e_negacao_ficam_indeterminados():
    for fonte in (
        "Quando o solo atingir 40%, o irrigador liga.",
        "O relatório não é publicado apenas se a revisão terminar.",
        "Ele disse: ‘se chover, talvez eu saia’.",
    ):
        sinal = analisar_marcador_condicional(fonte)
        assert sinal["estado"] == "indeterminado"
        assert sinal["direcao"] == "indeterminado"


def test_direcao_errada_eh_vetada_sem_consultar_gabarito():
    fonte = "O arquivo sai apenas se a revisão terminar."
    errado = confrontar_direcao_marcador(fonte, "condicoes_suficientes")
    assert errado["estado"] == "direcao_divergente_marcador"
    assert errado["autoriza_efeito"] is False
    correto = confrontar_direcao_marcador(fonte, "condicoes_necessarias")
    assert correto["estado"] == "direcao_compativel_marcador_revisao_pendente"
    assert correto["aprovado_para_producao"] is False


def test_tipo_invalido_na_direcao_falha_fechado():
    resultado = confrontar_direcao_marcador("Se chover, fico.", [])
    assert resultado["estado"] == "entrada_invalida"
    assert resultado["autoriza_efeito"] is False


def test_se_pronominal_antes_de_apenas_se_nao_rouba_o_marcador():
    fonte = "O motor se move apenas se o interruptor estiver ligado."
    sinal = analisar_marcador_condicional(fonte)
    assert sinal["citacao"] == "apenas se"
    assert sinal["direcao"] == "condicoes_necessarias"


def test_se_pronominal_isolado_nao_vira_regra():
    sinal = analisar_marcador_condicional("O motor se move devagar.")
    assert sinal["estado"] == "indeterminado"
    assert sinal["autoriza_efeito"] is False


@pytest.mark.parametrize("fonte,rotulo,efeito", [
    ("Se a latência ficar acima de 2,5 ms, o serviço é lento.",
     "lento", "o serviço é lento"),
    ("Se a carga ficar abaixo de 2.5 V, a bateria está fraca.",
     "fraca", "a bateria está fraca"),
    ("O solo é seco apenas se a umidade ficar abaixo de 20%.",
     "seco", "O solo é seco"),
    ("O painel fica verde se e somente se o autoteste passar.",
     "verde", "O painel fica verde"),
])
def test_efeito_preserva_trecho_e_offsets_sem_inferir_identidade(fonte, rotulo, efeito):
    resultado = analisar_efeito_qualificativo(fonte, rotulo)
    assert resultado["estado"] == "efeito_qualificativo_literal_revisao_pendente"
    assert resultado["citacao"] == efeito
    assert fonte[resultado["inicio"]:resultado["fim"]] == efeito
    assert resultado["predicado_literal"] == rotulo
    assert resultado["polaridade"] == "afirmativa_superficial"
    assert resultado["identidade_verificada"] is False
    assert resultado["aprovado_para_producao"] is False
    assert resultado["autoriza_efeito"] is False


@pytest.mark.parametrize("fonte", [
    "Se a carga cair, a bateria não é fraca.",
    "Se a carga cair, a bateria talvez é fraca.",
    "Se a carga cair, a bateria é fraca e perigosa.",
    "Se a carga cair, a bateria é fraca, exceto na bancada.",
    "Se a carga cair, a bateria é fraca. Apenas se o teste passar.",
    "Se a carga cair, se o teste passar, a bateria é fraca.",
    "A bateria é fraca.",
    "Se a bateria fraca descarregar, o alerta toca.",
    "Se a carga cair, o painel diz que a bateria é fraca.",
    "Se a carga cair, a bateria é fracamente carregada.",
    "Se a carga cair, a bateria é fraca?",
    "A bateria é fraca apenas se.",
    "Se, a bateria é fraca.",
    None,
    [],
])
def test_efeito_fora_da_gramatica_nao_recebe_aprovacao(fonte):
    resultado = analisar_efeito_qualificativo(fonte, "fraca")
    assert resultado["estado"] == "efeito_qualificativo_pendente"
    assert resultado["aprovado_para_producao"] is False


def test_predicado_extraido_nao_eh_preenchido_pelo_rotulo_desejado():
    resultado = analisar_efeito_qualificativo(
        "Se a temperatura cair, a sala é fria.", "quente",
    )
    assert resultado["predicado_literal"] == "fria"
    assert resultado["estado"] == "efeito_qualificativo_pendente"


def test_negacao_permanece_na_citacao_sem_ser_convertida_em_afirmacao():
    resultado = analisar_efeito_qualificativo(
        "Se a pressão subir, a porta não é aberta.", "aberta",
    )
    assert resultado["citacao"] == "a porta não é aberta"
    assert resultado["polaridade"] == "negacao_presente"
    assert resultado["estado"] == "efeito_qualificativo_pendente"


def test_prefixo_de_escopo_nao_eh_descartado_nem_declarado_satisfeito():
    for prefixo in ("Neste protocolo", "No modo automático"):
        resultado = analisar_efeito_qualificativo(
            prefixo + ", se a carga cair, a bateria é fraca.", "fraca",
        )
        assert resultado["estado"] == "efeito_qualificativo_literal_revisao_pendente"
        assert resultado["escopo_literal"] == prefixo
        assert resultado["escopo_verificado"] is False
        assert resultado["aprovado_para_producao"] is False
