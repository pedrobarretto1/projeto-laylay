"""Gera uma onda contrastiva a partir de erros observados no shadow.

As frases exatas confirmadas no runtime ficam reservadas para avaliação. Este
lote ensina mecanismos vizinhos e suas fronteiras sem transformar prediction,
contexto ou receipt isolado em autoridade operacional.
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


GRUPOS_COMANDO: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    ("MEDIA_CONTROL", "pause", "music", "pausa_eliptica_a", (
        "pausa aí", "pausa isso agora", "pausa um instante",
    )),
    ("MEDIA_CONTROL", "pause", "music", "pausa_eliptica_b", (
        "dá pause aí", "deixa no pause por enquanto", "segura a reprodução um pouco",
    )),
    ("MEDIA_CONTROL", "pause", "music", "pausa_objeto", (
        "pausa essa música", "pausa o som que está tocando", "pausa a reprodução por favor",
    )),
    ("MEDIA_CONTROL", "pause", "music", "pausa_modal", (
        "pode pausar o que está tocando", "consegue dar uma pausa no áudio", "tem como segurar a música um pouco",
    )),
    ("MEDIA_CONTROL", "pause", "music", "pausa_coloquial", (
        "segura esse som aí", "dá um tempo na reprodução", "deixa essa faixa pausada",
    )),
    ("MEDIA_CONTROL", "pause", "music", "pausa_temporal", (
        "pausa até eu voltar", "interrompe o som por um minuto", "põe a reprodução em pausa agora",
    )),
    ("MEDIA_CONTROL", "play", "music", "play_despausa", (
        "despausa aí", "despausa o som", "pode despausar agora",
    )),
    ("MEDIA_CONTROL", "play", "music", "play_retorno", (
        "volta a tocar", "retoma o que estava tocando", "continua o som de onde parou",
    )),
    ("MEDIA_CONTROL", "play", "music", "play_coloquial", (
        "dá play de novo", "solta a música", "tira o som do pause",
    )),
    ("MEDIA_CONTROL", "play", "music", "play_modal", (
        "pode continuar o áudio", "consegue retomar essa faixa", "tem como voltar com a música",
    )),
    ("MEDIA_CONTROL", "play", "music", "play_curto", (
        "continua aí", "retoma agora", "volta com o som",
    )),
    ("MEDIA_CONTROL", "play", "music", "play_estado", (
        "deixa tocar novamente", "remove a pausa da reprodução", "faz o áudio continuar",
    )),
    ("IOT_CONTROL", "on", "iot", "iot_on_luz_direta", (
        "liga essa luz", "liga a luz do quarto agora", "liga a iluminação daqui",
    )),
    ("IOT_CONTROL", "on", "iot", "iot_on_luz_polida", (
        "por favor liga a luz", "pode ligar a lâmpada para mim", "consegue acender a luz daqui",
    )),
    ("IOT_CONTROL", "on", "iot", "iot_on_dispositivo", (
        "ativa o abajur aqui", "liga a tomada do ventilador", "acende a luminária da mesa",
    )),
    ("IOT_CONTROL", "on", "iot", "iot_on_coloquial", (
        "deixa o quarto claro", "põe a lâmpada para funcionar", "manda energia para o abajur",
    )),
    ("IOT_CONTROL", "on", "iot", "iot_on_modal", (
        "tem como acender o quarto", "será que pode ligar o ventilador", "quero a luminária ligada",
    )),
    ("IOT_CONTROL", "off", "iot", "iot_off_luz_direta", (
        "desliga essa luz", "desliga a luz do quarto agora", "apaga a iluminação daqui",
    )),
    ("IOT_CONTROL", "off", "iot", "iot_off_luz_polida", (
        "por favor desliga a luz", "pode apagar a lâmpada para mim", "consegue desligar a luz daqui",
    )),
    ("IOT_CONTROL", "off", "iot", "iot_off_dispositivo", (
        "desativa o abajur aqui", "desliga a tomada do ventilador", "apaga a luminária da mesa",
    )),
    ("IOT_CONTROL", "off", "iot", "iot_off_coloquial", (
        "deixa o quarto escuro", "corta a energia do abajur", "faz a lâmpada parar de iluminar",
    )),
    ("IOT_CONTROL", "off", "iot", "iot_off_modal", (
        "tem como apagar o quarto", "será que pode desligar o ventilador", "quero a luminária desligada",
    )),
    ("APP_OPEN", "open", "app", "app_sistema_loja", (
        "inicia a Microsoft Store", "abre o aplicativo Microsoft Store", "executa a loja de aplicativos do Windows",
    )),
    ("APP_OPEN", "open", "app", "app_sistema_windows", (
        "abre as Configurações do Windows", "inicia o Terminal do Windows", "executa o Gerenciador de Tarefas",
    )),
    ("APP_OPEN", "open", "app", "app_jogos", (
        "abre o aplicativo Xbox", "inicia o Steam no computador", "executa o launcher da Epic Games",
    )),
    ("APP_OPEN", "open", "app", "app_criacao", (
        "abre o Paint no computador", "inicia o editor de fotos", "executa o gravador de som do Windows",
    )),
    ("APP_OPEN", "open", "app", "app_modal", (
        "pode iniciar a loja de aplicativos", "consegue abrir as configurações do sistema", "tem como executar o terminal",
    )),
    ("APP_OPEN", "open", "app", "app_alvo_explicito", (
        "abre o programa chamado Microsoft Store", "inicia o app chamado Xbox", "roda o aplicativo Paint aqui",
    )),
    ("CLOSE_TAB", "close", "browser", "aba_direta", (
        "fecha essa aba", "fecha a aba atual agora", "encerra esta guia do navegador",
    )),
    ("CLOSE_TAB", "close", "browser", "aba_modal", (
        "pode fechar a aba que está aberta", "consegue encerrar essa guia", "tem como tirar esta aba",
    )),
    ("CLOSE_TAB", "close", "browser", "aba_coloquial", (
        "manda essa aba embora", "tira essa guia da tela", "fecha só esta página do navegador",
    )),
    ("CLOSE_APP", "close", "app", "fechar_app_direto", (
        "fecha o Spotify agora", "encerra o Discord", "finaliza o aplicativo Xbox",
    )),
    ("CLOSE_APP", "close", "app", "fechar_app_modal", (
        "pode encerrar a calculadora", "consegue encerrar o Paint", "tem como sair do Steam",
    )),
    ("CLOSE_APP", "close", "app", "fechar_app_explicito", (
        "fecha o programa Microsoft Store", "encerra o aplicativo Configurações", "finaliza o processo do bloco de notas",
    )),
    ("OPEN_URL", "open", "browser", "url_explicita", (
        "abre https://apps.microsoft.com", "acessa https://www.microsoft.com/store", "entra em https://store.steampowered.com",
    )),
    ("OPEN_URL", "open", "browser", "site_explicito", (
        "abre o site apps.microsoft.com", "acessa o site da loja do Steam", "entra na página web da Microsoft",
    )),
    ("OPEN_URL", "open", "browser", "url_no_navegador", (
        "abre microsoft.com no navegador", "vai para steampowered.com no Chrome", "carrega xbox.com em uma aba",
    )),
    ("MUSIC_SEARCH", "search", "music", "musica_verbo_ligar", (
        "liga uma música animada", "liga um som tranquilo", "liga alguma música para trabalhar",
    )),
    ("MUSIC_SEARCH", "search", "music", "musica_verbo_colocar", (
        "coloca uma música romântica", "põe uma música brasileira", "bota um som para jogar",
    )),
    ("MUSIC_SEARCH", "search", "music", "musica_busca_explicita", (
        "procura uma faixa de rock", "busca uma música calma", "encontra uma canção dos anos noventa",
    )),
)


GRUPOS_NEGADOS: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    ("MEDIA_CONTROL", "pause", "music", "pausa_negada", (
        "não pausa ainda", "não deixa a música no pause", "evita interromper o som agora",
    )),
    ("MEDIA_CONTROL", "play", "music", "play_negado", (
        "não despausa agora", "não retoma a reprodução", "evita dar play de novo",
    )),
    ("IOT_CONTROL", "on", "iot", "iot_on_negado", (
        "não liga essa luz", "não acende a lâmpada agora", "evita ativar o abajur",
    )),
    ("IOT_CONTROL", "off", "iot", "iot_off_negado", (
        "não desliga essa luz", "não apaga a lâmpada agora", "evita desativar o abajur",
    )),
    ("APP_OPEN", "open", "app", "app_open_negado", (
        "não abre a loja de aplicativos", "não inicia o Xbox agora", "evita executar o Paint",
    )),
    ("CLOSE_TAB", "close", "browser", "aba_close_negado", (
        "não fecha essa aba", "não encerra a guia atual", "evita tirar esta aba",
    )),
    ("CLOSE_APP", "close", "app", "app_close_negado", (
        "não fecha o Spotify", "não encerra o Discord", "evita finalizar o Xbox",
    )),
    ("OPEN_URL", "open", "browser", "url_open_negado", (
        "não abre microsoft.com", "não acessa a loja do Steam", "evita entrar em xbox.com",
    )),
    ("MUSIC_SEARCH", "search", "music", "musica_search_negada", (
        "não coloca música agora", "não procura nenhuma faixa", "evita buscar um som novo",
    )),
)


NUCLEOS_NAO_COMANDO: tuple[tuple[str, str], ...] = (
    ("music", "pausa aí"),
    ("music", "despausa o som"),
    ("music", "dá play de novo"),
    ("iot", "liga essa luz"),
    ("iot", "desliga essa luz"),
    ("iot", "acende o abajur"),
    ("app", "abre a loja de aplicativos"),
    ("app", "fecha o Spotify"),
    ("browser", "fecha essa aba"),
    ("browser", "abre microsoft.com"),
)

MOLDURAS_NAO_COMANDO: tuple[tuple[str, str], ...] = (
    ("relato", "ontem eu falei {nucleo} e funcionou"),
    ("terceiro", "meu irmão pediu {nucleo} durante o teste"),
    ("citacao", "a frase {nucleo} apareceu no tutorial"),
    ("meta", "{nucleo} é um exemplo de comando curto"),
    ("hipotese", "se eu quisesse fazer isso eu diria {nucleo}"),
    ("interface", "o botão com o texto {nucleo} ficou visível"),
)

RECEIPTS_RESERVADOS = frozenset({
    "oi lay, pode ligar a luz para mim",
    "liga a luz",
    "desliga a luz",
    "pausa",
    "despausa",
    "abre a microsoft store",
})


def _normalizar(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", base)).strip()


def _exemplo(
    texto: str,
    *,
    intent: str,
    is_command: bool,
    negated: bool,
    action: str,
    family: str,
    validation_group: str,
    source: str,
    domain: str,
) -> dict[str, Any]:
    return {
        "text": texto,
        "intent": intent,
        "is_command": is_command,
        "negated": negated,
        "action": action,
        "family": f"shadow_contrastivo_v2_{family}",
        "validation_group": f"shadow_contrastivo_v2_{validation_group}",
        "source": source,
        "domain": domain,
    }


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for intent, action, domain, grupo, frases in GRUPOS_COMANDO:
        for indice, frase in enumerate(frases, 1):
            exemplos.append(_exemplo(
                frase,
                intent=intent,
                is_command=True,
                negated=False,
                action=action,
                family=f"{grupo}_{indice}",
                validation_group=grupo,
                source="MANUAL_PARAPHRASE",
                domain=domain,
            ))
    for intent, action, domain, grupo, frases in GRUPOS_NEGADOS:
        for indice, frase in enumerate(frases, 1):
            exemplos.append(_exemplo(
                frase,
                intent=intent,
                is_command=True,
                negated=True,
                action=action,
                family=f"{grupo}_{indice}",
                validation_group=grupo,
                source="HARD_NEGATIVE",
                domain=domain,
            ))
    for indice_molde, (mecanismo, molde) in enumerate(MOLDURAS_NAO_COMANDO):
        for indice_nucleo, (domain, nucleo) in enumerate(NUCLEOS_NAO_COMANDO):
            grupo = f"nao_comando_{mecanismo}_{domain}"
            exemplos.append(_exemplo(
                molde.format(nucleo=nucleo),
                intent="NONE",
                is_command=False,
                negated=False,
                action="none",
                family=f"{grupo}_{indice_molde}_{indice_nucleo}",
                validation_group=grupo,
                source="HARD_NEGATIVE",
                domain=domain,
            ))
    return exemplos


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, Any]:
    itens = [dict(item) for item in exemplos]
    normalizados = [_normalizar(item.get("text")) for item in itens]
    repetidos = sorted(texto for texto, total in Counter(normalizados).items() if total > 1)
    if repetidos:
        raise ValueError(f"o lote contém textos duplicados: {repetidos[:3]}")
    reservados = {_normalizar(texto) for texto in RECEIPTS_RESERVADOS}
    copiados = sorted(set(normalizados) & reservados)
    if copiados:
        raise ValueError(f"o lote copiou receipts reservados: {copiados}")
    if any(item.get("source") == "CURATED_RECEIPT" for item in itens):
        raise ValueError("receipt reservado não pode virar exemplo de treino")
    if any("autoriza_execucao" in item for item in itens):
        raise ValueError("dataset não pode conceder autoridade operacional")
    familias = Counter(str(item.get("family") or "") for item in itens)
    por_variante = Counter(
        f"{item['intent']}:{item['action']}"
        for item in itens
        if item.get("is_command")
    )
    return {
        "total": len(itens),
        "comandos": sum(bool(item.get("is_command")) for item in itens),
        "comandos_negados": sum(
            bool(item.get("is_command")) and bool(item.get("negated"))
            for item in itens
        ),
        "nao_comandos": sum(not bool(item.get("is_command")) for item in itens),
        "familias": len(familias),
        "grupos_validacao": len({item.get("validation_group") for item in itens}),
        "max_exemplos_por_familia": max(familias.values(), default=0),
        "por_variante": dict(sorted(por_variante.items())),
    }


def gravar_jsonl_atomico(destino: str | Path, exemplos: Iterable[dict[str, Any]]) -> None:
    caminho = Path(destino)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    descritor, nome_temporario = tempfile.mkstemp(
        prefix=f".{caminho.name}.", suffix=".tmp", dir=caminho.parent
    )
    try:
        with os.fdopen(descritor, "w", encoding="utf-8", newline="\n") as arquivo:
            for item in exemplos:
                arquivo.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
        Path(nome_temporario).replace(caminho)
    except Exception:
        Path(nome_temporario).unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default="mente_laylay/neural/datasets/candidatos/shadow_contrastivo_v2.jsonl",
    )
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    gravar_jsonl_atomico(args.destino, exemplos)
    print(json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
