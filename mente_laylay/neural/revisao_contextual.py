"""Aplica decisões humanas de revisão a uma vista offline, sem reescrever a fonte.

Não detecta pronomes, não resolve contexto e não converte desconhecido em NONE.
Itens não selecionados continuam não auditados, não certificados para treino.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def preparar_revisao_contextual(fonte: bytes, revisao: Mapping[str, Any]) -> dict[str, Any]:
    """Separa pendências explicitamente revisadas, vinculadas à fonte por hash."""
    sha = hashlib.sha256(fonte).hexdigest()
    if revisao.get("versao") != 1 or revisao.get("origem") != "REVISAO_MANUAL":
        raise ValueError("revisão exige versão e origem manual conhecidas")
    if revisao.get("treino_permitido") is not False or revisao.get("autoriza_execucao") is not False:
        raise ValueError("revisão não pode autorizar treino ou execução")
    if revisao.get("fonte_sha256") != sha:
        raise ValueError("hash da fonte divergiu; revisão não se aplica")
    itens = [json.loads(linha) for linha in fonte.decode("utf-8-sig").splitlines() if linha.strip()]
    if not itens or any(not isinstance(x, dict) or not isinstance(x.get("text"), str) or not x["text"].strip() for x in itens):
        raise ValueError("fonte exige exemplos com text")
    decisoes = revisao.get("decisoes")
    if not isinstance(decisoes, list) or not decisoes:
        raise ValueError("revisão exige decisões explícitas")
    indices: set[int] = set()
    pendentes = []
    for decisao in decisoes:
        if not isinstance(decisao, Mapping):
            raise ValueError("decisão precisa ser mapeamento")
        indice = decisao.get("indice")
        if type(indice) is not int or not 0 <= indice < len(itens) or indice in indices:
            raise ValueError("índice inválido ou duplicado na revisão")
        item = itens[indice]
        texto_sha = hashlib.sha256(item["text"].encode("utf-8")).hexdigest()
        if texto_sha != decisao.get("texto_sha256"):
            raise ValueError("hash do texto divergiu da decisão")
        campos = decisao.get("campos_dependentes")
        fatores = decisao.get("fatores_textuais")
        if not isinstance(campos, list) or not campos or any(not isinstance(c, str) or not c.strip() for c in campos):
            raise ValueError("decisão exige campos dependentes de contexto")
        if not isinstance(fatores, dict) or any(not isinstance(k, str) or not k or type(v) is not bool for k, v in fatores.items()):
            raise ValueError("fatores textuais exigem nomes e booleanos")
        if any(f"extension_factors.{nome}" in campos for nome in fatores):
            raise ValueError("fator não pode ser textual e dependente de contexto")
        if not isinstance(decisao.get("motivo"), str) or not decisao["motivo"].strip():
            raise ValueError("decisão exige motivo")
        indices.add(indice)
        pendentes.append({
            "indice_fonte": indice, "texto_sha256": texto_sha, "text": item["text"],
            "status": "requer_contexto", "motivo": decisao["motivo"],
            "fatores_textuais": dict(fatores),
            "rotulos_indeterminados": {campo: None for campo in campos},
            "exemplo_historico": item,
            "treino_permitido": False, "autoriza_execucao": False,
        })
    return {
        "status": "revisao_parcial_sem_treino", "fonte_sha256": sha,
        "total_fonte": len(itens), "total_revisados": len(indices),
        "total_nao_revisados": len(itens) - len(indices),
        "nao_revisados": [x for i, x in enumerate(itens) if i not in indices],
        "pendentes": pendentes,
        "treino_permitido": False, "autoriza_execucao": False,
    }


def escrever_revisao_contextual(fonte: Path, revisao: Path, saida: Path) -> dict[str, Any]:
    """Publica um bundle de revisão novo; nunca sobrescreve fonte ou relatório."""
    if saida.exists():
        raise FileExistsError("saída já existe; revisão não será sobrescrita")
    dados_fonte, dados_revisao = fonte.read_bytes(), revisao.read_bytes()
    resultado = preparar_revisao_contextual(dados_fonte, json.loads(dados_revisao))
    resultado["revisao_sha256"] = hashlib.sha256(dados_revisao).hexdigest()
    resultado["codigo_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    resultado["limites"] = [
        "nao_revisados não significa aprovados ou independentes de contexto",
        "bundle não é dataset de treino; pendências não são exemplos negativos",
        "não compara métricas da vista reduzida com a prova histórica de outra composição",
    ]
    serializado = json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False)
    if fonte.read_bytes() != dados_fonte or revisao.read_bytes() != dados_revisao:
        raise RuntimeError("insumos mudaram durante a revisão")
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("x", encoding="utf-8") as destino:
        destino.write(serializado + "\n")
    return {k: resultado[k] for k in (
        "status", "fonte_sha256", "revisao_sha256", "total_fonte",
        "total_revisados", "total_nao_revisados", "treino_permitido",
    )}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonte", type=Path, required=True)
    parser.add_argument("--revisao", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(escrever_revisao_contextual(args.fonte, args.revisao, args.saida), ensure_ascii=False))


if __name__ == "__main__":
    main()
