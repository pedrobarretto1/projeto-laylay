from __future__ import annotations

from mente_laylay.cognicao.arbitro_turno import CandidatoDecisao, arbitrar_turno
from mente_laylay.especialistas.coordenador import (
    construir_parecer_especialistas,
    registrar_resultado_operacional,
)
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.emocoes.leitura_usuario import analisar_funcao_comunicativa
from mente_laylay.memoria_mental.contexto_integrado import resumo_mente_integrada_para_prompt


def _montar(texto: str) -> tuple[dict, dict, dict]:
    turno = classificar_modalidade_turno(texto)
    funcao = analisar_funcao_comunicativa(texto)
    retrato, _ = construir_retrato_turno(
        texto,
        turno=turno,
        mente={},
        contexto_perceptivo={},
        agora=100.0,
    )
    especialistas = construir_parecer_especialistas(
        texto,
        turno=turno,
        funcao_comunicativa=funcao,
        retrato=retrato,
    )
    turno["especialistas"] = especialistas
    return turno, retrato, especialistas


def test_mensagem_mista_separa_pareceres_sem_criar_duas_mentes() -> None:
    turno, _retrato, especialistas = _montar(
        "estou bem sim lay, pode apagar a luz para mim"
    )

    assert turno["modalidade_geral"] == "misto"
    assert especialistas["coordenacao"]["modo"] == "integrado"
    assert especialistas["coordenacao"]["memoria_compartilhada"] is True
    assert especialistas["coordenacao"]["voz_unica"] is True
    assert especialistas["social"]["texto"] == "estou bem sim lay"
    assert especialistas["social"]["pode_executar"] is False
    assert especialistas["operacional"]["texto"] == "pode apagar a luz para mim"
    assert especialistas["operacional"]["autoriza_execucao"] is True


def test_pergunta_sobre_acao_nao_recebe_autorizacao_operacional() -> None:
    turno, retrato, especialistas = _montar("não abre o quê?")
    assert especialistas["operacional"]["autoriza_execucao"] is False

    decisao = arbitrar_turno(
        "não abre o quê?",
        [CandidatoDecisao(
            "comando_explicito",
            {"intent": "APP_OPEN", "params": {"nome_app": "que"}},
            "deterministico",
            0.98,
        )],
        turno=turno,
        retrato=retrato,
    )
    assert decisao["decisao"] is None
    assert "especialista operacional" in decisao["rejeitados"][0]["motivo"]


def test_consulta_somente_leitura_nao_e_vetada_por_ter_forma_de_pergunta() -> None:
    texto = "vai chover hoje?"
    turno, retrato, especialistas = _montar(texto)

    assert especialistas["operacional"]["autoriza_execucao"] is False
    decisao = arbitrar_turno(
        texto,
        [CandidatoDecisao(
            "comando_explicito",
            {"intent": "WEATHER", "params": {}},
            "deterministico",
            0.90,
        )],
        turno=turno,
        retrato=retrato,
    )

    assert decisao["decisao"] == {"intent": "WEATHER", "params": {}}


def test_playlist_add_com_faixa_atual_e_autorizado_sem_memoria_anterior() -> None:
    texto = "coloca essa musica na playlist rei do pop"
    turno, retrato, especialistas = _montar(texto)

    assert retrato["referencia_resolvida"]["origem"] == "reprodutor_atual"
    assert especialistas["operacional"]["requer_esclarecimento"] is False
    assert especialistas["operacional"]["autoriza_execucao"] is True

    decisao = arbitrar_turno(
        texto,
        [CandidatoDecisao(
            "comando_explicito",
            {"intent": "PLAYLIST_ADD", "params": {"nome_playlist": "rei do pop"}},
            "deterministico-explicito",
            0.98,
        )],
        turno=turno,
        retrato=retrato,
    )
    assert decisao["decisao"] == {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "rei do pop"},
    }


def test_playlist_add_com_a_playlist_mantem_referencia_ao_player_atual() -> None:
    texto = "coloca essa musica a playlist rei do pop"
    turno, retrato, especialistas = _montar(texto)

    assert retrato["operacao_explicita"] == "playlist_adicionar"
    assert retrato["referencia_resolvida"]["origem"] == "reprodutor_atual"
    assert especialistas["operacional"]["autoriza_execucao"] is True


def test_resultado_operacional_e_consultado_sem_gerar_segunda_fala() -> None:
    _turno, _retrato, especialistas = _montar("tô cansado, liga o ventilador")
    atualizado = registrar_resultado_operacional(especialistas, [{
        "intent": "IOT_CONTROL",
        "alvo": "tomada_ventilador",
        "status": "ligado",
        "executou": True,
        "confirmado": True,
    }])

    assert atualizado["operacional"]["resultado_disponivel"] is True
    assert atualizado["social"]["resultado_operacional_consultado"] is True
    assert atualizado["coordenacao"]["consulta_concluida"] is True
    assert atualizado["coordenacao"]["voz_unica"] is True


def test_plano_e_prompt_recebem_os_dois_pareceres() -> None:
    texto = "tô cansado, liga o ventilador"
    turno, retrato, especialistas = _montar(texto)
    plano = planejar_turno(texto, turno=turno, mente={})
    prompt = resumo_mente_integrada_para_prompt(
        texto_usuario=texto,
        ctx={},
        percepcao={},
        mente={
            "turno_atual": turno,
            "plano_turno_atual": plano,
            "retrato_turno_atual": retrato,
        },
    )

    assert plano["modo_coordenacao"] == "integrado"
    assert plano["especialistas"] == especialistas
    assert "ESPECIALISTAS DA MESMA MENTE" in prompt
    assert "autoriza_execução=True" in prompt
    assert "uma única fala" in prompt


def test_preferencia_forma_coalizao_sem_habilidade_vencedora() -> None:
    texto = "eu gosto de rock"
    turno = classificar_modalidade_turno(texto)
    turno["aprendizados_explicitos"] = [{
        "tipo": "preferencia", "valor": "rock", "confianca": 0.98,
    }]
    turno["tema_factual"] = "rock"
    funcao = analisar_funcao_comunicativa(texto)
    retrato, _ = construir_retrato_turno(
        texto, turno=turno, mente={}, contexto_perceptivo={}, agora=100.0,
    )
    especialistas = construir_parecer_especialistas(
        texto, turno=turno, funcao_comunicativa=funcao, retrato=retrato,
    )
    turno["especialistas"] = especialistas
    plano = planejar_turno(texto, turno=turno, mente={})
    prompt = resumo_mente_integrada_para_prompt(
        texto_usuario=texto, ctx={}, percepcao={},
        mente={"turno_atual": turno, "plano_turno_atual": plano},
    )

    deliberacao = especialistas["deliberacao"]
    assert deliberacao["arquitetura"] == "consenso_distribuido"
    assert deliberacao["regras"]["sem_vencedor_isolado"] is True
    assert {"conversa", "memoria_aprendizado", "pesquisa_factual", "personalidade"} <= set(
        deliberacao["participantes"]
    )
    assert "DELIBERAÇÃO COLETIVA DAS HABILIDADES" in prompt
    assert "Nenhuma habilidade vence as demais" in prompt
