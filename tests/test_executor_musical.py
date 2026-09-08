from __future__ import annotations

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_musical import (
    DependenciasExecutorMusical,
    executar_intencao_musical,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.autonomia.porteiro_acoes import autorizar_acao_pratica
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
    assert eventos == [(
        "resultado", "musica_reproduzindo", {
            "executou": True,
            "confirmado": True,
            "detalhe": "confirmacao_legada",
        },
    )]


def test_music_search_modal_infinitivo_atravessa_porteiro_e_executor() -> None:
    eventos: list[tuple] = []
    aberturas: list[tuple] = []
    url = "https://www.youtube.com/watch?v=glimpse01"

    despacho = executar_intencao_musical(
        "MUSIC_SEARCH",
        {"query": "glimpse of us"},
        "pode colocar glimpse of us",
        {
            "_autonomia_permite_execucao_musical": (
                lambda intent, texto, confirmado=False: autorizar_acao_pratica(
                    intent,
                    texto,
                    {},
                    confirmado=confirmado,
                )["permitido"]
            ),
            "_buscar_primeiro_video_youtube": lambda _query: url,
        },
        _dependencias(
            eventos,
            abrir=lambda alvo, **kwargs: aberturas.append((alvo, kwargs)) or True,
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert aberturas == [(url, {"query": ""})]
    assert eventos == [(
        "resultado", "musica_reproduzindo", {
            "executou": True,
            "confirmado": True,
            "detalhe": "confirmacao_legada",
        },
    )]


def test_fala_musical_limpa_metadados_sem_apagar_identidade_do_receipt() -> None:
    eventos: list[tuple] = []
    falas: list[tuple] = []
    titulo_bruto = (
        "Shiny - Vazio Constante | Bojack, Rick & Clancy | "
        "Ft. @AniRap & @AnnyTHN"
    )
    params = {"query": "vazio constante shiny sz"}

    despacho = executar_intencao_musical(
        "MUSIC_SEARCH",
        params,
        "coloca vazio constante shiny_sz",
        {
            "_autonomia_permite_execucao_musical": lambda *_a, **_k: True,
            "_resolver_primeiro_video_youtube": lambda *_a, **_k: {
                "url": "https://www.youtube.com/watch?v=JTq0Ut6XJzs",
                "title": titulo_bruto,
                "channel": "Shiny_sz",
            },
        },
        DependenciasExecutorMusical(
            marcar_resultado=lambda status, **kwargs: eventos.append(
                (status, kwargs)
            ),
            abrir_url_musical=lambda *_a, **_k: {
                "ok": True,
                "confirmado": True,
                "status": "playing_confirmed",
            },
            falar_por_status=lambda status, fala, **kwargs: falas.append(
                (status, fala, kwargs)
            ),
        ),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert params["alvo_executado"] == titulo_bruto
    assert params["alvo_apresentado"] == "Shiny - Vazio Constante"
    assert falas[0][2]["alvo"] == "Shiny - Vazio Constante"
    assert "Bojack" not in falas[0][1]
    assert "@AniRap" not in falas[0][1]


def test_music_search_video_aberto_nao_e_reportado_como_falha() -> None:
    eventos: list[tuple] = []
    falas: list[tuple] = []
    url = "https://www.youtube.com/watch?v=minecraft01"

    despacho = executar_intencao_musical(
        "MUSIC_SEARCH",
        {"query": "musica para jogar minecraft"},
        "coloca uma música para jogar Minecraft",
        {
            "_autonomia_permite_execucao_musical": lambda *_args, **_kwargs: True,
            "_resolver_query_musical_por_estilo": lambda *_args: {
                "query": "C418 - Sweden Minecraft Volume Alpha",
                "tipo_resultado": "faixa",
            },
            "_resolver_primeiro_video_youtube": lambda *_args, **_kwargs: {
                "url": url, "title": "C418 - Sweden - Minecraft Volume Alpha",
            },
        },
        DependenciasExecutorMusical(
            marcar_resultado=lambda status, **kwargs: eventos.append(
                ("resultado", status, kwargs)
            ),
            abrir_url_musical=lambda *_args, **_kwargs: {
                "ok": True,
                "confirmado": None,
                "status": "video_aberto_sem_confirmacao",
            },
            falar_por_status=lambda status, fala, **kwargs: falas.append(
                (status, fala, kwargs)
            ),
        ),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert eventos == [(
        "resultado", "musica_enviada_sem_confirmacao", {
            "executou": True,
            "confirmado": None,
            "detalhe": "video_aberto_sem_confirmacao",
        },
    )]
    assert falas and falas[0][0] == "musica_enviada_sem_confirmacao"
    fala = falas[0][1].casefold()
    assert "abri" in fala
    assert "não vou fingir" in fala


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
            "_resolver_primeiro_video_youtube": lambda _query: {
                "url": "https://www.youtube.com/watch?v=heavymetal01",
                "title": "Heavy Metal Mix",
            },
        },
        _dependencias(
            eventos,
            abrir=lambda url, **kwargs: aberturas.append((url, kwargs)) or True,
        ),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert aberturas == [(
        "https://www.youtube.com/watch?v=heavymetal01", {"query": ""},
    )]


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


def test_reproducao_da_curadoria_preserva_autoria_e_evidencia() -> None:
    eventos: list[tuple] = []
    falas: list[tuple] = []
    aberturas: list[str] = []

    class _CuradoriaOperacoes:
        def selecionar_curadoria(self, nome="", indice_faixa=0):
            assert nome == "#1"
            assert indice_faixa == 0
            return {
                "ok": True,
                "playlist": "climas que combinam com você",
                "faixa": {
                    "url": "https://www.youtube.com/watch?v=mine",
                    "titulo": "C418 - Sweden",
                },
            }

    despacho = executar_intencao_musical(
        "LAYLAY_PLAYLIST_PLAY",
        {"nome_playlist": "#1"},
        "toca a sua primeira playlist",
        {},
        DependenciasExecutorMusical(
            marcar_resultado=lambda status, **kwargs: eventos.append((status, kwargs)),
            abrir_url_musical=lambda url, **_kwargs: aberturas.append(url) or {
                "ok": True, "confirmado": True, "status": "playing_confirmed",
            },
            falar_por_status=lambda status, fala, **kwargs: falas.append(
                (status, fala, kwargs)
            ),
            musica_operacoes=_CuradoriaOperacoes(),
        ),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert aberturas == ["https://www.youtube.com/watch?v=mine"]
    assert eventos[0][0] == "playlist_laylay_reproduzindo"
    assert eventos[0][1]["alvo_resolvido"] == "climas que combinam com você"
    assert "minha playlist" in falas[0][1].casefold()


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
            "_resolver_primeiro_video_youtube": lambda _query: {
                "url": "https://www.youtube.com/watch?v=duality0001",
                "title": "Slipknot - Duality [OFFICIAL VIDEO]",
            },
            "_registro_navegador_operacoes_runtime": navegador,
            "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: resultados.append(
                contrato
            ),
            "falar_com_lipsync": lambda *_args: None,
        },
    )

    assert retorno is True
    comandos.extend(navegador.chamadas)
    assert comandos and comandos[0][0] == "youtube_play"
    assert resultados and resultados[0].status == "musica_reproduzindo"
