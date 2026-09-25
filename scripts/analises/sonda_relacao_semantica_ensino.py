"""Sonda offline de recuperação de exemplos por paráfrase.

Similaridade vetorial só propõe trechos para revisão; não é prova de
implicação, qualidade da fonte nem autorização para compor uma aula.
O conjunto de contrastes é fixo antes da primeira medição.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np

from mente_laylay.neural.comparar_contexto_semantico_v3 import (
    PASTA_ENCODER,
    SHA_ENCODER,
)
from mente_laylay.neural.encoder_semantico import EncoderSemanticoONNX
from scripts.analises.sonda_fala_integral_real import carregar_caso


# O gabarito vale para relevância à pergunta, não para verdade externa nem
# suficiência didática. Negativos conservam vocabulário e tema superficial.
CONTRASTES = (
    {
        "id": "luz_girassol_real",
        "consulta": "Mostre um exemplo de resposta de uma planta à luz do sol.",
        "positivo": "Um exemplo claro de adaptação extrema é o dos girassóis jovens , que movem seus caules e flores ao longo do dia, acompanhando o percurso do sol.",
        "negativo": "Na aula sobre luz, um exemplo de bactéria é a espécie descrita no estudo.",
    },
    {
        "id": "luz_tema_sem_relacao",
        "consulta": "Explique como a luz participa da fotossíntese da planta.",
        "positivo": "A luz é muito mais do que apenas iluminar o ambiente; ela é essencial para a vida, especialmente para a fotossíntese .",
        "negativo": "A luz na planta é um assunto citado no título desta página, sem explicação de fotossíntese.",
    },
    {
        "id": "divisao_papeis_invertidos",
        "consulta": "Exemplo de repartir 12 objetos igualmente entre 3 pessoas.",
        "positivo": "Ao repartir 12 objetos entre 3 pessoas, cada pessoa recebe 4 objetos.",
        "negativo": "Ao repartir 3 objetos entre 12 pessoas, cada pessoa recebe 4 objetos.",
    },
    {
        "id": "floricultura_condicao",
        "consulta": "Exemplo de perenes que são cultivadas como anuais em climas frios.",
        "positivo": "Algumas plantas perenes são consideradas sensíveis ao frio, o que significa que são perenes apenas em climas mais quentes. Em climas mais frios, são cultivadas como anuais. Os exemplos incluem begônias fúcsia e tuberosas.",
        "negativo": "Algumas plantas anuais são consideradas sensíveis ao frio, o que significa que são anuais apenas em climas mais quentes. Em climas mais frios, são cultivadas como perenes. Os exemplos incluem begônias fúcsia e tuberosas.",
    },
)


def conferir_ligacao_ao_artefato() -> bool:
    """Confere que o positivo histórico é texto realmente preservado."""
    luz = carregar_caso("luz")["fontes"]["F3"]
    flora = carregar_caso("floricultura")["fontes"]["F1"]
    return CONTRASTES[0]["positivo"] in luz and CONTRASTES[3]["positivo"] == flora


def priorizar_pendencias(
    tema: str,
    pendencias: list[dict[str, str]],
    encoder: EncoderSemanticoONNX | None = None,
) -> list[dict[str, Any]]:
    """Ordena para revisão; não devolve unidades aceitas ao compositor."""
    candidatos = [item for item in pendencias
                  if item.get("motivo") == "ligacao_semantica_pendente"
                  and item.get("trecho") and item.get("fonte_id")]
    if not str(tema or "").strip() or not candidatos:
        return []
    modelo = encoder or EncoderSemanticoONNX(
        PASTA_ENCODER, sha256_modelo=SHA_ENCODER, batch_size=16,
    )
    vetores = np.asarray(modelo.codificar(
        [tema, *(item["trecho"] for item in candidatos)]
    ), dtype=np.float32)
    if vetores.shape[0] != len(candidatos) + 1:
        raise ValueError("encoder não devolveu um vetor por texto")
    return sorted((
        {"fonte_id": item["fonte_id"], "papel": item.get("papel", ""),
         "trecho": item["trecho"],
         "similaridade": round(float(np.dot(vetores[0], vetores[indice + 1])), 4),
         "estado": "revisao_semantica_pendente", "aprovado_para_compor": False}
        for indice, item in enumerate(candidatos)
    ), key=lambda item: -item["similaridade"])


def medir_contrastes(encoder: EncoderSemanticoONNX | None = None) -> dict[str, Any]:
    if not conferir_ligacao_ao_artefato():
        raise ValueError("fonte histórica divergiu do contraste congelado")
    modelo = encoder or EncoderSemanticoONNX(
        PASTA_ENCODER, sha256_modelo=SHA_ENCODER, batch_size=16,
    )
    textos = [texto for caso in CONTRASTES
              for texto in (caso["consulta"], caso["positivo"], caso["negativo"])]
    vetores = np.asarray(modelo.codificar(textos), dtype=np.float32)
    if vetores.shape[0] != len(textos):
        raise ValueError("encoder não devolveu um vetor por texto")
    resultados = []
    for indice, caso in enumerate(CONTRASTES):
        consulta, positivo, negativo = vetores[3 * indice:3 * indice + 3]
        sim_positivo = float(np.dot(consulta, positivo))
        sim_negativo = float(np.dot(consulta, negativo))
        resultados.append({"id": caso["id"],
                           "similaridade_positivo": round(sim_positivo, 4),
                           "similaridade_negativo": round(sim_negativo, 4),
                           "ordem_correta": bool(sim_positivo > sim_negativo)})
    return {
        "resultados": resultados,
        "ordens_corretas": sum(item["ordem_correta"] for item in resultados),
        "total": len(resultados),
        "uso": "somente_recuperacao_para_revisao",
        "aprovado_para_compor": False,
        "aprovado_para_producao": False,
    }


def main() -> None:
    print(json.dumps(medir_contrastes(), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
