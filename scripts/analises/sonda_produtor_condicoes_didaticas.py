"""Sonda offline do Qwen para condições de regras; nunca publica ou executa."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Mapping

from mente_laylay.cognicao.contrato_inventario_contextual import ReferenteContextual
from scripts.analises.avaliar_grafo_premissas import confrontar_condicoes_revisadas
from scripts.analises.grafo_premissas_didaticas import (
    CondicaoDidatica, FonteDidatica, ReferenteAncorado, RegraDidatica,
    conferir_grafo_premissas,
)


DADOS = Path(__file__).parent / "dados"
ENTRADAS = DADOS / "sonda_condicoes_entradas_v1.json"
GABARITO = DADOS / "sonda_condicoes_gabarito_v1.json"


def carregar_painel() -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    entradas = json.loads(ENTRADAS.read_text(encoding="utf-8"))["casos"]
    gabarito = json.loads(GABARITO.read_text(encoding="utf-8"))["casos"]
    return entradas, gabarito


def preparar_entrada_modelo(caso: Mapping[str, object]) -> dict[str, object]:
    return {
        "fonte": caso["fonte"], "referentes": caso["referentes"],
        "efeito": caso["efeito"],
    }


def conferir_proposta(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    bruto: object,
) -> dict[str, object]:
    """Mede proposta contra revisão local; jamais a promove a fala ou efeito."""
    base = {"estado": "entrada_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    if not isinstance(bruto, Mapping) or not isinstance(gabarito, Mapping):
        return base
    if type(gabarito.get("representavel")) is not bool:
        return base
    if set(bruto) != {"representavel", "condicoes", "conectivo_condicoes",
                      "direcao_implicacao"} or type(bruto["representavel"]) is not bool:
        return base
    condicoes = bruto["condicoes"]
    if not isinstance(condicoes, list) or len(condicoes) > 8:
        return base
    if bruto["representavel"] is False:
        if (condicoes or bruto["conectivo_condicoes"] != "indeterminado"
                or bruto["direcao_implicacao"] != "indeterminado"):
            return base
        return {**base, "estado": ("abstencao_em_regra_representavel"
                                  if gabarito["representavel"] is True
                                  else "abstencao_compativel")}
    if gabarito.get("representavel") is False:
        return {**base, "estado": "forcou_regra_nao_representavel"}
    if gabarito.get("representavel") is not True:
        return base

    campos = {"referente_id", "atributo", "operador", "valor", "unidade",
              "fonte_id", "citacao"}
    for item in condicoes:
        if (not isinstance(item, Mapping) or set(item) != campos
                or any(not isinstance(item[campo], str)
                       or len(item[campo]) > 300 for campo in campos)):
            return base
    if not condicoes:
        return base
    try:
        escopo = caso["escopo"]
        fonte_texto = caso["fonte"]
        efeito = caso["efeito"]
        fonte = FonteDidatica("regra", "usuario", escopo, fonte_texto)
        referentes = tuple(
            ReferenteAncorado(
                ReferenteContextual(item["identificador"], item["tipo"],
                                    item["grandeza"], "usuario", escopo),
                "regra", item["citacao"],
            ) for item in caso["referentes"]
        )

        def montar_regra(dados: Mapping[str, object]) -> RegraDidatica:
            return RegraDidatica(
                "r1", tuple(CondicaoDidatica(**item) for item in dados["condicoes"]),
                efeito["referente_id"], efeito["atributo"], efeito["valor"],
                "regra", fonte_texto, dados["conectivo_condicoes"],
                dados["direcao_implicacao"],
            )

        proposta = montar_regra(bruto)
        referencia = montar_regra(gabarito)
    except (KeyError, TypeError, ValueError, AttributeError):
        return base

    estrutura = conferir_grafo_premissas(
        (fonte,), referentes, (), (proposta,), escopo=escopo,
    )
    if estrutura["estado"] != "estrutura_ancorada_revisao_pendente":
        return {**base, "estado": "proposta_invalida",
                "motivo": estrutura["estado"]}
    confronto = confrontar_condicoes_revisadas(
        (fonte,), referentes, (proposta,), (referencia,), escopo=escopo,
    )
    return {**confronto, "aprovado_para_producao": False,
            "autoriza_efeito": False}


def _formato_resposta() -> dict[str, object]:
    condicao = {
        "type": "object", "additionalProperties": False,
        "required": ["referente_id", "atributo", "operador", "valor",
                     "unidade", "fonte_id", "citacao"],
        "properties": {nome: {"type": "string"} for nome in (
            "referente_id", "atributo", "operador", "valor", "unidade",
            "fonte_id", "citacao",
        )},
    }
    return {
        "type": "object", "additionalProperties": False,
        "required": ["representavel", "condicoes", "conectivo_condicoes",
                     "direcao_implicacao"],
        "properties": {
            "representavel": {"type": "boolean"},
            "condicoes": {"type": "array", "items": condicao, "maxItems": 8},
            "conectivo_condicoes": {"type": "string", "enum": [
                "unico", "e", "ou", "indeterminado",
            ]},
            "direcao_implicacao": {"type": "string", "enum": [
                "condicoes_suficientes", "condicoes_necessarias",
                "equivalencia", "indeterminado",
            ]},
        },
    }


def medir_caso(caso: Mapping[str, object], gabarito: Mapping[str, object],
               *, url: str = "http://127.0.0.1:11434/api/chat",
               modelo: str = "qwen3:4b-instruct") -> dict[str, object]:
    """Consulta local única e mede; não persiste, ensina, executa ou publica."""
    import requests

    sistema = (
        "Extraia apenas a estrutura lógica da fonte fornecida. O efeito e os "
        "referentes já estão fixos; proponha somente as condições da regra. "
        "Use exatamente os identificadores fornecidos, fonte_id='regra' e "
        "citações literais contíguas da fonte. Não invente fatos ou condições. "
        "'Se condições, efeito' indica condições suficientes; 'efeito somente "
        "quando condições' indica condições necessárias; 'se e somente se' "
        "indica equivalência. Para uma condição use 'unico'; para múltiplas, "
        "indique 'e' ou 'ou'. Se a regra exigir árvore aninhada/mistura de e e "
        "ou que um conectivo plano não representa, responda representavel=false, "
        "condicoes=[], e ambos os rótulos indeterminado. Não responda ao usuário."
    )
    inicio = time.monotonic()
    try:
        resposta = requests.post(
            url,
            json={"model": modelo, "stream": False, "format": _formato_resposta(),
                  "options": {"temperature": 0, "num_predict": 900},
                  "messages": [
                      {"role": "system", "content": sistema},
                      {"role": "user", "content": json.dumps(
                          preparar_entrada_modelo(caso), ensure_ascii=False,
                      )},
                  ]},
            timeout=90,
        )
        resposta.raise_for_status()
        texto_resposta = resposta.json()["message"]["content"]
        bruto = json.loads(texto_resposta)
        afericao = conferir_proposta(caso, gabarito, bruto)
        return {"id": caso["id"], "duracao_s": round(time.monotonic()-inicio, 2),
                "proposta": bruto, "afericao": afericao}
    except (requests.RequestException, KeyError, TypeError, ValueError) as erro:
        return {"id": caso["id"], "duracao_s": round(time.monotonic()-inicio, 2),
                "erro": type(erro).__name__, "aprovado_para_producao": False}


def main() -> None:
    entradas, gabarito = carregar_painel()
    for caso in entradas:
        resultado = medir_caso(caso, gabarito[caso["id"]])
        print(json.dumps(resultado, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
