from __future__ import annotations

from types import SimpleNamespace

import pytest

from mente_laylay.autonomia import comandos_sistema


def _isolar_abertura(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(comandos_sistema, "resolver_jogo_steam", lambda _nome: None)
    monkeypatch.setattr(comandos_sistema, "buscar_executavel", lambda _nome: None)
    monkeypatch.setattr(comandos_sistema, "APP_OPENER_AVAILABLE", False)
    monkeypatch.setattr(comandos_sistema, "open_app", None)


def _isolar_fechamento(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(comandos_sistema, "gw", None)
    monkeypatch.setattr(comandos_sistema, "APP_OPENER_AVAILABLE", False)
    monkeypatch.setattr(comandos_sistema, "close_app", None)


def test_normalizar_nome_app_remove_extensao_acentos_e_espacos() -> None:
    assert comandos_sistema.normalizar_nome_app('  "Ópera   GX.exe"  ') == "opera gx"
    assert comandos_sistema.normalizar_nome_app("") == ""


def test_abrir_uri_rejeita_alvo_sem_protocolo() -> None:
    assert comandos_sistema.abrir_uri_sistema("www.example.com") is False


def test_abrir_uri_usa_shell_do_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    chamadas: list[str] = []

    class _Shell32:
        @staticmethod
        def ShellExecuteW(_hwnd, _verbo, alvo, _params, _dir, _show):
            chamadas.append(alvo)
            return 33

    monkeypatch.setattr(
        comandos_sistema,
        "ctypes",
        SimpleNamespace(windll=SimpleNamespace(shell32=_Shell32())),
    )

    assert comandos_sistema.abrir_uri_sistema("steam://rungameid/123") is True
    assert chamadas == ["steam://rungameid/123"]


def test_abrir_uri_faz_fallback_e_reporta_recusa(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(comandos_sistema, "ctypes", SimpleNamespace())
    abertos: list[str] = []
    monkeypatch.setattr(
        comandos_sistema.os,
        "startfile",
        lambda alvo: abertos.append(alvo),
        raising=False,
    )
    assert comandos_sistema.abrir_uri_sistema("ms-windows-store:") is True
    assert abertos == ["ms-windows-store:"]

    monkeypatch.setattr(
        comandos_sistema.os,
        "startfile",
        lambda _alvo: (_ for _ in ()).throw(OSError("recusado")),
        raising=False,
    )
    assert comandos_sistema.abrir_uri_sistema("ms-windows-store:") is False


def test_buscar_executavel_prioriza_path(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    executavel = tmp_path / "opera.exe"
    executavel.write_bytes(b"")
    monkeypatch.setattr(comandos_sistema.shutil, "which", lambda nome: str(executavel) if nome == "opera" else None)

    assert comandos_sistema.buscar_executavel("Opera") == str(executavel)


def test_buscar_executavel_varre_raiz_fornecida(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    executavel = tmp_path / "Ferramentas" / "Meu App.exe"
    executavel.parent.mkdir()
    executavel.write_bytes(b"")
    monkeypatch.setattr(comandos_sistema.shutil, "which", lambda _nome: None)

    assert comandos_sistema.buscar_executavel("meu app", roots=[tmp_path]) == str(executavel)


def test_abrir_programa_entrega_store_ao_shell_e_fala(monkeypatch: pytest.MonkeyPatch) -> None:
    falas: list[tuple[str, str, int]] = []
    monkeypatch.setattr(comandos_sistema, "abrir_uri_sistema", lambda uri: uri == "ms-windows-store:")

    assert comandos_sistema.abrir_programa("loja", lambda *args: falas.append(args)) is True
    assert falas == [("Abrindo loja.", "calma", 1)]


def test_abrir_programa_resolve_jogo_steam(monkeypatch: pytest.MonkeyPatch) -> None:
    uris: list[str] = []
    monkeypatch.setattr(
        comandos_sistema,
        "resolver_jogo_steam",
        lambda _nome: {"appid": "2694490", "nome": "Path of Exile 2", "confianca": 1.0},
    )
    monkeypatch.setattr(comandos_sistema, "abrir_uri_sistema", lambda uri: uris.append(uri) or True)

    assert comandos_sistema.abrir_programa("path of exile 2") is True
    assert uris == ["steam://rungameid/2694490"]


def test_abrir_programa_usa_caminho_direto_ou_appopener(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _isolar_abertura(monkeypatch)
    executavel = tmp_path / "utilitario.exe"
    executavel.write_bytes(b"")
    abertos: list[str] = []
    monkeypatch.setattr(comandos_sistema.os, "startfile", lambda alvo: abertos.append(str(alvo)), raising=False)

    assert comandos_sistema.abrir_programa(str(executavel)) is True
    assert abertos == [str(executavel)]

    monkeypatch.setattr(comandos_sistema, "APP_OPENER_AVAILABLE", True)
    monkeypatch.setattr(comandos_sistema, "open_app", lambda nome, match_closest: nome)
    assert comandos_sistema.abrir_programa("Aplicativo Inventado") is True


def test_abrir_programa_inexistente_falha_sem_falso_sucesso(monkeypatch: pytest.MonkeyPatch) -> None:
    _isolar_abertura(monkeypatch)

    with pytest.raises(Exception, match="Não consegui encontrar"):
        comandos_sistema.abrir_programa("programa plutao azul")


def test_fechar_programa_bloqueia_processos_perigosos(monkeypatch: pytest.MonkeyPatch) -> None:
    _isolar_fechamento(monkeypatch)
    monkeypatch.setattr(comandos_sistema.psutil, "process_iter", lambda _campos: [])

    with pytest.raises(Exception, match="processo protegido"):
        comandos_sistema.fechar_programa("python")
    with pytest.raises(Exception, match="close_tab"):
        comandos_sistema.fechar_programa("chrome")


def test_fechar_programa_mata_processo_exato_e_confirma(monkeypatch: pytest.MonkeyPatch) -> None:
    _isolar_fechamento(monkeypatch)
    mortos: list[int] = []
    falas: list[tuple[str, str, int]] = []

    class _Processo:
        info = {"name": "opera.exe", "pid": 321}
        pid = 321

        @staticmethod
        def name() -> str:
            return "opera.exe"

        def kill(self) -> None:
            mortos.append(self.info["pid"])

    monkeypatch.setattr(comandos_sistema.psutil, "process_iter", lambda _campos: [_Processo()])

    assert comandos_sistema.fechar_programa("opera", lambda *args: falas.append(args)) is True
    assert mortos == [321]
    assert falas == [("Pronto, opera foi fechado.", "debochada", 2)]


def test_fechar_programa_inexistente_falha_sem_falso_sucesso(monkeypatch: pytest.MonkeyPatch) -> None:
    _isolar_fechamento(monkeypatch)
    monkeypatch.setattr(comandos_sistema.psutil, "process_iter", lambda _campos: [])

    with pytest.raises(Exception, match="Não há nenhum programa aberto"):
        comandos_sistema.fechar_programa("programa plutao azul")
