from __future__ import annotations

from mente_laylay.autonomia.preferencias_sugestoes_runtime import (
    PreferenciasSugestoesRuntime,
)
from mente_laylay.memoria_mental.contexto_imediato import ContextoImediatoRuntime


def test_preferencias_consulta_legado_uma_vez_e_congela_conexao() -> None:
    chamadas = []
    chave_inicial = object()
    runtime = PreferenciasSugestoesRuntime(
        lambda: chamadas.append(True) or {
            "_chave_preferencia_sugestao_mente": chave_inicial,
            "SEGREDO": object(),
        }
    )
    runtime._ns()
    runtime._ns()
    assert chamadas == [True]
    assert runtime.servicos_registrados == ("_chave_preferencia_sugestao_mente",)

    chave_final = object()
    servicos = {
        "_chave_preferencia_sugestao_mente": chave_final,
        "MEMORIA_SQLITE": object(),
        "SEGREDO": object(),
    }
    runtime.conectar_servicos(servicos)
    servicos["_chave_preferencia_sugestao_mente"] = object()
    assert runtime._ns()["_chave_preferencia_sugestao_mente"] is chave_final
    assert "MEMORIA_SQLITE" in runtime.servicos_registrados
    assert "SEGREDO" not in runtime.servicos_registrados


def test_contexto_imediato_filtra_atualiza_e_preserva_estado_vivo() -> None:
    chamadas = []
    estado = object()
    normalizador_inicial = object()
    runtime = ContextoImediatoRuntime(
        namespace_getter=lambda: chamadas.append(True) or {
            "_normalizar_texto_com_apelidos": normalizador_inicial,
            "SEGREDO": object(),
        },
        estado_runtime_getter=lambda: estado,
    )
    runtime._namespace()
    runtime._namespace()
    assert chamadas == [True]

    normalizador_final = object()
    servicos = {
        "_normalizar_texto_com_apelidos": normalizador_final,
        "_foco_vivo_atual": object(),
        "SEGREDO": object(),
    }
    runtime.conectar_servicos(servicos)
    servicos["_normalizar_texto_com_apelidos"] = object()

    assert runtime._namespace()["_normalizar_texto_com_apelidos"] is normalizador_final
    assert runtime._estado() is estado
    assert "_foco_vivo_atual" in runtime.servicos_registrados
    assert "SEGREDO" not in runtime.servicos_registrados
