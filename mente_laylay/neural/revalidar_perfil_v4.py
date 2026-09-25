"""Revalidação explícita offline, sem substituir os protocolos históricos."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .curadoria_encoder import _hash
from .anotacao_escopo import referencia_canonica
from .candidato_relacional import validar_entrada
from .expandir_relacoes_v4 import BASE, FONTE, SHA_FONTE, preparar_dobras
from .comparar_ocorrencias_v4 import PASTA_FONTE, SHA_LOTE, rotular_ocorrencias
from .preparar_lote_relacional_v3 import VARIANTES
from .supervisao_relacoes_v4 import FLAGS, PAPEIS, alinhar_relacoes


# Migração explicitamente revisada; não aceitar outra mudança só porque os
# exemplos atuais continuam iguais. O replay integral abaixo segue obrigatório.
NORMALIZADOR_REVISADO = "mente_laylay/cognicao/normalizacao_linguagem.py"
HASHES_REVISADOS = (
    "fb48a34a71c6c94faf9fe0e031282e3ea73e956bf9b940c258ba30d5eee7fb69",
    "850dbbce1423fdca7162c47978618a73a727081ca7d9fc374d850277ae57bf55",
)

# Primeira revisão offline de 21/09: 144 leituras diferentes e 48
# resegmentações. Preservada aqui como evidência histórica; não é autorização
# para aceitar a linguagem atual.
HASH_MODALIDADE_REPROJECAO_V1 = (
    "403781e0c8171d6a355c9a9a0a2db6b2d3dab821566f2e64402a124212a4b8b4"
)
SHA_DIVERGENCIAS_REPROJECAO_V1 = (
    "be76d3f3b31429191dd14695a3af01cf2d7fe30a59ae582a5dc98ca97158b312"
)

# Segunda revisão offline de 21/09: a moldura declarativa
# "não é para + infinitivo operacional" passou a ser recusa atômica. O replay
# integral preservou gold, offsets absolutos e dobras, mas passou a registrar
# 160 leituras diferentes; 48 continuam envolvendo resegmentação.
REPROJECAO_REVISADA = {
    NORMALIZADOR_REVISADO: (
        HASHES_REVISADOS[0],
        "e14e8ef31351878cbb4b2d302ce95b39d0e1eb31848574bb42b61d0f9a97202e",
    ),
    "mente_laylay/cognicao/modalidade_turno.py": (
        "e1bef38f0195c52ec754ea937ac1f5c9e4a3bcd387bba1923352516ab5028e5a",
        "7dbe01fbc8f5090e30307c41003739fcc45f7e1849d0704632e80895783b6a56",
    ),
}
# Ambos os lotes contêm a mesma lista revisada de divergências. Qualquer nova
# diferença futura continua bloqueada, mesmo se os rótulos gold coincidirem.
SHA_DIVERGENCIAS_REVISADAS = "260bfdda4382a66addf3891da94fedb2af0d5137653de757b9fd8031991a2e8c"


def conferir_dependencias(dependencias: dict, hashes: dict, *, reprojetar: bool = False) -> dict:
    alteradas = {}
    for nome, antigo in dependencias.items():
        atual = hashes[str((BASE / nome).resolve())]
        if antigo == atual:
            continue
        revisadas = REPROJECAO_REVISADA if reprojetar else {NORMALIZADOR_REVISADO: HASHES_REVISADOS}
        if (antigo, atual) != revisadas.get(nome.replace("\\", "/")):
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


def _hash_json(dados: object) -> str:
    return hashlib.sha256(json.dumps(
        dados, sort_keys=True, ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")).hexdigest()


def _supervisao_literal(alinhado: dict) -> dict:
    """Compara conteúdo anotado, não índices relativos de uma segmentação.

    Somente transporte literal unívoco; normalização com edições exige outro
    perfil. Preserva todos os campos da supervisão e valida cada span antes
    de convertê-lo. Não interpreta texto nem deriva gold da leitura observada.
    """
    if (set(alinhado) != {"versao", "entrada", "supervisao", "referencia", "proveniencia", *FLAGS}
            or alinhado["versao"] != 4 or alinhado["proveniencia"]
            or any(alinhado[k] is not False for k in FLAGS)):
        raise ValueError("reprojeção exige perfil literal isolado")
    entrada = alinhado["entrada"]
    validar_entrada(entrada)
    ref = alinhado["referencia"]
    if ref != referencia_canonica(ref["leitura_observada"]):
        raise ValueError("referência histórica inconsistente")
    if entrada["segmentos"] != [
        {k: s[k] for k in ("indice", "texto")} for s in ref["leitura_observada"]["segmentos"]
    ]:
        raise ValueError("referência não corresponde à entrada")
    original = entrada["texto_entrada"]
    segmentos = {}
    anterior = 0
    for s in entrada["segmentos"]:
        texto = s["texto"]
        if original.count(texto) != 1:
            raise ValueError("segmento sem projeção literal única")
        inicio = original.index(texto)
        if inicio < anterior:
            raise ValueError("segmentos sobrepostos ou fora de ordem")
        segmentos[s["indice"]] = (inicio, texto)
        anterior = inicio + len(texto)
    supervisao = deepcopy(alinhado["supervisao"])
    for no in supervisao["nos"]:
        spans = [no["ancora"]] + [s for papel in PAPEIS.values() for s in no[papel]]
        for span in spans:
            if set(span) != {"segmento", "inicio", "fim", "texto"} or span["segmento"] not in segmentos:
                raise ValueError("span sem segmento válido")
            offset, texto = segmentos[span["segmento"]]
            a, b = span["inicio"], span["fim"]
            if (type(a) is not int or type(b) is not int or not 0 <= a < b <= len(texto)
                    or texto[a:b] != span["texto"]):
                raise ValueError("span incompatível com segmento")
            span.pop("segmento")
            span.update(inicio=offset + a, fim=offset + b)
    return {"texto_entrada": original, "supervisao": supervisao}


def reprojetar_casos(casos: list[dict]) -> tuple[list[dict], dict]:
    """Nova leitura, mesma anotação independente; nunca altera os casos fonte."""
    if not casos or len({c["id"] for c in casos}) != len(casos):
        raise ValueError("casos vazios ou identidades duplicadas")
    novos, divergencias = [], []
    cobertura = Counter()
    segmentacoes = 0
    for caso in casos:
        if caso.get("particao") != "desenvolvimento":
            raise ValueError("somente desenvolvimento conhecido pode ser reprojetado")
        antigo = caso["alinhado"]
        atual = alinhar_relacoes(caso["fonte"], variantes_permitidas=VARIANTES)
        if _supervisao_literal(antigo) != _supervisao_literal(atual):
            raise ValueError(f"supervisão literal divergiu: {caso['id']}")
        labels = rotular_ocorrencias({**caso, "alinhado": atual})
        if labels != rotular_ocorrencias(caso):
            raise ValueError(f"projeção divergiu: {caso['id']}")
        cobertura.update(labels)
        if antigo != atual:
            divergencias.append({"id": caso["id"],
                "campos": sorted(k for k in set(antigo) | set(atual) if antigo.get(k) != atual.get(k)),
                "historico_sha256": _hash_json(antigo), "atual_sha256": _hash_json(atual)})
        segmentacoes += antigo["entrada"]["segmentos"] != atual["entrada"]["segmentos"]
        novo = deepcopy(caso)
        novo["alinhado"] = atual
        novos.append(novo)
    return novos, {"casos": len(casos), "tokens": sum(cobertura.values()),
        "rotulos": dict(cobertura), "alinhamentos_identicos": not divergencias,
        "supervisao_literal_preservada": True, "casos_alterados": len(divergencias),
        "segmentacoes_alteradas": segmentacoes, "divergencias": divergencias,
        "divergencias_sha256": _hash_json(divergencias)}


def _carregar_bases(*, reprojetar: bool) -> tuple[list[list[dict]], list[dict], dict]:
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
    divergencias = conferir_dependencias(dependencias, hashes, reprojetar=reprojetar)
    bases = []
    resultados = []
    for pasta, sha, quantidade in ((FONTE, SHA_FONTE, 672), (PASTA_FONTE, SHA_LOTE, 1176)):
        bruto = (pasta / "lote.json").read_bytes()
        if hashlib.sha256(bruto).hexdigest() != sha:
            raise ValueError("lote histórico mudou; revalidação abortada")
        dados = json.loads(bruto)
        if any(dados.get(k) is not False for k in FLAGS) or len(dados["casos"]) != quantidade:
            raise ValueError("lote fora do contrato histórico")
        if reprojetar:
            casos, resultado = reprojetar_casos(dados["casos"])
            if resultado["divergencias_sha256"] != SHA_DIVERGENCIAS_REVISADAS:
                raise ValueError("divergências fora da reprojeção revisada")
        else:
            casos, resultado = dados["casos"], conferir_casos(dados["casos"])
        bases.append(casos)
        resultados.append(resultado)
    casos = bases[1]
    dobras = preparar_dobras(casos, {c["id"]: c["grupo_validacao"] for c in casos})
    historico = json.loads((PASTA_FONTE / "resultado.json").read_text(encoding="utf-8"))
    if dobras != historico["dobras"]:
        raise ValueError("dobras divergiram; não atualizar partições")
    if hashes != {str(p.resolve()): _hash(p) for p in arquivos}:
        raise RuntimeError("fontes mudaram durante revalidação")
    relatorio = {"perfil": "reprojecao_literal_v4_20260921_recusa_declarativa_v2" if reprojetar else "compatibilidade_projecao_v4",
                 "arquivos_sha256": hashes,
                 "dependencias_alteradas": divergencias, "lotes": resultados,
                 "casos_unicos": len({c['id'] for base in bases for c in base}),
                 "dobras_identicas": True, "quantidade_dobras": len(dobras),
                 "compatibilidade_no_corpus": not reprojetar,
                 "supervisao_literal_preservada": True, "classificador_reavaliado": False,
                 "runtime_validado": False, "guardas_historicas_alteradas": False, **FLAGS}
    return bases, dobras, relatorio


def carregar_perfil_revalidado(*, reprojetar: bool = False) -> tuple[list[dict], list[dict], dict]:
    """Replay estrito por padrão; reprojeção literal exige opt-in e nova prova."""
    bases, dobras, relatorio = _carregar_bases(reprojetar=reprojetar)
    return bases[1], dobras, relatorio


def carregar_base_reprojetada() -> list[dict]:
    """Base de desenvolvimento atual, após todas as guardas da reprojeção."""
    bases, _, _ = _carregar_bases(reprojetar=True)
    return bases[0]


def executar(destino: Path, *, reprojetar: bool = False) -> dict:
    if destino.exists():
        raise FileExistsError("preservar revalidação anterior")
    _, _, relatorio = carregar_perfil_revalidado(reprojetar=reprojetar)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as arquivo:
        json.dump(relatorio, arquivo, ensure_ascii=False, indent=2)
    return relatorio


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    parser.add_argument("--reprojetar", action="store_true", help="nova leitura; não certifica equivalência histórica")
    args = parser.parse_args()
    resultado = executar(args.destino, reprojetar=args.reprojetar)
    print(json.dumps({k: resultado[k] for k in (
        "compatibilidade_no_corpus", "casos_unicos", "dobras_identicas", "dependencias_alteradas")}, ensure_ascii=False))
