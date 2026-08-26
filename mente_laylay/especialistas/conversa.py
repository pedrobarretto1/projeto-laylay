"""Parecer de conversa: função humana, emoção e postura do turno."""

from __future__ import annotations

import re
from typing import Any, Dict


FUNCOES_SOCIAIS_PRIORITARIAS = {
    "agradecimento", "brincadeira", "conquista", "correcao", "decepcao",
    "desabafo", "elogio", "encerramento", "frustracao", "inseguranca",
    "reacao_positiva", "relato",
}


def limpar_fronteira_social(texto: str) -> str:
    """Remove somente uma moldura educada isolada antes do comando."""
    limpo = re.sub(r"\s+", " ", str(texto or "")).strip(" ,;")
    return re.sub(
        r"(?:,?\s+)(?:voce|você)?\s*(?:pode|poderia|consegue|conseguiria)$",
        "",
        limpo,
        flags=re.IGNORECASE,
    ).strip(" ,;")


def construir_parecer_conversa(
    texto: str,
    *,
    turno: Dict[str, Any],
    funcao_comunicativa: Dict[str, Any],
    operacional_ativo: bool,
) -> Dict[str, Any]:
    modalidade = str(turno.get("modalidade_geral") or turno.get("modalidade") or "conversa")
    texto_social = limpar_fronteira_social(str(turno.get("texto_conversacional") or ""))
    funcao_nome = str(funcao_comunicativa.get("funcao") or "informacao")
    if not texto_social and not operacional_ativo:
        texto_social = str(texto or "").strip()
    ativo = bool(texto_social) or funcao_nome in FUNCOES_SOCIAIS_PRIORITARIAS
    precisa_reconhecer = bool(
        ativo
        and (
            modalidade == "misto"
            or funcao_nome in FUNCOES_SOCIAIS_PRIORITARIAS
            or str(funcao_comunicativa.get("emocao_implicita") or "neutra") != "neutra"
        )
    )
    if funcao_nome == "encerramento":
        estrategia = "encerrar"
    elif funcao_nome in {"agradecimento", "elogio", "reacao_positiva"}:
        estrategia = "reconhecer_sem_pergunta"
    elif funcao_nome in {"correcao", "frustracao", "decepcao"}:
        estrategia = "reparar_sem_se_defender"
    elif funcao_nome in {"desabafo", "inseguranca"}:
        estrategia = "acolher_antes_de_sugerir"
    elif precisa_reconhecer:
        estrategia = "reconhecer_e_continuar"
    else:
        estrategia = "responder_diretamente"
    return {
        "ativo": ativo,
        "texto": texto_social[:300],
        "funcao": funcao_nome,
        "emocao": str(funcao_comunicativa.get("emocao_implicita") or "neutra"),
        "postura": str(funcao_comunicativa.get("postura_esperada") or "natural"),
        "permite_pergunta": bool(funcao_comunicativa.get("permite_pergunta", True)),
        "precisa_reconhecimento": precisa_reconhecer,
        "pode_executar": False,
        "politica_resposta": estrategia,
    }
