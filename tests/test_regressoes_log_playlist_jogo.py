from __future__ import annotations

import json

from mente_laylay.autonomia.roteador_deterministico import (
    detectar_playlist_contextual_musica_atual,
)
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.integracao.chrome_ws_handlers import handle_player_event
from mente_laylay.memoria_mental.contexto_imediato import (
    resolver_comando_acao_geral_contextual,
    resolver_comando_midia_contextual,
)
from mente_laylay.memoria_mental.playlist_mental import limpar_nome_playlist
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime
from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial
from mente_laylay.memoria_mental.continuidade_geral import registrar_evento_continuidade
from mente_laylay.personalidade.conversa_natural import (
    responder_comentario_jogo_em_foco,
)


def test_adicionar_musica_em_playlist_vence_replay_contextual() -> None:
    texto = "coloca essa musica na playlist alternativo"
    contexto_musical = {
        "tipo": "playlist",
        "alvo": "alternativo",
        "params": {"nome_playlist": "alternativo"},
    }

    assert resolver_comando_acao_geral_contextual(texto, contexto_musical) is None
    assert resolver_comando_midia_contextual(
        texto,
        mente_integrada_estado={"ultima_habilidade": "playlist", "ts": 1},
        contexto_musical=True,
    ) is None
    assert detectar_playlist_contextual_musica_atual(
        texto,
        params_cb=lambda **kwargs: kwargs,
        limpar_nome_playlist=limpar_nome_playlist,
    ) == {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "alternativo"},
    }


def test_playlist_add_explicito_e_consumido_antes_da_llm() -> None:
    chamadas = []
    registros = []

    class Estado:
        mental = {
            "turno_atual": {
                "autoriza_execucao": True,
                "operacao_explicita": "playlist_adicionar",
            },
            "retrato_turno_atual": {
                "operacao_explicita": "playlist_adicionar",
            },
        }

    namespace = {
        "_estado_compartilhado_runtime": Estado(),
        "detectar_intencao_deterministica": lambda _texto: {
            "intent": "PLAYLIST_ADD",
            "params": {"nome_playlist": "alternativo"},
        },
        "executar_intencao": lambda *args: chamadas.append(args) or True,
        "_registrar_resultado_execucao": lambda *args, **kwargs: registros.append((args, kwargs)),
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(
        "coloca essa musica na playlist alternativo"
    ) is True
    assert chamadas == [(
        {"intent": "PLAYLIST_ADD", "params": {"nome_playlist": "alternativo"}},
        "coloca essa musica na playlist alternativo",
    )]
    assert registros[0][0][2] is True
    assert registros[0][1]["origem"] == "prioritario_playlist"


def test_essa_tambem_percorre_composicao_prioritaria_sem_chegar_a_llm() -> None:
    mente = registrar_evento_continuidade(
        estado_mental_inicial(),
        evento="acao",
        intent="PLAYLIST_ADD",
        alvo="sendo sendo",
        params={"nome_playlist": "sendo sendo"},
        status="playlist_musica_adicionada",
    )
    mente["turno_atual"] = {
        "modalidade": "comando",
        "modalidade_geral": "comando",
        "autoriza_execucao": True,
    }
    mente["retrato_turno_atual"] = {}
    chamadas, registros = [], []

    class Estado:
        mental = mente

    contexto_detector = {
        "mente_integrada_estado": mente,
        "normalizar_texto": lambda texto: str(texto).casefold().strip(),
        "texto_expresso_melhor_no_deterministico": (
            lambda texto: texto in {"essa tambem", "essa também"}
        ),
        "limpar_destino_pc_b": lambda texto: texto,
        "limpar_nome_playlist": limpar_nome_playlist,
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": Estado(),
            "detectar_intencao_deterministica": lambda texto: (
                detectar_intencao_deterministica_mente(texto, contexto_detector)
            ),
            "executar_intencao": (
                lambda intent, texto: chamadas.append((intent, texto)) or True
            ),
            "_registrar_resultado_execucao": (
                lambda *args, **kwargs: registros.append((args, kwargs))
            ),
        },
        loop_getter=lambda: None,
    )

    assert texto_tem_comando_explicito("essa também") is True
    assert runtime.processar_prioritarios("essa tambem") is True
    assert chamadas == [({
        "intent": "PLAYLIST_ADD",
        "params": {
            "nome_playlist": "sendo sendo",
            "referencia_contextual": True,
        },
    }, "essa tambem")]
    assert registros[0][1]["origem"] == "prioritario_comando_explicito"


def test_lista_iot_e_consumida_na_prioridade_antes_da_llm() -> None:
    chamadas = []

    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "executar_intencao": lambda intent, texto: chamadas.append((intent, texto)) or True,
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(
        "quais dispositivos tem no quarto?"
    ) is True
    assert chamadas == [({
        "intent": "IOT_LIST", "params": {"ambiente": "quarto"},
    }, "quais dispositivos tem no quarto?")]


def test_status_iot_contextual_e_consumido_antes_da_llm() -> None:
    chamadas = []

    class Estado:
        mental = {"ultimo_dispositivo_iot": "tomada_ventilador"}

    class IoT:
        def detectar(self, texto, estado):
            return {
                "intent": "IOT_STATUS",
                "params": {"acao": "status", "alvo": estado["ultimo_dispositivo_iot"]},
            } if texto == "como ele está agora?" else None

    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": Estado(),
            "executar_intencao": lambda intent, texto: chamadas.append((intent, texto)) or True,
        },
        loop_getter=lambda: None,
        iot=IoT(),
    )

    assert runtime.processar_prioritarios("como ele está agora?") is True
    assert chamadas[0][0]["params"]["alvo"] == "tomada_ventilador"


def test_musica_contextual_no_jogo_e_executada_sem_depender_da_llm() -> None:
    chamadas = []
    registros = []

    class Estado:
        mental = {
            "turno_atual": {
                "modalidade": "comando",
                "modalidade_geral": "comando",
                "autoriza_execucao": True,
            },
            "retrato_turno_atual": {"modo_jogo_ativo": True},
        }

    comando = {
        "intent": "MUSIC_SEARCH",
        "params": {"query": "musica para jogar minecraft"},
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": Estado(),
            "detectar_intencao_deterministica": lambda _texto: comando,
            "executar_intencao": lambda intent, texto: chamadas.append((intent, texto)) or True,
            "_registrar_resultado_execucao": (
                lambda *args, **kwargs: registros.append((args, kwargs))
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(
        "coloca uma musica para jogar minecraft"
    ) is True
    assert chamadas == [(comando, "coloca uma musica para jogar minecraft")]
    assert registros[0][1]["origem"] == "prioritario_comando_explicito"


def test_comentario_musical_nao_ganha_execucao_prioritaria() -> None:
    chamadas = []

    class Estado:
        mental = {
            "turno_atual": {
                "modalidade": "conversa",
                "modalidade_geral": "conversa",
                "autoriza_execucao": False,
            },
        }

    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": Estado(),
            "detectar_intencao_deterministica": lambda _texto: {
                "intent": "MUSIC_SEARCH", "params": {"query": "minecraft"},
            },
            "executar_intencao": lambda *args: chamadas.append(args) or True,
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(
        "eu gosto de musica para jogar minecraft"
    ) is False
    assert chamadas == []


def test_rota_prioritaria_e_geral_para_comandos_deterministicos() -> None:
    casos = (
        ("abre a calculadora", "APP_OPEN", {"nome_app": "calculadora"}),
        ("cria uma pasta chamada teste", "CREATE_FOLDER", {"nome": "teste"}),
        ("desliga a luz", "IOT_CONTROL", {"acao": "desligar", "alvo": "lampada_quarto"}),
        ("me lembra de beber agua amanhã", "AGENDAR_LEMBRETE", {"texto": "beber agua"}),
    )

    for texto, intent, params in casos:
        chamadas = []

        class Estado:
            mental = {
                "turno_atual": {
                    "modalidade": "comando",
                    "modalidade_geral": "comando",
                    "autoriza_execucao": True,
                },
            }

        comando = {"intent": intent, "params": params}
        runtime = ComandosImediatosRuntime(
            namespace_getter=lambda comando=comando: {
                "_estado_compartilhado_runtime": Estado(),
                "detectar_intencao_deterministica": lambda _texto: comando,
                "executar_intencao": (
                    lambda detectada, original: chamadas.append((detectada, original)) or True
                ),
            },
            loop_getter=lambda: None,
        )

        assert runtime.processar_prioritarios(texto) is True
        assert chamadas == [(comando, texto)]


def test_rota_prioritaria_materializa_pronome_de_arquivo_antes_de_executar() -> None:
    chamadas = []
    caminho = r"C:\Users\teste\teste governança"

    class Estado:
        mental = {
            "turno_atual": {
                "modalidade": "comando",
                "modalidade_geral": "comando",
                "autoriza_execucao": True,
            },
            "retrato_turno_atual": {},
        }

    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": Estado(),
            "detectar_intencao_deterministica": lambda _texto: {
                "intent": "DELETE_ITEM", "params": {"alvo": "ele"},
            },
            "_resolver_comando_arquivo_contextual_forcado": lambda _texto: {
                "intent": "DELETE_ITEM",
                "params": {"alvo": caminho, "tipo": "arquivo"},
            },
            "executar_intencao": (
                lambda detectada, original: chamadas.append((detectada, original)) or True
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("apaga ele") is True
    assert chamadas == [({
        "intent": "DELETE_ITEM",
        "params": {"alvo": caminho, "tipo": "arquivo"},
    }, "apaga ele")]


def test_rota_geral_nao_executa_sem_autorizacao_do_turno() -> None:
    chamadas = []

    class Estado:
        mental = {
            "turno_atual": {
                "modalidade": "pergunta",
                "modalidade_geral": "pergunta",
                "autoriza_execucao": False,
            },
        }

    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": Estado(),
            "detectar_intencao_deterministica": lambda _texto: {
                "intent": "CLOSE_APP", "params": {"nome_app": "chrome"},
            },
            "executar_intencao": lambda *args: chamadas.append(args) or True,
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(
        "se eu pedir para fechar o Chrome, você consegue?"
    ) is False
    assert chamadas == []


def test_consulta_eliptica_lista_faixas_da_playlist_resolvida() -> None:
    contexto_playlist = {
        "tipo": "playlist",
        "alvo": "kamaitachi",
        "params": {"nome_playlist": "kamaitachi"},
    }

    assert resolver_comando_acao_geral_contextual(
        "quais musicas tem nela",
        contexto_playlist,
    ) == {
        "intent": "PLAYLIST_LIST",
        "params": {"nome_playlist": "kamaitachi", "referencia_contextual": True},
    }


def test_consulta_eliptica_nao_herda_playlist_em_contexto_iot() -> None:
    contexto_iot = {
        "tipo": "iot",
        "alvo": "lampada_quarto",
        "params": {"alvo": "lampada_quarto"},
    }

    assert resolver_comando_acao_geral_contextual(
        "quais musicas tem nela",
        contexto_iot,
        ultima_playlist="kamaitachi",
    ) is None


def test_playlist_add_prioritario_respeita_autorizacao_do_turno() -> None:
    chamadas = []

    class Estado:
        mental = {
            "turno_atual": {
                "autoriza_execucao": False,
                "operacao_explicita": "playlist_adicionar",
            },
            "retrato_turno_atual": {
                "operacao_explicita": "playlist_adicionar",
            },
        }

    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": Estado(),
            "detectar_intencao_deterministica": lambda _texto: {
                "intent": "PLAYLIST_ADD", "params": {"nome_playlist": "alternativo"},
            },
            "processar_comando_deterministico": lambda *args: chamadas.append(args),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(
        "talvez eu coloque essa musica na playlist alternativo"
    ) is False
    assert chamadas == []


def test_comentario_sobre_esse_jogo_usa_jogo_em_foco() -> None:
    contexto = {
        "contexto_perceptivo": {
            "jogo": {
                "ativo": True,
                "processo": "Soulframe.x64.exe",
                "titulo": "Soulframe",
            }
        },
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "_ajustar_fala_por_horario": lambda fala, _texto: fala,
    }

    resposta = responder_comentario_jogo_em_foco(contexto, "esse jogo é muito legal")

    assert "Soulframe" in resposta
    assert "o que mais" in resposta.casefold()


def test_falha_ao_abrir_proxima_musica_nao_avanca_indice(tmp_path) -> None:
    caminho = tmp_path / "playlists.json"
    caminho.write_text(json.dumps({
        "alternativo": [
            {"url": "https://youtube.com/watch?v=um", "titulo": "Um"},
            {"url": "https://youtube.com/watch?v=dois", "titulo": "Dois"},
        ]
    }), encoding="utf-8")
    estado = {"name": "alternativo", "index": 0, "last_url": "https://youtube.com/watch?v=um"}
    runtime = PlaylistRuntime(
        state_file=str(caminho),
        legacy_file=str(tmp_path / "legado.json"),
        cache={},
        ultima_playlist_getter=lambda: "alternativo",
        playlist_state=estado,
        youtube_play=lambda *_args, **_kwargs: False,
        log=lambda _linha: None,
    )

    assert runtime.avancar_proxima() is False
    assert estado["index"] == 0
    assert estado["name"] == "alternativo"
    assert estado["last_advance_status"] == "falha_execucao"


def test_falha_de_entrega_nao_e_anunciada_como_fim_da_playlist() -> None:
    falas: list[str] = []
    estado = {
        "name": "alternativo",
        "last_url": "https://youtube.com/watch?v=um",
        "last_advance_status": "ok",
    }

    def falhar_avanco() -> bool:
        estado["last_advance_status"] = "falha_execucao"
        return False

    handle_player_event(
        {
            "event": "video_ended",
            "eventId": "ended:um",
            "url": estado["last_url"],
            "duration": 180,
            "tabId": 12,
        },
        playlist_state=estado,
        yt_clean_url=lambda url: url,
        playlist_avancar_proxima=falhar_avanco,
        falar_com_lipsync=lambda texto, *_args: falas.append(texto),
    )

    assert falas == []
    assert estado["name"] == "alternativo"
