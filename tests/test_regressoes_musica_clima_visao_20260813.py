from __future__ import annotations

from mente_laylay.autonomia.comandos_imediatos import (
    texto_pede_continuacao_musical_curta,
)
from mente_laylay.autonomia.controle_midia import executar_media_control
from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_informacoes import (
    DependenciasExecutorInformacoes,
    executar_intencao_informacoes,
)
from mente_laylay.autonomia.executor_integracoes import (
    DependenciasExecutorIntegracoes,
    executar_intencao_integracoes,
)
from mente_laylay.autonomia.executor_playlists import (
    DependenciasExecutorPlaylists,
    executar_intencao_playlists,
)
from mente_laylay.autonomia.executor_sistema import (
    DependenciasExecutorSistema,
    executar_intencao_sistema,
)
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_clima,
    detectar_url_visual,
    detectar_volume_ou_midia,
)
from mente_laylay.cognicao.memoria_visual import MemoriaVisualRuntime
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime
from mente_laylay.percepcao.ambiente_sistema import (
    obter_clima_localidade,
    obter_clima_open_meteo,
)
from mente_laylay.especialistas.capacidades import (
    INTENTS_SOMENTE_LEITURA,
    intents_registradas,
)
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.cognicao.retrato_turno import dominio_intent


def _params(**kwargs):
    return kwargs


def _contexto_deterministico(*, musica_ativa: bool = False) -> dict:
    from mente_laylay.autonomia.roteador_deterministico import (
        texto_expresso_melhor_no_deterministico,
    )

    return {
        "normalizar_texto": normalizar_texto,
        "texto_conversa_casual_sem_acao": lambda _texto: True,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: True,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: True,
        "texto_expresso_melhor_no_deterministico": lambda texto: (
            texto_expresso_melhor_no_deterministico(
                texto, normalizar_texto=normalizar_texto,
            )
        ),
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda _params, _texto: "pc_a",
        "detectar_intencao_iot": lambda *_args: None,
        "detectar_sugestao_indireta": lambda *_args: None,
        "resolver_consulta_recurso_local": lambda _texto: None,
        "contexto_musical_ativo": lambda: musica_ativa,
        "mente_integrada_estado": {},
        "sites_diretos": {},
        "apps_map": {},
    }


def test_consulta_da_musica_atual_e_somente_leitura_e_nunca_replay() -> None:
    comando = detectar_volume_ou_midia(
        "qual música está tocando?",
        params_cb=_params,
        contexto_musical_ativo=True,
    )
    assert comando == {
        "intent": "MUSIC_STATUS",
        "params": {
            "acao": "status",
            "platform": "music",
            "somente_leitura": True,
        },
    }

    falas: list[str] = []
    resultados: list[tuple] = []

    class Leitura:
        @staticmethod
        def estado():
            return {
                "musica_atual_titulo": "(3) Duality (Official Video) - YouTube",
                "musica_atual_status": "tocando",
            }

    def nao_pode_mutar(*_args, **_kwargs):
        raise AssertionError("consulta de faixa não pode controlar o player")

    ok = executar_media_control(
        comando["params"],
        "Qual música está tocando?",
        "pc_a",
        {
            "_registro_musica_leitura_runtime": Leitura(),
            "_executar_controle_midia_nativo": nao_pode_mutar,
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        marcar_resultado=lambda status, *args, **kwargs: resultados.append(
            (status, args, kwargs)
        ),
        falar_por_status=lambda *_args, **_kwargs: None,
        ctx_fala=lambda: {},
    )

    assert ok is True
    assert falas == ["Está tocando Duality."]
    assert resultados[0][0] == "midia_status_consultado"
    assert resultados[0][2]["confirmado"] is True


def test_music_status_esta_registrado_e_chega_ao_executor_tipado() -> None:
    assert "MUSIC_STATUS" in intents_registradas()
    assert "MUSIC_STATUS" in INTENTS_SOMENTE_LEITURA
    assert dominio_intent("MUSIC_STATUS") == "musica"
    falas: list[str] = []
    resultados: list[tuple] = []

    class Leitura:
        @staticmethod
        def estado():
            return {
                "musica_atual_titulo": "Sweden - YouTube",
                "musica_atual_status": "tocando",
            }

    despacho = executar_intencao_integracoes(
        "MUSIC_STATUS",
        {"intent": "MUSIC_STATUS", "params": {"acao": "status"}},
        {"acao": "status", "somente_leitura": True},
        "Qual música está tocando?",
        "pc_a",
        {
            "_registro_musica_leitura_runtime": Leitura(),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        DependenciasExecutorIntegracoes(
            marcar_resultado=lambda status, *args, **kwargs: resultados.append(
                (status, args, kwargs)
            ),
            falar_por_status=lambda *_args, **_kwargs: None,
            contexto_fala=lambda: {},
        ),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert falas == ["Está tocando Sweden."]
    assert resultados[0][0] == "midia_status_consultado"


def test_music_status_e_clima_amanha_atravessam_o_roteador_principal() -> None:
    contexto = _contexto_deterministico(musica_ativa=True)
    assert detectar_intencao_deterministica_mente(
        "Qual música está tocando?", contexto,
    ) == {
        "intent": "MUSIC_STATUS",
        "params": {
            "acao": "status",
            "platform": "music",
            "somente_leitura": True,
        },
    }
    assert detectar_intencao_deterministica_mente(
        "Como estará o tempo amanhã?", contexto,
    ) == {"intent": "WEATHER", "params": {"day_offset": 1}}
    assert detectar_intencao_deterministica_mente(
        "Próxima.", contexto,
    ) == {"intent": "MEDIA_CONTROL", "params": {"acao": "next"}}
    assert detectar_intencao_deterministica_mente(
        "Volta para a anterior.", contexto,
    ) == {"intent": "MEDIA_CONTROL", "params": {"acao": "prev"}}


def test_proxima_e_anterior_curtas_exigem_contexto_musical() -> None:
    assert texto_pede_continuacao_musical_curta("Próxima.") is True
    assert texto_pede_continuacao_musical_curta("Volta para a anterior.") is True
    assert detectar_volume_ou_midia(
        "próxima", params_cb=_params, contexto_musical_ativo=True,
    ) == {"intent": "MEDIA_CONTROL", "params": {"acao": "next"}}
    assert detectar_volume_ou_midia(
        "volta para a anterior", params_cb=_params, contexto_musical_ativo=True,
    ) == {"intent": "MEDIA_CONTROL", "params": {"acao": "prev"}}
    assert detectar_volume_ou_midia(
        "próxima", params_cb=_params, contexto_musical_ativo=False,
    ) is None
    assert detectar_volume_ou_midia(
        "volta para a anterior", params_cb=_params, contexto_musical_ativo=False,
    ) is None


def test_playlist_add_repetido_preserva_uma_copia_e_expoe_idempotencia(tmp_path) -> None:
    runtime = PlaylistRuntime(
        state_file=str(tmp_path / "playlists.json"),
        legacy_file=str(tmp_path / "legacy.json"),
        cache={},
        ultima_playlist_getter=lambda: "rock",
        log=lambda _msg: None,
    )
    assert runtime.create("rock")["ok"] is True

    primeira = runtime.add_and_verify_result(
        "rock", "https://www.youtube.com/watch?v=abcdefghijk", "Duality", "Slipknot",
    )
    repetida = runtime.add_and_verify_result(
        "rock", "https://www.youtube.com/watch?v=abcdefghijk", "Duality", "Slipknot",
    )

    assert primeira["ok"] is True and primeira["added"] is True
    assert repetida == {
        "ok": True,
        "added": False,
        "duplicated": True,
        "duplicate_other_channel": False,
        "status": "playlist_musica_ja_existia",
    }
    assert runtime.len("rock") == 1


def test_retry_playlist_add_confirmado_nao_alega_nova_inclusao() -> None:
    eventos: list[tuple] = []

    class Operacoes:
        @staticmethod
        def faixa_atual():
            return {
                "url": "https://www.youtube.com/watch?v=abcdefghijk",
                "title": "Duality",
                "canal": "Slipknot",
            }

        @staticmethod
        def adicionar_faixa_resultado(*_args):
            return {
                "ok": True,
                "added": False,
                "duplicated": True,
                "status": "playlist_musica_ja_existia",
            }

        @staticmethod
        def definir_ultima_playlist(_nome):
            return None

    deps = DependenciasExecutorPlaylists(
        marcar_resultado=lambda status, **kwargs: eventos.append(
            ("resultado", status, kwargs)
        ),
        falar_por_status=lambda status, fala, **kwargs: eventos.append(
            ("fala", status, fala, kwargs)
        ),
        abrir_url_musical=lambda _url: True,
        contexto_fala=lambda: {},
        musica_operacoes=Operacoes(),
    )

    despacho = executar_intencao_playlists(
        "PLAYLIST_ADD",
        {"nome_playlist": "rock"},
        "tenta de novo",
        "pc_a",
        {},
        deps,
    )

    assert despacho == ResultadoDespacho.concluido(True)
    resultado = next(item for item in eventos if item[0] == "resultado")
    assert resultado[1] == "playlist_musica_ja_existia"
    assert resultado[2]["executou"] is False
    assert resultado[2]["confirmado"] is True
    fala = next(item for item in eventos if item[0] == "fala")
    assert "já" in fala[2].casefold()
    assert not any(verbo in fala[2].casefold() for verbo in ("salvei", "guardei", "adicionada"))


def test_clima_amanha_roteia_day_offset_e_usa_o_dia_correto_da_fonte() -> None:
    assert detectar_clima(
        "como estará o tempo amanhã?", params_cb=_params,
    ) == {"intent": "WEATHER", "params": {"day_offset": 1}}

    class Resposta:
        status_code = 200
        content = b"1"

        @staticmethod
        def json():
            return {
                "current_condition": [{
                    "temp_C": "21", "FeelsLikeC": "20", "humidity": "50",
                    "weatherDesc": [{"value": "Limpo"}],
                }],
                "weather": [
                    {
                        "avgtempC": "22", "maxtempC": "28", "mintempC": "16",
                        "hourly": [{"time": "1200", "chanceofrain": "5"}],
                    },
                    {
                        "avgtempC": "24", "maxtempC": "31", "mintempC": "18",
                        "hourly": [{
                            "time": "1200", "chanceofrain": "70",
                            "lang_pt": [{"value": "Chuva moderada"}],
                        }],
                    },
                ],
            }

    dados = obter_clima_localidade(
        "Boituva",
        day_offset=1,
        requests_get=lambda *_args, **_kwargs: Resposta(),
    )
    assert dados["fonte"] == "wttr"
    assert dados["day_offset"] == 1
    assert dados["temperatura_max_c"] == "31"
    assert dados["temperatura_min_c"] == "18"
    assert dados["chance_chuva_pct"] == 70
    assert dados["descricao"] == "Chuva moderada"


def test_executor_weather_amanha_nao_rotula_clima_atual_como_previsao() -> None:
    falas: list[str] = []
    resultados: list[tuple] = []
    offsets: list[int] = []

    def obter(_local, *, day_offset=0):
        offsets.append(day_offset)
        return {
            "ok": True,
            "localidade": "Boituva",
            "descricao": "parcialmente nublado",
            "temperatura_max_c": "30",
            "temperatura_min_c": "17",
            "chance_chuva_pct": 25,
            "fonte": "open_meteo",
            "day_offset": day_offset,
        }

    deps = DependenciasExecutorInformacoes(
        marcar_resultado=lambda status, **kwargs: resultados.append(
            (status, kwargs)
        ),
        falar_por_status=lambda *_args, **_kwargs: None,
        registrar_mente=lambda *_args, **_kwargs: None,
    )
    despacho = executar_intencao_informacoes(
        "WEATHER",
        {"day_offset": 1},
        "Como estará o tempo amanhã?",
        {
            "cidade_padrao_clima": "Boituva",
            "obter_clima_localidade": obter,
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        deps,
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert offsets == [1]
    assert falas == [
        "Amanhã em Boituva, o tempo fica parcialmente nublado, com mínima de 17 e máxima de 30 graus, e chance de chuva de até 25%."
    ]
    assert resultados[0][0] == "previsao_consultada"
    assert resultados[0][1]["confirmado"] is True


def test_open_meteo_seleciona_realmente_o_indice_de_amanha() -> None:
    chamadas_previsao: list[dict] = []

    class Resposta:
        def __init__(self, dados):
            self._dados = dados
            self.status_code = 200

        def json(self):
            return self._dados

    def get(url, **kwargs):
        if "geocoding-api" in url:
            return Resposta({
                "results": [{
                    "name": "Cidade Teste Amanhã",
                    "country_code": "BR",
                    "latitude": -20.0,
                    "longitude": -40.0,
                    "timezone": "America/Sao_Paulo",
                }],
            })
        chamadas_previsao.append(dict(kwargs.get("params") or {}))
        return Resposta({
            "current": {"temperature_2m": 20, "weather_code": 0},
            "daily": {
                "temperature_2m_mean": [21, 25],
                "temperature_2m_max": [28, 33],
                "temperature_2m_min": [15, 19],
                "weather_code": [1, 61],
                "precipitation_probability_max": [5, 80],
            },
        })

    dados = obter_clima_open_meteo(
        "Cidade Teste Amanhã",
        day_offset=1,
        requests_get=get,
        clock=lambda: 987654.0,
    )

    assert dados["ok"] is True
    assert dados["day_offset"] == 1
    assert dados["temperatura_c"] == "25"
    assert dados["temperatura_max_c"] == "33"
    assert dados["temperatura_min_c"] == "19"
    assert dados["chance_chuva_pct"] == 80
    assert dados["descricao"] == "chuva fraca"
    assert chamadas_previsao[0]["forecast_days"] == 2


def test_visao_publica_apenas_resultado_final_e_reutiliza_contexto_duas_vezes() -> None:
    falas: list[str] = []
    runtime = MemoriaVisualRuntime(
        namespace_getter=lambda: {
            "enviar_pc_b": lambda _payload: False,
            "capturar_tela": lambda: "imagem-base64",
            "analisar_imagem": lambda _imagem, _pergunta: "Há um editor aberto com um teste em Python.",
            "falar": lambda fala, *_args: falas.append(fala),
            "estado_emocional": lambda: ("calma", 1),
            "obter_contexto": lambda: {"exe": "code.exe"},
        },
        log=lambda _msg: None,
    )

    futuro = runtime.executar("pc_a")
    final = futuro.aguardar(2.0)

    assert final["status"] == "captura_concluida"
    assert final["confirmado"] is True
    assert falas == ["Há um editor aberto com um teste em Python."]
    primeira = runtime.executar(
        "pc_a", acao="consultar_contexto_visual", modo="identificar",
    )
    segunda = runtime.executar(
        "pc_a", acao="consultar_contexto_visual", modo="resumir",
    )
    assert primeira["descricao"] == final["descricao"]
    assert segunda["descricao"] == final["descricao"]


def test_executor_visual_confirma_somente_depois_da_descricao_final() -> None:
    falas: list[str] = []
    resultados: list[tuple] = []
    runtime = MemoriaVisualRuntime(
        namespace_getter=lambda: {
            "enviar_pc_b": lambda _payload: False,
            "capturar_tela": lambda: "imagem-base64",
            "analisar_imagem": lambda _imagem, _pergunta: "A tela mostra o VS Code.",
            "falar": lambda fala, *_args: falas.append(fala),
            "estado_emocional": lambda: ("calma", 1),
            "obter_contexto": lambda: {"exe": "code.exe"},
        },
        log=lambda _msg: None,
    )
    despacho = executar_intencao_sistema(
        "SCREEN_CAPTURE",
        {},
        "pc_a",
        {"_executar_captura_tela_intent": runtime.executar},
        DependenciasExecutorSistema(
            marcar_resultado=lambda status, **kwargs: resultados.append(
                (status, kwargs, list(falas))
            ),
            falar_por_status=lambda *_args, **_kwargs: None,
        ),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert falas == ["A tela mostra o VS Code."]
    assert resultados == [(
        "captura_concluida",
        {"executou": True, "confirmado": True, "detalhe": "pc_a"},
        ["A tela mostra o VS Code."],
    )]


def test_followups_visuais_consultam_contexto_sem_nova_captura() -> None:
    assert dominio_intent("VISION_QUERY") == "visao"
    identificar = detectar_url_visual(
        "o que você consegue identificar?", params_cb=_params,
    )
    resumir = detectar_url_visual(
        "resume o que você está vendo.", params_cb=_params,
    )
    assert identificar == {
        "intent": "VISION_QUERY",
        "params": {"acao": "consultar_contexto_visual", "modo": "identificar"},
    }
    assert resumir == {
        "intent": "VISION_QUERY",
        "params": {"acao": "consultar_contexto_visual", "modo": "resumir"},
    }
    assert detectar_intencao_deterministica_mente(
        "O que você consegue identificar?", _contexto_deterministico(),
    ) == identificar
    assert detectar_intencao_deterministica_mente(
        "Resume o que você está vendo.", _contexto_deterministico(),
    ) == resumir

    chamadas: list[tuple] = []
    falas: list[str] = []

    def executar(destino, **opcoes):
        chamadas.append((destino, opcoes))
        return {
            "ok": True,
            "status": "contexto_visual_consultado",
            "descricao": "Há um editor aberto.",
            "confirmado": True,
            "origem": "pc_a",
        }

    deps = DependenciasExecutorSistema(
        marcar_resultado=lambda *_args, **_kwargs: None,
        falar_por_status=lambda *_args, **_kwargs: None,
    )
    despacho = executar_intencao_sistema(
        "VISION_QUERY",
        identificar["params"],
        "pc_a",
        {
            "_executar_captura_tela_intent": executar,
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        deps,
    )
    assert despacho == ResultadoDespacho.concluido(True)
    assert chamadas == [(
        "pc_a",
        {"acao": "consultar_contexto_visual", "modo": "identificar"},
    )]
    assert falas == ["Há um editor aberto."]
