"""Pesquisa somente leitura: cobertura de exemplos explícitos em oito temas.

Execute com ``python -m scripts.analises.medir_cobertura_exemplos``.
Não altera a Laylay, não registra aprendizado e não certifica a veracidade
de uma página apenas porque uma frase satisfaz o formato estrutural.
"""

from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
import json
import time

import requests

from mente_laylay.cognicao.pesquisa_multifonte import (
    _TextoPagina,
    _dns_publico,
    _url_publica,
    pesquisar_evidencias_multifonte,
)
from scripts.analises.sonda_exemplos_lidos import (
    blocos_python_documentados,
    candidatos_calculo,
    candidatos_exemplo,
)


TEMAS = (
    ("fotossíntese", "fotossíntese"),
    ("planta baixa na arquitetura", "planta baixa"),
    ("plantas anuais", "plantas anuais"),
    ("multiplicação na matemática", "multiplicação"),
    ("circuito elétrico em série", "circuito em série"),
    ("laço for em Python", "laço for"),
    ("variáveis em Python", "variáveis"),
    ("orquídeas", "orquídeas"),
)


def extrair_tipos_de_pagina(texto_html: str, url: str, tema: str, conceito: str) -> dict:
    """Extrai candidatos por tipo do mesmo HTML já lido; nunca executa código."""
    parser = _TextoPagina()
    parser.feed(str(texto_html or "")[:1_500_000])
    codigos: list[dict] = []
    if "python" in tema.casefold():
        for bloco in blocos_python_documentados(texto_html, url):
            if bloco["tipo"] != "codigo_python":
                continue
            try:
                arvore = ast.parse(bloco["codigo_apresentavel"])
            except SyntaxError:
                continue
            if conceito == "laço for" and not any(isinstance(n, ast.For) for n in ast.walk(arvore)):
                continue
            if conceito == "variáveis" and not any(isinstance(n, ast.Assign) for n in ast.walk(arvore)):
                continue
            codigos.append(bloco)
    return {
        "exemplos": candidatos_exemplo(parser.paragrafos, conceito)[:3],
        "contas": candidatos_calculo(parser.paragrafos)[:3] if conceito == "multiplicação" else [],
        "codigos": codigos[:3],
        "paragrafos": len(parser.paragrafos),
    }


def ler_exemplos(fonte: dict, tema: str, conceito: str) -> dict:
    url = str(fonte.get("url_leitura") or fonte.get("url") or "")
    if not _url_publica(url) or not _dns_publico(url):
        return {"url": url, "lida": False, "exemplos": [], "contas": [], "codigos": [], "motivo": "url_nao_publica"}
    try:
        resposta = requests.get(
            url, timeout=5, allow_redirects=False,
            headers={"User-Agent": "Mozilla/5.0 LaylayAssistant/2.5", "Accept": "text/html"},
        )
        if (
            resposta.status_code != 200 or resposta.url != url
            or "html" not in resposta.headers.get("content-type", "").lower()
            or len(resposta.content) > 1_500_000
        ):
            return {"url": url, "lida": False, "exemplos": [], "contas": [], "codigos": [], "motivo": "resposta_invalidada"}
        return {"url": url, "lida": True,
                **extrair_tipos_de_pagina(resposta.text, url, tema, conceito)}
    except (OSError, requests.RequestException, ValueError) as exc:
        return {"url": url, "lida": False, "exemplos": [], "contas": [], "codigos": [], "motivo": type(exc).__name__}


def medir(tema: str, conceito: str) -> dict:
    inicio = time.monotonic()
    busca = pesquisar_evidencias_multifonte(tema, max_fontes=5)
    fontes = list(busca.get("fontes") or [])
    with ThreadPoolExecutor(max_workers=3) as pool:
        lidas = list(pool.map(lambda fonte: ler_exemplos(fonte, tema, conceito), fontes))
    return {
        "tema": tema, "conceito": conceito, "pesquisa_ok": bool(busca.get("ok")),
        "fontes_selecionadas": len(fontes),
        "paginas_relidas": sum(bool(item["lida"]) for item in lidas),
        "paginas_com_instancia": sum(bool(item["exemplos"]) for item in lidas),
        "paginas_com_conta_conferida": sum(bool(item["contas"]) for item in lidas),
        "paginas_com_codigo_sintatico": sum(bool(item["codigos"]) for item in lidas),
        "exemplos": [
            {"url": item["url"], "texto": exemplo}
            for item in lidas for exemplo in item["exemplos"][:1]
        ][:5],
        "contas": [
            {"url": item["url"], **conta}
            for item in lidas for conta in item["contas"][:1]
        ][:5],
        "codigos": [
            {"url": item["url"], "tipo": bloco["tipo"],
             "codigo": bloco["codigo_apresentavel"][:400],
             "saida_confirmada": bloco["saida_confirmada"]}
            for item in lidas for bloco in item["codigos"][:1]
        ][:5],
        "tempo_s": round(time.monotonic() - inicio, 2),
    }


def main() -> None:
    with ThreadPoolExecutor(max_workers=2) as pool:
        for resultado in pool.map(lambda item: medir(*item), TEMAS):
            print(json.dumps(resultado, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
