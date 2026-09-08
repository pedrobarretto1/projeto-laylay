"""Diagnóstico pareado da fronteira de pedidos, sem executar nem treinar.

A bateria conhecida não é reserva de promoção. O adaptador Python usa o
classificador canônico, não a composição completa (memória/aliases ausentes).
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import (
    autoriza_execucao_efetiva,
    classificar_modalidade_turno,
)

from .avaliacao import avaliar_previsoes
from .runtime import EspecialistaNeuralComandosRuntime


Preditor = Callable[[str], Mapping[str, Any]]


def prever_python_sem_contexto(texto: str) -> dict[str, Any]:
    """Reutiliza o classificador e detector reais, sem chamar um executor."""
    turno = classificar_modalidade_turno(
        texto, texto_tem_comando_explicito=texto_tem_comando_explicito,
        confirmacao_contextual_valida=False,
    )
    return {
        "pedido_operacional": bool(autoriza_execucao_efetiva(turno)),
        "modalidade": turno.get("modalidade"),
        "veto": bool(turno.get("veto_execucao_operacional")),
    }


def criar_preditor_neural(modelo: Any) -> Preditor:
    def prever(texto: str) -> dict[str, Any]:
        previsao = modelo.prever(texto)
        if not isinstance(previsao, Mapping) or any(
            type(previsao.get(chave)) is not bool
            for chave in ("is_command", "negated", "ood")
        ):
            raise ValueError("previsão neural incompleta")
        return {
            # Mesmo critério usado na observação por segmentos; não é o gate
            # de execução, que ainda exige catálogo, risco e autorização.
            "pedido_operacional": EspecialistaNeuralComandosRuntime._comando_executavel(previsao),
            "head_comando": previsao["is_command"],
            "negacao": previsao["negated"],
            "ood": previsao["ood"],
            "intent": previsao.get("intent"),
            "head_comando_bruto": previsao.get("raw_is_command"),
            "veto_comando": previsao.get("command_veto_reason"),
            "probabilidade_comando": previsao.get("command_probability"),
            "limiar_comando": previsao.get("command_threshold"),
        }
    return prever


def _medir(linhas: list[dict[str, Any]], sistema: str) -> dict[str, Any]:
    validas = [x for x in linhas if x[sistema].get("erro") is None]
    esperados = [
        {"is_command": x["esperado"], "training_heads": ["command"]}
        for x in validas
    ]
    metricas = avaliar_previsoes(
        esperados, [{"is_command": x[sistema]["pedido_operacional"]} for x in validas],
    )
    acertos = sum(x[sistema]["pedido_operacional"] == x["esperado"] for x in validas)
    return {
        "total": len(linhas), "previsoes_validas": len(validas),
        "falhas_inferencia": len(linhas) - len(validas), "acertos": acertos,
        # Falha nunca vira negativo correto, nem desaparece do denominador.
        "taxa_acerto_total": acertos / len(linhas) if linhas else None,
        "falsos_pedidos": metricas["false_command_count"],
        "pedidos_perdidos": sum(x["esperado"] and not x[sistema]["pedido_operacional"] for x in validas),
        "precisao_validas": metricas["command_precision"],
        "recall_validas": metricas["command_recall"],
    }


def comparar_pedidos(
    bateria: Mapping[str, Any], *, python: Preditor, neural: Preditor,
) -> dict[str, Any]:
    """Compara ambos com rótulo independente; nunca usa legado como verdade."""
    if bateria.get("treino_permitido") is not False or bateria.get("autoriza_execucao") is not False:
        raise ValueError("bateria precisa proibir treino e execução")
    casos = bateria.get("casos")
    if not isinstance(casos, list) or not casos:
        raise ValueError("bateria vazia ou inválida")
    ids: set[str] = set()
    # Validar tudo antes da primeira inferência: não retornar relatório parcial.
    for caso in casos:
        identidade = caso.get("id")
        esperado = caso.get("esperado", {})
        if not isinstance(identidade, str) or not identidade or identidade in ids:
            raise ValueError("id ausente ou duplicado")
        ids.add(identidade)
        if not isinstance(caso.get("text"), str) or not caso["text"].strip():
            raise ValueError("texto vazio ou inválido")
        if any(type(esperado.get(chave)) is not bool for chave in ("pedido_operacional", "requer_contexto")):
            raise ValueError("rótulos precisam ser booleanos explícitos")
        if caso.get("autoriza_execucao") is not False:
            raise ValueError("caso precisa proibir execução")

    linhas, excluidos = [], []
    for caso in casos:
        if caso.get("contexto") is not None or caso["esperado"]["requer_contexto"]:
            excluidos.append({"id": caso["id"], "motivo": "contexto_fora_do_escopo_v1"})
            continue
        linha = {
            "id": caso["id"], "dominio": caso.get("dominio_da_fatia", "sem_dominio"),
            "fenomeno": caso.get("fenomeno", "sem_fenomeno"),
            "esperado": caso["esperado"]["pedido_operacional"],
        }
        for nome, preditor in (("python", python), ("neural", neural)):
            try:
                # Só o texto chega aos modelos; nunca domínio, ID ou rótulo.
                previsao = dict(preditor(caso["text"]))
                if type(previsao.get("pedido_operacional")) is not bool:
                    raise ValueError("previsão sem booleano explícito")
                linha[nome] = previsao
            except Exception as erro:
                linha[nome] = {"erro": type(erro).__name__}
        if any("erro" in linha[nome] for nome in ("python", "neural")):
            linha["resultado"] = "inconclusivo"
        else:
            p = linha["python"]["pedido_operacional"] == linha["esperado"]
            n = linha["neural"]["pedido_operacional"] == linha["esperado"]
            linha["resultado"] = (
                "ambos_acertam" if p and n else "ambos_erram" if not p and not n
                else "ganho_neural" if n else "regressao_neural"
            )
        linhas.append(linha)
    return {
        "escopo": "diagnostico_pedido_sem_contexto_componentes_reais",
        "promocao_permitida": False, "autoriza_execucao": False,
        "limitacoes": [
            "bateria de desenvolvimento conhecida, não prova de generalização",
            "não mede alvo, intenção correta, efeito ou composição completa",
            "Python sem memória/aliases; rede recebe apenas texto",
            "critério neural da sombra não substitui gate operacional",
        ],
        "total_bateria": len(casos), "excluidos": excluidos,
        "pareado": dict(Counter(x["resultado"] for x in linhas)),
        "metricas": {nome: _medir(linhas, nome) for nome in ("python", "neural")},
        "fatias": {
            eixo: {
                valor: {nome: _medir([x for x in linhas if x[eixo] == valor], nome)
                        for nome in ("python", "neural")}
                for valor in sorted({x[eixo] for x in linhas})
            } for eixo in ("dominio", "fenomeno")
        },
        "casos": linhas,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bateria", type=Path, required=True)
    parser.add_argument("--modelo", type=Path, required=True, help="artefato local confiável")
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    if args.saida.exists():
        parser.error("saída já existe; use novo nome para preservar a evidência")
    from .modelo import carregar_modelo

    bateria_bytes = args.bateria.read_bytes()
    hash_modelo = hashlib.sha256(args.modelo.read_bytes()).hexdigest()
    modelo = carregar_modelo(args.modelo)
    relatorio = comparar_pedidos(
        json.loads(bateria_bytes), python=prever_python_sem_contexto,
        neural=criar_preditor_neural(modelo),
    )
    relatorio["proveniencia"] = {
        "bateria": str(args.bateria), "modelo": str(args.modelo),
        "sha256_bateria": hashlib.sha256(bateria_bytes).hexdigest(),
        "sha256_modelo": hash_modelo, "versao_modelo": modelo.versao,
    }
    raiz = Path(__file__).resolve().parents[2]
    def git(*argumentos: str) -> str:
        return subprocess.check_output(
            ["git", *argumentos], cwd=raiz, text=True, encoding="utf-8",
        ).strip()
    relatorio["proveniencia"].update(
        head=git("rev-parse", "HEAD"), branch=git("branch", "--show-current"),
        worktree=git("status", "--short"),
        sha256_componentes={
            nome: hashlib.sha256((raiz / nome).read_bytes()).hexdigest()
            for nome in (
                "mente_laylay/cognicao/modalidade_turno.py",
                "mente_laylay/autonomia/porteiro_acoes.py",
                "mente_laylay/neural/modelo.py",
                "mente_laylay/neural/runtime.py",
                "mente_laylay/neural/avaliacao.py",
                "mente_laylay/neural/comparacao_linguistica.py",
            )
        },
    )
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        json.dump(relatorio, arquivo, ensure_ascii=False, indent=2)
    print(json.dumps({"pareado": relatorio["pareado"], "metricas": relatorio["metricas"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
