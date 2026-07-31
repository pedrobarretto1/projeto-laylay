"""Organizacao musical da Laylay: playlists proprias e copia de faixas."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional


def _sem_acentos(texto: str) -> str:
    bruto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(ch for ch in bruto if not unicodedata.combining(ch))


def _normalizar(texto: str) -> str:
    t = _sem_acentos(str(texto or "").lower())
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _normalizar_nome_curadoria(texto: str) -> str:
    nome = _normalizar(texto)
    aliases = {
        "xodos que eu separei": "xodos que eu seperei",
        "xodos que eu seperei": "xodos que eu seperei",
        "climas que combinam comigo": "climas que combinam com voce",
        "climas que combinam com voce": "climas que combinam com voce",
    }
    return aliases.get(nome, nome)


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


def _frequencias_historico(historico_musical: Dict[str, Any]) -> Counter:
    """Consolida o histórico por título sem depender do horário da execução."""
    frequencias: Counter = Counter()
    if not isinstance(historico_musical, dict):
        return frequencias
    for bloco in historico_musical.values():
        if not isinstance(bloco, dict):
            continue
        for musica in bloco.get("musicas") or ():
            titulo = _normalizar(_limpar_texto_musical(str(musica or "")))
            if titulo:
                frequencias[titulo] += 1
    return frequencias


def _vezes_ouvida(titulo_normalizado: str, frequencias: Counter) -> int:
    if not titulo_normalizado:
        return 0
    exata = int(frequencias.get(titulo_normalizado, 0))
    if exata:
        return exata
    # O título vindo do navegador pode carregar artista, videoclipe ou sufixo
    # do YouTube. A aproximação só vale para nomes longos, evitando colisões
    # como "Love" e "Love Me".
    if len(titulo_normalizado) < 10:
        return 0
    return sum(
        int(total)
        for conhecido, total in frequencias.items()
        if len(conhecido) >= 10
        and (titulo_normalizado in conhecido or conhecido in titulo_normalizado)
    )


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

    historico_por_titulo = _frequencias_historico(historico_musical)
    por_titulo = Counter()
    por_artista = Counter()
    por_playlist = Counter()
    audicoes_por_playlist = Counter()
    melhores_por_titulo: Dict[str, dict] = {}
    ordem_por_titulo: Dict[str, int] = {}
    for ordem, item in enumerate(itens):
        titulo = _titulo_limpo(item)
        titulo_norm = _normalizar(titulo)
        if not titulo_norm:
            continue
        por_titulo[titulo_norm] += 1
        origem = str(item.get("_playlist_origem") or "").strip()
        por_playlist[origem] += 1
        audicoes_por_playlist[origem] += _vezes_ouvida(
            titulo_norm, historico_por_titulo,
        )
        artista = _extrair_artista(titulo, _canal_item(item))
        if artista:
            por_artista[artista] += 1
        if titulo_norm not in melhores_por_titulo and _url_item(item):
            ordem_por_titulo[titulo_norm] = ordem
            melhores_por_titulo[titulo_norm] = {
                "url": _url_item(item),
                "titulo": titulo,
                "canal": _canal_item(item),
                "data": str(item.get("data") or datetime.now().date().isoformat()),
                "titulo_norm": titulo_norm,
                "canal_norm": _normalizar(_canal_item(item)),
            }

    xodos: List[dict] = []
    titulos_ordenados = sorted(
        melhores_por_titulo,
        key=lambda titulo_norm: (
            -_vezes_ouvida(titulo_norm, historico_por_titulo),
            -int(por_titulo.get(titulo_norm, 0)),
            int(ordem_por_titulo.get(titulo_norm, 0)),
            titulo_norm,
        ),
    )
    for titulo_norm in titulos_ordenados[:max_faixas]:
        item = melhores_por_titulo.get(titulo_norm)
        if item:
            xodos.append(dict(item))

    climas: List[dict] = []
    playlists_prioritarias = sorted(
        por_playlist,
        key=lambda nome: (
            -int(audicoes_por_playlist.get(nome, 0)),
            -int(por_playlist.get(nome, 0)),
            _normalizar(nome),
        ),
    )[:3]
    vistos = set()
    # Rodízio entre as playlists preferidas evita que a maior delas ocupe
    # sozinha toda a curadoria de clima.
    cursores = {nome: 0 for nome in playlists_prioritarias}
    while len(climas) < max_faixas and playlists_prioritarias:
        adicionou = False
        for nome in list(playlists_prioritarias):
            lst = playlists_usuario.get(nome)
            if not isinstance(lst, list):
                playlists_prioritarias.remove(nome)
                continue
            cursor = cursores[nome]
            if cursor >= len(lst):
                playlists_prioritarias.remove(nome)
                continue
            item = lst[cursor]
            cursores[nome] = cursor + 1
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
                "titulo_norm": _normalizar(_titulo_limpo(item)),
                "canal_norm": _normalizar(_canal_item(item)),
            })
            adicionou = True
            if len(climas) >= max_faixas:
                break
        if not adicionou and not playlists_prioritarias:
            break

    atuais["xodos_que_eu_seperei"] = xodos[:max_faixas]
    atuais["climas_que_combinam_com_voce"] = climas[:max_faixas]
    atuais.setdefault("descobertas_da_laylay", [])
    return atuais


def encontrar_faixa_playlist(playlists_laylay: Dict[str, Any], nome_playlist: str, musica: str) -> Optional[dict]:
    if not isinstance(playlists_laylay, dict):
        return None
    nome_norm = _normalizar_nome_curadoria(nome_playlist)
    musica_norm = _normalizar(musica)
    if not nome_norm or not musica_norm:
        return None
    alvo = None
    for chave, lst in playlists_laylay.items():
        chave_norm = _normalizar_nome_curadoria(chave)
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
