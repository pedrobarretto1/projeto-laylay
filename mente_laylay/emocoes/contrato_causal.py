"""Contrato canônico de eventos emocionais causais da mente única."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import time
from typing import Any, Mapping


NATUREZAS_EVIDENCIA_EMOCIONAL = frozenset({
    "fato_observado",
    "inferencia",
    "leitura_social",
    "preferencia_aprendida",
})
RESPONSABILIDADES_EMOCIONAIS = frozenset({
    "sistema", "laylay", "usuario", "ambigua",
})
SENSIBILIDADES_EMOCIONAIS = frozenset({
    "normal", "sensivel", "vulneravel",
})


def _proporcao(valor: Any) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return 0.0
    if numero > 1.0:
        numero /= 100.0
    return round(max(0.0, min(1.0, numero)), 3)


@dataclass(frozen=True, slots=True)
class EventoEmocionalCausal:
    origem: str
    causa: str
    evidencia_ref: str
    natureza_evidencia: str
    responsabilidade: str
    confianca: float
    relevancia: float
    novidade: float
    intensidade: int
    sensibilidade: str
    alvo: str
    validade: dict[str, Any]
    permite_expressao: bool
    emocao: str
    nivel: int
    motivo_expressao: str
    arco: str
    ts: float
    autoriza_execucao: bool = False
    persistencia_pessoal: bool = False
    versao: int = 1

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


def criar_evento_emocional_causal(
    *,
    origem: str,
    causa: str,
    evidencia_ref: str,
    natureza_evidencia: str,
    responsabilidade: str = "ambigua",
    confianca: float = 0.0,
    relevancia: float = 0.0,
    novidade: float = 0.0,
    intensidade: int = 1,
    sensibilidade: str = "normal",
    alvo: str = "",
    validade_s: float = 120.0,
    permite_expressao: bool = False,
    emocao: str = "calma",
    nivel: int = 1,
    motivo_expressao: str = "evento_neutro_sem_expressao",
    arco: str = "neutro",
    ts: float | None = None,
) -> dict[str, Any]:
    instante = float(time.time() if ts is None else ts)
    origem_limpa = str(origem or "").strip()[:120]
    causa_limpa = str(causa or "").strip()[:300]
    evidencia_limpa = str(evidencia_ref or "").strip()[:240]
    natureza = str(natureza_evidencia or "").strip().casefold()
    confianca_limpa = _proporcao(confianca)
    responsabilidade_limpa = str(
        responsabilidade or "ambigua"
    ).strip().casefold()
    if responsabilidade_limpa not in RESPONSABILIDADES_EMOCIONAIS:
        responsabilidade_limpa = "ambigua"
    if responsabilidade_limpa != "ambigua" and confianca_limpa < 0.90:
        responsabilidade_limpa = "ambigua"
    sensibilidade_limpa = str(sensibilidade or "normal").strip().casefold()
    if sensibilidade_limpa not in SENSIBILIDADES_EMOCIONAIS:
        sensibilidade_limpa = "sensivel"
    try:
        duracao = max(0.0, float(validade_s))
    except (TypeError, ValueError):
        duracao = 0.0
    causa_rastreavel = bool(
        origem_limpa
        and causa_limpa
        and evidencia_limpa
        and natureza in NATUREZAS_EVIDENCIA_EMOCIONAL
        and duracao > 0.0
    )
    validade = {
        "valido": causa_rastreavel,
        "inicio_ts": instante,
        "expira_ts": instante + duracao if causa_rastreavel else instante,
        "motivo": (
            "causa_rastreavel" if causa_rastreavel else "causa_nao_rastreavel"
        ),
    }
    permite = bool(permite_expressao and causa_rastreavel)
    emocao_limpa = str(emocao or "calma").strip().casefold() or "calma"
    nivel_limpo = max(1, min(3, int(nivel or 1)))
    intensidade_limpa = max(0, min(3, int(intensidade or 0)))
    if not causa_rastreavel:
        emocao_limpa, nivel_limpo, intensidade_limpa = "calma", 1, 0

    return EventoEmocionalCausal(
        origem=origem_limpa,
        causa=causa_limpa,
        evidencia_ref=evidencia_limpa,
        natureza_evidencia=(
            natureza if natureza in NATUREZAS_EVIDENCIA_EMOCIONAL else "inferencia"
        ),
        responsabilidade=responsabilidade_limpa,
        confianca=confianca_limpa,
        relevancia=_proporcao(relevancia),
        novidade=_proporcao(novidade),
        intensidade=intensidade_limpa,
        sensibilidade=sensibilidade_limpa,
        alvo=str(alvo or "").strip()[:160],
        validade=validade,
        permite_expressao=permite,
        emocao=emocao_limpa,
        nivel=nivel_limpo,
        motivo_expressao=str(motivo_expressao or "").strip()[:160],
        arco=str(arco or "neutro").strip()[:80],
        ts=instante,
    ).como_dict()


def evento_tem_causa_rastreavel(evento: Mapping[str, Any] | None) -> bool:
    dados = dict(evento or {})
    validade = dict(dados.get("validade") or {})
    return bool(
        validade.get("valido") is True
        and str(dados.get("origem") or "").strip()
        and str(dados.get("causa") or "").strip()
        and str(dados.get("evidencia_ref") or "").strip()
        and str(dados.get("natureza_evidencia") or "").strip().casefold()
        in NATUREZAS_EVIDENCIA_EMOCIONAL
        and dados.get("autoriza_execucao") is False
    )


def evento_pode_alterar_estado(evento: Mapping[str, Any] | None) -> bool:
    return bool(
        evento_tem_causa_rastreavel(evento)
        and dict(evento or {}).get("permite_expressao") is True
    )


def criar_evento_leitura_emocional_usuario(
    leitura: Mapping[str, Any] | None,
    *,
    turno_id: str | int,
) -> dict[str, Any]:
    dados = dict(leitura or {})
    emocao_usuario = str(dados.get("emocao") or "").strip()
    if not emocao_usuario:
        return {}
    sensiveis = {
        "tristeza", "ansiedade", "medo", "culpa", "esgotamento",
    }
    return criar_evento_emocional_causal(
        origem="contingencia_lexical_usuario",
        causa=(
            "sinal emocional reconhecido pela contingência lexical "
            "no turno atual"
        ),
        evidencia_ref=f"turno:{turno_id}:texto_usuario",
        natureza_evidencia="leitura_social",
        responsabilidade="usuario",
        confianca=0.96,
        relevancia=0.95,
        novidade=0.8,
        intensidade=int(dados.get("intensidade") or 1),
        sensibilidade=(
            "vulneravel"
            if emocao_usuario.casefold() in sensiveis
            else "sensivel"
        ),
        alvo=str(dados.get("alvo") or "estado_emocional_usuario"),
        validade_s=120.0,
        permite_expressao=False,
        emocao="calma",
        nivel=1,
        motivo_expressao="leitura_do_usuario_nao_altera_emocao_da_laylay",
        arco="acolhimento",
        ts=float(dados.get("ts") or time.time()),
    )


def criar_evento_leitura_semantica_usuario(
    leitura_semantica: Mapping[str, Any] | None,
    *,
    turno_id: str | int,
) -> dict[str, Any]:
    """Converte somente leitura semântica validada em evento causal."""
    semantica = dict(leitura_semantica or {})
    leitura = (
        dict(semantica.get("leitura_emocional") or {})
        if isinstance(semantica.get("leitura_emocional"), Mapping)
        else {}
    )
    if leitura.get("valida") is not True:
        return {}
    evidencia = str(leitura.get("trecho_evidencia") or "").strip()
    causa = str(leitura.get("causa_expressa") or "").strip()
    estado_usuario = str(leitura.get("estado_usuario") or "").strip().casefold()
    if not evidencia or not causa or not estado_usuario:
        return {}
    assinatura = hashlib.sha256(
        evidencia.casefold().encode("utf-8", errors="replace")
    ).hexdigest()[:16]
    sensiveis = {
        "ansiedade", "culpa", "esgotamento", "medo", "tristeza",
    }
    return criar_evento_emocional_causal(
        origem="leitura_semantica_principal",
        causa=causa,
        evidencia_ref=f"turno:{turno_id}:semantica:{assinatura}",
        natureza_evidencia=str(
            leitura.get("natureza_evidencia") or "inferencia"
        ),
        responsabilidade="usuario",
        confianca=float(leitura.get("confianca") or 0.0),
        relevancia=max(0.8, float(leitura.get("confianca") or 0.0)),
        novidade=0.8,
        intensidade=int(leitura.get("intensidade") or 1),
        sensibilidade=(
            "vulneravel" if estado_usuario in sensiveis else "sensivel"
        ),
        alvo=str(leitura.get("alvo") or "estado_geral"),
        validade_s=120.0,
        permite_expressao=False,
        emocao="calma",
        nivel=1,
        motivo_expressao="leitura_do_usuario_nao_altera_emocao_da_laylay",
        arco="acolhimento",
    )
