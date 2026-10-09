"""Contratos tipados das fronteiras do turno da Laylay.

Os módulos legados ainda trocam dicionários. Estes contratos normalizam as
fronteiras sem obrigar uma migração ampla e preservam campos adicionais para
que a adoção possa ocorrer módulo por módulo.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from copy import deepcopy
import json
from typing import Any, Dict, Literal, Mapping, TypedDict

from mente_laylay.cognicao.estado_tecnico_llm import categoria_estado_tecnico_llm


ModalidadeTurno = Literal[
    "comando", "confirmacao", "conversa", "correcao", "deliberacao",
    "misto", "pergunta", "reacao", "recusa", "vazio",
]
NaturezaEntrada = Literal["utterance", "evento"]
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


class EventoCognitivoDict(TypedDict, total=False):
    natureza: Literal["evento"]
    origem: str
    tipo: str
    conteudo: str
    evidencia: Dict[str, Any]
    confianca: float
    timestamp: float
    trace_id: str
    autoridade_usuario: bool
    permissao_execucao: bool


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
    natureza_entrada: NaturezaEntrada
    entrada_cognitiva: EventoCognitivoDict


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
    natureza_entrada: NaturezaEntrada
    entrada_cognitiva: EventoCognitivoDict
    texto_evidencia: str


class RespostaPreparadaTurnoDict(TypedDict, total=False):
    resposta_bruta: Any
    fala: str
    comandos: list[Dict[str, Any]]
    tipo_interacao: str
    aprendizados: list[Any]
    leitura_semantica: Dict[str, Any]
    leitura_semantica_reparada: Dict[str, Any]
    autocorrigida: bool
    suprimir_fala: bool
    emocao: str
    nivel_emocao: int
    proposta_principal: ContratoPropostaPrincipal
    extracao_original: ExtracaoRespostaIA


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


def normalizar_evento_cognitivo(
    valor: Any,
    *,
    origem: str = "presenca",
) -> EventoCognitivoDict:
    """Reconhece evento estruturado e remove qualquer autoridade declarada.

    Um ``Mapping`` não vira utterance só porque seus valores são texto. Apenas
    entradas explicitamente marcadas como evento atravessam este contrato.
    """
    if not isinstance(valor, Mapping):
        return {}
    dados = dict(valor)
    if str(dados.get("natureza") or "").strip().casefold() != "evento":
        return {}
    dados["natureza"] = "evento"
    dados["origem"] = str(dados.get("origem") or origem or "presenca").strip()
    dados["tipo"] = str(dados.get("tipo") or "evento_observado").strip()
    dados["autoridade_usuario"] = False
    dados["permissao_execucao"] = False
    return dados  # type: ignore[return-value]


def texto_evento_cognitivo(evento: Mapping[str, Any] | None) -> str:
    """Extrai evidência textual sem serializar chaves de autoridade."""
    dados = dict(evento or {})
    partes: list[str] = []

    def adicionar(valor: Any) -> None:
        if isinstance(valor, Mapping):
            for chave in ("descricao", "conteudo", "texto", "texto_detectado"):
                adicionar(valor.get(chave))
            return
        if isinstance(valor, (list, tuple)):
            for item in valor:
                adicionar(item)
            return
        texto = str(valor or "").strip()
        if texto and texto not in partes:
            partes.append(texto)

    for chave in ("descricao", "conteudo", "texto", "evidencia"):
        adicionar(dados.get(chave))
    return " | ".join(partes)[:1500]


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
class ContratoOcorrenciaTurno:
    """Identidade capturada pelo runtime, sem certificar modelo ou efeito."""

    turno_id: Any = ""
    texto_usuario: str = ""
    autoriza_execucao: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        identificador = (
            str(self.turno_id).strip()
            if isinstance(self.turno_id, (str, int)) and not isinstance(self.turno_id, bool)
            else ""
        )
        texto = self.texto_usuario.strip() if isinstance(self.texto_usuario, str) else ""
        object.__setattr__(self, "turno_id", identificador)
        object.__setattr__(self, "texto_usuario", texto)


@dataclass(frozen=True, slots=True)
class ContratoPropostaPrincipal:
    """Emissão capturada pelo runtime antes de qualquer reparo.

    A procedência identifica somente a emissão e seu turno. Não comprova erro,
    responsabilidade, autorização ou efeito. O bruto permanece interno; JSON
    do modelo não materializa este contrato nem define seus campos de origem.
    """

    turno_id: Any = ""
    texto_usuario: str = ""
    resposta_bruta: Any = field(default="", repr=False)
    sucesso_modelo: bool = True
    origem: str = field(default="llm_principal", init=False)
    estado: str = field(default="", init=False)
    proveniencia_conhecida: bool = field(default=False, init=False)
    autoriza_execucao: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        turno_id = (
            str(self.turno_id).strip()
            if isinstance(self.turno_id, (str, int)) and not isinstance(self.turno_id, bool)
            else ""
        )
        texto = str(self.texto_usuario or "").strip()
        retorno_textual = isinstance(self.resposta_bruta, str)
        bruto = self.resposta_bruta if retorno_textual else ""
        sucesso = self.sucesso_modelo is True
        if not retorno_textual:
            estado = "retorno_nao_textual"
        elif not sucesso or categoria_estado_tecnico_llm(bruto):
            estado = "falha_tecnica"
        elif not bruto.strip():
            estado = "vazia"
        else:
            estado = "recebida"
        object.__setattr__(self, "turno_id", turno_id)
        object.__setattr__(self, "texto_usuario", texto)
        object.__setattr__(self, "resposta_bruta", bruto)
        object.__setattr__(self, "sucesso_modelo", sucesso)
        object.__setattr__(self, "estado", estado)
        object.__setattr__(
            self, "proveniencia_conhecida", bool(estado == "recebida" and turno_id and texto),
        )


@dataclass(frozen=True, slots=True)
class ViolacaoPropostaPrincipal:
    """Fato local demonstrado pelo owner do turno, sem payload ou receipt.

    Certifica somente a restrição violada pela proposta original. Não atesta
    validade dos parâmetros, identidade do alvo ou efeito no mundo externo.
    """

    turno_id: str
    indice_comando: int
    intent: str
    motivo: str
    proprietario: str
    operacao_explicita: str
    origem: str = field(default="contrato_proposta_principal", init=False)
    owner: str = field(default="validador_comandos_turno", init=False)
    autoriza_execucao: bool = field(default=False, init=False)
    comprova_efeito_externo: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if not (
            isinstance(self.turno_id, str) and self.turno_id and self.turno_id == self.turno_id.strip()
            and isinstance(self.indice_comando, int) and not isinstance(self.indice_comando, bool)
            and self.indice_comando >= 0
            and isinstance(self.intent, str) and self.intent
            and all(letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789" for letra in self.intent)
            and isinstance(self.motivo, str) and self.motivo in (
                "turno não autorizou execução", "intenção incompatível com a operação explícita",
            )
            and isinstance(self.proprietario, str) and self.proprietario in ("conversa", "operacional", "coordenador")
            and isinstance(self.operacao_explicita, str)
            and all(letra in "abcdefghijklmnopqrstuvwxyz_0123456789" for letra in self.operacao_explicita)
        ):
            raise ValueError("Prova de violação exige identidade, índice e restrição canônicos.")


@dataclass(frozen=True, slots=True)
class SnapshotComandoIA:
    """Árvore JSON isolada; toda projeção devolve uma cópia sem autoridade."""

    dados: InitVar[Dict[str, Any]]
    _dados_json: str = field(init=False, repr=False)
    autoriza_execucao: bool = field(default=False, init=False)

    def __post_init__(self, dados: Dict[str, Any]) -> None:
        if not isinstance(dados, dict):
            raise TypeError("Snapshot de comando exige objeto JSON.")
        serializado = json.dumps(dados, ensure_ascii=False, allow_nan=False)
        # Não converter silenciosamente chaves, tuplas ou tipos não JSON.
        if json.loads(serializado) != dados:
            raise ValueError("Snapshot de comando exige árvore JSON sem conversão de tipos.")
        object.__setattr__(self, "_dados_json", serializado)

    def como_dict(self) -> Dict[str, Any]:
        return json.loads(self._dados_json)


@dataclass(frozen=True, slots=True)
class ExtracaoRespostaIA:
    """Procedência interna da decodificação; não é autorização nem receipt.

    Os campos descrevem o caminho do parser, sem atestar que a proposta é
    correta. A string original permite vincular essa leitura à emissão
    capturada pelo chamador; coleções legadas não criam fonte textual.
    """

    resposta_bruta: str | None = field(default=None, repr=False)
    metodo: str = "desconhecido"
    campo_comandos_presente: bool = False
    quantidade_comandos: int = 0
    comandos_originais: tuple[SnapshotComandoIA, ...] | None = field(default=None, repr=False)
    comandos_normalizados: tuple[SnapshotComandoIA | None, ...] | None = field(default=None, repr=False)
    candidatos_preservados: bool = field(default=False, init=False)
    normalizacao_completa: bool = field(default=False, init=False)
    origem: str = field(default="decoder_canonico", init=False)
    autoriza_execucao: bool = field(default=False, init=False)
    proposta_operacional_explicita: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        bruto = self.resposta_bruta if isinstance(self.resposta_bruta, str) else None
        metodos = {
            "tupla_legada", "json_objeto", "json_envelope_textual",
            "recuperacao_campo_comandos", "recuperacao_padrao_textual",
            "recuperacao_fala", "texto_livre", "json_invalido_bloqueado",
        }
        metodo = (
            self.metodo if isinstance(self.metodo, str) and self.metodo in metodos
            else "desconhecido"
        )
        quantidade = (
            max(0, self.quantidade_comandos)
            if isinstance(self.quantidade_comandos, int)
            and not isinstance(self.quantidade_comandos, bool) else 0
        )
        campo_presente = self.campo_comandos_presente is True
        object.__setattr__(self, "resposta_bruta", bruto)
        object.__setattr__(self, "metodo", metodo)
        object.__setattr__(self, "quantidade_comandos", quantidade)
        object.__setattr__(self, "campo_comandos_presente", campo_presente)
        originais = self.comandos_originais
        preservados = (
            isinstance(originais, tuple) and len(originais) == quantidade
            and all(isinstance(item, SnapshotComandoIA) for item in originais)
        )
        if not preservados:
            object.__setattr__(self, "comandos_originais", None)
        normalizados = self.comandos_normalizados
        if not (
            preservados and isinstance(normalizados, tuple)
            and len(normalizados) == quantidade
            and all(item is None or isinstance(item, SnapshotComandoIA) for item in normalizados)
        ):
            normalizados = None
            object.__setattr__(self, "comandos_normalizados", None)
        object.__setattr__(self, "candidatos_preservados", preservados)
        object.__setattr__(self, "normalizacao_completa", bool(
            normalizados and all(item is not None for item in normalizados)
        ))
        object.__setattr__(self, "proposta_operacional_explicita", bool(
            metodo == "json_objeto" and campo_presente and quantidade > 0
            and bruto and not categoria_estado_tecnico_llm(bruto)
        ))


@dataclass(frozen=True, slots=True)
class ContratoRespostaTurno:
    resposta_bruta: Any = ""
    fala: str = ""
    comandos: tuple[Dict[str, Any], ...] = ()
    tipo_interacao: str = ""
    aprendizados: tuple[Any, ...] = ()
    leitura_semantica: Mapping[str, Any] = field(default_factory=dict)
    leitura_semantica_reparada: Mapping[str, Any] = field(default_factory=dict)
    autocorrigida: bool = False
    suprimir_fala: bool = False
    emocao: str = ""
    nivel_emocao: int = 0
    proposta_principal: ContratoPropostaPrincipal | None = None
    extracao_original: ExtracaoRespostaIA | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "fala", str(self.fala or "").strip())
        object.__setattr__(self, "comandos", tuple(
            dict(item) for item in (self.comandos or ()) if isinstance(item, dict)
        ))
        object.__setattr__(self, "tipo_interacao", str(self.tipo_interacao or "").strip().lower())
        object.__setattr__(self, "aprendizados", tuple(self.aprendizados or ()))
        object.__setattr__(self, "leitura_semantica", dict(self.leitura_semantica or {}))
        reparada = deepcopy(dict(self.leitura_semantica_reparada or {}))
        if reparada:
            reparada["origem"] = "resposta_reparada"
        object.__setattr__(self, "leitura_semantica_reparada", reparada)
        object.__setattr__(self, "autocorrigida", bool(self.autocorrigida))
        object.__setattr__(self, "suprimir_fala", bool(self.suprimir_fala))
        object.__setattr__(self, "emocao", str(self.emocao or "").strip().lower())
        try:
            nivel_emocao = int(self.nivel_emocao or 0)
        except (TypeError, ValueError):
            nivel_emocao = 0
        object.__setattr__(self, "nivel_emocao", max(0, min(3, nivel_emocao)))
        if not isinstance(self.proposta_principal, ContratoPropostaPrincipal):
            object.__setattr__(self, "proposta_principal", None)
        extracao = self.extracao_original
        if (
            not isinstance(extracao, ExtracaoRespostaIA)
            or (
                self.proposta_principal is not None
                and (
                    not self.proposta_principal.proveniencia_conhecida
                    or extracao.resposta_bruta != self.proposta_principal.resposta_bruta
                )
            )
        ):
            object.__setattr__(self, "extracao_original", None)

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
        if self.proposta_principal is not None:
            # Instância interna: não projetar o bruto para prompt, log ou receipt.
            dados["proposta_principal"] = self.proposta_principal
        if self.extracao_original is not None:
            dados["extracao_original"] = self.extracao_original
        if self.leitura_semantica_reparada:
            dados["leitura_semantica_reparada"] = deepcopy(dict(self.leitura_semantica_reparada))
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
        leitura_semantica_reparada=(
            origem.get("leitura_semantica_reparada")
            if isinstance(origem.get("leitura_semantica_reparada"), Mapping) else {}
        ),
        autocorrigida=origem.get("autocorrigida", False),
        suprimir_fala=origem.get("suprimir_fala", False),
        emocao=origem.get("emocao", ""),
        nivel_emocao=origem.get("nivel_emocao", 0),
        proposta_principal=origem.get("proposta_principal"),
        extracao_original=origem.get("extracao_original"),
    )
