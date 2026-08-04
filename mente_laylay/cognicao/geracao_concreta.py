"""Roteiro concreto para a geração da fala de cada turno.

Este módulo não valida a resposta depois de pronta. Ele organiza a geração
antes da chamada ao modelo: qual ideia precisa aparecer primeiro, em que ordem
os atos devem ser atendidos e quais fontes podem sustentar a fala. O roteiro é
efêmero, não executa ações e não transforma contexto em autorização.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Iterable, Mapping


_ABSTRACOES_COMUNS = (
    "energia",
    "vibe",
    "sensação",
    "sentir-se vivo",
    "alma",
    "universo",
    "ritmo",
    "essência",
)


def _texto_curto(valor: Any, limite: int) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()[:limite]


def _itens_unicos(valores: Iterable[Any], *, limite_item: int) -> tuple[str, ...]:
    itens: list[str] = []
    vistos: set[str] = set()
    for valor in valores:
        item = _texto_curto(valor, limite_item)
        chave = item.casefold()
        if not item or not chave or chave in vistos:
            continue
        vistos.add(chave)
        itens.append(item)
    return tuple(itens)


@dataclass(frozen=True, slots=True)
class RoteiroGeracaoConcreta:
    """Plano linguístico sem qualquer autoridade operacional."""

    versao: int = 1
    estrategia: str = "resposta_direta"
    ancora_literal: str = ""
    nucleo_resposta: str = "responder diretamente ao pedido atual"
    sequencia: tuple[str, ...] = ()
    exigencias_concretude: tuple[str, ...] = ()
    abstracoes_a_concretizar: tuple[str, ...] = _ABSTRACOES_COMUNS
    base_permitida: tuple[str, ...] = ("fala atual do usuário",)
    primeira_frase_responde_nucleo: bool = True
    autoriza_execucao: bool = False
    origem: str = "mente_unica"

    def __post_init__(self) -> None:
        object.__setattr__(self, "versao", 1)
        object.__setattr__(
            self,
            "estrategia",
            _texto_curto(self.estrategia, 64) or "resposta_direta",
        )
        object.__setattr__(self, "ancora_literal", _texto_curto(self.ancora_literal, 500))
        object.__setattr__(
            self,
            "nucleo_resposta",
            _texto_curto(self.nucleo_resposta, 320)
            or "responder diretamente ao pedido atual",
        )
        object.__setattr__(
            self,
            "sequencia",
            _itens_unicos(self.sequencia, limite_item=220),
        )
        object.__setattr__(
            self,
            "exigencias_concretude",
            _itens_unicos(self.exigencias_concretude, limite_item=240),
        )
        object.__setattr__(
            self,
            "abstracoes_a_concretizar",
            _itens_unicos(self.abstracoes_a_concretizar, limite_item=64),
        )
        object.__setattr__(
            self,
            "base_permitida",
            _itens_unicos(self.base_permitida, limite_item=180)
            or ("fala atual do usuário",),
        )
        object.__setattr__(self, "primeira_frase_responde_nucleo", True)
        # Invariante: roteiro de linguagem nunca é permissão de ação.
        object.__setattr__(self, "autoriza_execucao", False)
        object.__setattr__(self, "origem", "mente_unica")

    def como_dict(self) -> dict[str, Any]:
        dados = asdict(self)
        for campo in (
            "sequencia",
            "exigencias_concretude",
            "abstracoes_a_concretizar",
            "base_permitida",
        ):
            dados[campo] = list(dados[campo])
        return dados


def normalizar_roteiro_geracao_concreta(
    roteiro: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Reconstrói um roteiro externo mantendo limites e invariantes."""
    dados = dict(roteiro or {})
    if not dados:
        return {}
    return RoteiroGeracaoConcreta(
        estrategia=dados.get("estrategia", "resposta_direta"),
        ancora_literal=dados.get("ancora_literal", ""),
        nucleo_resposta=dados.get("nucleo_resposta", ""),
        sequencia=tuple(dados.get("sequencia") or ()),
        exigencias_concretude=tuple(dados.get("exigencias_concretude") or ()),
        abstracoes_a_concretizar=tuple(
            dados.get("abstracoes_a_concretizar") or _ABSTRACOES_COMUNS
        ),
        base_permitida=tuple(dados.get("base_permitida") or ()),
        primeira_frase_responde_nucleo=True,
        autoriza_execucao=False,
    ).como_dict()


def _atos_relevantes(atos: Iterable[Any]) -> list[str]:
    relevantes = {
        "saudacao",
        "estado_pessoal",
        "bem_estar",
        "opiniao",
        "esclarecimento",
    }
    saida: list[str] = []
    for item in atos:
        ato = _texto_curto(item, 48).casefold()
        if ato in relevantes and ato not in saida:
            saida.append(ato)
    return saida


def _sequencia_multiacto(atos: Iterable[str]) -> tuple[str, ...]:
    presentes = set(atos)
    sequencia: list[str] = []
    if "saudacao" in presentes:
        sequencia.append("responder brevemente à saudação")
    if "estado_pessoal" in presentes:
        sequencia.append("reconhecer literalmente o estado informado pelo usuário")
    if "bem_estar" in presentes:
        sequencia.append("responder à pergunta de bem-estar como presença digital")
    if "opiniao" in presentes:
        sequencia.append("declarar a posição e dar um critério concreto")
    if "esclarecimento" in presentes:
        sequencia.append("explicar literalmente a fala anterior")
    sequencia.append("adicionar personalidade somente depois de responder todos os atos")
    return tuple(sequencia)


def _fundamentacao_confiavel(dados: Mapping[str, Any] | None) -> bool:
    base = dict(dados or {})
    return bool(
        base.get("confiavel")
        and base.get("evidencia_dentro_validade", True) is not False
    )


def construir_roteiro_geracao_concreta(
    texto: str,
    *,
    contrato: Mapping[str, Any] | None = None,
    plano: Mapping[str, Any] | None = None,
    fundamentacao_factual: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Escolhe uma estratégia concreta a partir do contrato já deliberado."""
    dados_contrato = dict(contrato or {})
    planejamento = dict(plano or {})
    bruto = _texto_curto(texto, 500)
    atos = [str(item or "").casefold() for item in dados_contrato.get("atos") or []]
    especiais = _atos_relevantes(atos)
    referente = _texto_curto(dados_contrato.get("referente"), 180)
    anterior = _texto_curto(dados_contrato.get("fala_anterior_relevante"), 500)
    requer_execucao = bool(planejamento.get("requer_execucao"))

    base_permitida = ["fala atual do usuário"]
    if referente:
        base_permitida.append("referente resolvido no turno atual")
    if anterior and "esclarecimento" in especiais:
        base_permitida.append("fala anterior explicitamente vinculada ao esclarecimento")
    if requer_execucao:
        base_permitida.append("resultado operacional publicado pelo executor, quando existir")
    if _fundamentacao_confiavel(fundamentacao_factual):
        base_permitida.append("fundamentação factual confiável e válida do turno")

    exigencias = [
        "usar a fala atual antes de puxar contexto antigo",
        "nomear o referente quando ele estiver resolvido",
        "ligar toda abstração, na mesma frase, a uma característica descritiva ou observável",
        "marcar como opinião ou incerteza o que não estiver sustentado por uma fonte permitida",
    ]

    if requer_execucao:
        estrategia = "resultado_observado"
        ancora = referente or bruto
        nucleo = (
            "relatar primeiro o resultado realmente observado da ação e preservar "
            "a incerteza quando não houver confirmação"
        )
        sequencia = (
            "dizer o que foi observado, sem promover envio a sucesso",
            "informar a consequência prática ou a incerteza essencial",
            "adicionar personalidade apenas sem alterar o resultado",
        )
    elif len(especiais) > 1:
        estrategia = "resposta_multiacto"
        ancora = bruto
        nucleo = "responder, na mesma fala, a todos os atos explícitos da mensagem atual"
        sequencia = _sequencia_multiacto(especiais)
    elif "esclarecimento" in especiais:
        estrategia = "esclarecimento_literal"
        ancora = anterior or bruto
        nucleo = "explicar com palavras literais o sentido da fala anterior"
        sequencia = (
            "reformular literalmente a ideia anterior",
            "dar a razão concreta que sustenta essa ideia",
            "usar no máximo um exemplo simples, somente se ajudar",
        )
        exigencias.append("não substituir a explicação por outra metáfora")
    elif "opiniao" in especiais:
        estrategia = "opiniao_com_criterio"
        ancora = referente or bruto
        alvo = referente or "o tema perguntado"
        nucleo = (
            f"declarar primeiro uma posição clara sobre {alvo} e sustentá-la "
            "com um critério descritivo ou observável"
        )
        sequencia = (
            "declarar a posição ou preferência",
            "citar um aspecto concreto que explica a posição",
            "fazer pergunta curta somente se ela avançar a conversa",
        )
    elif "estado_pessoal" in especiais:
        estrategia = "acolhimento_literal"
        ancora = bruto
        nucleo = "reconhecer primeiro, sem reinterpretar, o estado que o usuário informou"
        sequencia = (
            "reconhecer o estado nas palavras do usuário",
            "responder com companhia proporcional, sem dramatizar",
            "oferecer ajuda somente se ela fizer sentido",
        )
    elif "bem_estar" in especiais:
        estrategia = "reciprocidade_social"
        ancora = bruto
        nucleo = "responder brevemente como presença digital disponível, sem inventar corpo ou rotina"
        sequencia = (
            "responder diretamente como Laylay está na conversa",
            "devolver a cortesia com naturalidade, se couber",
        )
    elif "saudacao" in especiais:
        estrategia = "saudacao_simples"
        ancora = bruto
        nucleo = "responder à saudação sem atribuir ao usuário um humor não declarado"
        sequencia = (
            "cumprimentar de volta",
            "fazer no máximo uma pergunta simples, se couber",
        )
    else:
        estrategia = "resposta_direta"
        ancora = referente or bruto
        nucleo = "responder primeiro ao conteúdo explícito da fala atual"
        sequencia = (
            "dar a resposta direta",
            "explicar apenas o necessário",
            "acrescentar personalidade sem desviar do assunto",
        )

    return RoteiroGeracaoConcreta(
        estrategia=estrategia,
        ancora_literal=ancora,
        nucleo_resposta=nucleo,
        sequencia=tuple(sequencia),
        exigencias_concretude=tuple(exigencias),
        abstracoes_a_concretizar=_ABSTRACOES_COMUNS,
        base_permitida=tuple(base_permitida),
        primeira_frase_responde_nucleo=True,
        autoriza_execucao=False,
    ).como_dict()
