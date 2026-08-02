"""P12: riscos de escrita, repetição, confirmação e cancelamento em arquivos."""

from __future__ import annotations

from pathlib import Path

from mente_laylay.arquivos import arquivos_sistema
from mente_laylay.arquivos.lixeira_laylay import ResultadoLixeira


def _autorizar(monkeypatch, raiz: Path) -> None:
    monkeypatch.setenv("LAYLAY_ARQUIVOS_RAIZES_PERMITIDAS", str(raiz))


def test_criar_pasta_e_repetir_e_idempotente(tmp_path, monkeypatch) -> None:
    _autorizar(monkeypatch, tmp_path)
    alvo = tmp_path / "projeto"

    assert arquivos_sistema.criar_pasta(str(alvo)) is True
    assert arquivos_sistema.criar_pasta(str(alvo)) is True
    assert alvo.is_dir()


def test_escrita_segura_nao_sobrescreve_sem_confirmacao(tmp_path, monkeypatch) -> None:
    _autorizar(monkeypatch, tmp_path)
    alvo = tmp_path / "nota.txt"
    primeiro = arquivos_sistema.escrever_arquivo_texto_seguro(str(alvo), "original")
    repetido = arquivos_sistema.escrever_arquivo_texto_seguro(str(alvo), "novo")

    assert primeiro["status"] == "arquivo_criado"
    assert primeiro["confirmado"] is True
    assert repetido["status"] == "arquivo_existente_requer_confirmacao"
    assert repetido["confirmado"] is False
    assert alvo.read_text(encoding="utf-8") == "original"


def test_sobrescrita_confirmada_e_atomica_e_revalidada(tmp_path, monkeypatch) -> None:
    _autorizar(monkeypatch, tmp_path)
    alvo = tmp_path / "nota.txt"
    alvo.write_text("antigo", encoding="utf-8")

    resultado = arquivos_sistema.escrever_arquivo_texto_seguro(
        str(alvo), "conteúdo confirmado", sobrescrever=True,
    )

    assert resultado["ok"] is True
    assert resultado["confirmado"] is True
    assert resultado["tamanho"] == len("conteúdo confirmado")
    assert alvo.read_text(encoding="utf-8") == "conteúdo confirmado"
    assert not list(tmp_path.glob("*.laylay.tmp"))


def test_mover_e_renomear_cobrem_sucesso_e_falha(tmp_path, monkeypatch) -> None:
    _autorizar(monkeypatch, tmp_path)
    origem = tmp_path / "origem.txt"
    destino = tmp_path / "destino.txt"
    origem.write_text("x", encoding="utf-8")

    assert arquivos_sistema.mover_arquivo(str(origem), str(destino)) is True
    assert arquivos_sistema.mover_arquivo(str(origem), str(destino)) is False
    assert arquivos_sistema.renomear_arquivo(str(destino), "final.txt") is True
    assert arquivos_sistema.renomear_arquivo(str(destino), "outro.txt") is False
    assert (tmp_path / "final.txt").is_file()


def test_exclusao_sem_confirmacao_nunca_aparece_como_sucesso(tmp_path, monkeypatch) -> None:
    _autorizar(monkeypatch, tmp_path)
    alvo = tmp_path / "sensivel.txt"
    alvo.write_text("não apagar", encoding="utf-8")
    monkeypatch.setattr(
        arquivos_sistema,
        "mover_para_lixeira",
        lambda caminho: ResultadoLixeira(
            "aguardando_confirmacao", False, caminho, requer_confirmacao=True,
        ),
    )

    assert arquivos_sistema.deletar_item(str(alvo)) is False
    assert alvo.exists()


def test_exclusao_distingue_falha_real_de_confirmacao(tmp_path, monkeypatch) -> None:
    _autorizar(monkeypatch, tmp_path)
    alvo = tmp_path / "item.txt"
    alvo.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        arquivos_sistema,
        "mover_para_lixeira",
        lambda caminho: ResultadoLixeira("falha_execucao", False, caminho),
    )
    assert arquivos_sistema.deletar_item(str(alvo)) is False

    monkeypatch.setattr(
        arquivos_sistema,
        "mover_para_lixeira",
        lambda caminho: ResultadoLixeira("movido_para_lixeira", True, caminho),
    )
    assert arquivos_sistema.deletar_item(str(alvo)) is True


def test_busca_exata_respeita_limite_e_rejeita_caminho(tmp_path, monkeypatch) -> None:
    _autorizar(monkeypatch, tmp_path)
    downloads = tmp_path / "Downloads"
    (downloads / "um").mkdir(parents=True)
    (downloads / "dois").mkdir(parents=True)
    (downloads / "um" / "alvo.txt").write_text("1", encoding="utf-8")
    (downloads / "dois" / "alvo.txt").write_text("2", encoding="utf-8")
    monkeypatch.setattr(arquivos_sistema.os.path, "expanduser", lambda _valor: str(tmp_path))

    encontrados = arquivos_sistema.buscar_itens_com_nome("alvo.txt", limite=2)

    assert len(encontrados) == 2
    assert arquivos_sistema.buscar_itens_com_nome("um/alvo.txt") == []

