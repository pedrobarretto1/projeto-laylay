"""Contrato do painel v3 antes de qualquer medicao por modelo."""

import pytest

from scripts.analises import sonda_produtor_criterios_v3 as sonda
from scripts.analises.sonda_produtor_criterios_v1 import conferir_proposta
from scripts.analises.sonda_produtor_criterios_v2 import conferir_selecao


CASOS, REVISAO = sonda.carregar_painel()
POR_ID = {caso["id"]: caso for caso in CASOS}
NORMALIZADOS = (
    "referente_id", "atributo", "operador", "limiar", "unidade",
    "direcao_implicacao", "citacao_condicao",
)


def test_painel_congelado_tem_cinco_criterios_e_cinco_abstencoes():
    assert len(CASOS) == 10
    assert sum(rev["estado"] == "criterio_candidato"
               for rev in REVISAO.values()) == 5
    assert sum(rev["estado"] == "abster"
               for rev in REVISAO.values()) == 5
    assert len({caso["dominio"] for caso in CASOS}) >= 7


def test_revisao_canonica_e_ancorada_mas_nao_aprova_fala():
    for caso in CASOS:
        revisao = REVISAO[caso["id"]]
        proposta = (
            {"estado": "criterio_candidato", "motivo": "",
             **{campo: revisao[campo] for campo in ("fonte_id", *NORMALIZADOS)}}
            if revisao["estado"] == "criterio_candidato" else
            {"estado": "abster", "motivo": revisao["motivo"],
             **{campo: "" for campo in ("fonte_id", *NORMALIZADOS)}}
        )
        resultado = conferir_proposta(caso, revisao, proposta)
        assert resultado["alinhado_revisao"] is True, caso["id"]
        assert resultado["aprovado_para_producao"] is False
        assert resultado["autoriza_efeito"] is False


def test_rotulo_na_leitura_e_regra_composta_expoem_limite_do_gate_literal():
    for id_caso, fonte_id in (
        ("PACOTE_ROTULO_NA_LEITURA", "leitura"),
        ("BATERIA_REGRA_COMPOSTA", "criterio"),
    ):
        resultado = conferir_selecao(POR_ID[id_caso], {
            "estado": "fonte_candidata", "motivo": "", "fonte_id": fonte_id,
        })
        assert resultado["estado"] == "fonte_literal_candidata_revisao_pendente"
        assert REVISAO[id_caso]["estado"] == "abster"
        assert resultado["aprovado_para_producao"] is False


def test_pre_filtro_nao_confunde_elegibilidade_literal_com_semantica():
    for id_caso, esperadas in (
        ("PACOTE_ROTULO_NA_LEITURA", ["leitura"]),
        ("BATERIA_REGRA_COMPOSTA", ["criterio"]),
        ("ESTUFA_REGRA_IRRIGACAO", []),
    ):
        caso = POR_ID[id_caso]
        recebido = {}

        def consultar(_sistema, entrada, formato, **_kwargs):
            recebido["entrada"] = entrada
            recebido["formato"] = formato
            return {"estado": "abster", "motivo": REVISAO[id_caso]["motivo"],
                    "fonte_id": ""}

        resultado = sonda.medir_caso(
            caso, REVISAO[id_caso], consulta=consultar,
        )
        assert recebido["entrada"]["fontes_com_rotulo_literal"] == esperadas
        assert recebido["formato"]["properties"]["fonte_id"]["enum"] == [
            "", *esperadas,
        ]
        assert "revisao" not in recebido["entrada"]
        assert resultado["normalizacao"] == "nao_executada"


def test_elegibilidade_literal_nao_depende_da_ordem_das_fontes():
    caso = POR_ID["ROBO_FONTE_DISTRATORA"]
    vistos = []

    def consultar(_sistema, entrada, formato, **_kwargs):
        vistos.append((entrada["fontes_com_rotulo_literal"],
                      formato["properties"]["fonte_id"]["enum"]))
        return {"estado": "abster", "motivo": "outro_indeterminado",
                "fonte_id": ""}

    sonda.medir_caso(caso, REVISAO[caso["id"]], consulta=consultar)
    invertido = {**caso, "fontes": list(reversed(caso["fontes"]))}
    sonda.medir_caso(invertido, REVISAO[caso["id"]], consulta=consultar)
    assert vistos == [(["criterio"], ["", "criterio"])] * 2


def test_criterio_unico_veta_rotulo_em_leitura_e_regra_composta():
    for id_caso, fonte_id in (
        ("PACOTE_ROTULO_NA_LEITURA", "leitura"),
        ("BATERIA_REGRA_COMPOSTA", "criterio"),
    ):
        caso = POR_ID[id_caso]
        chamadas = []

        def consultar(_sistema, entrada, formato, **_kwargs):
            chamadas.append((entrada, formato))
            return {"estado": "fonte_candidata", "motivo": "",
                    "fonte_id": fonte_id}

        resultado = sonda.medir_caso(
            caso, REVISAO[id_caso], consulta=consultar,
            exigir_condicao_unica=True,
        )
        assert len(chamadas) == 1
        assert chamadas[0][0]["fontes_com_condicao_unica"] == []
        assert chamadas[0][1]["properties"]["fonte_id"]["enum"] == [""]
        assert resultado["normalizacao"] == "nao_executada"
        assert resultado["afericao_selecao"]["estado"] == (
            "estrutura_condicional_inconclusiva"
        )


def test_criterio_unico_preserva_regra_simples_e_apenas_se():
    for id_caso in ("AQUARIO_CRITERIO_FRIO", "FILTRO_APENAS_SE"):
        caso = POR_ID[id_caso]
        chamadas = []

        def consultar(_sistema, entrada, formato, **_kwargs):
            chamadas.append((entrada, formato))
            if len(chamadas) == 1:
                return {"estado": "fonte_candidata", "motivo": "",
                        "fonte_id": "criterio"}
            return {campo: REVISAO[id_caso][campo] for campo in NORMALIZADOS}

        resultado = sonda.medir_caso(
            caso, REVISAO[id_caso], consulta=consultar,
            exigir_condicao_unica=True,
        )
        assert len(chamadas) == 2
        assert chamadas[0][0]["fontes_com_condicao_unica"] == ["criterio"]
        assert resultado["afericao_final"]["alinhado_revisao"] is True
        assert resultado["afericao_final"]["aprovado_para_producao"] is False


def test_loader_recusa_painel_alterado_apos_congelamento(monkeypatch, tmp_path):
    alterado = tmp_path / "entradas.json"
    alterado.write_bytes(sonda.ENTRADAS.read_bytes() + b" ")
    monkeypatch.setattr(sonda, "ENTRADAS", alterado)
    with pytest.raises(ValueError, match="alterado depois do congelamento"):
        sonda.carregar_painel()
