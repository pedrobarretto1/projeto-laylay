"""Validação cruzada por famílias linguísticas sem consultar o challenge."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable, Mapping

from sklearn.model_selection import GroupKFold

from mente_laylay.especialistas.capacidades import intents_registradas

from .avaliacao import avaliar_previsoes, head_aplicavel
from .calibracao_ood import calibrar_limiar_ood, carregar_dataset_ood
from .cobertura import carregar_manifesto_variantes
from .dataset import carregar_jsonl
from .modelo import (
    ARQUITETURAS_ACAO_PERMITIDAS,
    ARQUITETURAS_COMANDO_PERMITIDAS,
    ESTRATEGIAS_PERMITIDAS,
    REPRESENTACOES_PERMITIDAS,
    treinar_modelo,
    veto_intent_comando,
)


AGRUPAMENTOS_PERMITIDOS = frozenset({"family", "validation_group"})
ESTRATEGIAS_PARTICAO_PERMITIDAS = frozenset({"group_kfold", "hash_estavel"})


def atribuir_fold_estavel(grupo: str, *, n_splits: int) -> int:
    """Atribui grupo a fold sem depender dos demais grupos presentes."""
    quantidade = int(n_splits)
    if quantidade < 2:
        raise ValueError("partição estável exige ao menos dois folds")
    normalizado = str(grupo or "").strip().casefold()
    if not normalizado:
        raise ValueError("partição estável exige grupo não vazio")
    digest = hashlib.sha256(normalizado.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % quantidade


def varrer_limiares_comando(
    esperados: Iterable[Mapping[str, Any]],
    previstos: Iterable[Mapping[str, Any]],
    *,
    arquitetura_comando: str,
    acoes_por_intent: Mapping[str, Iterable[str]] | None = None,
    limiares_fallback_intent_semantica: Mapping[str, float] | None = None,
    limiares: Iterable[float] = (),
) -> list[dict[str, Any]]:
    """Reaplica somente o gate usando probabilidades out-of-fold já obtidas."""
    pares = list(zip(esperados, previstos, strict=True))
    arquitetura = str(arquitetura_comando or "").strip().casefold()
    if arquitetura not in ARQUITETURAS_COMANDO_PERMITIDAS:
        raise ValueError(f"arquitetura de comando desconhecida: {arquitetura}")
    valores = sorted({round(float(valor), 6) for valor in limiares})
    if any(valor < 0.5 or valor > 1.0 for valor in valores):
        raise ValueError("limiares de comando precisam estar em [0.5, 1.0]")
    resultados: list[dict[str, Any]] = []
    for limiar in valores:
        ajustados: list[dict[str, Any]] = []
        for _esperado, previsto_original in pares:
            previsto = dict(previsto_original)
            comando_bruto = bool(
                previsto.get("raw_is_command", previsto.get("is_command"))
            )
            probabilidade = float(
                previsto.get("command_probability")
                if previsto.get("command_probability") is not None
                else dict(previsto.get("confidence") or {}).get("command", 0.0)
            )
            intent = str(previsto.get("intent") or "").strip().upper()
            intent_gate = str(
                previsto.get("gate_intent") or intent
            ).strip().upper()
            previsto["is_command"] = bool(
                comando_bruto
                and probabilidade >= limiar
                and not veto_intent_comando(
                    arquitetura,
                    intent=intent,
                    intent_gate=intent_gate,
                    confianca_intent=float(
                        dict(previsto.get("confidence") or {}).get(
                            "intent", 0.0
                        )
                    ),
                    limiares_fallback_intent_semantica=(
                        limiares_fallback_intent_semantica
                    ),
                )
            )
            ajustados.append(previsto)
        metricas = avaliar_previsoes(
            [esperado for esperado, _previsto in pares],
            ajustados,
            acoes_por_intent=acoes_por_intent,
        )
        resultados.append({
            "limiar": limiar,
            "false_command_count": metricas["false_command_count"],
            "false_command_rate": metricas["false_command_rate"],
            "command_precision": metricas["command_precision"],
            "command_recall": metricas["command_recall"],
        })
    return resultados


def varrer_limiares_comando_por_intent(
    esperados: Iterable[Mapping[str, Any]],
    previstos: Iterable[Mapping[str, Any]],
    *,
    intent_alvo: str,
    limiar_padrao: float,
    arquitetura_comando: str,
    acoes_por_intent: Mapping[str, Iterable[str]] | None = None,
    limiares_fallback_intent_semantica: Mapping[str, float] | None = None,
    limiares: Iterable[float] = (),
) -> list[dict[str, Any]]:
    """Varia um único intent e preserva o limiar global nos demais."""
    pares = list(zip(esperados, previstos, strict=True))
    alvo = str(intent_alvo or "").strip().upper()
    if not alvo or alvo == "NONE":
        raise ValueError("intent_alvo precisa ser uma intent operacional")
    arquitetura = str(arquitetura_comando or "").strip().casefold()
    if arquitetura not in ARQUITETURAS_COMANDO_PERMITIDAS:
        raise ValueError(f"arquitetura de comando desconhecida: {arquitetura}")
    padrao = float(limiar_padrao)
    valores = sorted({round(float(valor), 6) for valor in limiares})
    if not 0.5 <= padrao <= 1.0 or any(
        valor < 0.5 or valor > 1.0 for valor in valores
    ):
        raise ValueError("limiares de comando precisam estar em [0.5, 1.0]")
    resultados: list[dict[str, Any]] = []
    for limiar_alvo in valores:
        ajustados: list[dict[str, Any]] = []
        mudancas: list[dict[str, Any]] = []
        for _esperado, previsto_original in pares:
            previsto = dict(previsto_original)
            intent = str(previsto.get("intent") or "").strip().upper()
            intent_gate = str(
                previsto.get("gate_intent") or intent
            ).strip().upper()
            limiar = (
                limiar_alvo
                if intent == alvo and intent_gate == alvo
                else padrao
            )
            comando_bruto = bool(
                previsto.get("raw_is_command", previsto.get("is_command"))
            )
            probabilidade = float(
                previsto.get("command_probability")
                if previsto.get("command_probability") is not None
                else dict(previsto.get("confidence") or {}).get("command", 0.0)
            )
            previsto["is_command"] = bool(
                comando_bruto
                and probabilidade >= limiar
                and not veto_intent_comando(
                    arquitetura,
                    intent=intent,
                    intent_gate=intent_gate,
                    confianca_intent=float(
                        dict(previsto.get("confidence") or {}).get(
                            "intent", 0.0
                        )
                    ),
                    limiares_fallback_intent_semantica=(
                        limiares_fallback_intent_semantica
                    ),
                )
            )
            if previsto["is_command"] != bool(previsto_original.get("is_command")):
                mudancas.append({
                    "text": str(_esperado.get("text") or ""),
                    "is_command_esperado": bool(_esperado.get("is_command")),
                    "intent_esperada": str(_esperado.get("intent") or "").upper(),
                    "is_command_anterior": bool(previsto_original.get("is_command")),
                    "is_command_ajustado": bool(previsto["is_command"]),
                    "intent_prevista": intent,
                    "command_probability": probabilidade,
                })
            ajustados.append(previsto)
        metricas = avaliar_previsoes(
            [esperado for esperado, _previsto in pares],
            ajustados,
            acoes_por_intent=acoes_por_intent,
        )
        resultados.append({
            "intent": alvo,
            "limiar": limiar_alvo,
            "false_command_count": metricas["false_command_count"],
            "false_command_rate": metricas["false_command_rate"],
            "command_precision": metricas["command_precision"],
            "command_recall": metricas["command_recall"],
            "mudancas": mudancas[:20],
            "mudancas_total": len(mudancas),
        })
    return resultados


def diagnosticar_erros_por_familia(
    esperados: Iterable[Mapping[str, Any]],
    previstos: Iterable[Mapping[str, Any]],
    *,
    max_amostras_por_familia: int = 3,
) -> dict[str, Any]:
    """Expõe a primeira fronteira de erro sem transformar previsão em rótulo."""
    pares = list(zip(esperados, previstos, strict=True))
    por_familia: dict[str, dict[str, Any]] = {}

    def acao_prevista(item: Mapping[str, Any]) -> str:
        if item.get("raw_action") is not None:
            return str(item.get("raw_action") or "none").strip().casefold()
        params = item.get("params")
        if isinstance(params, Mapping):
            return str(params.get("acao") or "none").strip().casefold()
        return str(item.get("action") or "none").strip().casefold()

    for esperado_original, previsto_original in pares:
        esperado = dict(esperado_original)
        previsto = dict(previsto_original)
        erros: list[str] = []
        comando_esperado = bool(esperado.get("is_command"))
        comando_previsto = bool(previsto.get("is_command"))
        intent_esperada = str(esperado.get("intent") or "").upper().strip()
        intent_prevista = str(previsto.get("intent") or "").upper().strip()
        negacao_esperada = bool(esperado.get("negated"))
        negacao_prevista = bool(previsto.get("negated"))
        acao_esperada = str(esperado.get("action") or "none").casefold().strip()
        acao_observada = acao_prevista(previsto)

        if (
            head_aplicavel(esperado, "command")
            and not comando_esperado
            and comando_previsto
        ):
            erros.append("falso_comando")
        if (
            head_aplicavel(esperado, "command")
            and comando_esperado
            and not comando_previsto
        ):
            erros.append("comando_perdido")
        if (
            head_aplicavel(esperado, "intent")
            and intent_esperada != intent_prevista
        ):
            erros.append("intent_divergente")
        if (
            head_aplicavel(esperado, "negation")
            and negacao_esperada
            and not negacao_prevista
        ):
            erros.append("negacao_perdida")
        if (
            head_aplicavel(esperado, "negation")
            and not negacao_esperada
            and negacao_prevista
        ):
            erros.append("negacao_falsa")
        if (
            head_aplicavel(esperado, "action")
            and comando_esperado
            and acao_esperada != acao_observada
        ):
            erros.append("acao_divergente")
        if not erros:
            continue

        familia = str(esperado.get("family") or "sem_familia").casefold().strip()
        registro = por_familia.setdefault(
            familia,
            {
                "family": familia,
                "domain": str(esperado.get("domain") or "geral").casefold(),
                "total_erros": 0,
                "tipos": {},
                "amostras": [],
            },
        )
        registro["total_erros"] += 1
        for erro in erros:
            registro["tipos"][erro] = int(registro["tipos"].get(erro, 0)) + 1
        if len(registro["amostras"]) < max(0, int(max_amostras_por_familia)):
            registro["amostras"].append({
                "text": str(esperado.get("text") or ""),
                "erros": erros,
                "esperado": {
                    "intent": intent_esperada,
                    "is_command": comando_esperado,
                    "negated": negacao_esperada,
                    "action": acao_esperada,
                },
                "previsto": {
                    "intent": intent_prevista,
                    "gate_intent": str(
                        previsto.get("gate_intent") or intent_prevista
                    ).upper().strip(),
                    "is_command": comando_previsto,
                    "raw_is_command": bool(
                        previsto.get("raw_is_command", comando_previsto)
                    ),
                    "command_veto_reason": str(
                        previsto.get("command_veto_reason") or ""
                    ),
                    "command_probability": (
                        float(previsto["command_probability"])
                        if previsto.get("command_probability") is not None
                        else None
                    ),
                    "command_threshold": (
                        float(previsto["command_threshold"])
                        if previsto.get("command_threshold") is not None
                        else None
                    ),
                    "command_head_scope": str(
                        previsto.get("command_head_scope") or "GLOBAL"
                    ).upper().strip(),
                    "intent_gate_confidence": (
                        float(dict(previsto.get("confidence") or {}).get(
                            "intent_gate"
                        ))
                        if dict(previsto.get("confidence") or {}).get(
                            "intent_gate"
                        ) is not None
                        else None
                    ),
                    "negated": negacao_prevista,
                    "action": acao_observada,
                },
            })

    ordenados = sorted(
        por_familia.values(),
        key=lambda item: (-int(item["total_erros"]), str(item["family"])),
    )
    totais_tipos: dict[str, int] = {}
    for item in ordenados:
        for tipo, total in dict(item["tipos"]).items():
            totais_tipos[tipo] = totais_tipos.get(tipo, 0) + int(total)
    return {
        "familias_com_erro": len(ordenados),
        "totais_por_tipo": dict(sorted(totais_tipos.items())),
        "por_familia": ordenados,
        "contrato": {
            "somente_diagnostico": True,
            "autoriza_execucao": False,
            "predicao_vira_label": False,
        },
    }


def diagnosticar_fronteira_intent_gate(
    esperados: Iterable[Mapping[str, Any]],
    previstos: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Lista casos cuja única proteção de intenção é o gate lexical ``NONE``."""
    candidatos: list[dict[str, Any]] = []
    for esperado_original, previsto_original in zip(
        esperados,
        previstos,
        strict=True,
    ):
        esperado = dict(esperado_original)
        previsto = dict(previsto_original)
        intent = str(previsto.get("intent") or "").strip().upper()
        intent_gate = str(
            previsto.get("gate_intent") or intent
        ).strip().upper()
        probabilidade = float(previsto.get("command_probability") or 0.0)
        limiar = float(previsto.get("command_threshold") or 0.5)
        if not (
            head_aplicavel(esperado, "command")
            and intent != "NONE"
            and intent_gate == "NONE"
            and bool(previsto.get("raw_is_command"))
            and probabilidade >= limiar
        ):
            continue
        confiancas = dict(previsto.get("confidence") or {})
        confianca = confiancas.get("intent_gate")
        confianca_intent = confiancas.get("intent")
        candidatos.append({
            "text": str(esperado.get("text") or ""),
            "family": str(esperado.get("family") or "sem_familia")
            .strip()
            .casefold(),
            "intent": intent,
            "is_command_esperado": bool(esperado.get("is_command")),
            "command_probability": probabilidade,
            "command_threshold": limiar,
            "intent_gate_confidence": (
                float(confianca) if confianca is not None else None
            ),
            "intent_confidence": (
                float(confianca_intent)
                if confianca_intent is not None
                else None
            ),
        })
    comandos = sum(item["is_command_esperado"] for item in candidatos)
    return {
        "totais": {
            "candidatos": len(candidatos),
            "comandos_esperados": comandos,
            "nao_comandos_esperados": len(candidatos) - comandos,
        },
        "candidatos": candidatos,
        "contrato": {
            "somente_diagnostico": True,
            "autoriza_execucao": False,
            "altera_decisao": False,
        },
    }


def validar_por_familias(
    exemplos: Iterable[Mapping[str, Any]],
    *,
    n_splits: int = 5,
    estrategia: str = "logistic",
    arquitetura_comando: str = "independent",
    arquitetura_acao: str = "global",
    limiar_comando: float = 0.5,
    limiares_comando_por_intent: Mapping[str, float] | None = None,
    limiares_fallback_intent_semantica: Mapping[str, float] | None = None,
    representacao: str = "tfidf",
    encoder_semantico: Any = None,
    pasta_encoder_semantico: str | Path | None = None,
    sha256_encoder_semantico: str = "",
    exemplos_ood: Iterable[Mapping[str, Any]] = (),
    alvo_falso_aceite_ood: float = 0.01,
    recall_id_minimo_ood: float = 0.85,
    agrupamento: str = "family",
    estrategia_particao: str = "group_kfold",
    quantidade_base_comparavel: int | None = None,
    acoes_por_intent: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, Any]:
    """Avalia generalização mantendo cada família inteira em um único fold."""
    itens = [dict(item) for item in exemplos]
    itens_ood = [dict(item) for item in exemplos_ood]
    if not itens:
        raise ValueError("validação cruzada exige exemplos")
    familias = [
        str(item.get("family") or "").strip().casefold()
        for item in itens
    ]
    if any(not familia for familia in familias):
        raise ValueError("todo exemplo precisa de family")
    agrupamento_normalizado = str(agrupamento or "").strip().casefold()
    if agrupamento_normalizado not in AGRUPAMENTOS_PERMITIDOS:
        raise ValueError(f"agrupamento desconhecido: {agrupamento_normalizado}")
    grupos = [
        str(
            (
                item.get("validation_group")
                if agrupamento_normalizado == "validation_group"
                else item.get("family")
            )
            or ""
        ).strip().casefold()
        or familias[indice]
        for indice, item in enumerate(itens)
    ]
    familias_unicas = sorted(set(familias))
    grupos_unicos = sorted(set(grupos))
    estrategia_normalizada = str(estrategia or "").strip().casefold()
    if estrategia_normalizada not in ESTRATEGIAS_PERMITIDAS:
        raise ValueError(f"estratégia neural desconhecida: {estrategia_normalizada}")
    representacao_normalizada = str(representacao or "").strip().casefold()
    if representacao_normalizada not in REPRESENTACOES_PERMITIDAS:
        raise ValueError(
            f"representação neural desconhecida: {representacao_normalizada}"
        )
    arquitetura_normalizada = str(arquitetura_acao or "").strip().casefold()
    if arquitetura_normalizada not in ARQUITETURAS_ACAO_PERMITIDAS:
        raise ValueError(
            f"arquitetura de ação desconhecida: {arquitetura_normalizada}"
        )
    arquitetura_comando_normalizada = str(
        arquitetura_comando or ""
    ).strip().casefold()
    if arquitetura_comando_normalizada not in ARQUITETURAS_COMANDO_PERMITIDAS:
        raise ValueError(
            "arquitetura de comando desconhecida: "
            f"{arquitetura_comando_normalizada}"
        )
    quantidade_splits = min(int(n_splits), len(grupos_unicos))
    if quantidade_splits < 2:
        raise ValueError("validação cruzada exige ao menos duas famílias")

    previsoes: list[dict[str, Any] | None] = [None] * len(itens)
    previsoes_ood_calibracao: list[dict[str, Any]] = []
    previsoes_ood_avaliacao: list[dict[str, Any]] = []
    folds: list[dict[str, Any]] = []
    indices = list(range(len(itens)))
    estrategia_particao_normalizada = str(
        estrategia_particao or ""
    ).strip().casefold()
    if estrategia_particao_normalizada not in ESTRATEGIAS_PARTICAO_PERMITIDAS:
        raise ValueError(
            f"estratégia de partição desconhecida: {estrategia_particao_normalizada}"
        )
    if estrategia_particao_normalizada == "hash_estavel":
        folds_indices = []
        for numero in range(quantidade_splits):
            indices_validacao = [
                indice
                for indice, grupo in enumerate(grupos)
                if atribuir_fold_estavel(grupo, n_splits=quantidade_splits) == numero
            ]
            if not indices_validacao:
                raise ValueError(
                    "partição hash_estavel produziu fold vazio; reduza --splits"
                )
            conjunto_validacao = set(indices_validacao)
            indices_treino = [
                indice for indice in indices if indice not in conjunto_validacao
            ]
            folds_indices.append((indices_treino, indices_validacao))
    else:
        divisor = GroupKFold(n_splits=quantidade_splits)
        folds_indices = list(divisor.split(indices, groups=grupos))

    with tempfile.TemporaryDirectory(prefix="laylay-neural-family-cv-") as temporario:
        pasta = Path(temporario)
        for numero, (indices_treino, indices_validacao) in enumerate(
            folds_indices,
            1,
        ):
            treino = [itens[int(indice)] for indice in indices_treino]
            validacao = [itens[int(indice)] for indice in indices_validacao]
            modelo = treinar_modelo(
                treino,
                caminho=pasta / f"fold_{numero}.joblib",
                versao=f"family-cv-fold-{numero}",
                estrategia=estrategia_normalizada,
                arquitetura_comando=arquitetura_comando_normalizada,
                arquitetura_acao=arquitetura_normalizada,
                limiar_comando=limiar_comando,
                limiares_comando_por_intent=limiares_comando_por_intent,
                limiares_fallback_intent_semantica=(
                    limiares_fallback_intent_semantica
                ),
                representacao=representacao_normalizada,
                encoder_semantico=encoder_semantico,
                pasta_encoder_semantico=pasta_encoder_semantico,
                sha256_encoder_semantico=sha256_encoder_semantico,
            )
            previstos_fold = [modelo.prever(item["text"]) for item in validacao]
            for item_ood in itens_ood:
                previsto_ood = modelo.prever(str(item_ood.get("text") or ""))
                if str(item_ood.get("partition") or "").casefold() == "calibration":
                    previsoes_ood_calibracao.append(previsto_ood)
                elif str(item_ood.get("partition") or "").casefold() == "evaluation":
                    previsoes_ood_avaliacao.append(previsto_ood)
                else:
                    raise ValueError("exemplo OOD possui partition desconhecida")
            for indice, previsto in zip(
                indices_validacao,
                previstos_fold,
                strict=True,
            ):
                previsoes[int(indice)] = previsto

            familias_treino = {familias[int(indice)] for indice in indices_treino}
            familias_validacao = {
                familias[int(indice)] for indice in indices_validacao
            }
            compartilhadas = sorted(familias_treino & familias_validacao)
            if compartilhadas:
                raise RuntimeError("GroupKFold compartilhou famílias entre partições")
            grupos_treino = {grupos[int(indice)] for indice in indices_treino}
            grupos_validacao = {
                grupos[int(indice)] for indice in indices_validacao
            }
            grupos_compartilhados = sorted(grupos_treino & grupos_validacao)
            if grupos_compartilhados:
                raise RuntimeError("GroupKFold compartilhou grupos entre partições")
            folds.append(
                {
                    "fold": numero,
                    "exemplos_treino": len(treino),
                    "exemplos_validacao": len(validacao),
                    "familias_treino": len(familias_treino),
                    "familias_validacao": len(familias_validacao),
                    "familias_compartilhadas": compartilhadas,
                    "grupos_treino": len(grupos_treino),
                    "grupos_validacao": len(grupos_validacao),
                    "grupos_compartilhados": grupos_compartilhados,
                    "metricas": avaliar_previsoes(
                        validacao,
                        previstos_fold,
                        acoes_por_intent=acoes_por_intent,
                    ),
                }
            )

    if any(previsto is None for previsto in previsoes):
        raise RuntimeError("existem exemplos sem previsão out-of-fold")
    previstos_finais = [dict(previsto or {}) for previsto in previsoes]
    quantidade_comparavel = (
        len(itens)
        if quantidade_base_comparavel is None
        else int(quantidade_base_comparavel)
    )
    if not 0 < quantidade_comparavel <= len(itens):
        raise ValueError("quantidade_base_comparavel fora do dataset")
    calibracao_ood = (
        calibrar_limiar_ood(
            itens,
            previstos_finais,
            previsoes_ood_calibracao,
            previsoes_ood_avaliacao,
            alvo_falso_aceite_ood=alvo_falso_aceite_ood,
            recall_id_minimo=recall_id_minimo_ood,
        )
        if itens_ood
        else {}
    )
    return {
        "versao": 1,
        "gerado_em": time.time(),
        "estrategia": estrategia_normalizada,
        "arquitetura_comando": arquitetura_comando_normalizada,
        "arquitetura_acao": arquitetura_normalizada,
        "limiar_comando": float(limiar_comando),
        "limiares_comando_por_intent": dict(
            sorted(dict(limiares_comando_por_intent or {}).items())
        ),
        "limiares_fallback_intent_semantica": dict(sorted(
            dict(limiares_fallback_intent_semantica or {}).items()
        )),
        "representacao": representacao_normalizada,
        "encoder_semantico_configurado": bool(
            encoder_semantico is not None or pasta_encoder_semantico is not None
        ),
        "encoder_semantico_sha256": str(sha256_encoder_semantico or ""),
        "agrupamento": agrupamento_normalizado,
        "estrategia_particao": estrategia_particao_normalizada,
        "totais": {
            "exemplos": len(itens),
            "exemplos_avaliados": len(previstos_finais),
            "familias": len(familias_unicas),
            "grupos_validacao": len(grupos_unicos),
            "folds": quantidade_splits,
            "exemplos_base_comparavel": quantidade_comparavel,
        },
        "metricas": avaliar_previsoes(
            itens,
            previstos_finais,
            acoes_por_intent=acoes_por_intent,
        ),
        "metricas_base_comparavel": avaliar_previsoes(
            itens[:quantidade_comparavel],
            previstos_finais[:quantidade_comparavel],
            acoes_por_intent=acoes_por_intent,
        ),
        "varredura_limiar_comando": varrer_limiares_comando(
            itens,
            previstos_finais,
            arquitetura_comando=arquitetura_comando_normalizada,
            acoes_por_intent=acoes_por_intent,
            limiares_fallback_intent_semantica=(
                limiares_fallback_intent_semantica
            ),
            limiares=(0.5 + passo * 0.001 for passo in range(501)),
        ),
        "varredura_limiar_comando_por_intent": {
            intent: varrer_limiares_comando_por_intent(
                itens,
                previstos_finais,
                intent_alvo=intent,
                limiar_padrao=float(limiar_comando),
                arquitetura_comando=arquitetura_comando_normalizada,
                acoes_por_intent=acoes_por_intent,
                limiares_fallback_intent_semantica=(
                    limiares_fallback_intent_semantica
                ),
                limiares=(0.5 + passo * 0.005 for passo in range(51)),
            )
            for intent in sorted(dict(acoes_por_intent or {}))
        },
        "varredura_limiar_por_intent_base_comparavel": {
            intent: varrer_limiares_comando_por_intent(
                itens[:quantidade_comparavel],
                previstos_finais[:quantidade_comparavel],
                intent_alvo=intent,
                limiar_padrao=float(limiar_comando),
                arquitetura_comando=arquitetura_comando_normalizada,
                acoes_por_intent=acoes_por_intent,
                limiares_fallback_intent_semantica=(
                    limiares_fallback_intent_semantica
                ),
                limiares=(0.5 + passo * 0.005 for passo in range(51)),
            )
            for intent in sorted(dict(acoes_por_intent or {}))
        },
        "diagnostico_erros": diagnosticar_erros_por_familia(
            itens,
            previstos_finais,
        ),
        "diagnostico_intent_gate": diagnosticar_fronteira_intent_gate(
            itens,
            previstos_finais,
        ),
        "calibracao_ood": calibracao_ood,
        "folds": folds,
        "contrato": {
            "somente_diagnostico": True,
            "challenge_usado": False,
            "familias_inteiras_por_fold": True,
            "grupos_semanticos_inteiros_por_fold": (
                agrupamento_normalizado == "validation_group"
            ),
            "autoriza_execucao": False,
            "autoriza_promocao": False,
            "ood_usado_como_treino": False,
        },
    }


def gerar_relatorio_validacao_cruzada(
    *,
    dev_path: str | Path,
    destino: str | Path,
    lotes_candidatos: Iterable[str | Path] = (),
    n_splits: int = 5,
    estrategia: str = "logistic",
    arquitetura_comando: str = "independent",
    arquitetura_acao: str = "global",
    limiar_comando: float = 0.5,
    limiares_comando_por_intent: Mapping[str, float] | None = None,
    limiares_fallback_intent_semantica: Mapping[str, float] | None = None,
    representacao: str = "tfidf",
    pasta_encoder_semantico: str | Path | None = None,
    sha256_encoder_semantico: str = "",
    ood_path: str | Path | None = None,
    alvo_falso_aceite_ood: float = 0.01,
    recall_id_minimo_ood: float = 0.85,
    agrupamento: str = "family",
    estrategia_particao: str = "group_kfold",
    lotes_base_comparavel: int | None = None,
    catalogo_variantes_path: str | Path | None = None,
) -> dict[str, Any]:
    catalogo = intents_registradas()
    dev = carregar_jsonl(dev_path, intents_permitidas=catalogo)
    caminhos_lotes = tuple(Path(caminho) for caminho in lotes_candidatos)
    candidatos = [
        item
        for caminho in caminhos_lotes
        for item in carregar_jsonl(caminho, intents_permitidas=catalogo)
    ]
    quantidade_lotes_base = (
        len(caminhos_lotes)
        if lotes_base_comparavel is None
        else int(lotes_base_comparavel)
    )
    if not 0 <= quantidade_lotes_base <= len(caminhos_lotes):
        raise ValueError("lotes_base_comparavel fora dos lotes candidatos")
    quantidade_base_comparavel = len(dev) + sum(
        len(carregar_jsonl(caminho, intents_permitidas=catalogo))
        for caminho in caminhos_lotes[:quantidade_lotes_base]
    )
    exemplos_ood = carregar_dataset_ood(ood_path) if ood_path else []
    manifesto = (
        carregar_manifesto_variantes(
            catalogo_variantes_path,
            intents_catalogadas=catalogo,
        )
        if catalogo_variantes_path
        else None
    )
    acoes_por_intent: dict[str, set[str]] = {}
    for variante in manifesto["variants"] if manifesto else []:
        acoes_por_intent.setdefault(variante["intent"], set()).add(
            variante["action"]
        )
    relatorio = validar_por_familias(
        [*dev, *candidatos],
        n_splits=n_splits,
        estrategia=estrategia,
        arquitetura_comando=arquitetura_comando,
        arquitetura_acao=arquitetura_acao,
        limiar_comando=limiar_comando,
        limiares_comando_por_intent=limiares_comando_por_intent,
        limiares_fallback_intent_semantica=(
            limiares_fallback_intent_semantica
        ),
        representacao=representacao,
        pasta_encoder_semantico=pasta_encoder_semantico,
        sha256_encoder_semantico=sha256_encoder_semantico,
        exemplos_ood=exemplos_ood,
        alvo_falso_aceite_ood=alvo_falso_aceite_ood,
        recall_id_minimo_ood=recall_id_minimo_ood,
        agrupamento=agrupamento,
        estrategia_particao=estrategia_particao,
        quantidade_base_comparavel=quantidade_base_comparavel,
        acoes_por_intent=acoes_por_intent,
    )
    relatorio["dataset"] = {
        "dev_canonico": len(dev),
        "exemplos_candidatos": len(candidatos),
        "lotes_candidatos": [caminho.name for caminho in caminhos_lotes],
        "ood_calibracao": len(exemplos_ood),
        "ood_path": Path(ood_path).name if ood_path else "",
    }
    caminho_destino = Path(destino)
    caminho_destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho_destino.with_suffix(caminho_destino.suffix + ".tmp")
    temporario.write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporario.replace(caminho_destino)
    return relatorio


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", default="mente_laylay/neural/datasets/dev_v0.jsonl")
    parser.add_argument("--lote-candidato", action="append", default=[])
    parser.add_argument("--splits", type=int, default=5)
    parser.add_argument(
        "--estrategia",
        choices=sorted(ESTRATEGIAS_PERMITIDAS),
        default="logistic",
    )
    parser.add_argument(
        "--arquitetura-comando",
        choices=sorted(ARQUITETURAS_COMANDO_PERMITIDAS),
        default="independent",
    )
    parser.add_argument(
        "--arquitetura-acao",
        choices=sorted(ARQUITETURAS_ACAO_PERMITIDAS),
        default="global",
    )
    parser.add_argument("--limiar-comando", type=float, default=0.5)
    parser.add_argument(
        "--limiar-comando-intent",
        action="append",
        default=[],
        metavar="INTENT=VALOR",
    )
    parser.add_argument(
        "--limiar-fallback-intent-semantica",
        action="append",
        default=[],
        metavar="INTENT=VALOR",
    )
    parser.add_argument(
        "--representacao",
        choices=sorted(REPRESENTACOES_PERMITIDAS),
        default="tfidf",
    )
    parser.add_argument(
        "--encoder-semantico",
        default="",
        help="pasta local do encoder ONNX experimental",
    )
    parser.add_argument(
        "--sha256-encoder-semantico",
        default="",
        help="SHA-256 opcional do arquivo ONNX",
    )
    parser.add_argument(
        "--ood-calibracao",
        default="",
        help="JSONL de comandos fora do catálogo; nunca entra no treino",
    )
    parser.add_argument("--ood-falso-aceite-maximo", type=float, default=0.01)
    parser.add_argument("--ood-recall-id-minimo", type=float, default=0.85)
    parser.add_argument(
        "--agrupamento",
        choices=sorted(AGRUPAMENTOS_PERMITIDOS),
        default="family",
    )
    parser.add_argument(
        "--estrategia-particao",
        choices=sorted(ESTRATEGIAS_PARTICAO_PERMITIDAS),
        default="group_kfold",
    )
    parser.add_argument(
        "--lotes-base-comparavel",
        type=int,
        default=None,
        help="quantos lotes iniciais formam a fatia histórica comparável",
    )
    parser.add_argument(
        "--destino",
        default="memoria/neural/validacao_cruzada_familias.json",
    )
    parser.add_argument(
        "--catalogo",
        default="mente_laylay/neural/datasets/catalogo_variantes_v0.json",
    )
    args = parser.parse_args()
    limiares_por_intent: dict[str, float] = {}
    for bruto in args.limiar_comando_intent:
        intent, separador, valor = str(bruto).partition("=")
        if not separador:
            parser.error("--limiar-comando-intent exige INTENT=VALOR")
        limiares_por_intent[intent.strip().upper()] = float(valor)
    limiares_fallback_semantico: dict[str, float] = {}
    for bruto in args.limiar_fallback_intent_semantica:
        intent, separador, valor = str(bruto).partition("=")
        if not separador:
            parser.error(
                "--limiar-fallback-intent-semantica exige INTENT=VALOR"
            )
        limiares_fallback_semantico[intent.strip().upper()] = float(valor)
    relatorio = gerar_relatorio_validacao_cruzada(
        dev_path=args.dev,
        destino=args.destino,
        lotes_candidatos=args.lote_candidato,
        n_splits=args.splits,
        estrategia=args.estrategia,
        arquitetura_comando=args.arquitetura_comando,
        arquitetura_acao=args.arquitetura_acao,
        limiar_comando=args.limiar_comando,
        limiares_comando_por_intent=limiares_por_intent,
        limiares_fallback_intent_semantica=limiares_fallback_semantico,
        representacao=args.representacao,
        pasta_encoder_semantico=args.encoder_semantico or None,
        sha256_encoder_semantico=args.sha256_encoder_semantico,
        ood_path=args.ood_calibracao or None,
        alvo_falso_aceite_ood=args.ood_falso_aceite_maximo,
        recall_id_minimo_ood=args.ood_recall_id_minimo,
        agrupamento=args.agrupamento,
        estrategia_particao=args.estrategia_particao,
        lotes_base_comparavel=args.lotes_base_comparavel,
        catalogo_variantes_path=args.catalogo,
    )
    print(json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
