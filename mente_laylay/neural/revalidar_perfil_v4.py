"""Revalidação explícita offline, sem substituir os protocolos históricos."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .curadoria_encoder import _hash
from .expandir_relacoes_v4 import BASE, FONTE, SHA_FONTE, preparar_dobras
from .comparar_ocorrencias_v4 import PASTA_FONTE, SHA_LOTE, rotular_ocorrencias
from .preparar_lote_relacional_v3 import VARIANTES
from .supervisao_relacoes_v4 import FLAGS, alinhar_relacoes


# Migração explicitamente revisada; não aceitar outra mudança só porque os
# exemplos atuais continuam iguais. O replay integral abaixo segue obrigatório.
NORMALIZADOR_REVISADO = "mente_laylay/cognicao/normalizacao_linguagem.py"
HASHES_REVISADOS = (
    "fb48a34a71c6c94faf9fe0e031282e3ea73e956bf9b940c258ba30d5eee7fb69",
    "850dbbce1423fdca7162c47978618a73a727081ca7d9fc374d850277ae57bf55",
)


def conferir_dependencias(dependencias: dict, hashes: dict) -> dict:
    alteradas = {}
    for nome, antigo in dependencias.items():
        atual = hashes[str((BASE / nome).resolve())]
        if antigo == atual:
            continue
        if nome.replace("\\", "/") != NORMALIZADOR_REVISADO or (antigo, atual) != HASHES_REVISADOS:
            raise ValueError("mudança de dependência sem revisão de compatibilidade")
        alteradas[nome] = {"historico": antigo, "atual": atual}
    return alteradas


def conferir_casos(casos: list[dict]) -> dict:
    """Reexecuta a fronteira real e compara todo o alinhamento, não só labels."""
    if not casos or len({c['id'] for c in casos}) != len(casos):
        raise ValueError("casos vazios ou identidades duplicadas")
    cobertura = Counter()
    for caso in casos:
        if caso.get("particao") != "desenvolvimento":
            raise ValueError("somente desenvolvimento conhecido pode ser revalidado")
        atual = alinhar_relacoes(caso["fonte"], variantes_permitidas=VARIANTES)
        if atual != caso["alinhado"]:
            raise ValueError(f"alinhamento divergiu: {caso['id']}")
        labels = rotular_ocorrencias({**caso, "alinhado": atual})
        if labels != rotular_ocorrencias(caso):
            raise ValueError(f"projeção divergiu: {caso['id']}")
        cobertura.update(labels)
    return {"casos": len(casos), "tokens": sum(cobertura.values()),
            "rotulos": dict(cobertura), "alinhamentos_identicos": True}


def carregar_perfil_revalidado() -> tuple[list[dict], list[dict], dict]:
    """Nova via explícita: comparação integral obrigatória a cada chamada.

    Não altera carregar_base/carregar_perfil históricos nem certifica os
    resultados dos classificadores treinados sob aquelas versões.
    """
    protocolo = FONTE / "protocolo.json"
    dependencias = json.loads(protocolo.read_text(encoding="utf-8"))["codigo_sha256"]
    arquivos = [protocolo, FONTE / "lote.json", PASTA_FONTE / "lote.json",
                PASTA_FONTE / "resultado.json", Path(__file__)]
    arquivos += [BASE / nome for nome in dependencias]
    # Inclui o código da projeção e seus consumidores, além das dependências
    # declaradas no protocolo original. Nenhum hash representa todo o runtime.
    arquivos += [Path(__file__).with_name(n) for n in (
        "comparar_ocorrencias_v4.py", "expandir_relacoes_v4.py", "candidato_relacional.py",
        "diagnosticar_head_relacional.py", "curadoria_encoder.py")]
    hashes = {str(p.resolve()): _hash(p) for p in arquivos}
    if any(h is None for h in hashes.values()):
        raise FileNotFoundError("fonte ou dependência da revalidação ausente")
    divergencias = conferir_dependencias(dependencias, hashes)
    bases = []
    resultados = []
    for pasta, sha, quantidade in ((FONTE, SHA_FONTE, 672), (PASTA_FONTE, SHA_LOTE, 1176)):
        bruto = (pasta / "lote.json").read_bytes()
        if hashlib.sha256(bruto).hexdigest() != sha:
            raise ValueError("lote histórico mudou; revalidação abortada")
        dados = json.loads(bruto)
        if any(dados.get(k) is not False for k in FLAGS) or len(dados["casos"]) != quantidade:
            raise ValueError("lote fora do contrato histórico")
        bases.append(dados["casos"])
        resultados.append(conferir_casos(dados["casos"]))
    casos = bases[1]
    dobras = preparar_dobras(casos, {c["id"]: c["grupo_validacao"] for c in casos})
    historico = json.loads((PASTA_FONTE / "resultado.json").read_text(encoding="utf-8"))
    if dobras != historico["dobras"]:
        raise ValueError("dobras divergiram; não atualizar partições")
    if hashes != {str(p.resolve()): _hash(p) for p in arquivos}:
        raise RuntimeError("fontes mudaram durante revalidação")
    relatorio = {"perfil": "compatibilidade_projecao_v4", "arquivos_sha256": hashes,
                 "dependencias_alteradas": divergencias, "lotes": resultados,
                 "casos_unicos": len({c['id'] for base in bases for c in base}),
                 "dobras_identicas": True, "quantidade_dobras": len(dobras),
                 "compatibilidade_no_corpus": True, "classificador_reavaliado": False,
                 "runtime_validado": False, "guardas_historicas_alteradas": False, **FLAGS}
    return casos, dobras, relatorio


def executar(destino: Path) -> dict:
    if destino.exists():
        raise FileExistsError("preservar revalidação anterior")
    _, _, relatorio = carregar_perfil_revalidado()
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as arquivo:
        json.dump(relatorio, arquivo, ensure_ascii=False, indent=2)
    return relatorio


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    args = parser.parse_args()
    resultado = executar(args.destino)
    print(json.dumps({k: resultado[k] for k in (
        "compatibilidade_no_corpus", "casos_unicos", "dobras_identicas", "dependencias_alteradas")}, ensure_ascii=False))
