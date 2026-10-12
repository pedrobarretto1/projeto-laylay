"""Transferência congelada: 16 fontes novas + quatro controles históricos."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

from scripts.analises import sonda_papel_apos_selecao_v1 as anterior

BASE = anterior.BASE
HASH_ANTERIOR = "3bf0c5a7a545d5977e03126a548089f0c3f7b3e7874b4f066088a479ec24b7ce"
NOVOS = [
    {"id":"H01","foco_id":"c1","texto":"A palestra tem o título “se eu recalibrasse a balança”, embora a expressão pareça uma hipótese.","papel":"nome_designacao","pista":"tem o título"},
    {"id":"H02","foco_id":"c1","texto":"Uma alteração hipotética é formulada em “se eu recalibrasse a balança”; o ajuste não aconteceu.","papel":"operacao_mencionada","pista":"Uma alteração hipotética é formulada"},
    {"id":"H03","foco_id":"c2","texto":"O programa informa “a oficina denominada 'desate o cordão' termina à tarde”.","papel":"nome_designacao","pista":"a oficina denominada"},
    {"id":"H04","foco_id":"c2","texto":"A ata relata “o instrutor pediu 'desate o cordão' para demonstrar o procedimento”.","papel":"operacao_mencionada","pista":"o instrutor pediu"},
    {"id":"H05","foco_id":"c1","texto":"O brinquedo se chama “alinhe o pêndulo”; no manual, a montadora orientou “alinhe o pêndulo”.","papel":"nome_designacao","pista":"O brinquedo se chama"},
    {"id":"H06","foco_id":"c2","texto":"O brinquedo se chama “alinhe o pêndulo”; no manual, a montadora orientou “alinhe o pêndulo”.","papel":"operacao_mencionada","pista":"a montadora orientou"},
    {"id":"H07","foco_id":"c1","texto":"“a comporta está selada” é o nome do documentário, não uma observação feita sobre uma comporta real.","papel":"nome_designacao","pista":"é o nome do documentário"},
    {"id":"H08","foco_id":"c1","texto":"A mecânica proibiu o movimento ao dizer “não trave o êmbolo”; estamos relatando a orientação.","papel":"operacao_mencionada","pista":"A mecânica proibiu o movimento"},
    {"id":"H09","foco_id":"c2","texto":"O laudo registra “a frase 'o reservatório está turvo' descreve uma condição observada”.","papel":"expressao_sem_operacao","pista":"descreve uma condição observada"},
    {"id":"H10","foco_id":"c1","texto":"O parágrafo anterior menciona um título. Nesta linha, “o reboco permanece seco” descreve o estado da parede.","papel":"expressao_sem_operacao","pista":"descreve o estado da parede"},
    {"id":"H11","foco_id":"c1","texto":"A anotação “o viveiro fica a oeste” informa a localização. Outra linha pede para mover uma bancada.","papel":"expressao_sem_operacao","pista":"informa a localização"},
    {"id":"H12","foco_id":"c1","texto":"“a mangueira não apresenta fissuras” é uma descrição da integridade da peça, sem solicitar conserto.","papel":"expressao_sem_operacao","pista":"é uma descrição da integridade da peça"},
    {"id":"H13","foco_id":"c1","texto":"O recorte não permite decidir se “se eu polisse a lente” era título de capítulo ou hipótese de manutenção.","papel":"indeterminado","pista":"O recorte não permite decidir"},
    {"id":"H14","foco_id":"c2","texto":"A ficha diz “não foi esclarecido se 'não dobre a haste' nomeava um curso ou expressava uma proibição”.","papel":"indeterminado","pista":"não foi esclarecido se"},
    {"id":"H15","foco_id":"c1","texto":"“o verniz está opaco” pode ser nome de uma série ou descrição de uma superfície; faltam dados para escolher a função.","papel":"indeterminado","pista":"faltam dados para escolher a função"},
    {"id":"H16","foco_id":"c1","texto":"Só restou a expressão “encaixe o lacre”. Não sabemos se identificava uma seção do catálogo ou reproduzia um pedido.","papel":"indeterminado","pista":"Não sabemos se"},
]


def carregar_painel() -> list[dict]:
    if hashlib.sha256(Path(anterior.__file__).read_bytes()).hexdigest() != HASH_ANTERIOR:
        raise ValueError("candidata congelada alterada")
    historicos = anterior.carregar_painel()
    antigos = anterior.anterior.carregar_painel()
    conhecidos = historicos + anterior.selecao.painel.carregar_painel() + antigos["demonstracoes"] + antigos["avaliacao"]
    preparar = anterior.anterior.papel.preparar_entrada
    focos_antigos = {preparar(c)["foco"]["texto"].casefold() for c in conhecidos}
    if len(NOVOS) != 16 or len({c["id"] for c in NOVOS}) != 16:
        raise ValueError("cobertura invalida")
    if Counter(c["papel"] for c in NOVOS) != dict.fromkeys(anterior.anterior.papel.PAPEIS, 4):
        raise ValueError("classes desbalanceadas")
    novos = [{**c, "texto": anterior.selecao.PREFIXO + c["texto"] + anterior.selecao.SUFIXO} for c in NOVOS]
    for c in novos:
        e = preparar(c)
        if not e["aspas_sintaticas"]["aspas_coerentes"] or e["foco"]["texto"].casefold() in focos_antigos:
            raise ValueError("fonte invalida ou foco reutilizado")
        if c["pista"] not in [i["texto"] for i in anterior.selecao.catalogar(c)]:
            raise ValueError("referencia nao catalogavel")
    # Cópia JSON para não expor o painel congelado à mutação do chamador.
    return json.loads(json.dumps(novos + [c for c in historicos if c["id"] in ("T03","T04","T11","T14")]))


def sequencia(casos: list[dict]) -> list[tuple[dict,int]]:
    return [(c,rep) for rep in (1,2) for c in (casos if rep==1 else casos[::-1])]


def aferir_bloco(c:dict,b:dict,rep:int)->dict:
    if (not isinstance(b,dict) or b.get("id")!=c["id"] or type(b.get("repeticao")) is not int
            or b["repeticao"]!=rep or b["primeira"]["repeticao"]!=rep
            or b["isolada"].get("modo")!="papel_sem_trecho"):
        raise ValueError("bloco divergente")
    return {"conjunto":anterior.conferir_primeira(c,b["primeira"]),
            "isolado":anterior.aferir_papel(c,b["primeira"],b["isolada"])}


def resumir(bs:list[dict])->dict:
    cs=carregar_painel(); invalido={**BASE,"tipo":"resumo_invalido"}
    if not isinstance(bs,list) or len(bs)!=len(cs)*2:return invalido
    try:
        a={(c["id"],rep):aferir_bloco(c,b,rep) for b,(c,rep) in zip(bs,sequencia(cs),strict=True)}
    except (ValueError,KeyError,TypeError,OverflowError):return invalido
    grupos={"novos":[c for c in cs if c["id"].startswith("H")],"historicos":[c for c in cs if c["id"].startswith("T")]}
    metricas=("shape","papel_alinhado")
    placar={g:{m:{str(rep):{k:sum(a[c["id"],rep][m][k] for c in itens) for k in metricas}
                   for rep in (1,2)} for m in ("conjunto","isolado")} for g,itens in grupos.items()}
    pares={g:{str(rep):{
        "ganhos":[c["id"] for c in itens if not a[c["id"],rep]["conjunto"]["papel_alinhado"] and a[c["id"],rep]["isolado"]["papel_alinhado"]],
        "perdas":[c["id"] for c in itens if a[c["id"],rep]["conjunto"]["papel_alinhado"] and not a[c["id"],rep]["isolado"]["papel_alinhado"]]}
        for rep in (1,2)} for g,itens in grupos.items()}
    return {**BASE,"tipo":"resumo_transferencia_papel_isolado","grupos":placar,"comparacoes":pares,
            "runtime_laylay":False,"revisao_humana_independente":False}


def main()->None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--saida",type=Path,required=True)
    args=p.parse_args();cs=carregar_painel();digest=anterior.anterior.etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True,exist_ok=True)
    with args.saida.open("x",encoding="utf-8") as arq:
        def escrever(r:dict)->None:
            arq.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+"\n");arq.flush()
        escrever({**BASE,"tipo":"metadata","casos_pre_consulta":cs,"digest_inicio":digest,
            "hash_script":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"hash_anterior":HASH_ANTERIOR,
            "head":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "branch":subprocess.check_output(["git","branch","--show-current"],text=True).strip(),
            "worktree":subprocess.check_output(["git","status","--short"],text=True).splitlines(),
            "ordem":[[c["id"],rep] for c,rep in sequencia(cs)],"runtime_laylay":False})
        bs=[]
        for c,rep in sequencia(cs):
            primeira=anterior.selecao.medir_caso(c,"catalogado",rep)
            isolada=anterior.medir_papel(c,primeira,"papel_sem_trecho")
            b={"id":c["id"],"repeticao":rep,"primeira":primeira,"isolada":isolada}
            escrever(b);bs.append(b);a=aferir_bloco(c,b,rep)
            print(json.dumps({"id":c["id"],"rep":rep,**{m:v["papel_proposto"] for m,v in a.items()}}),flush=True)
        resumo=resumir(bs)
        try:
            resumo["digest_final"]=anterior.anterior.etapas.coordenadas.digest_modelo()
            resumo["modelo_igual_entre_leituras"]=resumo["digest_final"]==digest
        except Exception as erro:resumo.update(erro_digest_final=type(erro).__name__,modelo_igual_entre_leituras=False)
        escrever(resumo);print(json.dumps(resumo),flush=True)


if __name__=="__main__":main()
