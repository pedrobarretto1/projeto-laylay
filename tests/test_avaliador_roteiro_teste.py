# -*- coding: utf-8 -*-
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
