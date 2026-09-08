"""Pesquisa contextual curta para opiniões e respostas mais informadas."""

from __future__ import annotations

import os
import re
import threading
import time
import unicodedata
import urllib.parse
import html as html_lib
from collections.abc import Callable
from datetime import datetime, timezone
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
    requests_get=None,
    clock: Callable[[], float] = time.time,
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
    get = requests_get or requests.get
    headers = {
        "User-Agent": "LaylayAssistant/2.5 (pesquisa contextual pessoal; contato local)",
        "Accept": "application/json",
    }

    def http_get(url: str, **kwargs):
        try:
            return get(url, headers=headers, **kwargs)
        except TypeError:
            # Mantem compatibilidade com callbacks de teste ou adaptadores
            # antigos que ainda nao aceitam o argumento headers.
            return get(url, **kwargs)
    chave = normalizar(consulta)
    agora = float(clock())
    try:
        item_cache = dict(cache_ref.get(chave) or {})
    except Exception:
        item_cache = {}
    ttl_cache = float(item_cache.get("ttl_s") or ttl_s) if item_cache else ttl_s
    if item_cache and (agora - float(item_cache.get("ts") or 0.0)) < ttl_cache:
        encontrado = dict(item_cache.get("data") or {})
        encontrado["evidencia_cache"] = True
        encontrado["evidencia_idade_s"] = max(
            0.0, agora - float(encontrado.get("evidencia_obtida_em") or item_cache.get("ts") or agora)
        )
        return encontrado

    def cachear(data: dict, *, ttl_item_s: float | None = None) -> dict:
        validade = max(0.0, float(ttl_item_s if ttl_item_s is not None else ttl_s))
        registrado = dict(data or {})
        registrado.update({
            "evidencia_obtida_em": agora,
            "evidencia_obtida_em_iso": datetime.fromtimestamp(agora, timezone.utc).isoformat(),
            "evidencia_validade_s": validade,
            "evidencia_expira_em": agora + validade,
            "evidencia_expira_em_iso": datetime.fromtimestamp(agora + validade, timezone.utc).isoformat(),
            "evidencia_idade_s": 0.0,
            "evidencia_cache": False,
        })
        cache_ref[chave] = {
            "ts": agora,
            "ttl_s": validade,
            "data": registrado,
        }
        if len(cache_ref) > 80:
            antigos = list(cache_ref.keys())[:-50]
            for chave_antiga in antigos:
                cache_ref.pop(chave_antiga, None)
        return dict(registrado)

    try:
        for lang in ("pt", "en"):
            try:
                api = f"https://{lang}.wikipedia.org/w/api.php"
                # Títulos de obras em inglês costumam funcionar melhor por
                # consulta direta do que pela busca textual da Wikipedia.
                r_direto = http_get(
                    api,
                    params={
                        "action": "query",
                        "format": "json",
                        "prop": "extracts",
                        "exintro": 1,
                        "explaintext": 1,
                        "redirects": 1,
                        "titles": consulta,
                        "utf8": 1,
                    },
                    timeout=4,
                )
                r_direto.raise_for_status()
                paginas_diretas = ((r_direto.json().get("query") or {}).get("pages") or {})
                for _, pagina in paginas_diretas.items():
                    if not isinstance(pagina, dict) or "missing" in pagina:
                        continue
                    resumo_direto = re.sub(r"\s+", " ", str(pagina.get("extract") or "")).strip()
                    titulo_direto = str(pagina.get("title") or consulta).strip()
                    if resumo_direto:
                        print(f"🔎 [PESQUISA TEMA] {consulta!r} encontrado em wikipedia_{lang} por título")
                        return cachear({
                            "ok": True,
                            "tema": bruto,
                            "consulta": consulta,
                            "titulo": titulo_direto,
                            "resumo": resumo_direto[:700],
                            "fonte": f"wikipedia_{lang}",
                            "confianca": 0.95,
                        })
                r = http_get(
                    api,
                    params={
                        "action": "query",
                        "format": "json",
                        "list": "search",
                        "srsearch": consulta,
                        "srlimit": 5,
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
                r2 = http_get(
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
                        print(f"🔎 [PESQUISA TEMA] {consulta!r} encontrado em wikipedia_{lang} por busca")
                        return cachear({
                            "ok": True,
                            "tema": bruto,
                            "consulta": consulta,
                            "titulo": titulo,
                            "resumo": resumo[:420],
                            "fonte": f"wikipedia_{lang}",
                            "confianca": min(0.98, 0.45 + (score_hit / 140.0)),
                        })
            except Exception as erro_wiki:
                print(f"⚠️ [PESQUISA TEMA] wikipedia_{lang} falhou: {erro_wiki}")
                continue

        try:
            r = http_get(
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
            resumo = str(data.get("AbstractText") or data.get("Abstract") or "").strip()
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
                    return cachear(
                        {"ok": False, "tema": bruto, "consulta": consulta, "motivo": "resultado_fraco"},
                        ttl_item_s=30.0,
                    )
                print(f"🔎 [PESQUISA TEMA] {consulta!r} encontrado no duckduckgo")
                return cachear({
                    "ok": True,
                    "tema": bruto,
                    "consulta": consulta,
                    "titulo": titulo,
                    "resumo": resumo[:420],
                    "fonte": "duckduckgo",
                    "confianca": min(0.9, 0.4 + (score_ddg / 140.0)),
                })
        except Exception as erro_ddg:
            print(f"⚠️ [PESQUISA TEMA] duckduckgo falhou: {erro_ddg}")
    except Exception as e:
        print(f"⚠️ [PESQUISA TEMA] falha geral em '{consulta}': {e}")

    print(f"⚠️ [PESQUISA TEMA] nenhum contexto confiável para {consulta!r}")
    return cachear(
        {"ok": False, "tema": bruto, "consulta": consulta},
        ttl_item_s=30.0,
    )


def pesquisar_recomendacoes_tema(
    tema: str,
    ttl_s: float = 1800.0,
    *,
    cache: dict | None = None,
    requests_get=None,
    clock: Callable[[], float] = time.time,
) -> dict:
    """Obtém candidatos reais para recomendações de filmes por gênero.

    A LLM escolhe e comenta, mas os títulos permitidos vêm de uma fonte
    externa observada no turno. Outros tipos de obra continuam no pesquisador
    factual genérico até possuírem uma fonte especializada equivalente.
    """
    bruto = re.sub(r"\s+", " ", str(tema or "")).strip()
    achado = re.fullmatch(
        r"filme\s+de\s+(?P<genero>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ -]{1,48})",
        bruto,
        flags=re.IGNORECASE,
    )
    if not achado:
        return {
            "ok": False,
            "tema": bruto,
            "motivo": "tipo_recomendacao_sem_fonte_especializada",
        }

    genero = re.sub(r"\s+", " ", achado.group("genero")).strip(" -")
    chave = "recomendacao:" + _normalizar_texto_curto_basico(bruto)
    cache_ref = cache if isinstance(cache, dict) else {}
    agora = float(clock())
    item_cache = dict(cache_ref.get(chave) or {})
    if item_cache and agora - float(item_cache.get("ts") or 0.0) < float(
        item_cache.get("ttl_s") or ttl_s
    ):
        encontrado = dict(item_cache.get("data") or {})
        encontrado["evidencia_cache"] = True
        return encontrado

    get = requests_get or requests.get
    slug = "Filmes_de_" + genero.replace(" ", "_")
    url = "https://pt.wikipedia.org/wiki/" + urllib.parse.quote(
        slug,
        safe="_:()-",
    )
    headers = {
        "User-Agent": "LaylayAssistant/2.5 (pesquisa contextual pessoal; contato local)",
        "Accept": "text/html",
    }
    try:
        try:
            resposta = get(url, headers=headers, timeout=4)
        except TypeError:
            resposta = get(url, timeout=4)
        resposta.raise_for_status()
        corpo = str(getattr(resposta, "text", "") or "")
    except Exception:
        return {
            "ok": False,
            "tema": bruto,
            "consulta": slug.replace("_", " "),
            "motivo": "fonte_recomendacao_indisponivel",
        }

    candidatos: list[str] = []
    for lista in re.findall(r"<ol\b[^>]*>(.*?)</ol>", corpo, flags=re.I | re.S):
        encontrados_lista: list[str] = []
        for href, rotulo in re.findall(
            r"<i\b[^>]*>\s*<a\b[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>",
            lista,
            flags=re.I | re.S,
        ):
            if "/wiki/" not in href or ":" in href.split("/wiki/", 1)[-1]:
                continue
            titulo = html_lib.unescape(
                re.sub(r"<[^>]+>", "", rotulo),
            ).strip()
            if 2 <= len(titulo) <= 100 and titulo not in encontrados_lista:
                encontrados_lista.append(titulo)
        if len(encontrados_lista) >= 3:
            candidatos = encontrados_lista[:8]
            break

    if not candidatos:
        return {
            "ok": False,
            "tema": bruto,
            "consulta": slug.replace("_", " "),
            "motivo": "fonte_sem_candidatos_verificaveis",
        }

    validade = max(0.0, float(ttl_s))
    resultado = {
        "ok": True,
        "tema": bruto,
        "consulta": slug.replace("_", " "),
        "titulo": f"Candidatos de {bruto}",
        "resumo": (
            f"Títulos listados pela Wikipédia para {bruto}: "
            + "; ".join(candidatos)
            + "."
        ),
        "candidatos": candidatos,
        "fonte": "wikipedia_pt",
        "confianca": 0.92,
        "evidencia_obtida_em": agora,
        "evidencia_obtida_em_iso": datetime.fromtimestamp(
            agora, timezone.utc,
        ).isoformat(),
        "evidencia_validade_s": validade,
        "evidencia_expira_em": agora + validade,
        "evidencia_expira_em_iso": datetime.fromtimestamp(
            agora + validade, timezone.utc,
        ).isoformat(),
        "evidencia_idade_s": 0.0,
        "evidencia_cache": False,
    }
    cache_ref[chave] = {"ts": agora, "ttl_s": validade, "data": resultado}
    return dict(resultado)


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
        clock: Callable[[], float] = time.time,
        orcamento_interativo_s: float = 4.0,
        thread_factory: Callable[..., object] = threading.Thread,
        log: Callable[[str], object] = print,
    ) -> None:
        self.cache_tema: dict = {}
        self.normalizar_texto_curto = normalizar_texto_curto
        self.requests_get = requests_get
        self.pasta_downloads = pasta_downloads
        self.clock = clock
        self.orcamento_interativo_s = max(0.0, float(orcamento_interativo_s))
        self.thread_factory = thread_factory
        self.log = log
        self._prefetch_lock = threading.RLock()
        self._pesquisas_em_andamento: dict[str, tuple[threading.Event, dict]] = {}

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
        consulta = normalizar_tema_pesquisa(tema)
        if not consulta or tema_pesquisa_baguncado(consulta):
            return self._pesquisar_contexto_tema_direto(tema, ttl_s)

        encontrado = self.obter_contexto_cache(tema, ttl_s=ttl_s)
        if encontrado:
            return encontrado

        evento, recipiente, _criada = self._iniciar_pesquisa(tema, ttl_s)
        if evento is None:
            return {"ok": False, "tema": str(tema or ""), "consulta": consulta}
        if evento.wait(timeout=self.orcamento_interativo_s):
            return dict(recipiente.get("resultado") or {
                "ok": False,
                "tema": str(tema or ""),
                "consulta": consulta,
            })

        self.log(
            f"⚡ [PESQUISA TEMA] limite de {self.orcamento_interativo_s:.1f}s atingido; "
            "continuando em segundo plano."
        )
        return {
            "ok": False,
            "tema": str(tema or ""),
            "consulta": consulta,
            "motivo": "pesquisa_em_background",
            "pesquisa_pendente": True,
        }

    def pesquisar_recomendacoes_tema(
        self,
        tema: str,
        ttl_s: float = 1800.0,
    ) -> dict:
        return pesquisar_recomendacoes_tema(
            tema,
            ttl_s=ttl_s,
            cache=self.cache_tema,
            requests_get=self.requests_get,
            clock=self.clock,
        )

    def _pesquisar_contexto_tema_direto(self, tema: str, ttl_s: float) -> dict:
        return pesquisar_contexto_tema(
            tema,
            ttl_s=ttl_s,
            cache=self.cache_tema,
            normalizar_texto_curto=self.normalizar_texto_curto,
            requests_get=self.requests_get,
            clock=self.clock,
        )

    def _iniciar_pesquisa(
        self,
        tema: str,
        ttl_s: float,
    ) -> tuple[threading.Event | None, dict, bool]:
        consulta = normalizar_tema_pesquisa(tema)
        normalizar = self.normalizar_texto_curto or _normalizar_texto_curto_basico
        chave = normalizar(consulta)
        if not chave:
            return None, {}, False

        with self._prefetch_lock:
            existente = self._pesquisas_em_andamento.get(chave)
            if existente is not None:
                return existente[0], existente[1], False
            evento = threading.Event()
            recipiente: dict = {}
            self._pesquisas_em_andamento[chave] = (evento, recipiente)

        def executar() -> None:
            try:
                recipiente["resultado"] = self._pesquisar_contexto_tema_direto(tema, ttl_s)
            except Exception as erro:
                recipiente["resultado"] = {
                    "ok": False,
                    "tema": str(tema or ""),
                    "consulta": consulta,
                    "motivo": "erro_pesquisa",
                }
                self.log(f"⚠️ [PESQUISA TEMA] falha em segundo plano: {erro}")
            finally:
                evento.set()
                with self._prefetch_lock:
                    atual = self._pesquisas_em_andamento.get(chave)
                    if atual is not None and atual[0] is evento:
                        self._pesquisas_em_andamento.pop(chave, None)

        try:
            thread = self.thread_factory(
                target=executar,
                name=f"laylay-pesquisa-{chave[:24]}",
                daemon=True,
            )
            thread.start()
        except Exception:
            with self._prefetch_lock:
                self._pesquisas_em_andamento.pop(chave, None)
            raise
        return evento, recipiente, True

    def obter_contexto_cache(self, tema: str, ttl_s: float = 1800.0) -> dict:
        """Lê somente evidência ainda válida, sem bloquear em rede."""
        consulta = normalizar_tema_pesquisa(tema)
        normalizar = self.normalizar_texto_curto or _normalizar_texto_curto_basico
        chave = normalizar(consulta)
        try:
            item = dict(self.cache_tema.get(chave) or {})
            agora = float(self.clock())
            validade = float(item.get("ttl_s") or ttl_s)
            if not item or agora - float(item.get("ts") or 0.0) >= validade:
                return {}
            dados = dict(item.get("data") or {})
            dados["evidencia_cache"] = True
            dados["evidencia_idade_s"] = max(
                0.0,
                agora - float(dados.get("evidencia_obtida_em") or item.get("ts") or agora),
            )
            return dados
        except Exception:
            return {}

    def precarregar_contexto_tema(self, tema: str, ttl_s: float = 1800.0) -> bool:
        """Atualiza o cache em segundo plano para falas que não exigem fonte agora."""
        consulta = normalizar_tema_pesquisa(tema)
        normalizar = self.normalizar_texto_curto or _normalizar_texto_curto_basico
        chave = normalizar(consulta)
        if not chave or self.obter_contexto_cache(tema, ttl_s=ttl_s):
            return False
        _evento, _recipiente, criada = self._iniciar_pesquisa(tema, ttl_s)
        return criada

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
    clock: Callable[[], float] = time.time,
    orcamento_interativo_s: float = 4.0,
    thread_factory: Callable[..., object] = threading.Thread,
    log: Callable[[str], object] = print,
) -> PesquisaContextualRuntime:
    return PesquisaContextualRuntime(
        normalizar_texto_curto=normalizar_texto_curto,
        requests_get=requests_get,
        pasta_downloads=pasta_downloads,
        clock=clock,
        orcamento_interativo_s=orcamento_interativo_s,
        thread_factory=thread_factory,
        log=log,
    )
