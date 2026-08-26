"""Parecer operacional: autorização, limites e resultados reais de ações."""

from __future__ import annotations

from typing import Any, Dict, Iterable

from mente_laylay.especialistas.capacidades import consultar_capacidade
from mente_laylay.memoria_mental.resultado_acao import normalizar_resultado_acao


def construir_parecer_operacional(
    texto: str,
    *,
    turno: Dict[str, Any],
    retrato: Dict[str, Any],
) -> Dict[str, Any]:
    modalidade = str(turno.get("modalidade_geral") or turno.get("modalidade") or "conversa")
    ato_principal = str(turno.get("ato_principal") or turno.get("modalidade") or "conversa")
    texto_operacional = str(turno.get("texto_operacional") or "").strip()
    operacao_explicita = str(retrato.get("operacao_explicita") or "").strip()
    ativo = bool(
        texto_operacional
        or operacao_explicita
        or ato_principal in {"comando", "confirmacao", "recusa"}
    )
    decisao_unificada_presente = "autoriza_execucao" in turno
    autorizacao_modalidade = (
        bool(turno.get("autoriza_execucao"))
        if decisao_unificada_presente
        else ato_principal in {"comando", "confirmacao", "recusa"}
    )
    autoriza_execucao = bool(
        ativo
        and autorizacao_modalidade
        and modalidade not in {"pergunta", "deliberacao", "correcao"}
    )
    referencia = dict(retrato.get("referencia_resolvida") or {})
    referencia_pedida = bool(retrato.get("referencia_tipo"))
    referencia_confianca = 0.95 if referencia else (0.25 if referencia_pedida else 1.0)
    alvo_confianca = referencia_confianca if referencia_pedida else (0.90 if ativo else 1.0)
    acao_confianca = float(turno.get("confianca") or (0.90 if ativo else 1.0))
    confianca_geral = min(acao_confianca, alvo_confianca, referencia_confianca)
    requer_esclarecimento = bool(
        turno.get("requer_esclarecimento")
        or (ativo and confianca_geral < 0.70)
    )
    if requer_esclarecimento:
        autoriza_execucao = False
    return {
        "ativo": ativo,
        "texto": (texto_operacional or (str(texto or "").strip() if ativo else ""))[:300],
        "autoriza_execucao": autoriza_execucao,
        "operacao": operacao_explicita,
        "intents_permitidos": list(retrato.get("intents_permitidos") or []),
        "referencia": referencia,
        "confianca": round(confianca_geral, 3),
        "confiancas": {
            "acao": round(acao_confianca, 3),
            "alvo": round(alvo_confianca, 3),
            "referencia": round(referencia_confianca, 3),
        },
        "requer_esclarecimento": requer_esclarecimento,
        "confirmacao_explicita": bool(
            ato_principal == "confirmacao"
            and turno.get("confirmacao_contextual_valida", not decisao_unificada_presente)
        ),
        "motivo_bloqueio": (
            "referencia_ambigua" if requer_esclarecimento
            else "modalidade_nao_autorizada" if ativo and not autoriza_execucao
            else ""
        ),
        "pode_falar_sem_resultado": False,
    }


def avaliar_candidato_operacional(
    parecer: Dict[str, Any] | None,
    intent: str,
    *,
    confianca_candidato: float = 0.0,
    saude: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    operacional = dict(parecer or {})
    capacidade = consultar_capacidade(
        intent,
        saude=saude if saude is not None else dict(operacional.get("saude_componentes") or {}),
    )
    confianca = min(
        float(operacional.get("confianca") or 1.0),
        float(confianca_candidato or 0.0),
    )
    permitido = bool(
        capacidade.get("disponivel")
        and operacional.get("autoriza_execucao")
        and not operacional.get("requer_esclarecimento")
    )
    requer_confirmacao = bool(capacidade.get("exige_confirmacao"))
    confirmacao_satisfeita = bool(
        operacional.get("confirmacao_explicita")
        or operacional.get("confirmacao_satisfeita")
    )
    motivo = ""
    if not capacidade.get("disponivel"):
        motivo = str(capacidade.get("motivo") or "capacidade_indisponivel")
    elif operacional.get("requer_esclarecimento"):
        motivo = "referencia_ambigua"
    elif not operacional.get("autoriza_execucao"):
        motivo = "turno_nao_autoriza_execucao"
    return {
        "permitido": permitido,
        "motivo": motivo,
        "confianca": round(confianca, 3),
        "capacidade": capacidade,
        "requer_confirmacao": requer_confirmacao,
        "confirmacao_satisfeita": confirmacao_satisfeita,
        # O executor pode preparar uma pendência, mas só pode aplicar o efeito
        # destrutivo quando este campo for verdadeiro.
        "efeito_autorizado": permitido and (not requer_confirmacao or confirmacao_satisfeita),
    }


def anexar_resultados_operacionais(
    parecer: Dict[str, Any] | None,
    comandos: Iterable[Dict[str, Any]] = (),
) -> tuple[Dict[str, Any], bool]:
    atualizado = dict(parecer or {})
    comandos_validos = [dict(item) for item in (comandos or ()) if isinstance(item, dict)]
    resultados_brutos = [
        item for item in comandos_validos
        if str(item.get("status") or "").strip()
        or item.get("executou") is not None
        or item.get("confirmado") is not None
    ]
    resultados = [normalizar_resultado_acao(item).como_dict() for item in resultados_brutos]
    if comandos_validos:
        atualizado["comandos_planejados"] = [
            str(item.get("intent") or item.get("acao") or "").strip()
            for item in comandos_validos
            if str(item.get("intent") or item.get("acao") or "").strip()
        ]
    if resultados:
        atualizado["resultados"] = resultados
        atualizado["resultado_disponivel"] = True
        atualizado["resultado_confirmado"] = bool(
            resultados
            and all(item.get("confirmado") is True for item in resultados)
        )
        atualizado["pode_afirmar_conclusao"] = atualizado["resultado_confirmado"]
        atualizado["sem_confirmacao"] = [
            item for item in resultados if item.get("confirmado") is not True
        ]
    return atualizado, bool(resultados)
