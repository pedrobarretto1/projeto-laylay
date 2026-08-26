# -*- coding: utf-8 -*-
"""Regressão C1-B — `maximiza` elíptico com alvo contextual tipado.

Congela a separação entre autoridade da ação e resolução do alvo.
A fala atual autoriza maximização; contexto só pode fornecer app válido.
"""

from __future__ import annotations

import re

from mente_laylay.autonomia.roteador_deterministico import detectar_janela_contextual
from mente_laylay.cognicao.arbitro_turno import CandidatoDecisao, arbitrar_turno
from mente_laylay.cognicao.modalidade_turno import (
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
)
from mente_laylay.memoria_mental.compatibilidade_contexto import (
    texto_depende_de_contexto as texto_depende_de_contexto_runtime,
)


def _params(**kwargs):
    return kwargs


def _estado_app(nome: str = "opera") -> dict:
    return {
        "ultimo_app_janela": nome,
        "ultima_acao_intent": "APP_OPEN",
        "ultima_acao_params": {"nome_app": nome},
    }


def _estado_sem_app() -> dict:
    return {
        "ultima_acao_intent": "OPEN_URL",
        "ultima_acao_params": {"alvo": "wikipedia"},
    }


def _normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", str(texto or "").casefold()).strip(" .,!?:;")


def _depende_contexto(texto: str) -> bool:
    return bool(
        texto_depende_de_contexto_runtime(
            texto,
            _normalizar,
        )
    )


def _detectar(texto: str, estado: dict | None):
    return detectar_janela_contextual(
        _normalizar(texto),
        params_cb=_params,
        estado_mental=dict(estado or {}),
        texto_depende_de_contexto=_depende_contexto,
    )


def test_guard_c1b_maximiza_puro_ja_e_acao_explicita_contextual_com_alvo_pendente():
    turno = classificar_modalidade_turno("maximiza")
    assert turno.get("acao_explicita") is True, turno
    assert turno.get("depende_contexto") is True, turno
    assert turno.get("requer_esclarecimento") is True, turno


def test_guard_c1b_callback_runtime_nao_promove_maximiza_a_referencia_linguistica():
    assert _depende_contexto("maximiza") is False
    assert _depende_contexto("maximiza ele") is True


def test_guard_c1b_detector_ja_materializa_maximize_window_com_app_vivo():
    candidato = _detectar("maximiza", _estado_app("opera"))
    assert isinstance(candidato, dict), candidato
    assert candidato.get("intent") == "MAXIMIZE_WINDOW", candidato
    assert str(dict(candidato.get("params") or {}).get("nome_app") or "").casefold() == "opera"


def test_guard_c1b_sem_app_vivo_nao_fabrica_alvo():
    assert _detectar("maximiza", {}) is None
    assert _detectar("maximiza", _estado_sem_app()) is None


def test_guard_c1b_referencia_sem_verbo_nao_fabrica_maximizacao():
    assert _detectar("ele", _estado_app("opera")) is None
    assert _detectar("ela", _estado_app("opera")) is None


def test_guard_c1b_formas_explicitas_existentes_continuam_autorizadas():
    for texto in (
        "Maximiza a Calculadora.",
        "Maximiza ele.",
    ):
        turno = classificar_modalidade_turno(texto)
        assert turno.get("autoriza_execucao") is True, (texto, turno)
        assert bloqueia_execucao_operacional_prioritaria(
            texto,
            classificacao=turno,
        ) is False, (texto, turno)


def test_guard_c1b_negacao_hipotese_pergunta_e_metalinguagem_continuam_bloqueadas():
    casos = (
        "Não maximiza.",
        "Talvez maximize.",
        "Como eu maximizaria?",
        "Você consegue maximizar?",
        "Maximizar uma janela muda a resolução?",
        "Estou apenas escrevendo: maximiza.",
    )
    for texto in casos:
        turno = classificar_modalidade_turno(texto)
        assert turno.get("autoriza_execucao") is False, (texto, turno)
        assert bloqueia_execucao_operacional_prioritaria(
            texto,
            classificacao=turno,
        ) is True, (texto, turno)


def test_guard_c1b_nao_globaliza_outros_verbos_sem_alvo():
    for texto in ("abre", "fecha", "apaga", "remove"):
        turno = classificar_modalidade_turno(texto)
        assert turno.get("autoriza_execucao") is False, (texto, turno)


def test_guard_c1b_arbitro_nao_aceita_referencia_de_dominio_errado():
    texto = "Maximiza ele."
    turno = classificar_modalidade_turno(texto)
    candidato = {
        "intent": "MAXIMIZE_WINDOW",
        "params": {"nome_app": "opera"},
    }
    resultado = arbitrar_turno(
        texto,
        [
            CandidatoDecisao(
                tipo="comando_contextual",
                valor=candidato,
                origem="guard_c1b_dominio",
                confianca=0.99,
            )
        ],
        turno=turno,
        retrato={
            "referencia_tipo": "site",
            "referencia_resolvida": {
                "tipo": "site",
                "alvo": "wikipedia",
            },
        },
    )
    assert resultado.get("decisao") is None, resultado
    assert resultado.get("rejeitados"), resultado


def test_c1b_maximiza_puro_autoriza_acao_mas_mantem_alvo_pendente():
    turno = classificar_modalidade_turno("maximiza")
    ok = bool(
        turno.get("acao_explicita") is True
        and turno.get("autoriza_execucao") is True
        and turno.get("depende_contexto") is True
        and turno.get("requer_esclarecimento") is True
    )
    assert ok, (
        "C1B_AUTORIDADE_MAXIMIZA_PURO: `maximiza` expressa a ação "
        "mutante de forma explícita; a ausência de alvo deve continuar "
        "registrada, mas não pode apagar a autoridade da própria ação. "
        f"turno={turno!r}"
    )


def test_c1b_barreira_libera_acao_explicitamente_autorizada():
    turno = classificar_modalidade_turno("maximiza")
    bloqueia = bloqueia_execucao_operacional_prioritaria(
        "maximiza",
        classificacao=turno,
    )
    assert bloqueia is False, (
        "C1B_BARREIRA_MAXIMIZA_PURO: a barreira deve respeitar a "
        "autoridade congelada da ação `maximiza`; alvo continua sendo "
        "responsabilidade da resolução tipada. "
        f"turno={turno!r} bloqueia={bloqueia!r}"
    )


def test_c1b_arbitro_aceita_maximizacao_com_referencia_app_tipificada():
    texto = "maximiza"
    turno = classificar_modalidade_turno(texto)
    candidato = _detectar(texto, _estado_app("opera"))
    assert isinstance(candidato, dict), candidato
    assert candidato.get("intent") == "MAXIMIZE_WINDOW", candidato

    resultado = arbitrar_turno(
        texto,
        [
            CandidatoDecisao(
                tipo="comando_contextual",
                valor=candidato,
                origem="red_c1b_detector_janela",
                confianca=0.99,
            )
        ],
        turno=turno,
        retrato={
            "referencia_tipo": "app",
            "referencia_resolvida": {
                "tipo": "app",
                "alvo": "opera",
                "intencao": "APP_OPEN",
                "params": {"nome_app": "opera"},
            },
        },
    )
    decisao = resultado.get("decisao")
    ok = bool(
        isinstance(decisao, dict)
        and decisao.get("intent") == "MAXIMIZE_WINDOW"
        and str(dict(decisao.get("params") or {}).get("nome_app") or "").casefold() == "opera"
    )
    assert ok, (
        "C1B_ARBITRO_MAXIMIZA_APP: o detector já resolveu o alvo app "
        "tipado, mas o árbitro ainda rejeita porque a autoridade congelada "
        "de `maximiza` está False no baseline. "
        f"turno={turno!r} candidato={candidato!r} resultado={resultado!r}"
    )


def test_candidate_c1b_maximiza_autorizado_sem_referencia_nao_fabrica_decisao():
    texto = "maximiza"
    turno = classificar_modalidade_turno(texto)
    assert turno.get("autoriza_execucao") is True
    candidato = _detectar(texto, {})
    assert candidato is None

    resultado = arbitrar_turno(
        texto,
        [],
        turno=turno,
        retrato={
            "referencia_tipo": "",
            "referencia_resolvida": {},
        },
    )
    assert resultado.get("decisao") is None
