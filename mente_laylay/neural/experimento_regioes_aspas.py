"""Experimento regional com controles pareados fora do fit e CV por grupos."""

from __future__ import annotations

import argparse
from copy import copy
import hashlib
import json
from pathlib import Path

import joblib
from sklearn.base import clone
from sklearn.pipeline import Pipeline

from mente_laylay.especialistas.capacidades import intents_registradas
from .avaliacao import head_aplicavel
from .comparacao_linguistica import criar_preditor_neural
from .dataset import carregar_jsonl, validar_exemplo
from .datasets.gerar_controles_aspas_v1 import gerar_controles
from .experimento_escopo_negacao import ajustar_cabeca, comparar_cv, medir_negacao
from .modelo import carregar_modelo
from .qualidade import auditar_leakage_dataset
from .representacao_regioes_texto import criar_extrator_regioes_texto
from .treino import _hash_dados


def executar(*, referencia: Path, historico: Path, destino: Path) -> dict:
    if destino.exists():
        raise FileExistsError("preservar artefatos existentes")
    raiz = Path(__file__).resolve().parents[2]
    ler = lambda p: json.loads(p.read_text(encoding="utf-8"))
    r = ler(referencia / "relatorio.json")
    prov = r["proveniencia"]
    for nome, digest in prov["sha256_componentes"].items():
        if hashlib.sha256((raiz / nome).read_bytes()).hexdigest() != digest:
            raise ValueError(f"componente de referência mudou: {nome}")
    catalogo = intents_registradas()
    datasets = raiz / "mente_laylay/neural/datasets"
    hist = carregar_jsonl(datasets / "dev_v0.jsonl", intents_permitidas=catalogo)
    for nome in ler(historico / "validacao_cruzada_heads.json")["dataset"]["lotes_candidatos"]:
        hist.extend(carregar_jsonl(datasets / "candidatos" / nome, intents_permitidas=catalogo))
    novos = carregar_jsonl(referencia / "lote_negacao.jsonl", intents_permitidas=catalogo)
    if _hash_dados(hist) != prov["sha256_historicos"] or _hash_dados(novos) != prov["sha256_novos"]:
        raise ValueError("dados de referência mudaram")
    controles = gerar_controles()
    for item in controles:
        validar_exemplo(item, intents_permitidas=catalogo)
    modelo_path = raiz / prov["modelo"]
    digest = hashlib.sha256(modelo_path.read_bytes()).hexdigest()
    if digest != prov["sha256_modelo"]:
        raise ValueError("modelo mudou")
    destino.mkdir(parents=True, exist_ok=False)
    protocolo = {"autoriza_promocao": False, "autoriza_execucao": False,
                 "representacao": "forma_mais_conteudo_regional", "limiar": 0, "peso_novos": 1,
                 "sha256_modelo": digest, "sha256_treino": _hash_dados(hist + novos),
                 "controles": controles, "sha256_controles": _hash_dados(controles),
                 "limites": ["controles sintéticos não representam uso real", "relatos avaliam comando, não negação",
                             "novo treino mantém distribuição antiga de aspas; controles só medem transferência"],
                 "fontes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                     (Path(__file__), raiz / "mente_laylay/neural/datasets/gerar_controles_aspas_v1.py",
                      raiz / "mente_laylay/neural/representacao_regioes_texto.py", raiz / "mente_laylay/neural/representacao_escopo_local.py",
                      raiz / "mente_laylay/arquivos/nome_natural.py", referencia / "relatorio.json")}}
    with (destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    # Aspas geram duplicatas normalizadas intencionais DENTRO dos pares.
    # Nunca permitir equivalentes desses pares no treino.
    auditoria = auditar_leakage_dataset(controles, hist + novos)
    with (destino / "auditoria.json").open("x", encoding="utf-8") as f:
        json.dump(auditoria, f, ensure_ascii=False, indent=2)
    if not auditoria["aprovado"]:
        raise ValueError("sobreposição detectada; sem treino, consulte auditoria.json")
    print("Controles sem sobreposição com treino. Iniciando CV.", flush=True)
    modelo = carregar_modelo(modelo_path)
    base = modelo.cabeca_negacao
    prototipo = Pipeline([("features", criar_extrator_regioes_texto()), ("classifier", clone(base.named_steps["classifier"]))])
    cvs = {}
    for chave, eixo in (("cv", "construcao"), ("cv_entidades", "entidade")):
        cvs[chave] = comparar_cv(base, hist, novos, prototipo_candidato=prototipo, eixo=eixo)
        if cvs[chave]["folds"] != r[chave]["folds"]:
            raise ValueError("folds mudaram")
        print(f"CV {eixo} concluída", flush=True)
    h = ajustar_cabeca(prototipo, hist + novos)
    lexical = ajustar_cabeca(base, hist + novos)
    resultados = {}
    for nome, cabeca in (("base_configurada", base), ("lexical_v2", lexical), ("regional", h)):
        neg = [bool(v) for v in cabeca.predict([i["text"] for i in controles])]
        candidato = copy(modelo)
        candidato.cabeca_negacao = cabeca
        pred = criar_preditor_neural(candidato)
        previstos = [pred(i["text"]) for i in controles]
        por_aspas = {}
        for aspas in (False, True):
            indices = [n for n, i in enumerate(controles) if i["com_aspas"] == aspas and head_aplicavel(i, "negation")]
            relatos = [n for n, i in enumerate(controles) if i["com_aspas"] == aspas and i["ato"] == "relato"]
            por_aspas[str(aspas)] = {"negacao": medir_negacao([controles[n] for n in indices], [neg[n] for n in indices]),
                "relatos": {"total": len(relatos), "pedidos_operacionais_falsos": sum(previstos[n]["pedido_operacional"] for n in relatos),
                            "head_comando_positivo": sum(previstos[n]["head_comando"] for n in relatos)}}
        pares = {}
        for n, i in enumerate(controles):
            pares.setdefault(i["pair_id"], []).append(n)
        resultados[nome] = {"por_aspas": por_aspas,
            "pares_negacao_divergentes": sum(neg[a] != neg[b] for a, b in pares.values() if head_aplicavel(controles[a], "negation")),
            "pares_negacao_total": sum(head_aplicavel(controles[a], "negation") for a, b in pares.values()),
            "previsoes": [{"id": n, "negated": neg[n], **previstos[n]} for n in range(len(controles))]}
    frozen = carregar_jsonl(datasets / "frozen_v0.jsonl", intents_permitidas=catalogo)
    frozen_m = {nome: medir_negacao(frozen, list(c.predict([i["text"] for i in frozen])))
                for nome, c in (("base", base), ("regional", h))}
    if hashlib.sha256(modelo_path.read_bytes()).hexdigest() != digest:
        raise ValueError("modelo mudou durante experimento")
    relatorio = {"autoriza_promocao": False, "autoriza_execucao": False, **cvs, "controles": resultados,
                 "frozen": frozen_m, "protocolo_sha256": hashlib.sha256((destino / "protocolo.json").read_bytes()).hexdigest()}
    joblib.dump(h, destino / "cabeca_regional_nao_promovida.joblib")
    with (destino / "relatorio.json").open("x", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
    return relatorio


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for nome in ("referencia", "historico", "destino"):
        p.add_argument("--" + nome, type=Path, required=True)
    r = executar(**vars(p.parse_args()))
    print(json.dumps({"cv": r["cv"]["fatias"], "frozen": r["frozen"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
