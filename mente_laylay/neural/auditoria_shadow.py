"""Auditoria fail-closed das evidências coletadas pelo especialista neural."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from .dataset import experiencias_para_dataset
from .experiencias import RegistroRevisoesCorrecoesNeurais


def _numero(valor: Any, padrao: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def _ler_jsonl(caminho: Path) -> tuple[list[dict[str, Any]], int]:
    if not caminho.exists():
        return [], 0
    registros: list[dict[str, Any]] = []
    invalidas = 0
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            item = json.loads(linha)
        except (TypeError, ValueError, json.JSONDecodeError):
            invalidas += 1
            continue
        if not isinstance(item, Mapping):
            invalidas += 1
            continue
        registros.append(dict(item))
    return registros, invalidas


def _percentil(valores: Iterable[float], proporcao: float) -> float:
    ordenados = sorted(
        numero for valor in valores if (numero := _numero(valor, -1.0)) >= 0.0
    )
    if not ordenados:
        return 0.0
    indice = round((len(ordenados) - 1) * proporcao)
    return round(ordenados[indice], 3)


def _chave_exemplo(item: Mapping[str, Any]) -> tuple[str, str]:
    texto = " ".join(str(item.get("text") or "").casefold().split())
    intent = str(item.get("intent_correta") or "").strip().upper()
    return texto, intent


def _metricas_modelo_esperado(
    eventos: Iterable[Mapping[str, Any]],
    *,
    intents_permitidas: Iterable[str],
) -> dict[str, Any]:
    """Recalcula métricas comparáveis sem confiar no resumo acumulado antigo."""
    permitidas = {
        str(intent).strip().upper()
        for intent in intents_permitidas
        if str(intent).strip()
    }
    metricas = {
        "turnos_segmentados": 0,
        "segmentos_comparaveis": 0,
        "concordancias_comando_segmento": 0,
        "divergencias_comando_segmento": 0,
        "falsos_comandos_neurais_segmento": 0,
        "comandos_perdidos_neurais_segmento": 0,
        "receipts_confirmados": 0,
        "receipts_nao_correlacionados": 0,
        "intents_fora_catalogo": 0,
        "intents_canonicas_ausentes": 0,
        "intents_comparaveis": 0,
        "concordancias_intent": 0,
        "divergencias_intent": 0,
        "acoes_canonicas_ausentes": 0,
        "acoes_comparaveis": 0,
        "concordancias_acao": 0,
        "divergencias_acao": 0,
    }
    for evento in eventos:
        tipo_evento = str(evento.get("tipo") or "")
        comparacao = evento.get("comparacao")
        if tipo_evento == "comparacao_turno" and isinstance(
            comparacao, Mapping
        ):
            segmentos_total = max(
                0, int(_numero(comparacao.get("segmentos_total"), 0.0))
            )
            if segmentos_total:
                metricas["turnos_segmentados"] += 1
            for chave in (
                "segmentos_comparaveis",
                "concordancias_comando_segmento",
                "divergencias_comando_segmento",
                "falsos_comandos_neurais_segmento",
                "comandos_perdidos_neurais_segmento",
            ):
                metricas[chave] += max(
                    0, int(_numero(comparacao.get(chave), 0.0))
                )
            continue
        if tipo_evento != "comparacao_receipt":
            continue
        canonico = evento.get("canonico")
        neural = evento.get("neural")
        if not isinstance(canonico, Mapping) or not isinstance(neural, Mapping):
            continue
        receipt_confirmado = bool(
            isinstance(comparacao, Mapping)
            and comparacao.get("receipt_confirmado") is True
        ) or bool(
            canonico.get("executou") is True
            and canonico.get("confirmado") is True
        )
        if not receipt_confirmado:
            continue
        metricas["receipts_confirmados"] += 1
        if (
            isinstance(comparacao, Mapping)
            and comparacao.get("intent_comparavel") is False
        ):
            metricas["receipts_nao_correlacionados"] += 1
            continue
        intent_canonica = str(canonico.get("intent") or "").strip().upper()
        intent_neural = str(neural.get("intent") or "").strip().upper()
        if not intent_canonica:
            metricas["intents_canonicas_ausentes"] += 1
            continue
        if intent_canonica not in permitidas:
            metricas["intents_fora_catalogo"] += 1
            continue

        metricas["intents_comparaveis"] += 1
        if intent_neural == intent_canonica:
            metricas["concordancias_intent"] += 1
        else:
            metricas["divergencias_intent"] += 1

        acao_canonica = str(canonico.get("acao") or "").strip().casefold()
        if not acao_canonica:
            metricas["acoes_canonicas_ausentes"] += 1
            continue
        acao_neural = str(neural.get("acao") or "").strip().casefold()
        metricas["acoes_comparaveis"] += 1
        if acao_neural == acao_canonica:
            metricas["concordancias_acao"] += 1
        else:
            metricas["divergencias_acao"] += 1

    intents_comparaveis = int(metricas["intents_comparaveis"])
    acoes_comparaveis = int(metricas["acoes_comparaveis"])
    metricas["taxa_concordancia_intent"] = round(
        metricas["concordancias_intent"] / intents_comparaveis, 6
    ) if intents_comparaveis else 0.0
    metricas["taxa_concordancia_acao"] = round(
        metricas["concordancias_acao"] / acoes_comparaveis, 6
    ) if acoes_comparaveis else 0.0
    return metricas


def auditar_evidencias_shadow(
    pasta_estado: str | Path,
    *,
    modelo_esperado: str,
    intents_permitidas: Iterable[str],
    intents_modelo: Iterable[str] | None = None,
    dominio_por_intent: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Resume evidências sem publicar texto, autorização ou rótulo automático."""
    pasta = Path(pasta_estado)
    eventos, eventos_invalidos = _ler_jsonl(pasta / "shadow_eventos.jsonl")
    experiencias, experiencias_invalidas = _ler_jsonl(pasta / "experiencias.jsonl")
    esperado = str(modelo_esperado or "").strip()
    permitidas = tuple(
        str(intent).strip().upper()
        for intent in intents_permitidas
        if str(intent).strip()
    )
    escopo_modelo = tuple(
        str(intent).strip().upper()
        for intent in (intents_modelo if intents_modelo is not None else permitidas)
        if str(intent).strip()
    )

    modelos = Counter(str(item.get("modelo") or "") for item in eventos)
    modelos.pop("", None)
    eventos_esperados = [
        item for item in eventos if str(item.get("modelo") or "") == esperado
    ]
    metricas_esperadas = _metricas_modelo_esperado(
        eventos_esperados,
        intents_permitidas=escopo_modelo,
    )
    latencias = []
    for item in eventos_esperados:
        neural = item.get("neural")
        if isinstance(neural, Mapping):
            try:
                latencias.append(float(neural.get("latency_ms") or 0.0))
            except (TypeError, ValueError):
                continue

    receipts_confirmados = sum(
        1
        for item in experiencias
        if item.get("tipo") == "resultado_comando"
        and item.get("executou") is True
        and item.get("confirmado") is True
        and item.get("evidencia") == "EXPECTED_RECEIPT_VERIFIED"
    )
    correcoes_fortes = sum(
        1
        for item in experiencias
        if item.get("tipo") == "correcao_interpretacao"
        and item.get("evidencia") == "EXPLICIT_CORRECTION"
        and item.get("apto_treino") is True
        and _numero(item.get("label_confidence"), -1.0) >= 1.0
    )

    experiencias_aptas: list[dict[str, Any]] = []
    chaves_aptas: set[tuple[str, str]] = set()
    aptos_total = 0
    correcoes_invalidas = 0
    for item in experiencias:
        try:
            convertidos = experiencias_para_dataset(
                [item],
                intents_permitidas=permitidas,
                dominio_por_intent=dominio_por_intent,
            )
        except (TypeError, ValueError):
            if item.get("tipo") == "correcao_interpretacao" and item.get("apto_treino") is True:
                correcoes_invalidas += 1
            continue
        if not convertidos:
            continue
        chave = _chave_exemplo(item)
        if chave in chaves_aptas:
            continue
        chaves_aptas.add(chave)
        aptos_total += 1
        experiencias_aptas.append(item)

    revisoes = RegistroRevisoesCorrecoesNeurais(
        pasta / "revisoes_correcoes.jsonl"
    ).classificar(experiencias_aptas)

    def _ids(itens: Iterable[Mapping[str, Any]]) -> list[str]:
        return [
            identificador[:100]
            for item in itens
            if (identificador := str(item.get("id") or "").strip())
        ]

    ids_aprovados = _ids(revisoes["aprovadas"])
    ids_rejeitados = _ids(revisoes["rejeitadas"])
    ids_pendentes = _ids(revisoes["pendentes"])

    modelo_observado = bool(esperado and eventos_esperados)
    if not modelo_observado:
        status = "aguardando_sessao_modelo_esperado"
    elif ids_pendentes:
        status = "correcoes_disponiveis_para_revisao"
    elif ids_aprovados:
        status = "correcoes_aprovadas_disponiveis_para_treino"
    elif ids_rejeitados:
        status = "sem_correcoes_pendentes_revisao"
    else:
        status = "sem_correcoes_explicitamente_confirmadas"

    timestamps = []
    for item in eventos:
        try:
            timestamps.append(float(item.get("ts") or 0.0))
        except (TypeError, ValueError):
            continue

    return {
        "versao": 1,
        "status": status,
        "modelo_esperado": esperado,
        "shadow": {
            "eventos_total": len(eventos),
            "linhas_invalidas": eventos_invalidos,
            "eventos_por_tipo": dict(sorted(Counter(
                str(item.get("tipo") or "desconhecido") for item in eventos
            ).items())),
            "eventos_por_modelo": dict(sorted(modelos.items())),
            "eventos_modelo_esperado": len(eventos_esperados),
            "modelo_esperado_observado": modelo_observado,
            "ultimo_evento_ts": max(timestamps, default=0.0),
            "metricas_modelo_esperado": metricas_esperadas,
            "latencia_modelo_esperado_ms": {
                "p50": _percentil(latencias, 0.50),
                "p95": _percentil(latencias, 0.95),
                "max": round(max(latencias, default=0.0), 3),
            },
        },
        "experiencias": {
            "registros_total": len(experiencias),
            "linhas_invalidas": experiencias_invalidas,
            "receipts_confirmados_revisaveis": receipts_confirmados,
            "correcoes_explicitamente_confirmadas": correcoes_fortes,
            "correcoes_aptas_invalidas": correcoes_invalidas,
            "exemplos_aptos_total": aptos_total,
            "ids_aptos_para_revisao": ids_pendentes,
            "exemplos_aprovados_treino": len(revisoes["aprovadas"]),
            "exemplos_rejeitados": len(revisoes["rejeitadas"]),
            "exemplos_pendentes_revisao": len(revisoes["pendentes"]),
            "ids_aprovados_treino": ids_aprovados,
            "ids_rejeitados": ids_rejeitados,
            "ids_pendentes_revisao": ids_pendentes,
        },
        "contrato": {
            "somente_auditoria": True,
            "incorporacao_automatica_no_dev": False,
            "incorporacao_automatica_no_treino": False,
            "receipt_isolado_vira_label": False,
            "divergencia_shadow_vira_label": False,
            "texto_publicado_no_relatorio": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pasta-estado", default="memoria/neural")
    parser.add_argument("--modelo-esperado", required=True)
    parser.add_argument(
        "--catalogo",
        default="mente_laylay/neural/datasets/catalogo_variantes_v0.json",
    )
    parser.add_argument("--saida")
    args = parser.parse_args()

    from mente_laylay.especialistas.capacidades import CAPACIDADES, intents_registradas
    from mente_laylay.neural.cobertura import carregar_manifesto_variantes

    intents_capacidades = intents_registradas()
    dominios = {
        intent: str(registro.get("dominio") or "geral")
        for intent, registro in CAPACIDADES.items()
    }
    manifesto = carregar_manifesto_variantes(
        args.catalogo,
        intents_catalogadas=intents_capacidades,
    )
    relatorio = auditar_evidencias_shadow(
        args.pasta_estado,
        modelo_esperado=args.modelo_esperado,
        intents_permitidas=intents_capacidades,
        intents_modelo={
            variante["intent"] for variante in manifesto["variants"]
        },
        dominio_por_intent=dominios,
    )
    serializado = json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.saida:
        destino = Path(args.saida)
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporario = destino.with_suffix(destino.suffix + ".tmp")
        temporario.write_text(serializado, encoding="utf-8")
        temporario.replace(destino)
    else:
        print(serializado, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
