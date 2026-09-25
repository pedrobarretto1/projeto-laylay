"""A seleção de trechos e a normalização falham fechadas e são medidas à parte."""

from scripts.analises import sonda_produtor_condicoes_v2 as sonda
from scripts.analises.sonda_produtor_condicoes_v2 import (
    carregar_painel, conferir_normalizacao, conferir_trechos, confrontar_trechos,
)


CASOS, OURO = carregar_painel()
POR_ID = {caso["id"]: caso for caso in CASOS}


def _trechos(id_caso):
    gabarito = OURO[id_caso]
    if not gabarito["representavel"]:
        return {"representavel": False, "trechos_condicoes": [],
                "conectivo_condicoes": "indeterminado",
                "direcao_implicacao": "indeterminado"}
    return {"representavel": True,
            "trechos_condicoes": [item["citacao"] for item in gabarito["condicoes"]],
            "conectivo_condicoes": gabarito["conectivo_condicoes"],
            "direcao_implicacao": gabarito["direcao_implicacao"]}


def test_painel_v2_eh_novo_e_gabarito_fica_separado():
    assert len(CASOS) == len(OURO) == 6
    assert set(POR_ID) == set(OURO)
    assert "parede estiver limpa" not in str(CASOS)


def test_painel_v3_congelado_antes_da_geracao_tem_referencias_validas():
    casos, ouro = carregar_painel(3)
    assert len(casos) == len(ouro) == 6
    assert set(item["id"] for item in casos) == set(ouro)
    assert not set(item["id"] for item in casos) & set(POR_ID)
    for caso in casos:
        revisado = ouro[caso["id"]]
        if revisado["representavel"]:
            bruto_trechos = {
                "representavel": True,
                "trechos_condicoes": [item["citacao"] for item in revisado["condicoes"]],
                "conectivo_condicoes": revisado["conectivo_condicoes"],
                "direcao_implicacao": revisado["direcao_implicacao"],
            }
            assert confrontar_trechos(caso, revisado, bruto_trechos)["estado"] \
                == "trechos_e_relacao_alinhados_revisao_pendente"
            normalizado = {"condicoes": [
                {chave: valor for chave, valor in item.items()
                 if chave not in {"fonte_id", "citacao"}}
                for item in revisado["condicoes"]
            ]}
            assert conferir_normalizacao(caso, revisado, bruto_trechos,
                                         normalizado)["estado"] \
                == "slots_e_relacao_alinhados_revisao_pendente"


def test_trechos_exatos_nao_aprovam_fala():
    resultado = confrontar_trechos(
        POR_ID["IMPORTACAO_E"], OURO["IMPORTACAO_E"],
        _trechos("IMPORTACAO_E"),
    )
    assert resultado["estado"] == "trechos_e_relacao_alinhados_revisao_pendente"
    assert resultado["aprovado_para_producao"] is False
    assert resultado["autoriza_efeito"] is False


def test_trecho_inventado_falha_antes_da_relacao():
    bruto = _trechos("IMPORTACAO_E")
    bruto["trechos_condicoes"][0] = "arquivo de vídeo"
    resultado = conferir_trechos(POR_ID["IMPORTACAO_E"], bruto)
    assert resultado["estado"] == "citacao_invalida"


def test_trecho_que_omite_condicao_fica_visivel():
    bruto = _trechos("RELATORIO_ONLY")
    bruto["trechos_condicoes"].pop()
    bruto["conectivo_condicoes"] = "unico"
    resultado = confrontar_trechos(POR_ID["RELATORIO_ONLY"], OURO["RELATORIO_ONLY"], bruto)
    assert resultado["estado"] == "trechos_divergentes"


def test_mesmos_trechos_com_ou_trocado_por_e_sao_divergentes():
    bruto = _trechos("AMBIENTE_OU")
    bruto["conectivo_condicoes"] = "e"
    resultado = confrontar_trechos(POR_ID["AMBIENTE_OU"], OURO["AMBIENTE_OU"], bruto)
    assert resultado["estado"] == "conectivo_divergente"


def test_arvore_mista_exige_abstencao():
    resultado = confrontar_trechos(POR_ID["PACOTE_MISTO"], OURO["PACOTE_MISTO"],
                                   _trechos("PACOTE_MISTO"))
    assert resultado["estado"] == "abstencao_compativel"
    assert resultado["aprovado_para_producao"] is False


def test_normalizacao_exata_nao_aprova_fala():
    gold = OURO["MOTOR_IFF"]
    normalizado = {"condicoes": [
        {chave: valor for chave, valor in item.items()
         if chave not in {"fonte_id", "citacao"}}
        for item in gold["condicoes"]
    ]}
    resultado = conferir_normalizacao(POR_ID["MOTOR_IFF"], gold,
                                      _trechos("MOTOR_IFF"), normalizado)
    assert resultado["estado"] == "slots_e_relacao_alinhados_revisao_pendente"
    assert resultado["aprovado_para_producao"] is False


def test_operador_conectivo_na_normalizacao_eh_rejeitado():
    gold = OURO["MOTOR_IFF"]
    resultado = conferir_normalizacao(
        POR_ID["MOTOR_IFF"], gold, _trechos("MOTOR_IFF"),
        {"condicoes": [{"referente_id": "interruptor", "atributo": "estado",
                       "operador": "e", "valor": "ligado", "unidade": ""}]},
    )
    assert resultado["estado"] == "proposta_invalida"
    assert resultado["autoriza_efeito"] is False


def test_saida_malformada_falha_fechada():
    bruto = _trechos("MOTOR_IFF")
    bruto["conectivo_condicoes"] = []
    assert conferir_trechos(POR_ID["MOTOR_IFF"], bruto)["estado"] == "entrada_invalida"


def test_gabarito_nao_vaza_e_segundo_estagio_para_na_primeira_fronteira(monkeypatch):
    chamadas = []

    def consulta(_sistema, entrada, _formato, *, url, modelo):
        chamadas.append(entrada)
        return {"representavel": True, "trechos_condicoes": ["importador aceita"],
                "conectivo_condicoes": "unico",
                "direcao_implicacao": "condicoes_suficientes"}

    monkeypatch.setattr(sonda, "_consultar_modelo", consulta)
    resultado = sonda.medir_caso(POR_ID["IMPORTACAO_E"], OURO["IMPORTACAO_E"])
    assert len(chamadas) == 1
    assert set(chamadas[0]) == {"fonte", "referentes", "efeito"}
    assert "condicoes" not in chamadas[0]
    assert resultado["afericao_trechos"]["estado"] == "trechos_divergentes"
    assert resultado["normalizacao"] == "nao_executada_primeira_fronteira_red"


def test_artigo_inicial_nao_mascara_erro_de_implicacao():
    bruto = _trechos("RELATORIO_ONLY")
    bruto["trechos_condicoes"] = ["a revisão for concluída", "a fonte estiver citada"]
    bruto["direcao_implicacao"] = "condicoes_suficientes"
    resultado = confrontar_trechos(POR_ID["RELATORIO_ONLY"],
                                   OURO["RELATORIO_ONLY"], bruto)
    assert resultado["trechos_alinhados_revisao"] is True
    assert resultado["estado"] == "implicacao_divergente"


def test_artigo_inicial_permite_medir_normalizacao_sem_copiar_gabarito():
    gold = OURO["MOTOR_IFF"]
    trechos = _trechos("MOTOR_IFF")
    trechos["trechos_condicoes"] = ["o interruptor estiver ligado"]
    normalizado = {"condicoes": [
        {chave: valor for chave, valor in gold["condicoes"][0].items()
         if chave not in {"fonte_id", "citacao"}}
    ]}
    assert confrontar_trechos(POR_ID["MOTOR_IFF"], gold, trechos)["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"
    resultado = conferir_normalizacao(POR_ID["MOTOR_IFF"], gold,
                                      trechos, normalizado)
    assert resultado["estado"] == "slots_e_relacao_alinhados_revisao_pendente"


def test_case_de_se_inicial_eh_ancorado_na_fonte():
    bruto = _trechos("TANQUE_SENSOR")
    bruto["trechos_condicoes"] = ["se o sensor do tanque indicar menos de 10 litros"]
    resultado = confrontar_trechos(POR_ID["TANQUE_SENSOR"],
                                   OURO["TANQUE_SENSOR"], bruto)
    assert resultado["estado"] == "trechos_e_relacao_alinhados_revisao_pendente"


def test_condicoes_fundidas_nao_viram_um_trecho_equivalente():
    bruto = _trechos("IMPORTACAO_E")
    bruto["trechos_condicoes"] = [
        "Se o arquivo tiver extensão .csv e o cabeçalho contiver a coluna data",
    ]
    bruto["conectivo_condicoes"] = "unico"
    resultado = confrontar_trechos(POR_ID["IMPORTACAO_E"],
                                   OURO["IMPORTACAO_E"], bruto)
    assert resultado["estado"] == "trechos_divergentes"


def test_tentar_achatar_arvore_mista_eh_erro_de_representabilidade_primeiro():
    bruto = {"representavel": True,
             "trechos_condicoes": ["se a revisao e o checksum passarem"],
             "conectivo_condicoes": "ou",
             "direcao_implicacao": "condicoes_suficientes"}
    resultado = confrontar_trechos(POR_ID["PACOTE_MISTO"],
                                   OURO["PACOTE_MISTO"], bruto)
    assert resultado["estado"] == "forcou_regra_nao_representavel"
    assert resultado["autoriza_efeito"] is False
