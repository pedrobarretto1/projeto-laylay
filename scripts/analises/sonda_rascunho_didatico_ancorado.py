"""Experimento isolado de aula composta a partir de poucas frases-fonte.

Não participa do runtime nem autoriza uma alegação só porque um ID foi citado.
Os trechos são curados de um artefato anterior para separar geração de busca.
"""

from __future__ import annotations

import json
import re

import requests

from scripts.analises.sonda_verificacao_ensino_com_fonte import carregar_fontes, frases_fonte


CASOS = (
    (12, "Me ensine a diferença entre planta baixa e corte na arquitetura, com um exemplo de uma casa.", ("E3", "E5")),
    (3, "Me explique fotossíntese de um jeito simples, com um exemplo do papel da luz.", ("E2", "E4")),
    (19, "Me explique a diferença entre plantas anuais e perenes com um exemplo de jardinagem.", ("E5", "E7")),
)


def gerar(pedido: str, frases: list[dict[str, str]]) -> dict:
    evidencia = "\n".join(f"{f['id']}: {f['texto']}" for f in frases)
    mensagens = [
        {"role": "system", "content": (
            "Você é Laylay ensinando com clareza e naturalidade. Use somente as "
            "frases-fonte fornecidas para afirmações sobre o mundo. Primeiro "
            "dê uma definição fiel. Depois um exemplo curto e explicitamente "
            "hipotético que mostre como aplicar a definição; não invente fatos "
            "específicos. Se a fonte não permitir o exemplo, diga o limite. "
            "Responda JSON com chaves definicao, exemplo, ids_definicao, "
            "ids_exemplo. Os IDs devem ser uma lista de IDs fornecidos, "
            "ou lista vazia se não houver apoio. Não escreva links inventados."
        )},
        {"role": "user", "content": f"Pedido: {pedido}\nFontes lidas:\n{evidencia}"},
    ]
    resposta = requests.post(
        "http://127.0.0.1:11434/api/chat",
        json={"model": "qwen3:4b-instruct", "messages": mensagens,
              "stream": False, "format": "json",
              "options": {"temperature": 0, "num_predict": 300}},
        timeout=80,
    )
    resposta.raise_for_status()
    gerado = json.loads(resposta.json()["message"]["content"])
    diagnostico = diagnosticar_citacoes(gerado, frases)
    return {"pedido": pedido, "fontes": frases, "gerado": gerado,
            "diagnostico": diagnostico,
            "auditoria_literal": auditar_publicacao(gerado, frases)}


def diagnosticar_citacoes(gerado: dict, frases: list[dict[str, str]]) -> dict[str, bool]:
    """IDs existentes são condição necessária, nunca prova de implicação."""
    ids_validos = {frase["id"] for frase in frases}
    definicao = gerado.get("ids_definicao")
    exemplo = gerado.get("ids_exemplo")
    return {
        "ids_existentes": (
            isinstance(definicao, list) and isinstance(exemplo, list)
            and all(isinstance(item, str) and item in ids_validos for item in definicao + exemplo)
        ),
        "definicao_com_id": isinstance(definicao, list) and bool(definicao),
        "exemplo_com_id": isinstance(exemplo, list) and bool(exemplo),
        # A veracidade dos dois campos continua exigindo julgamento separado.
        "implicacao_verificada": False,
    }


def auditar_publicacao(gerado: dict, frases: list[dict[str, str]]) -> dict[str, bool]:
    """Portão extrativo experimental; não mede paráfrase nem verdade da fonte."""
    por_id = {frase["id"]: frase["texto"] for frase in frases}

    def normalizar(texto: str) -> str:
        texto = str(texto or "").translate(str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"}))
        texto = re.sub(r"\s+", " ", texto).strip()
        return re.sub(r"\s+([.,;:!?])", r"\1", texto).casefold()

    def campo_literal(nome: str) -> bool:
        ids = gerado.get(f"ids_{nome}")
        texto = str(gerado.get(nome) or "").strip()
        if not isinstance(ids, list) or not ids or not texto or any(
            not isinstance(item, str) or item not in por_id for item in ids
        ):
            return False
        fontes_citadas = {normalizar(por_id[item]) for item in ids}
        partes = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý“\"(])", texto)
        return bool(partes) and all(normalizar(parte) in fontes_citadas for parte in partes)

    definicao_literal = campo_literal("definicao")
    exemplo_literal = campo_literal("exemplo")
    return {"definicao_literal": definicao_literal,
            "exemplo_literal": exemplo_literal,
            "publicavel": definicao_literal and exemplo_literal}


def main() -> None:
    fontes = carregar_fontes()
    for indice, pedido, ids in CASOS:
        frases = [frase for frase in frases_fonte(fontes[indice]) if frase["id"] in ids]
        print(json.dumps(gerar(pedido, frases), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
