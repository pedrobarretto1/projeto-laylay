"""Stress test de pragmática derivado da Arena v18; desenvolvimento, não promoção."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from mente_laylay.neural.modelo import carregar_modelo

ATIVO = RAIZ / "memoria/neural/modelo_ativo.joblib"
V18 = RAIZ / "memoria/neural/experimentos/hibrido_v26_v17_overlay_volume_gate_numeros_v1_20260923/modelo_candidato.joblib"
DESTINO = RAIZ / "memoria/neural/experimentos/stress_pragmatica_v1_20260923"


def caso(texto, intent, action, family, *, command=True, negated=False):
    return {
        "text": texto, "intent": intent, "action": action, "is_command": command,
        "negated": negated, "family": family, "development_only": True,
    }


CASOS = [
    caso("o volume está alto demais", "VOLUME", "down", "estado_volume_alto"),
    caso("esse som tá alto demais", "VOLUME", "down", "estado_volume_alto"),
    caso("o áudio ficou muito alto", "VOLUME", "down", "estado_volume_alto"),
    caso("isso aqui tá alto pra caramba", "VOLUME", "down", "estado_volume_alto"),
    caso("tá estourando meu ouvido esse volume", "VOLUME", "down", "estado_volume_alto"),
    caso("o som está forte demais", "VOLUME", "down", "estado_volume_alto"),
    caso("o volume está baixo demais", "VOLUME", "up", "estado_volume_baixo"),
    caso("esse som tá muito baixo", "VOLUME", "up", "estado_volume_baixo"),
    caso("mal dá pra ouvir o áudio", "VOLUME", "up", "estado_volume_baixo"),
    caso("o som ficou baixinho demais", "VOLUME", "up", "estado_volume_baixo"),
    caso("quase não tô ouvindo nada", "VOLUME", "up", "estado_volume_baixo"),
    caso("o volume sumiu de tão baixo", "VOLUME", "up", "estado_volume_baixo"),
    caso("tá muito escuro aqui no quarto", "IOT_CONTROL", "on", "estado_ambiente_escuro"),
    caso("não tô enxergando nada de tão escuro", "IOT_CONTROL", "on", "estado_ambiente_escuro"),
    caso("o quarto ficou escuro demais", "IOT_CONTROL", "on", "estado_ambiente_escuro"),
    caso("tá uma escuridão aqui", "IOT_CONTROL", "on", "estado_ambiente_escuro"),
    caso("não quero essa música, pula ela", "MEDIA_CONTROL", "next", "negacao_escopo"),
    caso("não gostei dessa música, passa pra próxima", "MEDIA_CONTROL", "next", "negacao_escopo"),
    caso("essa eu não quero ouvir, pula", "MEDIA_CONTROL", "next", "negacao_escopo"),
    caso("não quero ficar nessa faixa, próxima", "MEDIA_CONTROL", "next", "negacao_escopo"),
    caso("não quero mais usar o discord, fecha ele", "CLOSE_APP", "close", "negacao_escopo"),
    caso("não quero mais o discord aberto, fecha", "CLOSE_APP", "close", "negacao_escopo"),
    caso("não vou usar mais a steam, pode fechar", "CLOSE_APP", "close", "negacao_escopo"),
    caso("não preciso mais do vscode, fecha ele", "CLOSE_APP", "close", "negacao_escopo"),
    caso("não quero o chrome aberto, fecha pra mim", "CLOSE_APP", "close", "negacao_escopo"),
    caso("não vou mexer mais no spotify, fecha", "CLOSE_APP", "close", "negacao_escopo"),
    caso("seria legal você colocar tim maia", "MUSIC_SEARCH", "search", "pedido_indireto"),
    caso("seria bom ouvir tim maia agora", "MUSIC_SEARCH", "search", "pedido_indireto"),
    caso("eu queria ouvir umas músicas do tim maia", "MUSIC_SEARCH", "search", "pedido_indireto"),
    caso("bem que você podia colocar tim maia", "MUSIC_SEARCH", "search", "pedido_indireto"),
    caso("acho que cairia bem um tim maia agora", "MUSIC_SEARCH", "search", "pedido_indireto"),
    caso("uma música do tim maia seria boa agora", "MUSIC_SEARCH", "search", "pedido_indireto"),
    caso("seria legal abrir a steam", "APP_OPEN", "open", "pedido_indireto_app"),
    caso("bem que você podia abrir o vscode", "APP_OPEN", "open", "pedido_indireto_app"),
    caso("eu queria usar o discord agora", "APP_OPEN", "open", "pedido_indireto_app"),
    caso("tô a fim de abrir a steam", "APP_OPEN", "open", "pedido_indireto_app"),
    caso("seria bom abrir o chrome", "APP_OPEN", "open", "pedido_indireto_app"),
    caso("eu queria entrar no wikipedia", "OPEN_URL", "open", "objetivo_url"),
    caso("preciso pesquisar uma coisa, abre o wikipedia", "OPEN_URL", "open", "objetivo_url"),
    caso("quero consultar o wikipedia", "OPEN_URL", "open", "objetivo_url"),
    caso("vamos pesquisar isso no wikipedia", "OPEN_URL", "open", "objetivo_url"),
    caso("abre o wikipedia que eu preciso pesquisar", "OPEN_URL", "open", "objetivo_url"),
]


def executavel(p):
    return bool(p.get("is_command") and not p.get("negated") and not (p.get("ood") and p.get("ood_calibrated", True)))


def avaliar(modelo, item):
    p = modelo.prever(item["text"])
    action = str((p.get("params") or {}).get("acao") or p.get("raw_action") or "none").casefold()
    campos = {
        "intent": str(p.get("intent") or "NONE").upper(),
        "action": action,
        "is_command": bool(p.get("is_command")),
        "negated": bool(p.get("negated")),
        "executable": executavel(p),
        "gate": str(p.get("gate_intent") or "NONE").upper(),
        "command_probability": p.get("command_probability"),
    }
    esperado_exec = bool(item["is_command"] and not item["negated"])
    checks = {
        "intent": campos["intent"] == item["intent"],
        "action": campos["action"] == item["action"],
        "command": campos["is_command"] == item["is_command"],
        "negation": campos["negated"] == item["negated"],
        "executable": campos["executable"] == esperado_exec,
    }
    return campos, checks


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    modelos = {"ativo": carregar_modelo(ATIVO), "v18": carregar_modelo(V18)}
    resultados = []
    for item in CASOS:
        row = {"caso": item}
        for nome, modelo in modelos.items():
            row[nome], row[nome + "_checks"] = avaliar(modelo, item)
        resultados.append(row)
    resumo = {}
    for nome in modelos:
        checks = Counter()
        por_familia = defaultdict(lambda: Counter(total=0))
        for r in resultados:
            fam = r["caso"]["family"]
            por_familia[fam]["total"] += 1
            for k, ok in r[nome + "_checks"].items():
                checks[k] += int(ok)
                por_familia[fam][k] += int(ok)
            all_ok = all(r[nome + "_checks"].values())
            checks["completo"] += int(all_ok)
            por_familia[fam]["completo"] += int(all_ok)
        resumo[nome] = {"total": len(CASOS), "acertos": dict(checks), "por_familia": {k: dict(v) for k,v in por_familia.items()}}
    (DESTINO / "casos.json").write_text(json.dumps(CASOS, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (DESTINO / "resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (DESTINO / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    print("\nFALHAS V18:")
    for r in resultados:
        if not all(r["v18_checks"].values()):
            erros = [k for k,v in r["v18_checks"].items() if not v]
            print(f"- {r['caso']['family']}: {r['caso']['text']} -> {erros} | {r['v18']}")


if __name__ == "__main__":
    main()
