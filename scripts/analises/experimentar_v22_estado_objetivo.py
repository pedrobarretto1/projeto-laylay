from pathlib import Path
from copy import copy
import importlib.util, json, sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from mente_laylay.neural.modelo import (
    carregar_modelo, adicionar_overlay_comando_modalidade,
    adicionar_extensao_intent,
)
from mente_laylay.neural.dataset import carregar_jsonl
from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.neural.avaliacao import avaliar_previsoes

DS=ROOT/"mente_laylay/neural/datasets"
BASE=ROOT/"memoria/neural/experimentos/hibrido_v26_v21_escopo_comando_dedicado_v1_20260923/modelo_candidato.joblib"
LOTS=[
"onda_balanceada_v1.jsonl","musica_natural_modal_v2.jsonl","musica_search_onda_v4.jsonl",
"volume_piloto_v1.jsonl","volume_onda_v2.jsonl","navegador_onda_v1.jsonl",
"apps_arquivos_onda_v1.jsonl","iot_midia_clima_onda_v1.jsonl","shadow_mecanismos_v3.jsonl",
"iot_fronteira_comando_v4.jsonl","negacao_contrastiva_v5.jsonl","fronteiras_comando_v6.jsonl",
"expansao_mecanismos_v7.jsonl","contraste_telegraphico_v8.jsonl","iot_flexoes_imperativo_v5.jsonl",
"iot_luz_imperativo_v6.jsonl","volume_set_absoluto_v7_gate_duplo.jsonl",
"volume_modalidade_comando_v8.jsonl","volume_extremos_action_v7.jsonl"]
def hist():
    cat=intents_registradas()
    xs=carregar_jsonl(DS/"dev_v0.jsonl",intents_permitidas=cat)
    for n in LOTS:
        xs.extend(carregar_jsonl(DS/"candidatos"/n,intents_permitidas=cat))
    assert len(xs)==4066
    return xs

def build(rep,thr):
    cat=intents_registradas()
    base=carregar_modelo(BASE)
    estado=carregar_jsonl(DS/"candidatos/pragmatica_estado_v1.jsonl",intents_permitidas=cat)
    treino=[*hist(),*estado]
    cand=adicionar_overlay_comando_modalidade(
        base,treino,intent="VOLUME",overlay="pragmatica_estado_v6_sparse_v1",
        versao=f"exp-v22-{rep}-{thr}")
    cand=adicionar_overlay_comando_modalidade(
        cand,treino,intent="IOT_CONTROL",overlay="pragmatica_estado_v6_sparse_v1",
        versao=f"exp-v22-{rep}-{thr}")
    for intent,action in (("VOLUME","down"),("VOLUME","up"),("IOT_CONTROL","on")):
        cand=adicionar_extensao_intent(
            cand,estado,intent=intent,action=action,limiar=thr,
            representacao=rep,ativacao="estado_pragmatico_v1",
            versao=f"estado_objetivo_v1_{rep}_{thr}")
    cand.reavaliar_comando_apos_extensao=True
    return cand

def exe(z):
    return bool(z.get("is_command") and not z.get("negated")
                and not (z.get("ood") and z.get("ood_calibrated",True)))

def action(z):
    return str((z.get("params") or {}).get("acao") or z.get("raw_action") or "none").casefold()
def main():
    spec=importlib.util.spec_from_file_location("stress",ROOT/"scripts/analises/analisar_neural_pragmatica_v1.py")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    state=[x for x in mod.CASOS if x["family"].startswith("estado_")]
    controls=[
        ("eu gosto do volume alto",False),("o volume estava alto ontem",False),
        ("como saber se o volume está baixo?",False),
        ("o volume tá alto, mas não mexe",False),
        ("eu prefiro o volume baixo",False),
        ("o quarto escuro fica bonito",False),
        ("eu gosto do quarto escuro",False),
        ("como deixar o quarto escuro?",False),
        ("tá escuro aqui, mas não acende a luz",False),
        ("não quero clarear o quarto",False),
    ]
    configs=[]
    for rep in ("tfidf","semantico_hibrido_base","integral_v1"):
        for thr in (0.80,0.85,0.90,0.925,0.95):
            try:cand=build(rep,thr)
            except Exception as e:
                configs.append({"rep":rep,"thr":thr,"error":repr(e)});continue
            full=0;fam={}
            for x in state:
                z=cand.prever(x["text"])
                ok=(str(z.get("intent") or "NONE").upper()==x["intent"]
                    and action(z)==x["action"] and bool(z.get("is_command"))==x["is_command"]
                    and bool(z.get("negated"))==x["negated"] and exe(z))
                f=fam.setdefault(x["family"],{"ok":0,"total":0});f["total"]+=1;f["ok"]+=int(ok);full+=int(ok)
            bad=sum(int(exe(cand.prever(t))!=exp) for t,exp in controls)
            configs.append({"rep":rep,"thr":thr,"state_complete":full,"state_total":len(state),
                            "controls_wrong":bad,"families":fam})
    print(json.dumps(configs,ensure_ascii=False,indent=2))
    good=[x for x in configs if "error" not in x]
    good.sort(key=lambda x:(x["controls_wrong"],-x["state_complete"],-x["thr"]))
    best=good[0];print("\nBEST",json.dumps(best,ensure_ascii=False))
    cand=build(best["rep"],best["thr"])
    for dsname in ("frozen_v0.jsonl","dev_v0.jsonl"):
        data=[json.loads(x) for x in (DS/dsname).read_text(encoding="utf-8").splitlines() if x.strip()]
        met=avaliar_previsoes(data,[cand.prever(x["text"]) for x in data])
        keys=("command_precision","command_recall","false_executable_command_count",
              "executable_command_precision","executable_command_recall",
              "missed_executable_command_count","intent_accuracy","action_accuracy_command",
              "joint_intent_action_accuracy_command","negation_accuracy")
        print("SET",dsname,{k:met[k] for k in keys})
    critical=[
        "você pode alterar o volume?","como faço para silenciar o áudio?",
        "Para aumentar o volume, você pode dizer 'aumenta o volume'.",
        "é melhor apenas diminuir o volume","deixa o volume em 59 por cento",
        "voce poderia por acaso ligar a luz","como eu ligo a luz?",
        "a luz pode ligar por comando de voz","não quero que acenda nem apague luz nenhuma",
    ]
    print("\nCRITICAL")
    for t in critical:
        z=cand.prever(t)
        print(t,{"intent":z.get("intent"),"action":action(z),"cmd":z.get("is_command"),
                 "exe":exe(z),"prob":z.get("command_probability"),
                 "variant":z.get("command_head_variant"),"ext":z.get("intent_extension_applied")})

if __name__=="__main__":
    main()
