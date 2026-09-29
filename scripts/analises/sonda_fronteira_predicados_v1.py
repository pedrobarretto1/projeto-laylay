"""Sonda offline: indícios literais de predicado definem fronteiras.

O modelo propõe âncoras; a reconstrução, revisão e autorização são externas.
Isto não autentica análise gramatical nem integra fala ou execução da Laylay.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from typing import Mapping

from scripts.analises.sinal_relacao_condicional import analisar_marcador_condicional
from scripts.analises.sonda_produtor_candidatos_v1 import gerar_candidatos
from scripts.analises.sonda_produtor_condicoes_didaticas import preparar_entrada_modelo
from scripts.analises.sonda_produtor_condicoes_v2 import (
    _consultar_modelo, carregar_painel, confrontar_trechos,
)


def reconstruir_condicoes(
    caso: Mapping[str, object], bruto: object,
) -> dict[str, object]:
    """Ancora cada proposta e fecha um grupo somente quando há predicado."""
    base = {"estado": "entrada_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    gerados = gerar_candidatos(caso)
    if gerados["estado"] != "candidatos_gerados_revisao_pendente":
        return {**base, "estado": "abstencao_sem_estrutura_condicional"}
    if gerados["estrutura_plana_possivel"] is False:
        return {**base, "estado": "recusa_estrutura_plana"}
    candidatos = gerados["candidatos"]
    if (not isinstance(bruto, Mapping) or set(bruto) != {"segmentos"}
            or not isinstance(bruto["segmentos"], list)
            or len(bruto["segmentos"]) != len(candidatos)):
        return base
    recebidos = bruto["segmentos"]
    if (any(not isinstance(item, Mapping) or not isinstance(item.get("id"), str)
            for item in recebidos)
            or {item["id"] for item in recebidos}
            != {item["id"] for item in candidatos}
            or len({item["id"] for item in recebidos}) != len(recebidos)):
        return base
    por_id = {item["id"]: item for item in recebidos}
    segmentos = [por_id[item["id"]] for item in candidatos]
    for candidato, segmento in zip(candidatos, segmentos):
        if (not isinstance(segmento, Mapping)
                or set(segmento) != {"id", "tem_predicado", "ancora"}
                or type(segmento["tem_predicado"]) is not bool
                or not isinstance(segmento["ancora"], str)
                or len(segmento["ancora"]) > 40
                or (not segmento["tem_predicado"] and segmento["ancora"])):
            return base
        if segmento["tem_predicado"]:
            ancora = segmento["ancora"]
            if (not re.fullmatch(r"[^\W\d_][^\W_]{1,39}", ancora,
                                 flags=re.UNICODE)
                    or not re.search(rf"(?<!\w){re.escape(ancora)}(?!\w)",
                                     candidato["citacao"], flags=re.IGNORECASE)):
                return {**base, "estado": "ancora_invalida"}
    # Antes da primeira condição, fragmentos sem predicado podem compor o
    # sujeito. Entre duas condições já fechadas, a mesma ausência pode ser
    # tanto prefixo da próxima quanto um predicado perdido: não adivinhar.
    for indice, segmento in enumerate(segmentos):
        if (not segmento["tem_predicado"]
                and any(item["tem_predicado"] for item in segmentos[:indice])
                and any(item["tem_predicado"] for item in segmentos[indice + 1:])):
            return {**base, "estado": "fronteira_interna_sem_predicado_ambigua"}
    fonte = caso["fonte"]
    trechos = []
    inicio_grupo = 0
    for indice, segmento in enumerate(segmentos):
        if not segmento["tem_predicado"]:
            continue
        inicio = candidatos[inicio_grupo]["inicio"]
        fim = candidatos[indice]["fim"]
        trechos.append(fonte[inicio:fim])
        inicio_grupo = indice + 1
    if not trechos or inicio_grupo != len(candidatos):
        return {**base, "estado": "sem_predicado_suficiente"}
    direcao = analisar_marcador_condicional(fonte)["direcao"]
    return {**base, "estado": "segmentos_ancorados_revisao_pendente",
            "trechos": {"representavel": True,
                        "trechos_condicoes": trechos,
                        "conectivo_condicoes": (
                            "unico" if len(trechos) == 1
                            else gerados["conectivo_textual"]),
                        "direcao_implicacao": direcao}}


def _formato_predicados() -> dict[str, object]:
    return {"type": "object", "additionalProperties": False,
            "required": ["segmentos"], "properties": {
                "segmentos": {"type": "array", "maxItems": 8,
                             "items": {"type": "object",
                                       "additionalProperties": False,
                                       "required": ["id", "tem_predicado", "ancora"],
                                       "properties": {
                                           "id": {"type": "string"},
                                           "tem_predicado": {"type": "boolean"},
                                           "ancora": {"type": "string"},
                                       }}},
            }}


def medir_caso(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    *, url: str = "http://127.0.0.1:11434/api/chat",
    modelo: str = "qwen3:4b-instruct",
) -> dict[str, object]:
    """A proposta não vê o gabarito; alinhamento é só revisão local."""
    import requests

    inicio = time.monotonic()
    gerados = gerar_candidatos(caso)
    resultado = {"id": caso["id"], "candidatos": gerados,
                 "aprovado_para_producao": False, "autoriza_efeito": False}
    if gerados["estado"] != "candidatos_gerados_revisao_pendente":
        return {**resultado, "escolha": "nao_executada_sem_candidatos",
                "duracao_s": round(time.monotonic() - inicio, 2)}
    if gerados["estrutura_plana_possivel"] is False:
        return {**resultado, "escolha": "recusa_estrutura_plana",
                "duracao_s": round(time.monotonic() - inicio, 2)}
    sistema = (
        "Para CADA fragmento, indique se ele contém um verbo que predica "
        "explicitamente algo na própria fonte. Se sim, copie APENAS a palavra "
        "verbal literal em 'ancora'; se não, use ancora vazia. Um fragmento "
        "pode ser só parte de sujeito composto: não invente verbo que está no "
        "fragmento vizinho. Não escolha uma segmentação final nem interprete "
        "o efeito. Copie todos os IDs na ordem recebida. Não converse, não "
        "execute nada e não trate isto como autorização."
    )
    entrada = {**preparar_entrada_modelo(caso),
               "fragmentos": [{"id": item["id"], "citacao": item["citacao"]}
                              for item in gerados["candidatos"]]}
    try:
        bruto = _consultar_modelo(
            sistema, entrada, _formato_predicados(), url=url, modelo=modelo,
        )
        conversao = reconstruir_condicoes(caso, bruto)
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
    parser.add_argument("--painel", type=int, choices=(5, 6, 7), default=6)
    args = parser.parse_args()
    casos, gabarito = carregar_painel(args.painel)
    for caso in casos:
        print(json.dumps(medir_caso(caso, gabarito[caso["id"]]),
                         ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
