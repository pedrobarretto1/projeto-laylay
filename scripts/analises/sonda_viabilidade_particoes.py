"""Avalia cada partição isoladamente; somente experimento offline P01.

Um parecer do modelo pode ser falso mesmo com citação literal. Nenhum estado
deste módulo valida semântica, fala, treino, runtime ou efeito externo.
"""

from __future__ import annotations

from typing import Callable, Mapping

from scripts.analises.sonda_avaliador_fronteira_independente import (
    preparar_entrada,
    preparar_pares,
)
from scripts.analises.veto_superficie_sujeito_composto import (
    conferir_numero_condicao_curta,
)


FORMATO_VIABILIDADE = {
    "type": "object", "additionalProperties": False,
    "required": ["viabilidade", "motivo", "citacao"],
    "properties": {
        "viabilidade": {
            "type": "string",
            "enum": ["viavel", "inviavel", "incerta"],
        },
        "motivo": {
            "type": "string",
            "enum": ["nenhum", "concordancia", "semantica", "incerteza"],
        },
        "citacao": {"type": "string"},
    },
}
SISTEMA_VIABILIDADE = (
    "A frase_com_leitura preserva o 'Se' e o efeito originais. Os parênteses "
    "marcam duas condições; não fazem parte do texto-fonte. Julgue APENAS "
    "esta leitura, sem comparar com outras e sem reescrever palavras. Ela "
    "é gramaticalmente e semanticamente possível? "
    "Uma leitura menos natural ainda é viável. Se ambas as condições "
    "forem possíveis, use viavel/nenhum/citacao vazia. Se houver erro "
    "demonstrável de concordância entre sujeito e verbo, use "
    "inviavel/concordancia e copie em citacao a condição inteira que "
    "contém o erro. Se houver impossibilidade semântica direta, use "
    "inviavel/semantica e copie a condição inteira. Se não puder decidir, "
    "use incerta/incerteza/citacao vazia. Não trate preferência de leitura "
    "como impossibilidade. Não converse nem execute ações."
)


def _base(estado: str) -> dict[str, object]:
    return {"estado": estado, "aprovado_para_producao": False,
            "autoriza_efeito": False}


def validar_parecer(
    trechos_condicoes: list[str], bruto: object,
) -> dict[str, object]:
    if (not isinstance(bruto, Mapping)
            or set(bruto) != {"viabilidade", "motivo", "citacao"}
            or not all(isinstance(bruto[chave], str)
                       for chave in ("viabilidade", "motivo", "citacao"))):
        return _base("parecer_invalido")
    viabilidade = bruto["viabilidade"]
    motivo = bruto["motivo"]
    citacao = bruto["citacao"]
    if viabilidade == "viavel" and motivo == "nenhum" and not citacao:
        for trecho in trechos_condicoes:
            sinal = conferir_numero_condicao_curta(trecho)
            if sinal["estado"] == "numero_divergente":
                return {**_base("conflito_viabilidade_superficial"),
                        "citacao": trecho, "sinal_independente": sinal}
        return {**_base("viabilidade_alegada_revisao_pendente"),
                "viabilidade": viabilidade}
    if viabilidade == "incerta" and motivo == "incerteza" and not citacao:
        return {**_base("incerteza_modelo"), "viabilidade": viabilidade}
    normalizacao = "nenhuma"
    if (citacao not in trechos_condicoes and citacao.startswith("(")
            and citacao.endswith(")")
            and citacao[1:-1] in trechos_condicoes):
        citacao = citacao[1:-1]
        normalizacao = "parenteses_da_sonda"
    if (viabilidade == "inviavel"
            and motivo in {"concordancia", "semantica"}
            and citacao in trechos_condicoes):
        if motivo == "semantica":
            # A citacao prova apenas o alinhamento literal, nao a impossibilidade.
            # Sem corroboracao externa, essa alegacao nao elimina uma leitura.
            return {**_base("semantica_nao_corroborada"),
                    "citacao": citacao, "normalizacao": normalizacao}
        sinal: dict[str, object] | None = None
        if motivo == "concordancia":
            sinal = conferir_numero_condicao_curta(citacao)
            if sinal["estado"] == "numero_convergente":
                return {**_base("conflito_concordancia_superficial"),
                        "citacao": citacao, "sinal_independente": sinal}
            if sinal["estado"] != "numero_divergente":
                return {**_base("concordancia_nao_corroborada"),
                        "citacao": citacao, "sinal_independente": sinal}
        return {**_base("inviabilidade_alegada_revisao_pendente"),
                "viabilidade": viabilidade, "motivo": motivo,
                "citacao": citacao, "normalizacao": normalizacao,
                **({"sinal_independente": sinal} if sinal is not None else {})}
    return _base("parecer_invalido")


def concluir_pareceres(
    pareceres: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    if set(pareceres) != {"objeto_anterior", "sujeito_seguinte"}:
        return _base("abstencao_pareceres_incompletos")
    objeto = pareceres["objeto_anterior"]
    sujeito = pareceres["sujeito_seguinte"]
    estados = (objeto.get("viabilidade"), sujeito.get("viabilidade"))
    estados_validados = {
        "viavel": "viabilidade_alegada_revisao_pendente",
        "inviavel": "inviabilidade_alegada_revisao_pendente",
        "incerta": "incerteza_modelo",
    }
    if any(valor not in estados_validados
           or parecer.get("estado") != estados_validados[valor]
           for valor, parecer in zip(estados, (objeto, sujeito))):
        return _base("abstencao_pareceres_invalidos")
    if estados == ("viavel", "viavel"):
        return {**_base("ambiguidade_proposta_revisao_pendente"),
                "relacao_proposta": "indeterminado"}
    if estados == ("viavel", "inviavel"):
        return {**_base("relacao_proposta_revisao_pendente"),
                "relacao_proposta": "objeto_anterior"}
    if estados == ("inviavel", "viavel"):
        return {**_base("relacao_proposta_revisao_pendente"),
                "relacao_proposta": "sujeito_seguinte"}
    return _base("abstencao_viabilidade_insuficiente")


def propor_viabilidade(
    caso: Mapping[str, object],
    consultar: Callable[..., object],
) -> dict[str, object]:
    preparada = preparar_pares(caso)
    if preparada["estado"] != "pares_literais_preparados":
        return _base("abstencao_estrutura_lexical")
    literal = preparar_entrada(caso)["entrada"]
    fonte = literal["fonte"]
    anterior, _meio, seguinte = literal["fragmentos"]
    prefixo = fonte[:anterior["inicio"]]
    sufixo = fonte[seguinte["fim"]:]
    pareceres: dict[str, dict[str, object]] = {}
    for leitura in preparada["entrada"]["leituras"]:
        relacao = leitura["relacao"]
        trechos = leitura["trechos_condicoes"]
        bruto = consultar(
            SISTEMA_VIABILIDADE,
            {"frase_com_leitura": (
                f"{prefixo}({trechos[0]}) e ({trechos[1]}){sufixo}"
             ), "trechos_condicoes": trechos},
            FORMATO_VIABILIDADE,
        )
        pareceres[relacao] = {
            **validar_parecer(trechos, bruto), "resposta_bruta": bruto,
        }
    return {**concluir_pareceres(pareceres), "pareceres": pareceres}
