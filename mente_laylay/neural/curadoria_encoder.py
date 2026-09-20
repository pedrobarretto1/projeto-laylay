"""Fila local de revisão, nunca anotador automático de experiências."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from .auditoria_shadow import ler_jsonl_tolerante
from .experiencias import RegistroRevisoesCorrecoesNeurais


def _hash(caminho: Path) -> str | None:
    return hashlib.sha256(caminho.read_bytes()).hexdigest() if caminho.is_file() else None


def preparar_fila(experiencias: Path, revisoes: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Agrupa texto literal; índice de registro válido NÃO é número de linha."""
    hashes = {"experiencias": _hash(experiencias), "revisoes": _hash(revisoes)}
    if hashes["experiencias"] is None:
        raise FileNotFoundError(experiencias)
    registros, invalidas = ler_jsonl_tolerante(experiencias)
    _, revisoes_invalidas = ler_jsonl_tolerante(revisoes)
    ledger = RegistroRevisoesCorrecoesNeurais(revisoes)
    decisoes = ledger.decisoes_atuais()
    classificados = ledger.classificar(registros)
    filas: dict[str, dict[str, Any]] = {}
    sem_texto = []
    for indice, registro in enumerate(registros, 1):
        texto = registro.get("text")
        if not isinstance(texto, str) or not texto.strip():
            sem_texto.append(indice)
            continue
        if texto not in filas:
            filas[texto] = {
                "id": "revisao_" + hashlib.sha256(texto.encode()).hexdigest(), "texto": texto,
                "origem_texto": "desconhecida", "ancestrais": None, "particao": None,
                "anotacao": None, "revisao_encoder": "pendente", "referencias": [],
                "treino_permitido": False, "autoriza_execucao": False, "autoriza_promocao": False,
            }
        identificador = str(registro.get("id") or "").strip()
        filas[texto]["referencias"].append({
            "indice_registro_valido": indice, "experiencia_id": identificador or None,
            "tipo_registro": registro.get("tipo"), "origem_componente": registro.get("origem"),
            "evidencia_declarada": registro.get("evidencia"),
            "decisao_ledger": decisoes.get(identificador, "pendente"),
            "texto_pode_estar_truncado": len(texto) >= 500,
        })
    atuais = {"experiencias": _hash(experiencias), "revisoes": _hash(revisoes)}
    if hashes != atuais:
        raise RuntimeError("fontes mudaram durante leitura; exportação abortada")
    ids = [str(r.get("id") or "").strip() for r in registros]
    resumo = {
        "fontes": {"experiencias": str(experiencias.resolve()), "revisoes": str(revisoes.resolve())},
        "fontes_sha256": hashes, "registros_validos": len(registros),
        "registros_invalidos_nao_recuperados": invalidas, "revisoes_invalidas": revisoes_invalidas,
        "registros_sem_texto_indices": sem_texto, "textos_unicos": len(filas),
        "tipos": dict(Counter(str(r.get("tipo") or "ausente") for r in registros)),
        "evidencias": dict(Counter(str(r.get("evidencia") or "ausente") for r in registros)),
        "classificacao_ledger": {k: len(v) for k, v in classificados.items()},
        "revisoes_sem_experiencia": sum(i not in ids for i in decisoes),
        "ids_duplicados": [i for i, n in Counter(ids).items() if i and n > 1],
        "anotacoes_encoder": 0, "origem_turno_verificada": False,
        "quarentena": "linhas inválidas excluídas da fila; fonte original intacta",
        "treino_permitido": False, "autoriza_execucao": False, "autoriza_promocao": False,
    }
    return list(filas.values()), resumo


def executar(experiencias: Path, revisoes: Path, destino: Path) -> dict[str, Any]:
    if destino.exists():
        raise FileExistsError("preservar fila anterior")
    fila, resumo = preparar_fila(experiencias, revisoes)
    resumo["codigo_sha256"] = _hash(Path(__file__))
    serializada = "".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in fila)
    resumo["fila_sha256"] = hashlib.sha256(serializada.encode()).hexdigest()
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "fila.jsonl").open("x", encoding="utf-8", newline="\n") as f:
        f.write(serializada)
    with (destino / "resumo.json").open("x", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    return resumo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiencias", type=Path, default=Path("memoria/neural/experiencias.jsonl"))
    parser.add_argument("--revisoes", type=Path, default=Path("memoria/neural/revisoes_correcoes.jsonl"))
    parser.add_argument("--destino", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(executar(args.experiencias, args.revisoes, args.destino), ensure_ascii=False))
