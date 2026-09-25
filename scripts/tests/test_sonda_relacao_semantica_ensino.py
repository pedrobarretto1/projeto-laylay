"""A sonda semântica mede ranking; nunca concede suporte factual."""

import numpy as np
import pytest

from scripts.analises.sonda_relacao_semantica_ensino import (
    CONTRASTES,
    conferir_ligacao_ao_artefato,
    medir_contrastes,
    priorizar_pendencias,
)
from scripts.analises.sonda_fala_integral_real import carregar_caso
from scripts.analises.sonda_selecao_evidencias_ensino import selecionar_unidades


class _EncoderControlado:
    def codificar(self, textos: list[str]) -> np.ndarray:
        vetores = []
        for indice in range(len(textos)):
            vetores.append((1.0, 0.0) if indice % 3 != 2 else (0.0, 1.0))
        return np.asarray(vetores, dtype=np.float32)


def test_contrastes_historicos_ainda_apontam_para_fonte_congelada() -> None:
    assert conferir_ligacao_ao_artefato()
    assert len(CONTRASTES) == 4


def test_ranking_nao_vira_autorizacao_de_fala() -> None:
    resultado = medir_contrastes(_EncoderControlado())
    assert resultado["ordens_corretas"] == len(CONTRASTES)
    assert resultado["uso"] == "somente_recuperacao_para_revisao"
    assert resultado["aprovado_para_compor"] is False
    assert resultado["aprovado_para_producao"] is False


def test_encoder_com_vetores_faltando_falha_fechado() -> None:
    class _EncoderIncompleto:
        def codificar(self, textos: list[str]) -> np.ndarray:
            return np.zeros((len(textos) - 1, 2), dtype=np.float32)

    with pytest.raises(ValueError, match="um vetor por texto"):
        medir_contrastes(_EncoderIncompleto())


def test_exemplo_real_perdido_pelo_lexico_vai_apenas_para_revisao() -> None:
    caso = carregar_caso("luz")
    selecao = selecionar_unidades(caso["fontes_metadados"], caso["tema"], caso["pedido"])
    sugestoes = priorizar_pendencias(caso["tema"], selecao["pendencias"], _EncoderControlado())
    assert [item["fonte_id"] for item in sugestoes] == ["F3"]
    assert sugestoes[0]["estado"] == "revisao_semantica_pendente"
    assert sugestoes[0]["aprovado_para_compor"] is False
    assert all(item["fonte_id"] != "F3" for item in selecao["unidades"])
