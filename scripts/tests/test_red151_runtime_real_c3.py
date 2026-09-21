from __future__ import annotations

from mente_laylay.autonomia.executor_playlists import _sugerir_criacao
from mente_laylay.autonomia.feedback_pendente_runtime import FeedbackPendenteRuntime
from mente_laylay.autonomia.fluxo_resposta_ia import (
    processar_inicio_fluxo_resposta_ia,
)
from mente_laylay.autonomia.fluxos_conversa import handle_feedback_pendente
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.memoria_mental.operacoes_musicais_runtime import (
    OperacoesMusicaisRuntime,
)
from mente_laylay.memoria_mental.playlist_mental import yt_clean_title
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


URL = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
TITULO = "Faixa Runtime C3"
CANAL = "Canal Runtime C3"


class _PromptProibido:
    """
    Se a execução chegar aqui, o pré-fluxo não resolveu o turno.

    RED151 deve terminar em tratado_pre_fluxo sem acordar a LLM.
    """

    def __init__(self):
        self.chamadas = 0

    def preparar_pacote(self, *_args, **_kwargs):
        self.chamadas += 1
        raise AssertionError(
            "RED151-C3: a LLM foi acionada depois de uma confirmação "
            "que deveria ter sido resolvida pelo pré-fluxo."
        )

    def preparar(self, *_args, **_kwargs):
        self.chamadas += 1
        raise AssertionError(
            "RED151-C3: a LLM foi acionada depois de uma confirmação "
            "que deveria ter sido resolvida pelo pré-fluxo."
        )


def _novo_playlist_runtime(tmp_path):
    ultima = {"nome": ""}

    runtime = PlaylistRuntime(
        state_file=str(tmp_path / "playlists.json"),
        legacy_file=str(tmp_path / "playlists_legacy.json"),
        cache={},
        ultima_playlist_getter=lambda: ultima["nome"],
        ultima_playlist_setter=lambda nome: ultima.__setitem__(
            "nome",
            str(nome or ""),
        ),
        playlist_state={},
        log=lambda *_args, **_kwargs: None,
        artwork_dir=str(tmp_path / "artwork"),
    )

    return runtime, ultima


def _montar_cenario(tmp_path):
    playlists, ultima_playlist_runtime = _novo_playlist_runtime(tmp_path)

    continuidades = {
        "playlist_sugestao_pendente": None,
        "rotina_sugestao_pendente": None,
        "email_sugestao_pendente": None,
    }

    estado_musical = {}
    playlist_state = {}
    falas = []
    fases = []
    logs = []

    def falar(texto, *_args, **_kwargs):
        falas.append(str(texto))

    def continuidades_get(chave):
        return continuidades.get(chave)

    def continuidades_update(**campos):
        continuidades.update(campos)

    def musica_estado_getter(chave, default=None):
        return estado_musical.get(chave, default)

    def musica_estado_setter(chave, valor):
        estado_musical[chave] = valor
        return valor

    def solicitar_aba_ativa(*_args, **_kwargs):
        return {
            "url": URL,
            "title": TITULO,
            "canal": CANAL,
            "audibleConfirmed": True,
            "playingConfirmed": True,
            "source": "red151-c3",
        }

    musica_operacoes = OperacoesMusicaisRuntime(
        playlists_usuario=playlists,
        playlists_laylay=playlists,
        musica_estado_getter=musica_estado_getter,
        musica_estado_setter=musica_estado_setter,
        solicitar_aba_ativa=solicitar_aba_ativa,
        playlist_state=playlist_state,
        log=lambda *_args, **_kwargs: None,
    )

    feedback_runtime = FeedbackPendenteRuntime(
        contexto_getter=lambda: {
            "handle_feedback_pendente": handle_feedback_pendente,
            "continuidades_get": continuidades_get,
            "continuidades_update": continuidades_update,
            "musica_operacoes": musica_operacoes,
            "falar_com_lipsync": falar,
            "yt_clean_title": yt_clean_title,
        },
        log=lambda *_args, **_kwargs: None,
    )

    # Equivalente ao produtor real do turno 146.
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

    assert continuidades["playlist_sugestao_pendente"]["playlist"] == "vmz"

    mente = {
        "turno_atual": {},
        "pendencia_atual": {},
        "ultima_habilidade": "",
    }

    contexto_pre_fluxo = {
        "mente_integrada_estado": mente,
        "_handle_feedback_pendente": feedback_runtime.handle_feedback_pendente,
        "_handle_feedback_pendente_misto": (
            feedback_runtime.handle_feedback_pendente_misto
        ),
        "_contexto_horario_atual": lambda: "noite",
    }

    prompt_proibido = _PromptProibido()

    def marcar_inicio_turno(texto, origem="desconhecida"):
        texto_norm = str(texto or "").strip().casefold()

        if texto_norm == "sim":
            modalidade = "confirmacao"
            autoriza = False
        else:
            modalidade = "comando"
            autoriza = True

        mente["turno_atual"] = {
            "id": f"red151-{len(fases) + 1}",
            "modalidade": modalidade,
            "modalidade_geral": modalidade,
            "atos": [modalidade],
            "texto_operacional": texto,
            "autoriza_execucao": autoriza,
            "requer_esclarecimento": False,
            "motivo_decisao": "red151-c3",
        }

    def processar_comandos_prioritarios(texto):
        # Representa os 147-150: são comandos independentes e vencem
        # antes do pré-fluxo. O teste não finge seus efeitos; só prova
        # que essa passagem não consome a pendência de vmz.
        return str(texto or "").strip().casefold() != "sim"

    contexto_resposta = {
        "marcar_inicio_turno": marcar_inicio_turno,
        "obter_turno_atual": lambda: dict(mente["turno_atual"]),
        "processar_comandos_prioritarios": processar_comandos_prioritarios,
        "contexto_inicio": lambda: contexto_pre_fluxo,
        "processar_inicio_fluxo": processar_inicio_fluxo_resposta_ia,
        "atualizar_plano_turno": lambda fase: fases.append(str(fase)),
        "contexto_prompt_runtime": prompt_proibido,
        "usar_modo_rapido": lambda _texto: False,
        "texto_depende_de_contexto": lambda _texto: False,
        "modo_jogo_ativo": False,
        "iniciar_turno_voz": lambda: None,
        "finalizar_turno_voz": lambda: None,
    }

    resposta_runtime = RespostaIARuntime(
        contexto_getter=lambda: contexto_resposta,
        log=lambda *args, **_kwargs: logs.append(
            " ".join(str(x) for x in args)
        ),
    )

    return {
        "playlists": playlists,
        "ultima_playlist_runtime": ultima_playlist_runtime,
        "continuidades": continuidades,
        "estado_musical": estado_musical,
        "musica_operacoes": musica_operacoes,
        "feedback_runtime": feedback_runtime,
        "resposta_runtime": resposta_runtime,
        "prompt_proibido": prompt_proibido,
        "falas": falas,
        "fases": fases,
        "logs": logs,
    }


def test_red151_c3_runtime_real_146_151_cria_salva_sem_llm(tmp_path):
    c = _montar_cenario(tmp_path)

    # Oferta do 146 já produziu uma fala.
    assert len(c["falas"]) == 1

    # Equivalentes estruturais aos turnos 147-150.
    intermediarios = [
        "Continua a música, passa para a próxima faixa e me diz qual está tocando.",
        "Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela.",
        "Vai para a próxima faixa e adiciona essa também na caos sonora.",
        "Mostra a playlist caos sonora e depois apaga ela.",
    ]

    for texto in intermediarios:
        c["resposta_runtime"].processar(
            texto,
            origem="red151-c3-intermediario",
        )

        pendencia = c["continuidades"]["playlist_sugestao_pendente"]

        assert isinstance(pendencia, dict)
        assert pendencia.get("playlist") == "vmz"

    assert c["fases"][-4:] == [
        "tratado_prioritario",
        "tratado_prioritario",
        "tratado_prioritario",
        "tratado_prioritario",
    ]

    falas_antes = len(c["falas"])

    # Turno 151 real pela entrada do RespostaIARuntime.
    c["resposta_runtime"].processar(
        "sim",
        origem="red151-c3-confirmacao",
    )

    dados = c["playlists"].load()

    assert "vmz" in dados
    assert isinstance(dados["vmz"], list)
    assert len(dados["vmz"]) == 1

    faixa = dados["vmz"][0]

    assert "aaaaaaaaaaa" in str(faixa.get("url") or "")
    assert faixa.get("titulo") == TITULO

    assert c["continuidades"]["playlist_sugestao_pendente"] is None

    assert c["estado_musical"].get("ultima_playlist") == "vmz"

    assert c["fases"][-1] == "tratado_pre_fluxo"

    # Uma única conclusão observável para a confirmação.
    assert len(c["falas"]) == falas_antes + 1

    # A confirmação não pode acordar a IA principal.
    assert c["prompt_proibido"].chamadas == 0


def test_red151_c3_create_falha_bloqueia_add_e_nao_chama_llm(
    tmp_path,
    monkeypatch,
):
    c = _montar_cenario(tmp_path)

    chamadas_add = []

    def criar_falha(nome):
        return {
            "ok": False,
            "criada": False,
            "status": "falha_persistencia",
            "nome": nome,
        }

    def add_proibido(*args, **kwargs):
        chamadas_add.append((args, kwargs))
        raise AssertionError(
            "RED151-C3: ADD executou mesmo depois de CREATE falhar."
        )

    monkeypatch.setattr(
        c["playlists"],
        "create",
        criar_falha,
    )

    monkeypatch.setattr(
        c["playlists"],
        "add_and_verify",
        add_proibido,
    )

    falas_antes = len(c["falas"])

    c["resposta_runtime"].processar(
        "sim",
        origem="red151-c3-create-fail",
    )

    assert chamadas_add == []

    assert "vmz" not in c["playlists"].load()

    assert c["continuidades"]["playlist_sugestao_pendente"] is None

    assert c["fases"][-1] == "tratado_pre_fluxo"

    # C1 garante conclusão observável mesmo em falha.
    assert len(c["falas"]) == falas_antes + 1

    assert c["prompt_proibido"].chamadas == 0
