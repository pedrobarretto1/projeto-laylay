"""Sonda offline: chaves fixas impedem o modelo de inventar IDs de fragmentos.

O modelo só propõe indícios; validação, revisão e autorização seguem externas.
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Mapping

from scripts.analises.sonda_fronteira_predicados_v1 import reconstruir_condicoes
from scripts.analises.sonda_produtor_candidatos_v1 import gerar_candidatos
from scripts.analises.sonda_produtor_condicoes_didaticas import preparar_entrada_modelo
from scripts.analises.sonda_produtor_condicoes_v2 import (
    _consultar_modelo, carregar_painel, confrontar_trechos,
)


def formato_predicados_fixos(caso: Mapping[str, object]) -> dict[str, object]:
    ids = [item["id"] for item in gerar_candidatos(caso)["candidatos"]]
    valor = {"type": "object", "additionalProperties": False,
             "required": ["tem_predicado", "ancora"],
             "properties": {"tem_predicado": {"type": "boolean"},
                            "ancora": {"type": "string"}}}
    return {"type": "object", "additionalProperties": False,
            "required": ids, "properties": {chave: valor for chave in ids}}


def formato_predicados_plano(caso: Mapping[str, object]) -> dict[str, object]:
    propriedades = {}
    for item in gerar_candidatos(caso)["candidatos"]:
        chave = item["id"]
        propriedades[f"{chave}_tem_predicado"] = {"type": "boolean"}
        propriedades[f"{chave}_ancora"] = {"type": "string"}
    return {"type": "object", "additionalProperties": False,
            "required": list(propriedades), "properties": propriedades}


def converter_mapa_plano(
    caso: Mapping[str, object], bruto: object,
) -> dict[str, object]:
    base = {"estado": "entrada_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    gerados = gerar_candidatos(caso)
    if gerados["estado"] != "candidatos_gerados_revisao_pendente":
        return {**base, "estado": "abstencao_sem_estrutura_condicional"}
    if gerados["estrutura_plana_possivel"] is False:
        return {**base, "estado": "recusa_estrutura_plana"}
    ids = [item["id"] for item in gerados["candidatos"]]
    esperados = {f"{chave}_{campo}" for chave in ids
                 for campo in ("tem_predicado", "ancora")}
    if not isinstance(bruto, Mapping) or set(bruto) != esperados:
        return base
    mapa = {chave: {"tem_predicado": bruto[f"{chave}_tem_predicado"],
                    "ancora": bruto[f"{chave}_ancora"]} for chave in ids}
    return converter_mapa_predicados(caso, mapa)


def converter_mapa_predicados(
    caso: Mapping[str, object], bruto: object,
) -> dict[str, object]:
    base = {"estado": "entrada_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    gerados = gerar_candidatos(caso)
    if gerados["estado"] != "candidatos_gerados_revisao_pendente":
        return {**base, "estado": "abstencao_sem_estrutura_condicional"}
    if gerados["estrutura_plana_possivel"] is False:
        return {**base, "estado": "recusa_estrutura_plana"}
    ids = [item["id"] for item in gerados["candidatos"]]
    if (not isinstance(bruto, Mapping) or set(bruto) != set(ids)
            or any(not isinstance(bruto[chave], Mapping)
                   or set(bruto[chave]) != {"tem_predicado", "ancora"}
                   for chave in ids)):
        return base
    segmentos = [{"id": chave, **bruto[chave]} for chave in ids]
    return reconstruir_condicoes(caso, {"segmentos": segmentos})


def medir_caso(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    *, url: str = "http://127.0.0.1:11434/api/chat",
    modelo: str = "qwen3:4b-instruct",
    contrato: str = "aninhado_completo",
) -> dict[str, object]:
    """A estrutura de IDs é determinística; gabarito só entra na aferição."""
    import requests

    if contrato not in {"aninhado_completo", "plano_minimo"}:
        raise ValueError("contrato de sonda desconhecido")
    inicio = time.monotonic()
    gerados = gerar_candidatos(caso)
    resultado = {"id": caso["id"], "candidatos": gerados,
                 "contrato": contrato, "aprovado_para_producao": False,
                 "autoriza_efeito": False}
    if gerados["estado"] != "candidatos_gerados_revisao_pendente":
        return {**resultado, "escolha": "nao_executada_sem_candidatos",
                "duracao_s": round(time.monotonic() - inicio, 2)}
    if gerados["estrutura_plana_possivel"] is False:
        return {**resultado, "escolha": "recusa_estrutura_plana",
                "duracao_s": round(time.monotonic() - inicio, 2)}
    sistema = (
        "Para cada chave c0, c1 etc, indique se o fragmento correspondente "
        "contém um verbo que predica explicitamente algo na própria fonte. "
        "Se sim, copie apenas a palavra verbal literal para 'ancora'; se não, "
        "use ancora vazia. Um fragmento pode ser só parte de sujeito composto: "
        "não invente verbo que está no fragmento vizinho. Não escolha a "
        "segmentação final nem interprete o efeito. Responda com as mesmas "
        "chaves recebidas, sem campo 'id' ou chaves extras. Não converse e "
        "não execute ações."
    )
    fragmentos = {item["id"]: item["citacao"]
                  for item in gerados["candidatos"]}
    if contrato == "plano_minimo":
        sistema = (
            "Para cada fragmento, indique se há verbo predicativo explícito "
            "e copie só essa palavra literal. Use exatamente as chaves "
            "exigidas. Se não houver verbo no fragmento, marque false e "
            "deixe a âncora vazia. Não converse e não execute ações."
        )
        entrada = {"fonte": caso["fonte"], "fragmentos": fragmentos}
        formato = formato_predicados_plano(caso)
    else:
        entrada = {**preparar_entrada_modelo(caso),
                   "fragmentos": fragmentos}
        formato = formato_predicados_fixos(caso)
    try:
        bruto = _consultar_modelo(
            sistema, entrada, formato, url=url, modelo=modelo,
        )
        conversao = (converter_mapa_plano(caso, bruto)
                    if contrato == "plano_minimo"
                    else converter_mapa_predicados(caso, bruto))
        resultado = {**resultado, "proposta": bruto, "reconstrucao": conversao,
                     "duracao_s": round(time.monotonic() - inicio, 2)}
        if conversao["estado"] != "segmentos_ancorados_revisao_pendente":
            return resultado
        return {**resultado, "afericao": confrontar_trechos(
            caso, gabarito, conversao["trechos"],
        )}
    except (requests.RequestException, KeyError, TypeError, ValueError) as erro:
        return {**resultado, "erro": type(erro).__name__,
                "duracao_s": round(time.monotonic() - inicio, 2)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--painel", type=int, choices=(6, 7, 8), default=7)
    parser.add_argument("--contrato", choices=("aninhado_completo", "plano_minimo"),
                        default="aninhado_completo")
    args = parser.parse_args()
    casos, gabarito = carregar_painel(args.painel)
    for caso in casos:
        print(json.dumps(medir_caso(caso, gabarito[caso["id"]],
                                    contrato=args.contrato),
                         ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
