from __future__ import annotations

import json

from mente_laylay.neural.auditoria_shadow import auditar_evidencias_shadow


def _gravar_jsonl(caminho, registros) -> None:
    caminho.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in registros),
        encoding="utf-8",
    )


def _contem_chave_texto(valor) -> bool:
    if isinstance(valor, dict):
        return any(
            chave in {"text", "texto", "texto_correcao"}
            or _contem_chave_texto(item)
            for chave, item in valor.items()
        )
    if isinstance(valor, list):
        return any(_contem_chave_texto(item) for item in valor)
    return False


def test_auditoria_separa_modelo_antigo_receipt_e_correcao_forte(tmp_path) -> None:
    _gravar_jsonl(
        tmp_path / "shadow_eventos.jsonl",
        [
            {
                "id": "lexical",
                "ts": 10.0,
                "tipo": "comparacao_turno",
                "modelo": "tfidf-v0.4",
                "texto": "fecha aquilo",
                "neural": {"latency_ms": 2.0},
                "apto_treino": False,
            },
            {
                "id": "semantic",
                "ts": 20.0,
                "tipo": "comparacao_turno",
                "modelo": "minilm-shadow-v1-3106",
                "texto": "abaixa só um pouco",
                "neural": {"latency_ms": 12.5},
                "apto_treino": False,
            },
        ],
    )
    _gravar_jsonl(
        tmp_path / "experiencias.jsonl",
        [
            {
                "id": "receipt",
                "tipo": "resultado_comando",
                "text": "abaixa o som",
                "evidencia": "EXPECTED_RECEIPT_VERIFIED",
                "executou": True,
                "confirmado": True,
                "apto_treino": False,
                "label_confidence": 0.45,
            },
            {
                "id": "correcao-fraca",
                "tipo": "correcao_interpretacao",
                "text": "fecha o chrome",
                "texto_correcao": "eu quis dizer fechar o aplicativo",
                "intent_correta": "CLOSE_APP",
                "params_corretos": {"acao": "close"},
                "evidencia": "EXPLICIT_CORRECTION",
                "apto_treino": False,
                "label_confidence": 0.8,
            },
            {
                "id": "correcao-forte",
                "tipo": "correcao_interpretacao",
                "text": "encerra o navegador",
                "texto_correcao": "isso, feche o aplicativo",
                "intent_correta": "CLOSE_APP",
                "params_corretos": {"acao": "close"},
                "evidencia": "EXPLICIT_CORRECTION",
                "apto_treino": True,
                "label_confidence": 1.0,
            },
        ],
    )

    relatorio = auditar_evidencias_shadow(
        tmp_path,
        modelo_esperado="minilm-shadow-v1-3106",
        intents_permitidas={"CLOSE_APP", "VOLUME"},
        dominio_por_intent={"CLOSE_APP": "app", "VOLUME": "audio"},
    )

    assert relatorio["shadow"]["eventos_total"] == 2
    assert relatorio["shadow"]["eventos_modelo_esperado"] == 1
    assert relatorio["shadow"]["modelo_esperado_observado"] is True
    assert relatorio["experiencias"]["receipts_confirmados_revisaveis"] == 1
    assert relatorio["experiencias"]["correcoes_explicitamente_confirmadas"] == 1
    assert relatorio["experiencias"]["exemplos_aptos_total"] == 1
    assert relatorio["experiencias"]["ids_aptos_para_revisao"] == ["correcao-forte"]
    assert relatorio["experiencias"]["ids_pendentes_revisao"] == ["correcao-forte"]
    assert relatorio["experiencias"]["exemplos_aprovados_treino"] == 0
    assert relatorio["status"] == "correcoes_disponiveis_para_revisao"
    assert relatorio["contrato"]["incorporacao_automatica_no_dev"] is False
    assert relatorio["contrato"]["incorporacao_automatica_no_treino"] is False
    assert relatorio["contrato"]["receipt_isolado_vira_label"] is False
    assert relatorio["contrato"]["divergencia_shadow_vira_label"] is False
    assert not _contem_chave_texto(relatorio)


def test_auditoria_sem_evento_esperado_nao_confunde_log_antigo_com_coleta_real(
    tmp_path,
) -> None:
    _gravar_jsonl(
        tmp_path / "shadow_eventos.jsonl",
        [
            {
                "id": "antigo",
                "tipo": "comparacao_turno",
                "modelo": "tfidf-v0.4",
                "neural": {"latency_ms": 1.0},
            }
        ],
    )
    (tmp_path / "experiencias.jsonl").write_text("{linha quebrada\n", encoding="utf-8")

    relatorio = auditar_evidencias_shadow(
        tmp_path,
        modelo_esperado="minilm-shadow-v1-3106",
        intents_permitidas={"CLOSE_APP"},
    )

    assert relatorio["shadow"]["modelo_esperado_observado"] is False
    assert relatorio["experiencias"]["linhas_invalidas"] == 1
    assert relatorio["experiencias"]["exemplos_aptos_total"] == 0
    assert relatorio["status"] == "aguardando_sessao_modelo_esperado"


def test_auditoria_rejeita_correcao_com_confianca_corrompida_sem_interromper(
    tmp_path,
) -> None:
    _gravar_jsonl(
        tmp_path / "shadow_eventos.jsonl",
        [{"tipo": "comparacao_turno", "modelo": "minilm-shadow-v1-3106"}],
    )
    _gravar_jsonl(
        tmp_path / "experiencias.jsonl",
        [
            {
                "id": "corrompida",
                "tipo": "correcao_interpretacao",
                "text": "fecha o navegador",
                "intent_correta": "CLOSE_APP",
                "params_corretos": {"acao": "close"},
                "evidencia": "EXPLICIT_CORRECTION",
                "apto_treino": True,
                "label_confidence": "sem-numero",
            }
        ],
    )

    relatorio = auditar_evidencias_shadow(
        tmp_path,
        modelo_esperado="minilm-shadow-v1-3106",
        intents_permitidas={"CLOSE_APP"},
    )

    assert relatorio["experiencias"]["correcoes_aptas_invalidas"] == 1
    assert relatorio["experiencias"]["exemplos_aptos_total"] == 0
    assert relatorio["status"] == "sem_correcoes_explicitamente_confirmadas"


def test_auditoria_nao_consome_catalogo_iteravel_entre_correcoes(tmp_path) -> None:
    _gravar_jsonl(
        tmp_path / "shadow_eventos.jsonl",
        [{"tipo": "comparacao_turno", "modelo": "minilm-shadow-v1-3106"}],
    )
    _gravar_jsonl(
        tmp_path / "experiencias.jsonl",
        [
            {
                "id": identificador,
                "tipo": "correcao_interpretacao",
                "text": texto,
                "intent_correta": intent,
                "params_corretos": {"acao": acao},
                "evidencia": "EXPLICIT_CORRECTION",
                "apto_treino": True,
                "label_confidence": 1.0,
            }
            for identificador, texto, intent, acao in (
                ("uma", "fecha o navegador", "CLOSE_APP", "close"),
                ("duas", "abaixa o som", "VOLUME", "down"),
            )
        ],
    )

    relatorio = auditar_evidencias_shadow(
        tmp_path,
        modelo_esperado="minilm-shadow-v1-3106",
        intents_permitidas=(item for item in ("CLOSE_APP", "VOLUME")),
    )

    assert relatorio["experiencias"]["exemplos_aptos_total"] == 2
    assert relatorio["experiencias"]["ids_aptos_para_revisao"] == ["uma", "duas"]


def test_auditoria_separa_fora_catalogo_e_acao_canonica_ausente(tmp_path) -> None:
    _gravar_jsonl(
        tmp_path / "shadow_eventos.jsonl",
        [
            {
                "tipo": "comparacao_receipt",
                "modelo": "minilm-shadow-v1-3106",
                "neural": {"intent": "LIST_TABS", "acao": "list"},
                "canonico": {
                    "intent": "EMAIL_READ", "acao": "",
                    "executou": True, "confirmado": True,
                },
                "comparacao": {"receipt_confirmado": True},
            },
            {
                "tipo": "comparacao_receipt",
                "modelo": "minilm-shadow-v1-3106",
                "neural": {"intent": "CLOSE_APP", "acao": "close"},
                "canonico": {
                    "intent": "CLOSE_APP", "acao": "",
                    "executou": True, "confirmado": True,
                },
                "comparacao": {"receipt_confirmado": True},
            },
            {
                "tipo": "comparacao_receipt",
                "modelo": "minilm-shadow-v1-3106",
                "neural": {"intent": "VOLUME", "acao": "down"},
                "canonico": {
                    "intent": "VOLUME", "acao": "down",
                    "executou": True, "confirmado": True,
                },
                "comparacao": {"receipt_confirmado": True},
            },
        ],
    )
    (tmp_path / "experiencias.jsonl").write_text("", encoding="utf-8")

    relatorio = auditar_evidencias_shadow(
        tmp_path,
        modelo_esperado="minilm-shadow-v1-3106",
        intents_permitidas={"CLOSE_APP", "LIST_TABS", "VOLUME"},
        intents_modelo={"CLOSE_APP", "LIST_TABS", "VOLUME"},
    )

    metricas = relatorio["shadow"]["metricas_modelo_esperado"]
    assert metricas["receipts_confirmados"] == 3
    assert metricas["intents_fora_catalogo"] == 1
    assert metricas["intents_comparaveis"] == 2
    assert metricas["concordancias_intent"] == 2
    assert metricas["acoes_canonicas_ausentes"] == 1
    assert metricas["acoes_comparaveis"] == 1
    assert metricas["concordancias_acao"] == 1
    assert metricas["taxa_concordancia_intent"] == 1.0
    assert metricas["taxa_concordancia_acao"] == 1.0
    assert not _contem_chave_texto(relatorio)


def test_auditoria_separa_correcoes_aprovadas_rejeitadas_e_pendentes(
    tmp_path,
) -> None:
    _gravar_jsonl(
        tmp_path / "shadow_eventos.jsonl",
        [{"tipo": "comparacao_turno", "modelo": "modelo-v26"}],
    )
    _gravar_jsonl(
        tmp_path / "experiencias.jsonl",
        [
            {
                "id": identificador,
                "tipo": "correcao_interpretacao",
                "text": texto,
                "intent_correta": "VOLUME",
                "params_corretos": {"acao": "down"},
                "evidencia": "EXPLICIT_CORRECTION",
                "apto_treino": True,
                "label_confidence": 1.0,
            }
            for identificador, texto in (
                ("aprovada", "abaixa um pouco o som"),
                ("rejeitada", "reduz o volume agora"),
                ("pendente", "deixa o audio mais baixo"),
            )
        ],
    )
    _gravar_jsonl(
        tmp_path / "revisoes_correcoes.jsonl",
        [
            {"correcao_id": "aprovada", "decisao": "aprovada"},
            {"correcao_id": "rejeitada", "decisao": "rejeitada"},
        ],
    )

    relatorio = auditar_evidencias_shadow(
        tmp_path,
        modelo_esperado="modelo-v26",
        intents_permitidas={"VOLUME"},
    )

    experiencias = relatorio["experiencias"]
    assert experiencias["ids_aprovados_treino"] == ["aprovada"]
    assert experiencias["ids_rejeitados"] == ["rejeitada"]
    assert experiencias["ids_pendentes_revisao"] == ["pendente"]
    assert experiencias["exemplos_aprovados_treino"] == 1
    assert relatorio["status"] == "correcoes_disponiveis_para_revisao"


def test_auditoria_nao_anuncia_revisao_quando_todas_foram_rejeitadas(
    tmp_path,
) -> None:
    _gravar_jsonl(
        tmp_path / "shadow_eventos.jsonl",
        [{"tipo": "comparacao_turno", "modelo": "modelo-v26"}],
    )
    _gravar_jsonl(
        tmp_path / "experiencias.jsonl",
        [{
            "id": "incorreta",
            "tipo": "correcao_interpretacao",
            "text": "abaixa um pouco o som",
            "intent_correta": "VOLUME",
            "params_corretos": {"acao": "down"},
            "evidencia": "EXPLICIT_CORRECTION",
            "apto_treino": True,
            "label_confidence": 1.0,
        }],
    )
    _gravar_jsonl(
        tmp_path / "revisoes_correcoes.jsonl",
        [{"correcao_id": "incorreta", "decisao": "rejeitada"}],
    )

    relatorio = auditar_evidencias_shadow(
        tmp_path,
        modelo_esperado="modelo-v26",
        intents_permitidas={"VOLUME"},
    )

    assert relatorio["experiencias"]["ids_aptos_para_revisao"] == []
    assert relatorio["status"] == "sem_correcoes_pendentes_revisao"


def test_auditoria_mede_segmentos_e_nao_compara_receipt_multiacao_sem_vinculo(
    tmp_path,
) -> None:
    _gravar_jsonl(
        tmp_path / "shadow_eventos.jsonl",
        [
            {
                "tipo": "comparacao_turno",
                "modelo": "modelo-v27",
                "neural": {"latency_ms": 18.0},
                "comparacao": {
                    "segmentos_total": 2,
                    "segmentos_comparaveis": 2,
                    "concordancias_comando_segmento": 1,
                    "divergencias_comando_segmento": 1,
                    "falsos_comandos_neurais_segmento": 0,
                    "comandos_perdidos_neurais_segmento": 1,
                },
            },
            {
                "tipo": "comparacao_receipt",
                "modelo": "modelo-v27",
                "neural": {
                    "intent": "APP_OPEN",
                    "acao": "open",
                    "multi_segmento": True,
                    "receipt_comparavel": False,
                },
                "canonico": {
                    "intent": "VOLUME",
                    "acao": "down",
                    "executou": True,
                    "confirmado": True,
                },
                "comparacao": {
                    "receipt_confirmado": True,
                    "intent_comparavel": False,
                    "divergiu_receipt": False,
                },
            },
        ],
    )
    (tmp_path / "experiencias.jsonl").write_text("", encoding="utf-8")

    relatorio = auditar_evidencias_shadow(
        tmp_path,
        modelo_esperado="modelo-v27",
        intents_permitidas={"APP_OPEN", "VOLUME"},
    )

    metricas = relatorio["shadow"]["metricas_modelo_esperado"]
    assert metricas["turnos_segmentados"] == 1
    assert metricas["segmentos_comparaveis"] == 2
    assert metricas["concordancias_comando_segmento"] == 1
    assert metricas["divergencias_comando_segmento"] == 1
    assert metricas["comandos_perdidos_neurais_segmento"] == 1
    assert metricas["receipts_confirmados"] == 1
    assert metricas["receipts_nao_correlacionados"] == 1
    assert metricas["intents_comparaveis"] == 0
