"""Intervalos não fabricam citação nem promovem fala/efeito."""

from scripts.analises import sonda_produtor_intervalos_v1 as sonda


CASOS, OURO = sonda.carregar_painel(3)


def _intervalos_revisados(caso, gabarito):
    if not gabarito["representavel"]:
        return {"representavel": False, "intervalos_condicoes": [],
                "conectivo_condicoes": "indeterminado",
                "direcao_implicacao": "indeterminado"}
    tokens = sonda.tokenizar_fonte(caso["fonte"])
    intervalos = []
    for condicao in gabarito["condicoes"]:
        citacao = condicao["citacao"]
        inicio_char = caso["fonte"].index(citacao)
        fim_char = inicio_char + len(citacao)
        inicio = next(item["id"] for item in tokens
                      if item["inicio"] == inicio_char)
        fim = next(item["id"] + 1 for item in tokens
                   if item["fim"] == fim_char)
        intervalos.append({"inicio": inicio, "fim": fim})
    return {"representavel": True, "intervalos_condicoes": intervalos,
            "conectivo_condicoes": gabarito["conectivo_condicoes"],
            "direcao_implicacao": gabarito["direcao_implicacao"]}


def test_intervalos_reconstroem_citacoes_exatas_em_cinco_dominios():
    for caso in CASOS:
        ouro = OURO[caso["id"]]
        bruto = _intervalos_revisados(caso, ouro)
        convertido = sonda.converter_intervalos(caso, bruto)
        assert convertido["estado"] == "intervalos_convertidos"
        if ouro["representavel"]:
            assert convertido["trechos"]["trechos_condicoes"] == [
                item["citacao"] for item in ouro["condicoes"]
            ]
            estado = "trechos_e_relacao_alinhados_revisao_pendente"
        else:
            estado = "abstencao_compativel"
        afericao = sonda.confrontar_intervalos(caso, ouro, bruto)
        assert afericao["estado"] == estado
        assert afericao["aprovado_para_producao"] is False
        assert afericao["autoriza_efeito"] is False


def test_fim_exclusivo_fora_da_fonte_e_booleano_nao_sao_indices():
    caso = CASOS[0]
    bruto = _intervalos_revisados(caso, OURO[caso["id"]])
    bruto["intervalos_condicoes"][0]["fim"] = len(sonda.tokenizar_fonte(caso["fonte"])) + 1
    assert sonda.converter_intervalos(caso, bruto)["estado"] == "entrada_invalida"
    bruto["intervalos_condicoes"][0]["fim"] = True
    assert sonda.converter_intervalos(caso, bruto)["estado"] == "entrada_invalida"


def test_intervalos_sobrepostos_falham_fechados():
    caso = CASOS[0]
    bruto = _intervalos_revisados(caso, OURO[caso["id"]])
    bruto["intervalos_condicoes"][1]["inicio"] = bruto["intervalos_condicoes"][0]["fim"] - 1
    assert sonda.converter_intervalos(caso, bruto)["estado"] == "entrada_invalida"


def test_intervalo_que_inclui_efeito_nao_se_alinha():
    caso = next(item for item in CASOS if item["id"] == "SENSOR_CAIXA_B")
    bruto = _intervalos_revisados(caso, OURO[caso["id"]])
    bruto["intervalos_condicoes"][0]["fim"] = len(sonda.tokenizar_fonte(caso["fonte"]))
    resultado = sonda.confrontar_intervalos(caso, OURO[caso["id"]], bruto)
    assert resultado["estado"] == "trechos_divergentes"
    assert resultado["autoriza_efeito"] is False


def test_gabarito_nao_e_enviado_ao_modelo(monkeypatch):
    caso = CASOS[0]
    ouro = OURO[caso["id"]]
    bruto = _intervalos_revisados(caso, ouro)
    chamadas = []

    def consulta(_sistema, entrada, _formato, *, url, modelo):
        chamadas.append(entrada)
        return bruto

    monkeypatch.setattr(sonda, "_consultar_modelo", consulta)
    resultado = sonda.medir_caso(caso, ouro)
    assert len(chamadas) == 1
    assert set(chamadas[0]) == {"fonte", "referentes", "efeito", "tokens"}
    assert "condicoes" not in chamadas[0]
    assert resultado["afericao"]["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"
    assert resultado["afericao"]["aprovado_para_producao"] is False
