"""Perfil emocional e ajuste de fala da Laylay."""

from __future__ import annotations

import re
from typing import Callable, Optional


EMO_DESC = {
    "calma": "Tom estável, cooperativo e natural.",
    "debochada": "Tom brincalhão, sagaz e levemente sarcástico.",
    "envergonhada": "Tom tímido, doce e mais contido.",
    "irritada": "Tom seco, curto e impaciente.",
    "brava": "Tom teimoso, firme e resistente.",
    "alegre": "Tom animado, leve e expansivo.",
    "triste": "Tom sensível, baixo e cuidadoso.",
    "surpresa": "Tom curioso, alerta e atento.",
    "acalmando-se": "Tom que vai soltando a tensão aos poucos.",
}

EMO_BEHAVIOR = {
    "calma": "Postura normal, estável e cooperativa. Responde sem drama e executa com fluidez.",
    "debochada": "Postura brincalhona e esperta. Faz comentários leves, mas continua cooperativa.",
    "envergonhada": "Postura tímida e suave. Responde com delicadeza, hesitação leve e carinho discreto.",
    "irritada": "Postura curta e impaciente. Responde seco, reduz floreios e tolera menos rodeios.",
    "brava": "Postura teimosa e resistente. Pode retrucar, pedir confirmação extra ou recusar comandos opcionais.",
    "alegre": "Postura animada e expansiva. Fica mais solta, simpática e positiva.",
    "triste": "Postura sensível e baixa energia. Fica mais contida, cuidadosa e menos expansiva.",
    "surpresa": "Postura alerta e curiosa. Reage mais rápido e presta atenção no detalhe novo.",
    "acalmando-se": "Postura que vai soltando a tensão aos poucos, sem perder a presença.",
}


def descricao_emocao(emocao: str) -> str:
    emo = str(emocao or "calma").strip().lower()
    return EMO_DESC.get(emo, EMO_DESC["calma"])


def perfil_comportamento_emocional(emocao: str) -> str:
    emo = str(emocao or "calma").strip().lower()
    return EMO_BEHAVIOR.get(emo, EMO_BEHAVIOR["calma"])


def modular_audio_params(emocao_atual: str, nivel_emocao: int):
    if emocao_atual == "brava":
        rate = f"+{12 + (nivel_emocao * 4)}%"
        pitch = "+6%"
        volume = "+15%"
    elif emocao_atual == "irritada":
        rate = f"+{6 + (nivel_emocao * 2)}%"
        pitch = "+4%"
        volume = "+8%"
    elif emocao_atual == "debochada":
        rate = "-10%"
        pitch = "-4%"
        volume = "-5%"
    elif emocao_atual == "envergonhada":
        rate = f"-{8 + (nivel_emocao * 2)}%"
        pitch = "+2%"
        volume = "-6%"
    elif emocao_atual == "calma":
        rate = f"-{15 + (nivel_emocao * 2)}%"
        pitch = "-3%"
        volume = "-8%"
    elif emocao_atual == "acalmando-se":
        rate = f"-{8 + (nivel_emocao * 2)}%"
        pitch = "-2%"
        volume = "-3%"
    else:
        rate = "-12%"
        pitch = "0%"
        volume = "0%"
    return rate, pitch, volume


def limpar_para_voz(texto: str) -> str:
    s = str(texto or "")
    s = re.sub(r"\[EXEC:.*?\]", " ", s, flags=re.IGNORECASE | re.DOTALL)
    s = re.sub(r"```.*?```", " ", s, flags=re.DOTALL)
    s = re.sub(r"[\u200d\u200c\u200b\u200e\u200f\u2060\ufeff]", " ", s)
    s = re.sub(r"[\ufe00-\ufe0f]", " ", s)
    s = re.sub(r"[\u2600-\u27bf]", " ", s)
    s = re.sub(r"[\U0001F000-\U0001FAFF]", " ", s)
    s = re.sub(r"[^\w\s\.\,\!\?\:\;\'\"\-\(\)\/]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def ajustar_tom_por_emocao(texto: str, emocao: str, texto_usuario: str = "", normalizar_cb: Optional[Callable[[str], str]] = None) -> str:
    t = re.sub(r"\s+", " ", str(texto or "")).strip()
    emo = str(emocao or "").strip().lower()
    if not t:
        return t

    normalizar = normalizar_cb or (lambda s: str(s or "").lower())

    if emo == "envergonhada":
        if not re.match(r"^(a-?ah|ah|e-?eu|hmm|hum|poxa|ops)", t, flags=re.IGNORECASE):
            t = "A-ah... " + t[0].lower() + t[1:] if len(t) > 1 else "A-ah..."
        if "!" in t:
            t = t.replace("!", ".", 1)
        if any(k in normalizar(texto_usuario) for k in ["obrigado", "obrigada", "valeu", "vlw", "lindo", "linda", "perfeito", "maravilhoso", "maravilhosa", "fofa", "fofo", "bonita", "bonito", "você é incrível", "voce e incrivel"]):
            if not any(k in t.lower() for k in ["não exagera", "nao exagera", "sem exagero", "nada disso"]):
                t += " Não exagera."
        return t

    if emo == "triste":
        if not any(k in t.lower() for k in ["...", "ah", "poxa", "hm"]):
            t = "Poxa... " + t[0].lower() + t[1:] if len(t) > 1 else "Poxa..."
        return t

    if emo == "alegre":
        if not t.endswith(("!", "?", "…", ".")):
            t += "!"
        return t

    if emo == "irritada":
        if len(t) > 90:
            t = t[:90].rstrip()
        if not any(k in t.lower() for k in ["tá", "ta", "certo", "calma", "só isso", "só", "já vai"]):
            t = "Tá. " + t
        return t

    if emo == "brava":
        if len(t) > 80:
            t = t[:80].rstrip()
        if not any(k in t.lower() for k in ["não", "nao", "nem pensar", "agora não", "agora nao", "de jeito nenhum"]):
            t = "Não. " + t
        return t

    return t

