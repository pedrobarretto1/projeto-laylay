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
