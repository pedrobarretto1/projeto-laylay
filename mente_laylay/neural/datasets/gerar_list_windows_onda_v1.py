"""Gera cobertura contrastiva da consulta de aplicativos e janelas.

O lote ensina LIST_WINDOWS:list sem confundir consulta de estado com APP_OPEN,
CLOSE_APP ou LIST_TABS. Ele permanece em staging: não treina, não promove e
não concede autoridade operacional.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


MOLDURAS = (
    ("direta", "{verbo} {alvo}"),
    ("polida", "por favor {verbo} {alvo}"),
    ("modal", "pode {verbo} {alvo}"),
)

ALVOS_INVENTARIO = (
    "os aplicativos abertos",
    "os programas em execução",
    "os apps rodando",
    "os programas com janela aberta",
    "as janelas de aplicativos abertas",
    "os processos com janela aberta",
)

VERBOS_INVENTARIO = ("lista", "listar", "mostra", "mostrar")

APLICATIVOS = (
    ("o Discord", "aberto"),
    ("o Spotify", "aberto"),
    ("a calculadora", "aberta"),
    ("o bloco de notas", "aberto"),
    ("o VS Code", "aberto"),
    ("o explorador de arquivos", "aberto"),
)

FRASES_RUNTIME_RESERVADAS = (
    "O Opera está aberto?",
    "A microsoft store está aberta?",
    "A microsoft store continua aberta?",
    "O Prime Video está aberto?",
    "qual dos dois ainda está aberto?",
)

CONSULTAS_ALVO = (
    ("esta_aberto", "{alvo} está {estado}"),
    ("continua_aberto", "{alvo} continua {estado}"),
    ("ainda_aberto", "{alvo} ainda está {estado}"),
    ("esta_rodando", "{alvo} está rodando"),
    ("continua_rodando", "{alvo} continua rodando"),
    ("ainda_rodando", "{alvo} ainda está rodando"),
    ("ta_aberto", "{alvo} tá {estado}"),
    ("ta_rodando", "{alvo} ta rodando"),
)

NEGADAS = (
    ("nao_lista", "não lista {alvo}"),
    ("nao_listar", "não quero listar {alvo}"),
    ("nao_mostra", "não mostra {alvo}"),
    ("nao_mostrar", "não precisa mostrar {alvo}"),
    ("evitar", "evite listar {alvo}"),
    ("preferir", "prefiro não listar {alvo}"),
    ("deixar", "deixa de listar {alvo}"),
    ("cancelar", "cancela e não lista {alvo}"),
    ("nao_voltar", "não volte a mostrar {alvo}"),
    ("jamais", "jamais listar {alvo}"),
)

HARD_NEGATIVES = (
    ("relato_passado", "ontem eu conferi {alvo}"),
    ("relato_terceiro", "ela listou {alvo} durante o teste"),
    ("plano_futuro", "amanhã vou verificar {alvo}"),
    ("hipotese", "se fosse necessário eu listaria {alvo}"),
    ("citacao", "ele escreveu liste {alvo} na mensagem"),
    ("metalinguagem", "a frase mostre {alvo} parece uma ordem"),
    ("interface", "esse botão exibe {alvo} automaticamente"),
    ("tutorial", "o manual ensina como consultar {alvo}"),
    ("preferencia", "eu gosto de acompanhar {alvo}"),
    ("evento", "o sistema mostrou {alvo} sozinho"),
    ("capacidade", "você consegue identificar {alvo}"),
    ("condicional", "se o relatório pedir, a tela mostrará {alvo}"),
    ("descricao", "a lista de {alvo} ficou extensa"),
    ("causa", "muitos itens apareceram porque havia {alvo}"),
    ("comparacao", "ontem existiam mais itens entre {alvo}"),
    ("exemplo", "consultar {alvo} é só um exemplo de funcionalidade"),
)


def _exemplo(
    texto: str,
    *,
    intent: str,
    is_command: bool,
    negated: bool,
    family: str,
    source: str,
    treina_negacao: bool,
) -> dict[str, Any]:
    operacional = intent == "LIST_WINDOWS"
    validation_group = (
        family.rsplit("_", 1)[0]
        if family.endswith(("_a", "_b"))
        else family
    )
    heads = (
        ["action", "intent", "intent_gate"]
        if operacional
        else ["intent", "intent_gate"]
    )
    if operacional and treina_negacao:
        heads.append("negation")
    return {
        "text": texto,
        "intent": intent,
        "is_command": is_command,
        "negated": negated,
        "action": "list" if intent == "LIST_WINDOWS" else "none",
        "family": family,
        "validation_group": validation_group,
        "source": source,
        "domain": "app",
        "training_heads": heads,
    }


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    indice_afirmativo = 0
    for verbo in VERBOS_INVENTARIO:
        for modalidade, molde in MOLDURAS:
            for deslocamento, alvo in enumerate(ALVOS_INVENTARIO):
                variante = "a" if deslocamento < 3 else "b"
                familia = (
                    f"list_windows_v1_inventario_{verbo}_{modalidade}_{variante}"
                )
                texto = molde.format(verbo=verbo, alvo=alvo)
                if verbo == "lista" and modalidade == "direta" and deslocamento == 0:
                    texto = "que aplicativos estão abertos"
                exemplos.append(_exemplo(
                    texto,
                    intent="LIST_WINDOWS",
                    is_command=True,
                    negated=False,
                    family=familia,
                    source="MANUAL_PARAPHRASE",
                    treina_negacao=indice_afirmativo % 4 == 0,
                ))
                indice_afirmativo += 1

    for mecanismo, molde in CONSULTAS_ALVO:
        for deslocamento, (alvo, estado) in enumerate(APLICATIVOS):
            variante = "a" if deslocamento < 3 else "b"
            familia = f"list_windows_v1_consulta_alvo_{mecanismo}_{variante}"
            exemplos.append(_exemplo(
                molde.format(alvo=alvo, estado=estado),
                intent="LIST_WINDOWS",
                is_command=True,
                negated=False,
                family=familia,
                source="MANUAL_PARAPHRASE",
                treina_negacao=indice_afirmativo % 4 == 0,
            ))
            indice_afirmativo += 1

    for indice, (mecanismo, molde) in enumerate(NEGADAS):
        familia = f"list_windows_v1_negada_{mecanismo}"
        for deslocamento in range(3):
            alvo = ALVOS_INVENTARIO[
                (indice + deslocamento * 2) % len(ALVOS_INVENTARIO)
            ]
            exemplos.append(_exemplo(
                molde.format(alvo=alvo),
                intent="LIST_WINDOWS",
                is_command=True,
                negated=True,
                family=familia,
                source="HARD_NEGATIVE",
                treina_negacao=True,
            ))

    for indice, (mecanismo, molde) in enumerate(HARD_NEGATIVES):
        familia = f"list_windows_v1_nao_comando_{mecanismo}"
        for deslocamento in range(3):
            alvo = ALVOS_INVENTARIO[
                (indice + deslocamento * 2) % len(ALVOS_INVENTARIO)
            ]
            exemplos.append(_exemplo(
                molde.format(alvo=alvo),
                intent="NONE",
                is_command=False,
                negated=False,
                family=familia,
                source="HARD_NEGATIVE",
                treina_negacao=False,
            ))
    return exemplos


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", base)).strip()


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, int]:
    itens = [dict(item) for item in exemplos]
    textos = [_normalizar(item.get("text", "")) for item in itens]
    if len(textos) != len(set(textos)):
        repetidos = [texto for texto, total in Counter(textos).items() if total > 1]
        raise ValueError(f"o lote contém textos duplicados: {repetidos[:3]}")
    reservadas = {_normalizar(texto) for texto in FRASES_RUNTIME_RESERVADAS}
    if reservadas & set(textos):
        raise ValueError("receipt real reservado não pode entrar no treino")
    for item in itens:
        heads = item.get("training_heads")
        if item.get("intent") == "LIST_WINDOWS":
            permitidos = {
                ("action", "intent", "intent_gate"),
                ("action", "intent", "intent_gate", "negation"),
            }
        else:
            permitidos = {("intent", "intent_gate")}
        if tuple(heads or ()) not in permitidos:
            raise ValueError("training_heads não respeita o owner de cada rótulo")
    comandos = [item for item in itens if item.get("intent") == "LIST_WINDOWS"]
    resumo = {
        "total": len(itens),
        "list_windows": len(comandos),
        "list_windows_afirmativos": sum(not item["negated"] for item in comandos),
        "list_windows_negados": sum(item["negated"] for item in comandos),
        "list_windows_familias": len({item["family"] for item in comandos}),
        "hard_negatives_app": sum(
            item["intent"] == "NONE" and not item["is_command"]
            for item in itens
        ),
        "command_positivos": sum(
            item["intent"] == "LIST_WINDOWS"
            and "command" in item["training_heads"]
            for item in itens
        ),
        "command_negativos": sum(
            item["intent"] == "NONE" and "command" in item["training_heads"]
            for item in itens
        ),
        "negation_afirmativos": sum(
            item["intent"] == "LIST_WINDOWS"
            and not item["negated"]
            and "negation" in item["training_heads"]
            for item in itens
        ),
        "negation_negados": sum(
            item["intent"] == "LIST_WINDOWS"
            and item["negated"]
            and "negation" in item["training_heads"]
            for item in itens
        ),
        "grupos_validacao": len({item["validation_group"] for item in itens}),
        "max_exemplos_por_familia": max(
            Counter(item["family"] for item in itens).values(), default=0
        ),
    }
    esperado = {
        "total": 198,
        "list_windows": 150,
        "list_windows_afirmativos": 120,
        "list_windows_negados": 30,
        "list_windows_familias": 50,
        "hard_negatives_app": 48,
        "command_positivos": 0,
        "command_negativos": 0,
        "negation_afirmativos": 30,
        "negation_negados": 30,
        "grupos_validacao": 46,
        "max_exemplos_por_familia": 3,
    }
    if resumo != esperado:
        raise ValueError(f"cotas inesperadas: {resumo!r} != {esperado!r}")
    return resumo


def escrever_lote(destino: str | Path) -> dict[str, int]:
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    caminho = Path(destino)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conteudo = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in exemplos
    )
    descritor, temporario = tempfile.mkstemp(
        prefix=f".{caminho.name}.", suffix=".tmp", dir=str(caminho.parent)
    )
    try:
        with os.fdopen(descritor, "w", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(conteudo)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        Path(temporario).replace(caminho)
    except Exception:
        Path(temporario).unlink(missing_ok=True)
        raise
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default=(
            "mente_laylay/neural/datasets/candidatos/"
            "list_windows_onda_v1.jsonl"
        ),
    )
    args = parser.parse_args()
    resumo = escrever_lote(args.destino)
    print(json.dumps({"destino": args.destino, **resumo}, ensure_ascii=False))


if __name__ == "__main__":
    main()
