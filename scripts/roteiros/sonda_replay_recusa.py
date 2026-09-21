"""Compara payloads locais de recusa, sem runtime, aprendizado ou executor.

Os artefatos locais preservam entradas e respostas; podem conter contexto pessoal.
Esta sonda mede geração, não certifica efeitos nem promove um candidato.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import json
from pathlib import Path
import time

import requests

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao, montar_mensagens_reconhecimento_limite


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeticoes", type=int, default=2)
    parser.add_argument("--fase", choices=("ablacao", "ato", "projecao", "contrastes", "candidato"), default="ablacao")
    parser.add_argument("--reavaliar", type=Path, help="Reavalia captura local, sem chamar o modelo")
    args = parser.parse_args()
    if args.reavaliar:
        for linha in args.reavaliar.read_text(encoding="utf-8").splitlines():
            registro = json.loads(linha)
            texto = registro["texto"]
            try:
                fala = json.loads(registro["resposta"]["choices"][0]["message"]["content"]).get("fala", "")
            except (ValueError, AttributeError):
                continue
            turno = classificar_modalidade_turno(texto)
            plano = planejar_turno(texto, turno=turno, mente={})
            plano["contrato_fala"] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente={})
            atual = avaliar_qualidade_comunicacao(texto, fala, plano=plano)
            print(json.dumps(dict(variante=registro["variante"], fala=fala,
                                  antes=registro["avaliacao"]["problemas"], depois=atual["problemas"]),
                             ensure_ascii=False), flush=True)
        return
    raiz = Path(__file__).resolve().parent
    origem = raiz / "resultados_testes/transporte_evidencia-20260914-192126-521220/transporte.jsonl"
    envios = [json.loads(linha)["payload"] for linha in origem.read_text(encoding="utf-8").splitlines()
              if json.loads(linha)["etapa"] == "envio"]
    pasta = raiz / "resultados_testes" / ("replay_recusa-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    pasta.mkdir(exist_ok=False)
    print(f"ARTEFATOS: {pasta}", flush=True)
    indices = (3, 6)
    if args.fase == "candidato":
        textos = (
            "preciso que você não pause a música", "não ligue a lâmpada",
            "não apague o arquivo notas.txt", "não abra a calculadora",
            "preciso que você não feche o navegador", "não liste os programas abertos",
            "eu não perguntei se o Discord está aberto", "eu não perguntei se o Opera está fechado",
            "eu não pedi para abrir o Discord", "não desligue o ventilador",
        )
        base = envios[3]
        envios = [{**copy.deepcopy(base), "messages": [*copy.deepcopy(base["messages"][:-1]),
                   {"role": "user", "content": texto}]} for texto in textos]
        indices = range(len(envios))
    for indice in indices:
        original = envios[indice]
        texto = original["messages"][-1]["content"]
        turno = classificar_modalidade_turno(texto)
        plano = planejar_turno(texto, turno=turno, mente={})
        plano["contrato_fala"] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente={})
        assert not turno["autoriza_execucao"] and not plano.get("comandos")
        for repeticao in range(args.repeticoes):
            variantes = (("capturado", "orcamento_384", "contrato_focado_384")
                         if args.fase == "ablacao" else
                         (("ato_schema_completo", "ato_fala", "direto_fala")
                          if args.fase == "ato" else ("projecao_ato", "projecao_ato_literal")))
            if args.fase == "contrastes":
                variantes = ("contrastes",)
            if args.fase == "candidato":
                variantes = ("candidato",)
            for variante in variantes:
                payload = copy.deepcopy(original)
                if variante != "capturado":
                    payload["max_tokens"] = 384
                if variante == "contrato_focado_384":
                    base = payload["messages"][0]["content"]
                    marcador = "Retorne somente JSON válido"
                    assert marcador in base
                    # Ablação apenas da personalidade longa; mantém contrato,
                    # fala atual e esquema completo, sem fornecer resposta pronta.
                    payload["messages"][0]["content"] = (
                        "Você é Laylay, uma amiga digital. Responda em português brasileiro "
                        "natural, com atenção ao pedido atual. O contrato do turno abaixo "
                        "já identifica o ato e delimita a resposta.\n\n"
                        + base[base.index(marcador):]
                    )
                if args.fase == "ato":
                    base = payload["messages"][0]["content"]
                    instrucao = (
                        "Você é Laylay, uma assistente local. Fale em português brasileiro, "
                        "com naturalidade e atenção ao que o usuário disse. "
                    )
                    if variante != "direto_fala":
                        instrucao += (
                            "Neste turno o usuário delimita sua atuação: recusa uma ação ou "
                            "corrige uma solicitação que não fez. Reconheça essa decisão em "
                            "uma frase curta, com suas palavras. Você deve se abster da ação, "
                            "não manter nem mudar o estado do alvo. Não há informação sobre "
                            "esse estado. Não ofereça outra ação. Isso não é falta de capacidade: "
                            "é respeitar a decisão do usuário. Comandos devem ficar vazios. "
                        )
                    formato = (base[base.index("Retorne somente JSON válido"):]
                               if variante == "ato_schema_completo" else
                               'Retorne somente JSON válido: {"fala":"sua resposta","comandos":[]}.')
                    payload["messages"] = [
                        {"role": "system", "content": instrucao + formato},
                        {"role": "user", "content": texto},
                    ]
                if args.fase == "projecao":
                    ato = "correcao" if turno["modalidade"] == "correcao" else "recusa"
                    tarefa = (
                        "Reconhecer que o usuário não fez aquela pergunta, sem responder à pergunta."
                        if ato == "correcao" else
                        "Reconhecer a decisão do usuário de não autorizar uma ação, comprometendo-se a respeitá-la."
                    )
                    dados_ato = {"ato": ato, "tarefa": tarefa}
                    if variante == "projecao_ato_literal":
                        dados_ato["fala_usuario"] = texto
                    payload["messages"] = [
                        {"role": "system", "content": (
                            "Você é Laylay. Escreva uma resposta breve e natural em português brasileiro "
                            "para realizar o ato descrito. Fale diretamente com o usuário. "
                            "Não narre estados do mundo, ações passadas, motivos ou capacidades; "
                            "não ofereça outras ações. Use suas palavras, sem explicar estas instruções. "
                            'Retorne somente JSON: {"fala":"sua resposta","comandos":[]}.'
                        )},
                        {"role": "user", "content": json.dumps(dados_ato, ensure_ascii=False)},
                    ]
                if args.fase == "contrastes":
                    payload["messages"] = [
                        {"role": "system", "content": (
                            "Você é Laylay. O usuário recusou uma ação ou corrigiu uma pergunta "
                            "que não fez. Reconheça isso em uma única frase curta (até 12 palavras), "
                            "dirigida a ele, em português brasileiro. Respeitar uma recusa é se "
                            "abster, não garantir que o alvo permaneça em algum estado. "
                            "Reconhecer uma pergunta não feita não é respondê-la. "
                            "Não acrescente ações, explicações, estados, ofertas ou desculpas de incapacidade. "
                            'Responda JSON com "fala" e "comandos": [].'
                        )},
                        {"role": "user", "content": "Não envie o documento."},
                        {"role": "assistant", "content": '{"fala":"Certo, não vou enviar o documento.","comandos":[]}'},
                        {"role": "user", "content": "Eu não perguntei se a janela estava aberta."},
                        {"role": "assistant", "content": '{"fala":"Tem razão, você não fez essa pergunta.","comandos":[]}'},
                        {"role": "user", "content": texto},
                    ]
                if args.fase == "candidato":
                    payload["messages"] = montar_mensagens_reconhecimento_limite(texto)
                    payload["max_tokens"] = 256
                inicio = time.perf_counter()
                resposta = requests.post("http://127.0.0.1:11434/v1/chat/completions", json=payload, timeout=90)
                resposta.raise_for_status()
                bruto = resposta.json()
                escolha = bruto["choices"][0]
                conteudo = escolha["message"]["content"]
                try:
                    dados = json.loads(conteudo)
                    completo = isinstance(dados, dict) and {"fala", "comandos", "leitura_turno", "leitura_emocional"} <= dados.keys()
                except (ValueError, TypeError):
                    dados, completo = {}, False
                fala = dados.get("fala", "") if isinstance(dados, dict) else ""
                avaliacao = avaliar_qualidade_comunicacao(texto, fala, plano=plano)
                registro = dict(variante=variante, repeticao=repeticao, texto=texto,
                                payload=payload, resposta=bruto, json_completo=completo,
                                avaliacao=avaliacao, segundos=time.perf_counter() - inicio)
                with (pasta / "comparacao.jsonl").open("a", encoding="utf-8") as arquivo:
                    arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
                print(json.dumps(dict(variante=variante, repeticao=repeticao, texto=texto,
                                      json_completo=completo, fim=escolha.get("finish_reason"), fala=fala,
                                      problemas=avaliacao.get("problemas")), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
