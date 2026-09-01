from __future__ import annotations

import time

from mente_laylay.autonomia.executor_playlists import _sugerir_criacao
from mente_laylay.autonomia.feedback_pendente_runtime import FeedbackPendenteRuntime
from mente_laylay.autonomia.fluxos_conversa import handle_feedback_pendente


URL = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
TITULO = "Faixa Receipt"
CANAL = "Canal Receipt"


class _MusicaSucesso:
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


class _MusicaFalhaCriacao:
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
        raise AssertionError(
            "ADD não pode executar quando CREATE não confirmou o alvo."
        )

    def definir_ultima_playlist(self, nome):
        self.chamadas.append(("ultima", nome))


def _montar_feedback(musica):
    continuidades = {
        "playlist_sugestao_pendente": None,
        "rotina_sugestao_pendente": None,
        "email_sugestao_pendente": None,
    }
    falas = []
    receipts = []

    def falar(texto, *_args, **_kwargs):
        falas.append(str(texto))

    def continuidades_get(chave):
        return continuidades.get(chave)

    def continuidades_update(**valores):
        continuidades.update(valores)

    def registrar_resultado_execucao(
        resultado=None,
        texto="",
        executou=None,
        *,
        origem="",
        status="",
    ):
        receipts.append({
            "resultado": dict(resultado or {}) if isinstance(resultado, dict) else resultado,
            "texto": str(texto or ""),
            "executou": executou,
            "origem": str(origem or ""),
            "status": str(status or ""),
        })

    # Produtor real da oferta/pêndencia do caso 146.
    _sugerir_criacao(
        {
            "set_playlist_sugestao_pendente": (
                lambda valor: continuidades.__setitem__(
                    "playlist_sugestao_pendente",
                    valor,
                )
            ),
            "falar_com_lipsync": falar,
        },
        "vmz",
    )

    feedback = FeedbackPendenteRuntime(
        contexto_getter=lambda: {
            "handle_feedback_pendente": handle_feedback_pendente,
            "continuidades_get": continuidades_get,
            "continuidades_update": continuidades_update,
            "musica_operacoes": musica,
            "falar_com_lipsync": falar,
            "yt_clean_title": lambda valor: valor,
            "registrar_resultado_execucao": registrar_resultado_execucao,
        },
        log=lambda *_args, **_kwargs: None,
    )

    return feedback, continuidades, falas, receipts


def test_red151_receipt_sucesso_feedback_simples_publica_resultado_canonico():
    musica = _MusicaSucesso()
    feedback, continuidades, falas, receipts = _montar_feedback(musica)

    falas_antes = len(falas)

    tratado = feedback.handle_feedback_pendente("sim")

    assert tratado is True

    # O efeito real já está GREEN com C2.
    assert musica.chamadas[:3] == [
        ("create", "vmz"),
        ("add", "vmz", URL, TITULO, CANAL),
        ("ultima", "vmz"),
    ]
    assert continuidades["playlist_sugestao_pendente"] is None
    assert len(falas) == falas_antes + 1

    # PRIMEIRA FRONTEIRA RED:
    # o turno não pode ter efeito real sem publicar o receipt oficial.
    assert len(receipts) == 1, (
        "RED151-RECEIPT: CREATE+ADD foi confirmado e o turno foi tratado, "
        "mas registrar_resultado_execucao não recebeu exatamente um receipt. "
        f"Receipts observados: {receipts!r}"
    )

    registro = receipts[0]
    resultado = registro["resultado"]

    assert isinstance(resultado, dict)
    assert resultado.get("intent") == "PLAYLIST_ADD"
    assert resultado.get("status") == "playlist_musica_adicionada"
    assert resultado.get("confirmado") is True
    assert resultado.get("params", {}).get("nome_playlist") == "vmz"
    assert registro["executou"] is True
    assert registro["texto"].strip().casefold() == "sim"
    assert "feedback" in registro["origem"].casefold()


def test_red151_receipt_falha_create_publica_falha_sem_add():
    musica = _MusicaFalhaCriacao()
    feedback, continuidades, falas, receipts = _montar_feedback(musica)

    falas_antes = len(falas)

    tratado = feedback.handle_feedback_pendente("sim")

    assert tratado is True

    # C2 precisa continuar fail-closed.
    assert musica.chamadas == [
        ("create", "vmz"),
    ]
    assert continuidades["playlist_sugestao_pendente"] is None
    assert len(falas) == falas_antes + 1

    # Mesmo a falha é um resultado operacional observável e precisa de receipt.
    assert len(receipts) == 1, (
        "RED151-RECEIPT-FAIL: CREATE falhou e ADD foi corretamente bloqueado, "
        "mas a falha não foi publicada no registrador canônico. "
        f"Receipts observados: {receipts!r}"
    )

    registro = receipts[0]
    resultado = registro["resultado"]

    assert isinstance(resultado, dict)
    assert resultado.get("intent") == "PLAYLIST_ADD"
    assert resultado.get("status") == "falha_persistencia"
    assert resultado.get("confirmado") is False
    assert resultado.get("params", {}).get("nome_playlist") == "vmz"
    assert registro["executou"] is False
    assert registro["texto"].strip().casefold() == "sim"
    assert "feedback" in registro["origem"].casefold()
