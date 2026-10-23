"""Reconhecimento central dos estados internos do transporte da LLM."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FalhaRespostaObservada:
    """Retorno negativo do serviço ou da revisão, capturado pelo host."""
    turno_id: str
    texto_usuario: str
    principal_sha256: str
    etapa: str
    estado_tecnico: str
    problemas_revisao: tuple[str, ...] = ()


def realizacao_falha_resposta(plano: Any) -> str:
    """Só a realização exata do retorno negativo pode concluir esta resposta."""
    from collections.abc import Mapping
    from mente_laylay.personalidade.contingencia_natural import fala_falha_geracao
    if not isinstance(plano, Mapping) or plano.get("comandos") or plano.get("requer_execucao"):
        return ""
    fonte = plano.get("falha_resposta_observada")
    if (type(fonte) is not FalhaRespostaObservada or not fonte.turno_id
        or fonte.turno_id != str(plano.get("id") or "")
        or fonte.texto_usuario != plano.get("texto_usuario")
        or not isinstance(fonte.principal_sha256, str)
        or not re.fullmatch(r"[a-f0-9]{64}", fonte.principal_sha256)):
        return ""
    if (fonte.etapa == "revisao_comunicacao" and fonte.estado_tecnico == ""
        and type(fonte.problemas_revisao) is tuple and fonte.problemas_revisao
        and all(type(p) is str and p.strip() for p in fonte.problemas_revisao)):
        categoria = "reparo_rejeitado"
    elif (fonte.etapa in {"reparo_comunicacao", "reparo_factual", "reparo_json", "continuacao"}
          and fonte.problemas_revisao == ()):
        categoria = categoria_estado_tecnico_llm(fonte.estado_tecnico)
    else:
        return ""
    return fala_falha_geracao(categoria) if categoria else ""


def realizacao_falha_principal(plano: Any) -> str:
    """Conclusão fechada de uma emissão falha observada pelo host neste turno.

    A proposta não prova o conteúdo da IA. O retorno negativo do serviço,
    associado pelo host à identidade atual, sustenta somente sua própria falha
    de geração. JSON, histórico e receipts de outras ações não são essa fonte.
    """
    from collections.abc import Mapping
    from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
    from mente_laylay.personalidade.contingencia_natural import fala_falha_geracao

    if not isinstance(plano, Mapping) or plano.get("comandos"):
        return ""
    fonte = plano.get("falha_geracao_principal")
    if (type(fonte) is not ContratoPropostaPrincipal
        or fonte.sucesso_modelo is not False or fonte.estado != "falha_tecnica"
        or not fonte.turno_id or str(plano.get("id") or "") != fonte.turno_id
        or plano.get("texto_usuario") != fonte.texto_usuario):
        return ""
    categoria = categoria_estado_tecnico_llm(fonte.resposta_bruta)
    return fala_falha_geracao(categoria) if categoria else ""


_MOTIVOS_ORCAMENTO = frozenset({
    "limite_chamadas", "principal_duplicada", "reparo_duplicado", "prazo_esgotado",
    "turno_obsoleto", "turno_finalizado", "fatia_secundaria_insuficiente",
    "circuito_aberto", "probe_em_andamento",
})


def estado_bloqueio_orcamento_llm(motivo: str) -> str:
    """Codifica só razões canônicas; detalhes arbitrários nunca viram sentinela."""
    if motivo not in _MOTIVOS_ORCAMENTO:
        return "__LAYLAY_LLM_OCUPADA__"
    return f"__LAYLAY_LLM_ORCAMENTO_{motivo.upper()}__"


def eh_estado_tecnico_llm(valor: Any) -> bool:
    """Detecta sentinelas mesmo após pontuação ou sublinhados serem removidos."""
    return bool(categoria_estado_tecnico_llm(valor))


def categoria_estado_tecnico_llm(valor: Any) -> str:
    """Preserva o motivo conhecido; não infere a causa física da falha."""
    texto = str(valor or "").casefold().strip()
    compacto = re.sub(r"[^a-z0-9]+", "", texto)
    for motivo in _MOTIVOS_ORCAMENTO:
        if compacto == "laylayllmorcamento" + motivo.replace("_", ""):
            return "orcamento_" + motivo
    return {
        "laylayllmtimeout": "timeout",
        "laylayllmindisponivel": "indisponivel",
        # Também usado pelo orçamento/obsolescência: não comprova carga alta.
        "laylayllmocupada": "chamada_nao_disponivel",
    }.get(compacto, "")
