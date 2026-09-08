"""Congela e audita reserva manual contra datasets conhecidos, sem modelo."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from mente_laylay.especialistas.capacidades import intents_registradas
from .anotacao_escopo import referencia_canonica, validar_anotacao_escopo
from .cobertura import carregar_manifesto_variantes
from .qualidade import auditar_leakage_dataset
from .datasets.gerar_escopo_negacao_v2 import gerar_grade


def validar_reserva(dados: dict, variantes: set[tuple[str, str]]) -> None:
    if (dados.get("tipo") != "reserva_relacional_em_auditoria"
            or any(dados.get(k) is not False for k in (
                "treino_permitido", "autoriza_execucao", "autoriza_promocao"))
            or dados.get("alinhamento_canonico_revisado") is not False
            or dados.get("espaco_offsets") != "texto_entrada"):
        raise ValueError("reserva precisa permanecer isolada e em offsets da fonte")
    casos = dados.get("casos")
    if not isinstance(casos, list) or not casos:
        raise ValueError("reserva vazia")
    ids = set()
    for c in casos:
        if not isinstance(c.get("id"), str) or not c["id"] or c["id"] in ids:
            raise ValueError("id inválido ou repetido")
        ids.add(c["id"])
        if not c.get("familia") or not c.get("dominio"):
            raise ValueError("caso sem família/domínio")
        if len(c["segmentos"]) != 1 or c["segmentos"][0]["texto"] != c["texto_entrada"]:
            raise ValueError("fonte manual deve ser integral")
        # Contrato sintético de spans; não chamar classificador nem fingir
        # que essa segmentação é a composição real da Laylay.
        fonte = {"segmentos": [{"indice": 0, "texto": c["texto_entrada"]}]}
        validar_anotacao_escopo({"versao": 1, "origem": "anotacao_manual",
                                "referencia_sha256": referencia_canonica(fonte)["sha256"],
                                "segmentos": c["segmentos"]},
                               turno=fonte, variantes_permitidas=variantes)


def carregar_corpus(raiz: Path) -> tuple[list[dict], dict]:
    """Inventário explícito de treino/controles locais, não de logs pessoais."""
    ds = raiz / "mente_laylay/neural/datasets"
    experimentos = raiz / "memoria/neural/experimentos"
    jsonls = sorted(ds.rglob("*.jsonl")) + sorted(experimentos.rglob("lote_negacao.jsonl"))
    obrigatorios = [ds / "dev_v0.jsonl", ds / "frozen_v0.jsonl"]
    if any(p not in jsonls for p in obrigatorios):
        raise ValueError("datasets históricos obrigatórios ausentes")
    corpus, fontes = [], {}

    def adicionar(itens, caminho):
        contagem = 0
        for n, i in enumerate(itens, 1):
            texto = i.get("text", i.get("texto_entrada"))
            if not isinstance(texto, str) or not texto.strip():
                raise ValueError(f"registro sem texto: {caminho}:{n}")
            corpus.append({"text": texto, "family": i.get("family", i.get("familia", i.get("grupo_contraste", ""))),
                           "origem": str(caminho), "registro": n})
            contagem += 1
        fontes[str(caminho)] = {"sha256": hashlib.sha256(caminho.read_bytes()).hexdigest(), "registros": contagem}

    for p in jsonls:
        adicionar([json.loads(l) for l in p.read_text(encoding="utf-8-sig").splitlines() if l.strip()], p)
    jsons = [
        (ds / "escopo_relacional_piloto_v1.json", "casos"),
        (raiz / "tests/fixtures/neural/bateria_linguistica_v1.json", "casos"),
        (experimentos / "regioes_controles_aspas_v1_20260906/protocolo.json", "controles"),
    ]
    jsons.extend((experimentos / "escopo_relacional_v2_20260907" / (nome + ".json"), "casos")
                 for nome in ("desenvolvimento", "reserva_entidades", "reserva_construcoes", "reserva_ambas"))
    for p, chave in jsons:
        adicionar(json.loads(p.read_text(encoding="utf-8"))[chave], p)
    # Inclui também as reservas geradas do escopo booleano, não só seus lotes
    # de treino persistidos. A grade não consulta LLM nem modifica estado.
    adicionar(gerar_grade(), ds / "gerar_escopo_negacao_v2.py")
    return corpus, fontes


def executar(*, raiz: Path, reserva: Path, destino: Path) -> dict:
    if destino.exists():
        raise FileExistsError("preservar congelamento anterior")
    bruto = reserva.read_bytes()
    dados = json.loads(bruto)
    manifesto_path = raiz / "mente_laylay/neural/datasets/catalogo_variantes_v0.json"
    manifesto = carregar_manifesto_variantes(manifesto_path, intents_catalogadas=intents_registradas())
    variantes = {(v["intent"], v["action"]) for v in manifesto["variants"]}
    validar_reserva(dados, variantes)
    corpus, fontes = carregar_corpus(raiz)
    destino.mkdir(parents=True, exist_ok=False)
    protocolo = {"sha256_reserva": hashlib.sha256(bruto).hexdigest(), "reserva_fonte": str(reserva),
                 "fontes_corpus": fontes, "registros_historicos": len(corpus),
                 "fontes_codigo": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
                     Path(__file__), manifesto_path, Path(__file__).with_name("qualidade.py"),
                     Path(__file__).with_name("anotacao_escopo.py"))},
                 "treino_permitido": False, "autoriza_execucao": False, "autoriza_promocao": False,
                 "limiar_similaridade": 0.9}
    # Congelamento antes de calcular similaridades: não selecionar os textos
    # pelos resultados e não sobrescrever um protocolo já observado.
    with (destino / "reserva_congelada.json").open("xb") as f:
        f.write(bruto)
    with (destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    print(f"Reserva congelada. Comparando {len(corpus)} registros com {len(dados['casos'])} casos.", flush=True)
    novos = [{"text": c["texto_entrada"], "family": c["familia"]} for c in dados["casos"]]
    auditoria = auditar_leakage_dataset(corpus, novos)
    for nome, metadados in fontes.items():
        if hashlib.sha256(Path(nome).read_bytes()).hexdigest() != metadados["sha256"]:
            raise ValueError("fonte mudou durante auditoria")
    r = {"auditoria_lexical": auditoria, "total_reserva": len(novos),
         "cobertura_dominios": dict(Counter(c["dominio"] for c in dados["casos"])),
         "cobertura_atos": dict(Counter(a["ato"] for c in dados["casos"] for s in c["segmentos"] for a in s["acoes"])),
         "alinhamento_canonico_revisado": False, "modelo_avaliado": False,
         "treino_permitido": False, "autoriza_execucao": False, "autoriza_promocao": False,
         "limites": ["Auditoria lexical não prova independência semântica.",
                     "Cobertura limitada às fontes inventariadas; não inclui todos os logs de conversa.",
                     "Anotações em offsets da fonte ainda precisam de revisão de alinhamento.",
                     "32 casos não certificam todas as intenções nem risco operacional."]}
    with (destino / "auditoria.json").open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--destino", type=Path, required=True)
    args = p.parse_args()
    raiz = Path(__file__).resolve().parents[2]
    r = executar(raiz=raiz, reserva=Path(__file__).with_name("datasets") / "reserva_relacional_independente_v1.json", destino=args.destino)
    print(json.dumps(r["auditoria_lexical"]["totais"]))


if __name__ == "__main__":
    main()
