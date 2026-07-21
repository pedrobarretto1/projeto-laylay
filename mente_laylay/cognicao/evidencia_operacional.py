"""Guardas semânticas compartilhadas para candidatos de ação prática."""

from __future__ import annotations

import re
import unicodedata


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"[^a-z0-9\s?]", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def autoriza_candidato_iot_direto(texto: str, *, modalidade: str = "") -> bool:
    """Autoriza o detector IoT antes do portão casual somente em pedidos reais.

    O detector especializado ainda precisa reconhecer dispositivo, propriedade e
    parâmetros. Esta função decide apenas se a forma comunicativa permite ação.
    """
    t = _normalizar(texto)
    t = re.sub(
        r"^(?:por favor\s+)?(?:voce\s+)?(?:pode|poderia|consegue|conseguiria)\s+",
        "",
        t,
        count=1,
    ).strip()
    if not t or str(modalidade or "").casefold() == "deliberativo":
        return False

    if re.search(
        r"^(?:nao|nunca|jamais)\b|"
        r"\b(?:nao|nunca|jamais)\s+(?:deixa|deixe|deixar|coloca|muda|ajusta|define|bota|poe|torna)\b",
        t,
    ):
        return False
    if re.search(
        r"^(?:se|caso|quando)\s+(?:eu|voce|a gente)\b|"
        r"^(?:como|por que|porque|o que acontece se)\b|"
        r"\b(?:acho|imagino|suponho|talvez|seria bom|seria legal|quem sabe)\b|"
        r"\b(?:voce acha|o que voce acha|eu gosto de|eu costumo|eu queria)\b",
        t,
    ):
        return False

    # A moldura de cortesia já foi removida por ``normalizar_pedido_natural``.
    # Exigimos que o ato restante comece como pedido, não como comentário que
    # apenas contém um verbo operacional no meio.
    return bool(re.match(
        r"^(?:deixa|deixe|deixar|coloca|coloque|colocar|bota|bote|botar|poe|"
        r"muda|mude|mudar|ajusta|ajuste|ajustar|define|defina|definir|"
        r"torna|torne|tornar|quero)\b",
        t,
    ))


def texto_tem_evidencia_iot_parametro(texto: str) -> bool:
    """Reconhece pedido de propriedade IoT sem conhecer aliases do registro."""
    t = _normalizar(texto)
    if not autoriza_candidato_iot_direto(t):
        return False
    alvo = bool(re.search(
        r"\b(?:lampada|luz|tomada|ventilador|dispositivo|aparelho|iot|ela|ele|isso)\b",
        t,
    ))
    parametro = bool(re.search(
        r"\b(?:cor|brilho|clar[oa]|escur[oa]|pastel|branc[oa]|pret[oa]|cinza|"
        r"marrom|vermelh[oa]|verde|azul|amarel[oa]|rox[oa]|rosa|laranja|"
        r"cian[oa]|violeta|lilas|turquesa|dourad[oa]|magenta|coral|"
        r"\d{1,3}\s*(?:%|por cento))\b",
        t,
    ))
    return alvo and parametro
