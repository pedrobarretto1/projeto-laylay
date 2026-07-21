"""Leitura curta da intenção emocional expressa pelo usuário.

O módulo descreve o sinal emocional; ele não muda a emoção da Laylay e não
executa ações. Assim, acolhimento e comandos continuam responsabilidades
separadas dentro da mesma mente compartilhada.
"""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Dict


def analisar_funcao_comunicativa(texto: str) -> Dict[str, Any]:
    """Identifica o papel humano da fala sem decidir comandos."""
    bruto = str(texto or "").strip()
    base = re.sub(r"\s+", " ", bruto.casefold()).strip()
    if not base:
        return {}
    regras = (
        ("encerramento", r"\b(?:era so isso|era só isso|por hoje e so|por hoje é só|ate mais|até mais|falou|depois a gente ve|depois a gente vê)\b", "encerrar o assunto sem retomar contexto antigo"),
        ("correcao", r"^(?:na verdade|nao lay|não lay|eu quis dizer|quis dizer|meu nome n[aã]o|voce (?:ainda )?nao (?:tem|consegue)|você (?:ainda )?não (?:tem|consegue)|ja falei|já falei)\b", "aceitar a correcao e atualizar o entendimento"),
        ("conquista", r"\b(?:consegui|passei|ganhei|venci|tirei nota maxima|tirei nota máxima|deu certo|terminei|fui aprovado|fui aprovada)\b", "reconhecer a conquista antes de perguntar ou aconselhar"),
        ("agradecimento", r"\b(?:obrigad[oa]?|brigad[oa]?|valeu|vlw)\b", "reconhecer a ajuda concreta que motivou o agradecimento"),
        ("reacao_positiva", r"^(?:que bom|ainda bem|fico feliz)(?: lay| laylay)?[.!]*$", "receber a reação positiva sem inventar novo estado nem forçar pergunta"),
        ("elogio", r"\b(?:voce e incrivel|você é incrível|voce e maravilhosa|você é maravilhosa|gosto de voce|gosto de você|te adoro|te amo)\b", "receber o elogio como dirigido a Laylay"),
        ("desabafo", r"\b(?:nao aguento|não aguento|to triste|tô triste|to cansad|tô cansad|estou cansad|me sinto|dia horrivel|dia horrível)\b", "acolher antes de oferecer solucao"),
        ("frustracao", r"\b(?:nao foi|não foi|nao funcionou|não funcionou|de novo isso|voce errou|você errou|ja falei|já falei)\b", "reconhecer a frustracao e corrigir sem se defender"),
        ("decepcao", r"\b(?:fiquei decepcionad|esperava mais|que pena|achei que ia|poxa vida)\b", "reconhecer a decepcao antes de explicar"),
        ("inseguranca", r"\b(?:sera que eu consigo|será que eu consigo|nao sei se consigo|não sei se consigo|to com medo|tô com medo)\b", "acolher a inseguranca sem prometer resultado"),
        ("brincadeira", r"\b(?:kkk+|haha+|rsrs+|to brincando|tô brincando|zoeira)\b", "acompanhar a brincadeira sem tratar como fato"),
        ("relato", r"^(?:sabia que|hoje eu|ontem eu|sexta eu|eu fui|eu tive|aconteceu)\b", "reagir ao conteudo contado sem transformar em comando"),
    )
    perfis = {
        "encerramento": ("serenidade", "breve", False),
        "correcao": ("frustracao_possivel", "receptiva", False),
        "conquista": ("alegria_ou_orgulho", "celebratoria", True),
        "agradecimento": ("gratidao", "calorosa", False),
        "reacao_positiva": ("alegria_leve", "breve", False),
        "elogio": ("afeto", "envergonhada", False),
        "desabafo": ("sofrimento", "acolhedora", True),
        "frustracao": ("frustracao", "reparadora", False),
        "decepcao": ("decepcao", "cuidadosa", False),
        "inseguranca": ("inseguranca", "encorajadora", True),
        "brincadeira": ("diversao", "brincalhona", True),
        "relato": ("neutra", "interessada", True),
    }
    for funcao, padrao, objetivo in regras:
        if re.search(padrao, base):
            emocao, postura, permite_pergunta = perfis.get(funcao, ("neutra", "natural", True))
            return {
                "funcao": funcao, "objetivo": objetivo, "emocao_implicita": emocao,
                "postura_esperada": postura, "permite_pergunta": permite_pergunta,
                "confianca": 0.94, "texto": bruto, "ts": time.time(),
            }
    return {
        "funcao": "informacao", "objetivo": "responder ao conteudo atual",
        "emocao_implicita": "neutra", "postura_esperada": "natural",
        "permite_pergunta": True, "confianca": 0.60, "texto": bruto, "ts": time.time(),
    }


def analisar_intencao_emocional(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
) -> Dict[str, Any]:
    bruto = str(texto or "").strip()
    base = normalizar_texto(bruto) if callable(normalizar_texto) else bruto.casefold()
    base = re.sub(r"\s+", " ", str(base or "")).strip()
    if not base:
        return {}

    marcadores_pessoais = (
        r"\b(?:eu\s+)?(?:estou|to|tô|ando|me sinto|fiquei|ando me sentindo)\b",
        r"\b(?:nao|não)\s+aguento\b",
        r"\b(?:dia|tarde|noite|madrugada)\s+(?:chata|chato|arrastada|arrastado)\b",
        r"\b(?:nao tem|não tem|tem nada|nao tenho|não tenho)\s+(?:nada\s+)?(?:pra|para)\s+fazer\b",
    )
    if not any(re.search(padrao, base) for padrao in marcadores_pessoais):
        return {}

    emocoes = (
        ("cansaco", r"\b(?:cansad[oa]|exaust[oa]|esgotad[oa]|sem energia)\b"),
        ("tristeza", r"\b(?:triste|desanimad[oa]|abatid[oa]|pra baixo|mal)\b"),
        ("ansiedade", r"\b(?:ansios[oa]|preocupad[oa]|apreensiv[oa]|nervos[oa])\b"),
        ("irritacao", r"\b(?:irritad[oa]|estressad[oa]|brav[oa]|com raiva|de saco cheio)\b"),
        ("alegria", r"\b(?:feliz|animad[oa]|empolgad[oa]|contente)\b"),
        ("medo", r"\b(?:com medo|assustad[oa]|insegur[oa])\b"),
        ("tedio", r"\b(?:chata|chato|tedio|tédio|entediad[oa]|arrastad[oa])\b"),
        ("tedio", r"\b(?:nao tem|não tem|tem nada|nao tenho|não tenho)\s+(?:nada\s+)?(?:pra|para)\s+fazer\b"),
    )
    emocao = next((nome for nome, padrao in emocoes if re.search(padrao, base)), "")
    if not emocao and re.search(r"\b(?:nao|não)\s+aguento\b", base):
        emocao = "esgotamento"
    if not emocao:
        return {}

    intensidade = 2
    if re.search(r"\b(?:um pouco|meio|meio que|levemente)\b", base):
        intensidade = 1
    if re.search(r"\b(?:muito|demais|pra caramba|para caramba|nao aguento|não aguento|no limite)\b", base):
        intensidade = 3

    alvo = "estado_geral"
    if re.search(r"\b(?:de|com)\s+(?:voce|você|tu|lay|laylay)\b", base):
        alvo = "laylay"
    elif re.search(r"\b(?:disso|disto|dessa|deste|dessa situacao|dessa situação)\b", base):
        alvo = "isso"
    else:
        trecho_alvo = re.search(
            r"\b(?:cansad[oa]|exaust[oa]|esgotad[oa]|irritad[oa]|estressad[oa]|brav[oa]|triste|preocupad[oa])\s+(?:de|com|por causa de)\s+(.+)$",
            base,
        )
        if trecho_alvo:
            alvo = re.split(r"[,.!?]", trecho_alvo.group(1), maxsplit=1)[0].strip()[:120] or alvo

    pedido_implicito = "acolhimento"
    necessidade_acao = False
    if re.search(r"\b(?:quero|preciso)\s+(?:desabafar|conversar|falar)\b", base):
        pedido_implicito = "escuta"
    elif re.search(r"\b(?:me ajuda|me ajude|preciso de ajuda|o que eu faco|o que faço|faz alguma coisa|pode fazer algo)\b", base):
        pedido_implicito = "ajuda"
        necessidade_acao = True

    return {
        "emocao": emocao,
        "intensidade": intensidade,
        "alvo": alvo,
        "pedido_implicito": pedido_implicito,
        "necessidade_acao": necessidade_acao,
        "texto": bruto,
        "ts": time.time(),
    }


def registrar_leitura_emocional(
    estado: Dict[str, Any] | None,
    leitura: Dict[str, Any] | None,
) -> Dict[str, Any]:
    novo = dict(estado or {})
    dados = dict(leitura or {})
    if not dados.get("emocao"):
        return novo
    novo.update(
        {
            "emocao_usuario": str(dados.get("emocao") or ""),
            "emocao_usuario_intensidade": int(dados.get("intensidade") or 1),
            "emocao_usuario_alvo": str(dados.get("alvo") or "estado_geral"),
            "emocao_usuario_pedido_implicito": str(dados.get("pedido_implicito") or "acolhimento"),
            "emocao_usuario_necessidade_acao": bool(dados.get("necessidade_acao")),
            "emocao_usuario_texto": str(dados.get("texto") or ""),
            "emocao_usuario_ts": float(dados.get("ts") or time.time()),
        }
    )
    return novo
