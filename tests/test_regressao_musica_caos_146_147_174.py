from __future__ import annotations

import time

from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial
from mente_laylay.memoria_mental.continuidade_geral import (
    registrar_evento_continuidade,
    resolver_continuacao_aditiva,
)
from mente_laylay.memoria_mental.operacoes_musicais_runtime import (
    OperacoesMusicaisRuntime,
)


FALA_146 = "Coloca a playlist VMZ, pausa a música e me diz o estado dela."
FALA_147 = (
    "Continua a música, passa para a próxima faixa e me diz qual está tocando."
)


def _params(**kwargs):
    return kwargs


def test_turno_147_composto_musical_preserva_autoridade_do_usuario() -> None:
    turno = classificar_modalidade_turno(
        FALA_147,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )

    assert turno["modalidade"] == "comando", turno
    assert turno["autoriza_execucao"] is True, turno
    assert turno["acao_explicita"] is True, turno


def test_consultas_elipticas_do_player_exigem_contexto_musical() -> None:
    for fala in (
        "me diz o estado dela",
        "me diz qual está tocando",
        "estado",
        "qual?",
    ):
        resultado = detectar_volume_ou_midia(
            fala,
            params_cb=_params,
            contexto_musical_ativo=True,
        )
        assert resultado == {
            "intent": "MUSIC_STATUS",
            "params": {
                "acao": "status",
                "platform": "music",
                "somente_leitura": True,
                "referencia_contextual": True,
            },
        }, fala


def test_consulta_eliptica_nao_inventa_player_sem_contexto() -> None:
    for fala in ("me diz o estado dela", "estado", "qual?"):
        assert detectar_volume_ou_midia(
            fala,
            params_cb=_params,
            contexto_musical_ativo=False,
        ) is None


def test_turno_146_retrato_musical_bloqueia_iot_antigo_na_etapa_eliptica() -> None:
    estado = estado_mental_inicial()
    estado.update({
        "ultima_acao_intent": "IOT_STATUS",
        "ultima_intencao": "IOT_STATUS",
        "ultimo_dispositivo_iot": "lampada_quarto",
    })
    contexto = {
        "mente_integrada_estado": estado,
        "retrato_turno_atual": {
            "referencia_tipo": "midia",
            "referencia_resolvida": {
                "tipo": "midia",
                "nome": "musica",
                "origem": "dominio_explicito_cadeia",
            },
        },
        "detectar_intencao_iot": lambda *_args: {
            "intent": "IOT_STATUS",
            "params": {
                "acao": "status",
                "alvo": "lampada_quarto",
                "referencia_contextual": True,
            },
        },
        "contexto_musical_ativo": lambda: True,
        "normalizar_texto": lambda texto: str(texto).casefold().strip(),
    }

    resultado = detectar_intencao_deterministica_mente(
        "me diz o estado dela",
        contexto,
    )

    assert resultado and resultado["intent"] == "MUSIC_STATUS", resultado


def test_turno_146_arbitro_rejeita_candidato_contextual_iot_contra_retrato_musical() -> None:
    """Reproduz a segunda porta que venceu no caos apesar do detector correto."""
    resultado, rota = resolver_intencao(
        "me diz o estado dela",
        "turno-146-etapa-3",
        {
            "normalizar_texto": lambda texto: str(texto).casefold().strip(),
            "refinar_contexto_mental": lambda _texto: None,
            "turno_atual": {
                "modalidade": "comando",
                "modalidade_geral": "comando",
                "autoriza_execucao": True,
            },
            "retrato_turno_atual": {
                "referencia_tipo": "midia",
                "referencia_resolvida": {
                    "tipo": "midia",
                    "nome": "musica",
                    "origem": "continuidade_operacional_viva_cadeia",
                },
            },
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: True,
            "detectar_intencao_deterministica": lambda _texto: {
                "intent": "MUSIC_STATUS",
                "params": {
                    "acao": "status",
                    "platform": "music",
                    "somente_leitura": True,
                    "referencia_contextual": True,
                },
            },
            "resolver_comando_contextual_forcado": lambda _texto: {
                "intent": "IOT_STATUS",
                "params": {
                    "acao": "status",
                    "alvo": "lampada_quarto",
                    "referencia_contextual": True,
                },
                "_rota_contextual": "iot",
            },
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "registrar_arbitragem_turno": lambda *_args: None,
            "tentar_intencao_ai_primeiro": lambda _texto: None,
            "continuidade_geral": {},
        },
    )

    assert resultado and resultado["intent"] == "MUSIC_STATUS", (resultado, rota)
    assert rota != "contexto-iot"


def test_turno_146_cadeia_real_transporta_dominio_musical_entre_etapas() -> None:
    # O estado inicial reproduz o caos: há IoT antigo, mas nenhuma faixa
    # confirmada que possa fornecer um alvo musical. O domínio da cadeia ainda
    # precisa sobreviver sem que o runtime invente uma faixa.
    estado = registrar_evento_continuidade(
        estado_mental_inicial(),
        evento="acao",
        intent="IOT_STATUS",
        alvo="lampada_quarto",
        params={"acao": "status", "alvo": "lampada_quarto"},
        status="desligado",
    )
    estado["ultima_acao_intent"] = "IOT_STATUS"
    estado["ultima_intencao"] = "IOT_STATUS"
    estado["ultimo_dispositivo_iot"] = "lampada_quarto"
    executadas: list[dict] = []

    class Contexto:
        @staticmethod
        def montar():
            return {
                "mente_integrada_estado": estado,
                "turno_atual": classificar_modalidade_turno(
                    FALA_146,
                    texto_tem_comando_explicito=texto_tem_comando_explicito,
                ),
                "retrato_turno_atual": {},
                "continuidade_geral": dict(
                    estado.get("continuidade_geral") or {}
                ),
                "falar_com_lipsync": lambda *_args: None,
            }

    def detectar(trecho: str):
        t = str(trecho or "").casefold().strip(" .,!?:;")
        if t.startswith("coloca a playlist"):
            return {
                "intent": "PLAYLIST_PLAY",
                "params": {"nome_playlist": "vmz"},
            }
        if t.startswith("pausa a música"):
            return {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}
        if "estado dela" in t:
            # Reproduz a primeira escolha errada do roteador no caos. O
            # coordenador deve rejeitá-la pelo domínio da própria cadeia.
            return {
                "intent": "IOT_STATUS",
                "params": {
                    "acao": "status",
                    "alvo": "lampada_quarto",
                    "referencia_contextual": True,
                },
            }
        return None

    runtime = CicloComandosRuntime(
        namespace_getter=lambda: {
            "_normalizar_texto_com_apelidos": (
                lambda texto: str(texto).casefold().strip()
            ),
            "_texto_depende_de_contexto": (
                lambda texto: "dela" in str(texto).casefold()
            ),
            "_texto_parece_consulta_operacional": lambda _texto: True,
            "detectar_intencao_deterministica": detectar,
            "_resolver_comando_contextual_forcado": (
                lambda texto: {
                    "intent": "IOT_STATUS",
                    "params": {
                        "acao": "status",
                        "alvo": "lampada_quarto",
                        "referencia_contextual": True,
                    },
                    "_rota_contextual": "iot",
                }
                if "estado dela" in str(texto).casefold()
                else None
            ),
            "_resolver_comando_midia_contextual_forcado": lambda _texto: None,
            "_resolver_comando_acao_geral_contextual_forcado": (
                lambda _texto: None
            ),
            "_resolver_repeticao_ultima_acao": lambda _texto: None,
            "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
            "_registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
        },
        contexto_intencao_runtime=Contexto(),
        log=lambda *_args: None,
    )
    runtime.executar_intencao = (
        lambda comando, _texto: executadas.append(dict(comando)) or True
    )

    assert runtime.processar_cadeia(FALA_146, "turno-146") is True
    assert [item["intent"] for item in executadas] == [
        "PLAYLIST_PLAY",
        "MEDIA_CONTROL",
        "MUSIC_STATUS",
    ]


def test_turno_174_operacao_aditiva_nao_expira_por_ruido_de_outros_dominios() -> None:
    estado = registrar_evento_continuidade(
        estado_mental_inicial(),
        evento="acao",
        intent="PLAYLIST_ADD",
        alvo="caos sonora",
        params={"nome_playlist": "caos sonora"},
        status="faixa_atual_indisponivel",
    )
    assert resolver_continuacao_aditiva(estado, texto="essa também")

    for indice in range(40):
        if indice % 3 == 0:
            intent = "MEDIA_CONTROL"
            alvo = ""
            params = {"acao": "next", "platform": "music"}
            status = "midia_next"
        elif indice % 3 == 1:
            intent = "IOT_STATUS"
            alvo = "lampada_quarto"
            params = {"acao": "status", "alvo": "lampada_quarto"}
            status = "desligado"
        else:
            intent = "APP_OPEN"
            alvo = f"app-{indice}"
            params = {"nome_app": f"app-{indice}"}
            status = "app_focado"
        estado = registrar_evento_continuidade(
            estado,
            evento="acao",
            intent=intent,
            alvo=alvo,
            params=params,
            status=status,
        )

    assert resolver_continuacao_aditiva(estado, texto="essa também") == {
        "intent": "PLAYLIST_ADD",
        "params": {
            "nome_playlist": "caos sonora",
            "referencia_contextual": True,
        },
    }


def test_falha_generica_de_playlist_continua_inelegivel_para_essa_tambem() -> None:
    estado = registrar_evento_continuidade(
        estado_mental_inicial(),
        evento="acao",
        intent="PLAYLIST_ADD",
        alvo="caos sonora",
        params={"nome_playlist": "caos sonora"},
        status="falha_execucao",
    )

    assert resolver_continuacao_aditiva(estado, texto="essa também") == {}


class _PlaylistsInertes:
    pass


def _operacoes_com_player(
    *,
    player: dict | None,
    estado_musical: dict | None = None,
    aba_ativa: dict | None = None,
) -> OperacoesMusicaisRuntime:
    estado = dict(estado_musical or {})
    playlist_state = {"name": "vmz", "index": 0}
    if player is not None:
        playlist_state["player"] = dict(player)
    return OperacoesMusicaisRuntime(
        playlists_usuario=_PlaylistsInertes(),
        playlists_laylay=_PlaylistsInertes(),
        musica_estado_getter=lambda chave, padrao=None: estado.get(chave, padrao),
        musica_estado_setter=lambda chave, valor: estado.__setitem__(chave, valor),
        solicitar_aba_ativa=lambda: dict(aba_ativa or {}),
        playlist_state=playlist_state,
        log=lambda *_args: None,
    )


def test_turnos_147_e_174_usam_player_youtube_observado_mesmo_com_outra_aba_ativa() -> None:
    player = {
        "url": "https://www.youtube.com/watch?v=nova-faixa",
        "title": "Faixa nova",
        "channel": "Canal real",
        "state": "playing",
        "observed_at": time.time(),
        "source": "audible_youtube_tab",
        "_priority": 400,
    }
    runtime = _operacoes_com_player(
        player=player,
        aba_ativa={
            "url": "https://pt.wikipedia.org/wiki/Python",
            "title": "Python — Wikipédia",
        },
    )

    assert runtime.faixa_atual() == {
        "url": player["url"],
        "title": "Faixa nova",
        "canal": "Canal real",
        "origem": "audible_youtube_tab",
    }


def test_turno_147_nao_confirma_faixa_antiga_enquanto_proxima_esta_pendente() -> None:
    url_antiga = "https://www.youtube.com/watch?v=faixa-antiga"
    runtime = _operacoes_com_player(
        player={
            "url": url_antiga,
            "title": "Faixa antiga",
            "state": "playing",
            "observed_at": time.time(),
            "source": "playing_youtube_tab",
        },
        estado_musical={
            "musica_atual_status": "troca_nao_confirmada",
            "musica_troca_origem_url": url_antiga,
        },
    )

    assert runtime.faixa_atual() == {}


def test_turno_174_sem_player_real_continua_falhando_sem_inventar_faixa() -> None:
    runtime = _operacoes_com_player(
        player=None,
        aba_ativa={
            "url": "https://pt.wikipedia.org/wiki/Python",
            "title": "Python — Wikipédia",
        },
    )

    assert runtime.faixa_atual() == {}
