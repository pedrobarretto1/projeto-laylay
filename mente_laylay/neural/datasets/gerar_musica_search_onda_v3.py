"""Gera a primeira onda curada de MUSIC_SEARCH sem tocar o DEV canônico.

O arquivo produzido continua sendo candidato: não treina, não promove e não
autoriza execução. Cada molde representa uma família linguística inteira para
que a validação cruzada nunca separe paráfrases irmãs entre treino e validação.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import unicodedata
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

ARTISTAS = (
    "Anny",
    "Coldplay",
    "Linkin Park",
    "Lady Gaga",
    "Arctic Monkeys",
    "Gotye",
    "Melim",
    "Tribalistas",
    "The Weeknd",
    "Nando Reis",
)

CLIMAS = (
    "romântica e tranquila",
    "animada dos anos 2000",
    "de rock mais leve",
    "calma para trabalhar",
    "brasileira para relaxar",
    "de rap melódico",
    "nostálgica dos anos 90",
    "instrumental para estudar",
    "dançante para acordar",
    "suave para o fim da noite",
)

FAMILIAS_AFIRMATIVAS = (
    ("musica_direta_coloca_v3", "coloca {alvo}"),
    ("musica_direta_toca_v3", "toca {alvo} pra mim"),
    ("musica_direta_poe_v3", "põe {alvo} para tocar"),
    ("musica_desejo_quero_ouvir_v3", "quero ouvir {alvo} agora"),
    ("musica_convite_escutar_v3", "vamos escutar {alvo}"),
    ("musica_pedido_ve_se_v3", "vê se coloca {alvo}"),
    ("musica_pedido_favor_v3", "faz o favor de tocar {alvo} pra mim"),
    ("musica_coloquial_manda_v3", "manda {alvo} aí"),
    ("musica_desejo_gostaria_v3", "eu gostaria de ouvir {alvo}"),
    ("musica_modal_sera_que_v3", "será que você pode colocar {alvo}"),
    ("musica_modal_poderia_v3", "você poderia tocar {alvo}"),
    ("musica_modal_consegue_v3", "consegue colocar {alvo} pra tocar"),
    ("musica_modal_tem_como_v3", "tem como tocar {alvo}"),
    ("musica_subjuntivo_queria_v3", "eu queria que você colocasse {alvo}"),
    ("musica_condicional_se_puder_v3", "se puder põe {alvo}"),
    ("musica_modal_possivel_v3", "seria possível ouvir {alvo}"),
    ("musica_modal_da_para_v3", "dá para tocar {alvo}"),
    ("musica_polida_gentileza_v3", "por gentileza toque {alvo}"),
)

FAMILIAS_NEGADAS = (
    ("musica_negada_nao_toca_v3", "não toca {alvo}"),
    ("musica_negada_nao_coloca_v3", "não coloca {alvo}"),
    ("musica_negada_evitar_v3", "evita tocar {alvo} agora"),
    ("musica_negada_deixa_fora_v3", "deixa {alvo} fora da fila"),
    ("musica_negada_nao_quero_v3", "não quero ouvir {alvo}"),
    ("musica_negada_melhor_nao_v3", "melhor não tocar {alvo}"),
    ("musica_negada_pedido_composto_v3", "pode escolher outra mas não põe {alvo}"),
    ("musica_negada_nem_pense_v3", "nem pense em tocar {alvo}"),
    ("musica_negada_menos_essa_v3", "coloca qualquer uma menos {alvo}"),
    ("musica_negada_nao_bota_v3", "não bota {alvo} agora"),
)

FAMILIAS_NAO_COMANDO = (
    ("musica_relato_ouvi_v3", "ontem eu ouvi {alvo} no carro"),
    ("musica_terceira_pessoa_v3", "meu irmão colocou {alvo} na festa"),
    ("musica_capacidade_editor_v3", "um editor pode colocar {alvo} num vídeo"),
    ("musica_hipotese_dj_v3", "se eu fosse dj colocaria {alvo}"),
    ("musica_pergunta_instrumento_v3", "você sabe como tocar {alvo} no violão"),
    ("musica_metalinguagem_v3", "a frase toca {alvo} parece um comando"),
    ("musica_opiniao_festa_v3", "{alvo} seria uma boa escolha para a festa"),
    ("musica_preferencia_relato_v3", "eu gosto de ouvir {alvo} quando viajo"),
    ("musica_possibilidade_futura_v3", "talvez eu coloque {alvo} amanhã"),
    ("musica_relato_pedido_terceiro_v3", "ela me pediu para tocar {alvo}"),
    ("musica_citacao_v3", "ele disse coloca {alvo} e saiu"),
    ("musica_tutorial_video_v3", "como colocar {alvo} em um vídeo"),
    ("musica_preferencia_comparada_v3", "eu prefiro {alvo} para dias frios"),
    ("musica_pergunta_autoria_v3", "quem canta {alvo}"),
    ("musica_assunto_conversa_v3", "a gente estava falando de {alvo}"),
    ("musica_capacidade_botao_v3", "esse botão toca {alvo} automaticamente"),
    ("musica_duvida_pessoal_v3", "não sei se quero ouvir {alvo}"),
    ("musica_observacao_tocando_v3", "{alvo} está tocando no quarto"),
    ("musica_desejo_passado_v3", "ontem eu quis ouvir {alvo}"),
    ("musica_plano_futuro_v3", "vou colocar {alvo} mais tarde"),
)


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
        "source": source,
        "domain": "music",
    }


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for indice, (familia, molde) in enumerate(FAMILIAS_AFIRMATIVAS):
        for deslocamento in range(6):
            alvo = ALVOS[(indice + deslocamento) % len(ALVOS)]
            exemplos.append(_exemplo(
                molde.format(alvo=alvo),
                intent="MUSIC_SEARCH",
                is_command=True,
                negated=False,
                action="search",
                family=familia,
                source="MANUAL_PARAPHRASE",
            ))
    for familia, molde in (
        ("musica_artista_indefinida_v3", "toca alguma coisa da {artista}"),
        ("musica_clima_natural_v3", "coloca uma música {clima}"),
    ):
        usa_artista = "{artista}" in molde
        valores = ARTISTAS[:6] if usa_artista else CLIMAS[:6]
        chave = "artista" if usa_artista else "clima"
        for valor in valores:
            exemplos.append(_exemplo(
                molde.format(**{chave: valor}),
                intent="MUSIC_SEARCH",
                is_command=True,
                negated=False,
                action="search",
                family=familia,
                source="MANUAL_PARAPHRASE",
            ))
    for indice, (familia, molde) in enumerate(FAMILIAS_NEGADAS):
        for deslocamento in (0, 2, 4, 6):
            alvo = ALVOS[(indice + deslocamento) % len(ALVOS)]
            exemplos.append(_exemplo(
                molde.format(alvo=alvo),
                intent="MUSIC_SEARCH",
                is_command=True,
                negated=True,
                action="search",
                family=familia,
                source="HARD_NEGATIVE",
            ))
    for indice, (familia, molde) in enumerate(FAMILIAS_NAO_COMANDO):
        for deslocamento in (0, 2, 5, 7):
            alvo = ALVOS[(indice + deslocamento) % len(ALVOS)]
            texto = molde.format(alvo=alvo)
            exemplos.append(_exemplo(
                texto,
                intent="NONE",
                is_command=False,
                negated=bool(re.search(r"\b(?:não|nem)\b", texto.casefold())),
                action="none",
                family=familia,
                source="HARD_NEGATIVE",
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
        raise ValueError("o lote gerado contém textos duplicados")
    comandos = [item for item in itens if item["is_command"]]
    negados = [item for item in comandos if item["negated"]]
    nao_comandos = [item for item in itens if not item["is_command"]]
    familias_comando = {item["family"] for item in comandos}
    familias_nao_comando = {item["family"] for item in nao_comandos}
    esperado = {
        "total": 240,
        "comandos": 160,
        "comandos_negados": 40,
        "nao_comandos": 80,
        "familias_comando": 30,
        "familias_nao_comando": 20,
    }
    observado = {
        "total": len(itens),
        "comandos": len(comandos),
        "comandos_negados": len(negados),
        "nao_comandos": len(nao_comandos),
        "familias_comando": len(familias_comando),
        "familias_nao_comando": len(familias_nao_comando),
    }
    if observado != esperado:
        raise ValueError(f"cotas inesperadas: {observado!r} != {esperado!r}")
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
            "musica_search_onda_v3.jsonl"
        ),
    )
    args = parser.parse_args()
    resumo = escrever_lote(args.destino)
    print(json.dumps({"destino": args.destino, **resumo}, ensure_ascii=False))


if __name__ == "__main__":
    main()
