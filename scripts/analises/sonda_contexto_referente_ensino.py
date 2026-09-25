"""Sonda offline de vínculos estruturados entre referente e grandeza.

Um trecho contextual literal comprova transporte, não a ligação semântica
proposta entre sensor e grandeza. Nenhum resultado aprova fala ou efeito.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Callable

import requests

from scripts.analises.contrato_requisitos_ensino import (
    Requisito, comparar_rotulo_da_medida,
)
from scripts.analises.revisao_referencias_ensino import carregar_painel


INSTRUCAO = (
    "Analise um cenário sintético. Proponha ligações possíveis entre uma "
    "expressão literal do exemplo que nomeie o medidor e uma grandeza citada "
    "literalmente no contexto. Copie um trecho CONTÍGUO E EXATO do contexto "
    "para cada ligação. Se houver dois referentes possíveis para a mesma "
    "expressão, inclua os dois; não escolha por tópico. Sem contexto, use "
    "lista vazia. Não julgue se a leitura aconteceu ou se o exemplo está "
    "correto. Devolva JSON com vinculos: expressao_exemplo, grandeza, "
    "trecho_contexto."
)
FORMATO = {
    "type": "object", "properties": {
        "vinculos": {"type": "array", "items": {"type": "object", "properties": {
            "expressao_exemplo": {"type": "string"},
            "grandeza": {"type": "string"},
            "trecho_contexto": {"type": "string"},
        }, "required": ["expressao_exemplo", "grandeza", "trecho_contexto"],
           "additionalProperties": False}},
    }, "required": ["vinculos"], "additionalProperties": False,
}


def _unicidade_medidor_declarada(expressao: str, contextos: list[str]) -> bool:
    """Exige declaração positiva; silêncio sobre outros medidores não basta.

    Esta leitura textual estreita só classifica candidatos para revisão. Não
    certifica que o contexto está completo nem resolve a referência.
    """
    nominal = re.search(
        r"\b(?:o|a|os|as|um|uma|esse|essa|este|esta)\s+([^\W\d_]+)\b",
        expressao.casefold(), flags=re.UNICODE,
    )
    if nominal is None:
        return False
    medidor = nominal.group(1)
    plural = medidor + ("es" if medidor.endswith("r") else "s")
    declaracao = re.compile(
        rf"\b(?:existe|há|tem)\s+(?:um único|uma única|apenas um|"
        rf"apenas uma|só um|só uma)\s+{re.escape(medidor)}\b",
        flags=re.IGNORECASE,
    )
    contradicao = re.compile(
        rf"\b(?:(?:dois|duas|vários|várias)\s+{re.escape(plural)}|"
        rf"outro\s+{re.escape(medidor)})\b",
        flags=re.IGNORECASE,
    )
    texto = " ".join(contextos)
    if contradicao.search(texto):
        return False
    for encontrado in declaracao.finditer(texto):
        prefixo = texto[max(0, encontrado.start() - 12):encontrado.start()].casefold()
        if not re.search(r"\bnão\s*$", prefixo):
            return True
    return False


def conferir_vinculos(caso: dict[str, Any], proposta: Any) -> dict[str, Any]:
    base = {"aprovado_para_compor": False, "referente_resolvido": False,
            "contexto_autorizou_efeito": False, "contexto_verificado": False,
            "cobertura_contexto_verificada": False,
            "origem_contexto": "cenario_sintetico"}
    itens = proposta.get("vinculos") if isinstance(proposta, dict) else None
    if not isinstance(itens, list) or not all(isinstance(item, dict) for item in itens):
        return {**base, "estado": "formato_invalido"}
    if not itens:
        return {**base, "estado": "referencia_nao_proposta"}
    exemplo = caso["exemplo"]
    contextos = caso.get("contexto") or []
    for item in itens:
        if (not all(isinstance(item.get(chave), str) and item[chave].strip()
                    for chave in ("expressao_exemplo", "grandeza", "trecho_contexto"))):
            return {**base, "estado": "vinculo_invalido"}
        if item["expressao_exemplo"] not in exemplo:
            return {**base, "estado": "expressao_sem_origem"}
        if not any(item["trecho_contexto"] in texto for texto in contextos):
            return {**base, "estado": "trecho_contexto_sem_origem"}
        if item["grandeza"].casefold() not in item["trecho_contexto"].casefold():
            return {**base, "estado": "grandeza_sem_ancora"}
    pares = [(item["expressao_exemplo"], item["grandeza"]) for item in itens]
    if len(pares) != len(set(pares)):
        return {**base, "estado": "vinculos_duplicados"}
    # Um nome explícito na fala vence a proposta de referência genérica.
    for item in itens:
        qualificacao_interna = re.search(
            r"\b(?:o|a|os|as|um|uma|esse|essa|este|esta)\s+"
            r"[^\W\d_]+\s+((?:de|do|da|dos|das)\s+[^\W\d_]+)",
            item["expressao_exemplo"].casefold(), flags=re.UNICODE,
        )
        if (qualificacao_interna is not None
                and qualificacao_interna.group(1) not in item["grandeza"].casefold()):
            return {**base, "estado": "referencia_qualificada_na_fala"}
        posicao = exemplo.index(item["expressao_exemplo"]) + len(item["expressao_exemplo"])
        if re.match(r"\s+(?:de|do|da|dos|das)\s+\w+", exemplo[posicao:], flags=re.IGNORECASE):
            return {**base, "estado": "referencia_qualificada_na_fala"}
    rotulo = comparar_rotulo_da_medida(
        Requisito("limiar", "menor_que", caso["definicao"]), exemplo,
    )
    if rotulo["estado"] in {"qualificador_divergente", "rotulo_diferente"}:
        return {**base, "estado": "rotulo_explicito_divergente"}
    grandezas = {item["grandeza"].casefold() for item in itens}
    if len(grandezas) != 1:
        return {**base, "estado": "referencia_ambigua",
                "grandezas_candidatas": sorted(grandezas)}
    requerida = str(rotulo.get("entidade_requerida") or "").casefold()
    unica = next(iter(grandezas))
    if not requerida:
        return {**base, "estado": "entidade_origem_indeterminada"}
    cabeca = requerida.split()[0]
    padrao_grandeza = re.compile(
        rf"\b{re.escape(cabeca)}\s+(?:do|da|de|dos|das)\s+\w+",
        flags=re.IGNORECASE,
    )
    grandezas_no_contexto = {
        encontrado.group().casefold()
        for texto in contextos
        for encontrado in padrao_grandeza.finditer(texto)
    }
    # A lista proposta pelo modelo pode omitir um segundo medidor. Nesse
    # caso, só um qualificador explícito na própria expressão a desambigua.
    qualificador = " ".join(unica.split()[1:])
    expressao = itens[0]["expressao_exemplo"].casefold()
    if (len(grandezas_no_contexto) > 1
            and (not qualificador or qualificador not in expressao)):
        return {**base, "estado": "contexto_com_grandezas_concorrentes",
                "grandezas_citadas": sorted(grandezas_no_contexto)}
    if unica != requerida:
        return {**base, "estado": "grandeza_contextual_diferente"}
    if not _unicidade_medidor_declarada(expressao, contextos):
        return {**base, "estado": "unicidade_do_medidor_nao_demonstrada"}
    return {**base, "estado": "candidato_contextual_unico_revisao_pendente",
            "grandeza_candidata": itens[0]["grandeza"],
            "expressao_exemplo": itens[0]["expressao_exemplo"]}


def medir_caso(caso: dict[str, Any], *, post: Callable[..., Any] = requests.post) -> dict[str, Any]:
    inicio = time.monotonic()
    entrada = {chave: caso[chave] for chave in ("definicao", "exemplo", "contexto")}
    try:
        resposta = post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": "qwen3:4b-instruct", "messages": [
                {"role": "system", "content": INSTRUCAO},
                {"role": "user", "content": json.dumps(entrada, ensure_ascii=False)},
            ], "stream": False, "format": FORMATO,
                  "options": {"temperature": 0, "num_predict": 240}},
            timeout=80,
        )
        resposta.raise_for_status()
        proposta = json.loads(resposta.json()["message"]["content"])
        erro = ""
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        proposta, erro = {}, type(exc).__name__
    return {"id": caso["id"], "conferencia": conferir_vinculos(caso, proposta),
            "proposta": proposta, "erro": erro,
            "latencia_s": round(time.monotonic() - inicio, 3),
            "aprovado_para_producao": False}


def main() -> None:
    for caso in carregar_painel():
        print(json.dumps(medir_caso(caso), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
