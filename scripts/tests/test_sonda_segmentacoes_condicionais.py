"""Contrato offline: conjunção entre referentes não é sempre entre condições."""

from scripts.analises import sonda_segmentacoes_condicionais as sonda
from scripts.analises.sonda_produtor_condicoes_v2 import carregar_painel


CASOS, OURO = carregar_painel(5)
POR_ID = {caso["id"]: caso for caso in CASOS}


def _escolha(segmentacao_id, direcao="condicoes_suficientes"):
    return {"representavel": True, "segmentacao_id": segmentacao_id,
            "direcao_implicacao": direcao}


def test_sujeito_composto_tem_alternativa_integral_literal_e_alinha():
    caso = POR_ID["SENSORES_SUJEITO_COMPOSTO"]
    alternativas = sonda.gerar_segmentacoes(caso)
    assert [item["id"] for item in alternativas["segmentacoes"]] == [
        "integral", "atomica",
    ]
    inteira = alternativas["segmentacoes"][0]
    assert inteira["conectivo_condicoes"] == "unico"
    assert inteira["trechos"][0]["citacao"] == "os sensores A e B detectarem fumaça"
    for alternativa in alternativas["segmentacoes"]:
        for trecho in alternativa["trechos"]:
            assert caso["fonte"][trecho["inicio"]:trecho["fim"]] == trecho["citacao"]
    assert sonda.confrontar_segmentacao(
        caso, OURO[caso["id"]], alternativas, _escolha("integral"),
    )["estado"] == "trechos_e_relacao_alinhados_revisao_pendente"
    assert sonda.confrontar_segmentacao(
        caso, OURO[caso["id"]], alternativas, _escolha("atomica"),
    )["estado"] == "trechos_divergentes"


def test_duas_condicoes_precisam_da_segmentacao_atomica():
    caso = POR_ID["VASO_OU"]
    alternativas = sonda.gerar_segmentacoes(caso)
    assert sonda.conferir_cobertura_segmentacoes(
        caso, OURO[caso["id"]], alternativas,
    )["estado"] == "cobertura_alternativa_revisao_pendente"
    assert sonda.confrontar_segmentacao(
        caso, OURO[caso["id"]], alternativas, _escolha("atomica"),
    )["estado"] == "trechos_e_relacao_alinhados_revisao_pendente"
    assert sonda.confrontar_segmentacao(
        caso, OURO[caso["id"]], alternativas, _escolha("integral"),
    )["estado"] == "trechos_divergentes"


def test_alternativa_adulterada_e_id_desconhecido_sao_rejeitados():
    caso = POR_ID["SENSORES_SUJEITO_COMPOSTO"]
    alternativas = sonda.gerar_segmentacoes(caso)
    assert sonda.confrontar_segmentacao(
        caso, OURO[caso["id"]], alternativas, _escolha("inventada"),
    )["estado"] == "segmentacao_desconhecida"
    adulteradas = {**alternativas, "segmentacoes": [
        {**alternativas["segmentacoes"][0], "trechos": [{
            **alternativas["segmentacoes"][0]["trechos"][0], "citacao": "outra",
        }]}, *alternativas["segmentacoes"][1:],
    ]}
    assert sonda.confrontar_segmentacao(
        caso, OURO[caso["id"]], adulteradas, _escolha("integral"),
    )["estado"] == "segmentacoes_adulteradas"


def test_misto_recusa_antes_do_modelo(monkeypatch):
    caso = POR_ID["ACESSO_MISTO"]

    def proibida(*args, **kwargs):
        raise AssertionError("mistura exige arvore, fora do contrato plano")

    monkeypatch.setattr(sonda, "_consultar_modelo", proibida)
    resultado = sonda.medir_caso(caso, OURO[caso["id"]])
    assert resultado["escolha"] == "recusa_estrutura_plana"
    assert resultado["aprovado_para_producao"] is False


def test_prompt_nao_leva_gabarito_e_a_escolha_nao_autoriza(monkeypatch):
    caso = POR_ID["SENSORES_SUJEITO_COMPOSTO"]
    entradas = []

    def consultar(_sistema, entrada, _formato, *, url, modelo):
        entradas.append(entrada)
        return _escolha("integral")

    monkeypatch.setattr(sonda, "_consultar_modelo", consultar)
    resultado = sonda.medir_caso(caso, OURO[caso["id"]])
    assert len(entradas) == 1
    assert "condicoes" not in entradas[0]
    assert "gabarito" not in entradas[0]
    assert resultado["afericao"]["estado"] == "trechos_e_relacao_alinhados_revisao_pendente"
    assert resultado["aprovado_para_producao"] is False


def test_painel_v6_congelado_tem_cobertura_antes_do_modelo():
    casos, ouro = carregar_painel(6)
    assert len(casos) == len(ouro) == 7
    estados = {caso["id"]: sonda.conferir_cobertura_segmentacoes(
        caso, ouro[caso["id"]], sonda.gerar_segmentacoes(caso),
    )["estado"] for caso in casos}
    assert list(estados.values()).count("cobertura_alternativa_revisao_pendente") == 6
    assert estados["TRAVA_MISTA_V6"] == "cobertura_nao_medida_regra_nao_plana"


def test_ordem_invertida_muda_so_apresentacao_nao_ids_ou_cobertura(monkeypatch):
    caso = POR_ID["VASO_OU"]
    capturas = []

    def consultar(_sistema, entrada, _formato, *, url, modelo):
        capturas.append(entrada)
        return _escolha("atomica")

    monkeypatch.setattr(sonda, "_consultar_modelo", consultar)
    normal = sonda.medir_caso(caso, OURO[caso["id"]])
    invertida = sonda.medir_caso(
        caso, OURO[caso["id"]], ordem_segmentacoes="atomica_primeiro",
    )
    assert [item["id"] for item in capturas[0]["segmentacoes"]] == [
        "integral", "atomica",
    ]
    assert [item["id"] for item in capturas[1]["segmentacoes"]] == [
        "atomica", "integral",
    ]
    assert normal["segmentacoes"] == invertida["segmentacoes"]
    assert normal["cobertura"] == invertida["cobertura"]
    assert normal["afericao"]["estado"] == invertida["afericao"]["estado"]
