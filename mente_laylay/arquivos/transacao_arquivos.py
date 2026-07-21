"""Transacoes seguras para corrigir uma operacao recente de arquivo."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from typing import Any, Dict

from mente_laylay.arquivos.arquivos_sistema import verificar_trava_seguranca


@dataclass(frozen=True)
class ResultadoTransacaoArquivo:
    sucesso: bool
    status: str
    origem: str = ""
    destino: str = ""
    detalhes: Dict[str, Any] = field(default_factory=dict)


def resolver_local_usuario(valor: str) -> str:
    bruto = str(valor or "").strip(' "\'')
    normalizado = bruto.casefold()
    home = os.path.expanduser("~")
    aliases = {
        "downloads": os.path.join(home, "Downloads"),
        "download": os.path.join(home, "Downloads"),
        "desktop": os.path.join(home, "Desktop"),
        "area de trabalho": os.path.join(home, "Desktop"),
        "área de trabalho": os.path.join(home, "Desktop"),
        "documentos": os.path.join(home, "Documents"),
        "documents": os.path.join(home, "Documents"),
    }
    if normalizado in aliases:
        return aliases[normalizado]
    if os.path.isabs(bruto):
        return os.path.normpath(bruto)
    return os.path.join(home, "Downloads", bruto)


def caminho_criado_por_params(intent: str, params: Dict[str, Any]) -> str:
    dados = dict(params or {})
    if str(intent or "").upper() == "CREATE_FOLDER":
        nome = str(dados.get("nome") or dados.get("pasta") or dados.get("alvo") or "").strip()
        pai = str(dados.get("pasta_pai") or dados.get("parent") or "Downloads").strip()
        return os.path.join(resolver_local_usuario(pai), nome) if nome else ""
    if str(intent or "").upper() == "CREATE_FILE":
        alvo = str(dados.get("alvo") or dados.get("nome") or dados.get("arquivo") or "").strip()
        return resolver_local_usuario(alvo) if alvo else ""
    return ""


def executar_transacao_arquivo(params: Dict[str, Any]) -> ResultadoTransacaoArquivo:
    dados = dict(params or {})
    operacao = str(dados.get("operacao") or "").lower().strip()
    origem = os.path.normpath(str(dados.get("origem") or "").strip())
    if not origem or not os.path.exists(origem):
        return ResultadoTransacaoArquivo(False, "origem_nao_encontrada", origem=origem)
    if not verificar_trava_seguranca(origem):
        return ResultadoTransacaoArquivo(False, "origem_bloqueada", origem=origem)

    if operacao in {"mover", "renomear"}:
        if operacao == "mover":
            pasta_destino = resolver_local_usuario(str(dados.get("destino") or ""))
            destino = os.path.join(pasta_destino, os.path.basename(origem))
        else:
            novo_nome = str(dados.get("novo_nome") or "").strip(' "\'')
            if not novo_nome or os.path.basename(novo_nome) != novo_nome:
                return ResultadoTransacaoArquivo(False, "nome_invalido", origem=origem)
            destino = os.path.join(os.path.dirname(origem), novo_nome)
        destino = os.path.normpath(destino)
        if not verificar_trava_seguranca(destino):
            return ResultadoTransacaoArquivo(False, "destino_bloqueado", origem, destino)
        if os.path.exists(destino):
            return ResultadoTransacaoArquivo(False, "destino_ja_existe", origem, destino)
        try:
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            shutil.move(origem, destino)
            confirmado = os.path.exists(destino) and not os.path.exists(origem)
            if confirmado:
                return ResultadoTransacaoArquivo(True, "movido" if operacao == "mover" else "renomeado", origem, destino)
            if os.path.exists(destino) and not os.path.exists(origem):
                shutil.move(destino, origem)
            return ResultadoTransacaoArquivo(False, "validacao_falhou", origem, destino)
        except Exception as exc:
            if os.path.exists(destino) and not os.path.exists(origem):
                try:
                    shutil.move(destino, origem)
                except Exception:
                    pass
            return ResultadoTransacaoArquivo(False, "falha_execucao", origem, destino, {"erro": str(exc)[:180]})

    if operacao == "editar_conteudo" and os.path.isfile(origem):
        try:
            with open(origem, "r", encoding="utf-8") as arquivo:
                anterior = arquivo.read()
            novo = str(dados.get("conteudo") or "")
            with open(origem, "w", encoding="utf-8") as arquivo:
                arquivo.write(novo)
            with open(origem, "r", encoding="utf-8") as arquivo:
                confirmado = arquivo.read() == novo
            if confirmado:
                return ResultadoTransacaoArquivo(True, "conteudo_atualizado", origem, origem)
            with open(origem, "w", encoding="utf-8") as arquivo:
                arquivo.write(anterior)
            return ResultadoTransacaoArquivo(False, "validacao_falhou", origem, origem)
        except Exception as exc:
            return ResultadoTransacaoArquivo(False, "falha_execucao", origem, origem, {"erro": str(exc)[:180]})

    return ResultadoTransacaoArquivo(False, "operacao_nao_suportada", origem=origem)
