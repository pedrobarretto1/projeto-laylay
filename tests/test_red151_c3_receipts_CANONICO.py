from __future__ import annotations

import time

from mente_laylay.autonomia.fluxos_conversa import handle_feedback_pendente


URL = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
TITULO = "Faixa A"
CANAL = "Canal A"


class _MusicaC3:
    def __init__(
        self,
        *,
        create_ok=True,
        criada=True,
        create_status="playlist_criada",
        add_result=None,
        url=URL,
    ):
        self.create_ok = bool(create_ok)
        self.criada = bool(criada)
        self.create_status = str(create_status)
        self.add_result = dict(
            add_result
            if add_result is not None
            else {
                "ok": True,
                "added": True,
                "duplicated": False,
                "status": "playlist_musica_adicionada",
            }
        )
        self.url = str(url)
        self.chamadas = []

    def faixa_atual(self):
        self.chamadas.append(("faixa_atual",))
        return {
            "url": self.url,
            "title": TITULO,
            "canal": CANAL,
        }

    def criar_playlist(self, nome):
        self.chamadas.append(("create", nome))
        return {
            "ok": self.create_ok,
            "criada": self.criada if self.create_ok else False,
            "status": self.create_status,
            "nome": nome,
        }

    def adicionar_faixa_resultado(self, nome, url, titulo, canal):
        self.chamadas.append(("add_result", nome, url, titulo, canal))
        return dict(self.add_result)

    def adicionar_faixa(self, nome, url, titulo, canal):
        raise AssertionError(
            "O teste C3 deve usar adicionar_faixa_resultado quando disponível."
        )

    def definir_ultima_playlist(self, nome):
        self.chamadas.append(("ultima", nome))


def _executar(musica):
    falas = []
    receipts = []

    def registrar(receipt, texto, executou, *args, **kwargs):
        receipts.append(
            {
                "receipt": dict(receipt or {}),
                "texto": str(texto),
                "executou_arg": bool(executou),
                "args": tuple(args),
                "kwargs": dict(kwargs),
            }
        )

    contexto = {
        "_playlist_sugestao_pendente": {
            "playlist": "vmz",
            "ts": time.time(),
        },
        "_rotina_sugestao_pendente": None,
        "_email_sugestao_pendente": None,
        "_registro_musica_operacoes_runtime": musica,
        "_registrar_resultado_execucao": registrar,
        "_classificar_confirmacao_local": lambda _texto: True,
        "_classificar_confirmacao_contextual": lambda *_args: True,
        "_yt_clean_title": lambda valor: valor,
        "falar_com_lipsync": (
            lambda texto, *_args, **_kwargs: falas.append(str(texto))
        ),
    }

    tratado = handle_feedback_pendente(contexto, "sim")

    return {
        "tratado": tratado,
        "falas": falas,
        "receipts": receipts,
        "contexto": contexto,
        "musica": musica,
    }


def _receipt_unico(resultado):
    assert resultado["tratado"] is True
    assert len(resultado["receipts"]) == 1, (
        "RED151-C3: uma confirmação de playlist deve publicar exatamente "
        "um receipt canônico. Receipts observados: "
        f"{resultado['receipts']!r}"
    )
    return resultado["receipts"][0]


def test_red151_c3_sucesso_publica_um_unico_receipt_canonico():
    resultado = _executar(_MusicaC3())

    publicado = _receipt_unico(resultado)
    receipt = publicado["receipt"]

    assert receipt["intent"] == "PLAYLIST_ADD"
    assert receipt["acao"] == "PLAYLIST_ADD"
    assert receipt["alvo"] == "vmz"
    assert receipt["status"] == "playlist_musica_adicionada"
    assert receipt["ok"] is True
    assert receipt["executou"] is True
    assert receipt["confirmado"] is True
    assert receipt["origem"] == "feedback_playlist"
    assert receipt["detalhe"] == "confirmacao_feedback_playlist"

    params = receipt["params"]
    assert params["nome_playlist"] == "vmz"
    assert params["url"] == URL
    assert params["titulo"] == TITULO
    assert params["canal"] == CANAL
    assert params["playlist_criada"] is True
    assert params["status_criacao"] == "playlist_criada"

    assert publicado["executou_arg"] is True
    assert publicado["kwargs"]["origem"] == "feedback_playlist"
    assert publicado["kwargs"]["status"] == "playlist_musica_adicionada"


def test_red151_c3_duplicata_nao_pode_publicar_receipt_falso_de_mutacao():
    resultado = _executar(
        _MusicaC3(
            criada=False,
            create_status="playlist_ja_existia",
            add_result={
                "ok": True,
                "added": False,
                "duplicated": True,
                "status": "playlist_musica_ja_existia",
            },
        )
    )

    publicado = _receipt_unico(resultado)
    receipt = publicado["receipt"]

    assert receipt["status"] == "playlist_musica_ja_existia"
    assert receipt["ok"] is True
    assert receipt["executou"] is False
    assert receipt["confirmado"] is True
    assert publicado["executou_arg"] is False

    params = receipt["params"]
    assert params["playlist_criada"] is False
    assert params["status_criacao"] == "playlist_ja_existia"


def test_red151_c3_falha_de_add_publica_um_receipt_fail_closed():
    resultado = _executar(
        _MusicaC3(
            add_result={
                "ok": False,
                "added": False,
                "duplicated": False,
                "status": "falha_persistencia",
            }
        )
    )

    publicado = _receipt_unico(resultado)
    receipt = publicado["receipt"]

    assert receipt["status"] == "falha_persistencia"
    assert receipt["ok"] is False
    assert receipt["executou"] is False
    assert receipt["confirmado"] is False
    assert publicado["executou_arg"] is False

    assert len(resultado["falas"]) == 1
    assert resultado["contexto"]["_playlist_sugestao_pendente"] is None


def test_red151_c3_falha_de_create_nao_executa_add_e_publica_um_receipt():
    musica = _MusicaC3(
        create_ok=False,
        criada=False,
        create_status="falha_persistencia",
    )
    resultado = _executar(musica)

    publicado = _receipt_unico(resultado)
    receipt = publicado["receipt"]

    assert ("create", "vmz") in musica.chamadas
    assert not any(chamada[0] == "add_result" for chamada in musica.chamadas)

    assert receipt["status"] == "falha_persistencia"
    assert receipt["ok"] is False
    assert receipt["executou"] is False
    assert receipt["confirmado"] is False


def test_red151_c3_sem_faixa_atual_publica_receipt_sem_criar_ou_adicionar():
    musica = _MusicaC3(url="")
    resultado = _executar(musica)

    publicado = _receipt_unico(resultado)
    receipt = publicado["receipt"]

    assert not any(chamada[0] == "create" for chamada in musica.chamadas)
    assert not any(chamada[0] == "add_result" for chamada in musica.chamadas)

    assert receipt["status"] == "faixa_atual_indisponivel"
    assert receipt["ok"] is False
    assert receipt["executou"] is False
    assert receipt["confirmado"] is False
