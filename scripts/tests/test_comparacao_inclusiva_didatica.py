"""Operador composto é um átomo; não é conectivo entre condições."""

from copy import deepcopy

import pytest

from scripts.analises.sonda_produtor_candidatos_v1 import gerar_candidatos
from scripts.analises.sonda_produtor_criterios_v1 import _conferir_grafo_do_caso
from scripts.analises.sonda_produtor_criterios_v2 import (
    medir_caso, preparar_normalizacao_segmentada,
)
from scripts.analises.sonda_produtor_criterios_v5 import carregar_painel


CASOS, REVISAO = carregar_painel(6)
TANQUE = next(c for c in CASOS if c["id"] == "TANQUE_INCLUSIVO")


@pytest.mark.parametrize("condicao", [
    "o volume do tanque for maior ou igual a 40 L",
    "a temperatura da câmara for menor ou igual a -12,5 °C",
    "a latência do canal for MAIOR OU IGUAL A 80 ms",
])
def test_operador_composto_nao_divide_condicao_numerica(condicao):
    fonte = f"Se {condicao}, o sistema está estável."
    resultado = gerar_candidatos({"fonte": fonte})
    assert resultado["conectivo_textual"] == "unico"
    assert [c["citacao"] for c in resultado["candidatos"]] == [condicao]
    for c in resultado["candidatos"]:
        assert fonte[c["inicio"]:c["fim"]] == c["citacao"]
    assert resultado["autoriza_efeito"] is False


@pytest.mark.parametrize("conectivo", ["e", "ou"])
def test_preserva_juncao_real_ao_lado_de_operadores_compostos(conectivo):
    condicoes = ["a pressão for maior ou igual a 40 Pa",
                 "a vazão for menor ou igual a 12 L"]
    fonte = f"Se {condicoes[0]} {conectivo} {condicoes[1]}, a bomba está estável."
    resultado = gerar_candidatos({"fonte": fonte})
    assert resultado["conectivo_textual"] == conectivo
    assert [c["citacao"] for c in resultado["candidatos"]] == condicoes
    assert preparar_normalizacao_segmentada(fonte, "estável")["estado"] == "segmentacao_pendente"


@pytest.mark.parametrize("condicao", [
    "o tanque for maior ou o limite for igual a 40 L",
    "o tanque for maior ou igual ao reservatório",
    "o volume for maior ou igual a quarenta litros",
    "o volume for maior ou igual a 4e3 litros",
])
def test_superficie_nao_coberta_nao_vira_comparador_numerico(condicao):
    resultado = gerar_candidatos({"fonte": f"Se {condicao}, o tanque é cheio."})
    assert resultado["conectivo_textual"] == "ou"
    assert len(resultado["candidatos"]) == 2
    assert resultado["aprovado_para_producao"] is False


def _cenario(palavra, operador, valor, limite="40"):
    caso = deepcopy(TANQUE)
    medida = caso["medida"]
    medida["valor"] = valor
    medida["citacao"] = f"O volume do tanque foi {valor} L"
    caso["fontes"][0]["texto"] = medida["citacao"] + "."
    condicao = f"o volume do tanque for {palavra} ou igual a {limite} L"
    caso["fontes"][1]["texto"] = f"Se {condicao}, o tanque é cheio."
    proposta = {**REVISAO[TANQUE["id"]], "motivo": "", "operador": operador,
                "limiar": limite, "citacao_condicao": condicao}
    return caso, proposta


@pytest.mark.parametrize("palavra,operador,valor,satisfeita", [
    ("maior", ">=", "39", False), ("maior", ">=", "40", True),
    ("maior", ">=", "41", True), ("menor", "<=", "39", True),
    ("menor", "<=", "40", True), ("menor", "<=", "41", False),
])
def test_grafo_compara_limite_inclusivo_sem_aprovar_fala(palavra, operador, valor, satisfeita):
    caso, proposta = _cenario(palavra, operador, valor)
    resultado = _conferir_grafo_do_caso(caso, proposta)
    esperado = ("condicao_numerica_satisfeita_relacao_pendente" if satisfeita
                else "condicao_numerica_nao_satisfeita")
    assert resultado["estado"] == esperado
    assert resultado["comparacao_numerica"] is satisfeita
    assert resultado["aprovado_para_compor"] is False
    assert resultado["relacao_semantica_verificada"] is False
    assert resultado["autoriza_efeito"] is False


@pytest.mark.parametrize("operador", [">", "<", "<="])
def test_proposta_nao_pode_trocar_operador_inclusivo_da_fonte(operador):
    caso, proposta = _cenario("maior", operador, "40")
    resultado = _conferir_grafo_do_caso(caso, proposta)
    assert resultado["estado"] == "direcao_literal_pendente"
    assert resultado["comparacao_numerica"] is False


def test_revogacao_continua_bloqueando_comparacao_inclusiva():
    caso, proposta = _cenario("maior", ">=", "40")
    caso["fontes"].append({"id": "revogacao", "texto": "Não use mais essa regra."})
    resultado = _conferir_grafo_do_caso(caso, proposta)
    assert resultado["estado"] == "contexto_criterio_pendente"
    assert resultado["comparacao_numerica"] is False


@pytest.mark.parametrize("valor,satisfeita", [("-12,6", True), ("-12,5", True), ("-12,4", False)])
def test_outro_dominio_limite_decimal_negativo(valor, satisfeita):
    caso = deepcopy(next(c for c in CASOS if c["id"] == "CAMARA_LIMIAR_NEGATIVO"))
    medida = caso["medida"]
    medida["valor"] = valor
    medida["citacao"] = f"A temperatura da câmara foi {valor} °C"
    caso["fontes"][0]["texto"] = medida["citacao"] + "."
    condicao = "a temperatura da câmara for menor ou igual a -12,5 °C"
    caso["fontes"][1]["texto"] = f"Se {condicao}, a câmara está fria."
    proposta = {**REVISAO[caso["id"]], "motivo": "", "operador": "<=",
                "limiar": "-12,5", "citacao_condicao": condicao}
    resultado = _conferir_grafo_do_caso(caso, proposta)
    assert resultado["estado"] == (
        "condicao_numerica_satisfeita_relacao_pendente" if satisfeita
        else "condicao_numerica_nao_satisfeita")
    assert resultado["autoriza_efeito"] is False


@pytest.mark.parametrize("mudanca", ["negacao", "unidade", "limiar", "recorte_numerico"])
def test_comparador_reconhecido_nao_dispensa_ancoragem(mudanca):
    caso, proposta = _cenario("maior", ">=", "40")
    if mudanca == "negacao":
        fonte = caso["fontes"][1]
        fonte["texto"] = fonte["texto"].replace("for maior", "não for maior")
        proposta["citacao_condicao"] = proposta["citacao_condicao"].replace("for maior", "não for maior")
    elif mudanca == "unidade":
        proposta["unidade"] = "mL"
    elif mudanca == "limiar":
        proposta["limiar"] = "4"
    else:
        # Não confundir o prefixo de 40,5 com o inteiro 40 proposto.
        caso["fontes"][1]["texto"] = caso["fontes"][1]["texto"].replace("40 L", "40,5 L")
        proposta["citacao_condicao"] = proposta["citacao_condicao"].replace("40 L", "40,5 L")
    resultado = _conferir_grafo_do_caso(caso, proposta)
    assert resultado["comparacao_numerica"] is False
    assert resultado["aprovado_para_compor"] is False


def test_conectivos_mistos_continuam_nao_planos_apesar_do_atomo_inclusivo():
    fonte = "Se a pressão for maior ou igual a 40 Pa e a bomba parar ou a luz apagar, o sistema é instável."
    resultado = gerar_candidatos({"fonte": fonte})
    assert resultado["conectivo_textual"] == "misto"
    assert resultado["estrutura_plana_possivel"] is False
    assert len(resultado["candidatos"]) == 3


def test_sonda_segmentada_chega_ao_grafo_com_limite_inclusivo():
    chamadas = []
    revisao = REVISAO[TANQUE["id"]]

    def consultar(_sistema, entrada, _formato, **kwargs):
        chamadas.append(entrada)
        if len(chamadas) == 1:
            return {"estado": "fonte_candidata", "motivo": "", "fonte_id": "criterio"}
        assert entrada["condicao_literal"]["citacao"] == revisao["citacao_condicao"]
        return {k: revisao[k] for k in ("referente_id", "atributo", "operador", "limiar", "unidade")}

    resultado = medir_caso(TANQUE, revisao, consulta=consultar,
                           exigir_condicao_unica=True, normalizacao_segmentada=True)
    assert len(chamadas) == 2
    assert resultado["afericao_final"]["alinhado_revisao"] is True
    assert resultado["afericao_final"]["aprovado_para_producao"] is False
