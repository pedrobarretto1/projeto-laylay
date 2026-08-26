from __future__ import annotations

from mente_laylay.autonomia.coordenador_oportunidades import (
    CoordenadorOportunidadesRuntime,
)


def _coordenador(*, objetivos=()):
    estado = {}
    encaminhadas = []

    def encaminhar(dados):
        encaminhadas.append(dict(dados))
        return {"decisao": "sugerir", "pontuacao": dados["utilidade"]}

    runtime = CoordenadorOportunidadesRuntime(
        encaminhar=encaminhar,
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.clear() or estado.update(novo),
        contexto_getter=lambda: {"modo_jogo_ativo": True},
        objetivos_getter=lambda: list(objetivos),
        clock=lambda: 1000.0,
        log=lambda _mensagem: None,
    )
    return runtime, estado, encaminhadas


def test_baixa_confianca_nao_chega_ao_motor() -> None:
    runtime, estado, encaminhadas = _coordenador()

    resultado = runtime.registrar({
        "tipo": "observacao", "dominio": "jogo", "confianca": 0.30,
        "utilidade": 90, "item": "botas",
    })

    assert resultado["decisao"] == "ignorar_baixa_confianca"
    assert encaminhadas == []
    assert estado["contadores"]["baixa_confianca"] == 1


def test_equivalentes_com_chaves_diferentes_sao_agrupadas_sem_nova_fala() -> None:
    runtime, estado, encaminhadas = _coordenador()
    base = {
        "tipo": "contexto_janela", "dominio": "navegador",
        "acao_proposta": {"intent": "EXPLAIN_ERROR", "params": {"alvo": "chrome"}},
        "utilidade": 60, "risco": "baixo",
    }

    primeira = runtime.registrar({**base, "chave": "erro:chrome:um"})
    segunda = runtime.registrar({**base, "chave": "erro:chrome:dois"})

    assert primeira["decisao"] == "sugerir"
    assert segunda["decisao"] == "ignorar_duplicada_semantica"
    assert len(encaminhadas) == 1
    assert estado["contadores"]["duplicadas_semanticas"] == 1


def test_objetivo_ativo_aumenta_relevancia_sem_conceder_autoridade() -> None:
    runtime, estado, encaminhadas = _coordenador(objetivos=[{
        "nome": "melhorar_build_atual",
        "tags": ["jogo", "monge", "gelo"],
        "prioridade": 7,
        "expira_em": 1300.0,
    }])

    resultado = runtime.registrar({
        "tipo": "observacao", "dominio": "jogo", "item": "cajado_gelido",
        "tags": ["gelo", "monge"], "utilidade": 70, "confianca": 1.0,
    })

    assert resultado["decisao"] == "sugerir"
    assert encaminhadas[0]["utilidade"] == 79
    assert encaminhadas[0]["objetivos_ativos"] == ["melhorar_build_atual"]
    assert estado["contadores"]["alinhadas_objetivo"] == 1


def test_fonte_legada_sem_confianca_preserva_utilidade_original() -> None:
    runtime, _estado, encaminhadas = _coordenador()

    runtime.registrar({
        "chave": "ritmo:noite", "tipo": "ritmo_temporal", "dominio": "iot",
        "utilidade": 62, "risco": "baixo",
        "acao_proposta": {"intent": "TIME_LIGHT_ON"},
    })

    assert encaminhadas[0]["utilidade"] == 62
    assert encaminhadas[0]["confianca"] == 1.0


def test_objetivo_temporario_expira_e_estado_e_sanitizado() -> None:
    runtime, estado, _encaminhadas = _coordenador()

    assert runtime.definir_objetivo(
        "Melhorar build de gelo", tags=["Monge", "Gelo"], validade_s=120,
    ) is True

    objetivo = estado["objetivos"][0]
    assert objetivo["nome"] == "melhorar_build_de_gelo"
    assert set(objetivo["tags"]) >= {"monge", "gelo"}
    assert objetivo["expira_em"] == 1120.0


def test_aprendizado_so_ajusta_depois_de_tres_amostras_coerentes() -> None:
    relogio = [1000.0]
    estado = {}
    encaminhadas = []
    runtime = CoordenadorOportunidadesRuntime(
        encaminhar=lambda dados: encaminhadas.append(dict(dados)) or {"decisao": "sugerir"},
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.clear() or estado.update(novo),
        contexto_getter=lambda: {"modo_jogo_ativo": True},
        clock=lambda: relogio[0],
        log=lambda _mensagem: None,
    )

    for indice in range(3):
        relogio[0] += 301.0
        runtime.registrar({
            "chave": f"item:{indice}", "tipo": "observacao", "dominio": "jogo",
            "item": "botas", "utilidade": 70, "confianca": 1.0,
        })
        perfil = runtime.registrar_feedback("jogo", False, resultado="recusa")
        if indice < 2:
            assert perfil["ajuste_utilidade"] == 0

    assert perfil["amostras"] == 3
    assert perfil["ajuste_utilidade"] == -8
    assert perfil["status"] == "preferencia_emergente"

    relogio[0] += 301.0
    runtime.registrar({
        "chave": "item:seguinte", "tipo": "observacao", "dominio": "jogo",
        "item": "luvas", "utilidade": 70, "confianca": 1.0,
    })
    assert encaminhadas[-1]["utilidade"] == 62
    assert encaminhadas[-1]["ajuste_aprendido"] == -8


def test_feedback_duplicado_na_mesma_sugestao_conta_uma_vez() -> None:
    runtime, estado, _encaminhadas = _coordenador()
    runtime.registrar({
        "tipo": "observacao", "dominio": "jogo", "item": "anel",
        "utilidade": 70, "confianca": 1.0,
    })

    primeiro = runtime.registrar_feedback("jogo", True, resultado="aceita")
    repetido = runtime.registrar_feedback("jogo", True, resultado="aceita")

    assert primeiro["amostras"] == 1
    assert repetido == {}
    assert estado["contadores"]["feedbacks"] == 1


def test_sinais_conflitantes_nao_viram_preferencia() -> None:
    registro = {}
    for resultado in ("aceita", "aceita", "recusa"):
        campo = {"aceita": "aceitas", "recusa": "recusadas"}[resultado]
        registro[campo] = int(registro.get(campo) or 0) + 1
    calculado = CoordenadorOportunidadesRuntime._recalcular_aprendizado(registro)

    assert calculado["amostras"] == 3
    assert calculado["status"] == "sinais_conflitantes"
    assert calculado["ajuste_utilidade"] == 0


def test_silencio_e_correcao_sao_sinais_distintos() -> None:
    silencio = CoordenadorOportunidadesRuntime._recalcular_aprendizado({"silencios": 3})
    correcao = CoordenadorOportunidadesRuntime._recalcular_aprendizado({"correcoes": 3})

    assert silencio["ajuste_utilidade"] == -3
    assert correcao["ajuste_utilidade"] == -10
