from __future__ import annotations

import time

from mente_laylay.autonomia.fluxos_conversa import handle_feedback_pendente


URL = "https://www.youtube.com/watch?v=aaaaaaaaaaa"


class MusicaSucesso:
    def __init__(self):
        self.chamadas = []

    def faixa_atual(self):
        return {
            "url": URL,
            "title": "Faixa A",
            "canal": "Canal A",
        }

    def criar_playlist(self, nome):
        self.chamadas.append(("create", nome))
        return {
            "ok": True,
            "criada": True,
            "status": "playlist_criada",
            "nome": nome,
        }

    def adicionar_faixa_resultado(
        self,
        nome,
        url,
        titulo,
        canal,
    ):
        self.chamadas.append(
            ("add", nome, url, titulo, canal)
        )
        return {
            "ok": True,
            "added": True,
            "duplicated": False,
            "status": "playlist_musica_adicionada",
        }

    def adicionar_faixa(
        self,
        nome,
        url,
        titulo,
        canal,
    ):
        raise AssertionError(
            "O caminho detalhado deveria ter sido usado."
        )

    def definir_ultima_playlist(self, nome):
        self.chamadas.append(("ultima", nome))


def _contexto(musica, receipts, falas):
    def registrar(receipt, *_args, **_kwargs):
        receipts.append(dict(receipt))

    return {
        "_playlist_sugestao_pendente": {
            "playlist": "vmz",
            "ts": time.time(),
        },
        "_rotina_sugestao_pendente": None,
        "_email_sugestao_pendente": None,

        "_registro_musica_operacoes_runtime": musica,

        "_classificar_confirmacao_local": (
            lambda _texto: True
        ),
        "_classificar_confirmacao_contextual": (
            lambda *_args: True
        ),

        "_yt_clean_title": lambda valor: valor,

        "_registrar_resultado_execucao": registrar,

        "falar_com_lipsync": (
            lambda texto, *_args, **_kwargs:
            falas.append(str(texto))
        ),
    }


def test_red151_c3_sucesso_publica_exatamente_um_receipt():
    musica = MusicaSucesso()
    receipts = []
    falas = []

    contexto = _contexto(
        musica,
        receipts,
        falas,
    )

    tratado = handle_feedback_pendente(
        contexto,
        "sim",
    )

    assert tratado is True

    assert musica.chamadas == [
        ("create", "vmz"),
        (
            "add",
            "vmz",
            URL,
            "Faixa A",
            "Canal A",
        ),
        ("ultima", "vmz"),
    ]

    assert len(falas) == 1

    assert len(receipts) == 1, (
        "RED151-C3: um único efeito PLAYLIST_ADD "
        "publicou mais de um receipt canônico. "
        f"Receipts observados: {receipts!r}"
    )

    receipt = receipts[0]

    assert receipt.get("intent") == "PLAYLIST_ADD"
    assert receipt.get("acao") == "PLAYLIST_ADD"
    assert receipt.get("alvo") == "vmz"

    assert receipt.get("ok") is True
    assert receipt.get("executou") is True
    assert receipt.get("confirmado") is True

    assert (
        contexto["_playlist_sugestao_pendente"]
        is None
    )


class MusicaFalhaAdd(MusicaSucesso):
    def adicionar_faixa_resultado(
        self,
        nome,
        url,
        titulo,
        canal,
    ):
        self.chamadas.append(
            ("add", nome, url, titulo, canal)
        )
        return {
            "ok": False,
            "added": False,
            "duplicated": False,
            "status": "falha_persistencia",
        }

    def definir_ultima_playlist(self, nome):
        raise AssertionError(
            "Falha de ADD não pode definir última playlist."
        )


def test_regressivo_red151_c3_falha_add_publica_um_receipt():
    musica = MusicaFalhaAdd()
    receipts = []
    falas = []

    contexto = _contexto(
        musica,
        receipts,
        falas,
    )

    tratado = handle_feedback_pendente(
        contexto,
        "sim",
    )

    assert tratado is True

    assert len(receipts) == 1

    receipt = receipts[0]

    assert receipt.get("intent") == "PLAYLIST_ADD"
    assert receipt.get("alvo") == "vmz"

    assert receipt.get("ok") is False
    assert receipt.get("executou") is False
    assert receipt.get("confirmado") is False

    assert len(falas) == 1


class MusicaFalhaCreate(MusicaSucesso):
    def criar_playlist(self, nome):
        self.chamadas.append(("create", nome))
        return {
            "ok": False,
            "criada": False,
            "status": "falha_persistencia",
            "nome": nome,
        }

    def adicionar_faixa_resultado(self, *args):
        raise AssertionError(
            "CREATE falhou: ADD não pode executar."
        )

    def definir_ultima_playlist(self, nome):
        raise AssertionError(
            "CREATE falhou: não pode definir última playlist."
        )


def test_regressivo_red151_c3_falha_create_publica_um_receipt():
    musica = MusicaFalhaCreate()
    receipts = []
    falas = []

    contexto = _contexto(
        musica,
        receipts,
        falas,
    )

    tratado = handle_feedback_pendente(
        contexto,
        "sim",
    )

    assert tratado is True

    assert musica.chamadas == [
        ("create", "vmz"),
    ]

    assert len(receipts) == 1

    receipt = receipts[0]

    assert receipt.get("ok") is False
    assert receipt.get("executou") is False
    assert receipt.get("confirmado") is False

    assert len(falas) == 1
