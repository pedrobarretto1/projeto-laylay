"""Transferência offline da interface congelada; sem treino ou promoção."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

from scripts.analises import sonda_hierarquia_identidade_v1 as anterior


BASE = anterior.BASE
MODOS = ("base", "hierarquia")
HASH_ANTERIOR = "5a6612b1df26195f6a6d4a8f2040874789dcd5b24eda14023e4de46c2447adc9"
# Referências locais, nunca enviadas ao proponente. Fontes novas, não curadoria humana.
CASOS = [
    {"id": "T01", "foco_id": "c2", "texto": "A agenda anuncia “o minicurso chamado 'torça o arame' começa na terça”.", "papel": "nome_designacao", "pista": "o minicurso chamado"},
    {"id": "T02", "foco_id": "c2", "texto": "A transcrição informa “a artesã recomendou 'torça o arame' durante a demonstração”.", "papel": "operacao_mencionada", "pista": "a artesã recomendou"},
    {"id": "T03", "foco_id": "c1", "texto": "Embora pareça uma condição, “se eu nivelasse o terreno” é o título do ensaio, não uma tarefa.", "papel": "nome_designacao", "pista": "é o título do ensaio"},
    {"id": "T04", "foco_id": "c1", "texto": "Uma intervenção hipotética é expressa por “se eu nivelasse o terreno”; ninguém a realizou.", "papel": "operacao_mencionada", "pista": "Uma intervenção hipotética é expressa por"},
    {"id": "T05", "foco_id": "c1", "texto": "O quadro recebeu o nome “costure a nuvem”; ao fim da aula, a professora pediu “costure a nuvem”.", "papel": "nome_designacao", "pista": "recebeu o nome"},
    {"id": "T06", "foco_id": "c2", "texto": "O quadro recebeu o nome “costure a nuvem”; ao fim da aula, a professora pediu “costure a nuvem”.", "papel": "operacao_mencionada", "pista": "a professora pediu"},
    {"id": "T07", "foco_id": "c1", "texto": "“não esmague a pétala” consta como nome da instalação, embora soe como uma proibição.", "papel": "nome_designacao", "pista": "consta como nome da instalação"},
    {"id": "T08", "foco_id": "c1", "texto": "O florista proibiu a operação ao dizer “não esmague a pétala”; a frase não identifica uma obra.", "papel": "operacao_mencionada", "pista": "O florista proibiu a operação"},
    {"id": "T09", "foco_id": "c2", "texto": "O arquivo registra “faltam os dados que permitiriam saber se 'desdobre a vela' era nome ou orientação”.", "papel": "indeterminado", "pista": "faltam os dados que permitiriam saber"},
    {"id": "T10", "foco_id": "c1", "texto": "Pode ser título ou instrução: “resfrie o esmalte”. O registro não esclarece qual dessas funções tinha.", "papel": "indeterminado", "pista": "O registro não esclarece"},
    {"id": "T11", "foco_id": "c1", "texto": "A função de “se eu trocasse a dobradiça” não foi identificada: título de conto ou hipótese de reparo são possibilidades em aberto.", "papel": "indeterminado", "pista": "não foi identificada"},
    {"id": "T12", "foco_id": "c2", "texto": "A anotação diz “não há contexto para classificar 'afaste o cavalete' como nome ou pedido”.", "papel": "indeterminado", "pista": "não há contexto para classificar"},
    {"id": "T13", "foco_id": "c2", "texto": "O boletim relata “a expressão 'a argamassa está úmida' descreve o estado do material”.", "papel": "expressao_sem_operacao", "pista": "descreve o estado do material"},
    {"id": "T14", "foco_id": "c1", "texto": "“a janela tem duas folhas” descreve a composição da janela, sem instruir uma alteração.", "papel": "expressao_sem_operacao", "pista": "descreve a composição da janela"},
    {"id": "T15", "foco_id": "c1", "texto": "A frase “o canteiro fica ao norte” informa uma localização. Depois, alguém pediu para deslocar o vaso.", "papel": "expressao_sem_operacao", "pista": "informa uma localização"},
    {"id": "T16", "foco_id": "c1", "texto": "Apesar de haver um pedido de ajuste na página, “o ponteiro está imóvel” é uma descrição do estado observado.", "papel": "expressao_sem_operacao", "pista": "é uma descrição do estado observado"},
]


def carregar_painel() -> list[dict]:
    if hashlib.sha256(Path(anterior.__file__).read_bytes()).hexdigest() != HASH_ANTERIOR:
        raise ValueError("dependencia congelada alterada")
    antigos = anterior.anterior.carregar_painel()
    conhecidos = antigos["demonstracoes"] + antigos["avaliacao"]
    proibidos = {anterior.anterior.papel.preparar_entrada(c)["foco"]["texto"].casefold() for c in conhecidos}
    if len(CASOS) != 16 or len({c["id"] for c in CASOS}) != 16:
        raise ValueError("identidade ou cobertura divergente")
    if Counter(c["papel"] for c in CASOS) != dict.fromkeys(anterior.anterior.papel.PAPEIS, 4):
        raise ValueError("classes desbalanceadas")
    for c in CASOS:
        e = anterior.anterior.papel.preparar_entrada(c)
        if not e["aspas_sintaticas"]["aspas_coerentes"] or e["foco"]["texto"].casefold() in proibidos:
            raise ValueError("fonte invalida ou foco reutilizado")
        v = anterior.anterior.anterior.materializar_vinculo(c, e, {"papel": c["papel"], "predicado": c["pista"]})
        if not v["vinculo_estrutural_valido"]:
            raise ValueError("referencia literal invalida: " + c["id"])
    return deepcopy(CASOS)


def sequencia(casos: list[dict]) -> list[tuple[dict, str, int]]:
    primeira = [(c, m) for i, c in enumerate(casos) for m in (MODOS if i % 2 == 0 else MODOS[::-1])]
    return [(c, m, rep) for rep in (1, 2) for c, m in (primeira if rep == 1 else primeira[::-1])]


def resumir(rs: list[dict]) -> dict:
    casos = carregar_painel()
    invalido = {**BASE, "tipo": "resumo_invalido"}
    if not isinstance(rs, list) or any(not isinstance(r, dict) for r in rs):
        return invalido
    if [(r.get("id"), r.get("modo"), r.get("repeticao")) for r in rs] != [(c["id"], m, rep) for c, m, rep in sequencia(casos)]:
        return invalido
    ix = {c["id"]: c for c in casos}
    try:
        aferidos = {(r["id"], r["modo"], r["repeticao"]): anterior.aferir_caso(ix[r["id"]], r) for r in rs}
    except (ValueError, TypeError, KeyError, OverflowError):
        return invalido
    bracos = {m: {str(rep): {k: sum(aferidos[c["id"], m, rep][k] for c in casos)
                            for k in anterior.anterior.METRICAS} for rep in (1, 2)} for m in MODOS}
    comparacoes = {str(rep): {k: {
        "ganhos": [c["id"] for c in casos if not aferidos[c["id"], "base", rep][k] and aferidos[c["id"], "hierarquia", rep][k]],
        "perdas": [c["id"] for c in casos if aferidos[c["id"], "base", rep][k] and not aferidos[c["id"], "hierarquia", rep][k]]}
        for k in ("papel_alinhado", "conjunto")} for rep in (1, 2)}
    return {**BASE, "tipo": "resumo_transferencia_hierarquia", "consultas": len(rs), "bracos": bracos,
            "comparacoes": comparacoes, "runtime_laylay": False, "revisao_humana_independente": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    casos = carregar_painel()
    digest = anterior.anterior.etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arq:
        def escrever(r: dict) -> None:
            arq.write(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n")
            arq.flush()
        escrever({**BASE, "tipo": "metadata", "casos_pre_consulta": casos,
                  "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "hash_anterior": HASH_ANTERIOR, "digest_inicio": digest,
                  "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                  "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
                  "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
                  "ordem": [(c["id"], m, rep) for c, m, rep in sequencia(casos)],
                  "runtime_laylay": False, "revisao_humana_independente": False})
        rs = []
        for c, m, rep in sequencia(casos):
            r = anterior.medir_caso(c, modo=m, repeticao=rep)
            a = anterior.aferir_caso(c, r)
            rs.append(r)
            escrever({**r, "tipo": "consulta", "afericao": a})
            print(json.dumps({"id": c["id"], "modo": m, "rep": rep, "papel": a["papel_proposto"], "conjunto": a["conjunto"]}), flush=True)
        resumo = resumir(rs)
        try:
            resumo["digest_final"] = anterior.anterior.etapas.coordenadas.digest_modelo()
            resumo["modelo_igual_entre_leituras"] = resumo["digest_final"] == digest
        except Exception as erro:
            resumo.update(erro_digest_final=type(erro).__name__, modelo_igual_entre_leituras=False)
        escrever(resumo)
        print(json.dumps(resumo), flush=True)


if __name__ == "__main__":
    main()
