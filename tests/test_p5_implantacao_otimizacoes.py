from __future__ import annotations

import asyncio

from mente_laylay.autonomia.composicao_servicos import (
    ComposicaoServicosLaylayRuntime,
)
from mente_laylay.cognicao import resumo_conteudo
from mente_laylay.cognicao.resumo_conteudo import ResumoConteudoRuntime
from mente_laylay.memoria_mental.diagnostico_mente import (
    construir_diagnostico_mente,
)
from mente_laylay.memoria_mental.formatacao_diagnostico import (
    formatar_diagnostico_terminal,
)
from mente_laylay.memoria_mental.implantacao_desempenho import (
    GuardiaoImplantacaoDesempenho,
    flag_desempenho_ativa,
    snapshot_flags_desempenho,
)
from mente_laylay.memoria_mental.observabilidade import ObservabilidadeMenteRuntime


def test_flag_mestre_reverte_todas_as_otimizacoes(monkeypatch) -> None:
    monkeypatch.setenv("LAYLAY_OTIMIZACOES_DESEMPENHO", "0")
    monkeypatch.setenv("LAYLAY_CACHE_RESUMOS_ATIVO", "1")

    assert flag_desempenho_ativa("LAYLAY_CACHE_RESUMOS_ATIVO") is False
    snapshot = snapshot_flags_desempenho()
    assert snapshot["modo"] == "revertido"
    assert not any(snapshot["flags"].values())


def test_guardiao_so_reverte_depois_de_regressao_repetida() -> None:
    motivos = []
    publicados = []
    guardiao = GuardiaoImplantacaoDesempenho(
        desativar=motivos.append,
        publicar_estado=publicados.append,
        limite_consecutivo=3,
        limite_janela=5,
    )

    assert guardiao.observar("contradicao") is False
    assert guardiao.observar("contradicao") is False
    assert guardiao.observar("contradicao") is True
    assert motivos == ["contradicao"]
    assert guardiao.snapshot()["revertido"] is True
    assert publicados[-1]["conteudo_exposto"] is False


def test_observabilidade_liga_falso_sucesso_ao_guardiao() -> None:
    estado = {}
    sinais = []
    runtime = ObservabilidadeMenteRuntime(
        estado_getter=lambda chave, padrao=None: estado.get(chave, padrao),
        estado_setter=lambda **campos: estado.update(campos),
        observar_implantacao=sinais.append,
    )

    runtime.registrar_falha(
        "fala", "sucesso_sem_evidencia", classe="defeito",
        impacto="fala", fallback="fallback_local",
    )

    assert sinais == ["falso_sucesso"]


def test_falhas_repetidas_suprimidas_ainda_acionam_reversao() -> None:
    estado = {}
    motivos = []
    guardiao = GuardiaoImplantacaoDesempenho(
        desativar=motivos.append,
        limite_consecutivo=3,
        limite_janela=5,
    )
    runtime = ObservabilidadeMenteRuntime(
        estado_getter=lambda chave, padrao=None: estado.get(chave, padrao),
        estado_setter=lambda **campos: estado.update(campos),
        observar_implantacao=guardiao.observar,
        janela_repeticao_s=30,
    )

    for _ in range(3):
        runtime.relatar_falha(
            "fala", "contradicao_resultado", classe="defeito",
            impacto="fala", fallback="fallback_local",
        )

    assert motivos == ["contradicao"]
    assert guardiao.snapshot()["revertido"] is True


def test_cache_de_resumo_pode_ser_revertido_sem_perder_a_habilidade(
    monkeypatch,
) -> None:
    recebidos = []

    async def resumir_falso(**kwargs):
        recebidos.append(kwargs.get("cache_resumos"))
        return True

    class ModeloFalso:
        @staticmethod
        def executar(_pedido):
            return None

        @staticmethod
        def diagnostico():
            return {"disponivel": True}

    monkeypatch.setattr(resumo_conteudo, "resumir_pagina_ou_video", resumir_falso)
    runtime = ResumoConteudoRuntime(
        namespace_getter=lambda: {
            "websocket_disponivel": lambda: True,
            "solicitar_conteudo": lambda: None,
            "falar": lambda *_args: None,
            "limpar_resposta": lambda texto: texto,
            "remover_prefixo_exec": lambda texto: texto,
            "transcript_api": object(),
        },
        modelo_llm=ModeloFalso(),
        cache_habilitado=True,
    )

    assert asyncio.run(runtime.resumir()) is True
    runtime.desativar_cache()
    assert asyncio.run(runtime.resumir()) is True

    assert isinstance(recebidos[0], dict)
    assert recebidos[1] is None


def test_startup_reverte_para_sincrono_se_background_nao_agendar() -> None:
    ordem = []

    class Gerenciador:
        deve_parar = staticmethod(lambda: False)

        @staticmethod
        def iniciar(_nome, _target):
            return False

    class Orquestrador:
        @staticmethod
        def iniciar(*, etapas, threads, hotkeys):
            for target in etapas.values():
                target()
            return {"etapas": {}, "threads": {}}

        @staticmethod
        def executar_etapas(etapas):
            for target in etapas.values():
                target()
            return {nome: True for nome in etapas}

    runtime = ComposicaoServicosLaylayRuntime(
        gerenciador=Gerenciador(),
        etapas={"memoria": lambda: ordem.append("memoria")},
        etapas_diferidas={"avatar": lambda: ordem.append("avatar")},
        threads={},
        log=lambda *_args: None,
    )

    resultado = runtime.iniciar(Orquestrador())

    assert ordem == ["memoria", "avatar"]
    assert resultado["etapas_diferidas"] == {
        "agendada": False,
        "revertida_sincrona": True,
    }
    assert runtime.estado_prontidao()["fase"] == "servicos_completos"


def test_diagnostico_expoe_implantacao_sem_autorizacao() -> None:
    diagnostico = construir_diagnostico_mente(
        {
            "mental": {
                "diagnostico_implantacao_desempenho": {
                    "modo": "gradual",
                    "mestre_ativa": True,
                    "revertido": False,
                    "flags": {"cache_resumos": True},
                    "eventos_janela": 1,
                },
            },
        },
        {},
    )

    implantacao = diagnostico["implantacao_desempenho"]
    assert implantacao["flags"] == {"cache_resumos": True}
    assert implantacao["autoriza_execucao"] is False
    texto = formatar_diagnostico_terminal(diagnostico)
    assert "implantação de desempenho: modo=gradual" in texto
