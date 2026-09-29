"""Sonda offline: o conectivo pode unir condições ou compor um referente.

Só oferece segmentações literais. A escolha do modelo não valida semântica,
não publica ensino e não autoriza efeito no runtime da Laylay.
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Mapping

from scripts.analises.sinal_relacao_condicional import (
    analisar_marcador_condicional, confrontar_direcao_marcador,
)
from scripts.analises.sonda_produtor_candidatos_v1 import gerar_candidatos
from scripts.analises.sonda_produtor_condicoes_didaticas import preparar_entrada_modelo
from scripts.analises.sonda_produtor_condicoes_v2 import (
    _consultar_modelo, _mesma_condicao_em_superficie, carregar_painel,
    confrontar_trechos,
)


def gerar_segmentacoes(caso: Mapping[str, object]) -> dict[str, object]:
    """Duas leituras estruturais de uma região da fonte, sem usar gabarito."""
    base = {"estado": "abstencao_sem_estrutura_condicional", "segmentacoes": [],
            "estrutura_plana_possivel": False,
            "aprovado_para_producao": False, "autoriza_efeito": False}
    gerados = gerar_candidatos(caso)
    if gerados["estado"] != "candidatos_gerados_revisao_pendente":
        return base
    atomos = gerados["candidatos"]
    fonte = caso["fonte"]
    inicio, fim = atomos[0]["inicio"], atomos[-1]["fim"]
    integral = {"id": "integral", "conectivo_condicoes": "unico",
                "trechos": [{"citacao": fonte[inicio:fim],
                             "inicio": inicio, "fim": fim}]}
    segmentacoes = [integral]
    if len(atomos) > 1:
        segmentacoes.append({"id": "atomica",
                             "conectivo_condicoes": gerados["conectivo_textual"],
                             "trechos": [{chave: atomo[chave] for chave in (
                                 "citacao", "inicio", "fim",
                             )} for atomo in atomos]})
    return {**base, "estado": "segmentacoes_geradas_revisao_pendente",
            "segmentacoes": segmentacoes,
            "estrutura_plana_possivel": gerados["estrutura_plana_possivel"]}


def conferir_cobertura_segmentacoes(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    geradas: Mapping[str, object],
) -> dict[str, object]:
    base = {"estado": "cobertura_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    if geradas != gerar_segmentacoes(caso) or not isinstance(gabarito, Mapping):
        return base
    if gabarito.get("representavel") is not True:
        return {**base, "estado": "cobertura_nao_medida_regra_nao_plana"}
    try:
        esperados = [item["citacao"] for item in gabarito["condicoes"]]
        if not esperados or any(not isinstance(item, str) for item in esperados):
            return base
        cobertas = [alternativa["id"] for alternativa in geradas["segmentacoes"]
                    if alternativa["conectivo_condicoes"] == gabarito.get(
                        "conectivo_condicoes")
                    and len(alternativa["trechos"]) == len(esperados)
                    and all(_mesma_condicao_em_superficie(trecho["citacao"], esperado)
                            for trecho, esperado in zip(alternativa["trechos"],
                                                         esperados))]
    except (KeyError, TypeError):
        return base
    return {**base, "estado": ("cobertura_alternativa_revisao_pendente"
                              if cobertas else "cobertura_divergente"),
            "alternativas_cobertas": cobertas}


def converter_escolha(
    geradas: Mapping[str, object], bruto: object,
) -> dict[str, object]:
    base = {"estado": "entrada_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    if (not isinstance(bruto, Mapping)
            or set(bruto) != {"representavel", "segmentacao_id",
                              "direcao_implicacao"}
            or type(bruto["representavel"]) is not bool
            or not isinstance(bruto["segmentacao_id"], str)
            or not isinstance(bruto["direcao_implicacao"], str)
            or bruto["direcao_implicacao"] not in {
                "condicoes_suficientes", "condicoes_necessarias",
                "equivalencia", "indeterminado",
            } or not isinstance(geradas, Mapping)
            or geradas.get("estado") != "segmentacoes_geradas_revisao_pendente"):
        return base
    if not bruto["representavel"]:
        if (bruto["segmentacao_id"] != "indeterminado"
                or bruto["direcao_implicacao"] != "indeterminado"):
            return base
        return {**base, "estado": "escolha_convertida",
                "trechos": {"representavel": False, "trechos_condicoes": [],
                            "conectivo_condicoes": "indeterminado",
                            "direcao_implicacao": "indeterminado"}}
    if geradas["estrutura_plana_possivel"] is False:
        return {**base, "estado": "forcou_regra_nao_representavel"}
    alternativa = next((item for item in geradas["segmentacoes"]
                        if item["id"] == bruto["segmentacao_id"]), None)
    if alternativa is None:
        return {**base, "estado": "segmentacao_desconhecida"}
    return {**base, "estado": "escolha_convertida",
            "trechos": {"representavel": True,
                        "trechos_condicoes": [item["citacao"]
                                              for item in alternativa["trechos"]],
                        "conectivo_condicoes": alternativa["conectivo_condicoes"],
                        "direcao_implicacao": bruto["direcao_implicacao"]}}


def confrontar_segmentacao(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    geradas: Mapping[str, object], bruto: object,
) -> dict[str, object]:
    if geradas != gerar_segmentacoes(caso):
        return {"estado": "segmentacoes_adulteradas",
                "aprovado_para_producao": False, "autoriza_efeito": False}
    conversao = converter_escolha(geradas, bruto)
    if conversao["estado"] != "escolha_convertida":
        return conversao
    if conversao["trechos"]["representavel"]:
        sinal = confrontar_direcao_marcador(
            caso["fonte"], conversao["trechos"]["direcao_implicacao"],
        )
        if sinal["estado"] == "direcao_divergente_marcador":
            return sinal
    return confrontar_trechos(caso, gabarito, conversao["trechos"])


def _formato_escolha() -> dict[str, object]:
    return {"type": "object", "additionalProperties": False,
            "required": ["representavel", "segmentacao_id",
                         "direcao_implicacao"],
            "properties": {
                "representavel": {"type": "boolean"},
                "segmentacao_id": {"type": "string", "enum": [
                    "integral", "atomica", "indeterminado",
                ]},
                "direcao_implicacao": {"type": "string", "enum": [
                    "condicoes_suficientes", "condicoes_necessarias",
                    "equivalencia", "indeterminado",
                ]},
            }}


def medir_caso(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    *, url: str = "http://127.0.0.1:11434/api/chat",
    modelo: str = "qwen3:4b-instruct",
    ordem_segmentacoes: str = "integral_primeiro",
) -> dict[str, object]:
    """Mede seleção local; gabarito só participa do portão e da aferição."""
    import requests

    inicio = time.monotonic()
    geradas = gerar_segmentacoes(caso)
    cobertura = conferir_cobertura_segmentacoes(caso, gabarito, geradas)
    if ordem_segmentacoes not in {"integral_primeiro", "atomica_primeiro"}:
        raise ValueError("ordem de segmentacoes desconhecida")
    resultado = {"id": caso["id"], "segmentacoes": geradas,
                 "cobertura": cobertura, "aprovado_para_producao": False,
                 "autoriza_efeito": False,
                 "ordem_segmentacoes": ordem_segmentacoes}
    if geradas["estado"] != "segmentacoes_geradas_revisao_pendente":
        return {**resultado, "escolha": "nao_executada_primeira_fronteira_red",
                "duracao_s": round(time.monotonic() - inicio, 2)}
    if geradas["estrutura_plana_possivel"] is False:
        return {**resultado, "escolha": "recusa_estrutura_plana",
                "duracao_s": round(time.monotonic() - inicio, 2)}
    if (gabarito.get("representavel") is True
            and cobertura["estado"] != "cobertura_alternativa_revisao_pendente"):
        return {**resultado, "escolha": "nao_executada_primeira_fronteira_red",
                "duracao_s": round(time.monotonic() - inicio, 2)}
    sistema = (
        "Escolha a segmentação literal da região condicional. 'integral' é "
        "uma condição só; 'atomica' separa condições unidas por e/ou. Um "
        "conectivo pode estar dentro de um sujeito composto e NÃO separar "
        "condições. Se a regra exigir árvore mista, abstenha-se. "
        "'Se condições, efeito' sinaliza suficiência; 'efeito apenas se "
        "condições' sinaliza necessidade; 'se e somente se', equivalência. "
        "'quando' sozinho não prova implicação lógica. Responda só com ID e "
        "direção; não reescreva trechos, não converse e não execute ações."
    )
    opcoes = list(geradas["segmentacoes"])
    if ordem_segmentacoes == "atomica_primeiro":
        opcoes.reverse()
    entrada = {**preparar_entrada_modelo(caso),
               "sinal_relacao": analisar_marcador_condicional(caso["fonte"]),
               "segmentacoes": [{"id": item["id"],
                                  "conectivo_condicoes": item[
                                      "conectivo_condicoes"],
                                  "trechos": [trecho["citacao"] for trecho in
                                              item["trechos"]]}
                                 for item in opcoes]}
    try:
        bruto = _consultar_modelo(
            sistema, entrada, _formato_escolha(), url=url, modelo=modelo,
        )
        return {**resultado, "proposta": bruto,
                "afericao": confrontar_segmentacao(
                    caso, gabarito, geradas, bruto,
                ), "duracao_s": round(time.monotonic() - inicio, 2)}
    except (requests.RequestException, KeyError, TypeError, ValueError) as erro:
        return {**resultado, "erro": type(erro).__name__,
                "duracao_s": round(time.monotonic() - inicio, 2)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--painel", type=int, choices=(5, 6), default=5)
    parser.add_argument("--ordem", choices=("integral_primeiro", "atomica_primeiro"),
                        default="integral_primeiro")
    args = parser.parse_args()
    entradas, gabarito = carregar_painel(args.painel)
    for caso in entradas:
        print(json.dumps(medir_caso(caso, gabarito[caso["id"]],
                                    ordem_segmentacoes=args.ordem),
                         ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
