from pathlib import Path
import importlib.util, json, sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from mente_laylay.neural.modelo import (
    carregar_modelo, adicionar_overlay_comando_modalidade,
    adicionar_extensao_intent_fatorada,
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
def historico():
    cat=intents_registradas()
    xs=carregar_jsonl(DS/"dev_v0.jsonl",intents_permitidas=cat)
    for n in LOTS:
        xs.extend(carregar_jsonl(DS/"candidatos"/n,intents_permitidas=cat))
    assert len(xs)==4066
    return xs

def build(rep,thr):
    cat=intents_registradas()
    base=carregar_modelo(BASE)
    estado=carregar_jsonl(DS/"candidatos/pragmatica_estado_v2.jsonl",intents_permitidas=cat)
    fatores=carregar_jsonl(DS/"candidatos/pragmatica_estado_fatorado_v3.jsonl",intents_permitidas=cat)
    treino=[*historico(),*estado]
    cand=adicionar_overlay_comando_modalidade(
        base,treino,intent="VOLUME",overlay="pragmatica_estado_v6_sparse_v1")
    cand=adicionar_overlay_comando_modalidade(
        cand,treino,intent="IOT_CONTROL",overlay="pragmatica_estado_v6_sparse_v1")
    specs=(
        ("VOLUME","down",{"dominio_audio":"tfidf","estado_excesso_audio":rep,"pedido_corretivo":rep}),
        ("VOLUME","up",{"dominio_audio":"tfidf","estado_audio_insuficiente":rep,"pedido_corretivo":rep}),
        ("IOT_CONTROL","on",{"dominio_iot":"tfidf","estado_baixa_iluminacao":rep,"pedido_corretivo":rep}),
    )
    for intent,action,reps in specs:
        cand=adicionar_extensao_intent_fatorada(
            cand,fatores,intent=intent,action=action,limiar=thr,
            representacoes_fatores=reps,ativacao="estado_pragmatico_v1",
            versao=f"estado_fatorado_v2_{rep}_{thr}")
    cand.reavaliar_comando_apos_extensao=True
    return cand
def exe(z):
    return bool(z.get("is_command") and not z.get("negated")
                and not (z.get("ood") and z.get("ood_calibrated",True)))
def action(z):
    return str((z.get("params") or {}).get("acao") or z.get("raw_action") or "none").casefold()

def full_ok(m,x):
    z=m.prever(x["text"])
    return (str(z.get("intent") or "NONE").upper()==x["intent"]
            and action(z)==x["action"]
            and bool(z.get("is_command"))==x["is_command"]
            and bool(z.get("negated"))==x["negated"]
            and exe(z)==bool(x["is_command"] and not x["negated"]))

def main():
    spec=importlib.util.spec_from_file_location("stress",ROOT/"scripts/analises/analisar_neural_pragmatica_v1.py")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    state=[x for x in mod.CASOS if x["family"].startswith("estado_")]
    exact=[
        {"text":"o volume ta muito alto","intent":"VOLUME","action":"down","is_command":True,"negated":False},
        {"text":"ta muito baixo o volume","intent":"VOLUME","action":"up","is_command":True,"negated":False},
        {"text":"ta muito escuro o quarto","intent":"IOT_CONTROL","action":"on","is_command":True,"negated":False},
    ]
    controls=[
        "eu gosto do volume alto","o volume estava alto ontem",
        "como saber se o volume está baixo?","o volume tá alto, mas não mexe",
        "eu prefiro o volume baixo","o quarto escuro fica bonito",
        "eu gosto do quarto escuro","como deixar o quarto escuro?",
        "tá escuro aqui, mas não acende a luz","não quero clarear o quarto",
    ]
    rows=[]
    for rep in ("tfidf","integral_v1","semantico_hibrido_base"):
        for thr in (0.50,0.60,0.70,0.80,0.85,0.90):
            try:m=build(rep,thr)
            except Exception as e:
                rows.append({"rep":rep,"thr":thr,"error":repr(e)});continue
            rows.append({
                "rep":rep,"thr":thr,
                "exact":sum(full_ok(m,x) for x in exact),
                "state":sum(full_ok(m,x) for x in state),
                "controls_wrong":sum(exe(m.prever(t)) for t in controls),
            })
    print(json.dumps(rows,ensure_ascii=False,indent=2))
    good=[x for x in rows if "error" not in x]
    good.sort(key=lambda x:(x["controls_wrong"],-x["exact"],-x["state"],-x["thr"]))
    best=good[0]
    print("\nBEST",json.dumps(best,ensure_ascii=False))
    m=build(best["rep"],best["thr"])
    print("\nEXACT")
    for x in exact:
        z=m.prever(x["text"])
        print(x["text"],{"intent":z.get("intent"),"action":action(z),"cmd":z.get("is_command"),
                         "exe":exe(z),"prob":z.get("command_probability"),
                         "ext":z.get("intent_extension_applied"),
                         "extp":z.get("intent_extension_probability"),
                         "factors":z.get("intent_extension_factor_probabilities")})
    for dsname in ("frozen_v0.jsonl","dev_v0.jsonl"):
        data=[json.loads(x) for x in (DS/dsname).read_text(encoding="utf-8").splitlines() if x.strip()]
        met=avaliar_previsoes(data,[m.prever(x["text"]) for x in data])
        keys=("command_precision","command_recall","false_executable_command_count",
              "executable_command_precision","executable_command_recall",
              "missed_executable_command_count","intent_accuracy","action_accuracy_command",
              "joint_intent_action_accuracy_command","negation_accuracy")
        print("SET",dsname,{k:met[k] for k in keys})

if __name__=="__main__":
    main()

