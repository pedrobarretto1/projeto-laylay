from mente_laylay.percepcao.janelas_sistema import classificar_assunto


def test_classifica_atividades_de_foco_para_presenca_contextual() -> None:
    assert classificar_assunto("Code.exe", "laylay.py - Visual Studio Code") == "Programação"
    assert classificar_assunto("chrome.exe", "Curso de Python - Udemy") == "Estudo"
    assert classificar_assunto("EXCEL.EXE", "Planejamento.xlsx") == "Trabalho"


def test_nao_chama_navegacao_comum_de_estudo_ou_trabalho() -> None:
    assert classificar_assunto("chrome.exe", "Página inicial") == ""
