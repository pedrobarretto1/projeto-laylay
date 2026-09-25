"""Contrastes de desenvolvimento para pedidos indiretos.

Somente o command head consome estes rótulos. As probes usam construções e
entidades separadas e são diagnóstico de desenvolvimento, nunca promoção.
"""

from __future__ import annotations

import json
from pathlib import Path


CONFIGS = {
    "MUSIC_SEARCH": {
        "domain": "music",
        "action": "search",
        "treino": (
            "Legião Urbana", "Djavan", "Rita Lee", "Marisa Monte",
        ),
        "probe": ("Milton Nascimento", "Gal Costa"),
        "acao": lambda nome: f"colocar {nome}",
        "acao_alt": lambda nome: f"ouvir {nome}",
    },
    "APP_OPEN": {
        "domain": "app",
        "action": "open",
        "treino": ("calculadora", "bloco de notas", "paint", "firefox"),
        "probe": ("vlc", "wordpad"),
        "acao": lambda nome: f"abrir o {nome}",
        "acao_alt": lambda nome: f"usar o {nome} agora",
    },
    "OPEN_URL": {
        "domain": "browser",
        "action": "open",
        "treino": ("github", "mdn", "site do python", "stackoverflow"),
        "probe": ("w3schools", "archive.org"),
        "acao": lambda nome: f"entrar no {nome}",
        "acao_alt": lambda nome: f"acessar o {nome}",
    },
}
FORMAS_TREINO_POSITIVAS = (
    "seria legal você {acao}",
    "seria bom {acao_alt}",
    "eu queria {acao_alt}",
    "bem que você podia {acao}",
    "eu gostaria de {acao_alt}",
    "tô a fim de {acao_alt}",
)

FORMAS_TREINO_NEGATIVAS = (
    "seria legal saber como {acao}",
    "seria bom saber como {acao_alt}",
    "eu queria saber como {acao}",
    "bem que você podia explicar como {acao}",
    "eu gostaria de aprender como {acao}",
    "tô a fim de saber como {acao}",
)

FORMAS_PROBE_POSITIVAS = (
    "ia ser legal você {acao}",
    "seria ótimo se você pudesse {acao}",
    "eu estava com vontade de {acao_alt}",
)

FORMAS_PROBE_NEGATIVAS = (
    "ia ser legal aprender como {acao}",
    "seria ótimo entender como {acao}",
    "eu estava com vontade de saber como {acao}",
)


def _item(texto: str, intent: str, cfg: dict, positivo: bool, grupo: str) -> dict:
    return {
        "text": texto,
        "intent": intent if positivo else "NONE",
        "is_command": positivo,
        "negated": False,
        "action": cfg["action"] if positivo else "none",
        "family": f"pragmatica_indireta_v1_{intent.lower()}_{grupo}",
        "validation_group": f"pragmatica_indireta_v1_{grupo}",
        "source": "MANUAL_PARAPHRASE" if positivo else "HARD_NEGATIVE",
        "domain": cfg["domain"],
        "training_heads": ["command"],
        "command_head_intent": intent,
    }
def gerar() -> tuple[list[dict], list[dict]]:
    treino: list[dict] = []
    probe: list[dict] = []
    for intent, cfg in CONFIGS.items():
        for indice, nome in enumerate(cfg["treino"]):
            valores = {
                "acao": cfg["acao"](nome),
                "acao_alt": cfg["acao_alt"](nome),
            }
            for forma in FORMAS_TREINO_POSITIVAS:
                treino.append(_item(
                    forma.format(**valores), intent, cfg, True, f"treino_pos_{indice}",
                ))
            for forma in FORMAS_TREINO_NEGATIVAS:
                treino.append(_item(
                    forma.format(**valores), intent, cfg, False, f"treino_neg_{indice}",
                ))
        for indice, nome in enumerate(cfg["probe"]):
            valores = {
                "acao": cfg["acao"](nome),
                "acao_alt": cfg["acao_alt"](nome),
            }
            for forma in FORMAS_PROBE_POSITIVAS:
                probe.append(_item(
                    forma.format(**valores), intent, cfg, True, f"probe_pos_{indice}",
                ))
            for forma in FORMAS_PROBE_NEGATIVAS:
                probe.append(_item(
                    forma.format(**valores), intent, cfg, False, f"probe_neg_{indice}",
                ))
    return treino, probe


def _gravar(caminho: Path, itens: list[dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in itens),
        encoding="utf-8",
    )
def main() -> None:
    treino, probe = gerar()
    pasta = Path(__file__).resolve().parent / "candidatos"
    _gravar(pasta / "pragmatica_pedidos_indiretos_v1.jsonl", treino)
    _gravar(pasta / "pragmatica_pedidos_indiretos_v1_probe.jsonl", probe)
    print(json.dumps({
        "treino": len(treino),
        "probe": len(probe),
        "por_intent_treino": {
            intent: sum(x["command_head_intent"] == intent for x in treino)
            for intent in CONFIGS
        },
        "por_intent_probe": {
            intent: sum(x["command_head_intent"] == intent for x in probe)
            for intent in CONFIGS
        },
        "training_heads": ["command"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
