"""Identidade dinâmica e confirmada da pessoa que conversa com a Laylay."""

from __future__ import annotations

import re
from typing import Any, Mapping


_PREFIXO_CORRECAO = re.compile(
    r"^(?:(?:n[aã]o|na verdade|corrigindo|olha|ei|j[aá] falei)"
    r"(?:\s+(?:lay|laylay))?\s*[,;:.-]?\s*)+",
    re.IGNORECASE,
)


def normalizar_nome_usuario(valor: Any) -> str:
    nome = re.sub(r"\s+", " ", str(valor or "")).strip(" .,!?:;\t\r\n")
    if not nome or len(nome) > 60 or len(nome.split()) > 4:
        return ""
    if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ' -]+", nome):
        return ""
    return nome.title()


def extrair_nome_usuario_explicito(texto: Any) -> str:
    """Extrai apenas uma apresentação inequívoca feita pelo próprio usuário."""
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not bruto or "?" in bruto:
        return ""
    declaracao = _PREFIXO_CORRECAO.sub("", bruto).strip()

    correcao = re.fullmatch(
        r"meu nome n[aã]o (?:e|é|eh|è)\s+[A-Za-zÀ-ÖØ-öø-ÿ' -]{1,60}"
        r"\s*[,;]\s*(?:meu nome\s+)?(?:e|é|eh|è)\s+"
        r"(?P<nome>[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ' -]{0,59})[.!]?",
        declaracao,
        re.IGNORECASE,
    )
    if correcao:
        return normalizar_nome_usuario(correcao.group("nome"))

    afirmacao = re.fullmatch(
        r"(?:meu nome (?:e|é|eh|è)|eu me chamo|me chamo|"
        r"pode me chamar de|me chama de)\s+"
        r"(?P<nome>[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ' -]{0,59})[.!]?",
        declaracao,
        re.IGNORECASE,
    )
    if not afirmacao:
        return ""
    return normalizar_nome_usuario(afirmacao.group("nome"))


def _registro_identidade_canonico(item: Mapping[str, Any]) -> str:
    if str(item.get("status") or "") != "ativo":
        return ""
    if not bool(item.get("confirmado_usuario")):
        return ""
    # Registros das primeiras versões não carregavam ``tipo`` na projeção de
    # leitura. A chave canônica + confirmação ainda é evidência suficiente;
    # um tipo explícito diferente, porém, é rejeitado para impedir colisões.
    tipo = str(item.get("tipo") or "").casefold()
    if tipo and tipo != "identidade":
        return ""
    if str(item.get("chave_semantica") or "") != "identidade:nome_usuario":
        return ""
    return normalizar_nome_usuario(item.get("valor"))


def _nome_recuperavel_de_registro(item: Mapping[str, Any]) -> tuple[str, str]:
    if not bool(item.get("confirmado_usuario")):
        return "", ""
    for campo in ("evidencia", "texto_original"):
        evidencia = str(item.get(campo) or "").strip()
        nome = extrair_nome_usuario_explicito(evidencia)
        if nome:
            return nome, evidencia
    if str(item.get("tipo") or "").casefold() == "identidade":
        nome = normalizar_nome_usuario(item.get("valor"))
        if nome:
            return nome, str(item.get("texto_original") or "").strip()
    return "", ""


def carregar_nome_usuario_confirmado(memoria_sqlite: Any) -> str:
    """Lê somente identidade ativa que tenha sido confirmada pelo usuário."""
    try:
        itens = memoria_sqlite.listar_aprendizados_semanticos(limit=300)
    except Exception:
        return ""
    registros = [item for item in itens or [] if isinstance(item, dict)]
    for item in registros:
        nome = _registro_identidade_canonico(item)
        if nome:
            return nome

    # Recupera instalações antigas nas quais uma regra genérica contendo a
    # palavra "nome" ocupou a chave da identidade e contradisse o registro
    # correto. A evidência ainda precisa ser uma apresentação explícita do
    # próprio usuário; texto produzido pela assistente nunca é aceito.
    for item in registros:
        nome, _evidencia = _nome_recuperavel_de_registro(item)
        if nome:
            return nome
    return ""


def reconciliar_nome_usuario_confirmado(memoria_sqlite: Any) -> str:
    """Restaura no formato canônico uma identidade antiga ainda comprovável."""
    try:
        itens = memoria_sqlite.listar_aprendizados_semanticos(limit=300)
    except Exception:
        return ""
    registros = [item for item in itens or [] if isinstance(item, dict)]
    for item in registros:
        nome = _registro_identidade_canonico(item)
        if nome:
            return nome
    for item in registros:
        nome, evidencia = _nome_recuperavel_de_registro(item)
        if not nome:
            continue
        if salvar_nome_usuario_confirmado(
            memoria_sqlite,
            nome,
            texto_original=evidencia or f"meu nome é {nome}",
        ):
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
