from __future__ import annotations

import pytest

from mente_laylay.neural.cabeca_comando_direcionada import (
    adicionar_cabeca_comando_direcionada,
)
from mente_laylay.neural.modelo import treinar_modelo


def exemplos_base():
    return [
        {"text":"pausa a música","intent":"MEDIA_CONTROL","is_command":True,"negated":False,"action":"pause","domain":"music"},
        {"text":"essa música é boa","intent":"NONE","is_command":False,"negated":False,"action":"none","domain":"music"},
        {"text":"abre o chrome","intent":"APP_OPEN","is_command":True,"negated":False,"action":"open","domain":"app"},
        {"text":"o chrome está instalado","intent":"NONE","is_command":False,"negated":False,"action":"none","domain":"app"},
    ]


def test_adiciona_head_sem_mutar_base(tmp_path):
    base=treinar_modelo(exemplos_base(),caminho=tmp_path/"base.joblib",versao="base")
    treino=exemplos_base()+[
        {"text":"não gostei dessa faixa, pula ela","intent":"MEDIA_CONTROL","is_command":True,"negated":False,"action":"next","domain":"music","training_heads":["command"],"command_head_intent":"MEDIA_CONTROL"},
        {"text":"como eu pulo essa faixa?","intent":"NONE","is_command":False,"negated":False,"action":"none","domain":"music","training_heads":["command"],"command_head_intent":"MEDIA_CONTROL"},
    ]
    cand=adicionar_cabeca_comando_direcionada(base,treino,intent="MEDIA_CONTROL")
    assert "MEDIA_CONTROL" not in base.cabecas_comando_por_intent
    assert "MEDIA_CONTROL" in cand.cabecas_comando_por_intent
    assert cand.cabeca_intent is base.cabeca_intent
    assert cand.cabeca_negacao is base.cabeca_negacao


def test_recusa_substituir_head_existente(tmp_path):
    base=treinar_modelo(exemplos_base(),caminho=tmp_path/"base.joblib",versao="base")
    cand=adicionar_cabeca_comando_direcionada(base,exemplos_base(),intent="MEDIA_CONTROL")
    with pytest.raises(ValueError,match="já existe"):
        adicionar_cabeca_comando_direcionada(cand,exemplos_base(),intent="MEDIA_CONTROL")


def test_head_pos_extensao_fica_isolado_do_caminho_normal(tmp_path):
    base=treinar_modelo(exemplos_base(),caminho=tmp_path/"base.joblib",versao="base")
    cand=adicionar_cabeca_comando_direcionada(
        base,exemplos_base(),intent="APP_OPEN",somente_pos_extensao=True
    )
    assert "APP_OPEN" not in base.cabecas_comando_por_intent
    assert "APP_OPEN" not in cand.cabecas_comando_por_intent
    assert "APP_OPEN" not in base.cabecas_comando_extensao_por_intent
    assert "APP_OPEN" in cand.cabecas_comando_extensao_por_intent
