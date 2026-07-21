"""Ferramentas leves para interpretar comandos da autonomia da Laylay."""

from __future__ import annotations

import re
from typing import Callable, List, Optional


def limpar_resposta(texto: str) -> str:
    """Remove marcas visuais da resposta sem alterar o conteúdo semântico."""
    texto = str(texto or "")
    texto = re.sub(r"\*\*|__|\*|_", "", texto)
    texto = re.sub(r"\n+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto.replace('"', "")


def segmentar_comandos_em_cadeia(
    texto: str,
    *,
    normalizar_texto: Optional[Callable[[str], str]] = None,
) -> List[str]:
    """Separa comandos naturais em até duas etapas encadeadas."""
    bruto = str(texto or "").strip()
    if not bruto:
        return []

    t = normalizar_texto(bruto) if callable(normalizar_texto) else bruto.lower()
    t = re.sub(r"[,\.!\?:;]+", " ", t)
    t = re.sub(r"\b(laylay|lay|por favor|pfv)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return []

    for sep in (r"\be depois\b", r"\bem seguida\b", r"\bdepois\b", r"\bent[aã]o\b"):
        partes = re.split(sep, t, maxsplit=1)
        if len(partes) > 1:
            partes = [p.strip() for p in partes if p and p.strip()]
            if len(partes) > 1:
                return partes[:2]

    return [t]


def executar_comando_em_texto(
    texto: str,
    origem: str = "",
    *,
    detectar_repetir_briefing: Optional[Callable[[str], bool]] = None,
    repetir_briefing: Optional[Callable[[], object]] = None,
    processar_comando_deterministico: Optional[Callable[[str, str], bool]] = None,
    interpretar_comando_local_rapido: Optional[Callable[[str], object]] = None,
    executar_intencao: Optional[Callable[[object, str], object]] = None,
    log: Callable[[str], object] = print,
) -> bool:
    """Executa um trecho de comando textual usando callbacks do cérebro principal."""
    t = str(texto or "").strip()
    if not t:
        return False

    if callable(detectar_repetir_briefing) and detectar_repetir_briefing(t):
        if callable(repetir_briefing):
            repetir_briefing()
        return True

    if callable(processar_comando_deterministico) and processar_comando_deterministico(t, origem):
        return True

    comando_local = interpretar_comando_local_rapido(t) if callable(interpretar_comando_local_rapido) else None
    if comando_local:
        try:
            return bool(executar_intencao(comando_local, t)) if callable(executar_intencao) else False
        except Exception as e:
            log(f"⚠️ [COMANDO LOCAL] falha ao executar: {e}")
            return False

    return False


def processar_comandos_em_cadeia(
    texto: str,
    origem: str = "",
    *,
    normalizar_texto: Optional[Callable[[str], str]] = None,
    segmentar: Callable[..., List[str]] = segmentar_comandos_em_cadeia,
    executar_trecho: Optional[Callable[[str, str], bool]] = None,
) -> bool:
    """Executa comandos naturais encadeados, mantendo compatibilidade com o fluxo antigo."""
    texto_normalizado = normalizar_texto(texto) if callable(normalizar_texto) else str(texto or "")
    partes = segmentar(texto_normalizado, normalizar_texto=None)
    if len(partes) < 2:
        return False

    executou_algum = False
    tag = origem or "cadeia"
    for idx, parte in enumerate(partes[:2], start=1):
        if callable(executar_trecho) and executar_trecho(parte, f"{tag}-{idx}"):
            executou_algum = True

    return executou_algum
