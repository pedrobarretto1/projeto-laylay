"""Arena manual: compara o modelo ativo com a candidata shadow configurada."""

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
CONFIGURACAO = RAIZ / "configuracao.env"
DESTINO = RAIZ / "memoria" / "neural" / "arena" / "feedback_manual.jsonl"


def caminho_candidato_configurado() -> Path:
    if not CONFIGURACAO.is_file():
        raise FileNotFoundError(CONFIGURACAO)
    for linha in CONFIGURACAO.read_text(encoding="utf-8").splitlines():
        if linha.strip().startswith("LAYLAY_NEURAL_MODEL_PATH="):
            valor = linha.split("=", 1)[1].strip()
            if not valor:
                break
            caminho = Path(valor)
            return caminho if caminho.is_absolute() else RAIZ / caminho
    raise RuntimeError("LAYLAY_NEURAL_MODEL_PATH não está configurado.")


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
        "negation_input_variant": str(
            previsao.get("negation_input_variant") or "legado"
        ),
        "negation_scope_applied": bool(
            previsao.get("negation_scope_applied")
        ),
        "ood": bool(previsao.get("ood")),
        "command_probability": previsao.get("command_probability"),
        "command_head_variant": str(previsao.get("command_head_variant") or ""),
        "command_input_variant": str(previsao.get("command_input_variant") or ""),
        "intent_head_variant": str(previsao.get("intent_head_variant") or ""),
        "intent_extension_applied": str(
            previsao.get("intent_extension_applied") or ""
        ),
        "intent_extension_probability": previsao.get(
            "intent_extension_probability"
        ),
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
    if dados["command_input_variant"]:
        print(f"  entrada comando. {dados['command_input_variant']}")
    if dados["intent_extension_applied"]:
        prob_ext = dados.get("intent_extension_probability")
        prob_ext_txt = "-" if prob_ext is None else f"{float(prob_ext) * 100:.2f}%"
        print(
            f"  extensão........ {dados['intent_extension_applied']} "
            f"({prob_ext_txt})"
        )
    if dados["negation_scope_applied"]:
        print(
            "  escopo negação.. "
            f"{dados['negation_input_variant']} (cláusula operacional)"
        )


def registrar(
    texto: str,
    ativo: dict,
    candidato: dict,
    escolha: str,
    observacao: str,
    hashes: dict,
    versao_candidata: str,
) -> None:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    registro = {
        "id": uuid4().hex,
        "ts": datetime.now(timezone.utc).isoformat(),
        "origem": "arena_manual_shadow",
        "texto": texto,
        "texto_sha256": hashlib.sha256(texto.casefold().encode("utf-8")).hexdigest(),
        "modelo_ativo_sha256": hashes["ativo"],
        "modelo_candidato_sha256": hashes["candidato"],
        "modelo_candidato_versao": versao_candidata,
        "ativo": ativo,
        "candidato": candidato,
        "avaliacao_usuario": escolha,
        "observacao_usuario": observacao.strip()[:1200],
        "apto_treino": False,
        "predicao_propria_vira_label": False,
        "autoriza_execucao": False,
    }
    with DESTINO.open("a", encoding="utf-8", newline="\n") as arq:
        arq.write(json.dumps(registro, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    candidato_path = caminho_candidato_configurado()
    if not ATIVO.is_file() or not candidato_path.is_file():
        raise FileNotFoundError("Modelo ativo ou candidata shadow não encontrado.")
    modelos = {
        "ATIVO": carregar_modelo(ATIVO),
        "CANDIDATO": carregar_modelo(candidato_path),
    }
    hashes = {
        "ativo": sha256(ATIVO),
        "candidato": sha256(candidato_path),
    }
    versao_candidata = str(modelos["CANDIDATO"].versao)
    print("=" * 68)
    print(" LAYLAY NEURAL ARENA — ATIVO x CANDIDATO SHADOW (SEM EXECUÇÃO)")
    print("=" * 68)
    print(f"ATIVO:      {hashes['ativo'][:12]}...")
    print(f"CANDIDATO:  {hashes['candidato'][:12]}...  {versao_candidata}")
    print("Digite 'sair' para encerrar. Nenhuma frase é executada.\n")
    opcoes = {
        "1": "ativo_correto",
        "ativo": "ativo_correto",
        "2": "candidato_correto",
        "candidato": "candidato_correto",
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
        candidato = resumo(modelos["CANDIDATO"].prever(texto))
        mostrar("ATIVO", ativo)
        mostrar("CANDIDATO", candidato)
        print(
            "\n1 Ativo correto | 2 Candidato correto | "
            "3 Ambos corretos | 4 Ambos errados | 5 Ignorar"
        )
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
            registrar(
                texto,
                ativo,
                candidato,
                opcoes[escolha],
                observacao,
                hashes,
                versao_candidata,
            )
            if observacao:
                print("✓ avaliação + observação registradas; não entram em treino automático.\n")
            else:
                print("✓ avaliação registrada; não entra em treino automático.\n")
        else:
            print("Ignorado.\n")


if __name__ == "__main__":
    main()
