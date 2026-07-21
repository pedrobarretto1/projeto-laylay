from __future__ import annotations

from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
from mente_laylay.cognicao.decisao_turno import (
    consolidar_arbitragem,
    filtrar_comandos_pelo_turno,
)
from mente_laylay.cognicao.plano_turno import planejar_turno


def _turno(modalidade: str, *, autoriza: bool) -> dict:
    return {
        "id": 101,
        "modalidade": modalidade,
        "modalidade_geral": modalidade,
        "ato_principal": modalidade,
        "autoriza_execucao": autoriza,
        "confianca": 0.96,
        "segmentos": [{
            "modalidade": modalidade,
            "texto": "abre o youtube" if autoriza else "você conhece o youtube?",
        }],
    }


def _contexto_resolucao(turno: dict, intent_ia: dict, registros: list) -> dict:
    return {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "refinar_contexto_mental": lambda _texto: None,
        "extrair_agendamento": lambda _texto: None,
        "extrair_acao_agendada": lambda _texto: None,
        "texto_cancela_acao_agora": lambda _texto: False,
        "texto_depende_de_contexto": lambda _texto: False,
        "detectar_intencao_deterministica": lambda _texto: None,
        "resolver_comando_contextual_forcado": lambda _texto: None,
        "resolver_repeticao_ultima_acao": lambda _texto: None,
        "tentar_intencao_ai_primeiro": lambda _texto: intent_ia,
        "registrar_arbitragem_turno": lambda texto, resultado: registros.append(
            (texto, resultado)
        ),
        "turno_atual": turno,
        "retrato_turno_atual": {},
    }


def test_conversa_recebe_dono_social_sem_autorizacao_de_acao() -> None:
    turno = _turno("pergunta", autoriza=False)
    plano = planejar_turno("você conhece o YouTube?", turno=turno, mente={})

    assert plano["decisao_turno"]["proprietario"] == "conversa"
    assert plano["decisao_turno"]["permite_acao"] is False


def test_comando_explicito_recebe_dono_operacional() -> None:
    turno = _turno("comando", autoriza=True)
    plano = planejar_turno("abre o YouTube", turno=turno, mente={})

    assert plano["decisao_turno"]["proprietario"] == "operacional"
    assert plano["decisao_turno"]["permite_acao"] is True


def test_comando_json_da_ia_e_bloqueado_em_conversa() -> None:
    turno = _turno("pergunta", autoriza=False)
    plano = planejar_turno("você conhece o YouTube?", turno=turno, mente={})
    resultado = filtrar_comandos_pelo_turno(
        [{"intent": "OPEN_URL", "params": {"url": "https://youtube.com"}}],
        turno=turno,
        plano=plano,
        retrato={},
    )

    assert resultado["comandos"] == []
    assert resultado["rejeitados"][0]["intent"] == "OPEN_URL"
    assert "não autorizou" in resultado["rejeitados"][0]["motivo"]


def test_comando_json_continua_permitido_em_pedido_explicito() -> None:
    turno = _turno("comando", autoriza=True)
    plano = planejar_turno("abre o YouTube", turno=turno, mente={})
    comando = {"intent": "OPEN_URL", "params": {"url": "https://youtube.com"}}
    resultado = filtrar_comandos_pelo_turno(
        [comando], turno=turno, plano=plano, retrato={},
    )

    assert resultado["comandos"] == [comando]
    assert resultado["rejeitados"] == []


def test_detector_sem_candidato_nao_revoga_pedido_explicito() -> None:
    turno = _turno("comando", autoriza=True)
    plano = planejar_turno("abre o YouTube", turno=turno, mente={})

    contrato = consolidar_arbitragem(
        plano["decisao_turno"],
        {"decisao": None, "rejeitados": [], "origem": ""},
    )

    assert contrato["permite_acao"] is True
    assert contrato["status"] == "aguardando_intencao"


def test_intencao_da_ia_tambem_passa_pelo_arbitro_em_conversa() -> None:
    registros: list = []
    turno = _turno("conversa", autoriza=False)
    ctx = _contexto_resolucao(
        turno,
        {"intent": "OPEN_URL", "params": {"url": "https://rockstargames.com"}},
        registros,
    )

    intent, rota = resolver_intencao(
        "você viu que vai sair o GTA 6?", "chat", ctx,
    )

    assert intent is None
    assert rota == ""
    assert registros[-1][1]["decisao"] is None
    assert registros[-1][1]["rejeitados"]


def test_intencao_da_ia_ainda_executa_quando_o_pedido_e_explicito() -> None:
    registros: list = []
    turno = _turno("comando", autoriza=True)
    esperado = {"intent": "OPEN_URL", "params": {"url": "https://youtube.com"}}
    ctx = _contexto_resolucao(turno, esperado, registros)

    intent, rota = resolver_intencao("abre o YouTube", "chat", ctx)

    assert intent == esperado
    assert rota == "ia-first-arbitrada"
    assert registros[-1][1]["contrato_decisao"]["proprietario"] == "operacional"
