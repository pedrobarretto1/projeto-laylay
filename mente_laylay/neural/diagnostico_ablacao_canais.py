"""Zera canais somente numa cópia do vetor; não retreina nem promove."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from mente_laylay.especialistas.capacidades import intents_registradas
from .dataset import carregar_jsonl
from .experimento_escopo_negacao import medir_negacao
from .representacao_escopo_local import segmentar_estrutura_local


VARIANTES = {"integral": (), "sem_palavras": ("palavras",),
             "sem_caracteres": ("caracteres",), "somente_escopo": ("palavras", "caracteres")}


def medir_canais(cabeca: Any, textos: list[str]) -> dict:
    """Verifica classes, soma e predict antes de qualquer ablação do vetor."""
    if not textos or any(not isinstance(t, str) or not t.strip() for t in textos):
        raise ValueError("coleção não vazia de textos é obrigatória")
    features, clf = cabeca.named_steps["features"], cabeca.named_steps["classifier"]
    nomes_canais = [nome for nome, _ in features.transformer_list]
    if nomes_canais != ["palavras", "caracteres", "escopo_local"]:
        raise ValueError("exige três canais conhecidos")
    classes = np.asarray(clf.classes_)
    if classes.dtype.kind != "b" or classes.tolist() != [False, True]:
        raise ValueError("classes booleanas ordenadas são obrigatórias")
    x = features.transform(textos).tocsr()
    nomes = features.get_feature_names_out()
    coef = np.asarray(clf.coef_)
    if coef.shape != (1, x.shape[1]) or len(nomes) != x.shape[1]:
        raise ValueError("dimensões incompatíveis")
    if not np.isfinite(x.data).all() or not np.isfinite(coef).all() or not np.isfinite(clf.intercept_).all():
        raise ValueError("valores não finitos")
    contribuicoes = {}
    for canal in nomes_canais:
        ids = [i for i, nome in enumerate(nomes) if nome.startswith(canal + "__")]
        contribuicoes[canal] = np.asarray(x[:, ids] @ coef[0, ids]).ravel()
    real = np.asarray(clf.decision_function(x))
    soma = float(clf.intercept_[0]) + sum(contribuicoes.values())
    if not np.allclose(real, soma, atol=1e-10, rtol=1e-10) or not np.array_equal(real > 0, cabeca.predict(textos)):
        raise ValueError("soma não reproduz decisão real")
    resultados = {}
    for nome, removidos in VARIANTES.items():
        copia = x.copy()
        mascara = np.ones(x.shape[1])
        for i, feature in enumerate(nomes):
            if any(feature.startswith(c + "__") for c in removidos):
                mascara[i] = 0
        copia = copia.multiply(mascara).tocsr()
        score = np.asarray(clf.decision_function(copia))
        esperado = real - sum((contribuicoes[c] for c in removidos), np.zeros(len(textos)))
        if not np.allclose(score, esperado, atol=1e-10, rtol=1e-10):
            raise ValueError("ablação não corresponde à subtração dos canais")
        resultados[nome] = {"scores": score.tolist(), "negated": [bool(v) for v in clf.predict(copia)]}
    return {"variantes": resultados, "intercepto": float(clf.intercept_[0]),
            "contribuicoes": {c: v.tolist() for c, v in contribuicoes.items()},
            "erro_maximo_reconstrucao": float(np.max(np.abs(real - soma)))}


def contrastes_diagnosticos() -> list[dict]:
    pares = [
        ("audio", "coloca o volume em 30, não em 50", "não coloca o volume em 30"),
        ("apps", "abre o Opera, não o Firefox", "não abra o Opera"),
        ("musica", "toca a música Brisa, não a Aurora", "não toque a música Brisa"),
        ("arquivo", "abre o arquivo rascunho.txt, não o relatório.txt", "não abra o arquivo rascunho.txt"),
        ("musica_citada", 'toque "Não Volte"', 'não toque "Não Volte"'),
        ("arquivo_citado", 'leia "não apagar.txt"', 'não leia "não apagar.txt"'),
        ("arquivo_literal", "leia o arquivo não.txt", "não leia o arquivo não.txt"),
        ("recusa_modal", "quero que você inicie o Opera, não o Firefox", "não quero que você inicie o Opera"),
        ("iot", "por gentileza pare o ventilador", "não pare o ventilador"),
        ("apps_estado", "mantenha o VS Code aberto", "não abra o VS Code"),
    ]
    return [{"text": t, "negated": neg, "family": nome, "fatia": "recusa" if neg else "nao_recusa"}
            for nome, afirmacao, recusa in pares for neg, t in ((False, afirmacao), (True, recusa))]


def executar(*, experimento: Path, saida: Path) -> dict:
    if saida.exists():
        raise FileExistsError("preservar evidência existente")
    raiz = Path(__file__).resolve().parents[2]
    protocolo_path = experimento / "protocolo.json"
    protocolo = json.loads(protocolo_path.read_text(encoding="utf-8"))
    if protocolo["representacao"] != "lexical_mais_escopo_local":
        raise ValueError("candidato incompatível")
    for nome, digest in protocolo["fontes"].items():
        if hashlib.sha256(Path(nome).read_bytes()).hexdigest() != digest:
            raise ValueError(f"componente mudou: {nome}")
    p = experimento / "cabeca_negacao_nao_promovida.joblib"
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    h = joblib.load(p)
    referencia = raiz / "memoria/neural/experimentos/escopo_sinais_atomicos_v2_peso1_20260906/protocolo.json"
    reservas = json.loads(referencia.read_text(encoding="utf-8"))["reservas"]
    from .treino import _hash_dados
    if _hash_dados(reservas) != protocolo["sha256_reservas"]:
        raise ValueError("reserva divergiu")
    frozen_path = raiz / "mente_laylay/neural/datasets/frozen_v0.jsonl"
    lotes = {"contrastes": contrastes_diagnosticos(), "frozen": carregar_jsonl(frozen_path, intents_permitidas=intents_registradas())}
    lotes.update({nome: [i for i in reservas if i["particao"] == nome] for nome in ("entidade", "construcao", "ambas")})
    resultados = {}
    for nome, itens in lotes.items():
        medicao = medir_canais(h, [i["text"] for i in itens])
        resultados[nome] = {"itens": itens, **medicao, "metricas": {
            variante: medir_negacao(itens, v["negated"]) for variante, v in medicao["variantes"].items()}}
    # Diagnóstico do extrator: uma citação inteira perde seu conteúdo no
    # canal estrutural, embora esse conteúdo continue nos canais lexicais.
    citacoes = ['"abra o Opera"', '"não abra o Opera"']
    estrutural = dict(h.named_steps["features"].transformer_list)["escopo_local"]
    vetores = estrutural.transform(citacoes)
    colisao = (vetores[0] != vetores[1]).nnz == 0
    if hashlib.sha256(p.read_bytes()).hexdigest() != digest:
        raise ValueError("cabeça mudou")
    r = {"autoriza_promocao": False, "autoriza_execucao": False, "treino_executado": False,
         "limites": ["remoção de canais com pesos antigos altera distribuição; não é candidato validado",
                    "conjuntos diagnósticos conhecidos; nenhuma métrica representa runtime ou avaliação inédita",
                    "negated=False não concede permissão"],
         "sha256_cabeca": digest, "sha256_frozen": hashlib.sha256(frozen_path.read_bytes()).hexdigest(),
         "sha256_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         "sha256_protocolo": hashlib.sha256(protocolo_path.read_bytes()).hexdigest(),
         "citacao_total": {"textos": citacoes, "vetores_estruturais_iguais": colisao,
                           "segmentacao": [segmentar_estrutura_local(t) for t in citacoes]},
         "resultados": resultados}
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--experimento", type=Path, required=True)
    p.add_argument("--saida", type=Path, required=True)
    r = executar(**vars(p.parse_args()))
    print(json.dumps({nome: v["metricas"] for nome, v in r["resultados"].items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
