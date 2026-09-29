"""Diagnóstico dos componentes canônicos sobre o painel de relações existente.

Não é o loop de produção: usa getter sintético e transporte Ollama local
explícito, sem estado persistente, tools ou executor. Não decide vigência.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
from typing import Callable

from mente_laylay.cognicao.interpretador_semantico_runtime import InterpretadorSemanticoRuntime
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from scripts.analises.sonda_relacoes_fontes_v2 import carregar_painel, HASHES


def consultar_ollama(mensagens: list[dict], **opcoes: object) -> str:
    """Adaptador somente de transporte; preserva prompt e orçamento do componente."""
    import requests
    resposta = requests.post(
        "http://127.0.0.1:11434/api/chat",
        json={"model": "qwen3:4b-instruct", "stream": False, "format": "json",
              "messages": mensagens,
              "options": {"temperature": 0, "num_predict": opcoes["max_tokens"]}},
        timeout=opcoes["timeout"],
    )
    resposta.raise_for_status()
    return resposta.json()["message"]["content"]


def medir_componentes(caso: dict, *, enviar: Callable[..., str] | None = None) -> dict:
    """Mede entradas/saídas reais dos componentes, sem chamá-las de gabarito."""
    contexto = {"mente": {}, "mensagens": [{"role": "user", "content": caso["alvo"]}]}
    chamadas, logs = [], []

    def transporte(mensagens, **opcoes):
        registro = {"mensagens": mensagens, "opcoes": opcoes}
        chamadas.append(registro)
        try:
            bruto = enviar(mensagens, **opcoes)
            registro["resposta_bruta"] = bruto
            return bruto
        except Exception as erro:
            registro["erro"] = type(erro).__name__
            raise

    componente = InterpretadorSemanticoRuntime(
        contexto_getter=lambda: contexto, enviar_mensagem=transporte,
        modo="shadow", timeout_s=10, log=lambda texto: logs.append(texto),
    )
    falas = []
    for i, texto in enumerate(caso["posteriores"]):
        inicio = time.monotonic()
        legado = classificar_modalidade_turno(texto)
        resumo = componente._resumo_contexto(contexto)
        qtd_antes = len(chamadas)
        leitura = componente.analisar(texto, turno_legado=legado) if enviar is not None else {}
        falas.append({"indice": i, "texto": texto, "modalidade_local": legado,
                      "contexto_disponivel": json.loads(json.dumps(contexto)),
                      "contexto_resumido": resumo, "leitura_semantica": leitura,
                      "chamadas": chamadas[qtd_antes:], "duracao_s": round(time.monotonic()-inicio, 2)})
        contexto["mensagens"].append({"role": "user", "content": texto})
    return {"id": caso["id"], "falas": falas, "logs": logs,
            "aprovado_para_producao": False, "autoriza_efeito": False,
            "pode_registrar_vigencia": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--com-modelo", action="store_true")
    args = parser.parse_args()
    casos, _ = carregar_painel()  # Revisão não é enviada nem usada como classificador.
    from mente_laylay.cognicao import interpretador_semantico_runtime, modalidade_turno
    modulos = [Path(__file__), Path(interpretador_semantico_runtime.__file__), Path(modalidade_turno.__file__)]
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        meta = {"tipo": "metadata", "hashes_painel": HASHES, "com_modelo": args.com_modelo,
                "hashes_codigo": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in modulos},
                "modelo": "qwen3:4b-instruct", "timeout_s": 10, "num_predict": 420,
                "contexto": "sintetico", "runtime_completo": False, "aprovado_para_producao": False}
        arquivo.write(json.dumps(meta, ensure_ascii=False) + "\n")
        arquivo.flush()
        for caso in casos:
            resultado = medir_componentes(caso, enviar=consultar_ollama if args.com_modelo else None)
            arquivo.write(json.dumps(resultado, ensure_ascii=False) + "\n")
            arquivo.flush()
            print(json.dumps({"id": caso["id"], "falas": [{
                "modalidade_local": f["modalidade_local"].get("modalidade_geral"),
                "valida": f["leitura_semantica"].get("valida", False),
                "atos": [a["tipo"] for a in f["leitura_semantica"].get("atos", [])],
                "alvo": f["leitura_semantica"].get("operacional", {}).get("alvo"),
            } for f in resultado["falas"]]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
