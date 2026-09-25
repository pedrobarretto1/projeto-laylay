from __future__ import annotations

from mente_laylay.neural.experiencias import BufferExperienciasNeurais
from mente_laylay.neural.runtime import EspecialistaNeuralComandosRuntime


class _Modelo:
    versao = "teste-executavel"
    sha256 = "a" * 64

    def __init__(self, *, negated: bool, ood: bool = False) -> None:
        self.negated = negated
        self.ood = ood

    def prever(self, _texto: str) -> dict:
        return {
            "intent": "VOLUME",
            "gate_intent": "VOLUME",
            "params": {"acao": "down"},
            "is_command": True,
            "command_probability": 0.87,
            "command_head_variant": "modalidade_v4_sparse_v1",
            "intent_head_variant": "legado",
            "negated": self.negated,
            "ood": self.ood,
            "ood_calibrated": True,
            "confidence": {
                "intent": 0.99,
                "command": 0.99,
                "negation": 0.99,
                "action": 0.99,
            },
        }


def _runtime(tmp_path, *, negated: bool, ood: bool = False):
    return EspecialistaNeuralComandosRuntime(
        modelo=_Modelo(negated=negated, ood=ood),
        buffer=BufferExperienciasNeurais(tmp_path / "experiencias.jsonl"),
        publicar=None,
        modo="shadow",
        intents_permitidas={"VOLUME"},
        log=lambda *_args: None,
    )


def test_negacao_neural_nao_vira_divergencia_de_execucao(tmp_path):
    runtime = _runtime(tmp_path, negated=True)
    previsao = runtime.observar(
        "não abaixa o volume",
        turno_legado={"modalidade": "recusa", "autoriza_execucao": False},
    )

    assert previsao["is_command"] is True
    assert previsao["negated"] is True
    assert previsao["comparacao_legado"]["comando_neural_executavel"] is False
    assert previsao["comparacao_legado"]["divergiu_comando"] is False


def test_comando_neural_executavel_ainda_diverge_de_turno_nao_autorizado(tmp_path):
    runtime = _runtime(tmp_path, negated=False)
    previsao = runtime.observar(
        "abaixa o volume",
        turno_legado={"modalidade": "conversa", "autoriza_execucao": False},
    )

    assert previsao["comparacao_legado"]["comando_neural_executavel"] is True
    assert previsao["comparacao_legado"]["divergiu_comando"] is True


def test_ood_calibrado_nao_conta_como_comando_executavel(tmp_path):
    runtime = _runtime(tmp_path, negated=False, ood=True)
    previsao = runtime.observar(
        "abaixa o volume",
        turno_legado={"modalidade": "conversa", "autoriza_execucao": False},
    )

    assert previsao["comparacao_legado"]["comando_neural_executavel"] is False
    assert previsao["comparacao_legado"]["divergiu_comando"] is False


def test_runtime_preserva_telemetria_do_artefato_e_do_head(tmp_path):
    runtime = _runtime(tmp_path, negated=False)
    previsao = runtime.observar(
        "abaixa o volume",
        turno_legado={"modalidade": "comando", "autoriza_execucao": True},
    )

    assert previsao["model_sha256"] == "a" * 64
    assert previsao["gate_intent"] == "VOLUME"
    assert previsao["command_probability"] == 0.87
    assert previsao["command_head_variant"] == "modalidade_v4_sparse_v1"
    assert previsao["intent_head_variant"] == "legado"
