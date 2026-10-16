"""Interpretacao semantica de respostas curtas para pendencias da Laylay."""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Callable, Dict

from mente_laylay.cognicao.normalizacao_linguagem import texto_e_metalinguistico
from mente_laylay.memoria_mental.compatibilidade_contexto import classificar_repeticao_curta


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


def qualificar_feedback_humor(texto: str) -> Dict[str, Any]:
    """Qualifica avaliação literal de uma brincadeira; não presume a entrega.

    O vínculo e o contexto pertencem ao observador de entrega. Pedidos de
    preferência, citação, relato de terceiros e correção factual não são
    amostras de tolerância implícita.
    """
    literal = str(texto or "").strip()
    if not literal or "?" in literal or texto_e_metalinguistico(literal):
        return {}
    t = _normalizar(literal)
    t = re.sub(r"^(?:nao )?(?:lay|laylay)\s+|^nao (?:lay|laylay)\s+", "", t)
    entidade = r"(?:piada|brincadeira|zoeira|tirada)"
    referencia = rf"(?:(?:essa|esta|a|sua) {entidade}|seu tom de brincadeira)"
    padroes = (
        ("correcao", "leve", rf"(?:{referencia} (?:passou do ponto|foi pesada demais|foi ofensiva|me incomodou)|voce pegou pesado (?:nessa|nesta) {entidade})"),
        ("recusa", "leve", rf"(?:nao gostei (?:dessa|desta|da sua) {entidade}|para (?:com|de) (?:essas|as|suas) (?:piadas|brincadeiras|zoeiras|tiradas))"),
        ("aceitacao", "mais_humor", rf"(?:gostei (?:dessa|desta|da sua) {entidade}|gostei do seu tom de brincadeira|{referencia} foi (?:boa|engracada|divertida))"),
        ("repeticao", "mais_humor", rf"(?:repete|repita|pode repetir) (?:essa|esta|a) {entidade}"),
    )
    for tipo, direcao, padrao in padroes:
        if re.fullmatch(padrao, t):
            return {"alvo_feedback": "humor", "tipo": tipo, "direcao": direcao,
                    "evidencia_literal": literal}
    return {}


def solicitacao_feedback_humor(texto: str) -> bool:
    """Só uma pergunta literal sobre o estilo permite qualificar silêncio."""
    literal = str(texto or "").strip()
    return bool(literal.endswith("?") and re.fullmatch(
        r"(?:essa (?:piada|brincadeira|tirada) (?:foi pesada|passou do ponto|foi boa)|"
        r"voce gostou dessa (?:piada|brincadeira|tirada)|"
        r"esse tom de brincadeira (?:te incomodou|ficou bom))", _normalizar(literal)))


def resposta_indefinida_sobre_humor(texto: str) -> bool:
    """Reconhece resposta sem direção, somente diante da pergunta de estilo."""
    return bool(not texto_e_metalinguistico(texto) and re.fullmatch(
        r"(?:ainda )?nao sei|talvez|prefiro pensar|nao tenho certeza|estou pensando",
        _normalizar(texto)))


def qualificar_feedback_corporal(texto: str) -> Dict[str, Any]:
    """Entidades corporais no interpretador compartilhado; nunca autoriza motor."""
    literal = str(texto or "").strip()
    if not literal or "?" in literal or texto_e_metalinguistico(literal):
        return {}
    t = _normalizar(literal)
    entidade = r"(?:gesto|movimento|dancinha|giro)"
    referencia = rf"(?:esse|essa|este|esta|o seu|a sua) {entidade}"
    padroes = (
        ("recusa", False, rf"nao gostei (?:desse|dessa|deste|desta|do seu|da sua) {entidade}"),
        ("aceitacao", True, rf"(?:(?:gostei|curti) (?:desse|dessa|deste|desta|do seu|da sua) {entidade}|adorei {referencia})"),
        ("correcao", False, rf"{referencia} (?:ficou|foi|esta) (?:muito forte|muito rapido|muito fraco|lento demais)"),
        ("repeticao", None, rf"(?:repete|repita|pode repetir) {referencia}"),
    )
    for tipo, aceito, padrao in padroes:
        if re.fullmatch(padrao, t):
            return {"alvo_feedback": "corpo_motor", "tipo": tipo, "aceito": aceito, "evidencia_literal": literal}
    return {}


def classificar_feedback_comunicativo(texto: str) -> str:
    """Classifica evidência sobre uma comunicação, sem consumir ou autorizar.

    O chamador continua dono do vínculo com a entrega/turno. Não interpretar
    um sim solto aqui: confirmações pertencem à pendência canônica.
    """
    if texto_e_metalinguistico(texto):
        return ""
    corporal = qualificar_feedback_corporal(texto)
    if corporal:
        return "aceita" if corporal["tipo"] == "aceitacao" else corporal["tipo"]
    humor = qualificar_feedback_humor(texto)
    if humor:
        return "aceita" if humor["tipo"] == "aceitacao" else humor["tipo"]
    t = _normalizar(texto)
    if not t:
        return ""
    if re.search(
        r"\b(?:na verdade|nao e isso|voce entendeu errado|essa dica esta errada|"
        r"quis dizer|voce errou|nao lay|nao foi isso|corrigindo)\b", t,
    ):
        return "correcao"
    if re.search(
        r"\b(?:para de comentar|nao precisa comentar|fica quieta|isso e obvio|"
        r"nao interrompe|sem dica)\b", t,
    ):
        return "recusa"
    if classificar_repeticao_curta(t, _normalizar) or re.fullmatch(
        r"(?:repete|repita)\s+(?:de novo|outra vez)", t,
    ):
        return "repeticao"
    if re.search(
        r"\b(?:boa dica|isso ajudou|ajudou bastante|gostei dessa|manda mais|"
        r"foi util|foi boa|(?:esse|essa|o|a) (?:aviso|dica|comentario|alerta|observacao) ajudou)\b", t,
    ):
        return "aceita"
    return ""


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
