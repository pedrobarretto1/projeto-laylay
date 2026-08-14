from __future__ import annotations

import json
import time

from mente_laylay.autonomia.comandos_imediatos import (
    ComandosImediatosRuntime,
    texto_pede_continuacao_musical_curta,
)
from mente_laylay.autonomia.orquestrador_deterministico import (
    DeteccaoDeterministicaRuntime,
)
from mente_laylay.memoria_mental.contexto_imediato import ContextoImediatoRuntime
from mente_laylay.memoria_mental.mapa_recursos import MapaRecursosRuntime
from mente_laylay.memoria_mental.playlist_laylay_runtime import PlaylistLaylayRuntime


def _namespace_deteccao(
    mapa: MapaRecursosRuntime,
    *,
    detectar_nome_laylay=None,
) -> dict:
    return {
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold().strip(),
        "_texto_conversa_casual_sem_acao": lambda _texto: False,
        "_texto_bloqueia_playlist_agora": lambda _texto: False,
        "_texto_social_curto": lambda _texto: False,
        "_ignorar_token_solto": lambda _texto: False,
        "_fluxo_prioritario_da_ia": lambda _texto: False,
        "_texto_expresso_melhor_no_deterministico": lambda _texto: True,
        "_texto_depende_de_contexto": lambda _texto: False,
        "_limpar_destino_pc_b": lambda texto: texto,
        "_target_from_params": lambda _params, _texto: "pc_a",
        "_limpar_nome_playlist": lambda texto: str(texto).strip(" .?!"),
        "_musica_estado_get": lambda _chave: "",
        "_contexto_musical_ativo": lambda: False,
        "extrair_nome_playlist": lambda _texto: "",
        "_detectar_intencao_abrir_app": lambda _texto: None,
        "_detectar_playlist_nome_direto": lambda _texto: "",
        "_detectar_playlist_laylay_nome_direto": detectar_nome_laylay,
        "_normalizar_query_musical": lambda texto: str(texto).strip(),
        "_detectar_sugestao_indireta": lambda *_args: None,
        "_resolver_consulta_recurso_local": mapa.resolver_consulta,
    }


def _mapa_playlist_generica() -> MapaRecursosRuntime:
    mapa = MapaRecursosRuntime()
    mapa.registrar(
        "playlists_usuario",
        arquivo="playlists.json",
        descricao="playlists do usuário",
        termos=("playlist", "playlists"),
        leitor=lambda _texto: {"playlists": [{"nome": "rock", "total": 3}]},
        intent_consulta="PLAYLIST_LIST",
    )
    return mapa


def test_fluxo_real_preserva_posse_e_ordinal_antes_do_recurso_generico() -> None:
    mapa = _mapa_playlist_generica()
    estado: dict = {}
    runtime = DeteccaoDeterministicaRuntime(
        namespace_getter=lambda: _namespace_deteccao(mapa),
        estado_getter=lambda: estado,
        sites_diretos={},
        apps_map={},
    )

    assert runtime.detectar("O que tem na sua primeira playlist?") == {
        "intent": "LAYLAY_PLAYLIST_LIST",
        "params": {"nome_playlist": "#1"},
    }
    assert runtime.detectar("Toca a sua primeira playlist.") == {
        "intent": "LAYLAY_PLAYLIST_PLAY",
        "params": {"nome_playlist": "#1"},
    }


def test_desejo_imediato_de_abrir_opera_nao_vira_busca_musical() -> None:
    mapa = _mapa_playlist_generica()
    namespace = _namespace_deteccao(mapa)
    namespace["_normalizar_texto_com_apelidos"] = (
        lambda texto: str(texto).casefold().strip().rstrip(".")
    )
    namespace["_contexto_musical_ativo"] = lambda: True
    namespace["_extrair_intencao_abrir_app"] = lambda texto: (
        {"intent": "APP_OPEN", "params": {"nome_app": "opera"}}
        if str(texto).casefold().strip(" .") == "abre opera"
        else None
    )
    runtime = DeteccaoDeterministicaRuntime(
        namespace_getter=lambda: namespace,
        estado_getter=lambda: {
            "ultima_acao_intent": "MUSIC_SEARCH",
            "ultima_habilidade": "musica",
        },
        sites_diretos={},
        apps_map={"opera": "opera"},
    )

    assert runtime.detectar(
        "Eu queria que o Opera estivesse aberto agora.",
    ) == {
        "intent": "APP_OPEN",
        "params": {"nome_app": "opera"},
    }


def test_porta_prioritaria_executa_primeira_curadoria_sem_cair_na_conversa() -> None:
    estado = _EstadoMusical()
    mapa = _mapa_playlist_generica()
    detector = DeteccaoDeterministicaRuntime(
        namespace_getter=lambda: _namespace_deteccao(mapa),
        estado_getter=lambda: estado.mental,
        sites_diretos={},
        apps_map={},
    )
    execucoes: list[dict] = []
    registros: list[tuple[dict, bool, str]] = []
    imediato = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "detectar_intencao_deterministica": detector.detectar,
            "executar_intencao": (
                lambda intencao, _texto: execucoes.append(intencao) or True
            ),
            "_registrar_resultado_execucao": (
                lambda intencao, _texto, executou, *, origem, **_kwargs:
                registros.append((intencao, executou, origem))
            ),
        },
        loop_getter=lambda: None,
    )

    assert imediato.processar_prioritarios("Toca a sua primeira playlist") is True
    assert execucoes == [{
        "intent": "LAYLAY_PLAYLIST_PLAY",
        "params": {"nome_playlist": "#1"},
    }]
    assert registros == [(
        execucoes[0], True, "prioritario_curadoria_laylay",
    )]


def test_nome_manual_da_curadoria_continua_no_catalogo_real(tmp_path) -> None:
    arquivo = tmp_path / "playlists_da_laylay.json"
    arquivo.write_text(json.dumps({
        "climas_que_combinam_com_voce": [{
            "titulo": "C418 - Sweden",
            "url": "https://www.youtube.com/watch?v=a",
            "canal": "C418",
        }],
        "xodos_que_eu_seperei": [{
            "titulo": "Nirvana - Come As You Are",
            "url": "https://www.youtube.com/watch?v=b",
            "canal": "Nirvana",
        }],
    }), encoding="utf-8")
    curadoria = PlaylistLaylayRuntime(
        state_file=str(arquivo),
        cache={},
        playlists_usuario_getter=lambda: {},
        historico_musical_getter=lambda: {},
        adicionar_playlist_usuario=lambda *_args: {"ok": True},
    )
    mapa = _mapa_playlist_generica()
    estado = {
        "ultima_acao_intent": "LAYLAY_PLAYLIST_LIST",
        "ultima_acao_alvo": "#1",
    }
    runtime = DeteccaoDeterministicaRuntime(
        namespace_getter=lambda: _namespace_deteccao(
            mapa,
            detectar_nome_laylay=curadoria.detectar_nome_direto_contextual,
        ),
        estado_getter=lambda: estado,
        sites_diretos={},
        apps_map={},
    )

    assert curadoria.detectar_nome_direto_contextual(
        "climas que combinam com voce"
    ) == "climas que combinam com você"
    assert runtime.detectar("climas que combinam com voce") == {
        "intent": "LAYLAY_PLAYLIST_LIST",
        "params": {
            "nome_playlist": "climas que combinam com você",
            "referencia_contextual": True,
        },
    }
    assert curadoria.selecionar("#1")["faixa"]["titulo"] == "C418 - Sweden"


class _EstadoMusical:
    def __init__(self) -> None:
        self.mental: dict = {}


def test_continuacoes_musicais_passam_pelo_resolvedor_e_executor_reais() -> None:
    estado = _EstadoMusical()
    estado.mental = {
        "ultima_acao_intent": "MUSIC_SEARCH",
        "ultima_acao_params": {"query": "musica para trabalhar"},
        "ultima_acao_alvo": "Tycho - Awake",
        "ultima_habilidade": "musica",
        "ts": time.time(),
    }
    contexto = ContextoImediatoRuntime(
        estado_runtime_getter=lambda: estado,
        servicos_iniciais={
            "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold().strip(),
            "_contexto_musical_ativo": lambda: True,
        },
    )
    execucoes: list[tuple[dict, str]] = []
    registros: list[tuple[dict, str, bool, str]] = []
    namespace = {
        "_estado_compartilhado_runtime": estado,
        "processar_comandos_em_cadeia": lambda *_args: False,
        "_resolver_comando_midia_contextual_forcado": contexto.resolver_midia,
        "executar_intencao": lambda intent, texto: execucoes.append((intent, texto)) or True,
        "_registrar_resultado_execucao": (
            lambda intent, texto, executou, *, origem, **_kwargs:
            registros.append((intent, texto, executou, origem))
        ),
    }
    imediato = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert imediato.processar_prioritarios("Tenta outra.") is True
    assert execucoes[-1][0]["intent"] == "MUSIC_SEARCH"
    assert execucoes[-1][0]["params"]["origem"] == "continuacao_busca"

    estado.mental = {
        "ultima_acao_intent": "MEDIA_CONTROL",
        "ultima_acao_params": {"acao": "pause", "platform": "music"},
        "ultima_acao_status": "falha_execucao",
        "ultima_habilidade": "musica",
        "ts": time.time(),
    }
    assert imediato.processar_prioritarios("Continua") is True
    assert execucoes[-1] == ({
        "intent": "MEDIA_CONTROL",
        "params": {"acao": "play", "platform": "music"},
    }, "Continua")
    assert registros[-1][3] == "prioritario_continuidade_musical"


def test_agradecimento_nao_reabre_continuacao_musical() -> None:
    estado = _EstadoMusical()
    estado.mental = {
        "ultima_acao_intent": "MUSIC_SEARCH",
        "ultima_acao_params": {"query": "Tycho - Awake"},
        "ultima_habilidade": "musica",
        "ts": time.time(),
    }
    contexto = ContextoImediatoRuntime(
        estado_runtime_getter=lambda: estado,
        servicos_iniciais={
            "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold().strip(),
            "_contexto_musical_ativo": lambda: True,
        },
    )

    assert texto_pede_continuacao_musical_curta("Obrigado, Lay") is False
    assert contexto.resolver_midia("Obrigado, Lay") is None
