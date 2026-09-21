"""Contratos da medição; fixtures de previsão não são acurácia do modelo."""
from copy import deepcopy
import json

import pytest

from mente_laylay.neural.diagnosticar_contrastes_piloto import avaliar, executar
from mente_laylay.neural.preparar_contrastes_piloto import gerar_lote


class PrevisaoFixa:
    versao = "fixture"

    def __init__(self, **campos):
        self.recebidos = []
        self.previsao = {"intent": "APP_OPEN", "raw_action": "open", "params": {"acao": "open"},
                         "is_command": True, "negated": False, "ood": False, **campos}

    def prever(self, texto):
        assert isinstance(texto, str)
        self.recebidos.append(texto)
        return deepcopy(self.previsao)


def test_so_texto_entra_na_inferencia_e_gold_nao_e_alterado():
    casos = gerar_lote()[:3]
    antes = deepcopy(casos)
    modelo = PrevisaoFixa()
    r = avaliar(casos, modelo)
    assert modelo.recebidos == [c["texto"] for c in casos]
    assert casos == antes
    assert r["fatias"]["APP_OPEN|open|pedido"]["pedidos_corretos"] == 1
    for ato in ("recusa", "relato"):
        assert r["fatias"][f"APP_OPEN|open|{ato}"]["pedidos_indevidos"] == 1
    assert r["ato_por_ocorrencia_medido"] is False
    assert all(x["normalizado"]["autoriza_execucao"] is False for x in r["registros"])


@pytest.mark.parametrize("campos", [
    {"negated": True}, {"is_command": False}, {"ood": True},
])
def test_gates_canonicos_bloqueiam_proposta_sem_inventar_ato(campos):
    r = avaliar(gerar_lote()[:3], PrevisaoFixa(**campos))
    assert r["fatias"]["APP_OPEN|open|pedido"]["pedidos_perdidos"] == 1
    assert r["fatias"]["APP_OPEN|open|relato"]["pedidos_indevidos"] == 0
    assert all(not x["proposta_apos_gates"] for x in r["registros"])


def test_ood_nao_calibrado_preserva_semantica_do_predicado_existente():
    r = avaliar(gerar_lote()[:1], PrevisaoFixa(ood=True, ood_calibrated=False))
    assert r["registros"][0]["proposta_apos_gates"] is True
    assert r["registros"][0]["normalizado"]["autoriza_execucao"] is False


def test_intencao_correta_sem_acao_correta_nao_e_pedido_correto():
    r = avaliar(gerar_lote()[:1], PrevisaoFixa(raw_action="close", params={"acao": "close"}))
    f = r["fatias"]["APP_OPEN|open|pedido"]
    assert f["intent_correta"] == 1 and f["acao_bruta_correta"] == 0
    assert f["pedidos_corretos"] == 0 and f["pedidos_perdidos"] == 1


def test_fora_perfil_e_observado_sem_score_ou_gold_automatico():
    r = avaliar(gerar_lote()[-6:], PrevisaoFixa())
    assert r["fatias"] == {} and r["fora_perfil_sem_score"] == 6
    assert all(x["gold"] is x["medicao"] is None for x in r["registros"])


def test_particao_inedita_e_rejeitada_antes_de_inferir():
    casos = gerar_lote()[:1]
    casos[0]["particao"] = "selecao"
    modelo = PrevisaoFixa()
    with pytest.raises(ValueError, match="somente desenvolvimento"):
        avaliar(casos, modelo)
    assert modelo.recebidos == []


def test_falha_de_modelo_nao_vira_acerto_de_abstencao():
    class Quebrado:
        def prever(self, texto):
            raise RuntimeError("não carregou")

    with pytest.raises(RuntimeError, match="não carregou"):
        avaliar(gerar_lote()[:1], Quebrado())


def test_destino_existente_aborta_antes_de_carregar_fontes(tmp_path):
    with pytest.raises(FileExistsError, match="preservar"):
        executar(tmp_path / "inexistente.jsonl", {"a": tmp_path / "modelo.joblib"}, tmp_path)


def test_fonte_concorrente_impede_publicacao(monkeypatch, tmp_path):
    import mente_laylay.neural.diagnosticar_contrastes_piloto as modulo

    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(json.dumps(gerar_lote()[0]), encoding="utf-8")
    caminho = tmp_path / "modelo.joblib"
    caminho.write_bytes(b"fixture")
    def carregar(_):
        caminho.write_bytes(b"mudou")
        return PrevisaoFixa()
    monkeypatch.setattr(modulo, "carregar_modelo", carregar)
    destino = tmp_path / "saida"
    with pytest.raises(ValueError, match="fonte mudou"):
        executar(corpus, {"a": caminho}, destino)
    assert not destino.exists()
