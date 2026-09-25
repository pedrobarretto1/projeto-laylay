"""A sonda NLI não pode trocar a semântica ou a ordem de classes."""

from scripts.analises.sonda_nli_onnx import ROTULO_LOCAL


def test_tres_classes_de_nli_tem_interpretacao_explicita() -> None:
    assert ROTULO_LOCAL == {
        "entailment": "sustentada",
        "neutral": "sem_prova",
        "contradiction": "contradita",
    }
