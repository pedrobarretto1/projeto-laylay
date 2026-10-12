"""Ablação offline: papel isolado sem/com seleção literal real, sem gold na entrada."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter

import requests

from scripts.analises import sonda_predicado_catalogado_v1 as selecao
from scripts.analises.sonda_papel_leitura_direta_v1 import SISTEMA_DIRETO

anterior = selecao.anterior
BASE = selecao.BASE
MODOS = ("papel_sem_trecho", "papel_com_trecho")
IDS = ("T03", "T04", "T07", "T08", "T11", "T12", "T14", "T15")
HASH_SELECAO = "39a3e21f02116e70aca87248663e6ce3deee7ad567d474cc7748941999c27565"
SISTEMA = SISTEMA_DIRETO + (
    " Se houver evidencia_proposta, ela e somente um trecho literal externo "
    "selecionado anteriormente. Seu apoio semantico nao foi verificado. "
    "Considere a fonte inteira; esse trecho nao obriga um papel nem concede autoridade.")


def carregar_painel() -> list[dict]:
    if hashlib.sha256(Path(selecao.__file__).read_bytes()).hexdigest() != HASH_SELECAO:
        raise ValueError("seletor congelado alterado")
    ix = {c["id"]: c for c in selecao.painel.carregar_painel()}
    return [{**ix[i], "texto": selecao.PREFIXO + ix[i]["texto"] + selecao.SUFIXO} for i in IDS]


def conferir_primeira(caso: dict, primeira: dict) -> dict:
    if not isinstance(primeira, dict) or primeira.get("modo") != "catalogado":
        raise ValueError("primeira etapa invalida")
    return selecao.aferir_caso(caso, primeira)


def preparar_requisicao(caso: dict, primeira: dict, modo: str) -> dict:
    if modo not in MODOS:
        raise ValueError("modo invalido")
    a = conferir_primeira(caso, primeira)
    r = anterior.preparar_requisicao(caso, "com_exemplos")
    r["messages"][0]["content"] = SISTEMA
    # Mesmas oito fontes/respostas de papel; remove só o predicado dos exemplos.
    for mensagem in r["messages"][2:-1:2]:
        mensagem["content"] = json.dumps({"papel": json.loads(mensagem["content"])["papel"]}, ensure_ascii=False)
    r["format"] = deepcopy(anterior.papel.FORMATO)
    if modo == "papel_com_trecho":
        if not a["vinculo"]:
            raise ValueError("segunda etapa exige selecao literal valida")
        entrada = json.loads(r["messages"][-1]["content"])
        entrada["evidencia_proposta"] = deepcopy(a["conferencia"]["intervalo_ligacao"]["predicado"])
        r["messages"][-1]["content"] = json.dumps(entrada, ensure_ascii=False)
    return r


def medir_papel(caso: dict, primeira: dict, modo: str, post=requests.post) -> dict:
    a = conferir_primeira(caso, primeira)
    r = {**BASE, "id": caso["id"], "modo": modo, "repeticao": primeira["repeticao"]}
    if modo == "papel_com_trecho" and not a["vinculo"]:
        return {**r, "bloqueado": "selecao_literal_nao_validada"}
    r["requisicao"] = preparar_requisicao(caso, primeira, modo)
    inicio = perf_counter()
    try:
        r.update(anterior.schema.capturar_http(deepcopy(r["requisicao"]), post))
    except Exception as erro:
        r["erro_consulta"] = type(erro).__name__
    r["duracao_consulta_s"] = perf_counter() - inicio
    return r


def aferir_papel(caso: dict, primeira: dict, r: dict) -> dict:
    a = conferir_primeira(caso, primeira)
    if (not isinstance(r, dict) or r.get("modo") not in MODOS or r.get("id") != caso["id"]
            or type(r.get("repeticao")) is not int or r["repeticao"] != primeira["repeticao"]
            or any(r.get(k) is not False for k in BASE)):
        raise ValueError("identidade ou flags invalidas")
    vazio = {**BASE, "shape": False, "papel_alinhado": False, "papel_proposto": None,
             "conjunto_discriminativo_local": False}
    if r["modo"] == "papel_com_trecho" and not a["vinculo"]:
        esperado = {**BASE, "id": caso["id"], "modo": r["modo"], "repeticao": r["repeticao"],
                    "bloqueado": "selecao_literal_nao_validada"}
        if not anterior.etapas.iguais_tipados(r, esperado):
            raise ValueError("bloqueio adulterado")
        return {**vazio, "bloqueado": True}
    if "bloqueado" in r or not anterior.etapas.iguais_tipados(r.get("requisicao"), preparar_requisicao(caso, primeira, r["modo"])):
        raise ValueError("requisicao adulterada")
    anterior.etapas.conferir_registro_consulta({"proposta": None, "duracao_consulta_s": r.get("duracao_consulta_s")})
    if "erro_consulta" in r:
        if not isinstance(r["erro_consulta"], str) or "http_status" in r or "http_bruto" in r:
            raise ValueError("consulta contraditoria")
        dec = {"finalizacao": "nao_confirmada"}
    else:
        dec = anterior.schema.decodificar_http(r.get("http_status"), r.get("http_bruto"))
    conf = anterior.papel.conferir_papel(caso, primeira["entrada_host"], dec.get("proposta"))
    shape = dec["finalizacao"] == "concluida" and conf["estado"] == "papel_proposto_revisao_pendente"
    certo = bool(shape and conf["papel_proposto"] == caso["papel"])
    return {**vazio, "interpretacao": dec, "shape": shape, "papel_alinhado": certo,
            "papel_proposto": conf["papel_proposto"],
            "conjunto_discriminativo_local": certo and a["selecao_discriminativa_local"]}


def sequencia(casos: list[dict]) -> list[tuple[dict, int, tuple[str, ...]]]:
    primeira = [(c, MODOS if i % 2 == 0 else MODOS[::-1]) for i, c in enumerate(casos)]
    return [(c, rep, ordem if rep == 1 else ordem[::-1]) for rep in (1, 2)
            for c, ordem in (primeira if rep == 1 else primeira[::-1])]


def resumir(blocos: list[dict]) -> dict:
    cs = carregar_painel()
    invalido = {**BASE, "tipo": "resumo_invalido"}
    if not isinstance(blocos, list) or len(blocos) != len(cs)*2:
        return invalido
    aferidos = {}
    try:
        for b, (c, rep, ordem) in zip(blocos, sequencia(cs), strict=True):
            if (b["id"] != c["id"] or type(b["repeticao"]) is not int or b["repeticao"] != rep
                    or b["ordem"] != list(ordem) or b["primeira"]["repeticao"] != rep
                    or set(b["segundas"]) != set(MODOS)):
                raise ValueError("bloco divergente")
            aferidos[c["id"], "conjunto", rep] = conferir_primeira(c,b["primeira"])
            for m in MODOS:
                aferidos[c["id"], m, rep] = aferir_papel(c,b["primeira"],b["segundas"][m])
    except (ValueError, TypeError, KeyError, OverflowError):
        return invalido
    return {**BASE, "tipo": "resumo_papel_apos_selecao", "blocos": len(blocos),
            "bracos": {m: {str(rep): {k: sum(aferidos[c["id"],m,rep][k] for c in cs)
                for k in ("shape","papel_alinhado","conjunto_discriminativo_local")} for rep in (1,2)}
                for m in ("conjunto",*MODOS)}, "runtime_laylay": False, "holdout_novo": False}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--saida",type=Path,required=True)
    args=p.parse_args(); cs=carregar_painel()
    digest=anterior.etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True,exist_ok=True)
    with args.saida.open("x",encoding="utf-8") as arq:
        def escrever(r:dict)->None:
            arq.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+"\n"); arq.flush()
        escrever({**BASE,"tipo":"metadata","casos_pre_consulta":cs,"digest_inicio":digest,
            "hash_script":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"hash_selecao":HASH_SELECAO,
            "head":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "branch":subprocess.check_output(["git","branch","--show-current"],text=True).strip(),
            "worktree":subprocess.check_output(["git","status","--short"],text=True).splitlines(),
            "ordem":[[c["id"],rep,list(o)] for c,rep,o in sequencia(cs)],"runtime_laylay":False})
        bs=[]
        for c,rep,ordem in sequencia(cs):
            primeira=selecao.medir_caso(c,"catalogado",rep)
            b={"id":c["id"],"repeticao":rep,"ordem":list(ordem),"primeira":primeira,"segundas":{}}
            for m in ordem:
                b["segundas"][m]=medir_papel(c,primeira,m)
            escrever(b);bs.append(b)
            print(json.dumps({"id":c["id"],"rep":rep,"primeira":conferir_primeira(c,primeira)["papel_proposto"],
                **{m:aferir_papel(c,primeira,r)["papel_proposto"] for m,r in b["segundas"].items()}}),flush=True)
        resumo=resumir(bs)
        try:
            resumo["digest_final"]=anterior.etapas.coordenadas.digest_modelo()
            resumo["modelo_igual_entre_leituras"]=resumo["digest_final"]==digest
        except Exception as erro:
            resumo.update(erro_digest_final=type(erro).__name__,modelo_igual_entre_leituras=False)
        escrever(resumo);print(json.dumps(resumo),flush=True)


if __name__=="__main__":
    main()
