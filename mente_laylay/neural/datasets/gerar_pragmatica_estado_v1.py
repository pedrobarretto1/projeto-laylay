"""Lote contrastivo de estado -> objetivo para áudio e iluminação."""

from __future__ import annotations
import json
from pathlib import Path


def item(texto,intent,action,domain,command,head,family):
    return {
        "text":texto,"intent":intent,"action":action,
        "is_command":command,"negated":False,
        "domain":domain,"family":family,"validation_group":family,
        "source":"MANUAL_PARAPHRASE" if command else "HARD_NEGATIVE",
        "training_heads":["command"],"command_head_intent":head,
    }


def gerar_audio():
    out=[]
    altos=("alto demais","forte demais","bem alto","barulhento")
    baixos=("baixo demais","fraco demais","bem baixo","baixinho")
    for i,nome in enumerate(("volume","som","áudio")):
        for j,estado in enumerate(altos):
            out.append(item(f"o {nome} tá {estado}","VOLUME","down","audio",True,"VOLUME",f"estado_v1_audio_alto_pos_{i}_{j}"))
        for j,estado in enumerate(baixos):
            out.append(item(f"o {nome} tá {estado}","VOLUME","up","audio",True,"VOLUME",f"estado_v1_audio_baixo_pos_{i}_{j}"))
        negativos_altos=(
            f"eu gosto do {nome} alto",
            f"o {nome} estava alto ontem",
            f"como saber se o {nome} está alto?",
            f"o {nome} alto pode incomodar",
            f"o {nome} tá alto, mas não mexe",
        )
        negativos_baixos=(
            f"eu prefiro o {nome} baixo",
            f"o {nome} estava baixo ontem",
            f"como saber se o {nome} está baixo?",
            f"o {nome} baixo economiza energia",
            f"o {nome} tá baixo, mas deixa assim",
        )
        for j,t in enumerate(negativos_altos):
            out.append(item(t,"NONE","none","audio",False,"VOLUME",f"estado_v1_audio_alto_neg_{i}_{j}"))
        for j,t in enumerate(negativos_baixos):
            out.append(item(t,"NONE","none","audio",False,"VOLUME",f"estado_v1_audio_baixo_neg_{i}_{j}"))
    return out
def gerar_luz():
    out=[]
    positivos=(
        "o quarto tá escuro demais",
        "aqui tá muito escuro",
        "o ambiente ficou escuro demais",
        "esse quarto tá uma escuridão",
        "a iluminação aqui tá muito fraca",
        "tá faltando luz aqui no quarto",
        "o quarto ficou escuro",
        "esse ambiente tá escuro",
        "aqui ficou uma escuridão",
        "o quarto tá sem luz",
        "a iluminação tá fraca demais",
        "tá escuro demais nesse ambiente",
    )
    negativos=(
        "eu gosto do quarto escuro",
        "o quarto estava escuro ontem",
        "como deixar o quarto escuro?",
        "o quarto escuro fica bonito",
        "tá escuro aqui, mas não acende a luz",
        "prefiro o ambiente escuro",
        "ontem esse ambiente ficou escuro",
        "por que o quarto fica escuro?",
        "um ambiente escuro ajuda a dormir",
        "deixa o quarto escuro",
        "não quero clarear o quarto",
        "a escuridão do quarto é confortável",
    )
    for i,t in enumerate(positivos):
        out.append(item(t,"IOT_CONTROL","on","iot",True,"IOT_CONTROL",f"estado_v1_luz_pos_{i}"))
    for i,t in enumerate(negativos):
        out.append(item(t,"NONE","none","iot",False,"IOT_CONTROL",f"estado_v1_luz_neg_{i}"))
    return out


def main():
    dados=gerar_audio()+gerar_luz()
    out=Path(__file__).resolve().parent/"candidatos/pragmatica_estado_v1.jsonl"
    out.write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in dados),encoding="utf-8")
    print(json.dumps({
        "total":len(dados),
        "volume_down":sum(x["intent"]=="VOLUME" and x["action"]=="down" for x in dados),
        "volume_up":sum(x["intent"]=="VOLUME" and x["action"]=="up" for x in dados),
        "iot_on":sum(x["intent"]=="IOT_CONTROL" and x["action"]=="on" for x in dados),
        "negatives":sum(not x["is_command"] for x in dados),
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
