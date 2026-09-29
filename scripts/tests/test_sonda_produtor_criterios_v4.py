"""Revisao e limites do painel v4 antes de consultar qualquer modelo."""

import pytest
from copy import deepcopy

from scripts.analises import sonda_produtor_criterios_v4 as sonda
from scripts.analises.sonda_produtor_criterios_v1 import (
    _conferir_grafo_do_caso, conferir_proposta,
)
from scripts.analises.sonda_produtor_criterios_v2 import (
    _fontes_com_condicao_unica, conferir_selecao,
)


CASOS, REVISAO = sonda.carregar_painel()
POR_ID = {caso["id"]: caso for caso in CASOS}
NORMALIZADOS = (
    "referente_id", "atributo", "operador", "limiar", "unidade",
    "direcao_implicacao", "citacao_condicao",
)


def test_painel_congelado_e_revisao_canonica_sem_autoridade():
    assert len(CASOS) == 10
    assert sum(rev["estado"] == "criterio_candidato"
               for rev in REVISAO.values()) == 5
    assert sum(rev["estado"] == "abster"
               for rev in REVISAO.values()) == 5
    for caso in CASOS:
        revisao = REVISAO[caso["id"]]
        proposta = (
            {"estado": "criterio_candidato", "motivo": "",
             **{campo: revisao[campo] for campo in ("fonte_id", *NORMALIZADOS)}}
            if revisao["estado"] == "criterio_candidato" else
            {"estado": "abster", "motivo": revisao["motivo"],
             **{campo: "" for campo in ("fonte_id", *NORMALIZADOS)}}
        )
        afericao = conferir_proposta(caso, revisao, proposta)
        assert afericao["alinhado_revisao"] is True, caso["id"]
        assert afericao["aprovado_para_producao"] is False
        assert afericao["autoriza_efeito"] is False


def test_veto_estrutural_nao_confunde_regra_de_acao_com_criterio():
    assert _fontes_com_condicao_unica(POR_ID["CAIXA_ROTULO_NA_LEITURA"]) == []
    assert _fontes_com_condicao_unica(POR_ID["POMAR_REGRA_COMPOSTA"]) == []
    for id_caso, fonte_id in (
        ("CIRCUITO_ACAO_COM_ROTULO", "controle"),
        ("PORTA_EFEITO_NEGADO", "criterio"),
    ):
        caso = POR_ID[id_caso]
        assert _fontes_com_condicao_unica(caso) == [fonte_id]
        afericao = conferir_selecao(
            caso, {"estado": "fonte_candidata", "motivo": "",
                   "fonte_id": fonte_id}, exigir_condicao_unica=True,
        )
        assert afericao["estado"] == "fonte_literal_candidata_revisao_pendente"
        assert REVISAO[id_caso]["estado"] == "abster"
        assert afericao["aprovado_para_producao"] is False


def test_loader_veta_alteracao_pos_congelamento(monkeypatch, tmp_path):
    alterado = tmp_path / "revisao.json"
    alterado.write_bytes(sonda.REVISAO.read_bytes() + b" ")
    monkeypatch.setattr(sonda, "REVISAO", alterado)
    with pytest.raises(ValueError, match="alterado depois do congelamento"):
        sonda.carregar_painel()


@pytest.mark.parametrize("id_caso,sujeito", [
    ("POMAR_CRITERIO_SECO", "o reservatório"),
    ("EMPILHADEIRA_BATERIA_FRACA", "a bateria da empilhadeira reserva"),
    ("IMPRESSORA_CRITERIO_LENTA", "a ventoinha da impressora"),
    ("CAFETEIRA_AGUA_QUENTE", "a água da chaleira"),
    ("IMPRESSORA_CRITERIO_LENTA", "ela"),
])
def test_mencao_na_condicao_nao_valida_sujeito_diferente_no_efeito(id_caso, sujeito):
    caso = deepcopy(POR_ID[id_caso])
    proposta = REVISAO[id_caso]
    controle = _conferir_grafo_do_caso(caso, proposta)
    assert controle["estado"] == "condicao_numerica_satisfeita_relacao_pendente"
    regra = caso["fontes"][-1]
    regra["texto"] = regra["texto"].split(", ")[0] + (
        f", {sujeito} é {caso['rotulo_alvo']}."
    )
    resultado = _conferir_grafo_do_caso(caso, proposta)
    assert resultado["estado"] == "sujeito_efeito_pendente"
    assert resultado["comparacao_numerica"] is False
    assert resultado["aprovado_para_compor"] is False


def test_descricao_literal_duplicada_nao_escolhe_identidade_pelo_id_proposto():
    caso = deepcopy(POR_ID["IMPRESSORA_CRITERIO_LENTA"])
    caso["referentes"].append({**caso["referentes"][0], "id": "outra_impressora"})
    resultado = _conferir_grafo_do_caso(caso, REVISAO[caso["id"]])
    assert resultado["estado"] == "sujeito_efeito_pendente"
    assert resultado["comparacao_numerica"] is False


def test_sujeito_corresponde_a_outro_item_ancorado_sem_trocar_medicao():
    caso = deepcopy(POR_ID["IMPRESSORA_CRITERIO_LENTA"])
    fonte = caso["fontes"][-1]
    fonte["texto"] = fonte["texto"].replace(", a impressora é", ", a ventoinha é")
    caso["referentes"].append({
        "id": "ventoinha", "tipo": "componente", "grandeza": "rotação",
        "fonte_id": fonte["id"], "citacao": "ventoinha",
    })
    resultado = _conferir_grafo_do_caso(caso, REVISAO[caso["id"]])
    assert resultado["estado"] == "sujeito_efeito_pendente"
    assert resultado["sujeito_efeito"]["referentes_candidatos"] == ["ventoinha"]
    assert resultado["sujeito_efeito"]["identidade_verificada"] is False


def test_artigo_caixa_e_espacos_nao_eliminam_qualificadores_do_nome():
    caso = deepcopy(POR_ID["EMPILHADEIRA_BATERIA_FRACA"])
    caso["fontes"][-1]["texto"] = caso["fontes"][-1]["texto"].replace(
        ", a bateria da empilhadeira é", ", A BATERIA  DA EMPILHADEIRA é",
    )
    resultado = _conferir_grafo_do_caso(caso, REVISAO[caso["id"]])
    assert resultado["estado"] == "condicao_numerica_satisfeita_relacao_pendente"
    assert resultado["sujeito_efeito"]["estado"] == (
        "sujeito_literal_compativel_revisao_pendente"
    )
    assert resultado["sujeito_efeito"]["identidade_verificada"] is False
    assert resultado["relacao_semantica_verificada"] is False
    assert resultado["aprovado_para_compor"] is False


def test_sonda_composta_nao_usa_revisao_como_autoridade_para_sujeito_errado():
    from scripts.analises.sonda_produtor_criterios_v2 import medir_caso

    caso = deepcopy(POR_ID["IMPRESSORA_CRITERIO_LENTA"])
    caso["fontes"][-1]["texto"] = caso["fontes"][-1]["texto"].replace(
        ", a impressora é", ", a ventoinha da impressora é",
    )
    revisao = REVISAO[caso["id"]]
    chamadas = []

    def proponente(_sistema, entrada, _formato, **_kwargs):
        chamadas.append(entrada)
        if len(chamadas) == 1:
            return {"estado": "fonte_candidata", "motivo": "", "fonte_id": "criterio"}
        return {campo: revisao[campo] for campo in NORMALIZADOS}

    # Só o proponente é controlado; seleção, grafo e aferição são reais.
    resultado = medir_caso(caso, revisao, consulta=proponente,
                           exigir_condicao_unica=True)
    assert len(chamadas) == 2
    assert chamadas[-1]["fonte_integral"] == caso["fontes"][-1]["texto"]
    assert resultado["afericao_final"]["estado"] == "grafo_rejeitou_proposta"
    assert resultado["afericao_final"]["grafo_estado"] == "sujeito_efeito_pendente"
    assert resultado["afericao_final"]["alinhado_revisao"] is False
    assert resultado["afericao_final"]["aprovado_para_producao"] is False
