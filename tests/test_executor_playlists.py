from __future__ import annotations

import time

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_playlists import (
    DependenciasExecutorPlaylists,
    executar_intencao_playlists,
)
from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.autonomia.detectores_playlist import (
    detectar_playlist_contextual_musica_atual,
    detectar_playlist_usuario,
)
from mente_laylay.autonomia.roteador_deterministico import detectar_movimento_playlist
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.memoria_mental.contexto_compartilhado import registrar_resultado_execucao
from mente_laylay.memoria_mental.continuidade_geral import resolver_continuacao_aditiva
from mente_laylay.autonomia.roteador_intencao import executar_intencao


class _MusicaLeituraFake:
    def __init__(self, *, lista="Sem playlists.", conteudo=None, total=0):
        self.lista = lista
        self.conteudo = conteudo or {"ok": False, "name": "", "total": 0}
        self.total = total

    def listar_usuario(self): return self.lista
    def consultar_usuario(self, _nome): return dict(self.conteudo)
    def contar_usuario(self, _nome): return self.total


class _MusicaOperacoesFake:
    def __init__(
        self, *, faixa=None, adicionar=None, tocar=None, shuffle=None,
        primeira=None, apagar=None, definir_ultima=None, definir_url=None,
        mover=None, estado=None, criar=None,
    ):
        self._faixa = faixa or (lambda: {})
        self._adicionar = adicionar or (lambda *_args: False)
        self._tocar = tocar or (lambda _nome: False)
        self._shuffle = shuffle or (lambda _nome: {})
        self._primeira = primeira or (lambda _nome: "")
        self._apagar = apagar or (lambda _nome: False)
        self._definir_ultima = definir_ultima or (lambda _nome: None)
        self._definir_url = definir_url or (lambda _url: None)
        self._mover = mover or (lambda *_args: {})
        self._estado = estado or (lambda: {})
        self._criar = criar or (lambda nome: {
            "ok": True, "criada": True, "status": "playlist_criada", "nome": nome,
        })

    def faixa_atual(self): return dict(self._faixa() or {})
    def adicionar_faixa(self, *args): return bool(self._adicionar(*args))
    def tocar_playlist(self, nome): return bool(self._tocar(nome))
    def preparar_shuffle(self, nome): return dict(self._shuffle(nome) or {})
    def primeira_url(self, nome): return str(self._primeira(nome) or "")
    def apagar_playlist(self, nome): return bool(self._apagar(nome))
    def mover_faixa(self, origem, destino, musica=""):
        return dict(self._mover(origem, destino, musica) or {})
    def definir_ultima_playlist(self, nome): self._definir_ultima(nome)
    def definir_ultima_url(self, url): self._definir_url(url)
    def estado(self): return dict(self._estado() or {})
    def criar_playlist(self, nome): return dict(self._criar(nome) or {})


def _dependencias(
    eventos: list[tuple], abrir=lambda *_args, **_kwargs: True,
    musica_leitura=None, musica_operacoes=None,
):
    return DependenciasExecutorPlaylists(
        marcar_resultado=lambda status, **kwargs: eventos.append(
            ("resultado", status, kwargs)
        ),
        falar_por_status=lambda status, fala, **kwargs: eventos.append(
            ("fala_status", status, fala, kwargs)
        ),
        abrir_url_musical=abrir,
        contexto_fala=lambda: {},
        musica_leitura=musica_leitura,
        musica_operacoes=musica_operacoes,
    )


def test_executor_playlists_nao_interfere_em_outro_dominio() -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_playlists(
        "MUSIC_SEARCH", {}, "toca Duality", "pc_a", {}, _dependencias(eventos)
    )

    assert despacho == ResultadoDespacho.nao_tratado()
    assert eventos == []


def test_movimento_playlist_vira_intent_oficial_com_parametros_completos() -> None:
    resultado = detectar_movimento_playlist(
        "move Duality da playlist rock para a playlist treino",
        params_cb=lambda **kwargs: kwargs,
        limpar_nome_playlist=lambda valor: str(valor).strip().casefold(),
    )

    assert resultado == {
        "intent": "PLAYLIST_MOVE",
        "params": {"musica": "Duality", "origem": "rock", "destino": "treino"},
    }


def test_movimento_playlist_atravessa_roteador_canonico_e_catalogo() -> None:
    contexto = {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "limpar_nome_playlist": lambda valor: str(valor).strip().casefold(),
        "texto_conversa_casual_sem_acao": lambda _texto: False,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: False,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: False,
        "texto_expresso_melhor_no_deterministico": lambda _texto: True,
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda *_args: "pc_a",
    }

    resultado = detectar_intencao_deterministica_mente(
        "transfira Duality da playlist rock para a playlist treino",
        contexto,
    )

    assert resultado == {
        "intent": "PLAYLIST_MOVE",
        "params": {"musica": "duality", "origem": "rock", "destino": "treino"},
    }
    assert "PLAYLIST_MOVE" in intents_registradas()


def test_executor_move_faixa_pelo_caminho_canonico_e_confirma_persistencia() -> None:
    eventos: list[tuple] = []
    movimentos: list[tuple[str, str, str]] = []
    ultimas: list[str] = []

    despacho = executar_intencao_playlists(
        "PLAYLIST_MOVE",
        {"musica": "Duality", "origem": "rock", "destino": "treino"},
        "move Duality da playlist rock para a playlist treino",
        "pc_a",
        {},
        _dependencias(
            eventos,
            musica_operacoes=_MusicaOperacoesFake(
                mover=lambda origem, destino, musica: movimentos.append(
                    (origem, destino, musica)
                ) or {
                    "ok": True,
                    "titulo": "Duality",
                    "origem": origem,
                    "destino": destino,
                },
                definir_ultima=ultimas.append,
            ),
        ),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert movimentos == [("rock", "treino", "Duality")]
    assert ultimas == ["treino"]
    assert (
        "resultado",
        "playlist_faixa_movida",
        {
            "executou": True, "confirmado": True,
            "alvo_resolvido": "treino",
            "params_resolvidos": {"nome_playlist": "treino"},
        },
    ) in eventos
    assert any(
        evento[0] == "fala_status" and "Movi Duality" in evento[2]
        for evento in eventos
    )


def test_adicao_prefere_faixa_viva_do_player_em_vez_da_aba_ativa() -> None:
    eventos: list[tuple] = []
    adicoes: list[tuple] = []
    estado = {
        "musica_atual_ts": time.time(),
        "musica_atual_status": "tocando",
        "musica_atual_url": "https://www.youtube.com/watch?v=player",
        "musica_atual_titulo": "Duality (Official Video)",
    }

    despacho = executar_intencao_playlists(
        "PLAYLIST_ADD",
        {"nome_playlist": "rock"},
        "coloca essa musica na playlist rock",
        "pc_a",
        {
            "_musica_estado_get": lambda chave, padrao=None: estado.get(chave, padrao),
            "solicitar_aba_ativa": lambda: (_ for _ in ()).throw(
                AssertionError("a aba não deve vencer a faixa viva")
            ),
            "ADD_TO_PLAYLIST": lambda *args: adicoes.append(args) or True,
            "_yt_clean_title": lambda titulo: titulo.replace(" (Official Video)", ""),
            "set_ultima_playlist": lambda nome: eventos.append(("ultima", nome)),
        },
        _dependencias(eventos, musica_operacoes=_MusicaOperacoesFake(
            faixa=lambda: {
                "url": estado["musica_atual_url"],
                "title": estado["musica_atual_titulo"],
                "canal": "",
            },
            adicionar=lambda *args: adicoes.append(args) or True,
            definir_ultima=lambda nome: eventos.append(("ultima", nome)),
        )),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert adicoes == [(
        "rock",
        "https://www.youtube.com/watch?v=player",
        "Duality (Official Video)",
        "",
    )]
    assert ("ultima", "rock") in eventos
    assert (
        "resultado", "playlist_musica_adicionada", {
            "executou": True, "alvo_resolvido": "rock",
            "params_resolvidos": {"nome_playlist": "rock"},
        },
    ) in eventos


def test_adicao_com_estado_antigo_consulta_aba_ativa() -> None:
    adicoes: list[tuple] = []
    estado = {
        "musica_atual_ts": time.time() - 7201,
        "musica_atual_status": "tocando",
        "musica_atual_url": "https://www.youtube.com/watch?v=antiga",
        "musica_atual_titulo": "Antiga",
    }

    executar_intencao_playlists(
        "PLAYLIST_ADD",
        {"nome_playlist": "vibes"},
        "salva essa em vibes",
        "pc_a",
        {
            "_musica_estado_get": lambda chave, padrao=None: estado.get(chave, padrao),
            "solicitar_aba_ativa": lambda: {
                "url": "https://www.youtube.com/watch?v=nova",
                "title": "Nova",
                "canal": "Canal",
            },
            "ADD_TO_PLAYLIST": lambda *args: adicoes.append(args) or True,
        },
        _dependencias([], musica_operacoes=_MusicaOperacoesFake(
            faixa=lambda: {
                "url": "https://www.youtube.com/watch?v=nova",
                "title": "Nova", "canal": "Canal",
            },
            adicionar=lambda *args: adicoes.append(args) or True,
        )),
    )

    assert adicoes == [
        ("vibes", "https://www.youtube.com/watch?v=nova", "Nova", "Canal")
    ]


def test_nome_explicito_incompleto_nao_usa_ultima_playlist() -> None:
    falas: list[str] = []
    eventos: list[tuple] = []

    despacho = executar_intencao_playlists(
        "PLAYLIST_ADD",
        {},
        "coloca nessa playlist estranha",
        "pc_a",
        {
            "ultima_playlist": "rock",
            "_playlist_nome_explicito_na_frase": lambda _texto: True,
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "solicitar_aba_ativa": lambda: (_ for _ in ()).throw(
                AssertionError("não deve tentar adicionar")
            ),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido(False)
    assert eventos == [(
        "resultado",
        "alvo_ausente",
        {"executou": False, "confirmado": False},
    )]
    assert falas


def test_listagem_geral_nao_tenta_resolver_playlist_especifica() -> None:
    falas: list[str] = []

    executar_intencao_playlists(
        "PLAYLIST_LIST",
        {},
        "quais são minhas playlists",
        "pc_a",
        {
            "_pedido_lista_geral_playlist": lambda *_args: True,
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias(
            [], musica_leitura=_MusicaLeituraFake(lista="rock, anime e vibes")
        ),
    )

    assert falas == ["rock, anime e vibes"]


def test_listagem_especifica_estiliza_conteudo_e_atualiza_contexto() -> None:
    falas: list[str] = []
    ultimas: list[str] = []

    executar_intencao_playlists(
        "PLAYLIST_LIST",
        {"nome_playlist": "rock"},
        "o que tem na rock",
        "pc_a",
        {
            "_pedido_lista_geral_playlist": lambda *_args: False,
            "_fala_playlist_conteudo_estilosa": lambda *_args: "Rock tem três músicas.",
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "set_ultima_playlist": ultimas.append,
        },
        _dependencias(
            [],
            musica_leitura=_MusicaLeituraFake(conteudo={
                "ok": True, "name": "Rock", "total": 3,
            }),
            musica_operacoes=_MusicaOperacoesFake(
                definir_ultima=ultimas.append,
            ),
        ),
    )

    assert falas == ["Rock tem três músicas."]
    assert ultimas == ["Rock"]


def test_reproducao_sem_autorizacao_nao_executa() -> None:
    chamadas: list[str] = []

    despacho = executar_intencao_playlists(
        "PLAYLIST_PLAY",
        {"nome_playlist": "rock"},
        "eu gosto da playlist rock",
        "pc_a",
        {
            "_autonomia_permite_execucao_musical": lambda *_args: False,
            "play_playlist": lambda nome: chamadas.append(nome) or True,
        },
        _dependencias([]),
    )

    assert despacho == ResultadoDespacho.concluido(False)
    assert chamadas == []


def test_reproducao_local_abre_playlist_e_guarda_contexto() -> None:
    eventos: list[tuple] = []
    chamadas: list[str] = []

    despacho = executar_intencao_playlists(
        "PLAYLIST_PLAY",
        {"nome_playlist": "rock"},
        "toca a playlist rock",
        "pc_a",
        {
            "_autonomia_permite_execucao_musical": lambda *_args: True,
            "play_playlist": lambda nome: chamadas.append(nome) or True,
            "set_ultima_playlist": lambda nome: eventos.append(("ultima", nome)),
        },
        _dependencias(
            eventos,
            musica_leitura=_MusicaLeituraFake(total=3),
            musica_operacoes=_MusicaOperacoesFake(
                tocar=lambda nome: chamadas.append(nome) or True,
                definir_ultima=lambda nome: eventos.append(("ultima", nome)),
            ),
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert chamadas == ["rock"]
    assert ("ultima", "rock") in eventos
    assert (
        "resultado", "playlist_aberta", {
            "executou": True, "alvo_resolvido": "rock",
            "params_resolvidos": {"nome_playlist": "rock"},
        },
    ) in eventos


def test_shuffle_abre_primeira_faixa_e_registra_url() -> None:
    eventos: list[tuple] = []
    aberturas: list[str] = []
    urls: list[str] = []

    despacho = executar_intencao_playlists(
        "PLAYLIST_PLAY",
        {"nome_playlist": "rock", "modo": "shuffle"},
        "embaralha a playlist rock",
        "pc_a",
        {
            "_autonomia_permite_execucao_musical": lambda *_args: True,
            "_playlist_shuffle_start": lambda _nome: {
                "url": "https://www.youtube.com/watch?v=shuffle"
            },
            "set_playlist_state_last_url": urls.append,
        },
        _dependencias(
            eventos,
            abrir=lambda url, **_kwargs: aberturas.append(url) or True,
            musica_operacoes=_MusicaOperacoesFake(
                shuffle=lambda _nome: {
                    "url": "https://www.youtube.com/watch?v=shuffle"
                },
                definir_url=urls.append,
            ),
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert aberturas == ["https://www.youtube.com/watch?v=shuffle"]
    assert urls == aberturas
    assert (
        "resultado", "playlist_aberta", {
            "executou": True, "alvo_resolvido": "rock",
            "params_resolvidos": {"nome_playlist": "rock"},
        },
    ) in eventos


def test_pc_b_abre_primeira_faixa_sem_usar_player_local() -> None:
    eventos: list[tuple] = []
    aberturas: list[str] = []

    despacho = executar_intencao_playlists(
        "PLAYLIST_PLAY",
        {"nome_playlist": "anime"},
        "toca anime no pc b",
        "pc_b",
        {
            "_autonomia_permite_execucao_musical": lambda *_args: True,
            "_playlist_primeira_url": lambda _nome: "https://youtube.com/watch?v=anime",
            "play_playlist": lambda _nome: (_ for _ in ()).throw(
                AssertionError("não deve usar o player local")
            ),
        },
        _dependencias(
            eventos,
            abrir=lambda url, **_kwargs: aberturas.append(url) or True,
            musica_operacoes=_MusicaOperacoesFake(
                primeira=lambda _nome: "https://youtube.com/watch?v=anime",
            ),
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert aberturas == ["https://youtube.com/watch?v=anime"]
    assert (
        "resultado", "playlist_aberta_pc_b", {
            "executou": True, "alvo_resolvido": "anime",
            "params_resolvidos": {"nome_playlist": "anime"},
        },
    ) in eventos


def test_playlist_inexistente_cria_sugestao_pendente() -> None:
    eventos: list[tuple] = []
    pendencias: list[dict] = []

    despacho = executar_intencao_playlists(
        "PLAYLIST_PLAY",
        {"nome_playlist": "nova"},
        "toca a playlist nova",
        "pc_a",
        {
            "_autonomia_permite_execucao_musical": lambda *_args: True,
            "play_playlist": lambda _nome: False,
            "set_playlist_sugestao_pendente": pendencias.append,
            "falar_com_lipsync": lambda *_args: None,
        },
        _dependencias(
            eventos,
            musica_leitura=_MusicaLeituraFake(),
            musica_operacoes=_MusicaOperacoesFake(tocar=lambda _nome: False),
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert pendencias and pendencias[0]["playlist"] == "nova"
    assert (
        "resultado",
        "playlist_nao_encontrada",
        {
            "executou": False, "confirmado": False,
            "alvo_resolvido": "nova",
            "params_resolvidos": {"nome_playlist": "nova"},
        },
    ) in eventos


def test_playlist_existente_com_falha_de_player_nao_e_chamada_de_inexistente() -> None:
    eventos: list[tuple] = []
    pendencias: list[dict] = []

    executar_intencao_playlists(
        "PLAYLIST_PLAY",
        {"nome_playlist": "sendo sendo"},
        "coloca a playlit sendo sendo",
        "pc_a",
        {
            "_autonomia_permite_execucao_musical": lambda *_args: True,
            "set_playlist_sugestao_pendente": pendencias.append,
        },
        _dependencias(
            eventos,
            musica_leitura=_MusicaLeituraFake(
                conteudo={"ok": True, "name": "sendo sendo", "total": 9},
                total=9,
            ),
            musica_operacoes=_MusicaOperacoesFake(tocar=lambda _nome: False),
        ),
    )

    assert pendencias == []
    assert (
        "resultado", "falha_execucao", {
            "executou": False, "alvo_resolvido": "sendo sendo",
            "params_resolvidos": {"nome_playlist": "sendo sendo"},
        },
    ) in eventos
    assert any(
        evento[0] == "fala_status" and "existe" in evento[2].casefold()
        for evento in eventos
    )


def test_playlist_aberta_sem_confirmacao_preserva_sucesso_parcial() -> None:
    eventos: list[tuple] = []

    executar_intencao_playlists(
        "PLAYLIST_PLAY",
        {"nome_playlist": "sendo sendo"},
        "coloca a playlit sendo sendo",
        "pc_a",
        {"_autonomia_permite_execucao_musical": lambda *_args: True},
        _dependencias(
            eventos,
            musica_leitura=_MusicaLeituraFake(
                conteudo={"ok": True, "name": "sendo sendo", "total": 9},
                total=9,
            ),
            musica_operacoes=_MusicaOperacoesFake(
                tocar=lambda _nome: True,
                estado=lambda: {"status_avanco": "enviado_sem_confirmacao"},
            ),
        ),
    )

    assert (
        "resultado",
        "playlist_enviada_sem_confirmacao",
        {
            "executou": True, "alvo_resolvido": "sendo sendo",
            "params_resolvidos": {"nome_playlist": "sendo sendo"},
        },
    ) in eventos


def test_exclusao_bem_sucedida_limpa_ultima_playlist() -> None:
    eventos: list[tuple] = []

    executar_intencao_playlists(
        "PLAYLIST_DELETE",
        {"nome_playlist": "antiga"},
        "apaga a playlist antiga",
        "pc_a",
        {
            "delete_playlist": lambda _nome: True,
            "set_ultima_playlist": lambda nome: eventos.append(("ultima", nome)),
        },
        _dependencias(
            eventos,
            musica_operacoes=_MusicaOperacoesFake(
                apagar=lambda _nome: True,
                definir_ultima=lambda nome: eventos.append(("ultima", nome)),
            ),
        ),
    )

    assert ("ultima", "") in eventos
    assert (
        "resultado", "playlist_deletada", {
            "executou": True, "alvo_resolvido": "antiga",
            "params_resolvidos": {"nome_playlist": "antiga"},
        },
    ) in eventos


def test_roteador_principal_delega_adicao_da_faixa_viva() -> None:
    adicoes: list[tuple] = []
    estado = {
        "musica_atual_ts": time.time(),
        "musica_atual_status": "tocando",
        "musica_atual_url": "https://youtube.com/watch?v=atual",
        "musica_atual_titulo": "Atual",
    }

    retorno = executar_intencao(
        {"intent": "PLAYLIST_ADD", "params": {"nome_playlist": "rock"}},
        "coloca essa música na playlist rock",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_musica_estado_get": lambda chave, padrao=None: estado.get(chave, padrao),
            "ADD_TO_PLAYLIST": lambda *args: adicoes.append(args) or True,
            "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
            "falar_com_lipsync": lambda *_args: None,
            "_registro_musica_operacoes_runtime": _MusicaOperacoesFake(
                faixa=lambda: {
                    "url": estado["musica_atual_url"],
                    "title": estado["musica_atual_titulo"],
                    "canal": "",
                },
                adicionar=lambda *args: adicoes.append(args) or True,
            ),
        },
    )

    assert retorno is True
    assert adicoes == [(
        "rock", "https://youtube.com/watch?v=atual", "Atual", ""
    )]


def test_criacao_vazia_tem_intent_proprio_e_resultado_confirmado() -> None:
    detectado = detectar_playlist_usuario(
        "cria uma playlist chamada vmz",
        params_cb=lambda **kwargs: kwargs,
        limpar_nome_playlist=lambda valor: str(valor).strip().casefold(),
        extrair_nome_playlist=lambda _valor: "",
    )
    assert detectado == {
        "intent": "PLAYLIST_CREATE",
        "params": {"nome_playlist": "vmz"},
    }

    eventos: list[tuple] = []
    despacho = executar_intencao_playlists(
        "PLAYLIST_CREATE",
        {"nome_playlist": "vmz"},
        "cria uma playlist chamada VMZ",
        "pc_a",
        {"falar_com_lipsync": lambda *_args: None},
        _dependencias(
            eventos,
            musica_operacoes=_MusicaOperacoesFake(criar=lambda nome: {
                "ok": True, "criada": True, "status": "playlist_criada", "nome": nome,
            }),
        ),
    )
    assert despacho == ResultadoDespacho.concluido(True)
    assert (
        "resultado", "playlist_criada", {
            "executou": True,
            "confirmado": True,
            "alvo_resolvido": "vmz",
            "params_resolvidos": {"nome_playlist": "vmz"},
        },
    ) in eventos


def test_referencias_curtas_usam_playlist_ativa_sem_adivinhar() -> None:
    kwargs = {
        "params_cb": lambda **params: params,
        "limpar_nome_playlist": lambda valor: str(valor).strip(),
        "ultima_playlist": "sendo sendo",
    }
    assert detectar_playlist_contextual_musica_atual(
        "essa também", **kwargs,
    ) == {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "sendo sendo", "referencia_contextual": True},
    }
    assert detectar_playlist_contextual_musica_atual(
        "o que tem nela?", **kwargs,
    ) == {
        "intent": "PLAYLIST_LIST",
        "params": {"nome_playlist": "sendo sendo", "referencia_contextual": True},
    }


def test_alvo_resolvido_do_executor_alimenta_continuidade_aditiva_real() -> None:
    estado: dict = {}

    def registrar(contrato, texto, executou, **kwargs):
        nonlocal estado
        estado = registrar_resultado_execucao(
            estado, contrato, texto, executou, **kwargs,
        )

    adaptador = AdaptadorResultadoOperacional(
        {"intent": "PLAYLIST_ADD"}, {},
        "coloca essa música na playlist sendo sendo", "pc_a",
        {"_registrar_resultado_execucao": registrar},
    )
    adaptador.marcar_resultado(
        "playlist_musica_adicionada",
        True,
        confirmado=True,
        alvo_resolvido="sendo sendo",
        params_resolvidos={"nome_playlist": "sendo sendo"},
    )

    assert estado["ultima_acao_alvo"] == "sendo sendo"
    assert resolver_continuacao_aditiva(estado, texto="essa também") == {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "sendo sendo", "referencia_contextual": True},
    }
