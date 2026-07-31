"""Contrato único que limita decisão, execução e resposta em cada turno."""

from __future__ import annotations

from typing import Any, Dict, Iterable

from mente_laylay.cognicao.contratos_turno import ContratoDecisaoTurno


def criar_contrato_decisao(
    turno: Dict[str, Any] | None,
    plano: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Cria a autorização inicial sem inventar uma intenção operacional."""
    leitura = dict(turno or {})
    planejamento = dict(plano or {})
    modalidade = str(
        leitura.get("modalidade_geral")
        or leitura.get("modalidade")
        or planejamento.get("modalidade")
        or "conversa"
    ).strip().lower()
    autoriza_execucao = bool(leitura.get("autoriza_execucao"))
    requer_execucao = bool(planejamento.get("requer_execucao"))
    misto = bool(planejamento.get("misto")) or modalidade == "misto"
    permite_acao = bool(autoriza_execucao and requer_execucao)
    if misto and permite_acao:
        proprietario = "coordenador"
    elif permite_acao:
        proprietario = "operacional"
    else:
        proprietario = "conversa"
    return ContratoDecisaoTurno(
        turno_id=planejamento.get("id") or leitura.get("id"),
        modalidade=modalidade,
        proprietario=proprietario,
        permite_acao=permite_acao,
        permite_resposta=True,
        requer_esclarecimento=bool(leitura.get("requer_esclarecimento")),
        intencao="",
        origem_decisao="classificador_turno",
        confianca=leitura.get("confianca") or 0.0,
        status="planejada",
    ).como_dict()


def consolidar_arbitragem(
    contrato: Dict[str, Any] | None,
    arbitragem: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Anexa o vencedor real ao contrato; ausência de vencedor não autoriza ação."""
    novo = ContratoDecisaoTurno.de_mapping(contrato).como_dict()
    resultado = dict(arbitragem or {})
    decisao = resultado.get("decisao") if isinstance(resultado.get("decisao"), dict) else {}
    intent = str(decisao.get("intent") or decisao.get("acao") or "").strip().upper()
    if intent:
        novo.update(
            proprietario="operacional",
            permite_acao=True,
            intencao=intent,
            origem_decisao=str(resultado.get("origem") or "arbitro"),
            confianca=round(float(resultado.get("confianca") or novo.get("confianca") or 0.0), 3),
            status="decidida",
        )
    elif novo.get("permite_acao") and not list(resultado.get("rejeitados") or []):
        # Um detector que não encontrou candidato não revoga um pedido
        # explicitamente autorizado. Outro especialista ainda pode entendê-lo.
        novo.update(
            origem_decisao=str(resultado.get("origem") or "arbitro_sem_candidato"),
            status="aguardando_intencao",
        )
    else:
        novo.update(
            proprietario="conversa",
            permite_acao=False,
            intencao="",
            origem_decisao=str(resultado.get("origem") or "arbitro_sem_vencedor"),
            status="sem_acao",
        )
    return ContratoDecisaoTurno.de_mapping(novo).como_dict()


def filtrar_comandos_pelo_turno(
    comandos: Iterable[Dict[str, Any]] | None,
    *,
    turno: Dict[str, Any] | None,
    plano: Dict[str, Any] | None,
    retrato: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Impede que comandos inventados pela resposta da IA escapem do árbitro."""
    candidatos = [dict(item) for item in (comandos or ()) if isinstance(item, dict)]
    leitura = dict(turno or {})
    planejamento = dict(plano or {})
    snapshot = dict(retrato or {})
    contrato = dict(planejamento.get("decisao_turno") or {})
    autoriza = bool(
        leitura.get("autoriza_execucao")
        and planejamento.get("requer_execucao")
        and contrato.get("permite_acao", True)
    )
    permitidos = {str(item).strip().upper() for item in snapshot.get("intents_permitidos") or ()}
    aceitos: list[Dict[str, Any]] = []
    rejeitados: list[Dict[str, Any]] = []
    for comando in candidatos:
        intent = str(comando.get("intent") or comando.get("acao") or "").strip().upper()
        if not autoriza:
            motivo = "turno não autorizou execução"
        elif not intent:
            motivo = "comando sem intenção"
        elif permitidos and intent not in permitidos:
            motivo = "intenção incompatível com a operação explícita"
        else:
            aceitos.append(comando)
            continue
        rejeitados.append({"intent": intent, "motivo": motivo})
    return {
        "comandos": aceitos,
        "rejeitados": rejeitados,
        "autoriza_execucao": autoriza,
        "proprietario": str(contrato.get("proprietario") or "conversa"),
    }
