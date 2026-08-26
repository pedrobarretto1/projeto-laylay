"""Contrato de procedencia para aprendizados gerados durante uma conversa."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, List


TIPOS_DURAVEIS = {
    "apelido", "correcao", "fato_pessoal", "identidade", "permissao",
    "preferencia", "regra", "rotina",
}
_STOPWORDS = {
    "a", "ao", "as", "com", "como", "da", "das", "de", "do", "dos", "e", "em",
    "essa", "esse", "eu", "isso", "me", "meu", "minha", "na", "nao", "no", "o",
    "os", "para", "por", "que", "se", "ser", "sou", "um", "uma",
}
_SINAIS_EXPLICITOS = re.compile(
    r"(?:^\s*(?:tamb[eé]m\s+)?(?:n[aã]o\s+)?(?:gosto|curto|amo|adoro|odeio|prefiro)\b|"
    r"\b(?:meu nome (?:e|eh)|me chama de|eu (?:tamb[eé]m\s+)?"
    r"(?:n[aã]o\s+)?(?:gosto|curto|amo|adoro|odeio|prefiro)|"
    r"eu\s+(?:moro\s+em|trabalho\s+como|estudo)|"
    r"minha\s+profiss[aã]o\s+(?:e|é|eh)|fa[cç]o\s+faculdade\s+de|"
    r"(?:um dos|uma das) meus? .{0,50} favorit[oa]s?|meus? .{0,50} favorit[oa]s?|"
    r"n[aã]o gosto|lembra(?: de)? que|guarda(?: isso| que)?|anota(?: que)?|"
    r"quando eu|pode sempre|n[aã]o (?:abra|faca|toque|use)|na verdade|"
    r"corrigindo|n[aã]o e .+ e|isso significa)\b)",
    re.IGNORECASE,
)


def extrair_aprendizados_pessoais_explicitos(texto_usuario: str) -> List[Dict[str, Any]]:
    """Extrai preferências e fatos estáveis inequívocos da própria pessoa.

    A extração é deliberadamente estreita: registra favoritos, local de
    residência, profissão e área de estudo que o próprio usuário declarou.
    Fatos externos, estados momentâneos e inferências continuam fora da
    memória durável.
    """
    bruto = re.sub(r"\s+", " ", str(texto_usuario or "")).strip()
    # Uma pergunta sobre a própria memória ("eu gosto de sertanejo?") não é
    # uma nova afirmação. Promovê-la a fato inverteria exatamente o dado que a
    # pessoa está tentando conferir.
    declaracao_enquadrada = bool(re.search(
        r"\b(?:sabia|sabe)\s+que\s+(?:eu\s+)?(?:tamb[eé]m\s+)?"
        r"(?:n[aã]o\s+)?(?:gosto|curto|adoro|amo|prefiro)\b",
        bruto,
        flags=re.IGNORECASE,
    ))
    if not bruto or ("?" in bruto and not declaracao_enquadrada):
        return []

    resultados: List[Dict[str, Any]] = []
    afinidades = re.finditer(
        r"(?:^|\beu\s+)(?:tamb[eé]m\s+)?(?P<negacao>n[aã]o\s+)?"
        r"(?P<verbo>gosto|curto|adoro|amo|prefiro)\s+"
        r"(?:(?:muito|bastante|demais)\s+)?"
        r"(?:d[oa]s?|de|da|do)\s+(?P<valor>.+?)"
        r"(?=\s*,?\s+(?:mas|e\s+eu|e\s+tamb[eé]m)\b|[,.!?;]|$)",
        bruto,
        flags=re.IGNORECASE,
    )
    for achado in afinidades:
        valor = str(achado.group("valor") or "").strip(" ,.;:-")
        valor = re.sub(r"\s+", " ", valor)
        if not valor or len(valor) > 90 or len(valor.split()) > 12:
            continue
        negado = bool(achado.group("negacao"))
        verbo = str(achado.group("verbo") or "gosto").casefold()
        if negado:
            regra = f"você não gosta de {valor}"
        elif verbo == "prefiro":
            regra = f"você prefere {valor}"
        elif verbo in {"adoro", "amo"}:
            conjugado = "adora" if verbo == "adoro" else "ama"
            regra = f"você {conjugado} {valor}"
        else:
            conjugado = "curte" if verbo == "curto" else "gosta"
            preposicao = "" if conjugado == "curte" else " de"
            regra = f"você {conjugado}{preposicao} {valor}"
        resultados.append({
            "tipo": "preferencia",
            "gatilho": f"afinidade com {valor}",
            "valor": valor,
            "regra": regra,
            "confianca": 0.98,
        })

    padroes = (
        # "GTA 5 ..., um dos meus jogos favoritos"
        r"(?P<valor>[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9 '&+.:_-]{1,70}?)"
        r"(?:\s+(?:desde|foi|é|e|era|está|esta)\b[^,.;]{0,70})?,\s*"
        r"(?:um dos|uma das)\s+meus?\s+(?P<categoria>[A-Za-zÀ-ÿ ]{2,30}?)\s+favorit[oa]s?\b",
        # "GTA 5 é um dos meus jogos favoritos"
        r"(?P<valor>[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9 '&+.:_-]{1,70}?)\s+"
        r"(?:é|e|está|esta)\s+(?:um dos|uma das)\s+meus?\s+"
        r"(?P<categoria>[A-Za-zÀ-ÿ ]{2,30}?)\s+favorit[oa]s?\b",
    )
    for padrao in padroes:
        achado = re.search(padrao, bruto, flags=re.IGNORECASE)
        if not achado:
            continue
        valor = re.sub(r"^(?:eu\s+)?(?:jogo|jogava|curto|escuto|ouço|assisto)\s+", "", achado.group("valor"), flags=re.IGNORECASE)
        valor = valor.strip(" ,.;:-")
        categoria = achado.group("categoria").strip().casefold()
        if not valor or len(valor.split()) > 10:
            continue
        resultados.append({
            "tipo": "preferencia",
            "gatilho": f"{categoria} favoritos",
            "valor": valor,
            "regra": f"{valor} está entre os {categoria} favoritos do usuário",
            "confianca": 0.98,
        })
        break

    limite_fato = (
        r"(?=\s*,?\s+(?:mas|e\s+(?:eu\s+)?(?:moro|trabalho|estudo|fa[cç]o))\b|"
        r"[.!?;]|$)"
    )
    padroes_fatos = (
        (
            r"(?:^|[,;]\s*|\be\s+)(?:eu\s+)?moro\s+em\s+"
            rf"(?P<valor>.+?){limite_fato}",
            "local onde mora",
            "você mora em {valor}",
            60,
            7,
        ),
        (
            r"(?:^|[,;]\s*|\be\s+)(?:(?:eu\s+)?trabalho\s+como|minha\s+profiss[aã]o\s+"
            r"(?:e|é|eh|è))\s+"
            rf"(?P<valor>.+?){limite_fato}",
            "profissão",
            "você trabalha como {valor}",
            80,
            10,
        ),
        (
            r"(?:^|[,;]\s*|\be\s+)(?:(?:eu\s+)?estudo|fa[cç]o\s+faculdade\s+de)\s+"
            rf"(?P<valor>.+?){limite_fato}",
            "área de estudo",
            "você estuda {valor}",
            80,
            10,
        ),
    )
    for padrao, gatilho, regra, max_chars, max_palavras in padroes_fatos:
        achado = re.search(padrao, bruto, flags=re.IGNORECASE)
        if not achado:
            continue
        valor = re.sub(r"\s+", " ", str(achado.group("valor") or "")).strip(" ,.;:-")
        if not valor or len(valor) > max_chars or len(valor.split()) > max_palavras:
            continue
        resultados.append({
            "tipo": "fato_pessoal",
            "gatilho": gatilho,
            "valor": valor,
            "regra": regra.format(valor=valor),
            "confianca": 0.98,
        })
    return resultados


def normalizar_texto(texto: Any) -> str:
    bruto = unicodedata.normalize("NFD", str(texto or "").casefold())
    bruto = "".join(ch for ch in bruto if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", bruto)).strip()


def _tokens(texto: Any) -> set[str]:
    return {
        token for token in normalizar_texto(texto).split()
        if len(token) >= 3 and token not in _STOPWORDS
    }


def _texto_item(item: Any) -> str:
    if not isinstance(item, dict):
        return str(item or "").strip()
    return " ".join(
        str(item.get(chave) or "").strip()
        for chave in ("gatilho", "valor", "regra", "texto", "descricao")
        if str(item.get(chave) or "").strip()
    )


def _tipo_item(item: Any) -> str:
    if not isinstance(item, dict):
        return "regra"
    return normalizar_texto(item.get("tipo") or "regra").replace(" ", "_") or "regra"


def usuario_sustenta_aprendizado(texto_usuario: str, item: Any) -> bool:
    """Exige evidencia na fala atual; a saida criativa da IA nunca basta sozinha."""
    usuario = normalizar_texto(texto_usuario)
    memoria = normalizar_texto(_texto_item(item))
    if not usuario or not memoria:
        return False

    tipo = _tipo_item(item)
    tokens_usuario = _tokens(usuario)
    tokens_memoria = _tokens(memoria)
    compartilhados = tokens_usuario & tokens_memoria
    cobertura = len(compartilhados) / max(1, min(len(tokens_usuario), len(tokens_memoria)))
    sinal_explicito = bool(_SINAIS_EXPLICITOS.search(usuario))

    if tipo in {"preferencia", "identidade", "apelido"}:
        return bool(compartilhados) and (sinal_explicito or cobertura >= 0.6)
    if tipo in TIPOS_DURAVEIS:
        return sinal_explicito and bool(compartilhados)
    return sinal_explicito and cobertura >= 0.5


def preparar_aprendizados_confirmados(
    aprendizados: Iterable[Any], texto_usuario: str
) -> List[Dict[str, Any]]:
    """Converte apenas ensinamentos sustentados pelo usuario para o contrato duravel."""
    confirmados: List[Dict[str, Any]] = []
    evidencia = re.sub(r"\s+", " ", str(texto_usuario or "")).strip()[:500]
    for item in aprendizados or []:
        if not usuario_sustenta_aprendizado(evidencia, item):
            continue
        if isinstance(item, dict):
            memoria = dict(item)
        else:
            texto = str(item or "").strip()
            memoria = {"tipo": "regra", "gatilho": texto[:140], "regra": texto}
        memoria.update({
            "origem": "usuario",
            "evidencia": evidencia,
            "status": "ativo",
            "confirmado_usuario": True,
        })
        try:
            memoria["confianca"] = max(0.9, min(1.0, float(memoria.get("confianca") or 0.94)))
        except Exception:
            memoria["confianca"] = 0.94
        confirmados.append(memoria)
    return confirmados
