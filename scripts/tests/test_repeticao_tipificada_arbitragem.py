"""RED arquitetural — repetição tipada não pode perder no árbitro.

R1-C4 testa a concorrência entre duas rotas reais:

1. continuidade semântica -> candidato "comando_contextual";
2. retry canônico         -> candidato "repeticao".

O contrato não prescreve a implementação futura. A continuidade semântica
pode aprender LER, pode ceder (None), o retrato pode restringir intents ou o
árbitro pode rejeitar a herança incompatível.

A única regra soberana é:

    "Leia de novo."
        -> nunca pode terminar em IOT_CONTROL
           quando existe uma leitura compatível a repetir.
"""

from __future__ import annotations

from typing import Any

from mente_laylay.cognicao.arbitro_turno import (
    CandidatoDecisao,
    arbitrar_turno,
)
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.memoria_mental.compatibilidade_contexto import (
    resolver_repeticao_ultima_acao,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.continuidade_semantica import (
    resolver_continuidade_semantica,
)


INTENTS_LEITURA_COMPATIVEIS = {
    "EMAIL_READ",
    "FILE_READ",
}


def _registrar_email(
    estado: dict[str, Any],
) -> dict[str, Any]:
    return registrar_resultado_execucao(
        estado,
        {
            "intent": "EMAIL_READ",
            "params": {},
            "status": "executado",
            "executou": True,
            "confirmado": True,
            "origem": "email",
        },
        "Leia meus emails.",
        True,
        origem="email",
        status="executado",
    )


def _registrar_iot(
    estado: dict[str, Any],
) -> dict[str, Any]:
    return registrar_resultado_execucao(
        estado,
        {
            "intent": "IOT_CONTROL",
            "params": {
                "acao": "desligar",
                "alvo": "lampada_quarto",
            },
            "alvo": "lampada_quarto",
            "status": "dispositivo_desligado",
            "executou": True,
            "confirmado": True,
            "origem": "iot",
        },
        "Desliga a lâmpada.",
        True,
        origem="iot",
        status="dispositivo_desligado",
    )


def _estado_email_depois_iot() -> dict[str, Any]:
    estado = estado_mental_inicial()
    estado = _registrar_email(estado)
    estado = _registrar_iot(estado)
    return estado


def _turno_comando_minimo() -> dict[str, Any]:
    """Isola a arbitragem de modalidade; C4 testa concorrência de candidatos."""
    return {
        "modalidade": "comando",
        "modalidade_geral": "comando",
    }


def _candidato_retry_email() -> CandidatoDecisao:
    """Representa o retry correto que a R1 futura precisa materializar."""
    return CandidatoDecisao(
        tipo="repeticao",
        valor={
            "intent": "EMAIL_READ",
            "params": {},
        },
        origem="retry-tipado-ler",
        confianca=0.99,
        evidencia=("fala atual restringe repeticao a LER",),
    )


def _candidato_semantico(
    estado: dict[str, Any],
    texto: str,
) -> CandidatoDecisao | None:
    decisao = resolver_continuidade_semantica(
        texto,
        mente=estado,
        estrutura_arquivo={},
    )
    candidato = decisao.para_intencao()

    if not isinstance(candidato, dict):
        return None

    semantica = dict(candidato.get("_semantica") or {})

    return CandidatoDecisao(
        tipo="comando_contextual",
        valor=candidato,
        origem="continuidade-semantica",
        confianca=float(
            semantica.get("confianca")
            or decisao.confianca
            or 0.0
        ),
        evidencia=("continuidade semantica",),
    )


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


def test_guard_semantico_de_novo_generico_pode_repetir_iot() -> None:
    """Sem verbo restritivo, REPETIR continua podendo herdar IoT."""
    estado = _estado_email_depois_iot()

    decisao = resolver_continuidade_semantica(
        "de novo",
        mente=estado,
        estrutura_arquivo={},
    )
    candidato = decisao.para_intencao()

    assert candidato is not None
    assert candidato["intent"] == "IOT_CONTROL"
    assert candidato["params"]["acao"] == "desligar"
    assert candidato["params"]["alvo"] == "lampada_quarto"


def test_guard_arbitro_aceita_retry_de_leitura_quando_ele_e_o_unico_candidato() -> None:
    """O árbitro em si consegue materializar EMAIL_READ como repetição."""
    resultado = arbitrar_turno(
        "Leia de novo.",
        [_candidato_retry_email()],
        turno=_turno_comando_minimo(),
        retrato={},
    )

    assert resultado["decisao"] is not None
    assert resultado["decisao"]["intent"] == "EMAIL_READ"
    assert resultado["tipo"] == "repeticao"


# ---------------------------------------------------------------------------
# REDs
# ---------------------------------------------------------------------------


def test_red_continuidade_semantica_nao_pode_projetar_iot_em_leia_de_novo() -> None:
    """R1-C4/A: a rota semântica deve respeitar a restrição lexical LER."""
    estado = _estado_email_depois_iot()

    decisao = resolver_continuidade_semantica(
        "Leia de novo.",
        mente=estado,
        estrutura_arquivo={},
    )
    candidato = decisao.para_intencao()

    # A solução futura pode:
    # - ceder e não gerar candidato; ou
    # - resolver uma operação de leitura compatível.
    #
    # O que nunca pode fazer é materializar uma ação de outro domínio.
    if candidato is None:
        return

    assert str(candidato.get("intent") or "").upper() in (
        INTENTS_LEITURA_COMPATIVEIS
    )


def test_red_arbitro_nao_pode_deixar_contexto_incompativel_vencer_retry_tipado() -> None:
    """R1-C4/B: a decisão final do turno precisa continuar sendo leitura."""
    estado = _estado_email_depois_iot()

    candidatos: list[CandidatoDecisao] = [
        _candidato_retry_email(),
    ]

    semantico = _candidato_semantico(
        estado,
        "Leia de novo.",
    )
    if semantico is not None:
        candidatos.append(semantico)

    resultado = arbitrar_turno(
        "Leia de novo.",
        candidatos,
        turno=_turno_comando_minimo(),
        retrato={},
    )

    decisao = dict(resultado.get("decisao") or {})

    assert decisao
    assert str(decisao.get("intent") or "").upper() in (
        INTENTS_LEITURA_COMPATIVEIS
    )
    assert decisao["intent"] == "EMAIL_READ"
