from mente_laylay.emocoes.perfil_emocional import modular_audio_params


def test_voz_calma_nao_envelhece_a_francisca() -> None:
    assert modular_audio_params("calma", 1) == ("+1%", "+5Hz", "-1%")


def test_voz_neutra_mantem_perfil_leve() -> None:
    assert modular_audio_params("neutra", 1) == ("+1%", "+5Hz", "+0%")


def test_emocoes_continuam_a_ter_prosodias_distintas() -> None:
    alegre = modular_audio_params("alegre", 2)
    envergonhada = modular_audio_params("envergonhada", 2)
    triste = modular_audio_params("triste", 2)

    assert alegre != envergonhada != triste
    assert alegre[0].startswith("+")
    assert envergonhada[0].startswith("-")
    assert triste[0].startswith("-")
