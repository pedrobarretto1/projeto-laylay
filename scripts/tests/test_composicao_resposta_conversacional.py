from __future__ import annotations

import pytest
import time

from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.integracao.politicas_composicao import construir_estado_visual
from mente_laylay.personalidade.resposta_conversacional_runtime import (
    RespostaConversacionalRuntime,
)

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
    # A composição pode ser usada antes da conexão, mas um motivo livre não
    # substitui um evento causal publicado para alterar o estado emocional.
    assert estado.conversacional["current_emotion"] == "calma"
    assert estado.conversacional["emotion_level"] == 1
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


def test_resposta_curta_herda_nivel_do_episodio_para_voz() -> None:
    estado = _Estado()
    evento = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="redundância confirmada",
        evidencia_ref="resultado:turno:1", natureza_evidencia="fato_observado",
        responsabilidade="usuario", confianca=0.96,
        permite_expressao=True, emocao="brava", nivel=3,
        ts=time.time(),
    )
    estado.conversacional.update({
        "current_emotion": "brava", "emotion_level": 3,
        "episodio_emocional": evento,
    })
    falas = []

    class Memoria:
        def adicionar_interacao(self, *_args):
            pass

    runtime = RespostaConversacionalRuntime(
        namespace_getter=lambda: {
            "falar_com_lipsync": lambda *args: falas.append(args) or True,
            "_registrar_mente_curta": lambda *_args, **_kwargs: None,
            "memoria_inteligente": Memoria(),
            "salvar_memoria": lambda: None,
        },
        estado_runtime_getter=lambda: estado,
        fallback_fala="",
        log=lambda *_args: None,
    )

    assert runtime.emitir_resposta_curta("Oi", "Entendi.") is True
    assert falas == [("Entendi.", "brava", 3)]

    estado.conversacional["episodio_emocional"] = {}
    assert runtime.emitir_resposta_curta("Agora", "Tudo bem.") is True
    assert falas[-1] == ("Tudo bem.", "calma", 1)


def test_resposta_curta_nao_usa_tom_explicito_sem_causa_compartilhada() -> None:
    estado = _Estado()
    falas = []

    class Memoria:
        def adicionar_interacao(self, *_args):
            pass

    runtime = RespostaConversacionalRuntime(
        namespace_getter=lambda: {
            "falar_com_lipsync": lambda *args: falas.append(args) or True,
            "_registrar_mente_curta": lambda *_args, **_kwargs: None,
            "memoria_inteligente": Memoria(),
            "salvar_memoria": lambda: None,
        },
        estado_runtime_getter=lambda: estado,
        fallback_fala="",
        log=lambda *_args: None,
    )

    assert runtime.emitir_resposta_curta(
        "Você é incrível", "Obrigada!", emocao="envergonhada", nivel=2,
    )
    assert falas[-1] == ("Obrigada!", "calma", 1)
    visual = construir_estado_visual(
        conversa_get=lambda chave, padrao=None: estado.conversacional.get(chave, padrao),
        plano_get=lambda: {},
    )
    assert (visual["emotion"], visual["level"]) == falas[-1][1:]

    evento = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="redundância confirmada",
        evidencia_ref="resultado:turno:2", natureza_evidencia="fato_observado",
        responsabilidade="usuario", confianca=0.96,
        permite_expressao=True, emocao="brava", nivel=3,
        ts=time.time(),
    )
    estado.conversacional.update({
        "current_emotion": "brava", "emotion_level": 3,
        "episodio_emocional": evento,
    })
    assert runtime.emitir_resposta_curta(
        "Tudo bem", "Entendi.", emocao="envergonhada", nivel=2,
    )
    assert falas[-1] == ("Entendi.", "brava", 3)
    visual = construir_estado_visual(
        conversa_get=lambda chave, padrao=None: estado.conversacional.get(chave, padrao),
        plano_get=lambda: {},
    )
    assert (visual["emotion"], visual["level"]) == falas[-1][1:]
