"""Memoria e utilidades de playlists da Laylay."""

from __future__ import annotations

import difflib
import json
import os
import random
import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urlparse
import urllib.parse


_CORRECOES_FONETICAS = (
    (r"\bpaly\s*list\b", "playlist"),
    (r"\bplay\s*list\b", "playlist"),
    (r"\bpalylist\b", "playlist"),
    (r"\bplalyst\b", "playlist"),
    (r"\bplalist\b", "playlist"),
    (r"\bcamaitachi\b", "kamaitachi"),
    (r"\bkamaitaxi\b", "kamaitachi"),
    (r"\bkamaytachi\b", "kamaitachi"),
    (r"\byoutub\b", "youtube"),
    (r"\butube\b", "youtube"),
    (r"\bspotifi\b", "spotify"),
)

_ORDINAL_IDX = {
    "primeira": 0, "primeiro": 0, "1ª": 0, "1º": 0,
    "segunda": 1, "segundo": 1, "2ª": 1, "2º": 1,
    "terceira": 2, "terceiro": 2, "3ª": 2, "3º": 2,
    "quarta": 3, "quarto": 3, "4ª": 3, "4º": 3,
    "quinta": 4, "quinto": 4, "5ª": 4, "5º": 4,
    "última": -1, "ultimo": -1, "último": -1, "ultima": -1,
}


def remover_acentos(s: str) -> str:
    try:
        n = unicodedata.normalize("NFKD", str(s or ""))
        return "".join(c for c in n if not unicodedata.combining(c))
    except Exception:
        return str(s or "")


def aplicar_correcao_fonetica(texto: str) -> str:
    t = str(texto or "").lower().strip()
    if not t:
        return ""
    t = re.sub(r"\s+", " ", t)
    for padrao, troca in _CORRECOES_FONETICAS:
        t = re.sub(padrao, troca, t, flags=re.IGNORECASE)
    return t


def normalizar_texto(texto: str) -> str:
    t = remover_acentos(str(texto or "").lower())
    t = aplicar_correcao_fonetica(t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def yt_clean_url(url: str) -> str:
    try:
        u = urlparse(url)
        q = urllib.parse.parse_qs(u.query)
        vid = (q.get("v") or [""])[0]
        if vid:
            return f"https://www.youtube.com/watch?v={vid}"
        return url
    except Exception:
        return url


def yt_clean_title(title: str) -> str:
    t = str(title or "").strip()
    t = re.sub(r"^\s*\(\s*\d+\s*\)\s*", "", t).strip()
    t = re.sub(r"^\s*\d+\s*[-–:]\s*", "", t).strip()
    if t.lower().endswith(" - youtube"):
        t = t[:-10].strip()
    return t


def titulo_fingerprint(titulo: str) -> str:
    t = normalizar_texto(yt_clean_title(titulo))
    for w in ["oficial", "video", "lyrics", "clipe", "hd", "4k", "audio", "áudio", "official"]:
        t = re.sub(rf"\b{re.escape(normalizar_texto(w))}\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def canal_fingerprint(canal: str) -> str:
    return normalizar_texto(canal)


def sim_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    try:
        return float(difflib.SequenceMatcher(None, a, b).ratio())
    except Exception:
        return 0.0


def limpar_nome_playlist(nome: str) -> str:
    s = str(nome or "").strip().lower()
    s = re.sub(r"^[\s\-\.,;:]+|[\s\-\.,;:]+$", "", s)
    s = re.sub(r"\bmúsica\s+de\s+", "música ", s)
    s = re.sub(r"^(chamada|chamado|chamadas|chamados|nomeada|nomeado|com nome|de nome)\s+", "", s)
    s = re.sub(r"^(de|do|da|dos|das|um|uma|o|a)\s+", "", s)
    s = re.sub(
        r"\s+(?:e\s+)?(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add|toca|toque|abre|abra|cria|criar|crie|apaga|apagar|limpa|limpar|remove|remover|retira|retirar)\b.*$",
        "",
        s,
    )
    s = re.sub(r"\s+(de|do|da|dos|das)$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    toks = s.split()
    while toks and toks[-1] in {"aleatorio", "aleatória", "aleatoria", "shuffle", "misturar", "mistura"}:
        toks = toks[:-1]
    return " ".join(toks).strip()


def resolver_nome_playlist_contextual(nome: str, data: Dict[str, Any], ultima_playlist: str = "") -> str:
    bruto = normalizar_texto(str(nome or "").strip())
    nm = limpar_nome_playlist(bruto)
    if not nm:
        return ""
    if not isinstance(data, dict):
        data = {}
    if nm in data:
        return nm
    if nm in {"ultima playlist", "ultima_playlist", "ultima_playlist_do_contexto"}:
        atual = limpar_nome_playlist(normalizar_texto(str(ultima_playlist or "")))
        return atual
    candidatos = []
    for chave in data.keys():
        chave_nm = limpar_nome_playlist(str(chave or ""))
        if not chave_nm:
            continue
        if chave_nm == nm or chave_nm.startswith(nm) or nm.startswith(chave_nm):
            candidatos.append(chave_nm)
    candidatos = list(dict.fromkeys(candidatos))
    if len(candidatos) == 1:
        return candidatos[0]
    if len(nm) < 4:
        return ""
    return nm


def playlists_save(caminho: str, data: dict) -> bool:
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(data or {}, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write("{}")
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(data or {}, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False


def ensure_playlists_file(state_file: str, legacy_file: str) -> bool:
    created = False
    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        if not os.path.exists(state_file):
            if os.path.exists(legacy_file):
                try:
                    with open(legacy_file, "r", encoding="utf-8") as src:
                        legacy = src.read()
                    with open(state_file, "w", encoding="utf-8") as dst:
                        dst.write(legacy if legacy.strip() else "{}")
                except Exception:
                    with open(state_file, "w", encoding="utf-8") as f:
                        f.write("{}")
            else:
                with open(state_file, "w", encoding="utf-8") as f:
                    f.write("{}")
            created = True
    except Exception:
        pass
    return created


def playlists_load(state_file: str, legacy_file: str) -> Dict[str, Any]:
    try:
        ensure_playlists_file(state_file, legacy_file)
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            changed = False
            today = datetime.now().date().isoformat()
            for k, v in list(data.items()):
                if not isinstance(k, str):
                    try:
                        data.pop(k, None)
                        changed = True
                    except Exception:
                        pass
                    continue
                if not isinstance(v, list):
                    data[k] = []
                    changed = True
                    continue
                new_list = []
                for it in v:
                    if isinstance(it, str):
                        u = yt_clean_url(it.strip())
                        if u:
                            new_list.append({"url": u, "titulo": "", "canal": "", "data": today, "titulo_norm": "", "canal_norm": ""})
                            changed = True
                        continue
                    if isinstance(it, dict):
                        u = yt_clean_url(str(it.get("url") or "").strip())
                        if not u:
                            changed = True
                            continue
                        titulo = str(it.get("titulo") or "").strip()
                        canal = str(it.get("canal") or "").strip()
                        titulo_norm = str(it.get("titulo_norm") or titulo_fingerprint(titulo)).strip()
                        canal_norm = str(it.get("canal_norm") or canal_fingerprint(canal)).strip()
                        new_item = {
                            "url": u,
                            "titulo": titulo,
                            "canal": canal,
                            "data": str(it.get("data") or today).strip() or today,
                            "titulo_norm": titulo_norm,
                            "canal_norm": canal_norm,
                        }
                        if (new_item.get("url") != str(it.get("url") or "").strip()) or ("canal" not in it) or ("data" not in it) or ("titulo_norm" not in it) or ("canal_norm" not in it):
                            changed = True
                        new_list.append(new_item)
                        continue
                    changed = True
                data[k] = new_list
            if changed:
                playlists_save(state_file, data)
            return data
    except Exception:
        try:
            with open(state_file, "w", encoding="utf-8") as f:
                f.write("{}")
        except Exception:
            pass
        return {}


def playlist_len(nome: str, data: Dict[str, Any]) -> int:
    nm = limpar_nome_playlist(nome)
    lst = data.get(nm)
    return len(lst) if isinstance(lst, list) else 0


def playlist_primeira_url(nome: str, data: Dict[str, Any]) -> Optional[str]:
    nm = limpar_nome_playlist(nome)
    if not nm:
        return None
    lst = data.get(nm)
    if not isinstance(lst, list) or not lst:
        return None
    first = lst[0]
    url = str(first.get("url")) if isinstance(first, dict) else str(first)
    return url.strip() if url else None


def playlist_item_at(nome: str, idx: int, data: Dict[str, Any]) -> Optional[dict]:
    nm = limpar_nome_playlist(nome)
    if not nm:
        return None
    lst = data.get(nm)
    if not isinstance(lst, list):
        return None
    if idx < 0 or idx >= len(lst):
        return None
    item = lst[idx]
    if isinstance(item, dict):
        return {
            "url": str(item.get("url") or "").strip(),
            "titulo": str(item.get("titulo") or "").strip(),
            "canal": str(item.get("canal") or "").strip(),
            "data": str(item.get("data") or "").strip(),
        }
    if isinstance(item, str):
        return {"url": item.strip(), "titulo": "", "canal": "", "data": ""}
    return None


def add_to_playlist_url(
    playlist_name: str,
    url: str,
    title: str = "",
    canal: str = "",
    *,
    state_file: str,
    legacy_file: str,
    data: Optional[Dict[str, Any]] = None,
    ultima_playlist: str = "",
) -> dict:
    name = resolver_nome_playlist_contextual(playlist_name or "", data if isinstance(data, dict) else {}, ultima_playlist)
    if not name:
        return {"ok": False, "created_file": False, "created_playlist": False, "duplicated": False, "duplicated_meta": False}
    created_file = ensure_playlists_file(state_file, legacy_file)
    link = yt_clean_url(str(url or ""))
    if "youtube.com" not in link:
        return {"ok": False, "created_file": created_file, "created_playlist": False, "duplicated": False, "duplicated_meta": False}
    if data is None:
        data = playlists_load(state_file, legacy_file)
    lst = data.get(name)
    if not isinstance(lst, list):
        lst = []
        created_playlist = True
    else:
        created_playlist = False
    today = datetime.now().date().isoformat()
    titulo = yt_clean_title(str(title or "").strip())
    canal_txt = str(canal or "").strip()
    titulo_norm = titulo_fingerprint(titulo)
    canal_norm = canal_fingerprint(canal_txt)
    item = {"url": link, "titulo": titulo, "canal": canal_txt, "data": today, "titulo_norm": titulo_norm, "canal_norm": canal_norm}
    existing_urls = set()
    for it in lst:
        if isinstance(it, str):
            existing_urls.add(it)
        elif isinstance(it, dict) and it.get("url"):
            existing_urls.add(str(it.get("url")))
    if link in existing_urls:
        return {"ok": True, "created_file": created_file, "created_playlist": created_playlist, "duplicated": True, "duplicated_meta": False}
    if titulo_norm:
        for it in lst:
            if not isinstance(it, dict):
                continue
            ex_tn = str(it.get("titulo_norm") or titulo_fingerprint(str(it.get("titulo") or ""))).strip()
            if not ex_tn:
                continue
            if sim_ratio(titulo_norm, ex_tn) >= 0.9:
                ex_cn = str(it.get("canal_norm") or canal_fingerprint(str(it.get("canal") or ""))).strip()
                other_channel = True
                if canal_norm and ex_cn and sim_ratio(canal_norm, ex_cn) >= 0.9:
                    other_channel = False
                return {"ok": True, "created_file": created_file, "created_playlist": created_playlist, "duplicated": False, "duplicated_meta": True, "duplicate_other_channel": other_channel}
    lst.append(item)
    data[name] = lst
    ok = playlists_save(state_file, data)
    return {"ok": ok, "created_file": created_file, "created_playlist": created_playlist, "duplicated": False, "duplicated_meta": False}


def list_playlist_urls(name: str, data: Dict[str, Any]) -> list:
    nm = limpar_nome_playlist(name)
    if not nm:
        return []
    lst = data.get(nm)
    if not isinstance(lst, list):
        return []
    out = []
    for item in lst:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and item.get("url"):
            out.append(str(item.get("url")))
    return out


def fala_playlist_conteudo_estilosa(info: dict, fallback_nome: str = "") -> str:
    nm = str(info.get("name") or fallback_nome or "essa").strip()
    total = int(info.get("total") or 0)
    titulos = info.get("last_titles") if isinstance(info.get("last_titles"), list) else []
    nome_fala = nm.title() if nm else "essa"
    if total <= 0:
        return f"Sua playlist de {nome_fala} tá vazia por enquanto."
    if not titulos:
        return f"Sua playlist de {nome_fala} tem {total} músicas. Não consegui puxar os nomes agora."
    ult = "; ".join(str(x) for x in titulos[:3])
    if total <= 3:
        return f"A playlist {nome_fala} é curtinha: {total} músicas. As principais são {ult}."
    return f"A playlist {nome_fala} tem {total} músicas. As últimas que você guardou foram: {ult}."


def detectar_mover_playlist_texto(texto: str):
    t = str(texto or "").strip()
    padroes = [
        r"(?:tira|remove|retira)\s+(?P<musica>.+?)\s+da\s+playlist\s+(?P<origem>.+?)\s+e\s+(?:coloca|bota|adiciona|joga)\s+(?:na|pra|para a|para)\s+playlist\s+(?P<destino>.+)",
        r"(?:move|mova|transfere|transfira)\s+(?P<musica>.+?)\s+da\s+playlist\s+(?P<origem>.+?)\s+(?:pra|para|para a)\s+playlist\s+(?P<destino>.+)",
    ]
    for padrao in padroes:
        m = re.search(padrao, t, flags=re.IGNORECASE)
        if not m:
            continue
        musica = str(m.group("musica") or "").strip(" .,!?:;")
        origem = limpar_nome_playlist(m.group("origem"))
        destino = limpar_nome_playlist(m.group("destino"))
        if origem and destino:
            return {"musica": musica, "origem": origem, "destino": destino}
    return None
