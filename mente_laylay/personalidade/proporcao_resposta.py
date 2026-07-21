"""Ajusta tamanho de respostas sem decidir intenção ou conteúdo."""

from __future__ import annotations

import re
from typing import Dict


def classificar_proporcao(texto_usuario: str, tipo_interacao: str = "") -> str:
    texto = re.sub(r"\s+", " ", str(texto_usuario or "")).strip()
    base = texto.casefold()
    palavras = base.split()
    tipo = str(tipo_interacao or "").strip().lower()

    if tipo in {"acao", "aprendizado"}:
        return "tecnica"
    if any(sinal in base for sinal in (
        "explica detalhadamente", "explica melhor", "me explica direito",
        "quero entender", "passo a passo", "com detalhes", "aprofund",
        "por que isso acontece", "como isso funciona", "como funciona",
    )):
        return "explicativa"
    if any(sinal in base for sinal in (
        "estou triste", "to triste", "tô triste", "estou cansado",
        "estou cansada", "to mal", "tô mal", "desabafar", "me sinto",
        "estou preocupado", "estou preocupada", "não aguento", "nao aguento",
    )):
        return "emocional"
    if tipo == "confirmacao" or len(palavras) <= 4 and "?" not in texto:
        return "curta"
    if "?" in texto and len(palavras) <= 12:
        return "objetiva"
    return "normal"


LIMITES: Dict[str, tuple[int, int]] = {
    "curta": (2, 240),
    "objetiva": (3, 420),
    "emocional": (5, 700),
    "explicativa": (7, 1000),
    "normal": (5, 700),
    "tecnica": (3, 460),
}


def ajustar_proporcao_resposta(
    fala: str,
    texto_usuario: str,
    tipo_interacao: str = "",
    *,
    possui_comandos: bool = False,
) -> str:
    texto = re.sub(r"\s+", " ", str(fala or "")).strip()
    if not texto or possui_comandos:
        return texto

    perfil = classificar_proporcao(texto_usuario, tipo_interacao)
    max_frases, max_chars = LIMITES[perfil]
    if len(texto) <= max_chars:
        return texto

    frases = [f.strip() for f in re.split(r"(?<=[.!?…])\s+", texto) if f.strip()]
    if len(frases) <= 1:
        # Não corta uma ideia no meio quando o modelo produziu uma frase longa.
        return texto

    escolhidas = []
    total = 0
    for frase in frases:
        novo_total = total + len(frase) + (1 if escolhidas else 0)
        if escolhidas and (len(escolhidas) >= max_frases or novo_total > max_chars):
            break
        escolhidas.append(frase)
        total = novo_total

    return " ".join(escolhidas).strip() or texto


def limite_tokens_resposta(texto_usuario: str, *, modo_rapido: bool = False) -> int:
    perfil = classificar_proporcao(texto_usuario, "")
    limites = {
        "curta": 320,
        "objetiva": 420,
        "emocional": 520,
        "explicativa": 640,
        "normal": 520,
        "tecnica": 420,
    }
    limite = limites.get(perfil, 520)
    if modo_rapido:
        return min(limite, 384)
    return limite

