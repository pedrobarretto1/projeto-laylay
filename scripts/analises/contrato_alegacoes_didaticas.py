"""Contrato offline para propostas de alegações de uma fala didática inteira.

O modelo pode propor papéis e citações, mas fontes registradas vêm do chamador.
Cobertura dos caracteres e cópia literal são recibos formais, não implicação.
Nenhum resultado desta sonda autoriza publicação, efeito ou veto de fala.
"""

from __future__ import annotations

from decimal import Decimal
import re
from typing import Mapping, Sequence


_PAPEIS = frozenset({
    "premissa_usuario", "regra_hipotetica", "comparacao_numerica",
    "conclusao_derivada", "fato_externo", "nao_factual",
})
_ORIGENS_CITAVEIS = frozenset({"usuario", "pesquisa_verificada"})
_LIMIAR_QUALITATIVO = re.compile(
    r"\b(?P<operador>abaixo\s+de|menor\s+(?:do\s+)?que|"
    r"acima\s+de|maior\s+(?:do\s+)?que|a\s+partir\s+de|"
    r"no\s+m[aá]ximo|at[eé])\s+"
    r"(?P<valor>[+-]?\d+(?:[.,]\d+)?)\s*"
    r"(?P<unidade>%|°\s*[cf]|[a-zA-Z]{1,5})(?!\w)",
    flags=re.IGNORECASE,
)


def _conferir_limiar_qualitativo(
    citacoes: list[str], *, valor: str, unidade: str,
) -> str:
    """Confere somente uma desigualdade literal; relacao continua pendente."""
    if len(citacoes) != 1:
        return "criterio_relacao_indeterminada"
    citacao = citacoes[0]
    if re.search(r"\b(?:não|nao|nunca|nem)\b", citacao, re.IGNORECASE):
        return "criterio_relacao_indeterminada"
    limiares = list(_LIMIAR_QUALITATIVO.finditer(citacao))
    if not limiares:
        return "criterio_candidato_revisao_pendente"
    if len(limiares) != 1:
        return "criterio_relacao_indeterminada"
    limiar = limiares[0]
    unidade_citada = limiar["unidade"].replace(" ", "").casefold()
    if unidade_citada != unidade.replace(" ", "").casefold():
        return "criterio_unidade_divergente"
    observado = Decimal(valor.replace(",", "."))
    limite = Decimal(limiar["valor"].replace(",", "."))
    operador = " ".join(limiar["operador"].casefold().split())
    if operador.startswith(("abaixo", "menor")):
        satisfeito = observado < limite
    elif operador.startswith(("acima", "maior")):
        satisfeito = observado > limite
    elif operador.startswith("a partir"):
        satisfeito = observado >= limite
    else:
        satisfeito = observado <= limite
    return ("criterio_numerico_satisfeito_relacao_pendente" if satisfeito
            else "criterio_numerico_nao_satisfeito")


def _conferir_qualificacao_proposta(
    trecho: str, evidencias: list[object], derivacao: object,
    fontes: Mapping[str, Mapping[str, str]],
) -> str:
    """Uma medida nao autoriza, por si so, um rotulo qualitativo.

    Mesmo um criterio citado continua pendente de verificacao semantica;
    esta fronteira so demonstra ausencias e incompatibilidades formais.
    """
    campos = {"tipo", "referente_id", "atributo", "valor", "unidade",
              "rotulo", "medida_fonte_id", "criterio_fonte_id"}
    if (not isinstance(derivacao, Mapping) or set(derivacao) != campos
            or derivacao.get("tipo") != "qualificacao_qualitativa"
            or any(not isinstance(derivacao[chave], str)
                   for chave in campos)
            or any(not derivacao[chave].strip() for chave in campos - {
                "criterio_fonte_id",
            })
            or not re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?",
                                derivacao["valor"])):
        return "derivacao_invalida"
    rotulo = derivacao["rotulo"].casefold()
    if not re.search(rf"(?<!\w){re.escape(rotulo)}(?!\w)", trecho.casefold()):
        return "rotulo_nao_literal"
    medida_id = derivacao["medida_fonte_id"]
    medida = fontes.get(medida_id)
    citacoes_medida = [
        item.get("citacao") for item in evidencias
        if isinstance(item, Mapping) and item.get("fonte_id") == medida_id
    ]
    padrao_medida = (
        rf"(?<![\d.,]){re.escape(derivacao['valor'])}\s*"
        rf"{re.escape(derivacao['unidade'])}(?![\d.,])"
    )
    if (not isinstance(medida, Mapping) or not citacoes_medida
            or not any(isinstance(citacao, str)
                       and re.search(padrao_medida, citacao, re.IGNORECASE)
                       for citacao in citacoes_medida)):
        return "medida_sem_ancora_literal"
    criterio_id = derivacao["criterio_fonte_id"]
    if not criterio_id:
        return "qualificacao_sem_criterio"
    criterio = fontes.get(criterio_id)
    if (not isinstance(criterio, Mapping)
            or not isinstance(criterio.get("origem"), str)
            or criterio.get("origem") not in _ORIGENS_CITAVEIS
            or not isinstance(criterio.get("texto"), str)):
        return "criterio_sem_fonte_valida"
    citacoes_criterio = [
        item["citacao"] for item in evidencias
        if isinstance(item, Mapping)
        and item.get("fonte_id") == criterio_id
        and isinstance(item.get("citacao"), str)
        and re.search(rf"(?<!\w){re.escape(rotulo)}(?!\w)",
                      item["citacao"].casefold())
    ]
    if not citacoes_criterio:
        return "criterio_sem_citacao_do_rotulo"
    return _conferir_limiar_qualitativo(
        citacoes_criterio, valor=derivacao["valor"],
        unidade=derivacao["unidade"],
    )


def conferir_mapa_alegacoes(
    fala: str, *, fontes: Mapping[str, Mapping[str, str]],
    propostas: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Confere envelope textual e citações; deixa semântica para revisão.

    Não assume que os intervalos propostos são de fato alegações atômicas.
    ``pesquisa_verificada`` deve ser atribuída por outro serviço confiável,
    nunca pelo JSON proposto pelo modelo.
    """
    base: dict[str, object] = {
        "cobertura_textual": False,
        "atomizacao_verificada": False,
        "papeis_verificados": False,
        "condicoes_verificadas": False,
        "implicacao_verificada": False,
        "aprovado_para_compor": False,
        "autoriza_efeito": False,
        "alegacoes": [],
    }
    if (not isinstance(fala, str) or not fala or len(fala) > 4000
            or not isinstance(fontes, Mapping)
            or not isinstance(propostas, (list, tuple))
            or not propostas or len(propostas) > 128):
        return {**base, "estado": "entrada_invalida"}
    posicao = 0
    for proposta in propostas:
        if not isinstance(proposta, Mapping):
            return {**base, "estado": "proposta_invalida"}
        inicio, fim = proposta.get("inicio"), proposta.get("fim")
        if (type(inicio) is not int or type(fim) is not int
                or inicio != posicao or not inicio < fim <= len(fala)
                or not isinstance(proposta.get("papel"), str)
                or proposta.get("papel") not in _PAPEIS
                or not isinstance(proposta.get("evidencias"), list)
                or len(proposta["evidencias"]) > 16):
            return {**base, "estado": "cobertura_invalida"}
        posicao = fim
    if posicao != len(fala):
        return {**base, "estado": "cobertura_invalida"}

    alegacoes: list[dict[str, object]] = []
    for proposta in propostas:
        evidencias = proposta["evidencias"]
        estado = "revisao_semantica_pendente"
        if proposta["papel"] == "nao_factual":
            estado = "nao_factual_proposto_revisao_pendente"
        elif not evidencias:
            estado = "sem_fonte"
        else:
            for evidencia in evidencias:
                if not isinstance(evidencia, Mapping):
                    estado = "evidencia_invalida"
                    break
                identificador = evidencia.get("fonte_id")
                fonte = fontes.get(identificador) if isinstance(identificador, str) else None
                if not isinstance(fonte, Mapping):
                    estado = "fonte_desconhecida"
                    break
                origem = fonte.get("origem")
                if not isinstance(origem, str) or origem not in _ORIGENS_CITAVEIS:
                    estado = "fonte_sem_autoridade"
                    break
                citacao = evidencia.get("citacao")
                texto_fonte = fonte.get("texto")
                if (not isinstance(citacao, str) or not citacao.strip()
                        or not isinstance(texto_fonte, str)
                        or citacao not in texto_fonte):
                    estado = "citacao_invalida"
                    break
        fontes_conferidas = estado == "revisao_semantica_pendente"
        if fontes_conferidas and "derivacao" in proposta:
            estado = _conferir_qualificacao_proposta(
                fala[proposta["inicio"]:proposta["fim"]], evidencias,
                proposta["derivacao"], fontes,
            )
        alegacoes.append({
            "inicio": proposta["inicio"], "fim": proposta["fim"],
            "texto": fala[proposta["inicio"]:proposta["fim"]],
            "papel_proposto": proposta["papel"],
            "estado": estado,
            "fontes_literalmente_conferidas": fontes_conferidas,
        })
    pendencias = {item["estado"] for item in alegacoes}
    return {
        **base,
        "estado": (
            "evidencia_invalida" if pendencias & {
            "evidencia_invalida", "fonte_desconhecida",
                "fonte_sem_autoridade", "citacao_invalida",
            } else "alegacoes_criterio_incompativel"
            if pendencias & {"criterio_numerico_nao_satisfeito",
                            "criterio_unidade_divergente"}
            else "alegacoes_sem_criterio"
            if "qualificacao_sem_criterio" in pendencias
            else "alegacoes_sem_fonte" if "sem_fonte" in pendencias
            else "papeis_semanticos_pendentes"
            if "nao_factual_proposto_revisao_pendente" in pendencias
            else "cobertura_formal_revisao_pendente"
        ),
        "cobertura_textual": True,
        "alegacoes": alegacoes,
    }
