from pathlib import Path
from copy import copy
import json,sys,importlib.util

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))

from mente_laylay.neural.modelo import carregar_modelo,adicionar_extensao_intent_fatorada
from mente_laylay.neural.cabeca_comando_direcionada import adicionar_cabeca_comando_direcionada
from mente_laylay.neural.dataset import carregar_jsonl
from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.neural.avaliacao import avaliar_previsoes

DS=ROOT/"mente_laylay/neural/datasets"
BASE=ROOT/"memoria/neural/experimentos/hibrido_v26_v25_contexto_objetivo_v1_20260924/modelo_candidato.joblib"
LOTS=[
"onda_balanceada_v1.jsonl","musica_natural_modal_v2.jsonl","musica_search_onda_v4.jsonl",
"volume_piloto_v1.jsonl","volume_onda_v2.jsonl","navegador_onda_v1.jsonl",
"apps_arquivos_onda_v1.jsonl","iot_midia_clima_onda_v1.jsonl","shadow_mecanismos_v3.jsonl",
"iot_fronteira_comando_v4.jsonl","negacao_contrastiva_v5.jsonl","fronteiras_comando_v6.jsonl",
"expansao_mecanismos_v7.jsonl","contraste_telegraphico_v8.jsonl","iot_flexoes_imperativo_v5.jsonl",
"iot_luz_imperativo_v6.jsonl","volume_set_absoluto_v7_gate_duplo.jsonl",
"volume_modalidade_comando_v8.jsonl","volume_extremos_action_v7.jsonl"]

def hist():
    cat=intents_registradas();xs=carregar_jsonl(DS/"dev_v0.jsonl",intents_permitidas=cat)
    for n in LOTS: xs.extend(carregar_jsonl(DS/"candidatos"/n,intents_permitidas=cat))
    assert len(xs)==4066
    return xs

def build(rep_domain,rep_request,thr):
    cat=intents_registradas()
    base=carregar_modelo(BASE)
    app=carregar_jsonl(DS/"candidatos/app_jogo_fatorado_v1.jsonl",intents_permitidas=cat)
    allx=[*hist(),*app]
    cand=copy(base)
    cand.extensoes_intent=dict(base.extensoes_intent or {})
    if "IOT_CONTROL::off" in cand.extensoes_intent:
        ext_off=copy(cand.extensoes_intent["IOT_CONTROL::off"])
        ext_off.ativacao="base_intent_off_verb_v1"
        cand.extensoes_intent["IOT_CONTROL::off"]=ext_off
    cand=adicionar_cabeca_comando_direcionada(
        cand,allx,intent="APP_OPEN",
        versao=f"v26-app-head-ext-{rep_domain}-{rep_request}-{thr}",
        somente_pos_extensao=True)
    cand=adicionar_extensao_intent_fatorada(
        cand,app,intent="APP_OPEN",action="open",limiar=thr,
        representacoes_fatores={
            "dominio_app_jogo":rep_domain,
            "pedido_app_open":rep_request,
        },
        ativacao="app_open_signal_v1",
        versao=f"v26-app-ext-{rep_domain}-{rep_request}-{thr}")
    cand.reavaliar_comando_apos_extensao=True
    return cand

def exe(z):
    return bool(z.get("is_command") and not z.get("negated")
                and not(z.get("ood") and z.get("ood_calibrated",True)))
def act(z):
    return str((z.get("params") or {}).get("acao") or z.get("raw_action") or "none").casefold()

PROBES=[
("abre a steam pra mim","APP_OPEN","open",True,False),
("pode abrir a steam por favor","APP_OPEN","open",True,False),
("quero usar a steam agora","APP_OPEN","open",True,False),
("liga a steam pra mim","APP_OPEN","open",True,False),
("quero jogar far cry 5","APP_OPEN","open",True,False),
("abre o far cry 5 pra mim","APP_OPEN","open",True,False),
("coloca far cry 5 pra rodar","APP_OPEN","open",True,False),
("eu queria jogar minecraft agora","APP_OPEN","open",True,False),
("abre o minecraft","APP_OPEN","open",True,False),
("pode ligar a luz do quarto","IOT_CONTROL","on",True,False),
("abre a luz do quarto","IOT_CONTROL","on",True,False),
("abre o google","OPEN_URL","open",True,False),
("quero ouvir rock","MUSIC_SEARCH","search",True,False),
]
CONTROLS=[
"como eu abro a steam?","ontem eu abri a steam","eu gosto da steam",
"amanhã vou usar a steam","como eu jogo far cry 5?","ontem joguei far cry 5",
"amanhã vou jogar minecraft","a steam é uma loja de jogos",
"o far cry 5 é um jogo","não abra a steam","não quero abrir a steam",
]

def ok(m,row):
    t,i,a,c,n=row;z=m.prever(t)
    return (str(z.get("intent") or "NONE").upper()==i and act(z)==a
            and bool(z.get("is_command"))==c and bool(z.get("negated"))==n
            and exe(z)==bool(c and not n))

def main():
    base=carregar_modelo(BASE);rows=[]
    for d,r in (("tfidf","semantico_hibrido_base"),("semantico_hibrido_base","semantico_hibrido_base")):
        for thr in (.80,.85,.88,.90,.925,.95):
            m=build(d,r,thr)
            good=sum(ok(m,x) for x in PROBES)
            bad=sum(exe(m.prever(t)) for t in CONTROLS[:9])
            rows.append({"domain":d,"request":r,"thr":thr,"probe":good,"control_exec":bad})
    rows.sort(key=lambda x:(x["control_exec"],-x["probe"],-x["thr"]))
    print(json.dumps(rows,ensure_ascii=False,indent=2))
    best=rows[0];print("\nBEST",best)
    m=build(best["domain"],best["request"],best["thr"])
    for row in PROBES:
        z=m.prever(row[0]);print(row[0],{"intent":z.get("intent"),"gate":z.get("gate_intent"),
            "action":act(z),"cmd":z.get("is_command"),"neg":z.get("negated"),
            "exe":exe(z),"prob":z.get("command_probability"),"ext":z.get("intent_extension_applied"),
            "scope":z.get("command_head_scope")})
    for dsname in ("frozen_v0.jsonl","dev_v0.jsonl"):
        data=[json.loads(x) for x in (DS/dsname).read_text(encoding="utf-8").splitlines() if x.strip()]
        print("\n",dsname)
        for name,model in (("v25",base),("cand",m)):
            met=avaliar_previsoes(data,[model.prever(x["text"]) for x in data])
            keys=("command_precision","command_recall","false_executable_command_count",
                  "executable_command_precision","executable_command_recall",
                  "missed_executable_command_count","intent_accuracy",
                  "action_accuracy_command","joint_intent_action_accuracy_command")
            print(name,{k:met[k] for k in keys})

if __name__=="__main__":
    main()
