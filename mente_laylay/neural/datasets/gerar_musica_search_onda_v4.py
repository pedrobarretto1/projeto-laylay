"""Gera a onda contrastiva v4 de MUSIC_SEARCH sem tocar o DEV canônico.

A v3 tinha volume suficiente, mas cada fenômeno linguístico aparecia em uma
única família. Como a validação mantém famílias inteiras fora do treino, isso
media novidade total em vez de generalização entre formas irmãs. A v4 mantém o
mesmo número de exemplos e distribui cada mecanismo em duas famílias distintas.

O lote continua sendo apenas candidato: não treina, não promove e não autoriza
execução.
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


ALVOS = (
    "lua de neon da anny",
    "yellow do coldplay",
    "numb do linkin park",
    "bad romance da lady gaga",
    "505 do arctic monkeys",
    "somebody that i used to know",
    "meu abrigo do melim",
    "velha infância dos tribalistas",
    "blinding lights do the weeknd",
    "pra você guardei o amor",
)


# Cada mecanismo possui duas famílias de superfície realmente diferentes.
# A família, e não a música usada como alvo, continua sendo a unidade do fold.
AFIRMATIVAS = (
    ("direta_colocar", "a", "coloca {alvo}"),
    ("direta_colocar", "b", "coloca {alvo} pra tocar"),
    ("direta_tocar", "a", "toca {alvo}"),
    ("direta_tocar", "b", "toca {alvo} pra mim"),
    ("direta_por", "a", "põe {alvo} agora"),
    ("direta_por", "b", "bota {alvo} para tocar"),
    ("direta_mandar", "a", "manda {alvo} aí"),
    ("direta_mandar", "b", "solta {alvo} no som"),
    ("desejo_quero", "a", "quero ouvir {alvo}"),
    ("desejo_quero", "b", "quero escutar {alvo} agora"),
    ("desejo_queria", "a", "queria ouvir {alvo}"),
    ("desejo_queria", "b", "eu queria escutar {alvo}"),
    ("desejo_gostaria", "a", "gostaria de ouvir {alvo}"),
    ("desejo_gostaria", "b", "eu gostaria que tocasse {alvo}"),
    ("desejo_vontade", "a", "estou com vontade de ouvir {alvo}"),
    ("desejo_vontade", "b", "me deu vontade de escutar {alvo}"),
    ("coletivo_vamos", "a", "vamos ouvir {alvo}"),
    ("coletivo_vamos", "b", "vamos colocar {alvo} pra tocar"),
    ("modal_pode", "a", "pode colocar {alvo}"),
    ("modal_pode", "b", "você pode tocar {alvo} pra mim"),
    ("modal_poderia", "a", "poderia colocar {alvo}"),
    ("modal_poderia", "b", "você poderia tocar {alvo}"),
    ("modal_consegue", "a", "consegue colocar {alvo}"),
    ("modal_consegue", "b", "você consegue tocar {alvo}"),
    ("modal_tem_como", "a", "tem como tocar {alvo}"),
    ("modal_tem_como", "b", "tem um jeito de colocar {alvo}"),
    ("modal_sera_que", "a", "será que pode tocar {alvo}"),
    ("modal_sera_que", "b", "será que você coloca {alvo}"),
    ("modal_da_para", "a", "dá pra tocar {alvo}"),
    ("modal_da_para", "b", "dá para colocar {alvo} agora"),
    ("condicional_se_puder", "a", "se puder toca {alvo}"),
    ("condicional_se_puder", "b", "se você puder coloca {alvo}"),
    ("polidez_favor", "a", "por favor toca {alvo}"),
    ("polidez_favor", "b", "faz o favor de colocar {alvo}"),
    ("polidez_gentileza", "a", "por gentileza toque {alvo}"),
    ("polidez_gentileza", "b", "tenha a gentileza de pôr {alvo}"),
    ("pedido_ve_se", "a", "vê se toca {alvo}"),
    ("pedido_ve_se", "b", "vê se consegue colocar {alvo}"),
    ("busca_e_toca", "a", "procura e toca {alvo}"),
    ("busca_e_toca", "b", "acha {alvo} e coloca pra tocar"),
)

NEGADAS = (
    ("literal_nao_tocar", "a", "não toca {alvo}"),
    ("literal_nao_tocar", "b", "não reproduz {alvo}"),
    ("literal_nao_colocar", "a", "não coloca {alvo}"),
    ("literal_nao_colocar", "b", "não bota {alvo} agora"),
    ("recusa_nao_quero", "a", "não quero ouvir {alvo}"),
    ("recusa_nao_quero", "b", "não estou a fim de escutar {alvo}"),
    ("preferencia_nao", "a", "prefiro não tocar {alvo}"),
    ("preferencia_nao", "b", "é melhor não colocar {alvo}"),
    ("absoluta", "a", "jamais coloque {alvo}"),
    ("absoluta", "b", "nunca toque {alvo}"),
    ("evitacao", "a", "evita tocar {alvo}"),
    ("evitacao", "b", "passa longe de {alvo}"),
    ("exclusao_fora", "a", "deixa {alvo} fora da fila"),
    ("exclusao_fora", "b", "tira {alvo} das opções"),
    ("exclusao_menos", "a", "coloca qualquer uma menos {alvo}"),
    ("exclusao_menos", "b", "pode ser qualquer música exceto {alvo}"),
    ("escolha_outra", "a", "escolhe outra no lugar de {alvo}"),
    ("escolha_outra", "b", "troca {alvo} por outra música"),
    ("composta", "a", "pode escolher outra mas não põe {alvo}"),
    ("composta", "b", "toca alguma coisa só não coloca {alvo}"),
)

NAO_COMANDOS = (
    ("relato_passado", "a", "ontem eu ouvi {alvo} no carro"),
    ("relato_passado", "b", "eu escutei {alvo} mais cedo"),
    ("relato_terceiro", "a", "meu irmão colocou {alvo} na festa"),
    ("relato_terceiro", "b", "ela tocou {alvo} durante a viagem"),
    ("plano_futuro", "a", "vou colocar {alvo} mais tarde"),
    ("plano_futuro", "b", "amanhã pretendo ouvir {alvo}"),
    ("hipotese", "a", "se eu fosse dj colocaria {alvo}"),
    ("hipotese", "b", "se a festa fosse minha eu tocaria {alvo}"),
    ("citacao", "a", "ele disse coloca {alvo} e saiu"),
    ("citacao", "b", "ela escreveu toca {alvo} na mensagem"),
    ("metalinguagem", "a", "a frase toca {alvo} parece um comando"),
    ("metalinguagem", "b", "coloca {alvo} é só um exemplo de frase"),
    ("interface", "a", "esse botão toca {alvo} automaticamente"),
    ("interface", "b", "o aplicativo consegue colocar {alvo} sozinho"),
    ("tutorial", "a", "como colocar {alvo} em um vídeo"),
    ("tutorial", "b", "um guia ensina a tocar {alvo} no violão"),
    ("preferencia", "a", "eu gosto de ouvir {alvo} quando viajo"),
    ("preferencia", "b", "eu prefiro {alvo} para dias frios"),
    ("opiniao", "a", "{alvo} seria uma boa escolha para a festa"),
    ("opiniao", "b", "acho {alvo} uma música bonita"),
    ("evento_atual", "a", "{alvo} está tocando no quarto"),
    ("evento_atual", "b", "dá para ouvir {alvo} vindo da rua"),
    ("duvida_pessoal", "a", "não sei se quero ouvir {alvo}"),
    ("duvida_pessoal", "b", "ainda não decidi se coloco {alvo}"),
    ("pergunta_autoria", "a", "quem canta {alvo}"),
    ("pergunta_autoria", "b", "de quem é a música {alvo}"),
    ("pergunta_instrumento", "a", "você sabe como tocar {alvo} no violão"),
    ("pergunta_instrumento", "b", "qual acorde usam para tocar {alvo}"),
    ("assunto", "a", "a gente estava falando de {alvo}"),
    ("assunto", "b", "nossa conversa era sobre {alvo}"),
    ("condicional_irreal", "a", "talvez eu colocasse {alvo} numa viagem"),
    ("condicional_irreal", "b", "eu tocaria {alvo} se fosse uma festa"),
    ("pedido_reportado", "a", "ela me pediu para tocar {alvo}"),
    ("pedido_reportado", "b", "ele queria que eu colocasse {alvo}"),
    ("discussao_recomendacao", "a", "será que {alvo} combina com um jantar"),
    ("discussao_recomendacao", "b", "você acha {alvo} adequada para estudar"),
    ("descricao", "a", "{alvo} começa com um violão suave"),
    ("descricao", "b", "a letra de {alvo} é bem melancólica"),
    ("desejo_passado", "a", "ontem eu quis ouvir {alvo}"),
    ("desejo_passado", "b", "eu estava com vontade de tocar {alvo} mais cedo"),
)


def _familia(classe: str, mecanismo: str, variante: str) -> str:
    return f"musica_v4_{classe}_{mecanismo}_{variante}"


def _exemplo(
    texto: str,
    *,
    intent: str,
    is_command: bool,
    negated: bool,
    action: str,
    family: str,
    source: str,
) -> dict[str, Any]:
    return {
        "text": texto,
        "intent": intent,
        "is_command": is_command,
        "negated": negated,
        "action": action,
        "family": family,
        "validation_group": family.rsplit("_", 1)[0],
        "source": source,
        "domain": "music",
    }


def _tem_negacao(texto: str) -> bool:
    return bool(
        re.search(
            r"\b(?:não|nem|nunca|jamais|sem|menos|exceto|fora)\b",
            texto.casefold(),
        )
    )


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for indice, (mecanismo, variante, molde) in enumerate(AFIRMATIVAS):
        for deslocamento in range(3):
            alvo = ALVOS[(indice + deslocamento * 3) % len(ALVOS)]
            exemplos.append(_exemplo(
                molde.format(alvo=alvo),
                intent="MUSIC_SEARCH",
                is_command=True,
                negated=False,
                action="search",
                family=_familia("afirmativa", mecanismo, variante),
                source="MANUAL_PARAPHRASE",
            ))
    for indice, (mecanismo, variante, molde) in enumerate(NEGADAS):
        for deslocamento in range(2):
            alvo = ALVOS[(indice + deslocamento * 5) % len(ALVOS)]
            exemplos.append(_exemplo(
                molde.format(alvo=alvo),
                intent="MUSIC_SEARCH",
                is_command=True,
                negated=True,
                action="search",
                family=_familia("negada", mecanismo, variante),
                source="HARD_NEGATIVE",
            ))
    for indice, (mecanismo, variante, molde) in enumerate(NAO_COMANDOS):
        for deslocamento in range(2):
            alvo = ALVOS[(indice + deslocamento * 4) % len(ALVOS)]
            texto = molde.format(alvo=alvo)
            exemplos.append(_exemplo(
                texto,
                intent="NONE",
                is_command=False,
                negated=_tem_negacao(texto),
                action="none",
                family=_familia("nao_comando", mecanismo, variante),
                source="HARD_NEGATIVE",
            ))
    return exemplos


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", base)).strip()


def _mecanismos_por_classe(
    itens: Iterable[dict[str, Any]],
) -> dict[str, Counter[str]]:
    mecanismos: dict[str, Counter[str]] = {
        "afirmativa": Counter(),
        "negada": Counter(),
        "nao_comando": Counter(),
    }
    for item in itens:
        partes = str(item["family"]).rsplit("_", 1)
        mecanismo = partes[0]
        if not item["is_command"]:
            classe = "nao_comando"
        elif item["negated"]:
            classe = "negada"
        else:
            classe = "afirmativa"
        mecanismos[classe][mecanismo] += 1
    return mecanismos


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, int]:
    itens = [dict(item) for item in exemplos]
    textos = [_normalizar(item.get("text", "")) for item in itens]
    if len(textos) != len(set(textos)):
        raise ValueError("o lote gerado contém textos duplicados")
    comandos = [item for item in itens if item["is_command"]]
    negados = [item for item in comandos if item["negated"]]
    nao_comandos = [item for item in itens if not item["is_command"]]
    familias_comando = {item["family"] for item in comandos}
    familias_nao_comando = {item["family"] for item in nao_comandos}
    contagem_familias = Counter(item["family"] for item in itens)
    mecanismos = _mecanismos_por_classe(itens)
    observado = {
        "total": len(itens),
        "comandos": len(comandos),
        "comandos_negados": len(negados),
        "nao_comandos": len(nao_comandos),
        "familias_comando": len(familias_comando),
        "familias_nao_comando": len(familias_nao_comando),
        "max_exemplos_por_familia": max(contagem_familias.values(), default=0),
        "mecanismos_afirmativos": len(mecanismos["afirmativa"]),
        "mecanismos_negados": len(mecanismos["negada"]),
        "mecanismos_nao_comando": len(mecanismos["nao_comando"]),
    }
    esperado = {
        "total": 240,
        "comandos": 160,
        "comandos_negados": 40,
        "nao_comandos": 80,
        "familias_comando": 60,
        "familias_nao_comando": 40,
        "max_exemplos_por_familia": 3,
        "mecanismos_afirmativos": 20,
        "mecanismos_negados": 10,
        "mecanismos_nao_comando": 20,
    }
    if observado != esperado:
        raise ValueError(f"cotas inesperadas: {observado!r} != {esperado!r}")
    if any(total != 6 for total in mecanismos["afirmativa"].values()):
        raise ValueError("mecanismo afirmativo precisa de duas famílias equilibradas")
    if any(total != 4 for total in mecanismos["negada"].values()):
        raise ValueError("mecanismo negado precisa de duas famílias equilibradas")
    if any(total != 4 for total in mecanismos["nao_comando"].values()):
        raise ValueError("hard negative precisa de duas famílias equilibradas")
    return observado


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
        prefix=f".{caminho.name}.",
        suffix=".tmp",
        dir=str(caminho.parent),
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
            "musica_search_onda_v4.jsonl"
        ),
    )
    args = parser.parse_args()
    resumo = escrever_lote(args.destino)
    print(json.dumps({"destino": args.destino, **resumo}, ensure_ascii=False))


if __name__ == "__main__":
    main()
