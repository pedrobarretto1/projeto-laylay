"""Perfil explícito autorizado de desenvolvimento; reservas nunca são abertas.

As anotações de avaliação permanecem imutáveis e proibidas para treino direto.
Este perfil deriva supervisão SOMENTE dos 96 registros de desenvolvimento
revisados e fixados por hash. Não é feedback automático nem promoção.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import platform
import time
import warnings

import joblib
import sklearn
from threadpoolctl import threadpool_limits

from .anotacao_escopo import validar_anotacao_escopo
from .avaliacao_escopo import avaliar_escopo
from .candidato_relacional import CandidatoRelacional, PARAMETROS

BASE = Path(__file__).resolve().parents[2]
FONTES = {
    "memoria/neural/experimentos/escopo_relacional_v2_20260907/desenvolvimento.json":
        "ddcc5e1d1306926f4a654e9b95660720ccbada7cbce7ad530f2e1e15ccb73826",
    "resultados_testes/revisao_vinculos_segmentos_20260907.json":
        "a6a854d64465bb683d8f4c724f5f7ea2ef6c4cdcb0c5ff0509d6ff42cfbaa632",
}
VARIANTES = {("APP_OPEN", "open"), ("MUSIC_SEARCH", "search"), ("FILE_READ", "read")}


def exportar_supervisao(fontes: list[dict], sidecars: list[dict]) -> list[dict]:
    """Validar todo o lote antes de derivar qualquer supervisão autorizada."""
    por_id = {c["id"]: c for c in fontes}
    if (len(por_id) != len(fontes) or len({c["id"] for c in sidecars}) != len(sidecars)
            or set(por_id) != {c["id"] for c in sidecars}):
        raise ValueError("fontes e alinhamentos divergentes")
    exportados = []
    for c in sidecars:
        f = por_id[c["id"]]
        if (f.get("particao") != "desenvolvimento"
                or c.get("papel_dataset", "desenvolvimento") != "desenvolvimento"
                or c.get("treino_permitido") is not False
                or c.get("autoriza_execucao") is not False
                or c.get("autoriza_promocao") is not False
                or f["texto_entrada"] != c["texto_entrada"]):
            raise ValueError("reserva ou fonte incompatível: exportação proibida")
        validar_anotacao_escopo(c["anotacao"], turno=c["referencia"]["leitura_observada"],
                               variantes_permitidas=VARIANTES)
        exportados.append({
            "id": c["id"], "perfil_treino": "desenvolvimento_relacional_v1",
            "papel_dataset": "desenvolvimento", "autoriza_execucao": False,
            "autoriza_promocao": False,
            "entrada": {"texto_entrada": c["texto_entrada"], "segmentos": [
                {k: s[k] for k in ("indice", "texto")} for s in c["anotacao"]["segmentos"]]},
            "segmentos_anotados": deepcopy(c["anotacao"]["segmentos"]),
            **{k: f[k] for k in ("grupo_construcao", "grupo_entidades", "grupo_contraste")},
        })
    return exportados


def carregar_desenvolvimento(base: Path = BASE) -> tuple[list[dict], list[dict]]:
    conteudos = []
    for caminho, esperado in FONTES.items():
        bruto = (base / caminho).read_bytes()
        if hashlib.sha256(bruto).hexdigest() != esperado:
            raise ValueError("fonte congelada divergiu; não atualizar hash automaticamente")
        conteudos.append(json.loads(bruto)["casos"])
    exemplos = exportar_supervisao(*conteudos)
    if len(exemplos) != 96:
        raise ValueError("perfil exige os 96 exemplos revisados")
    return exemplos, conteudos[1]


def particoes_por_grupo(exemplos: list[dict], eixo: str) -> list[tuple[list[int], list[int]]]:
    if eixo not in {"grupo_construcao", "grupo_entidades"}:
        raise ValueError("eixo não pré-registrado")
    grupos = sorted({e[eixo] for e in exemplos})
    if len(grupos) < 2:
        raise ValueError("validação exige grupos independentes")
    partes = []
    for grupo in grupos:
        treino = [i for i, e in enumerate(exemplos) if e[eixo] != grupo]
        teste = [i for i, e in enumerate(exemplos) if e[eixo] == grupo]
        if ({exemplos[i]["grupo_contraste"] for i in treino}
                & {exemplos[i]["grupo_contraste"] for i in teste}):
            raise ValueError("irmãos de contraste vazaram entre treino e teste")
        partes.append((treino, teste))
    return partes


def executar(saida: Path) -> dict:
    exemplos, sidecars = carregar_desenvolvimento()
    saida.mkdir(parents=True, exist_ok=False)
    protocolo = {
        "perfil_treino": "desenvolvimento_relacional_v1", "fontes": FONTES,
        "parametros": PARAMETROS, "python": platform.python_version(),
        "sklearn": sklearn.__version__, "total_desenvolvimento": len(exemplos),
        "variantes": sorted(VARIANTES), "somente_experimento": True,
        "autoriza_execucao": False, "autoriza_promocao": False,
        "reservas_usadas": False, "ajuste_hiperparametros": False,
        "avaliacoes": ["grupo_construcao", "grupo_entidades"],
        "decodificacao": "BIO inválido é falha de inferência, sem reparo por gabarito",
        "codigo_sha256": {nome: hashlib.sha256((Path(__file__).parent / nome).read_bytes()).hexdigest()
                          for nome in ("candidato_relacional.py", "treinar_relacional_isolado.py",
                                       "avaliacao_escopo.py", "anotacao_escopo.py")},
        "ids_desenvolvimento": [e["id"] for e in exemplos],
    }
    # Congelado ANTES de qualquer fit. Diretório exclusivo: nunca sobrescrever.
    with (saida / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    inicio = time.perf_counter()
    relatorio = {"validacoes": {}, "reservas_avaliadas": False,
                 "comparacao_com_runtime": False, "autoriza_promocao": False,
                 "autoriza_execucao": False}
    with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        for eixo in protocolo["avaliacoes"]:
            dobras = []
            for treino, teste in particoes_por_grupo(exemplos, eixo):
                candidato = CandidatoRelacional().ajustar([exemplos[i] for i in treino])
                medido = avaliar_escopo([sidecars[i] for i in teste], prever=candidato.prever,
                                       variantes_permitidas=VARIANTES)
                dobras.append({"ids_treino": [exemplos[i]["id"] for i in treino],
                               "ids_teste": [exemplos[i]["id"] for i in teste], "metricas": medido})
            relatorio["validacoes"][eixo] = dobras
        final = CandidatoRelacional().ajustar(exemplos)
        relatorio["ajuste_in_sample_nao_generalizacao"] = avaliar_escopo(
            sidecars, prever=final.prever, variantes_permitidas=VARIANTES)
        joblib.dump(final, saida / "candidato_offline.joblib")
        relatorio["avisos"] = [{"tipo": a.category.__name__, "mensagem": str(a.message)} for a in avisos]
    relatorio["segundos"] = time.perf_counter() - inicio
    relatorio["candidato_sha256"] = hashlib.sha256((saida / "candidato_offline.joblib").read_bytes()).hexdigest()
    with (saida / "resultado.json").open("x", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
    return relatorio


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    r = executar(args.saida)
    print(json.dumps({"segundos": r["segundos"], "validacoes": {
        eixo: [d["metricas"]["totais"] for d in dobras] for eixo, dobras in r["validacoes"].items()
    }, "reservas_avaliadas": False, "autoriza_promocao": False}, ensure_ascii=False))
