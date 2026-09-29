"""Sonda offline: oferece candidatos literais de condições para seleção."""

from __future__ import annotations

import argparse
import json
import re
import time
from typing import Mapping

from scripts.analises.sonda_produtor_condicoes_didaticas import preparar_entrada_modelo
from scripts.analises.sonda_produtor_condicoes_v2 import (
    _consultar_modelo, _mesma_condicao_em_superficie, carregar_painel,
    confrontar_trechos,
)
from scripts.analises.sinal_relacao_condicional import (
    analisar_marcador_condicional, confrontar_direcao_marcador,
    encontrar_marcador_condicional,
    encontrar_comparadores_inclusivos,
)


_JUNCAO = re.compile(r"\s+(e|ou)\s+(?:se\s+)?", re.IGNORECASE)


def _sem_espacos_e_virgulas(fonte: str, inicio: int, fim: int) -> tuple[int, int]:
    while inicio < fim and (fonte[inicio].isspace() or fonte[inicio] == ","):
        inicio += 1
    while fim > inicio and (fonte[fim - 1].isspace() or fonte[fim - 1] == ","):
        fim -= 1
    return inicio, fim


def gerar_candidatos(caso: Mapping[str, object]) -> dict[str, object]:
    """Segmentação lexical limitada; não autentica premissa nem cobertura."""
    base = {"estado": "abstencao_sem_estrutura_condicional", "candidatos": [],
            "estrutura_plana_possivel": False,
            "conectivo_textual": "indeterminado",
            "aprovado_para_producao": False, "autoriza_efeito": False}
    fonte = caso.get("fonte")
    if not isinstance(fonte, str) or len(fonte) > 2000:
        return base
    marcador = encontrar_marcador_condicional(fonte)
    if marcador is None:
        return base
    inicio_regiao = marcador.end()
    separadores_efeito = list(re.finditer(r",\s+", fonte[inicio_regiao:]))
    if separadores_efeito:
        fim_regiao = inicio_regiao + separadores_efeito[-1].start()
    else:
        fim_regiao = len(fonte.rstrip(" .!?"))
    if fim_regiao <= inicio_regiao:
        return base
    regiao = fonte[inicio_regiao:fim_regiao]
    comparadores = encontrar_comparadores_inclusivos(regiao)
    # Operador composto tem precedência lexical sobre conectivo. Preservar
    # o texto e seus offsets; não substituir globalmente todo `ou` da regra.
    juncoes = [item for item in _JUNCAO.finditer(regiao)
               if not any(c.start() <= item.start(1) < c.end()
                          for c in comparadores)]
    operadores = {item.group(1).casefold() for item in juncoes}
    estrutura_plana_possivel = len(operadores) <= 1
    conectivo_textual = ("unico" if not operadores else
                         next(iter(operadores)) if len(operadores) == 1
                         else "misto")
    limites_fim = [inicio_regiao + item.start() for item in juncoes] + [fim_regiao]
    limites_inicio = [inicio_regiao] + [inicio_regiao + item.end()
                                         for item in juncoes]
    candidatos = []
    for indice, (inicio, fim) in enumerate(zip(limites_inicio, limites_fim)):
        inicio, fim = _sem_espacos_e_virgulas(fonte, inicio, fim)
        if inicio >= fim:
            return base
        candidatos.append({"id": f"c{indice}", "citacao": fonte[inicio:fim],
                           "inicio": inicio, "fim": fim})
    if not candidatos or len(candidatos) > 8:
        return base
    return {**base, "estado": "candidatos_gerados_revisao_pendente",
            "candidatos": candidatos,
            "conectivo_textual": conectivo_textual,
            "estrutura_plana_possivel": estrutura_plana_possivel}


def conferir_cobertura(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    gerados: Mapping[str, object],
) -> dict[str, object]:
    base = {"estado": "cobertura_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    if gerados != gerar_candidatos(caso) or not isinstance(gabarito, Mapping):
        return base
    if gabarito.get("representavel") is not True:
        return {**base, "estado": "cobertura_nao_medida_regra_nao_plana"}
    try:
        esperados = [item["citacao"] for item in gabarito["condicoes"]]
        candidatos = [item["citacao"] for item in gerados["candidatos"]]
        if len(esperados) != len(candidatos):
            return {**base, "estado": "cobertura_divergente"}
        alinhados = all(_mesma_condicao_em_superficie(candidato, esperado)
                       for candidato, esperado in zip(candidatos, esperados))
    except (KeyError, TypeError):
        return base
    return {**base, "estado": ("cobertura_candidatos_revisao_pendente"
                              if alinhados else "cobertura_divergente")}


def converter_escolha(
    gerados: Mapping[str, object], bruto: object,
) -> dict[str, object]:
    base = {"estado": "entrada_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    campos = {"representavel", "candidatos_ids", "conectivo_condicoes",
              "direcao_implicacao"}
    if (not isinstance(bruto, Mapping) or set(bruto) != campos
            or type(bruto["representavel"]) is not bool
            or not isinstance(bruto["candidatos_ids"], list)
            or len(bruto["candidatos_ids"]) > 8
            or not isinstance(bruto["conectivo_condicoes"], str)
            or not isinstance(bruto["direcao_implicacao"], str)
            or bruto["conectivo_condicoes"] not in {
                "unico", "e", "ou", "indeterminado",
            } or bruto["direcao_implicacao"] not in {
                "condicoes_suficientes", "condicoes_necessarias",
                "equivalencia", "indeterminado",
            } or not isinstance(gerados, Mapping)
            or gerados.get("estado") != "candidatos_gerados_revisao_pendente"):
        return base
    ids = bruto["candidatos_ids"]
    if not bruto["representavel"]:
        if (ids or bruto["conectivo_condicoes"] != "indeterminado"
                or bruto["direcao_implicacao"] != "indeterminado"):
            return base
        return {**base, "estado": "escolha_convertida",
                "trechos": {"representavel": False, "trechos_condicoes": [],
                            "conectivo_condicoes": "indeterminado",
                            "direcao_implicacao": "indeterminado"}}
    if (not ids or any(not isinstance(item, str) for item in ids)
            or len(ids) != len(set(ids))):
        return base
    if gerados.get("estrutura_plana_possivel") is False:
        return {**base, "estado": "forcou_regra_nao_representavel"}
    por_id = {item["id"]: item for item in gerados["candidatos"]}
    if any(item not in por_id for item in ids):
        return {**base, "estado": "candidato_desconhecido"}
    if ids != sorted(ids, key=lambda item: por_id[item]["inicio"]):
        return base
    return {**base, "estado": "escolha_convertida",
            "trechos": {"representavel": True,
                        "trechos_condicoes": [por_id[item]["citacao"] for item in ids],
                        "conectivo_condicoes": bruto["conectivo_condicoes"],
                        "direcao_implicacao": bruto["direcao_implicacao"]}}


def confrontar_escolha(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    gerados: Mapping[str, object], bruto: object,
) -> dict[str, object]:
    if gerados != gerar_candidatos(caso):
        return {"estado": "candidatos_adulterados",
                "aprovado_para_producao": False, "autoriza_efeito": False}
    conversao = converter_escolha(gerados, bruto)
    if conversao["estado"] != "escolha_convertida":
        return conversao
    if conversao["trechos"]["representavel"]:
        if (gerados["conectivo_textual"] in {"unico", "e", "ou"}
                and conversao["trechos"]["conectivo_condicoes"]
                != gerados["conectivo_textual"]):
            return {"estado": "conectivo_divergente_marcador",
                    "aprovado_para_producao": False,
                    "autoriza_efeito": False}
        sinal = confrontar_direcao_marcador(
            caso["fonte"], conversao["trechos"]["direcao_implicacao"],
        )
        if sinal["estado"] == "direcao_divergente_marcador":
            return sinal
    return confrontar_trechos(caso, gabarito, conversao["trechos"])


def _formato_escolha() -> dict[str, object]:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["representavel", "candidatos_ids", "conectivo_condicoes",
                     "direcao_implicacao"],
        "properties": {
            "representavel": {"type": "boolean"},
            "candidatos_ids": {"type": "array", "maxItems": 8,
                               "items": {"type": "string"}},
            "conectivo_condicoes": {"type": "string", "enum": [
                "unico", "e", "ou", "indeterminado",
            ]},
            "direcao_implicacao": {"type": "string", "enum": [
                "condicoes_suficientes", "condicoes_necessarias",
                "equivalencia", "indeterminado",
            ]},
        },
    }


def medir_caso(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    *, url: str = "http://127.0.0.1:11434/api/chat",
    modelo: str = "qwen3:4b-instruct",
) -> dict[str, object]:
    """Mede cobertura, escolha e relação separadamente; nunca publica."""
    import requests

    inicio = time.monotonic()
    gerados = gerar_candidatos(caso)
    cobertura = conferir_cobertura(caso, gabarito, gerados)
    resultado = {"id": caso["id"], "candidatos": gerados,
                 "cobertura": cobertura,
                 "aprovado_para_producao": False}
    if (gerados["estado"] != "candidatos_gerados_revisao_pendente"
            or (gabarito.get("representavel") is True
                and cobertura["estado"]
                != "cobertura_candidatos_revisao_pendente")):
        return {**resultado, "escolha": "nao_executada_primeira_fronteira_red",
                "duracao_s": round(time.monotonic() - inicio, 2)}
    if gerados["estrutura_plana_possivel"] is False:
        return {**resultado, "escolha": "recusa_estrutura_plana",
                "duracao_s": round(time.monotonic() - inicio, 2)}
    sistema = (
        "Selecione os IDs dos candidatos que são condições do efeito fixo. "
        "Os candidatos já são trechos literais da fonte; não reescreva texto. "
        "Para uma condição use 'unico'; para múltiplas, 'e' ou 'ou'. "
        "'Se condições, efeito' indica suficiência; 'efeito apenas se "
        "condições' indica necessidade; 'se e somente se' indica equivalência. "
        "O sinal_relacao é extraído literalmente da fonte: quando for explícito, "
        "sua direção é uma restrição da proposta. Quando for indeterminado, "
        "não trate o marcador temporal sozinho como prova de implicação. "
        "O sinal_conectivo é uma pista literal entre candidatos; não troque "
        "'ou' por 'e' nem o contrário, mas não o tome por prova semântica. "
        "Se a lógica exigir combinação aninhada de e/ou, responda "
        "representavel=false, candidatos_ids=[] e ambos os rótulos "
        "indeterminado. Não responda ao usuário nem execute ações."
    )
    entrada = {**preparar_entrada_modelo(caso),
               "sinal_relacao": analisar_marcador_condicional(caso["fonte"]),
               "sinal_conectivo": gerados["conectivo_textual"],
               "candidatos": [
        {"id": item["id"], "citacao": item["citacao"]}
        for item in gerados["candidatos"]
    ]}
    try:
        bruto = _consultar_modelo(
            sistema, entrada, _formato_escolha(), url=url, modelo=modelo,
        )
        return {**resultado, "proposta": bruto,
                "afericao": confrontar_escolha(caso, gabarito, gerados, bruto),
                "duracao_s": round(time.monotonic() - inicio, 2)}
    except (requests.RequestException, KeyError, TypeError, ValueError) as erro:
        return {**resultado, "erro": type(erro).__name__,
                "duracao_s": round(time.monotonic() - inicio, 2)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--painel", type=int, choices=(2, 3, 4, 5), default=3)
    args = parser.parse_args()
    entradas, gabarito = carregar_painel(args.painel)
    for caso in entradas:
        print(json.dumps(medir_caso(caso, gabarito[caso["id"]]),
                         ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
