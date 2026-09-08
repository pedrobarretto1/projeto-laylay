"""Gera cobertura contrastiva para aplicativos e arquivos.

Completa APP_OPEN, CLOSE_APP, FILE_READ e FILE_SEARCH sem consultar o Frozen.
O lote é staging: não treina, não promove e não autoriza execução.
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
    ("direta", "{imperativo}"),
    ("polida", "por favor {imperativo}"),
    ("modal", "pode {infinitivo}"),
    ("desejo", "quero que você {subjuntivo}"),
)

APLICATIVOS = (
    "a calculadora",
    "o bloco de notas",
    "o Spotify",
    "o aplicativo Discord",
    "o VS Code",
    "o explorador de arquivos",
)

ARQUIVOS = (
    "o relatório financeiro",
    "a planilha de orçamento",
    "o contrato de aluguel",
    "as notas da reunião",
    "o documento do projeto Laylay",
    "o arquivo de configuração",
)


ACOES = {
    ("APP_OPEN", "open"): (
        ("abrir", "abrir {alvo}", "abre {alvo}", "abra {alvo}"),
        ("iniciar", "iniciar {alvo}", "inicia {alvo}", "inicie {alvo}"),
        ("executar", "executar {alvo}", "executa {alvo}", "execute {alvo}"),
        ("rodar", "rodar {alvo}", "roda {alvo}", "rode {alvo}"),
        ("carregar", "carregar {alvo}", "carrega {alvo}", "carregue {alvo}"),
        ("lancar", "lançar {alvo}", "lança {alvo}", "lance {alvo}"),
        ("acionar", "acionar {alvo}", "aciona {alvo}", "acione {alvo}"),
        ("funcionar", "colocar {alvo} para funcionar", "coloca {alvo} para funcionar", "coloque {alvo} para funcionar"),
        ("ativar", "ativar {alvo}", "ativa {alvo}", "ative {alvo}"),
        ("subir", "subir {alvo} no computador", "sobe {alvo} no computador", "suba {alvo} no computador"),
    ),
    ("CLOSE_APP", "close"): (
        ("fechar", "fechar {alvo}", "fecha {alvo}", "feche {alvo}"),
        ("encerrar", "encerrar {alvo}", "encerra {alvo}", "encerre {alvo}"),
        ("sair", "sair de {alvo}", "sai de {alvo}", "saia de {alvo}"),
        ("finalizar", "finalizar {alvo}", "finaliza {alvo}", "finalize {alvo}"),
        ("terminar", "terminar a execução de {alvo}", "termina a execução de {alvo}", "termine a execução de {alvo}"),
        ("parar", "parar {alvo}", "para {alvo}", "pare {alvo}"),
        ("desativar", "desativar {alvo}", "desativa {alvo}", "desative {alvo}"),
        ("dispensar", "dispensar {alvo}", "dispensa {alvo}", "dispense {alvo}"),
        ("remover_tela", "tirar {alvo} da tela", "tira {alvo} da tela", "tire {alvo} da tela"),
        ("fechar_de_vez", "fechar {alvo} de vez", "fecha {alvo} de vez", "feche {alvo} de vez"),
        ("deixar_fechado", "deixar {alvo} fechado", "deixa {alvo} fechado", "deixe {alvo} fechado"),
    ),
    ("FILE_READ", "read"): (
        ("ler", "ler {alvo}", "lê {alvo}", "leia {alvo}"),
        ("conteudo", "mostrar o conteúdo de {alvo}", "mostra o conteúdo de {alvo}", "mostre o conteúdo de {alvo}"),
        ("abrir_leitura", "abrir {alvo} para leitura", "abre {alvo} para leitura", "abra {alvo} para leitura"),
        ("exibir_texto", "exibir o texto de {alvo}", "exibe o texto de {alvo}", "exiba o texto de {alvo}"),
        ("consultar", "consultar o conteúdo de {alvo}", "consulta o conteúdo de {alvo}", "consulte o conteúdo de {alvo}"),
        ("ver", "ver o que está escrito em {alvo}", "vê o que está escrito em {alvo}", "veja o que está escrito em {alvo}"),
        ("apresentar", "apresentar o conteúdo de {alvo}", "apresenta o conteúdo de {alvo}", "apresente o conteúdo de {alvo}"),
        ("recuperar_texto", "recuperar o texto de {alvo}", "recupera o texto de {alvo}", "recupere o texto de {alvo}"),
        ("carregar_texto", "carregar o texto de {alvo}", "carrega o texto de {alvo}", "carregue o texto de {alvo}"),
        ("mostrar_escrito", "mostrar o que diz {alvo}", "mostra o que diz {alvo}", "mostre o que diz {alvo}"),
    ),
    ("FILE_SEARCH", "search"): (
        ("localizar", "localizar {alvo}", "localiza {alvo}", "localize {alvo}"),
        ("encontrar", "encontrar {alvo}", "encontra {alvo}", "encontre {alvo}"),
        ("procurar", "procurar {alvo}", "procura {alvo}", "procure {alvo}"),
        ("buscar", "buscar {alvo} no computador", "busca {alvo} no computador", "busque {alvo} no computador"),
        ("achar", "achar {alvo}", "acha {alvo}", "ache {alvo}"),
        ("descobrir", "descobrir onde está {alvo}", "descobre onde está {alvo}", "descubra onde está {alvo}"),
        ("pesquisar", "pesquisar por {alvo} nos arquivos", "pesquisa por {alvo} nos arquivos", "pesquise por {alvo} nos arquivos"),
        ("vasculhar", "vasculhar as pastas atrás de {alvo}", "vasculha as pastas atrás de {alvo}", "vasculhe as pastas atrás de {alvo}"),
        ("verificar", "verificar a localização de {alvo}", "verifica a localização de {alvo}", "verifique a localização de {alvo}"),
        ("rastrear", "rastrear {alvo} no disco", "rastreia {alvo} no disco", "rastreie {alvo} no disco"),
    ),
}

ALVOS_POR_INTENT = {
    "APP_OPEN": APLICATIVOS,
    "CLOSE_APP": APLICATIVOS,
    "FILE_READ": ARQUIVOS,
    "FILE_SEARCH": ARQUIVOS,
}

NEGADAS = {
    "APP_OPEN": (
        ("nao", "não abra {alvo}"),
        ("evitar", "evita iniciar {alvo}"),
        ("dispensar", "não precisa executar {alvo}"),
        ("recusar", "prefiro não rodar {alvo}"),
        ("cancelar", "cancela a abertura de {alvo}"),
    ),
    "CLOSE_APP": (
        ("nao", "não feche {alvo}"),
        ("evitar", "evita encerrar {alvo}"),
        ("dispensar", "não precisa sair de {alvo}"),
        ("recusar", "prefiro não finalizar {alvo}"),
    ),
    "FILE_READ": (
        ("nao", "não leia {alvo}"),
        ("evitar", "evita abrir {alvo} para leitura"),
        ("dispensar", "não precisa mostrar {alvo}"),
        ("recusar", "prefiro não ver o conteúdo de {alvo}"),
        ("cancelar", "cancela a leitura de {alvo}"),
        ("manter", "mantenha {alvo} sem abrir"),
    ),
    "FILE_SEARCH": (
        ("nao", "não procure {alvo}"),
        ("evitar", "evita buscar {alvo}"),
        ("dispensar", "não precisa localizar {alvo}"),
        ("recusar", "prefiro não encontrar {alvo}"),
        ("cancelar", "cancela a busca por {alvo}"),
        ("deixar", "deixa a procura por {alvo} para depois"),
    ),
}

ESTADOS_AFIRMATIVOS_APP = (
    ("CLOSE_APP", "close", "manter_fechado", "mantenha {alvo} fechado"),
    ("APP_OPEN", "open", "manter_aberto", "mantenha {alvo} aberto"),
    ("APP_OPEN", "open", "continuar_funcionando", "deixa {alvo} funcionando"),
)

HARD_NEGATIVES = {
    "app": (
        ("relato_passado", "a", "ontem eu abri {alvo} para trabalhar"),
        ("relato_passado", "b", "mais cedo eu fechei {alvo} normalmente"),
        ("relato_terceiro", "a", "meu irmão iniciou {alvo} no computador"),
        ("relato_terceiro", "b", "ela encerrou {alvo} antes da reunião"),
        ("plano_futuro", "a", "amanhã vou instalar e abrir {alvo}"),
        ("plano_futuro", "b", "depois pretendo executar {alvo}"),
        ("hipotese", "a", "se fosse meu computador eu fecharia {alvo}"),
        ("hipotese", "b", "num trabalho eu iniciaria {alvo}"),
        ("citacao", "a", "ele disse abre {alvo} e saiu"),
        ("citacao", "b", "ela escreveu fecha {alvo} na mensagem"),
        ("metalinguagem", "a", "a frase execute {alvo} parece uma ordem"),
        ("metalinguagem", "b", "fechar {alvo} é apenas um exemplo de comando"),
        ("interface", "a", "esse botão inicia {alvo} automaticamente"),
        ("interface", "b", "o sistema consegue encerrar {alvo} sozinho"),
        ("tutorial", "a", "o manual ensina como executar {alvo}"),
        ("tutorial", "b", "assisti a um vídeo sobre configurar {alvo}"),
        ("preferencia", "a", "eu gosto de usar {alvo} para estudar"),
        ("preferencia", "b", "prefiro {alvo} para trabalhos longos"),
        ("evento", "a", "{alvo} iniciou sozinho depois da atualização"),
        ("evento", "b", "{alvo} fechou quando o computador travou"),
    ),
    "files": (
        ("relato_passado", "a", "ontem eu li {alvo} durante a reunião"),
        ("relato_passado", "b", "mais cedo eu encontrei {alvo} numa pasta"),
        ("relato_terceiro", "a", "meu irmão procurou {alvo} no notebook"),
        ("relato_terceiro", "b", "ela abriu {alvo} antes do almoço"),
        ("plano_futuro", "a", "amanhã vou revisar {alvo} com calma"),
        ("plano_futuro", "b", "depois pretendo buscar {alvo}"),
        ("hipotese", "a", "se fosse meu projeto eu leria {alvo}"),
        ("hipotese", "b", "numa auditoria eu procuraria {alvo}"),
        ("citacao", "a", "ele disse leia {alvo} e saiu"),
        ("citacao", "b", "ela escreveu procura {alvo} na mensagem"),
        ("metalinguagem", "a", "a frase localize {alvo} parece uma ordem"),
        ("metalinguagem", "b", "ler {alvo} é apenas um exemplo de comando"),
        ("interface", "a", "esse botão mostra {alvo} automaticamente"),
        ("interface", "b", "o sistema consegue localizar {alvo} sozinho"),
        ("tutorial", "a", "o manual ensina como encontrar {alvo}"),
        ("tutorial", "b", "assisti a um vídeo sobre organizar {alvo}"),
        ("preferencia", "a", "eu gosto de revisar {alvo} pela manhã"),
        ("preferencia", "b", "prefiro guardar {alvo} numa pasta separada"),
        ("evento", "a", "{alvo} apareceu sozinho na área de trabalho"),
        ("evento", "b", "{alvo} sumiu depois da atualização"),
    ),
}


def _exemplo(
    texto: str,
    *,
    intent: str,
    is_command: bool,
    negated: bool,
    action: str,
    family: str,
    source: str,
    domain: str,
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
        "domain": domain,
    }


def _dominio(intent: str) -> str:
    return "app" if intent in {"APP_OPEN", "CLOSE_APP"} else "files"


def _gerar_variante(intent: str, action: str) -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    alvos = ALVOS_POR_INTENT[intent]
    for indice, (label, infinitivo, imperativo, subjuntivo) in enumerate(
        ACOES[(intent, action)]
    ):
        for indice_molde, (modalidade, molde) in enumerate(MOLDURAS):
            familia = f"apps_arquivos_v1_{intent.casefold()}_{label}_{modalidade}"
            for deslocamento in range(3):
                alvo = alvos[(indice + indice_molde + deslocamento * 2) % len(alvos)]
                texto = molde.format(
                    infinitivo=infinitivo.format(alvo=alvo),
                    imperativo=imperativo.format(alvo=alvo),
                    subjuntivo=subjuntivo.format(alvo=alvo),
                )
                exemplos.append(_exemplo(
                    texto,
                    intent=intent,
                    is_command=True,
                    negated=False,
                    action=action,
                    family=familia,
                    source="MANUAL_PARAPHRASE",
                    domain=_dominio(intent),
                ))
    for indice, (mecanismo, molde) in enumerate(NEGADAS[intent]):
        for variante in ("a", "b"):
            familia = f"apps_arquivos_v1_{intent.casefold()}_negada_{mecanismo}_{variante}"
            base = 0 if variante == "a" else 3
            for deslocamento in range(2):
                alvo = alvos[(indice + base + deslocamento * 2) % len(alvos)]
                exemplos.append(_exemplo(
                    molde.format(alvo=alvo),
                    intent=intent,
                    is_command=True,
                    negated=True,
                    action=action,
                    family=familia,
                    source="HARD_NEGATIVE",
                    domain=_dominio(intent),
                ))
    return exemplos


def _gerar_estados_afirmativos_app() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for indice, (intent, action, mecanismo, molde) in enumerate(
        ESTADOS_AFIRMATIVOS_APP
    ):
        for variante in ("a", "b"):
            familia = (
                f"apps_arquivos_v1_{intent.casefold()}_"
                f"estado_{mecanismo}_{variante}"
            )
            base = 0 if variante == "a" else 3
            for deslocamento in range(2):
                alvo = APLICATIVOS[(indice + base + deslocamento * 2) % len(APLICATIVOS)]
                exemplos.append(_exemplo(
                    molde.format(alvo=alvo), intent=intent, is_command=True,
                    negated=False, action=action, family=familia,
                    source="MANUAL_PARAPHRASE", domain="app",
                ))
    return exemplos


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos = [
        item
        for intent, action in ACOES
        for item in _gerar_variante(intent, action)
    ]
    exemplos.extend(_gerar_estados_afirmativos_app())
    for domain, moldes in HARD_NEGATIVES.items():
        alvos = APLICATIVOS if domain == "app" else ARQUIVOS
        for indice, (mecanismo, variante, molde) in enumerate(moldes):
            familia = f"apps_arquivos_v1_{domain}_nao_comando_{mecanismo}_{variante}"
            for deslocamento in range(2):
                alvo = alvos[(indice + deslocamento * 3) % len(alvos)]
                exemplos.append(_exemplo(
                    molde.format(alvo=alvo),
                    intent="NONE",
                    is_command=False,
                    negated=False,
                    action="none",
                    family=familia,
                    source="HARD_NEGATIVE",
                    domain=domain,
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
    resumo: dict[str, int] = {
        "total": len(itens),
        "hard_negatives_app": sum(
            not item["is_command"] and item["domain"] == "app" for item in itens
        ),
        "hard_negatives_files": sum(
            not item["is_command"] and item["domain"] == "files" for item in itens
        ),
        "max_exemplos_por_familia": max(
            Counter(item["family"] for item in itens).values(), default=0
        ),
    }
    for intent, action in ACOES:
        chave = intent.casefold()
        comandos = [
            item for item in itens
            if item["intent"] == intent and item["action"] == action
        ]
        resumo[chave] = len(comandos)
        resumo[f"{chave}_negados"] = sum(item["negated"] for item in comandos)
        resumo[f"{chave}_familias"] = len({item["family"] for item in comandos})
    esperado = {
        "total": 668,
        "hard_negatives_app": 40,
        "hard_negatives_files": 40,
        "max_exemplos_por_familia": 3,
        "app_open": 148,
        "app_open_negados": 20,
        "app_open_familias": 54,
        "close_app": 152,
        "close_app_negados": 16,
        "close_app_familias": 54,
        "file_read": 144,
        "file_read_negados": 24,
        "file_read_familias": 52,
        "file_search": 144,
        "file_search_negados": 24,
        "file_search_familias": 52,
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
        default="mente_laylay/neural/datasets/candidatos/apps_arquivos_onda_v1.jsonl",
    )
    args = parser.parse_args()
    resumo = escrever_lote(args.destino)
    print(json.dumps({"destino": args.destino, **resumo}, ensure_ascii=False))


if __name__ == "__main__":
    main()
