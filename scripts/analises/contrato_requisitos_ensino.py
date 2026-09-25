"""Contrato offline de requisitos ancorados para exemplos didáticos.

Um modelo pode propor trechos, mas não autoriza a equivalência entre eles.
Só cópia literal e comparação numérica pequena recebem prova automática;
paráfrase, papel semântico e verdade externa permanecem pendentes.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable
import unicodedata


@dataclass(frozen=True)
class Requisito:
    id: str
    tipo: str  # literal, condicao_textual, menor_que ou parafrase
    trecho_definicao: str


@dataclass(frozen=True)
class Alinhamento:
    id: str
    trecho_exemplo: str


def localizar_valor_para_limiar(requisito: Requisito, exemplo: str) -> dict[str, object]:
    """Localiza valor+unidade únicos e reutiliza a comparação já contratada.

    Mesmo quando a aritmética é válida, não confere entidade, autorização,
    escopo da negação, modo, papéis ou causalidade da frase.
    """
    base: dict[str, object] = {
        "aprovado_para_compor": False,
        "comparacao_numerica": False,
        "entidade_verificada": False,
        "modo_verificado": False,
        "papeis_verificados": False,
        "trecho_exemplo": "",
    }
    if requisito.tipo != "menor_que":
        return {**base, "estado": "tipo_nao_suportado"}
    origem = re.search(r"\babaixo\s+de\s+(\d+(?:[.,]\d+)?)\s*(%|°[a-z]+|[a-z]+)",
                       _normalizar(requisito.trecho_definicao))
    if not origem:
        return {**base, "estado": "limiar_nao_conferivel"}
    unidade_origem = origem.group(2)
    numeros = list(re.finditer(
        r"(?<![\w.,])(\d+(?:[.,]\d+)?)\s*(%|°[a-zA-Z]|[a-zA-Z]+)(?!\w)",
        exemplo, flags=re.IGNORECASE,
    ))
    candidatos = [item for item in numeros
                  if _normalizar(item.group(2)) == unidade_origem]
    if not candidatos:
        return {**base, "estado": "unidade_incompativel" if numeros else "valor_ausente"}
    if len(candidatos) != 1:
        return {**base, "estado": "valores_ambiguos"}
    candidato = candidatos[0]
    trecho = candidato.group()
    prefixo = exemplo[:candidato.start()].rsplit(",", 1)[-1].rsplit(";", 1)[-1]
    if re.search(r"\b(?:nao|nunca|sem)\b", _normalizar(prefixo)):
        return {**base, "estado": "negacao_ou_escopo_pendente",
                "trecho_exemplo": trecho}
    recibo = conferir_requisitos(
        requisito.trecho_definicao, exemplo, (requisito,),
        (Alinhamento(requisito.id, trecho),),
    )
    situacao = recibo.get("slots", {}).get(requisito.id)
    if situacao == "comparacao_numerica_confirmada":
        return {**base, "estado": "numero_conferido_entidade_pendente",
                "comparacao_numerica": True, "trecho_exemplo": trecho}
    if situacao == "condicao_violada":
        return {**base, "estado": "limiar_nao_satisfeito",
                "trecho_exemplo": trecho}
    return {**base, "estado": "comparacao_nao_conferivel",
            "trecho_exemplo": trecho}


def comparar_rotulo_da_medida(requisito: Requisito, exemplo: str) -> dict[str, object]:
    """Compara rótulos explícitos junto ao limiar e ao valor observado.

    O padrão cobre apenas frases curtas de condição e o rótulo após o valor.
    Correspondência textual não confirma medição real nem referência implícita.
    """
    base: dict[str, object] = {
        "aprovado_para_compor": False,
        "entidade_verificada": False,
        "entidade_requerida": "",
        "entidade_exemplo": "",
        "rotulo_literal_igual": False,
    }
    numero = localizar_valor_para_limiar(requisito, exemplo)
    if numero["estado"] != "numero_conferido_entidade_pendente":
        return {**base, "estado": numero["estado"], "pista_numerica": numero}
    origem = re.search(
        r"\b(?:se|quando)\s+(?:a|o|as|os)\s+(.+?)\s+"
        r"(?:cair|ficar|estiver|for)\s+abaixo\s+de\s+"
        r"\d+(?:[.,]\d+)?\s*(?:%|°[a-z]+|[a-z]+)",
        requisito.trecho_definicao, flags=re.IGNORECASE,
    )
    if not origem:
        return {**base, "estado": "entidade_origem_indeterminada",
                "pista_numerica": numero}
    entidade_requerida = origem.group(1).strip()
    trecho_numero = str(numero["trecho_exemplo"])
    posicao = exemplo.index(trecho_numero) + len(trecho_numero)
    cauda = exemplo[posicao:]
    rotulo = re.match(r"\s+(?:de|da|do|das|dos)\s+([^.,;!?]+)",
                      cauda, flags=re.IGNORECASE)
    if not rotulo:
        return {**base, "estado": "rotulo_exemplo_ausente",
                "entidade_requerida": entidade_requerida,
                "pista_numerica": numero}
    entidade_exemplo = re.split(
        r"\s+(?:e|mas|porque|porem|porém|enquanto)\s+",
        rotulo.group(1), maxsplit=1, flags=re.IGNORECASE,
    )[0].strip()
    if not entidade_exemplo:
        return {**base, "estado": "rotulo_exemplo_ausente",
                "entidade_requerida": entidade_requerida,
                "pista_numerica": numero}
    requerida = _normalizar(entidade_requerida).split()
    encontrada = _normalizar(entidade_exemplo).split()
    if requerida == encontrada:
        estado = "rotulo_literal_igual_revisao_pendente"
    elif encontrada == requerida[:len(encontrada)]:
        estado = "qualificador_ausente"
    elif requerida and encontrada and requerida[0] == encontrada[0]:
        estado = "qualificador_divergente"
    else:
        estado = "rotulo_diferente"
    return {**base, "estado": estado,
            "entidade_requerida": entidade_requerida,
            "entidade_exemplo": entidade_exemplo,
            "rotulo_literal_igual": estado == "rotulo_literal_igual_revisao_pendente",
            "pista_numerica": numero}


def _normalizar(texto: str) -> str:
    sem_acentos = "".join(
        letra for letra in unicodedata.normalize("NFKD", texto.casefold())
        if not unicodedata.combining(letra)
    )
    return " ".join(sem_acentos.split())


def conferir_requisitos(
    definicao: str,
    exemplo: str,
    requisitos: Iterable[Requisito],
    alinhamentos: Iterable[Alinhamento],
) -> dict[str, object]:
    """Compara spans e aritmética; nunca certifica a interpretação inteira."""
    base: dict[str, object] = {
        "aprovado_para_compor": False,
        "anotacao_semantica_revisada": False,
        "papeis_semanticos_verificados": False,
    }
    regra = tuple(requisitos)
    propostas = tuple(alinhamentos)
    ids_regra = [item.id for item in regra]
    ids_propostas = [item.id for item in propostas]
    if (not regra or len(ids_regra) != len(set(ids_regra))
            or len(ids_propostas) != len(set(ids_propostas))
            or set(ids_regra) != set(ids_propostas)
            or any(item.tipo not in {"literal", "condicao_textual", "menor_que", "parafrase"}
                   for item in regra)):
        return {**base, "estado": "contrato_invalido"}
    if any(not item.trecho_definicao.strip()
           or _normalizar(item.trecho_definicao) not in _normalizar(definicao)
           for item in regra):
        return {**base, "estado": "requisito_origem_invalida"}
    por_id = {item.id: item for item in propostas}
    slots: dict[str, str] = {}
    for requisito in regra:
        trecho = por_id[requisito.id].trecho_exemplo.strip()
        if not trecho:
            slots[requisito.id] = "requisito_nao_demonstrado"
            continue
        if _normalizar(trecho) not in _normalizar(exemplo):
            slots[requisito.id] = "trecho_exemplo_invalido"
            continue
        if requisito.tipo == "literal":
            slots[requisito.id] = (
                "literal_localizado"
                if _normalizar(requisito.trecho_definicao) in _normalizar(trecho)
                else "requisito_nao_demonstrado"
            )
        elif requisito.tipo == "condicao_textual":
            slots[requisito.id] = (
                "condicao_semantica_pendente"
                if _normalizar(requisito.trecho_definicao) in _normalizar(trecho)
                else "requisito_nao_demonstrado"
            )
        elif requisito.tipo == "parafrase":
            slots[requisito.id] = (
                "literal_localizado"
                if _normalizar(requisito.trecho_definicao) in _normalizar(trecho)
                else "parafrase_pendente"
            )
        else:
            origem = re.search(r"\babaixo\s+de\s+(\d+(?:[.,]\d+)?)\s*(%|°[a-z]+|[a-z]+)?",
                                _normalizar(requisito.trecho_definicao))
            destino = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*(%|°[a-z]+|[a-z]+)?",
                                   _normalizar(trecho))
            if not origem or not destino or (origem.group(2) or "") != (destino.group(2) or ""):
                slots[requisito.id] = "comparacao_nao_conferivel"
            elif float(destino.group(1).replace(",", ".")) < float(origem.group(1).replace(",", ".")):
                slots[requisito.id] = "comparacao_numerica_confirmada"
            else:
                slots[requisito.id] = "condicao_violada"
    resultados = set(slots.values())
    if "trecho_exemplo_invalido" in resultados:
        estado = "alinhamento_invalido"
    elif "condicao_violada" in resultados:
        estado = "condicao_violada"
    elif "requisito_nao_demonstrado" in resultados:
        estado = "requisito_faltante"
    elif resultados & {"parafrase_pendente", "comparacao_nao_conferivel",
                       "condicao_semantica_pendente"}:
        estado = "revisao_semantica_pendente"
    else:
        estado = "estrutura_ancorada_revisao_pendente"
    return {**base, "estado": estado, "slots": slots,
            "mapeamento_de_entidades_verificado": False}
