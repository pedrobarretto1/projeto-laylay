"""Gera fronteiras dirigidas para heads de comando ainda instáveis.

O lote ensina somente se uma fala é comando para o intent já proposto. Ele não
treina intent, ação, negação, autoridade nem execução e permanece em staging.
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
        "o abajur da sala",
        "a luminária do corredor",
        "o ventilador do quarto",
    ),
    "OPEN_URL": (
        "o portal do banco",
        "a página da prefeitura",
        "a documentação do framework",
    ),
    "MUSIC_SEARCH": (
        "uma faixa romântica",
        "uma música calma",
        "uma canção para o jantar",
    ),
    "WEATHER": (
        "amanhã cedo",
        "esta noite",
        "no próximo fim de semana",
    ),
}


# A base usa oito mecanismos x três alvos. Música e clima recebem dois
# mecanismos adicionais porque o primeiro candidato provou essas lacunas.
POSITIVOS = {
    "IOT_CONTROL": (
        ("acender_curto", "on", "acende {alvo} agora"),
        ("ativar_curto", "on", "ativa {alvo}"),
        ("funcionar", "on", "coloca {alvo} para funcionar"),
        ("estado_ligado", "on", "quero {alvo} ligado agora"),
        ("apagar_curto", "off", "apaga {alvo} agora"),
        ("desativar_curto", "off", "desativa {alvo}"),
        ("parar", "off", "faz {alvo} parar"),
        ("estado_desligado", "off", "quero {alvo} desligado agora"),
    ),
    "OPEN_URL": (
        ("ir_ate", "open", "vai até {alvo}"),
        ("abrir_navegador", "open", "abre {alvo} no navegador"),
        ("entrar_agora", "open", "entra em {alvo} agora"),
        ("acessar_modal", "open", "pode acessar {alvo} para mim"),
        ("levar", "open", "me leva até {alvo}"),
        ("carregar_tela", "open", "carrega {alvo} na tela"),
        ("desejo_ver", "open", "quero ver {alvo} no navegador"),
        ("navegar", "open", "navega até {alvo}"),
    ),
    "MUSIC_SEARCH": (
        ("encontrar_tocar", "search", "encontra {alvo} e toca"),
        ("procurar", "search", "procura {alvo} para mim"),
        ("colocar", "search", "coloca {alvo} para tocar"),
        ("buscar", "search", "busca {alvo} agora"),
        ("desejo_ouvir", "search", "quero ouvir {alvo}"),
        ("tocar_modal", "search", "pode tocar {alvo} para mim"),
        ("escolher", "search", "escolhe {alvo} e reproduz"),
        ("localizar", "search", "localiza {alvo} no catálogo"),
        ("achar_direto", "search", "acha {alvo} para tocar agora"),
        ("achar_modal", "search", "pode achar {alvo} no catálogo"),
    ),
    "WEATHER": (
        ("pergunta_tempo", "query", "como fica o tempo {alvo}"),
        ("contar_previsao", "query", "me conta a previsão {alvo}"),
        ("pergunta_chuva", "query", "diz se vai chover {alvo}"),
        ("consultar_temperatura", "query", "consulta a temperatura {alvo}"),
        ("desejo_clima", "query", "quero saber o clima {alvo}"),
        ("pergunta_previsao", "query", "tem previsão de chuva {alvo}"),
        ("conferir_tempo", "query", "confere o tempo {alvo}"),
        ("mostrar_previsao", "query", "mostra a previsão {alvo}"),
        ("qual_previsao_direta", "query", "qual previsão vale para {alvo}"),
        (
            "qual_previsao_modal",
            "query",
            "pode me dizer qual é o tempo previsto {alvo}",
        ),
    ),
}


# Doze mecanismos x três alvos = 36 não-comandos por head dirigido.
NEGATIVOS = {
    "IOT_CONTROL": (
        ("estado", "{alvo} está ligado neste momento"),
        ("relato", "ontem eu desliguei {alvo}"),
        ("preferencia", "eu gosto de {alvo} ligado à noite"),
        ("terceiro", "meu irmão costuma acender {alvo}"),
        ("futuro", "amanhã pretendo testar {alvo}"),
        ("hipotese", "se estivesse calor eu ligaria {alvo}"),
        ("meta", "ligar {alvo} é um exemplo de instrução"),
        ("tutorial", "o manual explica como instalar {alvo}"),
        ("interface", "este botão controla {alvo}"),
        ("evento", "{alvo} apagou sozinho mais cedo"),
        ("duvida", "não sei se {alvo} está funcionando"),
        ("descricao", "{alvo} consome pouca energia"),
    ),
    "OPEN_URL": (
        ("estado", "{alvo} está aberto em outra aba"),
        ("relato", "ontem eu visitei {alvo}"),
        ("preferencia", "eu gosto do visual de {alvo}"),
        ("terceiro", "meu irmão acessou {alvo}"),
        ("futuro", "amanhã pretendo conhecer {alvo}"),
        ("hipotese", "se precisasse eu entraria em {alvo}"),
        ("meta", "abrir {alvo} é um exemplo de comando"),
        ("tutorial", "o guia ensina como publicar em {alvo}"),
        ("interface", "o navegador sugere {alvo}"),
        ("evento", "{alvo} ficou indisponível mais cedo"),
        ("duvida", "não sei se {alvo} é confiável"),
        ("descricao", "{alvo} tem uma área de notícias"),
    ),
    "MUSIC_SEARCH": (
        ("estado", "{alvo} está tocando na sala"),
        ("relato", "ontem eu ouvi {alvo}"),
        ("preferencia", "eu gosto de {alvo}"),
        ("terceiro", "meu irmão encontrou {alvo}"),
        ("futuro", "amanhã pretendo ouvir {alvo}"),
        ("hipotese", "num jantar eu escolheria {alvo}"),
        ("meta", "tocar {alvo} é um exemplo de pedido"),
        ("tutorial", "o vídeo ensina a compor {alvo}"),
        ("interface", "o aplicativo recomendou {alvo}"),
        ("evento", "{alvo} apareceu na rádio mais cedo"),
        ("duvida", "não sei quem canta {alvo}"),
        ("descricao", "{alvo} começa com piano"),
    ),
    "WEATHER": (
        ("estado", "a previsão para {alvo} mudou"),
        ("relato", "ontem eu conferi o tempo para {alvo}"),
        ("preferencia", "eu gosto de gráficos do clima para {alvo}"),
        ("terceiro", "meu irmão consultou a previsão para {alvo}"),
        ("futuro", "depois pretendo olhar a previsão para {alvo}"),
        ("hipotese", "se viajasse eu veria o clima para {alvo}"),
        ("meta", "consultar o tempo para {alvo} é um exemplo de pedido"),
        ("tutorial", "o guia explica como prever chuva para {alvo}"),
        ("interface", "o painel atualiza o clima para {alvo}"),
        ("evento", "o alerta de chuva para {alvo} apareceu sozinho"),
        ("duvida", "não sei se a previsão para {alvo} é confiável"),
        ("descricao", "a temperatura para {alvo} varia bastante"),
    ),
}


DOMINIOS = {
    "IOT_CONTROL": "iot",
    "OPEN_URL": "browser",
    "MUSIC_SEARCH": "music",
    "WEATHER": "weather",
}


MECANISMOS_MESMO_GRUPO = {
    ("MUSIC_SEARCH", "positivo", "achar_direto"): "achar",
    ("MUSIC_SEARCH", "positivo", "achar_modal"): "achar",
    ("WEATHER", "positivo", "qual_previsao_direta"): "qual_previsao",
    ("WEATHER", "positivo", "qual_previsao_modal"): "qual_previsao",
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
    grupo = f"fronteiras_comando_v6_{intent_head.casefold()}_{classe}_{mecanismo}"
    mecanismo_validacao = MECANISMOS_MESMO_GRUPO.get(
        (intent_head, classe, mecanismo),
        mecanismo,
    )
    grupo_validacao = (
        f"fronteiras_comando_v6_{intent_head.casefold()}_"
        f"{classe}_{mecanismo_validacao}"
    )
    return {
        "text": texto,
        "intent": intent_head if is_command else "NONE",
        "is_command": is_command,
        "negated": False,
        "action": action if is_command else "none",
        "family": grupo,
        "validation_group": grupo_validacao,
        "source": "MANUAL_PARAPHRASE" if is_command else "HARD_NEGATIVE",
        "domain": DOMINIOS[intent_head],
        "training_heads": ["command"],
        "command_head_intent": intent_head,
    }


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for intent_head in sorted(POSITIVOS):
        alvos = ALVOS[intent_head]
        for mecanismo, action, molde in POSITIVOS[intent_head]:
            for alvo in alvos:
                exemplos.append(_item(
                    molde.format(alvo=alvo),
                    intent_head=intent_head,
                    is_command=True,
                    action=action,
                    classe="positivo",
                    mecanismo=mecanismo,
                ))
        for mecanismo, molde in NEGATIVOS[intent_head]:
            for alvo in alvos:
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
    if len(itens) != 252:
        raise ValueError(f"lote v6 deveria ter 252 exemplos, recebeu {len(itens)}")
    if len(textos) != len(set(textos)):
        raise ValueError("lote v6 contém textos duplicados")
    if any(item.get("training_heads") != ["command"] for item in itens):
        raise ValueError("lote v6 só pode ensinar o head command")
    if any(item.get("negated") is not False for item in itens):
        raise ValueError("negação está fora do escopo do lote v6")
    if any(
        item.get("command_head_intent") not in POSITIVOS
        for item in itens
    ):
        raise ValueError("lote v6 exige owner de command conhecido")
    if any(
        item.get("intent")
        != (item["command_head_intent"] if item.get("is_command") else "NONE")
        for item in itens
    ):
        raise ValueError("rótulo de intent incompatível com a classe de comando")
    reservados = {
        "oi lay pode ligar a luz para mim",
        "liga a luz",
        "desliga a luz",
        "pausa",
        "despausa",
        "abre a microsoft store",
        "vai para o site do github",
        "acha uma cancao de amor",
        "qual e a previsao para hoje",
    }
    if reservados & set(textos):
        raise ValueError("receipt ou challenge reservado não pode entrar no treino")

    contagem: dict[str, Counter[bool]] = {
        intent: Counter() for intent in sorted(POSITIVOS)
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
        "training_heads": ["command"],
        "por_intent": por_intent,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default=(
            "mente_laylay/neural/datasets/candidatos/"
            "fronteiras_comando_v6.jsonl"
        ),
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(args.destino, exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
