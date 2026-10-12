"""Contraste de evidência proposta real, inclusive seleção de outra ocorrência."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from scripts.analises import sonda_interferencia_contextual_v1 as painel

proponente = painel.anterior.anterior
BASE = proponente.BASE
HASH_PAINEL = "f7cf9890d9f730eeeff3817f2272e5b7d450ffda6da890c74b15f4f2b925e939"
IDS = ("D0", "DA", "NS", "OS", "NR", "OR", "C0", "CN", "CX", "T03", "T04", "T11")


def carregar_painel() -> list[dict]:
    if hashlib.sha256(Path(painel.__file__).read_bytes()).hexdigest() != HASH_PAINEL:
        raise ValueError("painel congelado alterado")
    ix = {c["id"]:c for c in painel.carregar_painel()}
    return [ix[i] for i in IDS]


def resumir(blocos: list[dict]) -> dict:
    cs = carregar_painel()
    invalido = {**BASE, "tipo":"resumo_invalido"}
    if not isinstance(blocos,list) or len(blocos) != 2*len(cs):
        return invalido
    por_caso = {}
    try:
        for b,(c,rep,ordem) in zip(blocos,proponente.sequencia(cs),strict=True):
            if (b["id"]!=c["id"] or type(b["repeticao"]) is not int
                    or b["repeticao"]!=rep or b["primeira"]["repeticao"]!=rep
                    or b["ordem"]!=list(ordem) or set(b["segundas"])!=set(proponente.MODOS)):
                raise ValueError("identidade ou ordem divergente")
            primeira = proponente.conferir_primeira(c,b["primeira"])
            aferidos = {"conjunto":primeira}
            for m in proponente.MODOS:
                if b["segundas"][m].get("modo")!=m:
                    raise ValueError("modo divergente")
                aferidos[m] = proponente.aferir_papel(c,b["primeira"],b["segundas"][m])
            por_caso.setdefault(c["id"],{})[str(rep)] = {
                "selecao_literal_valida":primeira["vinculo"],
                "selecao_discriminativa_local":primeira["selecao_discriminativa_local"],
                "bracos":{m:{k:a[k] for k in ("shape","papel_proposto","papel_alinhado")}
                          for m,a in aferidos.items()}}
    except (KeyError,TypeError,ValueError,OverflowError):
        return invalido
    return {**BASE,"tipo":"resumo_evidencia_interferencia","por_caso":por_caso,
            "runtime_laylay":False,"holdout_novo":False}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--saida",type=Path,required=True)
    args = p.parse_args()
    cs = carregar_painel()
    digest = proponente.anterior.etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True,exist_ok=True)
    with args.saida.open("x",encoding="utf-8") as arq:
        def escrever(r:dict) -> None:
            arq.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+"\n")
            arq.flush()
        escrever({**BASE,"tipo":"metadata","casos_pre_consulta":cs,
                  "hash_script":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "hash_painel":HASH_PAINEL,"digest_inicio":digest,
                  "head":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
                  "branch":subprocess.check_output(["git","branch","--show-current"],text=True).strip(),
                  "worktree":subprocess.check_output(["git","status","--short"],text=True).splitlines(),
                  "ordem":[[c["id"],rep,list(o)] for c,rep,o in proponente.sequencia(cs)],
                  "runtime_laylay":False})
        blocos = []
        for c,rep,ordem in proponente.sequencia(cs):
            primeira = proponente.selecao.medir_caso(c,"catalogado",rep)
            b = dict(id=c["id"],repeticao=rep,ordem=list(ordem),primeira=primeira,segundas={})
            for m in ordem:
                b["segundas"][m] = proponente.medir_papel(c,primeira,m)
            escrever(b)
            blocos.append(b)
            print(json.dumps({"id":c["id"],"rep":rep,
                              **{m:proponente.aferir_papel(c,primeira,r)["papel_proposto"]
                                 for m,r in b["segundas"].items()}}),flush=True)
        resumo = resumir(blocos)
        try:
            resumo["digest_final"] = proponente.anterior.etapas.coordenadas.digest_modelo()
            resumo["modelo_igual_entre_leituras"] = resumo["digest_final"]==digest
        except Exception as erro:
            resumo.update(erro_digest_final=type(erro).__name__,modelo_igual_entre_leituras=False)
        escrever(resumo)


if __name__=="__main__":
    main()
