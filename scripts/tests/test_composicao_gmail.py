from __future__ import annotations

from mente_laylay.integracao.composicao_gmail import ComposicaoGmailLaylayRuntime


class _GmailFake:
    def __init__(self):
        self.nao_lidos_cache = [{"uid": "1"}]
        self.silenciados = []
        self.encerrado = False

    def silenciar_remetente(self, remetente):
        self.silenciados.append(remetente)
        return True

    def configurado(self):
        return True

    def buscar_nao_lidos(self):
        return list(self.nao_lidos_cache)

    def falar_resumo_estiloso(self, emails, **kwargs):
        return emails, kwargs

    def daemon(self):
        return None

    def encerrar(self):
        self.encerrado = True


def _dependencias(tmp_path):
    return {
        "arquivo_estado": str(tmp_path / "gmail.json"),
        "continuidades_set": lambda *_: None,
        "agendar_fala_proativa": lambda *_: None,
        "is_speaking_getter": lambda: False,
        "modo_jogo_getter": lambda: False,
        "stop_event": object(),
    }


def test_composicao_gmail_monta_configuracao_e_preserva_api(tmp_path) -> None:
    capturado = {}
    gmail = _GmailFake()
    ambiente = {
        "GMAIL_USER": " pedro@example.com ",
        "GMAIL_APP_PASSWORD": " senha-secreta ",
        "GMAIL_INTERVALO_S": "120",
        "GMAIL_MAX_LIDOS": "7",
    }

    def factory(**kwargs):
        capturado.update(kwargs)
        return gmail

    runtime = ComposicaoGmailLaylayRuntime(
        **_dependencias(tmp_path),
        env_getter=lambda nome, padrao="": ambiente.get(nome, padrao),
        gmail_factory=factory,
        log=lambda *_: None,
    )

    assert capturado["usuario"] == "pedro@example.com"
    assert capturado["app_password"] == "senha-secreta"
    assert capturado["intervalo_s"] == 120
    assert capturado["max_lidos"] == 7
    assert runtime.nao_lidos_cache == [{"uid": "1"}]
    assert runtime.configurado() is True
    assert runtime.silenciar_remetente("spam@example.com") is True
    assert runtime.buscar_nao_lidos() == [{"uid": "1"}]
    runtime.encerrar()
    assert gmail.encerrado is True


def test_composicao_gmail_corrige_numeros_invalidos_sem_expor_credenciais(tmp_path) -> None:
    falhas, logs, capturado = [], [], {}
    ambiente = {
        "GMAIL_USER": "privado@example.com",
        "GMAIL_APP_PASSWORD": "segredo-total",
        "GMAIL_INTERVALO_S": "agora",
        "GMAIL_MAX_LIDOS": "9999",
    }

    def factory(**kwargs):
        capturado.update(kwargs)
        return _GmailFake()

    ComposicaoGmailLaylayRuntime(
        **_dependencias(tmp_path),
        env_getter=lambda nome, padrao="": ambiente.get(nome, padrao),
        gmail_factory=factory,
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
        log=logs.append,
    )

    assert capturado["intervalo_s"] == 300
    assert capturado["max_lidos"] == 5
    assert len(falhas) == 2
    serializado = repr(logs).casefold()
    assert "privado@example.com" not in serializado
    assert "segredo-total" not in serializado
