"""Validação agrupada e somente-leitura para extensões aditivas de intent."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import unicodedata
from typing import Any, Iterable, Mapping

import sklearn
from sklearn.model_selection import GroupKFold

from .dataset import carregar_jsonl
from .modelo import (
    ModeloNeuralComandos, adicionar_extensao_intent,
    adicionar_extensao_intent_fatorada, carregar_modelo,
)


def _rotulo_extensao(
    item: Mapping[str, Any],
    *,
    intent: str,
    action: str,
    escopo: str,
) -> bool:
    intent_item = str(item.get("intent") or "NONE").strip().upper()
    action_item = str(item.get("action") or "none").strip().casefold()
    escopo_item = str(item.get("extension_scope") or "").strip().casefold()
    if intent_item == intent and action_item == "none":
        raise ValueError("exemplo da intent alvo exige action explícita")
    return bool(
        intent_item == intent
        and action_item == action
        and (not escopo or escopo_item == escopo)
    )


def _matriz(
    esperados: Iterable[bool],
    probabilidades: Iterable[float],
    *,
    limiar: float,
) -> dict[str, int | float]:
    tp = fn = fp = tn = 0
    for esperado, probabilidade in zip(
        esperados,
        probabilidades,
        strict=True,
    ):
        previsto = float(probabilidade) >= limiar
        tp += int(esperado and previsto)
        fn += int(esperado and not previsto)
        fp += int(not esperado and previsto)
        tn += int(not esperado and not previsto)
    propostas = tp + fp
    positivos = tp + fn
    return {
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "precisao": round(tp / propostas, 6) if propostas else 0.0,
        "recall": round(tp / positivos, 6) if positivos else 0.0,
    }


def validar_extensao_por_grupos(
    modelo_base: ModeloNeuralComandos,
    exemplos: Iterable[Mapping[str, Any]],
    *,
    intent: str,
    action: str,
    escopo: str = "",
    representacao: str = "tfidf",
    agrupamento: str = "validation_group",
    n_splits: int = 5,
    limiares: Iterable[float] = (0.5, 0.7, 0.8, 0.9, 0.925),
    representacoes_fatores: Mapping[str, str] | None = None,
    exemplos_complementares: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Mede uma extensão sem vazamento de grupos e sem persistir candidato."""
    itens = [dict(item) for item in exemplos]
    if not itens:
        raise ValueError("validação de extensão exige exemplos")
    limiares_validados = sorted({float(valor) for valor in limiares})
    if not limiares_validados or any(
        not math.isfinite(valor) or not 0.5 <= valor <= 1.0
        for valor in limiares_validados
    ):
        raise ValueError("limiares precisam ser não vazios e estar em [0.5, 1.0]")
    intent_alvo = str(intent or "").strip().upper()
    action_alvo = str(action or "").strip().casefold()
    escopo_alvo = str(escopo or "").strip().casefold()
    if not intent_alvo or intent_alvo == "NONE":
        raise ValueError("validação exige intent operacional")
    if not action_alvo or action_alvo == "none":
        raise ValueError("validação exige action operacional")
    grupos = [str(item.get(agrupamento) or "").strip() for item in itens]
    if any(not grupo for grupo in grupos):
        raise ValueError(f"exemplo sem agrupamento {agrupamento}")
    grupos_unicos = set(grupos)
    quantidade_splits = int(n_splits)
    if not 2 <= quantidade_splits <= len(grupos_unicos):
        raise ValueError("n_splits incompatível com os grupos disponíveis")

    esperados = [
        _rotulo_extensao(
            item,
            intent=intent_alvo,
            action=action_alvo,
            escopo=escopo_alvo,
        )
        for item in itens
    ]
    if len(set(esperados)) < 2:
        raise ValueError("validação exige positivos e negativos")
    fatores = dict(representacoes_fatores or {})
    if representacoes_fatores is not None and not fatores:
        raise ValueError("representacoes_fatores não pode ser vazio")
    esperados_fatores: dict[str, list[bool]] = {nome: [] for nome in fatores}
    for indice, item in enumerate(itens):
        rotulos = item.get("extension_factors")
        for nome in fatores:
            if not isinstance(rotulos, Mapping) or not isinstance(rotulos.get(nome), bool):
                raise ValueError(f"exemplo {indice} sem fator booleano {nome}")
            esperados_fatores[nome].append(rotulos[nome])
        if fatores and all(rotulos[nome] for nome in fatores) != esperados[indice]:
            raise ValueError(f"exemplo {indice}: conjunção dos fatores diverge do rótulo final")
    complementares = [dict(item) for item in exemplos_complementares]

    def chave_texto(texto: object) -> str:
        normalizado = unicodedata.normalize("NFKD", str(texto or "").casefold())
        return " ".join("".join(
            ch for ch in normalizado if not unicodedata.combining(ch)
        ).split())

    textos_vistos = {chave_texto(item.get("text")) for item in itens}
    for indice, item in enumerate(complementares):
        texto = chave_texto(item.get("text"))
        if not texto or texto in textos_vistos:
            raise ValueError(f"complemento {indice}: texto vazio ou duplicado")
        textos_vistos.add(texto)
        if not str(item.get(agrupamento) or "").strip():
            raise ValueError(f"complemento {indice}: sem agrupamento {agrupamento}")
        rotulos = item.get("extension_factors")
        for nome in fatores:
            if not isinstance(rotulos, Mapping) or not isinstance(rotulos.get(nome), bool):
                raise ValueError(f"complemento {indice}: sem fator booleano {nome}")
        if fatores and all(rotulos[nome] for nome in fatores) != _rotulo_extensao(
            item,
            intent=intent_alvo,
            action=action_alvo,
            escopo=escopo_alvo,
        ):
            raise ValueError(f"complemento {indice}: conjunção diverge do rótulo final")
    probabilidades: list[float | None] = [None] * len(itens)
    evidencias_fatores: list[dict[str, float]] = [{} for _ in itens]
    folds_por_indice: list[int] = [0] * len(itens)
    folds: list[dict[str, Any]] = []
    indices = list(range(len(itens)))
    divisor = GroupKFold(n_splits=quantidade_splits)
    for numero, (indices_treino, indices_validacao) in enumerate(
        divisor.split(indices, groups=grupos),
        1,
    ):
        treino = [itens[int(indice)] for indice in indices_treino]
        validacao_grupos = {grupos[int(indice)] for indice in indices_validacao}
        complemento_treino = [
            item for item in complementares
            if str(item[agrupamento]).strip() not in validacao_grupos
        ]
        treino.extend(complemento_treino)
        if fatores:
            candidato = adicionar_extensao_intent_fatorada(
                modelo_base, treino, intent=intent_alvo, action=action,
                limiar=0.5, representacoes_fatores=fatores,
                versao=f"validacao-extensao-fold-{numero}",
            )
        else:
            candidato = adicionar_extensao_intent(
                modelo_base, treino, intent=intent_alvo, action=action,
                limiar=0.5, escopo=escopo_alvo, representacao=representacao,
                versao=f"validacao-extensao-fold-{numero}",
            )
        extensoes_alvo = [
            extensao
            for extensao in candidato.extensoes_intent.values()
            if extensao.intent == intent_alvo
            and extensao.action == action_alvo
        ]
        if len(extensoes_alvo) != 1:
            raise RuntimeError(
                "candidato não contém extensão intent/action única"
            )
        extensao = extensoes_alvo[0]
        for indice in indices_validacao:
            item = itens[int(indice)]
            probabilidade, evidencias = extensao.avaliar(
                str(item.get("text") or "")
            )
            if any(
                not math.isfinite(p) or not 0.0 <= p <= 1.0
                for p in (probabilidade, *evidencias.values())
            ):
                raise ValueError(f"probabilidade inválida no fold {numero}")
            probabilidades[int(indice)] = probabilidade
            evidencias_fatores[int(indice)] = evidencias
            folds_por_indice[int(indice)] = numero
        treino_grupos = {str(item[agrupamento]).strip() for item in treino}
        validacao_grupos = {
            grupos[int(indice)] for indice in indices_validacao
        }
        compartilhados = sorted(treino_grupos & validacao_grupos)
        if compartilhados:
            raise RuntimeError("validação compartilhou grupos entre folds")
        folds.append({
            "fold": numero,
            "exemplos_treino": len(treino),
            "complementares_treino": len(complemento_treino),
            "complementares_excluidos": len(complementares) - len(complemento_treino),
            "exemplos_validacao": len(indices_validacao),
            "grupos_treino": len(treino_grupos),
            "grupos_validacao": len(validacao_grupos),
            "grupos_compartilhados": compartilhados,
        })

    if any(valor is None for valor in probabilidades):
        raise RuntimeError("existem exemplos sem previsão out-of-fold")
    probabilidades_finais = [float(valor) for valor in probabilidades if valor is not None]
    return {
        "versao": 1,
        "intent": intent_alvo,
        "action": action_alvo,
        "escopo": escopo_alvo,
        "representacao": "fatorada" if fatores else str(representacao or "").strip().casefold(),
        "representacoes_fatores": fatores,
        "agrupamento": agrupamento,
        "total": len(itens),
        "total_complementares": len(complementares),
        "positivos": sum(esperados),
        "negativos": len(itens) - sum(esperados),
        "folds": folds,
        "limiares": {
            f"{limiar:g}": _matriz(
                esperados,
                probabilidades_finais,
                limiar=limiar,
            )
            for limiar in limiares_validados
        },
        "fatores": {
            nome: {
                "positivos": sum(rotulos),
                "negativos": len(itens) - sum(rotulos),
                "limiares": {
                    f"{limiar:g}": _matriz(
                        rotulos, [linha[nome] for linha in evidencias_fatores],
                        limiar=limiar,
                    ) for limiar in limiares_validados
                },
            } for nome, rotulos in esperados_fatores.items()
        },
        "previsoes_oof": [
            {
                "indice": indice,
                "fold": folds_por_indice[indice],
                "grupo": grupos[indice],
                "familia": item.get("family", ""),
                "escopo_exemplo": item.get("extension_scope", ""),
                "texto_sha256": hashlib.sha256(item["text"].encode("utf-8")).hexdigest(),
                "esperado": esperados[indice],
                "probabilidade": probabilidades_finais[indice],
                "fatores": evidencias_fatores[indice],
                "fatores_esperados": {
                    nome: valores[indice] for nome, valores in esperados_fatores.items()
                },
            } for indice, item in enumerate(itens)
        ],
        "contrato": {
            "predicao_vira_label": False,
            "grupos_inteiros_por_fold": True,
            "nao_promove_modelo": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo-base", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--complemento", type=Path)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--escopo", default="")
    parser.add_argument("--representacao", default="tfidf")
    parser.add_argument("--fator", action="append", default=[], metavar="NOME=REPRESENTACAO")
    parser.add_argument("--agrupamento", action="append", choices=(
        "validation_group", "validation_entity_group",
    ))
    parser.add_argument("--splits", type=int, default=5)
    parser.add_argument("--limiares", nargs="+", type=float, default=[0.5, 0.7, 0.8, 0.9, 0.925])
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    if args.saida.exists():
        parser.error("saída já existe; escolha outro caminho para preservar o relatório")
    fatores: dict[str, str] = {}
    for declaracao in args.fator:
        nome, separador, representacao = declaracao.partition("=")
        if not separador or not nome or not representacao or nome in fatores:
            parser.error("fator exige NOME=REPRESENTACAO único")
        fatores[nome] = representacao

    caminhos = {
        "modelo_base": args.modelo_base, "dataset": args.dataset,
        "validador": Path(__file__),
        "codigo_modelo": Path(__file__).with_name("modelo.py"),
        "codigo_dataset": Path(__file__).with_name("dataset.py"),
    }
    if args.complemento is not None:
        caminhos["complemento"] = args.complemento
    def hashes() -> dict[str, str]:
        return {nome: hashlib.sha256(path.read_bytes()).hexdigest() for nome, path in caminhos.items()}

    antes = hashes()
    modelo = carregar_modelo(args.modelo_base)
    exemplos = carregar_jsonl(args.dataset, intents_permitidas={args.intent})
    complementares = (
        carregar_jsonl(args.complemento, intents_permitidas={args.intent})
        if args.complemento is not None else []
    )
    relatorios = {
        eixo: validar_extensao_por_grupos(
            modelo, exemplos, intent=args.intent, action=args.action,
            escopo=args.escopo, representacao=args.representacao,
            representacoes_fatores=fatores or None, agrupamento=eixo,
            n_splits=args.splits, limiares=args.limiares,
            exemplos_complementares=complementares,
        ) for eixo in (args.agrupamento or ["validation_group", "validation_entity_group"])
    }
    if hashes() != antes:
        raise RuntimeError("insumos mudaram durante a validação; relatório descartado")
    resultado = {
        "status": "diagnostico_sem_promocao", "modelo_versao": modelo.versao,
        "python": platform.python_version(), "sklearn": sklearn.__version__,
        "caminhos": {nome: str(path.resolve()) for nome, path in caminhos.items()},
        "sha256": antes, "insumos_preservados": True, "eixos": relatorios,
        "limitacoes": [
            "cada eixo isola somente o agrupamento declarado",
            "varredura diagnóstica; escolher limiar requer validação independente",
            "fatia histórica e runtime real não são avaliados por este relatório",
            "mínimo dos escores dos fatores não é uma probabilidade conjunta calibrada",
            "complemento participa só do treino, excluindo o grupo retido no eixo avaliado",
        ],
    }
    serializado = json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as destino:
        destino.write(serializado + "\n")
    print(json.dumps({
        "status": resultado["status"], "saida": str(args.saida),
        "eixos": {nome: relatorio["limiares"] for nome, relatorio in relatorios.items()},
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
