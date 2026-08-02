"""Classificação local e assistida de falas conversacionais curtas.

O módulo não produz a resposta final nem executa comandos. Ele apenas entrega
uma leitura semântica para a fachada de conversa natural.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from mente_laylay.cognicao.interpretacao_social import analisar_ato_social
from mente_laylay.emocoes.leitura_usuario import analisar_intencao_emocional
from mente_laylay.personalidade.base_conversa import _call, _get, _normalizar
from mente_laylay.personalidade.contingencias_conversa import responder_matematica_simples
from mente_laylay.personalidade.leitura_social_conversa import (
    _parece_confirmacao_curta,
    _parece_correcao_conversa,
    parece_elogio_ou_agradecimento_curto,
    parece_pedido_para_acalmar,
    texto_parece_correcao_conversacional,
)


_RECUSA_INICIAL = re.compile(
    r"^\s*(?:precisa\s+n[aã]o|n[aã]o\s+precisa|agora\s+n[aã]o|"
    r"deixa\s+quieto|deixa\s+(?:pra|para)\s+l[aá])\b[\s,;:.!-]*",
    re.IGNORECASE,
)


def recusa_tem_continuacao(texto: str) -> bool:
    """Distingue uma recusa isolada de uma recusa seguida por assunto atual."""
    restante = _RECUSA_INICIAL.sub("", str(texto or ""), count=1).strip()
    if not restante:
        return False
    palavras = re.findall(r"[\wÀ-ÿ]+", restante, flags=re.UNICODE)
    return len(palavras) >= 3


def ha_pendencia_operacional_ativa(ctx: Dict[str, Any]) -> bool:
    """Só considera recusa operacional quando há ação acionável real."""
    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    pendencia = mente.get("pendencia_atual")
    if isinstance(pendencia, dict) and pendencia.get("status") == "ativa":
        dominio = str(pendencia.get("dominio") or "").strip().casefold()
        intencao = str(pendencia.get("intencao") or "").strip()
        if intencao or dominio in {
            "arquivo", "iot", "musica", "navegacao", "sistema", "agenda",
        }:
            return True
    oferta = mente.get("oferta_pendente")
    return bool(isinstance(oferta, dict) and str(oferta.get("intent") or "").strip())


def analisar_conversa_curta_ia(ctx: Dict[str, Any], texto_usuario: str) -> dict:
    texto = str(texto_usuario or "").strip()
    if not texto:
        return {}
    try:
        palavras = texto.split()
        retrato_mente = ""
        if len(texto) > 40 or len(palavras) > 6:
            retrato_mente = str(_call(ctx, "_resumo_mente_integrada_para_prompt", texto, default="") or "")
        mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
        payload = {
            "texto": texto,
            "emocao": _get(ctx, "current_emotion", "calma"),
            "ultima_habilidade": mente.get("ultima_habilidade", ""),
            "ultimo_alvo": mente.get("ultimo_alvo", ""),
            "ultimo_topico": _get(ctx, "ultimo_topico_conversa", ""),
            "retrato_mente": retrato_mente,
        }
        prompt = (
            "Voce e o nucleo interpretativo da Laylay para conversa curta.\n"
            "Classifique a fala do usuario e devolva SOMENTE um JSON valido com:\n"
            "tipo: (GREETING, WELLBEING, WELLBEING_REPLY, EMOTIONAL_STATE, PLAYFUL_PROTEST, PRAISE, REACTION, SOFT_DECLINE, OPINION, QUESTION, RETAKE_TOPIC, THEME_CHAT, CONTINUE, NONE)\n"
            "confianca: numero de 0 a 1\n"
            "Regras:\n"
            "- Use interpretacao do contexto, nao palavras-chave secas.\n"
            "- Se houver qualquer sinal humano de conversa, escolha o tipo conversacional mais provavel em vez de NONE.\n"
            "- Se o usuario pedir opiniao, gosto, leitura pessoal ou recomendacao conceitual, prefira OPINION.\n"
            "- Se a pergunta puder ser respondida com uma hipotese honesta, nao use QUESTION so por cautela.\n"
            "- Use NONE so para ruido real, texto vazio ou algo claramente impossivel de interpretar.\n"
            "- Nunca invente comando pratico aqui.\n"
        )
        raw = _call(
            ctx,
            "enviar_mensagem",
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            _com_tools=False,
            max_tokens=90,
            modo_rapido=True,
            default="",
        )
        js = _call(ctx, "_extrair_json_da_ia", raw, default="")
        if not js:
            return {}
        data = json.loads(js)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"⚠️ [CONVERSA IA-FIRST] falha ao classificar conversa curta: {exc}")
        return {}


def _parece_protesto_brincalhao(ctx: Dict[str, Any], texto_usuario: str) -> bool:
    t = _normalizar(ctx, texto_usuario)
    if not t:
        return False
    sinais_diretos = (
        "vacilo", "sacanagem", "ai nao lay", "aí não lay", "olha ela",
        "me chamou de", "falando que eu sou", "falando que sou",
        "ja ta me julgando", "já tá me julgando", "me respeita",
    )
    if any(sinal in t for sinal in sinais_diretos):
        return True
    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    anterior = _normalizar(ctx, str(mente.get("ultima_resposta") or ""))
    provocacao_anterior = bool(anterior and any(s in anterior for s in (
        "celular", "memoria", "memória", "esqueceu", "dormiu", "preguica", "preguiça",
        "viciado", "nao vai", "não vai", "te peguei", "desafio",
    )))
    reacao_leve = any(s in t for s in (
        "assim voce me quebra", "assim você me quebra", "qual foi", "aí é fogo", "ai e fogo",
    ))
    return provocacao_anterior and reacao_leve


def classificar_conversa_curta_local(ctx: Dict[str, Any], texto_usuario: str) -> dict:
    texto = str(texto_usuario or "").strip()
    t = _normalizar(ctx, texto)
    if not t:
        return {}
    if texto_parece_correcao_conversacional(texto):
        return {}

    mente_turno = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    turno = dict(mente_turno.get("turno_atual") or {})
    segmentos = [item for item in list(turno.get("segmentos") or []) if isinstance(item, dict)]
    if str(turno.get("modalidade_geral") or "") == "misto" or len(segmentos) > 1:
        return {}

    leitura_semantica = dict(turno.get("leitura_semantica") or {})
    if leitura_semantica.get("uso_conversacional"):
        atos = [item for item in list(leitura_semantica.get("atos") or []) if isinstance(item, dict)]
        if len(atos) != 1:
            return {}
        tipo_ato = str(atos[0].get("tipo") or "").lower()
        mapa_semantico = {
            "saudacao": "GREETING", "pergunta": "QUESTION",
            "pergunta_opiniao": "OPINION", "pergunta_capacidade": "CAPABILITY_CHECK",
            "resposta_social": "WELLBEING_REPLY", "reacao": "REACTION",
            "agradecimento": "PRAISE", "recusa": "SOFT_DECLINE",
        }
        tipo_curto = mapa_semantico.get(tipo_ato)
        if tipo_curto == "SOFT_DECLINE" and (
            recusa_tem_continuacao(t) or not ha_pendencia_operacional_ativa(ctx)
        ):
            return {}
        if tipo_curto:
            return {
                "tipo": tipo_curto,
                "confianca": float(atos[0].get("confianca") or leitura_semantica.get("confianca") or 0.0),
                "origem": "leitura_semantica",
            }
        return {}

    if parece_elogio_ou_agradecimento_curto(ctx, texto):
        return {"tipo": "PRAISE", "confianca": 0.95}
    if re.fullmatch(r"(?:que bom|ainda bem|fico feliz)(?: lay| laylay)?", t):
        return {"tipo": "POSITIVE_ACK", "confianca": 0.96}
    if re.search(r"\b(?:tem certeza|entao|então)\b.*\b(?:voce|você)\b.*\b(?:consegue|pode|tem capacidade)\b", t):
        return {"tipo": "CAPABILITY_CHECK", "confianca": 0.96}
    if parece_pedido_para_acalmar(ctx, texto):
        return {"tipo": "CALM_DOWN", "confianca": 0.95}
    if re.search(
        r"\b(?:o que (?:voce|você) anda fazendo(?: de bom)?|o que (?:voce|você) tem feito|"
        r"quer(?: conversar| falar) sobre o que|tem (?:algum )?assunto (?:pra|para) (?:a gente|nos) conversar|"
        r"sobre o que (?:a gente|nos) (?:conversa|conversamos))\b", t,
    ):
        return {"tipo": "PERSONAL_CHAT", "confianca": 0.98}
    if re.search(
        r"\b(?:quero|queria)\s+(?:so|só|apenas)\s+(?:bater\s+um\s+papo|conversar|falar)\s+(?:com\s+voce|com\s+você|contigo)\b",
        t,
    ):
        return {"tipo": "CHAT_ONLY", "confianca": 0.98}
    if responder_matematica_simples(ctx, texto):
        return {"tipo": "MATH", "confianca": 0.98}
    if _parece_correcao_conversa(t):
        return {"tipo": "CONTINUE", "confianca": 0.93}
    if _parece_protesto_brincalhao(ctx, texto):
        return {"tipo": "PLAYFUL_PROTEST", "confianca": 0.96}
    if re.search(
        r"\b(?:voce|você)\s+(?:viu|soube|conhece)|\b(?:ja\s+|já\s+)?ouviu\s+falar\b|\bficou\s+sabendo\b",
        t,
    ):
        return {}
    leitura_emocional = analisar_intencao_emocional(
        texto, normalizar_texto=lambda valor: _normalizar(ctx, valor),
    )
    if leitura_emocional:
        _call(ctx, "_registrar_leitura_emocional_usuario", leitura_emocional)
        return {"tipo": "EMOTIONAL_STATE", "confianca": 0.96, "leitura_emocional": leitura_emocional}
    leitura_social = analisar_ato_social(t, mente=mente_turno)
    tipo_social = str(leitura_social.get("tipo") or "")
    if tipo_social in {"WELLBEING", "WELLBEING_REPLY"}:
        return leitura_social
    if tipo_social in {"COMPOSTO", "AMBIGUO"}:
        return {}
    if re.fullmatch(r"(?:oi|ola|olá|e ai|e aí|salve|bom dia|boa tarde|boa noite)(?: lay| laylay)?", t):
        return {"tipo": "GREETING", "confianca": 0.94}
    if (
        any(p in t for p in ["precisa nao", "nao precisa", "agora nao", "deixa quieto", "deixa pra la", "deixa para la"])
        and not recusa_tem_continuacao(t) and ha_pendencia_operacional_ativa(ctx)
    ):
        return {"tipo": "SOFT_DECLINE", "confianca": 0.92}
    if any(p in t for p in [
        "o que voce acha", "o que você acha", "o que voce sacha", "voce sacha", "voce acha", "você acha",
        "qual sua opiniao", "qual sua opinião", "me da sua opiniao", "me dá sua opinião",
        "voce gosta", "você gosta", "voce curte", "você curte", "qual voce prefere", "qual você prefere",
        "me recomenda", "me indica", "voce concorda", "você concorda", "concorda comigo",
        "voce discorda", "você discorda", "discorda de mim",
    ]):
        return {"tipo": "OPINION", "confianca": 0.88}
    if any(p in t for p in ["quem e", "quem é", "o que e", "o que é", "como funciona", "me explica", "fala sobre", "me fala sobre", "me fala de", "fala de"]):
        return {"tipo": "QUESTION", "confianca": 0.9}
    if "?" in texto and len(t.split()) <= 8:
        if any(p in t for p in ["como assim", "ue", "uai", "oxi", "o que", "que isso"]):
            return {"tipo": "QUESTION", "confianca": 0.88}
        return {"tipo": "QUESTION", "confianca": 0.78}
    if len(t.split()) <= 6 and any(p in t for p in ["pode explicar", "explica melhor", "explica isso", "me explica"]):
        return {"tipo": "QUESTION", "confianca": 0.86}
    if re.fullmatch(r"^(ue|ué|uai|oxi|ata|ah ta|ah tá|ah+ bom|a+ bom|tendi|entendi|hmm|hm+|hum+|caramba|nossa)$", t):
        return {"tipo": "REACTION", "confianca": 0.91}
    if _parece_confirmacao_curta(t):
        return {"tipo": "CONTINUE", "confianca": 0.84}
    if re.fullmatch(r"^(eu to|eu estou)\s+.+$", t):
        return {"tipo": "CONTINUE", "confianca": 0.82}
    if re.fullmatch(r"^(entao|então)\s+.+$", t):
        return {"tipo": "CONTINUE", "confianca": 0.74}
    if any(p in t for p in ["faz o l", "to indo", "indo", "na luta", "mais ou menos", "seguindo", "levando", "sobrevivendo"]):
        return {"tipo": "CONTINUE", "confianca": 0.72}
    parece_nav = bool(_call(ctx, "_texto_parece_navegacao_ou_janela_ia", t, default=False))
    if len(t.split()) <= 5 and not parece_nav:
        return {"tipo": "CONTINUE", "confianca": 0.60}
    return {}


def deve_classificar_conversa_curta_com_ia(ctx: Dict[str, Any], texto_usuario: str) -> bool:
    texto = str(texto_usuario or "").strip()
    if not texto:
        return False
    t = _normalizar(ctx, texto)
    if len(t.split()) > 8:
        return False
    if bool(_call(ctx, "_texto_parece_navegacao_ou_janela_ia", t, default=False)):
        return False
    sinais_conversa = [
        "?", "como", "porque", "por que", "pq", "acha", "opini", "gosta",
        "curte", "prefere", "hmm", "hm", "ue", "ué", "uai", "oxi",
        "tendi", "entendi", "ata", "kkk", "haha",
    ]
    return any(s in texto.lower() or s in t for s in sinais_conversa)

