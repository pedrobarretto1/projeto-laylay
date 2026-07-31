"""Decisoes leves de conversa musical da Laylay."""

from __future__ import annotations

import random
import re
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

    # Pedido de reprodução sem faixa é uma solicitação incompleta, não uma
    # pesquisa pela faixa literal "uma música". A conversa musical escolhe uma
    # sugestão real e mantém a confirmação/título seguinte como pendência.
    if re.fullmatch(
        r"(?:(?:por favor|lay|laylay)\s+)?"
        r"(?:coloca|coloque|toca|toque|bota|bote|poe|põe|manda)\s+"
        r"(?:(?:uma|alguma)\s+)?(?:musica|música|faixa|som)"
        r"(?:\s+(?:ai|aí|pra mim|para mim))?[.!?]*",
        t,
    ):
        return True

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
        "que tal uma musica", "que tal uma música", "que tal um som",
    ])
    estado = dict(estado_mental or {})
    continuacao_musical = (
        str(estado.get("ultima_intencao") or "").upper() == "MUSIC_OPINION_CHAT"
        and any(p in t for p in [
            "entao me fala", "então me fala", "me fala entao", "me fala então",
            "entao diz", "então diz", "me diz uma", "fala uma", "entao manda", "então manda",
        ])
    )
    ultima_resposta = _normalizar(str(estado.get("ultima_resposta") or ""), normalizar_texto)
    estilo_curto = any(p in t for p in [
        "romant", "calm", "leve", "pesad", "rock", "metal", "alternativ",
        "indie", "anime", "madrugada", "musica", "música", "geek", "nerd",
        "gamer", "jogo", "game", "eletronic", "synth",
    ]) and len(t.split()) <= 5
    pergunta_estilo_anterior = any(p in ultima_resposta for p in [
            "qual clima", "qual estilo", "voce quer", "você quer", "me da um estilo",
            "me dá um estilo", "artista", "quer que eu puxe", "posso escolher", "qual vibe",
            "que vibe", "qual energia",
        ])
    contexto_musical_recente = (
        any(p in ultima_resposta for p in ["musica", "música", "som", "faixa", "playlist"])
        or str(estado.get("ultima_habilidade") or "").lower() == "musica"
        or str(estado.get("ultima_intencao") or "").upper() in {"MUSIC_OPINION_CHAT", "MUSIC_SEARCH"}
    )
    pergunta_musical_anterior = pergunta_estilo_anterior and contexto_musical_recente
    assunto_musical = any(p in t for p in [
        "musica", "música", "som", "faixa", "canção", "cancao", "ouvir", "tocar",
    ])
    return bool((pede_escolha and assunto_musical) or continuacao_musical or (estilo_curto and pergunta_musical_anterior))


def sugestao_musical_nova_conversacional(
    texto: str = "",
    *,
    normalizar_texto: Callable[[str], str] | None = None,
    estado_mental: Dict[str, Any] | None = None,
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
        "geek": [
            "The Living Tombstone - My Ordinary Life",
            "DAGames - Build Our Machine",
            "CG5 - I See a Dreamer",
            "JT Music - Join Us For A Bite",
        ],
        "madrugada": [
            "Boogarins - Infinu",
            "Terno Rei - Solidão de Volta",
            "Tagua Tagua - Inteiro Metade",
            "Glue Trip - Elbow Pain",
        ],
    }

    # Um artista explicitamente pedido tem precedencia sobre o clima. Antes,
    # "me recomenda uma musica do Rubel" caia no sorteio generico e podia
    # devolver Scalene, quebrando o proprio assunto da conversa.
    candidatos = [faixa for faixas in base.values() for faixa in faixas]
    preferencias = dict((estado_mental or {}).get("preferencias_musicais") or {})
    artistas_rejeitados = {
        _normalizar(artista, normalizar_texto)
        for artista, peso in dict(preferencias.get("artistas") or {}).items()
        if int(peso or 0) < 0
    }
    faixas_rejeitadas = {
        _normalizar(faixa, normalizar_texto)
        for faixa, peso in dict(preferencias.get("faixas") or {}).items()
        if int(peso or 0) < 0
    }
    candidatos_validos = [
        faixa for faixa in candidatos
        if _normalizar(faixa.split(" - ", 1)[0], normalizar_texto) not in artistas_rejeitados
        and _normalizar(faixa, normalizar_texto) not in faixas_rejeitadas
    ]
    if candidatos_validos:
        candidatos = candidatos_validos
    pedido_artista = None
    for faixa in candidatos:
        artista = faixa.split(" - ", 1)[0].strip()
        artista_norm = _normalizar(artista, normalizar_texto)
        if any(marcador in f" {t} " for marcador in (
            f" do {artista_norm} ",
            f" da {artista_norm} ",
            f" de {artista_norm} ",
            f" pelo {artista_norm} ",
            f" pela {artista_norm} ",
        )):
            pedido_artista = artista_norm
            break
    if pedido_artista:
        do_artista = [
            faixa for faixa in candidatos
            if _normalizar(faixa.split(" - ", 1)[0], normalizar_texto) == pedido_artista
        ]
        if do_artista:
            return random.choice(do_artista)

    if any(p in t for p in ["pesad", "metal", "hard", "porrada"]):
        chave = "pesado"
    elif any(p in t for p in ["alternativ", "diferente", "estranh", "indie"]):
        chave = "alternativo"
    elif any(p in t for p in ["calm", "leve", "dormir", "relax", "romant"]):
        chave = "calmo"
    elif any(p in t for p in ["geek", "nerd", "gamer", "video game", "jogo"]):
        chave = "geek"
    elif any(p in t for p in ["anime", "jap", "opening", "ost"]):
        chave = "anime"
    elif any(p in t for p in ["madrugada", "noite", "brisa"]):
        chave = "madrugada"
    elif "rock" in t:
        chave = "rock"
    else:
        chave = random.choice(list(base.keys()))
    opcoes_chave = [faixa for faixa in (base.get(chave) or base["alternativo"]) if faixa in candidatos]
    return random.choice(opcoes_chave or candidatos or base["alternativo"])
