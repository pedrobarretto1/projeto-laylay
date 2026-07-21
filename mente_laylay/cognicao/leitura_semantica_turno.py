"""Contrato validado para a compreensão semântica de um turno.

Este módulo não responde ao usuário e nunca autoriza uma ação. Ele apenas
normaliza a leitura proposta por um interpretador, mantendo a decisão
operacional sob responsabilidade dos porteiros determinísticos.
"""

from __future__ import annotations

from typing import Any, Dict


TIPOS_ATO = {
    "saudacao",
    "pergunta",
    "pergunta_opiniao",
    "pergunta_capacidade",
    "resposta_social",
    "relato",
    "opiniao",
    "reacao",
    "agradecimento",
    "correcao",
    "recusa",
    "confirmacao",
    "contraproposta",
    "pedido_acao",
    "sugestao",
    "deliberacao",
    "encerramento",
    "outro",
}

MODALIDADES = {
    "vazio",
    "conversa",
    "pergunta",
    "comando",
    "misto",
    "correcao",
    "confirmacao",
    "recusa",
    "reacao",
    "deliberacao",
    "ambiguo",
}

RELACOES_CONTEXTO = {
    "independente",
    "responde_fala_anterior",
    "continua_assunto",
    "muda_assunto",
    "corrige_interpretacao",
    "confirma_pendencia",
    "recusa_pendencia",
    "ambiguo",
}


def _texto_curto(valor: Any, limite: int) -> str:
    return " ".join(str(valor or "").strip().split())[:limite]


def _confianca(valor: Any, padrao: float = 0.0) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        numero = padrao
    return round(max(0.0, min(1.0, numero)), 3)


def _lista_textos(valores: Any, *, limite_itens: int = 8, limite_texto: int = 120) -> list[str]:
    if not isinstance(valores, (list, tuple)):
        return []
    resultado: list[str] = []
    for valor in valores[:limite_itens]:
        texto = _texto_curto(valor, limite_texto)
        if texto and texto not in resultado:
            resultado.append(texto)
    return resultado


def _normalizar_ato(item: Any) -> Dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    tipo = _texto_curto(item.get("tipo"), 40).lower()
    if tipo not in TIPOS_ATO:
        tipo = "outro"
    ato = {
        "tipo": tipo,
        "falante": _texto_curto(item.get("falante") or "pedro", 40).lower(),
        "destinatario": _texto_curto(item.get("destinatario"), 40).lower(),
        "conteudo": _texto_curto(item.get("conteudo"), 240),
        "tema": _texto_curto(item.get("tema"), 160),
        "entidades": _lista_textos(item.get("entidades"), limite_itens=6, limite_texto=100),
        "confianca": _confianca(item.get("confianca"), 0.5),
    }
    return ato


def _normalizar_operacional(valor: Any) -> Dict[str, Any]:
    dados = dict(valor or {}) if isinstance(valor, dict) else {}
    return {
        "pedido_real": bool(dados.get("pedido_real")),
        "hipotetico": bool(dados.get("hipotetico")),
        "negado": bool(dados.get("negado")),
        "requer_esclarecimento": bool(dados.get("requer_esclarecimento")),
        "intent_candidato": _texto_curto(dados.get("intent_candidato"), 80).upper(),
        "acao": _texto_curto(dados.get("acao"), 100),
        "alvo": _texto_curto(dados.get("alvo"), 180),
        "parametros": dict(dados.get("parametros") or {}) if isinstance(dados.get("parametros"), dict) else {},
        "confianca": _confianca(dados.get("confianca"), 0.0),
        # Deliberadamente fixo: compreensão semântica não concede permissão.
        "autoriza_execucao": False,
    }


def normalizar_leitura_semantica(
    dados: Any,
    *,
    texto: str,
    origem: str = "llm",
) -> Dict[str, Any]:
    """Valida uma leitura externa e devolve somente o contrato conhecido."""
    if not isinstance(dados, dict):
        return {}
    atos = [
        ato
        for ato in (_normalizar_ato(item) for item in list(dados.get("atos") or [])[:8])
        if ato is not None
    ]
    modalidade = _texto_curto(dados.get("modalidade_geral"), 40).lower()
    if modalidade not in MODALIDADES:
        modalidade = "misto" if len(atos) > 1 else "conversa"
    relacao = dict(dados.get("relacao_contextual") or {}) if isinstance(dados.get("relacao_contextual"), dict) else {}
    tipo_relacao = _texto_curto(relacao.get("tipo"), 60).lower()
    if tipo_relacao not in RELACOES_CONTEXTO:
        tipo_relacao = "independente"
    operacional = _normalizar_operacional(dados.get("operacional"))
    return {
        "versao": 1,
        "texto": _texto_curto(texto, 500),
        "atos": atos,
        "modalidade_geral": modalidade,
        "ato_principal": _texto_curto(dados.get("ato_principal"), 60).lower(),
        "tema_principal": _texto_curto(dados.get("tema_principal"), 180),
        "entidades": _lista_textos(dados.get("entidades"), limite_itens=10, limite_texto=120),
        "relacao_contextual": {
            "tipo": tipo_relacao,
            "responde_fala_anterior": bool(relacao.get("responde_fala_anterior")),
            "inicia_assunto_novo": bool(relacao.get("inicia_assunto_novo")),
            "referencia_pendencia": bool(relacao.get("referencia_pendencia")),
        },
        "operacional": operacional,
        "ambiguidades": _lista_textos(dados.get("ambiguidades"), limite_itens=6, limite_texto=160),
        "evidencias": _lista_textos(dados.get("evidencias"), limite_itens=8, limite_texto=160),
        "confianca": _confianca(dados.get("confianca"), 0.0),
        "origem": _texto_curto(origem, 40) or "desconhecida",
        "valida": bool(atos),
        "somente_observacao": True,
    }


def comparar_com_legado(leitura: Dict[str, Any], turno_legado: Dict[str, Any] | None) -> Dict[str, Any]:
    """Resume divergências sem escolher qual classificador está correto."""
    legado = dict(turno_legado or {})
    modalidade_nova = str(leitura.get("modalidade_geral") or "")
    modalidade_legada = str(legado.get("modalidade_geral") or legado.get("modalidade") or "")
    pedido_semantico = bool((leitura.get("operacional") or {}).get("pedido_real"))
    autorizacao_legada = bool(legado.get("autoriza_execucao"))
    divergencias: list[str] = []
    if modalidade_nova and modalidade_legada and modalidade_nova != modalidade_legada:
        divergencias.append("modalidade")
    if pedido_semantico != autorizacao_legada:
        divergencias.append("sinal_operacional")
    return {
        "modalidade_semantica": modalidade_nova,
        "modalidade_legada": modalidade_legada,
        "pedido_semantico": pedido_semantico,
        "autorizacao_legada": autorizacao_legada,
        "divergencias": divergencias,
        "divergiu": bool(divergencias),
    }


_MODALIDADE_POR_ATO = {
    "pergunta": "pergunta",
    "pergunta_opiniao": "pergunta",
    "pergunta_capacidade": "pergunta",
    "correcao": "correcao",
    "recusa": "recusa",
    "confirmacao": "confirmacao",
    "reacao": "reacao",
    "deliberacao": "deliberacao",
    "pedido_acao": "comando",
}


def aplicar_leitura_conversacional(
    turno_legado: Dict[str, Any] | None,
    leitura: Dict[str, Any] | None,
    *,
    confianca_minima: float = 0.72,
) -> Dict[str, Any]:
    """Adapta somente conversa segura, sem ampliar permissão operacional.

    Nesta etapa, um turno que o legado já autorizou ou que a leitura descreveu
    como pedido de ação permanece totalmente sob o fluxo anterior.
    """
    original = dict(turno_legado or {})
    semantica = dict(leitura or {})
    atos = [dict(item) for item in list(semantica.get("atos") or []) if isinstance(item, dict)]
    operacional = dict(semantica.get("operacional") or {})
    tipos = {str(item.get("tipo") or "").lower() for item in atos}
    try:
        confianca = float(semantica.get("confianca") or 0.0)
    except (TypeError, ValueError):
        confianca = 0.0
    insegura = bool(
        not semantica.get("valida")
        or not tipos
        or tipos <= {"outro"}
        or confianca < float(confianca_minima)
        or original.get("autoriza_execucao")
        or operacional.get("pedido_real")
        or "pedido_acao" in tipos
        or str(semantica.get("modalidade_geral") or "").lower() == "comando"
    )
    if insegura:
        return original

    segmentos = []
    for indice, ato in enumerate(atos):
        tipo = str(ato.get("tipo") or "outro").lower()
        segmentos.append({
            "indice": indice,
            "texto": str(ato.get("conteudo") or "").strip()[:240],
            "modalidade": _MODALIDADE_POR_ATO.get(tipo, "conversa"),
            "ato": tipo,
            "tema": str(ato.get("tema") or "").strip()[:160],
            "confianca": _confianca(ato.get("confianca"), confianca),
        })
    modalidade_semantica = str(semantica.get("modalidade_geral") or "conversa").lower()
    if len(segmentos) > 1:
        modalidade_geral = "misto"
    elif modalidade_semantica in MODALIDADES:
        modalidade_geral = modalidade_semantica
    else:
        modalidade_geral = segmentos[0]["modalidade"] if segmentos else "conversa"
    principal = str(semantica.get("ato_principal") or (atos[-1].get("tipo") if atos else "conversa")).lower()
    modalidade_principal = _MODALIDADE_POR_ATO.get(principal, "conversa")
    resultado = dict(original)
    resultado.update(
        modalidade=modalidade_principal,
        modalidade_geral=modalidade_geral,
        ato_principal=principal,
        segmentos=segmentos,
        confianca=round(confianca, 3),
        motivo="leitura semântica conversacional validada",
        acao_explicita=False,
        autoriza_execucao=False,
        natureza_acao="nenhuma",
        origem_modalidade="semantica_conversacional",
        leitura_semantica={**semantica, "uso_conversacional": True},
        classificacao_legada={
            "modalidade": original.get("modalidade"),
            "modalidade_geral": original.get("modalidade_geral"),
            "confianca": original.get("confianca"),
            "autoriza_execucao": bool(original.get("autoriza_execucao")),
        },
    )
    return resultado
