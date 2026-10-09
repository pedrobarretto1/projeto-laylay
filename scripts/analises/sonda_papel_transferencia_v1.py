"""Transferência a frases novas com os dois prompts de papel já congelados."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import subprocess

from scripts.analises import sonda_papel_leitura_direta_v1 as contraste


BASE, MODOS, etapas, papel = contraste.BASE, contraste.MODOS, contraste.etapas, contraste.papel
ENTRADAS = Path(__file__).parent / "dados" / "sonda_papel_transferencia_v1.json"
HASH_PAINEL = "e93ae74cd152f93a75fdb52b226404ab7659288203188c509ef174ce0cbb8ee2"
HASH_CONTRASTE = "05e6a2c74001bd70a113e00b23837631bd7f8a33876357e7e7d189a6349cda59"
# Reutilizar a implementação real; não adaptar prompts, propostas ou registros.
medir_caso = contraste.medir_caso
aferir_caso = contraste.aferir_caso


def carregar_painel() -> tuple[list[dict], dict, list[str]]:
    if hashlib.sha256(Path(contraste.__file__).read_bytes()).hexdigest() != HASH_CONTRASTE:
        raise ValueError("contraste congelado alterado")
    conhecidos, _, _ = contraste.carregar_painel()
    bruto = ENTRADAS.read_bytes()
    if hashlib.sha256(bruto).hexdigest() != HASH_PAINEL:
        raise ValueError("painel novo alterado apos congelamento")
    dados = json.loads(bruto)
    casos, ouro, pares = dados["casos"], dados["revisao_local"], dados["pares_contextuais"]
    if (dados["versao"] != 1 or len(casos) != 32 or len({c["id"] for c in casos}) != 32
            or set(ouro) != {c["id"] for c in casos} or pares != [f"H{i:02}" for i in range(1, 13)]
            or set(ouro) != {p + lado for p in pares for lado in ("A", "B")} | {
                f"{prefixo}{i:02}" for prefixo in ("N", "U") for i in range(1, 5)}):
        raise ValueError("cobertura divergente")
    antigos_textos = {c["texto"] for c in conhecidos}
    antigos_focos = {papel.preparar_entrada(c)["foco"]["texto"] for c in conhecidos}
    focos = {}
    for c in casos:
        e = etapas.vinculo.preparar_entrada(c)
        ref = ouro[c["id"]]
        if (set(c) != {"id", "par", "foco_id", "texto"}
                or set(ref) != {"papel", "justificativa"} or ref["papel"] not in papel.PAPEIS
                or not isinstance(ref["justificativa"], str) or not ref["justificativa"].strip()
                or not e["aspas_sintaticas"]["aspas_coerentes"]
                or c["texto"] in antigos_textos or e["foco"]["texto"] in antigos_focos
                or c["par"] != (c["id"][:-1] if c["id"].startswith("H") else "")):
            raise ValueError("referencia ou fonte divergente")
        focos[c["id"]] = e["foco"]["texto"]
    for p in pares:
        if (focos[p + "A"] != focos[p + "B"] or ouro[p + "A"]["papel"] != "nome_designacao"
                or ouro[p + "B"]["papel"] != "operacao_mencionada"):
            raise ValueError("contraste contextual divergente")
    if Counter(r["papel"] for r in ouro.values()) != {
            "nome_designacao": 12, "operacao_mencionada": 12,
            "expressao_sem_operacao": 4, "indeterminado": 4}:
        raise ValueError("distribuicao divergente")
    return casos, ouro, pares


def resumir(casos: list[dict], resultados: list[dict], ouro: dict) -> dict:
    invalido = {**BASE, "tipo": "resumo_invalido"}
    canonicos, ref, pares = carregar_painel()
    if (not etapas.iguais_tipados({"casos": casos}, {"casos": canonicos})
            or not etapas.iguais_tipados(ouro, ref) or not isinstance(resultados, list)
            or any(not isinstance(r, dict) or not isinstance(r.get("id"), str)
                   or r.get("modo") not in MODOS for r in resultados)):
        return invalido
    chaves = [(r["id"], r["modo"]) for r in resultados]
    if len(set(chaves)) != len(chaves) or set(chaves) != {(c["id"], m) for c in casos for m in MODOS}:
        return invalido
    por_id = {c["id"]: c for c in casos}
    try:
        aferidos = {(r["id"], r["modo"]): aferir_caso(por_id[r["id"]], r, ouro[r["id"]]) for r in resultados}
        duracoes = {m: math.fsum(r["duracao_consulta_s"] for r in resultados if r["modo"] == m) for m in MODOS}
    except (ValueError, TypeError, KeyError, OverflowError):
        return invalido
    resumo = {**BASE, "tipo": "resumo_papel_transferencia", "painel_novo": True,
              "revisao_humana_independente": False, "avalia_runtime_laylay": False, "bracos": {}}
    for modo in MODOS:
        rs = [aferidos[c["id"], modo] for c in casos]
        por_papel, confusao = {}, {}
        for esperado in papel.PAPEIS:
            ids = [c["id"] for c in casos if ouro[c["id"]]["papel"] == esperado]
            por_papel[esperado] = {"total": len(ids), "alinhados_concluidos": sum(
                aferidos[i, modo]["papel_alinhado_concluido"] for i in ids)}
            confusao[esperado] = dict(Counter(aferidos[i, modo]["papel_proposto"]
                if aferidos[i, modo]["saida_valida_concluida"] else "saida_invalida_ou_inconclusa" for i in ids))
        resumo["bracos"][modo] = {
            **{k: sum(a[k] for a in rs) for k in ("saida_valida", "saida_valida_concluida",
                                                  "papel_alinhado_local", "papel_alinhado_concluido")},
            "casos": len(rs), "consultas": len(rs), "duracao_consultas_s": duracoes[modo],
            "pares_contextuais": len(pares), "pares_contextuais_alinhados_concluidos": sum(
                all(aferidos[p + lado, modo]["papel_alinhado_concluido"] for lado in ("A", "B")) for p in pares),
            "por_papel": por_papel, "confusao": confusao,
            "estados_transporte": dict(Counter(a["interpretacao"]["estado_transporte"] for a in rs)),
            "finalizacoes": dict(Counter(a["interpretacao"]["finalizacao"] for a in rs))}
    comparacoes, mudancas = Counter(), []
    for c in casos:
        a, b = [aferidos[c["id"], m] for m in MODOS]
        ca, cb = a["papel_alinhado_concluido"], b["papel_alinhado_concluido"]
        comparacoes["ganhos" if cb and not ca else "perdas" if ca and not cb
                    else "ambos_alinhados" if ca else "nenhum_alinhado"] += 1
        if (a["papel_proposto"], a["saida_valida_concluida"]) != (b["papel_proposto"], b["saida_valida_concluida"]):
            mudancas.append({"id": c["id"], "esperado_local": ouro[c["id"]]["papel"],
                **{m: aferidos[c["id"], m]["papel_proposto"] for m in MODOS},
                "alinhado_concluido_atual": ca, "alinhado_concluido_direto": cb})
    resumo["comparacao_pareada"] = {k: comparacoes[k] for k in (
        "ganhos", "perdas", "ambos_alinhados", "nenhum_alinhado")}
    resumo["mudancas"] = mudancas
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
            "hash_contraste": HASH_CONTRASTE, "hash_painel": HASH_PAINEL,
            "digest_modelo_inicio": digest, "ordem_16_ab_16_ba": True,
            "runtime_laylay": False, "painel_novo": True, "revisao_humana_independente": False,
            "prompts_congelados_sem_ajuste": True, "diferenca_somente_prompt_sistema": True,
            "schema_entrada_opcoes_iguais": True, "referencias_fornecidas_ao_modelo": False,
            "referencias_host_pre_consulta": ouro, "pares_pre_consulta": pares}
        arquivo.write(json.dumps(metadata, ensure_ascii=False, allow_nan=False) + "\n")
        arquivo.flush()
        resultados = []
        for i, caso in enumerate(casos):
            for modo in MODOS if i % 2 == 0 else tuple(reversed(MODOS)):
                r = medir_caso(caso, modo=modo)
                a = aferir_caso(caso, r, ouro[caso["id"]])
                resultados.append(r)
                arquivo.write(json.dumps({**r, "tipo": "consulta", "afericao": a}, ensure_ascii=False, allow_nan=False) + "\n")
                arquivo.flush()
                print(json.dumps({"id": caso["id"], "modo": modo, "papel": a["papel_proposto"],
                                  "alinhado_concluido": a["papel_alinhado_concluido"]}), flush=True)
        resumo = resumir(casos, resultados, ouro)
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
