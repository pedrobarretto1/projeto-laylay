"""Cruza o caos LIST_WINDOWS com as previsões v26/v27 e o ledger shadow."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence
import sys

# Ferramenta histórica somente de análise; não treina nem promove modelos.
RAIZ = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(RAIZ))

from mente_laylay.integracao.roteiro_teste_conversa import (
    carregar_configuracao_roteiro,
)
from mente_laylay.integracao.avaliador_roteiro_teste import avaliar_turno_roteiro
from mente_laylay.neural.modelo import carregar_modelo
from mente_laylay.neural.auditoria_shadow import ler_jsonl_tolerante


ROTEIRO = RAIZ / "scripts" / "roteiros" / "roteiro_neural_v27_list_windows_caos.py"
PASTA_RESULTADOS = RAIZ / "resultados_testes"
CAMINHO_BASE = (
    RAIZ / "memoria" / "neural" / "experimentos"
    / "hibrido_v3_iot_v4_negacao_v5_cmd_v6_exp_v7_telegraphic_final_v8_v26"
    / "modelo_candidato.joblib"
)
CAMINHO_CANDIDATO = (
    RAIZ / "memoria" / "neural" / "experimentos"
    / "v27_list_windows_onda_v1"
    / "modelo_candidato_extensao_estado_estrutura_v4.joblib"
)
CAMINHO_ATIVO = RAIZ / "memoria" / "neural" / "modelo_ativo.joblib"
CAMINHO_EVENTOS = RAIZ / "memoria" / "neural" / "shadow_eventos.jsonl"
VERSAO_CANDIDATA = "hibrido_v26_ext_list_windows_estado_estrutura_v4_v27"
HASH_ATIVO_ESPERADO = (
    "07C539917EAE7792B2B4ECB1F0335697802FC7F6672E920656F8C5DFC2289E62"
)


def _sha256_arquivo(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest().upper()


def _hash_texto(texto: str) -> str:
    limpo = " ".join(str(texto or "").strip().split())[:500]
    return hashlib.sha256(limpo.casefold().encode("utf-8")).hexdigest()


def _resultado_mais_recente() -> Path:
    candidatos = sorted(
        PASTA_RESULTADOS.glob("roteiro_neural_v27_list_windows_caos-*"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if not candidatos:
        raise FileNotFoundError("nenhum resultado do caos v27 foi encontrado")
    return candidatos[0]


def _eventos_shadow(
    *, hashes: set[str], inicio: float, fim: float,
) -> tuple[list[dict], int]:
    eventos: list[dict] = []
    if not CAMINHO_EVENTOS.is_file():
        return eventos, 0
    registros, linhas_invalidas = ler_jsonl_tolerante(CAMINHO_EVENTOS)
    for item in registros:
        ts = float(item.get("ts") or 0.0)
        if (
            inicio - 5.0 <= ts <= fim + 5.0
            and item.get("modelo") == VERSAO_CANDIDATA
            and item.get("texto_hash") in hashes
        ):
            eventos.append(item)
    return eventos, linhas_invalidas


def _normalizar_comando(texto: object) -> str:
    return " ".join(str(texto or "").strip().split()).casefold()


def _carregar_planos_completos(
    caminho: Path,
    *,
    comandos: Sequence[str],
) -> tuple[dict[int, dict], dict]:
    planos: dict[int, dict] = {}
    registros_descartados = 0
    if caminho.is_file():
        registros, linhas_invalidas = ler_jsonl_tolerante(caminho)
    else:
        registros, linhas_invalidas = [], 0

    for registro in registros:
        try:
            indice = int(registro.get("indice"))
        except (TypeError, ValueError):
            registros_descartados += 1
            continue
        plano = registro.get("plano")
        comando = registro.get("comando")
        if (
            not 0 <= indice < len(comandos)
            or not isinstance(plano, Mapping)
            or _normalizar_comando(comando)
            != _normalizar_comando(comandos[indice])
        ):
            registros_descartados += 1
            continue
        # O ledger e append-only: uma repeticao posterior do turno representa
        # o snapshot final mais recente produzido pelo runtime.
        planos[indice] = dict(plano)

    faltantes = [
        indice + 1 for indice in range(len(comandos)) if indice not in planos
    ]
    return planos, {
        "linhas_invalidas": linhas_invalidas,
        "registros_descartados": registros_descartados,
        "turnos_com_plano_completo": len(planos),
        "turnos_sem_plano_completo": faltantes,
    }


def analisar() -> dict:
    configuracao = carregar_configuracao_roteiro(ROTEIRO)
    pasta = _resultado_mais_recente()
    checkpoint = json.loads(
        (pasta / "checkpoint.json").read_text(encoding="utf-8")
    )
    itens = list(checkpoint.get("itens") or [])
    if len(itens) != len(configuracao.comandos):
        raise AssertionError("checkpoint não cobre todos os comandos do roteiro")

    modelo_base = carregar_modelo(CAMINHO_BASE)
    modelo_candidato = carregar_modelo(CAMINHO_CANDIDATO)
    planos_completos, diagnostico_planos = _carregar_planos_completos(
        pasta / "planos.jsonl",
        comandos=configuracao.comandos,
    )
    matriz = []
    familias: dict[str, Counter] = defaultdict(Counter)
    totais = Counter()
    resultados_reavaliados = Counter()
    for indice, texto in enumerate(configuracao.comandos, 1):
        expectativa = dict(configuracao.expectativas_semanticas.get(indice) or {})
        item_runtime = dict(itens[indice - 1])
        reavaliado = avaliar_turno_roteiro(
            indice=indice - 1,
            comando=texto,
            resposta=str(item_runtime.get("resposta") or ""),
            plano=planos_completos.get(
                indice - 1,
                item_runtime.get("plano"),
            ),
            respondeu=str(item_runtime.get("status") or "") == "respondido",
            motivo_resultado=str(item_runtime.get("motivo_resultado") or ""),
            enviado_em=item_runtime.get("enviado_em"),
            finalizado_em=item_runtime.get("finalizado_em"),
            expectativa_local=expectativa,
        )
        resultados_reavaliados[str(
            reavaliado.get("resultado_semantico") or "desconhecido"
        )] += 1
        esperado_list_windows = "LIST_WINDOWS" in {
            str(valor).upper() for valor in expectativa.get("intents_any") or ()
        }
        base = modelo_base.prever(texto)
        candidato = modelo_candidato.prever(texto)
        base_list_windows = base.get("intent") == "LIST_WINDOWS"
        candidato_list_windows = candidato.get("intent") == "LIST_WINDOWS"
        familia = str(expectativa.get("nome") or "sem_familia")
        if esperado_list_windows and candidato_list_windows:
            classe = "tp"
        elif esperado_list_windows:
            classe = "fn"
        elif candidato_list_windows:
            classe = "fp"
        else:
            classe = "tn"
        totais[classe] += 1
        familias[familia][classe] += 1
        familias[familia]["total"] += 1
        matriz.append({
            "turno": indice,
            "texto": texto,
            "familia": familia,
            "esperado_list_windows": esperado_list_windows,
            "base_intent": str(base.get("intent") or ""),
            "candidato_intent": str(candidato.get("intent") or ""),
            "classe_candidato": classe,
            "extensao_aplicada": str(
                candidato.get("intent_extension_applied") or ""
            ),
            "probabilidade_extensao": round(float(
                candidato.get("intent_extension_probability") or 0.0
            ), 6),
            "is_command": bool(candidato.get("is_command")),
            "raw_is_command": bool(candidato.get("raw_is_command")),
            "negated": bool(candidato.get("negated")),
        })

    positivos = totais["tp"] + totais["fn"]
    propostas = totais["tp"] + totais["fp"]
    inicio = float(checkpoint.get("criado_em") or 0.0)
    fim = float(checkpoint.get("finalizado_em") or 0.0)
    eventos, linhas_invalidas_shadow = _eventos_shadow(
        hashes={_hash_texto(texto) for texto in configuracao.comandos},
        inicio=inicio,
        fim=fim,
    )
    resumo_runtime = json.loads(
        (pasta / "resumo.json").read_text(encoding="utf-8")
    )
    hash_ativo = _sha256_arquivo(CAMINHO_ATIVO)
    return {
        "status": (
            "analisado_com_artefatos_degradados"
            if (
                linhas_invalidas_shadow
                or diagnostico_planos["linhas_invalidas"]
                or diagnostico_planos["registros_descartados"]
                or diagnostico_planos["turnos_sem_plano_completo"]
            )
            else "analisado"
        ),
        "resultado": str(pasta.relative_to(RAIZ)),
        "runtime": {
            "total": int(resumo_runtime.get("total_turnos") or 0),
            "respondidos": int(resumo_runtime.get("respondidos") or 0),
            "passaram": int(resumo_runtime.get("passaram") or 0),
            "falharam": int(resumo_runtime.get("falharam") or 0),
            "taxa_semantica_percentual": float(
                resumo_runtime.get("taxa_semantica_percentual") or 0.0
            ),
            "reavaliado_contrato_atual": dict(resultados_reavaliados),
            "planos_completos": diagnostico_planos,
        },
        "candidata": {
            "tp": totais["tp"], "fn": totais["fn"],
            "fp": totais["fp"], "tn": totais["tn"],
            "precisao": round(totais["tp"] / propostas, 6) if propostas else 0.0,
            "recall": round(totais["tp"] / positivos, 6) if positivos else 0.0,
            "extensoes_aplicadas": sum(
                bool(item["extensao_aplicada"]) for item in matriz
            ),
        },
        "familias": {
            nome: dict(contagem)
            for nome, contagem in sorted(familias.items())
        },
        "erros_candidata": [
            item for item in matriz if item["classe_candidato"] in {"fn", "fp"}
        ],
        "shadow": {
            "eventos": len(eventos),
            "linhas_invalidas": linhas_invalidas_shadow,
            "ledger_integro": linhas_invalidas_shadow == 0,
            "tipos": dict(Counter(str(item.get("tipo") or "") for item in eventos)),
            "somente_observacao": all(
                item.get("somente_observacao") is True for item in eventos
            ),
            "zero_autorizacao": all(
                item.get("autoriza_execucao") is False for item in eventos
            ),
            "zero_auto_rotulo": all(
                item.get("predicao_propria_vira_label") is False for item in eventos
            ),
        },
        "modelo_ativo": {
            "hash": hash_ativo,
            "preservado": hash_ativo == HASH_ATIVO_ESPERADO,
        },
    }


if __name__ == "__main__":
    print(json.dumps(analisar(), ensure_ascii=False, indent=2))
