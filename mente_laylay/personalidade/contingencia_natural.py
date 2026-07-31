"""Respostas locais curtas quando a LLM não conclui o turno."""

from __future__ import annotations

import re
from typing import Any, Mapping


def _ultima_observacao_visual(contexto: Any) -> str:
    if not isinstance(contexto, Mapping):
        return ""
    jogo = contexto.get("contexto_jogo_atual")
    fontes = [contexto, jogo] if isinstance(jogo, Mapping) else [contexto]
    for fonte in fontes:
        for chave in ("ultima_observacao", "observacao_visual", "ultima_resposta_visual"):
            valor = re.sub(r"\s+", " ", str(fonte.get(chave) or "")).strip()
            if valor:
                return valor[:700]
    return ""


def _resposta_sobre_visual_recente(texto: str, observacao: str) -> str:
    """Responde a uma avaliação dêitica usando somente evidência já percebida."""
    if not observacao:
        return ""
    avaliacao = bool(re.search(
        r"\b(?:t[aá]|est[aá]|ficou|parece)\b.{0,35}"
        r"\b(?:legal|bonit[ao]|boa|bom|aconchegante|bacana|massa|da hora)\b",
        texto,
        flags=re.IGNORECASE,
    ))
    referencia = bool(re.search(
        r"\b(?:meu|minha|esse|essa|isto|isso|aqui|casinha|casa|constru[cç][aã]o|decora[cç][aã]o)\b",
        texto,
        flags=re.IGNORECASE,
    ))
    if not (avaliacao and referencia):
        return ""

    detalhe = re.search(
        r"\bcom\s+(.+?)(?:[.!?]|$)", observacao, flags=re.IGNORECASE,
    )
    if detalhe:
        evidencia = detalhe.group(1).strip(" ,.;:!?")
        if evidencia:
            return (
                "Tá sim. O que mais me chamou atenção foi "
                f"{evidencia} — ficou bem aconchegante."
            )

    observacao_limpa = re.sub(
        r"^(?:ol[aá](?:\s+s[oó])?|(?:ei|opa),?\s*[^,!]{0,30},?)\s*",
        "",
        observacao,
        flags=re.IGNORECASE,
    ).strip()
    if observacao_limpa:
        observacao_limpa = observacao_limpa[0].lower() + observacao_limpa[1:]
        return f"Tá sim. Pelo que acabei de ver, {observacao_limpa}"
    return ""


def _resposta_social_curta(texto: str) -> str:
    """Conclui atos sociais inequívocos sem depender do modelo generativo."""
    limpo = texto.strip(" .,!?")
    if re.fullmatch(
        r"(?:eu\s+)?(?:"
        r"n[aã]o\s+(?:to|t[oô]|estou)\s+(?:muito\s+)?bem"
        r"|(?:to|t[oô]|estou)\s+(?:muito\s+)?mal"
        r")(?:\s+(?:lay|laylay))?",
        limpo,
        flags=re.IGNORECASE,
    ):
        return "Poxa... quer me contar o que aconteceu? Tô aqui com você."
    if re.fullmatch(
        r"(?:eu\s+)?(?:to|t[oô]|estou)\s+(?:muito\s+)?bem"
        r"(?:\s+sim)?(?:\s+(?:lay|laylay))?",
        limpo,
        flags=re.IGNORECASE,
    ):
        return "Aí sim, bom saber."
    if re.fullmatch(
        r"(?:obrigad[oa]|valeu)(?:\s+(?:lay|laylay))?",
        limpo,
        flags=re.IGNORECASE,
    ):
        return "Imagina. Tô contigo."
    if re.fullmatch(r"(?:k{2,}|h+a+h+a+)(?:\s+.*)?", limpo, flags=re.IGNORECASE):
        return "Kkkkk, tá bom, essa me pegou."
    return ""


def fala_contingencia_natural(
    texto_usuario: Any,
    contexto: Mapping[str, Any] | None = None,
) -> str:
    """Mantém humanidade sem fingir que a resposta da IA foi concluída."""
    bruto = re.sub(r"\s+", " ", str(texto_usuario or "")).strip()
    texto = bruto.casefold()
    if re.fullmatch(
        r"(?:oi|ol[aá]|opa|e a[ií]|bom dia|boa tarde|boa noite)"
        r"(?:[, ]+(?:lay|laylay))?[!?. ]*",
        texto,
    ):
        return "Oi. Tô aqui."

    social = _resposta_social_curta(bruto)
    if social:
        return social

    visual = _resposta_sobre_visual_recente(
        bruto,
        _ultima_observacao_visual(contexto),
    )
    if visual:
        return visual

    progresso = re.search(
        r"\b(?:eu\s+)?(?:to|tô|estou)\s+(terminando|construindo|fazendo|montando)\s+(.+?)[.!?]*$",
        bruto,
        flags=re.IGNORECASE,
    )
    if progresso:
        acao = progresso.group(1).casefold()
        alvo = progresso.group(2).strip(" .!?\"")
        alvo = re.sub(r"\bminha\b", "sua", alvo, count=1, flags=re.IGNORECASE)
        alvo = re.sub(r"\bmeu\b", "seu", alvo, count=1, flags=re.IGNORECASE)
        if acao == "terminando":
            return f"Ahh, então era isso. Vai terminando {alvo} no seu ritmo — quero ver como fica."
        return f"Aí sim. Continua {acao} {alvo}; quero ver onde essa ideia vai dar."

    if "?" in bruto or re.match(
        r"^(?:como|qual|quais|por que|porque|onde|quando|quem|o que|e esse|e essa)\b",
        texto,
    ):
        return "Pera, essa eu não quero responder pela metade. Tenta mais uma vez comigo."
    return "Entendi. Continua — eu tô acompanhando daqui."
