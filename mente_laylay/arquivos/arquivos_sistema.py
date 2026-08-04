"""Operações de arquivos e contexto de pastas da Laylay."""

from __future__ import annotations

import os
import hashlib
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional

from mente_laylay.arquivos.lixeira_laylay import mover_para_lixeira

_pastas_contexto_cache = {"ts": 0.0, "texto": ""}


def verificar_trava_seguranca(caminho: str) -> bool:
    """Permite operações apenas dentro das pastas pessoais autorizadas."""
    try:
        alvo = Path(str(caminho or "")).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return False
    if not str(caminho or "").strip() or alvo == Path(alvo.anchor):
        return False

    home = Path.home().resolve(strict=False)
    permitidos = [home]
    extras = os.environ.get("LAYLAY_ARQUIVOS_RAIZES_PERMITIDAS", "")
    for item in extras.split(os.pathsep):
        if item.strip():
            try:
                permitidos.append(Path(item.strip()).expanduser().resolve(strict=False))
            except (OSError, RuntimeError, ValueError):
                continue
    return any(alvo == raiz or raiz in alvo.parents for raiz in permitidos)


def resolver_caminho(nome_ou_caminho: str) -> str:
    """Se for apenas o nome (sem barras), converte para pasta Downloads, senão usa o caminho original."""
    nome_ou_caminho = str(nome_ou_caminho or "").strip(' "\'')
    if "\\" not in nome_ou_caminho and "/" not in nome_ou_caminho and ":" not in nome_ou_caminho:
        caminho_base = os.path.join(os.path.expanduser("~"), "Downloads")
        nome_ou_caminho = os.path.join(caminho_base, nome_ou_caminho)
    try:
        return str(Path(nome_ou_caminho).expanduser().resolve(strict=False))
    except (OSError, RuntimeError, ValueError):
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


def escrever_arquivo_texto_seguro(
    caminho: str,
    conteudo: str,
    *,
    sobrescrever: bool = False,
) -> dict:
    """Grava texto sem sobrescrita implícita e confirma o conteúdo relido.

    A rota cooperativa usa esta operação para manter a confirmação separada da
    simples aceitação do comando. O texto não aparece no retorno nem nos logs.
    """
    caminho_resolvido = resolver_caminho(caminho)
    if not verificar_trava_seguranca(caminho_resolvido):
        return {
            "ok": False,
            "status": "acesso_negado",
            "caminho": caminho_resolvido,
            "confirmado": False,
        }
    alvo = Path(caminho_resolvido)
    texto = str(conteudo or "")
    try:
        alvo.parent.mkdir(parents=True, exist_ok=True)
        if alvo.exists() and not sobrescrever:
            return {
                "ok": False,
                "status": "arquivo_existente_requer_confirmacao",
                "caminho": str(alvo),
                "confirmado": False,
            }

        if sobrescrever:
            temporario = ""
            try:
                with tempfile.NamedTemporaryFile(
                    "w",
                    encoding="utf-8",
                    newline="",
                    dir=str(alvo.parent),
                    prefix=f".{alvo.name}.",
                    suffix=".laylay.tmp",
                    delete=False,
                ) as arquivo:
                    temporario = arquivo.name
                    arquivo.write(texto)
                    arquivo.flush()
                    os.fsync(arquivo.fileno())
                os.replace(temporario, alvo)
            finally:
                if temporario and os.path.exists(temporario):
                    try:
                        os.remove(temporario)
                    except OSError:
                        pass
        else:
            # ``x`` garante que uma corrida entre a verificação e a escrita
            # nunca destrua um arquivo criado por outro processo.
            # Preserva exatamente o texto do clipboard. No Windows, a
            # tradução automática de quebras pode transformar CRLF e causar
            # um falso ``conteudo_nao_confirmado`` depois da releitura.
            with open(alvo, "x", encoding="utf-8", newline="") as arquivo:
                arquivo.write(texto)
                arquivo.flush()
                os.fsync(arquivo.fileno())

        with open(alvo, "r", encoding="utf-8", newline="") as arquivo:
            relido = arquivo.read()
        esperado = hashlib.sha256(texto.encode("utf-8")).hexdigest()
        observado = hashlib.sha256(relido.encode("utf-8")).hexdigest()
        confirmado = relido == texto and observado == esperado
        return {
            "ok": confirmado,
            "status": "arquivo_criado" if confirmado else "conteudo_nao_confirmado",
            "caminho": str(alvo),
            "confirmado": confirmado,
            "tamanho": len(relido),
            "hash": observado,
        }
    except FileExistsError:
        return {
            "ok": False,
            "status": "arquivo_existente_requer_confirmacao",
            "caminho": str(alvo),
            "confirmado": False,
        }
    except Exception as erro:
        print(f"❌ Erro ao gravar arquivo de forma segura: {type(erro).__name__}")
        return {
            "ok": False,
            "status": "falha_execucao",
            "caminho": str(alvo),
            "confirmado": False,
        }


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
        resultado = mover_para_lixeira(caminho)
        if resultado.requer_confirmacao:
            print(f"⚠️ [ARQUIVOS] Confirmação necessária antes da exclusão: {resultado.caminho}")
            return False
        if not resultado.sucesso:
            print(f"⚠️ [ARQUIVOS] Item não removido ({resultado.status}): {resultado.caminho}")
            return False
        print(f"🗑️ [ARQUIVOS] Enviado para a Lixeira da Laylay: {resultado.caminho}")
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


def buscar_itens_com_nome(nome: str, limite: int = 5) -> list[str]:
    """Localiza nomes exatos nas pastas pessoais para detectar exclusão ambígua."""
    alvo = str(nome or "").strip(' "\'').casefold()
    if not alvo or any(sep in alvo for sep in ("\\", "/", ":")):
        return []
    resultados: list[str] = []
    base = os.path.expanduser("~")
    for pasta in ("Downloads", "Desktop", "Documents", "Pictures"):
        raiz = os.path.join(base, pasta)
        if not os.path.isdir(raiz):
            continue
        for diretorio, pastas, arquivos in os.walk(raiz):
            for item in [*pastas, *arquivos]:
                if item.casefold() == alvo:
                    resultados.append(os.path.abspath(os.path.join(diretorio, item)))
                    if len(resultados) >= max(2, int(limite or 5)):
                        return resultados
    return resultados
