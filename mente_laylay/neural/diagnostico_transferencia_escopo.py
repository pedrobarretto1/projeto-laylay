"""Inspeção do candidato local já ajustado, sem fit nem alteração de pesos."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib

from .diagnostico_pistas_negacao import comparar_pistas, explicar_pistas


PARES = (
    ("apps_alvo", "inicie o Cedrion, não o Belmora", "inicie o Opera, não o Firefox"),
    ("apps_verbo", "inicie o Opera, não o Firefox", "abre o Opera, não o Firefox"),
    ("apps_aspas", "abre o Opera, não o Firefox", 'abre o "Opera", não o "Firefox"'),
    ("audio_valores", "ajuste o áudio para 14, não para 28", "ajuste o áudio para 30, não para 50"),
    ("audio_moldura", "ajuste o áudio para 30, não para 50", "coloca o volume em 30, não em 50"),
    ("musica_titulo", 'reproduza a canção "Rota Cedrion", não a canção "Rota Belmora"',
     'reproduza a canção "Brisa", não a canção "Aurora"'),
    ("musica_moldura", 'reproduza a canção "Brisa", não a canção "Aurora"',
     'toca a música "Brisa", não a "Aurora"'),
    ("musica_aspas", 'toca a música "Brisa", não a "Aurora"', "toca a música Brisa, não a Aurora"),
    ("arquivo_alvo", "leia inventario_Cedrion.txt, não inventario_Belmora.txt",
     "leia rascunho.txt, não relatório.txt"),
    ("arquivo_moldura", "leia rascunho.txt, não relatório.txt",
     "abre o arquivo rascunho.txt, não o relatório.txt"),
    ("recusa_controle", "inicie o Cedrion, não o Belmora", "não quero que você inicie o Cedrion"),
)


def diagnosticar(*, experimento: Path, saida: Path) -> dict:
    if saida.exists():
        raise FileExistsError("preservar diagnóstico anterior")
    cabeca_path = experimento / "cabeca_negacao_nao_promovida.joblib"
    protocolo_path = experimento / "protocolo.json"
    protocolo = json.loads(protocolo_path.read_text(encoding="utf-8"))
    if protocolo["representacao"] != "lexical_mais_escopo_local":
        raise ValueError("candidato incompatível")
    for nome, digest in protocolo["fontes"].items():
        if hashlib.sha256(Path(nome).read_bytes()).hexdigest() != digest:
            raise ValueError(f"componente do candidato mudou: {nome}")
    digest = hashlib.sha256(cabeca_path.read_bytes()).hexdigest()
    h = joblib.load(cabeca_path)
    if [n for n, _ in h.named_steps["features"].transformer_list] != ["palavras", "caracteres", "escopo_local"]:
        raise ValueError("canais incompatíveis")
    pares = {nome: comparar_pistas(h, a, b) for nome, a, b in PARES}
    textos = list(dict.fromkeys(t for _, a, b in PARES for t in (a, b)))
    explicacoes = [explicar_pistas(h, t) for t in textos]
    if hashlib.sha256(cabeca_path.read_bytes()).hexdigest() != digest:
        raise ValueError("cabeça mudou durante diagnóstico")
    r = {"autoriza_promocao": False, "autoriza_execucao": False, "treino_executado": False,
         "limites": ["pares diagnósticos escolhidos após observar erros; não medem acurácia inédita",
                    "moldura pode alterar verbo, substantivo e preposição; não atribuir tudo ao verbo",
                    "aspas são citação, não prova de autorização ou alvo"],
         "sha256_cabeca": digest, "sha256_protocolo": hashlib.sha256(protocolo_path.read_bytes()).hexdigest(),
         "sha256_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         "pares": pares, "explicacoes": explicacoes}
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--experimento", type=Path, required=True)
    p.add_argument("--saida", type=Path, required=True)
    r = diagnosticar(**vars(p.parse_args()))
    print(json.dumps({n: {"antes": p["antes"]["score"], "depois": p["depois"]["score"],
                           "mudou": p["mudou_decisao"]} for n, p in r["pares"].items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
