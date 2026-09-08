"""Calibração seletiva de OOD sem transformar o conjunto em treino."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import GroupKFold


PARTICOES_OOD = frozenset({"training", "calibration", "evaluation"})


def carregar_dataset_ood(caminho: str | Path) -> list[dict[str, Any]]:
    """Carrega comandos fora do catálogo sob um schema isolado e fail-closed."""
    itens: list[dict[str, Any]] = []
    for numero, linha in enumerate(
        Path(caminho).read_text(encoding="utf-8").splitlines(),
        1,
    ):
        if not linha.strip():
            continue
        try:
            bruto = json.loads(linha)
        except (TypeError, ValueError, json.JSONDecodeError) as erro:
            raise ValueError(f"OOD inválido na linha {numero}: JSON inválido") from erro
        if not isinstance(bruto, Mapping):
            raise ValueError(f"OOD inválido na linha {numero}: esperado objeto")
        texto = " ".join(str(bruto.get("text") or "").strip().split())
        familia = str(bruto.get("family") or "").strip().casefold()
        dominio = str(bruto.get("domain") or "").strip().casefold()
        particao = str(bruto.get("partition") or "").strip().casefold()
        if not texto or not familia or not dominio:
            raise ValueError(
                f"OOD inválido na linha {numero}: text, family e domain são obrigatórios"
            )
        if bruto.get("expected_ood") is not True:
            raise ValueError(
                f"OOD inválido na linha {numero}: expected_ood precisa ser true"
            )
        if particao not in PARTICOES_OOD:
            raise ValueError(
                f"OOD inválido na linha {numero}: partition desconhecida"
            )
        itens.append(
            {
                "text": texto,
                "family": familia,
                "domain": dominio,
                "partition": particao,
                "expected_ood": True,
                "source": "OOD_CURATED",
            }
        )
    if not itens:
        raise ValueError("dataset OOD vazio")
    textos = [item["text"].casefold() for item in itens]
    if len(textos) != len(set(textos)):
        raise ValueError("dataset OOD contém textos duplicados")
    return itens


def _acao(previsao: Mapping[str, Any]) -> str:
    params = previsao.get("params")
    if not isinstance(params, Mapping):
        return "none"
    return str(params.get("acao") or "none").strip().casefold()


def _confianca_intent(previsao: Mapping[str, Any]) -> float:
    confiancas = previsao.get("confidence")
    if not isinstance(confiancas, Mapping):
        return 0.0
    try:
        return max(0.0, min(1.0, float(confiancas.get("intent") or 0.0)))
    except (TypeError, ValueError):
        return 0.0


def _candidato_operacional(previsao: Mapping[str, Any], limiar: float) -> bool:
    return bool(
        previsao.get("is_command")
        and not previsao.get("negated")
        and str(previsao.get("intent") or "").strip().upper() not in {"", "NONE"}
        and _confianca_intent(previsao) >= limiar
    )


def _medir(
    exemplos_id: list[dict[str, Any]],
    previsoes_id: list[dict[str, Any]],
    previsoes_ood: list[dict[str, Any]],
    limiar: float,
) -> dict[str, Any]:
    total_id = sum(
        bool(item.get("is_command")) and not bool(item.get("negated"))
        for item in exemplos_id
    )
    corretos_id = 0
    for esperado, previsto in zip(exemplos_id, previsoes_id, strict=True):
        if not (bool(esperado.get("is_command")) and not esperado.get("negated")):
            continue
        if not _candidato_operacional(previsto, limiar):
            continue
        if (
            str(previsto.get("intent") or "").strip().upper()
            == str(esperado.get("intent") or "").strip().upper()
            and _acao(previsto)
            == str(esperado.get("action") or "none").strip().casefold()
        ):
            corretos_id += 1
    aceitos_ood = sum(
        _candidato_operacional(previsao, limiar) for previsao in previsoes_ood
    )
    return {
        "limiar": round(float(limiar), 8),
        "id_total_comandos_afirmativos": total_id,
        "id_corretos_aceitos": corretos_id,
        "id_recall_operacional": (
            float(corretos_id) / total_id if total_id else 0.0
        ),
        "ood_total": len(previsoes_ood),
        "ood_aceitos": aceitos_ood,
        "ood_false_accept_rate": (
            float(aceitos_ood) / len(previsoes_ood) if previsoes_ood else 0.0
        ),
    }


def calibrar_limiar_ood(
    exemplos_id: Iterable[Mapping[str, Any]],
    previsoes_id: Iterable[Mapping[str, Any]],
    previsoes_ood_calibracao: Iterable[Mapping[str, Any]],
    previsoes_ood_avaliacao: Iterable[Mapping[str, Any]],
    *,
    alvo_falso_aceite_ood: float = 0.01,
    recall_id_minimo: float = 0.85,
) -> dict[str, Any]:
    """Escolhe limiar na calibração e só aprova se o holdout OOD confirmar."""
    esperados = [dict(item) for item in exemplos_id]
    previstos_id = [dict(item) for item in previsoes_id]
    ood_calibracao = [dict(item) for item in previsoes_ood_calibracao]
    ood_avaliacao = [dict(item) for item in previsoes_ood_avaliacao]
    if len(esperados) != len(previstos_id):
        raise ValueError("exemplos e previsões ID precisam ter o mesmo tamanho")
    if not esperados or not ood_calibracao or not ood_avaliacao:
        raise ValueError("calibração OOD exige ID, calibração e avaliação")
    alvo = float(alvo_falso_aceite_ood)
    recall_minimo = float(recall_id_minimo)
    if not 0.0 <= alvo <= 1.0 or not 0.0 <= recall_minimo <= 1.0:
        raise ValueError("metas de calibração precisam estar em [0, 1]")

    confiancas = {
        _confianca_intent(item)
        for item in [*previstos_id, *ood_calibracao]
    }
    candidatos = sorted({0.0, 1.0, *confiancas})
    medidas = [
        _medir(esperados, previstos_id, ood_calibracao, limiar)
        for limiar in candidatos
    ]
    elegiveis = [
        item
        for item in medidas
        if item["ood_false_accept_rate"] <= alvo
        and item["id_recall_operacional"] >= recall_minimo
    ]
    sob_alvo_ood = [
        item for item in medidas if item["ood_false_accept_rate"] <= alvo
    ]
    sob_recall_id = [
        item for item in medidas if item["id_recall_operacional"] >= recall_minimo
    ]
    melhor_sob_alvo_ood = sorted(
        sob_alvo_ood,
        key=lambda item: (
            -float(item["id_recall_operacional"]),
            float(item["limiar"]),
        ),
    )[0] if sob_alvo_ood else {}
    melhor_sob_recall_id = sorted(
        sob_recall_id,
        key=lambda item: (
            float(item["ood_false_accept_rate"]),
            -float(item["id_recall_operacional"]),
            float(item["limiar"]),
        ),
    )[0] if sob_recall_id else {}
    escolhido = (
        sorted(
            elegiveis,
            key=lambda item: (
                -float(item["id_recall_operacional"]),
                float(item["limiar"]),
            ),
        )[0]
        if elegiveis
        else melhor_sob_alvo_ood
        or melhor_sob_recall_id
        or medidas[0]
    )
    avaliacao = _medir(
        esperados,
        previstos_id,
        ood_avaliacao,
        float(escolhido["limiar"]),
    )
    aprovado = bool(
        elegiveis
        and avaliacao["ood_false_accept_rate"] <= alvo
        and escolhido["id_recall_operacional"] >= recall_minimo
    )
    avaliacao_no_limiar_recall = (
        _medir(
            esperados,
            previstos_id,
            ood_avaliacao,
            float(melhor_sob_recall_id["limiar"]),
        )
        if melhor_sob_recall_id
        else {}
    )
    motivo = (
        "aprovado"
        if aprovado
        else "holdout_ood_reprovou"
        if elegiveis
        else "limiar_unico_nao_separa_id_de_ood"
    )
    return {
        "aprovado": aprovado,
        "motivo": motivo,
        "limiar_recomendado": (
            float(escolhido["limiar"]) if aprovado else None
        ),
        "alvos": {
            "ood_false_accept_rate_maximo": alvo,
            "id_recall_operacional_minimo": recall_minimo,
        },
        "calibracao": escolhido,
        "avaliacao_holdout": avaliacao,
        "melhor_sob_alvo_ood_calibracao": melhor_sob_alvo_ood,
        "melhor_sob_recall_id_calibracao": melhor_sob_recall_id,
        "avaliacao_holdout_no_limiar_recall": avaliacao_no_limiar_recall,
        "candidatos_avaliados": len(medidas),
        "contrato": {
            "somente_diagnostico": True,
            "autoriza_execucao": False,
            "autoriza_promocao": False,
            "ood_vira_treino": False,
        },
    }


def _medir_detector(
    exemplos_id: list[dict[str, Any]],
    probabilidades_id: list[float],
    probabilidades_ood: list[float],
    limiar: float,
) -> dict[str, Any]:
    indices_comando = [
        indice
        for indice, item in enumerate(exemplos_id)
        if bool(item.get("is_command")) and not bool(item.get("negated"))
    ]
    comandos_aceitos = sum(
        probabilidades_id[indice] < limiar for indice in indices_comando
    )
    id_aceitos = sum(probabilidade < limiar for probabilidade in probabilidades_id)
    ood_aceitos = sum(probabilidade < limiar for probabilidade in probabilidades_ood)
    return {
        "limiar": round(float(limiar), 8),
        "id_total": len(probabilidades_id),
        "id_aceitos": id_aceitos,
        "id_retention_rate": (
            float(id_aceitos) / len(probabilidades_id)
            if probabilidades_id
            else 0.0
        ),
        "id_command_total": len(indices_comando),
        "id_command_aceitos": comandos_aceitos,
        "id_command_retention_rate": (
            float(comandos_aceitos) / len(indices_comando)
            if indices_comando
            else 0.0
        ),
        "ood_total": len(probabilidades_ood),
        "ood_aceitos": ood_aceitos,
        "ood_false_accept_rate": (
            float(ood_aceitos) / len(probabilidades_ood)
            if probabilidades_ood
            else 0.0
        ),
    }


def calibrar_detector_ood(
    exemplos_id: Iterable[Mapping[str, Any]],
    probabilidades_id: Iterable[float],
    probabilidades_ood_calibracao: Iterable[float],
    probabilidades_ood_avaliacao: Iterable[float],
    *,
    alvo_falso_aceite_ood: float = 0.01,
    retencao_comandos_id_minima: float = 0.85,
) -> dict[str, Any]:
    """Calibra probabilidade OOD e exige confirmação no holdout reservado."""
    exemplos = [dict(item) for item in exemplos_id]
    probs_id = [max(0.0, min(1.0, float(item))) for item in probabilidades_id]
    probs_cal = [
        max(0.0, min(1.0, float(item)))
        for item in probabilidades_ood_calibracao
    ]
    probs_eval = [
        max(0.0, min(1.0, float(item)))
        for item in probabilidades_ood_avaliacao
    ]
    if len(exemplos) != len(probs_id):
        raise ValueError("exemplos ID e probabilidades precisam ter o mesmo tamanho")
    if not exemplos or not probs_cal or not probs_eval:
        raise ValueError("detector OOD exige ID, calibração e avaliação")
    alvo = float(alvo_falso_aceite_ood)
    retencao_minima = float(retencao_comandos_id_minima)
    if not 0.0 <= alvo <= 1.0 or not 0.0 <= retencao_minima <= 1.0:
        raise ValueError("metas do detector OOD precisam estar em [0, 1]")
    candidatos = sorted({0.0, 1.0, *probs_id, *probs_cal})
    medidas = [
        _medir_detector(exemplos, probs_id, probs_cal, limiar)
        for limiar in candidatos
    ]
    elegiveis = [
        item
        for item in medidas
        if item["ood_false_accept_rate"] <= alvo
        and item["id_command_retention_rate"] >= retencao_minima
    ]
    sob_alvo_ood = [
        item for item in medidas if item["ood_false_accept_rate"] <= alvo
    ]
    sob_retencao_id = [
        item
        for item in medidas
        if item["id_command_retention_rate"] >= retencao_minima
    ]
    melhor_sob_alvo_ood = sorted(
        sob_alvo_ood,
        key=lambda item: (
            -float(item["id_command_retention_rate"]),
            float(item["limiar"]),
        ),
    )[0] if sob_alvo_ood else {}
    melhor_sob_retencao_id = sorted(
        sob_retencao_id,
        key=lambda item: (
            float(item["ood_false_accept_rate"]),
            -float(item["id_command_retention_rate"]),
            float(item["limiar"]),
        ),
    )[0] if sob_retencao_id else {}
    escolhido = (
        sorted(
            elegiveis,
            key=lambda item: (
                -float(item["id_command_retention_rate"]),
                float(item["ood_false_accept_rate"]),
                float(item["limiar"]),
            ),
        )[0]
        if elegiveis
        else {}
    )
    avaliacao = (
        _medir_detector(
            exemplos,
            probs_id,
            probs_eval,
            float(escolhido["limiar"]),
        )
        if escolhido
        else {}
    )
    avaliacao_sob_alvo_ood = (
        _medir_detector(
            exemplos,
            probs_id,
            probs_eval,
            float(melhor_sob_alvo_ood["limiar"]),
        )
        if melhor_sob_alvo_ood
        else {}
    )
    avaliacao_sob_retencao_id = (
        _medir_detector(
            exemplos,
            probs_id,
            probs_eval,
            float(melhor_sob_retencao_id["limiar"]),
        )
        if melhor_sob_retencao_id
        else {}
    )
    aprovado = bool(
        escolhido
        and avaliacao["ood_false_accept_rate"] <= alvo
        and escolhido["id_command_retention_rate"] >= retencao_minima
    )
    return {
        "aprovado": aprovado,
        "motivo": (
            "aprovado"
            if aprovado
            else "holdout_ood_reprovou"
            if escolhido
            else "detector_nao_atingiu_calibracao"
        ),
        "limiar_recomendado": (
            float(escolhido["limiar"]) if aprovado else None
        ),
        "alvos": {
            "ood_false_accept_rate_maximo": alvo,
            "id_command_retention_rate_minimo": retencao_minima,
        },
        "calibracao": escolhido,
        "avaliacao_holdout": avaliacao,
        "melhor_sob_alvo_ood_calibracao": melhor_sob_alvo_ood,
        "melhor_sob_retencao_id_calibracao": melhor_sob_retencao_id,
        "avaliacao_holdout_sob_alvo_ood": avaliacao_sob_alvo_ood,
        "avaliacao_holdout_sob_retencao_id": avaliacao_sob_retencao_id,
        "candidatos_avaliados": len(medidas),
        "contrato": {
            "somente_diagnostico": True,
            "autoriza_execucao": False,
            "autoriza_promocao": False,
            "owner": "detector_pertinencia_catalogo_experimental",
        },
    }


def avaliar_detector_ood_semantico(
    exemplos_id: Iterable[Mapping[str, Any]],
    vetores_id: Any,
    grupos_id: Iterable[str],
    exemplos_ood: Iterable[Mapping[str, Any]],
    vetores_ood: Any,
    *,
    n_splits: int = 5,
    alvo_falso_aceite_ood: float = 0.01,
    retencao_comandos_id_minima: float = 0.85,
) -> dict[str, Any]:
    """Avalia uma cabeça OOD sem conectá-la ao modelo nem ao executor."""
    itens_id = [dict(item) for item in exemplos_id]
    grupos = [str(item or "").strip().casefold() for item in grupos_id]
    itens_ood = [dict(item) for item in exemplos_ood]
    matriz_id = np.asarray(vetores_id, dtype=np.float32)
    matriz_ood = np.asarray(vetores_ood, dtype=np.float32)
    if matriz_id.ndim != 2 or matriz_ood.ndim != 2:
        raise ValueError("vetores ID e OOD precisam ser matrizes")
    if len(itens_id) != len(matriz_id) or len(itens_id) != len(grupos):
        raise ValueError("exemplos, vetores e grupos ID precisam ter o mesmo tamanho")
    if len(itens_ood) != len(matriz_ood):
        raise ValueError("exemplos e vetores OOD precisam ter o mesmo tamanho")
    if matriz_id.shape[1] != matriz_ood.shape[1]:
        raise ValueError("vetores ID e OOD precisam ter a mesma dimensão")
    indices_ood_treino = [
        indice
        for indice, item in enumerate(itens_ood)
        if str(item.get("partition") or "").casefold() == "training"
    ]
    indices_ood_calibracao = [
        indice
        for indice, item in enumerate(itens_ood)
        if str(item.get("partition") or "").casefold() == "calibration"
    ]
    indices_ood_avaliacao = [
        indice
        for indice, item in enumerate(itens_ood)
        if str(item.get("partition") or "").casefold() == "evaluation"
    ]
    if not indices_ood_treino or not indices_ood_calibracao or not indices_ood_avaliacao:
        raise ValueError("detector OOD exige training, calibration e evaluation")
    familias_por_particao = {
        particao: {
            str(item.get("family") or "").strip().casefold()
            for item in itens_ood
            if str(item.get("partition") or "").strip().casefold() == particao
        }
        for particao in ("training", "calibration", "evaluation")
    }
    if any(not familias for familias in familias_por_particao.values()):
        raise ValueError("cada partição OOD precisa de famílias explícitas")
    compartilhadas = (
        (familias_por_particao["training"] & familias_por_particao["calibration"])
        | (familias_por_particao["training"] & familias_por_particao["evaluation"])
        | (familias_por_particao["calibration"] & familias_por_particao["evaluation"])
    )
    if compartilhadas:
        raise ValueError("famílias OOD não podem atravessar partições")
    grupos_unicos = sorted(set(grupos))
    quantidade_splits = min(int(n_splits), len(grupos_unicos))
    if quantidade_splits < 2:
        raise ValueError("detector OOD exige ao menos dois grupos ID")

    probabilidades_id = np.zeros(len(itens_id), dtype=np.float64)
    probabilidades_calibracao: list[float] = []
    probabilidades_avaliacao: list[float] = []
    folds: list[dict[str, Any]] = []
    divisor = GroupKFold(n_splits=quantidade_splits)
    indices_id = np.arange(len(itens_id))
    x_ood_treino = matriz_ood[indices_ood_treino]
    for numero, (indices_treino, indices_validacao) in enumerate(
        divisor.split(indices_id, groups=grupos),
        1,
    ):
        x_treino = np.vstack((matriz_id[indices_treino], x_ood_treino))
        y_treino = np.asarray(
            [False] * len(indices_treino) + [True] * len(indices_ood_treino)
        )
        classificador = SGDClassifier(
            loss="log_loss",
            class_weight="balanced",
            max_iter=2000,
            tol=1e-4,
            random_state=42,
        ).fit(x_treino, y_treino)
        indice_ood = list(classificador.classes_).index(True)
        probs_id_fold = classificador.predict_proba(
            matriz_id[indices_validacao]
        )[:, indice_ood]
        probabilidades_id[indices_validacao] = probs_id_fold
        probs_cal_fold = classificador.predict_proba(
            matriz_ood[indices_ood_calibracao]
        )[:, indice_ood]
        probs_eval_fold = classificador.predict_proba(
            matriz_ood[indices_ood_avaliacao]
        )[:, indice_ood]
        probabilidades_calibracao.extend(float(item) for item in probs_cal_fold)
        probabilidades_avaliacao.extend(float(item) for item in probs_eval_fold)
        folds.append(
            {
                "fold": numero,
                "id_treino": len(indices_treino),
                "id_validacao": len(indices_validacao),
                "ood_treino": len(indices_ood_treino),
                "ood_calibracao": len(indices_ood_calibracao),
                "ood_avaliacao": len(indices_ood_avaliacao),
                "grupos_compartilhados": sorted(
                    {grupos[int(i)] for i in indices_treino}
                    & {grupos[int(i)] for i in indices_validacao}
                ),
            }
        )
    calibracao = calibrar_detector_ood(
        itens_id,
        probabilidades_id.tolist(),
        probabilidades_calibracao,
        probabilidades_avaliacao,
        alvo_falso_aceite_ood=alvo_falso_aceite_ood,
        retencao_comandos_id_minima=retencao_comandos_id_minima,
    )
    return {
        "versao": 1,
        "arquitetura": "minilm_sgd_catalog_membership",
        "totais": {
            "id": len(itens_id),
            "grupos_id": len(grupos_unicos),
            "ood_treino": len(indices_ood_treino),
            "ood_calibracao_por_fold": len(indices_ood_calibracao),
            "ood_avaliacao_por_fold": len(indices_ood_avaliacao),
            "folds": quantidade_splits,
        },
        "calibracao": calibracao,
        "folds": folds,
        "contrato": {
            "somente_diagnostico": True,
            "autoriza_execucao": False,
            "autoriza_promocao": False,
            "ood_treina_somente_detector": True,
            "ood_treina_intent_ou_acao": False,
        },
    }


def avaliar_detector_ood_prototipos(
    exemplos_id: Iterable[Mapping[str, Any]],
    vetores_id: Any,
    grupos_id: Iterable[str],
    exemplos_ood: Iterable[Mapping[str, Any]],
    vetores_ood: Any,
    *,
    n_splits: int = 5,
    alvo_falso_aceite_ood: float = 0.01,
    retencao_comandos_id_minima: float = 0.85,
) -> dict[str, Any]:
    """Mede distância a protótipos do catálogo sem treinar com exemplos OOD."""
    itens_id = [dict(item) for item in exemplos_id]
    grupos = [str(item or "").strip().casefold() for item in grupos_id]
    itens_ood = [dict(item) for item in exemplos_ood]
    matriz_id = np.asarray(vetores_id, dtype=np.float32)
    matriz_ood = np.asarray(vetores_ood, dtype=np.float32)
    if matriz_id.ndim != 2 or matriz_ood.ndim != 2:
        raise ValueError("vetores ID e OOD precisam ser matrizes")
    if len(itens_id) != len(matriz_id) or len(itens_id) != len(grupos):
        raise ValueError("exemplos, vetores e grupos ID precisam ter o mesmo tamanho")
    if len(itens_ood) != len(matriz_ood) or matriz_id.shape[1] != matriz_ood.shape[1]:
        raise ValueError("vetores OOD incompatíveis")
    indices_calibracao = [
        indice
        for indice, item in enumerate(itens_ood)
        if str(item.get("partition") or "").casefold() == "calibration"
    ]
    indices_avaliacao = [
        indice
        for indice, item in enumerate(itens_ood)
        if str(item.get("partition") or "").casefold() == "evaluation"
    ]
    if not indices_calibracao or not indices_avaliacao:
        raise ValueError("protótipos OOD exigem calibration e evaluation")
    familias_calibracao = {
        str(itens_ood[indice].get("family") or "").strip().casefold()
        for indice in indices_calibracao
    }
    familias_avaliacao = {
        str(itens_ood[indice].get("family") or "").strip().casefold()
        for indice in indices_avaliacao
    }
    if not familias_calibracao or not familias_avaliacao:
        raise ValueError("partições OOD precisam de famílias explícitas")
    if familias_calibracao & familias_avaliacao:
        raise ValueError("famílias OOD não podem atravessar calibração e avaliação")

    def normalizar(matriz: Any) -> Any:
        norma = np.linalg.norm(matriz, axis=1, keepdims=True)
        return matriz / np.clip(norma, 1e-12, None)

    matriz_id = normalizar(matriz_id)
    matriz_ood = normalizar(matriz_ood)
    grupos_unicos = sorted(set(grupos))
    quantidade_splits = min(int(n_splits), len(grupos_unicos))
    if quantidade_splits < 2:
        raise ValueError("protótipos OOD exigem ao menos dois grupos ID")
    scores_id = np.zeros(len(itens_id), dtype=np.float64)
    scores_calibracao: list[float] = []
    scores_avaliacao: list[float] = []
    folds: list[dict[str, Any]] = []
    divisor = GroupKFold(n_splits=quantidade_splits)
    indices_id = np.arange(len(itens_id))
    for numero, (indices_treino, indices_validacao) in enumerate(
        divisor.split(indices_id, groups=grupos),
        1,
    ):
        por_variante: dict[tuple[str, str], list[int]] = {}
        for indice in indices_treino:
            item = itens_id[int(indice)]
            intent = str(item.get("intent") or "").strip().upper()
            acao = str(item.get("action") or "none").strip().casefold()
            if bool(item.get("is_command")) and intent not in {"", "NONE"}:
                por_variante.setdefault((intent, acao), []).append(int(indice))
        if not por_variante:
            raise ValueError("fold sem variantes conhecidas para protótipos")
        prototipos = np.vstack(
            [
                normalizar(matriz_id[indices].mean(axis=0, keepdims=True))[0]
                for indices in por_variante.values()
            ]
        )

        def pontuar(matriz: Any) -> Any:
            similaridade = normalizar(matriz) @ prototipos.T
            return np.clip((1.0 - similaridade.max(axis=1)) / 2.0, 0.0, 1.0)

        scores_id[indices_validacao] = pontuar(matriz_id[indices_validacao])
        scores_calibracao.extend(
            float(item) for item in pontuar(matriz_ood[indices_calibracao])
        )
        scores_avaliacao.extend(
            float(item) for item in pontuar(matriz_ood[indices_avaliacao])
        )
        folds.append(
            {
                "fold": numero,
                "id_treino": len(indices_treino),
                "id_validacao": len(indices_validacao),
                "prototipos": len(prototipos),
                "grupos_compartilhados": sorted(
                    {grupos[int(i)] for i in indices_treino}
                    & {grupos[int(i)] for i in indices_validacao}
                ),
            }
        )
    calibracao = calibrar_detector_ood(
        itens_id,
        scores_id.tolist(),
        scores_calibracao,
        scores_avaliacao,
        alvo_falso_aceite_ood=alvo_falso_aceite_ood,
        retencao_comandos_id_minima=retencao_comandos_id_minima,
    )
    return {
        "versao": 1,
        "arquitetura": "minilm_catalog_prototype_distance",
        "totais": {
            "id": len(itens_id),
            "grupos_id": len(grupos_unicos),
            "ood_calibracao_por_fold": len(indices_calibracao),
            "ood_avaliacao_por_fold": len(indices_avaliacao),
            "folds": quantidade_splits,
        },
        "calibracao": calibracao,
        "folds": folds,
        "contrato": {
            "somente_diagnostico": True,
            "autoriza_execucao": False,
            "autoriza_promocao": False,
            "ood_treina_detector": False,
            "owner": "distancia_prototipos_catalogo_experimental",
        },
    }
