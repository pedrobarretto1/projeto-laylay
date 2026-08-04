"""Escolha central e explicavel do unico caminho de um turno."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, Iterable

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.retrato_turno import dominio_intent
from mente_laylay.especialistas.operacional import avaliar_candidato_operacional
from mente_laylay.especialistas.capacidades import INTENTS_SOMENTE_LEITURA
from mente_laylay.cognicao.decisao_turno import (
    consolidar_arbitragem,
    criar_contrato_decisao,
)


@dataclass(frozen=True)
class CandidatoDecisao:
    tipo: str
    valor: Dict[str, Any]
    origem: str
    confianca: float = 0.0
    evidencia: tuple[str, ...] = field(default_factory=tuple)


_PRIORIDADE = {
    "correcao": 100,
    "resposta_pendencia": 90,
    "comando_explicito": 80,
    "comando_contextual": 60,
    "repeticao": 50,
    "conversa": 20,
}


def arbitrar_turno(
    texto: str,
    candidatos: Iterable[CandidatoDecisao],
    *,
    turno: Dict[str, Any] | None = None,
    retrato: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Retorna vencedor e rastreio; nunca devolve dois caminhos executaveis."""
    leitura = dict(turno or classificar_modalidade_turno(texto))
    modalidade = str(leitura.get("modalidade_geral") or leitura.get("modalidade") or "conversa")
    snapshot = dict(retrato or {})
    painel_bruto = leitura.get("especialistas")
    painel_especialistas = painel_bruto if isinstance(painel_bruto, dict) else {}
    parecer_bruto = painel_especialistas.get("operacional")
    parecer_operacional = parecer_bruto if isinstance(parecer_bruto, dict) else {}
    intents_permitidos = {str(x).upper() for x in snapshot.get("intents_permitidos") or []}
    aceitos: list[CandidatoDecisao] = []
    rejeitados: list[Dict[str, Any]] = []

    for candidato in candidatos:
        motivo = ""
        intent_candidato = str(candidato.valor.get("intent") or "").upper() if isinstance(candidato.valor, dict) else ""
        dominio_candidato = dominio_intent(intent_candidato)
        referencia = dict(snapshot.get("referencia_resolvida") or {})
        dominio_referencia = {
            "playlist": "musica", "musica": "musica", "jogo": "jogo",
            "artista": "musica", "cantor": "musica", "cantora": "musica",
            "banda": "musica",
            "janela": "app", "app": "app", "site": "site", "iot": "iot",
            "dispositivo": "iot", "arquivo": "arquivo", "pasta": "arquivo",
        }.get(str(referencia.get("tipo") or "").lower(), "")
        tem_verbo_operacional = bool(re.search(
            r"\b(?:abre|fecha|liga|desliga|toca|coloca|bota|salva|guarda|adiciona|"
            r"apaga|remove|pausa|retoma|repete|volta|avanca|avança|aumenta|diminui)\b",
            str(texto or "").casefold(),
        ))
        avaliacao_operacional = (
            avaliar_candidato_operacional(
                parecer_operacional,
                intent_candidato,
                confianca_candidato=float(candidato.confianca or 0.0),
            )
            if parecer_operacional and intent_candidato
            else {}
        )
        if not isinstance(candidato.valor, dict) or not candidato.valor.get("intent"):
            motivo = "candidato sem intencao executavel"
        elif (
            parecer_operacional
            and intent_candidato not in INTENTS_SOMENTE_LEITURA
            and not avaliacao_operacional.get("permitido")
        ):
            motivo = (
                "especialista operacional nao autorizou execucao neste turno: "
                f"{avaliacao_operacional.get('motivo') or 'sem_autorizacao'}"
            )
        elif (
            candidato.tipo == "comando_explicito"
            and intent_candidato not in INTENTS_SOMENTE_LEITURA
            and intent_candidato != "SUGGEST_ACTION"
            and not bool(
                leitura.get("autoriza_execucao")
                if "autoriza_execucao" in leitura
                else modalidade in {"comando", "misto"}
            )
        ):
            motivo = (
                f"modalidade {modalidade} não autorizou ação com efeito "
                "neste turno"
            )
        elif modalidade in {"deliberacao", "pergunta"} and candidato.tipo in {
            "comando_contextual", "repeticao"
        }:
            motivo = f"modalidade {modalidade} nao autoriza inferencia operacional"
        elif modalidade == "correcao" and candidato.tipo not in {"correcao", "comando_explicito"}:
            motivo = "correcao atual tem precedencia sobre contexto antigo"
        elif modalidade in {"conversa", "reacao"} and candidato.tipo in {"comando_contextual", "repeticao"} and not tem_verbo_operacional:
            motivo = "comentario sem verbo operacional nao autoriza acao herdada"
        elif intents_permitidos and str(candidato.valor.get("intent") or "").upper() not in intents_permitidos:
            motivo = f"operacao explicita {snapshot.get('operacao_explicita')} bloqueia heranca incompatível"
        elif candidato.tipo in {"comando_contextual", "repeticao"} and dominio_referencia and dominio_candidato and dominio_referencia != dominio_candidato:
            motivo = f"entidade referida pertence a {dominio_referencia}, nao a {dominio_candidato}"
        elif (
            candidato.tipo in {"comando_contextual", "repeticao"}
            and snapshot.get("referencia_tipo")
            and not snapshot.get("referencia_resolvida")
            and float(candidato.confianca or 0.0) < 0.75
        ):
            motivo = "referencia contextual sem entidade confiavel"

        if motivo:
            rejeitados.append({"origem": candidato.origem, "tipo": candidato.tipo, "motivo": motivo})
        else:
            aceitos.append(candidato)

    aceitos.sort(
        key=lambda item: (_PRIORIDADE.get(item.tipo, 0), float(item.confianca or 0.0)),
        reverse=True,
    )
    vencedor = aceitos[0] if aceitos else None
    for descartado in aceitos[1:]:
        rejeitados.append({
            "origem": descartado.origem,
            "tipo": descartado.tipo,
            "motivo": "menor prioridade que o vencedor do turno",
        })

    resultado = {
        "decisao": dict(vencedor.valor) if vencedor else None,
        "origem": vencedor.origem if vencedor else "",
        "tipo": vencedor.tipo if vencedor else "",
        "confianca": round(float(vencedor.confianca or 0.0), 3) if vencedor else 0.0,
        "modalidade": modalidade,
        "evidencias": list(vencedor.evidencia) if vencedor else [],
        "rejeitados": rejeitados,
        "retrato_id": snapshot.get("id"),
        "referencia_resolvida": dict(snapshot.get("referencia_resolvida") or {}),
    }
    resultado["contrato_decisao"] = consolidar_arbitragem(
        criar_contrato_decisao(leitura),
        resultado,
    )
    return resultado
