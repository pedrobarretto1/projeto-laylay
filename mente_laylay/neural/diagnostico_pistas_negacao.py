"""Decomposição exata de cabeça linear já treinada; nunca chama fit."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import copy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import joblib
import numpy as np

from .representacao_sinais_atomicos import SinaisNegacaoAtomicos


def _componentes(cabeca: Any, texto: str) -> tuple:
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("texto não vazio é obrigatório")
    features = cabeca.named_steps["features"]
    classificador = cabeca.named_steps["classifier"]
    classes = np.asarray(classificador.classes_)
    if classes.dtype.kind != "b" or classes.tolist() != [False, True]:
        raise ValueError("a direção do score exige classes booleanas [False, True]")
    vetor = features.transform([texto]).toarray()[0]
    nomes = features.get_feature_names_out()
    coef = np.asarray(classificador.coef_)
    if coef.shape != (1, len(vetor)) or len(nomes) != len(vetor):
        raise ValueError("cabeça linear binária incompatível com extrator")
    if not np.isfinite(vetor).all() or not np.isfinite(coef).all():
        raise ValueError("vetor ou coeficientes não finitos")
    return features, classificador, vetor, nomes, coef[0]


def explicar_pistas(cabeca: Any, texto: str) -> dict:
    features, clf, vetor, nomes, coef = _componentes(cabeca, texto)
    contribuicoes = vetor * coef
    intercepto = float(clf.intercept_[0])
    score = float(clf.decision_function(features.transform([texto]))[0])
    reconstruido = intercepto + float(contribuicoes.sum())
    if not np.isfinite(score) or not np.isclose(score, reconstruido, atol=1e-10, rtol=1e-10):
        raise ValueError("a soma das contribuições não reproduziu o modelo")
    canais = {}
    # Metadados fixos não possuem vocabulário nem OOV.
    for canal, transformador in features.transformer_list:
        indices = [i for i, nome in enumerate(nomes) if nome.startswith(canal + "__")]
        if isinstance(transformador, SinaisNegacaoAtomicos):
            canais[canal] = {
                "tipo": "sinais_atomicos",
                "soma_contribuicoes": float(contribuicoes[indices].sum()),
                "features_ativas": int(np.count_nonzero(vetor[indices])),
                "sinais": [{"feature": str(nomes[i]), "valor": float(vetor[i]),
                            "coeficiente": float(coef[i]), "contribuicao": float(contribuicoes[i])}
                           for i in indices],
            }
            continue
        if not hasattr(transformador, "vocabulary_"):
            raise ValueError("diagnóstico de OOV exige canais vetoriais lexicais")
        emitidos = Counter(transformador.build_analyzer()(texto))
        desconhecidos = sorted(set(emitidos) - set(transformador.vocabulary_))
        canais[canal] = {
            "soma_contribuicoes": float(contribuicoes[indices].sum()),
            "features_ativas": int(np.count_nonzero(vetor[indices])),
            "tipos_emitidos": len(emitidos), "tipos_ood_vocabulario": len(desconhecidos),
            "fora_vocabulario": desconhecidos if canal == "palavras" else desconhecidos[:20],
            "lista_truncada": canal != "palavras" and len(desconhecidos) > 20,
        }
    relevantes = sorted(np.flatnonzero(vetor), key=lambda i: abs(contribuicoes[i]), reverse=True)[:12]
    return {
        "texto": texto, "negated": bool(cabeca.predict([texto])[0]),
        "score": score, "intercepto": intercepto, "score_reconstruido": reconstruido,
        "erro_reconstrucao": abs(score - reconstruido), "canais": canais,
        "pistas_principais": [{"feature": str(nomes[i]), "valor": float(vetor[i]),
                               "coeficiente": float(coef[i]), "contribuicao": float(contribuicoes[i])}
                              for i in relevantes],
    }


def comparar_pistas(cabeca: Any, antes: str, depois: str) -> dict:
    _, _, a, nomes, coef = _componentes(cabeca, antes)
    _, _, b, _, _ = _componentes(cabeca, depois)
    delta = (b - a) * coef
    grupos = {
        "desapareceram": (a != 0) & (b == 0),
        "apareceram": (a == 0) & (b != 0),
        "compartilhadas_reponderadas": (a != 0) & (b != 0),
    }
    resumos = {nome: float(delta[mascara].sum()) for nome, mascara in grupos.items()}
    ea, eb = explicar_pistas(cabeca, antes), explicar_pistas(cabeca, depois)
    if not np.isclose(sum(resumos.values()), eb["score"] - ea["score"], atol=1e-10):
        raise ValueError("decomposição do delta inconsistente")
    principais = sorted(np.flatnonzero(delta), key=lambda i: abs(delta[i]), reverse=True)[:12]
    return {"antes": ea, "depois": eb, "mudou_decisao": ea["negated"] != eb["negated"],
            "delta_score": eb["score"] - ea["score"], "decomposicao_delta": resumos,
            "maiores_deltas": [{"feature": str(nomes[i]), "delta": float(delta[i])} for i in principais]}


def contrafactual_sem_marcadores_nos_caracteres(cabeca: Any, texto: str) -> dict:
    """Ablaciona apenas o vetor de caracteres numa CÓPIA, sem retreinar.

    Não é candidato: muda distribuição do extrator com pesos antigos. A
    mudança é diagnosticada, nunca usada como prova de segurança ou acurácia.
    """
    features, clf, vetor, nomes, _ = _componentes(cabeca, texto)
    canais = dict(features.transformer_list)
    caracteres = copy(canais["caracteres"])
    preprocessador = caracteres.build_preprocessor()
    enriquecido = preprocessador(texto)
    # Não remover ocorrências literais: só o sufixo efetivamente ANEXADO.
    from .modelo import enriquecer_texto_features
    import re
    import unicodedata
    normal = unicodedata.normalize("NFKD", texto.casefold())
    normal = "".join(c for c in normal if not unicodedata.combining(c))
    normal = re.sub(r"\s+", " ", normal).strip()
    if canais["caracteres"].preprocessor is not enriquecer_texto_features or not enriquecido.startswith(normal):
        raise ValueError("extrator diferente da fronteira lexical investigada")
    caracteres.preprocessor = lambda _: normal
    alternativo = caracteres.transform([texto]).toarray()[0]
    indices = [i for i, nome in enumerate(nomes) if nome.startswith("caracteres__")]
    vetor[indices] = alternativo
    return {
        "score": float(clf.decision_function(vetor.reshape(1, -1))[0]),
        "negated": bool(clf.predict(vetor.reshape(1, -1))[0]),
        "sufixo_retirado_apenas_do_canal_caracteres": enriquecido[len(normal):],
        "sem_retreino": True, "autoriza_promocao": False,
    }


PARES = (
    ("audio_alvo_novo", "ajuste o áudio para 14, não para 28", "ajuste o áudio para 83, não para 96"),
    ("apps_alvo_novo", "inicie o Cedrion, não o Belmora", "inicie o Zelvoria, não o Tarselio"),
    ("apps_alvo_historico", "inicie o Cedrion, não o Belmora", "inicie o Opera, não o Firefox"),
    ("verbo_mesmo_alvo", "inicie o Opera, não o Firefox", "abre o Opera, não o Firefox"),
    ("cancelamento_real", "inicie o Cedrion, não o Belmora", "não inicie o Cedrion"),
)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cabeca", type=Path, required=True, help="joblib local confiável")
    p.add_argument("--saida", type=Path, required=True)
    args = p.parse_args()
    if args.saida.exists():
        p.error("saída já existe; preservar evidência anterior")
    antes_hash = hashlib.sha256(args.cabeca.read_bytes()).hexdigest()
    cabeca = joblib.load(args.cabeca)
    pares = {nome: comparar_pistas(cabeca, a, b) for nome, a, b in PARES}
    textos = list(dict.fromkeys(t for _, a, b in PARES for t in (a, b)))
    contrafactuais = {t: contrafactual_sem_marcadores_nos_caracteres(cabeca, t) for t in textos}
    if hashlib.sha256(args.cabeca.read_bytes()).hexdigest() != antes_hash:
        raise RuntimeError("artefato mudou durante a inspeção")
    raiz = Path(__file__).resolve().parents[2]
    r = {"somente_diagnostico": True, "autoriza_promocao": False, "treino_executado": False,
         "sha256_cabeca": antes_hash, "cabeca": str(args.cabeca),
         "sha256_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=raiz, text=True).strip(),
         "worktree": subprocess.check_output(["git", "status", "--short"], cwd=raiz, text=True, encoding="utf-8"),
         "pares": pares, "contrafactuais_nao_promoviveis": contrafactuais}
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        json.dump(r, arquivo, ensure_ascii=False, indent=2)
    print(json.dumps({nome: {"delta": par["delta_score"], "componentes": par["decomposicao_delta"]} for nome, par in pares.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
