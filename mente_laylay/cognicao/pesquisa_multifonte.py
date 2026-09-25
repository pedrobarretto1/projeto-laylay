"""Pesquisa de leitura: descoberta, leitura e proveniência de até cinco sites.

Resultado de busca é somente um ponteiro. Apenas texto lido de uma página
externa pode compor evidência; ele nunca é instrução nem autoriza comandos.
"""

from __future__ import annotations

import base64
import html
import ipaddress
import re
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse

import requests


_STOPWORDS = frozenset(
    "a ao aos as com como da das de do dos e em entre o os ou para por que qual "
    "quando sobre um uma me explique explica ensina ensinar diferença diferente".split()
)
_INSTRUCAO_EXTERNA = re.compile(
    r"\b(?:ignore|ignora|desconsidere|esque[cç]a|instru[cç][oõ]es|"
    r"system\s*prompt|assistant\s*:|execute|executar|ligue|desligue|"
    r"apague|delete|envie\s+(?:seus|os)\s+dados)\b",
    re.IGNORECASE,
)


def extrair_consulta_didatica(texto: str, *, pedido_anterior: str = "") -> str:
    """Obtém o assunto de um pedido de ensino, nunca um alvo operacional."""
    entrada = re.sub(r"\s+", " ", str(texto or "")).strip()
    mudanca_dominio = re.match(r"^mudando\s+para\s+([^,]+),\s*", entrada, re.I)
    dominio = str(mudanca_dominio.group(1) or "").strip() if mudanca_dominio else ""
    entrada = re.sub(
        r"^(?:(?:agora|mudando\s+(?:de\s+assunto|para\s+[^,]+))\s*,?\s*)+",
        "", entrada, flags=re.I,
    )
    if re.search(r"\b(?:n[aã]o entendi|explica de novo|explica melhor|n[aã]o ficou claro)\b", entrada, re.I):
        entrada = str(pedido_anterior or "").strip()
    elif pedido_anterior and re.search(r"\b(?:com\s+um\s+exemplo|um\s+exemplo\s+simples|de\s+outro\s+jeito)\b", entrada, re.I):
        entrada = str(pedido_anterior or "").strip()
    match = re.match(
        r"^(?:(?:por favor|pode|consegue)\s+)?(?:me\s+)?"
        r"(?:ensin[ae](?:\s+(?:a|sobre))?|explic[ae](?:\s+(?:a|sobre))?|"
        r"explique(?:\s+(?:a|sobre))?|quero entender|quero aprender|"
        r"qual (?:a )?diferen[cç]a(?: entre)?|como funciona)\s+(.+)$",
        entrada, re.I,
    )
    if not match:
        return ""
    assunto = match.group(1).strip(" ?!.,:;")
    # O formato pedido para a explicação não é parte do conceito pesquisado.
    # Em reexplicações com pedido anterior, esse tema já foi recuperado acima;
    # esta limpeza cobre também uma aula iniciada diretamente por exemplo.
    assunto = re.sub(
        r"^(?:com\s+)?(?:um\s+)?exemplo(?:\s+simples)?\s+(?:de\s+|sobre\s+)?",
        "", assunto, flags=re.I,
    ).strip()
    if dominio and re.match(r"^diferen[cç]a\s+entre\s+", assunto, re.I):
        assunto = f"{assunto} na {dominio}"
    if re.match(r"^(?:isso|de novo|melhor|de um jeito|mais devagar)\b", assunto, re.I):
        return ""
    if re.search(r"\b(?:ligar|desligar|abrir|apagar|deletar|salvar)\b", assunto, re.I):
        return ""
    return assunto[:180] if len(assunto) >= 3 else ""


def extrair_foco_didatico(texto: str) -> str:
    """Foco de exemplo pedido agora; não substitui o conceito da aula."""
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    achado = re.search(r"\b(?:com\s+um\s+exemplo|um\s+exemplo\s+simples)\s+(?:de|do|da|o|a)\s+(.+)", bruto, re.I)
    return achado.group(1).strip(" ?!.,:;")[:100] if achado else ""


def _url_publica(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = str(parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
            return False
        if host in {"localhost", "metadata.google.internal"} or host.endswith((".localhost", ".local", ".internal")):
            return False
        try:
            return ipaddress.ip_address(host).is_global
        except ValueError:
            return "." in host
    except ValueError:
        return False


def _dns_publico(url: str) -> bool:
    """Bloqueia destinos que resolvem para rede local antes do GET externo."""
    host = str(urlparse(url).hostname or "")
    try:
        enderecos = {item[4][0] for item in socket.getaddrinfo(host, None)}
        return bool(enderecos) and all(ipaddress.ip_address(ip).is_global for ip in enderecos)
    except (OSError, ValueError):
        return False


def _resolver_link_bing(href: str) -> str:
    url = html.unescape(str(href or ""))
    parsed = urlparse(url)
    if parsed.hostname in {"bing.com", "www.bing.com"} and parsed.path.startswith("/ck/"):
        codigo = str((parse_qs(parsed.query).get("u") or [""])[0])
        if codigo.startswith("a1"):
            try:
                url = base64.urlsafe_b64decode(codigo[2:] + "=" * (-len(codigo[2:]) % 4)).decode("utf-8")
            except (ValueError, UnicodeError):
                return ""
    return url if _url_publica(url) else ""


def _dominio(url: str) -> str:
    host = str(urlparse(url).hostname or "").lower()
    partes = host.removeprefix("www.").split(".")
    if len(partes) >= 3 and partes[-2:] in (["com", "br"], ["org", "br"], ["co", "uk"], ["ac", "uk"]):
        return ".".join(partes[-3:])
    return ".".join(partes[-2:]) if len(partes) >= 2 else host


def _consultas_busca(assunto: str, foco: str = "") -> list[tuple[str, str]]:
    complemento = f" {foco}" if foco else ""
    comparacao = re.match(
        r"^(?:qual\s+(?:a\s+)?)?diferen[cç]a\s+entre\s+(.+?)\s+e\s+(.+)$",
        assunto, re.I,
    )
    if comparacao:
        primeiro, segundo = comparacao.group(1).strip(), comparacao.group(2).strip()
        contexto = ""
        contexto_match = re.search(r"\s+(?:em|na|no)\s+([\wÀ-ÿ -]{2,50})$", segundo, re.I)
        if contexto_match:
            contexto = contexto_match.group(1).strip()
            segundo = segundo[:contexto_match.start()].strip()
        if contexto.casefold() in {"inglês", "ingles", "língua inglesa", "lingua inglesa"}:
            foco_primeiro = re.split(r"\s+e\s+(?:de\s+)?", foco, maxsplit=1, flags=re.I)[0]
            contexto_exemplo = f" {foco_primeiro}" if foco_primeiro else ""
            return [
                (f'"{primeiro}" vs "{segundo}" English grammar{contexto_exemplo}', f"{primeiro}|{segundo}"),
                (f'{primeiro} {segundo} inglês{contexto_exemplo}', f"{primeiro}|{segundo}"),
                (f'"{primeiro}" English grammar meaning examples{contexto_exemplo}', primeiro),
                (f'"{segundo}" English grammar meaning examples', segundo),
            ]
        sufixo = f" {contexto}" if contexto else ""
        return [
            (f"{primeiro} vs {segundo}{sufixo} diferença{complemento}", f"{primeiro}|{segundo}"),
            (f"{primeiro}{sufixo} conceito definição{complemento}", primeiro),
            (f"{segundo}{sufixo} conceito definição{complemento}", segundo),
        ]
    return [(assunto + complemento, "")]


def _hits_bing(texto_html: str) -> list[dict[str, str]]:
    hits = []
    blocos = re.split(r'<li\b[^>]*class="[^"]*\bb_algo\b[^"]*"[^>]*>', texto_html, flags=re.I)
    for bloco in blocos[1:]:
        ancora = re.search(r'<h2\b[^>]*>\s*<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', bloco, re.I | re.S)
        if not ancora:
            continue
        url = _resolver_link_bing(ancora.group(1))
        titulo = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", ancora.group(2)))).strip()
        if url and titulo:
            hits.append({"url": url, "titulo": titulo})
        if len(hits) >= 20:
            break
    return hits


def _hits_duckduckgo_lite(texto_html: str) -> list[dict[str, str]]:
    hits = []
    for href, corpo in re.findall(
        r'<a\b[^>]*href="([^"]+)"[^>]*class=[\'"]result-link[\'"][^>]*>(.*?)</a>',
        texto_html, re.I | re.S,
    ):
        alvo = html.unescape(href)
        if alvo.startswith("//"):
            alvo = "https:" + alvo
        if urlparse(alvo).hostname in {"duckduckgo.com", "www.duckduckgo.com"}:
            alvo = str((parse_qs(urlparse(alvo).query).get("uddg") or [""])[0])
        titulo = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", corpo))).strip()
        if _url_publica(alvo) and titulo:
            hits.append({"url": alvo, "titulo": titulo})
        if len(hits) >= 20:
            break
    return hits


class _TextoPagina(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ignorar = 0
        self.em_paragrafo = 0
        self.partes: list[str] = []
        self.paragrafos: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "nav", "footer", "header", "form", "svg", "noscript"}:
            self.ignorar += 1
        elif not self.ignorar and tag in {"p", "li", "h1", "h2", "h3", "dd"} and not self.em_paragrafo:
            self.em_paragrafo = 1
            self.partes = []

    def handle_data(self, data: str) -> None:
        if self.em_paragrafo and not self.ignorar:
            self.partes.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav", "footer", "header", "form", "svg", "noscript"}:
            self.ignorar = max(0, self.ignorar - 1)
        elif self.em_paragrafo and tag in {"p", "li", "h1", "h2", "h3", "dd"}:
            parte = re.sub(r"\s+", " ", html.unescape(" ".join(self.partes))).strip()
            if len(parte) >= 40 and not _INSTRUCAO_EXTERNA.search(parte):
                self.paragrafos.append(parte[:900])
            self.em_paragrafo = 0
            self.partes = []


def _tokens(texto: str) -> set[str]:
    return {t for t in re.findall(r"[a-zà-ÿ0-9]+", texto.casefold()) if (len(t) >= 3 or t in {"am", "is", "be"}) and t not in _STOPWORDS}


def _alvo_presente(alvo: str, texto: str) -> bool:
    if "|" in alvo:
        return all(_alvo_presente(parte.strip(), texto) for parte in alvo.split("|") if parte.strip())
    curto = len(re.sub(r"[^a-z]", "", alvo.casefold())) <= 5 or alvo.casefold().startswith("i ")
    if curto:
        return bool(re.search(rf"(?<!\w){re.escape(alvo)}(?!\w)", texto, re.I))
    termos_alvo = _tokens(alvo)
    return bool(termos_alvo) and termos_alvo.issubset(_tokens(texto))


def _comparacao_explicita_no_titulo(alvo: str, titulo: str) -> bool:
    if "|" not in alvo:
        return True
    primeiro, segundo = (parte.strip() for parte in alvo.split("|", 1))
    separador = r"\s*(?:vs\.?|versus|/|x|e)\s*"
    return any(bool(re.search(
        rf"(?<!\w){re.escape(esquerda)}(?!\w){separador}(?<!\w){re.escape(direita)}(?!\w)",
        titulo, re.I,
    )) for esquerda, direita in ((primeiro, segundo), (segundo, primeiro)))


def _frases_completas(paragrafo: str) -> list[str]:
    """Só frases inteiras podem ser promovidas de página lida a evidência."""
    return [
        frase.strip()
        for frase in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý“\"(])", paragrafo)
        if 30 <= len(frase.strip()) <= 300 and frase.strip().endswith(".")
    ]


def _frase_afirma_sobre_alvo(frase: str, alvo: str) -> bool:
    """Menção no título/corpo não basta: o trecho precisa predicar o alvo."""
    encontrado = re.search(rf"(?<!\w){re.escape(alvo)}(?!\w)", frase, re.I)
    if not encontrado:
        return False
    depois = frase[encontrado.end():encontrado.end() + 110]
    return bool(re.search(
        r"\b(?:refere-se|representa|consiste|significa|mostra|usa|utiliza|"
        r"repete|executa|transforma|produz|contém|possui|vive|vivem|viver|são|"
        r"é\s+(?:um|uma|o|a)\b|is|are|means|represents|refers|"
        r"uses|shows|executes|repeats|contains|lives|converts|iterates)\b",
        depois, re.I,
    ))


def _ler_fonte(hit: dict, consulta: str, get) -> dict | None:
    url = str(hit.get("url") or "")
    if not _url_publica(url):
        return None
    try:
        url_leitura = url
        parsed = urlparse(url)
        if parsed.hostname in {"pt.wikipedia.org", "en.wikipedia.org"} and parsed.path.startswith("/wiki/"):
            url_leitura = f"https://{parsed.hostname}/w/rest.php/v1/page/{parsed.path.removeprefix('/wiki/')}/html"
        if get is requests.get and not _dns_publico(url_leitura):
            return None
        resposta = get(url_leitura, headers={"User-Agent": "Mozilla/5.0 LaylayAssistant/2.5", "Accept": "text/html"}, timeout=4, allow_redirects=False)
        resposta.raise_for_status()
        if str(getattr(resposta, "url", "")) != url_leitura or int(getattr(resposta, "status_code", 0)) != 200:
            return None
        if "html" not in str(resposta.headers.get("content-type") or "").lower():
            return None
        if len(resposta.content) > 1_500_000:
            return None
        parser = _TextoPagina()
        parser.feed(str(resposta.text or "")[:1_500_000])
        alvo = str(hit.get("alvo") or "")
        termos = _tokens(alvo or consulta)

        def pontuacao(frase: str, indice: int, alvo_local: str = "") -> int:
            nome_tokens = sorted(_tokens(alvo_local or alvo), key=len, reverse=True)
            nome_principal = nome_tokens[0] if nome_tokens else ""
            termos_da_frase = _tokens(frase)
            definicao = bool(
                nome_principal and re.search(
                    rf"\b{re.escape(nome_principal)}\b.{{0,70}}\b(?:refere-se|representa|consiste|significa|mostra|usa|utiliza|repete|executa|é\s+(?:um|uma|o|a))\b",
                    frase, re.I,
                )
            )
            sobreposicao = _tokens(alvo_local) if alvo_local else termos
            return (
                2 * len(sobreposicao & termos_da_frase)
                + (3 if indice < 3 else 0)
                + (5 if definicao else 0)
                + (4 if (alvo_local or alvo) and _alvo_presente(alvo_local or alvo, frase) else 0)
            )

        frases_origem = [
            (indice, frase)
            for indice, paragrafo in enumerate(parser.paragrafos)
            for frase in _frases_completas(paragrafo)
        ]
        pontuados = sorted(
            (
                (pontuacao(frase, indice), frase)
                for indice, frase in frases_origem
            ),
            key=lambda par: par[0], reverse=True,
        )
        trechos = [
            frase for score, frase in pontuados
            if score > 0 and (not alvo or _frase_afirma_sobre_alvo(frase, alvo))
        ][:1]
        if "|" in alvo:
            trechos = []
            for parte in alvo.split("|"):
                nome_parte = parte.strip()
                pontuados_parte = sorted(
                    (
                        (pontuacao(frase, indice, nome_parte), frase)
                        for indice, frase in frases_origem
                        if _frase_afirma_sobre_alvo(frase, nome_parte)
                    ),
                    key=lambda par: par[0], reverse=True,
                )
                trecho_parte = pontuados_parte[0][1] if pontuados_parte else ""
                if trecho_parte and trecho_parte not in trechos:
                    trechos.append(trecho_parte)
        if alvo and not all(
            any(_alvo_presente(parte.strip(), frase) for frase in trechos)
            for parte in alvo.split("|")
        ):
            return None
        if not trechos:
            return None
        if not alvo and len(termos & _tokens(trechos[0])) < min(2, len(termos)):
            return None
        trecho_final = " ".join(trechos)
        if len(trecho_final) > 300:
            return None
        nome = alvo.split("|", 1)[0] if alvo else consulta
        nome_tokens = sorted(_tokens(nome) & _tokens(trecho_final), key=len, reverse=True)
        definicao_informativa = bool(
            any(
                re.search(
                    rf"\b{re.escape(termo)}\b.{{0,100}}\b(?:refere-se|representa|consiste|significa|means|represents|refers)\b",
                    trecho_final, re.I,
                )
                for termo in nome_tokens
            )
        )
        definicao_generica = bool(
            any(
                re.search(
                    rf"\b{re.escape(termo)}\b.{{0,70}}\b(?:é\s+(?:um|uma|o|a)|is\s+(?:a|an|the))\b",
                    trecho_final, re.I,
                )
                for termo in nome_tokens
            )
        )
        return {
            "titulo": str(hit.get("titulo") or "")[:160],
            "url": url,
            "url_leitura": url_leitura,
            "dominio": _dominio(url),
            "alvo": alvo,
            "trecho": trecho_final,
            "qualidade_trecho": 3 if definicao_informativa else 1 if definicao_generica else 0,
        }
    except Exception:
        return None


def pesquisar_evidencias_multifonte(
    consulta: str,
    *,
    foco: str = "",
    requests_get=None,
    max_fontes: int = 5,
    clock=time.time,
) -> dict:
    """Lê páginas públicas independentes; não promove snippets a fatos."""
    assunto = re.sub(r"\s+", " ", str(consulta or "")).strip()[:180]
    foco = re.sub(r"\s+", " ", str(foco or "")).strip()[:100]
    agora = float(clock())
    base = {
        "tema": assunto, "consulta": assunto, "foco": foco, "fonte": "web_multifonte",
        "fontes": [], "resumo": "", "confianca": 0.0, "ok": False,
        "evidencia_obtida_em": agora, "evidencia_validade_s": 1800.0,
        "evidencia_obtida_em_iso": datetime.fromtimestamp(agora, timezone.utc).isoformat(),
    }
    if not assunto or len(_tokens(assunto)) == 0:
        return {**base, "motivo": "tema_invalido"}
    get = requests_get or requests.get
    def buscar(entrada: tuple[str, str]) -> list[dict[str, str]]:
        termo, alvo = entrada
        encontrados = []
        try:
            busca = get("https://lite.duckduckgo.com/lite/", params={"q": termo},
                        headers={"User-Agent": "Mozilla/5.0 LaylayAssistant/2.5"}, timeout=5,
                        allow_redirects=False)
            busca.raise_for_status()
            if int(getattr(busca, "status_code", 0)) == 200:
                encontrados = _hits_duckduckgo_lite(str(busca.text or "")[:1_500_000])
        except Exception:
            pass
        if not encontrados:
            try:
                busca = get("https://www.bing.com/search", params={"q": termo, "setlang": "pt-BR"},
                            headers={"User-Agent": "Mozilla/5.0 LaylayAssistant/2.5"}, timeout=5,
                            allow_redirects=False)
                busca.raise_for_status()
                if int(getattr(busca, "status_code", 0)) == 200:
                    encontrados = _hits_bing(str(busca.text or "")[:1_500_000])
            except Exception:
                pass
        termos = _tokens(alvo or termo)
        def titulo_relevante(hit: dict[str, str]) -> bool:
            titulo = str(hit.get("titulo") or "")
            if "|" in alvo:
                return _comparacao_explicita_no_titulo(alvo, titulo) or bool(foco and _tokens(foco) & _tokens(titulo))
            if alvo:
                return _alvo_presente(alvo, titulo)
            return bool(termos & _tokens(titulo))

        encontrados = [hit for hit in encontrados if titulo_relevante(hit)]
        return [{**hit, "alvo": alvo} for hit in encontrados]

    consultas = _consultas_busca(assunto, foco)
    with ThreadPoolExecutor(max_workers=3) as pool:
        grupos = list(pool.map(buscar, consultas))
    hits = [
        grupo[indice]
        for indice in range(max((len(grupo) for grupo in grupos), default=0))
        for grupo in grupos if indice < len(grupo)
    ]
    if not hits:
        return {**base, "motivo": "busca_indisponivel"}
    distintos = []
    dominios = set()
    for hit in hits:
        dominio = _dominio(hit["url"])
        if dominio in dominios:
            continue
        dominios.add(dominio)
        distintos.append(hit)
        if len(distintos) >= 12:
            break
    with ThreadPoolExecutor(max_workers=5) as pool:
        lidos = list(pool.map(lambda hit: _ler_fonte(hit, assunto, get), distintos))
    candidatas = [item for item in lidos if item]
    candidatas.sort(
        key=lambda item: (
            int(item.get("qualidade_trecho") or 0),
            1 if "wikipedia.org" in str(item.get("dominio") or "") else 0,
        ),
        reverse=True,
    )
    fontes = []
    for _consulta, alvo in consultas:
        if alvo:
            escolhida = next((item for item in candidatas if item.get("alvo") == alvo), None)
            if escolhida and escolhida not in fontes:
                fontes.append(escolhida)
    fontes.extend(item for item in candidatas if item not in fontes)
    fontes = fontes[:max(1, min(5, max_fontes))]
    resumo = " ".join(str(item["trecho"]) for item in fontes)[:1200]
    # Duas páginas realmente lidas, em domínios independentes, são o piso.
    alvos = {parte.strip() for _consulta, alvo in consultas for parte in alvo.split("|") if parte.strip()}
    cobertos = {parte.strip() for item in fontes for parte in str(item.get("alvo") or "").split("|") if parte.strip()}
    foco_tokens = _tokens(foco)
    foco_coberto = not foco_tokens or any(foco_tokens & _tokens(str(item.get("trecho") or "")) for item in fontes)
    suficiente = len(fontes) >= 2 and alvos.issubset(cobertos) and foco_coberto
    return {
        **base,
        "ok": suficiente,
        "fontes": fontes,
        "resumo": resumo if suficiente else "",
        "confianca": 0.72 if suficiente else 0.0,
        "motivo": "fontes_lidas" if suficiente else "fontes_insuficientes",
    }
