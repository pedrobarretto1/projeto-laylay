from pathlib import Path

import numpy as np

from mente_laylay.percepcao.treino_voz_pessoal import (
    DatasetVozPessoal,
    distancia_edicao_palavras,
    frases_pendentes,
    normalizar_transcricao,
)


class SoundFileFalso:
    def __init__(self):
        self.chamadas = []

    def write(self, caminho, audio, taxa, subtype):
        self.chamadas.append((caminho, len(audio), taxa, subtype))
        Path(caminho).write_bytes(b"RIFF-falso")


def test_normalizacao_e_wer_aceitam_pontuacao_e_acentos():
    assert normalizar_transcricao("Láylay, liga a LUZ!") == "laylay liga a luz"
    assert distancia_edicao_palavras("Laylay, liga a luz", "Laylay liga luz") == (1, 4)


def test_dataset_salva_audio_rotulo_e_separa_quinta_amostra_para_teste(tmp_path):
    dataset = DatasetVozPessoal(tmp_path / "voz")
    sf = SoundFileFalso()
    for _ in range(5):
        dataset.salvar(np.ones(1600, dtype=np.float32), 16000, "Laylay, liga a luz.", soundfile_mod=sf)

    registros = dataset.registros()
    assert len(registros) == 5
    assert registros[-1]["repeticao"] == 5
    assert registros[-1]["divisao"] == "teste"
    assert all((dataset.raiz / item["audio"]).exists() for item in registros)


def test_coleta_pode_retomar_somente_frases_pendentes(tmp_path):
    dataset = DatasetVozPessoal(tmp_path / "voz")
    sf = SoundFileFalso()
    dataset.salvar(np.ones(800, dtype=np.float32), 16000, "Frase um", soundfile_mod=sf)

    pendentes = frases_pendentes(dataset, ["Frase um", "Frase dois"], 2)

    assert pendentes.count("Frase um") == 1
    assert pendentes.count("Frase dois") == 2
