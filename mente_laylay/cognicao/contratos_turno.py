"""Contratos tipados das fronteiras do turno da Laylay.

Os módulos legados ainda trocam dicionários. Estes contratos normalizam as
fronteiras sem obrigar uma migração ampla e preservam campos adicionais para
que a adoção possa ocorrer módulo por módulo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Mapping, TypedDict


ModalidadeTurno = Literal[
    "comando", "confirmacao", "conversa", "correcao", "deliberacao",
    "misto", "pergunta", "reacao", "recusa", "vazio",
]
ProprietarioTurno = Literal["conversa", "coordenador", "operacional"]
StatusDecisao = Literal[
    "planejada", "decidida", "aguardando_intencao", "sem_acao",
]


class AtoTurnoDict(TypedDict, total=False):
    ordem: int
    tipo: str
    texto: str
    objetivo: str
    requer_execucao: bool


class RoteiroGeracaoConcretaDict(TypedDict, total=False):
    versao: int
    estrategia: str
    ancora_literal: str
    nucleo_resposta: str
    sequencia: list[str]
    exigencias_concretude: list[str]
    abstracoes_a_concretizar: list[str]
    base_permitida: list[str]
    primeira_frase_responde_nucleo: bool
    autoriza_execucao: bool
    origem: str


class ContratoFalaDict(TypedDict, total=False):
    versao: int
    turno_id: Any
    funcao: str
    atos: list[str]
    referente: str
    conteudos_obrigatorios: list[str]
    inferencias_proibidas: list[str]
    estrutura: list[str]
    max_frases: int
    permite_pergunta: bool
    permite_humor: bool
    permite_metafora: bool
    fala_anterior_relevante: str
    respostas_recentes_evitar: list[str]
    cooperacao_considerada: bool
    roteiro_concreto: RoteiroGeracaoConcretaDict
    autoriza_execucao: bool
    origem: str


class LeituraTurnoDict(TypedDict, total=False):
    id: int
    origem_entrada: str
    modalidade: str
    modalidade_geral: str
    ato_principal: str
    autoriza_execucao: bool
    requer_esclarecimento: bool
    confianca: float
    segmentos: list[Dict[str, Any]]
    texto_operacional: str
    texto_conversacional: str
    tema_factual: str
    aprendizados_explicitos: list[Dict[str, Any]]
    especialistas: Dict[str, Any]
    contrato_fala: ContratoFalaDict


class PlanoTurnoDict(TypedDict, total=False):
    id: int
    origem_entrada: str
    texto_usuario: str
    modalidade: str
    ato_principal: str
    atos: list[AtoTurnoDict]
    dominio: str
    contexto_necessario: list[str]
    requer_execucao: bool
    autoriza_execucao: bool
    natureza_acao: str
    turno_sem_autorizacao: bool
    misto: bool
    resposta_esperada: str
    fase: str
    comandos: list[Dict[str, Any]]
    erros: list[str]
    decisao_turno: Dict[str, Any]
    deliberacao_habilidades: Dict[str, Any]
    contrato_fala: ContratoFalaDict


class RespostaPreparadaTurnoDict(TypedDict, total=False):
    resposta_bruta: Any
    fala: str
    comandos: list[Dict[str, Any]]
    tipo_interacao: str
    aprendizados: list[Any]
    leitura_semantica: Dict[str, Any]
    autocorrigida: bool
    suprimir_fala: bool
    emocao: str
    nivel_emocao: int


_CAMPOS_DECISAO = {
    "turno_id", "modalidade", "proprietario", "permite_acao",
    "permite_resposta", "requer_esclarecimento", "intencao",
    "origem_decisao", "confianca", "status",
}


def _confianca_segura(valor: Any) -> float:
    try:
        return round(float(valor or 0.0), 3)
    except (TypeError, ValueError):
        return 0.0


@dataclass(frozen=True, slots=True)
class ContratoDecisaoTurno:
    turno_id: Any = None
    modalidade: str = "conversa"
    proprietario: str = "conversa"
    permite_acao: bool = False
    permite_resposta: bool = True
    requer_esclarecimento: bool = False
    intencao: str = ""
    origem_decisao: str = "classificador_turno"
    confianca: float = 0.0
    status: str = "planejada"
    extras: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "modalidade", str(self.modalidade or "conversa").strip().lower())
        object.__setattr__(self, "proprietario", str(self.proprietario or "conversa").strip().lower())
        object.__setattr__(self, "permite_acao", bool(self.permite_acao))
        object.__setattr__(self, "permite_resposta", bool(self.permite_resposta))
        object.__setattr__(self, "requer_esclarecimento", bool(self.requer_esclarecimento))
        object.__setattr__(self, "intencao", str(self.intencao or "").strip().upper())
        object.__setattr__(self, "origem_decisao", str(self.origem_decisao or "").strip())
        object.__setattr__(self, "confianca", _confianca_segura(self.confianca))
        object.__setattr__(self, "status", str(self.status or "planejada").strip().lower())
        object.__setattr__(self, "extras", dict(self.extras or {}))

    @classmethod
    def de_mapping(cls, dados: Mapping[str, Any] | None) -> "ContratoDecisaoTurno":
        origem = dict(dados or {})
        extras = {chave: valor for chave, valor in origem.items() if chave not in _CAMPOS_DECISAO}
        return cls(
            turno_id=origem.get("turno_id"),
            modalidade=origem.get("modalidade", "conversa"),
            proprietario=origem.get("proprietario", "conversa"),
            permite_acao=origem.get("permite_acao", False),
            permite_resposta=origem.get("permite_resposta", True),
            requer_esclarecimento=origem.get("requer_esclarecimento", False),
            intencao=origem.get("intencao", ""),
            origem_decisao=origem.get("origem_decisao", "classificador_turno"),
            confianca=origem.get("confianca", 0.0),
            status=origem.get("status", "planejada"),
            extras=extras,
        )

    def como_dict(self) -> Dict[str, Any]:
        dados = dict(self.extras)
        dados.update({
            "turno_id": self.turno_id,
            "modalidade": self.modalidade,
            "proprietario": self.proprietario,
            "permite_acao": self.permite_acao,
            "permite_resposta": self.permite_resposta,
            "requer_esclarecimento": self.requer_esclarecimento,
            "intencao": self.intencao,
            "origem_decisao": self.origem_decisao,
            "confianca": self.confianca,
            "status": self.status,
        })
        return dados


@dataclass(frozen=True, slots=True)
class ContratoRespostaTurno:
    resposta_bruta: Any = ""
    fala: str = ""
    comandos: tuple[Dict[str, Any], ...] = ()
    tipo_interacao: str = ""
    aprendizados: tuple[Any, ...] = ()
    leitura_semantica: Mapping[str, Any] = field(default_factory=dict)
    autocorrigida: bool = False
    suprimir_fala: bool = False
    emocao: str = ""
    nivel_emocao: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "fala", str(self.fala or "").strip())
        object.__setattr__(self, "comandos", tuple(
            dict(item) for item in (self.comandos or ()) if isinstance(item, dict)
        ))
        object.__setattr__(self, "tipo_interacao", str(self.tipo_interacao or "").strip().lower())
        object.__setattr__(self, "aprendizados", tuple(self.aprendizados or ()))
        object.__setattr__(self, "leitura_semantica", dict(self.leitura_semantica or {}))
        object.__setattr__(self, "autocorrigida", bool(self.autocorrigida))
        object.__setattr__(self, "suprimir_fala", bool(self.suprimir_fala))
        object.__setattr__(self, "emocao", str(self.emocao or "").strip().lower())
        try:
            nivel_emocao = int(self.nivel_emocao or 0)
        except (TypeError, ValueError):
            nivel_emocao = 0
        object.__setattr__(self, "nivel_emocao", max(0, min(3, nivel_emocao)))

    def como_dict(self) -> RespostaPreparadaTurnoDict:
        dados: RespostaPreparadaTurnoDict = {
            "resposta_bruta": self.resposta_bruta,
            "fala": self.fala,
            "comandos": [dict(item) for item in self.comandos],
            "tipo_interacao": self.tipo_interacao,
            "aprendizados": list(self.aprendizados),
            "leitura_semantica": dict(self.leitura_semantica),
            "autocorrigida": self.autocorrigida,
            "suprimir_fala": self.suprimir_fala,
        }
        if self.emocao:
            dados["emocao"] = self.emocao
            dados["nivel_emocao"] = self.nivel_emocao or 1
        return dados


def normalizar_resposta_preparada(
    dados: Mapping[str, Any] | None = None,
    **sobrescritas: Any,
) -> ContratoRespostaTurno:
    origem = dict(dados or {})
    origem.update(sobrescritas)
    comandos_brutos = origem.get("comandos")
    comandos: tuple[Dict[str, Any], ...] = (
        tuple(dict(item) for item in comandos_brutos if isinstance(item, dict))
        if isinstance(comandos_brutos, (list, tuple))
        else ()
    )
    aprendizados_brutos = origem.get("aprendizados")
    aprendizados: tuple[Any, ...] = (
        tuple(aprendizados_brutos)
        if isinstance(aprendizados_brutos, (list, tuple))
        else ()
    )
    leitura_bruta = origem.get("leitura_semantica")
    leitura: Mapping[str, Any] = (
        dict(leitura_bruta) if isinstance(leitura_bruta, Mapping) else {}
    )
    return ContratoRespostaTurno(
        resposta_bruta=origem.get("resposta_bruta", ""),
        fala=origem.get("fala", ""),
        comandos=comandos,
        tipo_interacao=origem.get("tipo_interacao", ""),
        aprendizados=aprendizados,
        leitura_semantica=leitura,
        autocorrigida=origem.get("autocorrigida", False),
        suprimir_fala=origem.get("suprimir_fala", False),
        emocao=origem.get("emocao", ""),
        nivel_emocao=origem.get("nivel_emocao", 0),
    )
