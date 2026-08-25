"""Contrato validado para a compreensão semântica de um turno.

Este módulo não responde ao usuário e nunca autoriza uma ação. Ele apenas
normaliza a leitura proposta por um interpretador, mantendo a decisão
operacional sob responsabilidade dos porteiros determinísticos.
"""

from __future__ import annotations

import re
from typing import Any, Dict
import unicodedata


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

ESTADOS_EMOCIONAIS_USUARIO = {
    "alegria", "alivio", "ansiedade", "cansaco", "culpa", "esgotamento",
    "irritacao", "medo", "orgulho", "tedio", "tristeza",
}
NATUREZAS_LEITURA_EMOCIONAL = {"leitura_social", "inferencia"}

_ALIASES_ESTADO_EMOCIONAL = {
    "alegre": "alegria",
    "contente": "alegria",
    "felicidade": "alegria",
    "feliz": "alegria",
    "aliviada": "alivio",
    "aliviado": "alivio",
    "ansiosa": "ansiedade",
    "ansioso": "ansiedade",
    "cansada": "cansaco",
    "cansado": "cansaco",
    "culpada": "culpa",
    "culpado": "culpa",
    "esgotada": "esgotamento",
    "esgotado": "esgotamento",
    "irritada": "irritacao",
    "irritado": "irritacao",
    "orgulhosa": "orgulho",
    "orgulhoso": "orgulho",
    "tediosa": "tedio",
    "tedioso": "tedio",
    "triste": "tristeza",
}

_ALIASES_NATUREZA_EMOCIONAL = {
    "direta": "leitura_social",
    "direto": "leitura_social",
    "explicita": "leitura_social",
    "explicito": "leitura_social",
    "expressa": "leitura_social",
    "expresso": "leitura_social",
    "literal": "leitura_social",
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


def _sem_acentos(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or "").casefold())
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip()


def _normalizar_leitura_emocional(valor: Any, *, texto: str) -> Dict[str, Any]:
    dados = dict(valor or {}) if isinstance(valor, dict) else {}
    estado = _sem_acentos(_texto_curto(dados.get("estado_usuario"), 40))
    estado = _ALIASES_ESTADO_EMOCIONAL.get(estado, estado)
    if estado not in ESTADOS_EMOCIONAIS_USUARIO:
        estado = "nenhum"
    causa = _texto_curto(dados.get("causa_expressa"), 300)
    evidencia = _texto_curto(dados.get("trecho_evidencia"), 240)
    natureza = _sem_acentos(_texto_curto(
        dados.get("natureza_evidencia") or "inferencia",
        40,
    ))
    natureza = _ALIASES_NATUREZA_EMOCIONAL.get(natureza, natureza)
    if natureza not in NATUREZAS_LEITURA_EMOCIONAL:
        natureza = "inferencia"
    confianca = _confianca(dados.get("confianca"), 0.0)
    hipotetica = bool(dados.get("hipotetica"))
    try:
        intensidade = max(0, min(3, int(dados.get("intensidade") or 0)))
    except (TypeError, ValueError):
        intensidade = 0
    evidencia_na_fala = bool(
        evidencia
        and _sem_acentos(evidencia) in _sem_acentos(texto)
    )
    valida = bool(
        estado != "nenhum"
        and intensidade > 0
        and causa
        and evidencia_na_fala
        and not hipotetica
        and confianca >= 0.72
    )
    return {
        "estado_usuario": estado,
        "intensidade": intensidade if valida else 0,
        "causa_expressa": causa,
        "trecho_evidencia": evidencia,
        "evidencia_na_fala": evidencia_na_fala,
        "natureza_evidencia": natureza,
        "hipotetica": hipotetica,
        "alvo": _texto_curto(dados.get("alvo") or "estado_geral", 160),
        "confianca": confianca,
        "valida": valida,
        "autoriza_execucao": False,
        "persistencia_pessoal": False,
    }


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
    leitura_emocional = _normalizar_leitura_emocional(
        dados.get("leitura_emocional"),
        texto=texto,
    )
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
        "leitura_emocional": leitura_emocional,
        "ambiguidades": _lista_textos(dados.get("ambiguidades"), limite_itens=6, limite_texto=160),
        "evidencias": _lista_textos(dados.get("evidencias"), limite_itens=8, limite_texto=160),
        "confianca": _confianca(dados.get("confianca"), 0.0),
        "origem": _texto_curto(origem, 40) or "desconhecida",
        # A leitura emocional é um contrato observacional independente da
        # classificação dos atos. Ela pode ser válida sozinha, mas nunca
        # concede autoridade operacional.
        "valida": bool(atos) or bool(leitura_emocional.get("valida")),
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
