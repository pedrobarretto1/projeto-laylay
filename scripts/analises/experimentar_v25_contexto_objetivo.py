from pathlib import Path
import json, sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))

from mente_laylay.neural.modelo import (
    carregar_modelo, adicionar_overlay_comando_modalidade,
    adicionar_extensao_intent, adicionar_extensao_intent_fatorada,
)
from mente_laylay.neural.dataset import carregar_jsonl
from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.neural.avaliacao import avaliar_previsoes

DS=ROOT/"mente_laylay/neural/datasets"
BASE=ROOT/"memoria/neural/experimentos/hibrido_v26_v24_estado_fatorado_v2_20260923/modelo_candidato.joblib"
LOTS=[
"onda_balanceada_v1.jsonl","musica_natural_modal_v2.jsonl","musica_search_onda_v4.jsonl",
"volume_piloto_v1.jsonl","volume_onda_v2.jsonl","navegador_onda_v1.jsonl",
"apps_arquivos_onda_v1.jsonl","iot_midia_clima_onda_v1.jsonl","shadow_mecanismos_v3.jsonl",
"iot_fronteira_comando_v4.jsonl","negacao_contrastiva_v5.jsonl","fronteiras_comando_v6.jsonl",
"expansao_mecanismos_v7.jsonl","contraste_telegraphico_v8.jsonl","iot_flexoes_imperativo_v5.jsonl",
"iot_luz_imperativo_v6.jsonl","volume_set_absoluto_v7_gate_duplo.jsonl",
"volume_modalidade_comando_v8.jsonl","volume_extremos_action_v7.jsonl"]
def historico():
    cat=intents_registradas()
    xs=carregar_jsonl(DS/"dev_v0.jsonl",intents_permitidas=cat)
    for n in LOTS:
        xs.extend(carregar_jsonl(DS/"candidatos"/n,intents_permitidas=cat))
    assert len(xs)==4066
    return xs

def build(rep_url,thr_url,rep_iot,thr_iot):
    cat=intents_registradas()
    base=carregar_modelo(BASE)
    estado=carregar_jsonl(DS/"candidatos/pragmatica_estado_v2.jsonl",intents_permitidas=cat)
    contexto=carregar_jsonl(DS/"candidatos/pragmatica_contexto_operacional_v1.jsonl",intents_permitidas=cat)
    fatores=carregar_jsonl(DS/"candidatos/pragmatica_contexto_fatorado_v2.jsonl",intents_permitidas=cat)
    url=[x for x in contexto if str(x.get("family","")).startswith(("ctx_url_","goal_url_"))]
    treino=[*historico(),*estado,*contexto]
    cand=adicionar_overlay_comando_modalidade(
        base,treino,intent="OPEN_URL",overlay="pragmatica_contexto_v7_sparse_v1")
    cand=adicionar_overlay_comando_modalidade(
        cand,treino,intent="IOT_CONTROL",overlay="pragmatica_contexto_v7_sparse_v1")
    cand=adicionar_extensao_intent(
        cand,url,intent="OPEN_URL",action="open",
        limiar=thr_url,representacao=rep_url,ativacao="gate_intent_match",
        versao=f"ctx_url_v1_{rep_url}_{thr_url}")
    cand=adicionar_extensao_intent_fatorada(
        cand,fatores,intent="IOT_CONTROL",action="off",
        limiar=thr_iot,
        representacoes_fatores={
            "acao_iot_off":"tfidf",
            "pedido_imediato":rep_iot,
        },
        ativacao="base_intent_match",
        versao=f"ctx_iot_off_fatorado_v2_{rep_iot}_{thr_iot}")
    cand.reavaliar_comando_apos_extensao=True
    return cand
def exe(z):
    return bool(z.get("is_command") and not z.get("negated")
                and not (z.get("ood") and z.get("ood_calibrated",True)))

def action(z):
    return str((z.get("params") or {}).get("acao") or z.get("raw_action") or "none").casefold()

TARGETS=[
    ("eu preciso pesquisar uma coisa no wikipedia","OPEN_URL","open"),
    ("estou com frio, desligue o ventilador","IOT_CONTROL","off"),
    ("quero comer algo, entra no ifood","OPEN_URL","open"),
]
CONTROLS=[
    "como faço para pesquisar no wikipedia?",
    "ontem pesquisei uma coisa no wikipedia",
    "gosto de pesquisar no wikipedia",
    "quando eu precisar pesquisar, abre o wikipedia",
    "estou com frio, como desligo o ventilador?",
    "ontem estava frio e desliguei o ventilador",
    "estou com frio, não desligue o ventilador",
    "ele disse, desligue o ventilador",
    "pode ligar a luz para mim",
    "como eu desligo o ventilador?",
]

def target_ok(m,t,intent,act):
    z=m.prever(t)
    return (str(z.get("intent") or "").upper()==intent and action(z)==act and exe(z))
def metrics_same_or_better(base,cand,dsname):
    data=[json.loads(x) for x in (DS/dsname).read_text(encoding="utf-8").splitlines() if x.strip()]
    mb=avaliar_previsoes(data,[base.prever(x["text"]) for x in data])
    mc=avaliar_previsoes(data,[cand.prever(x["text"]) for x in data])
    keys=("command_precision","command_recall","false_executable_command_count",
          "executable_command_precision","executable_command_recall",
          "missed_executable_command_count","intent_accuracy",
          "action_accuracy_command","joint_intent_action_accuracy_command",
          "negation_accuracy")
    return {k:(mb[k],mc[k]) for k in keys}

def main():
    base=carregar_modelo(BASE)
    rows=[]
    reps=("semantico_hibrido_base",)
    thrs=(0.70,0.80,0.85,0.90,0.925)
    for repu in reps:
        for thru in thrs:
            for repi in reps:
                for thri in thrs:
                    try:m=build(repu,thru,repi,thri)
                    except Exception as e:
                        rows.append({"repu":repu,"thru":thru,"repi":repi,"thri":thri,"error":repr(e)})
                        continue
                    good=sum(target_ok(m,*x) for x in TARGETS)
                    bad=0
                    for t in CONTROLS[:8]:
                        z=m.prever(t)
                        bad+=int(exe(z))
                    rows.append({"repu":repu,"thru":thru,"repi":repi,"thri":thri,
                                 "targets":good,"controls_wrong":bad})
    good=[x for x in rows if "error" not in x]
    good.sort(key=lambda x:(x["controls_wrong"],-x["targets"],-x["thru"],-x["thri"]))
    print(json.dumps(good[:20],ensure_ascii=False,indent=2))
    best=good[0]
    print("\nBEST",json.dumps(best,ensure_ascii=False))
    cand=build(best["repu"],best["thru"],best["repi"],best["thri"])
    print("\nTARGETS")
    for t,i,a in TARGETS:
        z=cand.prever(t)
        print(t,{"intent":z.get("intent"),"gate":z.get("gate_intent"),"action":action(z),
                 "cmd":z.get("is_command"),"exe":exe(z),"prob":z.get("command_probability"),
                 "ext":z.get("intent_extension_applied"),"extp":z.get("intent_extension_probability"),
                 "variant":z.get("command_head_variant")})
    print("\nCONTROLS")
    for t in CONTROLS:
        z=cand.prever(t)
        print(t,{"intent":z.get("intent"),"gate":z.get("gate_intent"),"action":action(z),
                 "cmd":z.get("is_command"),"exe":exe(z),"ext":z.get("intent_extension_applied")})
    print("\nFROZEN",json.dumps(metrics_same_or_better(base,cand,"frozen_v0.jsonl"),ensure_ascii=False))
    print("DEV",json.dumps(metrics_same_or_better(base,cand,"dev_v0.jsonl"),ensure_ascii=False))

if __name__=="__main__":
    main()
