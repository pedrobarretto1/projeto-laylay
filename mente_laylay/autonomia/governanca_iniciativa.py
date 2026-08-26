"""Interpretação restrita das permissões autônomas escolhidas pelo usuário."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping


PERMISSOES_INICIATIVA = frozenset({"bloqueado", "sugestao", "acao_reversivel"})
DOMINIOS_PERFIL_SEGURO = ("iot", "musica", "conforto")
ALIASES_DOMINIO = {
    "iot": ("iot", "luz", "luzes", "lampada", "lampadas", "iluminacao"),
    "musica": ("musica", "musicas", "som", "audio", "playlist"),
    "janelas": ("janela", "janelas", "programa", "programas", "aplicativo", "aplicativos"),
    "navegador": ("navegador", "site", "sites", "chrome", "opera", "aba", "abas"),
    "agenda": ("agenda", "lembrete", "lembretes", "alarme", "alarmes"),
    "arquivos": ("arquivo", "arquivos", "pasta", "pastas"),
    "rotina": ("rotina", "rotinas", "habito", "habitos"),
    "conforto": ("conforto", "modo noite", "volume noturno", "horario"),
    "jogo": ("jogo", "jogos", "game", "gaming", "inventario", "build", "equipamento"),
}


def _normalizar(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base).strip(" ?!.,")


def normalizar_dominio_iniciativa(valor: Any) -> str:
    texto = _normalizar(valor)
    for dominio, aliases in ALIASES_DOMINIO.items():
        if texto == dominio or any(re.search(rf"\b{re.escape(alias)}\b", texto) for alias in aliases):
            return dominio
    return ""


def detectar_comando_governanca_iniciativa(texto: str) -> dict[str, str] | None:
    t = _normalizar(texto)
    if t in {"/autonomia desfazer", "/desfazer autonomia"} or re.search(
        r"\bdesfa[cç]a\s+(?:a\s+)?(?:sua\s+)?(?:[uú]ltima\s+)?a[cç][aã]o\s+aut[oô]noma\b",
        t,
    ):
        return {"acao": "desfazer", "dominio": "", "permissao": ""}
    if t in {"/autonomia", "/permissoes autonomia", "/autonomia status"} or (
        re.search(r"\b(?:mostra|mostre|quais|ver|como estao)\b", t)
        and re.search(r"\b(?:permissoes|configuracao|status)\b", t)
        and "autonomia" in t
    ):
        return {"acao": "status", "dominio": "", "permissao": ""}

    # Perfil agrupado para quem não precisa conhecer os nomes internos. Só uma
    # autorização ou um bloqueio explícito altera essas permissões.
    perfil_seguro = bool(
        re.search(r"\bautonomia segura\b", t)
        or (
            re.search(r"\b(?:acoes|comandos) (?:autonomos )?(?:seguros|reversiveis)\b", t)
            and re.search(r"\b(?:quando for necessario|quando forem necessarias|se precisar)\b", t)
        )
    )
    if perfil_seguro:
        if re.search(r"\b(?:desative|desativar|bloqueie|bloquear|pare|nao execute)\b", t):
            return {
                "acao": "configurar_perfil", "perfil": "seguro",
                "dominio": "", "permissao": "bloqueado",
            }
        if re.search(r"\b(?:ative|ativar|autorize|autorizar|permita|permitir|pode executar)\b", t):
            return {
                "acao": "configurar_perfil", "perfil": "seguro",
                "dominio": "", "permissao": "acao_reversivel",
            }

    dominio = normalizar_dominio_iniciativa(t)
    if not dominio or not re.search(r"\b(?:autonomia|automatic|sugest|autorize|permita|bloqueie|desative)\w*\b", t):
        return None
    if re.search(r"\b(?:bloqueie|bloquear|desative|desativar|nao sugira|pare de sugerir|nao faca automaticamente)\b", t):
        permissao = "bloqueado"
    elif re.search(r"\b(?:acao|acoes) reversiveis\b|\bexecut(?:e|ar) automaticamente\b", t) and re.search(
        r"\b(?:autorize|autorizar|permita|permitir|pode)\b", t,
    ):
        permissao = "acao_reversivel"
    elif "sugest" in t and re.search(r"\b(?:autorize|autorizar|permita|permitir|pode)\b", t):
        permissao = "sugestao"
    else:
        return None
    return {"acao": "configurar", "dominio": dominio, "permissao": permissao}


def decisao_permite_emissao(resultado: Mapping[str, Any] | None) -> bool:
    """Modo sombra observa sem alterar legado; outros modos aplicam a permissão."""
    dados = dict(resultado or {})
    decisao = str(dados.get("decisao") or "").strip().casefold()
    if not decisao:
        return True
    # Quando a ponte executou (ou tentou executar), a fonte não deve emitir a
    # sugestão antiga e pedir confirmação para a mesma ação outra vez.
    return decisao.startswith("sombra_") or decisao == "sugerir"
