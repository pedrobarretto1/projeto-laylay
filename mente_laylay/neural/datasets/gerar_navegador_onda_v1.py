"""Gera cobertura contrastiva para quatro comandos de navegador.

O lote completa CLOSE_TAB, OPEN_URL, LIST_TABS e SEARCH sem consultar o Frozen.
Ele permanece em staging: não treina, não promove e não autoriza execução.
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

ALVOS_ABA = (
    "esta aba",
    "a guia atual",
    "a página aberta",
    "a aba de notícias",
    "essa guia do navegador",
    "a aba que está na frente",
)

DESTINOS = (
    "o portal da universidade",
    "a documentação do Python",
    "o site de receitas",
    "a página da biblioteca",
    "o painel do roteador",
    "o portal de notícias locais",
)

COLECOES_ABAS = (
    "as abas abertas",
    "todas as guias do navegador",
    "as páginas que estão abertas",
    "a relação das abas atuais",
    "as guias desta janela",
    "a lista de páginas abertas",
)

CONSULTAS = (
    "como cuidar de orquídeas",
    "receita de pão de queijo",
    "história da computação",
    "previsão de eclipse solar",
    "como funciona energia eólica",
    "bibliotecas Python para gráficos",
)


# label, infinitivo, imperativo, subjuntivo. Dez paradigmas x quatro molduras
# produzem 40 famílias afirmativas para cada variante.
ACOES = {
    ("CLOSE_TAB", "close"): (
        ("fechar", "fechar {alvo}", "fecha {alvo} agora", "feche {alvo}"),
        ("encerrar", "encerrar {alvo}", "encerra {alvo}", "encerre {alvo}"),
        ("remover", "remover {alvo}", "remove {alvo}", "remova {alvo}"),
        ("dispensar", "dispensar {alvo}", "dispensa {alvo}", "dispense {alvo}"),
        ("descartar", "descartar {alvo}", "descarta {alvo}", "descarte {alvo}"),
        ("finalizar", "finalizar {alvo}", "finaliza {alvo}", "finalize {alvo}"),
        ("tirar", "tirar {alvo} do navegador", "tira {alvo} do navegador", "tire {alvo} do navegador"),
        ("eliminar", "eliminar {alvo} da janela", "elimina {alvo} da janela", "elimine {alvo} da janela"),
        ("sumir", "fazer {alvo} sumir", "faz {alvo} sumir", "faça {alvo} sumir"),
        ("fechar_de_vez", "fechar {alvo} de vez", "fecha {alvo} de vez", "feche {alvo} de vez"),
    ),
    ("OPEN_URL", "open"): (
        ("abrir", "abrir {alvo}", "abre {alvo}", "abra {alvo}"),
        ("acessar", "acessar {alvo}", "acessa {alvo}", "acesse {alvo}"),
        ("visitar", "visitar {alvo}", "visita {alvo}", "visite {alvo}"),
        ("entrar", "entrar em {alvo}", "entra em {alvo}", "entre em {alvo}"),
        ("navegar", "navegar até {alvo}", "navega até {alvo}", "navegue até {alvo}"),
        ("ir", "ir para {alvo}", "vai para {alvo}", "vá para {alvo}"),
        ("carregar", "carregar {alvo}", "carrega {alvo}", "carregue {alvo}"),
        ("mostrar", "mostrar {alvo} no navegador", "mostra {alvo} no navegador", "mostre {alvo} no navegador"),
        ("exibir", "exibir {alvo} na tela", "exibe {alvo} na tela", "exiba {alvo} na tela"),
        ("levar", "me levar até {alvo}", "me leva até {alvo}", "me leve até {alvo}"),
    ),
    ("LIST_TABS", "list"): (
        ("listar", "listar {alvo}", "lista {alvo}", "liste {alvo}"),
        ("mostrar", "mostrar {alvo}", "mostra {alvo}", "mostre {alvo}"),
        ("exibir", "exibir {alvo}", "exibe {alvo}", "exiba {alvo}"),
        ("apresentar", "apresentar {alvo}", "apresenta {alvo}", "apresente {alvo}"),
        ("enumerar", "enumerar {alvo}", "enumera {alvo}", "enumere {alvo}"),
        ("relacionar", "relacionar {alvo}", "relaciona {alvo}", "relacione {alvo}"),
        ("ver", "ver {alvo}", "mostra para mim {alvo}", "mostre para mim {alvo}"),
        ("conferir", "conferir {alvo}", "confere {alvo}", "confira {alvo}"),
        ("consultar", "consultar {alvo}", "consulta {alvo}", "consulte {alvo}"),
        ("dizer", "dizer quais são {alvo}", "diz quais são {alvo}", "diga quais são {alvo}"),
    ),
    ("SEARCH", "search"): (
        ("pesquisar", "pesquisar {alvo}", "pesquisa {alvo}", "pesquise {alvo}"),
        ("buscar", "buscar {alvo}", "busca {alvo}", "busque {alvo}"),
        ("procurar", "procurar {alvo}", "procura {alvo}", "procure {alvo}"),
        ("investigar", "investigar {alvo} na internet", "investiga {alvo} na internet", "investigue {alvo} na internet"),
        ("encontrar", "encontrar informações sobre {alvo}", "encontra informações sobre {alvo}", "encontre informações sobre {alvo}"),
        ("consultar", "consultar na web sobre {alvo}", "consulta na web sobre {alvo}", "consulte na web sobre {alvo}"),
        ("fazer_busca", "fazer uma busca por {alvo}", "faz uma busca por {alvo}", "faça uma busca por {alvo}"),
        ("descobrir", "descobrir na internet {alvo}", "descobre na internet {alvo}", "descubra na internet {alvo}"),
        ("levantar", "levantar informações sobre {alvo}", "levanta informações sobre {alvo}", "levante informações sobre {alvo}"),
        ("pesquisar_web", "pesquisar na web por {alvo}", "pesquisa na web por {alvo}", "pesquise na web por {alvo}"),
    ),
}

ALVOS_POR_INTENT = {
    "CLOSE_TAB": ALVOS_ABA,
    "OPEN_URL": DESTINOS,
    "LIST_TABS": COLECOES_ABAS,
    "SEARCH": CONSULTAS,
}

NEGADAS = {
    "CLOSE_TAB": (
        ("nao", "não feche {alvo}"),
        ("manter", "mantenha {alvo} aberta"),
        ("deixar", "deixa {alvo} como está"),
        ("evitar", "evita fechar {alvo}"),
        ("continuar", "continue com {alvo} aberta"),
        ("conservar", "quero conservar {alvo}"),
    ),
    "OPEN_URL": (
        ("nao", "não abra {alvo}"),
        ("evitar", "evita acessar {alvo}"),
        ("ficar", "fica longe de {alvo}"),
        ("dispensar", "não precisa visitar {alvo}"),
        ("recusar", "prefiro não entrar em {alvo}"),
        ("cancelar", "cancela a abertura de {alvo}"),
    ),
    "LIST_TABS": (
        ("nao", "não liste {alvo}"),
        ("evitar", "evita mostrar {alvo}"),
        ("dispensar", "não precisa exibir {alvo}"),
        ("recusar", "prefiro não ver {alvo}"),
        ("ocultar", "mantenha {alvo} ocultas"),
        ("cancelar", "cancela a listagem de {alvo}"),
    ),
    "SEARCH": (
        ("nao", "não pesquise {alvo}"),
        ("evitar", "evita buscar {alvo}"),
        ("dispensar", "não precisa procurar {alvo}"),
        ("recusar", "prefiro não pesquisar {alvo}"),
        ("cancelar", "cancela a busca por {alvo}"),
        ("deixar", "deixa a pesquisa de {alvo} para depois"),
    ),
}

NAO_COMANDOS = (
    ("relato_passado", "a", "ontem eu abri {alvo} durante a pesquisa"),
    ("relato_passado", "b", "mais cedo eu fechei {alvo} sem problema"),
    ("relato_terceiro", "a", "meu irmão pesquisou {alvo} no computador"),
    ("relato_terceiro", "b", "ela listou {alvo} durante a reunião"),
    ("plano_futuro", "a", "amanhã vou visitar {alvo} com calma"),
    ("plano_futuro", "b", "depois pretendo pesquisar {alvo}"),
    ("hipotese", "a", "se fosse meu navegador eu fecharia {alvo}"),
    ("hipotese", "b", "num trabalho eu buscaria {alvo}"),
    ("citacao", "a", "ele disse abre {alvo} e saiu"),
    ("citacao", "b", "ela escreveu fecha {alvo} na mensagem"),
    ("metalinguagem", "a", "a frase pesquise {alvo} parece uma ordem"),
    ("metalinguagem", "b", "listar {alvo} é apenas um exemplo de comando"),
    ("interface", "a", "esse botão abre {alvo} automaticamente"),
    ("interface", "b", "o navegador consegue fechar {alvo} sozinho"),
    ("tutorial", "a", "o manual ensina como acessar {alvo}"),
    ("tutorial", "b", "assisti a um vídeo sobre pesquisar {alvo}"),
    ("preferencia", "a", "eu gosto de consultar {alvo} para estudar"),
    ("preferencia", "b", "prefiro deixar {alvo} aberta enquanto trabalho"),
    ("comparacao", "a", "no navegador antigo era difícil achar {alvo}"),
    ("comparacao", "b", "neste navegador {alvo} aparece mais rápido"),
    ("evento_automatico", "a", "{alvo} abriu sozinha depois da atualização"),
    ("evento_automatico", "b", "{alvo} sumiu quando o navegador travou"),
    ("pergunta_tecnica", "a", "como funciona o histórico de {alvo}"),
    ("pergunta_tecnica", "b", "qual componente lista {alvo} no navegador"),
    ("assunto", "a", "a conversa era sobre {alvo}"),
    ("assunto", "b", "estávamos discutindo como pesquisar {alvo}"),
    ("desejo_passado", "a", "ontem eu queria visitar {alvo}"),
    ("desejo_passado", "b", "mais cedo tive vontade de buscar {alvo}"),
    ("pedido_reportado", "a", "ela pediu que eu abrisse {alvo}"),
    ("pedido_reportado", "b", "ele queria que eu fechasse {alvo}"),
    ("descricao", "a", "{alvo} tem um endereço muito comprido"),
    ("descricao", "b", "a lista de {alvo} ocupa a lateral da tela"),
    ("capacidade", "a", "um script pode pesquisar {alvo} automaticamente"),
    ("capacidade", "b", "uma extensão sabe listar {alvo}"),
    ("condicional_irreal", "a", "eu abriria {alvo} se estivesse trabalhando"),
    ("condicional_irreal", "b", "eu fecharia {alvo} se fosse necessário"),
    ("lembranca", "a", "lembro de ter pesquisado {alvo} no ano passado"),
    ("lembranca", "b", "acho que já visitei {alvo} antes"),
    ("explicacao", "a", "pesquisar {alvo} significa procurar informação"),
    ("explicacao", "b", "fechar {alvo} libera espaço na janela"),
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
        "validation_group": family.rsplit("_", 1)[0],
        "source": source,
        "domain": "browser",
    }


def _gerar_variante(intent: str, action: str) -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    alvos = ALVOS_POR_INTENT[intent]
    for indice, (label, infinitivo, imperativo, subjuntivo) in enumerate(
        ACOES[(intent, action)]
    ):
        for indice_molde, (modalidade, molde) in enumerate(MOLDURAS):
            familia = f"navegador_v1_{intent.casefold()}_{label}_{modalidade}"
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
                ))
    for indice, (mecanismo, molde) in enumerate(NEGADAS[intent]):
        for variante in ("a", "b"):
            familia = (
                f"navegador_v1_{intent.casefold()}_negada_{mecanismo}_{variante}"
            )
            deslocamento_base = 0 if variante == "a" else 3
            for deslocamento in range(2):
                alvo = alvos[(indice + deslocamento_base + deslocamento * 2) % len(alvos)]
                exemplos.append(_exemplo(
                    molde.format(alvo=alvo),
                    intent=intent,
                    is_command=True,
                    negated=True,
                    action=action,
                    family=familia,
                    source="HARD_NEGATIVE",
                ))
    return exemplos


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos = [
        item
        for intent, action in ACOES
        for item in _gerar_variante(intent, action)
    ]
    alvos_contraste = (
        *ALVOS_ABA[:2],
        *DESTINOS[:2],
        *COLECOES_ABAS[:2],
        *CONSULTAS[:2],
    )
    for indice, (mecanismo, variante, molde) in enumerate(NAO_COMANDOS):
        familia = f"navegador_v1_nao_comando_{mecanismo}_{variante}"
        for deslocamento in range(2):
            alvo = alvos_contraste[(indice + deslocamento * 3) % len(alvos_contraste)]
            exemplos.append(_exemplo(
                molde.format(alvo=alvo),
                intent="NONE",
                is_command=False,
                negated=False,
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
        repetidos = [texto for texto, total in Counter(textos).items() if total > 1]
        raise ValueError(f"o lote contém textos duplicados: {repetidos[:3]}")
    resumo: dict[str, int] = {
        "total": len(itens),
        "nao_comandos": sum(not item["is_command"] for item in itens),
        "familias_nao_comando": len({
            item["family"] for item in itens if not item["is_command"]
        }),
        "max_exemplos_por_familia": max(
            Counter(item["family"] for item in itens).values(),
            default=0,
        ),
    }
    for intent, action in ACOES:
        prefixo = intent.casefold()
        comandos = [
            item
            for item in itens
            if item["intent"] == intent and item["action"] == action
        ]
        resumo[prefixo] = len(comandos)
        resumo[f"{prefixo}_negados"] = sum(item["negated"] for item in comandos)
        resumo[f"{prefixo}_familias"] = len({item["family"] for item in comandos})
    esperado = {
        "total": 656,
        "nao_comandos": 80,
        "familias_nao_comando": 40,
        "max_exemplos_por_familia": 3,
        "close_tab": 144,
        "close_tab_negados": 24,
        "close_tab_familias": 52,
        "open_url": 144,
        "open_url_negados": 24,
        "open_url_familias": 52,
        "list_tabs": 144,
        "list_tabs_negados": 24,
        "list_tabs_familias": 52,
        "search": 144,
        "search_negados": 24,
        "search_familias": 52,
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
        default="mente_laylay/neural/datasets/candidatos/navegador_onda_v1.jsonl",
    )
    args = parser.parse_args()
    resumo = escrever_lote(args.destino)
    print(json.dumps({"destino": args.destino, **resumo}, ensure_ascii=False))


if __name__ == "__main__":
    main()
