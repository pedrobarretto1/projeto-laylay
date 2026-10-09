"""Fatorial offline: unidade lexical da seleção e prioridade da indeterminação.

Fonte, materializador, referências e limites ficam fixos. A troca de nome
aplica-se ao campo e ao vocabulário correspondente do prompt. Não modifica
guardas nem transforma cobertura lexical em relação semântica verificada.
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

from scripts.analises import sonda_predicado_host_v1 as anterior


BASE, etapas, schema, papel = anterior.BASE, anterior.etapas, anterior.schema, anterior.papel
MODOS = ("predicado", "trecho_externo", "predicado_abstencao", "trecho_externo_abstencao")
HASH_ANTERIOR = "cabbfe97fa3c2f2e1711dda5cdce3f0c2343ba08475c953bde6e2f20257aa01c"
PRIORIDADE = """Decida primeiro se a fonte determina a funcao desta ocorrencia.
Se ela mantem duas ou mais funcoes possiveis sem selecionar uma, proponha
papel indeterminado. Alternativas citadas nao afirmam que uma delas vale.
So escolha nome_designacao, operacao_mencionada ou expressao_sem_operacao
depois de a fonte decidir uma dessas funcoes. Essa verificacao precede a
forma verbal do foco; palavras imperativas nao resolvem incerteza contextual.

"""
METRICAS = ("shape_valido_concluido", "papel_alinhado_concluido", "vinculo_estrutural_concluido",
            "pista_local_concluida", "conjunto_local_concluido", "reproduz_texto_foco_concluido",
            "falso_indeterminado_concluido")
# Quadrado latino: cada variante ocupa cada posição oito vezes em 32 casos.
ORDENS = tuple(MODOS[i:] + MODOS[:i] for i in range(4))
COMPARACOES = (("predicado", "trecho_externo"), ("predicado", "predicado_abstencao"),
              ("trecho_externo", "trecho_externo_abstencao"),
              ("predicado_abstencao", "trecho_externo_abstencao"))


def carregar_painel() -> tuple[list[dict], dict, list[str]]:
    if hashlib.sha256(Path(anterior.__file__).read_bytes()).hexdigest() != HASH_ANTERIOR:
        raise ValueError("dependencia congelada alterada")
    return anterior.carregar_painel()


def campo_do_modo(modo: str) -> str:
    if modo not in MODOS:
        raise ValueError("modo invalido")
    return "trecho_externo" if modo.startswith("trecho_externo") else "predicado"


def preparar_requisicao(caso: dict, modo: str) -> dict:
    campo = campo_do_modo(modo)
    r = anterior.preparar_requisicao(caso, "predicado_host")
    if campo == "trecho_externo":
        r["messages"][0]["content"] = r["messages"][0]["content"].replace("predicado", campo)
        r["format"]["required"] = [campo, "papel"]
        r["format"]["properties"] = {
            campo if k == "predicado" else k: v for k, v in r["format"]["properties"].items()}
    if modo.endswith("_abstencao"):
        r["messages"][0]["content"] = PRIORIDADE + r["messages"][0]["content"]
    return r


def conferir_proposta(caso: dict, entrada: object, proposta: object, *, modo: str) -> dict:
    """Traduz somente o nome de um campo após shape; preserva valores sem reparo."""
    campo = campo_do_modo(modo)
    # Autentica o host mesmo quando o shape da proposta está errado.
    autenticidade = papel.conferir_papel(caso, entrada, None)
    if autenticidade["estado"] in {"entrada_adulterada", "fonte_ou_foco_invalido"}:
        return anterior.materializar_vinculo(caso, entrada, None)
    if (not isinstance(proposta, dict) or set(proposta) != {campo, "papel"}
            or any(not isinstance(v, str) for v in proposta.values())):
        return anterior.materializar_vinculo(caso, entrada, None)
    return anterior.materializar_vinculo(caso, entrada,
        {"predicado": proposta[campo], "papel": proposta["papel"]})


def medir_caso(caso: dict, *, modo: str, post: Callable = requests.post) -> dict:
    r = {**BASE, "id": caso["id"], "modo": modo, "requisicao": preparar_requisicao(caso, modo),
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
    p = dec.get("proposta")
    entrada = papel.preparar_entrada(caso)
    rotulo = papel.conferir_papel(caso, entrada, {"papel": p.get("papel")} if isinstance(p, dict) else None)
    campo = campo_do_modo(r["modo"])
    valido = rotulo["estado"] == "papel_proposto_revisao_pendente"
    shape = (isinstance(p, dict) and set(p) == {campo, "papel"}
             and all(isinstance(v, str) for v in p.values()) and valido)
    v = conferir_proposta(caso, entrada, p, modo=r["modo"])
    concluida = dec["finalizacao"] == "concluida"
    alinhado = bool(valido and concluida and rotulo["papel_proposto"] == ouro["papel"])
    estrutural = v["vinculo_estrutural_valido"] and concluida
    pista = bool(estrutural and any(t.casefold() in v["intervalo_ligacao"]["predicado"]["texto"].casefold()
                                    for t in anterior.anterior.PISTAS_LOCAIS[caso["id"]]))
    # Diagnóstico de texto igual, não identidade da ocorrência ou nova guarda.
    copia_foco = bool(shape and concluida and entrada["foco"]["texto"].casefold() in p[campo].casefold())
    return {**BASE, "interpretacao": dec, "conferencia": v, "papel_proposto": rotulo["papel_proposto"],
        "shape_valido_concluido": bool(shape and concluida), "papel_alinhado_concluido": alinhado,
        "vinculo_estrutural_concluido": estrutural, "pista_local_concluida": pista,
        "conjunto_local_concluido": alinhado and pista, "reproduz_texto_foco_concluido": copia_foco,
        "falso_indeterminado_concluido": bool(valido and concluida and rotulo["papel_proposto"] == "indeterminado"
                                               and ouro["papel"] != "indeterminado")}


def resumir(resultados: list[dict]) -> dict:
    invalido = {**BASE, "tipo": "resumo_invalido"}
    casos, ouro, pares = carregar_painel()
    if (not isinstance(resultados, list) or any(not isinstance(r, dict)
            or not isinstance(r.get("id"), str) or r.get("modo") not in MODOS for r in resultados)):
        return invalido
    chaves = [(r["id"], r["modo"]) for r in resultados]
    if len(set(chaves)) != len(chaves) or set(chaves) != {(c["id"], m) for c in casos for m in MODOS}:
        return invalido
    indice = {c["id"]: c for c in casos}
    try:
        aferidos = {(r["id"], r["modo"]): aferir_caso(indice[r["id"]], r, ouro[r["id"]]) for r in resultados}
        duracoes = {m: math.fsum(r["duracao_consulta_s"] for r in resultados if r["modo"] == m) for m in MODOS}
    except (ValueError, TypeError, KeyError, OverflowError):
        return invalido
    resumo = {**BASE, "tipo": "resumo_unidade_abstencao", "holdout_novo": False,
              "runtime_laylay": False, "revisao_humana_independente": False, "bracos": {}, "comparacoes": {}}
    for modo in MODOS:
        rs = [aferidos[c["id"], modo] for c in casos]
        resumo["bracos"][modo] = {"casos": len(rs), "duracao_consultas_s": duracoes[modo],
            **{k: sum(a[k] for a in rs) for k in METRICAS},
            "pares_papel_alinhados": sum(all(aferidos[p + lado, modo]["papel_alinhado_concluido"]
                                            for lado in ("A", "B")) for p in pares),
            "pares_conjunto_alinhados": sum(all(aferidos[p + lado, modo]["conjunto_local_concluido"]
                                               for lado in ("A", "B")) for p in pares),
            "por_papel": {p: {"total": sum(ref["papel"] == p for ref in ouro.values()),
                "alinhados": sum(aferidos[c["id"], modo]["papel_alinhado_concluido"]
                    for c in casos if ouro[c["id"]]["papel"] == p)} for p in papel.PAPEIS},
            "estados_vinculo": dict(Counter(a["conferencia"]["estado"] for a in rs)),
            "finalizacoes": dict(Counter(a["interpretacao"]["finalizacao"] for a in rs)),
            "estados_transporte": dict(Counter(a["interpretacao"]["estado_transporte"] for a in rs))}
    for ma, mb in COMPARACOES:
        comparacao = {}
        for k in METRICAS[1:]:
            # 'ganho_booleano' é aumento da métrica, nem sempre melhoria (cópia/falso indeterminado).
            grupos = {g: [] for g in ("ganho_booleano", "perda_booleana", "ambos_true", "ambos_false")}
            for c in casos:
                a, b = [aferidos[c["id"], m][k] for m in (ma, mb)]
                grupos["ganho_booleano" if b and not a else "perda_booleana" if a and not b
                       else "ambos_true" if a else "ambos_false"].append(c["id"])
            comparacao[k] = grupos
        resumo["comparacoes"][ma + "->" + mb] = comparacao
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    casos, ouro, pares = carregar_painel()
    digest = etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        meta = {**BASE, "tipo": "metadata", "data_contexto": "2026-10-07",
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "hash_anterior": HASH_ANTERIOR, "hash_painel": anterior.anterior.transferencia.HASH_PAINEL,
            "digest_modelo_inicio": digest, "ordens_pre_consulta": ORDENS,
            "referencias_host_pre_consulta": ouro, "pistas_locais_pre_consulta": anterior.anterior.PISTAS_LOCAIS,
            "pares_pre_consulta": pares, "holdout_novo": False, "runtime_laylay": False,
            "referencias_fornecidas_ao_modelo": False, "revisao_humana_independente": False,
            "entrada_opcoes_materializador_iguais": True,
            "fatores": ["nome_campo_e_vocabulario", "prioridade_indeterminacao"]}
        arquivo.write(json.dumps(meta, ensure_ascii=False, allow_nan=False) + "\n")
        arquivo.flush()
        rs = []
        for i, c in enumerate(casos):
            for modo in ORDENS[i % 4]:
                r = medir_caso(c, modo=modo)
                a = aferir_caso(c, r, ouro[c["id"]])
                rs.append(r)
                arquivo.write(json.dumps({**r, "tipo": "consulta", "afericao": a}, ensure_ascii=False, allow_nan=False) + "\n")
                arquivo.flush()
                print(json.dumps({"id": c["id"], "modo": modo, "papel": a["papel_proposto"],
                    "alinhado": a["papel_alinhado_concluido"], "vinculo": a["vinculo_estrutural_concluido"],
                    "copia_foco": a["reproduz_texto_foco_concluido"]}), flush=True)
        resumo = resumir(rs)
        try:
            resumo["digest_modelo_final"] = etapas.coordenadas.digest_modelo()
            resumo["modelo_inalterado_entre_leituras"] = resumo["digest_modelo_final"] == digest
        except Exception as erro:
            resumo["erro_digest_final"] = type(erro).__name__
            resumo["modelo_inalterado_entre_leituras"] = False
        arquivo.write(json.dumps(resumo, ensure_ascii=False, allow_nan=False) + "\n")
        print(json.dumps({"tipo": resumo["tipo"], "bracos": resumo.get("bracos")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
