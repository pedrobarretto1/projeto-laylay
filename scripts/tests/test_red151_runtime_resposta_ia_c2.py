from __future__ import annotations

import time

from mente_laylay.autonomia.executor_playlists import _sugerir_criacao
from mente_laylay.autonomia.feedback_pendente_runtime import FeedbackPendenteRuntime
from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia
from mente_laylay.autonomia.fluxos_conversa import handle_feedback_pendente
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


URL = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
TITULO = "Faixa Runtime"
CANAL = "Canal Runtime"


def _novo_playlist_runtime(tmp_path):
    ultima = {"nome": ""}

    runtime = PlaylistRuntime(
        state_file=str(tmp_path / "playlists.json"),
        legacy_file=str(tmp_path / "playlists_legacy.json"),
        cache={},
        ultima_playlist_getter=lambda: ultima["nome"],
        ultima_playlist_setter=lambda nome: ultima.__setitem__(
            "nome", str(nome or "")
        ),
        playlist_state={},
        log=lambda *_args, **_kwargs: None,
        artwork_dir=str(tmp_path / "artwork"),
    )

    return runtime, ultima


class _MusicaOperacoesReal:
    def __init__(self, runtime, ultima):
        self.runtime = runtime
        self.ultima = ultima
        self.faixa = {
            "url": URL,
            "title": TITULO,
            "canal": CANAL,
        }
        self.chamadas = []

    def faixa_atual(self):
        return dict(self.faixa)

    def criar_playlist(self, nome):
        self.chamadas.append(("create", nome))
        return self.runtime.create(nome)

    def adicionar_faixa(self, nome, url, titulo, canal):
        self.chamadas.append(
            ("add", nome, url, titulo, canal)
        )
        return bool(
            self.runtime.add_and_verify_result(
                nome,
                url,
                titulo,
                canal,
            ).get("ok")
        )

    def definir_ultima_playlist(self, nome):
        self.chamadas.append(("ultima", nome))
        self.ultima["nome"] = str(nome or "")


class _MusicaOperacoesFalhaCriacao:
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

    def adicionar_faixa(self, nome, url, titulo, canal):
        self.chamadas.append(
            ("add", nome, url, titulo, canal)
        )
        return True

    def definir_ultima_playlist(self, nome):
        self.chamadas.append(("ultima", nome))


def _armar_pendencia_real(continuidades, falas, nome="vmz"):
    _sugerir_criacao(
        {
            "set_playlist_sugestao_pendente": (
                lambda valor: continuidades.__setitem__(
                    "playlist_sugestao_pendente",
                    valor,
                )
            ),
            "falar_com_lipsync": (
                lambda texto, *_args, **_kwargs:
                falas.append(str(texto))
            ),
        },
        nome,
    )

    pendencia = continuidades.get(
        "playlist_sugestao_pendente"
    )

    assert isinstance(pendencia, dict)
    assert pendencia.get("playlist") == nome


def _montar_resposta_runtime(
    *,
    continuidades,
    musica_operacoes,
    falas,
    fases,
    llm_chamadas,
):
    def continuidades_get(chave):
        return continuidades.get(chave)

    def continuidades_update(**valores):
        continuidades.update(valores)

    feedback_runtime = FeedbackPendenteRuntime(
        contexto_getter=lambda: {
            "handle_feedback_pendente": handle_feedback_pendente,
            "continuidades_get": continuidades_get,
            "continuidades_update": continuidades_update,
            "musica_operacoes": musica_operacoes,
            "falar_com_lipsync": (
                lambda texto, *_args, **_kwargs:
                falas.append(str(texto))
            ),
            "yt_clean_title": lambda valor: valor,
        },
        log=lambda *_args, **_kwargs: None,
    )

    contexto_pre_fluxo = {
        "mente_integrada_estado": {
            "turno_atual": {
                "modalidade": "confirmacao",
                "modalidade_geral": "confirmacao",
                "autoriza_execucao": False,
                "requer_esclarecimento": True,
                "motivo_decisao": "red151_confirmacao_pendente",
            },
            "pendencia_atual": {},
            "ultima_habilidade": "PLAYLIST_PLAY",
        },
        "_handle_feedback_pendente": (
            feedback_runtime.handle_feedback_pendente
        ),
        "_handle_feedback_pendente_misto": (
            feedback_runtime.handle_feedback_pendente_misto
        ),
        "_contexto_horario_atual": lambda: "teste",
    }

    class _LLMProibida:
        def preparar(self, *_args, **_kwargs):
            llm_chamadas.append("prompt")
            raise AssertionError(
                "RED151: o turno foi enviado à LLM "
                "mesmo após feedback pendente tratado."
            )

        def preparar_pacote(self, *_args, **_kwargs):
            llm_chamadas.append("prompt")
            raise AssertionError(
                "RED151: o turno foi enviado à LLM "
                "mesmo após feedback pendente tratado."
            )

    contexto_resposta = {
        "processar_comandos_prioritarios": (
            lambda _texto: False
        ),
        "contexto_inicio": lambda: contexto_pre_fluxo,
        "processar_inicio_fluxo": (
            processar_inicio_fluxo_resposta_ia
        ),
        "atualizar_plano_turno": (
            lambda fase: fases.append(str(fase))
        ),
        "usar_modo_rapido": lambda _texto: False,
        "preparacao_conversa": _LLMProibida(),
        "contexto_prompt_runtime": _LLMProibida(),
    }

    return RespostaIARuntime(
        contexto_getter=lambda: contexto_resposta,
        log=lambda *_args, **_kwargs: None,
    )


def test_red151_runtime_ciclo_resposta_confirma_vmz_sem_llm(tmp_path):
    """
    Validação pós-C2 no ciclo canônico de resposta:

    RespostaIARuntime
        -> processar_inicio_fluxo_resposta_ia
        -> FeedbackPendenteRuntime
        -> handle_feedback_pendente
        -> CREATE
        -> ADD
        -> fala
        -> tratado_pre_fluxo

    Não é o processo completo `laylay.py`, mas atravessa o runtime real
    responsável pela fronteira histórica `tratado_pre_fluxo`.
    """
    playlist_runtime, ultima = _novo_playlist_runtime(
        tmp_path
    )

    continuidades = {
        "playlist_sugestao_pendente": None,
        "rotina_sugestao_pendente": None,
        "email_sugestao_pendente": None,
    }

    falas = []
    fases = []
    llm_chamadas = []

    _armar_pendencia_real(
        continuidades,
        falas,
        "vmz",
    )

    falas_antes = len(falas)

    musica = _MusicaOperacoesReal(
        playlist_runtime,
        ultima,
    )

    resposta_runtime = _montar_resposta_runtime(
        continuidades=continuidades,
        musica_operacoes=musica,
        falas=falas,
        fases=fases,
        llm_chamadas=llm_chamadas,
    )

    resposta_runtime.processar(
        "sim",
        origem="red151-runtime",
    )

    assert fases[-1] == "tratado_pre_fluxo"
    assert llm_chamadas == []

    assert musica.chamadas[:2] == [
        ("create", "vmz"),
        (
            "add",
            "vmz",
            URL,
            TITULO,
            CANAL,
        ),
    ]

    assert ("ultima", "vmz") in musica.chamadas

    dados = playlist_runtime.load()

    assert "vmz" in dados
    assert len(dados["vmz"]) == 1
    assert dados["vmz"][0]["url"] == URL

    assert (
        continuidades["playlist_sugestao_pendente"]
        is None
    )

    assert len(falas) == falas_antes + 1
    assert falas[-1].strip()

    assert ultima["nome"] == "vmz"


def test_red151_runtime_create_falha_bloqueia_add_e_responde():
    """
    Fail-closed no mesmo ciclo de resposta.

    CREATE falha:
        -> ADD não executa
        -> turno continua tratado no pré-fluxo
        -> resposta observável
        -> LLM não é acionada
    """
    continuidades = {
        "playlist_sugestao_pendente": None,
        "rotina_sugestao_pendente": None,
        "email_sugestao_pendente": None,
    }

    falas = []
    fases = []
    llm_chamadas = []

    _armar_pendencia_real(
        continuidades,
        falas,
        "vmz",
    )

    falas_antes = len(falas)

    musica = _MusicaOperacoesFalhaCriacao()

    resposta_runtime = _montar_resposta_runtime(
        continuidades=continuidades,
        musica_operacoes=musica,
        falas=falas,
        fases=fases,
        llm_chamadas=llm_chamadas,
    )

    resposta_runtime.processar(
        "sim",
        origem="red151-runtime-fail-closed",
    )

    assert fases[-1] == "tratado_pre_fluxo"
    assert llm_chamadas == []

    assert musica.chamadas == [
        ("create", "vmz"),
    ]

    assert (
        continuidades["playlist_sugestao_pendente"]
        is None
    )

    assert len(falas) == falas_antes + 1
    assert falas[-1].strip()
