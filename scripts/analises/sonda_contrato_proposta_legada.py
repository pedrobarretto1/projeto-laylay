"""Ablação de contrato operacional no HTTP congelado, sem alterar produção.

Consulta só o Ollama escolhido, reutilizando payloads reais já coletados.
Compara controle, nomes registrados e formato/params derivados do dispatcher.
Não usa gold para construir prompts, não chama executor nem valida autoridade.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from functools import lru_cache
from pathlib import Path
import subprocess

import requests

from scripts.analises.sonda_escopo_geracao_real import (
    comparar_escopos, criar_guarda_http_local, selecao_local,
)
from scripts.analises.sonda_escopo_propostas_mistas import RAIZ
from mente_laylay.autonomia.dispatcher_comandos_json import adaptar_acao_json_para_intencao
from mente_laylay.especialistas.capacidades import CAPACIDADES
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime

MODOS = ("controle", "nomes", "parametros")
IDS = ("dominios_distintos_consulta", "dominios_distintos_condicao",
       "mesmo_intent_operacoes", "mesmo_intent_alvos",
       "controle_consulta_isolada", "controle_conjunto_legitimo")


@lru_cache(maxsize=1)
def aliases_documentais_apps() -> dict:
    """Lê o literal do owner, sem importar/main nem presumir app instalado."""
    arvore = ast.parse((RAIZ / "laylay.py").read_text(encoding="utf-8-sig"))
    blocos = [n.value for n in arvore.body if isinstance(n, ast.Assign)
              and any(isinstance(a, ast.Name) and a.id == "APPS_MAP" for a in n.targets)]
    if len(blocos) != 1:
        raise ValueError("APPS_MAP deixou de ser um literal único; não inventar aliases")
    valor = ast.literal_eval(blocos[0])
    if not isinstance(valor, dict):
        raise ValueError("APPS_MAP não documental")
    return valor


def exemplos_do_adaptador() -> list[dict]:
    """Representações ilustrativas, não interpretação da frase ou receipt.

    Cobertura deliberadamente parcial: não inventar schema de domínios cujo
    adaptador legado não fornece parâmetros. Nunca promover isto a catálogo.
    """
    sementes = (
        {"acao": "open_app", "app": "<programa>"},
        {"acao": "close_app", "app": "<programa>"},
        {"acao": "youtube_control", "command": "<operacao>"},
        {"acao": "youtube_search", "query": "<busca musical>"},
        {"acao": "open_url", "url": "<url>"},
        {"acao": "ligar", "dispositivo": "<dispositivo>"},
    )
    exemplos = []
    for semente in sementes:
        comando = adaptar_acao_json_para_intencao(semente, compactar_aliases=True)
        if comando is None or comando["intent"] not in CAPACIDADES:
            raise ValueError("exemplo não derivou de capacidade canônica")
        exemplos.append(comando)
    return exemplos


def instrucao(texto: str, modo: str) -> str:
    if modo not in MODOS:
        raise ValueError("modo inválido")
    if modo == "controle":
        return ""
    dominios = MapaHabilidadesRuntime(apps_getter=aliases_documentais_apps).dominios_relevantes(texto)
    nomes = sorted(i for i, c in CAPACIDADES.items() if c["dominio"] in dominios)
    cabecalho = (
        "CONTRATO DOCUMENTAL DE PROPOSTA, NÃO É AUTORIZAÇÃO NEM RECEIPT.\n"
        "Nomes registrados dos domínios mencionados (disponibilidade continua no mapa vivo): "
        + json.dumps(nomes, ensure_ascii=False)
        + ". Não invente nomes de comandos.\n"
    )
    if modo == "nomes":
        return cabecalho
    exemplos = [c for c in exemplos_do_adaptador() if c["intent"] in nomes]
    return cabecalho + (
        'Cada proposta em comandos usa {"intent":"NOME_REGISTRADO","params":{...}}. '
        "Exemplos estruturais do adaptador, com placeholders que devem ser substituídos "
        "pelos dados do pedido, nunca copiados como alvos: "
        + json.dumps(exemplos, ensure_ascii=False, separators=(",", ":"))
        + ". Não inclua sucesso, executado ou confirmação nos comandos; o executor fornece isso. "
        "O formato não autoriza ação. Pergunta sobre significado, relato e condição futura "
        "não viram comandos. Proponha somente as ações pedidas agora; sem pedido, comandos=[]."
    )


def preparar_payload(payload: dict, texto: str, modo: str) -> dict:
    novo = deepcopy(payload)
    extra = instrucao(texto, modo)
    if extra:
        mensagens = novo["messages"]
        indice = next(i for i in range(len(mensagens) - 1, -1, -1)
                      if mensagens[i]["role"] == "user")
        # Manter toda a instrução efêmera existente; não substituir contrato
        # de fala/receipts. Replay pós-compactação, não prova do preparador.
        if indice and mensagens[indice - 1]["role"] == "system":
            mensagens[indice - 1]["content"] += "\n\n" + extra
        else:
            mensagens.insert(indice, {"role": "system", "content": extra})
    return novo


def medir_http(registro: dict, esperados: list[dict]) -> dict:
    medida = {"json_valido": False, "finalizacao": "nao_confirmada",
              "proposta_completa_equivalente": False}
    if registro.get("status") != 200:
        return medida
    try:
        escolha = json.loads(registro["resposta_http"])["choices"][0]
        medida["finalizacao"] = escolha["finish_reason"]
        bruto = escolha["message"]["content"]
        medida["resposta_bruta"] = bruto
        objeto = json.loads(bruto)
        if not isinstance(objeto, dict) or not isinstance(objeto.get("comandos"), list):
            return medida
        medida.update(json_valido=True, comandos=deepcopy(objeto["comandos"]))
        comparacao = comparar_escopos(esperados, objeto["comandos"])
        medida.update(comparacao)
        medida["proposta_completa_equivalente"] = (
            medida["finalizacao"] == "stop" and not any(comparacao.values())
        )
    except (ValueError, KeyError, TypeError, IndexError):
        pass
    return medida


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonte", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    fonte, destino = args.fonte.resolve(), args.saida.resolve()
    resultados_dir = (RAIZ / "resultados_testes").resolve()
    if (not fonte.is_relative_to(resultados_dir) or not destino.is_relative_to(resultados_dir)
            or not fonte.is_file() or destino.exists()):
        parser.error("fonte existente e saída nova dentro de resultados_testes")
    selecao = selecao_local()
    dados = json.loads(fonte.read_text(encoding="utf-8"))
    if dados.get("selecao_persistida") != selecao or dados.get("fontes_estaveis") is not True:
        parser.error("fonte não estável ou seleção divergente")
    casos = {r["caso"]["id"]: r for r in dados["resultados"]}
    if any(i not in casos for i in IDS):
        parser.error("painel incompleto")
    fontes = [Path(__file__), fonte, RAIZ / "laylay.py", RAIZ / "mente_laylay/autonomia/dispatcher_comandos_json.py",
              RAIZ / "mente_laylay/especialistas/capacidades.py",
              RAIZ / "mente_laylay/especialistas/mapa_habilidades.py",
              RAIZ / "mente_laylay/cognicao/escopo_autorizacao.py",
              RAIZ / "scripts/analises/sonda_escopo_geracao_real.py", RAIZ / "configuracao.env"]
    def hashes():
        return {str(p.relative_to(RAIZ)): hashlib.sha256(p.read_bytes()).hexdigest() for p in fontes}
    antes = hashes()
    base = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=RAIZ, text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], cwd=RAIZ, text=True)}
    from mente_laylay.integracao.instancia_unica import adquirir_instancia_unica
    instancia = adquirir_instancia_unica(RAIZ / "laylay.py")
    if not instancia.adquirida:
        print("Laylay aberta: nenhuma sessão interrompida, sonda não iniciada.")
        return 73
    registros = []
    sessao = requests.Session()
    transportes = []
    http = criar_guarda_http_local(selecao, transportes, requests.sessions.Session.request)
    try:
        ordem = [(i, modo) for n, i in enumerate(IDS)
                 for modo in (MODOS if n % 2 == 0 else MODOS[::-1])]
        for repeticao in (1, 2):
            for ident, modo in (ordem if repeticao == 1 else ordem[::-1]):
                caso = casos[ident]["caso"]
                original = casos[ident]["transportes"][0]
                payload = preparar_payload(original["payload"], caso["texto"], modo)
                inicio = len(transportes)
                try:
                    http(sessao, method="POST", url=original["url"], json=payload, timeout=90)
                except requests.RequestException:
                    pass
                if len(transportes) != inicio + 1:
                    raise RuntimeError("chamada não registrada pela guarda")
                registro = transportes[-1]
                registros.append({"id": ident, "modo": modo, "repeticao": repeticao,
                    "caso": deepcopy(caso), "transporte": registro,
                    "medida": medir_http(registro, caso["esperados"])})
                print(f"{repeticao} {ident} {modo}: "
                      f"equivalente={registros[-1]['medida']['proposta_completa_equivalente']}", flush=True)
        depois = hashes()
        resumo = {modo: {
            "chamadas": sum(r["modo"] == modo for r in registros),
            "http_200": sum(r["modo"] == modo and r["transporte"].get("status") == 200 for r in registros),
            "json_validos": sum(r["modo"] == modo and r["medida"]["json_valido"] for r in registros),
            "propostas_completas_equivalentes": sum(r["modo"] == modo and r["medida"]["proposta_completa_equivalente"] for r in registros),
        } for modo in MODOS}
        relatorio = {**base, "instante_utc": datetime.now(timezone.utc).isoformat(),
            "selecao_persistida": selecao, "fonte_congelada": str(fonte.relative_to(RAIZ)),
            "hashes_antes": antes, "hashes_depois": depois, "fontes_estaveis": antes == depois,
            "registros": registros, "resumo": resumo, "holdout": False,
            "runtime_main_validado": False, "efeitos_externos_executados": False,
            "autoridade_validada": False, "voz_validada": False,
            "limite": "replay HTTP pós-compactação; geração não atravessa preparador, validador ou dispatcher; cobertura parcial de exemplos"}
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("x", encoding="utf-8") as arquivo:
            json.dump(relatorio, arquivo, ensure_ascii=False, indent=2)
        print(json.dumps(resumo, ensure_ascii=False))
        return int(antes != depois or any(r["transporte"].get("status") != 200 for r in registros))
    finally:
        sessao.close()
        instancia.liberar()


if __name__ == "__main__":
    raise SystemExit(main())
