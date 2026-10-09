"""Seleção de ocorrência host não é interpretação, autoridade ou ausência."""

from copy import deepcopy

import pytest

from scripts.analises import sonda_selecao_literal_proposicao_v1 as sonda
from scripts.analises import sonda_proposicoes_mencionadas_v1 as anterior
from scripts.analises.contrato_vigencia_criterios import RegistroVigenciaCriterios


CASOS, OURO = sonda.carregar_painel()


def caso(id_caso):
    return next(c for c in CASOS if c["id"] == id_caso)


def assert_inerte(r):
    assert all(r[k] is False for k in sonda.contrato.BASE)
    assert "tratado" not in r and "referente_id" not in r


@pytest.mark.parametrize("id_caso", list(OURO))
def test_mesma_escolha_local_tem_materializacao_equivalente_em_ambos_protocolos(id_caso):
    c = caso(id_caso)
    catalogo = sonda.preparar_catalogo(c)
    esperado = OURO[id_caso]
    trecho = next((item["texto"] for item in catalogo["candidatos"] if item["id"] == esperado), "")
    por_id = sonda.conferir_selecao(c, catalogo, {"candidato_id": esperado}, modo="id")
    copia = sonda.conferir_selecao(c, catalogo, {"trecho": trecho}, modo="copia")
    assert por_id == copia
    assert sonda.aferir({"conferencia": por_id}, esperado)["selecao_alinhada_revisao_local"] is True
    assert_inerte(por_id)


def test_fontes_e_pares_aninhados_sao_preservados_sem_filtrar_titulos():
    catalogo = sonda.preparar_catalogo(caso("L03"))
    fonte = catalogo["fonte"]["texto"]
    assert len(catalogo["candidatos"]) == 3
    assert catalogo["candidatos"][2]["texto"] == "renomeie o arquivo mapa.csv"
    q0, q1 = catalogo["aspas_sintaticas"]["regioes_entre_aspas"]
    assert q1["pai_id"] == q0["id"]
    for item in catalogo["candidatos"]:
        assert fonte[item["inicio"]:item["fim"]] == item["texto"]
    filename = sonda.preparar_catalogo(caso("L04"))
    assert filename["candidatos"][1]["texto"] == "apague isso.txt"
    assert "semantica_verificada" not in filename["candidatos"][1]


def test_id_literal_valido_de_filename_nao_certifica_operacao():
    c = caso("L04")
    r = sonda.conferir_selecao(c, sonda.preparar_catalogo(c), {"candidato_id": "c1"}, modo="id")
    assert r["estado"] == "selecao_literal_revisao_pendente"
    assert sonda.aferir({"conferencia": r}, OURO["L04"])["selecao_alinhada_revisao_local"] is False
    assert_inerte(r)


@pytest.mark.parametrize("id_caso", ["L06", "L10"])
def test_abstencao_com_ou_sem_operacoes_nao_prova_ausencia(id_caso):
    c = caso(id_caso)
    r = sonda.conferir_selecao(c, sonda.preparar_catalogo(c), {"candidato_id": "indeterminado"}, modo="id")
    assert r["estado"] == "abstencao_revisao_pendente" and r["selecao"] is None
    assert "sem_operacao" not in r
    assert_inerte(r)


def test_mesmo_prompt_substantivo_fonte_e_catalogo_sem_gabarito_em_ambos_bracos():
    chamadas = []
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append((sistema, deepcopy(entrada), formato, kwargs))
        assert set(entrada) == {"fonte", "aspas_sintaticas", "candidatos"}
        assert "L01" not in str(entrada) and "gabarito" not in entrada
        return {"candidato_id": "c1"} if "candidato_id" in formato["properties"] else {"trecho": entrada["candidatos"][0]["texto"]}
    for modo in sonda.MODOS:
        sonda.medir_caso(caso("L01"), modo=modo, inverter_candidatos=True, consulta=consulta)
    copia, por_id = chamadas
    assert copia[1] == por_id[1] and copia[3] == por_id[3]
    assert copia[0].startswith(sonda.SISTEMA_COMUM) and por_id[0].startswith(sonda.SISTEMA_COMUM)
    assert copia[1]["candidatos"][0]["id"] == "c1"
    assert por_id[2]["properties"]["candidato_id"]["enum"] == ["c1", "c0", "indeterminado"]


def test_selecao_preserva_envelope_e_nao_escreve_vigencia(monkeypatch):
    def proibida(*a, **k):
        raise AssertionError("a seleção não pode registrar vigência")
    monkeypatch.setattr(RegistroVigenciaCriterios, "registrar_revisao", proibida)
    r = sonda.medir_caso(caso("L01"), modo="id", consulta=lambda *a, **k: {"candidato_id": "c1"})
    assert r["conferencia"]["selecao"]["texto"] == "remova o arquivo quadro.svg"
    assert r["catalogo"]["fonte"]["texto"] == caso("L01")["texto"]
    assert_inerte(r)


def test_id_distingue_ocorrencias_repetidas_sem_escolher_primeira():
    c = {"id": "controle", "texto": 'As frases “remova o arquivo A” e “remova o arquivo A” se repetem.'}
    catalogo = sonda.preparar_catalogo(c)
    primeira, segunda = catalogo["candidatos"][1:]
    assert primeira["texto"] == segunda["texto"] and primeira["inicio"] != segunda["inicio"]
    r = sonda.conferir_selecao(c, catalogo, {"candidato_id": "c2"}, modo="id")
    assert r["selecao"]["inicio"] == segunda["inicio"]
    assert r["selecao"]["inicio"] != primeira["inicio"]
    assert sonda.conferir_selecao(c, catalogo, {"trecho": segunda["texto"]}, modo="copia")["estado"] == "copia_sem_ancora_unica"
    assert_inerte(r)


def test_copia_nao_aceita_reescrita_de_aspas_internas():
    c = caso("L03")
    catalogo = sonda.preparar_catalogo(c)
    trecho = catalogo["candidatos"][1]["texto"].replace("'", '"')
    r = sonda.conferir_selecao(c, catalogo, {"trecho": trecho}, modo="copia")
    assert r["estado"] == "copia_sem_ancora_unica" and r["selecao"] is None


def test_subtrecho_unico_nao_e_uma_alternativa_inventada():
    c = caso("L01")
    r = sonda.conferir_selecao(c, sonda.preparar_catalogo(c), {"trecho": "o arquivo quadro.svg"}, modo="copia")
    assert r["estado"] == "copia_fora_do_catalogo_ou_ambigua"


def test_ancora_existente_so_recupera_caixa_sem_perder_negacao():
    c = caso("L07")
    catalogo = sonda.preparar_catalogo(c)
    r = sonda.conferir_selecao(c, catalogo, {"trecho": "NÃO APAGUE O ARQUIVO MAPA.CSV"}, modo="copia")
    assert r["selecao"]["texto"] == "não apague o arquivo mapa.csv"
    assert sonda.conferir_selecao(c, catalogo, {"trecho": "apague o arquivo mapa.csv"}, modo="copia")["selecao"] is None


@pytest.mark.parametrize("proposta", [None, {}, {"candidato_id": []}, {"candidato_id": "c99"},
                                       {"candidato_id": "c1", "autoriza_efeito": True}])
def test_resposta_invalida_nao_fabrica_ocorrencia_ou_autoridade(proposta):
    c = caso("L01")
    r = sonda.conferir_selecao(c, sonda.preparar_catalogo(c), proposta, modo="id")
    assert r["selecao"] is None
    assert_inerte(r)


@pytest.mark.parametrize("chave,valor", [("inicio", 9), ("texto", "candidato inventado"),
                                         ("fonte_id", "f2"), ("id", "novo")])
def test_catalogo_adulterado_e_rejeitado_sem_materializacao(chave, valor):
    c = caso("L01")
    catalogo = sonda.preparar_catalogo(c)
    catalogo["candidatos"][1][chave] = valor
    r = sonda.conferir_selecao(c, catalogo, {"candidato_id": "c1"}, modo="id")
    assert r["estado"] == "catalogo_adulterado" and r["selecao"] is None


@pytest.mark.parametrize("valor", [0.0, False])
def test_tipo_de_offset_adulterado_nao_e_igualdade_autentica(valor):
    c = caso("L01")
    catalogo = sonda.preparar_catalogo(c)
    catalogo["candidatos"][0]["inicio"] = valor
    r = sonda.conferir_selecao(c, catalogo, {"candidato_id": "c0"}, modo="id")
    assert r["estado"] == "catalogo_adulterado" and r["selecao"] is None


def test_aspas_incoerentes_nao_fabricam_candidato_ou_ausencia():
    c = {"id": "controle", "texto": 'Ela escreveu “remova o arquivo A.'}
    catalogo = sonda.preparar_catalogo(c)
    assert catalogo["aspas_sintaticas"]["aspas_coerentes"] is False
    assert len(catalogo["candidatos"]) == 1
    r = sonda.conferir_selecao(c, catalogo, {"candidato_id": "indeterminado"}, modo="id")
    assert "sem_operacao" not in r
    assert_inerte(r)


@pytest.mark.parametrize("texto", [None, "", "   ", []])
def test_fonte_invalida_nao_chega_ao_modelo(texto):
    def proibida(*a, **k):
        raise AssertionError("fonte inválida não deve chamar modelo")
    with pytest.raises(ValueError):
        sonda.medir_caso({"id": "controle", "texto": texto}, modo="id", consulta=proibida)


def test_loader_nao_reescreve_revisao_para_fazer_placar_subir(tmp_path, monkeypatch):
    caminho = tmp_path / "revisao.json"
    caminho.write_bytes(sonda.REVISAO.read_bytes() + b" ")
    monkeypatch.setattr(sonda, "REVISAO", caminho)
    with pytest.raises(ValueError, match="congelamento"):
        sonda.carregar_painel()


def test_reparar_aspas_de_f02_nao_corrige_selecao_do_predicado_externo():
    # Falsificação local da hipótese de que cópia seria o único problema.
    antigos, ouro = anterior.carregar_painel()
    c = next(c for c in antigos if c["id"] == "F02")
    ascii_fonte = c["texto"].replace("“", '"').replace("”", '"')
    proposta = {"molduras": [{"id": "m0", "fonte_id": "f1", "tipo": "metalinguagem",
                 "trecho": ascii_fonte, "pai_id": ""}], "proposicoes": [{"id": "p0", "fonte_id": "f1",
                 "tipo": "acao", "trecho": ascii_fonte, "predicado": "Usei", "objeto": "remova o arquivo croqui.md",
                 "papel_objeto": "texto", "polaridade": "indeterminada", "moldura_id": "m0"}]}
    red = anterior.medir_caso(c, consulta=lambda *a, **k: deepcopy(proposta))
    assert red["conferencia"]["estado"] == "moldura_sem_ancora_unica"
    proposta["molduras"][0]["trecho"] = c["texto"]
    proposta["proposicoes"][0]["trecho"] = c["texto"]
    reparada = anterior.medir_caso(c, consulta=lambda *a, **k: deepcopy(proposta))
    assert reparada["conferencia"]["estado"] == "proposicoes_ancoradas_revisao_pendente"
    assert anterior.aferir(c, reparada, ouro["F02"])["predicado_alinhado"] is False
    assert_inerte(reparada)
