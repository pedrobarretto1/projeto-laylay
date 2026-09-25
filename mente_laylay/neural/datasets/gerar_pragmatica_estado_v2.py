"""Expansão contrastiva de estado inspirada em falas naturais, sem copiar probes."""

from __future__ import annotations
import json
from pathlib import Path
from .gerar_pragmatica_estado_v1 import gerar_audio, gerar_luz, item


def extras_audio():
    out=[]
    for i,nome in enumerate(("volume","som","áudio")):
        altos=(
            f"esse {nome} ficou muito alto",
            f"o {nome} está alto pra caramba",
            f"tá alto demais esse {nome}",
            f"ficou muito forte o {nome}",
        )
        baixos=(
            f"esse {nome} ficou muito baixo",
            f"o {nome} está baixo pra caramba",
            f"tá baixo demais esse {nome}",
            f"ficou muito fraco o {nome}",
        )
        neg_altos=(
            f"eu curto o {nome} muito alto",
            f"ontem o {nome} ficou muito alto",
            f"o {nome} estava muito alto durante o jogo",
            f"mais cedo o {nome} estava alto demais",
            f"como deixar o {nome} muito alto?",
            f"tá alto demais esse {nome}, mas não mexe",
        )
        neg_baixos=(
            f"eu curto o {nome} muito baixo",
            f"ontem o {nome} ficou muito baixo",
            f"o {nome} estava muito baixo durante a chamada",
            f"mais cedo o {nome} estava baixo demais",
            f"como deixar o {nome} muito baixo?",
            f"tá baixo demais esse {nome}, mas deixa assim",
        )
        for j,t in enumerate(altos):
            out.append(item(t,"VOLUME","down","audio",True,"VOLUME",f"estado_v2_audio_alto_pos_{i}_{j}"))
        for j,t in enumerate(baixos):
            out.append(item(t,"VOLUME","up","audio",True,"VOLUME",f"estado_v2_audio_baixo_pos_{i}_{j}"))
        for j,t in enumerate(neg_altos):
            out.append(item(t,"NONE","none","audio",False,"VOLUME",f"estado_v2_audio_alto_neg_{i}_{j}"))
        for j,t in enumerate(neg_baixos):
            out.append(item(t,"NONE","none","audio",False,"VOLUME",f"estado_v2_audio_baixo_neg_{i}_{j}"))
    return out


def extras_luz():
    pos=(
        "o quarto está muito escuro",
        "aqui no quarto tá escuro demais",
        "ficou escuro demais nesse quarto",
        "esse ambiente ficou muito escuro",
        "a iluminação do quarto ficou fraca demais",
        "quase não dá pra enxergar aqui no quarto",
    )
    neg=(
        "eu curto o quarto muito escuro",
        "ontem o quarto ficou muito escuro",
        "como deixar esse quarto muito escuro?",
        "o quarto está muito escuro, mas não acende nada",
        "prefiro esse ambiente bem escuro",
        "a iluminação fraca do quarto me agrada",
    )
    out=[]
    for i,t in enumerate(pos):
        out.append(item(t,"IOT_CONTROL","on","iot",True,"IOT_CONTROL",f"estado_v2_luz_pos_{i}"))
    for i,t in enumerate(neg):
        out.append(item(t,"NONE","none","iot",False,"IOT_CONTROL",f"estado_v2_luz_neg_{i}"))
    return out


def gerar():
    return [*gerar_audio(),*gerar_luz(),*extras_audio(),*extras_luz()]


def main():
    xs=gerar()
    p=Path(__file__).resolve().parent/"candidatos/pragmatica_estado_v2.jsonl"
    p.write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in xs),encoding="utf-8")
    print(json.dumps({"total":len(xs),"extras":len(xs)-78},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
