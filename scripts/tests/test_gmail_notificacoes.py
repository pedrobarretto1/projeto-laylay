from __future__ import annotations

from pathlib import Path

from mente_laylay.integracao import gmail_mental as modulo_gmail
from mente_laylay.integracao.gmail_mental import GmailMental


class _EventoUmaRodada:
    def __init__(self) -> None:
        self.esperas = 0

    def is_set(self) -> bool:
        return False

    def wait(self, _timeout: float) -> bool:
        self.esperas += 1
        # Primeira espera é a inicialização; a segunda encerra após uma rodada.
        return self.esperas >= 2

    def set(self) -> None:
        return None


def _email(uid: str = "uid:9001") -> dict:
    return {
        "uid": uid,
        "remetente": "Pessoa",
        "assunto": "Mensagem nova",
        "prioritario": False,
        "silenciado": False,
        "possivel_golpe": False,
    }


def test_daemon_nao_marca_email_quando_aviso_nao_entrou_na_fila(tmp_path: Path) -> None:
    gmail = GmailMental(
        arquivo_estado=str(tmp_path / "gmail.json"),
        usuario="pessoa@example.com",
        app_password="senha-de-aplicativo",
        intervalo_s=15,
        stop_event=_EventoUmaRodada(),
        agendar_fala_proativa=lambda *_args, **_kwargs: False,
        log=lambda *_args: None,
    )
    gmail.buscar_nao_lidos = lambda: [_email()]  # type: ignore[method-assign]

    gmail.daemon()

    assert "uid:9001" not in gmail.ids_vistos


def test_daemon_marca_email_somente_depois_que_aviso_entra_na_fila(tmp_path: Path) -> None:
    gmail = GmailMental(
        arquivo_estado=str(tmp_path / "gmail.json"),
        usuario="pessoa@example.com",
        app_password="senha-de-aplicativo",
        intervalo_s=15,
        stop_event=_EventoUmaRodada(),
        agendar_fala_proativa=lambda *_args, **_kwargs: True,
        log=lambda *_args: None,
    )
    gmail.buscar_nao_lidos = lambda: [_email()]  # type: ignore[method-assign]

    gmail.daemon()

    assert "uid:9001" in gmail.ids_vistos


def test_busca_usa_uid_estavel_em_vez_de_numero_de_sequencia(
    tmp_path: Path, monkeypatch,
) -> None:
    chamadas: list[tuple] = []

    class _Conexao:
        def login(self, *_args):
            return "OK", []

        def select(self, *_args, **_kwargs):
            return "OK", []

        def uid(self, comando, *args):
            chamadas.append((comando, *args))
            if comando == "search":
                return "OK", [b"9001"]
            cabecalho = b"From: Pessoa <pessoa@example.com>\r\nSubject: Ola\r\n\r\n"
            return "OK", [(b"9001 (BODY[HEADER] {60}", cabecalho), b")"]

        def logout(self):
            return "BYE", []

    monkeypatch.setattr(modulo_gmail.imaplib, "IMAP4_SSL", lambda *_args: _Conexao())
    gmail = GmailMental(
        arquivo_estado=str(tmp_path / "gmail.json"),
        usuario="pessoa@example.com",
        app_password="senha-de-aplicativo",
    )

    emails = gmail.buscar_nao_lidos()

    assert emails[0]["uid"] == "uid:9001"
    assert chamadas[0][:2] == ("search", None)
    assert chamadas[1][0] == "fetch"


def test_daemon_explica_quando_credenciais_nao_estao_configuradas(tmp_path: Path) -> None:
    logs: list[str] = []
    gmail = GmailMental(
        arquivo_estado=str(tmp_path / "gmail.json"),
        stop_event=_EventoUmaRodada(),
        log=logs.append,
    )

    gmail.daemon()

    assert any("Monitor inativo" in linha for linha in logs)
    assert any("GMAIL_USER" in linha and "GMAIL_APP_PASSWORD" in linha for linha in logs)


def test_daemon_entrega_lote_a_central_e_marca_os_aceitos(tmp_path: Path) -> None:
    recebidos = []
    gmail = GmailMental(
        arquivo_estado=str(tmp_path / "gmail.json"),
        usuario="pessoa@example.com",
        app_password="senha-de-aplicativo",
        intervalo_s=15,
        stop_event=_EventoUmaRodada(),
        centralizar_notificacoes_cb=lambda emails: recebidos.extend(emails) or {"uid:9001"},
        log=lambda *_args: None,
    )
    gmail.buscar_nao_lidos = lambda: [_email()]  # type: ignore[method-assign]

    gmail.daemon()

    assert recebidos and recebidos[0]["uid"] == "uid:9001"
    assert "uid:9001" in gmail.ids_vistos
