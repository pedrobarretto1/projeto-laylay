"""Contrastes manuais fatoriais: artefatos de pesquisa, ainda sem treino."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

PARES = (("zafrin", "pelvora"), ("mezdar", "tuvlen"), ("quensir", "jovrul"))

# Família 2 e par 2 são reservas desta grade, definidos antes de inferência.
FORMAS = (
    {"pedido": "{verbo} {a}, não {b}", "recusa": "não {verbo} {a}",
     "alternativa": "{verbo} {outro}, menos {a}",
     "relato": "ontem ela disse para {infinitivo} {a}"},
    {"pedido": "em vez de {b}, {verbo} {a}", "recusa": "evite {infinitivo} {a}",
     "alternativa": "{verbo} {outro}, exceto {a}",
     "relato": "ela comentou que queria {infinitivo} {a}"},
    {"pedido": "o que eu quero é {infinitivo} {a}; descarte {b}",
     "recusa": "meu pedido é que você não {verbo} {a}",
     "alternativa": "escolha {outro} para {infinitivo}, deixando {a} de fora",
     "relato": "na conversa de ontem, ela mencionou {a}"},
)


def gerar_grade_relacional() -> list[dict]:
    """Slots e papéis definidos nos moldes, nunca extraídos por uma previsão."""
    casos = []
    for entidade, (a, b) in enumerate(PARES):
        dominios = (
            ("apps", "APP_OPEN", "open", "abra", "abrir", "o aplicativo chamado", "outro aplicativo", a, b),
            ("musica", "MUSIC_SEARCH", "search", "toque", "tocar", "a faixa chamada", "outra faixa", f"não volte {a}", f"não volte {b}"),
            ("arquivos", "FILE_READ", "read", "leia", "ler", "o arquivo chamado", "outro arquivo", f"não apagar {a}.txt", f"não apagar {b}.txt"),
        )
        for familia, formas in enumerate(FORMAS):
            particao = ("desenvolvimento" if entidade < 2 and familia < 2 else
                        "reserva_entidades" if familia < 2 else
                        "reserva_construcoes" if entidade < 2 else "reserva_ambas")
            for dominio, intent, action, verbo, infinitivo, objeto, outro, alvo_a, alvo_b in dominios:
                for aspas in (False, True):
                    envolver = lambda s: f'"{s}"' if aspas else s
                    for mecanismo, molde in formas.items():
                        texto = molde.format(verbo=verbo, infinitivo=infinitivo, outro=outro,
                                             a=f"{objeto} {envolver(alvo_a)}", b=f"{objeto} {envolver(alvo_b)}")

                        def mencao(alvo: str) -> dict:
                            if texto.count(alvo) != 1:
                                raise ValueError("slot manual não é único")
                            inicio = texto.index(alvo)
                            return {"inicio": inicio, "fim": inicio + len(alvo), "texto": alvo}

                        ato = "pedido" if mecanismo == "alternativa" else mecanismo
                        resolucao = ("alternativa" if mecanismo == "alternativa" else
                                     "explicito" if ato == "pedido" else "nao_aplicavel")
                        acao = {"intent": intent, "action": action, "ato": ato,
                                "resolucao_alvo": resolucao,
                                "alvos_solicitados": [mencao(alvo_a)] if mecanismo == "pedido" else [],
                                "alvos_excluidos": ([mencao(alvo_b)] if mecanismo == "pedido" else
                                                    [mencao(alvo_a)] if mecanismo in {"recusa", "alternativa"} else []),
                                "alvos_mencionados": [mencao(alvo_a)] if mecanismo == "relato" else []}
                        casos.append({
                            "id": f"rel_v2_e{entidade}_f{familia}_{dominio}_{mecanismo}_q{int(aspas)}",
                            "texto_entrada": texto, "particao": particao,
                            "grupo_entidades": f"rel_v2_e{entidade}",
                            "grupo_construcao": f"rel_v2_f{familia}",
                            "grupo_contraste": f"rel_v2_e{entidade}_f{familia}_{dominio}_{mecanismo}",
                            "dominio": dominio, "mecanismo": mecanismo, "com_aspas": aspas,
                            "segmentos": [{"indice": 0, "texto": texto, "acoes": [acao]}],
                        })
    return casos


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    args = parser.parse_args()
    if args.destino.exists():
        raise FileExistsError("preservar partições anteriores")
    casos = gerar_grade_relacional()
    # Congela TODOS os textos/rótulos antes de qualquer avaliação de modelo.
    args.destino.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for particao in sorted({c["particao"] for c in casos}):
        dados = {"versao": 1, "tipo": "piloto_anotacao_escopo_manual",
                 "treino_permitido": False, "autoriza_execucao": False,
                 "casos": [c for c in casos if c["particao"] == particao]}
        caminho = args.destino / (particao + ".json")
        with caminho.open("x", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        hashes[caminho.name] = hashlib.sha256(caminho.read_bytes()).hexdigest()
    protocolo = {"versao": 1, "fontes": {str(Path(__file__)): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
                 "particoes": dict(Counter(c["particao"] for c in casos)), "sha256_particoes": hashes,
                 "treino_permitido": False, "autoriza_promocao": False, "autoriza_execucao": False,
                 "reservas_relativas_a_grade": True, "historico_booleano_preservado": True}
    with (args.destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    print(json.dumps(protocolo["particoes"]))


if __name__ == "__main__":
    main()
