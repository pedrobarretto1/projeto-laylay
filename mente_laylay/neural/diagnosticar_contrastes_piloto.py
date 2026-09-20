"""Diagnóstico de desenvolvimento dos modelos salvos; sem fit ou execução.

O modelo atual prevê intenção/ação/comando/negação por texto, não os nove
atos por ocorrência do piloto. Não converter ausência de comando em relato
nem confundir uma proposta neural com autorização do runtime completo.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import platform
import time

from mente_laylay.especialistas.capacidades import intents_registradas
from .contratos import normalizar_previsao_neural
from .modelo import carregar_modelo
from .protocolo_ajuste_supervisionado import auditar_corpus
from .runtime import EspecialistaNeuralComandosRuntime
from .supervisao_relacoes_v4 import FLAGS


def avaliar(casos: list[dict], modelo: object) -> dict:
    """Entrada da inferência: somente texto. Gold é consultado após a previsão."""
    auditar_corpus(casos)
    if any(c["particao"] != "desenvolvimento" for c in casos):
        raise ValueError("diagnóstico aceita somente desenvolvimento conhecido")
    if any(c["fonte_v4"] and len(c["fonte_v4"]["nos"]) != 1 for c in casos):
        raise ValueError("modelo por texto não mede múltiplas ocorrências")
    fatias = defaultdict(lambda: {"casos": 0, "intent_correta": 0,
                                 "acao_bruta_correta": 0, "pedidos_propostos": 0,
                                 "pedidos_corretos": 0, "pedidos_indevidos": 0,
                                 "pedidos_perdidos": 0})
    registros = []
    for c in casos:
        inicio = time.perf_counter()
        bruto = modelo.prever(c["texto"])
        normalizado = normalizar_previsao_neural(
            bruto, texto=c["texto"], modelo=str(getattr(modelo, "versao", "desconhecido")),
            intents_permitidas=intents_registradas(), agora=0,
        )
        # Mesmo predicado que o especialista usa para priorizar propostas.
        # O nome do helper não significa que houve autorização ou execução.
        proposta = EspecialistaNeuralComandosRuntime._comando_executavel(normalizado)
        registro = {"id": c["id"], "texto": c["texto"], "bruto": bruto,
                    "normalizado": normalizado, "proposta_apos_gates": proposta,
                    "latencia_ms": (time.perf_counter() - inicio) * 1000,
                    "gold": None, "medicao": None}
        if c["enquadramento"] == "supervisionado":
            n = c["fonte_v4"]["nos"][0]
            chave = f"{n['intent']}|{n['action']}|{n['ato']}"
            pedido = n["ato"] == "pedido"
            intent_ok = bruto.get("intent") == n["intent"]
            acao_ok = bruto.get("raw_action") == n["action"]
            variante_proposta_ok = (normalizado["intent"] == n["intent"]
                                   and normalizado["params"].get("acao") == n["action"])
            medicao = {"intent_correta": intent_ok, "acao_bruta_correta": acao_ok,
                       "pedidos_propostos": proposta,
                       "pedidos_corretos": pedido and proposta and variante_proposta_ok,
                       "pedidos_indevidos": not pedido and proposta,
                       "pedidos_perdidos": pedido and not (proposta and variante_proposta_ok)}
            fatias[chave]["casos"] += 1
            for k, v in medicao.items():
                fatias[chave][k] += int(v)
            registro.update(gold={"intent": n["intent"], "action": n["action"], "ato": n["ato"]},
                            medicao=medicao)
        else:
            registro["motivo_fora_perfil"] = c["motivo_fora_perfil"]
        registros.append(registro)
    return {"modelo_versao": str(getattr(modelo, "versao", "desconhecido")),
            "representacao": str(getattr(modelo, "representacao", "desconhecida")),
            "fatias": dict(sorted(fatias.items())), "registros": registros,
            "fora_perfil_sem_score": sum(c["enquadramento"] == "fora_perfil" for c in casos),
            "ato_por_ocorrencia_medido": False, "alvos_medidos": False,
            "runtime_completo_avaliado": False, "avaliacao_independente": False, **FLAGS}


def _hash(caminho: Path) -> str:
    with caminho.open("rb") as arquivo:
        return hashlib.file_digest(arquivo, "sha256").hexdigest()


def executar(corpus: Path, modelos: dict[str, Path], destino: Path) -> dict:
    """Congela fontes antes da carga e reconfere antes de publicar resultados.

Aceita apenas artefatos joblib locais confiáveis do projeto. Nenhum treinador
é chamado, nenhum buffer prospectivo é instanciado, nenhum resultado vira gold.
"""
    if destino.exists():
        raise FileExistsError("preservar diagnóstico anterior")
    if not modelos or any(not nome.strip() for nome in modelos):
        raise ValueError("informar modelos identificados")
    fontes = [corpus, *modelos.values()]
    # Fonte e dependências do diagnóstico/modelo ficam identificadas mesmo
    # quando a worktree diverge do HEAD. Nenhum hash histórico é reescrito.
    fontes += list(Path(__file__).parent.glob("*.py"))
    hashes = {str(p.resolve()): _hash(p) for p in fontes}
    casos = [json.loads(l) for l in corpus.read_text(encoding="utf-8").splitlines() if l.strip()]
    auditar_corpus(casos)
    resultados = {}
    for nome, caminho in modelos.items():
        modelo = carregar_modelo(caminho)
        encoder = getattr(modelo, "encoder_semantico", None)
        # Há representações compostas; capturar o encoder ONNX também.
        encoder = getattr(encoder, "encoder_semantico", encoder)
        for atributo in ("caminho_modelo", "caminho_tokenizer"):
            p = getattr(encoder, atributo, None)
            if p is not None:
                p = Path(p)
                chave, digest = str(p.resolve()), _hash(p)
                if chave in hashes and hashes[chave] != digest:
                    raise ValueError("dependência mudou durante diagnóstico")
                hashes[chave] = digest
        resultados[nome] = avaliar(casos, modelo)
    if any(_hash(Path(p)) != digest for p, digest in hashes.items()):
        raise ValueError("fonte mudou durante diagnóstico; não publicar")
    resultado = {"python": platform.python_version(), "fontes_sha256": hashes,
                 "modelos": {nome: str(p.resolve()) for nome, p in modelos.items()},
                 "resultados": resultados, "comparacao_pareada_de_fine_tuning": False,
                 "limites": ["desenvolvimento sintético conhecido", "gold de curadoria IA",
                             "somente inferência do modelo e normalizador neural",
                             "sem segmentação, autoridade ou executor da Laylay",
                             "não mede ato completo, alvos, relações ou superioridade sobre o legado"],
                 **FLAGS}
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "resultado.json").open("x", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--modelo", action="append", required=True, help="nome=caminho local confiável")
    parser.add_argument("--destino", type=Path, required=True)
    args = parser.parse_args()
    pares = [v.split("=", 1) for v in args.modelo]
    if any(len(p) != 2 for p in pares) or len({p[0] for p in pares}) != len(pares):
        parser.error("modelos precisam de nomes únicos no formato nome=caminho")
    r = executar(args.corpus, {nome: Path(p) for nome, p in pares}, args.destino)
    print(json.dumps({nome: v["fatias"] for nome, v in r["resultados"].items()}, ensure_ascii=False))
