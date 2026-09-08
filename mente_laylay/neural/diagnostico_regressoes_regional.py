"""Reproduz previsões fora do treino da rodada regional, sem novo candidato."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from sklearn.base import clone
from sklearn.pipeline import Pipeline

from mente_laylay.especialistas.capacidades import intents_registradas
from .avaliacao import head_aplicavel
from .dataset import carregar_jsonl
from .diagnostico_fold_negacao import selecionar_fold
from .diagnostico_pistas_negacao import explicar_pistas
from .experimento_escopo_negacao import ajustar_cabeca, medir_negacao
from .modelo import carregar_modelo
from .representacao_regioes_texto import criar_extrator_regioes_texto
from .representacao_sinais_atomicos import separar_texto_e_sinais
from .treino import _hash_dados


def executar(*, experimento: Path, referencia: Path, historico: Path, saida: Path) -> dict:
    if saida.exists():
        raise FileExistsError("preservar diagnóstico anterior")
    raiz = Path(__file__).resolve().parents[2]
    ler = lambda p: json.loads(p.read_text(encoding="utf-8"))
    protocolo, rel = ler(experimento / "protocolo.json"), ler(experimento / "relatorio.json")
    ref = ler(referencia / "relatorio.json")
    for nome, digest in protocolo["fontes"].items():
        if hashlib.sha256(Path(nome).read_bytes()).hexdigest() != digest:
            raise ValueError(f"fonte mudou: {nome}")
    prov = ref["proveniencia"]
    catalogo = intents_registradas()
    datasets = raiz / "mente_laylay/neural/datasets"
    hist = carregar_jsonl(datasets / "dev_v0.jsonl", intents_permitidas=catalogo)
    for nome in ler(historico / "validacao_cruzada_heads.json")["dataset"]["lotes_candidatos"]:
        hist.extend(carregar_jsonl(datasets / "candidatos" / nome, intents_permitidas=catalogo))
    novos = carregar_jsonl(referencia / "lote_negacao.jsonl", intents_permitidas=catalogo)
    if _hash_dados(hist + novos) != protocolo["sha256_treino"]:
        raise ValueError("treino divergiu")
    modelo_path = raiz / prov["modelo"]
    digest = hashlib.sha256(modelo_path.read_bytes()).hexdigest()
    if digest != protocolo["sha256_modelo"]:
        raise ValueError("modelo mudou")
    hist = [i for i in hist if head_aplicavel(i, "negation")]
    novos = [i for i in novos if head_aplicavel(i, "negation")]
    itens = hist + novos
    base = carregar_modelo(modelo_path).cabeca_negacao
    proto = Pipeline([("features", criar_extrator_regioes_texto()), ("classifier", clone(base.named_steps["classifier"]))])
    previsoes = {n: [None] * len(itens) for n in ("controle", "candidato")}
    regressoes, ganhos = [], []
    for fold in rel["cv"]["folds"]:
        tr, te = selecionar_fold(itens, rel["cv"], fold["grupos_teste"][0])
        controle = ajustar_cabeca(base, [itens[i] for i in tr if i < len(hist)])
        candidato = ajustar_cabeca(proto, [itens[i] for i in tr])
        for nome, h in (("controle", controle), ("candidato", candidato)):
            for i, p in zip(te, h.predict([itens[i]["text"] for i in te]), strict=True):
                previsoes[nome][i] = bool(p)
        for i in te:
            if i >= len(hist):
                continue
            esperado = itens[i]["negated"]
            a, b = previsoes["controle"][i], previsoes["candidato"][i]
            if a == b:
                continue
            registro = {"id": i, "fold": fold["fold"], "item": itens[i],
                        "sinais_canonicos": list(separar_texto_e_sinais(itens[i]["text"])[1]),
                        "controle": explicar_pistas(controle, itens[i]["text"]),
                        "candidato": explicar_pistas(candidato, itens[i]["text"])}
            (regressoes if a == esperado else ganhos).append(registro)
        print(f"fold {fold['fold']} reproduzido", flush=True)
    medidas = {f: {nome: medir_negacao([itens[i] for i in ids], [ps[i] for i in ids])
                   for nome, ps in previsoes.items()}
               for f, ids in (("historica", list(range(len(hist)))), ("nova", list(range(len(hist), len(itens)))))}
    for fatia in medidas:
        for nome in previsoes:
            if medidas[fatia][nome] != rel["cv"]["fatias"][fatia][nome]:
                raise ValueError("métricas por grupo não reproduzem a rodada")
    if len(regressoes) != rel["cv"]["fatias"]["historica"]["regressoes"] or len(ganhos) != rel["cv"]["fatias"]["historica"]["ganhos"]:
        raise ValueError("comparação pareada divergiu")
    if hashlib.sha256(modelo_path.read_bytes()).hexdigest() != digest:
        raise ValueError("modelo mudou durante diagnóstico")
    r = {"autoriza_promocao": False, "autoriza_execucao": False, "novo_candidato": False,
         "fit_apenas_reproducao": True, "modelos_salvos": False, "sha256_modelo": digest,
         "sha256_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         "sha256_relatorio_reproduzido": hashlib.sha256((experimento / "relatorio.json").read_bytes()).hexdigest(),
         "medidas": medidas, "regressoes": regressoes, "ganhos": ganhos,
         "regressoes_por_sinal": dict(Counter(str(x["sinais_canonicos"]) for x in regressoes)),
         "previsoes": previsoes}
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for nome in ("experimento", "referencia", "historico", "saida"):
        p.add_argument("--" + nome, type=Path, required=True)
    r = executar(**vars(p.parse_args()))
    print(json.dumps({"regressoes": len(r["regressoes"]), "ganhos": len(r["ganhos"]),
                      "sinais": r["regressoes_por_sinal"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
