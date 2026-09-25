from pathlib import Path
import ast, hashlib, json, re, sys, unicodedata

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from mente_laylay.neural.modelo import carregar_modelo
from mente_laylay.neural.avaliacao import avaliar_previsoes

V18=ROOT/"memoria/neural/experimentos/hibrido_v26_v17_overlay_volume_gate_numeros_v1_20260923/modelo_candidato.joblib"
V19=ROOT/"memoria/neural/experimentos/hibrido_v26_v18_negacao_escopo_operacional_v1_20260923/modelo_candidato.joblib"
m18,m19=carregar_modelo(V18),carregar_modelo(V19)
report={}
controls=[
    "não fecha o discord",
    "não pula essa música",
    "não aumenta o volume",
    "não quero que você feche o discord",
    "não abre o chrome, por favor",
    "não quero essa música, não pula ela",
    "fecha o discord, não a steam",
]
rows=[]
for t in controls:
    row={"text":t}
    for n,m in (("v18",m18),("v19",m19)):
        z=m.prever(t)
        row[n]={
            "intent":z.get("intent"),
            "command":z.get("is_command"),
            "negated":z.get("negated"),
            "scope":z.get("negation_scope_applied"),
            "neg_conf":(z.get("confidence") or {}).get("negation"),
        }
    rows.append(row)
report["controles"]=rows

for ds in ("frozen_v0.jsonl","dev_v0.jsonl"):
    data=[json.loads(x) for x in (ROOT/"mente_laylay/neural/datasets"/ds).read_text(encoding="utf-8").splitlines() if x.strip()]
    out={}
    for n,m in (("v18",m18),("v19",m19)):
        met=avaliar_previsoes(data,[m.prever(x["text"]) for x in data])
        keys=("command_precision","command_recall","false_executable_command_count",
              "executable_command_precision","executable_command_recall",
              "missed_executable_command_count","intent_accuracy",
              "action_accuracy_command","negation_accuracy")
        out[n]={k:met[k] for k in keys}
    report[ds]=out
texts=set()
for ff in (ROOT/"scripts/tests").rglob("*.py"):
    try:
        tree=ast.parse(ff.read_text(encoding="utf-8"))
    except Exception:
        continue
    for node in ast.walk(tree):
        if not isinstance(node,ast.Constant) or not isinstance(node.value,str):
            continue
        t=" ".join(node.value.strip().split())
        if not (2<=len(t)<=180 and ("," in t or ";" in t)):
            continue
        base=unicodedata.normalize("NFKD",t.casefold())
        base="".join(c for c in base if not unicodedata.combining(c))
        if re.search(r"\bnao\b",base) and re.search(
            r"\b(?:pula|pule|passa|passe|proxima|proximo|fecha|feche|"
            r"abre|abra|toca|toque|coloca|coloque|aumenta|aumente|"
            r"abaixa|abaixe|diminui|diminua)\b",base
        ):
            texts.add(t)

changes=[]
for t in sorted(texts):
    a,b=m18.prever(t),m19.prever(t)
    sig=lambda z:(z.get("intent"),z.get("gate_intent"),z.get("raw_action"),
                  z.get("is_command"),z.get("negated"))
    if sig(a)!=sig(b):
        changes.append({
            "text":t,"v18":sig(a),"v19":sig(b),
            "scope":b.get("negation_scope_applied"),
        })

report["targeted_literal_scan"]={
    "candidate_texts":len(texts),
    "changes":changes,
}
report["active_sha256"]=hashlib.sha256(
    (ROOT/"memoria/neural/modelo_ativo.joblib").read_bytes()
).hexdigest()
out=V19.parent/"validacao_v19_escopo_negacao.json"
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
