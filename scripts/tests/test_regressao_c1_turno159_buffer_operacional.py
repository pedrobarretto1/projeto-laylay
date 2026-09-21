# -*- coding: utf-8 -*-
"""Regressão C1 — buffer operacional após no-op idempotente confirmado.

Congela a separação entre mutação, confirmação, referência e autoridade.
Caso causal: APP_OPEN + ja_aberto_focado + executou=False + confirmado=True.
"""

from __future__ import annotations

import time

from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.contexto_imediato import (
    _dominio_contrato_referencia,
    referencia_contextual_imediata,
    resolver_comando_acao_geral_contextual,
)


def _resultado(
    *,
    intent: str = "APP_OPEN",
    nome: str = "opera",
    executou: bool,
    confirmado: bool,
    status: str,
) -> dict:
    params = {"nome_app": nome} if intent == "APP_OPEN" else {"alvo": nome}
    return {
        "intent": intent,
        "alvo": nome,
        "params": params,
        "status": status,
        "executou": executou,
        "confirmado": confirmado,
        "origem": "candidate_c1_turno159",
    }


def _estado_fresco() -> dict:
    estado = estado_mental_inicial()
    estado["ts"] = time.time()
    return estado


def _registrar(
    estado: dict,
    *,
    intent: str = "APP_OPEN",
    nome: str = "opera",
    executou: bool,
    confirmado: bool,
    status: str,
) -> dict:
    novo = registrar_resultado_execucao(
        estado,
        _resultado(
            intent=intent,
            nome=nome,
            executou=executou,
            confirmado=confirmado,
            status=status,
        ),
        texto=f"acao {intent} {nome}",
    )
    novo["ts"] = time.time()
    return novo


def _estado_manual_noop_app(*, status: str = "ja_aberto_focado", confirmado=True):
    agora = time.time()
    estado = _estado_fresco()
    estado.update({
        "ts": agora,
        "ultima_acao_ts": agora,
        "ultima_acao_promovivel": False,
        "ultima_acao_intent": "APP_OPEN",
        "ultima_acao_params": {"nome_app": "opera"},
        "ultimo_app_janela": "opera",
        "ultima_acao_contrato": {
            "intent": "APP_OPEN",
            "alvo": "opera",
            "status": status,
            "dominio": "app",
            "executou": False,
            "confirmado": confirmado,
            "origem": "candidate_c1_turno159",
        },
    })
    return estado


def test_guard_c1_execucao_real_confirmada_continua_promovendo():
    estado = _registrar(
        _estado_fresco(),
        executou=True,
        confirmado=True,
        status="app_iniciado_focado",
    )
    assert estado.get("ultima_acao_promovivel") is True
    assert str(estado.get("ultimo_app_janela") or "").casefold() == "opera"


def test_guard_c1_execucao_real_status_neutro_mantem_caminho_historico_de_promocao():
    # O caminho histórico de execução observada continua válido quando o
    # status não carrega marcador explícito de falha/ausência de confirmação.
    estado = _registrar(
        _estado_fresco(),
        executou=True,
        confirmado=False,
        status="executado",
    )
    assert estado.get("ultima_acao_promovivel") is True


def test_guard_c1_status_sem_confirmacao_continua_nao_promovivel():
    # ``sem_confirmacao`` é marcador de bloqueio no contrato atual. Mesmo com
    # executou=True, esse resultado NÃO deve virar referente operacional.
    estado = _registrar(
        _estado_fresco(),
        executou=True,
        confirmado=False,
        status="executado_sem_confirmacao",
    )
    assert estado.get("ultima_acao_promovivel") is False

def test_guard_c1_noop_nao_confirmado_nao_promove():
    estado = _registrar(
        _estado_fresco(),
        executou=False,
        confirmado=False,
        status="ja_aberto_focado",
    )
    assert estado.get("ultima_acao_promovivel") is False


def test_guard_c1_noop_confirmado_status_arbitrario_nao_promove():
    estado = _registrar(
        _estado_fresco(),
        executou=False,
        confirmado=True,
        status="noop_generico_confirmado",
    )
    assert estado.get("ultima_acao_promovivel") is False


def test_guard_c1_status_de_app_em_outro_intent_nao_promove():
    estado = _registrar(
        _estado_fresco(),
        intent="IOT_CONTROL",
        nome="lampada",
        executou=False,
        confirmado=True,
        status="ja_aberto_focado",
    )
    assert estado.get("ultima_acao_promovivel") is False


def test_guard_c1_app_sem_alvo_nao_fabrica_referencia():
    estado = registrar_resultado_execucao(
        _estado_fresco(),
        {
            "intent": "APP_OPEN",
            "status": "app_iniciado_focado",
            "executou": True,
            "confirmado": True,
            "params": {},
            "origem": "candidate_c1_guard",
        },
        texto="abre",
    )
    assert not str(estado.get("ultimo_app_janela") or "").strip()


def test_guard_c1_falha_posterior_nao_apaga_ultimo_app_valido():
    estado = _registrar(
        _estado_fresco(),
        nome="opera",
        executou=True,
        confirmado=True,
        status="app_iniciado_focado",
    )
    estado = _registrar(
        estado,
        nome="calculadora",
        executou=False,
        confirmado=False,
        status="falha_app",
    )
    assert estado.get("ultima_acao_promovivel") is False
    assert str(estado.get("ultimo_app_janela") or "").casefold() == "opera"


def test_guard_c1_ttl_expirado_nao_define_dominio():
    estado = _estado_manual_noop_app()
    estado["ultima_acao_ts"] = time.time() - 999.0
    assert _dominio_contrato_referencia(estado, ttl_s=300.0) == ""


def test_guard_c1_referencia_nao_inventa_autoridade():
    referencia = {
        "tipo": "app",
        "alvo": "opera",
        "intencao": "APP_OPEN",
        "params": {"nome_app": "opera"},
    }
    assert resolver_comando_acao_geral_contextual("ela", referencia) is None
    plano = resolver_comando_acao_geral_contextual("fecha ela", referencia)
    assert isinstance(plano, dict)
    assert plano.get("intent") == "CLOSE_APP"
    assert str(dict(plano.get("params") or {}).get("nome_app") or "").casefold() == "opera"


def test_c1_buffer_promove_app_ja_aberto_focado():
    estado = _registrar(
        _estado_fresco(),
        executou=False,
        confirmado=True,
        status="ja_aberto_focado",
    )
    ok = (
        estado.get("ultima_acao_promovivel") is True
        and str(estado.get("ultimo_app_janela") or "").casefold() == "opera"
    )
    assert ok, (
        "C1_BUFFER_JA_ABERTO_FOCADO: estado confirmado e ja satisfeito "
        "de APP_OPEN deve continuar referenciavel; "
        f"promovivel={estado.get('ultima_acao_promovivel')!r} "
        f"ultimo_app={estado.get('ultimo_app_janela')!r}"
    )


def test_c1_dominio_contrato_preserva_app_noop_confirmado():
    estado = _estado_manual_noop_app()
    dominio = _dominio_contrato_referencia(estado, ttl_s=300.0)
    assert dominio == "app", (
        "C1_DOMINIO_APP_JA_ABERTO_FOCADO: contrato APP_OPEN "
        "ja_aberto_focado confirmado deve preservar dominio app; "
        f"dominio={dominio!r}"
    )


def test_c1_ponte_fecha_ela_aceita_noop_confirmado():
    estado = _estado_manual_noop_app()
    referencia = referencia_contextual_imediata(
        mente_integrada_estado=estado,
        foco_vivo={},
        texto_atual="fecha ela",
    )
    plano = resolver_comando_acao_geral_contextual("fecha ela", referencia)
    ok = bool(
        isinstance(referencia, dict)
        and referencia.get("tipo") == "app"
        and str(referencia.get("alvo") or "").casefold() == "opera"
        and isinstance(plano, dict)
        and plano.get("intent") == "CLOSE_APP"
        and str(dict(plano.get("params") or {}).get("nome_app") or "").casefold() == "opera"
    )
    assert ok, (
        "C1_PONTE_FECHA_ELA_JA_ABERTO_FOCADO: ponte deve usar o "
        "referente confirmado sem fabricar autoridade; "
        f"referencia={referencia!r} plano={plano!r}"
    )
