"""A segunda leitura não recebe parse, gabarito nem autoridade."""

from scripts.analises import sonda_avaliador_fronteira_independente as sonda
from scripts.analises.sonda_produtor_condicoes_v2 import carregar_painel


CASOS, _ = carregar_painel(21)
POR_ID = {caso["id"]: caso for caso in CASOS}


def test_entrada_contem_apenas_fonte_e_fragmentos_lexicais():
    caso = POR_ID["CAMERA_PORTAO_MOTOR_BOMBA_PRESENTE"]
    preparada = sonda.preparar_entrada(caso)
    assert preparada["estado"] == "entrada_literal_preparada"
    assert set(preparada["entrada"]) == {"fonte", "fragmentos"}
    assert preparada["entrada"]["fonte"] == caso["fonte"]
    assert [item["citacao"] for item in preparada["entrada"]["fragmentos"]] \
        == ["a câmera observa o portão", "o motor", "a bomba param"]
    assert "gabarito" not in str(preparada["entrada"])
    assert "pos_" not in str(preparada["entrada"])
    assert preparada["autoriza_efeito"] is False


def test_julgamento_exige_citacao_literal_no_lado_escolhido():
    objeto = POR_ID["SENSOR_PACOTE_SELO_REDE_PRESENTE"]
    valido = sonda.validar_julgamento(objeto, {
        "relacao": "objeto_anterior",
        "citacao": "o sensor registra o pacote e o selo",
    })
    assert valido["estado"] == "julgamento_ancorado_revisao_pendente"
    assert valido["relacao"] == "objeto_anterior"
    assert valido["autoriza_efeito"] is False

    sujeito = POR_ID["CAMERA_PORTAO_MOTOR_BOMBA_PRESENTE"]
    valido_sujeito = sonda.validar_julgamento(sujeito, {
        "relacao": "sujeito_seguinte",
        "citacao": "o motor e a bomba param",
    })
    assert valido_sujeito["estado"] == "julgamento_ancorado_revisao_pendente"
    assert valido_sujeito["relacao"] == "sujeito_seguinte"

    errado = sonda.validar_julgamento(sujeito, {
        "relacao": "objeto_anterior",
        "citacao": "o motor e a bomba param",
    })
    assert errado["estado"] == "citacao_fora_do_lado_declarado"


def test_inventar_citacao_ou_usar_frase_inteira_nao_valida_julgamento():
    caso = POR_ID["CAMERA_PORTAO_MOTOR_BOMBA_PRESENTE"]
    for citacao in ("o motor e a usina param", caso["fonte"]):
        resposta = sonda.validar_julgamento(caso, {
            "relacao": "sujeito_seguinte", "citacao": citacao,
        })
        assert resposta["estado"] != "julgamento_ancorado_revisao_pendente"
        assert resposta["aprovado_para_producao"] is False


def test_citacao_so_com_conectivo_nao_prova_nenhum_lado():
    objeto = POR_ID["SENSOR_PACOTE_SELO_REDE_PRESENTE"]
    resultado = sonda.validar_julgamento(objeto, {
        "relacao": "objeto_anterior", "citacao": "e o selo",
    })
    assert resultado["estado"] == "citacao_fora_do_lado_declarado"

    sujeito = POR_ID["CAMERA_PORTAO_MOTOR_BOMBA_PRESENTE"]
    resultado = sonda.validar_julgamento(sujeito, {
        "relacao": "sujeito_seguinte", "citacao": "o motor e ",
    })
    assert resultado["estado"] == "citacao_fora_do_lado_declarado"


def test_indeterminado_nao_pode_trazer_citacao_ou_acao():
    caso = POR_ID["CAMERA_PORTAO_MOTOR_BOMBA_PRESENTE"]
    resposta = sonda.validar_julgamento(caso, {
        "relacao": "indeterminado", "citacao": "",
    })
    assert resposta["estado"] == "abstencao_modelo"
    assert resposta["autoriza_efeito"] is False
    assert sonda.validar_julgamento(caso, {
        "relacao": "indeterminado", "citacao": "o motor",
    })["estado"] == "entrada_invalida"
    assert sonda.validar_julgamento(caso, {
        "relacao": "objeto_anterior", "citacao": "o motor",
        "executar": True,
    })["estado"] == "entrada_invalida"


def test_proposta_nao_recebe_parse_e_afericao_nao_altera_escolha():
    caso = POR_ID["SENSOR_PACOTE_SELO_REDE_PRESENTE"]
    chamadas = []

    def consultar(sistema, entrada, formato):
        chamadas.append((sistema, entrada, formato))
        return {"relacao": "objeto_anterior",
                "citacao": "o sensor registra o pacote e o selo"}

    resultado = sonda.propor(caso, consultar)
    assert resultado["estado"] == "julgamento_ancorado_revisao_pendente"
    assert resultado["resposta_bruta"] == {
        "relacao": "objeto_anterior",
        "citacao": "o sensor registra o pacote e o selo",
    }
    assert len(chamadas) == 1
    assert set(chamadas[0][1]) == {"fonte", "fragmentos"}
    assert "spaCy" not in str(chamadas[0][1])
    assert "gabarito" not in str(chamadas[0][1])
    alinhado = sonda.aferir({"relacao": "objeto_anterior"}, resultado)
    divergente = sonda.aferir({"relacao": "sujeito_seguinte"}, resultado)
    assert alinhado["estado"] == "alinhado_revisao_local"
    assert divergente["estado"] == "divergente_revisao_local"
    assert resultado["relacao"] == "objeto_anterior"


def test_instrucao_explicita_de_ambiguidade_nao_altera_contrato_de_entrada():
    caso = POR_ID["SENSOR_PACOTE_SELO_REDE_PRESENTE"]
    chamadas = []

    def consultar(sistema, entrada, formato):
        chamadas.append((sistema, entrada, formato))
        return {"relacao": "indeterminado", "citacao": ""}

    resultado = sonda.propor(
        caso, consultar, sistema=sonda.SISTEMA_AMBIGUIDADE_EXPLICITA,
    )
    assert resultado["estado"] == "abstencao_modelo"
    assert "as duas leituras" in chamadas[0][0]
    assert set(chamadas[0][1]) == {"fonte", "fragmentos"}
    assert "gabarito" not in str(chamadas[0][1])
    assert resultado["autoriza_efeito"] is False


def test_regra_mista_nao_chama_modelo():
    caso = {"id": "MISTO", "fonte": (
        "Se a chuva cair e o vento soprar ou a bateria acabar, o aviso toca."
    )}

    def proibido(*_args):
        raise AssertionError("regra mista nao deve ir ao modelo plano")

    resultado = sonda.propor(caso, proibido)
    assert resultado["estado"] == "abstencao_estrutura_lexical"
    assert resultado["autoriza_efeito"] is False


def test_painel_v22_historico_preserva_rotulos_originais_nao_validados():
    casos, revisao = sonda.carregar_painel_v22()
    assert len(casos) == len(revisao) == 10
    assert len({caso["id"] for caso in casos}) == 10
    assert [item["relacao"] for item in revisao.values()].count(
        "sujeito_seguinte",
    ) == 4
    assert [item["relacao"] for item in revisao.values()].count(
        "objeto_anterior",
    ) == 4
    assert [item["relacao"] for item in revisao.values()].count(
        "indeterminado",
    ) == 2
    assert all(sonda.preparar_entrada(caso)["estado"]
               == "entrada_literal_preparada" for caso in casos)


def test_painel_v23_historico_preserva_revisao_parcialmente_invalida():
    casos, revisao = sonda.carregar_painel_fronteira(23)
    assert len(casos) == len(revisao) == 12
    assert len({caso["id"] for caso in casos}) == 12
    assert [item["relacao"] for item in revisao.values()].count(
        "sujeito_seguinte",
    ) == 4
    assert [item["relacao"] for item in revisao.values()].count(
        "objeto_anterior",
    ) == 4
    assert [item["relacao"] for item in revisao.values()].count(
        "indeterminado",
    ) == 4
    assert all(sonda.preparar_entrada(caso)["estado"]
               == "entrada_literal_preparada" for caso in casos)


def test_painel_v24_exige_duas_leituras_literais_para_ambiguidade():
    casos, revisao = sonda.carregar_painel_fronteira(24)
    assert len(casos) == len(revisao) == 6
    for caso in casos:
        revisado = revisao[caso["id"]]
        assert revisado["relacao"] == "indeterminado"
        preparado = sonda.preparar_pares(caso)
        assert preparado["estado"] == "pares_literais_preparados"
        leituras = {
            item["relacao"]: item["trechos_condicoes"]
            for item in preparado["entrada"]["leituras"]
        }
        assert leituras == revisado["leituras_plausiveis"]
        assert all(trecho for partes in leituras.values()
                   for trecho in partes)


def test_painel_v25_tem_controles_e_ambiguidade_com_duas_leituras():
    casos, revisao = sonda.carregar_painel_fronteira(25)
    assert len(casos) == len(revisao) == 9
    assert all([item["relacao"] for item in revisao.values()].count(rotulo)
               == 3 for rotulo in sonda.RELACOES)
    for caso in casos:
        assert sonda.preparar_entrada(caso)["estado"] \
            == "entrada_literal_preparada"
        revisado = revisao[caso["id"]]
        if revisado["relacao"] == "indeterminado":
            leituras = {
                item["relacao"]: item["trechos_condicoes"]
                for item in sonda.preparar_pares(caso)["entrada"]["leituras"]
            }
            assert leituras == revisado["leituras_plausiveis"]


def test_rotulo_bruto_e_aferido_separado_da_citacao_rejeitada():
    resultado = {"estado": "citacao_fora_do_lado_declarado",
                 "resposta_bruta": {"relacao": "sujeito_seguinte",
                                     "citacao": "o paciente acordar"}}
    afericao = sonda.aferir_rotulo_bruto(
        {"relacao": "objeto_anterior"}, resultado,
    )
    assert afericao["estado"] == "rotulo_bruto_divergente_revisao_local"
    assert afericao["autoriza_efeito"] is False
    assert sonda.aferir({"relacao": "objeto_anterior"}, resultado)["estado"] \
        == "proposta_nao_aferida"


def test_rotulo_bruto_invalido_nao_aceita_campos_extras():
    resultado = {"resposta_bruta": {"relacao": "objeto_anterior",
                                     "citacao": "o copo", "executar": True}}
    assert sonda.aferir_rotulo_bruto(
        {"relacao": "objeto_anterior"}, resultado,
    )["estado"] == "rotulo_bruto_invalido"


def test_pares_expoem_duas_particoes_literais_sem_parse_ou_gabarito():
    caso = POR_ID["SENSOR_PACOTE_SELO_REDE_PRESENTE"]
    entrada = sonda.preparar_pares(caso)
    assert entrada["estado"] == "pares_literais_preparados"
    assert set(entrada["entrada"]) == {"fonte", "fragmento_medio", "leituras"}
    assert entrada["entrada"]["fragmento_medio"] == "o selo"
    assert entrada["entrada"]["leituras"] == [
        {"relacao": "objeto_anterior", "trechos_condicoes": [
            "o sensor registra o pacote e o selo", "a rede cai",
        ]},
        {"relacao": "sujeito_seguinte", "trechos_condicoes": [
            "o sensor registra o pacote", "o selo e a rede cai",
        ]},
    ]
    assert "gabarito" not in str(entrada["entrada"])
    assert "pos_" not in str(entrada["entrada"])


def test_pares_com_ordem_invertida_so_contam_concordancia_estavel():
    caso = POR_ID["SENSOR_PACOTE_SELO_REDE_PRESENTE"]
    ordens = []

    def consultar(_sistema, entrada, _formato):
        ordens.append([item["relacao"] for item in entrada["leituras"]])
        return {"relacao": "objeto_anterior"}

    resultado = sonda.propor_pares(caso, consultar)
    assert ordens == [
        ["objeto_anterior", "sujeito_seguinte"],
        ["sujeito_seguinte", "objeto_anterior"],
    ]
    assert resultado["estado"] == "rotulo_concordante_revisao_pendente"
    assert resultado["relacao"] == "objeto_anterior"
    assert resultado["autoriza_efeito"] is False


def test_pares_discordantes_ou_invalidos_se_abstem():
    caso = POR_ID["SENSOR_PACOTE_SELO_REDE_PRESENTE"]
    respostas = iter(({"relacao": "objeto_anterior"},
                     {"relacao": "sujeito_seguinte"}))
    resultado = sonda.propor_pares(
        caso, lambda *_args: next(respostas),
    )
    assert resultado["estado"] == "abstencao_por_ordem"
    assert "relacao" not in resultado
    assert resultado["autoriza_efeito"] is False

    respostas = iter(({"relacao": "objeto_anterior", "executar": True},
                     {"relacao": "objeto_anterior"}))
    invalido = sonda.propor_pares(caso, lambda *_args: next(respostas))
    assert invalido["estado"] == "rotulo_invalido"
    assert "relacao" not in invalido


def test_pares_indeterminados_e_regra_mista_nao_viram_acordo_operacional():
    caso = POR_ID["CAMERA_PORTAO_MOTOR_BOMBA_PRESENTE"]
    resultado = sonda.propor_pares(
        caso, lambda *_args: {"relacao": "indeterminado"},
    )
    assert resultado["estado"] == "abstencao_modelo"
    assert "relacao" not in resultado
    assert sonda.aferir_pares(
        {"relacao": "sujeito_seguinte"}, resultado,
    )["estado"] == "abstencao_em_caso_definido"
    assert resultado["autoriza_efeito"] is False

    misto = {"id": "MISTO", "fonte": (
        "Se a chuva cair e o vento soprar ou a bateria acabar, o aviso toca."
    )}

    def proibido(*_args):
        raise AssertionError("regra mista nao deve consultar o modelo")

    assert sonda.propor_pares(misto, proibido)["estado"] \
        == "abstencao_estrutura_lexical"
