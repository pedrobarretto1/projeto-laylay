"""Sonda offline de enunciado enquadrador; ancoragem não certifica o papel.

Reusa o catálogo literal, o contrato de proposições e a captura HTTP existentes.
Não seleciona instruções para execução, não treina e não entra no runtime.
Comparação de interface composta (prompt + schema), não ablação de um fator.
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

from scripts.analises import sonda_papel_transferencia_v1 as transferencia


contraste = transferencia.contraste
etapas, schema, papel, BASE = contraste.etapas, contraste.schema, contraste.papel, contraste.BASE
contrato = papel.literal.contrato
MODOS = ("leitura_direta", "vinculo_enunciado")
HASH_TRANSFERENCIA = "05ddfa7d4be55e47c6f4942df196d2e5a2e775e78ada2e588b4ab457428689b2"
HASH_CONTRATO = "e286c3032fa7ee2c02f14112b353b949d167a96bec1699ee3958503dc01dfb99"
SISTEMA_VINCULO = contraste.SISTEMA_DIRETO.removesuffix("Retorne somente JSON com papel.") + """
Antes de rotular, identifique o enunciado que enquadra a ocorrencia marcada.
enunciado: copie da fonte um trecho contiguo que contenha essa ocorrencia
uma unica vez e diga como ela e usada, ou explicite a falta de definicao.
Nao copie apenas as palavras do foco nem empreste o enquadramento de outra
ocorrencia com palavras iguais. Mantenha a fonte, nao reescreva nem resuma.
predicado: copie um trecho literal desse enunciado, externo ao foco, que
atribui a funcao ou apresenta sua indefinicao; nao a acao dentro do foco.
papel: proponha a funcao dessa ocorrencia, conservando indeterminado se o
enunciado deixa a alternativa em aberto. Copiar um trecho nao prova o papel.
Se nao conseguir ancorar enunciado/predicado, deixe esses campos vazios;
isso e revisao pendente, nao prova de ausencia nem permissao.
Retorne somente JSON com enunciado, predicado e papel."""
FORMATO = {"type": "object", "additionalProperties": False,
    "required": ["enunciado", "predicado", "papel"], "properties": {
        "enunciado": {"type": "string"}, "predicado": {"type": "string"},
        "papel": {"type": "string", "enum": list(papel.PAPEIS)}}}
# Revisão lexical local congelada, somente host. Não é verdade semântica,
# seletor de trecho ou gabarito entregue ao modelo. As alternativas devem
# aparecer fora do foco no enunciado ancorado, não apenas em justificativa.
PISTAS_LOCAIS = {
    "H01A": ["nome"], "H01B": ["pediu"],
    "H02A": ["nome"], "H02B": ["orientação"],
    "H03A": ["título"], "H03B": ["hipótese"],
    "H04A": ["denominada"], "H04B": ["instrução"],
    "H05A": ["denominado"], "H05B": ["instrução"],
    "H06A": ["se chama"], "H06B": ["exemplifica"],
    "H07A": ["título"], "H07B": ["pedido"],
    "H08A": ["batizada"], "H08B": ["exemplificar"],
    "H09A": ["identifica", "nome"], "H09B": ["ordem"],
    "H10A": ["intitulado"], "H10B": ["solicitou"],
    "H11A": ["título"], "H11B": ["ordem"],
    "H12A": ["nome"], "H12B": ["ordem"],
    "N01": ["diagnóstico", "informa"], "N02": ["descreve"],
    "N03": ["indica estado"], "N04": ["descrição"],
    "U01": ["sem a linha"], "U02": ["não sei"],
    "U03": ["faltou explicar"], "U04": ["não há informação"],
}


def carregar_painel() -> tuple[list[dict], dict, list[str]]:
    for modulo, esperado in ((transferencia, HASH_TRANSFERENCIA), (contrato, HASH_CONTRATO)):
        if hashlib.sha256(Path(modulo.__file__).read_bytes()).hexdigest() != esperado:
            raise ValueError("dependencia congelada alterada")
    casos, ouro, pares = transferencia.carregar_painel()
    if set(PISTAS_LOCAIS) != set(ouro):
        raise ValueError("cobertura lexical divergente")
    for c in casos:
        foco = papel.preparar_entrada(c)["foco"]
        externos = (c["texto"][:foco["inicio"]], c["texto"][foco["fim"]:])
        if not any(p.casefold() in t.casefold() for p in PISTAS_LOCAIS[c["id"]] for t in externos):
            raise ValueError("pista local nao consta fora do foco")
    return casos, ouro, pares


def preparar_requisicao(caso: dict, modo: str) -> dict:
    if modo not in MODOS:
        raise ValueError("modo invalido")
    r = contraste.preparar_requisicao(caso, "leitura_direta")
    if modo == "vinculo_enunciado":
        r["messages"][0]["content"] = SISTEMA_VINCULO
        r["format"] = deepcopy(FORMATO)
    return r


def conferir_vinculo(caso: dict, entrada: object, proposta: object) -> dict:
    """Confere o vínculo geométrico com a ocorrência, não sua interpretação.

    O objeto é o foco já conhecido pelo host. Campos semânticos neutros são
    placeholders explícitos do contrato reutilizado, não predições do modelo.
    Capitalização da cópia pode diferir: a guarda canônica recupera a grafia
    da fonte e os offsets. Não há busca privada pela primeira string igual.
    """
    base = {**BASE, "estado": "proposta_invalida", "vinculo_estrutural_valido": False,
            "proposicao_ancorada": None, "papel_proposto": None}
    conf = papel.conferir_papel(caso, entrada,
        {"papel": proposta.get("papel")} if isinstance(proposta, dict) else None)
    if conf["estado"] != "papel_proposto_revisao_pendente":
        return {**base, "estado": conf["estado"]}
    if (set(proposta) != {"enunciado", "predicado", "papel"}
            or any(not isinstance(v, str) for v in proposta.values())):
        return base
    base["papel_proposto"] = conf["papel_proposto"]
    if not proposta["enunciado"].strip() or not proposta["predicado"].strip():
        return {**base, "estado": "vinculo_sem_ancora_revisao_pendente"}
    fonte = contrato.FonteDidatica(**conf["entrada"]["fonte"])
    foco = conf["entrada"]["foco"]
    quadro = {"molduras": [], "proposicoes": [{
        "id": "enq0", "fonte_id": fonte.identificador, "tipo": "indeterminada",
        "trecho": proposta["enunciado"], "predicado": proposta["predicado"],
        "objeto": foco["texto"], "papel_objeto": "indeterminado",
        "polaridade": "indeterminada", "moldura_id": ""}]}
    r = contrato.conferir_proposicoes_mencionadas((fonte,), quadro, escopo=fonte.escopo)
    if r["estado"] != "proposicoes_ancoradas_revisao_pendente":
        return {**base, "estado": r["estado"]}
    p = r["proposicoes"][0]
    objeto, predicado = p["objeto"], p["predicado"]
    if (p["fonte_id"] != foco["fonte_id"] or objeto is None
            or (objeto["inicio"], objeto["fim"]) != (foco["inicio"], foco["fim"])):
        return {**base, "estado": "objeto_de_outra_ocorrencia"}
    if predicado["inicio"] < objeto["fim"] and objeto["inicio"] < predicado["fim"]:
        return {**base, "estado": "predicado_sobrepoe_foco"}
    return {**base, "estado": "vinculo_ancorado_revisao_pendente",
            "vinculo_estrutural_valido": True, "proposicao_ancorada": p}


def medir_caso(caso: dict, *, modo: str, post: Callable = requests.post) -> dict:
    requisicao = preparar_requisicao(caso, modo)
    r = {**BASE, "id": caso["id"], "modo": modo, "requisicao": deepcopy(requisicao),
         "entrada_host": etapas.vinculo.preparar_entrada(caso)}
    inicio = perf_counter()
    try:
        r.update(schema.capturar_http(deepcopy(requisicao), post))
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
        raise ValueError("requisicao, host ou flags adulterados")
    etapas.conferir_registro_consulta({"proposta": None, "duracao_consulta_s": r.get("duracao_consulta_s")})
    if "erro_consulta" in r:
        if not isinstance(r["erro_consulta"], str) or "http_bruto" in r or "http_status" in r:
            raise ValueError("consulta contraditoria")
        dec = {"estado_transporte": "erro_consulta", "finalizacao": "nao_confirmada"}
    else:
        dec = schema.decodificar_http(r.get("http_status"), r.get("http_bruto"))
    proposta = dec.get("proposta")
    # Projeção do rótulo é uma métrica independente, não conserto de shape.
    conf = papel.conferir_papel(caso, papel.preparar_entrada(caso),
        {"papel": proposta.get("papel")} if isinstance(proposta, dict) else None)
    rotulo = conf["papel_proposto"]
    valido = conf["estado"] == "papel_proposto_revisao_pendente"
    concluida = dec["finalizacao"] == "concluida"
    alinhado = valido and rotulo == ouro["papel"]
    rbase = {**BASE, "interpretacao": dec, "papel_proposto": rotulo,
        "rotulo_valido_concluido": valido and concluida,
        "papel_alinhado_concluido": bool(alinhado and concluida),
        "avaliacao": "rotulo_e_cobertura_locais_nao_verdade_semantica"}
    if r["modo"] == "leitura_direta":
        a = contraste.aferir_caso(caso, r, ouro)
        return {**rbase, "shape_valido_concluido": a["saida_valida_concluida"],
            "vinculo_estrutural_concluido": None, "pista_externa_local_concluida": None,
            "pista_predicado_local_concluida": None,
            "proposta_composta_alinhada_local_concluida": None, "vinculo": None}
    # O registro antigo inclui tokens host. Sua autenticidade foi conferida
    # acima; a porta de papel/proposições recebe o envelope canônico de três
    # campos, não a estrutura ampliada de outra porta.
    v = conferir_vinculo(caso, papel.preparar_entrada(caso), proposta)
    shape = (isinstance(proposta, dict) and set(proposta) == {"enunciado", "predicado", "papel"}
             and all(isinstance(valor, str) for valor in proposta.values()) and valido)
    estrutural = v["vinculo_estrutural_valido"]
    cobertura = cobertura_predicado = False
    if estrutural:
        p = v["proposicao_ancorada"]
        f = p["objeto"]
        fonte = r["entrada_host"]["fonte"]["texto"]
        externos = (fonte[p["inicio"]:f["inicio"]], fonte[f["fim"]:p["fim"]])
        cobertura = any(pista.casefold() in t.casefold()
            for pista in PISTAS_LOCAIS[caso["id"]] for t in externos)
        cobertura_predicado = any(pista.casefold() in p["predicado"]["texto"].casefold()
            for pista in PISTAS_LOCAIS[caso["id"]])
    return {**rbase, "shape_valido_concluido": bool(shape and concluida),
        "vinculo_estrutural_concluido": estrutural and concluida,
        "pista_externa_local_concluida": cobertura and concluida,
        "pista_predicado_local_concluida": cobertura_predicado and concluida,
        "proposta_composta_alinhada_local_concluida": bool(estrutural and cobertura and alinhado and concluida),
        "vinculo": v}


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
    except (ValueError, TypeError, KeyError, OverflowError):
        return invalido
    resumo = {**BASE, "tipo": "resumo_vinculo_enunciado", "holdout_novo": False,
        "revisao_humana_independente": False, "avalia_runtime_laylay": False,
        "comparacao_interface_composta": True, "bracos": {}}
    for modo in MODOS:
        rs = [aferidos[c["id"], modo] for c in casos]
        b = {"casos": len(rs), "consultas": len(rs), "duracao_consultas_s": duracoes[modo],
            "pares_contextuais": len(pares), "pares_papel_alinhados_concluidos": sum(
                all(aferidos[p + lado, modo]["papel_alinhado_concluido"] for lado in ("A", "B")) for p in pares),
            "por_papel": {p: {"total": sum(ouro[c["id"]]["papel"] == p for c in casos),
                "alinhados_concluidos": sum(aferidos[c["id"], modo]["papel_alinhado_concluido"]
                    for c in casos if ouro[c["id"]]["papel"] == p)} for p in papel.PAPEIS},
            "estados_transporte": dict(Counter(a["interpretacao"]["estado_transporte"] for a in rs)),
            "finalizacoes": dict(Counter(a["interpretacao"]["finalizacao"] for a in rs))}
        for k in ("rotulo_valido_concluido", "shape_valido_concluido", "papel_alinhado_concluido",
                  "vinculo_estrutural_concluido", "pista_externa_local_concluida",
                  "pista_predicado_local_concluida",
                  "proposta_composta_alinhada_local_concluida"):
            b[k] = sum(a[k] for a in rs) if modo == "vinculo_enunciado" or rs[0][k] is not None else None
        if modo == "vinculo_enunciado":
            b["estados_vinculo"] = dict(Counter(a["vinculo"]["estado"] for a in rs))
            b["pares_proposta_composta_alinhados_locais"] = sum(all(
                aferidos[p + lado, modo]["proposta_composta_alinhada_local_concluida"]
                for lado in ("A", "B")) for p in pares)
        resumo["bracos"][modo] = b
    comparacoes, mudancas = Counter(), []
    for c in casos:
        a, b = [aferidos[c["id"], modo] for modo in MODOS]
        ca, cb = a["papel_alinhado_concluido"], b["papel_alinhado_concluido"]
        comparacoes["ganhos" if cb and not ca else "perdas" if ca and not cb
                    else "ambos_alinhados" if ca else "nenhum_alinhado"] += 1
        if a["papel_proposto"] != b["papel_proposto"] or ca != cb:
            mudancas.append({"id": c["id"], "esperado_local": ouro[c["id"]]["papel"],
                            **{modo: aferidos[c["id"], modo]["papel_proposto"] for modo in MODOS}})
    resumo["comparacao_papel_pareada"] = {k: comparacoes[k] for k in (
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
            "hash_transferencia": HASH_TRANSFERENCIA, "hash_contrato": HASH_CONTRATO,
            "hash_painel": transferencia.HASH_PAINEL, "digest_modelo_inicio": digest,
            "ordem_16_ab_16_ba": True, "runtime_laylay": False, "holdout_novo": False,
            "revisao_humana_independente": False, "comparacao_interface_composta": True,
            "entrada_e_opcoes_iguais": True, "recortes_oraculo_fornecidos": False,
            "referencias_fornecidas_ao_modelo": False, "prompts_congelados_sem_ajuste": True,
            "referencias_host_pre_consulta": ouro, "pistas_locais_pre_consulta": PISTAS_LOCAIS,
            "pares_pre_consulta": pares}
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
                    "composta_local": a["proposta_composta_alinhada_local_concluida"]}), flush=True)
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
