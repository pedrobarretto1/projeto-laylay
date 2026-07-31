"""Identidade dinâmica e confirmada da pessoa que conversa com a Laylay."""

from __future__ import annotations

import re
from typing import Any


def normalizar_nome_usuario(valor: Any) -> str:
    nome = re.sub(r"\s+", " ", str(valor or "")).strip(" .,!?:;\t\r\n")
    if not nome or len(nome) > 60 or len(nome.split()) > 4:
        return ""
    if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ' -]+", nome):
        return ""
    return nome.title()


def carregar_nome_usuario_confirmado(memoria_sqlite: Any) -> str:
    """Lê somente identidade ativa que tenha sido confirmada pelo usuário."""
    try:
        itens = memoria_sqlite.listar_aprendizados_semanticos(limit=300)
    except Exception:
        return ""
    for item in itens or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "") != "ativo" or not bool(item.get("confirmado_usuario")):
            continue
        if str(item.get("chave_semantica") or "") != "identidade:nome_usuario":
            continue
        nome = normalizar_nome_usuario(item.get("valor"))
        if nome:
            return nome
    return ""


def salvar_nome_usuario_confirmado(
    memoria_sqlite: Any,
    nome: str,
    *,
    texto_original: str = "",
) -> bool:
    nome_limpo = normalizar_nome_usuario(nome)
    if not nome_limpo:
        return False
    try:
        salvo = memoria_sqlite.salvar_aprendizado_semantico(
            tipo="identidade",
            gatilho="nome do usuário",
            valor=nome_limpo,
            regra=f"O nome confirmado do usuário é {nome_limpo}.",
            texto_original=str(texto_original or f"meu nome é {nome_limpo}").strip(),
            confianca=1.0,
            origem="usuario_explicito",
            evidencia=str(texto_original or f"meu nome é {nome_limpo}").strip(),
            status="ativo",
            confirmado_usuario=True,
        )
    except Exception:
        return False
    return bool(salvo)


def contexto_identidade_usuario(nome: str) -> str:
    nome_limpo = normalizar_nome_usuario(nome)
    if nome_limpo:
        return (
            "--- IDENTIDADE CONFIRMADA DO INTERLOCUTOR ---\n"
            f"O usuário informou explicitamente que seu nome é {nome_limpo}. "
            "Use o nome com moderação e somente quando combinar com a conversa."
        )
    return (
        "--- IDENTIDADE DO INTERLOCUTOR ---\n"
        "O usuário ainda não informou um nome confirmado. Trate-o por 'você', "
        "não adivinhe um nome e não use nomes encontrados em caminhos, contas ou exemplos."
    )
