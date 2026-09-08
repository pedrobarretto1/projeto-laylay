"""Ciclo controlado de treino, avaliação e promoção do especialista neural."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any, Iterable, Mapping

from mente_laylay.especialistas.capacidades import CAPACIDADES, intents_registradas
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito

from .avaliacao import avaliar_previsoes
from .cobertura import carregar_manifesto_variantes
from .dataset import carregar_jsonl, experiencias_para_dataset
from .experiencias import (
    BufferExperienciasNeurais,
    RegistroRevisoesCorrecoesNeurais,
)
from .modelo import (
    ARQUITETURAS_ACAO_PERMITIDAS,
    ARQUITETURAS_COMANDO_PERMITIDAS,
    ESTRATEGIAS_PERMITIDAS,
    REPRESENTACOES_PERMITIDAS,
    carregar_modelo,
    treinar_modelo,
)
from .promocao import avaliar_promocao
from .qualidade import auditar_leakage_dataset


def _hash(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _hash_dados(dados: Any) -> str:
    serializado = json.dumps(
        dados,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def _ler_json(caminho: Path) -> dict[str, Any]:
    if not caminho.exists():
        return {}
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return dict(dados) if isinstance(dados, dict) else {}


def _metricas(
    modelo: Any,
    frozen: list[dict[str, Any]],
    *,
    acoes_por_intent: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    return avaliar_previsoes(
        frozen,
        [modelo.prever(item["text"]) for item in frozen],
        acoes_por_intent=acoes_por_intent,
    )


def _metricas_modalidade_legada(frozen: list[dict[str, Any]]) -> dict[str, Any]:
    previsoes = []
    for item in frozen:
        turno = classificar_modalidade_turno(
            item["text"],
            normalizar_texto=lambda valor: str(valor or "").casefold().strip(),
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )
        previsoes.append(
            {
                "intent": "NONE",
                "is_command": bool(turno.get("autoriza_execucao")),
                "negated": str(turno.get("modalidade") or "") == "recusa",
            }
        )
    completas = avaliar_previsoes(frozen, previsoes)
    return {
        chave: completas[chave]
        for chave in (
            "command_precision",
            "command_recall",
            "false_command_count",
            "false_command_rate",
            "negation_accuracy",
            "missed_negation_count",
            "missed_negation_rate",
        )
    }


def _gravar_json_atomico(caminho: Path, dados: dict[str, Any]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporario.replace(caminho)


def executar_ciclo_treino(
    *,
    pasta_estado: str | Path,
    promover_se_aprovado: bool = False,
    versao: str | None = None,
    lotes_candidatos: Iterable[str | Path] = (),
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
) -> dict[str, Any]:
    pasta = Path(pasta_estado)
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
    limiares_intent_normalizados = {
        str(intent or "").strip().upper(): float(valor)
        for intent, valor in dict(limiares_comando_por_intent or {}).items()
    }
    limiares_fallback_normalizados = {
        str(intent or "").strip().upper(): float(valor)
        for intent, valor in dict(
            limiares_fallback_intent_semantica or {}
        ).items()
    }
    caminhos_lotes = tuple(Path(caminho) for caminho in lotes_candidatos)
    if caminhos_lotes and promover_se_aprovado:
        raise ValueError(
            "lote candidato não pode promover antes de ser aprovado e incorporado ao DEV"
        )
    if promover_se_aprovado and (
        estrategia_normalizada != "logistic"
        or arquitetura_comando_normalizada != "independent"
        or arquitetura_normalizada != "global"
        or float(limiar_comando) != 0.5
        or bool(limiares_intent_normalizados)
        or bool(limiares_fallback_normalizados)
        or representacao_normalizada != "tfidf"
    ):
        raise ValueError("configuração experimental não pode promover")
    datasets = Path(__file__).with_name("datasets")
    dev_path = datasets / "dev_v0.jsonl"
    frozen_path = datasets / "frozen_v0.jsonl"
    manifesto_path = datasets / "catalogo_variantes_v0.json"
    catalogo = intents_registradas()
    dev = carregar_jsonl(dev_path, intents_permitidas=catalogo)
    frozen = carregar_jsonl(frozen_path, intents_permitidas=catalogo)
    manifesto = carregar_manifesto_variantes(
        manifesto_path,
        intents_catalogadas=catalogo,
    )
    acoes_por_intent: dict[str, set[str]] = {}
    for variante in manifesto["variants"]:
        acoes_por_intent.setdefault(variante["intent"], set()).add(
            variante["action"]
        )
    candidatos = [
        item
        for caminho in caminhos_lotes
        for item in carregar_jsonl(caminho, intents_permitidas=catalogo)
    ]
    auditoria_lote = auditar_leakage_dataset([*dev, *candidatos], frozen)
    if not auditoria_lote["aprovado"]:
        raise ValueError("lote candidato reprovado por leakage com o challenge")
    buffer = BufferExperienciasNeurais(pasta / "experiencias.jsonl")
    revisoes = RegistroRevisoesCorrecoesNeurais(
        pasta / "revisoes_correcoes.jsonl"
    ).classificar(buffer.listar(apenas_aptas=True))
    dominios = {
        intent: str(registro.get("dominio") or "geral")
        for intent, registro in CAPACIDADES.items()
    }
    aprendidos = experiencias_para_dataset(
        revisoes["aprovadas"],
        intents_permitidas=catalogo,
        dominio_por_intent=dominios,
    )
    treino = [*dev, *candidatos, *aprendidos]
    identificador = versao or time.strftime("tfidf-%Y%m%d-%H%M%S")
    candidato_path = pasta / "modelo_candidato.joblib"
    ativo_path = pasta / "modelo_ativo.joblib"
    relatorio_path = pasta / "ultimo_relatorio_treino.json"
    relatorio_anterior = _ler_json(relatorio_path)
    dataset_anterior = dict(relatorio_anterior.get("dataset") or {})
    estrategia_anterior = str(
        relatorio_anterior.get("estrategia")
        or ("logistic" if ativo_path.exists() else "")
    ).strip().casefold()
    arquitetura_anterior = str(
        relatorio_anterior.get("arquitetura_acao")
        or ("global" if ativo_path.exists() else "")
    ).strip().casefold()
    arquitetura_comando_anterior = str(
        relatorio_anterior.get("arquitetura_comando")
        or ("independent" if ativo_path.exists() else "")
    ).strip().casefold()
    limiar_comando_anterior = float(
        relatorio_anterior.get("limiar_comando")
        if relatorio_anterior.get("limiar_comando") is not None
        else 0.5
    )
    limiares_intent_anteriores = {
        str(intent or "").strip().upper(): float(valor)
        for intent, valor in dict(
            relatorio_anterior.get("limiares_comando_por_intent") or {}
        ).items()
    }
    limiares_fallback_anteriores = {
        str(intent or "").strip().upper(): float(valor)
        for intent, valor in dict(
            relatorio_anterior.get(
                "limiares_fallback_intent_semantica"
            ) or {}
        ).items()
    }
    representacao_anterior = str(
        relatorio_anterior.get("representacao")
        or ("tfidf" if ativo_path.exists() else "")
    ).strip().casefold()
    dev_sha256 = _hash(dev_path)
    frozen_sha256 = _hash(frozen_path)
    aprendidos_sha256 = _hash_dados(aprendidos)
    lotes_candidatos_sha256 = _hash_dados(candidatos)
    evidencia_aprendizado = {
        "dados_aprendidos_novos": bool(
            aprendidos
            and aprendidos_sha256
            != str(dataset_anterior.get("aprendidos_sha256") or "")
        ),
        "dataset_base_alterado": bool(
            dataset_anterior.get("dev_sha256")
            and dev_sha256 != str(dataset_anterior.get("dev_sha256") or "")
        ),
        "lotes_candidatos_novos": bool(
            candidatos
            and lotes_candidatos_sha256
            != str(dataset_anterior.get("lotes_candidatos_sha256") or "")
        ),
        "estrategia_alterada": bool(
            estrategia_anterior
            and estrategia_normalizada != estrategia_anterior
        ),
        "arquitetura_acao_alterada": bool(
            arquitetura_anterior
            and arquitetura_normalizada != arquitetura_anterior
        ),
        "arquitetura_comando_alterada": bool(
            arquitetura_comando_anterior
            and arquitetura_comando_normalizada != arquitetura_comando_anterior
        ),
        "limiar_comando_alterado": bool(
            limiar_comando_anterior != float(limiar_comando)
        ),
        "limiares_comando_por_intent_alterados": bool(
            limiares_intent_anteriores != limiares_intent_normalizados
        ),
        "limiares_fallback_intent_semantica_alterados": bool(
            limiares_fallback_anteriores != limiares_fallback_normalizados
        ),
        "representacao_alterada": bool(
            representacao_anterior
            and representacao_normalizada != representacao_anterior
        ),
    }
    candidato = treinar_modelo(
        treino,
        caminho=candidato_path,
        versao=identificador,
        estrategia=estrategia_normalizada,
        arquitetura_comando=arquitetura_comando_normalizada,
        arquitetura_acao=arquitetura_normalizada,
        limiar_comando=limiar_comando,
        limiares_comando_por_intent=limiares_intent_normalizados,
        limiares_fallback_intent_semantica=limiares_fallback_normalizados,
        representacao=representacao_normalizada,
        encoder_semantico=encoder_semantico,
        pasta_encoder_semantico=pasta_encoder_semantico,
        sha256_encoder_semantico=sha256_encoder_semantico,
    )
    metricas_candidato = _metricas(
        candidato,
        frozen,
        acoes_por_intent=acoes_por_intent,
    )
    metricas_modalidade_legada = _metricas_modalidade_legada(frozen)
    metricas_estavel: dict[str, Any] = {}
    versao_estavel = ""
    if ativo_path.exists():
        try:
            estavel = carregar_modelo(ativo_path)
            metricas_estavel = _metricas(
                estavel,
                frozen,
                acoes_por_intent=acoes_por_intent,
            )
            versao_estavel = estavel.versao
        except Exception as erro:
            metricas_estavel = {"erro": type(erro).__name__}
    comparavel = metricas_estavel if not metricas_estavel.get("erro") else {}
    decisao = avaliar_promocao(
        comparavel,
        metricas_candidato,
        evidencia_aprendizado=evidencia_aprendizado,
    )
    promovido = bool(promover_se_aprovado and decisao.get("promover"))
    if promovido:
        pasta.mkdir(parents=True, exist_ok=True)
        if ativo_path.exists():
            shutil.copy2(ativo_path, pasta / "modelo_ativo.anterior.joblib")
        temporario = pasta / "modelo_ativo.joblib.tmp"
        shutil.copy2(candidato_path, temporario)
        temporario.replace(ativo_path)
    relatorio = {
        "versao_candidato": identificador,
        "versao_estavel": versao_estavel,
        "estrategia": estrategia_normalizada,
        "arquitetura_comando": arquitetura_comando_normalizada,
        "arquitetura_acao": arquitetura_normalizada,
        "limiar_comando": float(limiar_comando),
        "limiares_comando_por_intent": dict(
            sorted(limiares_intent_normalizados.items())
        ),
        "limiares_fallback_intent_semantica": dict(
            sorted(limiares_fallback_normalizados.items())
        ),
        "representacao": representacao_normalizada,
        "encoder_semantico_configurado": bool(
            encoder_semantico is not None or pasta_encoder_semantico is not None
        ),
        "encoder_semantico_sha256": str(sha256_encoder_semantico or ""),
        "configuracao_experimental": bool(
            estrategia_normalizada != "logistic"
            or arquitetura_comando_normalizada != "independent"
            or arquitetura_normalizada != "global"
            or float(limiar_comando) != 0.5
            or bool(limiares_intent_normalizados)
            or bool(limiares_fallback_normalizados)
            or representacao_normalizada != "tfidf"
        ),
        "dataset": {
            "dev_sha256": dev_sha256,
            "frozen_sha256": frozen_sha256,
            "aprendidos_sha256": aprendidos_sha256,
            "exemplos_base": len(dev),
            "correcoes_fortes": len(aprendidos),
            "correcoes_aprovadas": len(revisoes["aprovadas"]),
            "correcoes_rejeitadas": len(revisoes["rejeitadas"]),
            "correcoes_pendentes_revisao": len(revisoes["pendentes"]),
            "exemplos_candidatos": len(candidatos),
            "lotes_candidatos_sha256": lotes_candidatos_sha256,
            "total_treino": len(treino),
            "challenge": len(frozen),
        },
        "evidencia_aprendizado": evidencia_aprendizado,
        "metricas_candidato": metricas_candidato,
        "metricas_modalidade_legada": metricas_modalidade_legada,
        "metricas_estavel": metricas_estavel,
        "decisao": decisao,
        "promovido": promovido,
        "lote_candidato_apenas_avaliacao": bool(candidatos),
        "auditoria_lote": {
            "aprovado": bool(auditoria_lote["aprovado"]),
            "familias_compartilhadas": int(
                auditoria_lote["totais"]["familias_compartilhadas"]
            ),
            "pares_duplicados_exatos": int(
                auditoria_lote["totais"]["pares_duplicados_exatos"]
            ),
            "pares_quase_duplicados": int(
                auditoria_lote["totais"]["pares_quase_duplicados"]
            ),
        },
        "modo_operacional_apos_promocao": "shadow",
        "ts": time.time(),
    }
    _gravar_json_atomico(relatorio_path, relatorio)
    return relatorio


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--estado", default="memoria/neural")
    parser.add_argument("--versao", default="")
    parser.add_argument("--promover-se-aprovado", action="store_true")
    parser.add_argument("--lote-candidato", action="append", default=[])
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
    relatorio = executar_ciclo_treino(
        pasta_estado=args.estado,
        promover_se_aprovado=args.promover_se_aprovado,
        versao=args.versao or None,
        lotes_candidatos=args.lote_candidato,
        estrategia=args.estrategia,
        arquitetura_comando=args.arquitetura_comando,
        arquitetura_acao=args.arquitetura_acao,
        limiar_comando=args.limiar_comando,
        limiares_comando_por_intent=limiares_por_intent,
        limiares_fallback_intent_semantica=limiares_fallback_semantico,
        representacao=args.representacao,
        pasta_encoder_semantico=args.encoder_semantico or None,
        sha256_encoder_semantico=args.sha256_encoder_semantico,
    )
    print(json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if relatorio["decisao"].get("promover") else 2


if __name__ == "__main__":
    raise SystemExit(main())
