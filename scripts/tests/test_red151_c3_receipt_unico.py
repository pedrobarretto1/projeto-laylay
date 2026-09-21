from __future__ import annotations

import time

from mente_laylay.autonomia.fluxos_conversa import handle_feedback_pendente


URL = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
TITULO = "Faixa Receipt"
CANAL = "Canal Receipt"


class MusicaSucesso:
    def __init__(self):
        self.chamadas = []

    def faixa_atual(self):
        return {
            "url": URL,
            "title": TITULO,
            "canal": CANAL,
        }

    def criar_playlist(self, nome):
        self.chamadas.append(("create", nome))
        return {
            "ok": True,
            "criada": True,
            "status": "playlist_criada",
            "nome": nome,
        }

    def adicionar_faixa(self, nome, url, titulo, canal):
        self.chamadas.append(("add", nome, url, titulo, canal))
        return True

    def definir_ultima_playlist(self, nome):
        self.chamadas.append(("ultima", nome))


class MusicaFalhaCriacao:
    def __init__(self):
        self.chamadas = []

    def faixa_atual(self):
        return {
            "url": URL,
            "title": TITULO,
            "canal": CANAL,
        }

    def criar_playlist(self, nome):
        self.chamadas.append(("create", nome))
        return {
            "ok": False,
            "criada": False,
            "status": "falha_persistencia",
            "nome": nome,
        }

    def adicionar_faixa(self, *args):
        self.chamadas.append(("add", *args))
        return True

    def definir_ultima_playlist(self, nome):
        self.chamadas.append(("ultima", nome))


class MusicaFalhaAdd:
    def __init__(self):
        self.chamadas = []

    def faixa_atual(self):
        return {
            "url": URL,
            "title": TITULO,
            "canal": CANAL,
        }

    def criar_playlist(self, nome):
        self.chamadas.append(("create", nome))
        return {
            "ok": True,
            "criada": True,
            "status": "playlist_criada",
            "nome": nome,
        }

    def adicionar_faixa(self, nome, url, titulo, canal):
        self.chamadas.append(("add", nome, url, titulo, canal))
        return False

    def definir_ultima_playlist(self, nome):
        self.chamadas.append(("ultima", nome))


def _executar(musica):
    falas = []
    receipts = []

    def registrar(*args, **kwargs):
        receipts.append({
            "args": args,
            "kwargs": kwargs,
        })

    contexto = {
        "_playlist_sugestao_pendente": {
            "playlist": "vmz",
            "ts": time.time(),
        },
        "_rotina_sugestao_pendente": None,
        "_email_sugestao_pendente": None,
        "_registro_musica_operacoes_runtime": musica,
        "_classificar_confirmacao_local": lambda _texto: True,
        "_classificar_confirmacao_contextual": lambda *_args: True,
        "_yt_clean_title": lambda valor: valor,
        "_registrar_resultado_execucao": registrar,
        "falar_com_lipsync": (
            lambda texto, *_args, **_kwargs:
            falas.append(str(texto))
        ),
    }

    tratado = handle_feedback_pendente(contexto, "sim")

    return tratado, falas, receipts, musica.chamadas, contexto


def _receipt_payload(registro):
    args = registro["args"]
    assert args, "registrar_resultado_execucao foi chamado sem payload."
    assert isinstance(args[0], dict)
    return args[0]


def test_red151_c3_sucesso_publica_exatamente_um_receipt():
    tratado, falas, receipts, chamadas, contexto = _executar(
        MusicaSucesso()
    )

    assert tratado is True
    assert chamadas[:2] == [
        ("create", "vmz"),
        ("add", "vmz", URL, TITULO, CANAL),
    ]
    assert ("ultima", "vmz") in chamadas
    assert len(falas) == 1
    assert contexto["_playlist_sugestao_pendente"] is None

    assert len(receipts) == 1, (
        "RED151-C3: uma única confirmação bem-sucedida publicou "
        f"{len(receipts)} receipts. Esperado: exatamente 1. "
        f"Receipts: {receipts!r}"
    )

    payload = _receipt_payload(receipts[0])

    assert payload.get("intent") == "PLAYLIST_ADD"
    assert payload.get("alvo") == "vmz"
    assert payload.get("ok") is True
    assert payload.get("confirmado") is True


def test_red151_c3_falha_create_publica_um_receipt_e_nao_add():
    tratado, falas, receipts, chamadas, contexto = _executar(
        MusicaFalhaCriacao()
    )

    assert tratado is True
    assert chamadas == [("create", "vmz")]
    assert len(falas) == 1
    assert contexto["_playlist_sugestao_pendente"] is None

    assert len(receipts) == 1

    payload = _receipt_payload(receipts[0])

    assert payload.get("intent") == "PLAYLIST_ADD"
    assert payload.get("alvo") == "vmz"
    assert payload.get("ok") is False
    assert payload.get("executou") is False
    assert payload.get("confirmado") is False


def test_red151_c3_falha_add_publica_exatamente_um_receipt():
    tratado, falas, receipts, chamadas, contexto = _executar(
        MusicaFalhaAdd()
    )

    assert tratado is True
    assert chamadas[:2] == [
        ("create", "vmz"),
        ("add", "vmz", URL, TITULO, CANAL),
    ]
    assert not any(chamada[0] == "ultima" for chamada in chamadas)
    assert len(falas) == 1
    assert contexto["_playlist_sugestao_pendente"] is None

    assert len(receipts) == 1

    payload = _receipt_payload(receipts[0])

    assert payload.get("intent") == "PLAYLIST_ADD"
    assert payload.get("alvo") == "vmz"
    assert payload.get("ok") is False
    assert payload.get("confirmado") is False
