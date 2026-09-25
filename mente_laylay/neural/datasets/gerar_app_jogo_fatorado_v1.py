"""Contrastes fatorados para APP_OPEN e objetivos de jogo/uso."""

from __future__ import annotations

import json
from pathlib import Path

APPS=("epic games","ubisoft connect","battle net","telegram","krita","blender","obsidian","vlc")
JOGOS=("doom eternal","portal 2","terraria","stardew valley","elden ring","cyberpunk 2077","hollow knight","hades")
IOT=("a luz","o ventilador","o ar condicionado","a tomada")
SITES=("o google","o github","o mercado livre","o stack overflow")
MIDIA=("rock","tim maia","essa música","a playlist de anime")


def row(text,intent,action,domain,is_command,family):
    return {
        "text":text,"intent":intent,"action":action,"domain":domain,
        "is_command":is_command,"negated":False,
        "family":family,"validation_group":family,
        "source":"MANUAL_PARAPHRASE" if is_command else "HARD_NEGATIVE",
    }


def gerar():
    xs=[]
    for i,app in enumerate(APPS):
        pos=(
            f"abre o {app} pra mim",
            f"pode abrir o {app} por favor",
            f"quero usar o {app} agora",
            f"inicia o {app}",
            f"coloca o {app} pra funcionar",
        )
        neg=(
            f"como eu abro o {app}?",
            f"ontem eu abri o {app}",
            f"eu gosto do {app}",
            f"amanhã vou usar o {app}",
        )
        for j,t in enumerate(pos): xs.append(row(t,"APP_OPEN","open","app",True,f"appgame_app_pos_{i}_{j}"))
        for j,t in enumerate(neg): xs.append(row(t,"NONE","none","app",False,f"appgame_app_neg_{i}_{j}"))
    for i,jogo in enumerate(JOGOS):
        pos=(
            f"quero jogar {jogo}",
            f"abre o {jogo} pra mim",
            f"coloca {jogo} pra rodar",
            f"pode iniciar {jogo}",
            f"eu queria jogar {jogo} agora",
        )
        neg=(
            f"como eu abro {jogo}?",
            f"ontem eu joguei {jogo}",
            f"eu gosto de jogar {jogo}",
            f"amanhã vou jogar {jogo}",
        )
        for j,t in enumerate(pos): xs.append(row(t,"APP_OPEN","open","app",True,f"appgame_game_pos_{i}_{j}"))
        for j,t in enumerate(neg): xs.append(row(t,"NONE","none","app",False,f"appgame_game_neg_{i}_{j}"))
    for i,alvo in enumerate(IOT):
        for j,t in enumerate((f"liga {alvo}",f"abre {alvo}",f"pode ligar {alvo}")):
            xs.append(row(t,"IOT_CONTROL","on","iot",True,f"appgame_iot_negdomain_{i}_{j}"))
    for i,alvo in enumerate(SITES):
        for j,t in enumerate((f"abre {alvo}",f"entra no {alvo}",f"quero consultar {alvo}")):
            xs.append(row(t,"OPEN_URL","open","browser",True,f"appgame_url_negdomain_{i}_{j}"))
    for i,alvo in enumerate(MIDIA):
        for j,t in enumerate((f"coloca {alvo}",f"quero ouvir {alvo}",f"toca {alvo}")):
            xs.append(row(t,"MUSIC_SEARCH","search","music",True,f"appgame_music_negdomain_{i}_{j}"))

    for x in xs:
        x["extension_factors"]={
            "dominio_app_jogo": x["domain"]=="app",
            "pedido_app_open": x["intent"]=="APP_OPEN" and bool(x["is_command"]),
        }
    return xs


def main():
    xs=gerar()
    p=Path(__file__).resolve().parent/"candidatos/app_jogo_fatorado_v1.jsonl"
    p.write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in xs),encoding="utf-8")
    print(json.dumps({
        "total":len(xs),
        "app_domain":sum(x["extension_factors"]["dominio_app_jogo"] for x in xs),
        "pedido_open":sum(x["extension_factors"]["pedido_app_open"] for x in xs),
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
