from __future__ import annotations

from mente_laylay.autonomia.executor_acoes_autonomas import (
    ExecutorAcoesAutonomasRuntime,
)


def _montar(
    *, resultado_iot=None, volume=35, confirmar_volume=True, mente=None,
    confirmar_midia=True, executar_intencao=None,
):
    chamadas_iot, falas, ajustes, midia = [], [], [], []
    estado_volume = {"valor": volume}

    def executar_iot(comando, texto):
        chamadas_iot.append((comando, texto))
        return dict(resultado_iot or {})

    def ajustar(nivel):
        ajustes.append(nivel)
        if confirmar_volume:
            estado_volume["valor"] = nivel
        return True

    runtime = ExecutorAcoesAutonomasRuntime(
        executar_iot=executar_iot,
        estado_mental_getter=lambda: dict(mente or {}),
        obter_volume=lambda: estado_volume["valor"],
        ajustar_volume=ajustar,
        falar=lambda *args: falas.append(args),
        executar_intencao=executar_intencao,
        controlar_midia=lambda acao: midia.append(acao) or confirmar_midia,
    )
    return runtime, {
        "iot": chamadas_iot,
        "falas": falas,
        "ajustes": ajustes,
        "volume": estado_volume,
        "midia": midia,
    }


def test_executor_iot_confirmado_cria_desfazer_e_preserva_fala() -> None:
    runtime, dados = _montar(resultado_iot={
        "ok": True,
        "confirmado": True,
        "status": "ligado",
        "estado_anterior": False,
        "plano_resposta": {
            "fala": "Acendi a lâmpada.", "emocao": "animada", "nivel": 2,
        },
    })

    resultado = runtime.executar({
        "intent": "IOT_CONTROL",
        "params": {"acao": "ligar", "alvo": "lampada_quarto"},
    })

    assert resultado["ok"] is True
    assert resultado["desfazer"] == {
        "intent": "IOT_CONTROL",
        "params": {"acao": "desligar", "alvo": "lampada_quarto"},
    }
    assert dados["falas"] == [(
        "Tomei a iniciativa com a permissão que você me deu. Acendi a lâmpada.",
        "animada",
        2,
    )]


def test_executor_brilho_guarda_parametro_anterior_por_dispositivo() -> None:
    runtime, _ = _montar(
        resultado_iot={"ok": True, "confirmado": True, "status": "brilho_ajustado"},
        mente={
            "parametros_iot_por_dispositivo": {
                "lampada_quarto": {"brilho": 42},
            },
        },
    )

    resultado = runtime.executar({
        "intent": "IOT_CONTROL",
        "params": {
            "acao": "ajustar_brilho", "alvo": "lampada_quarto", "valor": 20,
        },
    })

    assert resultado["desfazer"]["params"]["valor"] == 42


def test_executor_cor_guarda_cor_anterior_para_desfazer() -> None:
    runtime, _ = _montar(
        resultado_iot={"ok": True, "confirmado": True, "status": "cor_ajustada"},
        mente={
            "parametros_iot_por_dispositivo": {
                "lampada_quarto": {"cor": "azul", "rgb": (0, 0, 255)},
            },
        },
    )

    resultado = runtime.executar({
        "intent": "IOT_CONTROL",
        "params": {
            "acao": "ajustar_cor", "alvo": "lampada_quarto",
            "cor": "roxo", "rgb": (128, 0, 255),
        },
    })

    assert resultado["desfazer"] == {
        "intent": "IOT_CONTROL",
        "params": {
            "acao": "ajustar_cor", "alvo": "lampada_quarto",
            "cor": "azul", "rgb": (0, 0, 255),
        },
    }


def test_executor_volume_confirma_releitura_e_cria_token_reversivel() -> None:
    runtime, dados = _montar(volume=35)

    resultado = runtime.executar({
        "intent": "VOLUME", "params": {"nivel_volume": 20},
    })

    assert resultado == {
        "ok": True,
        "confirmado": True,
        "status": "volume_ajustado",
        "desfazer": {"intent": "VOLUME", "params": {"nivel_volume": 35}},
    }
    assert dados["ajustes"] == [20]
    assert "20 por cento" in dados["falas"][0][0]


def test_executor_volume_relativo_usa_nivel_atual_e_preserva_desfazer() -> None:
    runtime, dados = _montar(volume=35)

    resultado = runtime.executar({
        "intent": "VOLUME_RELATIVE", "params": {"delta": -10},
    })

    assert resultado == {
        "ok": True,
        "confirmado": True,
        "status": "volume_ajustado",
        "desfazer": {"intent": "VOLUME", "params": {"nivel_volume": 35}},
    }
    assert dados["ajustes"] == [25]


def test_executor_desligar_ventilador_guarda_ligar_como_desfazer() -> None:
    runtime, _ = _montar(resultado_iot={
        "ok": True, "confirmado": True, "status": "desligado",
        "estado_anterior": True,
    })

    resultado = runtime.executar({
        "intent": "IOT_CONTROL",
        "params": {"acao": "desligar", "alvo": "tomada_ventilador"},
    })

    assert resultado["desfazer"] == {
        "intent": "IOT_CONTROL",
        "params": {"acao": "ligar", "alvo": "tomada_ventilador"},
    }


def test_executor_midia_confirma_e_cria_controle_inverso() -> None:
    runtime, dados = _montar()

    resultado = runtime.executar({
        "intent": "MEDIA_CONTROL", "params": {"acao": "pause"},
    })

    assert resultado == {
        "ok": True,
        "confirmado": True,
        "status": "midia_pause",
        "desfazer": {"intent": "MEDIA_CONTROL", "params": {"acao": "play"}},
    }
    assert dados["midia"] == ["pause"]
    assert "pausei" in dados["falas"][0][0]


def test_executor_midia_nao_declara_sucesso_sem_confirmacao() -> None:
    runtime, dados = _montar(confirmar_midia=False)

    resultado = runtime.executar({
        "intent": "MEDIA_CONTROL", "params": {"acao": "next"},
    })

    assert resultado["ok"] is False
    assert resultado["confirmado"] is False
    assert resultado["desfazer"] == {}
    assert dados["falas"] == []


def test_executor_busca_musical_usa_executor_central_e_pode_pausar_ao_desfazer() -> None:
    chamadas = []
    runtime, _ = _montar(
        executar_intencao=lambda comando, texto: chamadas.append((comando, texto)) or True,
    )

    resultado = runtime.executar({
        "intent": "MUSIC_SEARCH", "params": {"query": "rock pesado"},
    })

    assert resultado["ok"] is True
    assert resultado["desfazer"] == {
        "intent": "MEDIA_CONTROL", "params": {"acao": "pause"},
    }
    assert chamadas == [({
        "intent": "MUSIC_SEARCH",
        "params": {"query": "rock pesado", "origem": "autonomia"},
    }, "toca rock pesado")]


def test_executor_nao_confirma_volume_quando_releitura_diverge() -> None:
    runtime, dados = _montar(volume=35, confirmar_volume=False)

    resultado = runtime.executar({
        "intent": "VOLUME", "params": {"nivel_volume": 20},
    })

    assert resultado["ok"] is False
    assert resultado["confirmado"] is False
    assert resultado["status"] == "falha_confirmacao_volume"
    assert resultado["desfazer"] == {}
    assert dados["falas"] == []


def test_executor_desfaz_iot_e_volume_com_confirmacao() -> None:
    runtime, dados = _montar(
        resultado_iot={"ok": True, "confirmado": True, "status": "desligado"},
        volume=20,
    )
    iot = runtime.desfazer({
        "intent": "IOT_CONTROL",
        "params": {"acao": "desligar", "alvo": "lampada_quarto"},
    })
    volume = runtime.desfazer({
        "intent": "VOLUME", "params": {"nivel_volume": 35},
    })

    assert iot == {"ok": True, "confirmado": True, "status": "desligado"}
    params_iot = dados["iot"][0][0]["params"]
    assert params_iot["origem"] == "autonomia"
    assert params_iot["confirmado"] is True
    assert volume == {
        "ok": True, "confirmado": True, "status": "volume_restaurado",
    }
    assert dados["ajustes"] == [35]


def test_executor_rejeita_payload_ou_volume_malformado_sem_excecao() -> None:
    runtime, _ = _montar()
    assert runtime.executar(None)["status"] == "intent_nao_elegivel"
    assert runtime.executar({"intent": "VOLUME", "params": {}})["status"] == "volume_invalido"
    assert runtime.desfazer({"intent": "VOLUME", "params": {}})["status"] == "token_invalido"
