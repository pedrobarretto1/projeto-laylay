from __future__ import annotations

import time

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


URL_A = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
TITULO_A = "Faixa Runtime Real"
CANAL_A = "Canal Runtime Real"

COMANDOS_INTERMEDIARIOS_147_150 = (
    "Continua a música, passa para a próxima faixa e me diz qual está tocando.",
    "Adiciona essa música na playlist caos sonora e depois me mostra o que tem nela.",
    "Vai para a próxima faixa e adiciona essa também na caos sonora.",
    "Mostra a playlist caos sonora e depois apaga ela.",
)


class _LLMProibida:
    """
    Se o pré-fluxo não consumir o "sim", o teste deve morrer imediatamente.

    Isso transforma "não caiu na LLM" em contrato observável, em vez de
    depender de inspeção de log.
    """

    def __init__(self):
        self.chamadas = 0

    def preparar(self, *_args, **_kwargs):
        self.chamadas += 1
        raise AssertionError(
            "RED151-RUNTIME: o turno 'sim' escapou do pré-fluxo e tentou "
            "preparar a LLM principal."
        )

    def preparar_pacote(self, *_args, **_kwargs):
        self.chamadas += 1
        raise AssertionError(
            "RED151-RUNTIME: o turno 'sim' escapou do pré-fluxo e tentou "
            "preparar a LLM principal."
        )


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


def _novo_operacoes_musicais_reais(tmp_path):
    playlist_runtime, ultima_playlist_runtime = _novo_playlist_runtime(tmp_path)

    estado_musical = {
        "musica_atual_ts": time.time(),
        "musica_atual_status": "tocando",
        "musica_atual_url": URL_A,
        "musica_atual_titulo": TITULO_A,
        "musica_troca_origem_url": "",
        "ultima_playlist": "",
    }

    def musica_get(chave, default=None):
        return estado_musical.get(chave, default)

    def musica_set(chave, valor):
        estado_musical[chave] = valor
        return valor

    operacoes = OperacoesMusicaisRuntime(
        playlists_usuario=playlist_runtime,
        # Curadoria da Laylay não participa deste fluxo.
        playlists_laylay=object(),
        musica_estado_getter=musica_get,
        musica_estado_setter=musica_set,
        # Evita qualquer dependência de Chrome/extensão.
        solicitar_aba_ativa=lambda: {},
        playlist_state={},
        log=lambda *_args, **_kwargs: None,
        # Não será usado pelo fluxo de faixa atual; ainda assim, impede rede
        # caso algum regressivo passe por resolução de metadados por engano.
        youtube_metadata_resolver=lambda _url: {},
    )

    return operacoes, playlist_runtime, ultima_playlist_runtime, estado_musical


def _montar_entrada_resposta_real(
    *,
    musica_operacoes,
    continuidades,
    falas,
    fases,
    comandos_intermediarios=COMANDOS_INTERMEDIARIOS_147_150,
):
    """
    Composição dedicada do caminho real que interessa ao RED151:

        RespostaIARuntime.processar
            -> processar_inicio_fluxo_resposta_ia
                -> processar_feedback_pendente
                    -> FeedbackPendenteRuntime
                        -> handle_feedback_pendente

    O executor dos comandos 147-150 é deliberadamente uma fronteira controlada:
    o objetivo deles nesta prova é somente atravessar a rota
    `tratado_prioritario` sem consumir a pendência. O efeito musical completo
    desses comandos já não é parte da raiz do RED151.
    """

    llm = _LLMProibida()

    mente = {
        "turno_atual": {
            "modalidade": "conversa",
            "modalidade_geral": "conversa",
            "autoriza_execucao": False,
            "requer_esclarecimento": False,
        },
        "pendencia_atual": {},
        "ultima_habilidade": "",
    }

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
            "musica_operacoes": musica_operacoes,
            "falar_com_lipsync": falar,
            "yt_clean_title": yt_clean_title,
            # "sim" é resolvido localmente pelo runtime; qualquer necessidade
            # de LLM de confirmação deve permanecer ausente neste caso.
            "interpretar_confirmacao_llm": lambda *_args, **_kwargs: (
                (_ for _ in ()).throw(
                    AssertionError(
                        "RED151-RUNTIME: 'sim' simples tentou usar LLM "
                        "de confirmação."
                    )
                )
            ),
        },
        log=lambda *_args, **_kwargs: None,
    )

    pre_ctx = {
        "mente_integrada_estado": mente,
        "_handle_feedback_pendente": feedback.handle_feedback_pendente,
        "_handle_feedback_pendente_misto": (
            feedback.handle_feedback_pendente_misto
        ),
        "falar_com_lipsync": falar,
        "_contexto_horario_atual": lambda: "teste",
    }

    comandos = set(comandos_intermediarios)

    def marcar_inicio_turno(texto, origem="desconhecida"):
        if str(texto).strip().casefold() == "sim":
            mente["turno_atual"] = {
                "modalidade": "confirmacao",
                "modalidade_geral": "confirmacao",
                "autoriza_execucao": False,
                "requer_esclarecimento": False,
                # Importante: autoriza_execucao=False não é veto explícito.
                "veto_execucao_operacional": False,
            }
        else:
            mente["turno_atual"] = {
                "modalidade": "comando",
                "modalidade_geral": "comando",
                "autoriza_execucao": True,
                "requer_esclarecimento": False,
                "veto_execucao_operacional": False,
            }

    def processar_comandos_prioritarios(texto):
        return str(texto).strip() in comandos

    contexto_resposta = {
        "marcar_inicio_turno": marcar_inicio_turno,
        "obter_turno_atual": lambda: dict(mente["turno_atual"]),
        "processar_comandos_prioritarios": processar_comandos_prioritarios,
        "contexto_inicio": lambda: pre_ctx,
        "processar_inicio_fluxo": processar_inicio_fluxo_resposta_ia,
        "atualizar_plano_turno": lambda fase: fases.append(str(fase)),
        "preparacao_conversa": llm,
        "usar_modo_rapido": lambda _texto: False,
    }

    resposta = RespostaIARuntime(
        contexto_getter=lambda: contexto_resposta,
        log=lambda *_args, **_kwargs: None,
    )

    return resposta, feedback, mente, llm, falar


def test_red151_runtime_real_146_151_cria_salva_responde_sem_llm(tmp_path):
    """
    Prova dedicada do caso histórico depois de C1+C2.

    Não é o chaos completo; é a cadeia crítica atravessando a entrada real
    de RespostaIARuntime e o pré-fluxo real.
    """
    (
        musica_operacoes,
        playlist_runtime,
        _ultima_playlist_runtime,
        estado_musical,
    ) = _novo_operacoes_musicais_reais(tmp_path)

    continuidades = {
        "playlist_sugestao_pendente": None,
        "rotina_sugestao_pendente": None,
        "email_sugestao_pendente": None,
    }
    falas = []
    fases = []

    resposta, _feedback, _mente, llm, falar = _montar_entrada_resposta_real(
        musica_operacoes=musica_operacoes,
        continuidades=continuidades,
        falas=falas,
        fases=fases,
    )

    # ------------------------------------------------------------------
    # Equivalente à fronteira do turno 146:
    # produtor REAL da oferta cria a continuidade que o 151 deverá consumir.
    # ------------------------------------------------------------------
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
    assert "vmz" not in playlist_runtime.load()
    assert len(falas) == 1

    # ------------------------------------------------------------------
    # Turnos equivalentes a 147-150:
    # atravessam a rota prioritária da RespostaIARuntime e não podem consumir
    # uma autorização pendente que pertence ao "sim" futuro.
    # ------------------------------------------------------------------
    for comando in COMANDOS_INTERMEDIARIOS_147_150:
        resposta.processar(comando, origem="red151-runtime")
        assert (
            continuidades["playlist_sugestao_pendente"]["playlist"] == "vmz"
        )

    assert fases.count("tratado_prioritario") == 4
    assert "vmz" not in playlist_runtime.load()

    # ------------------------------------------------------------------
    # Turno 151 real: "sim" entra pela RespostaIARuntime.
    # ------------------------------------------------------------------
    falas_antes = len(falas)
    inicio = time.perf_counter()

    resposta.processar("sim", origem="red151-runtime")

    duracao = time.perf_counter() - inicio

    # O histórico esperou ~120 s. Aqui a confirmação deve terminar localmente.
    assert duracao < 3.0, (
        "RED151-RUNTIME: confirmação demorou demais; possível retorno do "
        f"comportamento de timeout. Duração={duracao:.3f}s"
    )

    assert fases[-1] == "tratado_pre_fluxo"
    assert llm.chamadas == 0

    # Uma única conclusão nova para o "sim".
    assert len(falas) == falas_antes + 1
    assert falas[-1].strip()

    # A continuidade foi consumida somente após a confirmação.
    assert continuidades["playlist_sugestao_pendente"] is None

    # Receipt real de persistência: alvo e faixa existem no armazenamento.
    dados = playlist_runtime.load()
    assert "vmz" in dados
    assert len(dados["vmz"]) == 1

    faixa = dados["vmz"][0]
    assert str(faixa.get("url") or "") == URL_A
    assert str(faixa.get("titulo") or "") == TITULO_A

    # Efeito observável no estado musical compartilhado.
    assert estado_musical["ultima_playlist"] == "vmz"


class _OperacoesCreateFalha:
    """Injeta apenas a falha de CREATE; o restante continua observável."""

    def __init__(self, base):
        self.base = base
        self.chamadas = []

    def faixa_atual(self):
        return self.base.faixa_atual()

    def criar_playlist(self, nome):
        self.chamadas.append(("create", nome))
        return {
            "ok": False,
            "criada": False,
            "status": "falha_persistencia",
            "nome": nome,
        }

    def adicionar_faixa(self, nome, url, titulo, canal=""):
        self.chamadas.append(("add", nome, url, titulo, canal))
        return self.base.adicionar_faixa(nome, url, titulo, canal)

    def definir_ultima_playlist(self, nome):
        self.chamadas.append(("ultima", nome))
        self.base.definir_ultima_playlist(nome)


def test_red151_runtime_real_create_falha_bloqueia_add_e_responde(tmp_path):
    """
    Prova negativa pela mesma entrada real:
    receipt CREATE=False deve bloquear ADD e ainda encerrar o turno com fala.
    """
    (
        base_operacoes,
        playlist_runtime,
        _ultima_playlist_runtime,
        _estado_musical,
    ) = _novo_operacoes_musicais_reais(tmp_path)

    musica_operacoes = _OperacoesCreateFalha(base_operacoes)

    continuidades = {
        "playlist_sugestao_pendente": None,
        "rotina_sugestao_pendente": None,
        "email_sugestao_pendente": None,
    }
    falas = []
    fases = []

    resposta, _feedback, _mente, llm, falar = _montar_entrada_resposta_real(
        musica_operacoes=musica_operacoes,
        continuidades=continuidades,
        falas=falas,
        fases=fases,
        comandos_intermediarios=(),
    )

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

    falas_antes = len(falas)

    resposta.processar("sim", origem="red151-runtime-create-fail")

    assert fases[-1] == "tratado_pre_fluxo"
    assert llm.chamadas == 0

    # CREATE foi a única mutação tentada.
    assert musica_operacoes.chamadas == [
        ("create", "vmz"),
    ]

    assert "vmz" not in playlist_runtime.load()

    # Mesmo em falha, o turno consumido termina observavelmente (C1).
    assert len(falas) == falas_antes + 1
    assert falas[-1].strip()

    assert continuidades["playlist_sugestao_pendente"] is None
