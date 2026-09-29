"""Experimento offline: modelo propõe índices e fontes para a fala didática.

Não consulta páginas, não altera a Laylay e não usa a proposta como juiz de
verdade. A origem e o texto das fontes são registrados fora do modelo.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Mapping

import requests

from mente_laylay.cognicao.auditoria_alegacoes_didaticas import (
    auditar_fala_didatica_sombra,
)
from scripts.analises.contrato_alegacoes_didaticas import conferir_mapa_alegacoes
from scripts.analises.contrato_unidades_ensino import extrair_contas_explicitas


_PAPEIS = (
    "premissa_usuario", "regra_hipotetica", "comparacao_numerica",
    "conclusao_derivada", "fato_externo", "nao_factual",
)
_FORMATO = {
    "type": "object", "properties": {
        "alegacoes": {"type": "array", "items": {"type": "object", "properties": {
            "indice": {"type": "integer"},
            "papel": {"type": "string", "enum": list(_PAPEIS)},
            "evidencias": {"type": "array", "items": {"type": "object", "properties": {
                "fonte_id": {"type": "string"}, "citacao": {"type": "string"},
            }, "required": ["fonte_id", "citacao"], "additionalProperties": False}},
        }, "required": ["indice", "papel", "evidencias"],
            "additionalProperties": False}},
    }, "required": ["alegacoes"], "additionalProperties": False,
}
_INSTRUCAO = (
    "Você propõe um mapa da fala didática, não decide se ela está correta. "
    "Retorne uma entrada para CADA índice de segmento, na mesma ordem. "
    "Escolha um papel proposto. Cite apenas uma frase contínua e exata de uma "
    "fonte listada se ela sustenta a alegação INTEIRA, inclusive condições, "
    "entidade, números e causa. Se parte do segmento não tiver apoio, use "
    "evidencias vazias; não cite só a metade fácil. Não use conhecimentos "
    "externos nem falas anteriores da assistente. Responda somente JSON."
)
_FORMATO_CLASSIFICACAO = {
    "type": "object", "additionalProperties": False,
    "required": ["segmentos"],
    "properties": {"segmentos": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["indice", "tipo", "rotulo"],
        "properties": {
            "indice": {"type": "integer"},
            "tipo": {"type": "string", "enum": ["qualificacao_qualitativa", "outro"]},
            "rotulo": {"type": "string"},
        },
    }}},
}
_INSTRUCAO_CLASSIFICACAO = (
    "Esta e somente uma triagem de segmentos de uma fala, nao uma prova de "
    "verdade. Para CADA indice, na mesma ordem, marque "
    "qualificacao_qualitativa APENAS quando o segmento atribui a uma "
    "medicao uma categoria descritiva como seco, alto, frio ou seguro. "
    "Copie em rotulo apenas a palavra dessa categoria tal como aparece "
    "no segmento. Medicao numerica literal, comparacao entre numeros, "
    "regra citada e codigo sao outro, com rotulo vazio. Nao extraia "
    "evidencias nesta etapa. Responda somente JSON."
)


def conferir_classificacao_qualitativa(
    fala: str, bruto: object,
) -> dict[str, object]:
    """Confere cobertura e rotulo literal; o tipo continua mera proposta."""
    base: dict[str, object] = {
        "estado": "classificacao_invalida", "candidatos": [],
        "classificacao_verificada": False,
        "aprovado_para_producao": False, "autoriza_efeito": False,
    }
    if not isinstance(fala, str) or not isinstance(bruto, Mapping):
        return base
    auditoria = auditar_fala_didatica_sombra(fala, fontes={}, plano_id="sonda")
    segmentos = list(auditoria["segmentos"])
    propostas = bruto.get("segmentos")
    if (not auditoria["cobertura_textual"] or not segmentos
            or not isinstance(propostas, list)
            or len(propostas) != len(segmentos)):
        return base
    candidatos: list[dict[str, object]] = []
    for indice, (segmento, proposta) in enumerate(zip(segmentos, propostas)):
        if (not isinstance(proposta, Mapping)
                or set(proposta) != {"indice", "tipo", "rotulo"}
                or type(proposta["indice"]) is not int
                or proposta["indice"] != indice
                or not isinstance(proposta["tipo"], str)
                or proposta["tipo"] not in {
                    "qualificacao_qualitativa", "outro",
                }
                or not isinstance(proposta["rotulo"], str)):
            return base
        if proposta["tipo"] == "outro":
            if proposta["rotulo"]:
                return base
            continue
        rotulo = proposta["rotulo"]
        if (not rotulo or len(rotulo) > 60
                or not re.search(rf"(?<!\w){re.escape(rotulo)}(?!\w)",
                                 segmento["texto"], re.IGNORECASE)):
            return base
        candidatos.append({"indice": indice, "inicio": segmento["inicio"],
                           "fim": segmento["fim"], "texto": segmento["texto"],
                           "rotulo": rotulo})
    return {**base, "estado": "candidatos_qualitativos_revisao_pendente",
            "candidatos": candidatos}


def medir_classificacao_caso(caso: Mapping[str, object]) -> dict[str, object]:
    """Segunda sonda isolada: localiza candidatos sem pedir evidencias."""
    from scripts.analises.sonda_produtor_condicoes_v2 import _consultar_modelo

    fala = str(caso["fala"])
    auditoria = auditar_fala_didatica_sombra(fala, fontes={}, plano_id="sonda")
    entrada = {"segmentos": [
        {"indice": indice, "texto": item["texto"]}
        for indice, item in enumerate(auditoria["segmentos"])
    ], "fontes": caso["fontes"]}
    inicio = time.monotonic()
    try:
        bruto: Any = _consultar_modelo(
            _INSTRUCAO_CLASSIFICACAO, entrada, _FORMATO_CLASSIFICACAO,
            url="http://127.0.0.1:11434/api/chat", modelo="qwen3:4b-instruct",
        )
        erro = ""
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        bruto, erro = {}, type(exc).__name__
    conferido = conferir_classificacao_qualitativa(fala, bruto)
    return {"id": caso["id"], "proposta": bruto, "resultado": conferido,
            "erro": erro, "latencia_s": round(time.monotonic() - inicio, 2),
            "aprovado_para_producao": False}


def conferir_proposta(
    fala: str, fontes: Mapping[str, Mapping[str, str]], bruto: object,
) -> dict[str, object]:
    base: dict[str, object] = {"aprovado_para_producao": False,
                               "cobertura_textual": False, "alegacoes": [],
                               "recibos_calculo": (
                                   extrair_contas_explicitas(fala)
                                   if isinstance(fala, str) else []
                               )}
    if not isinstance(fala, str) or len(fala) > 4000:
        return {**base, "estado": "fala_invalida"}
    auditoria = auditar_fala_didatica_sombra(fala, fontes={}, plano_id="sonda")
    segmentos = list(auditoria["segmentos"])
    if not auditoria["cobertura_textual"] or not segmentos:
        return {**base, "estado": "fala_invalida"}
    itens = bruto.get("alegacoes") if isinstance(bruto, Mapping) else None
    if (not isinstance(itens, list) or len(itens) != len(segmentos)
            or any(not isinstance(item, Mapping)
                   or type(item.get("indice")) is not int
                   or item["indice"] != indice
                   for indice, item in enumerate(itens))):
        return {**base, "estado": "indices_invalidos",
                "segmentos_esperados": len(segmentos)}
    propostas = [
        {"inicio": segmento["inicio"], "fim": segmento["fim"],
         "papel": item.get("papel"), "evidencias": item.get("evidencias"),
         **({"derivacao": item["derivacao"]}
            if "derivacao" in item else {})}
        for segmento, item in zip(segmentos, itens)
    ]
    conferencia = conferir_mapa_alegacoes(
        fala, fontes=fontes, propostas=propostas,
    )
    return {**base, **conferencia, "aprovado_para_producao": False,
            "segmentos_esperados": len(segmentos)}


def medir_caso(caso: Mapping[str, object]) -> dict[str, object]:
    fala = str(caso["fala"])
    fontes = caso["fontes"]
    auditoria = auditar_fala_didatica_sombra(fala, fontes={}, plano_id="sonda")
    segmentos = [
        {"indice": indice, "texto": item["texto"]}
        for indice, item in enumerate(auditoria["segmentos"])
    ]
    entrada = {"segmentos": segmentos, "fontes": fontes}
    inicio = time.monotonic()
    try:
        resposta = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json={"model": "qwen3:4b-instruct", "stream": False,
                  "format": _FORMATO,
                  "messages": [
                      {"role": "system", "content": _INSTRUCAO},
                      {"role": "user", "content": json.dumps(entrada, ensure_ascii=False)},
                  ],
                  "options": {"temperature": 0, "num_predict": 900}},
            timeout=80,
        )
        resposta.raise_for_status()
        bruto: Any = json.loads(resposta.json()["message"]["content"])
        erro = ""
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        bruto, erro = {}, type(exc).__name__
    conferido = conferir_proposta(fala, fontes, bruto)
    return {
        "id": caso["id"], "dominio": caso["dominio"],
        "estado_formal": conferido["estado"],
        "estados_alegacoes": [item["estado"] for item in conferido["alegacoes"]],
        "papeis_propostos": [item["papel_proposto"] for item in conferido["alegacoes"]],
        "proposta": bruto,
        "erro": erro, "latencia_s": round(time.monotonic() - inicio, 2),
        "aprovado_para_producao": False,
    }


CASOS: tuple[dict[str, object], ...] = (
    {
        "id": "SENSOR_REAL_24_09", "dominio": "irrigacao",
        "fontes": {
            "cenario": {"origem": "usuario", "texto": (
                "Neste cenário hipotético há exatamente dois sensores: um mede "
                "a umidade do solo e o outro mede a umidade do ar. Estamos "
                "falando do sensor de umidade do solo. O sensor leu 15% de umidade."
            )},
            "regra": {"origem": "usuario", "texto": (
                "Se o modo automático liga a bomba quando a umidade do solo "
                "cai abaixo de 20%, o que deve acontecer nesse cenário e por quê?"
            )},
        },
        "fala": (
            "Se a umidade do solo cai abaixo de 20% e o modo automático está "
            "ligado, a bomba deve ligar para regar o solo — porque o solo está "
            "seca demais para manter a vegetação saudável. O sensor detecta "
            "15%, que é abaixo do limiar, então o sistema age automaticamente "
            "pra manter o equilíbrio de umidade."
        ),
    },
    {
        "id": "DIVISAO_CONTROLE", "dominio": "matematica",
        "fontes": {"enunciado": {"origem": "usuario", "texto":
            "Divida igualmente 12 objetos entre 3 pessoas."}},
        "fala": "12 dividido por 3 = 4. Cada pessoa recebe 4 objetos.",
    },
    {
        "id": "FLOR_CONDICAO", "dominio": "floricultura",
        "fontes": {"fonte": {"origem": "pesquisa_verificada", "texto":
            "Em climas frios, certas begônias perenes podem ser cultivadas como anuais."}},
        "fala": "Begônias são plantas anuais. Elas florescem todo inverno.",
    },
    {
        "id": "CODIGO_CONDICAO", "dominio": "programacao",
        "fontes": {"enunciado": {"origem": "usuario", "texto":
            "A função retorna True se x > 0; caso contrário retorna False."}},
        "fala": "A função sempre retorna True. Ela ignora números negativos.",
    },
    {
        "id": "LITERAL_CONTROLE", "dominio": "programacao",
        "fontes": {"enunciado": {"origem": "usuario", "texto":
            "A função retorna True se x > 0."}},
        "fala": "A função retorna True se x > 0.",
    },
)


def main() -> None:
    for caso in CASOS:
        print(json.dumps(medir_caso(caso), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
