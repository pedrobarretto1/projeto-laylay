"""Auditoria de cobertura do dataset neural por intenção e ação."""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from mente_laylay.especialistas.capacidades import intents_registradas

from .dataset import carregar_jsonl


RISCOS_VARIANTE_PERMITIDOS = frozenset(
    {"LOW_RISK", "REVERSIBLE", "DESTRUCTIVE", "CRITICAL"}
)

CHAVES_COTAS_QUALIDADE = (
    "minimum_linguistic_families_dev_per_variant",
    "minimum_negated_dev_per_variant",
    "minimum_hard_negatives_dev_per_domain",
)


def validar_catalogo_variantes(
    variantes: Iterable[Mapping[str, Any]],
    *,
    intents_catalogadas: Iterable[str],
) -> list[dict[str, Any]]:
    """Valida classes de dataset sem transformá-las em rotas operacionais."""
    intents = {
        str(intent or "").strip().upper()
        for intent in intents_catalogadas
        if str(intent or "").strip()
    }
    resultado: list[dict[str, Any]] = []
    vistos: set[str] = set()
    for indice, bruto in enumerate(variantes, 1):
        if not isinstance(bruto, Mapping):
            raise TypeError(f"variante {indice} deve ser um mapeamento")
        intent = str(bruto.get("intent") or "").strip().upper()
        action = str(bruto.get("action") or "").strip().casefold()
        domain = str(bruto.get("domain") or "").strip().casefold()
        risk = str(bruto.get("risk") or "").strip().upper()
        if intent not in intents:
            raise ValueError(f"intent não catalogada na variante {indice}: {intent or '<vazia>'}")
        if not action or action == "none":
            raise ValueError(f"action none não declara comando na variante {indice}")
        if not domain:
            raise ValueError(f"domain vazio na variante {indice}")
        if risk not in RISCOS_VARIANTE_PERMITIDOS:
            raise ValueError(f"risk inválido na variante {indice}: {risk or '<vazio>'}")
        if bruto.get("operational_influence_enabled") is not False:
            raise ValueError(
                "catálogo de dataset não pode habilitar influência operacional"
            )
        chave = f"{intent}:{action}"
        if chave in vistos:
            raise ValueError(f"variante duplicada: {chave}")
        vistos.add(chave)
        resultado.append({
            "intent": intent,
            "action": action,
            "domain": domain,
            "risk": risk,
            "operational_influence_enabled": False,
        })
    if not resultado:
        raise ValueError("catálogo de variantes vazio")
    return sorted(resultado, key=lambda item: (item["intent"], item["action"]))


def validar_manifesto_variantes(
    bruto: Mapping[str, Any],
    *,
    intents_catalogadas: Iterable[str],
) -> dict[str, Any]:
    """Valida metas de coleta sem transformar o catálogo em autoridade."""
    if not isinstance(bruto, Mapping):
        raise TypeError("manifesto de variantes deve ser um mapeamento")
    if bruto.get("operational_influence_enabled") is not False:
        raise ValueError("manifesto não pode habilitar influência operacional")
    if str(bruto.get("purpose") or "") != "dataset_coverage_only":
        raise ValueError("purpose do manifesto deve ser dataset_coverage_only")
    if int(bruto.get("schema_version") or 0) != 1:
        raise ValueError("schema_version do manifesto não suportada")

    faixa = bruto.get("target_dev_examples_per_variant")
    if not isinstance(faixa, Mapping):
        raise ValueError("manifesto precisa declarar target_dev_examples_per_variant")
    minima = faixa.get("minimum")
    maxima = faixa.get("maximum")
    if (
        isinstance(minima, bool)
        or isinstance(maxima, bool)
        or not isinstance(minima, int)
        or not isinstance(maxima, int)
        or minima <= 0
        or maxima < minima
    ):
        raise ValueError("faixa de exemplos DEV inválida no manifesto")

    cotas = bruto.get("quality_targets")
    if not isinstance(cotas, Mapping):
        raise ValueError("manifesto precisa declarar quality_targets")
    cotas_normalizadas: dict[str, int] = {}
    for chave in CHAVES_COTAS_QUALIDADE:
        valor = cotas.get(chave)
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise ValueError(f"cota de qualidade inválida: {chave}")
        cotas_normalizadas[chave] = valor

    variantes = bruto.get("variants")
    if not isinstance(variantes, list):
        raise ValueError("catálogo de variantes precisa de uma lista variants")
    return {
        "schema_version": 1,
        "purpose": "dataset_coverage_only",
        "operational_influence_enabled": False,
        "target_dev_examples_per_variant": {
            "minimum": minima,
            "maximum": maxima,
        },
        "quality_targets": cotas_normalizadas,
        "variants": validar_catalogo_variantes(
            variantes,
            intents_catalogadas=intents_catalogadas,
        ),
    }


def carregar_manifesto_variantes(
    caminho: str | Path,
    *,
    intents_catalogadas: Iterable[str],
) -> dict[str, Any]:
    try:
        bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as erro:
        raise ValueError(f"catálogo de variantes ilegível: {erro}") from erro
    return validar_manifesto_variantes(
        bruto,
        intents_catalogadas=intents_catalogadas,
    )


def carregar_catalogo_variantes(
    caminho: str | Path,
    *,
    intents_catalogadas: Iterable[str],
) -> list[dict[str, Any]]:
    return carregar_manifesto_variantes(
        caminho,
        intents_catalogadas=intents_catalogadas,
    )["variants"]


def _itens(exemplos: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(item) for item in exemplos]


def _chave_comando(item: Mapping[str, Any]) -> str:
    intent = str(item.get("intent") or "").strip().upper()
    acao = str(item.get("action") or "none").strip().casefold()
    return f"{intent}:{acao}"


def _status_meta(quantidade: int, minima: int, maxima: int) -> str:
    if quantidade < minima:
        return "abaixo_da_meta"
    if quantidade <= maxima:
        return "faixa_planejada"
    return "acima_da_faixa_planejada"


def analisar_cobertura_dataset(
    dev: Iterable[Mapping[str, Any]],
    frozen: Iterable[Mapping[str, Any]],
    *,
    intents_catalogadas: Iterable[str],
    comandos_planejados: Iterable[Mapping[str, Any]] = (),
    meta_minima_dev: int = 150,
    meta_maxima_dev: int = 200,
    meta_minima_familias_dev: int = 12,
    meta_minima_negados_dev: int = 15,
    meta_minima_hard_negatives_dev_por_dominio: int = 30,
) -> dict[str, Any]:
    """Mede cobertura sem confundir quantidade com qualidade ou autoridade."""
    minima = int(meta_minima_dev)
    maxima = int(meta_maxima_dev)
    if minima <= 0 or maxima < minima:
        raise ValueError("faixa de meta inválida")
    minima_familias = int(meta_minima_familias_dev)
    minima_negados = int(meta_minima_negados_dev)
    minima_hard_negatives = int(meta_minima_hard_negatives_dev_por_dominio)
    if minima_familias <= 0 or minima_negados <= 0 or minima_hard_negatives <= 0:
        raise ValueError("cotas mínimas de qualidade devem ser positivas")

    dev_itens = _itens(dev)
    frozen_itens = _itens(frozen)
    catalogo = sorted({
        str(intent or "").strip().upper()
        for intent in intents_catalogadas
        if str(intent or "").strip() and str(intent or "").strip().upper() != "NONE"
    })
    planejados_brutos = [dict(item) for item in comandos_planejados]
    planejados = validar_catalogo_variantes(
        planejados_brutos,
        intents_catalogadas=catalogo,
    ) if planejados_brutos else []
    metadados_planejados = {
        f"{item['intent']}:{item['action']}": dict(item) for item in planejados
    }
    todos = [("dev", item) for item in dev_itens] + [
        ("frozen", item) for item in frozen_itens
    ]

    contagem_intent: dict[str, Counter[str]] = defaultdict(Counter)
    familias_intent: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"dev": set(), "frozen": set()}
    )
    acoes_intent: dict[str, set[str]] = defaultdict(set)
    contagem_comando: dict[str, Counter[str]] = defaultdict(Counter)
    familias_comando: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"dev": set(), "frozen": set()}
    )
    fontes_comando: dict[str, dict[str, Counter[str]]] = defaultdict(
        lambda: {"dev": Counter(), "frozen": Counter()}
    )
    comandos_sem_acao: Counter[str] = Counter()
    hard_negatives_dominio: dict[str, Counter[str]] = defaultdict(Counter)

    for particao, item in todos:
        intent = str(item.get("intent") or "").strip().upper()
        familia = str(item.get("family") or "").strip().casefold()
        contagem_intent[intent][particao] += 1
        if familia:
            familias_intent[intent][particao].add(familia)
        if not bool(item.get("is_command")) or intent == "NONE":
            fonte = str(item.get("source") or "").strip().upper()
            dominio = str(item.get("domain") or "geral").strip().casefold()
            if fonte == "HARD_NEGATIVE" and dominio:
                hard_negatives_dominio[dominio][particao] += 1
            continue
        acao = str(item.get("action") or "none").strip().casefold()
        if acao == "none":
            comandos_sem_acao[particao] += 1
            continue
        chave = _chave_comando(item)
        acoes_intent[intent].add(acao)
        contagem_comando[chave][particao] += 1
        if bool(item.get("negated")):
            contagem_comando[chave][f"negados_{particao}"] += 1
        if familia:
            familias_comando[chave][particao].add(familia)
        fonte = str(item.get("source") or "").strip().upper()
        if fonte:
            fontes_comando[chave][particao][fonte] += 1

    intents_observadas = sorted(
        intent for intent in contagem_intent if intent and intent != "NONE"
    )
    todas_intents = sorted(set(catalogo) | set(intents_observadas))
    por_intent: dict[str, dict[str, Any]] = {}
    for intent in todas_intents:
        dev_total = int(contagem_intent[intent]["dev"])
        frozen_total = int(contagem_intent[intent]["frozen"])
        por_intent[intent] = {
            "dev": dev_total,
            "frozen": frozen_total,
            "total": dev_total + frozen_total,
            "familias_dev": len(familias_intent[intent]["dev"]),
            "familias_frozen": len(familias_intent[intent]["frozen"]),
            "acoes_observadas": sorted(acoes_intent[intent]),
            "catalogada": intent in catalogo,
        }

    por_comando: dict[str, dict[str, Any]] = {}
    chaves_observadas = set(contagem_comando)
    chaves_planejadas = set(metadados_planejados)
    for chave in sorted(chaves_observadas | chaves_planejadas):
        dev_total = int(contagem_comando[chave]["dev"])
        frozen_total = int(contagem_comando[chave]["frozen"])
        intent, acao = chave.split(":", 1)
        familias_dev = len(familias_comando[chave]["dev"])
        negados_dev = int(contagem_comando[chave]["negados_dev"])
        por_comando[chave] = {
            "intent": intent,
            "acao": acao,
            "dev": dev_total,
            "frozen": frozen_total,
            "total": dev_total + frozen_total,
            "negados_dev": negados_dev,
            "negados_frozen": int(contagem_comando[chave]["negados_frozen"]),
            "familias_dev": familias_dev,
            "familias_frozen": len(familias_comando[chave]["frozen"]),
            "fontes_dev": dict(sorted(fontes_comando[chave]["dev"].items())),
            "fontes_frozen": dict(
                sorted(fontes_comando[chave]["frozen"].items())
            ),
            "faltam_para_meta_dev": max(0, minima - dev_total),
            "faltam_familias_dev": max(0, minima_familias - familias_dev),
            "faltam_negados_dev": max(0, minima_negados - negados_dev),
            "status_meta_dev": _status_meta(dev_total, minima, maxima),
            "cotas_coleta_atendidas": (
                dev_total >= minima
                and familias_dev >= minima_familias
                and negados_dev >= minima_negados
            ),
            "declarada": chave in chaves_planejadas,
            "domain": str(
                metadados_planejados.get(chave, {}).get("domain") or ""
            ),
            "risk": str(metadados_planejados.get(chave, {}).get("risk") or ""),
            "operational_influence_enabled": False,
        }

    intents_sem_exemplos = [
        intent
        for intent in catalogo
        if not int(contagem_intent[intent]["dev"])
        and not int(contagem_intent[intent]["frozen"])
    ]
    comandos_abaixo_meta = [
        chave
        for chave, dados in por_comando.items()
        if dados["status_meta_dev"] == "abaixo_da_meta"
    ]
    todos_comandos_na_meta = bool(por_comando and not comandos_abaixo_meta)
    todos_comandos_com_cotas = bool(
        por_comando
        and all(dados["cotas_coleta_atendidas"] for dados in por_comando.values())
    )
    cobertura_catalogo_completa = not intents_sem_exemplos
    comandos_observados_nao_declarados = (
        sorted(chaves_observadas - chaves_planejadas) if planejados else []
    )
    comandos_planejados_sem_exemplos = sorted(
        chave
        for chave in chaves_planejadas
        if not int(contagem_comando[chave]["dev"])
        and not int(contagem_comando[chave]["frozen"])
    )
    dominios_planejados = {
        str(item.get("domain") or "").strip().casefold()
        for item in planejados
        if str(item.get("domain") or "").strip()
    }
    dominios_observados = set(hard_negatives_dominio)
    por_dominio: dict[str, dict[str, Any]] = {}
    for dominio in sorted(dominios_planejados | dominios_observados):
        dev_total = int(hard_negatives_dominio[dominio]["dev"])
        frozen_total = int(hard_negatives_dominio[dominio]["frozen"])
        cota_aplicavel = dominio in dominios_planejados
        por_dominio[dominio] = {
            "hard_negatives_dev": dev_total,
            "hard_negatives_frozen": frozen_total,
            "cota_aplicavel": cota_aplicavel,
            "faltam_hard_negatives_dev": (
                max(0, minima_hard_negatives - dev_total)
                if cota_aplicavel
                else 0
            ),
            "cota_hard_negatives_dev_atendida": (
                dev_total >= minima_hard_negatives if cota_aplicavel else None
            ),
        }
    todos_dominios_com_hard_negatives = bool(
        dominios_planejados
        and all(
            por_dominio[dominio]["cota_hard_negatives_dev_atendida"]
            for dominio in dominios_planejados
        )
    )
    return {
        "versao": 1,
        "gerado_em": time.time(),
        "meta": {
            "unidade": "exemplos_dev_por_intent_e_acao",
            "minima": minima,
            "maxima": maxima,
            "frozen_nao_conta_para_meta_dev": True,
            "minima_familias_dev_por_variante": minima_familias,
            "minima_negados_dev_por_variante": minima_negados,
            "minima_hard_negatives_dev_por_dominio": minima_hard_negatives,
        },
        "totais": {
            "dev": len(dev_itens),
            "frozen": len(frozen_itens),
            "total": len(dev_itens) + len(frozen_itens),
            "intents_catalogadas": len(catalogo),
            "intents_com_exemplos": len(set(catalogo) - set(intents_sem_exemplos)),
            "variantes_comando_observadas": len(chaves_observadas),
            "variantes_comando_declaradas": len(chaves_planejadas),
        },
        "por_intent": por_intent,
        "por_comando": por_comando,
        "por_dominio": por_dominio,
        "intents_sem_exemplos": intents_sem_exemplos,
        "comandos_abaixo_meta_dev": comandos_abaixo_meta,
        "comandos_observados_nao_declarados": comandos_observados_nao_declarados,
        "comandos_planejados_sem_exemplos": comandos_planejados_sem_exemplos,
        "nao_comandos": {
            "dev": int(contagem_intent["NONE"]["dev"]),
            "frozen": int(contagem_intent["NONE"]["frozen"]),
        },
        "comandos_sem_acao": {
            "dev": int(comandos_sem_acao["dev"]),
            "frozen": int(comandos_sem_acao["frozen"]),
        },
        "cobertura_catalogo_completa": cobertura_catalogo_completa,
        "todos_comandos_observados_na_meta_dev": todos_comandos_na_meta,
        "todos_comandos_com_cotas_minimas_dev": todos_comandos_com_cotas,
        "todos_dominios_com_hard_negatives_minimos_dev": (
            todos_dominios_com_hard_negatives
        ),
        "pronto_para_ampliar_influencia": False,
        "contrato": {
            "somente_diagnostico": True,
            "autoriza_execucao": False,
            "cobertura_nao_prova_qualidade": True,
            "cotas_nao_provam_qualidade": True,
            "challenge_nao_vira_treino": True,
        },
    }


def gerar_relatorio_cobertura(
    *,
    dev_path: str | Path,
    frozen_path: str | Path,
    destino: str | Path,
    catalogo_variantes_path: str | Path | None = None,
    meta_minima_dev: int | None = None,
    meta_maxima_dev: int | None = None,
    meta_minima_familias_dev: int | None = None,
    meta_minima_negados_dev: int | None = None,
    meta_minima_hard_negatives_dev_por_dominio: int | None = None,
) -> dict[str, Any]:
    catalogo = intents_registradas()
    dev = carregar_jsonl(dev_path, intents_permitidas=catalogo)
    frozen = carregar_jsonl(frozen_path, intents_permitidas=catalogo)
    manifesto = (
        carregar_manifesto_variantes(
            catalogo_variantes_path,
            intents_catalogadas=catalogo,
        )
        if catalogo_variantes_path
        else None
    )
    variantes = manifesto["variants"] if manifesto else []
    faixa = manifesto["target_dev_examples_per_variant"] if manifesto else {}
    cotas = manifesto["quality_targets"] if manifesto else {}
    relatorio = analisar_cobertura_dataset(
        dev,
        frozen,
        intents_catalogadas=catalogo,
        comandos_planejados=variantes,
        meta_minima_dev=(
            meta_minima_dev if meta_minima_dev is not None else faixa.get("minimum", 150)
        ),
        meta_maxima_dev=(
            meta_maxima_dev if meta_maxima_dev is not None else faixa.get("maximum", 200)
        ),
        meta_minima_familias_dev=(
            meta_minima_familias_dev
            if meta_minima_familias_dev is not None
            else cotas.get("minimum_linguistic_families_dev_per_variant", 12)
        ),
        meta_minima_negados_dev=(
            meta_minima_negados_dev
            if meta_minima_negados_dev is not None
            else cotas.get("minimum_negated_dev_per_variant", 15)
        ),
        meta_minima_hard_negatives_dev_por_dominio=(
            meta_minima_hard_negatives_dev_por_dominio
            if meta_minima_hard_negatives_dev_por_dominio is not None
            else cotas.get("minimum_hard_negatives_dev_per_domain", 30)
        ),
    )
    caminho = Path(destino)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporario.replace(caminho)
    return relatorio


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", default="mente_laylay/neural/datasets/dev_v0.jsonl")
    parser.add_argument(
        "--frozen", default="mente_laylay/neural/datasets/frozen_v0.jsonl"
    )
    parser.add_argument(
        "--destino", default="memoria/neural/cobertura_dataset.json"
    )
    parser.add_argument(
        "--catalogo",
        default="mente_laylay/neural/datasets/catalogo_variantes_v0.json",
    )
    parser.add_argument("--meta-minima-dev", type=int)
    parser.add_argument("--meta-maxima-dev", type=int)
    parser.add_argument("--meta-minima-familias-dev", type=int)
    parser.add_argument("--meta-minima-negados-dev", type=int)
    parser.add_argument("--meta-minima-hard-negatives-dev-por-dominio", type=int)
    args = parser.parse_args()
    relatorio = gerar_relatorio_cobertura(
        dev_path=args.dev,
        frozen_path=args.frozen,
        destino=args.destino,
        catalogo_variantes_path=args.catalogo,
        meta_minima_dev=args.meta_minima_dev,
        meta_maxima_dev=args.meta_maxima_dev,
        meta_minima_familias_dev=args.meta_minima_familias_dev,
        meta_minima_negados_dev=args.meta_minima_negados_dev,
        meta_minima_hard_negatives_dev_por_dominio=(
            args.meta_minima_hard_negatives_dev_por_dominio
        ),
    )
    print(json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
