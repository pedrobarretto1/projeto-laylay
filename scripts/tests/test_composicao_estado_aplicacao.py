from __future__ import annotations

from mente_laylay.integracao.composicao_estado_aplicacao import (
    ComposicaoEstadoAplicacaoRuntime,
)


def test_composicao_separa_registros_e_atualiza_uma_unica_vez() -> None:
    capturado = {}
    estado_runtime = object()
    normalizador_inicial = object()
    base_inicial = object()

    def estado_factory(**kwargs):
        capturado["estado"] = kwargs
        return "estado-contexto"

    def adaptadores_factory(**kwargs):
        capturado["adaptadores"] = kwargs
        return "adaptadores"

    composicao = ComposicaoEstadoAplicacaoRuntime(
        servicos_iniciais={
            "_normalizar_texto_curto": normalizador_inicial,
            "_registrar_mente_curta_base": base_inicial,
            "SEGREDO": "não reter",
        },
        estado_runtime_getter=lambda: estado_runtime,
        estado_factory=estado_factory,
        adaptadores_factory=adaptadores_factory,
    )
    assert capturado["estado"]["namespace_getter"]() == {
        "_normalizar_texto_curto": normalizador_inicial,
    }
    assert capturado["adaptadores"]["namespace_getter"]() == {
        "_registrar_mente_curta_base": base_inicial,
    }
    assert capturado["estado"]["estado_runtime_getter"]() is estado_runtime

    normalizador_final = object()
    base_final = object()
    conectados = composicao.conectar(servicos={
        "_normalizar_texto_curto": normalizador_final,
        "_registrar_mente_curta_base": base_final,
        "SEGREDO": "não reter",
    })
    assert conectados == ("estado-contexto", "adaptadores")
    assert capturado["estado"]["namespace_getter"]() == {
        "_normalizar_texto_curto": normalizador_final,
    }
    assert capturado["adaptadores"]["namespace_getter"]() == {
        "_registrar_mente_curta_base": base_final,
    }
    assert "SEGREDO" not in composicao.servicos_estado_registrados
    assert "SEGREDO" not in composicao.servicos_adaptadores_registrados

    composicao.conectar(servicos={})
    assert capturado["estado"]["namespace_getter"]()[
        "_normalizar_texto_curto"
    ] is normalizador_final
    assert capturado["adaptadores"]["namespace_getter"]()[
        "_registrar_mente_curta_base"
    ] is base_final


def test_objetos_publicos_sao_estaveis_antes_e_depois_da_conexao() -> None:
    estado = object()
    adaptadores = object()
    composicao = ComposicaoEstadoAplicacaoRuntime(
        servicos_iniciais={},
        estado_runtime_getter=lambda: object(),
        estado_factory=lambda **_kwargs: estado,
        adaptadores_factory=lambda **_kwargs: adaptadores,
    )

    assert composicao.conectar(servicos={}) == (estado, adaptadores)
    assert composicao.estado is estado
    assert composicao.adaptadores is adaptadores
    assert composicao.conectado is True
