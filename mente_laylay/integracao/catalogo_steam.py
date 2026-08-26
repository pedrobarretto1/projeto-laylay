"""Descoberta local e abertura de jogos instalados pela Steam."""

from __future__ import annotations

import os
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable


def _normalizar(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or "").casefold())
    texto = "".join(letra for letra in texto if not unicodedata.combining(letra))
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def _raizes_steam_registro() -> list[str]:
    try:
        import winreg
    except Exception:
        return []
    encontrados: list[str] = []
    chaves = (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
    )
    for hive, chave in chaves:
        try:
            with winreg.OpenKey(hive, chave) as registro:
                for campo in ("SteamPath", "InstallPath"):
                    try:
                        encontrados.append(str(winreg.QueryValueEx(registro, campo)[0]))
                    except OSError:
                        pass
        except OSError:
            pass
    return encontrados


def descobrir_raizes_steam(roots: Iterable[str] | None = None) -> list[Path]:
    if roots is not None:
        candidatos = list(roots)
    else:
        candidatos = _raizes_steam_registro()
        candidatos.extend(filter(None, (
            os.environ.get("STEAM_PATH"),
            r"C:\Program Files (x86)\Steam",
            r"C:\Program Files\Steam",
        )))
    raizes: list[Path] = []
    vistas: set[str] = set()
    for candidato in candidatos:
        raiz = Path(os.path.expandvars(str(candidato or "").replace("\\\\", "\\")))
        chave = os.path.normcase(os.path.abspath(str(raiz)))
        if chave in vistas or not raiz.is_dir():
            continue
        vistas.add(chave)
        raizes.append(raiz)

    # Cada instalação mantém no VDF os caminhos das bibliotecas adicionais.
    for raiz in list(raizes):
        arquivo = raiz / "steamapps" / "libraryfolders.vdf"
        try:
            conteudo = arquivo.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for caminho in re.findall(r'^\s*"path"\s+"([^"]+)"', conteudo, re.MULTILINE):
            biblioteca = Path(caminho.replace("\\\\", "\\"))
            chave = os.path.normcase(os.path.abspath(str(biblioteca)))
            if chave not in vistas and biblioteca.is_dir():
                vistas.add(chave)
                raizes.append(biblioteca)
    return raizes


def _campo_manifesto(conteudo: str, campo: str) -> str:
    encontrado = re.search(
        rf'^\s*"{re.escape(campo)}"\s+"([^"]*)"', conteudo, re.MULTILINE | re.IGNORECASE,
    )
    return encontrado.group(1).strip() if encontrado else ""


def listar_jogos_steam(roots: Iterable[str] | None = None) -> list[dict[str, Any]]:
    jogos: list[dict[str, Any]] = []
    appids: set[str] = set()
    for raiz in descobrir_raizes_steam(roots):
        steamapps = raiz / "steamapps"
        try:
            manifestos = tuple(steamapps.glob("appmanifest_*.acf"))
        except OSError:
            continue
        for manifesto in manifestos:
            try:
                conteudo = manifesto.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            appid = _campo_manifesto(conteudo, "appid")
            nome = _campo_manifesto(conteudo, "name")
            if not appid.isdigit() or not nome or appid in appids:
                continue
            appids.add(appid)
            pasta = _campo_manifesto(conteudo, "installdir")
            jogos.append({
                "appid": appid,
                "nome": nome,
                "nome_normalizado": _normalizar(nome),
                "pasta": str(steamapps / "common" / pasta) if pasta else "",
                "manifesto": str(manifesto),
            })
    return jogos


def resolver_jogo_steam(nome: str, roots: Iterable[str] | None = None) -> dict[str, Any] | None:
    procurado = _normalizar(nome)
    if not procurado:
        return None
    melhor: dict[str, Any] | None = None
    melhor_nota = 0.0
    for jogo in listar_jogos_steam(roots):
        candidato = str(jogo.get("nome_normalizado") or "")
        if candidato == procurado:
            nota = 1.0
        elif candidato.replace(" ", "") == procurado.replace(" ", ""):
            nota = 0.99
        else:
            similaridade = SequenceMatcher(None, procurado, candidato).ratio()
            tokens = set(procurado.split())
            cobertura = len(tokens & set(candidato.split())) / max(1, len(tokens))
            nota = (similaridade * 0.7) + (cobertura * 0.3)
        if nota > melhor_nota:
            melhor_nota = nota
            melhor = jogo
    # Permite pequenos erros de digitação, mas evita abrir outro jogo por um
    # fragmento vago como "path" ou "jogo".
    if melhor is None or melhor_nota < 0.78:
        return None
    return {**melhor, "confianca": round(melhor_nota, 3)}
