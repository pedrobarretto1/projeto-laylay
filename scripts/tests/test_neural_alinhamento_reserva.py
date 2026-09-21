from copy import deepcopy
import json
from pathlib import Path

import pytest

from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.neural.cobertura import carregar_manifesto_variantes
from mente_laylay.neural.alinhar_reserva_independente import alinhar_caso, executar
from mente_laylay.neural.revisar_vinculos_segmentos import vincular_plano_manual

DS = Path(__file__).parents[1] / "mente_laylay/neural/datasets"
CASOS = json.loads((DS / "reserva_relacional_independente_v1.json").read_text(encoding="utf-8"))["casos"]
VARIANTES = {(v["intent"], v["action"]) for v in carregar_manifesto_variantes(
    DS / "catalogo_variantes_v0.json", intents_catalogadas=intents_registradas())["variants"]}


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["id"])
def test_alinhamento_preserva_rotulos_e_reserva_fora_do_treino(caso):
    antes = deepcopy(caso)
    r = alinhar_caso(caso, VARIANTES)
    assert caso == antes
    original = caso["segmentos"][0]["acoes"][0]
    nova = next(a for s in r["anotacao"]["segmentos"] for a in s["acoes"])
    for k in ("intent", "action", "ato", "resolucao_alvo"):
        assert original[k] == nova[k]
    for k in ("alvos_solicitados", "alvos_excluidos", "alvos_mencionados"):
        assert [m["texto"] for m in original[k]] == [m["texto"] for m in nova[k]]
    assert r["papel_dataset"] == "reserva_independente"
    assert r["treino_permitido"] is r["autoriza_execucao"] is False


def test_conector_retirado_dos_segmentos_continua_na_entrada_e_no_plano():
    c = next(c for c in CASOS if c["id"] == "res_ind_v1_iot_01")
    r = alinhar_caso(c, VARIANTES)
    assert ", mas " in r["texto_entrada"]
    lacuna = r["plano_manual"]["lacunas_revisadas"][0]
    assert lacuna["texto"] == ", mas "
    assert c["texto_entrada"][lacuna["inicio"]:lacuna["fim"]] == lacuna["texto"]
    turno = r["referencia"]["leitura_observada"]
    intervalos = r["plano_manual"]["intervalos"]
    with pytest.raises(ValueError, match="descartaria conteúdo"):
        vincular_plano_manual(c, turno, intervalos=intervalos, donos={("IOT_CONTROL", "on"): 0}, variantes_permitidas=VARIANTES)
    lacuna["fim"] += 1
    with pytest.raises(ValueError, match="lacuna revisada"):
        vincular_plano_manual(c, turno, intervalos=intervalos, donos={("IOT_CONTROL", "on"): 0},
                             variantes_permitidas=VARIANTES, lacunas_revisadas=[lacuna])


def test_reserva_alinhada_nao_sobrescreve_destino_existente(tmp_path):
    with pytest.raises(FileExistsError):
        executar(reserva=tmp_path / "ausente", saida=tmp_path)
