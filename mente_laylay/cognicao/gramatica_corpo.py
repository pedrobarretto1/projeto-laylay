"""Entidades e verbos do corpo; não concede autorização de execução."""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal
from typing import Any


_VERBOS_GIRO = r"(?:gira|gire|girar|vira|vire|virar|(?:da|de|dar)\s+uma\s+girada)"
_VERBOS_DESLOCAMENTO = r"(?:anda|ande|andar|avanca|avance|avancar|recua|recue|recuar)"
_NUMEROS_TEMPO = dict(zip(
    ("um", "dois", "tres", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez"),
    range(1, 11),
))
_TEMPO_SOLICITADO = re.compile(
    r"\s+(?:por|durante)\s+(?P<quantidade>\d{1,7}(?:[.,]\d{1,3})?|meio|"
    + "|".join(_NUMEROS_TEMPO)
    + r")\s*(?P<unidade>milissegundos?|ms|segundos?|s)(?=\s|$)"
)


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
    giro_medido = re.fullmatch(
        r"(?:gira|gire|girar|vira|vire|virar)\s+(\d{1,3})\s*(?:graus|°)\s+"
        r"(?:(?:para|pra)\s+)?(?:a\s+)?(esquerda|direita)", t)
    if giro_medido and 15 <= int(giro_medido[1]) <= 360:
        return {"intent": "CORPO_MOVER", "params": {"alvo": "corpo", "direcao": giro_medido[2],
                "angulo_graus": int(giro_medido[1]), "pwm": 160, "duracao_ms": 5000}}

    duracao_ms = 250
    tempo = _TEMPO_SOLICITADO.search(t)
    if tempo:
        quantidade = tempo["quantidade"]
        valor = Decimal("0.5") if quantidade == "meio" else Decimal(
            _NUMEROS_TEMPO.get(quantidade, quantidade.replace(",", "."))
        )
        if tempo["unidade"].startswith("s"):
            valor *= 1000
        if valor != valor.to_integral_value():
            return None
        duracao_ms = int(valor)
        t = t[:tempo.start()] + t[tempo.end():]

    giro = re.fullmatch(_VERBOS_GIRO
        + r"(?:\s+(?:(?:para|pra)\s+)?(?:a\s+)?(esquerda|direita))?"
        + r"(?:\s+um\s+(?:pouco|pouquinho))?", t)
    if giro:
        direcao = giro.group(1) or ""
    else:
        movimento = re.fullmatch(
            rf"({_VERBOS_DESLOCAMENTO})"
            r"(?:\s+um\s+(?:pouco|pouquinho))?"
            r"(?:\s+(?:(?:para|pra)\s+)?(?:a\s+)?(frente|tras))?"
            r"(?:\s+um\s+(?:pouco|pouquinho))?", t,
        )
        if not movimento:
            return None
        direcao = movimento.group(2) or ("tras" if movimento.group(1).startswith("recu") else "frente")
    return {"intent": "CORPO_MOVER", "params": {
        "alvo": "corpo", "direcao": direcao, "pwm": 160 if duracao_ms > 500 else 255,
        "duracao_ms": duracao_ms,
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
