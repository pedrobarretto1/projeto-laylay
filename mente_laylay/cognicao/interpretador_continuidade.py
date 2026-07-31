"""Interpretacao semantica de respostas curtas para pendencias da Laylay."""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Callable, Dict


DECISOES_VALIDAS = {
    "ACEITAR",
    "RECUSAR",
    "TROCAR_ALTERNATIVA",
    "PEDIR_EXPLICACAO",
    "CORRIGIR_INFORMACAO",
    "MUDAR_ASSUNTO",
    "INDEFINIDO",
}


def _normalizar(texto: str) -> str:
    bruto = unicodedata.normalize("NFKD", str(texto or "").lower())
    sem_acento = "".join(ch for ch in bruto if not unicodedata.combining(ch))
    sem_acento = re.sub(r"[^\w\s]", " ", sem_acento)
    return re.sub(r"\s+", " ", sem_acento).strip()


def _extrair_json(raw: str) -> Dict[str, Any]:
    texto = str(raw or "").strip()
    if not texto:
        return {}
    try:
        data = json.loads(texto)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _normalizar_decisao(valor: Any) -> str:
    decisao = str(valor or "").upper().strip()
    decisao = re.sub(r"[^A-Z_]", "", decisao)
    return decisao if decisao in DECISOES_VALIDAS else "INDEFINIDO"


def _fallback_baixa_conf(texto: str) -> Dict[str, Any]:
    """Rede de seguranca pequena; a decisao principal deve vir da IA."""
    t = _normalizar(texto)
    if not t:
        return {"decisao": "INDEFINIDO", "confianca": 0.0, "motivo": "resposta vazia"}
    if any(p in t for p in ["explica", "como assim", "por que", "porque"]):
        return {"decisao": "PEDIR_EXPLICACAO", "confianca": 0.72, "motivo": "pedido curto de explicacao"}
    if any(p in t for p in ["outra", "outro", "diferente", "vibe", "estilo"]):
        return {"decisao": "TROCAR_ALTERNATIVA", "confianca": 0.70, "motivo": "resposta pede alternativa"}
    if any(p in t for p in ["nao", "agora nao", "deixa", "cancela", "esquece"]):
        return {"decisao": "RECUSAR", "confianca": 0.68, "motivo": "resposta recusa a pendencia"}
    if any(p in t for p in ["sim", "pode", "quero", "bora", "manda", "toca"]):
        return {"decisao": "ACEITAR", "confianca": 0.66, "motivo": "resposta aceita a pendencia"}
    return {"decisao": "INDEFINIDO", "confianca": 0.35, "motivo": "sem sinal semantico claro"}


def interpretar_resposta_pendente(
    *,
    texto_usuario: str,
    pendencia: Dict[str, Any],
    contexto: str = "",
    interpretar_llm: Callable[[str], str] | None = None,
) -> Dict[str, Any]:
    """Classifica o papel da resposta curta diante de uma pendencia.

    A IA decide primeiro. O fallback existe apenas para manter a Laylay
    funcional quando o modelo local estiver indisponivel.
    """
    texto = str(texto_usuario or "").strip()
    pend = pendencia if isinstance(pendencia, dict) else {}
    if not texto or not pend:
        return {"decisao": "INDEFINIDO", "confianca": 0.0, "motivo": "sem texto ou pendencia"}

    if callable(interpretar_llm):
        prompt = (
            "Voce interpreta respostas curtas do usuário para a Laylay.\n"
            "Nao execute nada. Apenas classifique a intencao semantica da resposta diante da pendencia.\n"
            "Decisoes possiveis: ACEITAR, RECUSAR, TROCAR_ALTERNATIVA, PEDIR_EXPLICACAO, "
            "CORRIGIR_INFORMACAO, MUDAR_ASSUNTO, INDEFINIDO.\n"
            "Responda APENAS JSON valido neste formato:\n"
            "{\"decisao\":\"...\",\"confianca\":0.0,\"motivo\":\"...\"}\n\n"
            f"Pendencia: {json.dumps(pend, ensure_ascii=False)}\n"
            f"Contexto recente: {contexto or 'nenhum'}\n"
            f"Resposta do usuário: {texto!r}\n"
        )
        try:
            data = _extrair_json(interpretar_llm(prompt))
            decisao = _normalizar_decisao(data.get("decisao"))
            confianca = float(data.get("confianca") or 0.0)
            motivo = str(data.get("motivo") or "").strip()
            if decisao != "INDEFINIDO" and confianca >= 0.55:
                return {"decisao": decisao, "confianca": confianca, "motivo": motivo or "interpretado pela IA"}
        except Exception:
            pass

    return _fallback_baixa_conf(texto)
