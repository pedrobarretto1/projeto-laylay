from __future__ import annotations

import time

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_playlists import (
    DependenciasExecutorPlaylists,
    executar_intencao_playlists,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao


class _MusicaLeituraFake:
    def __init__(self, *, lista="Sem playlists.", conteudo=None, total=0):
        self.lista = lista
        self.conteudo = conteudo or {"ok": False, "name": "", "total": 0}
        self.total = total

    def listar_usuario(self): return self.lista
    def consultar_usuario(self, _nome): return dict(self.conteudo)
    def contar_usuario(self, _nome): return self.total


def _dependencias(
    eventos: list[tuple], abrir=lambda *_args, **_kwargs: True,
    musica_leitura=None,
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
    )


def test_executor_playlists_nao_interfere_em_outro_dominio() -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_playlists(
        "MUSIC_SEARCH", {}, "toca Duality", "pc_a", {}, _dependencias(eventos)
    )

    assert despacho == ResultadoDespacho.nao_tratado()
    assert eventos == []


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
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert adicoes == [(
        "rock",
        "https://www.youtube.com/watch?v=player",
        "Duality (Official Video)",
        "",
    )]
    assert ("ultima", "rock") in eventos
    assert ("resultado", "playlist_musica_adicionada", {"executou": True}) in eventos


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
        _dependencias([]),
    )

    assert adicoes == [
        ("vibes", "https://www.youtube.com/watch?v=nova", "Nova", "Canal")
    ]


def test_nome_explicito_incompleto_nao_usa_ultima_playlist() -> None:
    falas: list[str] = []

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
        _dependencias([]),
    )

    assert despacho == ResultadoDespacho.concluido()
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
        _dependencias([], musica_leitura=_MusicaLeituraFake(conteudo={
            "ok": True, "name": "Rock", "total": 3,
        })),
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
        _dependencias(eventos, musica_leitura=_MusicaLeituraFake(total=3)),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert chamadas == ["rock"]
    assert ("ultima", "rock") in eventos
    assert ("resultado", "playlist_aberta", {"executou": True}) in eventos


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
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert aberturas == ["https://www.youtube.com/watch?v=shuffle"]
    assert urls == aberturas
    assert ("resultado", "playlist_aberta", {"executou": True}) in eventos


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
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert aberturas == ["https://youtube.com/watch?v=anime"]
    assert ("resultado", "playlist_aberta_pc_b", {"executou": True}) in eventos


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
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert pendencias and pendencias[0]["playlist"] == "nova"
    assert ("resultado", "falha_execucao", {"executou": False}) in eventos


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
        _dependencias(eventos),
    )

    assert ("ultima", "") in eventos
    assert ("resultado", "playlist_deletada", {"executou": True}) in eventos


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
        },
    )

    assert retorno is True
    assert adicoes == [(
        "rock", "https://youtube.com/watch?v=atual", "Atual", ""
    )]
