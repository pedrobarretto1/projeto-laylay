"""Contrastes para command heads dedicados de mídia e fechamento de apps."""

from __future__ import annotations

import json
from pathlib import Path

APPS_TREINO=("calculadora","paint","firefox","bloco de notas")
APPS_PROBE=("discord","steam","vscode")
MIDIA_TREINO=("essa canção","essa faixa","essa música","esse áudio")
MIDIA_PROBE=("essa música","essa faixa")


def item(texto,intent,domain,positivo,grupo):
    return {
        "text":texto,
        "intent": intent if positivo else "NONE",
        "is_command": positivo,
        "negated": False,
        "action": "next" if intent=="MEDIA_CONTROL" and positivo else "close" if intent=="CLOSE_APP" and positivo else "none",
        "family":f"escopo_comando_operacional_v1_{intent.lower()}_{grupo}",
        "validation_group":f"escopo_comando_operacional_v1_{grupo}",
        "source":"MANUAL_PARAPHRASE" if positivo else "HARD_NEGATIVE",
        "domain":domain,
        "training_heads":["command"],
        "command_head_intent":intent,
    }
def gerar_apps(entidades, prefixo):
    out=[]
    for i,app in enumerate(entidades):
        positivos=(
            f"não vou usar mais o {app}, fecha ele",
            f"não preciso mais do {app}; fecha ele",
            f"não quero mais o {app} aberto, pode fechar",
            f"já terminei no {app}, fecha pra mim",
            f"não fecha o {app}",
        )
        negativos=(
            f"não quero que você feche o {app}",
            f"não quero que feche o {app}",
            f"como eu fecho o {app}?",
            f"quero saber como fechar o {app}",
            f"o {app} pode ser fechado",
        )
        for j,t in enumerate(positivos):
            out.append(item(t,"CLOSE_APP","app",True,f"{prefixo}_app_pos_{i}_{j}"))
        for j,t in enumerate(negativos):
            out.append(item(t,"CLOSE_APP","app",False,f"{prefixo}_app_neg_{i}_{j}"))
    return out
def gerar_midia(entidades,prefixo):
    out=[]
    for i,alvo in enumerate(entidades):
        positivos=(
            f"não quero ouvir {alvo}, pula ela",
            f"não gostei de {alvo}, passa pra próxima",
            f"cansei de {alvo}; próxima",
            f"não vou ouvir {alvo}, pode pular",
            f"não pula {alvo}",
        )
        negativos=(
            f"não quero que você pule {alvo}",
            f"não quero que pule {alvo}",
            f"como eu pulo {alvo}?",
            f"quero saber como pular {alvo}",
            f"{alvo} tem botão de próxima",
        )
        for j,t in enumerate(positivos):
            out.append(item(t,"MEDIA_CONTROL","music",True,f"{prefixo}_media_pos_{i}_{j}"))
        for j,t in enumerate(negativos):
            out.append(item(t,"MEDIA_CONTROL","music",False,f"{prefixo}_media_neg_{i}_{j}"))
    return out
def gerar():
    treino=gerar_apps(APPS_TREINO,"treino")+gerar_midia(MIDIA_TREINO,"treino")
    probe=gerar_apps(APPS_PROBE,"probe")+gerar_midia(MIDIA_PROBE,"probe")
    return treino,probe


def gravar(path,itens):
    path.write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in itens),encoding="utf-8")


def main():
    treino,probe=gerar()
    pasta=Path(__file__).resolve().parent/"candidatos"
    gravar(pasta/"escopo_comando_operacional_v1.jsonl",treino)
    gravar(pasta/"escopo_comando_operacional_v1_probe.jsonl",probe)
    print(json.dumps({
        "treino":len(treino),"probe":len(probe),
        "treino_media":sum(x["command_head_intent"]=="MEDIA_CONTROL" for x in treino),
        "treino_close":sum(x["command_head_intent"]=="CLOSE_APP" for x in treino),
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
