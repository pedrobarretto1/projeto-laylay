"""Adição de um canal estrutural à cabeça lexical, com protocolo imutável."""

from __future__ import annotations

import argparse
from copy import copy
import hashlib
import json
from pathlib import Path
import subprocess

import joblib

from mente_laylay.especialistas.capacidades import intents_registradas
from .comparacao_linguistica import comparar_pedidos, criar_preditor_neural, prever_python_sem_contexto
from .dataset import carregar_jsonl
from .experimento_escopo_negacao import ajustar_cabeca, comparar_cv, medir_negacao, validar_reserva_entidades
from .modelo import carregar_modelo
from .representacao_escopo_local import criar_prototipo_escopo_local
from .treino import _hash_dados


def executar(*, referencia: Path, historico: Path, destino: Path) -> dict:
    if destino.exists():
        raise FileExistsError("preservar experimento existente")
    raiz = Path(__file__).resolve().parents[2]
    ler = lambda p: json.loads(p.read_text(encoding="utf-8"))
    ref, protocolo_ref = ler(referencia / "relatorio.json"), ler(referencia / "protocolo.json")
    prov = ref["proveniencia"]
    for nome, digest in prov["sha256_componentes"].items():
        if hashlib.sha256((raiz / nome).read_bytes()).hexdigest() != digest:
            raise ValueError(f"componente de referência mudou: {nome}")
    datasets = raiz / "mente_laylay/neural/datasets"
    catalogo = intents_registradas()
    hist = carregar_jsonl(datasets / "dev_v0.jsonl", intents_permitidas=catalogo)
    for nome in ler(historico / "validacao_cruzada_heads.json")["dataset"]["lotes_candidatos"]:
        hist.extend(carregar_jsonl(datasets / "candidatos" / nome, intents_permitidas=catalogo))
    novos = carregar_jsonl(referencia / "lote_negacao.jsonl", intents_permitidas=catalogo)
    if _hash_dados(hist) != prov["sha256_historicos"] or _hash_dados(novos) != prov["sha256_novos"]:
        raise ValueError("dados não reproduzem a referência")
    reservas = protocolo_ref["reservas"]
    if _hash_dados(reservas) != protocolo_ref["sha256_reserva"]:
        raise ValueError("reserva mudou")
    auditoria = validar_reserva_entidades(hist + novos, reservas)
    modelo_path = raiz / prov["modelo"]
    digest = hashlib.sha256(modelo_path.read_bytes()).hexdigest()
    if digest != prov["sha256_modelo"]:
        raise ValueError("modelo mudou")
    bateria_path = raiz / "tests/fixtures/neural/bateria_linguistica_v1.json"
    if hashlib.sha256(bateria_path.read_bytes()).hexdigest() != prov["sha256_bateria"]:
        raise ValueError("bateria mudou")
    modelo = carregar_modelo(modelo_path)
    base = modelo.cabeca_negacao
    protocolo = {"autoriza_promocao": False, "autoriza_execucao": False,
                 "representacao": "lexical_mais_escopo_local", "peso_novos": 1, "limiar": 0,
                 "sha256_modelo": digest, "sha256_dados": _hash_dados(hist + novos),
                 "sha256_reservas": _hash_dados(reservas), "reservas_conhecidas": True,
                 "auditoria_reserva": auditoria,
                 "folds_referencia": {e: ref[e]["folds"] for e in ("cv", "cv_entidades")},
                 "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=raiz, text=True).strip(),
                 "worktree": subprocess.check_output(["git", "status", "--short"], cwd=raiz, text=True, encoding="utf-8"),
                 "fontes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                     (Path(__file__), raiz / "mente_laylay/neural/representacao_escopo_local.py",
                      raiz / "mente_laylay/arquivos/nome_natural.py", referencia / "relatorio.json")}}
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    prototipo = criar_prototipo_escopo_local(base)
    cvs = {}
    for chave, eixo in (("cv", "construcao"), ("cv_entidades", "entidade")):
        cv = comparar_cv(base, hist, novos, prototipo_candidato=prototipo, eixo=eixo)
        if cv["folds"] != ref[chave]["folds"]:
            raise ValueError("partições não reproduzem a referência")
        cvs[chave] = cv
        print(f"CV {eixo} concluída", flush=True)
    h = ajustar_cabeca(prototipo, hist + novos)
    candidato = copy(modelo)
    candidato.cabeca_negacao = h
    candidato.versao += "_escopo_local_nao_promovido"
    bateria = ler(bateria_path)
    diagnostico = comparar_pedidos(bateria, python=prever_python_sem_contexto, neural=criar_preditor_neural(candidato))
    for caso in bateria["casos"]:
        a, b = modelo.prever(caso["text"]), candidato.prever(caso["text"])
        for resultado in (a, b):
            resultado.pop("negated")
            resultado["confidence"].pop("negation")
        if a != b:
            raise ValueError("outra cabeça mudou")
    frozen = carregar_jsonl(datasets / "frozen_v0.jsonl", intents_permitidas=catalogo)
    medidas = {nome: {ch: medir_negacao(lote, list(c.predict([i["text"] for i in lote])))
                      for ch, c in (("base", base), ("candidato", h))}
               for nome, lote in [("treino_novo", novos), ("frozen", frozen)] +
                   [(p, [i for i in reservas if i["particao"] == p]) for p in ("entidade", "construcao", "ambas")]}
    if hashlib.sha256(modelo_path.read_bytes()).hexdigest() != digest:
        raise ValueError("modelo mudou durante experimento")
    r = {"autoriza_promocao": False, "autoriza_execucao": False, **cvs,
         "medidas": medidas, "bateria": diagnostico, "outros_heads_preservados": True,
         "protocolo_sha256": hashlib.sha256((destino / "protocolo.json").read_bytes()).hexdigest()}
    joblib.dump(h, destino / "cabeca_negacao_nao_promovida.joblib")
    with (destino / "relatorio.json").open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for nome in ("referencia", "historico", "destino"):
        p.add_argument("--" + nome, type=Path, required=True)
    r = executar(**vars(p.parse_args()))
    print(json.dumps({"cv": r["cv"]["fatias"], "medidas": r["medidas"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
