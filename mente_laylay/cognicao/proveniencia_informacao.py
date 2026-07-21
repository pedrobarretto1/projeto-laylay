"""Contrato único para distinguir a origem e o alcance de uma informação."""

from __future__ import annotations

from typing import Any, Dict


_STATUS_BLOQUEADOS = {"contestado", "corrigido", "incerto"}


def classificar_proveniencia_informacao(
    item: Dict[str, Any] | None,
    *,
    contexto: str = "",
) -> Dict[str, Any]:
    """Interpreta metadados já existentes sem tentar adivinhar pelo texto.

    O resultado separa a categoria da informação de seu alcance. Um relato do
    usuário pode sustentar preferências e experiências pessoais, mas não vira
    confirmação de um fato externo. Uma opinião continua subjetiva, mesmo com
    alta confiança. Somente evidência externa válida pode sustentar fatos sobre
    o mundo.
    """
    dados = dict(item or {})
    status = str(dados.get("status") or "").strip().casefold()
    tipo_alegacao = str(dados.get("tipo") or "").strip().casefold()
    autor = str(dados.get("autor") or "").strip().casefold()
    origem_declarada = str(dados.get("origem") or "").strip()
    origem_norm = origem_declarada.casefold()
    fonte = str(dados.get("fonte") or "").strip()
    contexto_norm = str(contexto or "").strip().casefold()

    bloqueada = status in _STATUS_BLOQUEADOS
    eh_opiniao = tipo_alegacao == "opiniao" or status == "opiniao"
    eh_usuario = bool(
        autor == "usuario"
        or origem_norm == "usuario"
        or status == "relatado_pelo_usuario"
        or dados.get("confirmado_usuario") is True
    )
    eh_externa = bool(
        fonte
        and (
            status == "confirmado_por_fonte"
            or contexto_norm == "fundamentacao_factual"
            or dados.get("confiavel") is True
        )
    )

    if eh_opiniao:
        subtipo = "opiniao_usuario" if eh_usuario else "opiniao_laylay"
        return {
            "tipo": "opiniao",
            "subtipo": subtipo,
            "origem": "usuario" if eh_usuario else (autor or "laylay"),
            "autor": autor or ("usuario" if eh_usuario else "laylay"),
            "subjetiva": True,
            "bloqueada": bloqueada,
            "pode_sustentar_fato_externo": False,
            "pode_sustentar_contexto_pessoal": eh_usuario and not bloqueada,
        }

    if eh_externa:
        dentro_validade = dados.get("evidencia_dentro_validade")
        confiavel = bool(
            not bloqueada
            and dados.get("confiavel", status == "confirmado_por_fonte")
            and dentro_validade is not False
        )
        return {
            "tipo": "informacao_externa",
            "subtipo": "evidencia_externa",
            "origem": fonte,
            "autor": autor or "fonte_externa",
            "subjetiva": False,
            "bloqueada": bloqueada,
            "pode_sustentar_fato_externo": confiavel,
            "pode_sustentar_contexto_pessoal": False,
        }

    if eh_usuario:
        return {
            "tipo": "memoria_usuario",
            "subtipo": "relato_ou_preferencia_pessoal",
            "origem": origem_declarada or "usuario",
            "autor": autor or "usuario",
            "subjetiva": False,
            "bloqueada": bloqueada,
            "pode_sustentar_fato_externo": False,
            "pode_sustentar_contexto_pessoal": not bloqueada,
        }

    return {
        "tipo": "sem_evidencia",
        "subtipo": status or "origem_desconhecida",
        "origem": origem_declarada or fonte,
        "autor": autor,
        "subjetiva": False,
        "bloqueada": bloqueada,
        "pode_sustentar_fato_externo": False,
        "pode_sustentar_contexto_pessoal": False,
    }


def limitar_proveniencia_invalida(
    proveniencia: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Preserva a origem para diagnóstico, removendo seu poder factual."""
    resultado = dict(proveniencia or {})
    resultado["pode_sustentar_fato_externo"] = False
    resultado["bloqueada"] = True
    return resultado
