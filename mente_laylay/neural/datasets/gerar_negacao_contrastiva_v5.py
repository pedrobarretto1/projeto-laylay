"""Gera a onda contrastiva v5 exclusiva do head de negação.

O lote separa pedidos afirmativos de estado de recusas sintáticas e de estados
que impedem uma ação semântica. Ele não concede autoridade e não treina os
heads de comando, intenção ou ação.
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .gerar_shadow_contrastivo_v2 import gravar_jsonl_atomico


GRUPOS = {
    # Afirmativos: estados pedidos que materializam uma ação canônica.
    (False, "IOT_CONTROL", "on", "iot_on_deixar_ligado"): (
        "deixa a luminária da mesa ligada agora",
        "deixa a iluminação da cozinha acesa por favor",
        "deixa o ventilador do quarto funcionando",
    ),
    (False, "IOT_CONTROL", "on", "iot_on_manter_ativo"): (
        "mantenha a luz da varanda ligada",
        "mantenha o abajur da sala aceso",
        "mantenha a tomada principal funcionando",
    ),
    (False, "IOT_CONTROL", "on", "iot_on_continuar_ativo"): (
        "continue com a iluminação da sala acesa",
        "continue mantendo o ventilador em funcionamento",
        "continue com a tomada do escritório ligada",
    ),
    (False, "IOT_CONTROL", "off", "iot_off_deixar_desligado"): (
        "deixa a luminária da mesa apagada agora",
        "deixa a iluminação da cozinha desligada por favor",
        "deixa o ventilador do quarto parado",
    ),
    (False, "IOT_CONTROL", "off", "iot_off_manter_inativo"): (
        "mantenha a luz da varanda apagada",
        "mantenha o abajur da sala desligado",
        "mantenha a tomada principal sem energia",
    ),
    (False, "APP_OPEN", "open", "app_open_manter_aberto"): (
        "mantenha a calculadora aberta na tela",
        "mantenha o editor de texto aberto por enquanto",
        "mantenha o aplicativo de música funcionando",
    ),
    (False, "APP_OPEN", "open", "app_open_deixar_funcionando"): (
        "deixa o navegador funcionando agora",
        "deixa o mensageiro aberto para mim",
        "deixa o editor de código rodando",
    ),
    (False, "CLOSE_APP", "close", "app_close_manter_fechado"): (
        "mantenha a calculadora fechada",
        "mantenha o editor de texto encerrado",
        "mantenha o aplicativo de música fora de execução",
    ),
    (False, "MEDIA_CONTROL", "play", "midia_play_continuar"): (
        "continue com o áudio tocando",
        "deixa a faixa atual continuar",
        "mantenha a reprodução em andamento",
    ),
    (False, "MEDIA_CONTROL", "play", "midia_play_retomar"): (
        "retome o som a partir do ponto atual",
        "volte a reproduzir a faixa atual",
        "faça o áudio continuar tocando",
    ),
    (False, "MEDIA_CONTROL", "pause", "midia_pause_manter"): (
        "mantenha a reprodução pausada",
        "deixa o áudio parado neste ponto",
        "mantenha a faixa atual em pausa",
    ),
    (False, "CLOSE_TAB", "close", "aba_fechar_afirmativo"): (
        "feche a guia de notícias agora",
        "encerre a página de receitas",
        "remova a aba de pesquisa da janela",
    ),
    (False, "OPEN_URL", "open", "url_abrir_afirmativo"): (
        "acesse a página oficial do Python",
        "entre no portal da universidade",
        "visite o endereço da documentação",
    ),
    (False, "SEARCH", "search", "busca_web_afirmativa"): (
        "pesquise na internet sobre energia solar",
        "procure na web uma receita vegetariana",
        "busque informações sobre astronomia",
    ),
    (False, "LIST_TABS", "list", "abas_listar_afirmativo"): (
        "mostre todas as guias desta janela",
        "liste as páginas abertas no navegador",
        "exiba as abas que estão em uso",
    ),
    (False, "FILE_READ", "read", "arquivo_ler_afirmativo"): (
        "leia o conteúdo do relatório mensal",
        "mostre o texto das anotações da reunião",
        "abra a configuração somente para leitura",
    ),
    (False, "FILE_SEARCH", "search", "arquivo_buscar_afirmativo"): (
        "procure a planilha de despesas no computador",
        "encontre as notas da última reunião",
        "busque o arquivo de preferências no disco",
    ),
    (False, "WEATHER", "query", "clima_consultar_afirmativo"): (
        "consulte o tempo previsto para amanhã cedo",
        "verifique o clima esperado para esta noite",
        "mostre a previsão do fim de semana",
    ),

    # Negados: recusas explícitas ou preservação sem ação inversa catalogada.
    (True, "IOT_CONTROL", "on", "iot_on_negado_explicito"): (
        "não acenda a iluminação da cozinha",
        "evite ativar o abajur da sala",
        "cancele a ligação da tomada principal",
    ),
    (True, "IOT_CONTROL", "off", "iot_off_negado_explicito"): (
        "não apague a iluminação da cozinha",
        "evite parar o ventilador do quarto",
        "cancele o desligamento da tomada principal",
    ),
    (True, "APP_OPEN", "open", "app_open_negado_explicito"): (
        "não abra a calculadora agora",
        "evite iniciar o editor de texto",
        "cancele a abertura do aplicativo de música",
    ),
    (True, "CLOSE_APP", "close", "app_close_negado_explicito"): (
        "não feche o navegador agora",
        "evite encerrar o mensageiro",
        "cancele o fechamento do editor de código",
    ),
    (True, "MEDIA_CONTROL", "play", "midia_play_negado_explicito"): (
        "não retome o áudio ainda",
        "evite continuar a faixa atual",
        "cancele a reprodução desta playlist",
    ),
    (True, "MEDIA_CONTROL", "pause", "midia_pause_negado_explicito"): (
        "não pause o áudio agora",
        "evite interromper a faixa atual",
        "cancele a pausa da reprodução",
    ),
    (True, "CLOSE_TAB", "close", "aba_preservar_aberta"): (
        "mantenha a guia de notícias aberta",
        "deixa a página de receitas como está",
        "continue com a aba de pesquisa aberta",
    ),
    (True, "CLOSE_TAB", "close", "aba_fechar_negado_explicito"): (
        "não feche a guia de notícias",
        "evite remover a página de receitas",
        "cancele o fechamento da aba de pesquisa",
    ),
    (True, "OPEN_URL", "open", "url_abrir_negado_explicito"): (
        "não acesse a página oficial do Python",
        "evite entrar no portal da universidade",
        "cancele a visita ao endereço da documentação",
    ),
    (True, "LIST_TABS", "list", "abas_ocultar_listagem"): (
        "mantenha as guias desta janela ocultas",
        "não mostre as páginas abertas no navegador",
        "evite listar as abas que estão em uso",
    ),
    (True, "SEARCH", "search", "busca_web_negada"): (
        "não pesquise na internet sobre energia solar",
        "evite procurar na web uma receita vegetariana",
        "cancele a busca de informações sobre astronomia",
    ),
    (True, "WEATHER", "query", "clima_consulta_negada"): (
        "não consulte o tempo previsto para amanhã cedo",
        "evite verificar o clima esperado para esta noite",
        "deixa a previsão do fim de semana para depois",
    ),
    (True, "FILE_READ", "read", "arquivo_leitura_negada"): (
        "não leia o conteúdo do relatório mensal",
        "evite mostrar o texto das anotações da reunião",
        "mantenha a configuração sem abrir",
    ),
    (True, "FILE_SEARCH", "search", "arquivo_busca_negada"): (
        "não procure a planilha de despesas no computador",
        "evite encontrar as notas da última reunião",
        "cancele a busca do arquivo de preferências no disco",
    ),
    (True, "MUSIC_SEARCH", "search", "musica_busca_negada"): (
        "não procure uma faixa romântica agora",
        "evite buscar músicas instrumentais",
        "deixa a pesquisa por jazz para depois",
    ),
    (True, "VOLUME", "up", "volume_subir_negado"): (
        "não aumente o volume da reprodução",
        "evite deixar o áudio mais alto",
        "cancele o aumento da intensidade sonora",
    ),
    (True, "VOLUME", "down", "volume_baixar_negado"): (
        "não diminua o volume da reprodução",
        "evite deixar o áudio mais baixo",
        "cancele a redução da intensidade sonora",
    ),
    (True, "MEDIA_CONTROL", "next", "midia_avancar_negado"): (
        "não pule para a faixa seguinte",
        "evite avançar a música atual",
        "cancele a troca para a próxima canção",
    ),
}

DOMINIOS = {
    "IOT_CONTROL": "iot", "APP_OPEN": "app", "CLOSE_APP": "app",
    "MEDIA_CONTROL": "music", "MUSIC_SEARCH": "music", "VOLUME": "audio",
    "CLOSE_TAB": "browser", "OPEN_URL": "browser", "SEARCH": "browser",
    "LIST_TABS": "browser", "FILE_READ": "files", "FILE_SEARCH": "files",
    "WEATHER": "weather",
}


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    return "".join(ch for ch in base if not unicodedata.combining(ch)).strip()


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for (negated, intent, action, mecanismo), frases in GRUPOS.items():
        grupo = f"negacao_v5_{mecanismo}"
        for indice, texto in enumerate(frases, 1):
            exemplos.append({
                "text": texto,
                "intent": intent,
                "is_command": True,
                "negated": negated,
                "action": action,
                "family": f"{grupo}_{indice}",
                "validation_group": grupo,
                "source": "HARD_NEGATIVE" if negated else "MANUAL_PARAPHRASE",
                "domain": DOMINIOS[intent],
                "training_heads": ["negation"],
            })
    return exemplos


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, Any]:
    itens = [dict(item) for item in exemplos]
    textos = [_normalizar(item.get("text", "")) for item in itens]
    if len(textos) != len(set(textos)):
        raise ValueError("lote de negação v5 contém textos duplicados")
    reservados = {
        _normalizar(texto) for texto in (
            "deixa a lâmpada acesa", "não pare a reprodução",
            "não deixa o som mais alto", "evita desligar a lâmpada agora",
            "liga a luz", "desliga a luz", "pausa", "despausa",
            "abre a microsoft store", "oi lay, pode ligar a luz para mim",
        )
    }
    if reservados & set(textos):
        raise ValueError("receipt ou challenge reservado entrou no lote v5")
    if any(item.get("training_heads") != ["negation"] for item in itens):
        raise ValueError("lote v5 só pode ensinar o head negation")
    contagem = Counter(bool(item.get("negated")) for item in itens)
    resumo = {
        "total": len(itens),
        "afirmativos": contagem[False],
        "negados": contagem[True],
        "grupos_validacao": len({item["validation_group"] for item in itens}),
        "max_exemplos_por_familia": max(
            Counter(item["validation_group"] for item in itens).values(),
            default=0,
        ),
        "training_heads": ["negation"],
    }
    esperado = {
        "total": 108, "afirmativos": 54, "negados": 54,
        "grupos_validacao": 36, "max_exemplos_por_familia": 3,
        "training_heads": ["negation"],
    }
    if resumo != esperado:
        raise ValueError(f"cotas inesperadas no v5: {resumo!r} != {esperado!r}")
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default=(
            "mente_laylay/neural/datasets/candidatos/"
            "negacao_contrastiva_v5.jsonl"
        ),
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(Path(args.destino), exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
