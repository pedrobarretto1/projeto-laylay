"""Ensina hábitos/estados ao head command direcionado de IoT."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .gerar_shadow_contrastivo_v2 import gravar_jsonl_atomico


POSITIVOS = {
    ("on", "direto_a"): (
        "acende a iluminação deste cômodo", "ativa o abajur agora", "coloca o ventilador em funcionamento",
    ),
    ("on", "direto_b"): (
        "faz a luminária funcionar agora", "aciona a tomada da sala", "põe o ventilador para rodar",
    ),
    ("on", "polido_a"): (
        "por favor acenda a iluminação daqui", "pode ativar este abajur agora", "consegue ligar o ventilador para mim",
    ),
    ("on", "polido_b"): (
        "você pode iluminar este cômodo", "será que consegue ativar a tomada", "por gentileza acione o ventilador",
    ),
    ("on", "desejo_a"): (
        "quero claridade neste quarto agora", "quero o abajur funcionando neste momento", "quero que o ventilador comece a rodar",
    ),
    ("on", "desejo_b"): (
        "preciso da iluminação ativa agora", "gostaria que acionasse esta tomada", "faz o ventilador continuar rodando para mim",
    ),
    ("on", "eliptico_a"): (
        "iluminação ativa agora", "abajur funcionando por favor", "ventilador rodando neste momento",
    ),
    ("on", "eliptico_b"): (
        "claridade aqui por favor", "tomada da sala ativa agora", "luminária funcionando já",
    ),
    ("off", "direto_a"): (
        "apaga a iluminação deste cômodo", "desativa o abajur agora", "faz o ventilador parar",
    ),
    ("off", "direto_b"): (
        "corta a luz deste ambiente", "desaciona a tomada da sala", "põe o ventilador fora de funcionamento",
    ),
    ("off", "polido_a"): (
        "por favor apague a iluminação daqui", "pode desativar este abajur agora", "consegue parar o ventilador para mim",
    ),
    ("off", "polido_b"): (
        "você pode tirar a claridade deste cômodo", "será que consegue desativar a tomada", "por gentileza pare o ventilador",
    ),
    ("off", "desejo_a"): (
        "quero este quarto sem iluminação agora", "quero o abajur fora de funcionamento", "quero que o ventilador pare de rodar",
    ),
    ("off", "desejo_b"): (
        "preciso da iluminação desativada agora", "gostaria que cortasse esta tomada", "faz o ventilador parar para mim",
    ),
    ("off", "eliptico_a"): (
        "iluminação desativada agora", "abajur fora de funcionamento por favor", "ventilador parado neste momento",
    ),
    ("off", "eliptico_b"): (
        "sem claridade aqui por favor", "tomada da sala desativada agora", "luminária apagada já",
    ),
    ("on", "deixa_a"): (
        "deixa o abajur funcionando agora", "deixa a iluminação ligada por favor", "deixa o ventilador rodando para mim",
    ),
    ("on", "deixa_b"): (
        "deixa a luz do corredor ligada", "deixa essa luminária acesa agora", "deixa a tomada funcionando por favor",
    ),
    ("on", "deixa_c"): (
        "deixa o quarto iluminado para mim", "deixa este ventilador em funcionamento", "deixa o abajur dando claridade agora",
    ),
    ("off", "deixa_a"): (
        "deixa o abajur fora de funcionamento agora", "deixa a iluminação desativada por favor", "deixa o ventilador parado para mim",
    ),
    ("off", "deixa_b"): (
        "deixa a luz do corredor apagada agora", "deixa essa luminária desligada por favor", "deixa a tomada sem energia agora",
    ),
    ("off", "deixa_c"): (
        "deixa o quarto sem iluminação agora", "deixa este ventilador fora de funcionamento", "deixa o abajur sem claridade por favor",
    ),
}


NEGATIVOS = {
    "habito": (
        "geralmente deixo o ventilador desligado", "sempre mantenho a luz apagada ao dormir", "costumo ficar com o abajur desligado",
    ),
    "preferencia": (
        "prefiro manter a lâmpada desligada", "gosto do ventilador ligado durante o dia", "eu prefiro o quarto com a luz acesa",
    ),
    "estado": (
        "o ventilador está desligado neste momento", "a lâmpada continua apagada", "o abajur está ligado desde cedo",
    ),
    "relato": (
        "ontem deixei a luz desligada", "mais cedo mantive o ventilador ligado", "eu tinha apagado o abajur",
    ),
    "planejamento": (
        "amanhã vou deixar a lâmpada apagada", "depois pretendo manter o ventilador ligado", "à noite quero ficar com o abajur desligado",
    ),
    "desejo_estado": (
        "quero ficar com a luz apagada quando dormir", "quero continuar com o ventilador desligado à noite", "quero manter o abajur aceso durante a leitura",
    ),
    "preferencia_futura": (
        "no verão pretendo ficar com o ventilador ligado", "na viagem prefiro manter as luzes apagadas", "mais tarde pretendo deixar o abajur desligado",
    ),
    "condicional": (
        "se eu sair vou deixar a luz apagada", "quando fizer calor prefiro o ventilador ligado", "se estiver claro o abajur fica desligado",
    ),
    "terceiro": (
        "meu irmão costuma deixar a luz acesa", "ela prefere o ventilador desligado", "Pedro gosta do abajur ligado",
    ),
    "meta": (
        "deixar a luz desligada descreve um estado", "ventilador ligado pode ser uma preferência", "abajur apagado não é sempre um comando",
    ),
    "futuro_acao_a": (
        "mais tarde pretendo ligar a luz", "depois penso em acender o abajur", "amanhã planejo ligar o ventilador",
    ),
    "futuro_acao_b": (
        "daqui a pouco pretendo desligar a tomada", "no fim do dia penso em apagar a luz", "semana que vem planejo ativar a luminária",
    ),
    "meta_comando_a": (
        "ligar a lâmpada é um exemplo de comando", "desligar o ventilador é uma forma de pedido", "apagar a luz pode aparecer numa instrução",
    ),
    "meta_comando_b": (
        "acender o abajur é um exemplo de ordem", "ativar a tomada é uma frase de comando", "desativar a luminária pode ser um pedido",
    ),
    "condicional_estado_a": (
        "se estiver escuro a luz fica acesa", "quando fizer frio o ventilador fica desligado", "se anoitecer o abajur permanece ligado",
    ),
    "condicional_estado_b": (
        "quando o quarto clareia a luminária fica apagada", "se chover a tomada continua desligada", "quando esquentar o ventilador permanece ligado",
    ),
    "desejo_temporal_a": (
        "à noite quero continuar com a luz apagada", "durante o filme quero ficar com o abajur aceso", "ao dormir quero manter o ventilador desligado",
    ),
    "desejo_temporal_b": (
        "pela manhã quero ficar com a luminária apagada", "no verão quero continuar com o ventilador ligado", "durante a viagem quero manter as tomadas desligadas",
    ),
    "condicional_estado_c": (
        "se a sala estiver vazia a luz permanece apagada", "quando o sol aparece o abajur fica desligado", "se o ambiente aquecer o ventilador fica ligado",
    ),
    "condicional_estado_d": (
        "caso fique tarde a luminária continua acesa", "se ninguém estiver em casa a tomada fica desligada", "quando o quarto esfriar o ventilador permanece parado",
    ),
    "condicional_estado_e": (
        "com claridade a lâmpada costuma ficar apagada", "no calor o ventilador geralmente fica ligado", "quando escurece o abajur costuma permanecer aceso",
    ),
    "condicional_estado_f": (
        "se estiver muito claro deixo a luz apagada", "quando o dia esquenta deixo o ventilador ligado", "se eu dormir cedo mantenho o abajur desligado",
    ),
    "condicional_estado_g": (
        "caso esteja frio prefiro o ventilador desligado", "se a janela estiver aberta prefiro a luz apagada", "quando recebo visitas gosto do abajur aceso",
    ),
    "condicional_estado_h": (
        "se chover gosto de manter a luminária ligada", "quando viajo prefiro as tomadas desligadas", "caso o sol esteja forte gosto da luz apagada",
    ),
    "meta_comando_c": (
        "a expressão ligar a luz é um comando", "a frase desligar o ventilador parece uma ordem", "dizer acender o abajur pode ser um pedido",
    ),
    "meta_comando_d": (
        "apagar a lâmpada é só um exemplo de instrução", "ligar a tomada é uma construção imperativa", "desativar a luz serve como exemplo de pedido",
    ),
    "meta_comando_e": (
        "quando alguém diz liga a luz isso soa como ordem", "a frase apaga o abajur tem formato de comando", "pedir para ativar o ventilador é uma instrução",
    ),
    "meta_comando_f": (
        "estou explicando que desligar a tomada é um comando", "mencionar acender a luz não executa nada", "falar sobre apagar a lâmpada não é pedir isso",
    ),
    "meta_comando_g": (
        "o exemplo da aula era ligar o ventilador", "no texto aparece a ordem desligar o abajur", "a documentação cita o comando acender a luz",
    ),
    "desejo_temporal_c": (
        "quando eu voltar quero encontrar a luz apagada", "mais tarde quero permanecer com o ventilador ligado", "amanhã quero ficar com o abajur desligado",
    ),
    "desejo_temporal_d": (
        "na hora de dormir quero a luminária apagada", "durante a tarde quero o ventilador funcionando", "nas férias quero as tomadas desligadas",
    ),
    "desejo_temporal_e": (
        "depois quero continuar com a lâmpada acesa", "no jantar quero ficar com o abajur ligado", "ao sair quero manter o ventilador desligado",
    ),
    "desejo_temporal_f": (
        "para o futuro quero a casa com as luzes apagadas", "no próximo verão quero o ventilador ligado", "na próxima noite quero o abajur aceso",
    ),
    "desejo_temporal_g": (
        "enquanto eu leio quero permanecer com a luminária ligada", "quando estiver fora quero as tomadas desativadas", "durante o descanso quero o ventilador parado",
    ),
}


def _item(
    texto: str,
    *,
    intent: str,
    is_command: bool,
    action: str,
    grupo: str,
    indice: int,
) -> dict[str, Any]:
    return {
        "text": texto,
        "intent": intent,
        "is_command": is_command,
        "negated": False,
        "action": action,
        "family": f"iot_fronteira_comando_v4_{grupo}_{indice}",
        "validation_group": f"iot_fronteira_comando_v4_{grupo}",
        "source": "MANUAL_PARAPHRASE" if is_command else "HARD_NEGATIVE",
        "domain": "iot",
        "training_heads": (
            ["command", "negation"] if is_command else ["command"]
        ),
        "command_head_intent": "IOT_CONTROL",
    }


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for (acao, mecanismo), frases in POSITIVOS.items():
        for indice, frase in enumerate(frases, 1):
            exemplos.append(_item(
                frase, intent="IOT_CONTROL", is_command=True, action=acao,
                grupo=f"positivo_{acao}_{mecanismo}", indice=indice,
            ))
    for mecanismo, frases in NEGATIVOS.items():
        for indice, frase in enumerate(frases, 1):
            exemplos.append(_item(
                frase, intent="NONE", is_command=False, action="none",
                grupo=f"negativo_{mecanismo}", indice=indice,
            ))
    return exemplos


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, Any]:
    itens = [dict(item) for item in exemplos]
    textos = [str(item.get("text") or "").casefold().strip() for item in itens]
    if len(textos) != len(set(textos)):
        raise ValueError("lote v4 contém textos duplicados")
    if len(itens) != 168:
        raise ValueError(f"lote v4 deveria ter 168 exemplos, recebeu {len(itens)}")
    if any(
        item.get("training_heads") != ["command", "negation"]
        for item in itens if item.get("is_command")
    ):
        raise ValueError("positivos v4 devem ensinar command e negation")
    if any(
        item.get("training_heads") != ["command"]
        for item in itens if not item.get("is_command")
    ):
        raise ValueError("não-comandos v4 só podem ensinar command")
    if any(item.get("command_head_intent") != "IOT_CONTROL" for item in itens):
        raise ValueError("lote v4 só pode ensinar o head command de IOT_CONTROL")
    reservados = {
        "oi lay, pode ligar a luz para mim",
        "liga a luz",
        "desliga a luz",
        "deixa a lâmpada acesa",
    }
    if reservados & set(textos):
        raise ValueError("receipt ou challenge reservado não pode entrar no treino")
    contagem = Counter(bool(item.get("is_command")) for item in itens)
    return {
        "total": len(itens),
        "comandos": contagem[True],
        "nao_comandos": contagem[False],
        "grupos_validacao": len({item["validation_group"] for item in itens}),
        "positivos_training_heads": ["command", "negation"],
        "negativos_training_heads": ["command"],
        "command_head_intent": "IOT_CONTROL",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default="mente_laylay/neural/datasets/candidatos/iot_fronteira_comando_v4.jsonl",
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(args.destino, exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
