from pathlib import Path
import json, sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))

from mente_laylay.neural.modelo import carregar_modelo

MODEL=ROOT/"memoria/neural/experimentos/hibrido_v26_v25_contexto_objetivo_v1_20260924/modelo_candidato.joblib"

CASES=[
    # APP_OPEN vs IOT
    ("abre a steam pra mim","APP_OPEN","open",True,False,"app_direto"),
    ("pode abrir a steam por favor","APP_OPEN","open",True,False,"app_modal"),
    ("quero usar a steam agora","APP_OPEN","open",True,False,"app_objetivo"),
    ("liga a steam pra mim","APP_OPEN","open",True,False,"app_verbo_ambigua"),
    ("abre o discord aqui","APP_OPEN","open",True,False,"app_direto"),
    ("pode ligar a luz do quarto","IOT_CONTROL","on",True,False,"iot_luz"),
    ("abre a luz do quarto","IOT_CONTROL","on",True,False,"iot_verbo_ambigua"),
    ("liga o ventilador","IOT_CONTROL","on",True,False,"iot_ventilador"),

    # Jogos como abertura de app/jogo
    ("quero jogar far cry 5","APP_OPEN","open",True,False,"jogo_objetivo"),
    ("abre o far cry 5 pra mim","APP_OPEN","open",True,False,"jogo_direto"),
    ("coloca far cry 5 pra rodar","APP_OPEN","open",True,False,"jogo_rodar"),
    ("eu queria jogar minecraft agora","APP_OPEN","open",True,False,"jogo_objetivo"),
    ("abre o minecraft","APP_OPEN","open",True,False,"jogo_direto"),

    # CLOSE_APP / escopo de negacao
    ("não quero usar mais o discord","CLOSE_APP","close",True,False,"close_desejo_negativo"),
    ("não quero mais a steam aberta","CLOSE_APP","close",True,False,"close_estado_desejado"),
    ("cansei do discord, fecha ele","CLOSE_APP","close",True,False,"close_contexto"),
    ("não fecha o discord","CLOSE_APP","close",True,True,"close_negado"),
    ("não quero que você feche o discord","NONE","none",False,False,"close_recusa"),

    # contexto + ordem
    ("estou com calor, liga o ventilador","IOT_CONTROL","on",True,False,"ctx_iot_on"),
    ("estou cansado dessa música, pula ela","MEDIA_CONTROL","next",True,False,"ctx_media_next"),
    ("preciso pesquisar isso, entra no wikipedia","OPEN_URL","open",True,False,"ctx_url"),
    ("quero comprar comida, entra no ifood","OPEN_URL","open",True,False,"ctx_url"),
]

def exe(z):
    return bool(z.get("is_command") and not z.get("negated")
                and not (z.get("ood") and z.get("ood_calibrated",True)))

def action(z):
    return str((z.get("params") or {}).get("acao") or z.get("raw_action") or "none").casefold()

def main():
    m=carregar_modelo(MODEL)
    rows=[]
    for text,intent,act,cmd,neg,fam in CASES:
        z=m.prever(text)
        expected_exe=bool(cmd and not neg)
        checks={
            "intent":str(z.get("intent") or "NONE").upper()==intent,
            "action":action(z)==act,
            "command":bool(z.get("is_command"))==cmd,
            "negation":bool(z.get("negated"))==neg,
            "executable":exe(z)==expected_exe,
        }
        rows.append({
            "text":text,"family":fam,
            "expected":{"intent":intent,"action":act,"command":cmd,"negated":neg,"executable":expected_exe},
            "actual":{
                "intent":z.get("intent"),"gate":z.get("gate_intent"),"action":action(z),
                "command":bool(z.get("is_command")),"negated":bool(z.get("negated")),
                "executable":exe(z),"prob":z.get("command_probability"),
                "head":z.get("command_head_variant"),"ext":z.get("intent_extension_applied"),
            },
            "checks":checks,"complete":all(checks.values()),
        })
    summary={
        "total":len(rows),
        "complete":sum(r["complete"] for r in rows),
        "by_family":{},
        "failures":[r for r in rows if not r["complete"]],
    }
    for r in rows:
        f=summary["by_family"].setdefault(r["family"],{"total":0,"complete":0})
        f["total"]+=1;f["complete"]+=int(r["complete"])
    out={"summary":summary,"rows":rows}
    dst=MODEL.parent/"probe_v25_adversarial_usuario_style.json"
    dst.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
