from pathlib import Path

from cliente.iniciar_laylay import comando_inicializacao


def test_launcher_abre_laylay_no_cmd_sem_concatenar_comando(tmp_path, monkeypatch):
    monkeypatch.setenv("COMSPEC", r"C:\Windows\System32\cmd.exe")

    executavel, comando = comando_inicializacao(tmp_path)

    esperado = str(Path(tmp_path).resolve() / "Laylay.exe")
    assert executavel == esperado
    assert comando == [r"C:\Windows\System32\cmd.exe", "/d", "/k", esperado]
