"""Pesquisa contextual curta para opiniões e respostas mais informadas."""

from __future__ import annotations

import os
import re
import time
import unicodedata
import urllib.parse
from collections.abc import Callable
from urllib.parse import urlparse

import requests


def _normalizar_texto_curto_basico(texto: str) -> str:
    bruto = str(texto or "").lower()
    sem_acento = unicodedata.normalize("NFKD", bruto)
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", sem_acento).strip()


def normalizar_tema_pesquisa(tema: str) -> str:
    t = str(tema or "").strip()
    if not t:
        return ""
    t = re.sub(
        r"^(?:o\s+que\s+voce\s+acha|o\s+que\s+você\s+acha|voce\s+acha|você\s+acha|qual\s+sua\s+opiniao|qual\s+sua\s+opinião|quem\s+e|quem\s+é|o\s+que\s+e|o\s+que\s+é|como\s+funciona|como\s+que\s+funciona|me\s+explica|explica|me\s+fala\s+sobre|fala\s+sobre|me\s+fala\s+de|fala\s+de)\s+",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"^(o|a|os|as|um|uma)\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(que saiu|que lançou|que lancou|que lançou agora|novo|nova|recentemente)\b", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(daqui|disso|daquilo|nisso|nesse|nessa|dela|dele|ela|ele|isso)\b", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip(" -,.!?;:")
    return t


def tema_pesquisa_baguncado(tema: str) -> bool:
    t = normalizar_tema_pesquisa(tema)
    if not t:
        return True
    if len(t) < 3:
        return True
    tokens = re.findall(r"[a-zA-Z0-9À-ÿ_-]+", t)
    if len(tokens) >= 10:
        return True
    lixo = {"que", "de", "do", "da", "pra", "para", "isso", "essa", "esse", "ela", "ele", "negocio", "negócio", "coisa"}
    uteis = [tok for tok in tokens if tok.lower() not in lixo and len(tok) >= 3]
    if len(uteis) == 0:
        return True
    return False


def pontuar_hit_tema(
    consulta: str,
    titulo: str,
    snippet: str = "",
    *,
    normalizar_texto_curto: Callable[[str], str] | None = None,
) -> int:
    normalizar = normalizar_texto_curto or _normalizar_texto_curto_basico
    c = normalizar(consulta)
    t = normalizar(titulo)
    s = normalizar(snippet)
    score = 0
    if c == t:
        score += 120
    if c and c in t:
        score += 70
    for token in re.findall(r"[a-z0-9à-ÿ_-]{3,}", c):
        if token in t:
            score += 18
        if token in s:
            score += 7
    if "(" in titulo or ")" in titulo:
        score -= 4
    return score


def pesquisar_contexto_tema(
    tema: str,
    ttl_s: float = 1800.0,
    *,
    cache: dict | None = None,
    normalizar_texto_curto: Callable[[str], str] | None = None,
) -> dict:
    """Busca um contexto curto sobre um tema para opiniões mais informadas."""
    cache_ref = cache if isinstance(cache, dict) else {}
    bruto = str(tema or "").strip()
    consulta = normalizar_tema_pesquisa(bruto)
    if not consulta:
        return {"ok": False, "tema": bruto}
    if tema_pesquisa_baguncado(consulta):
        return {"ok": False, "tema": bruto, "consulta": consulta, "motivo": "tema_baguncado"}

    normalizar = normalizar_texto_curto or _normalizar_texto_curto_basico
    chave = normalizar(consulta)
    agora = time.time()
    try:
        item_cache = dict(cache_ref.get(chave) or {})
    except Exception:
        item_cache = {}
    if item_cache and (agora - float(item_cache.get("ts") or 0.0)) < ttl_s:
        return dict(item_cache.get("data") or {})

    def cachear(data: dict) -> dict:
        cache_ref[chave] = {"ts": agora, "data": dict(data or {})}
        if len(cache_ref) > 80:
            antigos = list(cache_ref.keys())[:-50]
            for chave_antiga in antigos:
                cache_ref.pop(chave_antiga, None)
        return data

    try:
        for lang in ("pt", "en"):
            try:
                api = f"https://{lang}.wikipedia.org/w/api.php"
                r = requests.get(
                    api,
                    params={
                        "action": "query",
                        "format": "json",
                        "list": "search",
                        "srsearch": consulta,
                        "srlimit": 1,
                        "utf8": 1,
                    },
                    timeout=4,
                )
                r.raise_for_status()
                data = r.json()
                hits = ((data.get("query") or {}).get("search") or [])
                if not hits:
                    continue
                melhores = sorted(
                    hits[:4],
                    key=lambda h: pontuar_hit_tema(
                        consulta,
                        str(h.get("title") or ""),
                        str(h.get("snippet") or ""),
                        normalizar_texto_curto=normalizar,
                    ),
                    reverse=True,
                )
                hit = melhores[0] if melhores else {}
                titulo = str(hit.get("title") or consulta).strip()
                score_hit = pontuar_hit_tema(
                    consulta,
                    titulo,
                    str(hit.get("snippet") or ""),
                    normalizar_texto_curto=normalizar,
                )
                if score_hit < 18:
                    continue
                r2 = requests.get(
                    api,
                    params={
                        "action": "query",
                        "format": "json",
                        "prop": "extracts",
                        "exintro": 1,
                        "explaintext": 1,
                        "redirects": 1,
                        "titles": titulo,
                        "utf8": 1,
                    },
                    timeout=4,
                )
                r2.raise_for_status()
                data2 = r2.json()
                pages = ((data2.get("query") or {}).get("pages") or {})
                for _, page in pages.items():
                    resumo = str((page or {}).get("extract") or "").strip()
                    if resumo:
                        resumo = re.sub(r"\s+", " ", resumo).strip()
                        return cachear({
                            "ok": True,
                            "tema": bruto,
                            "consulta": consulta,
                            "titulo": titulo,
                            "resumo": resumo[:420],
                            "fonte": f"wikipedia_{lang}",
                            "confianca": min(0.98, 0.45 + (score_hit / 140.0)),
                        })
            except Exception:
                continue

        try:
            r = requests.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": consulta,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                    "kl": "br-pt",
                },
                timeout=4,
            )
            r.raise_for_status()
            data = r.json()
            resumo = str(data.get("AbstractText") or "").strip()
            titulo = str(data.get("Heading") or consulta).strip()
            if not resumo:
                for item in list(data.get("RelatedTopics") or []):
                    if isinstance(item, dict) and item.get("Text"):
                        resumo = str(item.get("Text") or "").strip()
                        break
            if resumo:
                resumo = re.sub(r"\s+", " ", resumo).strip()
                score_ddg = pontuar_hit_tema(consulta, titulo, resumo, normalizar_texto_curto=normalizar)
                if score_ddg < 14:
                    return cachear({"ok": False, "tema": bruto, "consulta": consulta, "motivo": "resultado_fraco"})
                return cachear({
                    "ok": True,
                    "tema": bruto,
                    "consulta": consulta,
                    "titulo": titulo,
                    "resumo": resumo[:420],
                    "fonte": "duckduckgo",
                    "confianca": min(0.9, 0.4 + (score_ddg / 140.0)),
                })
        except Exception:
            pass
    except Exception as e:
        print(f"⚠️ [PESQUISA TEMA] falha geral em '{consulta}': {e}")

    return cachear({"ok": False, "tema": bruto, "consulta": consulta})


def buscar_imagem_url(assunto: str, *, requests_get=None) -> str | None:
    termo = str(assunto or "").strip()
    if not termo:
        return None
    get = requests_get or requests.get
    for lang in ["pt", "en"]:
        try:
            api = f"https://{lang}.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "prop": "pageimages",
                "titles": termo,
                "pithumbsize": 1000,
                "redirects": 1,
            }
            r = get(api, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            pages = (data.get("query") or {}).get("pages") or {}
            for _, page in pages.items():
                thumb = page.get("thumbnail") if isinstance(page, dict) else None
                if isinstance(thumb, dict) and thumb.get("source"):
                    return str(thumb.get("source"))
        except Exception:
            continue
    return f"https://source.unsplash.com/featured/?{urllib.parse.quote(termo)}"


def nome_arquivo_imagem(assunto: str, ext: str, *, pasta_downloads: str | None = None) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "_", (assunto or "").strip().lower()).strip("_")
    base = base or "imagem_laylay"
    ext = (ext or "jpg").lower().lstrip(".")
    downloads = pasta_downloads or os.path.join(os.path.expanduser("~"), "Downloads")
    try:
        os.makedirs(downloads, exist_ok=True)
    except Exception:
        pass
    path = os.path.join(downloads, f"{base}.{ext}")
    if not os.path.exists(path):
        return path
    i = 2
    while True:
        cand = os.path.join(downloads, f"{base}_{i}.{ext}")
        if not os.path.exists(cand):
            return cand
        i += 1


def baixar_imagem_direto(
    assunto: str,
    *,
    buscar_url_cb: Callable[[str], str | None] | None = None,
    requests_get=None,
    pasta_downloads: str | None = None,
) -> str | None:
    termo = str(assunto or "").strip()
    if not termo:
        return None
    buscar_url = buscar_url_cb or (lambda valor: buscar_imagem_url(valor, requests_get=requests_get))
    url_img = buscar_url(termo)
    if not url_img:
        return None
    try:
        get = requests_get or requests.get
        r = get(url_img, stream=True, timeout=30)
        r.raise_for_status()
        ctype = str(r.headers.get("content-type") or "").lower()
        ext = "jpg"
        if "png" in ctype:
            ext = "png"
        elif "webp" in ctype:
            ext = "webp"
        elif "gif" in ctype:
            ext = "gif"
        elif "jpeg" in ctype or "jpg" in ctype:
            ext = "jpg"
        else:
            try:
                p = urlparse(url_img).path
                e = os.path.splitext(p)[1].lower().lstrip(".")
                if e in {"jpg", "jpeg", "png", "webp", "gif"}:
                    ext = "jpg" if e == "jpeg" else e
            except Exception:
                pass
        destino = nome_arquivo_imagem(termo, ext, pasta_downloads=pasta_downloads)
        with open(destino, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)
        return destino
    except Exception:
        return None


class PesquisaContextualRuntime:
    def __init__(
        self,
        *,
        normalizar_texto_curto: Callable[[str], str] | None = None,
        requests_get=None,
        pasta_downloads: str | None = None,
    ) -> None:
        self.cache_tema: dict = {}
        self.normalizar_texto_curto = normalizar_texto_curto
        self.requests_get = requests_get
        self.pasta_downloads = pasta_downloads

    def normalizar_tema_pesquisa(self, tema: str) -> str:
        return normalizar_tema_pesquisa(tema)

    def tema_pesquisa_baguncado(self, tema: str) -> bool:
        return tema_pesquisa_baguncado(tema)

    def pontuar_hit_tema(self, consulta: str, titulo: str, snippet: str = "") -> int:
        return pontuar_hit_tema(
            consulta,
            titulo,
            snippet,
            normalizar_texto_curto=self.normalizar_texto_curto,
        )

    def pesquisar_contexto_tema(self, tema: str, ttl_s: float = 1800.0) -> dict:
        return pesquisar_contexto_tema(
            tema,
            ttl_s=ttl_s,
            cache=self.cache_tema,
            normalizar_texto_curto=self.normalizar_texto_curto,
        )

    def buscar_imagem_url(self, assunto: str) -> str | None:
        return buscar_imagem_url(assunto, requests_get=self.requests_get)

    def nome_arquivo_imagem(self, assunto: str, ext: str) -> str:
        return nome_arquivo_imagem(assunto, ext, pasta_downloads=self.pasta_downloads)

    def baixar_imagem_direto(self, assunto: str) -> str | None:
        return baixar_imagem_direto(
            assunto,
            buscar_url_cb=self.buscar_imagem_url,
            requests_get=self.requests_get,
            pasta_downloads=self.pasta_downloads,
        )


def criar_pesquisa_contextual_runtime(
    *,
    normalizar_texto_curto: Callable[[str], str] | None = None,
    requests_get=None,
    pasta_downloads: str | None = None,
) -> PesquisaContextualRuntime:
    return PesquisaContextualRuntime(
        normalizar_texto_curto=normalizar_texto_curto,
        requests_get=requests_get,
        pasta_downloads=pasta_downloads,
    )
