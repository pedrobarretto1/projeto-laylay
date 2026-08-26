"""Retrato efêmero de como a Laylay deve se expressar no turno atual.

O retrato não interpreta nem autoriza ações. Ele junta postura, sensibilidade,
timing e variedade numa instrução pequena compartilhada pelos prompts.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from mente_laylay.personalidade.antirrepeticao import assinaturas_recentes
from mente_laylay.personalidade.perfil_amizade import (
    VERSAO_PERFIL_PERSONALIDADE,
    selecionar_postura_amizade,
)


@dataclass(frozen=True, slots=True)
class RetratoExpressaoTurno:
    versao_perfil: str
    postura: str
    estrategia_humor: str
    orcamento_humor: int
    motivo: str
    detalhe_obrigatorio: bool
    permite_pergunta: bool
    max_frases: int
    preservar_resultado: bool
    sensivel: bool
    assinaturas_evitar: tuple[str, ...] = ()
    autoriza_execucao: bool = False

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


def _houve_humor_recente(mensagens: list[Mapping[str, Any]]) -> bool:
    falas = [
        str(item.get("content") or "").casefold()
        for item in mensagens[-4:]
        if isinstance(item, Mapping)
        and str(item.get("role") or "").casefold() == "assistant"
    ]
    return any(re.search(r"\b(?:kk+k*|criatura|pose|novela|milagre|dignidade)\b", fala) for fala in falas)


def construir_retrato_expressivo(
    texto_usuario: str,
    *,
    estado_mental: Mapping[str, Any] | None = None,
    operacional: bool = False,
) -> RetratoExpressaoTurno:
    estado = dict(estado_mental or {})
    mensagens = [item for item in list(estado.get("messages") or []) if isinstance(item, Mapping)]
    postura = selecionar_postura_amizade(
        texto_usuario,
        estado_mental=estado,
        operacional=operacional,
    )
    social = dict(dict(estado.get("especialistas_turno_atual") or {}).get("social") or {})
    funcao = str(social.get("funcao") or "").casefold()
    sensivel = postura.humor == "bloqueado" or funcao in {
        "desabafo", "inseguranca", "decepcao", "frustracao", "correcao",
    }
    estrategia, motivo = "nenhum", "turno_literal"
    if operacional:
        evento = dict(estado.get("avaliacao_emocional_operacional_atual") or {})
        if evento.get("permite_expressao"):
            estrategia = str(evento.get("arco") or "reacao_causal")
            motivo = str(evento.get("causa") or "resultado operacional observado")
    elif not sensivel and postura.nome in {"brincalhona", "firme_debochada"}:
        estrategia, motivo = "acompanhar_brincadeira", "abertura social do usuário"
    elif not sensivel and postura.nome == "opinativa":
        estrategia, motivo = "observacao_seca_opcional", "opinião solicitada"
    elif not sensivel and funcao in {"agradecimento", "elogio", "reacao_positiva", "conquista"}:
        estrategia, motivo = "cumplicidade_curta", f"ato social: {funcao}"

    orcamento = int(estrategia != "nenhum" and postura.max_tirada > 0)
    # Uma tirada recente cria espaço para a conversa respirar. Se o usuário
    # sustenta a brincadeira, a postura brincalhona mantém o arco.
    if (
        orcamento
        and _houve_humor_recente(mensagens)
        and postura.nome not in {"brincalhona", "firme_debochada"}
    ):
        orcamento, motivo = 0, "intervalo depois de humor recente"

    return RetratoExpressaoTurno(
        versao_perfil=VERSAO_PERFIL_PERSONALIDADE,
        postura=postura.nome,
        estrategia_humor=estrategia if orcamento else "nenhum",
        orcamento_humor=orcamento,
        motivo=motivo,
        detalhe_obrigatorio=bool(orcamento),
        permite_pergunta=bool(postura.permite_pergunta and not operacional),
        max_frases=postura.max_frases,
        preservar_resultado=bool(operacional),
        sensivel=sensivel,
        assinaturas_evitar=tuple(assinaturas_recentes(mensagens, limite=6)),
    )


def formatar_retrato_expressivo_para_prompt(retrato: RetratoExpressaoTurno) -> str:
    evitar = ", ".join(retrato.assinaturas_evitar[-4:]) or "nenhuma"
    regra_humor = (
        f"Pode usar uma tirada de {retrato.estrategia_humor}, ancorada num detalhe literal do turno."
        if retrato.orcamento_humor else
        "Não force tirada neste turno."
    )
    return (
        "--- RETRATO EXPRESSIVO EFÊMERO ---\n"
        f"Perfil={retrato.versao_perfil}; postura={retrato.postura}; "
        f"sensível={'sim' if retrato.sensivel else 'não'}; máximo={retrato.max_frases} frases. "
        f"{regra_humor} Evite os moldes recentes: {evitar}. "
        "Responda ao conteúdo primeiro. Humor não cria fatos, comandos, autorização ou confirmação."
    )
