"""Arena manual: compara o modelo ativo com a candidata v18 sem executar ações."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from mente_laylay.neural.modelo import carregar_modelo
ATIVO = RAIZ / "memoria" / "neural" / "modelo_ativo.joblib"
V18 = (
    RAIZ
    / "memoria"
    / "neural"
    / "experimentos"
    / "hibrido_v26_v17_overlay_volume_gate_numeros_v1_20260923"
    / "modelo_candidato.joblib"
)
DESTINO = RAIZ / "memoria" / "neural" / "arena_v18" / "feedback_manual.jsonl"


def sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()
def executavel(previsao: dict) -> bool:
    return bool(
        previsao.get("is_command")
        and not previsao.get("negated")
        and not (
            previsao.get("ood")
            and previsao.get("ood_calibrated", True)
        )
    )


def acao(previsao: dict) -> str:
    params = previsao.get("params")
    if isinstance(params, dict) and params.get("acao"):
        return str(params["acao"])
    return str(previsao.get("raw_action") or "")


def resumo(previsao: dict) -> dict:
    return {
        "intent": str(previsao.get("intent") or ""),
        "gate": str(previsao.get("gate_intent") or ""),
        "acao": acao(previsao),
        "is_command": bool(previsao.get("is_command")),
        "executavel": executavel(previsao),
        "negated": bool(previsao.get("negated")),
        "ood": bool(previsao.get("ood")),
        "command_probability": previsao.get("command_probability"),
        "command_head_variant": str(previsao.get("command_head_variant") or ""),
        "intent_head_variant": str(previsao.get("intent_head_variant") or ""),
    }


def mostrar(nome: str, dados: dict) -> None:
    prob = dados.get("command_probability")
    prob_txt = "-" if prob is None else f"{float(prob) * 100:.2f}%"
    print(f"\n[{nome}]")
    print(f"  intent.......... {dados['intent'] or '-'}")
    print(f"  gate............ {dados['gate'] or '-'}")
    print(f"  ação............ {dados['acao'] or '-'}")
    print(f"  comando......... {'SIM' if dados['is_command'] else 'NÃO'}")
    print(f"  executável...... {'SIM' if dados['executavel'] else 'NÃO'}")
    print(f"  prob. comando... {prob_txt}")
    print(f"  negado / OOD.... {dados['negated']} / {dados['ood']}")
    print(f"  head comando.... {dados['command_head_variant'] or 'legado'}")


def registrar(
    texto: str,
    ativo: dict,
    v18: dict,
    escolha: str,
    observacao: str,
    hashes: dict,
) -> None:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    registro = {
        "id": uuid4().hex,
        "ts": datetime.now(timezone.utc).isoformat(),
        "origem": "arena_manual_v18",
        "texto": texto,
        "texto_sha256": hashlib.sha256(texto.casefold().encode("utf-8")).hexdigest(),
        "modelo_ativo_sha256": hashes["ativo"],
        "modelo_v18_sha256": hashes["v18"],
        "ativo": ativo,
        "v18": v18,
        "avaliacao_usuario": escolha,
        "observacao_usuario": observacao.strip()[:1200],
        "apto_treino": False,
        "predicao_propria_vira_label": False,
        "autoriza_execucao": False,
    }
    with DESTINO.open("a", encoding="utf-8", newline="\n") as arq:
        arq.write(json.dumps(registro, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    if not ATIVO.is_file() or not V18.is_file():
        raise FileNotFoundError("Modelo ativo ou candidata v18 não encontrado.")
    modelos = {"ATIVO": carregar_modelo(ATIVO), "V18": carregar_modelo(V18)}
    hashes = {"ativo": sha256(ATIVO), "v18": sha256(V18)}
    print("=" * 62)
    print(" LAYLAY NEURAL ARENA — ATIVO x V18 (SEM EXECUÇÃO)")
    print("=" * 62)
    print(f"ATIVO: {hashes['ativo'][:12]}...")
    print(f"V18:   {hashes['v18'][:12]}...")
    print("Digite 'sair' para encerrar. Nenhuma frase é executada.\n")
    opcoes = {
        "1": "ativo_correto",
        "ativo": "ativo_correto",
        "2": "v18_correto",
        "v18": "v18_correto",
        "3": "ambos_corretos",
        "ambos": "ambos_corretos",
        "4": "ambos_errados",
        "errados": "ambos_errados",
        "5": "ignorar",
        "ignorar": "ignorar",
    }
    while True:
        try:
            texto = input("Você > ").strip().lstrip("\ufeff")
        except EOFError:
            break
        if texto.casefold() in {"sair", "exit", "quit"}:
            break
        if not texto:
            continue
        ativo = resumo(modelos["ATIVO"].prever(texto))
        v18 = resumo(modelos["V18"].prever(texto))
        mostrar("ATIVO", ativo)
        mostrar("V18", v18)
        print("\n1 Ativo correto | 2 V18 correto | 3 Ambos corretos | 4 Ambos errados | 5 Ignorar")
        escolha = ""
        while escolha not in opcoes:
            try:
                escolha = input("Sua avaliação > ").strip()
            except EOFError:
                return
        if escolha != "5":
            try:
                observacao = input(
                    "Observação (o que você queria que acontecesse; 0 = sem observação) > "
                ).strip()
            except EOFError:
                observacao = ""
            if observacao == "0":
                observacao = ""
            registrar(texto, ativo, v18, opcoes[escolha], observacao, hashes)
            if observacao:
                print("✓ avaliação + observação registradas; não entram em treino automático.\n")
            else:
                print("✓ avaliação registrada; não entra em treino automático.\n")
        else:
            print("Ignorado.\n")


if __name__ == "__main__":
    main()
