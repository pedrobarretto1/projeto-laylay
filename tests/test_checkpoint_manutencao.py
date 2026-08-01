from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from scripts.gerar_checkpoint_manutencao import (
    caminho_parece_sensivel,
    coletar_inventario_python,
    criar_checkpoint,
)


def test_classificacao_sensivel_preserva_exemplos_publicos() -> None:
    assert caminho_parece_sensivel("memoria/conversa.json") is True
    assert caminho_parece_sensivel("dados/voz_pessoal/amostra.wav") is True
    assert caminho_parece_sensivel("devices.json") is True
    assert caminho_parece_sensivel("config/credentials-google.json") is True
    assert caminho_parece_sensivel(".env.example") is False
    assert caminho_parece_sensivel("dados/devices.example.json") is False
    assert caminho_parece_sensivel("tests/test_memoria.py") is False


def test_inventario_ignora_ambientes_build_e_cache(tmp_path: Path) -> None:
    (tmp_path / "mente_laylay").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / ".venv314").mkdir()
    (tmp_path / "build").mkdir()
    (tmp_path / "mente_laylay" / "habilidade.py").write_text(
        "linha_1\nlinha_2\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "test_habilidade.py").write_text(
        "def test_ok():\n    assert True\n", encoding="utf-8"
    )
    (tmp_path / ".venv314" / "dependencia.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "build" / "gerado.py").write_text("x = 1\n", encoding="utf-8")

    inventario = coletar_inventario_python(tmp_path)

    assert inventario["arquivos_python"] == 2
    assert inventario["arquivos_producao"] == 1
    assert inventario["arquivos_testes"] == 1
    assert inventario["linhas_python"] == 4


def test_checkpoint_nao_le_conteudo_pessoal_e_detecta_nome_versionado(
    tmp_path: Path,
) -> None:
    (tmp_path / "mente_laylay").mkdir()
    (tmp_path / "mente_laylay" / "modulo.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
    (tmp_path / ".gitattributes").write_text("*.py text eol=lf\n", encoding="utf-8")
    saidas = {
        ("rev-parse", "--short", "HEAD"): "abc123\n",
        ("branch", "--show-current"): "main\n",
        ("status", "--porcelain=v1", "-z"): " M modulo.py\0",
        ("ls-files", "-z"): "mente_laylay/modulo.py\0memoria/pessoal.json\0",
    }

    checkpoint = criar_checkpoint(
        tmp_path,
        executor_git=lambda argumentos: saidas[tuple(argumentos)],
        agora=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )

    assert checkpoint["schema"] == 1
    assert checkpoint["gerado_em_utc"] == "2026-08-01T00:00:00+00:00"
    assert checkpoint["git"]["commit"] == "abc123"
    assert checkpoint["git"]["entradas_alteradas"] == 1
    assert checkpoint["git"]["arquivos_sensiveis_versionados"] == [
        "memoria/pessoal.json"
    ]
    assert checkpoint["privacidade"] == {
        "conteudo_pessoal_lido": False,
        "seguro_para_compartilhar": True,
    }
