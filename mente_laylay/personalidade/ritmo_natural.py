"""Varia o ritmo superficial sem alterar o conteúdo da resposta."""

from __future__ import annotations

import re
import time
from collections import deque
from threading import RLock
from typing import Iterable, Sequence


_LOCK = RLock()
_FALAS_RECENTES: deque[str] = deque(maxlen=8)
_ABERTURAS_RECENTES: deque[str] = deque(maxlen=4)


def abertura_da_fala(texto: str) -> str:
    fala = re.sub(r"\s+", " ", str(texto or "")).strip().casefold()
    if not fala:
        return ""
    achado = re.match(r"^(tá|ta|entendi|boa|ei|beleza|pronto|certo|claro|fechado)\b", fala)
    if achado:
        return achado.group(1)
    palavras = re.findall(r"[\wÀ-ÿ]+", fala)
    return " ".join(palavras[:2])


def escolher_sem_repeticao(
    items: Sequence[str] | Iterable[str],
    *,
    fallback: str = "",
    escolha_aleatoria,
) -> str:
    opcoes = [str(item).strip() for item in items if str(item or "").strip()]
    if not opcoes:
        return fallback
    with _LOCK:
        recentes = set(_FALAS_RECENTES)
        aberturas = set(_ABERTURAS_RECENTES)
        preferidas = [
            item for item in opcoes
            if item.casefold() not in recentes and abertura_da_fala(item) not in aberturas
        ]
        if not preferidas:
            preferidas = [item for item in opcoes if item.casefold() not in recentes]
        escolhida = escolha_aleatoria(preferidas or opcoes)
        _FALAS_RECENTES.append(escolhida.casefold())
        abertura = abertura_da_fala(escolhida)
        if abertura:
            _ABERTURAS_RECENTES.append(abertura)
        return escolhida


def ajustar_abertura_repetida(texto: str, historico: deque[str]) -> str:
    """Remove somente marcador discursivo repetido, mantendo a frase útil."""
    fala = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not fala:
        return fala
    abertura = abertura_da_fala(fala)
    marcadores = {"tá", "ta", "entendi", "boa", "ei", "beleza", "pronto", "certo", "claro", "fechado"}
    if abertura in marcadores and abertura in list(historico)[-2:]:
        restante = re.sub(
            r"^(?:tá|ta|entendi|boa|ei|beleza|pronto|certo|claro|fechado)\s*[,.:;!\-]*\s*",
            "",
            fala,
            count=1,
            flags=re.IGNORECASE,
        ).strip()
        if len(restante.split()) >= 2:
            fala = restante[0].upper() + restante[1:]
            abertura = abertura_da_fala(fala)
    if abertura:
        historico.append(abertura)
    return fala


def ajustar_uso_natural_nome(
    texto: str,
    emocao: str,
    ultimo_uso_ts: float = 0.0,
    *,
    intervalo_s: float = 180.0,
    nome_usuario: str = "",
) -> tuple[str, float]:
    """Mantém o nome quando ele tem função; remove vocativo decorativo."""
    fala = re.sub(r"\s+", " ", str(texto or "")).strip()
    nome = re.sub(r"\s+", " ", str(nome_usuario or "")).strip()
    if not nome or not re.search(rf"\b{re.escape(nome)}\b", fala, flags=re.IGNORECASE):
        return fala, float(ultimo_uso_ts or 0.0)

    agora = time.time()
    emo = str(emocao or "calma").strip().casefold()
    emocional = emo not in {"", "calma", "neutra", "neutral"}
    importante = bool(re.search(
        r"\b(?:cuidado|aten[cç][aã]o|alerta|perigo|foi mal|desculpa|preocup|"
        r"n[aã]o consegui|falhou|erro|preciso te falar|olha isso)\b",
        fala,
        flags=re.IGNORECASE,
    ))
    tecnico = bool(re.search(
        r"\b(?:abri|abrindo|fechei|fechando|maximizei|maximizado|volume|"
        r"playlist|arquivo|pasta|aba|janela|aplicativo|programa|ventilador|"
        r"liguei|desliguei|executado|confirmado)\b",
        fala,
        flags=re.IGNORECASE,
    ))
    recente = bool(ultimo_uso_ts and agora - float(ultimo_uso_ts) < intervalo_s)

    if emocional or importante or (not tecnico and not recente):
        return fala, agora

    # Remove apenas o nome confirmado usado como vocativo pontuado. Sem essa
    # exigência, construções como "o quarto de Ana" perderiam o nome legítimo.
    nome_re = re.escape(nome)
    limpa = re.sub(rf"^{nome_re}\s*[,.:;!\-]+\s*", "", fala, flags=re.IGNORECASE)
    limpa = re.sub(rf"\s*,\s*{nome_re}(?=[.!?…]|$)", "", limpa, flags=re.IGNORECASE)
    limpa = re.sub(r"\s+([,.!?…])", r"\1", limpa)
    limpa = re.sub(r"\s{2,}", " ", limpa).strip()
    if limpa and limpa[0].islower():
        limpa = limpa[0].upper() + limpa[1:]
    return (limpa or fala), float(ultimo_uso_ts or 0.0)


def ajustar_encerramento_organico(texto: str, texto_usuario: str = "") -> str:
    """Remove convite opcional, nunca uma pergunta necessária isolada."""
    fala = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not fala or "?" not in fala:
        return fala
    partes = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", fala) if p.strip()]
    pergunta = partes[-1].casefold().strip()
    entrada = str(texto_usuario or "").casefold()
    baixa_demanda = bool(re.fullmatch(
        r"(?:agora )?(?:nada(?: demais)?|de boa|tranquilo|tranquila|suave|tudo certo|so isso|só isso)",
        entrada.strip(" .!?"),
    ))
    oferta_generica = bool(re.fullmatch(
        r"(?:posso|quer que eu)\s+(?:te ajudar(?: em mais alguma coisa)?|fazer algo|ajudar com algo)\??",
        pergunta,
    ))
    if len(partes) == 1 and baixa_demanda and oferta_generica:
        return "Tudo certo. Um pouco de sossego também vale."
    if len(partes) < 2 or "?" not in partes[-1]:
        return fala

    convite_opcional = bool(re.fullmatch(
        r"(?:quer(?: que eu)?\s+)?(?:ir mais fundo|aprofundar|continuar(?: nisso| nesse assunto)?|"
        r"seguir por ai|seguir por aí|trocar de assunto|puxar mais detalhes?|abrir mais esse assunto|"
        r"conversar sobre algo(?: em particular)?|falar sobre algo(?: em particular)?|"
        r"continuar conversando|falar mais sobre isso)\??",
        pergunta,
    ))
    opiniao_ja_pedida = any(
        sinal in entrada
        for sinal in ("o que voce acha", "o que você acha", "sua opiniao", "sua opinião", "voce concorda", "você concorda")
    )
    devolucao_opiniao = opiniao_ja_pedida and pergunta in {
        "e voce?", "e você?", "o que acha?", "qual a sua?", "concorda?",
    }
    if not convite_opcional and not devolucao_opiniao and not (baixa_demanda and oferta_generica):
        return fala

    restante = " ".join(partes[:-1]).strip()
    return restante or fala
