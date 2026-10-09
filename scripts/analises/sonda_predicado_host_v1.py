"""Contraste offline: copiar enunciado versus materializar intervalo no host.

O modelo propõe predicado e papel. O host conhece a ocorrência do foco e
materializa um intervalo literal; não inventa um enunciado ou uma relação.
Geometria, cobertura lexical e rótulo local continuam sem autoridade.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import subprocess
from time import perf_counter
from typing import Callable

import requests

from scripts.analises import sonda_vinculo_enunciado_v1 as anterior


BASE, etapas, schema, papel = anterior.BASE, anterior.etapas, anterior.schema, anterior.papel
contrato = anterior.contrato
MODOS = ("vinculo_enunciado", "predicado_host")
HASH_ANTERIOR = "5020f5bb72a45528025bb85e5f1a7c5a796133a294d2be5b144b02a6628fa570"
SISTEMA = anterior.contraste.SISTEMA_DIRETO.removesuffix("Retorne somente JSON com papel.") + """
O host ja conhece a ocorrencia exata do foco e preserva o texto da fonte.
predicado: copie apenas um trecho literal externo ao foco que atribui sua
funcao ou apresenta sua indefinicao. Escolha palavras contextuais suficientes
para esse trecho ocorrer uma unica vez na fonte. Preserve a grafia; nao
reescreva, nao resuma e nao copie a acao dentro do foco.
papel: proponha a funcao da ocorrencia marcada, conservando indeterminado
quando a fonte deixa alternativas em aberto. Um predicado copiado nao prova
o papel. Se nao conseguir selecionar o predicado, deixe predicado vazio;
isso significa revisao pendente, nao ausencia nem permissao.
O host materializa o intervalo entre o predicado e o foco. Voce nao deve
copiar o enunciado, calcular offsets ou selecionar uma lista de contextos.
Retorne somente JSON com predicado e papel."""
FORMATO = {"type": "object", "additionalProperties": False,
           "required": ["predicado", "papel"], "properties": {
               "predicado": {"type": "string"},
               "papel": {"type": "string", "enum": list(papel.PAPEIS)}}}


def carregar_painel() -> tuple[list[dict], dict, list[str]]:
    if hashlib.sha256(Path(anterior.__file__).read_bytes()).hexdigest() != HASH_ANTERIOR:
        raise ValueError("sonda anterior congelada alterada")
    return anterior.carregar_painel()


def materializar_vinculo(caso: dict, entrada: object, proposta: object) -> dict:
    """Ancoragem única antes do intervalo; não escolhe predicado por proximidade.

    O primeiro uso do contrato ancora só o predicado na fonte integral. O
    segundo verifica objeto/identidade/sobreposição no intervalo materializado.
    Esse intervalo é geométrico, não uma proposição descoberta pelo host.
    """
    base = {**BASE, "estado": "proposta_invalida", "vinculo_estrutural_valido": False,
            "intervalo_ligacao": None, "papel_proposto": None}
    c = papel.conferir_papel(caso, entrada,
        {"papel": proposta.get("papel")} if isinstance(proposta, dict) else None)
    if c["estado"] != "papel_proposto_revisao_pendente":
        return {**base, "estado": c["estado"]}
    if set(proposta) != {"predicado", "papel"} or not isinstance(proposta["predicado"], str):
        return base
    base["papel_proposto"] = c["papel_proposto"]
    if not proposta["predicado"].strip():
        return {**base, "estado": "predicado_vazio_revisao_pendente"}
    fonte = contrato.FonteDidatica(**c["entrada"]["fonte"])
    foco = c["entrada"]["foco"]
    p = {"id": "ancora0", "fonte_id": fonte.identificador, "tipo": "indeterminada",
         "trecho": fonte.texto, "predicado": proposta["predicado"], "objeto": "",
         "papel_objeto": "indeterminado", "polaridade": "indeterminada", "moldura_id": ""}
    r = contrato.conferir_proposicoes_mencionadas((fonte,), {"molduras": [], "proposicoes": [p]}, escopo=fonte.escopo)
    if r["estado"] != "proposicoes_ancoradas_revisao_pendente":
        return {**base, "estado": r["estado"]}
    predicado = r["proposicoes"][0]["predicado"]
    inicio = min(predicado["inicio"], foco["inicio"])
    fim = max(predicado["fim"], foco["fim"])
    # A fonte é fatiada por offsets verificados; nada é reescrito ou completado.
    v = anterior.conferir_vinculo(caso, entrada, {
        "enunciado": fonte.texto[inicio:fim], "predicado": predicado["texto"],
        "papel": proposta["papel"]})
    if not v["vinculo_estrutural_valido"]:
        return {**base, "estado": v["estado"]}
    return {**base, "estado": "intervalo_literal_revisao_pendente",
            "vinculo_estrutural_valido": True, "intervalo_ligacao": v["proposicao_ancorada"]}


def preparar_requisicao(caso: dict, modo: str) -> dict:
    if modo not in MODOS:
        raise ValueError("modo invalido")
    r = anterior.preparar_requisicao(caso, "vinculo_enunciado")
    if modo == "predicado_host":
        r["messages"][0]["content"] = SISTEMA
        r["format"] = deepcopy(FORMATO)
    return r


def medir_caso(caso: dict, *, modo: str, post: Callable = requests.post) -> dict:
    r = {**BASE, "id": caso["id"], "modo": modo,
         "requisicao": preparar_requisicao(caso, modo),
         "entrada_host": etapas.vinculo.preparar_entrada(caso)}
    inicio = perf_counter()
    try:
        r.update(schema.capturar_http(deepcopy(r["requisicao"]), post))
    except Exception as erro:
        r["erro_consulta"] = type(erro).__name__
    r["duracao_consulta_s"] = perf_counter() - inicio
    return r


def aferir_caso(caso: dict, r: dict, ouro: dict) -> dict:
    if not isinstance(r, dict) or r.get("id") != caso["id"] or r.get("modo") not in MODOS:
        raise ValueError("registro invalido")
    if (not etapas.iguais_tipados(r.get("entrada_host"), etapas.vinculo.preparar_entrada(caso))
            or not etapas.iguais_tipados(r.get("requisicao"), preparar_requisicao(caso, r["modo"]))
            or any(r.get(k) is not False for k in BASE)):
        raise ValueError("host, requisicao ou flags adulterados")
    etapas.conferir_registro_consulta({"proposta": None, "duracao_consulta_s": r.get("duracao_consulta_s")})
    if "erro_consulta" in r:
        if not isinstance(r["erro_consulta"], str) or "http_status" in r or "http_bruto" in r:
            raise ValueError("consulta contraditoria")
        dec = {"estado_transporte": "erro_consulta", "finalizacao": "nao_confirmada"}
    else:
        dec = schema.decodificar_http(r.get("http_status"), r.get("http_bruto"))
    proposta = dec.get("proposta")
    entrada = papel.preparar_entrada(caso)
    conf = papel.conferir_papel(caso, entrada,
        {"papel": proposta.get("papel")} if isinstance(proposta, dict) else None)
    rotulo = conf["papel_proposto"]
    valido = conf["estado"] == "papel_proposto_revisao_pendente"
    campos = {"predicado", "papel"} | ({"enunciado"} if r["modo"] == MODOS[0] else set())
    shape = (isinstance(proposta, dict) and set(proposta) == campos
             and all(isinstance(v, str) for v in proposta.values()) and valido)
    if r["modo"] == MODOS[0]:
        v = anterior.conferir_vinculo(caso, entrada, proposta)
        intervalo = v["proposicao_ancorada"]
    else:
        v = materializar_vinculo(caso, entrada, proposta)
        intervalo = v["intervalo_ligacao"]
    concluida = dec["finalizacao"] == "concluida"
    alinhado = bool(valido and concluida and rotulo == ouro["papel"])
    estrutural = v["vinculo_estrutural_valido"] and concluida
    pista = bool(estrutural and any(a.casefold() in intervalo["predicado"]["texto"].casefold()
                                   for a in anterior.PISTAS_LOCAIS[caso["id"]]))
    return {**BASE, "interpretacao": dec, "papel_proposto": rotulo, "conferencia": v,
            "shape_valido_concluido": bool(shape and concluida),
            "papel_alinhado_concluido": alinhado, "vinculo_estrutural_concluido": estrutural,
            "pista_predicado_local_concluida": pista,
            "papel_vinculo_pista_local_concluidos": alinhado and pista,
            "avaliacao": "geometria_e_referencia_local_nao_relacao_semantica"}


def resumir(resultados: list[dict]) -> dict:
    invalido = {**BASE, "tipo": "resumo_invalido"}
    casos, ouro, pares = carregar_painel()
    if (not isinstance(resultados, list) or any(not isinstance(r, dict)
            or not isinstance(r.get("id"), str) or r.get("modo") not in MODOS for r in resultados)):
        return invalido
    chaves = [(r["id"], r["modo"]) for r in resultados]
    if len(set(chaves)) != len(chaves) or set(chaves) != {(c["id"], m) for c in casos for m in MODOS}:
        return invalido
    por_id = {c["id"]: c for c in casos}
    try:
        aferidos = {(r["id"], r["modo"]): aferir_caso(por_id[r["id"]], r, ouro[r["id"]]) for r in resultados}
        duracoes = {m: math.fsum(r["duracao_consulta_s"] for r in resultados if r["modo"] == m) for m in MODOS}
    except (KeyError, ValueError, TypeError, OverflowError):
        return invalido
    resumo = {**BASE, "tipo": "resumo_predicado_host", "holdout_novo": False,
        "revisao_humana_independente": False, "runtime_laylay": False,
        "comparacao_interface_composta": True, "bracos": {}, "comparacoes": {}}
    metricas = ("shape_valido_concluido", "papel_alinhado_concluido", "vinculo_estrutural_concluido",
                "pista_predicado_local_concluida", "papel_vinculo_pista_local_concluidos")
    for modo in MODOS:
        rs = [aferidos[c["id"], modo] for c in casos]
        resumo["bracos"][modo] = {"casos": len(rs), "duracao_consultas_s": duracoes[modo],
            **{k: sum(a[k] for a in rs) for k in metricas},
            "pares_papel_alinhados": sum(all(aferidos[p + lado, modo]["papel_alinhado_concluido"]
                                            for lado in ("A", "B")) for p in pares),
            "pares_compostos_alinhados": sum(all(aferidos[p + lado, modo]["papel_vinculo_pista_local_concluidos"]
                                                for lado in ("A", "B")) for p in pares),
            "por_papel": {p: {"casos": sum(ref["papel"] == p for ref in ouro.values()),
                "alinhados": sum(aferidos[c["id"], modo]["papel_alinhado_concluido"]
                    for c in casos if ouro[c["id"]]["papel"] == p)} for p in papel.PAPEIS},
            "estados_vinculo": dict(Counter(a["conferencia"]["estado"] for a in rs)),
            "estados_transporte": dict(Counter(a["interpretacao"]["estado_transporte"] for a in rs)),
            "finalizacoes": dict(Counter(a["interpretacao"]["finalizacao"] for a in rs))}
    for metrica in metricas[1:]:
        grupos = {k: [] for k in ("ganhos", "perdas", "ambos_alinhados", "nenhum_alinhado")}
        for c in casos:
            a, b = [aferidos[c["id"], m][metrica] for m in MODOS]
            grupos["ganhos" if b and not a else "perdas" if a and not b
                   else "ambos_alinhados" if a else "nenhum_alinhado"].append(c["id"])
        resumo["comparacoes"][metrica] = grupos
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    casos, ouro, pares = carregar_painel()
    digest = etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        metadata = {**BASE, "tipo": "metadata", "data_contexto": "2026-10-07",
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "hash_anterior": HASH_ANTERIOR, "hash_painel": anterior.transferencia.HASH_PAINEL,
            "digest_modelo_inicio": digest, "ordem_16_ab_16_ba": True,
            "referencias_host_pre_consulta": ouro, "pistas_locais_pre_consulta": anterior.PISTAS_LOCAIS,
            "pares_pre_consulta": pares, "holdout_novo": False, "runtime_laylay": False,
            "referencias_fornecidas_ao_modelo": False, "comparacao_interface_composta": True,
            "revisao_humana_independente": False, "entrada_e_opcoes_iguais": True}
        arquivo.write(json.dumps(metadata, ensure_ascii=False, allow_nan=False) + "\n")
        arquivo.flush()
        resultados = []
        for i, c in enumerate(casos):
            for modo in MODOS if i % 2 == 0 else tuple(reversed(MODOS)):
                r = medir_caso(c, modo=modo)
                a = aferir_caso(c, r, ouro[c["id"]])
                resultados.append(r)
                arquivo.write(json.dumps({**r, "tipo": "consulta", "afericao": a}, ensure_ascii=False, allow_nan=False) + "\n")
                arquivo.flush()
                print(json.dumps({"id": c["id"], "modo": modo, "papel": a["papel_proposto"],
                    "alinhado": a["papel_alinhado_concluido"], "vinculo": a["vinculo_estrutural_concluido"],
                    "composto": a["papel_vinculo_pista_local_concluidos"]}), flush=True)
        resumo = resumir(resultados)
        try:
            resumo["digest_modelo_final"] = etapas.coordenadas.digest_modelo()
            resumo["modelo_inalterado_entre_leituras"] = resumo["digest_modelo_final"] == digest
        except Exception as erro:
            resumo["erro_digest_final"] = type(erro).__name__
            resumo["modelo_inalterado_entre_leituras"] = False
        arquivo.write(json.dumps(resumo, ensure_ascii=False, allow_nan=False) + "\n")
        print(json.dumps(resumo, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
