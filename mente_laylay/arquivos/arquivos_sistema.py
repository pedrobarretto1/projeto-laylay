"""Operações de arquivos e contexto de pastas da Laylay."""

from __future__ import annotations

import os
import shutil
import time
from typing import Optional

_pastas_contexto_cache = {"ts": 0.0, "texto": ""}


def verificar_trava_seguranca(caminho: str) -> bool:
    """Trava de segurança para evitar que a IA mexa em pastas críticas do Windows."""
    c = str(caminho).upper()
    bloqueados = [
        "C:\\WINDOWS",
        "C:/WINDOWS",
        "SYSTEM32",
        "PROGRAM FILES",
        "PROGRAMDATA",
        "C:\\USERS\\PUBLIC",
        "C:\\$",
    ]
    if c in {"C:\\", "C:/", "C:"}:
        return False
    for b in bloqueados:
        if b in c:
            return False
    return True


def resolver_caminho(nome_ou_caminho: str) -> str:
    """Se for apenas o nome (sem barras), converte para pasta Downloads, senão usa o caminho original."""
    nome_ou_caminho = str(nome_ou_caminho or "").strip(' "\'')
    if "\\" not in nome_ou_caminho and "/" not in nome_ou_caminho and ":" not in nome_ou_caminho:
        caminho_base = os.path.join(os.path.expanduser("~"), "Downloads")
        return os.path.join(caminho_base, nome_ou_caminho)
    return nome_ou_caminho


def criar_pasta(caminho: str) -> bool:
    caminho = resolver_caminho(caminho)
    if not verificar_trava_seguranca(caminho):
        print(f"❌ [SEGURANÇA] Acesso negado ao caminho: {caminho}")
        return False
    try:
        os.makedirs(caminho, exist_ok=True)
        print(f"📂 [ARQUIVOS] Pasta criada/verificada: {caminho}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar pasta: {e}")
        return False


def criar_ou_editar_arquivo(caminho: str, conteudo: str, modo: str = "w") -> bool:
    caminho = resolver_caminho(caminho)
    if not verificar_trava_seguranca(caminho):
        print(f"❌ [SEGURANÇA] Acesso negado ao caminho: {caminho}")
        return False
    try:
        pasta_pai = os.path.dirname(caminho)
        if pasta_pai:
            os.makedirs(pasta_pai, exist_ok=True)
        with open(caminho, modo, encoding="utf-8") as f:
            f.write(str(conteudo))
        print(f"📄 [ARQUIVOS] Arquivo {'atualizado' if modo == 'a' else 'criado'}: {caminho}")
        return True
    except Exception as e:
        print(f"❌ Erro ao manipular arquivo: {e}")
        return False


def mover_arquivo(origem: str, destino: str) -> bool:
    origem = resolver_caminho(origem)
    destino = resolver_caminho(destino)
    if not verificar_trava_seguranca(origem) or not verificar_trava_seguranca(destino):
        print(f"❌ [SEGURANÇA] Acesso negado para mover: {origem} -> {destino}")
        return False
    try:
        shutil.move(origem, destino)
        print(f"🚚 [ARQUIVOS] Movido: {origem} -> {destino}")
        return True
    except Exception as e:
        print(f"❌ Erro ao mover item: {e}")
        return False


def renomear_arquivo(caminho: str, novo_nome: str) -> bool:
    caminho = resolver_caminho(caminho)
    novo_nome = str(novo_nome or "").strip(' "\'')
    if not verificar_trava_seguranca(caminho):
        print(f"❌ [SEGURANÇA] Acesso negado ao renomear: {caminho}")
        return False
    try:
        diretorio = os.path.dirname(caminho)
        novo_caminho = os.path.join(diretorio, novo_nome)
        if not verificar_trava_seguranca(novo_caminho):
            return False
        os.rename(caminho, novo_caminho)
        print(f"✏️ [ARQUIVOS] Renomeado: {caminho} -> {novo_nome}")
        return True
    except Exception as e:
        print(f"❌ Erro ao renomear: {e}")
        return False


def deletar_item(caminho: str) -> bool:
    caminho = resolver_caminho(caminho)
    if not verificar_trava_seguranca(caminho):
        print(f"❌ [SEGURANÇA] Acesso negado ao deletar: {caminho}")
        return False
    try:
        if os.path.isfile(caminho):
            os.remove(caminho)
        elif os.path.isdir(caminho):
            shutil.rmtree(caminho)
        else:
            print(f"⚠️ [ARQUIVOS] Item não encontrado para deletar: {caminho}")
            return False
        print(f"🗑️ [ARQUIVOS] Deletado: {caminho}")
        return True
    except Exception as e:
        print(f"❌ Erro ao deletar item: {e}")
        return False


def mapear_pastas_principais() -> str:
    """Mapeia as pastas do usuário para dar contexto à IA."""
    global _pastas_contexto_cache

    agora = time.time()
    ttl_segundos = 60.0
    cache = _pastas_contexto_cache
    if cache.get("texto") and (agora - float(cache.get("ts") or 0.0)) < ttl_segundos:
        return str(cache.get("texto") or "")

    user_home = os.path.expanduser("~")
    pastas = {
        "Downloads": os.path.join(user_home, "Downloads"),
        "Desktop": os.path.join(user_home, "Desktop"),
        "Documentos": os.path.join(user_home, "Documents"),
        "Imagens": os.path.join(user_home, "Pictures"),
        "Vídeos": os.path.join(user_home, "Videos"),
    }

    contexto_arquivos = "ESTRUTURA DE PASTAS DO PEDRO:\n"
    for nome, caminho in pastas.items():
        if os.path.exists(caminho):
            try:
                itens = os.listdir(caminho)[:15]
                contexto_arquivos += f"- {nome} ({caminho}): {', '.join(itens)}\n"
            except Exception:
                contexto_arquivos += f"- {nome} ({caminho}): [Acesso negado ou erro]\n"

    _pastas_contexto_cache = {"ts": agora, "texto": contexto_arquivos}
    return contexto_arquivos


def buscar_arquivo_no_pc(nome_arquivo: str) -> Optional[str]:
    """Busca um arquivo em todo o diretório do usuário (Downloads, Desktop, etc)."""
    user_home = os.path.expanduser("~")
    print(f"🔍 [BUSCA] Procurando por '{nome_arquivo}' em {user_home}...")

    resultados = []
    pastas_busca = ["Downloads", "Desktop", "Documents", "Pictures"]

    for p in pastas_busca:
        caminho_base = os.path.join(user_home, p)
        if not os.path.exists(caminho_base):
            continue

        for root, _, files in os.walk(caminho_base):
            if not verificar_trava_seguranca(root):
                continue
            for f in files:
                if str(nome_arquivo).lower() in f.lower():
                    resultados.append(os.path.join(root, f))
                    if len(resultados) >= 3:
                        break
            if len(resultados) >= 3:
                break

    if resultados:
        print(f"✅ [BUSCA] Encontrado: {resultados[0]}")
        return resultados[0]
    return None
