"""Ablação local de P01. Gera texto; não abre a Laylay nem executa propostas.

Usa uma captura explícita do transporte. Resultados não substituem teste runtime.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess

import requests

from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.personalidade.perfil_amizade import (
    IDENTIDADE_VOZ_LAYLAY, CONTRATO_AMIZADE_PROMPT, CONTRATO_AMIZADE_COMPACTO,
)


TAREFA = (
    "Tarefa de explicação: ensine o caminho para realizar o que foi perguntado. "
    "Se a habilidade está disponível no catálogo, explique como pedir à Laylay, "
    "com um exemplo de pedido relacionado à dúvida; se indisponível, explique o limite. "
    "A utilidade vem primeiro: trate a dúvida com atenção e respeito, sem avaliar "
    "a competência de quem perguntou. Escreva a orientação, não uma ação: comandos=[]."
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captura", type=Path)
    parser.add_argument("--texto", default="como eu poderia pausar a música?")
    parser.add_argument("--sementes", type=int, nargs="+", default=[11, 23, 47])
    parser.add_argument("--grupo", choices=("conteudo", "organizacao", "realizacao"), default="conteudo")
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parent
    captura = args.captura.resolve(strict=True)
    if not captura.is_relative_to((raiz / "resultados_testes").resolve()):
        parser.error("somente captura local em resultados_testes")
    eventos = [json.loads(l) for l in captura.read_text(encoding="utf-8").splitlines()]
    candidatos = [e["payload"] for e in eventos if e.get("etapa") == "envio"
                  and next((m["content"] for m in reversed(e["payload"]["messages"])
                            if m["role"] == "user"), "") == args.texto]
    if len(candidatos) != 1:
        parser.error("exige uma única requisição para a entrada")
    original = candidatos[0]
    if original["model"].casefold() != "qwen3:4b-instruct":
        parser.error("o estudo foi delimitado ao Qwen local usado pela Laylay")
    # Contraste documental: exemplos hoje existentes são por domínio, não por intent.
    cap = MapaHabilidadesRuntime().consultar("MEDIA_CONTROL")
    documento = "\n".join([
        "Documentação da capacidade MEDIA_CONTROL (consulta local, sem executor):",
        f"estado={cap['estado']}; autorização={cap['autorizacao']}",
        "Exemplos de pedidos do domínio música: " + "; ".join(cap["invocacao_natural"]),
        "Evidência: " + cap["evidencia_confirmacao"],
    ])
    pasta = raiz / "resultados_testes" / ("estudo_explicacao-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    pasta.mkdir(parents=True, exist_ok=False)
    meta = {"captura": str(captura), "sha256": hashlib.sha256(captura.read_bytes()).hexdigest(),
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "status": subprocess.check_output(["git", "status", "--short"], text=True),
            "runtime_real": False, "executor": False}
    (pasta / "base.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ARTEFATO:", pasta, flush=True)
    variantes = []
    if args.grupo == "conteudo":
        for nome, adicional in (("original", ""), ("documentacao", documento),
                                ("tarefa", TAREFA), ("documentacao_tarefa", documento + "\n" + TAREFA)):
            candidato = deepcopy(original)
            if adicional:
                candidato["messages"][-2]["content"] += "\n\n" + adicional
            variantes.append((nome, candidato))
    elif args.grupo == "organizacao":
        fundido = deepcopy(original)
        fundido["messages"] = [{"role": "system", "content": "\n\n".join(
            m["content"] for m in original["messages"] if m["role"] == "system")},
            original["messages"][-1]]
        variantes.append(("sistema_unico", fundido))
        compacto = deepcopy(original)
        compacto["messages"][0]["content"] = compacto["messages"][0]["content"].replace(
            CONTRATO_AMIZADE_PROMPT, CONTRATO_AMIZADE_COMPACTO)
        compacto["messages"][-2]["content"] += "\n" + documento + "\n" + TAREFA
        variantes.append(("amizade_compacta", compacto))
        focado = deepcopy(original)
        focado["messages"] = [{"role": "system", "content": (
            IDENTIDADE_VOZ_LAYLAY + "\n" + TAREFA + "\n" + documento
            + '\nResponda somente JSON válido: {"fala":"sua explicação",'
              '"emocao":"calma","nivel_emocao":1,"tipo_interacao":"conversa",'
              '"comandos":[],"aprendizados":[]}')}, original["messages"][-1]]
        variantes.append(("realizacao_focada", focado))
        indisponivel = deepcopy(focado)
        indisponivel["messages"][0]["content"] = indisponivel["messages"][0]["content"].replace(
            "estado=disponivel", "estado=indisponivel; motivo=integração de mídia desconectada")
        variantes.append(("realizacao_indisponivel", indisponivel))
    else:
        sistema = (
            IDENTIDADE_VOZ_LAYLAY + "\n"
            "Você está explicando uma habilidade, não planejando uma execução. "
            "Responda à dúvida em até três frases úteis e respeitosas. "
            "Use a documentação abaixo para explicar como pedir ajuda à Laylay. "
            "Exemplos de pedidos são texto didático, não comandos deste turno. "
            "A disponibilidade descreve a habilidade, não o estado atual de apps ou objetos. "
            "Quando indisponível, explique esse limite; não invente uma rota alternativa. "
            'Devolva somente JSON com o campo fala: {"fala":"sua explicação"}.'
        )
        for exemplos in (False, True):
            for disponivel in (True, False):
                candidato = deepcopy(original)
                candidato["messages"] = [{"role": "system", "content": sistema}]
                if exemplos:
                    candidato["messages"].extend([
                        {"role": "user", "content": 'Documento: habilidade=lembretes; disponível=true; exemplo="me lembre de beber água às 15h".\nDúvida: como eu peço um lembrete?'},
                        {"role": "assistant", "content": '{"fala":"Me diga o que lembrar e quando, por exemplo: ‘me lembre de beber água às 15h’. Esse seria o pedido; por enquanto estou só te explicando."}'},
                        {"role": "user", "content": 'Documento: habilidade=email; disponível=false; motivo=conta desconectada.\nDúvida: como eu consulto meus emails com você?'},
                        {"role": "assistant", "content": '{"fala":"Minha integração de email está desconectada, então a consulta por aqui precisa dessa conexão primeiro. Depois disso posso te ajudar com a leitura."}'},
                    ])
                candidato["messages"].append({"role": "user", "content": (
                    'Documento: habilidade=controle de música; disponível=' + str(disponivel).lower()
                    + ('; exemplo="pausa a música".' if disponivel else '; motivo=integração desconectada.')
                    + '\nDúvida: ' + args.texto)})
                variantes.append((f"fala_{'demonstrada' if exemplos else 'isolada'}_{disponivel}", candidato))
    for nome, candidato in variantes:
        for seed in args.sementes:
            payload = deepcopy(candidato)
            payload["seed"] = seed
            response = requests.post("http://localhost:11434/v1/chat/completions", json=payload, timeout=90)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = {"json_invalido": True, "bruto": content}
            row = {"variante": nome, "seed": seed, "payload": payload, "resposta": data, "parsed": parsed}
            with (pasta / "resultados.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(json.dumps({"variante": nome, "seed": seed, "parsed": parsed}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
