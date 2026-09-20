"""Extrai texto registrado nas divergências, sem transformá-las em gold."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .auditoria_shadow import ler_jsonl_tolerante
from .curadoria_encoder import _hash
from .supervisao_relacoes_v4 import FLAGS


def preparar_fila(shadow: Path, fila_anterior: Path) -> tuple[list[dict], dict]:
    hashes = {str(p.resolve()): _hash(p) for p in (shadow, fila_anterior)}
    if any(h is None for h in hashes.values()):
        raise FileNotFoundError("shadow e fila anterior são obrigatórios")
    anteriores, erros_fila = ler_jsonl_tolerante(fila_anterior)
    if erros_fila or not anteriores or any(not isinstance(c.get("texto"), str) or not c["texto"].strip() for c in anteriores):
        raise ValueError("fila anterior inválida; não perder controle de sobreposição")
    conhecidos = {c["texto"] for c in anteriores}
    eventos, invalidos = ler_jsonl_tolerante(shadow)
    filas, sobrepostos = {}, Counter()
    sem_texto = tipos_desconhecidos = 0
    for indice, e in enumerate(eventos, 1):
        if e.get("tipo") not in {"comparacao_turno", "comparacao_receipt"}:
            tipos_desconhecidos += 1
            continue
        texto = e.get("texto")
        if not isinstance(texto, str) or not texto.strip():
            sem_texto += 1
            continue
        if texto in conhecidos:
            sobrepostos[texto] += 1
            continue
        if texto not in filas:
            filas[texto] = {
                "id": "revisao_" + hashlib.sha256(texto.encode()).hexdigest(), "texto": texto,
                "origem_texto": "desconhecida", "ancestrais": None, "particao": None,
                "anotacao": None, "revisao_encoder": "pendente", "referencias": [],
                "fidelidade_texto": "literal_do_log_nao_transcricao_bruta",
                "transformacoes_do_coletor": ["espacos_compactados", "limite_500_caracteres"],
                "vies_selecao": "texto_persistido_em_divergencias", **FLAGS,
            }
        filas[texto]["referencias"].append({
            "indice_registro_valido": indice, "evento_id": e.get("id"),
            "tipo_registro": e["tipo"], "ts_registro": e.get("ts"),
            "texto_hash_declarado": e.get("texto_hash"),
            "texto_pode_estar_truncado": len(texto) >= 500,
        })
    if any(_hash(Path(p)) != h for p, h in hashes.items()):
        raise RuntimeError("fonte mudou durante leitura")
    resumo = {"fontes_sha256": hashes, "eventos_validos": len(eventos), "linhas_invalidas": invalidos,
              "eventos_sem_texto": sem_texto, "eventos_tipo_desconhecido": tipos_desconhecidos,
              "textos_sobrepostos": len(sobrepostos), "eventos_sobrepostos": sum(sobrepostos.values()),
              "textos_adicionais": len(filas),
              "eventos_na_fila": sum(len(c["referencias"]) for c in filas.values()),
              "tipos_na_fila": dict(Counter(r["tipo_registro"] for c in filas.values() for r in c["referencias"])),
              "origem_evento_verificada": False, "revisao_humana": False,
              "representatividade_certificada": False, "hash_declarado_identifica_turno": False,
              "linhas_invalidas_preservadas_na_fonte": True, **FLAGS}
    return list(filas.values()), resumo


def executar(shadow: Path, fila_anterior: Path, destino: Path) -> dict:
    if destino.exists():
        raise FileExistsError("preservar fila anterior")
    fila, resumo = preparar_fila(shadow, fila_anterior)
    serializada = "".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in fila)
    resumo.update(codigo_sha256=_hash(Path(__file__)), fila_sha256=hashlib.sha256(serializada.encode()).hexdigest())
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "fila.jsonl").open("x", encoding="utf-8", newline="\n") as f:
        f.write(serializada)
    with (destino / "resumo.json").open("x", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    return resumo


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--shadow", type=Path, required=True)
    p.add_argument("--fila-anterior", type=Path, required=True)
    p.add_argument("--destino", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(executar(a.shadow, a.fila_anterior, a.destino), ensure_ascii=False))
