"""Sonda isolada de candidatos a exemplos literais em páginas já lidas.

Um candidato não é uma alegação verificada e não entra na fala da Laylay.
"""

from __future__ import annotations

import ast
from html.parser import HTMLParser
import re

from mente_laylay.cognicao.pesquisa_multifonte import _INSTRUCAO_EXTERNA, _frases_completas


def candidatos_exemplo(paragrafos: list[str], conceito: str) -> list[str]:
    """Aceita só instância nomeada explicitamente como membro da classe.

    Intencionalmente conservador: não infere exemplo de uma definição genérica
    nem de uma chamada do tipo "veja exemplos". Outros formatos podem ser
    estudados depois, sem afrouxar este contrato.
    """
    alvo = str(conceito or "").strip()
    if not alvo:
        return []
    encontrados: list[str] = []
    for paragrafo in paragrafos:
        for frase in _frases_completas(paragrafo):
            if not re.search(rf"(?<!\w){re.escape(alvo)}(?!\w)", frase, re.I):
                continue
            nomeado = re.match(r"^(?:\d+\.\s*)?(?P<nome>[^:]{3,50}):\s+(?P<descricao>.+)$", frase)
            if not nomeado:
                continue
            nome = re.sub(r"^(?:a|as|o|os|um|uma)\s+", "", nomeado.group("nome"), flags=re.I).strip()
            descricao = nomeado.group("descricao")
            verbo = re.search(r"\b(?:é|são|is|are)\b", descricao, re.I)
            if not verbo or nome.casefold() == alvo.casefold():
                continue
            # "Baratas: as plantas anuais são mais baratas" classifica uma
            # propriedade, não uma instância. O nome deve ser o sujeito.
            sujeito = descricao[:verbo.start()]
            if not re.search(rf"(?<!\w){re.escape(nome)}(?!\w)", sujeito, re.I):
                continue
            encontrados.append(frase)
    return encontrados


def candidatos_calculo(paragrafos: list[str]) -> list[dict[str, str]]:
    """Extrai só a conta conferida; a frase original permanece como proveniência."""
    encontrados: list[dict[str, str]] = []
    for paragrafo in paragrafos:
        for frase in _frases_completas(paragrafo):
            expressoes = re.findall(r"(?<!\w)(\d{1,5})\s*[x×*]\s*(\d{1,5})\s*=\s*(\d{1,10})(?!\w)", frase, re.I)
            if expressoes and all(int(a) * int(b) == int(resultado) for a, b, resultado in expressoes):
                encontrados.extend(
                    {"conta": f"{a} × {b} = {resultado}", "frase_fonte": frase}
                    for a, b, resultado in expressoes
                )
    return encontrados


class _BlocosPythonHTML(HTMLParser):
    _IGNORAR = frozenset({"script", "style", "nav", "footer", "header", "form", "svg", "noscript"})

    def __init__(self, url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.url = url
        self.ignorar = 0
        self.ultimo_paragrafo = ""
        self.partes_paragrafo: list[str] = []
        self.em_paragrafo = False
        self.em_pre = False
        self.partes_pre: list[str] = []
        self.pre_python = False
        self.contexto_pre = ""
        self.blocos: list[dict] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self._IGNORAR:
            self.ignorar += 1
            return
        if self.ignorar:
            return
        atributos = dict(attrs)
        if tag == "p" and not self.em_pre:
            self.em_paragrafo = True
            self.partes_paragrafo = []
        elif tag == "pre":
            self.em_pre = True
            self.partes_pre = []
            self.pre_python = False
            self.contexto_pre = self.ultimo_paragrafo
        elif tag == "code" and self.em_pre:
            classes = str(atributos.get("class") or "").casefold().split()
            self.pre_python = self.pre_python or any(
                classe in {"language-python", "language-py", "lang-python"}
                for classe in classes
            )

    def handle_data(self, data: str) -> None:
        if self.ignorar:
            return
        if self.em_pre:
            self.partes_pre.append(data)
        elif self.em_paragrafo:
            self.partes_paragrafo.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in self._IGNORAR:
            self.ignorar = max(0, self.ignorar - 1)
            return
        if self.ignorar:
            return
        if tag == "p" and self.em_paragrafo:
            contexto = re.sub(r"\s+", " ", "".join(self.partes_paragrafo)).strip()[:300]
            self.ultimo_paragrafo = "" if _INSTRUCAO_EXTERNA.search(contexto) else contexto
            self.em_paragrafo = False
        elif tag == "pre" and self.em_pre:
            codigo = "".join(self.partes_pre).strip("\r\n")
            self.em_pre = False
            if not codigo or len(codigo) > 5000 or len(codigo.splitlines()) > 100:
                return
            codigo_apresentavel = ""
            if re.search(r"(?m)^\s*(?:>>>|\.\.\.)\s", codigo):
                tipo = "transcricao"
            elif self.pre_python:
                try:
                    codigo_apresentavel = ast.unparse(ast.parse(codigo))
                    tipo = "codigo_python"
                except (SyntaxError, RecursionError, ValueError):
                    tipo = "fragmento_sintatico"
            else:
                return
            self.blocos.append({
                "tipo": tipo, "codigo": codigo,
                "codigo_apresentavel": codigo_apresentavel,
                "contexto": self.contexto_pre, "url": self.url,
                "saida_confirmada": None,
            })


def blocos_python_documentados(texto_html: str, url: str) -> list[dict]:
    """Lê código/REPL da página; sintaxe não autoriza execução nem prova saída."""
    parser = _BlocosPythonHTML(str(url or ""))
    parser.feed(str(texto_html or "")[:1_500_000])
    return parser.blocos
