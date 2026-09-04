"""Amplia mecanismos independentes nas fronteiras linguísticas mais frágeis.

Pedidos positivos ensinam apenas os heads que originaram cada erro; descrições
negativas ensinam somente o head ``command`` dirigido. O lote não treina o
gate lexical de intenção, negação, autoridade ou execução e permanece em
staging.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from typing import Any, Iterable

from .gerar_shadow_contrastivo_v2 import gravar_jsonl_atomico


ALVOS = {
    "IOT_CONTROL": (
        "a tomada da cozinha",
        "a fita de LED da estante",
        "o umidificador do escritório",
    ),
    "OPEN_URL": (
        "o site da universidade",
        "o painel da operadora",
        "a central de documentação",
    ),
    "MUSIC_SEARCH": (
        "um samba animado",
        "uma trilha instrumental",
        "um rock brasileiro",
    ),
    "WEATHER": (
        "na manhã de segunda",
        "durante a madrugada",
        "para o feriado",
    ),
}

POSITIVOS = {
    "OPEN_URL": (
        ("ir_para", "open", "vai para {alvo} agora"),
    ),
    "MUSIC_SEARCH": (
        ("achar_eliptico", "search", "acha {alvo}"),
        ("reproduzir", "search", "reproduz {alvo}"),
        ("escutar_pedido", "search", "deixa eu escutar {alvo}"),
        ("iniciar", "search", "inicia {alvo} pra gente"),
        ("pesquisar_tocar", "search", "pesquisa {alvo} e coloca pra tocar"),
        ("selecionar", "search", "seleciona {alvo} no aplicativo"),
        ("arranjar", "search", "arranja {alvo} para eu ouvir"),
        ("botar", "search", "bota {alvo} aí"),
        ("escutar_desejo", "search", "eu quero escutar {alvo} agora"),
        ("encontrar_audio", "search", "encontra o áudio de {alvo}"),
        ("tocar_direto", "search", "toca {alvo} agora"),
        ("escolha_assistente", "search", "escolha {alvo} e dê play"),
        (
            "buscar_reproducao",
            "search",
            "faz uma busca por {alvo} e reproduz",
        ),
    ),
    "WEATHER": (
        ("temperatura_direta", "query", "quantos graus vai fazer {alvo}"),
        ("chuva_direta", "query", "vai chover {alvo}"),
        (
            "condicoes",
            "query",
            "como estarão as condições do tempo {alvo}",
        ),
        ("resumo", "query", "me dá um resumo do clima {alvo}"),
        ("temperatura_maxima", "query", "qual será a máxima {alvo}"),
        ("temperatura_minima", "query", "qual será a mínima {alvo}"),
        (
            "probabilidade_chuva",
            "query",
            "qual é a chance de chuva {alvo}",
        ),
        (
            "planejar",
            "query",
            "veja a previsão {alvo} para eu me planejar",
        ),
        ("meteorologia", "query", "consulta a meteorologia {alvo}"),
        ("clima_modal", "query", "você consegue ver o clima {alvo}"),
        (
            "previsao_eliptica",
            "query",
            "previsão do tempo {alvo}, por favor",
        ),
        (
            "informar_tempo",
            "query",
            "me informa como estará o tempo {alvo}",
        ),
    ),
}


NEGATIVOS = {
    "IOT_CONTROL": (
        ("estado_continuado", "{alvo} continua ligado desde ontem"),
        ("capacidade", "{alvo} pode ligar por comando de voz"),
        ("localizacao", "{alvo} fica ao lado da janela"),
        ("consumo", "{alvo} gasta bastante energia"),
        ("comparacao", "{alvo} é mais silencioso que o antigo"),
        ("compra", "estou pensando em comprar {alvo}"),
        ("defeito", "{alvo} às vezes demora para ligar"),
        ("duvida_capacidade", "será que {alvo} aceita automação"),
    ),
    "OPEN_URL": (
        ("conhecimento", "você conhece {alvo}"),
        ("avaliacao", "{alvo} parece bem organizado"),
        ("historico", "{alvo} foi atualizado ontem"),
        ("link_recebido", "recebi um link de {alvo}"),
        ("noticia", "li uma notícia em {alvo}"),
        ("disponibilidade", "{alvo} costuma sair do ar"),
        ("favorito", "{alvo} está nos meus favoritos"),
        ("comparacao", "{alvo} é mais simples que o concorrente"),
    ),
}


DOMINIOS = {
    "IOT_CONTROL": "iot",
    "OPEN_URL": "browser",
    "MUSIC_SEARCH": "music",
    "WEATHER": "weather",
}


MECANISMOS_MESMO_GRUPO = {
    ("MUSIC_SEARCH", "positivo", "reproduzir"): "reproduzir",
    ("MUSIC_SEARCH", "positivo", "buscar_reproducao"): "reproduzir",
    ("MUSIC_SEARCH", "positivo", "escutar_pedido"): "escutar",
    ("MUSIC_SEARCH", "positivo", "escutar_desejo"): "escutar",
    ("WEATHER", "positivo", "temperatura_maxima"): "temperatura_extrema",
    ("WEATHER", "positivo", "temperatura_minima"): "temperatura_extrema",
}


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", base)).strip()


def _item(
    texto: str,
    *,
    intent_head: str,
    is_command: bool,
    action: str,
    classe: str,
    mecanismo: str,
) -> dict[str, Any]:
    familia = (
        f"expansao_mecanismos_v7_{intent_head.casefold()}_{classe}_{mecanismo}"
    )
    mecanismo_validacao = MECANISMOS_MESMO_GRUPO.get(
        (intent_head, classe, mecanismo),
        mecanismo,
    )
    grupo_validacao = (
        f"expansao_mecanismos_v7_{intent_head.casefold()}_"
        f"{classe}_{mecanismo_validacao}"
    )
    erro_apenas_comando = (
        intent_head == "OPEN_URL"
        or (intent_head == "MUSIC_SEARCH" and mecanismo == "achar_eliptico")
    )
    heads_positivos = (
        ["command"] if erro_apenas_comando
        else ["action", "command", "intent"]
    )
    return {
        "text": texto,
        "intent": intent_head if is_command else "NONE",
        "is_command": is_command,
        "negated": False,
        "action": action if is_command else "none",
        "family": familia,
        "validation_group": grupo_validacao,
        "source": "MANUAL_PARAPHRASE" if is_command else "HARD_NEGATIVE",
        "domain": DOMINIOS[intent_head],
        "training_heads": (
            heads_positivos
            if is_command
            else ["command"]
        ),
        "command_head_intent": intent_head,
    }


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for intent_head in sorted(POSITIVOS):
        for mecanismo, action, molde in POSITIVOS[intent_head]:
            for alvo in ALVOS[intent_head]:
                exemplos.append(_item(
                    molde.format(alvo=alvo),
                    intent_head=intent_head,
                    is_command=True,
                    action=action,
                    classe="positivo",
                    mecanismo=mecanismo,
                ))
    for intent_head in sorted(NEGATIVOS):
        for mecanismo, molde in NEGATIVOS[intent_head]:
            for alvo in ALVOS[intent_head]:
                exemplos.append(_item(
                    molde.format(alvo=alvo),
                    intent_head=intent_head,
                    is_command=False,
                    action="none",
                    classe="negativo",
                    mecanismo=mecanismo,
                ))
    return exemplos


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, Any]:
    itens = [dict(item) for item in exemplos]
    textos = [_normalizar(item.get("text", "")) for item in itens]
    if len(itens) != 126:
        raise ValueError(f"lote v7 deveria ter 126 exemplos, recebeu {len(itens)}")
    if len(textos) != len(set(textos)):
        raise ValueError("lote v7 contém textos duplicados")
    if any(
        item.get("training_heads")
        != (
            ["command"]
            if (
                not item.get("is_command")
                or item.get("command_head_intent") == "OPEN_URL"
                or item.get("family", "").endswith("_achar_eliptico")
            )
            else ["action", "command", "intent"]
        )
        for item in itens
    ):
        raise ValueError("escopo de heads incompatível com a classe do lote v7")
    if any(item.get("negated") is not False for item in itens):
        raise ValueError("negação está fora do escopo do lote v7")
    if any(item.get("command_head_intent") not in DOMINIOS for item in itens):
        raise ValueError("lote v7 exige owner de command conhecido")
    if any(
        item.get("intent")
        != (item["command_head_intent"] if item.get("is_command") else "NONE")
        for item in itens
    ):
        raise ValueError("rótulo de intent incompatível com a classe de comando")

    contagem: dict[str, Counter[bool]] = {
        intent: Counter() for intent in sorted(DOMINIOS)
    }
    for item in itens:
        contagem[item["command_head_intent"]][bool(item["is_command"])] += 1
    por_intent = {
        intent: {
            "comandos": classes[True],
            "nao_comandos": classes[False],
        }
        for intent, classes in contagem.items()
    }
    totais = Counter(bool(item["is_command"]) for item in itens)
    familias = Counter(str(item["family"]) for item in itens)
    return {
        "total": len(itens),
        "comandos": totais[True],
        "nao_comandos": totais[False],
        "grupos_validacao": len({item["validation_group"] for item in itens}),
        "max_exemplos_por_familia": max(familias.values()),
        "positivos_training_heads_por_intent": {
            "MUSIC_SEARCH": {
                "achar_eliptico": ["command"],
                "demais": ["action", "command", "intent"],
            },
            "OPEN_URL": ["command"],
            "WEATHER": ["action", "command", "intent"],
        },
        "negativos_training_heads": ["command"],
        "por_intent": por_intent,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default=(
            "mente_laylay/neural/datasets/candidatos/"
            "expansao_mecanismos_v7.jsonl"
        ),
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(args.destino, exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
