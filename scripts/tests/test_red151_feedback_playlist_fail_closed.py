from __future__ import annotations

from mente_laylay.autonomia.fluxos_conversa import handle_feedback_pendente


class MusicaFalha:
    def criar_playlist(self, nome):
        return {
            "ok": True,
            "criada": True,
            "status": "playlist_criada",
            "nome": nome,
        }

    def __init__(self):
        self.add_calls = 0

    def faixa_atual(self):
        return {
            "url": "https://www.youtube.com/watch?v=abcdefghijk",
            "title": "Faixa Teste",
            "canal": "Canal Teste",
        }

    def adicionar_faixa(self, playlist, url, titulo, canal=""):
        self.add_calls += 1
        return False

    def definir_ultima_playlist(self, playlist):
        raise AssertionError(
            "não deve definir última playlist quando salvar falhou"
        )


def test_red151_save_false_nao_pode_ser_consumido_em_silencio():
    falas = []
    musica = MusicaFalha()

    contexto = {
        "_playlist_sugestao_pendente": {
            "playlist": "vmz",
            "ts": 9999999999.0,
        },
        "_rotina_sugestao_pendente": None,
        "_email_sugestao_pendente": None,
        "_classificar_confirmacao_contextual": (
            lambda texto, sugestao: True
        ),
        "_classificar_confirmacao_local": lambda texto: True,
        "_registro_musica_operacoes_runtime": musica,
        "_yt_clean_title": lambda titulo: titulo,
        "falar_com_lipsync": (
            lambda texto, *args: falas.append(str(texto))
        ),
    }

    tratado = handle_feedback_pendente(contexto, "sim")

    assert tratado is True
    assert musica.add_calls == 1

    assert falas, (
        "RED151: save=False foi marcado como tratado, "
        "mas nenhuma resposta foi produzida"
    )

    assert any(
        termo in falas[-1].casefold()
        for termo in ("não consegui", "falhou", "não deu")
    )
