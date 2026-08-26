"""Memoria e utilidades de playlists da Laylay."""

from __future__ import annotations

import difflib
import json
import os
import re
import tempfile
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse
import urllib.parse

from mente_laylay.cognicao.normalizacao_linguagem import (
    normalizar_texto,
)

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
        atual = str(ultima_playlist or "").strip()
        return resolver_nome_playlist_contextual(atual, data) if atual else ""
    candidatos = []
    for chave in data.keys():
        chave_nm = limpar_nome_playlist(normalizar_texto(str(chave or "")))
        if not chave_nm:
            continue
        if chave_nm == nm or chave_nm.startswith(nm) or nm.startswith(chave_nm):
            candidatos.append(str(chave))
    candidatos = list(dict.fromkeys(candidatos))
    if len(candidatos) == 1:
        return candidatos[0]
    if len(nm) < 4:
        return ""
    return nm


def playlist_nome_explicito_na_frase(
    texto: str,
    normalizar_texto_cb: Callable[[str], str] | None = None,
) -> bool:
    normalizar = normalizar_texto_cb if callable(normalizar_texto_cb) else normalizar_texto
    t = normalizar(str(texto or "").strip())
    if not t or "playlist" not in t:
        return False
    m = re.search(r"\bplaylist\b\s+(.+)$", t, flags=re.IGNORECASE)
    if not m:
        return False
    resto = str(m.group(1) or "").strip()
    resto = re.sub(r"^(chamada|com nome|de nome)\s+", "", resto, flags=re.IGNORECASE)
    resto = re.sub(
        r"^(e\s+)?(coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add|toca|toque|abre|abra|cria|criar|crie|apaga|apagar|limpa|limpar|remove|remover|retira|retirar)\b.*$",
        "",
        resto,
        flags=re.IGNORECASE,
    )
    resto = resto.strip(" .,!?:;")
    return bool(resto)


def extrair_nome_playlist(
    texto: str,
    *,
    normalizar_texto_cb: Callable[[str], str] | None = None,
) -> str:
    normalizar = normalizar_texto_cb if callable(normalizar_texto_cb) else normalizar_texto
    t = normalizar(str(texto or "").strip())
    padroes = [
        r"(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add).{0,80}?(?:na|nessa|nesta|para a|pra|em)\s+playlist\s+(?P<nome>.+)$",
        r"(?:na|para|a)\s+playlist\s+(?P<nome>.+?)(?:\s+(?:e\s+)?(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add|toca|toque|abre|abra|cria|criar|crie|apaga|apagar|limpa|limpar|remove|remover|retira|retirar)\b.*|$)",
        r"playlist\s+(?:chamada|com nome)?\s*(?P<nome>.+?)(?:\s+(?:e\s+)?(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add|toca|toque|abre|abra|cria|criar|crie|apaga|apagar|limpa|limpar|remove|remover|retira|retirar)\b.*|$)",
    ]
    nome = ""
    for padrao in padroes:
        match = re.search(padrao, t, flags=re.IGNORECASE)
        if match:
            nome = match.group("nome")
            break
    return limpar_nome_playlist(nome)


def detectar_playlist_nome_direto(
    texto: str,
    data: Dict[str, Any] | None,
    *,
    normalizar_texto_cb: Callable[[str], str] | None = None,
) -> str:
    normalizar = normalizar_texto_cb if callable(normalizar_texto_cb) else normalizar_texto
    t = normalizar(str(texto or "").strip())
    if not t:
        return ""

    data = data if isinstance(data, dict) else {}
    resto = t
    for gatilho in [
        "coloca",
        "coloque",
        "toca",
        "toque",
        "abre",
        "abra",
        "sintoniza",
        "sintonize",
        "manda",
        "manda tocar",
    ]:
        if resto.startswith(gatilho + " "):
            resto = resto[len(gatilho):].strip()
            break

    resto = re.sub(
        r"^(a|o|as|os|um|uma|essa|esse|essa musica|essa música|essa playlist|esse som)\s+",
        "",
        resto,
    ).strip()
    resto = limpar_nome_playlist(resto)
    if not resto:
        return ""
    if resto in data:
        return resto

    candidatos = []
    for chave in data.keys():
        chave_nm = limpar_nome_playlist(normalizar(str(chave or "")))
        if not chave_nm:
            continue
        if resto == chave_nm:
            candidatos.append(str(chave))
            continue

        # Um nome salvo pode vir seguido apenas de uma moldura operacional.
        # Palavras descritivas pertencem ao pedido musical: se existe a
        # playlist "rock", "rock pesado" deve procurar o gênero completo, não
        # truncar silenciosamente o modificador e abrir a playlist.
        if resto.startswith(chave_nm + " "):
            sufixo = resto[len(chave_nm):].strip()
            sufixo = re.sub(r"\s+", " ", sufixo)
            if re.fullmatch(
                r"(?:agora|por favor|ai|aí|pra tocar|para tocar|"
                r"agora por favor|por favor agora)",
                sufixo,
            ):
                candidatos.append(str(chave))
                continue

        # Abreviação só é segura quando Pedro disse explicitamente
        # "playlist"; sem isso, uma palavra curta também pode ser gênero,
        # artista ou começo de um título.
        if "playlist" in t and chave_nm.startswith(resto):
            candidatos.append(str(chave))
    candidatos = list(dict.fromkeys(candidatos))
    return candidatos[0] if len(candidatos) == 1 else ""


def playlists_save(caminho: str, data: dict) -> bool:
    temporario = ""
    try:
        pasta = os.path.dirname(os.path.abspath(caminho))
        os.makedirs(pasta, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=pasta,
            prefix=".playlists-", suffix=".tmp", delete=False,
        ) as f:
            temporario = f.name
            json.dump(data or {}, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporario, caminho)
        return True
    except Exception:
        if temporario:
            try:
                os.unlink(temporario)
            except OSError:
                pass
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
        # Falha transitória de leitura nunca deve apagar as playlists.
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


def fala_playlist_conteudo_estilosa(
    info: dict,
    fallback_nome: str = "",
    *,
    proprietario: str = "usuario",
) -> str:
    nm = str(info.get("name") or fallback_nome or "essa").strip()
    total = int(info.get("total") or 0)
    titulos = info.get("last_titles") if isinstance(info.get("last_titles"), list) else []
    nome_fala = nm.title() if nm else "essa"
    quantidade_faixas = f"{total} música" if total == 1 else f"{total} músicas"
    playlist_da_laylay = str(proprietario or "").casefold().strip() == "laylay"
    if playlist_da_laylay:
        if total <= 0:
            return f"Minha playlist {nome_fala} está vazia por enquanto."
        if not titulos:
            return (
                f"Minha playlist {nome_fala} tem {quantidade_faixas}. "
                "Não consegui puxar os nomes agora."
            )
        faixas = "; ".join(str(x) for x in titulos[:3])
        if total <= 3:
            return (
                f"Minha playlist {nome_fala} é curtinha: {quantidade_faixas}. "
                f"As faixas que eu separei são: {faixas}."
            )
        return (
            f"Minha playlist {nome_fala} tem {quantidade_faixas}. "
            f"Algumas faixas que eu separei são: {faixas}."
        )
    if total <= 0:
        return f"Sua playlist de {nome_fala} tá vazia por enquanto."
    if not titulos:
        return f"Sua playlist de {nome_fala} tem {quantidade_faixas}. Não consegui puxar os nomes agora."
    ult = "; ".join(str(x) for x in titulos[:3])
    if total <= 3:
        rotulo = "A principal é" if total == 1 else "As principais são"
        return f"A playlist {nome_fala} é curtinha: {quantidade_faixas}. {rotulo} {ult}."
    return f"A playlist {nome_fala} tem {quantidade_faixas}. As últimas que você guardou foram: {ult}."


def playlist_item_label(item: Any) -> str:
    if isinstance(item, dict):
        return yt_clean_title(str(item.get("titulo") or "")) or str(item.get("url") or "essa musica")
    return str(item or "essa musica")


def playlist_item_match(
    item: Any,
    musica: str,
    *,
    normalizar_texto_cb: Callable[[str], str] | None = None,
) -> bool:
    normalizar = normalizar_texto_cb if callable(normalizar_texto_cb) else normalizar_texto
    alvo = normalizar(str(musica or ""))
    if not alvo or alvo in {"ela", "essa", "isso", "musica", "música"}:
        return False
    if isinstance(item, dict):
        titulo = normalizar(str(item.get("titulo") or ""))
        url = normalizar(str(item.get("url") or ""))
        return alvo in titulo or alvo in url
    return alvo in normalizar(str(item or ""))


def pedido_lista_geral_playlist(
    texto_original: str,
    params: Dict[str, Any] | None,
    *,
    normalizar_texto_cb: Callable[[str], str] | None = None,
) -> bool:
    normalizar = normalizar_texto_cb if callable(normalizar_texto_cb) else normalizar_texto
    texto = normalizar(str(texto_original or ""))
    if any(kw in texto for kw in [
        "quais sao minhas playlists",
        "quais são minhas playlists",
        "quais minhas playlists",
        "quais as minhas playlists",
        "quais playlists eu tenho",
        "que playlists eu tenho",
        "listar minhas playlists",
        "lista minhas playlists",
        "mostra minhas playlists",
        "mostra as playlists",
        "quais sao as minhas playlists",
        "quais são as minhas playlists",
    ]):
        return True
    # Concordância imperfeita e ditado por voz não devem empurrar uma
    # consulta objetiva do inventário para a LLM. A correção fica restrita à
    # estrutura inequívoca "quais + minhas + playlist(s)".
    if re.fullmatch(
        r"quais\s+(?:(?:sao|são|e|é)\s+)?(?:as?\s+)?minhas?\s+playlists?",
        texto,
        flags=re.IGNORECASE,
    ):
        return True

    params = params if isinstance(params, dict) else {}
    raw = str(
        params.get("nome_playlist")
        or params.get("playlist")
        or params.get("nome")
        or ""
    ).strip()
    if not raw:
        return False

    if any(sep in raw for sep in [",", ";", "|", "/"]):
        return True

    raw_norm = limpar_nome_playlist(raw)
    return raw_norm in {"minhas playlists", "minha playlist", "playlist", "playlists"}


def listar_playlists_salvas(data: Dict[str, Any] | None) -> str:
    data = data if isinstance(data, dict) else {}
    nomes = []
    for chave, itens in sorted(data.items(), key=lambda kv: str(kv[0]).lower()):
        nome = str(chave or "").strip()
        if not nome:
            continue
        total = len(itens) if isinstance(itens, list) else 0
        nomes.append(f"{nome} ({total})")
    if not nomes:
        return "Você ainda não tem nenhuma playlist salva."
    if len(nomes) == 1:
        return f"Sua playlist salva é {nomes[0]}."
    return f"Suas playlists são: {', '.join(nomes)}."
