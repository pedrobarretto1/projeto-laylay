from __future__ import annotations

from datetime import datetime

import pytest

from mente_laylay.autonomia.motor_temporal import MotorTemporalRuntime
from mente_laylay.memoria_mental.consciencia_temporal import (
    atualizar_consciencia_temporal,
    estado_temporal_inicial,
    registrar_evento_visual_temporal,
    resumo_temporal_para_prompt,
    selecionar_eventos_temporais,
)
from mente_laylay.memoria_mental.interpretacao_temporal import (
    interpretar_referencia_temporal,
)


@pytest.fixture
def base_ts() -> float:
    return datetime(2026, 7, 21, 14, 0).timestamp()


def test_interpreta_data_extensa_numerica_relativa_e_horario(base_ts: float) -> None:
    extensa = interpretar_referencia_temporal(
        "tenho consulta dia 25 de agosto às 15h30", agora=base_ts,
    )
    numerica = interpretar_referencia_temporal(
        "a prova ficou para 03/08/2026 às 9h", agora=base_ts,
    )
    relativa = interpretar_referencia_temporal(
        "daqui a duas semanas tenho apresentação", agora=base_ts,
    )

    assert datetime.fromtimestamp(extensa["data_alvo_ts"]) == datetime(2026, 8, 25, 15, 30)
    assert datetime.fromtimestamp(numerica["data_alvo_ts"]) == datetime(2026, 8, 3, 9, 0)
    assert datetime.fromtimestamp(relativa["data_alvo_ts"]) == datetime(2026, 8, 4, 9, 0)
    assert extensa["confianca"] == 0.99


def test_interpreta_recorrencia_semanal_e_intervalo_mensal(base_ts: float) -> None:
    semanal = interpretar_referencia_temporal(
        "toda segunda tenho reunião às 10h", agora=base_ts,
    )
    mensal = interpretar_referencia_temporal(
        "a cada 3 meses tenho consulta", agora=base_ts,
    )

    assert semanal["recorrencia"] == {
        "frequencia": "semanal", "intervalo": 1, "dia_semana": 0,
    }
    assert datetime.fromtimestamp(semanal["data_alvo_ts"]) == datetime(2026, 7, 27, 10, 0)
    assert mensal["recorrencia"] == {"frequencia": "mensal", "intervalo": 3}
    assert datetime.fromtimestamp(mensal["data_alvo_ts"]) == datetime(2026, 10, 21, 9, 0)


def test_interpreta_dia_isolado_proximo_mes_e_mes_nomeado(base_ts: float) -> None:
    dia = interpretar_referencia_temporal("consulta dia 25", agora=base_ts)
    proximo_mes = interpretar_referencia_temporal("consulta no próximo mês", agora=base_ts)
    mes = interpretar_referencia_temporal("consulta em outubro", agora=base_ts)

    assert datetime.fromtimestamp(dia["data_alvo_ts"]) == datetime(2026, 7, 25, 9, 0)
    assert datetime.fromtimestamp(proximo_mes["data_alvo_ts"]) == datetime(2026, 8, 1, 9, 0)
    assert datetime.fromtimestamp(mes["data_alvo_ts"]) == datetime(2026, 10, 1, 9, 0)


def test_evento_recorrente_cria_proxima_ocorrencia_ao_concluir(base_ts: float) -> None:
    estado = atualizar_consciencia_temporal(
        None, "toda segunda tenho reunião às 10h", agora=base_ts,
    )
    alvo_original = estado["pendencias_vivas"][0]["data_alvo_ts"]
    conclusao_ts = datetime(2026, 7, 27, 11, 0).timestamp()

    estado = atualizar_consciencia_temporal(
        estado, "a reunião deu tudo certo", agora=conclusao_ts,
    )

    pendencia = estado["pendencias_vivas"][0]
    assert pendencia["status"] == "aberta"
    assert pendencia["ocorrencias_concluidas"] == 1
    assert pendencia["data_alvo_ts"] > alvo_original
    assert datetime.fromtimestamp(pendencia["data_alvo_ts"]) == datetime(2026, 8, 3, 10, 0)


def test_aprende_duracao_media_de_projetos(base_ts: float) -> None:
    estado = estado_temporal_inicial()
    estado = atualizar_consciencia_temporal(estado, "comecei o projeto alpha", agora=base_ts)
    estado = atualizar_consciencia_temporal(
        estado, "terminei o projeto alpha", agora=base_ts + 4 * 86400,
    )
    estado = atualizar_consciencia_temporal(
        estado, "comecei o projeto beta", agora=base_ts + 5 * 86400,
    )
    estado = atualizar_consciencia_temporal(
        estado, "terminei o projeto beta", agora=base_ts + 11 * 86400,
    )

    metrica = estado["estatisticas_duracao"]["projeto"]
    assert metrica["amostras"] == 2
    assert metrica["media_s"] == pytest.approx(5 * 86400)
    assert metrica["minimo_s"] == 4 * 86400
    assert metrica["maximo_s"] == 6 * 86400


def test_conclusao_ambigua_exige_identificacao_antes_de_fechar(base_ts: float) -> None:
    estado = atualizar_consciencia_temporal(None, "comecei o projeto alpha", agora=base_ts)
    estado = atualizar_consciencia_temporal(
        estado, "comecei o projeto beta", agora=base_ts + 10,
    )

    estado = atualizar_consciencia_temporal(estado, "terminei", agora=base_ts + 20)

    assert estado["evento_turno"]["tipo"] == "confirmacao_conclusao_necessaria"
    assert all(item["status"] == "aberta" for item in estado["pendencias_vivas"])

    estado = atualizar_consciencia_temporal(estado, "o projeto alpha", agora=base_ts + 30)

    assert estado["evento_turno"]["tipo"] == "conclusao_confirmada"
    status = {item["assunto"]: item["status"] for item in estado["pendencias_vivas"]}
    assert status["comecei o projeto alpha"] == "concluida"
    assert status["comecei o projeto beta"] == "aberta"


def test_memoria_visual_enriquece_linha_do_tempo_sem_concluir_pendencia(base_ts: float) -> None:
    estado = atualizar_consciencia_temporal(None, "comecei o projeto alpha", agora=base_ts)

    estado = registrar_evento_visual_temporal(
        estado,
        "A tela mostra o projeto alpha finalizado no VS Code",
        memoria_id="captura-1",
        contexto={"exe": "Code.exe"},
        agora=base_ts + 86400,
    )

    assert estado["linha_do_tempo"][-1]["status"] == "evidencia_conclusao"
    assert estado["linha_do_tempo"][-1]["origem"] == "memoria_visual"
    assert estado["pendencias_vivas"][0]["status"] == "aberta"
    assert estado["pendencias_vivas"][0]["memoria_visual_id"] == "captura-1"


def test_resumo_trata_media_como_estimativa_e_mostra_recorrencia(base_ts: float) -> None:
    estado = atualizar_consciencia_temporal(
        None, "toda segunda tenho reunião às 10h", agora=base_ts,
    )
    estado["estatisticas_duracao"]["evento"] = {
        "amostras": 3, "media_s": 2 * 86400,
    }

    resumo = resumo_temporal_para_prompt(
        estado, texto_usuario="e a reunião?", agora=base_ts,
    )

    assert "recorrência semanal" in resumo
    assert "média histórica aproximada" in resumo
    assert "nunca como prazo garantido" in resumo


def test_motor_avisa_prazo_e_so_marca_depois_da_fala(base_ts: float) -> None:
    estado = atualizar_consciencia_temporal(
        None, "amanhã tenho consulta", agora=base_ts,
    )
    agendadas = []
    runtime = MotorTemporalRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.update(novo),
        contexto_getter=lambda: {},
        agendar_fala=lambda *args, **kwargs: agendadas.append((args, kwargs)) or True,
        interacao_iniciada=lambda: True,
        conversa_ativa=lambda: False,
        clock=lambda: base_ts,
    )

    resultado = runtime.executar_ciclo()

    assert resultado["status"] == "agendado"
    assert agendadas[0][0][0] == "lembrete"
    assert estado["proatividade_temporal"] == {}
    agendadas[0][1]["ao_concluir"](True, "entregue")
    assert estado["proatividade_temporal"]


def test_motor_nao_puxa_acompanhamento_durante_frustracao(base_ts: float) -> None:
    estado = atualizar_consciencia_temporal(None, "comecei o projeto alpha", agora=base_ts)
    runtime = MotorTemporalRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.update(novo),
        contexto_getter=lambda: {
            "emocao_usuario": "frustração", "assunto": "programação projeto alpha",
        },
        agendar_fala=lambda *_args, **_kwargs: True,
        interacao_iniciada=lambda: True,
        conversa_ativa=lambda: False,
        clock=lambda: base_ts + 20 * 86400,
    )

    assert runtime.executar_ciclo()["status"] == "sem_candidato"


def test_perfil_com_recusas_aumenta_tempo_antes_do_acompanhamento(base_ts: float) -> None:
    estado = atualizar_consciencia_temporal(None, "comecei o projeto alpha", agora=base_ts)
    runtime = MotorTemporalRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.update(novo),
        contexto_getter=lambda: {
            "assunto": "programação projeto alpha",
            "perfil_proatividade": {"observacao": {"recusas_consecutivas": 1}},
        },
        agendar_fala=lambda *_args, **_kwargs: True,
        interacao_iniciada=lambda: True,
        conversa_ativa=lambda: False,
        clock=lambda: base_ts + 10 * 86400,
    )

    # Sem recusa, projetos são retomados depois de sete dias. Uma recusa
    # dobra esse tempo, portanto dez dias ainda é cedo.
    assert runtime.executar_ciclo()["status"] == "sem_candidato"


def test_evento_antigo_continua_recuperavel_mas_recencia_ordena_empates(base_ts: float) -> None:
    eventos = [
        {"assunto": "projeto alpha", "texto": "primeiro teste alpha", "ts": base_ts - 200 * 86400},
        {"assunto": "projeto alpha", "texto": "teste recente alpha", "ts": base_ts - 2 * 86400},
    ]

    escolhidos = selecionar_eventos_temporais(
        eventos, "como está o projeto alpha?", agora=base_ts, limite=2,
    )

    assert len(escolhidos) == 2
    assert escolhidos[-1]["texto"] == "teste recente alpha"


def test_tempo_vivido_conta_convivencia_ativa_e_nao_toda_ausencia(base_ts: float) -> None:
    estado = atualizar_consciencia_temporal(None, "oi lay", agora=base_ts)
    estado = atualizar_consciencia_temporal(estado, "vamos continuar", agora=base_ts + 120)
    estado = atualizar_consciencia_temporal(estado, "voltei", agora=base_ts + 7200)

    assert estado["tempo_vivido_total_s"] == 120
    assert estado["sessoes_total"] == 2
    assert estado["tempo_vivido_sessao_s"] == 0
