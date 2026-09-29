"""Sinal lexical conservador de direção lógica, apenas para sondas offline."""

from __future__ import annotations

import re


_MARCADORES = re.compile(
    r"\b(?:se\s+e\s+somente\s+se|se\s+e\s+só\s+se|"
    r"apenas\s+se|somente\s+se|só\s+se|"
    r"apenas\s+quando|somente\s+quando|quando|se)\b",
    re.IGNORECASE,
)

_NECESSARIOS = {
    "apenas se", "somente se", "só se", "apenas quando", "somente quando",
}
_EQUIVALENTES = {"se e somente se", "se e só se"}

_COMPARADOR_INCLUSIVO = re.compile(
    r"\b(?P<direcao>maior|menor)\s+ou\s+igual\s+a\s+"
    r"(?P<numero>[+-]?\d+(?:[.,]\d+)?)(?!\d|[.,]\d|e[+-]?\d)", re.IGNORECASE,
)


def encontrar_comparadores_inclusivos(fonte: str) -> list[re.Match[str]]:
    """Localiza átomos numéricos compostos preservando offsets literais.

    Não confere sujeito, unidade, negação ou escopo. Consumidores continuam
    responsáveis por essas guardas; o `ou` interno não une duas condições.
    Números por extenso e comparações elípticas não estão cobertos.
    """
    return list(_COMPARADOR_INCLUSIVO.finditer(fonte))


def encontrar_marcador_condicional(fonte: str) -> re.Match[str] | None:
    """Prioriza operador composto sem ler `se` pronominal como condição."""
    marcadores = list(_MARCADORES.finditer(fonte))
    if not marcadores:
        return None
    primeiro = marcadores[0]
    prefixo_frase = re.split(r"[.!?;]", fonte[:primeiro.start()])[-1]
    if not prefixo_frase.strip():
        return primeiro
    explicitos = [item for item in marcadores
                 if item.group().casefold() not in {"se", "quando"}]
    if explicitos:
        return explicitos[0]
    if primeiro.group().casefold() == "quando":
        return primeiro
    # `se` no meio da frase é indistinguível do pronome em muitos casos.
    # Aceitar só um início nominal inequívoco; o restante se abstém.
    if re.match(r"\s+(?:o|a|os|as|um|uma|ele|ela)\b",
                fonte[primeiro.end():], re.IGNORECASE):
        return primeiro
    return None


def analisar_marcador_condicional(fonte: str) -> dict[str, object]:
    """Extrai apenas sinal explícito; ambiguidades continuam indeterminadas."""
    base = {"estado": "indeterminado", "direcao": "indeterminado",
            "citacao": "", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    if not isinstance(fonte, str) or len(fonte) > 2000:
        return base
    # Uma citação ou negação pode trocar o escopo do operador textual.
    if any(aspas in fonte for aspas in ('"', "'", "‘", "’", "“", "”", "«", "»")):
        return base
    marcador = encontrar_marcador_condicional(fonte)
    if marcador is None:
        return base
    prefixo_frase = re.split(r"[.!?]", fonte[:marcador.start()])[-1]
    if re.search(r"\b(?:não|nao)\b", prefixo_frase, re.IGNORECASE):
        return base
    texto = re.sub(r"\s+", " ", marcador.group().casefold())
    if texto in _EQUIVALENTES:
        direcao = "equivalencia"
    elif texto in _NECESSARIOS:
        direcao = "condicoes_necessarias"
    elif texto == "se":
        direcao = "condicoes_suficientes"
    else:
        return base
    return {**base, "estado": "marcador_explicito", "direcao": direcao,
            "citacao": marcador.group()}


def confrontar_direcao_marcador(fonte: str, direcao_proposta: object) -> dict[str, object]:
    base = {"estado": "entrada_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    if not isinstance(direcao_proposta, str) or direcao_proposta not in {
        "condicoes_suficientes", "condicoes_necessarias", "equivalencia",
        "indeterminado",
    }:
        return base
    sinal = analisar_marcador_condicional(fonte)
    if sinal["estado"] != "marcador_explicito":
        return {**base, "estado": "direcao_sem_marcador_conclusivo"}
    return {**base, "estado": (
        "direcao_compativel_marcador_revisao_pendente"
        if direcao_proposta == sinal["direcao"]
        else "direcao_divergente_marcador"
    ), "marcador": sinal["citacao"]}


def analisar_efeito_qualificativo(fonte: str, rotulo: str) -> dict[str, object]:
    """Separa uma predicação simples sem inferir identidade ou verdade.

    Gramática deliberadamente limitada: `Se condição, sujeito é/está/fica
    predicado` ou `sujeito é/está/fica predicado apenas se condição` (também
    os demais marcadores explícitos). Um prefixo separado por vírgula é
    preservado como escopo não verificado. Outros formatos ficam pendentes.
    O predicado é extraído da fonte, nunca preenchido pelo rótulo desejado.
    """
    base = {"estado": "efeito_qualificativo_pendente", "citacao": "",
            "sujeito_literal": "", "predicado_literal": "",
            "polaridade": "indeterminada", "inicio": None, "fim": None,
            "escopo_literal": "", "escopo_verificado": False,
            "identidade_verificada": False, "aprovado_para_producao": False,
            "autoriza_efeito": False}
    if (not isinstance(rotulo, str) or not rotulo.strip()
            or analisar_marcador_condicional(fonte)["estado"] != "marcador_explicito"):
        return base
    marcador = encontrar_marcador_condicional(fonte)
    if marcador is None or len(list(_MARCADORES.finditer(fonte))) != 1:
        return base
    # Não abreviar a fonte: outra frase/ressalva pode mudar o escopo.
    corpo = fonte.rstrip().removesuffix(".")
    if re.search(r"[!?;\n\r]|(?<!\d)\.|\.(?!\d)", corpo):
        return base
    prefixo = fonte[:marcador.start()].strip()
    if not prefixo or (prefixo.endswith(",") and prefixo.count(",") == 1):
        base["escopo_literal"] = prefixo.rstrip(",").rstrip()
        separadores = list(re.finditer(r",\s+", corpo[marcador.end():]))
        if len(separadores) != 1:
            return base
        separador = separadores[0]
        if not corpo[marcador.end():marcador.end() + separador.start()].strip():
            return base
        inicio, fim = marcador.end() + separador.end(), len(corpo)
    else:
        if re.search(r",\s+", corpo) or not corpo[marcador.end():].strip():
            return base
        inicio, fim = 0, marcador.start()
    while inicio < fim and fonte[inicio].isspace():
        inicio += 1
    while fim > inicio and fonte[fim - 1].isspace():
        fim -= 1
    citacao = fonte[inicio:fim]
    evidencia = {**base, "citacao": citacao, "inicio": inicio, "fim": fim}
    if re.search(r"\b(?:não|nao|nunca|jamais|nem)\b", citacao, re.IGNORECASE):
        return {**evidencia, "polaridade": "negacao_presente"}
    predicacao = re.fullmatch(
        r"(?P<sujeito>[\w -]+?)\s+(?:é|está|fica)\s+(?P<predicado>[\w -]+)",
        citacao, re.IGNORECASE,
    )
    if predicacao is None:
        return evidencia
    sujeito = predicacao.group("sujeito").strip()
    predicado = predicacao.group("predicado").strip()
    evidencia = {**evidencia, "sujeito_literal": sujeito,
                 "predicado_literal": predicado}
    # Uma oração/modalidade no sujeito não deve sumir no recorte da cópula.
    if re.search(r"\b(?:que|talvez|possivelmente|provavelmente|pode|deve|seria)\b",
                 sujeito, re.IGNORECASE):
        return evidencia
    if predicado.casefold() != rotulo.strip().casefold():
        return evidencia
    return {**evidencia, "estado": "efeito_qualificativo_literal_revisao_pendente",
            "polaridade": "afirmativa_superficial"}
