import numpy as np

from mente_laylay.percepcao.reconhecedor_voz_pessoal import (
    distancia_dtw,
    extrair_caracteristicas,
    extrair_comando_rotulado,
)


def test_extrai_rotulo_sem_variacao_da_palavra_de_ativacao():
    assert extrair_comando_rotulado("Laylay, liga a luz.") == "liga a luz"
    assert extrair_comando_rotulado("Lelei, liga a luz.") == "liga a luz"


def test_caracteristicas_acusticas_sao_finitas_e_comparaveis():
    tempo = np.arange(32000, dtype=np.float32) / 16000
    audio = np.sin(2 * np.pi * 220 * tempo).astype(np.float32) * 0.1
    caracteristicas = extrair_caracteristicas(audio, 16000, numpy_mod=np)

    assert caracteristicas.ndim == 2
    assert caracteristicas.shape[1] == 26
    assert np.isfinite(caracteristicas).all()
    assert distancia_dtw(caracteristicas, caracteristicas, numpy_mod=np) < 0.001
