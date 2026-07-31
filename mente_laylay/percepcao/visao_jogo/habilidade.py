"""Contrato visual para habilidades, gemas, passivas e nós de árvore."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


MARCADOR_HABILIDADE = "DADOS_HABILIDADE_JSON:"


def _texto(valor: Any, limite: int = 180) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()[:limite]


def _lista(valor: Any, limite: int = 10) -> list[str]:
    return [
        _texto(item) for item in list(valor or [])[:limite] if _texto(item)
    ]


def normalizar_habilidade(dados: Mapping[str, Any] | None) -> dict[str, Any]:
    bruto = dict(dados or {})
    try:
        confianca = round(max(0.0, min(1.0, float(bruto.get("confianca") or 0.0))), 3)
    except (TypeError, ValueError):
        confianca = 0.0
    try:
        custo = int(bruto.get("custo_pontos")) if bruto.get("custo_pontos") is not None else None
    except (TypeError, ValueError):
        custo = None
    nome = _texto(bruto.get("nome"), 120)
    tipo = _texto(bruto.get("tipo"), 60)
    termos = _lista(bruto.get("termos_pesquisa"), 5)
    return {
        "nome": nome,
        "tipo": tipo,
        "efeito": _texto(bruto.get("efeito"), 420),
        "custo_pontos": custo,
        "beneficios": _lista(bruto.get("beneficios")),
        "limitacoes": _lista(bruto.get("limitacoes")),
        "sinergias": _lista(bruto.get("sinergias")),
        "situacoes_fortes": _lista(bruto.get("situacoes_fortes"), 6),
        "situacoes_fracas": _lista(bruto.get("situacoes_fracas"), 6),
        "termos_pesquisa": list(dict.fromkeys(termos or [nome, tipo]))[:5],
        "confianca": confianca,
    }


def extrair_habilidade_da_resposta_visual(resposta: str) -> tuple[str, dict[str, Any]]:
    original = str(resposta or "").strip()
    padrao = re.compile(
        rf"(?:^|\n)\s*{re.escape(MARCADOR_HABILIDADE)}\s*(\{{[^\n]*\}})\s*$",
        re.IGNORECASE,
    )
    achado = padrao.search(original)
    if not achado:
        return original, {}
    fala = (original[:achado.start()] + original[achado.end():]).strip()
    try:
        bruto = json.loads(achado.group(1))
    except (TypeError, ValueError, json.JSONDecodeError):
        return fala, {}
    return fala, normalizar_habilidade(bruto if isinstance(bruto, Mapping) else {})


def parecer_local_habilidade(habilidade: Mapping[str, Any], perfil: Mapping[str, Any]) -> str:
    """Fallback imediato e honesto quando a síntese remota não responde."""
    dados = dict(habilidade or {})
    nome = str(dados.get("nome") or "essa habilidade")
    efeito = str(dados.get("efeito") or "").strip()
    texto = " ".join((efeito, *list(dados.get("beneficios") or []))).casefold()
    custo = dados.get("custo_pontos")
    if re.search(r"vida.{0,35}(?:matar|morto|inimigo)|(?:matar|inimigo).{0,35}vida", texto):
        return (
            f"{nome} ajuda mais limpando grupos, porque depende de inimigos mortos, mas quase não "
            "contribui contra chefes. Eu só priorizaria se sua recuperação estiver ruim ou se esse "
            + (f"for apenas um custo de {custo} ponto no caminho de algo melhor." if custo else "nó já estiver no caminho de uma passiva melhor.")
        )
    if efeito:
        classe = str(dict(perfil or {}).get("classe") or "sua build")
        custo_texto = f" O custo visível é de {custo} ponto(s)." if custo is not None else ""
        return (
            f"{nome} oferece {efeito}. Para {classe}, ela vale a pena somente se esse efeito apoiar "
            f"o foco principal da build; sem ver o custo de caminho e o que você deixaria de pegar, "
            f"eu trataria como opção, não prioridade.{custo_texto}"
        )
    return (
        f"Eu mantive a referência a {nome}, mas não li efeito e custo suficientes para recomendar "
        "o ponto sem inventar."
    )

