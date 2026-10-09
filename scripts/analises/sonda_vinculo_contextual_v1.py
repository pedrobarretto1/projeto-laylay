"""A/B offline: mesmo papel de foco, sem/com evidência contextual por tokens.

Host materializa intervalos na fonte original; rótulo, cobertura de pistas
e suporte semântico são fronteiras distintas. Não seleciona ação principal,
autoriza, registra vigência, treina ou se integra ao runtime.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Callable, Mapping

from scripts.analises import sonda_papel_trecho_v1 as papel
from scripts.analises.sonda_produtor_condicoes_v2 import _ancorar_trecho, _consultar_modelo
from scripts.analises.sonda_produtor_intervalos_v1 import tokenizar_fonte


BASE = papel.literal.contrato.BASE
DADOS = Path(__file__).parent / "dados"
ENTRADAS = DADOS / "sonda_vinculo_contextual_v1.json"
REVISAO = DADOS / "sonda_vinculo_contextual_revisao_v1.json"
HASHES = ("fe94a2a77ac28b2b870004f16f9ca21f4bebf4469955b6f17b4cd10f29dfc682",
          "04d53c818d217f910dfd2eb766e3800865544c9a3fd7b64ccd98318743c5d6a0")
MODOS = ("rotulo", "vinculo")
SISTEMA_VINCULO = papel.SISTEMA.removesuffix("Retorne somente JSON com papel.") + (
    "Indique primeiro ate dois intervalos de tokens de CONTEXTO EXTERNO ao "
    "foco que sustentam sua leitura; depois proponha o mesmo papel. Use inicio "
    "inclusivo e fim exclusivo dos IDs de tokens, preservando ordem dos "
    "intervalos. Nao inclua tokens do foco, nao invente texto nem explique "
    "livremente. Contexto externo ao foco interno pode pertencer a aspas "
    "externas. Se nao consegue indicar contexto, use evidencias vazias; isso "
    "nao prova ausencia nem suporte. Retorne JSON com evidencias e papel."
)
FORMATO_VINCULO = {"type": "object", "additionalProperties": False,
    "required": ["evidencias", "papel"], "properties": {
        "evidencias": {"type": "array", "maxItems": 2, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["inicio", "fim"], "properties": {
                "inicio": {"type": "integer"}, "fim": {"type": "integer"}}}},
        "papel": deepcopy(papel.FORMATO["properties"]["papel"])}}


def preparar_entrada(caso: Mapping[str, object]) -> dict:
    """Mesma entrada em ambos os braços, incluindo tokens sem ouro."""
    entrada = papel.preparar_entrada(caso)
    if not entrada["foco"]["regiao_aspas_id"] or not entrada["foco"]["texto"].strip():
        raise ValueError("diagnostico exige foco citado nao vazio")
    return {**entrada, "tokens": tokenizar_fonte(entrada["fonte"]["texto"])}


def conferir_vinculo(caso: Mapping[str, object], entrada: object, proposta: object) -> dict:
    """Somente integridade, tipo e intervalos externos; vínculo não provado."""
    base = {**BASE, "estado": "proposta_invalida", "papel_proposto": None,
            "evidencias": [], "evidencia_literal_externa": False}
    try:
        autentica = preparar_entrada(caso)
    except (KeyError, TypeError, ValueError):
        return {**base, "estado": "fonte_ou_foco_invalido"}
    try:
        igual = (isinstance(entrada, dict) and entrada == autentica
                 and json.dumps(entrada, sort_keys=True, allow_nan=False)
                 == json.dumps(autentica, sort_keys=True, allow_nan=False))
    except (TypeError, ValueError):
        igual = False
    if not igual:
        return {**base, "estado": "entrada_adulterada"}
    if (not isinstance(proposta, dict) or set(proposta) != {"evidencias", "papel"}
            or not isinstance(proposta["papel"], str) or proposta["papel"] not in papel.PAPEIS
            or not isinstance(proposta["evidencias"], list) or len(proposta["evidencias"]) > 2):
        return base
    tokens, foco, fonte = autentica["tokens"], autentica["foco"], autentica["fonte"]
    evidencias, fim_anterior = [], 0
    for item in proposta["evidencias"]:
        if (not isinstance(item, dict) or set(item) != {"inicio", "fim"}
                or type(item["inicio"]) is not int or type(item["fim"]) is not int
                or not 0 <= item["inicio"] < item["fim"] <= len(tokens)
                or item["inicio"] < fim_anterior):
            return {**base, "estado": "intervalos_invalidos"}
        inicio = tokens[item["inicio"]]["inicio"]
        fim = tokens[item["fim"] - 1]["fim"]
        if inicio < foco["fim"] and foco["inicio"] < fim:
            return {**base, "estado": "evidencia_intersecta_foco"}
        evidencias.append({"fonte_id": fonte["identificador"], "inicio": inicio, "fim": fim,
                           "texto": fonte["texto"][inicio:fim]})
        fim_anterior = item["fim"]
    return {**base, "estado": "vinculo_proposto_revisao_pendente", "papel_proposto": proposta["papel"],
            "evidencias": evidencias, "evidencia_literal_externa": bool(evidencias)}


def medir_caso(caso: Mapping[str, object], *, modo: str,
               consulta: Callable[..., object] = _consultar_modelo) -> dict:
    if modo not in MODOS:
        raise ValueError("modo invalido")
    entrada = preparar_entrada(caso)
    sistema, formato = ((papel.SISTEMA, papel.FORMATO) if modo == "rotulo"
                        else (SISTEMA_VINCULO, FORMATO_VINCULO))
    proposta = consulta(sistema, deepcopy(entrada), deepcopy(formato),
                       url="http://127.0.0.1:11434/api/chat", modelo="qwen3:4b-instruct")
    conferencia = (papel.conferir_papel(caso, papel.preparar_entrada(caso), proposta) if modo == "rotulo"
                   else conferir_vinculo(caso, entrada, proposta))
    return {**BASE, "id": caso["id"], "modo": modo, "proposta": proposta,
            "entrada": entrada, "conferencia": conferencia}


def aferir(resultado: Mapping[str, object], ouro: Mapping[str, object]) -> dict:
    """Rótulo bruto separado da guarda conjunta; cobertura local não é suporte."""
    proposta, conferencia = resultado.get("proposta"), resultado.get("conferencia", {})
    papel_observado = proposta.get("papel") if isinstance(proposta, dict) else None
    rotulo_valido = isinstance(papel_observado, str) and papel_observado in papel.PAPEIS
    rotulo_alinhado = rotulo_valido and papel_observado == ouro["papel"]
    conjunta = conferencia.get("estado") in {
        "papel_proposto_revisao_pendente", "vinculo_proposto_revisao_pendente"}
    literal = conjunta and conferencia.get("evidencia_literal_externa") is True
    evidencias = conferencia.get("evidencias", []) if literal else []
    cobertura = bool(literal and any(all(
        any(ancora.casefold() in e["texto"].casefold() for e in evidencias)
        for ancora in alternativa) for alternativa in ouro["ancoras"]))
    return {**BASE, "rotulo_valido": rotulo_valido, "papel_alinhado_revisao_local": bool(rotulo_alinhado),
            "envelope_conjunto_valido": conjunta, "evidencia_literal_externa": literal,
            "cobertura_ancoras_relacionais_locais": cobertura,
            "papel_e_ancoras_alinhados_localmente": bool(rotulo_alinhado and cobertura),
            "avaliacao": "papel_e_cobertura_lexical_nao_suporte_semantico"}


def carregar_painel() -> tuple[list[dict], dict, list[str]]:
    brutos = [p.read_bytes() for p in (ENTRADAS, REVISAO)]
    if tuple(hashlib.sha256(b).hexdigest() for b in brutos) != HASHES:
        raise ValueError("painel alterado apos congelamento")
    dados, revisao = [json.loads(b) for b in brutos]
    casos, ouro, pares_contextuais = dados["casos"], revisao["casos"], revisao["pares_contextuais"]
    if (dados["versao"] != 1 or revisao["versao"] != 1 or len(casos) != 20
            or len({c["id"] for c in casos}) != 20 or set(ouro) != {c["id"] for c in casos}
            or pares_contextuais != ["Q01", "Q02", "Q03", "Q04", "Q05", "Q06", "Q09", "Q10"]):
        raise ValueError("cobertura divergente")
    pares = defaultdict(list)
    for caso in casos:
        entrada = preparar_entrada(caso)
        esperado = ouro[caso["id"]]
        if (set(esperado) != {"papel", "ancoras"} or esperado["papel"] not in papel.PAPEIS
                or not esperado["ancoras"] or not entrada["aspas_sintaticas"]["aspas_coerentes"]):
            raise ValueError("revisao invalida")
        for alternativa in esperado["ancoras"]:
            if not isinstance(alternativa, list) or not alternativa:
                raise ValueError("ancoras invalidas")
            for ancora in alternativa:
                if not isinstance(ancora, str) or not ancora.strip():
                    raise ValueError("ancora vazia")
                literal = _ancorar_trecho(caso["texto"], ancora)
                if literal is None:
                    raise ValueError("ancora sem ocorrencia unica")
                inicio = caso["texto"].index(literal)
                fim, foco = inicio + len(literal), entrada["foco"]
                if inicio < foco["fim"] and foco["inicio"] < fim:
                    raise ValueError("ancora intersecta foco")
        pares[caso["par"]].append(caso)
    if set(pares) != {f"Q{i:02}" for i in range(1, 11)} or any(len(p) != 2 for p in pares.values()):
        raise ValueError("pares divergentes")
    for par in pares_contextuais:
        a, b = pares[par]
        if (preparar_entrada(a)["foco"]["texto"] != preparar_entrada(b)["foco"]["texto"]
                or {ouro[a["id"]]["papel"], ouro[b["id"]]["papel"]} != {"nome_designacao", "operacao_mencionada"}):
            raise ValueError("contraste contextual divergente")
    return casos, ouro, pares_contextuais


def resumir(casos: list[dict], resultados: list[dict], pares_contextuais: list[str]) -> dict:
    """Cobertura completa antes de contar; não importa métricas externas."""
    resumo = {**BASE, "tipo": "resumo_local", "avalia_pipeline_completo": False, "bracos": {}}
    esperados = {(c["id"], m) for c in casos for m in MODOS}
    if any(not isinstance(r, dict) or not isinstance(r.get("id"), str)
           or r.get("modo") not in MODOS for r in resultados):
        return {**BASE, "tipo": "resumo_invalido"}
    chaves = [(r["id"], r["modo"]) for r in resultados]
    if len(set(chaves)) != len(chaves) or set(chaves) != esperados:
        return {**BASE, "tipo": "resumo_invalido"}
    pares = defaultdict(list)
    for c in casos:
        pares[c["par"]].append(c["id"])
    for modo in MODOS:
        rs = [r for r in resultados if r["modo"] == modo]
        alinhados = {r["id"] for r in rs if r["afericao"]["papel_alinhado_revisao_local"]}
        campos = ("rotulo_valido", "papel_alinhado_revisao_local", "envelope_conjunto_valido",
                  "evidencia_literal_externa", "cobertura_ancoras_relacionais_locais",
                  "papel_e_ancoras_alinhados_localmente")
        resumo["bracos"][modo] = {**{k: sum(r["afericao"][k] for r in rs) for k in campos},
            "casos": len(rs), "pares_contextuais_completos": sum(
                all(i in alinhados for i in pares[p]) for p in pares_contextuais),
            "pares_contextuais": len(pares_contextuais)}
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    casos, ouro, pares_contextuais = carregar_painel()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        metadata = {**BASE, "tipo": "metadata", "hashes_painel": HASHES,
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "hash_papel": hashlib.sha256(Path(papel.__file__).read_bytes()).hexdigest(),
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
            "modelo": "qwen3:4b-instruct", "temperatura": 0, "num_predict": 700,
            "runtime_laylay": False, "revisao_humana_independente": False,
            "mesma_entrada_tokenizada_em_ambos_bracos": True, "baseline_prompt_schema_papel_preservados": True,
            "ordem_bracos_contrabalanceada": True, "evidencia_nao_e_suporte_semantico": True,
            "ordem_evidencias_antes_papel_solicitada_nao_garantida": True}
        arquivo.write(json.dumps(metadata, ensure_ascii=False) + "\n")
        arquivo.flush()
        resultados = []
        for indice, caso in enumerate(casos):
            ordem = MODOS if indice % 2 == 0 else tuple(reversed(MODOS))
            for modo in ordem:
                try:
                    r = medir_caso(caso, modo=modo)
                except Exception as erro:
                    r = {**BASE, "id": caso["id"], "modo": modo, "erro": type(erro).__name__}
                r["afericao"] = aferir(r, ouro[caso["id"]])
                resultados.append(r)
                arquivo.write(json.dumps(r, ensure_ascii=False) + "\n")
                arquivo.flush()
                print(json.dumps({"id": r["id"], "modo": modo, "afericao": r["afericao"]}, ensure_ascii=False), flush=True)
        resumo = resumir(casos, resultados, pares_contextuais)
        arquivo.write(json.dumps(resumo, ensure_ascii=False) + "\n")
        print(json.dumps(resumo, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
