from __future__ import annotations

import time

from mente_laylay.autonomia.executor_playlists import _sugerir_criacao
from mente_laylay.autonomia.feedback_pendente_runtime import FeedbackPendenteRuntime
from mente_laylay.autonomia.fluxo_resposta_ia import (
    processar_inicio_fluxo_resposta_ia,
)
from mente_laylay.autonomia.fluxos_conversa import handle_feedback_pendente
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.integracao.registro_operacoes_musicais import (
    RegistroOperacoesMusicais,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)
from mente_laylay.memoria_mental.estado_continuidades import (
    estado_continuidades_inicial,
)
from mente_laylay.memoria_mental.operacoes_musicais_runtime import (
    OperacoesMusicaisRuntime,
)
from mente_laylay.memoria_mental.playlist_mental import yt_clean_title
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


URL_A = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
TITULO_A = "Faixa Runtime Real"
CANAL_A = "Canal Runtime Real"


class _CuradoriaNaoUsada:
    def copiar_faixa(self, *args, **kwargs):
        raise AssertionError(
            "Curadoria não pertence ao caminho do RED151."
        )


class _LLMProibida:
    def preparar(self, *_args, **_kwargs):
        raise AssertionError(
            "RED151 escapou do pré-fluxo e tentou chegar à LLM."
        )


def _montar_runtime(tmp_path):
    playlist_state = {
        "name": "",
        "index": 0,
        "shuffle": False,
        "player": {
            "url": URL_A,
            "title": TITULO_A,
            "channel": CANAL_A,
            "state": "playing",
            "source": "teste_runtime_real",
            "observed_at": time.time(),
        },
    }

    estado = EstadoCompartilhadoRuntime(
        continuidades=estado_continuidades_inicial(),
        musical={
            "ultima_playlist": "",
        },
        mental={
            "turno_atual": {
                "modalidade": "confirmacao",
                "modalidade_geral": "confirmacao",
                "ato_principal": "confirmacao",
                "autoriza_execucao": False,
                "requer_esclarecimento": True,
                "veto_execucao_operacional": False,
                "modalidade_execucao": "",
            },
            "pendencia_atual": {},
        },
    )

    runtime_playlist = PlaylistRuntime(
        state_file=str(tmp_path / "playlists.json"),
        legacy_file=str(tmp_path / "playlists_legacy.json"),
        cache={},
        ultima_playlist_getter=lambda: str(
            estado.musica_get("ultima_playlist", "") or ""
        ),
        ultima_playlist_setter=lambda nome: estado.musica_set(
            "ultima_playlist",
            str(nome or ""),
        ),
        playlist_state=playlist_state,
        log=lambda *_args, **_kwargs: None,
        artwork_dir=str(tmp_path / "artwork"),
    )

    operacoes = OperacoesMusicaisRuntime(
        playlists_usuario=runtime_playlist,
        playlists_laylay=_CuradoriaNaoUsada(),
        musica_estado_getter=estado.musica_get,
        musica_estado_setter=estado.musica_set,
        solicitar_aba_ativa=lambda: {},
        playlist_state=playlist_state,
        log=lambda *_args, **_kwargs: None,
    )

    registro_musical = RegistroOperacoesMusicais.criar(
        operacoes
    )

    falas = []

    def falar(texto, *_args, **_kwargs):
        falas.append(str(texto))

    feedback = FeedbackPendenteRuntime(
        contexto_getter=lambda: {
            "handle_feedback_pendente": handle_feedback_pendente,
            "continuidades_get": estado.continuidades_get,
            "continuidades_update": estado.continuidades_update,
            "musica_operacoes": registro_musical,
            "falar_com_lipsync": falar,
            "yt_clean_title": yt_clean_title,
        },
        log=lambda *_args, **_kwargs: None,
    )

    def contexto_inicio():
        return {
            "mente_integrada_estado": estado.mental,
            "_handle_feedback_pendente":
                feedback.handle_feedback_pendente,
            "_handle_feedback_pendente_misto":
                feedback.handle_feedback_pendente_misto,
            "_contexto_horario_atual": lambda: "noite",
            "_semantica_na_resposta_principal": False,
            "falar_com_lipsync": falar,
        }

    fases = []
    comandos_prioritarios = []

    def processar_prioritario(texto):
        if str(texto).strip().casefold() == "sim":
            return False

        comandos_prioritarios.append(str(texto))
        return True

    contexto_resposta = {
        "processar_comandos_prioritarios":
            processar_prioritario,
        "contexto_inicio":
            contexto_inicio,
        "processar_inicio_fluxo":
            processar_inicio_fluxo_resposta_ia,
        "atualizar_plano_turno":
            fases.append,
        "obter_turno_atual":
            lambda: dict(
                estado.mental.get("turno_atual") or {}
            ),
        # Se o pré-fluxo falhar em consumir "sim",
        # RespostaIARuntime chegará aqui e o teste explode.
        "preparacao_conversa":
            _LLMProibida(),
        "usar_modo_rapido":
            lambda _texto: False,
    }

    resposta = RespostaIARuntime(
        contexto_getter=lambda: contexto_resposta,
        log=lambda *_args, **_kwargs: None,
    )

    return {
        "estado": estado,
        "runtime_playlist": runtime_playlist,
        "registro_musical": registro_musical,
        "feedback": feedback,
        "resposta": resposta,
        "falas": falas,
        "fases": fases,
        "comandos_prioritarios": comandos_prioritarios,
    }


def _armar_vmz(stack):
    estado = stack["estado"]
    falas = stack["falas"]

    _sugerir_criacao(
        {
            "set_playlist_sugestao_pendente":
                lambda valor: estado.continuidades_set(
                    "playlist_sugestao_pendente",
                    valor,
                ),
            "falar_com_lipsync":
                lambda texto, *_args, **_kwargs:
                falas.append(str(texto)),
        },
        "vmz",
    )

    pendencia = estado.continuidades_get(
        "playlist_sugestao_pendente"
    )

    assert isinstance(pendencia, dict)
    assert pendencia.get("playlist") == "vmz"


def test_rt151_c2_146_151_pendencia_sobrevive_e_sim_fecha_no_prefluxo(
    tmp_path,
):
    stack = _montar_runtime(tmp_path)

    estado = stack["estado"]
    resposta = stack["resposta"]
    falas = stack["falas"]
    fases = stack["fases"]
    runtime_playlist = stack["runtime_playlist"]

    # Equivalente à oferta do turno 146.
    _armar_vmz(stack)

    falas_apos_oferta = len(falas)

    # Equivalentes aos turnos 147–150.
    # O objetivo desta prova é atravessar o RespostaIARuntime real
    # e confirmar que a saída "tratado_prioritario" não consome
    # a continuidade da oferta anterior.
    intermediarios = [
        (
            "Continua a música, passa para a próxima faixa "
            "e me diz qual está tocando."
        ),
        (
            "Adiciona essa música na playlist caos sonora "
            "e depois me mostra o que tem nela."
        ),
        (
            "Vai para a próxima faixa e adiciona essa também "
            "na caos sonora."
        ),
        (
            "Mostra a playlist caos sonora e depois apaga ela."
        ),
    ]

    for texto in intermediarios:
        resposta.processar(
            texto,
            origem="teste_rt151",
        )

        pendencia = estado.continuidades_get(
            "playlist_sugestao_pendente"
        )

        assert isinstance(pendencia, dict)
        assert pendencia.get("playlist") == "vmz"

    assert fases[-4:] == [
        "tratado_prioritario",
        "tratado_prioritario",
        "tratado_prioritario",
        "tratado_prioritario",
    ]

    # Turno 151 real na camada RespostaIARuntime.
    resposta.processar(
        "sim",
        origem="teste_rt151",
    )

    dados = runtime_playlist.load()

    assert "vmz" in dados
    assert isinstance(dados["vmz"], list)
    assert len(dados["vmz"]) == 1

    assert dados["vmz"][0]["url"] == URL_A

    assert estado.continuidades_get(
        "playlist_sugestao_pendente"
    ) is None

    assert estado.musica_get(
        "ultima_playlist",
        "",
    ) == "vmz"

    assert fases[-1] == "tratado_pre_fluxo"

    # Oferta 146 + exatamente uma conclusão no 151.
    assert len(falas) == falas_apos_oferta + 1

    assert falas[-1].strip()


def test_rt151_c2_create_falha_e_fail_closed_sem_llm(
    tmp_path,
):
    stack = _montar_runtime(tmp_path)

    estado = stack["estado"]
    resposta = stack["resposta"]
    falas = stack["falas"]
    fases = stack["fases"]
    runtime_playlist = stack["runtime_playlist"]

    _armar_vmz(stack)

    falas_antes = len(falas)

    chamadas_add = {"total": 0}
    add_original = runtime_playlist.add_and_verify

    def add_observado(*args, **kwargs):
        chamadas_add["total"] += 1
        return add_original(*args, **kwargs)

    runtime_playlist.add_and_verify = add_observado

    # CREATE real chama PlaylistRuntime.save().
    # Forçamos apenas o receipt de persistência a falhar.
    runtime_playlist.save = lambda _data: False

    resposta.processar(
        "sim",
        origem="teste_rt151_create_fail",
    )

    assert chamadas_add["total"] == 0, (
        "CREATE falhou, mas ADD foi executado."
    )

    assert "vmz" not in runtime_playlist.load()

    assert estado.continuidades_get(
        "playlist_sugestao_pendente"
    ) is None

    assert estado.musica_get(
        "ultima_playlist",
        "",
    ) == ""

    assert fases[-1] == "tratado_pre_fluxo"

    # C1 garante conclusão observável mesmo na falha.
    assert len(falas) == falas_antes + 1
    assert falas[-1].strip()