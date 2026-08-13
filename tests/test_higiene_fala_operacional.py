from mente_laylay.personalidade.higiene_fala import (
    limpar_fala_operacional,
    limpar_titulo_musical_para_fala,
    nome_janela_para_fala,
)


def test_titulo_musical_real_perde_contador_editorial_e_navegador() -> None:
    titulo = (
        "1043 patrick jane pegou o telefone dela- o mentalista edit pros "
        "bandido edit mentalist - youtube - opera"
    )

    assert limpar_titulo_musical_para_fala(titulo) == (
        "patrick jane pegou o telefone dela - o mentalista"
    )


def test_titulo_musical_preserva_nome_legitimo_com_um_edit() -> None:
    assert limpar_titulo_musical_para_fala("Somebody Else (Radio Edit) - YouTube") == (
        "Somebody Else (Radio Edit)"
    )
    assert limpar_titulo_musical_para_fala("1979 - The Smashing Pumpkins") == (
        "1979 - The Smashing Pumpkins"
    )


def test_nomes_de_janelas_sao_apresentados_sem_cromos_tecnicos() -> None:
    assert nome_janela_para_fala("Música longa - YouTube - Opera") == "YouTube"
    assert nome_janela_para_fala("laylay.py - projeto lay - Visual Studio Code") == "VS Code"
    assert nome_janela_para_fala("Bloco de Notas") == "Bloco de Notas"


def test_higiene_operacional_remove_residuo_sem_resumir_a_informacao() -> None:
    assert limpar_fala_operacional("  Abri o Opera  ,  mas não troquei sua tela.  ") == (
        "Abri o Opera, mas não troquei sua tela."
    )
