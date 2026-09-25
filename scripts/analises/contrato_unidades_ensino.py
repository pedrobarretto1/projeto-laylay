"""Contrato experimental de evidência didática; não participa do runtime."""

from __future__ import annotations

import re
from typing import Any, Mapping
from urllib.parse import urlparse


_PAPEIS = frozenset({"definicao", "exemplo", "explicacao"})
_CONTA = re.compile(r"(?P<a>\d{1,5})\s*[x×*]\s*(?P<b>\d{1,5})\s*=\s*(?P<resultado>\d{1,10})")
_CONTA_NA_FALA = re.compile(
    r"(?<!\w)(?P<a>\d{1,5})\s*"
    r"(?P<operador>dividido\s+por|/|[x×*])\s*"
    r"(?P<b>\d{1,5})\s*(?:=|é\s+igual\s+a)\s*"
    r"(?P<resultado>\d{1,10})(?!\w)",
    re.IGNORECASE,
)


def extrair_contas_explicitas(texto: str) -> list[dict[str, Any]]:
    """Confere apenas contas inteiras explícitas, preservando seu span.

    Nunca aprova a sentença que contém a conta nem inferências sobre caixas,
    pessoas ou outras frases sem uma operação explícita.
    """
    contas: list[dict[str, Any]] = []
    for achado in _CONTA_NA_FALA.finditer(texto):
        a, b, resultado = (int(achado[campo]) for campo in ("a", "b", "resultado"))
        operador = achado["operador"].casefold()
        if operador == "/" or operador.startswith("dividido"):
            estado = (
                "operacao_invalida" if b == 0 else
                "calculo_conferido" if a == b * resultado else
                "calculo_incorreto"
            )
        else:
            estado = "calculo_conferido" if a * b == resultado else "calculo_incorreto"
        contas.append({
            "inicio": achado.start(), "fim": achado.end(),
            "expressao": achado.group(), "estado": estado,
        })
    return contas


def _normalizar(texto: object) -> str:
    return re.sub(r"\s+", " ", str(texto or "")).strip()


def _resultado(estado: str, fonte_id: str, trecho: str, *, implicacao: bool = False) -> dict[str, Any]:
    return {
        "estado": estado,
        "fonte_id": fonte_id,
        "trecho": trecho,
        # Não confundir localização textual com prova de uma paráfrase ou
        # com a verdade da página no mundo externo.
        "implicacao_verificada": implicacao,
    }


def avaliar_unidade_ensino(
    proposta: Mapping[str, Any], fontes: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Separa proveniência, cópia literal e implicação, sem usar LLM como juiz.

    A saída é diagnóstico de uma candidata, nunca autorização para publicar a
    aula. Um campo ``verificado`` vindo do proponente é deliberadamente ignorado.
    """
    fonte_id = _normalizar(proposta.get("fonte_id"))
    trecho = _normalizar(proposta.get("trecho"))
    afirmacao = _normalizar(proposta.get("afirmacao"))
    if _normalizar(proposta.get("papel")) not in _PAPEIS:
        return _resultado("papel_invalido", fonte_id, trecho)
    fonte = fontes.get(fonte_id)
    if not isinstance(fonte, Mapping):
        return _resultado("fonte_nao_localizada", fonte_id, trecho)
    url = urlparse(_normalizar(fonte.get("url")))
    if url.scheme not in {"http", "https"} or not url.netloc:
        return _resultado("fonte_sem_url", fonte_id, trecho)
    texto_lido = _normalizar(fonte.get("trecho"))
    if not trecho or not texto_lido or not re.search(
        rf"(?<!\w){re.escape(trecho)}(?!\w)", texto_lido,
    ):
        return _resultado("trecho_nao_localizado", fonte_id, trecho)
    if not afirmacao or afirmacao.casefold() != trecho.casefold():
        return _resultado("pendente_implicacao", fonte_id, trecho)
    conta = _CONTA.fullmatch(afirmacao)
    if conta:
        correto = int(conta["a"]) * int(conta["b"]) == int(conta["resultado"])
        return _resultado(
            "calculo_conferido" if correto else "calculo_incorreto",
            fonte_id, trecho, implicacao=correto,
        )
    return _resultado("literal_rastreavel", fonte_id, trecho)
