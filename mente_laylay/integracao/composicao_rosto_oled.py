"""Conecta a saída do rosto aos owners compartilhados já existentes."""
from __future__ import annotations
from typing import Any
from mente_laylay.especialistas.rosto_oled_runtime import criar_rosto_oled_runtime, RostoOledRuntime


def criar_composicao_rosto_oled_runtime(*, estado: Any, observabilidade: Any, **kwargs: Any) -> RostoOledRuntime:
    return criar_rosto_oled_runtime(
        estado_getter=lambda: estado.retrato_dominio("conversacional"),
        atividade_getter=lambda: estado.obter_copia("mental", "atividade_operacional", {}),
        publicar_diagnostico=lambda dados: estado.atualizar_campos("mental", rosto_oled=dados),
        relatar_falha=observabilidade.relatar_falha,
        **kwargs,
    )
