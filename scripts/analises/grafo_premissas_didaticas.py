"""Grafo offline de premissas didáticas anteriores à redação."""

from __future__ import annotations

import re
from dataclasses import dataclass

from mente_laylay.cognicao.contrato_inventario_contextual import ReferenteContextual


@dataclass(frozen=True)
class FonteDidatica:
    identificador: str
    origem: str
    escopo: str
    texto: str


@dataclass(frozen=True)
class ReferenteAncorado:
    referente: ReferenteContextual
    fonte_id: str
    citacao: str


@dataclass(frozen=True)
class PremissaDidatica:
    identificador: str
    referente_id: str
    atributo: str
    valor: str
    unidade: str
    fonte_id: str
    citacao: str


@dataclass(frozen=True)
class CondicaoDidatica:
    referente_id: str
    atributo: str
    operador: str
    valor: str
    unidade: str
    fonte_id: str
    citacao: str


@dataclass(frozen=True)
class RegraDidatica:
    identificador: str
    condicoes: tuple[CondicaoDidatica, ...]
    efeito_referente_id: str
    efeito_atributo: str
    efeito_valor: str
    fonte_id: str
    citacao: str
    conectivo_condicoes: str = "indeterminado"
    direcao_implicacao: str = "indeterminado"


def conferir_grafo_premissas(
    fontes: tuple[FonteDidatica, ...],
    referentes: tuple[ReferenteAncorado, ...],
    premissas: tuple[PremissaDidatica, ...],
    regras: tuple[RegraDidatica, ...],
    *, escopo: str,
) -> dict[str, object]:
    """Confere proveniência estrutural, sem certificar a semântica das frases.

    A citação é somente uma âncora literal. Mesmo um grafo aceito aqui precisa
    de revisão independente das relações antes de compor uma resposta.
    """
    resultado: dict[str, object] = {
        "estado": "estrutura_invalida",
        "referentes": [],
        "condicoes_por_regra": {},
        "anotacao_semantica_revisada": False,
        "condicoes_satisfeitas": False,
        "consequencias_observadas": False,
        "aprovado_para_compor": False,
        "autoriza_efeito": False,
    }

    def falha(estado: str) -> dict[str, object]:
        return {**resultado, "estado": estado}

    def texto(valor: object) -> bool:
        return isinstance(valor, str) and bool(valor.strip())

    if (not texto(escopo)
            or not all(isinstance(itens, tuple)
                       for itens in (fontes, referentes, premissas, regras))
            or not fontes or not referentes or not regras
            or any(not isinstance(item, FonteDidatica) for item in fontes)
            or any(not isinstance(item, ReferenteAncorado) for item in referentes)
            or any(not isinstance(item, PremissaDidatica) for item in premissas)
            or any(not isinstance(item, RegraDidatica) for item in regras)):
        return falha("estrutura_invalida")

    ids_fontes = [item.identificador for item in fontes]
    ids_referentes = [item.referente.identificador for item in referentes
                      if isinstance(item.referente, ReferenteContextual)]
    ids_premissas = [item.identificador for item in premissas]
    ids_regras = [item.identificador for item in regras]
    if (len(ids_referentes) != len(referentes)
            or any(not texto(identificador) for identificador in
                   (*ids_fontes, *ids_referentes, *ids_premissas, *ids_regras))
            or any(len(ids) != len(set(ids)) for ids in
                   (ids_fontes, ids_referentes, ids_premissas, ids_regras))):
        return falha("identidade_invalida")

    for fonte in fontes:
        if fonte.escopo != escopo:
            return falha("escopo_divergente")
        if fonte.origem not in {"usuario", "pesquisa_verificada"}:
            return falha("origem_sem_autoridade")
        if not texto(fonte.texto):
            return falha("estrutura_invalida")
    por_fonte = {fonte.identificador: fonte for fonte in fontes}
    por_referente = {}

    def citacao_valida(fonte_id: str, citacao: str) -> str:
        if fonte_id not in por_fonte:
            return "fonte_desconhecida"
        if not texto(citacao) or citacao not in por_fonte[fonte_id].texto:
            return "citacao_invalida"
        return ""

    for item in referentes:
        referente = item.referente
        if referente.escopo != escopo:
            return falha("escopo_divergente")
        erro = citacao_valida(item.fonte_id, item.citacao)
        if erro:
            return falha(erro)
        if (referente.origem != por_fonte[item.fonte_id].origem
                or not texto(referente.tipo) or not texto(referente.grandeza)):
            return falha("referente_invalido")
        por_referente[referente.identificador] = referente

    def valor_ancorado(valor: str, unidade: str, citacao: str) -> bool:
        if not texto(valor) or not isinstance(unidade, str):
            return False
        # Delimitar tokens numéricos evita validar 20 com uma citação de 120.
        if re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?", valor):
            padrao = rf"(?<![\d.,]){re.escape(valor)}\s*{re.escape(unidade)}(?![\d.,])"
            return bool(re.search(padrao, citacao))
        return valor.casefold() in citacao.casefold()

    for premissa in premissas:
        if premissa.referente_id not in por_referente:
            return falha("referente_desconhecido")
        erro = citacao_valida(premissa.fonte_id, premissa.citacao)
        if erro:
            return falha(erro)
        if (not texto(premissa.atributo)
                or not valor_ancorado(premissa.valor, premissa.unidade,
                                      premissa.citacao)):
            return falha("valor_sem_ancora_literal")

    por_regra: dict[str, int] = {}
    for regra in regras:
        if regra.efeito_referente_id not in por_referente:
            return falha("referente_desconhecido")
        erro = citacao_valida(regra.fonte_id, regra.citacao)
        if erro:
            return falha(erro)
        if (not isinstance(regra.condicoes, tuple) or not regra.condicoes
                or not texto(regra.efeito_atributo)
                or not valor_ancorado(regra.efeito_valor, "", regra.citacao)
                or regra.conectivo_condicoes not in {
                    "indeterminado", "unico", "e", "ou",
                }
                or regra.direcao_implicacao not in {
                    "indeterminado", "condicoes_suficientes",
                    "condicoes_necessarias", "equivalencia",
                }
                or (len(regra.condicoes) == 1
                    and regra.conectivo_condicoes in {"e", "ou"})
                or (len(regra.condicoes) > 1
                    and regra.conectivo_condicoes == "unico")):
            return falha("regra_invalida")
        for condicao in regra.condicoes:
            if not isinstance(condicao, CondicaoDidatica):
                return falha("regra_invalida")
            if condicao.referente_id not in por_referente:
                return falha("referente_desconhecido")
            erro = citacao_valida(condicao.fonte_id, condicao.citacao)
            if erro:
                return falha(erro)
            if (condicao.fonte_id != regra.fonte_id
                    or condicao.citacao not in regra.citacao
                    or condicao.operador not in {"<", "<=", ">", ">=", "=", "!="}
                    or not texto(condicao.atributo)):
                return falha("regra_invalida")
            if not valor_ancorado(condicao.valor, condicao.unidade,
                                  condicao.citacao):
                return falha("valor_sem_ancora_literal")
        por_regra[regra.identificador] = len(regra.condicoes)

    return {
        **resultado,
        "estado": "estrutura_ancorada_revisao_pendente",
        "referentes": ids_referentes,
        "condicoes_por_regra": por_regra,
    }


def auditar_vinculos_literais(
    fontes: tuple[FonteDidatica, ...],
    referentes: tuple[ReferenteAncorado, ...],
    premissas: tuple[PremissaDidatica, ...],
    regras: tuple[RegraDidatica, ...],
    *, escopo: str,
) -> dict[str, object]:
    """Compara vínculos e sinais explícitos; não certifica relações semânticas.

    Referência textual compartilhada é apenas uma pista. Mesmo um resultado
    coerente não prova que a medição, a condição ou o efeito são verdadeiros.
    """
    estrutura = conferir_grafo_premissas(
        fontes, referentes, premissas, regras, escopo=escopo,
    )
    base = {**estrutura, "premissas": {}, "condicoes": {}, "efeitos": {}}
    if estrutura["estado"] != "estrutura_ancorada_revisao_pendente":
        return base

    por_referente = {item.referente.identificador: item for item in referentes}

    def mencionado(referente_id: str, citacao: str) -> str:
        item = por_referente[referente_id]
        trechos = (item.citacao, item.referente.grandeza)
        for trecho in trechos:
            if re.search(rf"(?<!\w){re.escape(trecho)}(?!\w)",
                         citacao, flags=re.IGNORECASE):
                return "referente_literal_localizado"
        return "referente_sem_ancora_literal"

    def direcao(condicao: CondicaoDidatica) -> str:
        if not re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?", condicao.valor):
            return "direcao_indeterminada"
        unidade = re.escape(condicao.unidade.casefold())
        numero = re.escape(condicao.valor)
        trecho = condicao.citacao.casefold()
        if re.search(r"\b(?:não|nao|nunca)\b", trecho):
            return "direcao_indeterminada"
        operadores = set()
        for palavra, operador in (("abaixo de", "<"), ("acima de", ">")):
            for _ in re.finditer(
                rf"\b{palavra}\s+{numero}\s*{unidade}(?![\d.,])", trecho,
            ):
                operadores.add(operador)
        for operador in ("<", ">"):
            if re.search(
                rf"(?<![<>=]){re.escape(operador)}\s*{numero}\s*{unidade}(?![\d.,])",
                trecho,
            ):
                operadores.add(operador)
        if len(operadores) != 1:
            return "direcao_indeterminada"
        return ("direcao_literal_coerente" if condicao.operador in operadores
                else "direcao_literal_divergente")

    premissas_auditadas = {
        item.identificador: mencionado(item.referente_id, item.citacao)
        for item in premissas
    }
    condicoes_auditadas = {
        regra.identificador: [
            {"referente": mencionado(item.referente_id, item.citacao),
             "direcao": direcao(item)}
            for item in regra.condicoes
        ]
        for regra in regras
    }
    efeitos_auditados = {
        regra.identificador: mencionado(regra.efeito_referente_id, regra.citacao)
        for regra in regras
    }
    return {
        **base,
        "estado": "pistas_literais_revisao_pendente",
        "premissas": premissas_auditadas,
        "condicoes": condicoes_auditadas,
        "efeitos": efeitos_auditados,
    }
