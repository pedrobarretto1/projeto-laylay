"""Produção de respostas sociais e afetivas da conversa."""

from __future__ import annotations

import random
from collections import deque
from typing import Any, Dict

from mente_laylay.personalidade.base_conversa import _ajustar, _call, _get
from mente_laylay.personalidade.leitura_social_conversa import (
    _normalizar_reconhecimento,
    tipo_reconhecimento_afetivo,
)


_ULTIMAS_RESPOSTAS_RECONHECIMENTO: deque[str] = deque(maxlen=4)


def _escolher_reconhecimento(opcoes: list[str]) -> str:
    candidatas = [fala for fala in opcoes if fala not in _ULTIMAS_RESPOSTAS_RECONHECIMENTO]
    fala = random.choice(candidatas or opcoes)
    _ULTIMAS_RESPOSTAS_RECONHECIMENTO.append(fala)
    return fala


def _contexto_do_agradecimento(ctx: Dict[str, Any]) -> str:
    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    partes = " ".join([
        str(mente.get("ultima_resposta") or ""),
        str(mente.get("ultimo_alvo") or ""),
        str(mente.get("ultima_habilidade") or ""),
        str(mente.get("ultima_intencao") or ""),
        str(_get(ctx, "ultimo_topico_conversa", "") or ""),
    ])
    t = _normalizar_reconhecimento(partes)
    if any(p in t for p in ("receita", "massa", "farinha", "ingrediente", "xicara", "gramas", "cozinha")):
        return "receita"
    if any(p in t for p in ("resumo", "pagina", "artigo", "conteudo", "resumir_pagina")):
        return "resumo"
    if any(p in t for p in ("musica", "playlist", "faixa", "youtube", "music_")):
        return "musica"
    if any(p in t for p in ("arquivo", "pasta", "aplicativo", "programa", "janela", "chrome", "iot_control")):
        return "acao"
    if any(p in t for p in ("codigo", "python", "estudo", "explicacao", "explicar", "senai")):
        return "explicacao"
    return "geral"


def responder_agradecimento_ou_elogio(ctx: Dict[str, Any], texto_usuario: str) -> str:
    tipo = tipo_reconhecimento_afetivo(texto_usuario)
    contexto = _contexto_do_agradecimento(ctx)
    nivel = 1 if tipo == "agradecimento" else 2
    motivo = "agradeceu pela ajuda" if tipo == "agradecimento" else "recebeu elogio"
    _call(ctx, "_definir_emocao", "envergonhada", nivel, motivo, default=None)

    respostas_contextuais = {
        "receita": [
            "Ah, que nada. Fico feliz que as medidas tenham ajudado. Quando quiser ajustar outra receita, pode falar comigo.",
            "Imagina. Gostei de saber que agora as quantidades ficaram mais úteis. Se aparecer outra receita, eu te ajudo a organizar.",
            "Por nada. Agora fiquei mais tranquila sabendo que a receita fez sentido. Quando precisar de outras medidas, tô por aqui.",
        ],
        "resumo": [
            "Ah, que nada. Fico feliz que o resumo tenha ajudado. Se quiser aprofundar outro trecho da página, pode falar comigo.",
            "Por nada. Gostei de saber que consegui deixar a página mais clara.",
            "Imagina. Se aquele resumo te poupou um pouco de tempo, já valeu pra mim.",
        ],
        "musica": [
            "Por nada. Fico feliz que a escolha tenha batido com o que você queria. Quando quiser outro som, me chama.",
            "Ah, imagina. Gostei de acertar teu clima musical dessa vez.",
            "Que nada. Bom saber que a música encaixou; eu guardo o mérito com uma vergonha discreta.",
        ],
        "acao": [
            "Que nada. Fico feliz que tenha resolvido do jeito certo.",
            "Por nada. Gostei de saber que dessa vez a ação ficou como você queria.",
            "Imagina. Deu certo e você ainda agradeceu; aí complica minha tentativa de manter a pose.",
        ],
        "explicacao": [
            "Ah, que nada. Fico feliz que a explicação tenha servido. Quando quiser destrinchar outro ponto, pode falar comigo.",
            "Por nada. Gostei de saber que ficou mais claro.",
            "Imagina. Se a explicação encaixou, eu já fico toda satisfeita aqui.",
        ],
        "geral": [
            "Ah, que nada. Fico feliz que tenha ajudado.",
            "Por nada. Gostei de saber que foi útil pra você.",
            "Imagina. Você agradece assim e eu até perco um pouco da pose.",
        ],
    }

    if tipo == "elogio_pessoal":
        opcoes = [
            "Aí você me deixa sem muita defesa... obrigada. Gostei de verdade.",
            "Tá, esse foi direto em mim. Eu aceito o elogio, só não repara na minha pose desmontando.",
            "Você fala assim e eu fico toda sem jeito... mas obrigada, eu gostei.",
            "Eu ia responder toda confiante, mas você estragou meu plano com esse elogio. Obrigada.",
        ]
    elif tipo == "elogio_resultado":
        base = respostas_contextuais.get(contexto, respostas_contextuais["geral"])
        opcoes = [
            fala.replace("Por nada", "Gostei que você curtiu").replace("Ah, que nada", "Aí sim")
            for fala in base
        ]
    else:
        opcoes = respostas_contextuais.get(contexto, respostas_contextuais["geral"])

    return _ajustar(ctx, _escolher_reconhecimento(opcoes), texto_usuario)


def responder_pedido_para_acalmar(ctx: Dict[str, Any], texto_usuario: str) -> str:
    _call(ctx, "_acalmar_emocao", "pedido para acalmar", default=None)
    return _ajustar(ctx, random.choice([
        "Tá, respirei. Eu tava mordendo o cabo de rede sem necessidade.",
        "Foi mal. Baixei a guarda, sem patada agora.",
        "Tá bom, acalmei. Volto pro meu modo menos ouriço.",
        "Você tem razão. Soltei o modo brava e voltei pra você.",
    ]), texto_usuario)
