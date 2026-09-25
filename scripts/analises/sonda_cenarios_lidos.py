"""Sonda de cenários com proveniência local, sem promover fatos ao runtime."""

from __future__ import annotations

from html.parser import HTMLParser
import re

from mente_laylay.cognicao.pesquisa_multifonte import _INSTRUCAO_EXTERNA


def _presente(expressao: str, texto: str) -> bool:
    return bool(expressao and re.search(rf"(?<!\w){re.escape(expressao)}(?!\w)", texto, re.I))


def _frase_util(texto: str) -> bool:
    frase = str(texto or "").strip()
    return (
        40 <= len(frase) <= 300 and frase.endswith(".") and "?" not in frase
        and not re.search(r"^\s*(?:veja|confira|acesse|exemplo de)\b", frase, re.I)
    )


def candidatos_causais(blocos: list[dict], dominio: str) -> list[dict]:
    candidatos = []
    for bloco in blocos:
        frase = str(bloco.get("texto") or "").strip()
        if not (bloco.get("url") and bloco.get("secao")):
            continue
        if not _frase_util(frase) or not _presente(dominio, frase):
            continue
        condicao = re.search(r"\b(?:se|quando)\b", frase, re.I)
        mecanismo = re.search(r"\b(?:porque|pois|devido\s+a)\b", frase, re.I)
        efeito = re.search(r"\b(?:por\s+isso|portanto|ent[aã]o)\b", frase, re.I)
        if not (condicao and mecanismo and efeito and condicao.start() < mecanismo.start() < efeito.start()):
            continue
        candidatos.append({
            "tipo": "causal", "texto_fonte": frase,
            "url": str(bloco.get("url") or ""), "secao": str(bloco.get("secao") or ""),
            "indice": bloco.get("indice"), "mecanismo_textual": True,
            "verdade_externa_verificada": False,
        })
    return candidatos


def contrastes_observacionais(
    blocos: list[dict], objeto: str, lente_a: str, lente_b: str,
) -> list[dict]:
    """Candidatos próximos na mesma seção ou em subseções irmãs de um h2.

    A expressão "a mesma janela" só pode retomar um objeto explícito no
    bloco anterior próximo e sob o mesmo título-pai; ainda não prova verdade.
    """
    nome_objeto = re.sub(r"^(?:a|as|o|os|um|uma)\s+", "", objeto, flags=re.I).strip()
    nucleo = nome_objeto.split()[0] if nome_objeto else ""

    def menciona_objeto(texto: str, *, anafora: bool) -> bool:
        return _presente(objeto, texto) or bool(
            anafora and nucleo and re.search(
                rf"\b(?:o|a)\s+mesm[oa]\s+{re.escape(nucleo)}\b",
                texto, re.I,
            )
        )

    predicado = re.compile(r"\b(?:mostra|revela|representa|indica|lê|mede|é)\b", re.I)
    encontrados = []
    for a in blocos:
        texto_a = str(a.get("texto") or "").strip()
        if not (
            _frase_util(texto_a) and menciona_objeto(texto_a, anafora=False)
            and (_presente(lente_a, texto_a) or _presente(lente_a, str(a.get("secao") or "")))
        ):
            continue
        if not predicado.search(texto_a):
            continue
        for b in blocos:
            texto_b = str(b.get("texto") or "").strip()
            if a is b or not (
                _frase_util(texto_b) and menciona_objeto(texto_b, anafora=True)
                and (_presente(lente_b, texto_b) or _presente(lente_b, str(b.get("secao") or "")))
                and predicado.search(texto_b)
            ):
                continue
            try:
                distancia = int(b.get("indice")) - int(a.get("indice"))
            except (TypeError, ValueError):
                continue
            mesmo_pai = bool(
                a.get("secao_pai_id") == b.get("secao_pai_id")
                if a.get("secao_pai_id") is not None or b.get("secao_pai_id") is not None
                else a.get("secao_pai") == b.get("secao_pai")
            )
            mesma_secao = bool(
                a.get("secao") and a.get("secao") == b.get("secao")
                and mesmo_pai
                and (
                    a.get("secao_id") == b.get("secao_id")
                    if a.get("secao_id") is not None or b.get("secao_id") is not None
                    else True
                )
            )
            subsecoes_irmas = bool(
                a.get("secao_pai") and mesmo_pai
                and (
                    a.get("secao_id") != b.get("secao_id")
                    if a.get("secao_id") is not None or b.get("secao_id") is not None
                    else a.get("secao") != b.get("secao")
                )
            )
            proximos = 0 < distancia <= (3 if subsecoes_irmas else 2)
            if not (
                proximos and a.get("url") and a.get("url") == b.get("url")
                and (mesma_secao or subsecoes_irmas)
            ):
                continue
            encontrados.append({
                "tipo": "observacional", "texto_a": texto_a, "texto_b": texto_b,
                "url": a["url"],
                "secao": a["secao"] if mesma_secao else a["secao_pai"],
                "objeto": objeto, "indices": (a["indice"], b["indice"]),
                "verdade_externa_verificada": False,
            })
    return encontrados


class _BlocosComSecaoHTML(HTMLParser):
    _IGNORAR = frozenset({"script", "style", "nav", "footer", "header", "form", "svg", "noscript"})

    def __init__(self, url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.url = url
        self.ignorar = 0
        self.capturando = ""
        self.partes: list[str] = []
        self.secao = ""
        self.secao_pai = ""
        self._proximo_id_secao = 0
        self.secao_id = 0
        self.secao_pai_id = 0
        self.blocos: list[dict] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self._IGNORAR:
            self.ignorar += 1
        elif not self.ignorar and not self.capturando and tag in {"h1", "h2", "h3", "p", "li"}:
            self.capturando = tag
            self.partes = []
        elif not self.ignorar and self.capturando and tag == "br":
            self.partes.append(" ")

    def handle_data(self, data: str) -> None:
        if self.capturando and not self.ignorar:
            self.partes.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in self._IGNORAR:
            self.ignorar = max(0, self.ignorar - 1)
        elif tag == self.capturando:
            texto = re.sub(r"\s+", " ", "".join(self.partes)).strip()
            if tag in {"h1", "h2"}:
                self._proximo_id_secao += 1
                self.secao_pai_id = self._proximo_id_secao
                self.secao_id = self.secao_pai_id
                self.secao_pai = texto[:160]
                self.secao = texto[:160]
            elif tag == "h3":
                self._proximo_id_secao += 1
                self.secao_id = self._proximo_id_secao
                self.secao = texto[:160]
            elif 40 <= len(texto) <= 900 and not _INSTRUCAO_EXTERNA.search(texto):
                self.blocos.append({
                    "texto": texto, "indice": len(self.blocos),
                    "url": self.url, "secao": self.secao,
                    "secao_pai": self.secao_pai,
                    "secao_id": self.secao_id,
                    "secao_pai_id": self.secao_pai_id,
                })
            self.capturando = ""
            self.partes = []


def blocos_com_secao(texto_html: str, url: str) -> list[dict]:
    """Extrai blocos ordenados com seção da mesma página, sem promover fatos."""
    parser = _BlocosComSecaoHTML(str(url or ""))
    parser.feed(str(texto_html or "")[:1_500_000])
    return parser.blocos
