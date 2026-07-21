"""Busca e curadoria leve de resultados musicais do YouTube."""

from __future__ import annotations

import html as _html
import re
from typing import Any, Callable


TERMOS_NAO_MUSICA = (
    "familia da pesada", "família da pesada", "family guy", "episodio", "episódio",
    "temporada", "desenho", "cartoon", "trailer", "react", "reaction", "review",
    "podcast", "entrevista", "meme", "cena completa", "melhores momentos", "gameplay",
)


def _duracao_em_segundos(texto: str) -> int | None:
    partes = str(texto or "").strip().split(":")
    if len(partes) not in {2, 3} or not all(parte.isdigit() for parte in partes):
        return None
    valores = [int(parte) for parte in partes]
    if len(valores) == 2:
        return valores[0] * 60 + valores[1]
    return valores[0] * 3600 + valores[1] * 60 + valores[2]


def normalizar_query_musical(texto: str, normalizar_texto_cb: Callable[[str], str] | None = None) -> str:
    bruto = str(texto or "").strip()
    if not bruto:
        return ""
    bruto = re.sub(r"^\s*\(\s*\d+\s*\)\s*", "", bruto).strip()
    bruto = re.sub(r"^\s*\d+\s*[-–:]\s*", "", bruto).strip()

    if callable(normalizar_texto_cb):
        try:
            t = str(normalizar_texto_cb(bruto) or "").strip()
        except Exception:
            t = bruto.lower()
    else:
        t = bruto.lower()

    t = re.sub(r"\b(laylay|lay|por favor|pfv|pra mim|para mim)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return ""

    t = re.sub(
        r"^(?:quero\s+ouvir|quero\s+tocar|toca|toque|coloca|coloque|abre|abrir|pode\s+abrir|bota|poe|põe|me\s+mostra|me\s+deixa\s+ouvir)\s+",
        "",
        t,
    )
    t = re.sub(r"^(?:a|o|as|os|uma|um|essa|esse|essa\s+mesma)\s+", "", t)
    t = re.sub(r"\b(música|musica|song|faixa|track)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return ""

    m = re.search(r"^(.+?)\s+(?:da|do|de|dos|das|by)\s+(.+)$", t)
    if m:
        musica = m.group(1).strip()
        artista = m.group(2).strip()
        if musica and artista:
            return f"{musica} {artista}".strip()

    return t


def pontuar_resultado_youtube(
    query: str,
    titulo: str,
    canal: str = "",
    *,
    normalizar_texto_cb: Callable[[str], str] | None = None,
) -> int:
    q = normalizar_query_musical(query or "", normalizar_texto_cb)
    t = normalizar_query_musical(titulo or "", normalizar_texto_cb)
    c = normalizar_query_musical(canal or "", normalizar_texto_cb)
    if not q or not t:
        return 0

    q_tokens = [tok for tok in q.split() if len(tok) > 1]
    t_tokens = [tok for tok in t.split() if len(tok) > 1]
    c_tokens = [tok for tok in c.split() if len(tok) > 1]

    score = 0
    if any(termo in t for termo in TERMOS_NAO_MUSICA):
        return -500
    if q == t:
        score += 120
    if q in t or t in q:
        score += 70

    for tok in q_tokens:
        if tok in t:
            score += 10
        if tok in c:
            score += 4

    termos_combo = [
        "album", "álbum", "full album", "playlist", "mix", "compilation", "coletanea",
        "coletânea", "varias musicas", "várias músicas", "varias músicas", "top ",
        "best of", "as melhores", "melhores musicas", "melhores músicas", "setlist",
        "1 hora", "1h", "2 horas", "2h", "completo", "completa",
    ]
    if any(x in t for x in termos_combo):
        score -= 90

    if any(x in t for x in ["ao vivo", "live", "lyrics", "lyric", "8d", "sped up", "slowed", "remix"]):
        score -= 4
    if any(x in q for x in ["ao vivo", "live"]) and any(x in t for x in ["ao vivo", "live"]):
        score += 12
    if any(x in q for x in ["lyrics", "letra", "lyric"]):
        if any(x in t for x in ["lyrics", "letra", "lyric"]):
            score += 14
    if any(x in q for x in ["official", "oficial", "video"]):
        if any(x in t for x in ["official", "oficial", "video"]):
            score += 10

    if c_tokens and any(tok in q for tok in c_tokens[:3]):
        score += 6

    return score


def resultado_youtube_parece_faixa_unica(
    titulo: str,
    canal: str = "",
    *,
    normalizar_texto_cb: Callable[[str], str] | None = None,
) -> bool:
    del canal
    t = normalizar_query_musical(titulo or "", normalizar_texto_cb)
    if not t:
        return False
    if any(termo in t for termo in TERMOS_NAO_MUSICA):
        return False
    termos_combo = [
        "album", "álbum", "full album", "playlist", "mix", "compilation", "coletanea",
        "coletânea", "varias musicas", "várias músicas", "top ", "best of",
        "as melhores", "melhores musicas", "melhores músicas", "setlist",
        "1 hora", "1h", "2 horas", "2h", "completo", "completa",
    ]
    if any(x in t for x in termos_combo):
        return False

    titulo_bruto = str(titulo or "")
    if any(sep in titulo_bruto for sep in [" - ", "|", ":", "(", ")"]):
        return True
    return 3 <= len(t.split()) <= 8


def extrair_resultados_youtube_busca(
    html_text: str,
    query: str,
    limite: int = 10,
    *,
    normalizar_texto_cb: Callable[[str], str] | None = None,
) -> list[dict[str, Any]]:
    html_text = str(html_text or "")
    if not html_text:
        return []

    vistos = set()
    candidatos = []
    padrao = re.compile(r'"videoId":"([a-zA-Z0-9_-]{11})"', re.DOTALL)
    for match in padrao.finditer(html_text):
        video_id = match.group(1)
        if not video_id or video_id in vistos:
            continue
        vistos.add(video_id)
        snippet = html_text[match.start(): match.start() + 3500]
        titulo = ""
        canal = ""
        m_titulo = re.search(r'"title":\{"runs":\[\{"text":"([^"]+)"\}\]\}', snippet, re.DOTALL)
        if m_titulo:
            titulo = _html.unescape(m_titulo.group(1))
        else:
            m_titulo = re.search(r'"title":\{"simpleText":"([^"]+)"\}', snippet, re.DOTALL)
            if m_titulo:
                titulo = _html.unescape(m_titulo.group(1))

        m_canal = re.search(r'"longBylineText":\{"runs":\[\{"text":"([^"]+)"\}\]\}', snippet, re.DOTALL)
        if not m_canal:
            m_canal = re.search(r'"ownerText":\{"runs":\[\{"text":"([^"]+)"\}\]\}', snippet, re.DOTALL)
        if m_canal:
            canal = _html.unescape(m_canal.group(1))

        duracao_texto = ""
        m_duracao = re.search(
            r'"lengthText":\{.*?"simpleText":"(\d{1,2}:\d{2}(?::\d{2})?)"',
            snippet,
            re.DOTALL,
        )
        if m_duracao:
            duracao_texto = m_duracao.group(1)
        duracao_segundos = _duracao_em_segundos(duracao_texto)

        if not titulo:
            continue

        if not resultado_youtube_parece_faixa_unica(titulo, canal, normalizar_texto_cb=normalizar_texto_cb):
            continue
        if duracao_segundos is not None and duracao_segundos > 12 * 60:
            continue
        score = pontuar_resultado_youtube(query, titulo, canal, normalizar_texto_cb=normalizar_texto_cb)
        if score < 15:
            continue
        candidatos.append({
            "video_id": video_id,
            "title": titulo,
            "channel": canal,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "score": score,
            "duration": duracao_texto,
        })
        if len(candidatos) >= max(limite * 3, 20):
            break

    if not candidatos:
        return []

    candidatos.sort(key=lambda x: (-int(x.get("score") or 0), len(str(x.get("title") or ""))))
    return candidatos[:limite]
