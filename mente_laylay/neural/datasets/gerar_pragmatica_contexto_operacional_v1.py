"""Contexto pessoal + ordem posterior e objetivos implícitos de navegação."""

from __future__ import annotations
import json
from pathlib import Path


def item(text, intent, action, domain, command, *, head=None, family=""):
    row={
        "text":text,"intent":intent,"action":action,"domain":domain,
        "is_command":command,"negated":False,"family":family,
        "validation_group":family,
        "source":"MANUAL_PARAPHRASE" if command else "HARD_NEGATIVE",
    }
    if head:
        row["training_heads"]=["command"]
        row["command_head_intent"]=head
    return row


def contexto_iot():
    positivos=[
        ("aqui está gelado, desliga o ventilador","off"),
        ("estou sentindo frio, pode desligar o ventilador","off"),
        ("ficou frio aqui, desligue o ventilador por favor","off"),
        ("agora está frio, apaga o ventilador","off"),
        ("eu estou com frio, pode desligar o ventilador","off"),
        ("tô com frio aqui, desliga o ventilador","off"),
        ("estou com frio agora, pode apagar o ventilador","off"),
        ("com esse frio, desligue o ventilador por favor","off"),
        ("estou com calor, liga o ventilador","on"),
        ("tá abafado aqui, pode ligar o ventilador","on"),
        ("ficou quente no quarto, ligue o ventilador","on"),
        ("aqui está escuro, liga a luz","on"),
    ]
    negativos=[
        "estou com frio, como desligo o ventilador?",
        "ele disse, desligue o ventilador",
        "quando estiver frio, desligue o ventilador",
        "estou com frio, não desligue o ventilador",
        "ontem estava frio e desliguei o ventilador",
        "eu estou com frio e já desliguei o ventilador",
        "estou com frio, mas deixa o ventilador ligado",
        "com esse frio eu queria saber como desligar o ventilador",
        "quero saber como desligar o ventilador",
        "estou com calor, como ligar o ventilador?",
        "ela falou, liga o ventilador",
    ]
    out=[]
    for i,(t,a) in enumerate(positivos):
        out.append(item(t,"IOT_CONTROL",a,"iot",True,head="IOT_CONTROL",family=f"ctx_iot_pos_{i}"))
    for i,t in enumerate(negativos):
        out.append(item(t,"NONE","none","iot",False,head="IOT_CONTROL",family=f"ctx_iot_neg_{i}"))
    return out


def contexto_url():
    positivos=[
        "preciso consultar um assunto, abre o google",
        "quero ver uma página, entra no github",
        "tenho que pesquisar uma coisa, abre o google",
        "quero conferir uma informação, entra no stack overflow",
        "preciso procurar um produto, abre o mercado livre",
        "quero consultar a documentação, entra no github",
        "agora preciso pesquisar, abre o google",
        "tenho uma dúvida, entra no stack overflow",
    ]
    negativos=[
        "preciso pesquisar como abrir o google",
        "eu disse, abre o google",
        "quando eu precisar pesquisar, abre o google",
        "quero saber como entrar no github",
        "ontem eu entrei no google para pesquisar",
        "o google abre páginas rapidamente",
        "preciso pesquisar, não abre o google",
        "ela falou, entra no github",
    ]
    out=[]
    for i,t in enumerate(positivos):
        out.append(item(t,"OPEN_URL","open","browser",True,head="OPEN_URL",family=f"ctx_url_pos_{i}"))
    for i,t in enumerate(negativos):
        out.append(item(t,"NONE","none","browser",False,head="OPEN_URL",family=f"ctx_url_neg_{i}"))
    return out


def objetivo_url():
    positivos=[
        "preciso pesquisar um assunto no google",
        "quero consultar um projeto no github",
        "tenho que procurar uma informação no google",
        "preciso conferir uma resposta no stack overflow",
        "quero pesquisar um produto no mercado livre",
        "tenho que consultar a documentação no github",
        "preciso buscar uma referência no google",
        "quero olhar um repositório no github",
        "tenho uma pesquisa para fazer no google",
        "preciso ver uma página no mercado livre",
    ]
    negativos=[
        "ontem pesquisei um assunto no google",
        "como faço para pesquisar no google?",
        "gosto de pesquisar no google",
        "o github é um site de código",
        "eu usava o stack overflow para pesquisar",
        "pesquisar no google pode ajudar",
        "amanhã vou pesquisar isso no google",
        "quero saber como usar o github",
        "o mercado livre tem muitos produtos",
        "ela pesquisou uma coisa no google",
    ]
    out=[]
    for i,t in enumerate(positivos):
        out.append(item(t,"OPEN_URL","open","browser",True,family=f"goal_url_pos_{i}"))
    for i,t in enumerate(negativos):
        out.append(item(t,"NONE","none","browser",False,family=f"goal_url_neg_{i}"))
    return out


def iot_off_extension():
    positivos=[
        "aqui está gelado, desliga o ventilador",
        "estou sentindo frio, pode desligar o ventilador",
        "ficou frio aqui, desligue o ventilador por favor",
        "agora está frio, apaga o ventilador",
        "o quarto esfriou, desliga o ventilador",
        "estou tremendo de frio, pode desligar o ventilador",
        "eu estou com frio, desliga o ventilador por favor",
        "tô com frio aqui, pode desligar o ventilador",
        "estou com frio agora, apaga o ventilador",
        "com esse frio, pode desligar o ventilador",
    ]
    negativos=[
        "estou com frio, como desligo o ventilador?",
        "ontem senti frio e desliguei o ventilador",
        "estou com frio, não desligue o ventilador",
        "estou com calor, liga o ventilador",
        "quero saber como desligar o ventilador",
        "o ventilador desligado deixa o quarto quieto",
    ]
    out=[]
    for i,t in enumerate(positivos):
        out.append(item(t,"IOT_CONTROL","off","iot",True,family=f"iot_off_ext_pos_{i}"))
    for i,t in enumerate(negativos):
        out.append(item(t,"NONE","none","iot",False,family=f"iot_off_ext_neg_{i}"))
    return out


def gerar():
    return contexto_iot()+contexto_url()+objetivo_url()+iot_off_extension()


def main():
    xs=gerar()
    p=Path(__file__).resolve().parent/"candidatos/pragmatica_contexto_operacional_v1.jsonl"
    p.write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in xs),encoding="utf-8")
    print(json.dumps({
        "total":len(xs),
        "command_targeted":sum("command_head_intent" in x for x in xs),
        "open_url_positive":sum(x["intent"]=="OPEN_URL" for x in xs),
        "iot_off_positive":sum(x["intent"]=="IOT_CONTROL" and x["action"]=="off" for x in xs),
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
