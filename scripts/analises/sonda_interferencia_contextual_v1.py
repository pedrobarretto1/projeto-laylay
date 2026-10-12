"""Diagnóstico offline: contexto concorrente e ocorrência, sem candidato novo."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from scripts.analises import sonda_transferencia_papel_isolado_v1 as anterior

BASE = anterior.BASE
HASH_ANTERIOR = "2c9a9c039827ca5283ab3b266b502ccca872f360faba61b1e382ab3b05e22138"
DESCRICAO = 'A anotação “o viveiro fica a oeste” informa a localização.'
ACAO = 'Outra linha pede para mover uma bancada.'
NOME = 'O brinquedo se chama “alinhe o pêndulo”'
TITULO = 'A palestra tem o título “se eu recalibrasse a balança”'
INVERTIDA = 'No manual, a montadora orientou “alinhe o pêndulo”; o brinquedo se chama “alinhe o pêndulo”.'


def carregar_painel() -> list[dict]:
    if hashlib.sha256(Path(anterior.__file__).read_bytes()).hexdigest() != HASH_ANTERIOR:
        raise ValueError("dependencia congelada alterada")
    historicos = {c["id"]: c for c in anterior.carregar_painel()}
    specs = [
        ("D0", DESCRICAO, "c1", "expressao_sem_operacao", "informa a localização"),
        ("DN", DESCRICAO + ' Outra linha descreve uma bancada de madeira.', "c1", "expressao_sem_operacao", "informa a localização"),
        ("DA", DESCRICAO + ' ' + ACAO, "c1", "expressao_sem_operacao", "informa a localização"),
        ("DB", ACAO + ' ' + DESCRICAO, "c1", "expressao_sem_operacao", "informa a localização"),
        ("N0", NOME + '.', "c1", "nome_designacao", "O brinquedo se chama"),
        ("NN", NOME + '; no manual, a página tem uma borda azul.', "c1", "nome_designacao", "O brinquedo se chama"),
        ("ND", NOME + '; no manual, a montadora orientou “aperte o parafuso”.', "c1", "nome_designacao", "O brinquedo se chama"),
        ("NS", NOME + '; no manual, a montadora orientou “alinhe o pêndulo”.', "c1", "nome_designacao", "O brinquedo se chama"),
        ("OS", NOME + '; no manual, a montadora orientou “alinhe o pêndulo”.', "c2", "operacao_mencionada", "a montadora orientou"),
        ("NR", INVERTIDA, "c2", "nome_designacao", "o brinquedo se chama"),
        ("OR", INVERTIDA, "c1", "operacao_mencionada", "a montadora orientou"),
        ("C0", TITULO + '.', "c1", "nome_designacao", "tem o título"),
        ("CN", TITULO + ', e a programação foi impressa em papel azul.', "c1", "nome_designacao", "tem o título"),
        ("CX", TITULO + ', embora a expressão pareça uma hipótese.', "c1", "nome_designacao", "tem o título"),
    ]
    seletor = anterior.anterior.selecao
    casos = [dict(id=i, texto=seletor.PREFIXO+t+seletor.SUFIXO,
                  foco_id=f, papel=p, pista=v) for i,t,f,p,v in specs]
    casos += [historicos[i] for i in ("T03", "T04", "T11", "T14")]
    for c in casos:
        entrada = anterior.anterior.anterior.papel.preparar_entrada(c)
        if not entrada["aspas_sintaticas"]["aspas_coerentes"]:
            raise ValueError("aspas invalidas")
        if c["pista"] not in [p["texto"] for p in seletor.catalogar(c)]:
            raise ValueError("pista nao catalogavel")
    return casos


def resumir(blocos: list[dict]) -> dict:
    casos = carregar_painel()
    invalido = {**BASE, "tipo": "resumo_invalido"}
    if not isinstance(blocos, list) or len(blocos) != 2*len(casos):
        return invalido
    por_caso = {}
    try:
        for b,(c,rep) in zip(blocos, anterior.sequencia(casos), strict=True):
            aferido = anterior.aferir_bloco(c,b,rep)
            por_caso.setdefault(c["id"], {})[str(rep)] = {
                m: {k:a[k] for k in ("shape", "papel_proposto", "papel_alinhado")}
                for m,a in aferido.items()}
    except (KeyError, TypeError, ValueError, OverflowError):
        return invalido
    return {**BASE, "tipo":"resumo_interferencia_contextual", "por_caso":por_caso,
            "runtime_laylay":False, "holdout_novo":False}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--saida", type=Path, required=True)
    args = p.parse_args()
    casos = carregar_painel()
    etapas = anterior.anterior.anterior.etapas
    digest = etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arq:
        def escrever(r:dict) -> None:
            arq.write(json.dumps(r, ensure_ascii=False, allow_nan=False)+"\n")
            arq.flush()
        escrever({**BASE, "tipo":"metadata", "casos_pre_consulta":casos,
                  "hash_script":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "hash_anterior":HASH_ANTERIOR, "digest_inicio":digest,
                  "head":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
                  "branch":subprocess.check_output(["git","branch","--show-current"],text=True).strip(),
                  "worktree":subprocess.check_output(["git","status","--short"],text=True).splitlines(),
                  "ordem":[[c["id"],rep] for c,rep in anterior.sequencia(casos)],
                  "runtime_laylay":False})
        blocos = []
        for c,rep in anterior.sequencia(casos):
            primeira = anterior.anterior.selecao.medir_caso(c,"catalogado",rep)
            isolada = anterior.anterior.medir_papel(c,primeira,"papel_sem_trecho")
            b = dict(id=c["id"],repeticao=rep,primeira=primeira,isolada=isolada)
            escrever(b)
            blocos.append(b)
            a = anterior.aferir_bloco(c,b,rep)
            print(json.dumps({"id":c["id"], "rep":rep,
                              **{m:v["papel_proposto"] for m,v in a.items()}}),flush=True)
        resumo = resumir(blocos)
        try:
            resumo["digest_final"] = etapas.coordenadas.digest_modelo()
            resumo["modelo_igual_entre_leituras"] = resumo["digest_final"] == digest
        except Exception as erro:
            resumo.update(erro_digest_final=type(erro).__name__,modelo_igual_entre_leituras=False)
        escrever(resumo)


if __name__ == "__main__":
    main()
