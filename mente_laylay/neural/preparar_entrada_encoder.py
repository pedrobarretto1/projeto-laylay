"""Ponte de texto bruto para o encoder treinável; preparação não realiza fit.

Mantém a unidade de supervisão em tokens literais. O mapa de agregação depende
só do texto e reproduz a interseção por caracteres do comparador existente.
Assim um subtoken que cruza pontuação não recebe dois rótulos incompatíveis:
seu estado participa de dois tokens, cada um com sua supervisão separada.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from tokenizers import Tokenizer

from .candidato_relacional import tokens
from .comparar_ocorrencias_v4 import alinhar_subtokens, ROTULOS
from .protocolo_ajuste_supervisionado import (
    _rotulos_brutos, auditar_corpus, preparar_particao,
)
from .sonda_ambiente_encoder import PASTA_MODELO, SHA_TOKENIZER
from .supervisao_relacoes_v4 import FLAGS


def carregar_tokenizer(caminho: Path) -> Tokenizer:
    """Instância offline da revisão fixada, sem truncamento silencioso."""
    bruto = caminho.read_bytes()
    if hashlib.sha256(bruto).hexdigest() != SHA_TOKENIZER:
        raise ValueError("tokenizer diverge da revisão fixada")
    tokenizer = Tokenizer.from_str(bruto.decode("utf-8"))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    return tokenizer


def representar_texto(texto: str, tokenizer: Tokenizer, *, max_length: int = 128) -> dict:
    """Somente texto entra no tokenizer e determina o mapa, nunca o gold."""
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("texto vazio")
    if type(max_length) is not int or not 1 <= max_length <= 128:
        raise ValueError("comprimento fora do perfil técnico validado")
    if tokenizer.truncation is not None or tokenizer.padding is not None:
        raise ValueError("tokenizer deve estar sem truncamento e sem padding")
    codificado = tokenizer.encode(texto)
    if codificado.overflowing or len(codificado.ids) > max_length:
        raise ValueError("texto excede comprimento; não truncar supervisão")
    if tokenizer.token_to_id("<unk>") in codificado.ids:
        raise ValueError("token desconhecido exige revisão da representação")
    offsets = codificado.offsets
    mapa = []
    for palavra, a, b in tokens(texto):
        indices = [i for i, (x, y) in enumerate(offsets)
                   if codificado.attention_mask[i] and not codificado.special_tokens_mask[i]
                   and x < b and a < y]
        cobertos = {j for i in indices for j in range(*offsets[i])}
        if not indices or not set(range(a, b)) <= cobertos:
            raise ValueError("subtokens não cobrem token literal integralmente")
        pesos = [min(b, offsets[i][1]) - max(a, offsets[i][0]) for i in indices]
        total = sum(pesos)
        mapa.append({"texto": palavra, "inicio": a, "fim": b, "indices": indices,
                     "pesos": [p / total for p in pesos]})
    return {"texto": texto, "encoder": {"input_ids": codificado.ids,
             "attention_mask": codificado.attention_mask, "token_type_ids": codificado.type_ids},
            "offsets": [list(p) for p in offsets], "especiais": codificado.special_tokens_mask,
            "mapa_tokens": mapa, "agregacao": "media_intersecao_caracteres_depois_l2"}


def conferir_equivalencia(entrada: dict) -> None:
    """Prova numérica contra o agregador canônico; estados artificiais, sem fit."""
    n = len(entrada["offsets"])
    estados = np.random.default_rng(27).normal(size=(n, 384)).astype(np.float32)
    esperado = alinhar_subtokens(entrada["texto"], entrada["offsets"],
                                entrada["encoder"]["attention_mask"], entrada["especiais"], estados)
    previsto = []
    for token in entrada["mapa_tokens"]:
        v = np.average(estados[token["indices"]], axis=0, weights=token["pesos"])
        previsto.append(v / np.linalg.norm(v))
    if not np.allclose(np.asarray(previsto), esperado, rtol=1e-5, atol=1e-6):
        raise ValueError("mapa diverge do agregador canônico")


def preparar(casos: list[dict], tokenizer: Tokenizer, *, particao: str) -> dict:
    """Desenvolvimento é diagnóstico. Demais partições passam pelo gate real."""
    auditoria = auditar_corpus(casos)
    if particao == "desenvolvimento":
        selecionados = [c for c in casos if c["particao"] == particao]
        exemplos = [{"id": c["id"], "entrada": {"texto": c["texto"]},
                     "rotulos": _rotulos_brutos(c["fonte_v4"])}
                    for c in selecionados if c["enquadramento"] == "supervisionado"]
        fora = [{"id": c["id"], "motivo": c["motivo_fora_perfil"]}
                for c in selecionados if c["enquadramento"] == "fora_perfil"]
    else:
        # Nenhum caminho local alternativo pode converter desenvolvimento
        # insuficiente em treino aprovado.
        lote = preparar_particao(casos, particao)
        exemplos, fora = lote["exemplos"], lote["fora_perfil"]
    if not exemplos:
        raise ValueError("partição sem exemplos supervisionados")
    catalogo = sorted(ROTULOS)
    saida = []
    for e in exemplos:
        entrada = representar_texto(e["entrada"]["texto"], tokenizer)
        conferir_equivalencia(entrada)
        if len(entrada["mapa_tokens"]) != len(e["rotulos"]):
            raise ValueError("quantidade de tokens diverge da supervisão canônica")
        saida.append({"id": e["id"], "entrada": entrada,
                      "supervisao": {"rotulos": e["rotulos"],
                                     "ids_rotulos": [catalogo.index(r) for r in e["rotulos"]]}})
    return {"particao": particao, "uso": "diagnostico" if particao == "desenvolvimento" else "preparacao",
            "rotulos_catalogo": catalogo, "exemplos": saida, "fora_perfil": fora,
            "auditoria_corpus": auditoria, "equivalencia_agregador_verificada": True,
            "forward_encoder_executado": False, "aprendizado_medido": False, **FLAGS}


def executar(corpus: Path, destino: Path, *, particao: str = "desenvolvimento",
             caminho_tokenizer: Path = PASTA_MODELO / "tokenizer.json") -> dict:
    if destino.exists():
        raise FileExistsError("preservar preparação anterior")
    fontes = [corpus, caminho_tokenizer, Path(__file__),
              *[Path(__file__).with_name(n) for n in (
                  "candidato_relacional.py", "comparar_ocorrencias_v4.py",
                  "protocolo_ajuste_supervisionado.py", "supervisao_relacoes_v4.py")]]
    def hashes():
        return {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in fontes}
    antes = hashes()
    casos = [json.loads(l) for l in corpus.read_text(encoding="utf-8").splitlines() if l.strip()]
    r = preparar(casos, carregar_tokenizer(caminho_tokenizer), particao=particao)
    if hashes() != antes:
        raise ValueError("fontes mudaram durante preparação")
    r["fontes_sha256"] = antes
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "preparacao.json").open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return {"exemplos": len(r["exemplos"]), "fora_perfil": len(r["fora_perfil"]),
            "tokens": sum(len(e["entrada"]["mapa_tokens"]) for e in r["exemplos"]),
            "max_subtokens": max(len(e["entrada"]["encoder"]["input_ids"]) for e in r["exemplos"]),
            "dados_prontos": r["auditoria_corpus"]["dados_prontos_para_preparacao"], **FLAGS}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--destino", type=Path, required=True)
    parser.add_argument("--particao", default="desenvolvimento")
    args = parser.parse_args()
    print(json.dumps(executar(args.corpus, args.destino, particao=args.particao), ensure_ascii=False))
