"""Decisoes leves de conversa musical da Laylay."""

from __future__ import annotations

import random
from typing import Any, Callable, Dict


def _normalizar(texto: str, normalizar_texto: Callable[[str], str] | None = None) -> str:
    if callable(normalizar_texto):
        try:
            return str(normalizar_texto(texto) or "").strip()
        except Exception:
            pass
    return str(texto or "").strip().lower()


def texto_pede_direcao_musical_generica(
    texto: str,
    *,
    estado_mental: Dict[str, Any] | None = None,
    normalizar_texto: Callable[[str], str] | None = None,
) -> bool:
    """Detecta pedido conversacional de sugestao musical sem virar comando tecnico."""
    t = _normalizar(texto, normalizar_texto)
    if not t:
        return False

    if any(p in t for p in [
        "nao tenho ouvido antes", "não tenho ouvido antes",
        "nao ouvi antes", "não ouvi antes",
        "uma que nao ouvi", "uma que não ouvi",
        "uma nova", "musica nova", "música nova",
    ]):
        estado = dict(estado_mental or {})
        if str(estado.get("ultima_habilidade") or "").lower() == "musica":
            return True

    pede_escolha = any(p in t for p in [
        "recomenda", "recomendacao", "recomendação", "me indica", "indica uma",
        "sugere", "sugestao", "sugestão", "escolhe uma", "escolha uma",
        "me lista", "me liste", "lista musicas", "liste musicas",
        "me fale uma musica", "me fala uma musica", "me diga uma musica",
        "qual voce acha", "qual você acha", "voce acha que eu gostaria", "você acha que eu gostaria",
    ])
    estado = dict(estado_mental or {})
    continuacao_musical = (
        str(estado.get("ultima_intencao") or "").upper() == "MUSIC_OPINION_CHAT"
        and any(p in t for p in [
            "entao me fala", "então me fala", "me fala entao", "me fala então",
            "entao diz", "então diz", "me diz uma", "fala uma", "entao manda", "então manda",
        ])
    )
    assunto_musical = any(p in t for p in [
        "musica", "música", "som", "faixa", "canção", "cancao", "ouvir", "tocar",
    ])
    return bool((pede_escolha and assunto_musical) or continuacao_musical)


def sugestao_musical_nova_conversacional(
    texto: str = "",
    *,
    normalizar_texto: Callable[[str], str] | None = None,
) -> str:
    """Palpite conversacional: nao usa playlists do Pedro e nao executa nada."""
    t = _normalizar(texto, normalizar_texto)
    base = {
        "rock": [
            "Scalene - Surreal",
            "Supercombo - Piloto Automatico",
            "Far From Alaska - Thievery",
            "Vivendo do Ocio - Nostalgia",
        ],
        "pesado": [
            "Black Pantera - Fogo nos Racistas",
            "Project46 - Erro +55",
            "Sepultura - Roots Bloody Roots",
            "Surra - Bom Dia Senhor",
        ],
        "alternativo": [
            "Boogarins - Lucifernandis",
            "Terno Rei - Yoko",
            "Carne Doce - Artemisia",
            "Maglore - Mantra",
        ],
        "calmo": [
            "Tim Bernardes - Recomeçar",
            "Rubel - Quando Bate Aquela Saudade",
            "Cicero - Tempo de Pipa",
            "Ana Frango Eletrico - Electric Fish",
        ],
        "anime": [
            "Eve - Kaikai Kitan",
            "Aimer - Brave Shine",
            "TK from Ling tosite sigure - Unravel",
            "Asian Kung-Fu Generation - Rewrite",
        ],
        "madrugada": [
            "Boogarins - Infinu",
            "Terno Rei - Solidão de Volta",
            "Tagua Tagua - Inteiro Metade",
            "Glue Trip - Elbow Pain",
        ],
    }
    if any(p in t for p in ["pesad", "metal", "hard", "porrada"]):
        chave = "pesado"
    elif any(p in t for p in ["alternativ", "diferente", "estranh", "indie"]):
        chave = "alternativo"
    elif any(p in t for p in ["calm", "leve", "dormir", "relax"]):
        chave = "calmo"
    elif any(p in t for p in ["anime", "jap", "opening", "ost"]):
        chave = "anime"
    elif any(p in t for p in ["madrugada", "noite", "brisa"]):
        chave = "madrugada"
    elif "rock" in t:
        chave = "rock"
    else:
        chave = random.choice(list(base.keys()))
    return random.choice(base.get(chave) or base["alternativo"])
