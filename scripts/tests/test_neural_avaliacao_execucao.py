from mente_laylay.neural.avaliacao import avaliar_previsoes


def _item(*, is_command: bool, negated: bool) -> dict:
    return {
        "intent": "VOLUME" if is_command else "NONE",
        "is_command": is_command,
        "negated": negated,
        "action": "down" if is_command else "none",
    }


def test_comando_negado_pode_divergir_no_head_sem_ser_executavel():
    esperado = [_item(is_command=False, negated=False)]
    previsto = [{
        "intent": "VOLUME",
        "is_command": True,
        "negated": True,
        "params": {"acao": "down"},
        "ood": False,
    }]

    metricas = avaliar_previsoes(esperado, previsto)

    assert metricas["false_command_count"] == 1
    assert metricas["false_executable_command_count"] == 0
    assert metricas["predicted_executable_command_count"] == 0


def test_negacao_perdida_cria_falso_comando_executavel():
    esperado = [_item(is_command=True, negated=True)]
    previsto = [{
        "intent": "VOLUME",
        "is_command": True,
        "negated": False,
        "params": {"acao": "down"},
        "ood": False,
    }]

    metricas = avaliar_previsoes(esperado, previsto)

    assert metricas["false_command_count"] == 0
    assert metricas["false_executable_command_count"] == 1
    assert metricas["false_executable_command_rate"] == 1.0


def test_ood_calibrado_bloqueia_execucao_na_metrica():
    esperado = [_item(is_command=False, negated=False)]
    previsto = [{
        "intent": "VOLUME",
        "is_command": True,
        "negated": False,
        "params": {"acao": "down"},
        "ood": True,
        "ood_calibrated": True,
    }]

    metricas = avaliar_previsoes(esperado, previsto)

    assert metricas["false_command_count"] == 1
    assert metricas["false_executable_command_count"] == 0
    assert metricas["predicted_executable_command_count"] == 0


def test_comando_executavel_correto_preserva_precision_e_recall():
    esperado = [_item(is_command=True, negated=False)]
    previsto = [{
        "intent": "VOLUME",
        "is_command": True,
        "negated": False,
        "params": {"acao": "down"},
        "ood": False,
    }]

    metricas = avaliar_previsoes(esperado, previsto)

    assert metricas["executable_command_precision"] == 1.0
    assert metricas["executable_command_recall"] == 1.0
    assert metricas["false_executable_command_count"] == 0
    assert metricas["missed_executable_command_count"] == 0
