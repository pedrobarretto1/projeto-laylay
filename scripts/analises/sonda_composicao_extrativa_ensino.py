"""Protótipo offline: evidência escolhida antes da fala, sem reescrita factual.

Os casos reais têm seleção manual de trechos; isto prova transporte e
ausência de acréscimos, NÃO descoberta automática, relevância ou verdade
externa das páginas. Nenhum componente da Laylay usa esta composição.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping
from urllib.parse import urlparse

from mente_laylay.cognicao.pesquisa_multifonte import _INSTRUCAO_EXTERNA
from scripts.analises.contrato_unidades_ensino import extrair_contas_explicitas
from scripts.analises.sonda_fala_integral_real import carregar_caso


_ANA_FORA_DE_CONTEXTO = re.compile(
    r"^(?:os|as)\s+exemplos\b|^(?:isso|essa|esse|ela|ele|eles|elas)\b",
    re.IGNORECASE,
)
_PAPEIS = frozenset({"definicao", "exemplo"})


def _normalizar_forma(texto: str) -> str:
    sem_espacos = re.sub(r"\s+", " ", str(texto or "")).strip()
    return re.sub(r"\s+([.,;:!?])", r"\1", sem_espacos)


def _sentenca_iniciada_por(texto: str, inicio: str) -> str:
    posicao = texto.find(inicio)
    if posicao < 0:
        raise ValueError(f"início de sentença ausente: {inicio}")
    fim = texto.find(".", posicao)
    if fim < 0:
        raise ValueError(f"sentença incompleta: {inicio}")
    return texto[posicao:fim + 1]


def validar_unidade(
    proposta: Mapping[str, str],
    fontes: Mapping[str, Mapping[str, str]],
    pedido: str,
) -> dict[str, Any]:
    """Valida proveniência textual ou cálculo; não julga a verdade da fonte."""
    tipo = proposta.get("tipo")
    if tipo == "conta":
        expressao = _normalizar_forma(proposta.get("texto") or "")
        contas = extrair_contas_explicitas(expressao)
        if len(contas) != 1 or contas[0]["inicio"] != 0 or contas[0]["fim"] != len(expressao):
            return {"estado": "conta_nao_integral"}
        if contas[0]["estado"] != "calculo_conferido":
            return {"estado": contas[0]["estado"]}
        numeros = re.findall(r"\b\d+\b", expressao)
        if not all(re.search(rf"(?<!\d){re.escape(valor)}(?!\d)", pedido) for valor in numeros[:2]):
            return {"estado": "operandos_sem_pedido"}
        return {"estado": "conta_conferida", "tipo": tipo, "papel": "exemplo",
                "texto": expressao, "verdade_externa_verificada": False,
                "mapeamento_de_entidades_verificado": False}

    if tipo != "literal" or proposta.get("papel") not in _PAPEIS:
        return {"estado": "tipo_ou_papel_invalido"}
    fonte_id = str(proposta.get("fonte_id") or "")
    fonte = fontes.get(fonte_id)
    if not isinstance(fonte, Mapping):
        return {"estado": "fonte_ausente"}
    url = str(fonte.get("url") or "")
    url_lida = urlparse(url)
    if url_lida.scheme not in {"http", "https"} or not url_lida.netloc:
        return {"estado": "url_invalida"}
    original = _normalizar_forma(proposta.get("trecho") or "")
    corpo = _normalizar_forma(fonte.get("trecho") or "")
    apresentado = _normalizar_forma(proposta.get("texto") or original)
    if not original or original not in corpo:
        return {"estado": "trecho_ausente"}
    if not original.endswith((".", "!", "?")):
        return {"estado": "trecho_incompleto"}
    if _INSTRUCAO_EXTERNA.search(original):
        return {"estado": "instrucao_externa"}
    if apresentado.casefold() != original.casefold():
        return {"estado": "reescrita_factual"}
    if _ANA_FORA_DE_CONTEXTO.search(original) and not corpo.startswith(original):
        return {"estado": "referencia_sem_antecedente"}
    return {"estado": "literal_rastreavel", "tipo": tipo,
            "papel": proposta["papel"], "texto": apresentado,
            "fonte_id": fonte_id, "url": url,
            "verdade_externa_verificada": False}


def compor_fala(
    propostas: list[Mapping[str, str]],
    fontes: Mapping[str, Mapping[str, str]],
    pedido: str,
) -> dict[str, Any]:
    unidades = [validar_unidade(item, fontes, pedido) for item in propostas]
    problemas = [item["estado"] for item in unidades if item["estado"] not in {
        "literal_rastreavel", "conta_conferida",
    }]
    if problemas:
        return {"estado": "evidencia_invalida", "problemas": problemas, "fala": ""}
    if not any(item["papel"] == "definicao" for item in unidades) or not any(
        item["papel"] == "exemplo" for item in unidades
    ):
        return {"estado": "aula_incompleta", "problemas": [], "fala": ""}
    fala = "Vamos por partes."
    atribuicoes: list[dict[str, Any]] = []
    for unidade in unidades:
        if unidade["tipo"] == "conta":
            # Os números vieram do pedido, mas seu papel semântico não foi
            # validado. Não dizer que esta é necessariamente a conta pedida.
            prefixo = " Com esses números, "
            inicio = len(fala) + len(prefixo)
            fala += prefixo + unidade["texto"] + "."
            atribuicoes.append({"inicio": inicio, "fim": inicio + len(unidade["texto"]),
                                "tipo": "calculo", "fonte_id": ""})
        else:
            inicio = len(fala) + 1
            fala += " " + unidade["texto"]
            atribuicoes.append({"inicio": inicio, "fim": inicio + len(unidade["texto"]),
                                "tipo": "fonte_literal", "fonte_id": unidade["fonte_id"],
                                "url": unidade["url"]})
    return {
        "estado": "forma_rastreavel", "fala": fala,
        "unidades": unidades,
        "atribuicoes": atribuicoes,
        "verdade_externa_verificada": False,
        "naturalidade_revisada": False,
        "aprovado_para_producao": False,
    }


def auditar_saida(
    fala: str,
    propostas: list[Mapping[str, str]],
    fontes: Mapping[str, Mapping[str, str]],
    pedido: str,
) -> dict[str, bool]:
    """Compara a fala integral ao único render permitido; não julga fontes."""
    reconstruido = compor_fala(propostas, fontes, pedido)
    return {
        "forma_integral_preservada": bool(
            reconstruido["estado"] == "forma_rastreavel" and fala == reconstruido["fala"]
        ),
        "verdade_externa_verificada": False,
        "aprovado_para_producao": False,
    }


def casos_manuais_reais() -> dict[str, dict[str, Any]]:
    """Recorta fontes já capturadas; não representa recuperador automático."""
    divisao = carregar_caso("divisao")
    luz = carregar_caso("luz")
    floricultura = carregar_caso("floricultura")
    arquitetura = carregar_caso("arquitetura")
    divisao_fonte = divisao["fontes"]["F5"]
    luz_fonte = luz["fontes"]
    flora_fonte = floricultura["fontes"]
    return {
        "divisao": {"pedido": divisao["pedido"], "fontes": divisao["fontes_metadados"],
                    "propostas": [
                        {"tipo": "literal", "papel": "definicao", "fonte_id": "F5",
                         "trecho": (sentenca := _sentenca_iniciada_por(divisao_fonte, "SEMPRE QUE QUEREMOS")),
                         "texto": sentenca.capitalize()},
                        {"tipo": "conta", "texto": "12 / 3 = 4"},
                    ]},
        "luz": {"pedido": luz["pedido"], "fontes": luz["fontes_metadados"],
                "propostas": [
                    {"tipo": "literal", "papel": "definicao", "fonte_id": "F2",
                     "trecho": _sentenca_iniciada_por(luz_fonte["F2"], "A luz é muito")},
                    {"tipo": "literal", "papel": "exemplo", "fonte_id": "F3",
                     "trecho": _sentenca_iniciada_por(luz_fonte["F3"], "Um exemplo claro")},
                ]},
        "floricultura": {"pedido": floricultura["pedido"],
                         "fontes": floricultura["fontes_metadados"], "propostas": [
                             {"tipo": "literal", "papel": "definicao", "fonte_id": "F2",
                              "trecho": _sentenca_iniciada_por(flora_fonte["F2"], "As plantas anuais")},
                             {"tipo": "literal", "papel": "definicao", "fonte_id": "F3",
                              "trecho": _sentenca_iniciada_por(flora_fonte["F3"], "Enquanto as flores")},
                             {"tipo": "literal", "papel": "exemplo", "fonte_id": "F1",
                              "trecho": flora_fonte["F1"]},
                         ]},
        "arquitetura_sem_fonte": {"pedido": arquitetura["pedido"],
                                  "fontes": arquitetura["fontes_metadados"],
                                  "propostas": []},
    }


def main() -> None:
    for nome, dados in casos_manuais_reais().items():
        resultado = compor_fala(dados["propostas"], dados["fontes"], dados["pedido"])
        print(json.dumps({"caso": nome, "resultado": resultado}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
