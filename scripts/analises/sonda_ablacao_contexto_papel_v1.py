"""Ablação diagnóstica manual, não seletor: contexto concorrente versus controles."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

from scripts.analises import sonda_papel_transferencia_v1 as transferencia


BASE, MODOS, etapas, papel = transferencia.BASE, transferencia.MODOS, transferencia.etapas, transferencia.papel
VARIANTES = ("integral", "recorte_diagnostico")
HASH_TRANSFERENCIA = "05ddfa7d4be55e47c6f4942df196d2e5a2e775e78ada2e588b4ab457428689b2"
IDS = ("H05A", "H10A", "H11A", "H11B", "H02A", "H06A", "U01", "U02", "U03", "U04")
# Escolhas manuais pré-consulta. Nenhum algoritmo seleciona contexto semanticamente.
RECORTES = {
    "H05A": "o arquivo denominado “mova relatório.csv”",
    "H10A": "o documento intitulado “limpe o histórico”",
    "H11A": "A placa recebeu o título “abra o registro”",
    "H11B": "no manual, “abra o registro” aparece como ordem.",
}


def carregar_base() -> tuple[list[dict], dict]:
    if hashlib.sha256(Path(transferencia.__file__).read_bytes()).hexdigest() != HASH_TRANSFERENCIA:
        raise ValueError("transferencia congelada alterada")
    casos, ouro, _ = transferencia.carregar_painel()
    por_id = {c["id"]: c for c in casos}
    return [por_id[i] for i in IDS], {i: ouro[i] for i in IDS}


def projetar_caso(caso: dict, variante: str) -> tuple[dict, dict]:
    """Preserva a ocorrência por offsets; texto repetido não resolve identidade."""
    if variante not in VARIANTES or caso["id"] not in IDS:
        raise ValueError("variante ou caso invalido")
    foco_original = papel.preparar_entrada(caso)["foco"]
    texto = caso["texto"]
    trecho = RECORTES.get(caso["id"], texto) if variante == "recorte_diagnostico" else texto
    if texto.count(trecho) != 1:
        raise ValueError("recorte nao unico")
    inicio = texto.index(trecho)
    fim = inicio + len(trecho)
    if not inicio <= foco_original["inicio"] < foco_original["fim"] <= fim:
        raise ValueError("recorte perdeu foco")
    projetado = {**caso, "texto": trecho}
    catalogo = papel.literal.preparar_catalogo(projetado)
    candidatos = [c for c in catalogo["candidatos"]
                  if c["inicio"] == foco_original["inicio"] - inicio
                  and c["fim"] == foco_original["fim"] - inicio]
    if len(candidatos) != 1:
        raise ValueError("ocorrencia projetada nao unica")
    projetado["foco_id"] = candidatos[0]["id"]
    foco = papel.preparar_entrada(projetado)["foco"]
    if foco["texto"] != foco_original["texto"]:
        raise ValueError("conteudo do foco alterado")
    mapa = {"inicio_na_fonte_original": inicio, "fim_na_fonte_original": fim,
            "foco_original": deepcopy(foco_original), "foco_projetado": deepcopy(foco),
            "recorte_manual": variante == "recorte_diagnostico" and caso["id"] in RECORTES,
            "fonte_alterada": trecho != texto, "suporte_semantico_verificado": False}
    return projetado, mapa


def medir_caso(caso: dict, *, variante: str, modo: str, **opcoes: object) -> dict:
    projetado, mapa = projetar_caso(caso, variante)
    r = transferencia.medir_caso(projetado, modo=modo, **opcoes)
    return {**r, "variante": variante, "mapa_projecao": mapa}


def aferir_caso(caso: dict, r: dict, ouro: dict) -> dict:
    if not isinstance(r, dict):
        raise ValueError("registro invalido")
    projetado, mapa = projetar_caso(caso, r.get("variante"))
    if not etapas.iguais_tipados(r.get("mapa_projecao"), mapa):
        raise ValueError("projecao adulterada")
    return transferencia.aferir_caso(projetado, r, ouro)


def resumir(resultados: list[dict]) -> dict:
    casos, ouro = carregar_base()
    invalido = {**BASE, "tipo": "resumo_invalido"}
    if not isinstance(resultados, list) or any(not isinstance(r, dict) for r in resultados):
        return invalido
    chaves = [(r.get("id"), r.get("variante"), r.get("modo")) for r in resultados]
    try:
        if len(set(chaves)) != len(chaves) or set(chaves) != {(i, v, m) for i in IDS for v in VARIANTES for m in MODOS}:
            return invalido
        por_id = {c["id"]: c for c in casos}
        aferidos = {(r["id"], r["variante"], r["modo"]): aferir_caso(por_id[r["id"]], r, ouro[r["id"]])
                    for r in resultados}
    except (KeyError, ValueError, TypeError, OverflowError):
        return invalido
    resumo = {**BASE, "tipo": "resumo_ablacao_contexto_papel", "recorte_manual_nao_seletor": True,
              "holdout_novo": False, "avalia_runtime_laylay": False, "bracos": {}, "comparacoes": {}}
    for modo in MODOS:
        for variante in VARIANTES:
            rs = [aferidos[i, variante, modo] for i in IDS]
            grupos = {"intervencoes": list(RECORTES), "controles_identicos": [i for i in IDS if i not in RECORTES],
                      "indeterminados": [i for i in IDS if ouro[i]["papel"] == "indeterminado"]}
            resumo["bracos"][modo + "/" + variante] = {
                "casos": len(rs), "saida_valida_concluida": sum(a["saida_valida_concluida"] for a in rs),
                "alinhados_concluidos": sum(a["papel_alinhado_concluido"] for a in rs),
                "grupos": {g: {"casos": len(ids), "alinhados_concluidos": sum(
                    aferidos[i, variante, modo]["papel_alinhado_concluido"] for i in ids)} for g, ids in grupos.items()},
                "finalizacoes": dict(Counter(a["interpretacao"]["finalizacao"] for a in rs))}
        mudancas = []
        for i in IDS:
            a, b = [aferidos[i, v, modo] for v in VARIANTES]
            ca, cb = a["papel_alinhado_concluido"], b["papel_alinhado_concluido"]
            mudancas.append({"id": i, "intervencao": i in RECORTES,
                "integral": a["papel_proposto"], "recorte": b["papel_proposto"],
                "resultado": "ganho" if cb and not ca else "perda" if ca and not cb
                    else "ambos_alinhados" if ca else "nenhum_alinhado",
                "rotulo_mudou": a["papel_proposto"] != b["papel_proposto"]})
        resumo["comparacoes"][modo] = {"contagens": dict(Counter(x["resultado"] for x in mudancas)),
            "mudancas": mudancas}
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    casos, ouro = carregar_base()
    digest = etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        meta = {**BASE, "tipo": "metadata", "data_contexto": "2026-10-07",
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "hash_transferencia": HASH_TRANSFERENCIA, "hash_painel": transferencia.HASH_PAINEL,
            "digest_modelo_inicio": digest, "referencias_host_pre_consulta": ouro,
            "recortes_manuais_pre_consulta": RECORTES, "casos_host_pre_consulta": casos,
            "prompts_congelados": True, "holdout_novo": False, "runtime_laylay": False,
            "recorte_manual_nao_seletor": True, "ordem_5_integral_primeiro_5_recorte_primeiro": True}
        arquivo.write(json.dumps(meta, ensure_ascii=False, allow_nan=False) + "\n")
        arquivo.flush()
        resultados = []
        for i, caso in enumerate(casos):
            for variante in VARIANTES if i % 2 == 0 else tuple(reversed(VARIANTES)):
                for modo in MODOS if i % 2 == 0 else tuple(reversed(MODOS)):
                    r = medir_caso(caso, variante=variante, modo=modo)
                    a = aferir_caso(caso, r, ouro[caso["id"]])
                    resultados.append(r)
                    arquivo.write(json.dumps({**r, "tipo": "consulta", "afericao": a}, ensure_ascii=False, allow_nan=False) + "\n")
                    arquivo.flush()
                    print(json.dumps({"id": caso["id"], "variante": variante, "modo": modo,
                                      "papel": a["papel_proposto"], "alinhado": a["papel_alinhado_concluido"]}), flush=True)
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
