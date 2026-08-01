from __future__ import annotations

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_musical import (
    DependenciasExecutorMusical,
    executar_intencao_musical,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from tests.fakes_navegador import NavegadorOperacoesFake


def _dependencias(
    eventos: list[tuple], abrir=lambda *_args, **_kwargs: True,
    musica_operacoes=None,
):
    return DependenciasExecutorMusical(
        marcar_resultado=lambda status, **kwargs: eventos.append(("resultado", status, kwargs)),
        abrir_url_musical=abrir,
        musica_operacoes=musica_operacoes,
    )


class _MusicaOperacoesFake:
    def __init__(self, copiar, definir=lambda _nome: None):
        self._copiar = copiar
        self._definir = definir

    def copiar_curadoria(self, origem, musica, destino):
        return dict(self._copiar(origem, musica, destino) or {})

    def definir_ultima_playlist(self, nome):
        self._definir(nome)


class _MusicaLeituraFake:
    def __init__(self, listar):
        self._listar = listar

    def listar_laylay(self, nome=""):
        return self._listar(nome)


def test_executor_musical_nao_interfere_em_playlist_local() -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_musical(
        "PLAYLIST_PLAY", {}, "toca rock", {}, _dependencias(eventos)
    )

    assert despacho == ResultadoDespacho.nao_tratado()
    assert eventos == []


def test_music_search_sem_autorizacao_nao_abre_nada() -> None:
    eventos: list[tuple] = []
    aberturas: list[tuple] = []

    despacho = executar_intencao_musical(
        "MUSIC_SEARCH",
        {"query": "Duality"},
        "gosto de Duality",
        {"_autonomia_permite_execucao_musical": lambda *_args, **_kwargs: False},
        _dependencias(eventos, abrir=lambda *args, **kwargs: aberturas.append((args, kwargs))),
    )

    assert despacho.tratado is True
    assert despacho.retorno is False
    assert aberturas == []
    assert eventos == []


def test_music_search_com_link_direto_nao_repassa_query_ao_navegador() -> None:
    eventos: list[tuple] = []
    aberturas: list[tuple] = []
    url = "https://www.youtube.com/watch?v=abc"

    despacho = executar_intencao_musical(
        "MUSIC_SEARCH",
        {"query": "Duality"},
        "toca Duality",
        {
            "_autonomia_permite_execucao_musical": lambda *_args, **_kwargs: True,
            "_buscar_primeiro_video_youtube": lambda _query: url,
        },
        _dependencias(
            eventos,
            abrir=lambda alvo, **kwargs: aberturas.append((alvo, kwargs)) or True,
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert aberturas == [(url, {"query": ""})]
    assert eventos == [("resultado", "musica_aberta", {"executou": True})]


def test_music_search_por_estilo_refina_query_e_abre_busca() -> None:
    eventos: list[tuple] = []
    aberturas: list[tuple] = []

    despacho = executar_intencao_musical(
        "MUSIC_SEARCH",
        {"query": "rock pesado"},
        "coloca um rock pesado",
        {
            "_autonomia_permite_execucao_musical": lambda *_args, **_kwargs: True,
            "_normalizar_query_musical": lambda query: query,
            "_resolver_query_musical_por_estilo": lambda *_args: {
                "query": "heavy metal mix"
            },
            "_buscar_primeiro_video_youtube": lambda _query: "",
        },
        _dependencias(
            eventos,
            abrir=lambda url, **kwargs: aberturas.append((url, kwargs)) or True,
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert "heavy+metal+mix" in aberturas[0][0]
    assert aberturas[0][1] == {"query": "heavy metal mix"}


def test_music_search_contextual_usa_faixa_curada_em_vez_da_frase_literal() -> None:
    eventos: list[tuple] = []
    consultas: list[tuple[str, str]] = []
    url = "https://www.youtube.com/watch?v=minecraft01"

    despacho = executar_intencao_musical(
        "MUSIC_SEARCH",
        {
            "query": "musica boa para jogar minecraft",
            "genre": "ambient",
            "mood": "calmo",
            "context": "jogando minecraft",
        },
        "coloca uma musica boa para jogar minecraft",
        {
            "_autonomia_permite_execucao_musical": lambda *_args, **_kwargs: True,
            "_normalizar_query_musical": lambda query: query,
            "_resolver_query_musical_por_estilo": (
                lambda query, texto, params: {
                    "query": "C418 - Sweden Minecraft Volume Alpha",
                    "origem": "contexto_curado",
                    "tipo_resultado": "faixa",
                }
            ),
            "_buscar_primeiro_video_youtube": (
                lambda query, *, tipo_resultado: consultas.append((query, tipo_resultado)) or url
            ),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert consultas == [("C418 - Sweden Minecraft Volume Alpha", "faixa")]


def test_music_search_generico_pede_alvo_e_registra_esclarecimento() -> None:
    eventos: list[tuple] = []
    registros: list[tuple] = []
    falas: list[str] = []

    despacho = executar_intencao_musical(
        "MUSIC_SEARCH",
        {"query": "uma musica"},
        "coloca uma música",
        {
            "_autonomia_permite_execucao_musical": lambda *_args, **_kwargs: True,
            "_normalizar_query_musical": lambda _query: "",
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        DependenciasExecutorMusical(
            marcar_resultado=lambda status, **kwargs: eventos.append((status, kwargs)),
            abrir_url_musical=lambda *_args, **_kwargs: False,
            registrar_mente=lambda *args: registros.append(args),
        ),
    )

    assert despacho == ResultadoDespacho.concluido(False)
    assert eventos == [("alvo_ausente", {"executou": False})]
    assert falas
    assert registros[0][0] == "coloca uma música"
    assert registros[0][2] == "MUSIC_SEARCH"


def test_listagem_da_curadoria_repassa_nome_especifico() -> None:
    eventos: list[tuple] = []
    nomes: list[str] = []
    falas: list[str] = []

    despacho = executar_intencao_musical(
        "LAYLAY_PLAYLIST_LIST",
        {"nome_playlist": "metal"},
        "o que tem na sua playlist metal",
        {
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        DependenciasExecutorMusical(
            marcar_resultado=lambda status, **kwargs: eventos.append(
                ("resultado", status, kwargs)
            ),
            abrir_url_musical=lambda *_args, **_kwargs: True,
            musica_leitura=_MusicaLeituraFake(
                lambda nome: nomes.append(nome) or "Minha seleção metal."
            ),
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert nomes == ["metal"]
    assert falas == ["Minha seleção metal."]


def test_copia_da_curadoria_atualiza_ultima_playlist() -> None:
    eventos: list[tuple] = []
    ultimas: list[str] = []
    chamadas: list[tuple] = []

    despacho = executar_intencao_musical(
        "LAYLAY_PLAYLIST_COPY",
        {"musica": "Duality", "origem": "metal", "destino": "rock"},
        "copia Duality da sua metal para minha rock",
        {
            "_copiar_faixa_da_playlist_laylay": lambda *args: chamadas.append(args) or {
                "ok": True,
                "faixa": {"titulo": "Duality - Slipknot"},
            },
            "set_ultima_playlist": ultimas.append,
            "falar_com_lipsync": lambda *_args: None,
        },
        _dependencias(
            eventos,
            musica_operacoes=_MusicaOperacoesFake(
                lambda *args: chamadas.append(args) or {
                    "ok": True,
                    "faixa": {"titulo": "Duality - Slipknot"},
                },
                definir=ultimas.append,
            ),
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert chamadas == [("metal", "Duality", "rock")]
    assert ultimas == ["rock"]
    assert eventos == [(
        "resultado", "playlist_musica_adicionada", {"executou": True}
    )]


def test_copia_inexistente_registra_nao_encontrado() -> None:
    eventos: list[tuple] = []

    executar_intencao_musical(
        "LAYLAY_PLAYLIST_COPY",
        {"musica": "Inexistente", "origem": "metal", "destino": "rock"},
        "copia a música",
        {"_copiar_faixa_da_playlist_laylay": lambda *_args: {"ok": False}},
        _dependencias(
            eventos,
            musica_operacoes=_MusicaOperacoesFake(
                lambda *_args: {"ok": False}
            ),
        ),
    )

    assert eventos == [("resultado", "nao_encontrado", {"executou": False})]


def test_copia_normaliza_retorno_legado_malformado_sem_quebrar_turno() -> None:
    eventos: list[tuple] = []
    ultimas: list[str] = []

    class _OperacoesLegadas:
        def copiar_curadoria(self, *_args):
            return True

        def definir_ultima_playlist(self, nome):
            ultimas.append(nome)

    despacho = executar_intencao_musical(
        "LAYLAY_PLAYLIST_COPY",
        {"musica": "Duality", "origem": "metal", "destino": "rock"},
        "copia essa música",
        {"falar_com_lipsync": lambda *_args: None},
        _dependencias(eventos, musica_operacoes=_OperacoesLegadas()),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert ultimas == ["rock"]
    assert eventos == [(
        "resultado", "playlist_musica_adicionada", {"executou": True}
    )]


def test_roteador_principal_delega_music_search_ao_executor_musical() -> None:
    comandos: list[tuple] = []
    navegador = NavegadorOperacoesFake()
    resultados = []

    retorno = executar_intencao(
        {"intent": "MUSIC_SEARCH", "params": {"query": "Duality"}},
        "toca Duality",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_autonomia_permite_execucao_musical": lambda *_args, **_kwargs: True,
            "_normalizar_query_musical": lambda query: query,
            "_buscar_primeiro_video_youtube": lambda _query: "",
            "_registro_navegador_operacoes_runtime": navegador,
            "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: resultados.append(
                contrato
            ),
            "falar_com_lipsync": lambda *_args: None,
        },
    )

    assert retorno is True
    comandos.extend(navegador.chamadas)
    assert comandos and comandos[0][0] == "youtube_search"
    assert resultados and resultados[0].status == "musica_aberta"
