"""Candidatos de trechos são literais e não fazem revisão semântica."""

from scripts.analises import sonda_produtor_candidatos_v1 as sonda
from scripts.analises.sonda_produtor_condicoes_v2 import carregar_painel


CASOS, OURO = carregar_painel(3)
POR_ID = {caso["id"]: caso for caso in CASOS}


def test_gerador_independente_cobre_condicoes_do_painel_de_desenvolvimento():
    for caso in CASOS:
        candidatos = sonda.gerar_candidatos(caso)
        assert candidatos["estado"] == "candidatos_gerados_revisao_pendente"
        assert candidatos["aprovado_para_producao"] is False
        assert candidatos["autoriza_efeito"] is False
        for item in candidatos["candidatos"]:
            assert caso["fonte"][item["inicio"]:item["fim"]] == item["citacao"]
        if OURO[caso["id"]]["representavel"]:
            cobertura = sonda.conferir_cobertura(caso, OURO[caso["id"]], candidatos)
            assert cobertura["estado"] == "cobertura_candidatos_revisao_pendente"


def test_escolha_correta_ainda_nao_autoriza_fala():
    caso = POR_ID["PAINEL_IFF"]
    candidatos = sonda.gerar_candidatos(caso)
    proposta = {"representavel": True, "candidatos_ids": ["c0"],
                "conectivo_condicoes": "unico",
                "direcao_implicacao": "equivalencia"}
    resultado = sonda.confrontar_escolha(caso, OURO[caso["id"]],
                                         candidatos, proposta)
    assert resultado["estado"] == "trechos_e_relacao_alinhados_revisao_pendente"
    assert resultado["aprovado_para_producao"] is False


def test_id_inexistente_duplicado_e_extra_sao_rejeitados():
    caso = POR_ID["PAINEL_IFF"]
    candidatos = sonda.gerar_candidatos(caso)
    base = {"representavel": True, "candidatos_ids": ["c9"],
            "conectivo_condicoes": "unico",
            "direcao_implicacao": "equivalencia"}
    assert sonda.converter_escolha(candidatos, base)["estado"] == "candidato_desconhecido"
    base["candidatos_ids"] = ["c0", "c0"]
    assert sonda.converter_escolha(candidatos, base)["estado"] == "entrada_invalida"
    base["candidatos_ids"] = ["c0"]
    base["autorizar"] = True
    assert sonda.converter_escolha(candidatos, base)["estado"] == "entrada_invalida"


def test_arvore_mista_nao_vira_regra_plana_por_existir_candidatos():
    caso = POR_ID["FILTRO_MISTO"]
    candidatos = sonda.gerar_candidatos(caso)
    proposta = {"representavel": True,
                "candidatos_ids": [item["id"] for item in candidatos["candidatos"]],
                "conectivo_condicoes": "ou",
                "direcao_implicacao": "condicoes_suficientes"}
    resultado = sonda.confrontar_escolha(caso, OURO[caso["id"]],
                                         candidatos, proposta)
    assert resultado["estado"] == "forcou_regra_nao_representavel"


def test_sem_condicional_ou_sem_ancora_nao_publica_candidatos():
    caso = {"fonte": "A bomba está ativa e o filtro está limpo."}
    resultado = sonda.gerar_candidatos(caso)
    assert resultado["estado"] == "abstencao_sem_estrutura_condicional"
    assert resultado["candidatos"] == []
    assert resultado["autoriza_efeito"] is False


def test_segmentacao_que_corta_sujeito_composto_nao_eh_cobertura(monkeypatch):
    caso = {"id": "SUJEITO_COMPOSTO", "fonte":
            "Se os sensores A e B indicarem falha, o aviso aparece.",
            "referentes": [],
            "efeito": {"referente_id": "aviso", "atributo": "estado",
                       "valor": "aparece"}}
    revisado = {"representavel": True,
                "condicoes": [{"citacao": "sensores A e B indicarem falha"}]}
    gerados = sonda.gerar_candidatos(caso)
    assert sonda.conferir_cobertura(caso, revisado, gerados)["estado"] \
        == "cobertura_divergente"

    def proibida(*args, **kwargs):
        raise AssertionError("nao chamar modelo sem cobertura")

    monkeypatch.setattr(sonda, "_consultar_modelo", proibida)
    resultado = sonda.medir_caso(caso, revisado)
    assert resultado["escolha"] == "nao_executada_primeira_fronteira_red"


def test_modelo_recebe_candidatos_sem_gabarito(monkeypatch):
    caso = POR_ID["PAINEL_IFF"]
    ouro = OURO[caso["id"]]
    entradas = []

    def consulta(_sistema, entrada, _formato, *, url, modelo):
        entradas.append(entrada)
        return {"representavel": True, "candidatos_ids": ["c0"],
                "conectivo_condicoes": "unico",
                "direcao_implicacao": "equivalencia"}

    monkeypatch.setattr(sonda, "_consultar_modelo", consulta)
    resultado = sonda.medir_caso(caso, ouro)
    assert len(entradas) == 1
    assert set(entradas[0]) == {"fonte", "referentes", "efeito", "candidatos",
                               "sinal_relacao", "sinal_conectivo"}
    assert entradas[0]["sinal_relacao"]["direcao"] == "equivalencia"
    assert entradas[0]["sinal_conectivo"] == "unico"
    assert "condicoes" not in entradas[0]
    assert resultado["afericao"]["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"


def test_painel_v4_reprojeta_cobertura_sem_apagar_historico():
    casos, ouro = carregar_painel(4)
    assert len(casos) == len(ouro) == 7
    assert set(item["id"] for item in casos) == set(ouro)
    assert not set(item["id"] for item in casos) & set(POR_ID)
    estados = {
        caso["id"]: sonda.conferir_cobertura(
            caso, ouro[caso["id"]], sonda.gerar_candidatos(caso),
        )["estado"] for caso in casos
    }
    assert list(estados.values()).count("cobertura_candidatos_revisao_pendente") == 6
    assert estados["SOLO_QUANDO"] == "cobertura_candidatos_revisao_pendente"
    assert estados["TRAVA_MISTA"] == "cobertura_nao_medida_regra_nao_plana"


def test_quando_gera_trecho_sem_inferir_direcao_logica():
    casos, ouro = carregar_painel(4)
    caso = next(item for item in casos if item["id"] == "SOLO_QUANDO")
    gerados = sonda.gerar_candidatos(caso)
    assert gerados["estado"] == "candidatos_gerados_revisao_pendente"
    assert [item["citacao"] for item in gerados["candidatos"]] \
        == ["o solo atingir 40% de umidade"]
    assert sonda.conferir_cobertura(caso, ouro[caso["id"]], gerados)["estado"] \
        == "cobertura_candidatos_revisao_pendente"


def test_marcador_veta_direcao_errada_mesmo_se_gabarito_errar():
    casos, ouro = carregar_painel(4)
    caso = next(item for item in casos if item["id"] == "ARQUIVO_ONLY")
    gabarito_errado = {**ouro[caso["id"]],
                       "direcao_implicacao": "condicoes_suficientes"}
    gerados = sonda.gerar_candidatos(caso)
    proposta = {"representavel": True, "candidatos_ids": ["c0", "c1"],
                "conectivo_condicoes": "e",
                "direcao_implicacao": "condicoes_suficientes"}
    resultado = sonda.confrontar_escolha(caso, gabarito_errado,
                                         gerados, proposta)
    assert resultado["estado"] == "direcao_divergente_marcador"
    assert resultado["autoriza_efeito"] is False


def test_variantes_so_se_e_se_e_so_se_geram_trechos_literais():
    casos = (
        ("Só se a chave estiver presente, o processo inicia.",
         "a chave estiver presente"),
        ("O aviso toca se e só se a janela abrir.",
         "a janela abrir"),
    )
    for fonte, esperado in casos:
        gerados = sonda.gerar_candidatos({"fonte": fonte})
        assert gerados["estado"] == "candidatos_gerados_revisao_pendente"
        assert [item["citacao"] for item in gerados["candidatos"]] == [esperado]


def test_se_pronominal_nao_inicia_regiao_de_condicao():
    gerados = sonda.gerar_candidatos({
        "fonte": "O motor se move apenas se o interruptor estiver ligado.",
    })
    assert [item["citacao"] for item in gerados["candidatos"]] \
        == ["o interruptor estiver ligado"]


def test_painel_v5_fixa_cobertura_e_controles_antes_da_geracao():
    casos, ouro = carregar_painel(5)
    assert len(casos) == len(ouro) == 7
    assert set(item["id"] for item in casos) == set(ouro)
    assert not set(item["id"] for item in casos) & set(POR_ID)
    estados = {
        caso["id"]: sonda.conferir_cobertura(
            caso, ouro[caso["id"]], sonda.gerar_candidatos(caso),
        )["estado"] for caso in casos
    }
    assert list(estados.values()).count("cobertura_candidatos_revisao_pendente") == 5
    assert estados["SENSORES_SUJEITO_COMPOSTO"] == "cobertura_divergente"
    assert estados["ACESSO_MISTO"] == "cobertura_nao_medida_regra_nao_plana"


def test_ou_explicito_veta_e_mesmo_com_gabarito_errado():
    casos, ouro = carregar_painel(5)
    caso = next(item for item in casos if item["id"] == "VASO_OU")
    gabarito_errado = {**ouro[caso["id"]], "conectivo_condicoes": "e"}
    gerados = sonda.gerar_candidatos(caso)
    proposta = {"representavel": True, "candidatos_ids": ["c0", "c1"],
                "conectivo_condicoes": "e",
                "direcao_implicacao": "condicoes_suficientes"}
    resultado = sonda.confrontar_escolha(caso, gabarito_errado,
                                         gerados, proposta)
    assert resultado["estado"] == "conectivo_divergente_marcador"
    assert resultado["autoriza_efeito"] is False


def test_mistura_de_conectivos_para_antes_do_modelo(monkeypatch):
    caso = POR_ID["FILTRO_MISTO"]

    def proibida(*args, **kwargs):
        raise AssertionError("arvore mista nao cabe no contrato plano")

    monkeypatch.setattr(sonda, "_consultar_modelo", proibida)
    resultado = sonda.medir_caso(caso, OURO[caso["id"]])
    assert resultado["escolha"] == "recusa_estrutura_plana"
    assert resultado["aprovado_para_producao"] is False
