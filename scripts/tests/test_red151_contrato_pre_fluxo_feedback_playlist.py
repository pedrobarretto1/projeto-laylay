from __future__ import annotations

import time

from mente_laylay.autonomia.feedback_pendente_runtime import (
    FeedbackPendenteRuntime,
)
from mente_laylay.autonomia.fluxos_conversa import (
    handle_feedback_pendente,
)


# ROOT_RED151_PRE_FLUXO_SILENCIOSO_20260830


class _MusicaOperacoesFake:
    def criar_playlist(self, nome):
        return {
            "ok": True,
            "criada": True,
            "status": "playlist_criada",
            "nome": nome,
        }

    def __init__(
        self,
        *,
        save_ok: bool,
        faixa_disponivel: bool = True,
    ) -> None:
        self.save_ok = bool(save_ok)
        self.faixa_disponivel = bool(faixa_disponivel)
        self.add_calls = 0
        self.ultima_playlist = None

    def faixa_atual(self) -> dict:
        if not self.faixa_disponivel:
            return {}

        return {
            "url": "https://www.youtube.com/watch?v=red151",
            "title": "Faixa Teste",
            "canal": "Canal Teste",
        }

    def adicionar_faixa(
        self,
        nome: str,
        url: str,
        titulo: str,
        canal: str = "",
    ) -> bool:
        self.add_calls += 1
        return self.save_ok

    def definir_ultima_playlist(self, nome: str) -> None:
        self.ultima_playlist = str(nome or "").strip()


def _montar_runtime(
    *,
    save_ok: bool,
    faixa_disponivel: bool = True,
):
    continuidades = {
        "rotina_sugestao_pendente": None,
        "playlist_sugestao_pendente": {
            "playlist": "vmz",
            "ts": time.time(),
        },
        "email_sugestao_pendente": None,
    }

    musica = _MusicaOperacoesFake(
        save_ok=save_ok,
        faixa_disponivel=faixa_disponivel,
    )

    falas: list[str] = []

    def falar_com_lipsync(
        fala: str,
        _emocao: str = "calma",
        _nivel: int = 1,
    ) -> None:
        falas.append(str(fala or "").strip())

    def continuidades_get(chave: str):
        return continuidades.get(chave)

    def continuidades_update(**campos) -> None:
        continuidades.update(campos)

    contexto = {
        "handle_feedback_pendente": handle_feedback_pendente,
        "continuidades_get": continuidades_get,
        "continuidades_update": continuidades_update,
        "musica_operacoes": musica,
        "extrair_nome_playlist": lambda _texto: "",
        "yt_clean_title": lambda titulo: str(titulo or "").strip(),
        "falar_com_lipsync": falar_com_lipsync,
    }

    runtime = FeedbackPendenteRuntime(
        contexto_getter=lambda: contexto,
        log=lambda *_args, **_kwargs: None,
    )

    return runtime, continuidades, musica, falas


def test_controle_save_ok_fecha_feedback_com_efeito_e_fala() -> None:
    runtime, continuidades, musica, falas = _montar_runtime(
        save_ok=True,
    )

    tratado = runtime.handle_feedback_pendente("sim")

    assert tratado is True
    assert musica.add_calls == 1
    assert musica.ultima_playlist == "vmz"
    assert continuidades["playlist_sugestao_pendente"] is None
    assert falas


def test_controle_faixa_ausente_fecha_feedback_com_fala_de_falha() -> None:
    runtime, continuidades, musica, falas = _montar_runtime(
        save_ok=False,
        faixa_disponivel=False,
    )

    tratado = runtime.handle_feedback_pendente("sim")

    assert tratado is True
    assert musica.add_calls == 0
    assert musica.ultima_playlist is None
    assert continuidades["playlist_sugestao_pendente"] is None
    assert falas


def test_red151_pre_fluxo_tratado_exige_efeito_ou_resposta_terminal() -> None:
    runtime, _continuidades, musica, falas = _montar_runtime(
        save_ok=False,
    )

    tratado = runtime.handle_feedback_pendente("sim")

    # A mutação realmente foi tentada.
    assert musica.add_calls == 1

    # save=False significa que nenhum efeito foi confirmado.
    efeito_confirmado = musica.ultima_playlist == "vmz"

    # Alguma resposta terminal foi efetivamente produzida?
    resposta_emitida = bool(falas)

    # CONTRATO CANÔNICO:
    #
    # Se o pré-fluxo toma posse do turno (tratado=True), ele só pode
    # encerrá-lo quando houver:
    #
    #   efeito confirmado
    #       OU
    #   resposta terminal ao usuário.
    #
    # Caso contrário, RespostaIARuntime encerra o turno em
    # "tratado_pre_fluxo" e ninguém mais poderá responder.
    assert (
        not tratado
        or efeito_confirmado
        or resposta_emitida
    ), (
        "RED151: o pré-fluxo consumiu a confirmação como tratado=True, "
        "mas adicionar_faixa retornou False e nenhuma resposta terminal "
        "foi emitida ao usuário."
    )