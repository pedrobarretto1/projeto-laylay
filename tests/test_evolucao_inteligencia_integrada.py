from __future__ import annotations

from mente_laylay.especialistas.capacidades import consultar_capacidade, intents_registradas
from mente_laylay.especialistas.conversa import construir_parecer_conversa
from mente_laylay.especialistas.operacional import (
    avaliar_candidato_operacional,
    construir_parecer_operacional,
)
from mente_laylay.memoria_mental.assunto_estruturado import atualizar_assunto_estruturado
from mente_laylay.memoria_mental.correcoes_interpretacao import (
    abrir_correcao_interpretacao,
    concluir_correcao_interpretacao,
)
from mente_laylay.memoria_mental.resultado_acao import normalizar_resultado_acao
from mente_laylay.memoria_mental.trilha_turno import registrar_etapa_turno


def test_registro_central_conhece_iot_e_rejeita_intent_inventada() -> None:
    assert "IOT_CONTROL" in intents_registradas()
    assert consultar_capacidade("IOT_CONTROL")["disponivel"] is True
    assert consultar_capacidade("INVENTEI_UMA_ACAO")["disponivel"] is False


def test_referencia_ambigua_bloqueia_parecer_operacional() -> None:
    parecer = construir_parecer_operacional(
        "desliga ela",
        turno={
            "ato_principal": "comando",
            "modalidade_geral": "comando",
            "texto_operacional": "desliga ela",
            "confianca": 0.96,
        },
        retrato={"referencia_tipo": "pronome", "referencia_resolvida": {}},
    )
    assert parecer["confiancas"]["acao"] == 0.96
    assert parecer["confiancas"]["referencia"] == 0.25
    assert parecer["requer_esclarecimento"] is True
    assert parecer["autoriza_execucao"] is False


def test_capacidade_entra_em_modo_degradado_quando_componente_cai() -> None:
    avaliacao = avaliar_candidato_operacional(
        {
            "autoriza_execucao": True,
            "confianca": 0.95,
            "saude_componentes": {"iot": {"status": "indisponivel"}},
        },
        "IOT_CONTROL",
        confianca_candidato=0.98,
    )
    assert avaliacao["permitido"] is False
    assert avaliacao["motivo"] == "componente_indisponivel"


def test_resultado_universal_expoe_estado_final() -> None:
    resultado = normalizar_resultado_acao({
        "request_id": "abc-1",
        "intent": "IOT_CONTROL",
        "status": "ligado",
        "alvo": "lampada_quarto",
        "executou": True,
        "confirmado": True,
    }).como_dict()
    assert resultado["id_solicitacao"] == "abc-1"
    assert resultado["estado_final"] == "confirmado"
    assert resultado["alvo"] == "lampada_quarto"


def test_politica_social_nao_forca_pergunta_em_agradecimento() -> None:
    parecer = construir_parecer_conversa(
        "obrigado lay",
        turno={"modalidade_geral": "reacao", "texto_conversacional": "obrigado lay"},
        funcao_comunicativa={
            "funcao": "agradecimento",
            "permite_pergunta": False,
            "emocao_implicita": "gratidao",
        },
        operacional_ativo=False,
    )
    assert parecer["politica_resposta"] == "reconhecer_sem_pergunta"
    assert parecer["permite_pergunta"] is False


def test_assunto_pode_ser_encerrado_sem_apagar_historico() -> None:
    ativo = atualizar_assunto_estruturado(
        {}, "esse jogo é muito legal",
        turno={"ato_principal": "conversa"},
        retrato={"referencia_resolvida": {"tipo": "jogo", "nome": "Soulframe"}},
        agora=100.0,
    )
    encerrado = atualizar_assunto_estruturado(
        ativo, "vamos falar de outra coisa",
        turno={"ato_principal": "conversa"}, retrato={}, encerramento="topico", agora=110.0,
    )
    assert ativo["titulo"] == "Soulframe"
    assert encerrado["titulo"] == "Soulframe"
    assert encerrado["status"] == "encerrado"


def test_correcao_liga_intent_errada_a_execucao_correta() -> None:
    pendente = abrir_correcao_interpretacao(
        {
            "ultima_acao_intent": "MEDIA_CONTROL",
            "ultima_acao_alvo": "musica",
            "ultima_entrada": "pausa essa música",
        },
        "não Lay, pedi para colocar na playlist",
        eh_correcao=True,
        agora=100.0,
    )
    concluida = concluir_correcao_interpretacao(
        pendente,
        intent_correta="PLAYLIST_ADD",
        alvo_correto="anime",
        texto_execucao="não Lay, pedi para colocar na playlist",
        agora=101.0,
    )
    assert concluida["intent_errada"] == "MEDIA_CONTROL"
    assert concluida["texto_original"] == "pausa essa música"
    assert concluida["intent_correta"] == "PLAYLIST_ADD"
    assert concluida["status"] == "confirmada_por_execucao"


def test_correcao_nao_e_confirmada_por_execucao_de_turno_posterior() -> None:
    pendente = abrir_correcao_interpretacao(
        {
            "ultima_acao_intent": "LEARNING_QUERY",
            "ultima_entrada": "Do que eu gosto?",
        },
        "Na verdade, não considere jazz como algo que eu gosto.",
        eh_correcao=True,
        agora=100.0,
    )

    resultado = concluir_correcao_interpretacao(
        pendente,
        intent_correta="PEOPLE_REMEMBER",
        alvo_correto="Nanda",
        texto_execucao="Nanda é minha amiga.",
        agora=110.0,
    )

    assert resultado["status"] == "descartada_execucao_nao_correlacionada"
    assert "intent_correta" not in resultado


def test_trilha_de_turno_e_limitada_e_explica_fase() -> None:
    historico = []
    for indice in range(5):
        historico = registrar_etapa_turno(
            historico,
            {"id": indice, "texto_usuario": f"fala {indice}", "especialistas": {}},
            fase="planejado",
            limite=3,
        )
    assert len(historico) == 3
    assert historico[-1]["entrada"] == "fala 4"
    assert historico[-1]["fase"] == "planejado"
