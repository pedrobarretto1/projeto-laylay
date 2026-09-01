# -*- coding: utf-8 -*-
import pytest

from mente_laylay.integracao.avaliador_roteiro_teste import (
    avaliar_turno_roteiro,
    gravar_relatorios_roteiro,
    resumir_estado_roteiro,
)


def plano(*comandos):
    return {"fase": "tratado_prioritario", "comandos": list(comandos), "erros": []}


def test_opera_read_only_passa_e_app_open_e_proibido():
    ok = avaliar_turno_roteiro(
        indice=48,
        comando="O Opera continua aberto?",
        resposta="Opera está aberto e em foco.",
        plano=plano({
            "intent": "LIST_WINDOWS", "status": "estado_app_consultado",
            "executou": True, "confirmado": True,
        }),
        respondeu=True, motivo_resultado="execucao_confirmada",
        enviado_em=10.0, finalizado_em=10.4,
    )
    assert ok["resultado_semantico"] == "passou"

    ruim = avaliar_turno_roteiro(
        indice=48,
        comando="O Opera continua aberto?",
        resposta="Opera já está aberto.",
        plano=plano({
            "intent": "APP_OPEN", "status": "ja_aberto_focado",
            "executou": False, "confirmado": True,
        }),
        respondeu=True,
    )
    assert ruim["resultado_semantico"] == "falhou"
    assert any("intent_proibida" in x for x in ruim["erros_semanticos"])


def test_fala_confirmada_nao_pode_dizer_que_nao_confirmou():
    av = avaliar_turno_roteiro(
        indice=113,
        comando="Guarda essa ideia e me lembra dela amanhã às 15 e 20.",
        resposta="Enviei, mas não consegui confirmar o resultado.",
        plano=plano({
            "intent": "AGENDAR_LEMBRETE", "status": "lembrete_ja_agendado",
            "executou": False, "confirmado": True,
        }),
        respondeu=True,
    )
    assert av["resultado_semantico"] == "falhou"
    assert av["fala_coerente"] == "nao"


def test_pergunta_de_capacidade_nao_pode_executar_efeito():
    av = avaliar_turno_roteiro(
        indice=1,
        comando="Você consegue criar arquivos?",
        resposta="Consigo, sim.",
        plano=plano({
            "intent": "CREATE_FILE", "status": "arquivo_criado",
            "executou": True, "confirmado": True,
        }),
        respondeu=True,
    )
    assert av["resultado_semantico"] == "falhou"


def test_expectativa_local_tem_prioridade_sem_contaminar_avaliador_global():
    comando = "continua"
    local = avaliar_turno_roteiro(
        indice=21,
        comando=comando,
        resposta="Pedi para a música continuar.",
        plano=plano({
            "intent": "MEDIA_CONTROL",
            "status": "midia_play",
            "executou": True,
            "confirmado": True,
        }),
        respondeu=True,
        expectativa_local={
            "intents_any": ("MEDIA_CONTROL",),
            "nome": "continuidade_musical_dedicada",
            "dominio": "musica",
        },
    )
    global_legado = avaliar_turno_roteiro(
        indice=21,
        comando=comando,
        resposta="Continua o quê?",
        plano={"fase": "fala_verificada", "comandos": [], "erros": []},
        respondeu=True,
        motivo_resultado="execucao_nao_publicada",
    )

    assert local["resultado_semantico"] == "passou"
    assert local["expectativa"] == "continuidade_musical_dedicada"
    assert local["origem_expectativa"] == "roteiro_dedicado"
    assert global_legado["resultado_semantico"] == "passou"
    assert global_legado["expectativa"] == "continua_ambigua_sem_contexto"
    assert global_legado["origem_expectativa"] == "avaliador_global"


def test_expectativa_local_verifica_campos_genericos_do_plano_sem_regra_de_habilidade():
    expectativa = {
        "sem_comando": True,
        "nome": "contrato_causal_publicado",
        "dominio": "personalidade",
        "campos_plano": {
            "evento_emocional_causal.origem": "conversa",
            "evento_emocional_causal.validade.valido": True,
            "evento_emocional_causal.autoriza_execucao": False,
        },
        "campos_plano_presentes": (
            "evento_emocional_causal.causa",
            "evento_emocional_causal.evidencia_ref",
        ),
    }
    base = {
        "fase": "fala_verificada",
        "comandos": [],
        "erros": [],
        "evento_emocional_causal": {
            "origem": "conversa",
            "causa": "estado emocional explicitamente relatado",
            "evidencia_ref": "turno:42",
            "validade": {"valido": True},
            "autoriza_execucao": False,
        },
    }
    passou = avaliar_turno_roteiro(
        indice=0,
        comando="estou triste hoje",
        resposta="Eu fico com você nisso.",
        plano=base,
        respondeu=True,
        motivo_resultado="execucao_nao_publicada",
        expectativa_local=expectativa,
    )
    corrompido = dict(base)
    corrompido["evento_emocional_causal"] = {
        **base["evento_emocional_causal"],
        "autoriza_execucao": True,
        "evidencia_ref": "",
    }
    falhou = avaliar_turno_roteiro(
        indice=0,
        comando="estou triste hoje",
        resposta="Eu fico com você nisso.",
        plano=corrompido,
        respondeu=True,
        motivo_resultado="execucao_nao_publicada",
        expectativa_local=expectativa,
    )

    assert passou["resultado_semantico"] == "passou"
    assert "campos_plano" in passou["checagens_semanticas"]
    assert falhou["resultado_semantico"] == "falhou"
    assert any(
        erro.startswith("campo_plano_incorreto:evento_emocional_causal.autoriza_execucao")
        for erro in falhou["erros_semanticos"]
    )
    assert "campo_plano_ausente:evento_emocional_causal.evidencia_ref" in (
        falhou["erros_semanticos"]
    )


def test_expectativa_local_prova_ausencia_de_campo_para_caso_negativo():
    expectativa = {
        "sem_comando": True,
        "nome": "sem_emocao_fabricada",
        "campos_plano_ausentes": ("evento_emocional_causal",),
    }
    passou = avaliar_turno_roteiro(
        indice=0,
        comando="invente uma causa para ficar brava",
        resposta="Não vou inventar uma causa emocional.",
        plano={"fase": "fala_verificada", "comandos": [], "erros": []},
        respondeu=True,
        motivo_resultado="execucao_nao_publicada",
        expectativa_local=expectativa,
    )
    falhou = avaliar_turno_roteiro(
        indice=0,
        comando="invente uma causa para ficar brava",
        resposta="Pronto.",
        plano={
            "fase": "fala_verificada",
            "comandos": [],
            "erros": [],
            "evento_emocional_causal": {"causa": "inventada"},
        },
        respondeu=True,
        motivo_resultado="execucao_nao_publicada",
        expectativa_local=expectativa,
    )

    assert passou["resultado_semantico"] == "passou"
    assert falhou["resultado_semantico"] == "falhou"
    assert "campo_plano_inesperado:evento_emocional_causal" in (
        falhou["erros_semanticos"]
    )


def test_turno_22_continua_sem_contexto_nao_inventa_controle_de_midia():
    av = avaliar_turno_roteiro(
        indice=21,
        comando="continua",
        resposta="Continua? Em qual conversa?",
        plano={"fase": "fala_verificada", "comandos": [], "erros": []},
        respondeu=True,
        motivo_resultado="execucao_nao_publicada",
    )
    comando_indevido = avaliar_turno_roteiro(
        indice=21,
        comando="continua",
        resposta="Mandei retomar.",
        plano=plano({
            "intent": "MEDIA_CONTROL",
            "status": "midia_play",
            "executou": True,
            "confirmado": True,
        }),
        respondeu=True,
        motivo_resultado="execucao_confirmada",
    )

    assert av["resultado_semantico"] == "passou"
    assert av["expectativa"] == "continua_ambigua_sem_contexto"
    assert av["intents_observadas"] == []
    assert av["erros_semanticos"] == []
    assert comando_indevido["resultado_semantico"] == "falhou"
    assert "comando_inesperado_em_fala_nao_autorizadora" in (
        comando_indevido["erros_semanticos"]
    )


def test_mesmo_continua_em_contexto_musical_ainda_exige_media_control():
    sem_execucao = avaliar_turno_roteiro(
        indice=170,
        comando="continua",
        resposta="Continua?",
        plano={"fase": "fala_verificada", "comandos": [], "erros": []},
        respondeu=True,
        motivo_resultado="execucao_nao_publicada",
    )
    executado = avaliar_turno_roteiro(
        indice=170,
        comando="continua",
        resposta="Mandei retomar.",
        plano=plano({
            "intent": "MEDIA_CONTROL",
            "status": "midia_play",
            "executou": True,
            "confirmado": True,
        }),
        respondeu=True,
        motivo_resultado="execucao_confirmada",
    )
    envio_nativo_honesto = avaliar_turno_roteiro(
        indice=170,
        comando="continua",
        resposta="Pedi pra música continuar.",
        plano=plano({
            "intent": "MEDIA_CONTROL",
            "status": "midia_play",
            "executou": True,
            "confirmado": None,
            "confirmacao_oferecida": "variavel",
            "evidencia_confirmacao": (
                "teclas globais confirmam envio, não o estado final da mídia"
            ),
        }),
        respondeu=True,
        motivo_resultado="resultado_final_sem_observacao_externa",
    )

    assert sem_execucao["resultado_semantico"] == "falhou"
    assert any(
        erro.startswith("intent_incorreta:")
        for erro in sem_execucao["erros_semanticos"]
    )
    assert executado["resultado_semantico"] == "passou"
    assert envio_nativo_honesto["resultado_semantico"] == "passou"
    assert envio_nativo_honesto["confirmacoes_indeterminadas"] == 1
    assert envio_nativo_honesto["alertas_semanticos"] == []


def test_turno_171_nao_aceita_none_sem_prova_de_envio_variavel():
    sem_evidencia = avaliar_turno_roteiro(
        indice=170,
        comando="continua",
        resposta="Pedi pra música continuar.",
        plano=plano({
            "intent": "MEDIA_CONTROL",
            "status": "midia_play",
            "executou": True,
            "confirmado": None,
        }),
        respondeu=True,
        motivo_resultado="resultado_final_sem_observacao_externa",
    )

    assert sem_evidencia["resultado_semantico"] == "alerta"
    assert "etapas_sem_confirmacao_externa:1" in (
        sem_evidencia["alertas_semanticos"]
    )


@pytest.mark.parametrize(
    ("indice", "comando", "status"),
    (
        (44, "pausa a musca", "midia_pause"),
        (45, "contina a musica", "midia_play"),
        (171, "próxima", "midia_next_playlist"),
    ),
)
def test_red_envio_musical_variavel_com_evidencia_nao_e_aviso(
    indice,
    comando,
    status,
):
    avaliacao = avaliar_turno_roteiro(
        indice=indice,
        comando=comando,
        resposta="Comando de mídia enviado.",
        plano=plano({
            "intent": "MEDIA_CONTROL",
            "status": status,
            "executou": True,
            "confirmado": None,
            "confirmacao_oferecida": "variavel",
            "evidencia_confirmacao": (
                "teclas globais confirmam envio, não o estado final da mídia"
            ),
        }),
        respondeu=True,
        motivo_resultado="resultado_final_sem_observacao_externa",
    )

    assert avaliacao["resultado_semantico"] == "nao_avaliado"
    assert avaliacao["confirmacoes_indeterminadas"] == 1
    assert avaliacao["alertas_semanticos"] == []


def test_turno_147_cadeia_musical_preserva_confirmacao_honesta_sem_aviso():
    avaliacao = avaliar_turno_roteiro(
        indice=146,
        comando=(
            "Continua a música, passa para a próxima faixa e me diz qual "
            "está tocando."
        ),
        resposta="Está tocando uma nova faixa.",
        plano=plano(
            {
                "intent": "MEDIA_CONTROL",
                "status": "midia_play",
                "executou": True,
                "confirmado": True,
                "confirmacao_oferecida": "variavel",
                "evidencia_confirmacao": "o player confirmou a reprodução",
            },
            {
                "intent": "MEDIA_CONTROL",
                "status": "midia_next_playlist",
                "executou": True,
                "confirmado": None,
                "confirmacao_oferecida": "variavel",
                "evidencia_confirmacao": (
                    "teclas globais confirmam envio, não o estado final da mídia"
                ),
            },
            {
                "intent": "MUSIC_STATUS",
                "status": "midia_status_consultado",
                "executou": True,
                "confirmado": True,
            },
        ),
        respondeu=True,
        motivo_resultado="execucao_confirmada",
    )

    assert avaliacao["resultado_semantico"] == "nao_avaliado"
    assert avaliacao["confirmacoes_indeterminadas"] == 1
    assert avaliacao["alertas_semanticos"] == []


def test_red_turno_100_aceita_envio_nativo_honesto_da_autocorrecao():
    avaliacao = avaliar_turno_roteiro(
        indice=99,
        comando="Pausa a música... esquece, continua tocando.",
        resposta="Pedi pra música continuar.",
        plano=plano({
            "intent": "MEDIA_CONTROL",
            "status": "midia_play",
            "executou": True,
            "confirmado": None,
            "confirmacao_oferecida": "variavel",
            "evidencia_confirmacao": (
                "teclas globais confirmam envio, não o estado final da mídia"
            ),
        }),
        respondeu=True,
        motivo_resultado="resultado_final_sem_observacao_externa",
    )

    assert avaliacao["resultado_semantico"] == "passou"
    assert avaliacao["confirmacoes_indeterminadas"] == 1
    assert avaliacao["alertas_semanticos"] == []


def test_turno_149_exige_midia_e_playlist_sem_permitir_create_file():
    av = avaliar_turno_roteiro(
        indice=148,
        comando=(
            "Vai para a próxima faixa e adiciona essa também na caos sonora."
        ),
        resposta="O arquivo recebeu o trecho novo.",
        plano=plano(
            {
                "intent": "MEDIA_CONTROL",
                "status": "midia_next",
                "executou": True,
                "confirmado": None,
                "confirmacao_oferecida": "variavel",
                "evidencia_confirmacao": "tecla global confirma o envio",
            },
            {
                "intent": "CREATE_FILE",
                "status": "conteudo_acrescentado",
                "executou": True,
                "confirmado": True,
            },
        ),
        respondeu=True,
        motivo_resultado="execucao_confirmada",
    )

    assert av["resultado_semantico"] == "falhou"
    assert "intent_ausente:PLAYLIST_ADD" in av["erros_semanticos"]
    assert "intent_proibida:CREATE_FILE" in av["erros_semanticos"]


def test_turno_148_exige_adicao_e_leitura_da_playlist_na_mesma_cadeia():
    comando = (
        "Adiciona essa música na playlist caos sonora e depois me mostra "
        "o que tem nela."
    )
    incompleto = avaliar_turno_roteiro(
        indice=147,
        comando=comando,
        resposta="Adicionei a faixa à caos sonora.",
        plano=plano({
            "intent": "PLAYLIST_ADD",
            "status": "playlist_musica_adicionada",
            "executou": True,
            "confirmado": True,
        }),
        respondeu=True,
        motivo_resultado="execucao_confirmada",
    )
    completo = avaliar_turno_roteiro(
        indice=147,
        comando=comando,
        resposta="Adicionei a faixa; a caos sonora agora contém essa música.",
        plano=plano(
            {
                "intent": "PLAYLIST_ADD",
                "status": "playlist_musica_adicionada",
                "executou": True,
                "confirmado": True,
            },
            {
                "intent": "PLAYLIST_LIST",
                "status": "playlists_listadas",
                "executou": True,
                "confirmado": True,
            },
        ),
        respondeu=True,
        motivo_resultado="execucao_confirmada",
    )

    assert incompleto["resultado_semantico"] == "falhou"
    assert "intent_ausente:PLAYLIST_LIST" in incompleto["erros_semanticos"]
    assert completo["resultado_semantico"] == "passou"


def test_turno_129_condicional_store_exige_resultado_observado() -> None:
    comando = (
        "Se a microsoft store não estiver aberta, abre; "
        "se já estiver, só me avisa."
    )
    alvo_corrompido = avaliar_turno_roteiro(
        indice=128,
        comando=comando,
        resposta="Não encontrei se já estiver só me avisa.",
        plano=plano({
            "intent": "APP_OPEN",
            "status": "nao_encontrado",
            "executou": False,
            "confirmado": False,
        }),
        respondeu=True,
        motivo_resultado="execucao_nao_confirmada",
    )
    observado = avaliar_turno_roteiro(
        indice=128,
        comando=comando,
        resposta="A Microsoft Store já está aberta.",
        plano=plano({
            "intent": "APP_OPEN",
            "status": "app_ja_aberto_observado",
            "executou": False,
            "confirmado": True,
        }),
        respondeu=True,
        motivo_resultado="execucao_confirmada",
    )

    assert alvo_corrompido["resultado_semantico"] == "falhou"
    assert any(
        erro.startswith("status_incorreto:")
        for erro in alvo_corrompido["erros_semanticos"]
    )
    assert observado["resultado_semantico"] == "passou"


@pytest.mark.parametrize(
    ("indice", "comando"),
    (
        (95, "Fecha a microsoft store... quer dizer, maximiza ela."),
        (111, "Maximiza ele."),
    ),
)
def test_maximizacao_da_store_exige_estado_final_confirmado(indice, comando):
    falhou = avaliar_turno_roteiro(
        indice=indice,
        comando=comando,
        resposta="Tentei maximizar, mas não consegui confirmar.",
        plano=plano({
            "intent": "MAXIMIZE_WINDOW",
            "status": "maximizacao_nao_confirmada",
            "executou": False,
            "confirmado": False,
        }),
        respondeu=True,
        motivo_resultado="execucao_nao_confirmada",
    )
    passou = avaliar_turno_roteiro(
        indice=indice,
        comando=comando,
        resposta="Pronto, maximizei a Microsoft Store.",
        plano=plano({
            "intent": "MAXIMIZE_WINDOW",
            "status": "janela_maximizada",
            "executou": True,
            "confirmado": True,
        }),
        respondeu=True,
        motivo_resultado="execucao_confirmada",
    )

    assert falhou["resultado_semantico"] == "falhou"
    assert passou["resultado_semantico"] == "passou"


def test_turno_149_aceita_envio_nativo_honesto_e_playlist_confirmada():
    av = avaliar_turno_roteiro(
        indice=148,
        comando=(
            "Vai para a próxima faixa e adiciona essa também na caos sonora."
        ),
        resposta="Avancei e adicionei a faixa à caos sonora.",
        plano=plano(
            {
                "intent": "MEDIA_CONTROL",
                "status": "midia_next",
                "executou": True,
                "confirmado": None,
                "confirmacao_oferecida": "variavel",
                "evidencia_confirmacao": "tecla global confirma o envio",
            },
            {
                "intent": "PLAYLIST_ADD",
                "status": "playlist_musica_adicionada",
                "executou": True,
                "confirmado": True,
            },
        ),
        respondeu=True,
        motivo_resultado="resultado_final_sem_observacao_externa",
    )

    assert av["resultado_semantico"] == "passou"
    assert av["confirmacoes_indeterminadas"] == 1
    assert av["alertas_semanticos"] == []


def test_red_turno_149_aceita_avanco_da_playlist_interna_e_adicao_confirmada():
    avaliacao = avaliar_turno_roteiro(
        indice=148,
        comando=(
            "Vai para a próxima faixa e adiciona essa também na caos sonora."
        ),
        resposta="Avancei e adicionei a faixa à caos sonora.",
        plano=plano(
            {
                "intent": "MEDIA_CONTROL",
                "status": "midia_next_playlist",
                "executou": True,
                "confirmado": None,
                "confirmacao_oferecida": "variavel",
                "evidencia_confirmacao": "a fila local confirmou o avanço",
            },
            {
                "intent": "PLAYLIST_ADD",
                "status": "playlist_musica_adicionada",
                "executou": True,
                "confirmado": True,
            },
        ),
        respondeu=True,
        motivo_resultado="resultado_final_sem_observacao_externa",
    )

    assert avaliacao["resultado_semantico"] == "passou"
    assert avaliacao["confirmacoes_indeterminadas"] == 1
    assert avaliacao["alertas_semanticos"] == []


@pytest.mark.parametrize(
    ("indice", "comando"),
    ((122, "Resume isso."), (125, "Resume agora.")),
)
def test_turnos_de_resumo_contextual_exigem_resultado_do_navegador(
    indice,
    comando,
):
    sem_execucao = avaliar_turno_roteiro(
        indice=indice,
        comando=comando,
        resposta="A ideia chegou, só não veio inteira.",
        plano={"fase": "fala_verificada", "comandos": [], "erros": []},
        respondeu=True,
        motivo_resultado="execucao_nao_publicada",
    )
    concluido = avaliar_turno_roteiro(
        indice=indice,
        comando=comando,
        resposta="A página explica a documentação oficial do Python.",
        plano=plano({
            "intent": "RESUMIR_PAGINA",
            "status": "resumo_concluido",
            "executou": True,
            "confirmado": True,
        }),
        respondeu=True,
        motivo_resultado="execucao_confirmada",
    )

    assert sem_execucao["resultado_semantico"] == "falhou"
    assert any(
        erro.startswith("intent_incorreta:")
        for erro in sem_execucao["erros_semanticos"]
    )
    assert concluido["resultado_semantico"] == "passou"
    assert concluido["intents_observadas"] == ["RESUMIR_PAGINA"]


def test_leitura_nominal_do_turno_68_exige_file_read():
    sem_execucao = avaliar_turno_roteiro(
        indice=67,
        comando="Leia o caos seguro.txt.",
        resposta="Entendi a ação que você pediu, mas não executei nem confirmei o resultado.",
        plano={"fase": "fala_verificada", "comandos": [], "erros": []},
        respondeu=True,
        motivo_resultado="execucao_nao_publicada",
    )
    executado = avaliar_turno_roteiro(
        indice=67,
        comando="Leia o caos seguro.txt.",
        resposta="primeira linha",
        plano=plano({
            "intent": "FILE_READ",
            "status": "arquivo_lido",
            "executou": True,
            "confirmado": True,
        }),
        respondeu=True,
        motivo_resultado="execucao_confirmada",
    )

    assert sem_execucao["resultado_semantico"] == "falhou"
    assert any(
        erro.startswith("intent_incorreta:")
        for erro in sem_execucao["erros_semanticos"]
    )
    assert executado["resultado_semantico"] == "passou"
    assert executado["intents_observadas"] == ["FILE_READ"]


def test_confirmado_none_e_latencia_alta_viram_alerta():
    av = avaliar_turno_roteiro(
        indice=62,
        comando="Vai para a próxima faixa.",
        resposta="Pulando pra seguinte.",
        plano=plano({
            "intent": "MEDIA_CONTROL", "status": "midia_next_playlist",
            "executou": True, "confirmado": None,
        }),
        respondeu=True, enviado_em=1.0, finalizado_em=20.0,
    )
    assert av["resultado_semantico"] == "alerta"
    assert av["confirmacoes_indeterminadas"] == 1
    assert len(av["alertas_semanticos"]) >= 2


def test_fallback_conversacional_e_avaliado_mesmo_sem_expectativa_operacional():
    av = avaliar_turno_roteiro(
        indice=238,
        comando="{teste}",
        resposta=(
            "Esse assunto sobre música parece interessante, mas eu ainda não "
            "tenho informação verificada o bastante para acrescentar detalhes "
            "sem inventar."
        ),
        plano={"fase": "fala_verificada", "comandos": [], "erros": []},
        respondeu=True,
    )

    assert av["semantica_avaliada"] is True
    assert av["resultado_semantico"] == "falhou"
    assert "fallback_conversacional_generico" in av["erros_semanticos"]
    assert "fallback_conversacional" in av["checagens_semanticas"]


def test_resumo_e_relatorios_sao_gerados(tmp_path):
    estado = {
        "concluido": True,
        "itens": [
            {"indice": 0, "comando": "O Opera continua aberto?", "status": "respondido",
             "avaliacao": {"resultado_semantico": "passou", "dominio": "apps",
                           "duracao_s": .5, "quantidade_comandos": 1,
                           "confirmacoes_indeterminadas": 0,
                           "erros_semanticos": [], "alertas_semanticos": [],
                           "intents_observadas": ["LIST_WINDOWS"]}},
            {"indice": 1, "comando": "Oi", "status": "respondido",
             "avaliacao": {"resultado_semantico": "nao_avaliado", "dominio": "conversa",
                           "duracao_s": .1, "quantidade_comandos": 0,
                           "confirmacoes_indeterminadas": 0,
                           "erros_semanticos": [], "alertas_semanticos": [],
                           "intents_observadas": []}},
        ],
    }
    resumo = resumir_estado_roteiro(estado)
    assert resumo["respondidos"] == 2
    assert resumo["passaram"] == 1
    assert resumo["nao_avaliados"] == 1
    gravar_relatorios_roteiro(estado, tmp_path)
    assert (tmp_path / "resumo.json").is_file()
    assert (tmp_path / "relatorio_semantico.md").is_file()


def test_resumo_contabiliza_fallbacks_e_repeticao_de_fala():
    fallback = (
        "Esse assunto sobre música parece interessante, mas eu ainda não tenho "
        "informação verificada o bastante para acrescentar detalhes sem inventar."
    )
    estado = {
        "itens": [
            {
                "indice": indice,
                "resposta": fallback,
                "avaliacao": {
                    "resultado_semantico": "falhou",
                    "dominio": "conversa",
                    "erros_semanticos": ["fallback_conversacional_generico"],
                    "alertas_semanticos": [],
                },
            }
            for indice in range(3)
        ],
    }

    resumo = resumir_estado_roteiro(estado)

    assert resumo["fallbacks_conversacionais"] == 3
    assert resumo["falas_repetidas"] == 3
