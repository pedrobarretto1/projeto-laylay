"""Piloto offline de produtor de regras em dois estágios; sem runtime."""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Mapping

from scripts.analises.sonda_produtor_condicoes_didaticas import (
    conferir_proposta, preparar_entrada_modelo,
)


DADOS = Path(__file__).parent / "dados"


def _ancorar_trecho(fonte: str, trecho: str) -> str | None:
    """Recupera grafia literal única da fonte sem aceitar paráfrase/acento novo."""
    ocorrencias = list(re.finditer(re.escape(trecho), fonte, flags=re.IGNORECASE))
    if len(ocorrencias) != 1:
        return None
    return ocorrencias[0].group()


def _mesma_condicao_em_superficie(observado: str, esperado: str) -> bool:
    """Admite só artigo/`se` inicial; nunca junta cláusulas nem remove negação."""
    if observado == esperado:
        return True
    if not observado.endswith(esperado):
        return False
    prefixo = observado[:-len(esperado)]
    return bool(re.fullmatch(r"\s*(?:se\s+)?(?:(?:o|a|os|as)\s+)?",
                             prefixo, flags=re.IGNORECASE))


def carregar_painel(
    versao: int = 2,
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    if versao not in {2, 3}:
        raise ValueError("painel desconhecido")
    entradas_arquivo = DADOS / f"sonda_condicoes_entradas_v{versao}.json"
    gabarito_arquivo = DADOS / f"sonda_condicoes_gabarito_v{versao}.json"
    entradas = json.loads(entradas_arquivo.read_text(encoding="utf-8"))["casos"]
    gabarito = json.loads(gabarito_arquivo.read_text(encoding="utf-8"))["casos"]
    return entradas, gabarito


def conferir_trechos(caso: Mapping[str, object], bruto: object) -> dict[str, object]:
    base = {"estado": "entrada_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    campos = {"representavel", "trechos_condicoes", "conectivo_condicoes",
              "direcao_implicacao"}
    if (not isinstance(bruto, Mapping) or set(bruto) != campos
            or type(bruto["representavel"]) is not bool
            or not isinstance(bruto["trechos_condicoes"], list)
            or len(bruto["trechos_condicoes"]) > 8
            or not isinstance(bruto["conectivo_condicoes"], str)
            or not isinstance(bruto["direcao_implicacao"], str)
            or bruto["conectivo_condicoes"] not in {
                "unico", "e", "ou", "indeterminado",
            } or bruto["direcao_implicacao"] not in {
                "condicoes_suficientes", "condicoes_necessarias",
                "equivalencia", "indeterminado",
            }):
        return base
    trechos = bruto["trechos_condicoes"]
    if not bruto["representavel"]:
        if (trechos or bruto["conectivo_condicoes"] != "indeterminado"
                or bruto["direcao_implicacao"] != "indeterminado"):
            return base
        return {**base, "estado": "abstencao_estrutural"}
    if (not trechos or any(not isinstance(item, str) or not item.strip()
                           or len(item) > 300 for item in trechos)
            or (len(trechos) == 1 and bruto["conectivo_condicoes"] in {"e", "ou"})
            or (len(trechos) > 1 and bruto["conectivo_condicoes"] == "unico")):
        return base
    fonte = caso.get("fonte")
    ancorados = ([_ancorar_trecho(fonte, item) for item in trechos]
                 if isinstance(fonte, str) else [])
    if not ancorados or any(item is None for item in ancorados):
        return {**base, "estado": "citacao_invalida"}
    if len(ancorados) != len(set(ancorados)):
        return {**base, "estado": "trecho_duplicado"}
    return {**base, "estado": "trechos_ancorados_revisao_pendente",
            "trechos_ancorados": ancorados}


def confrontar_trechos(
    caso: Mapping[str, object], gabarito: Mapping[str, object], bruto: object,
) -> dict[str, object]:
    base_fechada = {"estado": "entrada_invalida", "aprovado_para_producao": False,
                    "autoriza_efeito": False}
    if (not isinstance(gabarito, Mapping)
            or type(gabarito.get("representavel")) is not bool):
        return {**base_fechada, "estado": "referencia_invalida"}
    if (gabarito["representavel"] is False and isinstance(bruto, Mapping)
            and bruto.get("representavel") is True):
        return {**base_fechada, "estado": "forcou_regra_nao_representavel"}
    estrutura = conferir_trechos(caso, bruto)
    if estrutura["estado"] not in {
        "abstencao_estrutural", "trechos_ancorados_revisao_pendente",
    }:
        return estrutura
    base = {**estrutura, "trechos_alinhados_revisao": False}
    if estrutura["estado"] == "abstencao_estrutural":
        return {**base, "estado": ("abstencao_em_regra_representavel"
                                  if gabarito["representavel"]
                                  else "abstencao_compativel")}
    if not gabarito["representavel"]:
        return {**base, "estado": "forcou_regra_nao_representavel"}
    try:
        esperados = [item["citacao"] for item in gabarito["condicoes"]]
        if any(not isinstance(item, str) for item in esperados):
            raise TypeError
    except (KeyError, TypeError):
        return {**base, "estado": "referencia_invalida"}
    if any(_ancorar_trecho(caso["fonte"], item) is None for item in esperados):
        return {**base, "estado": "referencia_invalida"}
    restantes = Counter(esperados)
    for observado in estrutura["trechos_ancorados"]:
        equivalente = next(
            (esperado for esperado in restantes if restantes[esperado] > 0
             and _mesma_condicao_em_superficie(observado, esperado)), None,
        )
        if equivalente is not None:
            restantes[equivalente] -= 1
    if any(restantes.values()) or len(estrutura["trechos_ancorados"]) != len(esperados):
        return {**base, "estado": "trechos_divergentes",
                "esperados": esperados,
                "observados": estrutura["trechos_ancorados"]}
    base["trechos_alinhados_revisao"] = True
    for chave, estado in (("conectivo_condicoes", "conectivo_divergente"),
                          ("direcao_implicacao", "implicacao_divergente")):
        if bruto[chave] != gabarito.get(chave):
            return {**base, "estado": estado}
    return {**base, "estado": "trechos_e_relacao_alinhados_revisao_pendente"}


def conferir_normalizacao(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    trechos: object, bruto: object,
) -> dict[str, object]:
    base = {"estado": "entrada_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    estado_trechos = conferir_trechos(caso, trechos)["estado"]
    if estado_trechos != "trechos_ancorados_revisao_pendente":
        return {**base, "estado": "trechos_invalidos"}
    confronto_trechos = confrontar_trechos(caso, gabarito, trechos)
    if confronto_trechos["estado"] != "trechos_e_relacao_alinhados_revisao_pendente":
        return {**base, "estado": "trechos_sem_revisao_alinhada"}
    if (not isinstance(bruto, Mapping) or set(bruto) != {"condicoes"}
            or not isinstance(bruto["condicoes"], list)
            or len(bruto["condicoes"]) != len(trechos["trechos_condicoes"])):
        return base
    campos = {"referente_id", "atributo", "operador", "valor", "unidade"}
    condicoes = []
    ancorados = confronto_trechos["trechos_ancorados"]
    for item, citacao in zip(bruto["condicoes"], ancorados):
        if (not isinstance(item, Mapping) or set(item) != campos
                or any(not isinstance(item[chave], str) or len(item[chave]) > 300
                       for chave in campos)):
            return base
        condicoes.append({**item, "fonte_id": "regra", "citacao": citacao})
    proposta = {"representavel": True, "condicoes": condicoes,
                "conectivo_condicoes": trechos["conectivo_condicoes"],
                "direcao_implicacao": trechos["direcao_implicacao"]}
    referencia = dict(gabarito)
    condicoes_revisadas = []
    for condicao in gabarito["condicoes"]:
        citacao = next(
            (item for item in ancorados if _mesma_condicao_em_superficie(
                item, condicao["citacao"])), None,
        )
        if citacao is None:
            return {**base, "estado": "referencia_invalida"}
        condicoes_revisadas.append({**condicao, "citacao": citacao})
    referencia["condicoes"] = condicoes_revisadas
    return conferir_proposta(caso, referencia, proposta)


def _formato_trechos() -> dict[str, object]:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["representavel", "trechos_condicoes", "conectivo_condicoes",
                     "direcao_implicacao"],
        "properties": {
            "representavel": {"type": "boolean"},
            "trechos_condicoes": {"type": "array", "items": {"type": "string"},
                                  "maxItems": 8},
            "conectivo_condicoes": {"type": "string", "enum": [
                "unico", "e", "ou", "indeterminado",
            ]},
            "direcao_implicacao": {"type": "string", "enum": [
                "condicoes_suficientes", "condicoes_necessarias",
                "equivalencia", "indeterminado",
            ]},
        },
    }


def _formato_normalizacao() -> dict[str, object]:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["condicoes"],
        "properties": {"condicoes": {
            "type": "array", "maxItems": 8,
            "items": {"type": "object", "additionalProperties": False,
                      "required": ["referente_id", "atributo", "operador",
                                   "valor", "unidade"],
                      "properties": {
                          "referente_id": {"type": "string"},
                          "atributo": {"type": "string"},
                          "operador": {"type": "string", "enum": [
                              "<", "<=", ">", ">=", "=", "!=",
                          ]},
                          "valor": {"type": "string"},
                          "unidade": {"type": "string"},
                      }},
        }},
    }


def _consultar_modelo(
    sistema: str, entrada: Mapping[str, object], formato: Mapping[str, object],
    *, url: str, modelo: str,
) -> object:
    import requests

    resposta = requests.post(
        url,
        json={"model": modelo, "stream": False, "format": formato,
              "options": {"temperature": 0, "num_predict": 700},
              "messages": [
                  {"role": "system", "content": sistema},
                  {"role": "user", "content": json.dumps(
                      entrada, ensure_ascii=False,
                  )},
              ]},
        timeout=90,
    )
    resposta.raise_for_status()
    return json.loads(resposta.json()["message"]["content"])


def medir_caso(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    *, url: str = "http://127.0.0.1:11434/api/chat",
    modelo: str = "qwen3:4b-instruct",
) -> dict[str, object]:
    """Duas propostas locais; gabarito é usado só após cada chamada."""
    import requests

    inicio = time.monotonic()
    sistema_trechos = (
        "Sua tarefa é localizar apenas condições que governam o efeito fixo. "
        "Em trechos_condicoes, copie da fonte uma citação literal contínua por "
        "condição, incluindo o valor; não inclua o efeito nem explicações. "
        "Use 'unico' para uma condição, 'e' para conjunção e 'ou' para disjunção. "
        "'Se condições, efeito' significa condições suficientes; "
        "'efeito apenas se condições' significa condições necessárias; "
        "'se e somente se' significa equivalência. Se houver mistura aninhada "
        "de e/ou, o contrato plano não representa a regra: responda "
        "representavel=false, lista vazia e ambos os rótulos indeterminado. "
        "Não converse nem execute nada."
    )
    try:
        trechos = _consultar_modelo(
            sistema_trechos, preparar_entrada_modelo(caso), _formato_trechos(),
            url=url, modelo=modelo,
        )
        confronto = confrontar_trechos(caso, gabarito, trechos)
        resultado = {"id": caso["id"], "trechos": trechos,
                     "afericao_trechos": confronto,
                     "normalizacao": "nao_executada_primeira_fronteira_red"}
        if confronto["estado"] != "trechos_e_relacao_alinhados_revisao_pendente":
            return {**resultado, "duracao_s": round(time.monotonic()-inicio, 2)}

        sistema_normalizacao = (
            "Cada trecho_condicoes já foi extraído da fonte. Para CADA trecho, "
            "na mesma ordem, produza apenas referente_id, atributo, operador, "
            "valor e unidade. Use um ID existente dos referentes. O operador "
            "descreve comparação entre atributo e valor: use somente <, <=, "
            ">, >=, = ou !=; e/ou NÃO são operadores. O valor precisa estar "
            "literalmente no respectivo trecho; unidade é vazia para valores "
            "textuais. Não acrescente condições, efeito, citação ou fonte_id. "
            "Não converse nem execute nada."
        )
        entrada = {**preparar_entrada_modelo(caso),
                   "trechos_condicoes": trechos["trechos_condicoes"]}
        bruto = _consultar_modelo(
            sistema_normalizacao, entrada, _formato_normalizacao(),
            url=url, modelo=modelo,
        )
        return {**resultado, "normalizacao": bruto,
                "afericao_normalizacao": conferir_normalizacao(
                    caso, gabarito, trechos, bruto,
                ), "duracao_s": round(time.monotonic()-inicio, 2)}
    except (requests.RequestException, KeyError, TypeError, ValueError) as erro:
        return {"id": caso["id"], "erro": type(erro).__name__,
                "duracao_s": round(time.monotonic()-inicio, 2),
                "aprovado_para_producao": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--painel", type=int, choices=(2, 3), default=2)
    args = parser.parse_args()
    entradas, gabarito = carregar_painel(args.painel)
    for caso in entradas:
        print(json.dumps(medir_caso(caso, gabarito[caso["id"]]),
                         ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
