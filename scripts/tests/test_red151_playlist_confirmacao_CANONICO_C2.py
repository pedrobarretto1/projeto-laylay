from __future__ import annotations

import time

from mente_laylay.autonomia.executor_playlists import _sugerir_criacao
from mente_laylay.autonomia.feedback_pendente_runtime import FeedbackPendenteRuntime
from mente_laylay.autonomia.fluxos_conversa import handle_feedback_pendente
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


URL_A = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
URL_B = "https://www.youtube.com/watch?v=bbbbbbbbbbb"

TITULO_A = "Faixa A"
TITULO_B = "Faixa B"

CANAL_A = "Canal A"
CANAL_B = "Canal B"


def _novo_runtime_playlist(tmp_path):
    """PlaylistRuntime real, mas isolado do estado real do usuário."""
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


class _MusicaOperacoesFalha:
    """Porta mínima que reproduz um save real retornando False."""

    def __init__(self):
        self.chamadas = []
        self.ultima_playlist = ""

    def faixa_atual(self):
        return {
            "url": URL_A,
            "title": TITULO_A,
            "canal": CANAL_A,
        }

    def criar_playlist(self, nome):
        return {
            "ok": True,
            "criada": True,
            "status": "playlist_criada",
            "nome": nome,
        }

    def adicionar_faixa(self, playlist, url, titulo, canal):
        self.chamadas.append(
            (playlist, url, titulo, canal)
        )
        return False

    def definir_ultima_playlist(self, nome):
        self.ultima_playlist = str(nome or "")


class _MusicaOperacoesPlaylistReal:
    """
    Adapta o PlaylistRuntime real para a porta que o feedback legado usa.

    O armazenamento continua sendo o real da arquitetura de playlists;
    somente a faixa atual é fixa para deixar o teste determinístico.
    """

    def __init__(self, runtime, ultima):
        self.runtime = runtime
        self.ultima = ultima
        self.faixa = {
            "url": URL_B,
            "title": TITULO_B,
            "canal": CANAL_B,
        }
        self.ultimo_resultado = None

    def faixa_atual(self):
        return dict(self.faixa)

    def criar_playlist(self, nome):
        return self.runtime.create(nome)

    def adicionar_faixa(self, playlist, url, titulo, canal):
        self.ultimo_resultado = self.runtime.add_and_verify_result(
            playlist,
            url,
            titulo,
            canal,
        )
        return bool(
            isinstance(self.ultimo_resultado, dict)
            and self.ultimo_resultado.get("ok")
        )

    def definir_ultima_playlist(self, nome):
        self.ultima["nome"] = str(nome or "")


class _MusicaOperacoesCriacaoObservavel:
    """
    Porta controlada para provar o contrato create -> add.

    ADD só confirma quando a playlist já foi materializada.
    """

    def __init__(self):
        self.chamadas = []
        self.playlists = set()

    def faixa_atual(self):
        return {
            "url": URL_A,
            "title": TITULO_A,
            "canal": CANAL_A,
        }

    def criar_playlist(self, nome):
        self.chamadas.append(("create", nome))

        if nome in self.playlists:
            return {
                "ok": True,
                "criada": False,
                "status": "playlist_ja_existia",
                "nome": nome,
            }

        self.playlists.add(nome)

        return {
            "ok": True,
            "criada": True,
            "status": "playlist_criada",
            "nome": nome,
        }

    def adicionar_faixa(self, nome, url, titulo, canal):
        self.chamadas.append(
            ("add", nome, url, titulo, canal)
        )
        return nome in self.playlists

    def definir_ultima_playlist(self, nome):
        self.chamadas.append(
            ("ultima", nome)
        )


# ============================================================================
# REGRESSIVO A1
# ADD DIRETO EM ALVO CURTO INEXISTENTE NÃO CRIA IMPLICITAMENTE
# ============================================================================


def test_regressivo_add_direto_curto_inexistente_nao_cria_implicitamente(tmp_path):
    """
    O ADD puro continua sendo lookup/escrita em alvo já resolvido.

    A criação de uma playlist inexistente deve acontecer explicitamente
    pelo fluxo que possui essa autorização; não por efeito colateral do ADD.
    """
    runtime, _ultima = _novo_runtime_playlist(tmp_path)

    resultado = runtime.add_and_verify_result(
        "vmz",
        URL_A,
        TITULO_A,
        CANAL_A,
    )

    assert resultado.get("ok") is False
    assert resultado.get("status") == "alvo_ausente"
    assert "vmz" not in runtime.load()


# ============================================================================
# RED151-A2
# A CONFIRMAÇÃO DE UMA OFERTA DE CRIAÇÃO DEVE CRIAR ANTES DO ADD
# ============================================================================


def test_red151_a2_confirmacao_de_playlist_inexistente_deve_criar_antes_de_adicionar():
    falas = []
    musica = _MusicaOperacoesCriacaoObservavel()

    contexto = {
        "_playlist_sugestao_pendente": {
            "playlist": "vmz",
            "ts": time.time(),
        },
        "_rotina_sugestao_pendente": None,
        "_email_sugestao_pendente": None,
        "_registro_musica_operacoes_runtime": musica,
        "_classificar_confirmacao_local": lambda _texto: True,
        "_classificar_confirmacao_contextual": (
            lambda _texto, _sugestao: True
        ),
        "_yt_clean_title": lambda valor: valor,
        "falar_com_lipsync": (
            lambda texto, *_args, **_kwargs:
            falas.append(str(texto))
        ),
    }

    tratado = handle_feedback_pendente(
        contexto,
        "sim",
    )

    assert tratado is True

    assert musica.chamadas[:2] == [
        ("create", "vmz"),
        (
            "add",
            "vmz",
            URL_A,
            TITULO_A,
            CANAL_A,
        ),
    ], (
        "RED151-A2: a confirmação de uma oferta de criação "
        "deve materializar o alvo antes de adicionar a faixa. "
        f"Chamadas observadas: {musica.chamadas!r}"
    )

    assert contexto["_playlist_sugestao_pendente"] is None

    assert len(falas) == 1

    assert any(
        chamada == ("ultima", "vmz")
        for chamada in musica.chamadas
    )


# ============================================================================
# RED151-A3
# CORRIDA BENIGNA: PLAYLIST PODE PASSAR A EXISTIR ANTES DO "SIM"
# ============================================================================


def test_red151_a3_se_playlist_ja_existir_no_momento_do_sim_ainda_deve_adicionar():
    falas = []
    musica = _MusicaOperacoesCriacaoObservavel()

    # Outra ação criou a playlist entre a oferta e a confirmação.
    musica.playlists.add("vmz")

    contexto = {
        "_playlist_sugestao_pendente": {
            "playlist": "vmz",
            "ts": time.time(),
        },
        "_rotina_sugestao_pendente": None,
        "_email_sugestao_pendente": None,
        "_registro_musica_operacoes_runtime": musica,
        "_classificar_confirmacao_local": lambda _texto: True,
        "_classificar_confirmacao_contextual": lambda *_args: True,
        "_yt_clean_title": lambda valor: valor,
        "falar_com_lipsync": (
            lambda texto, *_args, **_kwargs:
            falas.append(str(texto))
        ),
    }

    assert handle_feedback_pendente(contexto, "sim") is True

    assert musica.chamadas[0] == ("create", "vmz")

    assert musica.chamadas[1][:2] == (
        "add",
        "vmz",
    )

    assert contexto["_playlist_sugestao_pendente"] is None

    assert len(falas) == 1

    assert ("ultima", "vmz") in musica.chamadas


# ============================================================================
# RED151-A4
# FAIL-CLOSED: SE CREATE FALHAR, ADD NÃO PODE EXECUTAR
# ============================================================================


def test_red151_a4_se_criacao_falhar_nao_deve_tentar_add():
    falas = []

    class MusicaFalhaCriacao:
        def __init__(self):
            self.chamadas = []

        def faixa_atual(self):
            return {
                "url": URL_A,
                "title": TITULO_A,
                "canal": CANAL_A,
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
            return True

        def definir_ultima_playlist(self, nome):
            self.chamadas.append(("ultima", nome))

    musica = MusicaFalhaCriacao()

    contexto = {
        "_playlist_sugestao_pendente": {
            "playlist": "vmz",
            "ts": time.time(),
        },
        "_rotina_sugestao_pendente": None,
        "_email_sugestao_pendente": None,
        "_registro_musica_operacoes_runtime": musica,
        "_classificar_confirmacao_local": lambda _texto: True,
        "_classificar_confirmacao_contextual": lambda *_args: True,
        "_yt_clean_title": lambda valor: valor,
        "falar_com_lipsync": (
            lambda texto, *_args, **_kwargs:
            falas.append(str(texto))
        ),
    }

    assert handle_feedback_pendente(contexto, "sim") is True

    assert musica.chamadas == [
        ("create", "vmz"),
    ], (
        "RED151-A4: quando a criação do alvo falha, ADD não pode "
        f"ser executado. Chamadas observadas: {musica.chamadas!r}"
    )

    assert contexto["_playlist_sugestao_pendente"] is None

    assert len(falas) == 1


# ============================================================================
# RED151-B
# SAVE=False NÃO PODE ENCERRAR O TURNO SEM CONCLUSÃO OBSERVÁVEL
# ============================================================================


def test_red151_b_save_false_deve_produzir_conclusao_observavel():
    falas = []
    musica = _MusicaOperacoesFalha()

    contexto = {
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
            lambda _texto, _sugestao: True
        ),
        "_yt_clean_title": lambda valor: valor,
        "falar_com_lipsync": (
            lambda texto, *_args, **_kwargs: falas.append(str(texto))
        ),
    }

    tratado = handle_feedback_pendente(
        contexto,
        "sim",
    )

    assert tratado is True

    assert musica.chamadas == [
        (
            "vmz",
            URL_A,
            TITULO_A,
            CANAL_A,
        )
    ]

    assert contexto["_playlist_sugestao_pendente"] is None

    assert len(falas) == 1, (
        "RED151-B: o handler retornou tratado=True depois de uma falha "
        "de save, mas não produziu nenhuma conclusão observável."
    )

    fala = falas[0].strip()

    assert fala, (
        "RED151-B: a conclusão observável não pode ser uma fala vazia."
    )


# ============================================================================
# REGRESSIVOS DE RED151-A
# ============================================================================


def test_regressivo_playlist_curta_ja_existente_continua_valida(tmp_path):
    runtime, _ultima = _novo_runtime_playlist(tmp_path)

    criada = runtime.create("vmz")

    assert criada.get("ok") is True
    assert "vmz" in runtime.load()

    resultado = runtime.add_and_verify_result(
        "vmz",
        URL_A,
        TITULO_A,
        CANAL_A,
    )

    assert resultado.get("ok") is True
    assert len(runtime.load()["vmz"]) == 1


def test_regressivo_criacao_explicita_de_vmz_ja_e_permitida(tmp_path):
    """
    Prova importante para o diagnóstico:

    'vmz' não é um nome inválido no domínio de playlists.
    O próprio CREATE já aceita o nome.
    """
    runtime, _ultima = _novo_runtime_playlist(tmp_path)

    resultado = runtime.create("vmz")

    assert resultado.get("ok") is True
    assert resultado.get("criada") is True
    assert "vmz" in runtime.load()


def test_regressivo_novo_nome_longo_continua_auto_criando_no_add(tmp_path):
    runtime, _ultima = _novo_runtime_playlist(tmp_path)

    resultado = runtime.add_and_verify_result(
        "caos sonora",
        URL_A,
        TITULO_A,
        CANAL_A,
    )

    assert resultado.get("ok") is True

    dados = runtime.load()

    assert "caos sonora" in dados
    assert len(dados["caos sonora"]) == 1


def test_regressivo_duplicata_continua_sendo_sucesso_idempotente(tmp_path):
    runtime, _ultima = _novo_runtime_playlist(tmp_path)

    primeira = runtime.add_and_verify_result(
        "caos sonora",
        URL_A,
        TITULO_A,
        CANAL_A,
    )

    segunda = runtime.add_and_verify_result(
        "caos sonora",
        URL_A,
        TITULO_A,
        CANAL_A,
    )

    assert primeira.get("ok") is True

    assert segunda.get("ok") is True, (
        "Duplicata confirmada não pode virar falha operacional."
    )

    assert segunda.get("added") is False
    assert segunda.get("duplicated") is True
    assert len(runtime.load()["caos sonora"]) == 1


def test_regressivo_abreviacao_curta_ambigua_continua_rejeitada(tmp_path):
    """
    Esta é a proteção que NÃO queremos destruir ao corrigir RED151-A.

    'vmz' como alvo explícito novo:
        válido.

    'vmz' tentando resolver duas playlists existentes:
        ambíguo, portanto deve continuar rejeitado.
    """
    runtime, _ultima = _novo_runtime_playlist(tmp_path)

    assert runtime.create("vmz rock").get("ok") is True
    assert runtime.create("vmz pop").get("ok") is True

    resultado = runtime.add_and_verify_result(
        "vmz",
        URL_A,
        TITULO_A,
        CANAL_A,
    )

    assert resultado.get("ok") is False
    assert resultado.get("status") == "alvo_ausente"

    dados = runtime.load()

    assert "vmz" not in dados
    assert dados["vmz rock"] == []
    assert dados["vmz pop"] == []


# ============================================================================
# RED151 COMPOSTO
# PRODUTOR REAL DA PENDÊNCIA
#       ↓
# CONTINUIDADE COMPARTILHADA
#       ↓
# FEEDBACKPENDENTERUNTIME REAL
#       ↓
# PLAYLISTRUNTIME REAL
# ============================================================================


def test_red151_composto_vmz_confirmada_deve_salvar_e_responder(tmp_path):
    runtime_playlist, ultima = _novo_runtime_playlist(tmp_path)

    continuidades = {
        "playlist_sugestao_pendente": None,
        "rotina_sugestao_pendente": None,
        "email_sugestao_pendente": None,
    }

    falas = []

    def falar(texto, *_args, **_kwargs):
        falas.append(str(texto))

    def continuidades_get(chave):
        return continuidades.get(chave)

    def continuidades_update(**valores):
        continuidades.update(valores)

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

    pendencia = continuidades["playlist_sugestao_pendente"]

    assert isinstance(pendencia, dict)
    assert pendencia.get("playlist") == "vmz"
    assert len(falas) == 1

    controle_a = runtime_playlist.add_and_verify_result(
        "caos sonora",
        URL_A,
        TITULO_A,
        CANAL_A,
    )

    controle_b = runtime_playlist.add_and_verify_result(
        "caos sonora",
        URL_B,
        TITULO_B,
        CANAL_B,
    )

    assert controle_a.get("ok") is True
    assert controle_b.get("ok") is True

    assert (
        continuidades["playlist_sugestao_pendente"]["playlist"]
        == "vmz"
    )

    musica_operacoes = _MusicaOperacoesPlaylistReal(
        runtime_playlist,
        ultima,
    )

    feedback = FeedbackPendenteRuntime(
        contexto_getter=lambda: {
            "handle_feedback_pendente": handle_feedback_pendente,
            "continuidades_get": continuidades_get,
            "continuidades_update": continuidades_update,
            "musica_operacoes": musica_operacoes,
            "falar_com_lipsync": falar,
            "yt_clean_title": lambda valor: valor,
        },
        log=lambda *_args, **_kwargs: None,
    )

    falas_antes_da_confirmacao = len(falas)

    tratado = feedback.handle_feedback_pendente("sim")

    assert tratado is True

    dados = runtime_playlist.load()

    assert "vmz" in dados, (
        "RED151-INTEGRAÇÃO/A: a confirmação da oferta de criação não "
        "materializou 'vmz' antes de salvar a faixa."
    )

    assert len(dados["vmz"]) == 1

    assert len(falas) == falas_antes_da_confirmacao + 1, (
        "RED151-INTEGRAÇÃO/B: a confirmação foi consumida, mas o turno "
        "não publicou conclusão observável."
    )

    assert continuidades["playlist_sugestao_pendente"] is None

    assert ultima["nome"] == "vmz"
