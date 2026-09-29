"""Regressão canônica: fonte observada não equivale a critério vigente.

Reproduz a fronteira offline encontrada no painel v6, sem modelo/gabarito.
Não afrouxar a expectativa nem confundir essa prova com efeito em produção.
"""

from copy import deepcopy
import pytest

from scripts.analises.sonda_produtor_criterios_v5 import carregar_painel
from scripts.analises.sonda_produtor_criterios_v1 import _conferir_grafo_do_caso


def _cenario():
    casos, _ = carregar_painel(6)
    caso = deepcopy(next(c for c in casos if c["id"] == "DUTO_REGRA_REVOGADA"))
    proposta = {
        "fonte_id": "criterio", "referente_id": "duto",
        "atributo": caso["medida"]["atributo"], "operador": ">",
        "limiar": "8", "unidade": "bar",
        "direcao_implicacao": "condicoes_suficientes",
        "citacao_condicao": caso["fontes"][1]["texto"][3:].split(", ")[0],
    }
    return caso, proposta


def test_controle_sem_revogacao_chega_a_comparacao_sem_autoridade():
    caso, proposta = _cenario()
    caso["fontes"] = caso["fontes"][:-1]
    resultado = _conferir_grafo_do_caso(caso, proposta)
    assert resultado["comparacao_numerica"] is True
    assert resultado["aprovado_para_compor"] is False
    assert resultado["autoriza_efeito"] is False


def test_revogacao_observada_impede_usar_regra_antiga_como_criterio_atual():
    caso, proposta = _cenario()
    assert caso["fontes"][-1]["id"] == "revogacao"
    resultado = _conferir_grafo_do_caso(caso, proposta)
    assert resultado["comparacao_numerica"] is False, (
        "Fonte observada foi tratada como vigente apesar da revogação "
        "presente no contexto; precisa de contrato de validade da fonte."
    )
    assert resultado["aprovado_para_compor"] is False


def test_rota_opt_in_exige_revisao_real_sem_auto_aprovar_contexto():
    from scripts.analises.contrato_vigencia_criterios import RegistroVigenciaCriterios

    caso, proposta = _cenario()
    resultado = _conferir_grafo_do_caso(
        caso, proposta, registro_vigencia=RegistroVigenciaCriterios(),
    )
    assert resultado["estado"] == "vigencia_fonte_pendente"
    assert resultado["comparacao_numerica"] is False
    assert resultado["vigencia"] == "sem_revisao"
    assert resultado["aprovado_para_compor"] is False


def test_rota_opt_in_nao_aceita_registro_fabricado_pelo_proponente():
    caso, proposta = _cenario()
    resultado = _conferir_grafo_do_caso(
        caso, proposta, registro_vigencia={"fonte_id": "criterio", "vigente": True},
    )
    assert resultado["estado"] == "registro_vigencia_invalido"
    assert resultado["comparacao_numerica"] is False


@pytest.mark.parametrize("texto", [
    "Não use mais o critério anterior.",
    "A regra anterior foi revogada?",
    "A regra anterior não foi revogada.",
    "A regra do compressor foi revogada, não a do duto.",
    "Ela disse: a regra anterior foi revogada.",
    "O limite agora é outro.",
])
def test_contexto_posterior_nao_conferido_fica_pendente_sem_afirmar_revogacao(texto):
    caso, proposta = _cenario()
    caso["fontes"][-1]["texto"] = texto
    resultado = _conferir_grafo_do_caso(caso, proposta)
    assert resultado["estado"] == "contexto_criterio_pendente"
    assert resultado["comparacao_numerica"] is False
    assert resultado["vigencia"] == "nao_demonstrada"


def test_leitura_posterior_simples_nao_invalida_criterio():
    caso, proposta = _cenario()
    caso["fontes"] = [caso["fontes"][1], caso["fontes"][0]]
    resultado = _conferir_grafo_do_caso(caso, proposta)
    assert resultado["comparacao_numerica"] is True
    assert resultado["aprovado_para_compor"] is False


def test_leitura_com_ressalva_nao_esconde_contexto_na_citacao_de_premissa():
    caso, proposta = _cenario()
    leitura = caso["fontes"][0]
    leitura["texto"] += " Não use mais a regra anterior."
    caso["medida"]["citacao"] = leitura["texto"]
    caso["fontes"] = [caso["fontes"][1], leitura]
    resultado = _conferir_grafo_do_caso(caso, proposta)
    assert resultado["comparacao_numerica"] is False
    assert resultado["estado"] == "contexto_criterio_pendente"
