# -*- coding: utf-8 -*-
"""M1 / turno 149 — contrato revisado do candidato.

Fala real:
"Vai para a próxima faixa e adiciona essa também na caos sonora."

Escopo:
- reconhecer a primeira etapa sem promover ``vai`` globalmente;
- preservar autoridade do turno composto;
- reutilizar apenas a playlist recente realmente nomeada;
- provar o plano determinístico de duas etapas.
"""

from mente_laylay.autonomia.analise_comandos import segmentar_comandos_em_cadeia
from mente_laylay.autonomia.coordenador_intencao import (
    CicloComandosRuntime,
    _intencao_deterministica_tem_alvo_explicito,
)
from mente_laylay.autonomia.detectores_playlist import (
    detectar_playlist_contextual_musica_atual,
)
from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.continuidade_contexto import (
    registrar_estrutura_arquivo_recente,
)
from mente_laylay.memoria_mental.operacoes_musicais_runtime import (
    OperacoesMusicaisRuntime,
)


FALA_M1 = "Vai para a próxima faixa e adiciona essa também na caos sonora."


def _params(**kwargs):
    return kwargs


def _limpar_nome(valor):
    return str(valor or "").strip(" .,!?:;")


# ---------------------------------------------------------------------------
# REDS DO BASELINE
# ---------------------------------------------------------------------------

def test_m1_red_01_segmenta_vai_e_adiciona_em_duas_etapas():
    partes = segmentar_comandos_em_cadeia(FALA_M1)
    assert partes == [
        "Vai para a próxima faixa",
        "adiciona essa também na caos sonora",
    ]


def test_m1_red_02_vai_para_proxima_faixa_concede_autoridade():
    turno = classificar_modalidade_turno("Vai para a próxima faixa.")
    assert turno["modalidade"] == "comando", turno
    assert turno["autoriza_execucao"] is True, turno
    assert turno["acao_explicita"] is True, turno


def test_m1_red_03_composto_inteiro_preserva_autoridade():
    turno = classificar_modalidade_turno(FALA_M1)
    assert turno["modalidade"] == "comando", turno
    assert turno["autoriza_execucao"] is True, turno
    assert turno["acao_explicita"] is True, turno


def test_m1_red_04_adiciona_essa_tambem_reusa_playlist_recente_nomeada():
    resultado = detectar_playlist_contextual_musica_atual(
        "adiciona essa também na caos sonora",
        params_cb=_params,
        limpar_nome_playlist=_limpar_nome,
        ultima_playlist="",
    )
    assert isinstance(resultado, dict), resultado
    assert resultado["intent"] == "PLAYLIST_ADD", resultado
    assert resultado["params"]["nome_playlist"] == "caos sonora", resultado
    assert resultado["params"].get("referencia_contextual") is True, resultado


def test_m1_red_05_fala_real_produz_duas_intencoes_na_ordem():
    turno = classificar_modalidade_turno(FALA_M1)
    assert turno["autoriza_execucao"] is True, turno

    partes = segmentar_comandos_em_cadeia(FALA_M1)
    assert len(partes) == 2, partes

    primeira = detectar_volume_ou_midia(
        partes[0].casefold(),
        params_cb=_params,
        contexto_musical_ativo=True,
    )
    segunda = detectar_playlist_contextual_musica_atual(
        partes[1].casefold(),
        params_cb=_params,
        limpar_nome_playlist=_limpar_nome,
        ultima_playlist="caos sonora",
    )

    assert primeira and primeira["intent"] == "MEDIA_CONTROL", primeira
    assert primeira["params"]["acao"] == "next", primeira
    assert segunda and segunda["intent"] == "PLAYLIST_ADD", segunda
    assert segunda["params"]["nome_playlist"] == "caos sonora", segunda


def test_m1_red_06_destino_musical_nao_pode_escrever_no_arquivo_recente():
    caminho = "C:/tmp/correcao.txt"
    estado = registrar_estrutura_arquivo_recente(
        {},
        {
            "tipo": "arquivo",
            "caminho": caminho,
            "arquivo_nome": "correcao.txt",
            "tipo_arquivo": "texto",
        },
    )

    resultado = detectar_intencao_arquivos(
        "adiciona essa também na caos sonora",
        params_cb=_params,
        estado_mental=estado,
    )

    assert resultado is None, resultado


# ---------------------------------------------------------------------------
# GUARDAS
# ---------------------------------------------------------------------------

def test_m1_guard_01_detector_midia_ja_enxerga_next_na_fala_real():
    resultado = detectar_volume_ou_midia(
        FALA_M1.casefold().strip(" .,!?:;"),
        params_cb=_params,
        contexto_musical_ativo=True,
    )
    assert isinstance(resultado, dict), resultado
    assert resultado["intent"] == "MEDIA_CONTROL", resultado
    assert resultado["params"]["acao"] == "next", resultado


def test_m1_guard_02_proxima_faixa_canonica_continua_autorizada():
    turno = classificar_modalidade_turno("Próxima faixa.")
    assert turno["modalidade"] == "comando", turno
    assert turno["autoriza_execucao"] is True, turno


def test_m1_guard_03_vai_chover_nao_autoriza_execucao():
    turno = classificar_modalidade_turno("Vai chover amanhã.")
    assert turno["autoriza_execucao"] is False, turno


def test_m1_guard_04_narrativa_com_vai_nao_autoriza_execucao():
    turno = classificar_modalidade_turno("Meu irmão vai para a escola amanhã.")
    assert turno["autoriza_execucao"] is False, turno


def test_m1_guard_05_segmentador_nao_promove_vai_narrativo():
    texto = "Vai chover e depois adiciona essa música na playlist rock."
    partes = segmentar_comandos_em_cadeia(texto)
    assert len(partes) == 1, partes


def test_m1_guard_06_atalho_essa_tambem_existente_permanece_valido():
    resultado = detectar_playlist_contextual_musica_atual(
        "essa também",
        params_cb=_params,
        limpar_nome_playlist=_limpar_nome,
        ultima_playlist="caos sonora",
    )
    assert isinstance(resultado, dict), resultado
    assert resultado["intent"] == "PLAYLIST_ADD", resultado
    assert resultado["params"]["nome_playlist"] == "caos sonora", resultado
    assert resultado["params"].get("referencia_contextual") is True, resultado


def test_m1_guard_07_destino_nomeado_na_fala_vence_playlist_recente():
    resultado = detectar_playlist_contextual_musica_atual(
        "adiciona essa também na rock",
        params_cb=_params,
        limpar_nome_playlist=_limpar_nome,
        ultima_playlist="caos sonora",
    )
    assert isinstance(resultado, dict), resultado
    assert resultado["intent"] == "PLAYLIST_ADD", resultado
    assert resultado["params"]["nome_playlist"] == "rock", resultado
    assert resultado["params"].get("referencia_contextual") is True, resultado


def test_m1_guard_08_forma_explicita_com_palavra_playlist_permanece_valida():
    resultado = detectar_playlist_contextual_musica_atual(
        "adiciona essa música na playlist rock",
        params_cb=_params,
        limpar_nome_playlist=_limpar_nome,
        ultima_playlist="caos sonora",
    )
    assert isinstance(resultado, dict), resultado
    assert resultado["intent"] == "PLAYLIST_ADD", resultado
    assert resultado["params"]["nome_playlist"] == "rock", resultado


def test_m1_guard_09_vai_para_proxima_reuniao_nao_autoriza():
    turno = classificar_modalidade_turno("Vai para a próxima reunião amanhã.")
    assert turno["autoriza_execucao"] is False, turno


def test_m1_guard_10_faixa_nao_musical_com_complemento_nao_autoriza():
    turno = classificar_modalidade_turno("Vai para a próxima faixa da estrada.")
    assert turno["autoriza_execucao"] is False, turno


def test_m1_red_07_cadeia_real_publica_add_mesmo_sem_ultima_playlist_global():
    executadas: list[dict] = []

    class Contexto:
        @staticmethod
        def montar():
            return {
                "turno_atual": {
                    "id": "turno-149",
                    "modalidade": "comando",
                    "modalidade_geral": "comando",
                    "autoriza_execucao": True,
                },
                "retrato_turno_atual": {},
                "continuidade_geral": {},
            }

    def detectar(trecho: str):
        t = str(trecho or "").casefold().strip(" .,!?:;")
        midia = detectar_volume_ou_midia(
            t,
            params_cb=_params,
            contexto_musical_ativo=True,
        )
        if midia:
            return midia
        return detectar_playlist_contextual_musica_atual(
            t,
            params_cb=_params,
            limpar_nome_playlist=_limpar_nome,
            ultima_playlist="",
        )

    runtime = CicloComandosRuntime(
        namespace_getter=lambda: {
            "_normalizar_texto_com_apelidos": str.casefold,
            "_texto_depende_de_contexto": lambda _texto: False,
            "_texto_parece_consulta_operacional": lambda _texto: True,
            "detectar_intencao_deterministica": detectar,
            "_resolver_comando_contextual_forcado": lambda _texto: None,
            "_resolver_repeticao_ultima_acao": lambda _texto: None,
            "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
            "_registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
        },
        contexto_intencao_runtime=Contexto(),
        log=lambda *_args: None,
    )
    runtime.executar_intencao = lambda comando, _texto: (
        executadas.append(dict(comando)) or True
    )

    assert runtime.processar_cadeia(FALA_M1, "turno-149") is True
    assert [item["intent"] for item in executadas] == [
        "MEDIA_CONTROL",
        "PLAYLIST_ADD",
    ]
    assert executadas[1]["params"] == {
        "nome_playlist": "caos sonora",
        "referencia_contextual": True,
    }


def test_m1_red_09_cadeia_real_nao_descarta_destino_nomeado_por_fonte_contextual():
    """Replica a fronteira real que o caos expôs no turno 149.

    ``essa`` torna a fonte da música contextual, mas ``caos sonora`` continua
    sendo um destino escrito no turno atual. O coordenador deve publicar
    ``PLAYLIST_ADD`` e deixar o executor decidir, pela observação do player, se
    existe uma faixa que possa ser persistida.
    """

    executadas: list[dict] = []

    class Contexto:
        @staticmethod
        def montar():
            return {
                "turno_atual": {
                    "id": "turno-149-contextual",
                    "modalidade": "comando",
                    "modalidade_geral": "comando",
                    "autoriza_execucao": True,
                },
                "retrato_turno_atual": {},
                "continuidade_geral": {},
            }

    def detectar(trecho: str):
        t = str(trecho or "").casefold().strip(" .,!?:;")
        midia = detectar_volume_ou_midia(
            t,
            params_cb=_params,
            contexto_musical_ativo=True,
        )
        if midia:
            return midia
        return detectar_playlist_contextual_musica_atual(
            t,
            params_cb=_params,
            limpar_nome_playlist=_limpar_nome,
            ultima_playlist="",
        )

    runtime = CicloComandosRuntime(
        namespace_getter=lambda: {
            "_normalizar_texto_com_apelidos": str.casefold,
            "_texto_depende_de_contexto": lambda texto: (
                "essa" in str(texto or "").casefold()
            ),
            "_texto_parece_consulta_operacional": lambda _texto: True,
            "detectar_intencao_deterministica": detectar,
            "_resolver_comando_contextual_forcado": lambda _texto: None,
            "_resolver_repeticao_ultima_acao": lambda _texto: None,
            "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
            "_registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
        },
        contexto_intencao_runtime=Contexto(),
        log=lambda *_args: None,
    )
    runtime.executar_intencao = lambda comando, _texto: (
        executadas.append(dict(comando)) or True
    )

    assert runtime.processar_cadeia(FALA_M1, "turno-149-contextual") is True
    assert [item["intent"] for item in executadas] == [
        "MEDIA_CONTROL",
        "PLAYLIST_ADD",
    ]
    assert executadas[1]["params"] == {
        "nome_playlist": "caos sonora",
        "referencia_contextual": True,
    }


def test_m1_guard_11_destino_inferido_nao_vira_explicito_so_por_estar_no_estado():
    candidato = {
        "intent": "PLAYLIST_ADD",
        "params": {
            "nome_playlist": "caos sonora",
            "referencia_contextual": True,
        },
    }

    assert _intencao_deterministica_tem_alvo_explicito(
        candidato,
        "essa também",
    ) is False


def test_m1_guard_12_nome_parcial_nao_prova_destino_explicito():
    candidato = {
        "intent": "PLAYLIST_ADD",
        "params": {
            "nome_playlist": "rock",
            "referencia_contextual": True,
        },
    }

    assert _intencao_deterministica_tem_alvo_explicito(
        candidato,
        "adiciona essa também na rock alternativo",
    ) is False


def test_m1_red_10_variantes_naturais_do_usuario_segmentam_as_duas_etapas():
    casos = {
        "Pula para a próxima faixa e adiciona essa na playlist caos sonora.": [
            "Pula para a próxima faixa",
            "adiciona essa na playlist caos sonora",
        ],
        "Avança uma música e salva essa também na caos sonora.": [
            "Avança uma música",
            "salva essa também na caos sonora",
        ],
        "Troca para a próxima e acrescenta ela na caos sonora.": [
            "Troca para a próxima",
            "acrescenta ela na caos sonora",
        ],
    }

    for fala, esperado in casos.items():
        assert segmentar_comandos_em_cadeia(fala) == esperado


def test_m1_red_10b_variantes_naturais_concedem_autoridade_operacional():
    casos = (
        "Pula para a próxima faixa e adiciona essa na playlist caos sonora.",
        "Avança uma música e salva essa também na caos sonora.",
        "Troca para a próxima e acrescenta ela na caos sonora.",
    )

    for fala in casos:
        turno = classificar_modalidade_turno(fala)
        assert turno["modalidade"] == "comando", turno
        assert turno["autoriza_execucao"] is True, turno
        assert turno["acao_explicita"] is True, turno


def test_m1_red_11_variantes_naturais_publicam_as_duas_intencoes_na_ordem():
    casos = (
        "Pula para a próxima faixa e adiciona essa na playlist caos sonora.",
        "Avança uma música e salva essa também na caos sonora.",
        "Troca para a próxima e acrescenta ela na caos sonora.",
    )

    for indice, fala in enumerate(casos, start=1):
        executadas: list[dict] = []

        class Contexto:
            @staticmethod
            def montar():
                return {
                    "turno_atual": {
                        "id": f"turno-149-natural-{indice}",
                        "modalidade": "comando",
                        "modalidade_geral": "comando",
                        "autoriza_execucao": True,
                    },
                    "retrato_turno_atual": {},
                    "continuidade_geral": {},
                }

        def detectar(trecho: str):
            t = str(trecho or "").casefold().strip(" .,!?:;")
            midia = detectar_volume_ou_midia(
                t,
                params_cb=_params,
                contexto_musical_ativo=True,
            )
            if midia:
                return midia
            return detectar_playlist_contextual_musica_atual(
                t,
                params_cb=_params,
                limpar_nome_playlist=_limpar_nome,
                ultima_playlist="caos sonora",
                contexto_musical_ativo=True,
            )

        runtime = CicloComandosRuntime(
            namespace_getter=lambda: {
                "_normalizar_texto_com_apelidos": str.casefold,
                "_texto_depende_de_contexto": lambda texto: any(
                    pronome in str(texto or "").casefold().split()
                    for pronome in ("essa", "ela")
                ),
                "_texto_parece_consulta_operacional": lambda _texto: True,
                "detectar_intencao_deterministica": detectar,
                "_resolver_comando_contextual_forcado": lambda _texto: None,
                "_resolver_repeticao_ultima_acao": lambda _texto: None,
                "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
                "_registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
            },
            contexto_intencao_runtime=Contexto(),
            log=lambda *_args: None,
        )
        runtime.executar_intencao = lambda comando, _texto: (
            executadas.append(dict(comando)) or True
        )

        assert runtime.processar_cadeia(
            fala,
            f"turno-149-natural-{indice}",
        ) is True
        assert [item["intent"] for item in executadas] == [
            "MEDIA_CONTROL",
            "PLAYLIST_ADD",
        ]
        assert executadas[1]["params"]["nome_playlist"] == "caos sonora"
        if indice > 1:
            assert executadas[1]["params"]["referencia_contextual"] is True


def test_m1_guard_13_variantes_naturais_nao_promovem_narrativa_a_comando():
    texto = "Ela pula para a próxima página e adiciona uma observação ao texto."
    assert segmentar_comandos_em_cadeia(texto) == [texto.casefold().rstrip(".")]


def test_m1_guard_14_proxima_aba_nao_vira_controle_de_musica():
    resultado = detectar_volume_ou_midia(
        "troca para a próxima aba",
        params_cb=_params,
        contexto_musical_ativo=True,
    )
    assert resultado is None


def test_m1_guard_15_lista_comum_nao_vira_playlist_por_pronome():
    resultado = detectar_playlist_contextual_musica_atual(
        "acrescenta ela na lista de tarefas",
        params_cb=_params,
        limpar_nome_playlist=_limpar_nome,
        ultima_playlist="caos sonora",
        contexto_musical_ativo=True,
    )
    assert resultado is None


def test_m1_red_08_cadeia_real_adiciona_a_faixa_nova_e_nunca_a_anterior():
    faixa_anterior = {
        "url": "https://www.youtube.com/watch?v=AAAAAAAAAAA",
        "title": "Faixa anterior",
        "canal": "Canal A",
    }
    faixa_nova = {
        "url": "https://www.youtube.com/watch?v=BBBBBBBBBBB",
        "title": "Faixa nova",
        "canal": "Canal B",
    }

    estado = {
        "musica_atual_ts": 9999999999.0,
        "musica_atual_status": "tocando",
        "musica_atual_url": faixa_anterior["url"],
        "musica_atual_titulo": faixa_anterior["title"],
    }
    aba_atual = {
        "valor": {**faixa_anterior, "tabId": 149, "playingConfirmed": True},
    }

    class PlaylistsUsuario:
        def __init__(self):
            self.adicoes: list[tuple[str, str, str, str]] = []

        def add_and_verify(self, nome, url, titulo, canal):
            self.adicoes.append((nome, url, titulo, canal))
            return True

    playlists = PlaylistsUsuario()
    musica = OperacoesMusicaisRuntime(
        playlists_usuario=playlists,
        playlists_laylay=object(),
        musica_estado_getter=lambda chave, padrao=None: estado.get(chave, padrao),
        musica_estado_setter=lambda chave, valor: estado.__setitem__(chave, valor),
        solicitar_aba_ativa=lambda: dict(aba_atual["valor"]),
        playlist_state={},
        log=lambda *_args: None,
    )

    class NavegadorLeitura:
        @staticmethod
        def aba_ativa():
            return dict(aba_atual["valor"])

    class NavegadorOperacoes:
        def __init__(self):
            self.comandos: list[str] = []

        def controlar_youtube_detalhado(self, comando, **_kwargs):
            self.comandos.append(str(comando))
            if comando == "next":
                aba_atual["valor"] = {
                    **faixa_nova,
                    "tabId": 149,
                    "playingConfirmed": True,
                }
                return {"ok": True, "confirmado": True, "status": "success"}
            return {"ok": False, "confirmado": False, "status": "falha_execucao"}

    navegador = NavegadorOperacoes()

    def detectar(trecho: str):
        texto = str(trecho or "").casefold().strip(" .,!?:;")
        midia = detectar_volume_ou_midia(
            texto,
            params_cb=_params,
            contexto_musical_ativo=True,
        )
        if midia:
            return midia
        return detectar_playlist_contextual_musica_atual(
            texto,
            params_cb=_params,
            limpar_nome_playlist=_limpar_nome,
            ultima_playlist="",
        )

    contexto = {
        "turno_atual": {
            "id": "turno-149-real",
            "modalidade": "comando",
            "modalidade_geral": "comando",
            "autoriza_execucao": True,
        },
        "retrato_turno_atual": {},
        "continuidade_geral": {},
        "_target_from_params": lambda *_args: "pc_a",
        "_registro_navegador_leitura_runtime": NavegadorLeitura(),
        "_registro_navegador_operacoes_runtime": navegador,
        "_registro_musica_operacoes_runtime": musica,
        "_musica_estado_get": lambda chave, padrao=None: estado.get(chave, padrao),
        "_musica_estado_set": lambda chave, valor: estado.__setitem__(chave, valor),
        "falar_com_lipsync": lambda *_args: None,
        "_yt_clean_title": lambda titulo: titulo,
    }

    class Contexto:
        @staticmethod
        def montar():
            return contexto

    runtime = CicloComandosRuntime(
        namespace_getter=lambda: {
            "_normalizar_texto_com_apelidos": str.casefold,
            "_texto_depende_de_contexto": lambda _texto: False,
            "_texto_parece_consulta_operacional": lambda _texto: True,
            "detectar_intencao_deterministica": detectar,
            "_resolver_comando_contextual_forcado": lambda _texto: None,
            "_resolver_repeticao_ultima_acao": lambda _texto: None,
            "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
            "_registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
        },
        contexto_intencao_runtime=Contexto(),
        log=lambda *_args: None,
    )
    runtime.executar_intencao = lambda comando, texto: executar_intencao(
        comando, texto, contexto,
    )

    assert runtime.processar_cadeia(FALA_M1, "turno-149-real") is True
    assert navegador.comandos == ["next"]
    assert playlists.adicoes == [(
        "caos sonora",
        faixa_nova["url"],
        faixa_nova["title"],
        faixa_nova["canal"],
    )]
    assert estado["ultima_playlist"] == "caos sonora"
