"""Representar não é interpretar: fontes, vínculos e autoridade ficam separados."""

from copy import deepcopy

import pytest

from scripts.analises import contrato_proposicoes_mencionadas as contrato
from scripts.analises.contrato_vigencia_criterios import RegistroVigenciaCriterios
from scripts.analises.grafo_premissas_didaticas import FonteDidatica


ESCOPO = "laboratorio_offline"


def fonte(texto, id_fonte="f1"):
    return FonteDidatica(id_fonte, "usuario", ESCOPO, texto)


def moldura(id_moldura, tipo, trecho, pai="", id_fonte="f1"):
    return {"id": id_moldura, "fonte_id": id_fonte, "tipo": tipo,
            "trecho": trecho, "pai_id": pai}


def proposicao(trecho, predicado, objeto, *, papel="entidade", polaridade="positiva",
               tipo="acao", id_proposicao="p1", id_fonte="f1", id_moldura=""):
    return {"id": id_proposicao, "fonte_id": id_fonte, "tipo": tipo, "trecho": trecho,
            "predicado": predicado, "objeto": objeto, "papel_objeto": papel,
            "polaridade": polaridade, "moldura_id": id_moldura}


def conferir(texto, proposicoes, molduras=()):
    return contrato.conferir_proposicoes_mencionadas(
        (fonte(texto),), {"proposicoes": proposicoes, "molduras": list(molduras)}, escopo=ESCOPO,
    )


def assert_inerte(resultado):
    assert all(resultado[k] is False for k in contrato.BASE)
    assert "tratado" not in resultado and "referente_id" not in resultado


@pytest.mark.parametrize("texto,predicado,objeto", [
    ("Apague o arquivo notas.txt.", "Apague", "o arquivo notas.txt"),
    ("Desligue a lâmpada da mesa.", "Desligue", "a lâmpada da mesa"),
    ("Remova a faixa da playlist estudo.", "Remova", "a faixa da playlist estudo"),
    ("Retire a regra da oficina.", "Retire", "a regra da oficina"),
])
def test_pedido_de_dominios_distintos_nao_vira_permissao_no_laboratorio(texto, predicado, objeto, monkeypatch):
    def proibida(*a, **k):
        raise AssertionError("a representação não pode escrever vigência")
    monkeypatch.setattr(RegistroVigenciaCriterios, "registrar_revisao", proibida)
    r = conferir(texto, [proposicao(texto, predicado, objeto, id_moldura="m1")],
                 [moldura("m1", "pedido", texto)])
    assert r["estado"] == "proposicoes_ancoradas_revisao_pendente"
    assert r["proposicoes"][0]["objeto"]["texto"] == objeto
    assert r["fontes"][0]["texto"] == texto
    assert_inerte(r)


def test_citacao_aninhada_preserva_pedido_interno_sem_adotar_a_ordem():
    texto = 'Ela citou “a frase \'apague o arquivo notas.txt\' é um exemplo”.'
    interno = "apague o arquivo notas.txt"
    r = conferir(texto, [proposicao(interno, "apague", "o arquivo notas.txt", id_moldura="m2")], [
        moldura("m1", "metalinguagem", texto),
        moldura("m2", "pedido", interno, pai="m1"),
    ])
    assert r["estado"] == "proposicoes_ancoradas_revisao_pendente"
    aspas = r["aspas_por_fonte"][0]
    assert aspas["aspas_coerentes"] is True
    externa, interna = aspas["regioes_entre_aspas"]
    assert externa["pai_id"] == "" and interna["pai_id"] == externa["id"]
    assert r["proposicoes"][0]["aspas_do_predicado"] == ["q0", "q1"]
    assert r["proposicoes"][0]["aspas_do_objeto"] == ["q0", "q1"]
    for regiao in aspas["regioes_entre_aspas"]:
        assert texto[regiao["inicio"]:regiao["fim"]] == regiao["texto"]
    assert r["molduras"][1]["pai_id"] == "m1"
    assert_inerte(r)


def test_hipotese_dentro_de_pergunta_nao_apaga_a_proposicao():
    texto = "Se eu desligasse a lâmpada da mesa, o que aconteceria?"
    trecho = "eu desligasse a lâmpada da mesa"
    r = conferir(texto, [proposicao(trecho, "desligasse", "a lâmpada da mesa", id_moldura="m2")], [
        moldura("m1", "pergunta", texto),
        moldura("m2", "hipotese", "Se " + trecho, pai="m1"),
    ])
    assert r["estado"] == "proposicoes_ancoradas_revisao_pendente"
    assert [m["tipo_proposto"] for m in r["molduras"]] == ["pergunta", "hipotese"]
    assert r["proposicoes"][0]["moldura_id"] == "m2"
    assert_inerte(r)


def test_apagar_texto_da_regra_nao_forca_objeto_a_ser_regra():
    texto = "Apague o texto que descreve a regra da oficina."
    r = conferir(texto, [proposicao(texto, "Apague", "o texto que descreve a regra da oficina", papel="texto")])
    assert r["estado"] == "proposicoes_ancoradas_revisao_pendente"
    assert r["proposicoes"][0]["papel_objeto_proposto"] == "texto"
    assert_inerte(r)


def test_alteracao_negada_e_pedido_sobre_outro_objeto_nao_sao_fundidos():
    texto = "A regra da oficina não foi revogada. Retire a regra do cofre."
    r = conferir(texto, [
        proposicao("A regra da oficina não foi revogada", "foi revogada", "A regra da oficina",
                   polaridade="negativa", id_moldura="m1"),
        proposicao("Retire a regra do cofre", "Retire", "a regra do cofre",
                   id_proposicao="p2", id_moldura="m2"),
    ], [moldura("m1", "relato", "A regra da oficina não foi revogada"),
        moldura("m2", "pedido", "Retire a regra do cofre")])
    assert r["estado"] == "proposicoes_ancoradas_revisao_pendente"
    assert [p["polaridade_proposta"] for p in r["proposicoes"]] == ["negativa", "positiva"]
    assert r["proposicoes"][0]["objeto"]["texto"] != r["proposicoes"][1]["objeto"]["texto"]
    assert_inerte(r)


def test_estado_de_validade_com_objeto_desconhecido_nao_inventa_revogacao():
    r = conferir("Uma não vale mais.", [proposicao("Uma não vale mais", "vale", "",
                 papel="indeterminado", polaridade="negativa", tipo="estado")])
    assert r["estado"] == "proposicoes_ancoradas_revisao_pendente"
    assert r["proposicoes"][0]["tipo_proposto"] == "estado"
    assert r["proposicoes"][0]["objeto"] is None
    assert_inerte(r)


def test_literalidade_nao_certifica_o_objeto_nem_a_polaridade_propostos():
    texto = "Não apague o texto que descreve o arquivo notas.txt."
    # Interpretação semanticamente errada, mas os trechos são literais.
    r = conferir(texto, [proposicao(texto, "apague", "o arquivo notas.txt", polaridade="positiva")])
    assert r["estado"] == "proposicoes_ancoradas_revisao_pendente"
    assert_inerte(r)


def test_moldura_omitida_nao_comprova_discurso_direto_ou_cobertura():
    texto = "Quero saber se a regra do cofre foi retirada."
    r = conferir(texto, [proposicao("a regra do cofre foi retirada", "foi retirada", "a regra do cofre")])
    assert r["estado"] == "proposicoes_ancoradas_revisao_pendente"
    assert r["molduras"] == []
    assert r["fontes"][0]["texto"] == texto  # a moldura original continua acessível.
    assert_inerte(r)


def test_lista_vazia_nao_certifica_ausencia_de_evento():
    r = conferir("Retire a regra da oficina.", [])
    assert r["estado"] == "proposicoes_ancoradas_revisao_pendente"
    assert r["proposicoes"] == []
    assert_inerte(r)


def test_filename_entre_aspas_nao_vira_citacao_semantica_de_ordem():
    texto = 'Apague o arquivo "notas.txt".'
    r = conferir(texto, [proposicao(texto, "Apague", 'o arquivo "notas.txt"')])
    assert r["aspas_por_fonte"][0]["aspas_coerentes"] is True
    assert r["proposicoes"][0]["aspas_do_predicado"] == []
    assert r["molduras"] == []
    assert_inerte(r)


def test_aspas_incoerentes_nao_sao_reparadas_ou_omitidas_da_fonte():
    texto = 'Ela escreveu "apague o arquivo notas.txt.'
    r = conferir(texto, [proposicao("apague o arquivo notas.txt", "apague", "o arquivo notas.txt")])
    assert r["aspas_por_fonte"][0]["aspas_coerentes"] is False
    assert r["aspas_por_fonte"][0]["regioes_entre_aspas"] == []
    assert r["fontes"][0]["texto"] == texto
    assert_inerte(r)


def test_predicado_repetido_so_e_ancorado_dentro_da_proposicao_unica():
    texto = "Apague o arquivo A.txt. Apague o arquivo B.txt."
    r = conferir(texto, [proposicao("Apague o arquivo B.txt", "apague", "o arquivo B.txt")])
    p = r["proposicoes"][0]
    assert p["predicado"]["inicio"] == texto.rindex("Apague")
    assert p["predicado"]["texto"] == "Apague"


@pytest.mark.parametrize("chave,valor,estado", [
    ("trecho", "apague o arquivo inventado.txt", "proposicao_sem_ancora_unica"),
    ("predicado", "Desligue", "predicado_fora_da_proposicao_ou_ambiguo"),
    ("objeto", "o arquivo B.txt", "objeto_fora_da_proposicao_ou_ambiguo"),
    ("objeto", "", "objeto_ausente_sem_abstencao"),
    ("fonte_id", "f0", "fonte_desconhecida"),
    ("polaridade", "comprovada", "rotulo_de_proposicao_invalido"),
    ("moldura_id", "m_desconhecida", "vinculo_de_proposicao_invalido"),
    ("autoriza_efeito", "sim", "proposta_invalida"),
])
def test_falha_de_um_vinculo_nao_publica_grafo_parcial(chave, valor, estado):
    texto = "Apague o arquivo A.txt. O arquivo B.txt está aberto."
    p = proposicao("Apague o arquivo A.txt", "Apague", "o arquivo A.txt")
    r = conferir(texto, [p, {**p, "id": "p2", chave: valor}])
    assert r["estado"] == estado
    assert r["proposicoes"] == [] and r["molduras"] == []
    assert_inerte(r)


def test_moldura_de_outra_oracao_nao_pode_adotar_proposicao():
    texto = "Retire a regra. Posso abrir a calculadora?"
    r = conferir(texto, [proposicao("Retire a regra", "Retire", "a regra", id_moldura="m1")],
                 [moldura("m1", "pergunta", "Posso abrir a calculadora?")])
    assert r["estado"] == "vinculo_de_proposicao_invalido"


@pytest.mark.parametrize("molduras,estado", [
    ([moldura("m1", "pedido", "Retire a regra", "m1")], "ciclo_de_molduras"),
    ([moldura("m1", "pergunta", "Retire a regra", "m2"),
      moldura("m2", "hipotese", "Retire a regra", "m1")], "ciclo_de_molduras"),
    ([moldura("m1", "pedido", "Retire a regra", "ausente")], "parentesco_de_moldura_invalido"),
    ([moldura("m1", "pedido", "Retire a regra"),
      moldura("m1", "pergunta", "Retire a regra")], "identidade_de_proposta_invalida"),
    ([moldura("m1", "autoriza", "Retire a regra")], "tipo_de_moldura_invalido"),
])
def test_parentesco_tem_identidade_contencao_e_ausencia_de_ciclo(molduras, estado):
    r = conferir("Retire a regra.", [], molduras)
    assert r["estado"] == estado
    assert_inerte(r)


def test_parentesco_nao_pula_entre_fontes_com_texto_igual():
    texto = "Retire a regra"
    proposta = {"proposicoes": [], "molduras": [moldura("m1", "pedido", texto),
                moldura("m2", "hipotese", texto, "m1", id_fonte="f2")]}
    r = contrato.conferir_proposicoes_mencionadas((fonte(texto), fonte(texto, "f2")), proposta, escopo=ESCOPO)
    assert r["estado"] == "parentesco_de_moldura_invalido"


@pytest.mark.parametrize("origem,escopo,id_fonte,texto,estado", [
    ("modelo", ESCOPO, "f1", "Retire a regra", "origem_de_fonte_invalida"),
    ("usuario", "outro", "f1", "Retire a regra", "escopo_divergente"),
    ("usuario", ESCOPO, "", "Retire a regra", "identidade_de_fonte_invalida"),
    ("usuario", ESCOPO, "f1", "", "identidade_de_fonte_invalida"),
])
def test_proveniencia_nao_e_fabricada_pelo_proponente(origem, escopo, id_fonte, texto, estado):
    r = contrato.conferir_proposicoes_mencionadas((FonteDidatica(id_fonte, origem, escopo, texto),),
        {"proposicoes": [], "molduras": []}, escopo=ESCOPO)
    assert r["estado"] == estado
    assert_inerte(r)


@pytest.mark.parametrize("origem", [[], {}, set(), None, True, 1])
def test_origem_de_tipo_invalido_falha_fechado_sem_excecao(origem):
    r = contrato.conferir_proposicoes_mencionadas((FonteDidatica("f1", origem, ESCOPO, "Texto"),),
        {"proposicoes": [], "molduras": []}, escopo=ESCOPO)
    assert r["estado"] == "origem_de_fonte_invalida"
    assert r["proposicoes"] == [] and r["fontes"] == []
    assert_inerte(r)


def test_trecho_repetido_nao_escolhe_a_primeira_ocorrencia_por_conveniencia():
    r = conferir("Retire a regra. Retire a regra.", [proposicao("Retire a regra", "Retire", "a regra")])
    assert r["estado"] == "proposicao_sem_ancora_unica"


def test_fonte_longa_e_proposta_nao_sao_normalizadas_truncadas_ou_mutadas():
    trecho = "Apague o arquivo notas.txt"
    texto = "  Contexto\n" + "texto anterior; " * 60 + trecho + ".  "
    proposta = {"proposicoes": [proposicao(trecho, "apague", "o arquivo notas.txt")], "molduras": []}
    antes = deepcopy(proposta)
    r = contrato.conferir_proposicoes_mencionadas((fonte(texto),), proposta, escopo=ESCOPO)
    assert r["estado"] == "proposicoes_ancoradas_revisao_pendente"
    assert r["fontes"][0]["texto"] == texto
    assert r["proposicoes"][0]["inicio"] == texto.index(trecho)
    assert proposta == antes


def test_molduras_coextensivas_sao_preservadas_sem_fusao():
    texto = "Se eu retirasse a regra, isso resolveria?"
    r = conferir(texto, [], [moldura("m1", "pergunta", texto),
                           moldura("m2", "hipotese", texto, "m1")])
    assert r["estado"] == "proposicoes_ancoradas_revisao_pendente"
    assert len(r["molduras"]) == 2
    assert_inerte(r)
