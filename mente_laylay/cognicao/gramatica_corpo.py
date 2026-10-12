"""Entidades e verbos do corpo; não concede autorização de execução."""
from __future__ import annotations

import re
import unicodedata
from typing import Any


def analisar_pedido_corporal(texto: str) -> dict[str, Any] | None:
    t = unicodedata.normalize("NFKD", str(texto or "").casefold())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"\s+", " ", t).strip(" .,!?:;")
    t = re.sub(r"^por favor[,]?\s+", "", t)
    if re.fullmatch(r"(?:ativa|ative|ativar)\s+(?:o\s+)?(?:modo\s+)?passeio\s+(?:na mesa com barreiras|na bancada|na area delimitada|com rodas suspensas)", t):
        return {"intent": "CORPO_COMPANHIA", "params": {"alvo": "corpo", "acao": "ativar", "passeio": True}}
    if re.fullmatch(r"(?:desativa|desative|desativar)\s+(?:o\s+)?(?:modo\s+)?passeio", t):
        return {"intent": "CORPO_COMPANHIA", "params": {"alvo": "corpo", "acao": "desativar"}}
    if re.fullmatch(r"(?:ativa|ative|ativar)\s+(?:o\s+)?modo companhia\s+(?:na bancada|na area delimitada|com rodas suspensas)", t):
        return {"intent": "CORPO_COMPANHIA", "params": {"alvo": "corpo", "acao": "ativar"}}
    if re.fullmatch(r"(?:desativa|desative|desativar)\s+(?:o\s+)?modo companhia", t):
        return {"intent": "CORPO_COMPANHIA", "params": {"alvo": "corpo", "acao": "desativar"}}
    if re.fullmatch(r"(?:para|pare|parar)\s+(?:(?:os|seus|meus)\s+)?(?:motores|motor|corpo)", t):
        return {"intent": "CORPO_PARAR", "params": {"alvo": "corpo"}}
    giro = re.fullmatch(r"(?:gira|gire|girar|vira|vire|virar)\s+(?:(?:para|pra)\s+)?(?:a\s+)?(esquerda|direita)(?:\s+um\s+(?:pouco|pouquinho))?", t)
    if giro:
        direcao = giro.group(1)
    else:
        movimento = re.fullmatch(
            r"(anda|ande|andar|avanca|avance|avancar|recua|recue|recuar)"
            r"(?:\s+um\s+(?:pouco|pouquinho))?"
            r"(?:\s+(?:(?:para|pra)\s+)?(?:a\s+)?(frente|tras))?"
            r"(?:\s+um\s+(?:pouco|pouquinho))?", t,
        )
        if not movimento:
            return None
        direcao = movimento.group(2) or ("tras" if movimento.group(1).startswith("recu") else "frente")
    return {"intent": "CORPO_MOVER", "params": {
        "alvo": "corpo", "direcao": direcao, "pwm": 255, "duracao_ms": 250,
    }}


def detectar_intencao_corpo(texto: str) -> dict[str, Any] | None:
    # Moldura e polaridade são lidas pelo owner canônico, sobre o original.
    from mente_laylay.cognicao.modalidade_turno import (
        analisar_protecao_operacional, extrair_nucleo_pedido_operacional,
    )
    if analisar_protecao_operacional(texto).get("bloqueia_execucao"):
        return None
    nucleo = extrair_nucleo_pedido_operacional(texto) or texto
    return analisar_pedido_corporal(nucleo)
