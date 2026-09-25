"""Triagem cega auxiliar do painel de referências, sem gabarito ou promoção.

O segundo modelo recebe somente os cenários congelados. Seus julgamentos
podem apontar discordâncias para revisão humana, mas não são rótulos ouro.
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any, Callable

import requests

from scripts.analises.revisao_referencias_ensino import (
    ROTULOS_LEITURA, ROTULOS_REFERENTE, carregar_painel, validar_revisao,
)


MODELO_AUXILIAR = "gemma4:26b"
INSTRUCAO = (
    "Revise um cenário sintético de ensino sem assumir fatos ausentes. "
    "Compare a grandeza do exemplo com a da definição: referente=mesmo, "
    "outro ou indeterminado. Julgue separadamente se o exemplo afirma, "
    "nega ou não estabelece que uma leitura ocorreu: leitura=afirmada, "
    "negada ou indeterminada. Contexto pode desambiguar referente, mas não "
    "prova efeito externo. Copie uma evidencia literal da definição, do "
    "exemplo ou do contexto; justifique em uma frase. Se falta antecedente "
    "para escolher entre dois sensores, marque indeterminado. Não complete "
    "o cenário com suposições. Responda só com JSON."
)
FORMATO = {
    "type": "object", "properties": {
        "referente": {"type": "string", "enum": sorted(ROTULOS_REFERENTE)},
        "leitura": {"type": "string", "enum": sorted(ROTULOS_LEITURA)},
        "evidencia": {"type": "string"},
        "justificativa": {"type": "string"},
    },
    "required": ["referente", "leitura", "evidencia", "justificativa"],
    "additionalProperties": False,
}


def _revisao_valida(caso: dict[str, Any], proposta: Any) -> bool:
    if not isinstance(proposta, dict) or set(proposta) != set(FORMATO["required"]):
        return False
    if (proposta["referente"] not in ROTULOS_REFERENTE
            or proposta["leitura"] not in ROTULOS_LEITURA
            or not isinstance(proposta["evidencia"], str)
            or not isinstance(proposta["justificativa"], str)
            or len(proposta["justificativa"].strip()) < 10):
        return False
    return any(proposta["evidencia"] and proposta["evidencia"] in texto
               for texto in (caso["definicao"], caso["exemplo"], *caso["contexto"]))


def revisar_caso(caso: dict[str, Any], *,
                post: Callable[..., Any] = requests.post) -> dict[str, Any]:
    inicio = time.monotonic()
    entrada = {chave: caso[chave]
               for chave in ("definicao", "exemplo", "contexto")}
    try:
        resposta = post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": MODELO_AUXILIAR, "messages": [
                {"role": "system", "content": INSTRUCAO},
                {"role": "user", "content": json.dumps(entrada, ensure_ascii=False)},
            ], "stream": False, "think": False, "format": FORMATO,
                  "options": {"temperature": 0, "num_predict": 320}},
            timeout=120,
        )
        resposta.raise_for_status()
        proposta = json.loads(resposta.json()["message"]["content"])
        erro = "" if _revisao_valida(caso, proposta) else "revisao_invalida"
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        proposta, erro = {}, type(exc).__name__
    return {
        "id": caso["id"], "modelo_auxiliar": MODELO_AUXILIAR,
        "revisao": proposta if not erro else {}, "erro": erro,
        "latencia_s": round(time.monotonic() - inicio, 3),
        "revisao_humana_confirmada": False,
        "aprovado_para_treino": False, "aprovado_para_compor": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Triagem cega cruzada de referências")
    parser.add_argument("--ids", nargs="*", help="subconjunto para sonda de latência")
    opcoes = parser.parse_args()
    casos = carregar_painel()
    if opcoes.ids:
        escolhidos = set(opcoes.ids)
        desconhecidos = escolhidos - {caso["id"] for caso in casos}
        if desconhecidos:
            parser.error(f"IDs desconhecidos: {sorted(desconhecidos)}")
        casos = [caso for caso in casos if caso["id"] in escolhidos]
    resultados = []
    for caso in casos:
        resultado = revisar_caso(caso)
        resultados.append(resultado)
        print(json.dumps(resultado, ensure_ascii=False), flush=True)
        if resultado["erro"]:
            # Timeout/formato quebrado não justifica gastar o painel inteiro.
            break
    if len(casos) == 10 and all(not item["erro"] for item in resultados):
        revisoes = [{"id": item["id"], **item["revisao"]} for item in resultados]
        print(json.dumps({"validacao_formato": validar_revisao(revisoes),
                          "modelo_auxiliar_nao_e_gabarito": True},
                         ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
