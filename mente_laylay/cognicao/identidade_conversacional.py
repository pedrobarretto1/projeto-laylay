"""Identidade e perspectiva linguistica da mente unica da Laylay."""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Any, Dict


IDENTIDADE_LAYLAY = {
    "id": "laylay",
    "nome": "Laylay",
    "apelidos": ("laylay", "lay"),
    "papel": "assistente e interlocutora",
}
IDENTIDADE_USUARIO = {
    "id": "pedro",
    "nome": "Pedro",
    "papel": "usuario e interlocutor",
}


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base).strip()


def remover_vocativo_laylay(texto: str) -> str:
    """Remove o chamado, preservando nomes de arquivo como Laylay.py."""
    fala = str(texto or "").strip()
    fala = re.sub(r"^(?:oi\s+|ei\s+|ola\s+|olá\s+)?(?:laylay|lay)(?!\s*\.py)\s*[,;:!\-]*\s*", "", fala, flags=re.IGNORECASE)
    fala = re.sub(r"\s*[,;:]?\s+(?:laylay|lay)\s*[.!]?\s*$", "", fala, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", fala).strip()


def analisar_identidade_turno(texto: str, *, falante: str = "pedro") -> Dict[str, Any]:
    bruto = str(texto or "").strip()
    base = _normalizar(bruto)
    menciona_arquivo = bool(re.search(r"\blaylay\s*\.\s*py\b", base))
    menciona_nome = bool(re.search(r"\b(?:laylay|lay)\b", base))
    vocativo = remover_vocativo_laylay(bruto) != bruto and menciona_nome and not menciona_arquivo
    relacao_self = ""
    relacoes = (
        ("codigo", r"\b(?:codigo|projeto|programa)\s+(?:da|de)\s+laylay\b"),
        ("memoria", r"\bmemoria\s+(?:da|de)\s+laylay\b"),
        ("voz", r"\bvoz\s+(?:da|de)\s+laylay\b"),
        ("habilidades", r"\bhabilidades?\s+(?:da|de)\s+laylay\b"),
        ("personalidade", r"\b(?:personalidade|jeito)\s+(?:da|de)\s+laylay\b"),
    )
    relacao_self = next((nome for nome, padrao in relacoes if re.search(padrao, base)), "")
    referencia_laylay = bool(
        (menciona_nome and not menciona_arquivo)
        or re.search(r"\b(?:voce|você|tu|te|contigo)\b", bruto.casefold())
    )
    referencia_pedro = bool(
        re.search(r"\bpedro\b", base)
        or (falante == "pedro" and re.search(r"\b(?:eu|meu|minha|me|mim)\b", base))
    )
    ambigua = bool(re.search(r"\bela\b", base) and not menciona_nome)
    return {
        "falante": falante,
        "interlocutor": "laylay" if falante == "pedro" else "pedro",
        "laylay_eu": referencia_laylay,
        "pedro_eu": falante == "pedro",
        "referencia_laylay": referencia_laylay,
        "referencia_pedro": referencia_pedro,
        "vocativo_laylay": vocativo,
        "texto_sem_vocativo": remover_vocativo_laylay(bruto),
        "objeto_laylay_py": menciona_arquivo,
        "relacao_com_laylay": relacao_self,
        "pronome_ambiguo": ambigua,
        "ts": time.time(),
    }


def resumo_identidade_turno(analise: Dict[str, Any] | None) -> str:
    dados = dict(analise or {})
    if not dados:
        return ""
    partes = [
        "Identidade conversacional: quem fala agora e Pedro; quem responde e Laylay.",
        "Na fala de Pedro, 'voce', 'tu', 'Lay' e 'Laylay' apontam para a propria Laylay.",
        "Na resposta da Laylay, 'eu', 'meu' e 'minha' apontam para a propria Laylay; 'voce' aponta para Pedro.",
    ]
    if dados.get("objeto_laylay_py"):
        partes.append("Laylay.py e um arquivo/projeto; nao confundir o arquivo com o nome da interlocutora.")
    if dados.get("relacao_com_laylay"):
        partes.append(
            f"A referencia a {dados.get('relacao_com_laylay')} da Laylay trata de algo que pertence a voce; responda em primeira pessoa quando natural."
        )
    if dados.get("vocativo_laylay"):
        partes.append("O nome Laylay foi apenas um chamado, nao e o alvo do comando.")
    return " ".join(partes)


def ajustar_autorreferencia_assistente(texto: str) -> str:
    """Converte terceira pessoa artificial em primeira pessoa, sem tocar Laylay.py."""
    fala = str(texto or "").strip()
    if not fala:
        return fala
    substituicoes = (
        (r"\b(?:o\s+)?c[oó]digo\s+da\s+Laylay\b", "meu código"),
        (r"\b(?:a\s+)?mem[oó]ria\s+da\s+Laylay\b", "minha memória"),
        (r"\b(?:a\s+)?voz\s+da\s+Laylay\b", "minha voz"),
        (r"\b(?:as\s+)?habilidades\s+da\s+Laylay\b", "minhas habilidades"),
        (r"\b(?:a\s+)?personalidade\s+da\s+Laylay\b", "minha personalidade"),
    )
    for padrao, troca in substituicoes:
        fala = re.sub(padrao, troca, fala, flags=re.IGNORECASE)

    verbos = {
        "pode": "posso", "consegue": "consigo", "acha": "acho", "pensa": "penso",
        "está": "estou", "esta": "estou", "vai": "vou", "quer": "quero",
        "precisa": "preciso", "gosta": "gosto", "lembra": "lembro", "sabe": "sei",
    }
    padrao_verbo = "|".join(sorted(map(re.escape, verbos), key=len, reverse=True))

    def primeira_pessoa(match: re.Match[str]) -> str:
        verbo = match.group("verbo").casefold()
        convertido = verbos.get(verbo, match.group("verbo"))
        return convertido.capitalize() if match.group(0)[:1].isupper() else convertido

    fala = re.sub(
        rf"\b(?:a\s+)?Laylay\s+(?P<verbo>{padrao_verbo})\b",
        primeira_pessoa,
        fala,
        flags=re.IGNORECASE,
    )
    # Na resposta da própria Laylay, um vocativo "Lay/Laylay" dirigido à
    # interlocutora é inversão de papéis. Remove apenas o vocativo, sem tocar
    # usos legítimos como "eu sou a Laylay" ou o arquivo Laylay.py.
    fala = re.sub(
        r"\s*[,;]\s*(?:Laylay|Lay)\s*(?=[.!?]|$)",
        "",
        fala,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", fala).strip()
