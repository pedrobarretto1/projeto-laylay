"""Guardas da sonda; nenhum teste desta suíte abre ou move janelas."""
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_execucao_contextual_windows as sonda


def proibido(*_args, **_kwargs):
    raise AssertionError("Uma guarda falhou: acesso a efeito/subprocesso indevido.")


def test_sem_opt_in_nao_consulta_sessao_nem_executa(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", ["sonda", "--saida", str(tmp_path / "resultado.json")])
    monkeypatch.setattr(sonda, "verificar_sessao", proibido)
    with pytest.raises(SystemExit) as erro:
        sonda.main()
    assert erro.value.code == 2


def test_artefato_existente_nao_e_sobrescrito_nem_inicia_efeito(monkeypatch, tmp_path):
    destino = tmp_path / "existente.json"
    destino.touch()
    monkeypatch.setattr("sys.argv", ["sonda", "--executar-windows", "--saida", str(destino)])
    monkeypatch.setattr(sonda, "verificar_sessao", proibido)
    with pytest.raises(SystemExit) as erro:
        sonda.main()
    assert erro.value.code == 2 and destino.stat().st_size == 0


def test_calculadora_preexistente_nao_inicia_subprocesso(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", ["sonda", "--executar-windows", "--saida", str(tmp_path / "novo.json")])
    monkeypatch.setattr(sonda, "verificar_sessao", lambda: None)
    monkeypatch.setattr(sonda, "observar_calculadora", lambda: [{"hwnd": 123}])
    monkeypatch.setattr(sonda.subprocess, "run", proibido)
    with pytest.raises(SystemExit) as erro:
        sonda.main()
    assert erro.value.code == 2
    assert not (tmp_path / "novo.json").exists()


@pytest.mark.parametrize("nome,argumentos", [
    ("python.exe", ["python.exe", r"C:\projeto\laylay.py"]),
    ("pythonw.exe", ["pythonw.exe", "-u", r"C:\projeto\laylay.py"]),
])
def test_sessao_laylay_ativa_bloqueia_sem_interromper_processo(monkeypatch, nome, argumentos):
    import psutil
    processo = SimpleNamespace(info={"name": nome, "cmdline": argumentos})
    monkeypatch.setattr(psutil, "process_iter", lambda *_: [processo])
    with pytest.raises(RuntimeError, match="Laylay aberta"):
        sonda.verificar_sessao()


def test_python_de_outro_projeto_nao_e_sessao_laylay(monkeypatch):
    import psutil
    processo = SimpleNamespace(info={"name": "python.exe", "cmdline": ["python.exe", "server.py"]})
    monkeypatch.setattr(psutil, "process_iter", lambda *_: [processo])
    sonda.verificar_sessao()


@pytest.mark.parametrize("caminho,lado", [("ignorar_guardas", "esquerda"), ("entrada", "todas")])
def test_escopo_invalido_recusa_antes_de_iniciar_instalacao(monkeypatch, tmp_path, caminho, lado):
    monkeypatch.setattr(sonda, "verificar_sessao", proibido)
    with pytest.raises(ValueError, match="fora do escopo"):
        sonda.coletar_instalado(tmp_path, caminho=caminho, lado=lado)


def test_repeticao_sem_alternancia_recusa_antes_de_efeitos(monkeypatch, tmp_path):
    monkeypatch.setattr(sonda, "verificar_sessao", proibido)
    with pytest.raises(ValueError, match="Repetição exige"):
        sonda.coletar_instalado(tmp_path, repetir_primeiro_lado=True)
    monkeypatch.setattr("sys.argv", ["sonda", "--executar-windows", "--repetir-primeiro-lado",
        "--saida", str(tmp_path / "novo.json")])
    with pytest.raises(SystemExit) as erro:
        sonda.main()
    assert erro.value.code == 2


@pytest.mark.parametrize("autoria", ["ignorar", "real", "controlada"])
def test_autoria_fora_do_principal_nao_inicia_efeitos(monkeypatch, tmp_path, autoria):
    monkeypatch.setattr(sonda, "verificar_sessao", proibido)
    with pytest.raises(ValueError, match="Autoria fora do escopo"):
        sonda.coletar_instalado(tmp_path, autoria=autoria)


def test_selecao_real_invalida_aborta_cli_antes_da_sessao(monkeypatch, tmp_path):
    monkeypatch.setattr(sonda, "verificar_sessao", proibido)
    from scripts.analises import sonda_escopo_geracao_real as real
    def recusar(): raise RuntimeError("seleção inválida")
    monkeypatch.setattr(real, "selecao_local", recusar)
    monkeypatch.setattr("sys.argv", ["sonda", "--executar-windows", "--caminho", "principal",
        "--autoria", "real", "--saida", str(tmp_path / "novo.json")])
    with pytest.raises(RuntimeError, match="seleção inválida"):
        sonda.main()
