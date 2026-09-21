from __future__ import annotations

import json
from pathlib import Path

import pytest

from mente_laylay.neural.dataset import validar_exemplo
from mente_laylay.neural.datasets.gerar_list_windows_atos_v3 import (
    MOLDES, gerar_exemplos, validar_lote,
)
from mente_laylay.neural.datasets.gerar_list_windows_onda_v2 import _chave_texto


DATASETS = Path(__file__).resolve().parents[2] / "mente_laylay/neural/datasets"


def test_complemento_reproduz_staging_sem_command_ou_rotulo_da_propria_previsao():
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    assert resumo == {"total": 320, "positivos": 128, "negativos": 192, "grupos": 15, "entidades": 16}
    gravados = [json.loads(linha) for linha in (
        DATASETS / "candidatos/list_windows_atos_v3.jsonl"
    ).read_text(encoding="utf-8").splitlines()]
    assert gravados == exemplos
    for item in exemplos:
        assert item["extension_factors"]["ato_consulta"] == (item["intent"] == "LIST_WINDOWS")
        assert item["extension_factors"]["dominio_app"] is True
        assert "command" not in item["training_heads"]
        assert item["source"] in {"MANUAL_PARAPHRASE", "HARD_NEGATIVE"}
        assert "autoriza_execucao" not in item


def test_variantes_dos_mecanismos_historicos_preservam_grupo():
    exemplos = gerar_exemplos()
    for numero, (grupo, _, _) in enumerate(MOLDES):
        fatia = [x for x in exemplos if x["family"] == f"{grupo}_complemento_{numero}"]
        assert len(fatia) == 16
        assert {x["validation_group"] for x in fatia} == {grupo}
    assert sum(x["validation_group"].startswith("list_windows_v2_") for x in exemplos) == 288


def test_reserva_e_separada_e_nao_e_dataset_de_treino():
    reserva = json.loads((DATASETS / "reservas/list_windows_ato_v1.json").read_text(encoding="utf-8"))
    assert reserva["treino_permitido"] is False
    assert reserva["autoriza_execucao"] is False
    itens = reserva["exemplos"]
    assert len(itens) == len({x["id"] for x in itens}) == 24
    assert {(x["ato_consulta"], x["dominio_app"]) for x in itens} == {
        (True, True), (True, False), (False, True), (False, False),
    }
    chaves = {_chave_texto(x["text"]) for x in itens}
    assert len(chaves) == 24
    for caminho in [*DATASETS.glob("*.jsonl"), *DATASETS.joinpath("candidatos").glob("*.jsonl")]:
        textos_treino = {
            _chave_texto(json.loads(linha).get("text"))
            for linha in caminho.read_text(encoding="utf-8-sig").splitlines() if linha.strip()
        }
        assert not chaves & textos_treino, f"reserva colide com {caminho.name}"
    for item in itens:
        with pytest.raises(ValueError):
            validar_exemplo(item, intents_permitidas={"LIST_WINDOWS"})


@pytest.mark.parametrize("origem", ["duplicado", "ancora", "reserva"])
def test_gerador_recusa_contaminacao(origem):
    exemplos = gerar_exemplos()
    item = dict(exemplos[0])
    if origem == "ancora":
        item["text"] = json.loads((DATASETS / "candidatos/list_windows_onda_v2.jsonl").read_text(encoding="utf-8").splitlines()[0])["text"]
    elif origem == "reserva":
        item["text"] = json.loads((DATASETS / "reservas/list_windows_ato_v1.json").read_text(encoding="utf-8"))["exemplos"][0]["text"]
    with pytest.raises(ValueError, match="colisão"):
        validar_lote([*exemplos, item])
