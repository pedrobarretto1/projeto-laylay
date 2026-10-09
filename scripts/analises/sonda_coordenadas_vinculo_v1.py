"""Replay diagnóstico: offsets nos tokens vs somente id/texto para o modelo.

Reusa painel, tarefa, schema, materializador e aferição do vínculo congelado.
Não é holdout novo nem integração com a Laylay; não altera artefatos antigos.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter
from typing import Callable, Mapping

from scripts.analises import sonda_vinculo_contextual_v1 as vinculo


BASE = vinculo.BASE
MODOS = ("tokens_com_offsets", "tokens_id_texto")
HASH_VINCULO = "0231344e4d4a9ac975ab1a98995b382222264197e5bea8d835facb7599aca89c"


def projetar_entrada_modelo(caso: Mapping[str, object], *, modo: str) -> dict:
    """Projeção independente da entrada que será mantida pelo host."""
    if modo not in MODOS:
        raise ValueError("modo de coordenadas invalido")
    entrada = deepcopy(vinculo.preparar_entrada(caso))
    if modo == "tokens_id_texto":
        entrada["tokens"] = [{"id": t["id"], "texto": t["texto"]} for t in entrada["tokens"]]
    return entrada


def carregar_painel() -> tuple[list[dict], dict, list[str]]:
    """Não modifica a dependência ou recongela gabarito depois da geração."""
    if hashlib.sha256(Path(vinculo.__file__).read_bytes()).hexdigest() != HASH_VINCULO:
        raise ValueError("sonda de vinculo alterada apos baseline")
    return vinculo.carregar_painel()


def medir_caso(caso: Mapping[str, object], *, modo: str,
               consulta: Callable[..., object] = vinculo._consultar_modelo) -> dict:
    entrada_modelo = projetar_entrada_modelo(caso, modo=modo)
    entrada_host = vinculo.preparar_entrada(caso)
    resultado = {**BASE, "id": caso["id"], "modo": modo,
                 "entrada": entrada_host, "entrada_modelo": entrada_modelo}
    inicio = perf_counter()
    try:
        resultado["proposta"] = consulta(
            vinculo.SISTEMA_VINCULO, deepcopy(entrada_modelo), deepcopy(vinculo.FORMATO_VINCULO),
            url="http://127.0.0.1:11434/api/chat", modelo="qwen3:4b-instruct")
    except Exception as erro:
        resultado["erro"] = type(erro).__name__
    resultado["duracao_consulta_s"] = perf_counter() - inicio
    resultado["conferencia"] = vinculo.conferir_vinculo(caso, entrada_host, resultado.get("proposta"))
    return resultado


def resumir(casos: list[dict], resultados: list[dict], ouro: dict, pares_contextuais: list[str]) -> dict:
    """Cobertura e origem antes do placar; não confia em métricas armazenadas."""
    invalido = {**BASE, "tipo": "resumo_invalido"}
    esperados = {(c["id"], m) for c in casos for m in MODOS}
    if any(not isinstance(r, dict) or not isinstance(r.get("id"), str)
           or r.get("modo") not in MODOS for r in resultados):
        return invalido
    chaves = [(r["id"], r["modo"]) for r in resultados]
    if len(set(chaves)) != len(chaves) or set(chaves) != esperados:
        return invalido
    indice = {c["id"]: c for c in casos}
    conferidos = []
    for resultado in resultados:
        c = indice[resultado["id"]]
        try:
            if json.dumps(resultado.get("entrada_modelo"), sort_keys=True, allow_nan=False) != json.dumps(
                    projetar_entrada_modelo(c, modo=resultado["modo"]), sort_keys=True, allow_nan=False):
                return invalido
        except (TypeError, ValueError):
            return invalido
        conferencia = vinculo.conferir_vinculo(c, resultado.get("entrada"), resultado.get("proposta"))
        if conferencia["estado"] == "entrada_adulterada":
            return invalido
        r = {**resultado, "conferencia": conferencia}
        r["afericao"] = vinculo.aferir(r, ouro[r["id"]])
        conferidos.append(r)
    resumo = {**BASE, "tipo": "resumo_diagnostico_coordenadas", "holdout_novo": False,
              "avalia_pipeline_completo": False, "bracos": {}}
    campos = ("rotulo_valido", "papel_alinhado_revisao_local", "envelope_conjunto_valido",
              "evidencia_literal_externa", "cobertura_ancoras_relacionais_locais",
              "papel_e_ancoras_alinhados_localmente")
    for modo in MODOS:
        rs = [r for r in conferidos if r["modo"] == modo]
        alinhados = {r["id"] for r in rs if r["afericao"]["papel_alinhado_revisao_local"]}
        resumo["bracos"][modo] = {
            **{k: sum(r["afericao"][k] for r in rs) for k in campos}, "casos": len(rs),
            "pares_contextuais_completos": sum(all(c["id"] in alinhados
                for c in casos if c["par"] == p) for p in pares_contextuais),
            "pares_contextuais": len(pares_contextuais),
            "consultas_com_erro": sum("erro" in r for r in rs),
            "evidencias_vazias": sum(isinstance(r.get("proposta"), dict)
                and r["proposta"].get("evidencias") == [] for r in rs),
            "intervalos_invalidos": sum(r["conferencia"]["estado"] == "intervalos_invalidos" for r in rs),
            "evidencia_intersecta_foco": sum(r["conferencia"]["estado"] == "evidencia_intersecta_foco" for r in rs)}
    return resumo


def digest_modelo() -> str:
    """Identidade local observada, não prova qualidade ou determinismo."""
    import requests

    resposta = requests.get("http://127.0.0.1:11434/api/tags", timeout=10)
    resposta.raise_for_status()
    modelos = [m for m in resposta.json()["models"] if m["name"] == "qwen3:4b-instruct"]
    if len(modelos) != 1 or not isinstance(modelos[0].get("digest"), str) or not modelos[0]["digest"]:
        raise ValueError("identidade local do modelo indisponivel")
    return modelos[0]["digest"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    casos, ouro, pares = carregar_painel()
    digest = digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        metadata = {**BASE, "tipo": "metadata", "hashes_painel": vinculo.HASHES,
            "hash_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "hash_vinculo": HASH_VINCULO, "digest_modelo_inicio": digest,
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
            "modelo": "qwen3:4b-instruct", "temperatura": 0, "num_predict": 700,
            "runtime_laylay": False, "holdout_novo": False, "revisao_humana_independente": False,
            "prompt_schema_materializador_iguais": True, "ordem_bracos_contrabalanceada": True,
            "diferenca_somente_offsets_dos_tokens": True,
            "offsets_foco_aspas_ainda_visiveis": True, "propostas_json_parseadas_nao_http_bruto": True}
        arquivo.write(json.dumps(metadata, ensure_ascii=False) + "\n")
        arquivo.flush()
        resultados = []
        for i, c in enumerate(casos):
            for modo in MODOS if i % 2 == 0 else tuple(reversed(MODOS)):
                r = medir_caso(c, modo=modo)
                r["afericao"] = vinculo.aferir(r, ouro[c["id"]])
                resultados.append(r)
                arquivo.write(json.dumps(r, ensure_ascii=False) + "\n")
                arquivo.flush()
                print(json.dumps({"id": r["id"], "modo": modo, "estado": r["conferencia"]["estado"],
                    "afericao": r["afericao"], "erro": r.get("erro")}, ensure_ascii=False), flush=True)
        resumo = resumir(casos, resultados, ouro, pares)
        try:
            resumo["digest_modelo_final"] = digest_modelo()
            resumo["modelo_inalterado_entre_leituras"] = resumo["digest_modelo_final"] == digest
        except Exception as erro:
            resumo["erro_leitura_modelo_final"] = type(erro).__name__
            resumo["modelo_inalterado_entre_leituras"] = False
        arquivo.write(json.dumps(resumo, ensure_ascii=False) + "\n")
        print(json.dumps(resumo, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
