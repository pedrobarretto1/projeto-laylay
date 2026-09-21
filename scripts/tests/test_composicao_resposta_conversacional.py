from __future__ import annotations

import pytest

from mente_laylay.personalidade.composicao_resposta_conversacional import (
    DEPENDENCIAS_RESPOSTA_CONVERSACIONAL,
    ComposicaoRespostaConversacionalRuntime,
)


class _Estado:
    def __init__(self) -> None:
        self.conversacional = {
            "current_emotion": "calma",
            "emotion_level": 1,
            "humor_level": 0,
        }
        self.memoria_conversa = {"messages": []}

    def substituir(self, nome, valor) -> None:
        setattr(self, nome, valor)

    def atualizar_campos(self, nome, **campos) -> None:
        atual = dict(getattr(self, nome))
        atual.update(campos)
        setattr(self, nome, atual)


def _servicos_completos() -> dict:
    return {nome: object() for nome in DEPENDENCIAS_RESPOSTA_CONVERSACIONAL}


def test_personalidade_independente_funciona_antes_da_conexao() -> None:
    estado = _Estado()
    runtime = ComposicaoRespostaConversacionalRuntime(
        estado_runtime_getter=lambda: estado,
        fallback_fala="fallback",
        log=lambda *_args: None,
    )

    assert runtime.runtime.limpar_texto_fala_ia("Olá! Comandos: []") == "Olá!"
    runtime.runtime.definir_emocao("feliz", 2, motivo="teste")
    assert estado.conversacional["current_emotion"] == "feliz"
    assert estado.conversacional["emotion_level"] == 2
    assert runtime.conectado is False


def test_conexao_filtra_congela_e_reutiliza_runtime() -> None:
    capturado = {}
    runtime_interno = object()

    def factory(**kwargs):
        capturado.update(kwargs)
        return runtime_interno

    composicao = ComposicaoRespostaConversacionalRuntime(
        estado_runtime_getter=lambda: object(),
        fallback_fala="fallback",
        runtime_factory=factory,
    )
    with pytest.raises(RuntimeError, match="ainda não conectada"):
        capturado["namespace_getter"]()

    servicos = _servicos_completos()
    original = servicos["falar_com_lipsync"]
    servicos["SEGREDO_FORA_DO_CONTRATO"] = "não reter"
    assert composicao.conectar(servicos=servicos) is runtime_interno
    servicos["falar_com_lipsync"] = object()
    servicos["novo_servico"] = object()
    snapshot = capturado["namespace_getter"]()

    assert snapshot["falar_com_lipsync"] is original
    assert "SEGREDO_FORA_DO_CONTRATO" not in snapshot
    assert "novo_servico" not in snapshot
    assert len(composicao.servicos_registrados) == len(
        DEPENDENCIAS_RESPOSTA_CONVERSACIONAL
    )
    assert composicao.conectar(servicos={}) is runtime_interno


def test_conexao_falha_cedo_com_dependencia_ausente() -> None:
    composicao = ComposicaoRespostaConversacionalRuntime(
        estado_runtime_getter=lambda: object(),
        fallback_fala="fallback",
        runtime_factory=lambda **_kwargs: object(),
    )
    servicos = _servicos_completos()
    servicos.pop("salvar_memoria")

    with pytest.raises(RuntimeError, match="salvar_memoria"):
        composicao.conectar(servicos=servicos)
