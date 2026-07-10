"""Organizacao musical da Laylay: playlists proprias e copia de faixas."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional


_STOPWORDS = {
    "official", "video", "audio", "lyrics", "lyric", "feat", "ft", "music", "musica",
    "música", "clipe", "oficial", "live", "ao", "vivo", "tema", "version", "versao",
    "versão", "remix", "slowed", "sped", "up", "nightcore", "amv",
}


def _sem_acentos(texto: str) -> str:
    bruto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(ch for ch in bruto if not unicodedata.combining(ch))


def _normalizar(texto: str) -> str:
    t = _sem_acentos(str(texto or "").lower())
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _limpar_texto_musical(texto: str) -> str:
    t = str(texto or "").strip()
    t = re.sub(r"^\s*\(\s*\d+\s*\)\s*", "", t).strip()
    t = re.sub(r"^\s*\d+\s*[-–:]\s*", "", t).strip()
    return re.sub(r"\s+", " ", t).strip()


def _limpar_nome_artista(artista: str) -> str:
    bruto = _limpar_texto_musical(artista)
    partes = bruto.split()
    if len(partes) >= 2:
        normalizadas = [_normalizar(p) for p in partes if _normalizar(p)]
        if normalizadas and len(set(normalizadas)) == 1:
            return partes[0]
    return bruto


def _titulo_limpo(item: Any) -> str:
    if isinstance(item, dict):
        return _limpar_texto_musical(str(item.get("titulo") or "").strip())
    return _limpar_texto_musical(str(item or "").strip())


def _url_item(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("url") or "").strip()
    return ""


def _canal_item(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("canal") or "").strip()
    return ""


def _extrair_artista(titulo: str, canal: str = "") -> str:
    t = _limpar_texto_musical(titulo)
    if " - " in t:
        artista = t.split(" - ", 1)[0].strip()
        if len(artista) >= 2:
            return _limpar_nome_artista(artista)
    if canal:
        return _limpar_nome_artista(str(canal or "").strip())
    return ""


def _tokens_relevantes(*textos: str) -> List[str]:
    tokens: List[str] = []
    for texto in textos:
        for tok in _normalizar(texto).split():
            if len(tok) < 3 or tok in _STOPWORDS or tok.isdigit():
                continue
            tokens.append(tok)
    return tokens


def _todos_itens(playlists_usuario: Dict[str, Any]) -> List[dict]:
    itens: List[dict] = []
    if not isinstance(playlists_usuario, dict):
        return itens
    for nome, lst in playlists_usuario.items():
        if not isinstance(lst, list):
            continue
        for item in lst:
            if isinstance(item, dict):
                novo = dict(item)
                novo["_playlist_origem"] = str(nome or "").strip()
                itens.append(novo)
    return itens


def sincronizar_playlists_da_laylay(
    playlists_usuario: Dict[str, Any],
    historico_musical: Dict[str, Any],
    existentes: Optional[Dict[str, Any]] = None,
    *,
    max_faixas: int = 20,
) -> Dict[str, Any]:
    atuais = dict(existentes or {}) if isinstance(existentes, dict) else {}
    itens = _todos_itens(playlists_usuario)
    if not itens:
        return atuais

    por_titulo = Counter()
    por_artista = Counter()
    por_playlist = Counter()
    melhores_por_titulo: Dict[str, dict] = {}
    for item in itens:
        titulo = _titulo_limpo(item)
        titulo_norm = _normalizar(titulo)
        if not titulo_norm:
            continue
        por_titulo[titulo_norm] += 1
        por_playlist[str(item.get("_playlist_origem") or "").strip()] += 1
        artista = _extrair_artista(titulo, _canal_item(item))
        if artista:
            por_artista[artista] += 1
        if titulo_norm not in melhores_por_titulo and _url_item(item):
            melhores_por_titulo[titulo_norm] = {
                "url": _url_item(item),
                "titulo": titulo,
                "canal": _canal_item(item),
                "data": str(item.get("data") or datetime.now().date().isoformat()),
                "motivo": "curadoria_laylay",
            }

    xodos: List[dict] = []
    for titulo_norm, _ in por_titulo.most_common(max_faixas):
        item = melhores_por_titulo.get(titulo_norm)
        if item:
            xodos.append(dict(item))

    climas: List[dict] = []
    playlists_prioritarias = [nome for nome, _ in por_playlist.most_common(3)]
    vistos = set()
    for nome in playlists_prioritarias:
        lst = playlists_usuario.get(nome)
        if not isinstance(lst, list):
            continue
        for item in lst:
            if not isinstance(item, dict):
                continue
            url = _url_item(item)
            if not url or url in vistos:
                continue
            vistos.add(url)
            climas.append({
                "url": url,
                "titulo": _titulo_limpo(item),
                "canal": _canal_item(item),
                "data": str(item.get("data") or datetime.now().date().isoformat()),
                "motivo": f"clima_{_normalizar(nome)}",
            })
            if len(climas) >= max_faixas:
                break
        if len(climas) >= max_faixas:
            break

    atuais["xodos_que_eu_seperei"] = xodos[:max_faixas]
    atuais["climas_que_combinam_com_voce"] = climas[:max_faixas]
    atuais.setdefault("descobertas_da_laylay", [])
    return atuais


def encontrar_faixa_playlist(playlists_laylay: Dict[str, Any], nome_playlist: str, musica: str) -> Optional[dict]:
    if not isinstance(playlists_laylay, dict):
        return None
    nome_norm = _normalizar(nome_playlist)
    musica_norm = _normalizar(musica)
    if not nome_norm or not musica_norm:
        return None
    alvo = None
    for chave, lst in playlists_laylay.items():
        chave_norm = _normalizar(chave)
        if chave_norm == nome_norm or chave_norm.startswith(nome_norm) or nome_norm.startswith(chave_norm):
            alvo = lst
            break
    if not isinstance(alvo, list):
        return None
    for item in alvo:
        if not isinstance(item, dict):
            continue
        titulo_norm = _normalizar(_titulo_limpo(item))
        if musica_norm in titulo_norm or titulo_norm in musica_norm:
            return dict(item)
    return None
