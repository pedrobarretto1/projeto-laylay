"""IDs dos fragmentos são campos fixos, nunca texto inventado pelo modelo."""

from scripts.analises import sonda_fronteira_predicados_v2 as sonda
from scripts.analises.sonda_produtor_condicoes_v2 import carregar_painel


CASOS, OURO = carregar_painel(7)
POR_ID = {caso["id"]: caso for caso in CASOS}


def test_schema_exige_ids_fixos_sem_campo_id_livre():
    formato = sonda.formato_predicados_fixos(POR_ID["SENSORES_E_BATERIA"])
    assert formato["type"] == "object"
    assert formato["additionalProperties"] is False
    assert formato["required"] == ["c0", "c1", "c2"]
    assert set(formato["properties"]) == {"c0", "c1", "c2"}
    for valor in formato["properties"].values():
        assert valor["required"] == ["tem_predicado", "ancora"]
        assert "id" not in valor["properties"]


def test_mapa_fixo_reconstroi_particao_intermediaria():
    caso = POR_ID["SENSORES_E_BATERIA"]
    bruto = {"c0": {"tem_predicado": False, "ancora": ""},
             "c1": {"tem_predicado": True, "ancora": "detectarem"},
             "c2": {"tem_predicado": True, "ancora": "estiver"}}
    resultado = sonda.converter_mapa_predicados(caso, bruto)
    assert resultado["estado"] == "segmentos_ancorados_revisao_pendente"
    assert resultado["trechos"]["trechos_condicoes"] == [
        "os sensores A e B detectarem fumaça", "a bateria estiver carregada",
    ]
    assert resultado["aprovado_para_producao"] is False
    assert resultado["autoriza_efeito"] is False


def test_mapa_sem_chave_com_extra_ou_ancora_inventada_recusa():
    caso = POR_ID["MODULOS_SUJEITO_E"]
    valido = {"c0": {"tem_predicado": False, "ancora": ""},
              "c1": {"tem_predicado": True, "ancora": "enviarem"}}
    assert sonda.converter_mapa_predicados(caso, {"c0": valido["c0"]})[
        "estado"] == "entrada_invalida"
    assert sonda.converter_mapa_predicados(caso, {**valido, "c9": valido["c1"]})[
        "estado"] == "entrada_invalida"
    assert sonda.converter_mapa_predicados(caso, {**valido, "c1": {
        "tem_predicado": True, "ancora": "inexistente",
    }})["estado"] == "ancora_invalida"


def test_modelo_recebe_ids_fixos_sem_gabarito(monkeypatch):
    caso = POR_ID["MODULOS_SUJEITO_E"]
    chamadas = []

    def consultar(_sistema, entrada, formato, *, url, modelo):
        chamadas.append((entrada, formato))
        return {"c0": {"tem_predicado": False, "ancora": ""},
                "c1": {"tem_predicado": True, "ancora": "enviarem"}}

    monkeypatch.setattr(sonda, "_consultar_modelo", consultar)
    resultado = sonda.medir_caso(caso, OURO[caso["id"]])
    assert len(chamadas) == 1
    entrada, formato = chamadas[0]
    assert "gabarito" not in entrada and "condicoes" not in entrada
    assert set(entrada["fragmentos"]) == {"c0", "c1"}
    assert formato["required"] == ["c0", "c1"]
    assert resultado["afericao"]["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"
    assert resultado["aprovado_para_producao"] is False


def test_misto_recusa_antes_do_modelo(monkeypatch):
    caso = POR_ID["PROTOCOLO_MISTO_V7"]

    def proibida(*args, **kwargs):
        raise AssertionError("arvore mista fora do contrato")

    monkeypatch.setattr(sonda, "_consultar_modelo", proibida)
    assert sonda.medir_caso(caso, OURO[caso["id"]])["escolha"] \
        == "recusa_estrutura_plana"


def test_schema_plano_tem_campos_tipados_e_ids_fixos():
    formato = sonda.formato_predicados_plano(POR_ID["SENSORES_E_BATERIA"])
    assert formato["type"] == "object"
    assert formato["additionalProperties"] is False
    assert formato["required"] == [
        "c0_tem_predicado", "c0_ancora", "c1_tem_predicado", "c1_ancora",
        "c2_tem_predicado", "c2_ancora",
    ]
    assert formato["properties"]["c0_tem_predicado"] == {"type": "boolean"}
    assert formato["properties"]["c1_ancora"] == {"type": "string"}


def test_conversao_plana_ancora_e_recusa_campos_errados():
    caso = POR_ID["SENSORES_E_BATERIA"]
    proposta = {"c0_tem_predicado": False, "c0_ancora": "",
                "c1_tem_predicado": True, "c1_ancora": "detectarem",
                "c2_tem_predicado": True, "c2_ancora": "estiver"}
    resultado = sonda.converter_mapa_plano(caso, proposta)
    assert resultado["estado"] == "segmentos_ancorados_revisao_pendente"
    assert resultado["trechos"]["trechos_condicoes"] == [
        "os sensores A e B detectarem fumaça", "a bateria estiver carregada",
    ]
    assert sonda.converter_mapa_plano(caso, {**proposta, "extra": True})[
        "estado"] == "entrada_invalida"
    assert sonda.converter_mapa_plano(caso, {**proposta, "c1_ancora": "inventado"})[
        "estado"] == "ancora_invalida"


def test_contrato_plano_envia_so_fonte_e_fragmentos(monkeypatch):
    caso = POR_ID["MODULOS_SUJEITO_E"]
    chamadas = []

    def consultar(_sistema, entrada, formato, *, url, modelo):
        chamadas.append((entrada, formato))
        return {"c0_tem_predicado": False, "c0_ancora": "",
                "c1_tem_predicado": True, "c1_ancora": "enviarem"}

    monkeypatch.setattr(sonda, "_consultar_modelo", consultar)
    resultado = sonda.medir_caso(
        caso, OURO[caso["id"]], contrato="plano_minimo",
    )
    assert len(chamadas) == 1
    entrada, formato = chamadas[0]
    assert set(entrada) == {"fonte", "fragmentos"}
    assert formato["required"] == [
        "c0_tem_predicado", "c0_ancora", "c1_tem_predicado", "c1_ancora",
    ]
    assert resultado["afericao"]["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"
    assert resultado["aprovado_para_producao"] is False
