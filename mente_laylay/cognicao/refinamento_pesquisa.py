"""Refina pedidos de pesquisa sem confundir a frase de comando com a consulta.

O módulo não acessa a internet. Ele transforma intenção, contexto e restrições
em uma consulta útil para o especialista que realmente fará a busca.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any, Mapping, MutableMapping


def _normalizar(texto: Any) -> str:
    bruto = unicodedata.normalize("NFD", str(texto or "").casefold())
    bruto = "".join(ch for ch in bruto if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", bruto).strip(" .,!?:;\"'")


_CURADORIA_CONTEXTO = {
    "minecraft": (
        "C418 - Sweden Minecraft Volume Alpha",
        "C418 - Wet Hands Minecraft Volume Alpha",
        "C418 - Subwoofer Lullaby Minecraft Volume Alpha",
        "C418 - Mice on Venus Minecraft Volume Alpha",
    ),
    "rpg": (
        "Jeremy Soule - Secunda Skyrim soundtrack",
        "Marcin Przybylowicz - The Fields of Ard Skellig",
        "Yasunori Mitsuda - Corridors of Time",
    ),
    "competitivo": (
        "Carpenter Brut - Turbo Killer official",
        "The Prodigy - Breathe official video",
        "Pendulum - Witchcraft official video",
    ),
    "estudo": (
        "Tycho - Awake official audio",
        "Nujabes - Aruarian Dance",
        "Khruangbin - Friday Morning official audio",
    ),
    "academia": (
        "Royal Blood - Out of the Black official video",
        "Linkin Park - Given Up official audio",
        "Queens of the Stone Age - No One Knows official video",
    ),
    "relaxar": (
        "Men I Trust - Show Me How official video",
        "Cigarettes After Sex - Apocalypse audio",
        "Khruangbin - Friday Morning official audio",
    ),
}

_CONSULTAS_LONGAS = {
    "minecraft": "C418 Minecraft relaxing music mix 1 hour",
    "rpg": "fantasy RPG ambient soundtrack mix 1 hour",
    "competitivo": "high energy gaming music mix 1 hour",
    "estudo": "instrumental focus music mix 1 hour no lyrics",
    "academia": "workout rock music mix 1 hour",
    "relaxar": "calm ambient music mix 1 hour",
}

_CURADORIA_ESTILO = {
    "pesada": (
        "Sepultura - Roots Bloody Roots official video",
        "Slipknot - Duality official video",
        "System Of A Down - B.Y.O.B. official video",
        "Linkin Park - Given Up official audio",
        "Bring Me The Horizon - Shadow Moses official video",
    ),
    "alternativa": (
        "Tame Impala - The Less I Know The Better official video",
        "Boogarins - Infinu official audio",
        "Tagua Tagua - Inteiro Metade official video",
    ),
    "calma": (
        "Men I Trust - Show Me How official video",
        "Cigarettes After Sex - Apocalypse audio",
        "Khruangbin - Friday Morning official audio",
    ),
    "animada": (
        "Paramore - Still Into You official video",
        "The Strokes - Reptilia official video",
        "Franz Ferdinand - Take Me Out official video",
    ),
}

_ALIASES_ESTILO = {
    "pesada": ("pesada", "pesado", "som pesado", "mais pesado", "heavy", "metal pesado", "rock pesado"),
    "alternativa": ("alternativa", "alternativo", "indie", "diferente"),
    "calma": ("calma", "calmo", "tranquila", "tranquilo", "relaxante", "suave", "ambient"),
    "animada": ("animada", "animado", "agitada", "agitado", "pra cima", "para cima", "energica"),
}


def _contexto_musical(texto: str, params: Mapping[str, Any]) -> str:
    contexto = _normalizar(
        " ".join(str(params.get(chave) or "") for chave in ("context", "contexto", "game", "jogo", "activity", "atividade"))
        + " " + texto
    )
    if "minecraft" in contexto:
        return "minecraft"
    if re.search(r"\b(?:rpg|path of exile|poe|diablo|baldur|skyrim)\b", contexto):
        return "rpg"
    if re.search(r"\b(?:competitiv|ranked|fps|fragpunk|valorant|cs2|counter strike|overwatch)\b", contexto):
        return "competitivo"
    if re.search(r"\b(?:estud|foco|concentr|trabalh|program|codigo|código)\b", contexto):
        return "estudo"
    if re.search(r"\b(?:academia|treino|malhar|exercicio|exercício)\b", contexto):
        return "academia"
    if re.search(r"\b(?:relax|descans|dormir|sono|calm)\b", contexto):
        return "relaxar"
    return ""


def _pedido_longo(texto: str, params: Mapping[str, Any]) -> bool:
    combinado = _normalizar(
        texto + " " + " ".join(str(params.get(k) or "") for k in ("duration", "duracao", "format", "formato"))
    )
    return bool(re.search(
        r"\b(?:mix|playlist|selecao|coletanea|album completo|full album|"
        r"varias musicas|musicas para|1 ?h|uma hora|horas)\b",
        combinado,
    ))


def _parece_titulo_explicito(query: str, texto_original: str) -> bool:
    q = _normalizar(query)
    if not q:
        return False
    molduras_genericas = (
        "musica boa", "uma musica", "alguma musica", "musica para", "musica pra",
        "som para", "som pra", "algo para ouvir", "trilha para", "playlist para",
    )
    if any(m in q for m in molduras_genericas):
        return False
    if re.search(r"\b(?:para|pra)\s+(?:jogar|estudar|trabalhar|dormir|treinar|relaxar)\b", q):
        return False
    termos_genericos = {
        _normalizar(termo)
        for termos in _ALIASES_ESTILO.values()
        for termo in termos
    } | {
        "rock", "metal", "pop", "rap", "trap", "funk", "jazz", "blues",
        "eletronica", "eletronico", "lofi", "lo-fi", "ambient", "classica",
    }
    if q in termos_genericos:
        return False
    # Consultas curtas que não descrevem gênero, humor ou ocasião normalmente
    # são títulos/artistas escolhidos pelo usuário e nunca devem ser curadas.
    return len(q.split()) <= 12


def refinar_consulta_musical(
    query: str,
    texto_original: str = "",
    params: Mapping[str, Any] | None = None,
    *,
    cursores: MutableMapping[str, int] | None = None,
) -> dict[str, str]:
    """Resolve um pedido musical em uma faixa ou seleção pesquisável."""
    dados = dict(params or {})
    normalizada = _normalizar(query or texto_original)
    texto = _normalizar(f"{query} {texto_original}")
    if not normalizada:
        return {"query": "", "origem": "vazia", "tipo_resultado": ""}
    if _parece_titulo_explicito(normalizada, texto_original):
        return {"query": str(query or normalizada).strip(), "origem": "explicita", "tipo_resultado": "faixa"}

    contexto = _contexto_musical(texto, dados)
    if contexto:
        if _pedido_longo(texto, dados):
            return {
                "query": _CONSULTAS_LONGAS[contexto],
                "origem": "contexto_curado",
                "contexto": contexto,
                "tipo_resultado": "selecao_longa",
            }
        opcoes = _CURADORIA_CONTEXTO[contexto]
        chave = f"contexto:{contexto}"
        indice = int((cursores or {}).get(chave, 0)) % len(opcoes)
        if cursores is not None:
            cursores[chave] = indice + 1
        return {
            "query": opcoes[indice],
            "origem": "contexto_curado",
            "contexto": contexto,
            "tipo_resultado": "faixa",
        }

    combinado = _normalizar(
        texto + " " + str(dados.get("genre") or "") + " " + str(dados.get("mood") or "")
    )
    estilo = next(
        (nome for nome, termos in _ALIASES_ESTILO.items() if any(_normalizar(termo) in combinado for termo in termos)),
        "",
    )
    generica = any(m in normalizada for m in (
        "musica", "som", "faixa", "boa", "alguma", "uma ", "para ", "pra ",
    )) or normalizada in {termo for termos in _ALIASES_ESTILO.values() for termo in termos}
    if estilo and generica:
        if _pedido_longo(texto, dados):
            return {
                "query": f"{estilo} music mix 1 hour",
                "origem": "estilo_curado",
                "estilo": estilo,
                "tipo_resultado": "selecao_longa",
            }
        opcoes = _CURADORIA_ESTILO[estilo]
        chave = f"estilo:{estilo}"
        indice = int((cursores or {}).get(chave, 0)) % len(opcoes)
        if cursores is not None:
            cursores[chave] = indice + 1
        return {
            "query": opcoes[indice],
            "origem": "estilo_curado",
            "estilo": estilo,
            "tipo_resultado": "faixa",
        }
    return {"query": normalizada, "origem": "nao_resolvida", "tipo_resultado": "busca"}


def refinar_consulta_web(
    query: str,
    texto_original: str = "",
    params: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Remove a moldura operacional e preserva o assunto real da pesquisa."""
    dados = dict(params or {})
    bruto = str(query or texto_original or "").strip()
    if re.match(r"^https?://", bruto, flags=re.IGNORECASE):
        return {"query": bruto, "origem": "url_explicita"}
    consulta = re.sub(
        r"^(?:(?:lay|laylay)\s*,?\s*)?(?:pesquisa|pesquise|procura|procure|busca|busque|"
        r"veja|descubra|me mostra|me mostre|quero saber)\s+(?:na internet\s+|no google\s+|sobre\s+|por\s+)?",
        "",
        bruto,
        flags=re.IGNORECASE,
    )
    consulta = re.sub(r"\s+(?:na internet|no google)\s*$", "", consulta, flags=re.IGNORECASE)
    consulta = re.sub(r"\s+", " ", consulta).strip(" .,!?:;")
    tema = str(dados.get("topic") or dados.get("tema") or "").strip()
    if tema and len(consulta.split()) <= 2:
        consulta = tema
    if bool(dados.get("current") or dados.get("atual")) and not re.search(r"\b20\d{2}\b", consulta):
        consulta = f"{consulta} {datetime.now().year}"
    return {"query": consulta or bruto, "origem": "consulta_refinada"}
