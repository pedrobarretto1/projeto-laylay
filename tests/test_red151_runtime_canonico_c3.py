from __future__ import annotations

import time

from mente_laylay.autonomia.executor_playlists import _sugerir_criacao
from mente_laylay.autonomia.feedback_pendente_runtime import FeedbackPendenteRuntime
from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia
from mente_laylay.autonomia.fluxos_conversa import handle_feedback_pendente
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.integracao.registro_operacoes_musicais import RegistroOperacoesMusicais
from mente_laylay.memoria_mental.operacoes_musicais_runtime import OperacoesMusicaisRuntime
from mente_laylay.memoria_mental.playlist_mental import yt_clean_title, yt_clean_url
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


URL_A = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
URL_B = "https://www.youtube.com/watch?v=bbbbbbbbbbb"
TITULO_A = "Faixa A"
TITULO_B = "Faixa B"
CANAL_A = "Canal A"
CANAL_B = "Canal B"

COMANDOS_147_150 = (
    "Continua a música, passa para a próxima faixa e me diz qual está tocando.",
    "Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela.",
    "Vai para a próxima faixa e adiciona essa também na caos sonora.",
    "Mostra a playlist caos sonora e depois apaga ela.",
)


class _PromptSentinela:
    def __init__(self, chamadas):
        self.chamadas = chamadas

    def preparar(self, texto):
        self.chamadas.append(("prompt_normal", str(texto)))
        return [], ""


def _novo_playlist_runtime(tmp_path):
    ultima = {"nome": ""}
    runtime = PlaylistRuntime(
        state_file=str(tmp_path / "playlists.json"),
        legacy_file=str(tmp_path / "playlists_legacy.json"),
        cache={},
        ultima_playlist_getter=lambda: ultima["nome"],
        ultima_playlist_setter=lambda nome: ultima.__setitem__("nome", str(nome or "")),
        playlist_state={},
        log=lambda *_args, **_kwargs: None,
        artwork_dir=str(tmp_path / "artwork"),
    )
    return runtime, ultima


def _montar_runtime_red151(tmp_path, *, falhar_create_vmz=False):
    playlist_runtime, ultima = _novo_playlist_runtime(tmp_path)

    continuidades = {
        "playlist_sugestao_pendente": None,
        "rotina_sugestao_pendente": None,
        "email_sugestao_pendente": None,
    }
    falas = []
    fases = []
    logs = []
    chamadas_llm = []
    comandos_prioritarios = []
    contadores = {"add_final": 0}

    estado_musica = {
        "ultima_playlist": "",
        "musica_atual_ts": 0.0,
        "musica_atual_status": "",
        "musica_atual_url": "",
        "musica_atual_titulo": "",
        "musica_troca_origem_url": "",
    }

    playlist_state = {
        "name": "",
        "index": 0,
        "shuffle": False,
        "player": {
            "url": URL_A,
            "title": TITULO_A,
            "channel": CANAL_A,
            "state": "playing",
            "observed_at": time.time(),
            "source": "teste_red151_player_observado",
        },
    }

    def musica_get(chave, default=None):
        return estado_musica.get(chave, default)

    def musica_set(chave, valor):
        estado_musica[chave] = valor
        if chave == "ultima_playlist":
            ultima["nome"] = str(valor or "")
        return valor

    operacoes = OperacoesMusicaisRuntime(
        playlists_usuario=playlist_runtime,
        playlists_laylay=object(),
        musica_estado_getter=musica_get,
        musica_estado_setter=musica_set,
        solicitar_aba_ativa=lambda: {},
        playlist_state=playlist_state,
        log=lambda *args, **_kwargs: logs.append(" ".join(str(x) for x in args)),
    )

    if falhar_create_vmz:
        original_create = playlist_runtime.create
        original_add = playlist_runtime.add_and_verify

        def create_controlado(nome):
            if str(nome or "").strip().casefold() == "vmz":
                return {
                    "ok": False,
                    "criada": False,
                    "status": "falha_persistencia",
                    "nome": "vmz",
                }
            return original_create(nome)

        def add_controlado(nome, url, titulo, canal=""):
            if str(nome or "").strip().casefold() == "vmz":
                contadores["add_final"] += 1
            return original_add(nome, url, titulo, canal)

        playlist_runtime.create = create_controlado
        playlist_runtime.add_and_verify = add_controlado
    else:
        original_add = playlist_runtime.add_and_verify

        def add_observavel(nome, url, titulo, canal=""):
            if str(nome or "").strip().casefold() == "vmz":
                contadores["add_final"] += 1
            return original_add(nome, url, titulo, canal)

        playlist_runtime.add_and_verify = add_observavel

    registro_musical = RegistroOperacoesMusicais.criar(operacoes)

    def falar(texto, *_args, **_kwargs):
        falas.append(str(texto))

    def continuidades_get(chave):
        return continuidades.get(chave)

    def continuidades_update(**valores):
        continuidades.update(valores)

    feedback = FeedbackPendenteRuntime(
        contexto_getter=lambda: {
            "handle_feedback_pendente": handle_feedback_pendente,
            "continuidades_get": continuidades_get,
            "continuidades_update": continuidades_update,
            "musica_operacoes": registro_musical,
            "falar_com_lipsync": falar,
            "yt_clean_title": yt_clean_title,
        },
        log=lambda *args, **_kwargs: logs.append(" ".join(str(x) for x in args)),
    )

    contexto_pre_fluxo = {
        "mente_integrada_estado": {
            "turno_atual": {
                "modalidade": "confirmacao",
                "modalidade_geral": "confirmacao",
                "autoriza_execucao": False,
                "requer_esclarecimento": False,
            },
            "pendencia_atual": {},
            "ultima_habilidade": "musica",
        },
        "_handle_feedback_pendente": feedback.handle_feedback_pendente,
        "_handle_feedback_pendente_misto": feedback.handle_feedback_pendente_misto,
        "_contexto_horario_atual": lambda: "teste",
    }

    def processar_prioritario(texto):
        t = str(texto or "").strip()
        if t == "sim":
            return False
        if t not in COMANDOS_147_150:
            return False

        comandos_prioritarios.append(t)
        indice = COMANDOS_147_150.index(t)

        if indice == 0:
            playlist_state["player"] = {
                "url": URL_A,
                "title": TITULO_A,
                "channel": CANAL_A,
                "state": "playing",
                "observed_at": time.time(),
                "source": "teste_red151_turno147",
            }
        elif indice == 1:
            resultado = playlist_runtime.add_and_verify_result(
                "caos sonora", URL_A, TITULO_A, CANAL_A
            )
            assert resultado.get("ok") is True
        elif indice == 2:
            playlist_state["player"] = {
                "url": URL_B,
                "title": TITULO_B,
                "channel": CANAL_B,
                "state": "playing",
                "observed_at": time.time(),
                "source": "teste_red151_turno149",
            }
            resultado = playlist_runtime.add_and_verify_result(
                "caos sonora", URL_B, TITULO_B, CANAL_B
            )
            assert resultado.get("ok") is True
        elif indice == 3:
            assert playlist_runtime.delete("caos sonora") is True

        return True

    contexto_resposta = {
        "processar_comandos_prioritarios": processar_prioritario,
        "contexto_inicio": lambda: contexto_pre_fluxo,
        "processar_inicio_fluxo": processar_inicio_fluxo_resposta_ia,
        "atualizar_plano_turno": fases.append,
        "usar_modo_rapido": lambda _texto: False,
        "preparacao_conversa": _PromptSentinela(chamadas_llm),
    }

    resposta_runtime = RespostaIARuntime(
        contexto_getter=lambda: contexto_resposta,
        log=lambda *args, **_kwargs: logs.append(" ".join(str(x) for x in args)),
    )

    _sugerir_criacao(
        {
            "set_playlist_sugestao_pendente": (
                lambda valor: continuidades.__setitem__("playlist_sugestao_pendente", valor)
            ),
            "falar_com_lipsync": falar,
        },
        "vmz",
    )

    return {
        "resposta_runtime": resposta_runtime,
        "playlist_runtime": playlist_runtime,
        "continuidades": continuidades,
        "falas": falas,
        "fases": fases,
        "logs": logs,
        "chamadas_llm": chamadas_llm,
        "comandos_prioritarios": comandos_prioritarios,
        "playlist_state": playlist_state,
        "ultima": ultima,
        "contadores": contadores,
    }


def test_red151_c3_runtime_canonico_146_151_cria_salva_responde_sem_llm(tmp_path):
    h = _montar_runtime_red151(tmp_path)
    resposta = h["resposta_runtime"]
    continuidades = h["continuidades"]

    pendencia = continuidades["playlist_sugestao_pendente"]
    assert isinstance(pendencia, dict)
    assert pendencia.get("playlist") == "vmz"
    assert len(h["falas"]) == 1

    for comando in COMANDOS_147_150:
        resposta.processar(comando, origem="teste_red151_c3")
        pendencia = continuidades["playlist_sugestao_pendente"]
        assert isinstance(pendencia, dict)
        assert pendencia.get("playlist") == "vmz"

    assert h["comandos_prioritarios"] == list(COMANDOS_147_150)
    assert h["fases"][:4] == ["tratado_prioritario"] * 4
    assert "caos sonora" not in h["playlist_runtime"].load()
    assert "vmz" not in h["playlist_runtime"].load()

    falas_antes = len(h["falas"])
    resposta.processar("sim", origem="teste_red151_c3")

    dados = h["playlist_runtime"].load()

    assert h["fases"][-1] == "tratado_pre_fluxo"
    assert h["chamadas_llm"] == []
    assert continuidades["playlist_sugestao_pendente"] is None

    assert "vmz" in dados
    assert len(dados["vmz"]) == 1

    item = dados["vmz"][0]
    assert yt_clean_url(str(item.get("url") or "")) == yt_clean_url(URL_B)
    assert str(item.get("titulo") or "") == TITULO_B

    assert h["contadores"]["add_final"] == 1
    assert h["ultima"]["nome"] == "vmz"

    assert len(h["falas"]) == falas_antes + 1
    assert str(h["falas"][-1]).strip()


def test_red151_c3_runtime_canonico_create_falha_bloqueia_add_e_responde(tmp_path):
    h = _montar_runtime_red151(tmp_path, falhar_create_vmz=True)

    resposta = h["resposta_runtime"]
    continuidades = h["continuidades"]

    assert continuidades["playlist_sugestao_pendente"]["playlist"] == "vmz"

    falas_antes = len(h["falas"])
    resposta.processar("sim", origem="teste_red151_c3_fail_closed")

    assert h["fases"][-1] == "tratado_pre_fluxo"
    assert h["chamadas_llm"] == []
    assert h["contadores"]["add_final"] == 0

    dados = h["playlist_runtime"].load()
    assert "vmz" not in dados
    assert continuidades["playlist_sugestao_pendente"] is None

    assert len(h["falas"]) == falas_antes + 1
    assert str(h["falas"][-1]).strip()
