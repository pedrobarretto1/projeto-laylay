"""Grafo offline de premissas didáticas anteriores à redação."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from mente_laylay.cognicao.auditoria_alegacoes_didaticas import (
    fontes_usuario_da_conversa,
)
from mente_laylay.cognicao.contrato_inventario_contextual import ReferenteContextual
from scripts.analises.sinal_relacao_condicional import (
    analisar_efeito_qualificativo, confrontar_direcao_marcador,
    encontrar_comparadores_inclusivos,
)


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
        if (not isinstance(fonte.origem, str)
                or fonte.origem not in {"usuario", "pesquisa_verificada"}):
            return falha("origem_sem_autoridade")
        if not texto(fonte.texto):
            return falha("estrutura_invalida")
    por_fonte = {fonte.identificador: fonte for fonte in fontes}
    por_referente = {}

    def citacao_valida(fonte_id: str, citacao: str) -> str:
        if not texto(fonte_id) or fonte_id not in por_fonte:
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
            # A pontuacao depois de uma unidade encerra o trecho ("20%,");
            # sem unidade, virgula/ponto so continuam o decimal com digito.
            sufixo = r"(?![\w/])" if unidade else r"(?!\d|[.,]\d)"
            padrao = rf"(?<![\d.,]){re.escape(valor)}\s*{re.escape(unidade)}{sufixo}"
            return bool(re.search(padrao, citacao))
        return valor.casefold() in citacao.casefold()

    for premissa in premissas:
        if (not texto(premissa.referente_id)
                or premissa.referente_id not in por_referente):
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
        if (not texto(regra.efeito_referente_id)
                or regra.efeito_referente_id not in por_referente):
            return falha("referente_desconhecido")
        erro = citacao_valida(regra.fonte_id, regra.citacao)
        if erro:
            return falha(erro)
        if (not isinstance(regra.condicoes, tuple) or not regra.condicoes
                or not texto(regra.efeito_atributo)
                or not valor_ancorado(regra.efeito_valor, "", regra.citacao)
                or not isinstance(regra.conectivo_condicoes, str)
                or regra.conectivo_condicoes not in {
                    "indeterminado", "unico", "e", "ou",
                }
                or not isinstance(regra.direcao_implicacao, str)
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
            if (not texto(condicao.referente_id)
                    or condicao.referente_id not in por_referente):
                return falha("referente_desconhecido")
            erro = citacao_valida(condicao.fonte_id, condicao.citacao)
            if erro:
                return falha(erro)
            if (condicao.fonte_id != regra.fonte_id
                    or condicao.citacao not in regra.citacao
                    or not isinstance(condicao.operador, str)
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
        sufixo = r"(?![\w/])" if condicao.unidade else r"(?!\d|[.,]\d)"
        if re.search(r"\b(?:não|nao|nunca)\b", trecho):
            return "direcao_indeterminada"
        operadores = set()
        for comparador in encontrar_comparadores_inclusivos(trecho):
            if (comparador["numero"] == condicao.valor
                    and re.match(rf"\s*{unidade}{sufixo}", trecho[comparador.end():])):
                operadores.add(">=" if comparador["direcao"] == "maior" else "<=")
        for palavra, operador in (("abaixo de", "<"), ("acima de", ">")):
            for _ in re.finditer(
                rf"\b{palavra}\s+{numero}\s*{unidade}{sufixo}", trecho,
            ):
                operadores.add(operador)
        for operador in ("<", ">"):
            if re.search(
                rf"(?<![<>=]){re.escape(operador)}\s*{numero}\s*{unidade}{sufixo}",
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


def conferir_vinculo_qualificacao(
    fontes: tuple[FonteDidatica, ...],
    referentes: tuple[ReferenteAncorado, ...],
    premissas: tuple[PremissaDidatica, ...],
    regras: tuple[RegraDidatica, ...],
    *, escopo: str, premissa_id: str, regra_id: str, rotulo: str,
) -> dict[str, object]:
    """Confere o encadeamento tipado, sem transformar texto em prova semantica.

    Identidade/atributo vêm do grafo ancorado, não de nova inferência aqui.
    Mesmo quando a condição é satisfeita, a relação textual regra→rótulo
    requer revisão independente antes de qualquer composição de fala.
    """
    base: dict[str, object] = {
        "estado": "vinculo_pendente",
        "comparacao_numerica": False,
        "relacao_semantica_verificada": False,
        "aprovado_para_compor": False,
        "autoriza_efeito": False,
    }

    def falha(estado: str) -> dict[str, object]:
        return {**base, "estado": estado}

    estrutura = conferir_grafo_premissas(
        fontes, referentes, premissas, regras, escopo=escopo,
    )
    if estrutura["estado"] != "estrutura_ancorada_revisao_pendente":
        return falha("grafo_invalido")
    if (not isinstance(premissa_id, str) or not isinstance(regra_id, str)
            or not isinstance(rotulo, str) or not rotulo.strip()):
        return falha("selecao_invalida")
    premissa = next((item for item in premissas
                     if item.identificador == premissa_id), None)
    regra = next((item for item in regras
                  if item.identificador == regra_id), None)
    if premissa is None or regra is None:
        return falha("selecao_invalida")
    if regra.efeito_valor.casefold() != rotulo.casefold():
        return falha("rotulo_divergente")
    if (len(regra.condicoes) != 1
            or regra.conectivo_condicoes != "unico"):
        return falha("regra_composta_pendente")
    if regra.direcao_implicacao != "condicoes_suficientes":
        return falha("direcao_implicacao_pendente")
    direcao_fonte = confrontar_direcao_marcador(
        regra.citacao, regra.direcao_implicacao,
    )
    if direcao_fonte["estado"] == "direcao_divergente_marcador":
        return falha("direcao_literal_divergente")
    if direcao_fonte["estado"] \
            != "direcao_compativel_marcador_revisao_pendente":
        return falha("direcao_literal_pendente")
    condicao = regra.condicoes[0]
    if (premissa.referente_id != condicao.referente_id
            or premissa.referente_id != regra.efeito_referente_id
            or premissa.atributo != condicao.atributo
            or premissa.unidade.casefold() != condicao.unidade.casefold()):
        return falha("referente_atributo_unidade_divergente")
    # O rótulo tipado pode ter vindo da pergunta, não do efeito da fonte.
    # Conferir a fonte integral impede que o proponente recorte uma negação
    # ou ressalva; a identidade do sujeito ainda exige revisão semântica.
    fonte_regra = next(item for item in fontes if item.identificador == regra.fonte_id)
    efeito = analisar_efeito_qualificativo(fonte_regra.texto, regra.efeito_valor)
    base["efeito_literal"] = efeito
    if efeito["estado"] != "efeito_qualificativo_literal_revisao_pendente":
        return falha("efeito_qualificativo_pendente")
    # Compatibilidade literal, não resolução semântica: a descrição inteira
    # deve corresponder a um único item ancorado. Grandeza, ID, substring e
    # menção na condição não substituem a descrição do sujeito do efeito.
    def nome_literal(texto: str) -> str:
        normalizado = re.sub(r"\s+", " ", texto.casefold()).strip()
        return re.sub(r"^(?:o|a|os|as)\s+", "", normalizado)

    sujeito = nome_literal(efeito["sujeito_literal"])
    candidatos = [item.referente.identificador for item in referentes
                  if nome_literal(item.citacao) == sujeito]
    base["sujeito_efeito"] = {
        "estado": "sujeito_efeito_pendente",
        "referentes_candidatos": candidatos,
        "identidade_verificada": False,
    }
    if candidatos != [regra.efeito_referente_id]:
        return falha("sujeito_efeito_pendente")
    base["sujeito_efeito"]["estado"] = "sujeito_literal_compativel_revisao_pendente"
    vinculos = auditar_vinculos_literais(
        fontes, referentes, premissas, regras, escopo=escopo,
    )
    if (vinculos["premissas"].get(premissa_id)
            != "referente_literal_localizado"
            or vinculos["condicoes"][regra_id][0]["referente"]
            != "referente_literal_localizado"
            or vinculos["efeitos"].get(regra_id)
            != "referente_literal_localizado"):
        return falha("vinculo_literal_pendente")
    if vinculos["condicoes"][regra_id][0]["direcao"] \
            != "direcao_literal_coerente":
        return falha("direcao_literal_pendente")
    if (not re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?", premissa.valor)
            or not re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?", condicao.valor)
            or condicao.operador not in {"<", ">", "<=", ">="}):
        return falha("comparacao_indeterminada")
    observado = Decimal(premissa.valor.replace(",", "."))
    limite = Decimal(condicao.valor.replace(",", "."))
    satisfeita = {"<": observado < limite, ">": observado > limite,
                  "<=": observado <= limite, ">=": observado >= limite}[condicao.operador]
    if not satisfeita:
        return falha("condicao_numerica_nao_satisfeita")
    return {**base,
            "estado": "condicao_numerica_satisfeita_relacao_pendente",
            "comparacao_numerica": True}


def conferir_qualificacao_na_conversa(
    fontes: tuple[FonteDidatica, ...],
    referentes: tuple[ReferenteAncorado, ...],
    premissas: tuple[PremissaDidatica, ...],
    regras: tuple[RegraDidatica, ...],
    *, escopo: str, premissa_id: str, regra_id: str, rotulo: str,
    texto_atual: str, mensagens: Sequence[object], registro_vigencia: object = None,
) -> dict[str, object]:
    """Ancora fontes propostas na fala real da sessão, sem aprovar a alegação.

    O grafo pode ser proposto por um modelo. Seu campo ``origem=usuario`` não
    prova autoria; a comparação usa mensagens recebidas pelo runtime. Uma
    fonte abreviada não substitui a fala integral, pois poderia omitir uma
    negação, exceção ou outra condição da regra.
    """
    base = {
        "estado": "fonte_pendente", "comparacao_numerica": False,
        "relacao_semantica_verificada": False,
        "aprovado_para_compor": False, "autoriza_efeito": False,
    }
    if (not isinstance(fontes, tuple) or not isinstance(regras, tuple)
            or not isinstance(texto_atual, str)
            or not isinstance(mensagens, Sequence)
            or isinstance(mensagens, (str, bytes))):
        return {**base, "estado": "entrada_invalida"}
    if not regras:
        return {**base, "estado": "qualificacao_sem_criterio_observado"}
    if any(not isinstance(fonte, FonteDidatica)
           or not isinstance(fonte.texto, str)
           or not isinstance(fonte.origem, str)
           for fonte in fontes):
        return {**base, "estado": "entrada_invalida"}
    observadas = set(fontes_usuario_da_conversa(
        texto_atual, mensagens,
    ).values())
    for fonte in fontes:
        if fonte.origem != "usuario":
            # Pesquisa demanda registro/validação próprios, não uma declaração
            # textual do proponente; este adaptador só confere fala do usuário.
            return {**base, "estado": "fonte_sem_registro_confiavel"}
        if fonte.texto not in observadas:
            return {**base, "estado": "fonte_nao_observada"}
    from scripts.analises.contrato_vigencia_criterios import conferir_contexto_criterio

    estrutura = conferir_grafo_premissas(
        fontes, referentes, premissas, regras, escopo=escopo,
    )
    if estrutura["estado"] != "estrutura_ancorada_revisao_pendente":
        return {**base, "estado": "grafo_invalido"}
    contexto = conferir_contexto_criterio(
        fontes, referentes, premissas, regras, escopo=escopo,
        premissa_id=premissa_id, regra_id=regra_id,
        texto_atual=texto_atual, mensagens=mensagens, registro=registro_vigencia,
    )
    if contexto["estado"] != "contexto_conferido":
        return contexto
    resultado = conferir_vinculo_qualificacao(
        fontes, referentes, premissas, regras, escopo=escopo,
        premissa_id=premissa_id, regra_id=regra_id, rotulo=rotulo,
    )
    return {**resultado, "vigencia": contexto["vigencia"]}
