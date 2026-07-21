"""Extracao conservadora de correcoes explicitamente ensinadas por Pedro."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base).strip()


def extrair_correcao_duravel(
    texto: str,
    *,
    estado_mental: Dict[str, Any] | None = None,
) -> Dict[str, Any] | None:
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    t = _normalizar(bruto)
    if not bruto or not any(sinal in t for sinal in (
        "nao e", "nao sou", "meu nome nao", "na verdade", "eu quis dizer",
        "voce ainda nao", "voce nao tem", "ja falei", "corrigindo",
    )):
        return None

    nome = re.search(
        r"\bmeu nome n[aã]o (?:e|é)\s+([^,.;]+?)[,;]\s*(?:meu nome )?(?:e|é)\s+([^,.;!?]+)",
        bruto,
        flags=re.IGNORECASE,
    )
    if nome:
        anterior, correto = (parte.strip(" '\"") for parte in nome.groups())
        return {
            "tipo": "identidade", "gatilho": "nome do usuario", "valor": correto,
            "regra": f"O nome do usuário é {correto}.", "erro": anterior,
            "confianca": 0.99,
        }

    capacidade = re.search(
        r"\b(?:voce|você)\s+(?:ainda\s+)?n[aã]o\s+(?:tem|consegue)\s+"
        r"(?:(?:essa|esta|aquela)\s+)?(?:habilidade|capacidade)?(?:\s+de)?\s*(.*)$",
        bruto,
        flags=re.IGNORECASE,
    )
    if capacidade:
        alvo = str(capacidade.group(1) or "").strip(" .,!?:;")
        estado = dict(estado_mental or {})
        futura = estado.get("capacidade_futura") if isinstance(estado.get("capacidade_futura"), dict) else {}
        if _normalizar(alvo) in {
            "", "ela", "ela ainda", "isso", "isso ainda", "essa", "essa ainda",
            "essa habilidade", "essa habilidade ainda", "essa capacidade",
        }:
            alvo = ""
        alvo = alvo or str(futura.get("alvo") or estado.get("ultimo_alvo") or "essa habilidade").strip()
        return {
            "tipo": "correcao", "gatilho": f"capacidade da Laylay: {alvo}",
            "valor": "indisponivel",
            "regra": f"A Laylay ainda não possui a capacidade de {alvo}; não deve oferecê-la nem afirmar que executou.",
            "erro": f"capacidade de {alvo} disponível",
            "confianca": 0.98,
        }

    troca = re.search(
        r"\b(?:na verdade[,;]?\s*|eu quis dizer\s+|corrigindo[,;]?\s*)?"
        r"n[aã]o (?:e|é|era)\s+([^,.;]+?)[,;]\s*(?:e|é|era)\s+([^,.;!?]+)",
        bruto,
        flags=re.IGNORECASE,
    )
    if troca:
        anterior, correto = (parte.strip(" '\"") for parte in troca.groups())
        if anterior and correto and anterior.casefold() != correto.casefold():
            return {
                "tipo": "correcao", "gatilho": anterior[:140], "valor": correto[:180],
                "regra": f"Quando aparecer {anterior}, considerar a correção ensinada: {correto}.",
                "erro": anterior, "confianca": 0.96,
            }
    return None


def persistir_correcao_duravel(memoria_sqlite: Any, correcao: Dict[str, Any], texto_original: str) -> bool:
    if memoria_sqlite is None or not isinstance(correcao, dict) or not correcao.get("gatilho"):
        return False
    salvo = memoria_sqlite.salvar_aprendizado_semantico(
        tipo=str(correcao.get("tipo") or "correcao"),
        gatilho=str(correcao.get("gatilho") or ""),
        valor=str(correcao.get("valor") or ""),
        regra=str(correcao.get("regra") or ""),
        texto_original=str(texto_original or "")[:500],
        confianca=float(correcao.get("confianca") or 0.96),
        origem="usuario",
        evidencia=str(texto_original or "")[:500],
        status="ativo",
        confirmado_usuario=True,
    )
    return bool(salvo)
